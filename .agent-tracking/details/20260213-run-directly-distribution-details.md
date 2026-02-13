<!-- markdownlint-disable-file -->
# Task Details: TeamBot Distribution & Installation

## Research Reference

**Source Research**: .teambot/run-directly-downloads/artifacts/research.md
**Feature Spec**: .teambot/run-directly-downloads/artifacts/feature_spec.md
**Test Strategy**: .teambot/run-directly-downloads/artifacts/test_strategy.md

## Phase 1: PyPI Package Configuration

### Task 1.1: Update pyproject.toml with PyPI metadata

Update the `[project]` section in `pyproject.toml` to include all required PyPI publishing metadata.

* **Files**:
  * `pyproject.toml` - Add package name, classifiers, keywords, URLs, license, authors
* **Changes Required**:
  ```toml
  [project]
  name = "copilot-teambot"  # Changed from "teambot"
  version = "0.2.0"
  description = "CLI wrapper for GitHub Copilot CLI enabling autonomous AI agent teams"
  readme = "README.md"
  requires-python = ">=3.10"
  license = "MIT"
  authors = [
      { name = "TeamBot Contributors" }
  ]
  keywords = ["copilot", "ai", "agent", "automation", "cli", "github"]
  classifiers = [
      "Development Status :: 4 - Beta",
      "Environment :: Console",
      "Intended Audience :: Developers",
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
      "Programming Language :: Python :: 3",
      "Programming Language :: Python :: 3.10",
      "Programming Language :: Python :: 3.11",
      "Programming Language :: Python :: 3.12",
      "Topic :: Software Development :: Code Generators",
  ]
  
  [project.urls]
  Homepage = "https://github.com/teambot-ai/teambot"
  Documentation = "https://github.com/teambot-ai/teambot/tree/main/docs"
  Repository = "https://github.com/teambot-ai/teambot"
  Issues = "https://github.com/teambot-ai/teambot/issues"
  ```
* **Success**:
  * All required PyPI fields present
  * `uv build` succeeds
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/research.md (Lines 90-134) - PyPI metadata example
* **Dependencies**:
  * None

### Task 1.2: Add hatchling build system configuration

Add `[build-system]` section to enable PyPI-compatible wheel building.

* **Files**:
  * `pyproject.toml` - Add build-system section
* **Changes Required**:
  ```toml
  [build-system]
  requires = ["hatchling>=1.26"]
  build-backend = "hatchling.build"
  
  [tool.hatch.build.targets.wheel]
  packages = ["src/teambot"]
  ```
* **Success**:
  * `uv build` produces wheel file
  * Wheel contains correct entry point
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/research.md (Lines 96-101) - Build system config
* **Dependencies**:
  * Task 1.1 completion

### Task 1.3: Implement Copilot CLI detection in cli.py

Add startup check for Copilot CLI availability with helpful error message.

* **Files**:
  * `src/teambot/cli.py` - Add `check_copilot_cli()` function and call at startup
* **Implementation**:
  ```python
  import shutil
  
  COPILOT_CLI_INSTALL_URL = "https://githubnext.com/projects/copilot-cli/"
  
  def check_copilot_cli() -> bool:
      """Check if Copilot CLI is installed and accessible.
      
      Returns:
          True if Copilot CLI is available, False otherwise.
      """
      if shutil.which("copilot") is not None:
          return True
      
      # Print helpful error message
      console = Console()
      console.print(
          "[bold red]Error:[/bold red] GitHub Copilot CLI is required but not found.",
          style="red"
      )
      console.print(
          f"Install from: [link]{COPILOT_CLI_INSTALL_URL}[/link]"
      )
      return False
  ```
* **Integration Point**:
  * Call `check_copilot_cli()` early in `main()` function (before command dispatch)
  * Return exit code 1 if check fails
* **Success**:
  * Error displayed when Copilot CLI missing
  * Error includes installation URL
  * Normal operation when Copilot CLI present
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/research.md (Lines 386-414) - Windows considerations
  * .teambot/run-directly-downloads/artifacts/feature_spec.md (Lines 136-139) - UX requirements
* **Dependencies**:
  * None (can parallelize with 1.1-1.2)

## Phase 2: CI/CD Infrastructure

### Task 2.1: Create PyPI publish workflow

Create GitHub Actions workflow for automated PyPI publishing on release.

* **Files**:
  * `.github/workflows/publish.yml` - New file
* **Workflow Content**:
  ```yaml
  name: Publish to PyPI
  
  on:
    release:
      types: [published]
  
  permissions:
    id-token: write  # Required for trusted publishing
    contents: read
  
  jobs:
    build:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        
        - name: Install uv
          uses: astral-sh/setup-uv@v4
        
        - name: Build package
          run: uv build
        
        - name: Upload artifacts
          uses: actions/upload-artifact@v4
          with:
            name: dist
            path: dist/
  
    publish:
      needs: build
      runs-on: ubuntu-latest
      environment: pypi
      steps:
        - name: Download artifacts
          uses: actions/download-artifact@v4
          with:
            name: dist
            path: dist/
        
        - name: Install uv
          uses: astral-sh/setup-uv@v4
        
        - name: Publish to PyPI
          run: uv publish
          env:
            UV_PUBLISH_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
  ```
* **Success**:
  * Workflow runs on release
  * Package published to PyPI
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/research.md (Lines 546-591) - CI workflow example
* **Dependencies**:
  * Phase 1 completion
  * PyPI account with API token configured as secret

### Task 2.2: Add Windows runner to existing CI matrix

Update existing test workflow to include Windows runner.

* **Files**:
  * `.github/workflows/ci.yml` (or existing test workflow) - Add Windows to matrix
* **Changes Required**:
  ```yaml
  strategy:
    matrix:
      os: [ubuntu-latest, macos-latest, windows-latest]
      python-version: ['3.10', '3.11', '3.12']
  
  runs-on: ${{ matrix.os }}
  ```
* **Success**:
  * CI runs on Windows
  * All tests pass on Windows
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/test_strategy.md (Lines 529-534) - CI matrix config
* **Dependencies**:
  * Task 2.1

### Task 2.3: Add Python version matrix (3.10, 3.11, 3.12)

Ensure CI tests all supported Python versions.

* **Files**:
  * `.github/workflows/ci.yml` - Update Python version matrix
* **Changes Required**:
  ```yaml
  python-version: ['3.10', '3.11', '3.12']
  ```
* **Success**:
  * All Python versions tested
  * Tests pass on all versions
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/feature_spec.md (Lines 361-370) - AT-007 cross-version
* **Dependencies**:
  * Task 2.2

## Phase 3: Container Support

### Task 3.1: Create devcontainer feature

Create devcontainer feature for VS Code / GitHub Codespaces integration.

* **Files**:
  * `features/teambot/devcontainer-feature.json` - Feature definition
  * `features/teambot/install.sh` - Installation script
  * `features/teambot/README.md` - Feature documentation
* **Directory Structure**:
  ```
  features/
  └── teambot/
      ├── devcontainer-feature.json
      ├── install.sh
      └── README.md
  ```
* **Feature Definition** (`devcontainer-feature.json`):
  ```json
  {
      "id": "teambot",
      "version": "1.0.0",
      "name": "TeamBot - AI Agent Teams",
      "description": "Installs TeamBot CLI for autonomous AI agent workflows",
      "documentationURL": "https://github.com/teambot-ai/teambot",
      "options": {
          "version": {
              "type": "string",
              "default": "latest",
              "description": "TeamBot version to install"
          }
      },
      "installsAfter": [
          "ghcr.io/devcontainers/features/python"
      ],
      "containerEnv": {
          "TEAMBOT_INSTALLED": "true"
      }
  }
  ```
* **Install Script** (`install.sh`):
  ```bash
  #!/usr/bin/env bash
  set -e
  
  VERSION="${VERSION:-latest}"
  
  # Install uv if not present
  if ! command -v uv &> /dev/null; then
      curl -LsSf https://astral.sh/uv/install.sh | sh
      export PATH="$HOME/.local/bin:$PATH"
  fi
  
  # Install TeamBot
  if [ "$VERSION" = "latest" ]; then
      uv tool install copilot-teambot
  else
      uv tool install "copilot-teambot==$VERSION"
  fi
  
  # Ensure tool bin is in PATH for all shells
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> /etc/profile.d/teambot.sh
  
  echo "TeamBot installed successfully!"
  ```
* **Success**:
  * Feature builds locally
  * TeamBot available after container creation
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/research.md (Lines 205-304) - Devcontainer feature spec
* **Dependencies**:
  * Phase 2 completion (package on PyPI)

### Task 3.2: Create Dockerfile

Create Docker image for non-Python users.

* **Files**:
  * `docker/Dockerfile` - Multi-stage Dockerfile
  * `docker/.dockerignore` - Exclude unnecessary files
* **Dockerfile Content**:
  ```dockerfile
  FROM python:3.12-slim AS base
  
  # Install uv
  RUN pip install uv
  
  # Install TeamBot
  RUN uv tool install copilot-teambot
  
  # Add tool bin to PATH
  ENV PATH="/root/.local/bin:$PATH"
  
  # Create workspace
  WORKDIR /workspace
  
  # Default command
  ENTRYPOINT ["teambot"]
  CMD ["--help"]
  ```
* **Success**:
  * Docker image builds
  * `docker run --rm teambot-test --help` works
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/research.md (Lines 306-374) - Docker image spec
* **Dependencies**:
  * Task 3.1

### Task 3.3: Create container publish workflow

Create GitHub Actions workflow for publishing containers to ghcr.io.

* **Files**:
  * `.github/workflows/containers.yml` - Container build and push workflow
* **Workflow Content**:
  ```yaml
  name: Publish Containers
  
  on:
    release:
      types: [published]
    workflow_dispatch:
  
  permissions:
    contents: read
    packages: write
  
  jobs:
    docker:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        
        - name: Set up Docker Buildx
          uses: docker/setup-buildx-action@v3
        
        - name: Login to ghcr.io
          uses: docker/login-action@v3
          with:
            registry: ghcr.io
            username: ${{ github.actor }}
            password: ${{ secrets.GITHUB_TOKEN }}
        
        - name: Build and push Docker image
          uses: docker/build-push-action@v5
          with:
            context: docker
            push: true
            tags: |
              ghcr.io/${{ github.repository }}:latest
              ghcr.io/${{ github.repository }}:${{ github.ref_name }}
    
    devcontainer-feature:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        
        - name: Publish feature
          uses: devcontainers/action@v1
          with:
            publish-features: true
            base-path-to-features: features
          env:
            GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  ```
* **Success**:
  * Workflow publishes on release
  * Images available on ghcr.io
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/research.md (Lines 600-606) - Container publishing
* **Dependencies**:
  * Tasks 3.1, 3.2

## Phase 4: Documentation

### Task 4.1: Update README.md with installation section

Add comprehensive installation section with all supported methods.

* **Files**:
  * `README.md` - Add installation section near top
* **Content to Add**:
  ```markdown
  ## Installation
  
  ### Quick Start (Recommended)
  
  ```bash
  # Try without installing (requires uv)
  uvx copilot-teambot --help
  
  # Or install with pip
  pip install copilot-teambot
  ```
  
  ### Prerequisites
  
  - Python 3.10 or later
  - [GitHub Copilot CLI](https://githubnext.com/projects/copilot-cli/) installed and authenticated
  
  ### Installation Methods
  
  | Method | Command | Best For |
  |--------|---------|----------|
  | pip | `pip install copilot-teambot` | Most users |
  | uvx | `uvx copilot-teambot` | Quick evaluation |
  | pipx | `pipx install copilot-teambot` | Isolated global install |
  | Devcontainer | See [installation guide](docs/guides/installation.md) | VS Code / Codespaces |
  | Docker | `docker run ghcr.io/teambot-ai/teambot` | No Python environment |
  
  ### Windows
  
  ```powershell
  # PowerShell
  pip install copilot-teambot
  teambot --version
  ```
  ```
* **Success**:
  * Installation section appears in README
  * All methods documented with commands
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/feature_spec.md (Lines 282-290) - Communication plan
* **Dependencies**:
  * Phase 1 completion

### Task 4.2: Create installation guide in docs/guides/

Create comprehensive installation guide covering all 6 personas.

* **Files**:
  * `docs/guides/installation.md` - New detailed guide
* **Guide Structure**:
  1. Prerequisites
  2. Installation by Persona
     - Evaluator (uvx)
     - Python Developer (pip)
     - Existing Codebase Adopter (requirements.txt)
     - Devcontainer User (feature)
     - Windows Developer (pip + PowerShell)
     - Non-Python Developer (Docker)
  3. Verification
  4. Troubleshooting
  5. Upgrading
* **Success**:
  * All 6 personas have documented path
  * Commands are copy-pasteable
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/feature_spec.md (Lines 72-91) - Persona definitions
* **Dependencies**:
  * Task 4.1

## Phase 5: Testing & Validation

### Task 5.1: Add distribution and installation tests

Create tests for package metadata and Copilot CLI detection.

* **Files**:
  * `tests/test_distribution.py` - New test file
* **Test Content**:
  ```python
  """Tests for package distribution and installation."""
  
  import tomllib
  from pathlib import Path
  from unittest.mock import patch
  
  import pytest
  
  
  class TestPackageMetadata:
      """Tests for PyPI package configuration."""
      
      def test_pyproject_has_required_fields(self):
          """Verify pyproject.toml has all required PyPI fields."""
          with open("pyproject.toml", "rb") as f:
              config = tomllib.load(f)
          
          assert config["project"]["name"] == "copilot-teambot"
          assert "version" in config["project"]
          assert "description" in config["project"]
          assert config["project"]["requires-python"] == ">=3.10"
      
      def test_entry_point_defined(self):
          """Verify CLI entry point is defined."""
          with open("pyproject.toml", "rb") as f:
              config = tomllib.load(f)
          
          scripts = config["project"]["scripts"]
          assert "teambot" in scripts
          assert scripts["teambot"] == "teambot.cli:main"
  
  
  class TestCopilotCLIDetection:
      """Tests for Copilot CLI detection (FR-006)."""
      
      def test_copilot_cli_present_returns_true(self):
          """When Copilot CLI is installed, check returns True."""
          with patch("shutil.which", return_value="/usr/local/bin/copilot"):
              from teambot.cli import check_copilot_cli
              
              result = check_copilot_cli()
              assert result is True
      
      def test_copilot_cli_missing_returns_false(self, capsys):
          """When Copilot CLI is missing, check returns False with error."""
          with patch("shutil.which", return_value=None):
              from teambot.cli import check_copilot_cli
              
              result = check_copilot_cli()
              
              assert result is False
              captured = capsys.readouterr()
              output = captured.out + captured.err
              assert "Copilot CLI" in output or "copilot" in output.lower()
              assert "githubnext.com" in output
  ```
* **Success**:
  * Tests pass
  * Copilot CLI detection tested
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/test_strategy.md (Lines 398-440) - Test patterns
  * .teambot/run-directly-downloads/artifacts/research.md (Lines 478-532) - Test examples
* **Dependencies**:
  * Task 1.3 (Copilot CLI detection implementation)

### Task 5.2: Validate test coverage and acceptance scenarios

Run full test suite and verify coverage targets.

* **Validation Commands**:
  ```bash
  # Run all tests
  uv run pytest
  
  # Run with coverage
  uv run pytest --cov=src/teambot --cov-report=term-missing
  
  # Run acceptance tests
  uv run pytest -m acceptance
  ```
* **Success Criteria**:
  * All tests pass
  * Coverage ≥ 80% for new code
  * No regressions in existing tests
* **Research References**:
  * .teambot/run-directly-downloads/artifacts/test_strategy.md (Lines 266-288) - Coverage targets
* **Dependencies**:
  * Task 5.1

## Dependencies

* uv >= 0.4.0 (build and publish)
* hatchling >= 1.26 (build backend)
* pytest >= 7.4 (testing)
* pytest-cov >= 4.1 (coverage)
* GitHub Actions runners
* PyPI account (trusted publishing)
* ghcr.io access (container publishing)

## Success Criteria

* `pip install copilot-teambot` works on Python 3.10+
* `uvx copilot-teambot --help` responds in < 30 seconds
* Devcontainer feature installs in < 60 seconds
* Docker image builds and runs
* All CI matrix jobs pass (3 platforms × 3 Python versions)
* Windows compatibility verified
* All 6 personas documented
* Test coverage ≥ 80% for new code
