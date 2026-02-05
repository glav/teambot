# Getting Started

This guide covers installation, prerequisites, and running your first TeamBot objective.

## Prerequisites

- **Python 3.12+** - [Download Python](https://www.python.org/downloads/)
- **uv package manager** - [Install uv](https://github.com/astral-sh/uv)
- **GitHub Copilot access** - SDK authenticates via GitHub CLI

## Installation

```bash
# Clone the repository
git clone https://github.com/teambot-ai/teambot.git
cd teambot

# Install dependencies
uv sync

# Verify installation
uv run teambot --version
```

## Initialize a Project

Create TeamBot configuration in your project directory:

```bash
uv run teambot init
```

This creates:
- `teambot.json` - Configuration file
- `.teambot/` - Shared workspace directory

Use `--force` to overwrite existing configuration:

```bash
uv run teambot init --force
```

## Running TeamBot

### Autonomous Mode (Objective File)

```bash
# Run with an objective file
uv run teambot run objectives/my-feature.md

# Set custom time limit (default: 8 hours)
uv run teambot run objectives/task.md --max-hours 4

# Resume interrupted execution
uv run teambot run --resume
```

### Interactive Mode

```bash
# Start interactive REPL (no objective file)
uv run teambot run
```

### Check Status

```bash
uv run teambot status
```

## First Run Example

1. **Initialize**: `uv run teambot init`
2. **Create objective**: Write your goals in `objectives/my-task.md`
3. **Run**: `uv run teambot run objectives/my-task.md`
4. **Monitor**: Watch the 13-stage workflow execute automatically

---

## Troubleshooting FAQ

### Copilot SDK Not Available

```
Error: Copilot SDK not available - install github-copilot-sdk
```

The SDK should be installed automatically with `uv sync`. If missing:

```bash
uv add github-copilot-sdk
```

### Configuration Already Exists

```bash
# Use --force to overwrite
teambot init --force
```

### No State to Resume

```
Error: No orchestration state to resume
```

Run a new objective first, then use `--resume` after cancellation.

### Review Failed After 4 Iterations

Check `.teambot/failures/` for detailed failure reports with suggestions.

### Workflow State Corrupted

```bash
# Remove corrupted state files
rm .teambot/workflow_state.json
rm .teambot/orchestration_state.json

# Re-run
teambot run objectives/my-task.md
```

---

## Next Steps

- [File-Based Orchestration](file-based-orchestration.md) - Running objectives in detail
- [Interactive Mode](interactive-mode.md) - REPL and pipelines
- [CLI Reference](cli-reference.md) - All available commands
