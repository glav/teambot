# AGENTS.md

## Project Overview

TeamBot is a CLI tool that wraps the GitHub Copilot CLI to enable collaborative, multi-agent AI workflows for software development. It orchestrates a team of 6 specialized AI agent personas that work together autonomously to achieve development objectives.

## Repo Layout

```
teambot/
├── src/teambot/              # Main package
│   ├── __init__.py           # Package version (0.1.0)
│   ├── cli.py                # CLI entry point (init/run/status commands)
│   ├── orchestrator.py       # Agent lifecycle and workflow management
│   ├── agent_runner.py       # Individual agent process execution
│   ├── window_manager.py     # Cross-platform window spawning
│   ├── config/               # Configuration loading (JSON)
│   ├── copilot/              # Copilot CLI wrapper
│   ├── history/              # History file management with frontmatter
│   ├── messaging/            # Inter-agent messaging (multiprocessing queues)
│   ├── prompts/              # Persona-specific prompt templates
│   ├── visualization/        # Rich console display
│   └── workflow/             # 13-stage workflow state machine
├── tests/                    # Test suite (192 tests, 88% coverage)
├── docs/
│   ├── guides/               # User documentation (10 guides)
│   ├── feature-specs/        # Feature specifications
│   └── objectives/           # Objective file examples
├── .agent-tracking/          # SDD workflow artifacts
└── teambot.json              # Default configuration
```

## Setup

### Install uv

TeamBot uses `uv` for dependency management.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If `uv` is installed during devcontainer creation, restart the terminal so `uv` is on your `PATH`.

### Install Dependencies

```bash
uv sync
```

### External Dependency

TeamBot requires the standalone GitHub Copilot CLI (`copilot` command):
- Install from: https://githubnext.com/projects/copilot-cli/
- Verify with: `copilot --version`

## Development Workflow

### Run TeamBot

```bash
# Initialize a project
uv run teambot init

# Run with an objective
uv run teambot run objectives/my-task.md

# Check status
uv run teambot status
```

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src/teambot --cov-report=term-missing

# Specific module
uv run pytest tests/test_workflow/
```

### Linting and Formatting

```bash
uv sync --group dev
uv run ruff check .
uv run ruff format .
```

## Architecture

### Agent Personas (6 MVP)

| ID | Persona | Role |
|----|---------|------|
| `pm` | Project Manager | Planning, coordination |
| `ba` | Business Analyst | Requirements, specs |
| `writer` | Technical Writer | Documentation |
| `builder-1` | Builder (Primary) | Implementation |
| `builder-2` | Builder (Secondary) | Implementation (parallel) |
| `reviewer` | Reviewer | Code review, QA |

### Workflow Stages (13)

```
SETUP → BUSINESS_PROBLEM → SPEC → SPEC_REVIEW → RESEARCH →
TEST_STRATEGY → PLAN → PLAN_REVIEW → IMPLEMENTATION →
IMPLEMENTATION_REVIEW → TEST → POST_REVIEW → COMPLETE
```

### Key Components

- **Orchestrator**: Manages agent lifecycle, workflow state, message routing
- **AgentRunner**: Executes tasks via CopilotClient with persona prompts
- **WorkflowStateMachine**: Enforces stage transitions, validates personas
- **HistoryManager**: Creates/reads history files with YAML frontmatter
- **MessageRouter**: Routes messages between agents via multiprocessing queues

## Copilot / AI Assisted Workflow

- All Copilot and AI assisted workflows exist in the `.agent/` directory
- SDD (Spec-Driven Development) workflow in `.agent/commands/sdd/`
- Artifacts tracked in `.agent-tracking/`

## Testing

- Framework: `pytest` with `pytest-cov` and `pytest-mock`
- Tests located in `tests/` directory
- Current coverage: 88% (192 tests)

## Security and Secrets

- Never commit `.env` or API keys
- Copilot CLI handles authentication separately
- History files in `.teambot/` may contain task details - review before sharing

## Clean commits
- When commiting or changing code, always ensure properly linted code by running:
- `uv run ruff format -- .` and `v run ruff check . --fix` as part of the process.

## Troubleshooting

- If Copilot CLI not found: Install from https://githubnext.com/projects/copilot-cli/
- If workflow state corrupted: Delete `.teambot/workflow_state.json`
- If tests fail: Ensure `uv sync --group dev` was run
