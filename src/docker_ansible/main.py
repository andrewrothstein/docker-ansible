from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import dagger
from dagger import dag, function, object_type
import asyncio
import json


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
            .with_exec(["uv", "tool", "install", "ansible-core", "--with", "ansible"])
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

    @function
    async def scan(
        self,
        os: str,
        os_ver: str,
        upstream_org: Optional[str] = None,
        upstream_os: Optional[str] = None,
        upstream_os_ver: Optional[str] = None,
        uv_version: str = "latest",
        platforms: str = "linux/amd64",
        severity: str = "HIGH,CRITICAL",
        exit_code: int = 0,
        ignore_unfixed: bool = True,
        output_format: str = "table",
    ) -> str:
        """
        Build and scan images for vulnerabilities using Trivy.
        
        Args:
            os: Operating system
            os_ver: OS version
            severity: Comma-separated list of severities to include
            exit_code: Exit code to use when vulnerabilities found (0 = don't fail)
            ignore_unfixed: Ignore vulnerabilities without fixes
            output_format: Output format (table, json, sarif)
            
        Returns:
            Scan results as string
        """
        # Build the containers
        containers = await self.build(
            os, os_ver, upstream_org, upstream_os, upstream_os_ver, uv_version, platforms
        )
        
        results = []
        platform_list = [p for p in platforms.split(",") if p]
        
        for i, platform in enumerate(platform_list):
            container = containers[i]
            
            # Create a unique tag for this scan
            scan_tag = f"scan-{os}-{os_ver}-{platform.replace('/', '-')}"
            
            # Publish to a local registry for scanning
            # Since we can't scan Dagger containers directly, we'll export and scan
            
            # Export container to tar
            tar_path = f"/tmp/{scan_tag}.tar"
            tar_file = await container.export(tar_path)
            
            # Run Trivy on the exported tar
            scan_cmd = [
                "trivy", "image",
                "--input", tar_path,
                "--severity", severity,
                "--format", output_format,
                "--exit-code", "0",  # Don't fail, capture output
            ]
            
            if ignore_unfixed:
                scan_cmd.append("--ignore-unfixed")
            
            # Use Trivy container to scan
            trivy_result = await (
                dag.container()
                .from_("aquasec/trivy:latest")
                .with_mounted_file(tar_path, tar_file)
                .with_exec(scan_cmd)
                .stdout()
            )
            
            results.append(f"\n=== Scan results for {os}:{os_ver} on {platform} ===\n{trivy_result}")
        
        # Combine all results
        combined_results = "\n".join(results)
        
        # If exit_code is set and vulnerabilities found, we should indicate this
        if exit_code > 0 and "Total:" in combined_results and not "Total: 0" in combined_results:
            combined_results += f"\n\nWARNING: Vulnerabilities found. In CI/CD, this would exit with code {exit_code}"
        
        return combined_results

    @function
    async def build_and_export_scan_results(
        self,
        os: str,
        os_ver: str,
        upstream_org: Optional[str] = None,
        upstream_os: Optional[str] = None,
        upstream_os_ver: Optional[str] = None,
        uv_version: str = "latest",
        platforms: str = "linux/amd64",
        severity: str = "HIGH,CRITICAL",
        ignore_unfixed: bool = True,
    ) -> dagger.Directory:
        """
        Build images and export Trivy scan results as SARIF files.
        
        Returns:
            Directory containing SARIF files for each platform
        """
        # Build the containers
        containers = await self.build(
            os, os_ver, upstream_org, upstream_os, upstream_os_ver, uv_version, platforms
        )
        
        # Create output directory
        output_dir = dag.directory()
        platform_list = [p for p in platforms.split(",") if p]
        
        for i, platform in enumerate(platform_list):
            container = containers[i]
            
            # Create a unique tag for this scan
            platform_safe = platform.replace('/', '-')
            scan_tag = f"{os}-{os_ver}-{platform_safe}"
            
            # Export container to tar
            tar_path = f"/tmp/{scan_tag}.tar"
            tar_file = await container.export(tar_path)
            
            # Output file path
            sarif_filename = f"trivy-{scan_tag}.sarif"
            sarif_path = f"/output/{sarif_filename}"
            
            # Run Trivy on the exported tar
            scan_cmd = [
                "trivy", "image",
                "--input", tar_path,
                "--severity", severity,
                "--format", "sarif",
                "--output", sarif_path,
                "--exit-code", "0",
            ]
            
            if ignore_unfixed:
                scan_cmd.append("--ignore-unfixed")
            
            # Use Trivy container to scan and generate SARIF
            scan_container = await (
                dag.container()
                .from_("aquasec/trivy:latest")
                .with_mounted_file(tar_path, tar_file)
                .with_exec(["mkdir", "-p", "/output"])
                .with_exec(scan_cmd)
            )
            
            # Get the SARIF file
            sarif_file = await scan_container.file(sarif_path)
            
            # Add to output directory
            output_dir = output_dir.with_file(sarif_filename, sarif_file)
            
            # Also generate a summary
            summary_cmd = [
                "trivy", "image",
                "--input", tar_path,
                "--severity", severity,
                "--format", "table",
                "--exit-code", "0",
            ]
            
            if ignore_unfixed:
                summary_cmd.append("--ignore-unfixed")
                
            summary_container = await (
                dag.container()
                .from_("aquasec/trivy:latest")
                .with_mounted_file(tar_path, tar_file)
                .with_exec(summary_cmd)
            )
            
            summary = await summary_container.stdout()
            summary_file = await dag.file(f"summary-{scan_tag}.txt", contents=summary)
            output_dir = output_dir.with_file(f"summary-{scan_tag}.txt", summary_file)
        
        return output_dir