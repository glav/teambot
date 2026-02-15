<!-- markdownlint-disable-file -->
# Release Changes: TeamBot Distribution & Installation

**Related Plan**: 20260213-run-directly-distribution-plan.instructions.md
**Implementation Date**: 2026-02-13

## Summary

Enable zero-friction installation and evaluation of TeamBot through PyPI publishing, uvx ephemeral execution, devcontainer features, and Docker images with cross-platform support.

## Changes

### Added

* `pyproject.toml` - Added `[build-system]` section with hatchling backend
* `pyproject.toml` - Added `[project.urls]` section with Homepage, Documentation, Repository, Issues
* `pyproject.toml` - Added `[tool.hatch.build.targets.wheel]` configuration for package building
* `src/teambot/cli.py` - Added `check_copilot_cli()` function for Copilot CLI detection at startup
* `src/teambot/cli.py` - Added `COPILOT_CLI_INSTALL_URL` constant
* `.github/workflows/publish.yml` - New PyPI publish workflow triggered on release
* `features/teambot/devcontainer-feature.json` - Devcontainer feature definition
* `features/teambot/install.sh` - Feature installation script
* `features/teambot/README.md` - Feature documentation
* `docker/Dockerfile` - Docker image for non-Python environments
* `docker/.dockerignore` - Docker build context exclusions
* `.github/workflows/containers.yml` - Container and feature publish workflow
* `docs/guides/installation.md` - Comprehensive installation guide for all 6 personas
* `tests/test_distribution.py` - New test file for distribution and Copilot CLI detection

### Modified

* `pyproject.toml` - Changed package name from "teambot" to "copilot-teambot"
* `pyproject.toml` - Updated version to 0.2.0
* `pyproject.toml` - Added license, authors, keywords, classifiers metadata for PyPI
* `src/teambot/cli.py` - Added shutil import for CLI detection
* `src/teambot/cli.py` - Integrated Copilot CLI check into main() for run command
* `.github/workflows/ci.yml` - Added test matrix with Windows/macOS/Ubuntu runners
* `.github/workflows/ci.yml` - Added Python version matrix (3.10, 3.11, 3.12)
* `README.md` - Added comprehensive installation section with all methods
* `README.md` - Added PyPI badge and updated prerequisites
* `README.md` - Updated Quick Start to use installed command
* `tests/test_e2e.py` - Updated version assertion to match 0.2.0

### Removed

* None

## Release Summary

**Total Files Affected**: 15

### Files Created (9)

* `.github/workflows/publish.yml` - PyPI publish workflow with trusted publishing
* `.github/workflows/containers.yml` - Docker and devcontainer feature publishing
* `features/teambot/devcontainer-feature.json` - Devcontainer feature definition
* `features/teambot/install.sh` - Feature installation script
* `features/teambot/README.md` - Feature documentation
* `docker/Dockerfile` - Docker image for non-Python environments
* `docker/.dockerignore` - Docker build context exclusions
* `docs/guides/installation.md` - Comprehensive installation guide
* `tests/test_distribution.py` - Distribution and CLI detection tests

### Files Modified (6)

* `pyproject.toml` - PyPI metadata, build system, version update
* `src/teambot/cli.py` - Copilot CLI detection function
* `.github/workflows/ci.yml` - Cross-platform and Python version matrix
* `README.md` - Installation section and badges

### Files Removed (0)

* None

### Dependencies & Infrastructure

* **New Dependencies**: hatchling>=1.26 (build backend)
* **Updated Dependencies**: None
* **Infrastructure Changes**: 
  * PyPI publish workflow with OIDC trusted publishing
  * Docker image on ghcr.io
  * Devcontainer feature on ghcr.io
* **Configuration Updates**: 
  * Package name changed from "teambot" to "copilot-teambot"
  * Version bumped to 0.2.0

### Deployment Notes

1. Configure PyPI trusted publisher in PyPI project settings
2. Create `pypi` environment in GitHub repository settings
3. Add `PYPI_API_TOKEN` secret (or use OIDC)
4. First release will trigger all publish workflows

