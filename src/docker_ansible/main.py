from dataclasses import dataclass
from typing import Optional, List
import dagger
from dagger import dag, function, object_type
import asyncio
import textwrap


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
            contents=textwrap.dedent(
                """
                [defaults]
                inventory = /etc/ansible/inventories
                transport = local
                callbacks_enabled = ansible.posix.timer,ansible.posix.profile_tasks
                # Enable interpreter discovery to find the right Python for each module
                interpreter_python = auto_silent
                # Allow Ansible to use system Python for package modules
                ansible_python_interpreter = /root/.local/share/uv/tools/ansible-core/bin/python3
                """
            ),
        )

    async def localhost_inventory(self) -> dagger.File:
        return await dag.file("localhost", contents="localhost")

    async def local_bin_path_sh(self) -> dagger.File:
        return await dag.file(
            "local-bin-path.sh", contents="export PATH=$HOME/.local/bin:$PATH"
        )

    async def pkg_manager_sh(self) -> dagger.File:
        return await dag.file(
            "pkg-manager.sh",
            contents=textwrap.dedent(
                """
                #!/bin/sh

                # Package manager detection and helper functions

                detect_pkg_manager() {
                    if command -v apk >/dev/null 2>&1; then
                        echo "apk"
                    elif command -v apt-get >/dev/null 2>&1; then
                        echo "apt"
                    elif command -v dnf >/dev/null 2>&1; then
                        echo "dnf"
                    elif command -v yum >/dev/null 2>&1; then
                        echo "yum"
                    elif command -v pacman >/dev/null 2>&1; then
                        echo "pacman"
                    else
                        echo "unknown"
                    fi
                }

                pkg_update() {
                    PKG_MGR=$(detect_pkg_manager)
                    case "$PKG_MGR" in
                        apk)
                            apk update
                            ;;
                        apt)
                            apt-get update
                            ;;
                        dnf|yum)
                            # dnf/yum don't need explicit update
                            :
                            ;;
                        pacman)
                            pacman -Sy
                            ;;
                        *)
                            echo "Unknown package manager"
                            return 1
                            ;;
                    esac
                }

                pkg_install() {
                    PKG_MGR=$(detect_pkg_manager)
                    case "$PKG_MGR" in
                        apk)
                            apk add --no-cache "$@"
                            ;;
                        apt)
                            apt-get install -y "$@"
                            ;;
                        dnf)
                            dnf install -y "$@"
                            ;;
                        yum)
                            yum install -y "$@"
                            ;;
                        pacman)
                            pacman -S --noconfirm "$@"
                            ;;
                        *)
                            echo "Unknown package manager"
                            return 1
                            ;;
                    esac
                }

                # Install CA certificates using the appropriate package name for each distro
                install_ca_certificates() {
                    PKG_MGR=$(detect_pkg_manager)
                    case "$PKG_MGR" in
                        apk)
                            pkg_install ca-certificates
                            ;;
                        apt)
                            pkg_install ca-certificates
                            ;;
                        dnf|yum)
                            pkg_install ca-certificates
                            ;;
                        pacman)
                            pkg_install ca-certificates
                            ;;
                        *)
                            echo "Unknown package manager"
                            return 1
                            ;;
                    esac
                }

                # Install minimal Python packages for package management modules
                install_ansible_deps() {
                    PKG_MGR=$(detect_pkg_manager)
                    case "$PKG_MGR" in
                        apk)
                            # Alpine: Install Python and py3-pip for package management
                            pkg_install python3 py3-pip
                            ;;
                        apt)
                            # Debian/Ubuntu: Install python3-apt for apt module
                            pkg_install python3 python3-apt
                            ;;
                        dnf)
                            # Fedora/RHEL 9+: Install python3-dnf or python3-libdnf5 for newer versions
                            pkg_install python3
                            # Try to install both packages - dnf will ignore already satisfied dependencies
                            # python3-libdnf5 is for Fedora 41+ and newer systems using DNF5
                            # python3-dnf is for older systems still using DNF4
                            pkg_install python3-libdnf5 python3-dnf || pkg_install python3-dnf
                            ;;
                        yum)
                            # RHEL 7/8: Install python3 and python3-dnf
                            if command -v python3 >/dev/null 2>&1; then
                                pkg_install python3-dnf
                            else
                                # RHEL 7 might need python2
                                pkg_install python python-dnf
                            fi
                            ;;
                        pacman)
                            # Arch: Python is usually already installed
                            pkg_install python
                            ;;
                        *)
                            echo "Unknown package manager"
                            return 1
                            ;;
                    esac
                }
                """
            ),
        )

    async def etc_profiled(self) -> dagger.Directory:
        return (
            dag.directory()
            .with_file("local-bin-path.sh", await self.local_bin_path_sh())
            .with_file("pkg-manager.sh", await self.pkg_manager_sh())
        )

    async def requirements_yml(self) -> dagger.File:
        return await dag.file(
            "requirements.yml",
            contents=textwrap.dedent(
                """
                ---
                collections:
                  - name: ansible.posix
                  - name: ansible.utils
                  - name: community.general
                roles:
                  - name: andrewrothstein.unarchivedeps
                """
            ),
        )

    async def playbook_yml(self) -> dagger.File:
        return await dag.file(
            "playbook.yml",
            contents=textwrap.dedent(
                """
                ---
                - hosts: all
                  roles:
                    - andrewrothstein.unarchivedeps
                """
            ),
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
            .with_directory("/etc/profile.d", await self.etc_profiled())
            .with_env_variable("SHELL", "/bin/sh -lc")
            .with_exec(
                [
                    "sh",
                    "-lc",
                    "pkg_update && install_ca_certificates && install_ansible_deps",
                ]
            )
            .with_file("/usr/local/bin/uv", await uv_bin)
            .with_exec(["uv", "tool", "install", "ansible-core"])
            .with_env_variable(
                "ANSIBLE_PYTHON_INTERPRETER",
                "/root/.local/share/uv/tools/ansible-core/bin/python3",
            )
            .with_file("/etc/ansible/ansible.cfg", await self.ansible_cfg())
            .with_file(
                "/etc/ansible/inventories/localhost",
                await self.localhost_inventory(),
            )
            .with_workdir("/root")
            .with_file("requirements.yml", await self.requirements_yml())
            .with_file("playbook.yml", await self.playbook_yml())
            .with_exec(
                [
                    "sh",
                    "-lc",
                    textwrap.dedent(
                        """
                        ansible --version \
                            && ansible-galaxy install -r requirements.yml \
                            && ansible all --list-hosts \
                            && ansible localhost -m ping \
                            && ansible-playbook playbook.yml
                        """
                    ),
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

        # Collect publish operations without awaiting
        publish_tasks = []

        # Create publish task for Docker Hub
        if dockerhub_username and dockerhub_password:
            publish_tasks.append(
                dag.container()
                .with_registry_auth(
                    dockerhub_registry, dockerhub_username, dockerhub_password
                )
                .publish(f"{dockerhub}:{v}", platform_variants=ctr)
            )

        # Create publish task for GHCR
        if ghcr_username and ghcr_password:
            publish_tasks.append(
                dag.container()
                .with_registry_auth(ghcr_registry, ghcr_username, ghcr_password)
                .publish(f"{ghcr}:{v}", platform_variants=ctr)
            )

        # Execute all publish operations in parallel
        if publish_tasks:
            return await asyncio.gather(*publish_tasks)
        else:
            return []

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
