# GitHub Actions Workflows

This directory contains GitHub Actions workflows for building and publishing container images to GitHub Container Registry (ghcr.io).

## Workflows

### build-containers.yml

**Trigger:** Push to `main` branch  
**Purpose:** Builds and publishes all container images with `latest` and SHA tags  
**Images:**

- `ghcr.io/<owner>/<repo>:latest` - Main API container
- `ghcr.io/<owner>/<repo>-webui:latest` - Web UI container
- `ghcr.io/<owner>/<repo>-devportal:latest` - DevPortal container

### build-pr.yml

**Trigger:** Pull requests to `main` branch  
**Purpose:** Builds all container images (without publishing) to verify they build correctly  
**Images:** Same as above but not pushed to registry

### build-release.yml

**Trigger:** Git tags matching `v*.*.*` pattern (e.g., `v1.0.0`)  
**Purpose:** Builds and publishes release versions with semantic versioning tags  
**Images:** Same containers as above but tagged with:

- Full version (e.g., `v1.2.3`)
- Major.minor version (e.g., `v1.2`)
- Major version (e.g., `v1`)
- SHA commit hash

## Container Images

### Main API (`Dockerfile`)

The core NGINX Declarative API service built with Python and Alpine Linux.

### Web UI (`webui/Dockerfile`)

The web interface for managing the NGINX Declarative API, built with Node.js and served by NGINX.

### DevPortal (`contrib/devportal/redocly/Dockerfile`)

The Redocly-based developer portal for API documentation.

## Usage

### Pushing to Main Branch

```bash
git push origin main
```

This triggers `build-containers.yml` and publishes images with the `latest` tag.

### Creating a Release

```bash
git tag v1.0.0
git push origin v1.0.0
```

This triggers `build-release.yml` and publishes versioned images.

### Pull Requests

When creating a pull request to `main`, the `build-pr.yml` workflow automatically runs to verify all containers build successfully.

## Permissions

The workflows require the following GitHub token permissions:

- `contents: read` - To checkout the repository
- `packages: write` - To publish to GitHub Container Registry

These are automatically provided by the `GITHUB_TOKEN` secret.

## Registry Access

Published images are available at:

```
ghcr.io/<owner>/<repo>
ghcr.io/<owner>/<repo>-webui
ghcr.io/<owner>/<repo>-devportal
```

To pull images:

```bash
docker pull ghcr.io/<owner>/<repo>:latest
docker pull ghcr.io/<owner>/<repo>-webui:latest
docker pull ghcr.io/<owner>/<repo>-devportal:latest
```

For versioned releases:

```bash
docker pull ghcr.io/<owner>/<repo>:v1.0.0
docker pull ghcr.io/<owner>/<repo>-webui:v1.0.0
docker pull ghcr.io/<owner>/<repo>-devportal:v1.0.0
```
