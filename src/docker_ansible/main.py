from dataclasses import dataclass
from typing import Any
import dagger
from dagger import dag, function, object_type
import asyncio
import json
import textwrap

import yaml

# Galaxy OS name mapping for meta/main.yml platforms section
GALAXY_OS_NAME = {
    "alpine": "Alpine",
    "archlinux": "ArchLinux",
    "debian": "Debian",
    "fedora": "Fedora",
    "kali": "Kali",
    "rockylinux": "EL",
    "ubi": "EL",
    "ubuntu": "Ubuntu",
}

# OS types that use "all" for versions in Galaxy metadata
# (Galaxy only accepts limited version strings for some distros)
GALAXY_ALL_VERSIONS = {"alpine", "archlinux", "fedora", "kali"}


class IndentedDumper(yaml.SafeDumper):
    """Custom YAML dumper that properly indents list items under their parent keys."""
    pass


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    """Represent strings, using literal style for multi-line strings."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


IndentedDumper.add_representer(str, _str_representer)


def _increase_indent(self, flow: bool = False, indentless: bool = False) -> None:  # type: ignore
    """Override to ensure proper indentation of list items."""
    return super(IndentedDumper, self).increase_indent(flow, False)


IndentedDumper.increase_indent = _increase_indent  # type: ignore


@dataclass
class Tag:
    semver: str
    os: str
    os_ver: str

    def __str__(self) -> str:
        return f"{self.semver}-{self.os}.{self.os_ver}"


@dataclass
class Image:
    registry: str
    org: str
    repo: str

    def __str__(self) -> str:
        return f"{self.registry}/{self.org}/{self.repo}"


@object_type
class DockerAnsible:
    def ansible_cfg(self) -> dagger.File:
        return dag.file(
            "ansible.cfg",
            contents=textwrap.dedent(
                """
                [defaults]
                inventory = /etc/ansible/inventories
                transport = local
                callbacks_enabled = ansible.posix.timer,ansible.posix.profile_tasks
                # Enable interpreter discovery to find the right Python for each module
                interpreter_python = auto_silent
                """
            ),
        )

    def localhost_inventory(self) -> dagger.File:
        return dag.file("localhost", contents="localhost")

    def local_bin_path_sh(self) -> dagger.File:
        return dag.file(
            "local-bin-path.sh", contents="export PATH=$HOME/.local/bin:$PATH"
        )

    def pkg_manager_sh(self) -> dagger.File:
        return dag.file(
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
                            export DEBIAN_FRONTEND=noninteractive
                            apt-get update -qq
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
                            DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$@"
                            ;;
                        dnf)
                            dnf install -y --nobest --skip-broken "$@"
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
                            # DNF-based systems: RHEL 9+, Fedora, etc.
                            # First ensure Python 3 is installed
                            pkg_install python3
                            # Install development tools needed for building Python packages with C extensions
                            pkg_install gcc python3-devel libffi-devel
                            # Try to install both packages - dnf will ignore already satisfied dependencies
                            # python3-libdnf5 is for Fedora 41+ and newer systems using DNF5
                            # python3-dnf is for older systems still using DNF4
                            pkg_install python3-libdnf5 python3-dnf || pkg_install python3-dnf
                            ;;
                        yum)
                            # YUM-based systems: older RHEL/CentOS
                            pkg_install python3 python3-dnf
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

    def etc_profiled(self) -> dagger.Directory:
        return (
            dag.directory()
            .with_file("local-bin-path.sh", self.local_bin_path_sh())
            .with_file("pkg-manager.sh", self.pkg_manager_sh())
        )

    def requirements_yml(self) -> dagger.File:
        return dag.file(
            "requirements.yml",
            contents=textwrap.dedent(
                """
                ---
                collections:
                  - name: ansible.posix
                  - name: ansible.utils
                  - name: community.general
                roles:
                  - name: andrewrothstein.pkg_upgrade
                  - name: andrewrothstein.unarchivedeps
                """
            ),
        )

    def playbook_yml(self) -> dagger.File:
        return dag.file(
            "playbook.yml",
            contents=textwrap.dedent(
                """
                ---
                - hosts: all
                  roles:
                    - andrewrothstein.pkg_upgrade
                    - andrewrothstein.unarchivedeps
                """
            ),
        )

    def login_sh(self, cmd: str) -> list[str]:
        return ["/bin/sh", "-lec", cmd]

    def build_one(
        self,
        os: str,
        os_ver: str,
        upstream_org: str | None = None,
        upstream_os: str | None = None,
        upstream_os_ver: str | None = None,
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
            .with_directory("/etc/profile.d", self.etc_profiled())
            .with_exec(
                self.login_sh(
                    textwrap.dedent(
                        """
                        pkg_update \
                            && install_ca_certificates \
                            && install_ansible_deps
                        """
                    )
                )
            )
            .with_file("/usr/local/bin/uv", uv_bin)
            .with_exec(["uv", "tool", "install", "ansible-core"])
            .with_file("/etc/ansible/ansible.cfg", self.ansible_cfg())
            .with_file(
                "/etc/ansible/inventories/localhost",
                self.localhost_inventory(),
            )
            .with_workdir("/root")
            .with_file("requirements.yml", self.requirements_yml())
            .with_file("playbook.yml", self.playbook_yml())
            .with_exec(
                self.login_sh(
                    textwrap.dedent(
                        """
                        ansible --version \
                            && ansible-galaxy install -r requirements.yml \
                            && ansible all --list-hosts \
                            && ansible localhost -m ping \
                            && ansible-playbook playbook.yml
                        """
                    ),
                )
            )
        )

    @function(doc="Build docker-ansible images for specified OS and platforms")
    def build(
        self,
        os: str,
        os_ver: str,
        upstream_org: str | None = None,
        upstream_os: str | None = None,
        upstream_os_ver: str | None = None,
        uv_version: str = "latest",
        platforms: str = "linux/amd64",
    ) -> list[dagger.Container]:
        return [
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

    @function(doc="Build and publish docker-ansible images to Docker Hub and GHCR")
    async def publish(
        self,
        os: str,
        os_ver: str,
        dockerhub_username: str | None = None,
        dockerhub_password: dagger.Secret | None = None,
        ghcr_username: str | None = None,
        ghcr_password: dagger.Secret | None = None,
        upstream_org: str | None = None,
        upstream_os: str | None = None,
        upstream_os_ver: str | None = None,
        target_image_semver: str = "0.0.0",
        uv_version: str = "latest",
        dockerhub_registry: str = "docker.io",
        dockerhub_org: str = "andrewrothstein",
        dockerhub_repo: str = "docker-ansible",
        ghcr_registry: str = "ghcr.io",
        ghcr_org: str = "andrewrothstein",
        ghcr_repo: str = "docker-ansible",
        platforms: str = "linux/amd64",
    ) -> list[str]:
        # Compose image tags
        v = Tag(
            semver=target_image_semver,
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

        ctr = self.build(
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

    def test_role_one(
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
                self.login_sh(
                    textwrap.dedent(
                        """
                        if [ -f meta/requirements.yml ];
                        then
                            ansible-galaxy install \
                                -r meta/requirements.yml;
                        fi
                        if [ -f test-requirements.yml ];
                        then
                            ansible-galaxy install \
                                -r test-requirements.yml;
                        fi
                        if [ -f test-inventory.ini ];
                        then
                            ansible-playbook \
                                -i test-inventory.ini \
                                test.yml;
                        else
                            ansible-playbook \
                                test.yml;
                        fi
                        """
                    )
                )
            )
        )

    @function(doc="Test an Ansible role and optionally publish to a registry")
    async def test_role(
        self,
        os: str,
        os_ver: str,
        role_name: str = "test-role",
        role_dir: dagger.Directory | None = None,
        upstream_registry: str = "ghcr.io",
        upstream_org: str = "andrewrothstein",
        upstream_repo: str = "docker-ansible",
        upstream_semver: str = "0.0.0",
        target_registry: str | None = None,
        target_org: str | None = None,
        target_username: str | None = None,
        target_password: dagger.Secret | None = None,
        target_semver: str = "0.0.0",
        platforms: str = "linux/amd64",
        git_sha: str | None = None,
        publish_latest: bool = False,
    ) -> list[str]:
        # Construct the base image tag
        tag = Tag(
            semver=upstream_semver,
            os=os,
            os_ver=os_ver,
        )

        # Use GHCR by default
        fq_upstream_image = f"{upstream_registry}/{upstream_org}/{upstream_repo}:{tag}"

        # Default role_dir to source directory if not provided
        if role_dir is None:
            role_dir = dag.current_module().source()

        # Test on each platform
        containers = [
            self.test_role_one(
                role_dir=role_dir,
                os=os,
                os_ver=os_ver,
                base_image=fq_upstream_image,
                p=p,
            )
            for p in platforms.split(",")
            if p
        ]

        published_images = []

        # Only publish if all required parameters are provided
        if target_registry and target_org and target_username and target_password:
            # Build list of tags to publish
            tags_to_publish = []

            # Primary tag with git SHA if provided, otherwise just semver
            if git_sha:
                # During build stage: publish with SHA
                primary_tag = f"{target_semver}-{os}.{os_ver}.{git_sha}"
                tags_to_publish.append(primary_tag)
            else:
                # During final publish stage: publish clean semver tag
                primary_tag = Tag(
                    semver=target_semver,
                    os=os,
                    os_ver=os_ver,
                )
                tags_to_publish.append(str(primary_tag))

                # Also publish latest tag if requested
                if publish_latest:
                    latest_tag = Tag(
                        semver="latest",
                        os=os,
                        os_ver=os_ver,
                    )
                    tags_to_publish.append(str(latest_tag))

            # Publish to all tags
            for tag_str in tags_to_publish:
                image_ref = f"{target_registry}/{target_org}/{role_name}:{tag_str}"

                published = (
                    await dag.container()
                    .with_registry_auth(
                        target_registry, target_username, target_password
                    )
                    .publish(image_ref, platform_variants=containers)
                )

                published_images.append(published)

        return published_images

    # --- Helper methods for gen_role_files ---

    async def _get_master_platform_matrix(self) -> list[dict[str, Any]]:
        """Read docker-ansible's platform-matrix-v1.json from module source."""
        matrix_file = dag.current_module().source().file("platform-matrix-v1.json")
        content = await matrix_file.contents()
        return json.loads(content)

    async def _read_exclusions(
        self, role_dir: dagger.Directory
    ) -> dict[str, Any] | None:
        """Read exclude-platforms.json from role_dir if present."""
        try:
            content = await role_dir.file("exclude-platforms.json").contents()
            return json.loads(content)
        except Exception:
            return None

    def _apply_os_exclusions(
        self,
        platforms: list[dict[str, Any]],
        exclusions: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Filter out excluded OS/version combinations."""
        if not exclusions or "exclude_os" not in exclusions:
            return platforms

        exclude_os = exclusions["exclude_os"]
        result = []

        for p in platforms:
            excluded = False
            for excl in exclude_os:
                # Check if this platform matches the exclusion
                if p["OS"] == excl["OS"]:
                    # If OS_VER is specified, only exclude that specific version
                    if "OS_VER" in excl:
                        if p["OS_VER"] == excl["OS_VER"]:
                            excluded = True
                            break
                    else:
                        # Exclude all versions of this OS
                        excluded = True
                        break
            if not excluded:
                result.append(p)

        return result

    def _apply_arch_exclusions(
        self,
        platforms: list[dict[str, Any]],
        exclusions: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Remove excluded architectures from platforms field."""
        if not exclusions or "exclude_arch" not in exclusions:
            return platforms

        exclude_arch = set(exclusions["exclude_arch"])
        result = []

        for p in platforms:
            p_copy = p.copy()
            if "PLATFORMS" in p_copy:
                # Filter out excluded architectures
                archs = [
                    a.strip()
                    for a in p_copy["PLATFORMS"].split(",")
                    if a.strip() and a.strip() not in exclude_arch
                ]
                if archs:
                    p_copy["PLATFORMS"] = ",".join(archs)
                    result.append(p_copy)
                # If no archs remain, skip this entry entirely
            else:
                result.append(p_copy)

        return result

    def _render_role_platform_matrix(
        self,
        platforms: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Convert master matrix to role format with lowercase 'platforms' field."""
        result = []
        for p in platforms:
            entry = {
                "OS": p["OS"],
                "OS_VER": p["OS_VER"],
            }
            if "PLATFORMS" in p:
                # Use lowercase 'platforms' for role matrix
                entry["platforms"] = p["PLATFORMS"]
            result.append(entry)
        return result

    def _render_galaxy_platforms(
        self,
        platforms: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Convert platform matrix to Galaxy-compatible format."""
        by_os: dict[str, set[str]] = {}

        for p in platforms:
            os = p["OS"]
            galaxy_name = GALAXY_OS_NAME.get(os, os.title())
            versions = by_os.setdefault(galaxy_name, set())

            if os in GALAXY_ALL_VERSIONS:
                versions.add("all")
            else:
                versions.add(p["OS_VER"])

        result = []
        for os_name in sorted(by_os.keys()):
            result.append({
                "name": os_name,
                "versions": sorted(by_os[os_name]),
            })
        return result

    def _render_build_workflow(self, workflow_ref: str) -> str:
        """Generate .github/workflows/build.yml content."""
        workflow = {
            "name": "build",
            "on": "push",
            "jobs": {
                "dagger-ansible-test-role": {
                    "uses": f"andrewrothstein/docker-ansible/.github/workflows/dagger-ansible-test-role.yml@{workflow_ref}",
                    "secrets": "inherit",
                }
            },
        }
        return yaml.dump(workflow, Dumper=IndentedDumper, explicit_start=True, default_flow_style=False, sort_keys=False)

    def _render_gitignore(self) -> str:
        """Generate .gitignore content."""
        return textwrap.dedent("""\
            **~*.retry
            Dockerfile.*
            requirements.yml
            !meta/requirements.yml
            **/*undo-tree*
            .ansible
            """)

    async def _read_meta_main(
        self, role_dir: dagger.Directory
    ) -> dict[str, Any] | None:
        """Read existing meta/main.yml from role_dir if present."""
        try:
            content = await role_dir.file("meta/main.yml").contents()
            return yaml.safe_load(content)
        except Exception:
            return None

    def _update_meta_main(
        self,
        existing_meta: dict[str, Any] | None,
        galaxy_platforms: list[dict[str, Any]],
        role_name: str,
    ) -> dict[str, Any]:
        """Update or create meta/main.yml with platforms."""
        if existing_meta is None:
            existing_meta = {}

        # Ensure galaxy_info exists
        if "galaxy_info" not in existing_meta:
            existing_meta["galaxy_info"] = {}

        galaxy_info = existing_meta["galaxy_info"]

        # Set defaults if not present
        if "author" not in galaxy_info:
            galaxy_info["author"] = "andrewrothstein"
        if "namespace" not in galaxy_info:
            galaxy_info["namespace"] = "andrewrothstein"

        # Compute role_name from directory name if not present
        if "role_name" not in galaxy_info:
            # Strip 'ansible-' prefix if present
            computed_name = role_name
            if computed_name.startswith("ansible-"):
                computed_name = computed_name[8:]
            galaxy_info["role_name"] = computed_name

        # Update platforms
        galaxy_info["platforms"] = galaxy_platforms

        return existing_meta

    @function(doc="Generate GitHub Actions workflow and config files for an Ansible role")
    async def gen_role_files(
        self,
        role_name: str,
        role_dir: dagger.Directory | None = None,
        workflow_ref: str = "develop",
    ) -> dagger.Directory:
        """
        Generate role configuration files:
        - .github/workflows/build.yml
        - platform-matrix-v1.json
        - .gitignore
        - meta/main.yml (updated with platforms)

        Reads exclude-platforms.json from role_dir if present to filter platforms.
        """
        # Get master platform matrix from docker-ansible
        master_matrix = await self._get_master_platform_matrix()

        # Default role_dir to empty directory if not provided
        if role_dir is None:
            role_dir = dag.directory()

        # Read exclusions from role_dir
        exclusions = await self._read_exclusions(role_dir)

        # Apply exclusions
        filtered = self._apply_os_exclusions(master_matrix, exclusions)
        filtered = self._apply_arch_exclusions(filtered, exclusions)

        # Generate role platform matrix (with lowercase 'platforms')
        role_matrix = self._render_role_platform_matrix(filtered)

        # Generate Galaxy platforms for meta/main.yml
        galaxy_platforms = self._render_galaxy_platforms(filtered)

        # Read existing meta/main.yml if present
        existing_meta = await self._read_meta_main(role_dir)

        # Update meta/main.yml
        updated_meta = self._update_meta_main(existing_meta, galaxy_platforms, role_name)

        # Build output directory
        return (
            dag.directory()
            .with_new_file(
                ".github/workflows/build.yml",
                self._render_build_workflow(workflow_ref),
            )
            .with_new_file(
                "platform-matrix-v1.json",
                json.dumps(role_matrix, indent=2) + "\n",
            )
            .with_new_file(
                ".gitignore",
                self._render_gitignore(),
            )
            .with_new_file(
                "meta/main.yml",
                yaml.dump(updated_meta, Dumper=IndentedDumper, explicit_start=True, default_flow_style=False, sort_keys=False),
            )
        )
