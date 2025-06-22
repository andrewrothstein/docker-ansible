from dataclasses import dataclass
from typing import Optional
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
    @function
    async def build(
        self,
        wdir: dagger.Directory,
        os: str,
        os_ver: str,
        upstream_org: Optional[str] = None,
        upstream_os: Optional[str] = None,
        upstream_os_ver: Optional[str] = None,
        uv_version: str = "latest",
    ) -> dagger.Container:
        upstream_image = Image(
            registry="docker.io",
            org=upstream_org or "library",
            repo=upstream_os or os,
        )
        upstream_image = f"{upstream_image}:{upstream_os_ver or os_ver}"

        # Get uv binary from the uv image
        uv_bin = dag.container().from_(f"ghcr.io/astral-sh/uv:{uv_version}").file("/uv")

        # Start from the upstream image
        return (
            dag.container()
            .from_(upstream_image)
            .with_file("/usr/local/bin/uv", await uv_bin)
            .with_exec(["uv", "tool", "install", "ansible-core", "--with", "ansible"])
            .with_directory("/etc/profile.d", await wdir.directory("profile.d"))
            .with_env_variable("SHELL", "/bin/sh -lc")
            .with_env_variable(
                "ANSIBLE_PYTHON_INTERPRETER",
                "/root/.local/share/uv/tools/ansible-core/bin/python3",
            )
            .with_file("/etc/ansible/ansible.cfg", await wdir.file("ansible.cfg"))
            .with_file(
                "/etc/ansible/inventories/localhost",
                await wdir.file("localhost-inventory"),
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
        wdir: dagger.Directory,
        os: str,
        os_ver: str,
        dockerhub_username: str,
        dockerhub_password: dagger.Secret,
        ghcr_username: str,
        ghcr_password: dagger.Secret,
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
    ) -> None:
        # Compose image tags
        ctr = await self.build(
            wdir,
            os,
            os_ver,
            upstream_org,
            upstream_os,
            upstream_os_ver,
            uv_version,
        )

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

        await ctr.with_registry_auth(
            dockerhub_registry, dockerhub_username, dockerhub_password
        ).publish(f"{dockerhub}:{v}")
        await ctr.with_registry_auth(
            ghcr_registry, ghcr_username, ghcr_password
        ).publish(f"{ghcr}:{v}")
