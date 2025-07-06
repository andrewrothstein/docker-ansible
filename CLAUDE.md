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
# Alpine: 3.20.x, 3.21.x
# Fedora: 40, 41
# Rocky: 8, 9
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
     - `test_role()`: Tests Ansible roles using pre-built images
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

The `test_role` function tests Ansible roles using the pre-built docker-ansible base images from ghcr.io.

Expected role structure:
- `test.yml` - Test playbook at the repository root
- `meta/requirements.yml` - Galaxy dependencies (optional)
- `test-requirements.yml` - Additional test dependencies (optional)
- `test-inventory.ini` - Custom inventory for tests (optional)
- Standard Ansible role directories: `tasks/`, `vars/`, `defaults/`, etc.

### Local Testing (from this repository)
```bash
# Test a role on Ubuntu Noble (uses version 0.0.0 by default)
dagger call test-role --role-dir=. --os=ubuntu --os-ver=noble

# Test on multiple platforms
dagger call test-role --role-dir=. --os=ubuntu --os-ver=noble --platforms=linux/amd64,linux/arm64

# Use latest docker-ansible version
dagger call test-role --role-dir=. --os=ubuntu --os-ver=noble --target-image-semver=latest

# Use specific docker-ansible version
dagger call test-role --role-dir=. --os=ubuntu --os-ver=noble --target-image-semver=1.2.3
```

### Remote Usage (from other repositories)

When using this module from another repository, you need to specify the module reference:

```bash
# Use from default branch
dagger call --mod github.com/andrewrothstein/docker-ansible test-role --role-dir=. --os=ubuntu --os-ver=noble

# Use from specific branch
dagger call --mod github.com/andrewrothstein/docker-ansible@develop test-role --role-dir=. --os=ubuntu --os-ver=noble

# Use from specific tag
dagger call --mod github.com/andrewrothstein/docker-ansible@v1.0.0 test-role --role-dir=. --os=ubuntu --os-ver=noble

# Use from specific commit
dagger call --mod github.com/andrewrothstein/docker-ansible@abc123def test-role --role-dir=. --os=ubuntu --os-ver=noble
```

### GitHub Actions Integration

Create `.github/workflows/test.yml` in your Ansible role repository:

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
    strategy:
      matrix:
        include: ${{ fromJson(needs.matrix.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - uses: dagger/dagger-for-github@v8
        with:
          cloud-token: ${{ secrets.DAGGER_CLOUD_TOKEN }}
          args: >-
            call --mod github.com/andrewrothstein/docker-ansible@develop
            test-role
            --role-dir=.
            --os=${{ matrix.OS }}
            --os-ver=${{ matrix.OS_VER }}
            --platforms=${{ matrix.PLATFORMS }}
```

Note: The `--mod` parameter specifies the remote module reference:
- `github.com/{owner}/{repo}` - uses the default branch
- `github.com/{owner}/{repo}@{ref}` - where ref can be a branch, tag, or commit SHA

This enables matrix testing across all supported OS/platform combinations using the same `platform-matrix-v1.json` format.