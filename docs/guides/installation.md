# Installation Guide

This guide covers all installation methods for TeamBot, organized by user persona.

## Prerequisites

Before installing TeamBot, ensure you have:

1. **Python 3.10 or later** - [Download Python](https://www.python.org/downloads/)
2. **uv** - [Install uv](https://astral.sh/uv)
3. **GitHub Copilot CLI** - [Install Copilot CLI](https://githubnext.com/projects/copilot-cli/)

### Verify Copilot CLI

```bash
copilot --version
copilot auth  # Authenticate if needed
```

---

## Installation by Persona

### 🚀 Evaluator (Quick Trial)

**Goal**: Try TeamBot without installing anything permanently.

```bash
# Using uvx with git (requires uv installed)
uvx --from git+https://github.com/glav/teambot teambot --help
uvx --from git+https://github.com/glav/teambot teambot init

# Install uv first if needed
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Pros**: No permanent installation, always uses latest version  
**Cons**: Slightly slower startup (clones on each run)

---

### 🐍 Python Developer (From Source)

**Goal**: Install TeamBot for development.

```bash
# Clone and install
git clone https://github.com/glav/teambot.git
cd teambot
uv sync

# Run TeamBot
uv run teambot --version
```

**Verify**:
```bash
uv run teambot --version
```

---

### 🔧 Devcontainer User (VS Code / Codespaces)

**Goal**: Pre-install TeamBot in development container.

Add to your `devcontainer.json`:

```json
{
    "features": {
        "ghcr.io/glav/features/teambot:1": {}
    }
}
```

#### With Version Pinning

```json
{
    "features": {
        "ghcr.io/glav/features/teambot:1": {
            "version": "0.1.0"
        }
    }
}
```

#### With Copilot CLI

```json
{
    "features": {
        "ghcr.io/devcontainers/features/copilot-cli:latest": {},
        "ghcr.io/glav/features/teambot:1": {}
    }
}
```

#### Understanding the Feature Reference

The devcontainer feature reference follows this format:

| Part | Meaning |
|------|---------|
| `ghcr.io` | GitHub Container Registry |
| `/glav` | GitHub organization (repository owner) |
| `/features/teambot` | Feature name (from `id` in feature definition) |
| `:1` | Major version selector (from semver `1.x.x`) |

The feature is published as an OCI artifact to GitHub Container Registry when TeamBot creates a new release. The `:1` selector automatically resolves to the latest `1.x.x` version.

> **Note**: The devcontainer feature is only available after TeamBot publishes a release. If the reference doesn't resolve, check the [TeamBot releases page](https://github.com/glav/teambot/releases) to verify a release exists.

---

### 🪟 Windows Developer

**Goal**: Install on Windows 10/11 using PowerShell or CMD.

#### PowerShell

```powershell
# Install Python if needed (using winget)
winget install Python.Python.3.12

# Install uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone and install TeamBot
git clone https://github.com/glav/teambot.git
cd teambot
uv sync

# Verify
uv run teambot --version
```

#### Windows Notes

- Ensure Python is added to PATH during installation
- The `uv run teambot` command works in both PowerShell and CMD

---

### 🐳 Non-Python Developer (Docker)

**Goal**: Use TeamBot without installing Python locally.

```bash
# Run help
docker run --rm ghcr.io/glav/teambot --help

# Initialize in current directory
docker run -it -v $(pwd):/workspace ghcr.io/glav/teambot init

# Run interactive mode
docker run -it -v $(pwd):/workspace ghcr.io/glav/teambot run

# Run with objective
docker run -it -v $(pwd):/workspace ghcr.io/glav/teambot run objectives/task.md
```

#### Docker Notes

- Mount your project directory as `/workspace`
- Use `-it` for interactive mode
- Copilot CLI authentication must be handled separately

---

## Verification

After installation, verify everything works:

```bash
# Check version
teambot --version

# Check help
teambot --help

# Initialize in a project
cd your-project
teambot init

# Check status
teambot status
```

---

## Upgrading

### From Source

```bash
cd teambot
git pull
uv sync
```

### uvx (git)

```bash
# uvx with git always fetches latest
uvx --from git+https://github.com/glav/teambot teambot --version
```

---

## Troubleshooting

### "teambot: command not found"

When installing from source, use `uv run teambot` instead of `teambot` directly.

### "Copilot CLI not found"

TeamBot requires the GitHub Copilot CLI:

```bash
# Install Copilot CLI
# Follow: https://githubnext.com/projects/copilot-cli/

# Authenticate
copilot auth
```

### "uv: command not found"

Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Next Steps

After installation:

1. [Getting Started](getting-started.md) - First run walkthrough
2. [Interactive Mode](interactive-mode.md) - REPL and ad-hoc tasks
3. [File-Based Orchestration](file-based-orchestration.md) - Autonomous objectives
4. [Configuration](configuration.md) - Customize TeamBot behavior
