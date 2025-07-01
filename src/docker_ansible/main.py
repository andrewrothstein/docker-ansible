from dataclasses import dataclass
from typing import Optional, List
import dagger
from dagger import dag, function, object_type
import asyncio


@dataclass
class Tag:
    target_image_semver: str
    os: str
    os_ver: str

    def __str__(self) -> str:
        return f"{self.target_image_semver}-{self.os}.{self.os_ver}"


@dataclass
class Image:
    registry: str
    org: str
    repo: str

    def __str__(self) -> str:
        return f"{self.registry}/{self.org}/{self.repo}"


@object_type
class DockerAnsible:
    async def ansible_cfg(self) -> dagger.File:
        # Updated for Dagger Python SDK: use dag.client().file(name, contents=...)
        return await dag.file(
            "ansible.cfg",
            contents="""
[defaults]
inventory = /etc/ansible/inventories
transport = local
callbacks_enabled = ansible.posix.timer,ansible.posix.profile_tasks
                """,
        )

    async def localhost_inventory(self) -> dagger.File:
        return await dag.file("localhost", contents="localhost")

    async def local_bin_path_sh(self) -> dagger.File:
        return await dag.file(
            "local-bin-path.sh", contents="export PATH=$HOME/.local/bin:$PATH"
        )

    async def etc_profiled(self) -> dagger.Directory:
        return dag.directory().with_file(
            "local-bin-path.sh", await self.local_bin_path_sh()
        )

    async def build_one(
        self,
        os: str,
        os_ver: str,
        upstream_org: Optional[str] = None,
        upstream_os: Optional[str] = None,
        upstream_os_ver: Optional[str] = None,
        uv_version: str = "latest",
        p: str = "linux/amd64",
    ) -> dagger.Container:
        plat = dagger.Platform(p)
        upstream_image = Image(
            registry="docker.io",
            org=upstream_org or "library",
            repo=upstream_os or os,
        )
        upstream_image = f"{upstream_image}:{upstream_os_ver or os_ver}"

        # Get uv binary from the uv image
        uv_bin = (
            dag.container(platform=plat)
            .from_(f"ghcr.io/astral-sh/uv:{uv_version}")
            .file("/uv")
        )

        # Start from the upstream image
        return (
            dag.container(platform=plat)
            .from_(upstream_image)
            .with_file("/usr/local/bin/uv", await uv_bin)
            .with_exec(["uv", "tool", "install", "ansible-core"])
            .with_directory("/etc/profile.d", await self.etc_profiled())
            .with_env_variable(
                "ANSIBLE_PYTHON_INTERPRETER",
                "/root/.local/share/uv/tools/ansible-core/bin/python3",
            )
            .with_file("/etc/ansible/ansible.cfg", await self.ansible_cfg())
            .with_file(
                "/etc/ansible/inventories/localhost",
                await self.localhost_inventory(),
            )
            .with_exec(
                [
                    "sh",
                    "-lc",
                    """
    ansible --version \
        && ansible all --list-hosts \
        && ansible localhost -m ping
                    """,
                ]
            )
                .with_workdir("/root")
                .with_file(
                    "requirements.yml",
                    await wdir.file("requirements.yml")
                )
                .with_file(
                    "playbook.yml",
                    await wdir.file("playbook.yml")
                )
                .with_exec(
                    [
                        "sh",
                        "-lc",
                        """
                        ansible-galaxy install -r requirements.yml \
                        ansible-playbook playbook.yml
                        """,
                    ]
                )
        )

    @function
    async def build(
        self,
        os: str,
        os_ver: str,
        upstream_org: Optional[str] = None,
        upstream_os: Optional[str] = None,
        upstream_os_ver: Optional[str] = None,
        uv_version: str = "latest",
        platforms: str = "linux/amd64",
    ) -> List[dagger.Container]:
        tasks = [
            self.build_one(
                os=os,
                os_ver=os_ver,
                upstream_org=upstream_org,
                upstream_os=upstream_os,
                upstream_os_ver=upstream_os_ver,
                uv_version=uv_version,
                p=p,
            )
            for p in platforms.split(",")
            if p
        ]
        return await asyncio.gather(*tasks)

    @function
    async def publish(
        self,
        os: str,
        os_ver: str,
        dockerhub_username: Optional[str] = None,
        dockerhub_password: Optional[dagger.Secret] = None,
        ghcr_username: Optional[str] = None,
        ghcr_password: Optional[dagger.Secret] = None,
        upstream_org: Optional[str] = None,
        upstream_os: Optional[str] = None,
        upstream_os_ver: Optional[str] = None,
        target_image_semver: str = "0.0.0",
        uv_version: str = "latest",
        dockerhub_registry: str = "docker.io",
        dockerhub_org: str = "andrewrothstein",
        dockerhub_repo: str = "docker-ansible",
        ghcr_registry: str = "ghcr.io",
        ghcr_org: str = "andrewrothstein",
        ghcr_repo: str = "docker-ansible",
        platforms: str = "linux/amd64",
    ) -> List[str]:
        # Compose image tags
        v = Tag(
            target_image_semver=target_image_semver,
            os=os,
            os_ver=os_ver,
        )

        dockerhub = Image(
            registry=dockerhub_registry,
            org=dockerhub_org,
            repo=dockerhub_repo,
        )

        ghcr = Image(
            registry=ghcr_registry,
            org=ghcr_org,
            repo=ghcr_repo,
        )

        ctr = await self.build(
            os,
            os_ver,
            upstream_org,
            upstream_os,
            upstream_os_ver,
            uv_version,
            platforms=platforms,
        )

        image_pushes: List[str] = []
        # tag and publish images
        if dockerhub_username and dockerhub_password:
            image_pushes.append(
                dag.container()
                .with_registry_auth(
                    dockerhub_registry, dockerhub_username, dockerhub_password
                )
                .publish(f"{dockerhub}:{v}", platform_variants=ctr)
            )
        if ghcr_username and ghcr_password:
            image_pushes.append(
                dag.container()
                .with_registry_auth(ghcr_registry, ghcr_username, ghcr_password)
                .publish(f"{ghcr}:{v}", platform_variants=ctr)
            )
        return await asyncio.gather(*image_pushes) if len(image_pushes) > 0 else []

    async def test_role_one(
        self,
        role_dir: dagger.Directory,
        os: str,
        os_ver: str,
        base_image: str,
        p: str = "linux/amd64",
    ) -> dagger.Container:
        """Test a single platform."""
        plat = dagger.Platform(p)

        # Start from the pre-built docker-ansible image
        return (
            dag.container(platform=plat)
            .from_(base_image)
            .with_directory("/ansible-role", role_dir)
            .with_workdir("/ansible-role")
            .with_exec(
                [
                    "sh",
                    "-lc",
                    "if [ -f meta/requirements.yml ]; then ansible-galaxy install -r meta/requirements.yml; fi",
                ]
            )
            .with_exec(
                [
                    "sh",
                    "-lc",
                    "if [ -f test-requirements.yml ]; then ansible-galaxy install -r test-requirements.yml; fi",
                ]
            )
            .with_exec(
                [
                    "sh",
                    "-lc",
                    """
                    if [ -f test-inventory.ini ]; then
                        ansible-playbook -i test-inventory.ini test.yml
                    else
                        ansible-playbook test.yml
                    fi
                    """,
                ]
            )
        )

    @function
    async def test_role(
        self,
        role_dir: dagger.Directory,
        os: str,
        os_ver: str,
        upstream_org: Optional[str] = None,
        upstream_os: Optional[str] = None,
        upstream_os_ver: Optional[str] = None,
        target_image_semver: str = "0.0.0",
        dockerhub_registry: str = "docker.io",
        dockerhub_org: str = "andrewrothstein",
        dockerhub_repo: str = "docker-ansible",
        ghcr_registry: str = "ghcr.io",
        ghcr_org: str = "andrewrothstein",
        ghcr_repo: str = "docker-ansible",
        use_ghcr: bool = True,
        platforms: str = "linux/amd64",
    ) -> List[dagger.Container]:
        """
        Test an Ansible role using the pre-built docker-ansible base images.

        Expects the role directory structure:
        - test.yml at the root (the test playbook)
        - meta/requirements.yml (optional Galaxy dependencies)
        - Standard Ansible role structure (tasks/, vars/, defaults/, etc.)

        Args:
            role_dir: Directory containing the Ansible role to test
            os: Operating system (e.g., ubuntu, debian, alpine)
            os_ver: OS version (e.g., noble, bookworm, 3.20)
            upstream_org: Override upstream organization (for special cases like kali)
            upstream_os: Override upstream OS name
            upstream_os_ver: Override upstream OS version
            target_image_semver: Version of docker-ansible image to use (default: latest)
            dockerhub_registry: Docker Hub registry URL
            dockerhub_org: Docker Hub organization
            dockerhub_repo: Docker Hub repository name
            ghcr_registry: GitHub Container Registry URL
            ghcr_org: GHCR organization
            ghcr_repo: GHCR repository name
            use_ghcr: Use GHCR instead of Docker Hub for base image (default: True)
            platforms: Comma-separated list of platforms to test

        Returns:
            List of containers with test results
        """
        # Construct the base image tag
        tag = Tag(
            target_image_semver=target_image_semver,
            os=os,
            os_ver=os_ver,
        )

        # Use GHCR by default
        if use_ghcr:
            base_image = f"{ghcr_registry}/{ghcr_org}/{ghcr_repo}:{tag}"
        else:
            base_image = f"{dockerhub_registry}/{dockerhub_org}/{dockerhub_repo}:{tag}"

        # Test on each platform
        tasks = [
            self.test_role_one(
                role_dir=role_dir,
                os=os,
                os_ver=os_ver,
                base_image=base_image,
                p=p,
            )
            for p in platforms.split(",")
            if p
        ]
        return await asyncio.gather(*tasks)
