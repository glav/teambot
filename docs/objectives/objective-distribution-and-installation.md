## Objective

- Define and implement flexible installation and distribution options for TeamBot, enabling seamless adoption across diverse development environments including new projects, existing codebases, devcontainers, WSL, and standard Linux/Windows setups.

**Goal**:

- Make TeamBot easy to install and use regardless of the user's development environment
- Support zero-dependency quick-start scenarios (e.g., `uvx teambot`)
- Enable devcontainer-based usage without requiring TeamBot source code in the repository
- Provide clear pathways for different user personas: new project creators, existing codebase adopters, devcontainer users
- Support both ephemeral (try it out) and persistent (project-integrated) installation models
- **Support Windows environments** natively (not just WSL)
- **Support non-Python environments** where users don't have or want Python installed locally (via Docker, devcontainers, or pre-built binaries)

**Problem Statement**:

- Currently, TeamBot requires cloning the repository and running `uv sync` to use
- Users wanting to use TeamBot on existing projects must either copy files or manage it as a separate concern
- Devcontainer users have no streamlined way to include TeamBot as a feature or pre-installed tool
- There is no pip/uvx installable package for quick adoption
- Windows and WSL users lack clear installation guidance

**Success Criteria**:

- [ ] Document all viable distribution options with pros/cons
- [ ] Select primary distribution method(s) for initial implementation
- [ ] Define acceptance criteria for each selected option
- [ ] Create implementation plan for chosen approaches
- [ ] `pip install copilot-teambot` completes successfully on Python 3.10+ environments
- [ ] `uvx copilot-teambot --help` works without prior installation
- [ ] Devcontainer feature installs and initializes TeamBot in under 60 seconds

**Non-Goals** (explicitly out of scope for initial implementation):

- Homebrew tap / Homebrew formula
- conda-forge package
- Snap or Flatpak packages
- Native installers (.msi, .pkg, .deb, .rpm)

> **Note**: Chocolatey and standalone binaries may be considered in future phases if Windows adoption warrants it.

---

## Technical Context

**Target Codebase**:

- TeamBot packaging, distribution, and documentation

**Primary Language/Framework**:

- Python (packaging: pyproject.toml, uv, pip)

**Testing Preference**:

- Installation methods should be testable via CI/CD where possible

**Key Constraints**:

- Must maintain compatibility with Python 3.10+
- Must work with the GitHub Copilot SDK dependency
- Cannot include Copilot CLI itself (user must have it installed separately)
- Windows support must work on Windows 10/11 with PowerShell or CMD
- Non-Python environments must have a viable path (Docker or devcontainer-based)

---

## Distribution Options Analysis

### Option 1: PyPI Package (pip install teambot)

**Description**: Publish TeamBot as a standard Python package to PyPI.

**Installation**:
```bash
pip install copilot-teambot
teambot init
teambot run
```

**Pros**:
- Standard Python distribution method, familiar to all Python users
- Works everywhere pip works (WSL, Linux, Windows, macOS)
- Version management via pip
- Easy upgrades: `pip install --upgrade copilot-teambot`

**Cons**:
- Requires PyPI account and release process
- Must manage versioning and releases

**Effort**: Medium

---

### Option 2: uvx (uv tool run)

**Description**: Enable running TeamBot directly via `uvx` without explicit installation.

**Installation/Usage**:
```bash
# Run directly (downloads and caches automatically)
uvx copilot-teambot init
uvx copilot-teambot run

# Or install as a tool
uv tool install copilot-teambot
teambot run
```

**Pros**:
- Zero-installation quick start
- Automatic dependency resolution
- Always runs latest version (or pinned version)
- Perfect for trying TeamBot without commitment
- Works with uv's fast dependency resolution

**Cons**:
- Requires uv to be installed
- Less familiar to users not using uv ecosystem
- Requires publishing to PyPI (same as Option 1)

**Effort**: Low (once PyPI package exists)

---

### Option 3: Devcontainer Feature

**Description**: Create a devcontainer feature that installs TeamBot into any devcontainer.

**Usage in devcontainer.json**:
```json
{
  "features": {
    "ghcr.io/your-org/features/teambot:1": {
      "version": "latest"
    }
  }
}
```

> **Note**: `your-org` is a placeholder. Replace with actual GitHub org/user (e.g., the repository owner) when implementing.

**Constraints**:
- Feature must validate Python 3.10+ is available or install it
- Feature should document Python version requirement clearly in feature metadata

**Pros**:
- One-line integration for any devcontainer-based project
- No TeamBot source code needed in the repository
- Automatic installation when container builds
- Can include Copilot CLI as optional bundled feature
- Consistent environment across team members

**Cons**:
- Requires creating and hosting a devcontainer feature
- Feature versioning and maintenance overhead
- Users need to understand devcontainer features

**Effort**: Medium-High

---

### Option 4: Devcontainer Template

**Description**: Create a devcontainer template that includes TeamBot pre-configured.

**Usage**:
```bash
# Create new project with TeamBot devcontainer
devcontainer templates apply ghcr.io/your-org/templates/teambot-python

# Or add to existing project
cp -r .devcontainer-teambot .devcontainer
```

**Pros**:
- Complete environment setup including TeamBot
- Can bundle recommended extensions, settings, Copilot CLI
- Great for new projects starting from scratch
- Reproducible development environment

**Cons**:
- Template maintenance as base images evolve
- May conflict with existing devcontainer setup
- Less flexible than a feature (harder to add to existing devcontainers)

**Effort**: Medium

---

### Option 5: Docker Image

**Description**: Publish a Docker image with TeamBot pre-installed.

**Usage**:
```bash
# Pull and run interactively
docker run -it -v $(pwd):/workspace ghcr.io/your-org/teambot:latest

# Use as devcontainer base image
# In devcontainer.json:
{
  "image": "ghcr.io/your-org/teambot:latest"
}
```

**Pros**:
- Complete isolated environment
- Can bundle all dependencies including Copilot CLI
- Works on any system with Docker
- Consistent environment guaranteed

**Cons**:
- Larger download than pip install
- Docker overhead
- Volume mounting complexity for workspace access
- Authentication for Copilot needs to be handled

**Effort**: Medium

---

### Option 6: GitHub Codespaces Prebuilds

**Description**: Provide a Codespaces-optimized setup with prebuilds for instant start.

**Usage**:
- Click "Open in Codespaces" badge on any TeamBot-enabled repo
- TeamBot already installed and ready

**Pros**:
- Zero local setup required
- Instant development environment
- Prebuilds eliminate container startup time
- Perfect for demos and quick contributions

**Cons**:
- Requires Codespaces access (paid for private repos)
- Only works within GitHub ecosystem
- Not applicable for local development

**Effort**: Low (configuration only)

---

### Option 7: Install Script (curl | bash pattern)

**Description**: Provide an install script for quick setup.

**Usage**:
```bash
curl -sSL https://raw.githubusercontent.com/your-org/teambot/main/install.sh | bash
```

**Pros**:
- Single command installation
- Can handle all setup steps (uv, dependencies, PATH)
- Familiar pattern for CLI tools

**Cons**:
- Security concerns with curl|bash pattern
- OS-specific script maintenance
- Less transparent than package managers

**Security Mitigations** (if implemented):
- Provide SHA256 checksums for script verification
- Support `curl | bash -s -- --verify` flag to check signature before execution
- Host script on HTTPS with pinned certificate
- Recommend users inspect script before execution: `curl -sSL <url> | less`

**Effort**: Low-Medium

---

### Option 8: GitHub CLI Extension

**Description**: Distribute as a `gh` CLI extension.

**Usage**:
```bash
gh extension install your-org/teambot
gh teambot init
gh teambot run
```

**Pros**:
- Integrates with GitHub workflow
- Automatic updates via gh extension upgrade
- Single command installation
- Cross-platform (wherever gh works)

**Cons**:
- Requires gh CLI to be installed
- May be confusing (teambot vs gh teambot)
- Extension limitations

**Effort**: Medium-High

---

## Decision Matrix

| Option | Effort | Reach | Maintenance | Dependencies | Best For |
|--------|--------|-------|-------------|--------------|----------|
| 1. PyPI | Medium | ★★★★★ | Low | None | Universal |
| 2. uvx | Low* | ★★★★☆ | Low | PyPI | Quick start |
| 3. Devcontainer Feature | Med-High | ★★★☆☆ | Medium | GHCR | Container users |
| 4. Devcontainer Template | Medium | ★★☆☆☆ | Medium | GHCR | New projects |
| 5. Docker Image | Medium | ★★★☆☆ | Medium | GHCR | Isolation |
| 6. Codespaces | Low | ★★☆☆☆ | Low | None | Demos |
| 7. Install Script | Low-Med | ★★★☆☆ | High | Hosting | Automation |
| 8. gh Extension | Med-High | ★★☆☆☆ | Medium | gh CLI | GitHub users |

*Low effort assumes PyPI package already exists

**Legend**: Reach = potential user base coverage; ★★★★★ = highest

---

## Scenario-Based Recommendations

### Scenario: New Empty Repository

**Recommended Options**: 
1. Devcontainer Template (Option 4) - for complete project setup
2. uvx (Option 2) - for quick initialization

**Workflow**:
```bash
# Option A: Start with template
mkdir my-project && cd my-project
git init
devcontainer templates apply ghcr.io/your-org/templates/teambot-python
# Open in devcontainer, TeamBot ready

# Option B: Quick init with uvx
mkdir my-project && cd my-project
git init
uvx teambot init
uvx teambot run
```

---

### Scenario: Existing Codebase

**Recommended Options**:
1. pip/uvx install (Options 1/2) - minimal footprint
2. Devcontainer Feature (Option 3) - if using devcontainers

**Workflow**:
```bash
# Option A: Direct install
pip install copilot-teambot
teambot init
teambot run objectives/add-feature.md

# Option B: Add to existing devcontainer
# In devcontainer.json, add:
# "features": { "ghcr.io/your-org/features/teambot:1": {} }
```

---

### Scenario: Devcontainer Without TeamBot Source

**Recommended Options**:
1. Devcontainer Feature (Option 3) - cleanest integration
2. pip install in postCreateCommand

**Workflow**:
```json
// devcontainer.json
{
  "name": "My Project",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "features": {
    "ghcr.io/your-org/features/teambot:1": {
      "version": "0.1.0",
      "include-copilot-cli": true
    }
  }
}
```

Alternative using postCreateCommand:
```json
{
  "postCreateCommand": "pip install copilot-teambot && teambot init --non-interactive"
}
```

---

### Scenario: WSL / Linux Environment

**Recommended Options**:
1. pip install (Option 1) - standard approach
2. uvx (Option 2) - if uv is already in use
3. Install script (Option 7) - for full automation

**Workflow**:
```bash
# Standard pip
pip install copilot-teambot

# Or with uv (faster)
uv tool install copilot-teambot

# Or install script
curl -sSL https://teambot.dev/install.sh | bash
```

---

### Scenario: Windows (Native, not WSL)

**Recommended Options**:
1. pip install (Option 1) - works with Python for Windows
2. Docker (Option 5) - isolated environment, no Python required
3. Devcontainer (Option 3/4) - if using VS Code with Dev Containers extension

**Workflow**:
```powershell
# Standard pip (requires Python installed)
pip install copilot-teambot
teambot init

# Or via Docker Desktop (no Python required)
docker run -it -v ${PWD}:/workspace ghcr.io/your-org/teambot:latest

# Or via VS Code Dev Containers (no Python required locally)
# Open folder in VS Code, add devcontainer feature, reopen in container
```

---

### Scenario: Non-Python Environment (No Python Installed)

**Recommended Options**:
1. Docker Image (Option 5) - fully self-contained
2. Devcontainer (Option 3/4) - for VS Code users
3. GitHub Codespaces (Option 6) - zero local setup

**Workflow**:
```bash
# Docker - no local Python needed
docker run -it -v $(pwd):/workspace ghcr.io/your-org/teambot:latest
teambot init
teambot run

# Or open project in Codespaces (browser-based, nothing local)
# Click "Open in Codespaces" badge on repo
```

**Key Point**: Users without Python can still use TeamBot via containerized options. The Docker image and devcontainer feature bundle Python internally.

---

## Implementation Phases

### Phase 1: PyPI Foundation (Required First)

- [ ] Verify package name availability on PyPI
- [ ] Set up TestPyPI publishing workflow first (GitHub Actions)
- [ ] Test full publish cycle on TestPyPI
- [ ] Set up production PyPI publishing workflow (GitHub Actions)
- [ ] Configure pyproject.toml for distribution
- [ ] Publish initial version to PyPI
- [ ] Test pip install from PyPI
- [ ] Document pip installation in README

### Phase 2: uvx Support (Low Effort After Phase 1)

- [ ] Verify uvx compatibility with published package
- [ ] Test uvx teambot workflow
- [ ] Document uvx usage as quick-start option
- [ ] Add uvx examples to getting-started guide

### Phase 3: Devcontainer Feature (High Value)

- [ ] Create devcontainer feature specification
- [ ] Implement feature install script with Python 3.10+ validation
- [ ] Set up feature publishing to GHCR
- [ ] Test feature in base images:
  - [ ] `mcr.microsoft.com/devcontainers/python:3.10`
  - [ ] `mcr.microsoft.com/devcontainers/python:3.12`
  - [ ] `mcr.microsoft.com/devcontainers/universal:2` (universal base)
  - [ ] `mcr.microsoft.com/devcontainers/base:ubuntu` (non-Python base)
- [ ] Document feature usage

### Phase 4: Documentation & Guides

- [ ] Update getting-started guide with all installation methods
- [ ] Create scenario-specific quick-start guides
- [ ] Add installation troubleshooting section
- [ ] Update README with installation options
- [ ] Create "Open in Codespaces" badge

### Phase 5: Optional Enhancements

- [ ] Devcontainer template (if demand exists)
- [ ] Docker image (if demand exists)
- [ ] Install script (if demand exists)

---

## Decisions (Resolved)

1. **Package Name**: `copilot-teambot` (confirmed "teambot" is not available on PyPI)

2. **Devcontainer Feature Hosting**: Part of main teambot repo (simplifies maintenance and versioning)

3. **Copilot CLI Bundling**: Install Copilot CLI if not already installed (feature should be self-sufficient)

4. **Priority Order** (confirmed):
   1. New project creation
   2. Existing codebase adoption
   3. Devcontainer integration
   4. WSL/Linux quick install

5. **Version Strategy**: Semantic Versioning (SemVer) across all distribution channels:
   - PyPI package: `copilot-teambot==X.Y.Z`
   - Devcontainer feature: `ghcr.io/.../teambot:X.Y.Z`
   - Docker image tags: `ghcr.io/.../teambot:X.Y.Z`

---

## Next Steps

1. ~~Review this document and select priority options~~ ✅
2. ~~Verify PyPI package name availability~~ ✅ → using `copilot-teambot`
3. Begin Phase 1 implementation (PyPI publishing)
4. Create detailed implementation specs for selected options

---
