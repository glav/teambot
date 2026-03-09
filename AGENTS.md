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
│   └── workflow/             # 11-stage workflow state machine
├── tests/                    # Test suite (1050 tests, 80% coverage)
├── docs/
│   ├── guides/               # User documentation (10 guides)
│   ├── feature-specs/        # Feature specifications
│   └── objectives/           # Objective file examples
├── .agent-tracking/          # SDD workflow artifacts
└── teambot.json              # Default configuration
```

## Objective Template

TeamBot provides an objective template for defining development tasks:

| File | Description |
|------|-------------|
| `docs/sdd-objective-template.md` | Template for creating TeamBot objectives. Copy this file and fill in the sections to define your development task. Run with `teambot run docs/objectives/my-objective.md`. |

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
uv run teambot run docs/objectives/my-task.md

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

### Workflow Stages (11)

```
SETUP → SPEC → SPEC_REVIEW → RESEARCH →
PLAN → PLAN_REVIEW → IMPLEMENTATION →
IMPLEMENTATION_REVIEW → ACCEPTANCE_TEST → POST_REVIEW → COMPLETE
```

**Notes:**
- `IMPLEMENTATION_REVIEW` now also verifies test execution and coverage (the former standalone `TEST` stage has been merged into it)
- Stages support `prerequisite_artifacts`, `output_schema`, `max_context_tokens`, and git checkpoints for fine-grained control

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

### `.agent` directory structure

The `.agent` directory contains commands, instructions, and standards used by AI-assisted workflows.

#### Commands (`commands/`)

Prompt files invoked as slash commands (e.g. `/sdd:0-initialize`).

| Path | Description |
|------|-------------|
| `commands/azdo/azdo.generate-pr-description.prompt.md` | Generates pull request descriptions using Azure DevOps templates. |
| `commands/docs/docs.create-adr.prompt.md` | Creates architecture decision records following organisational standards. |
| `commands/project/proj.sprint-planning.prompt.md` | Builds sprint plans for software engineering teams to deliver implementation engagements. |
| `commands/setup/setup.agents-md-creation.prompt.md` | Generates or updates the `AGENTS.md` file for the repository. |

**Spec-Driven Development (SDD) workflow** (`commands/sdd/`)

A sequential workflow with quality gates for taking a feature from specification through to implementation.

| Path | Description |
|------|-------------|
| `commands/sdd/README.md` | Documents the SDD workflow overview and its 9 sequential steps. |
| `commands/sdd/sdd.0-initialize.prompt.md` | Initialises the SDD workflow by verifying prerequisites and creating tracking directories. |
| `commands/sdd/sdd.1-create-feature-spec.prompt.md` | Guides creation of feature specifications with Q&A and reference integration. |
| `commands/sdd/sdd.2-review-spec.prompt.md` | Reviews and validates specifications before the research phase. |
| `commands/sdd/sdd.3-research-feature.prompt.md` | Conducts comprehensive research and analysis for the feature. |
| `commands/sdd/sdd.4-task-planner-for-feature.prompt.md` | Creates actionable implementation plans for the feature. |
| `commands/sdd/sdd.5-review-plan.prompt.md` | Reviews and validates implementation plans before execution. |
| `commands/sdd/sdd.6-task-implementer-for-feature.prompt.md` | Implements task plans with progressive tracking and change records. |
| `commands/sdd/sdd.6b-implementation-review.prompt.md` | Reviews implementation changes, verifies test execution and coverage. |
| `commands/sdd/sdd.7-post-implementation-review.prompt.md` | Performs post-implementation review and final validation. |

#### Instructions (`instructions/`)

Contextual guidelines automatically applied to AI interactions.

| Path | Description |
|------|-------------|
| `instructions/prompt.instructions.md` | Guidelines for creating high-quality prompt files for GitHub Copilot. |
| `instructions/bash/bash.instructions.md` | Instructions for bash script implementation with established conventions. |
| `instructions/bash/bash.md` | Guidelines for secure, maintainable bash scripting practices. |
| `instructions/bicep/bicep-standards.md` | Coding standards and best practices for Bicep Infrastructure as Code. |
| `instructions/bicep/bicep.instructions.md` | Instructions for Bicep infrastructure implementation. |
| `instructions/bicep/bicep.md` | Structural guidelines for Bicep development. |

#### Standards (`standards/`)

Templates and standards referenced by commands and instructions.

| Path | Description |
|------|-------------|
| `standards/decision-record-standards.md` | Standards for creating decision records capturing architectural and policy decisions. |
| `standards/decision-record-template.md` | Template for decision records with status, deciders, context, and consequences. |
| `standards/feature-spec-template.md` | Template for feature specification documents with progress tracking. |
| `standards/research-feature-template.md` | Template for task research documents with implementation analysis. |
| `standards/task-planning-template.md` | Template for task checklists with overview and implementation instructions. |


## Testing

- Framework: `pytest` with `pytest-cov` and `pytest-mock`
- Tests located in `tests/` directory
- Current coverage: 80% (1050 tests)

## Security and Secrets

- Never commit `.env` or API keys
- Copilot CLI handles authentication separately
- History files in `.teambot/` may contain task details - review before sharing

## Clean commits
- When committing or changing code, always ensure properly linted code by running:
- `uv run ruff format -- .` and `uv run ruff check . --fix` as part of the process.
- Also ensure thet `uv run ruff format --check .` is executed as part of the process.

## Troubleshooting

- If Copilot CLI not found: Install from https://githubnext.com/projects/copilot-cli/
- If workflow state corrupted: Delete `.teambot/workflow_state.json`
- If tests fail: Ensure `uv sync --group dev` was run
