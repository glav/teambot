# Installation Guide

This guide covers all installation methods for TeamBot, organized by user persona.

## Prerequisites

Before installing TeamBot, ensure you have:

1. **Python 3.10 or later** - [Download Python](https://www.python.org/downloads/)
2. **GitHub Copilot CLI** - [Install Copilot CLI](https://githubnext.com/projects/copilot-cli/)

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
# Using uvx (requires uv installed)
uvx copilot-teambot --help
uvx copilot-teambot init

# Install uv first if needed
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Pros**: No permanent installation, always uses latest version  
**Cons**: Slightly slower startup (downloads on each run)

---

### 🐍 Python Developer (pip)

**Goal**: Install TeamBot as a global or virtual environment package.

```bash
# Global installation
pip install copilot-teambot

# Or in a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install copilot-teambot
```

**Verify**:
```bash
teambot --version
```

---

### 📦 Existing Codebase Adopter

**Goal**: Add TeamBot to an existing project's dependencies.

#### Using requirements.txt

```bash
echo "copilot-teambot>=0.2.0" >> requirements.txt
pip install -r requirements.txt
```

#### Using pyproject.toml

```toml
[project.optional-dependencies]
dev = [
    "copilot-teambot>=0.2.0",
]
```

Then install:
```bash
pip install -e ".[dev]"
```

---

### 🔧 Devcontainer User (VS Code / Codespaces)

**Goal**: Pre-install TeamBot in development container.

Add to your `devcontainer.json`:

```json
{
    "features": {
        "ghcr.io/teambot-ai/features/teambot:1": {}
    }
}
```

#### With Version Pinning

```json
{
    "features": {
        "ghcr.io/teambot-ai/features/teambot:1": {
            "version": "0.2.0"
        }
    }
}
```

#### With Copilot CLI

```json
{
    "features": {
        "ghcr.io/devcontainers/features/copilot-cli:latest": {},
        "ghcr.io/teambot-ai/features/teambot:1": {}
    }
}
```

---

### 🪟 Windows Developer

**Goal**: Install on Windows 10/11 using PowerShell or CMD.

#### PowerShell

```powershell
# Install Python if needed (using winget)
winget install Python.Python.3.12

# Install TeamBot
pip install copilot-teambot

# Verify
teambot --version
```

#### CMD

```cmd
pip install copilot-teambot
teambot --version
```

#### Windows Notes

- Ensure Python is added to PATH during installation
- Use `python -m pip` if `pip` is not recognized
- The `teambot` command works in both PowerShell and CMD

---

### 🐳 Non-Python Developer (Docker)

**Goal**: Use TeamBot without installing Python locally.

```bash
# Run help
docker run --rm ghcr.io/teambot-ai/teambot --help

# Initialize in current directory
docker run -it -v $(pwd):/workspace ghcr.io/teambot-ai/teambot init

# Run interactive mode
docker run -it -v $(pwd):/workspace ghcr.io/teambot-ai/teambot run

# Run with objective
docker run -it -v $(pwd):/workspace ghcr.io/teambot-ai/teambot run objectives/task.md
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

### pip

```bash
pip install --upgrade copilot-teambot
```

### uvx

```bash
# uvx always uses latest by default
uvx copilot-teambot@latest --version
```

### pipx

```bash
pipx upgrade copilot-teambot
```

---

## Troubleshooting

### "teambot: command not found"

Python scripts directory may not be in PATH:

```bash
# Check where pip installed it
pip show copilot-teambot

# Add to PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"

# Add to PATH (Windows PowerShell)
$env:Path += ";$env:APPDATA\Python\Python312\Scripts"
```

### "Copilot CLI not found"

TeamBot requires the GitHub Copilot CLI:

```bash
# Install Copilot CLI
# Follow: https://githubnext.com/projects/copilot-cli/

# Authenticate
copilot auth
```

### Dependency conflicts

Use pipx or uvx for isolated installation:

```bash
pipx install copilot-teambot
# or
uvx copilot-teambot
```

### SSL certificate errors

Update certificates or use trusted hosts:

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org copilot-teambot
```

---

## Next Steps

After installation:

1. [Getting Started](getting-started.md) - First run walkthrough
2. [Interactive Mode](interactive-mode.md) - REPL and ad-hoc tasks
3. [File-Based Orchestration](file-based-orchestration.md) - Autonomous objectives
4. [Configuration](configuration.md) - Customize TeamBot behavior
