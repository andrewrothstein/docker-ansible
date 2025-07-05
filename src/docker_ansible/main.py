from dataclasses import dataclass
from typing import Optional, List
import dagger
from dagger import dag, function, object_type


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
        return dag.file().with_contents(
            """
[defaults]
inventory = /etc/ansible/inventories
transport = local
callbacks_enabled = ansible.posix.timer,ansible.posix.profile_tasks
                """
        )

    async def localhost_inventory(self) -> dagger.File:
        return dag.file().with_contents("localhost")

    async def local_bin_path_sh(self) -> dagger.File:
        return dag.file().with_contents("""export PATH=$HOME/.local/bin:$PATH""")

    async def etc_profiled(self) -> dagger.Directory:
        return dag.directory().with_file(
            "local-bin-path.sh", await self.local_bin_path_sh()
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
        containers = []
        for p in platforms.split(",") or []:
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
            containers.append(
                dag.container(platform=plat)
                .from_(upstream_image)
                .with_file("/usr/local/bin/uv", await uv_bin)
                .with_exec(
                    ["uv", "tool", "install", "ansible-core", "--with", "ansible"]
                )
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
            )
        return containers

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
    ) -> None:
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

        # tag and publish images
        if dockerhub_username and dockerhub_password:
            await (
                dag.container()
                .with_registry_auth(
                    dockerhub_registry, dockerhub_username, dockerhub_password
                )
                .publish(f"{dockerhub}:{v}", platform_variants=ctr)
            )
        if ghcr_username and ghcr_password:
            await (
                dag.container()
                .with_registry_auth(ghcr_registry, ghcr_username, ghcr_password)
                .publish(f"{ghcr}:{v}", platform_variants=ctr)
            )
