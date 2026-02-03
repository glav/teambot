# TeamBot

**Autonomous AI Agent Teams for Software Development**

TeamBot is a CLI tool that uses the [GitHub Copilot SDK](https://github.com/github/copilot-sdk) to enable collaborative, multi-agent AI workflows. Instead of single-threaded AI interactions, TeamBot orchestrates a team of specialized AI agents that work together autonomously to achieve development objectives.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-650%20passing-green.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-83%25-green.svg)]()

## Features

- 🤖 **Multi-Agent Orchestration** - 6 specialized agent personas working together
- 📋 **Prescriptive Workflow** - 13-stage workflow from Setup to Post-Implementation Review
- 🔄 **Autonomous Operation** - Define objectives in markdown, let the team execute
- ⚡ **Parallel Builders** - builder-1 and builder-2 execute concurrently during implementation
- 🔁 **Review Iteration** - Automatic review cycles with max 4 iterations per stage
- ➡️ **Pipeline Operator** - Chain tasks with `->` to pass output between agents
- 💾 **State Persistence** - Resume interrupted workflows with `--resume`
- ⏱️ **Time Limits** - Configurable execution timeout (default 8 hours)
- 📁 **Shared Context** - Agents collaborate via `.teambot/` directory
- 🖥️ **Split-Pane Interface** - Separate input and output panes for interactive mode

---

## Table of Contents

- [Quick Start](#quick-start)
- [File-Based Orchestration](#file-based-orchestration)
- [Interactive Mode](#interactive-mode)
- [CLI Commands](#cli-commands)
- [Agent Personas](#agent-personas)
- [Prescriptive Workflow](#prescriptive-workflow)
- [Configuration](#configuration)
- [Objective File Format](#objective-file-format)
- [Shared Workspace](#shared-workspace)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- GitHub Copilot access (SDK authenticates via GitHub CLI)

### Installation

```bash
# Clone the repository
git clone https://github.com/teambot-ai/teambot.git
cd teambot

# Install dependencies
uv sync

# Verify installation
uv run teambot --version
```

### Initialize a Project

```bash
# Create TeamBot configuration in current directory
uv run teambot init

# This creates:
# - teambot.json (configuration)
# - .teambot/ (shared workspace directory)
```

### Run TeamBot

```bash
# Run with an objective file (autonomous mode)
uv run teambot run objectives/my-feature.md

# Resume interrupted execution
uv run teambot run --resume

# Interactive mode (no objective file)
uv run teambot run

# Check status
uv run teambot status
```

---

## File-Based Orchestration

The primary way to use TeamBot is with objective files. Define your goals in markdown, and TeamBot autonomously executes the 13-stage workflow.

### Running an Objective

```bash
# Run an objective file
uv run teambot run objectives/my-task.md

# Set custom time limit (default: 8 hours)
uv run teambot run objectives/task.md --max-hours 4

# Resume interrupted execution
uv run teambot run --resume
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Review Iteration** | Each review stage iterates up to 4 times until approval |
| **Parallel Builders** | builder-1 and builder-2 execute concurrently during IMPLEMENTATION |
| **Time Limits** | Configurable timeout prevents runaway execution (default: 8 hours) |
| **State Persistence** | State saved on completion, cancellation, or timeout |
| **Progress Display** | Real-time stage and agent status updates |

### Execution Flow

1. Parse objective file (goals, success criteria, constraints)
2. Progress through 13 workflow stages
3. For review stages: iterate until approval or 4 failures
4. Save state on completion, cancellation, or timeout

### Cancellation & Resume

- Press `Ctrl+C` to gracefully cancel execution
- State is saved automatically to `.teambot/orchestration_state.json`
- Resume later with `uv run teambot run --resume`

### Review Failure Handling

If a review stage fails after 4 iterations:
- Execution stops with error message
- Detailed failure report saved to `.teambot/failures/`
- Report contains all iteration feedback and suggestions

---

## Interactive Mode

For ad-hoc tasks without an objective file, TeamBot provides an interactive REPL:

```bash
uv run teambot run
```

### Basic Commands

```bash
# Send a task to an agent
teambot: @pm Create a project plan for the new feature

# Check agent status
teambot: /status

# Get help
teambot: /help
```

### Pipelines with Dependencies

Use `->` to chain tasks where each depends on the previous output:

```bash
# Two-stage pipeline: plan then implement
teambot: @pm Create a plan for user authentication -> @builder-1 Implement based on this plan

# Three-stage pipeline: requirements -> implementation -> review
teambot: @ba Write requirements for the API -> @builder-1 Implement this API -> @reviewer Review the implementation
```

The output from each stage is automatically injected into the next agent's context:

```
# Stage 1: @ba produces requirements
=== @ba ===
Requirements: 1. REST API endpoint...

# Stage 2: @builder-1 receives @ba's output
[Context: "=== Output from @ba ===\n{requirements}\n\n=== Your Task ===\nImplement this API"]
Implementation complete...

# Stage 3: @reviewer receives @builder-1's output
[Context includes implementation from @builder-1]
Code review feedback...
```

### Multi-Agent Same Prompt

Use `,` to send the same prompt to multiple agents simultaneously:

```bash
# Ask multiple agents to analyze the same thing
teambot: @pm,ba,writer Analyze the requirements for the login feature
```

All agents work in parallel and results are combined:

```
=== @pm ===
From a project management perspective...

=== @ba ===
The business requirements include...

=== @writer ===
Documentation needs for this feature...
```

### Combined Syntax

Combine `,` and `->` for complex workflows:

```bash
# Multiple analysts work in parallel, then results go to builder
teambot: @pm,ba Analyze the feature -> @builder-1 Implement based on analysis
```

### Task Management

```bash
# List all tasks
teambot: /tasks

# View task details
teambot: /task 1

# Cancel a task
teambot: /cancel 1
```

### Syntax Quick Reference

| Syntax | Description | Example |
|--------|-------------|---------|
| `@agent task` | Single agent task | `@pm Create a plan` |
| `@a,b,c task` | Multi-agent parallel, same prompt | `@pm,ba,writer Analyze feature` |
| `@a task -> @b task` | Pipeline with dependency | `@pm Plan -> @builder-1 Implement` |
| `@a,b t1 -> @c t2` | Parallel then pipeline | `@pm,ba Analyze -> @builder-1 Build` |
| `/tasks` | List all tasks | |
| `/task <id>` | View task details | `/task 1` |
| `/cancel <id>` | Cancel task | `/cancel 3` |
| `/status` | Show agent status | |

### Split-Pane Interface

TeamBot features a split-pane terminal interface (powered by [Textual](https://textual.textualize.io/)):

- **Left pane**: Command input with live agent status display
- **Right pane**: Agent output displayed asynchronously

The interface automatically falls back to legacy (single-pane) mode when:
- `TEAMBOT_LEGACY_MODE=true` environment variable is set
- Terminal width is less than 80 columns
- stdout is not a TTY

---

## CLI Commands

### `teambot init`

Initialize TeamBot configuration in the current directory.

```bash
teambot init [--force]
```

| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing configuration |

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

### `teambot status`

Display current TeamBot status.

```bash
teambot status
```

### Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version number |
| `-v, --verbose` | Enable verbose/debug output |

---

## Agent Personas

TeamBot includes 6 specialized agent personas:

| Agent | Persona | Role |
|-------|---------|------|
| `pm` | Project Manager | Planning, coordination, task assignment |
| `ba` | Business Analyst | Requirements, problem definition, specs |
| `writer` | Technical Writer | Documentation, guides, API docs |
| `builder-1` | Builder (Primary) | Implementation, coding, testing |
| `builder-2` | Builder (Secondary) | Implementation, coding, testing |
| `reviewer` | Reviewer | Code review, quality assurance |

### Persona Capabilities

**Project Manager (`pm`)**: Creates project plans, breaks down features, coordinates team members, tracks progress.

**Business Analyst (`ba`)**: Gathers requirements, defines business problems, creates user stories and acceptance criteria.

**Technical Writer (`writer`)**: Writes documentation, API docs, user guides, architecture decision records.

**Builder (`builder-1`, `builder-2`)**: Implements features, writes tests, debugs issues. Both builders can execute concurrently during implementation.

**Reviewer (`reviewer`)**: Reviews code and documentation for quality, identifies bugs and improvements, verifies standards compliance.

---

## Prescriptive Workflow

TeamBot enforces a 13-stage workflow:

```
SETUP → BUSINESS_PROBLEM → SPEC → SPEC_REVIEW → RESEARCH →
TEST_STRATEGY → PLAN → PLAN_REVIEW → IMPLEMENTATION →
IMPLEMENTATION_REVIEW → TEST → POST_REVIEW → COMPLETE
```

### Stage Details

| Stage | Description | Allowed Personas |
|-------|-------------|------------------|
| `SETUP` | Initialize project and configuration | PM |
| `BUSINESS_PROBLEM` | Define business problem and goals (optional) | BA, PM |
| `SPEC` | Create feature specification | BA, Writer |
| `SPEC_REVIEW` | Review and approve spec | Reviewer, PM |
| `RESEARCH` | Research technical approaches | Builder, Writer |
| `TEST_STRATEGY` | Define testing approach | Builder, Reviewer |
| `PLAN` | Create implementation plan | PM, Builder |
| `PLAN_REVIEW` | Review and approve plan | Reviewer, PM |
| `IMPLEMENTATION` | Execute the plan | Builder (parallel) |
| `IMPLEMENTATION_REVIEW` | Review changes | Reviewer |
| `TEST` | Execute tests and validate | Builder, Reviewer |
| `POST_REVIEW` | Final review and retrospective | PM, Reviewer |
| `COMPLETE` | Workflow complete | - |

### Review Stages

Four stages require review approval:
- `SPEC_REVIEW`, `PLAN_REVIEW`, `IMPLEMENTATION_REVIEW`, `POST_REVIEW`

Each review stage iterates up to 4 times:
1. Work agent produces output
2. Review agent evaluates
3. If rejected: feedback incorporated, repeat
4. If approved: advance to next stage
5. After 4 rejections: stop with failure report

---

## Configuration

### teambot.json

```json
{
  "teambot_dir": ".teambot",
  "default_agent": "pm",
  "agents": [
    {
      "id": "pm",
      "persona": "project_manager",
      "display_name": "Project Manager"
    },
    {
      "id": "builder-1",
      "persona": "builder",
      "display_name": "Builder (Primary)"
    },
    {
      "id": "builder-2",
      "persona": "builder",
      "display_name": "Builder (Secondary)"
    }
  ]
}
```

### Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `teambot_dir` | string | No | Directory for TeamBot workspace (default: `.teambot`) |
| `default_agent` | string | No | Default agent for plain text input in interactive mode |
| `agents` | array | Yes | List of agent configurations |

### Default Agent

When `default_agent` is configured, plain text input without `@agent` or `/command` prefixes is automatically routed to the specified agent. This provides a more natural interaction model for frequent use of a primary agent.

**Example:**
```json
{
  "default_agent": "pm",
  "agents": [...]
}
```

With this configuration:
- `Create a project plan` → routes to `@pm`
- `@ba Analyze requirements` → routes to `@ba` (explicit override)
- `/help` → system command (not affected)

If `default_agent` is not set (default behavior), plain text shows a helpful tip message.

### Agent Configuration

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique agent identifier |
| `persona` | string | Persona type |
| `display_name` | string | Human-readable name for UI |

---

## Objective File Format

### Basic Format

```markdown
# Objective: Build User Dashboard

## Goals
1. Create user profile page
2. Add settings management
3. Implement notification preferences

## Success Criteria
- [ ] Profile page displays user information
- [ ] Users can edit their profile
- [ ] Notification settings are persisted

## Constraints
- Must work with existing authentication
- Use existing UI component library

## Context
The application uses React for frontend and Express for backend.
```

### Schema

| Section | Required | Description |
|---------|----------|-------------|
| `# Objective:` | Yes | Title/goal of the work |
| `## Goals` | Yes | Numbered list of goals |
| `## Success Criteria` | Yes | Checklist with `- [ ]` items |
| `## Constraints` | No | Technical or business constraints |
| `## Context` | No | Additional context for agents |

### SDD Template

For complex features, use the Spec-Driven Development template:

```bash
cp docs/sdd-objective-template.md objectives/my-feature.md
```

---

## Shared Workspace

All agents share the `.teambot/` directory:

```
.teambot/
├── orchestration_state.json  # Current execution state
├── workflow_state.json       # Workflow progress
├── history/                  # Agent action history
│   └── *.md                  # Timestamped history files
├── failures/                 # Review failure reports
│   └── *.md                  # Detailed failure analysis
└── artifacts/                # Generated artifacts
    ├── spec.md
    ├── plan.md
    └── test-strategy.md
```

### History Files

Each agent action creates a history file with YAML frontmatter:

```markdown
---
title: Implemented user authentication
timestamp: 2026-01-22T08:30:00
agent_id: builder-1
action_type: task-complete
files_affected:
  - src/auth/login.py
---

## Task
Implement user authentication module.

## Output
Created login endpoint with JWT generation.
```

---

## Development

### Setup

```bash
# Install all dependencies
uv sync --group dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/teambot --cov-report=term-missing

# Lint and format
uv run ruff check .
uv run ruff format .
```

### Project Structure

```
teambot/
├── src/teambot/
│   ├── cli.py                # CLI entry point
│   ├── orchestrator.py       # Agent lifecycle management
│   ├── orchestration/        # File-based orchestration
│   │   ├── objective_parser.py
│   │   ├── execution_loop.py
│   │   ├── review_iterator.py
│   │   ├── parallel_executor.py
│   │   └── time_manager.py
│   ├── config/               # Configuration loading
│   ├── copilot/              # Copilot CLI wrapper
│   ├── history/              # History file management
│   ├── messaging/            # Inter-agent messaging
│   ├── prompts/              # Persona templates
│   ├── ui/                   # Split-pane interface
│   └── workflow/             # Workflow state machine
├── tests/                    # Test suite (650 tests)
└── docs/                     # Documentation
```

### Test Coverage

Current: **83% coverage** with **650 tests**

| Module | Coverage |
|--------|----------|
| `orchestration/objective_parser.py` | 100% |
| `orchestration/time_manager.py` | 100% |
| `orchestration/review_iterator.py` | 95% |
| `orchestration/execution_loop.py` | 94% |
| `orchestration/parallel_executor.py` | 92% |
| `workflow/stages.py` | 100% |
| `workflow/state_machine.py` | 96% |

---

## Troubleshooting

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

## Dependencies

### Runtime

| Package | Purpose |
|---------|---------|
| `github-copilot-sdk` | GitHub Copilot SDK for AI agent execution |
| `python-frontmatter` | YAML frontmatter parsing |
| `rich` | Console UI and formatting |
| `textual` | Split-pane terminal interface |

### External

| Tool | Purpose |
|------|---------|
| [uv](https://github.com/astral-sh/uv) | Package management |
| [GitHub CLI](https://cli.github.com/) | Authentication (optional, SDK handles auth) |

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `uv run pytest` and `uv run ruff check .`
5. Open a Pull Request

---

<p align="center">
  Made with 🤖 by TeamBot
</p>
