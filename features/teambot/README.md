# TeamBot Devcontainer Feature

Installs [TeamBot](https://github.com/teambot-ai/teambot) CLI for autonomous AI agent workflows with GitHub Copilot.

## Usage

Add to your `devcontainer.json`:

```json
{
    "features": {
        "ghcr.io/teambot-ai/features/teambot:1": {}
    }
}
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `version` | string | `latest` | TeamBot version to install |

### Example with version pinning

```json
{
    "features": {
        "ghcr.io/teambot-ai/features/teambot:1": {
            "version": "0.2.0"
        }
    }
}
```

## Prerequisites

- GitHub Copilot CLI must be installed separately
- Python 3.10+ (handled by Python feature dependency)

## What's Installed

- `uv` package manager (if not present)
- `copilot-teambot` Python package via `uv tool install`
- `teambot` command available in PATH

## Post-Installation

After the container starts, you can use TeamBot:

```bash
# Initialize TeamBot in your project
teambot init

# Start interactive mode
teambot run

# Run with an objective
teambot run objectives/my-task.md
```

## More Information

- [TeamBot Documentation](https://github.com/teambot-ai/teambot/tree/main/docs)
- [Getting Started Guide](https://github.com/teambot-ai/teambot/blob/main/docs/guides/getting-started.md)
