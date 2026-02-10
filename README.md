# TeamBot

**Autonomous AI Agent Teams for Software Development**

TeamBot is a CLI tool that uses the [GitHub Copilot SDK](https://github.com/github/copilot-sdk) to enable collaborative, multi-agent AI workflows. Instead of single-threaded AI interactions, TeamBot orchestrates a team of specialized AI agents that work together autonomously to achieve development objectives.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-1050%20passing-green.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-80%25-green.svg)]()

## Key Features

- 🤖 **6 Specialized Agent Personas** - PM, BA, Writer, 2 Builders, Reviewer
- 📋 **14-Stage Prescriptive Workflow** - From setup through acceptance testing to completion
- 🔄 **Autonomous Operation** - Define objectives in markdown, let the team execute
- ⚡ **Parallel Builders** - builder-1 and builder-2 execute concurrently
- 💬 **Interactive REPL** - Ad-hoc tasks with pipelines and multi-agent mode
- ⚙️ **Configurable** - Custom stages, models, and workflows

### Interactive mode
![Screenshot](./docs/guides/teambot-shot1.png)

### Autonomous mode
![Screenshot](./docs/guides/teambot-shot2.png)
![Screenshot](./docs/guides/teambot-shot3.png)

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- GitHub Copilot access

## Quick Start

```bash
# Install dependencies
uv sync

# Initialize TeamBot
uv run teambot init

# Run with an objective file
uv run teambot run objectives/my-feature.md

# Or start interactive mode
uv run teambot run
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/guides/getting-started.md) | Installation, setup, first run, troubleshooting |
| [File-Based Orchestration](docs/guides/file-based-orchestration.md) | Running objectives autonomously |
| [Interactive Mode](docs/guides/interactive-mode.md) | REPL, pipelines, multi-agent mode |
| [CLI Reference](docs/guides/cli-reference.md) | All commands and options |
| [Agent Personas](docs/guides/agent-personas.md) | The 6 specialized AI agents |
| [Workflow Stages](docs/guides/workflow-stages.md) | 14-stage development process |
| [Configuration](docs/guides/configuration.md) | teambot.json, stages.yaml, models |
| [Objective Format](docs/guides/objective-format.md) | Writing objective files |
| [Shared Workspace](docs/guides/shared-workspace.md) | .teambot/ directory structure |
| [Development](docs/guides/development.md) | Contributing and development setup |
| [Architecture](docs/guides/architecture.md) | Internal components and design |

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

See [Development Guide](docs/guides/development.md) for setup and contribution guidelines.

---

<p align="center">
  Made with 🤖 by TeamBot
</p>
