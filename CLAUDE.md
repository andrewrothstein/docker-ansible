# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Building Docker Images Locally
```bash
# Build using Taskfile (recommended)
task build os=ubuntu os_ver=noble platforms=linux/amd64,linux/arm64

# Build using Dagger directly
dagger call build --os=ubuntu --os-ver=noble --platforms=linux/amd64,linux/arm64

# Common OS/version combinations:
# Ubuntu: jammy, noble
# Debian: bullseye, bookworm
# Alpine: 3.20, 3.21
# Fedora: 41, 42
# RockyLinux: 9
# Arch Linux: latest
# RedHat Universal Base Image: 9, 10
```

### Publishing Images
```bash
# Publish using Taskfile (requires environment variables)
task publish os=ubuntu os_ver=noble

# Required environment variables:
# DOCKERHUB_USERNAME, DOCKERHUB_PASSWORD
# GITHUB_ACTOR, GITHUB_TOKEN
```

### Development Tasks
```bash
# View available platforms/OS combinations
cat platform-matrix-v1.json

# Test Dagger functions locally
dagger functions

# Check Python dependencies
uv pip list
```

### Vulnerability Scanning
```bash
# Scan published GHCR images locally with Trivy
docker run --rm aquasec/trivy:latest image ghcr.io/andrewrothstein/docker-ansible:latest-ubuntu.noble

# View scan results in GitHub
# Go to Security > Code scanning alerts after workflows run
```

**Note**: The `publish.yml` workflow automatically scans all published GHCR images using Trivy and uploads results to the GitHub Security tab. Scans run on every publish (daily schedule and push to develop).

## High-Level Architecture

### Project Purpose
This project creates multi-platform Docker container images with Ansible pre-installed using `uv` (a fast Python package manager). Images are published to both Docker Hub and GitHub Container Registry.

### Core Components

1. **Dagger Pipeline (`src/docker_ansible/main.py`)**
   - Main orchestration using Dagger's Python SDK
   - `DockerAnsible` class defines the build pipeline
   - Key methods:
     - `build_one()`: Builds a single OS/platform combination
     - `build()`: Builds for all platforms (parallel)
     - `publish()`: Pushes to registries
     - `test_role()`: Tests Ansible roles and publishes results to registry
     - `test_role_one()`: Tests a role on a single platform
   - Embeds Ansible configuration and inventory files into images
   - Uses uv for efficient Ansible installation

2. **CI/CD Workflows (`.github/workflows/`)**
   - `build.yml`: PR validation builds
   - `publish.yml`: Daily and push-to-develop publishing with vulnerability scanning
   - Both use Dagger Cloud for optimized caching
   - Matrix builds from `platform-matrix-v1.json`
   - Vulnerability reports uploaded to GitHub Security tab via SARIF

3. **Build System Design**
   - Multi-architecture support via Docker buildx
   - Parallel builds for efficiency
   - Each image includes:
     - Ansible installed via uv tool
     - Pre-configured ansible.cfg
     - Local inventory setup
     - PATH configuration via /etc/profile.d

4. **Image Tagging Strategy**
   - Format: `{version}-{os}.{os_ver}`
   - Example: `0.0.0-ubuntu.noble`
   - Also creates `latest-{os}.{os_ver}` tags

### Key Design Decisions

- **uv over pip**: Faster, more reliable Python package management
- **Dagger over traditional CI**: Portable, testable CI/CD pipelines
- **Multi-registry publishing**: Redundancy and accessibility
- **Embedded configuration**: Images are ready-to-use without additional setup

## Testing Ansible Roles

The `test_role` function tests Ansible roles using pre-built docker-ansible base images and optionally publishes the tested containers to a registry.

**Key features:**
- Tests roles against docker-ansible base images
- Optionally publishes tested containers to specified registry
- Follows the same naming convention as docker-ansible images: `{version}-{os}.{os_ver}`
- Supports multi-platform testing
- Publishing is optional - omit registry parameters for local testing only

Expected role structure:
- `test.yml` - Test playbook at the repository root
- `meta/requirements.yml` - Galaxy dependencies (optional)
- `test-requirements.yml` - Additional test dependencies (optional)
- `test-inventory.ini` - Custom inventory for tests (optional)
- Standard Ansible role directories: `tasks/`, `vars/`, `defaults/`, etc.

### Testing Your Ansible Role

When you're in your own Ansible role repository and want to test it:

```bash
# From your ansible role directory (e.g., ansible-sudoers)
cd ~/git/github.com/andrewrothstein/ansible-sudoers

# Test locally without publishing (defaults to current directory)
dagger call --mod github.com/andrewrothstein/docker-ansible test-role \
  --os=ubuntu \
  --os-ver=noble

# Test on Alpine (role-name defaults to "test-role" for container name)
dagger call --mod github.com/andrewrothstein/docker-ansible test-role \
  --os=alpine \
  --os-ver=3.22

# Test on multiple platforms
dagger call --mod github.com/andrewrothstein/docker-ansible test-role \
  --os=ubuntu \
  --os-ver=noble \
  --platforms=linux/amd64,linux/arm64

# Test and publish to GHCR with custom role name
dagger call --mod github.com/andrewrothstein/docker-ansible test-role \
  --os=ubuntu \
  --os-ver=noble \
  --role-name=ansible-sudoers \
  --target-registry=ghcr.io \
  --target-org=$GITHUB_REPOSITORY_OWNER \
  --target-username=$GITHUB_ACTOR \
  --target-password=env:GITHUB_TOKEN
```

### Local Testing (from this repository)
```bash
# Test a role locally without publishing
dagger call test-role \
  --role-name=my-role \
  --role-dir=. \
  --os=ubuntu \
  --os-ver=noble

# Test and publish to GHCR
dagger call test-role \
  --role-name=my-role \
  --role-dir=. \
  --os=ubuntu \
  --os-ver=noble \
  --target-registry=ghcr.io \
  --target-org=$GITHUB_REPOSITORY_OWNER \
  --target-username=$GITHUB_ACTOR \
  --target-password=env:GITHUB_TOKEN

# Test on multiple platforms without publishing
dagger call test-role \
  --role-name=my-role \
  --role-dir=. \
  --os=ubuntu \
  --os-ver=noble \
  --platforms=linux/amd64,linux/arm64

# Use specific docker-ansible base image version
dagger call test-role \
  --role-name=my-role \
  --role-dir=. \
  --os=ubuntu \
  --os-ver=noble \
  --upstream-semver=1.2.3

# Publish with specific version tag
dagger call test-role \
  --role-name=ansible-sudoers \
  --role-dir=. \
  --os=ubuntu \
  --os-ver=noble \
  --target-registry=ghcr.io \
  --target-org=$GITHUB_REPOSITORY_OWNER \
  --target-username=$GITHUB_ACTOR \
  --target-password=env:GITHUB_TOKEN \
  --target-semver=v1.0.0
```

### Advanced Examples

These examples show different ways to reference the docker-ansible module:

```bash
# Test locally without publishing (from default branch)
dagger call --mod github.com/andrewrothstein/docker-ansible test-role \
  --os=ubuntu \
  --os-ver=noble

# Test and publish to GHCR (from specific branch)
dagger call --mod github.com/andrewrothstein/docker-ansible@develop test-role \
  --os=ubuntu \
  --os-ver=noble \
  --role-name=my-role \
  --target-registry=ghcr.io \
  --target-org=$GITHUB_REPOSITORY_OWNER \
  --target-username=$GITHUB_ACTOR \
  --target-password=env:GITHUB_TOKEN

# Test without publishing (from specific tag)
dagger call --mod github.com/andrewrothstein/docker-ansible@v1.0.0 test-role \
  --os=ubuntu \
  --os-ver=noble

# Test and publish (from specific commit SHA)
dagger call --mod github.com/andrewrothstein/docker-ansible@a1b2c3d4 test-role \
  --os=ubuntu \
  --os-ver=noble \
  --role-name=my-role \
  --target-registry=ghcr.io \
  --target-org=$GITHUB_REPOSITORY_OWNER \
  --target-username=$GITHUB_ACTOR \
  --target-password=env:GITHUB_TOKEN
```

### GitHub Actions Integration

For testing with publishing, use the reusable workflow:

```yaml
name: Test Ansible Role
on: [push, pull_request]

jobs:
  test:
    uses: andrewrothstein/docker-ansible/.github/workflows/dagger-ansible-test-role.yml@develop
    secrets: inherit
```

Or create your own workflow for custom testing:

```yaml
name: Test Ansible Role
on: [push, pull_request]

jobs:
  matrix:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.read-matrix.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - id: read-matrix
        run: echo "matrix=$(cat platform-matrix-v1.json | jq -c .)" >> $GITHUB_OUTPUT

  test:
    needs: matrix
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write  # Required if publishing to GHCR
    strategy:
      matrix:
        include: ${{ fromJson(needs.matrix.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - uses: dagger/dagger-for-github@v8
        env:
          GITHUB_TOKEN: ${{ github.token }}
        with:
          cloud-token: ${{ secrets.DAGGER_CLOUD_TOKEN }}
          args: >-
            call --mod github.com/andrewrothstein/docker-ansible@develop
            test-role
            --role-name=${{ github.event.repository.name }}
            --role-dir=.
            --os=${{ matrix.OS }}
            --os-ver=${{ matrix.OS_VER }}
            --platforms=${{ matrix.PLATFORMS }}
            --target-registry=ghcr.io
            --target-org=${{ github.repository_owner }}
            --target-username=${{ github.actor }}
            --target-password=env:GITHUB_TOKEN
            --target-semver=${{ github.sha }}
```

Note: The `--mod` parameter specifies the remote module reference:
- `github.com/{owner}/{repo}` - uses the default branch
- `github.com/{owner}/{repo}@{ref}` - where ref can be a branch, tag, or commit SHA

This enables matrix testing across all supported OS/platform combinations using the same `platform-matrix-v1.json` format.

### Security Scanning and Tagging Strategy

The reusable workflow uses a three-step process to ensure only secure images are published:

1. **Build & Test**: Builds the role container and publishes with SHA tag (`0.0.0-{os}.{os_ver}.{sha}`)
2. **Security Scan**: Scans the SHA-tagged image with Trivy, failing if vulnerabilities are found
3. **Final Publish**: Only if the scan passes, publishes to clean semver tags:
   - `0.0.0-{os}.{os_ver}` - Version-specific tag
   - `latest-{os}.{os_ver}` - Latest tag for easy consumption

This approach ensures:
- Every build is traceable via its SHA tag
- Only secure images get the clean version tags
- The SHA-tagged images serve as an audit trail
- Re-tagging is fast since layers are already in the registry

**Note**: SHA-tagged images (e.g., `0.0.0-ubuntu.noble.a1b2c3d4`) can be retained for audit purposes or cleaned up periodically using your container registry's retention policies.
