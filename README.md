# Template - Python

This repository is a small, intentionally minimal Python template you can use as the starting point for new repos.

It’s designed to be a quick workflow to get started while keeping the day-0 developer experience solid (devcontainer support, modern dependency management, and a place for agent instructions).

## What this template includes

- Python 3.12 devcontainer setup
- `uv` for dependency management (`pyproject.toml` + `uv.lock`)
- A tiny runnable entrypoint (`src/app.py`) that loads environment variables from `.env` via `python-dotenv`
- `AGENTS.md` for coding-agent guidance

## Using this repo as a template

Typical workflow:

1. Create a new repository from this template (GitHub: “Use this template”).
2. Update project metadata in `pyproject.toml` (name/description).
3. Replace the sample app code under `src/` with your real project.
4. Update `AGENTS.md` and this README to reflect the new repo’s purpose.

## Setup

This repo uses `uv`.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
```

## Run

```bash
uv run python src/app.py
```

## Linting and formatting

This template includes `ruff`.

```bash
uv sync --group dev
uv run ruff check .
uv run ruff format .
```

## Environment variables

- Copy `.env-sample` to `.env` and fill in values as needed.
- `.env` is gitignored.

```bash
cp .env-sample .env
```

## Copilot / AI Assisted workflow

This template includes an `.agent/` directory containing reusable prompt “commands” and standards you can use with GitHub Copilot (and other coding agents).

- `.agent/commands/`: ready-to-run prompts for common tasks, for example:
	- `setup/`: repo bootstrap tasks (e.g. creating `AGENTS.md`)
	- `project/`: planning prompts (e.g. sprint planning)
	- `docs/`: documentation prompts (e.g. creating ADRs)
- `.agent/standards/`: templates and standards for consistent artifacts (ADRs, feature specs, task plans)
- `.agent/instructions/`: “apply-to” instructions that guide how agents write certain file types (e.g. Bash and Bicep)

If you base a new repository on this template, treat `.agent/` as a starting library: keep what helps your team, remove what doesn’t, and add org-specific workflows over time.

## Copilot CLI (devcontainer)

The devcontainer includes GitHub Copilot CLI via the official devcontainer feature (`ghcr.io/devcontainers/features/copilot-cli:latest`).

## Spec-Driven Development (SDD) Workflow

This template includes an enhanced **Spec-Driven Development (SDD)** workflow in `.agent/commands/sdd/`. The SDD workflow provides a structured, 9-step process for developing features with built-in quality gates and testing integration.

### SDD Workflow Steps

| Step | Prompt File | Purpose |
|------|-------------|---------|
| 0 | `sdd.0-initialize.prompt.md` | Initialize environment and verify prerequisites |
| 1 | `sdd.1-create-feature-spec.prompt.md` | Create feature specification via guided Q&A |
| 2 | `sdd.2-review-spec.prompt.md` | Review spec for completeness (quality gate) |
| 3 | `sdd.3-research-feature.prompt.md` | Research implementation approach |
| 4 | `sdd.4-determine-test-strategy.prompt.md` | Determine TDD vs Code-First approach |
| 5 | `sdd.5-task-planner-for-feature.prompt.md` | Create implementation plan with test phases |
| 6 | `sdd.6-review-plan.prompt.md` | Review plan for readiness (quality gate) |
| 7 | `sdd.7-task-implementer-for-feature.prompt.md` | Execute implementation systematically |
| 8 | `sdd.8-post-implementation-review.prompt.md` | Final validation before completion |

### How to Use

1. **Initialize**: Run `sdd.0-initialize.prompt.md` to set up the environment
2. **Start a feature**: Run `sdd.1-create-feature-spec.prompt.md` with your feature idea
3. **Follow handoffs**: Each step tells you which step to run next
4. **Don't skip review gates**: Steps 2, 4, 6, and 8 catch issues early

### Key Features

- **Quality gates** at review steps with explicit PASS/FAIL validation
- **Deterministic test strategy** using a scoring-based decision matrix
- **Integrated testing** with mandatory test phases in implementation plans
- **State management** for session continuity across steps
- **Artifact tracking** in `.agent-tracking/` directory

For full documentation, see `.agent/commands/sdd/README.md`.
