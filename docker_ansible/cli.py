import dagger
import typer
import asyncio
from dotenv import load_dotenv

app = typer.Typer()

@app.command()
def build_and_publish(
    os: str = typer.Option(..., help="Target OS name, e.g. alpine, debian, etc."),
    os_ver: str = typer.Option(
        ..., help="Target OS version, e.g. 3.20, bookworm, etc."
    ),
    upstream_org: str = typer.Option(None, help="Override upstream org (optional)"),
    upstream_os: str = typer.Option(None, help="Override upstream OS (optional)"),
    upstream_os_ver: str = typer.Option(
        None, help="Override upstream OS version (optional)"
    ),
    target_image_semver: str = typer.Option("0.0.0", help="Target image semver tag"),
    uv_version: str = typer.Option("latest", help="uv version to use"),
    sha: str = typer.Option("", help="SHA for working dir/env"),
    dockerhub_repo: str = typer.Option(
        "docker.io/andrewrothstein", help="Docker Hub repo"
    ),
    ghcr_repo: str = typer.Option("ghcr.io/andrewrothstein", help="GHCR repo"),
    push: bool = typer.Option(False, help="Push images after build"),
    dockerhub_username: str = typer.Option(None, help="Docker Hub username (for auth)"),
    dockerhub_password: str = typer.Option(None, help="Docker Hub password (for auth)"),
    ghcr_username: str = typer.Option(None, help="GHCR username (for auth)"),
    ghcr_password: str = typer.Option(None, help="GHCR password (for auth)"),
):
    """
    Build and publish docker-ansible image for a given OS/OS_VER using Dagger.
    """
    load_dotenv()
    asyncio.run(_build_and_publish_async(
        os,
        os_ver,
        upstream_org,
        upstream_os,
        upstream_os_ver,
        target_image_semver,
        uv_version,
        sha,
        dockerhub_repo,
        ghcr_repo,
        push,
        dockerhub_username,
        dockerhub_password,
        ghcr_username,
        ghcr_password,
    ))

async def _build_and_publish_async(
    os: str,
    os_ver: str,
    upstream_org: str,
    upstream_os: str,
    upstream_os_ver: str,
    target_image_semver: str,
    uv_version: str,
    sha: str,
    dockerhub_repo: str,
    ghcr_repo: str,
    push: bool,
    dockerhub_username: str,
    dockerhub_password: str,
    ghcr_username: str,
    ghcr_password: str
):
    # Compose image tags
    tag = f"docker-ansible:{target_image_semver}-{os}.{os_ver}"
    dockerhub_tag = f"{dockerhub_repo}/{tag}"
    ghcr_tag = f"{ghcr_repo}/{tag}"

    # Compose build args
    build_args = {
        "OS": os,
        "OS_VER": os_ver,
        "TARGET_IMAGE_SEMVER": target_image_semver,
        "UV_VERSION": uv_version,
        "SHA": sha,
    }
    if upstream_org:
        build_args["UPSTREAM_ORG"] = upstream_org
    if upstream_os:
        build_args["UPSTREAM_OS"] = upstream_os
    if upstream_os_ver:
        build_args["UPSTREAM_OS_VER"] = upstream_os_ver

    # Compose UPSTREAM_IMAGE as in docker-bake.hcl
    upstream_registry = "docker.io"
    default_upstream_org = "library"
    uorg = upstream_org if upstream_org else default_upstream_org
    uos = upstream_os if upstream_os else os
    uosver = upstream_os_ver if upstream_os_ver else os_ver
    upstream_image = f"{upstream_registry}/{uorg}/{uos}:{uosver}"

    # Read Dagger Cloud token from environment (optional, now loaded via dotenv)
    async with dagger.Connection() as client:
        src = await client.host().directory(".")
        # Get uv binary from the uv image
        uv_container = await client.container().from_(f"ghcr.io/astral-sh/uv:{uv_version}")
        uv_bin = await uv_container.file("/uv")

        # Start from the upstream image
        ctr = await client.container().from_(upstream_image)
        # Copy uv binary
        ctr = await (
            ctr.with_file("/usr/local/bin/uv", uv_bin)
            .with_exec(["uv", "tool", "install", "ansible-core", "--with", "ansible"])
        )

        # Copy profile.d scripts
        ctr = await ctr.with_directory(
            "/etc/profile.d",
            await src.directory("profile.d")
        )
        # Set up working directory
        wdir = f"/docker-ansible{sha}"
        ctr = await (
            ctr
            .with_directory(wdir, src.directory("docker_ansible"))
            .with_files(wdir, [
                src.file("uv.lock"),
                src.file("pyproject.toml")
                ])
            .with_workdir(wdir)
            .with_exec(["uv", "sync", "--frozen", "--no-dev"])
            .with_env_variable("SHELL", "/bin/sh -lc")
            .with_env_variable(
                "ANSIBLE_PYTHON_INTERPRETER",
                "/root/.local/share/uv/tools/ansible-core/bin/python3"
            )
            .with_file("/etc/ansible/ansible.cfg", await src.file("ansible.cfg"))
            .with_file("/etc/ansible/inventories/localhost", await src.file("localhost-inventory"))
        )
        # Run ansible_install and clean up .git
        ctr = await ctr.with_exec(
            [
                "sh", "-lc",
                """
                ansible --version \
                    && ansible all --list-hosts \
                    && ansible localhost -m ping
                rm -rf .git/
                """
            ]
        )

        if push:
            # Docker Hub
            if dockerhub_username and dockerhub_password:
                dockerhub_password_secret = client.set_secret("dockerhub_password", dockerhub_password)
                ctr = await ctr.with_registry_auth(
                    "docker.io", dockerhub_username, dockerhub_password_secret
                )
            await ctr.publish(dockerhub_tag)
            # GHCR
            if ghcr_username and ghcr_password:
                ghcr_password_secret = client.set_secret("ghcr_password", ghcr_password)
                ctr = await ctr.with_registry_auth("ghcr.io", ghcr_username, ghcr_password_secret)
            await ctr.publish(ghcr_tag)
            print(f"Pushed: {dockerhub_tag} and {ghcr_tag}")
        else:
            print(
                f"Built image but did not push (dry run): {dockerhub_tag} and {ghcr_tag}"
            )

if __name__ == "__main__":
    app()
