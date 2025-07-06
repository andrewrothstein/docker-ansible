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
   - Embeds Ansible configuration and inventory files into images
   - Uses uv for efficient Ansible installation

2. **CI/CD Workflows (`.github/workflows/`)**
   - `build.yml`: PR validation builds
   - `publish.yml`: Daily and push-to-develop publishing
   - Both use Dagger Cloud for optimized caching
   - Matrix builds from `platform-matrix-v1.json`

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
   - Example: `v0.0.0-ubuntu.noble`
   - Also creates `latest-{os}.{os_ver}` tags

### Key Design Decisions

- **uv over pip**: Faster, more reliable Python package management
- **Dagger over traditional CI**: Portable, testable CI/CD pipelines
- **Multi-registry publishing**: Redundancy and accessibility
- **Embedded configuration**: Images are ready-to-use without additional setup