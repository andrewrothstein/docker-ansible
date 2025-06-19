from typing import Optional
import dagger
from dagger import dag, function, object_type


@object_type
class DockerAnsible:
    @function
    def container_echo(self, string_arg: str) -> dagger.Container:
        """Returns a container that echoes whatever string argument is provided"""
        return dag.container().from_("alpine:latest").with_exec(["echo", string_arg])

    @function
    async def grep_dir(self, directory_arg: dagger.Directory, pattern: str) -> str:
        """Returns lines that match a pattern
        in the files of the provided Directory"""
        return await (
            dag.container()
            .from_("alpine:latest")
            .with_mounted_directory("/mnt", directory_arg)
            .with_workdir("/mnt")
            .with_exec(["grep", "-R", pattern, "."])
            .stdout()
        )

    @function
    async def build(
        self,
        directory_arg: dagger.Directory,
        os: str,
        os_ver: str,
        upstream_org: Optional[str] = None,
        upstream_os: Optional[str] = None,
        upstream_os_ver: Optional[str] = None,
        uv_version: str = "latest",
    ) -> dagger.Container:
        # Compose UPSTREAM_IMAGE as in docker-bake.hcl
        upstream_registry = "docker.io"
        default_upstream_org = "library"
        uorg = upstream_org if upstream_org else default_upstream_org
        uos = upstream_os if upstream_os else os
        uosver = upstream_os_ver if upstream_os_ver else os_ver
        upstream_image = f"{upstream_registry}/{uorg}/{uos}:{uosver}"

        # Get uv binary from the uv image
        uv_bin = dag.container().from_(f"ghcr.io/astral-sh/uv:{uv_version}").file("/uv")

        # Start from the upstream image
        return (
            dag.container()
            .from_(upstream_image)
            .with_file("/usr/local/bin/uv", await uv_bin)
            .with_exec(["uv", "tool", "install", "ansible-core", "--with", "ansible"])
            .with_directory(
                "/etc/profile.d", await directory_arg.directory("profile.d")
            )
            .with_env_variable("SHELL", "/bin/sh -lc")
            .with_env_variable(
                "ANSIBLE_PYTHON_INTERPRETER",
                "/root/.local/share/uv/tools/ansible-core/bin/python3",
            )
            .with_file(
                "/etc/ansible/ansible.cfg", await directory_arg.file("ansible.cfg")
            )
            .with_file(
                "/etc/ansible/inventories/localhost",
                await directory_arg.file("localhost-inventory"),
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

    @function
    async def publish(
        self,
        directory_arg: dagger.Directory,
        os: str = "ubuntu",
        os_ver: str = "noble",
        upstream_org: Optional[str] = None,
        upstream_os: Optional[str] = None,
        upstream_os_ver: Optional[str] = None,
        target_image_semver: str = "0.0.0",
        uv_version: str = "latest",
        dockerhub_repo: str = "docker.io/andrewrothstein",
        ghcr_repo: str = "ghcr.io/andrewrothstein",
        dockerhub_username: Optional[str] = None,
        dockerhub_password: Optional[dagger.Secret] = None,
        ghcr_username: Optional[str] = None,
        ghcr_password: Optional[dagger.Secret] = None,
    ) -> None:
        # Compose image tags
        ctr = await self.build(
            directory_arg,
            os,
            os_ver,
            upstream_org,
            upstream_os,
            upstream_os_ver,
            uv_version,
        )

        slug = "docker-ansible"
        tag = f"{slug}:{target_image_semver}-{os}.{os_ver}"

        # Docker Hub
        if dockerhub_username and dockerhub_password:
            dockerhub_tag = f"{dockerhub_repo}/{tag}"
            await ctr.with_registry_auth(
                "docker.io", dockerhub_username, dockerhub_password
            ).publish(dockerhub_tag)
            print(f"Pushed: {dockerhub_tag}")

        # GHCR
        if ghcr_username and ghcr_password:
            ghcr_tag = f"{ghcr_repo}/{tag}"
            await ctr.with_registry_auth(
                "ghcr.io", ghcr_username, ghcr_password
            ).publish(ghcr_tag)
            print(f"Pushed: {ghcr_tag}")
