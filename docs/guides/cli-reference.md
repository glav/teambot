# CLI Reference

Complete reference for all TeamBot CLI commands and options.

## Commands

### `teambot init`

Initialize TeamBot configuration in the current directory.

```bash
teambot init [--force]
```

| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing configuration |

**Creates**:
- `teambot.json` - Configuration file
- `.teambot/` - Shared workspace directory

### `teambot run`

Run TeamBot with an optional objective file.

```bash
teambot run [objective] [-c CONFIG] [--resume] [--max-hours HOURS]
```

| Option | Description |
|--------|-------------|
| `objective` | Path to objective markdown file (optional) |
| `-c, --config` | Configuration file path (default: `teambot.json`) |
| `--resume` | Resume interrupted orchestration |
| `--max-hours` | Maximum execution hours (default: 8) |

**Examples**:

```bash
# Run with objective file (autonomous mode)
uv run teambot run objectives/my-feature.md

# Start interactive REPL
uv run teambot run

# Resume interrupted execution
uv run teambot run --resume

# Custom time limit
uv run teambot run objectives/task.md --max-hours 4
```

### `teambot status`

Display current TeamBot status.

```bash
teambot status
```

Shows:
- Current workflow stage
- Active agents
- Recent history

## Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version number |
| `-v, --verbose` | Enable verbose/debug output |

## Interactive Mode Commands

When in interactive mode (`teambot run` without objective):

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/status` | Show agent status |
| `/tasks` | List all tasks |
| `/task <id>` | View task details |
| `/cancel <id>` | Cancel a task |
| `/models` | List available models |
| `/model` | Show current model overrides |
| `/model @agent <model>` | Set model for agent |
| `/model @agent clear` | Clear model override |

---

## Next Steps

- [Getting Started](getting-started.md) - Installation and first run
- [Interactive Mode](interactive-mode.md) - REPL details
- [Configuration](configuration.md) - Configuration options
