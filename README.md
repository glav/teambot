# TeamBot

**Autonomous AI Agent Teams for Software Development**

TeamBot is a CLI tool that wraps the [GitHub Copilot CLI](https://githubnext.com/projects/copilot-cli/) to enable collaborative, multi-agent AI workflows. Instead of single-threaded AI interactions, TeamBot orchestrates a team of specialized AI agents that work together autonomously to achieve development objectives.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-192%20passing-green.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-88%25-green.svg)]()

## Features

- 🤖 **Multi-Agent Orchestration** - 6 specialized agent personas working in parallel or sequentially
- 📋 **Prescriptive Workflow** - 13-stage workflow from Setup to Post-Implementation Review
- 🔄 **Autonomous Operation** - Define objectives in markdown, let the team execute
- 📁 **Shared Context** - Agents collaborate via `.teambot/` directory with history files
- 🎨 **Rich Console UI** - Colorful status display with progress tracking
- 💾 **State Persistence** - Resume workflows across restarts

---

## Table of Contents

- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [Agent Personas](#agent-personas)
- [Prescriptive Workflow](#prescriptive-workflow)
- [Configuration](#configuration)
- [Objective Files](#objective-files)
- [Shared Workspace](#shared-workspace)
- [Inter-Agent Communication](#inter-agent-communication)
- [Dependencies](#dependencies)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- [GitHub Copilot CLI](https://githubnext.com/projects/copilot-cli/) (the standalone `copilot` command)

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

**Output:**
```
✓ Created configuration: teambot.json
✓ Created directory: .teambot
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Agent               ┃ Persona          ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Project Manager     │ project_manager  │ idle   │
│ Business Analyst    │ business_analyst │ idle   │
│ Technical Writer    │ technical_writer │ idle   │
│ Builder (Primary)   │ builder          │ idle   │
│ Builder (Secondary) │ builder          │ idle   │
│ Reviewer            │ reviewer         │ idle   │
└─────────────────────┴──────────────────┴────────┘
```

### Run TeamBot

```bash
# Interactive mode (no objective file)
uv run teambot run

# With an objective file
uv run teambot run objectives/build-chatbot.md

# Check status
uv run teambot status
```

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

**Creates:**
- `teambot.json` - Agent and workflow configuration
- `.teambot/` - Shared workspace directory

### `teambot run`

Run TeamBot with an optional objective file.

```bash
teambot run [objective] [-c CONFIG]
```

| Option | Description |
|--------|-------------|
| `objective` | Path to objective markdown file (optional) |
| `-c, --config` | Configuration file path (default: `teambot.json`) |

**Examples:**
```bash
# Interactive mode
teambot run

# With objective
teambot run today.md

# Custom config
teambot run -c custom-team.json objectives/feature.md
```

### `teambot status`

Display current TeamBot status including agents and workflow progress.

```bash
teambot status
```

**Output:**
```
╭──────────────────────────────────────────────────╮
│ TeamBot Status                                   │
╰──────────────────────────────────────────────────╯
✓ History files: 5
✓ Configuration: teambot.json
✓ Current stage: IMPLEMENTATION
✓ Progress: 58.3%
```

### Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version number |
| `-v, --verbose` | Enable verbose/debug output |

---

## Agent Personas

TeamBot includes 6 specialized agent personas, each with distinct roles and capabilities:

| Agent | Persona | Role | Parallel |
|-------|---------|------|----------|
| `pm` | Project Manager | Planning, coordination, task assignment | No |
| `ba` | Business Analyst | Requirements, problem definition, specs | No |
| `writer` | Technical Writer | Documentation, guides, API docs | No |
| `builder-1` | Builder (Primary) | Implementation, coding, testing | Yes |
| `builder-2` | Builder (Secondary) | Implementation, coding, testing | Yes |
| `reviewer` | Reviewer | Code review, quality assurance | No |

### Persona Details

#### Project Manager (`project_manager`, `pm`)

**Capabilities:**
- Create and maintain project plans
- Break down features into tasks
- Assign tasks to appropriate team members
- Track progress and identify blockers
- Coordinate between team members

**Constraints:**
- Does NOT implement code directly - delegates to builders
- Focus on planning and coordination
- Ensure all work has clear acceptance criteria

#### Business Analyst (`business_analyst`, `ba`)

**Capabilities:**
- Gather and document requirements
- Define business problems clearly
- Create user stories and acceptance criteria
- Validate solutions against requirements

**Constraints:**
- Focus on the "what" not the "how"
- Ensure requirements are testable
- Document assumptions and dependencies

#### Technical Writer (`technical_writer`, `writer`)

**Capabilities:**
- Write clear technical documentation
- Create API documentation
- Write user guides and tutorials
- Document architecture decisions

**Constraints:**
- Use clear, concise language
- Include code examples where appropriate
- Keep documentation up to date

#### Builder (`builder`, `developer`)

**Capabilities:**
- Write clean, maintainable code
- Implement features according to specifications
- Write unit and integration tests
- Debug and fix issues

**Constraints:**
- Follow project coding standards
- Write tests for new functionality
- Create history files for all changes

#### Reviewer (`reviewer`)

**Capabilities:**
- Review code for quality and correctness
- Review documentation for accuracy
- Identify bugs, security issues, and improvements
- Verify adherence to standards

**Constraints:**
- Be thorough but constructive
- Focus on significant issues, not style nitpicks
- Explain reasoning behind feedback

---

## Prescriptive Workflow

TeamBot enforces a 13-stage workflow to ensure quality and determinism:

```
┌─────────┐    ┌──────────────────┐    ┌──────┐    ┌─────────────┐
│  SETUP  │───▶│ BUSINESS_PROBLEM │───▶│ SPEC │───▶│ SPEC_REVIEW │
└─────────┘    └──────────────────┘    └──────┘    └─────────────┘
                    (optional)                            │
                                                          ▼
┌─────────────┐    ┌───────────────┐    ┌──────┐    ┌──────────┐
│ PLAN_REVIEW │◀───│     PLAN      │◀───│ TEST │◀───│ RESEARCH │
└─────────────┘    └───────────────┘    │STRAT │    └──────────┘
       │                                └──────┘
       ▼
┌────────────────┐    ┌─────────────────────┐    ┌──────┐
│ IMPLEMENTATION │───▶│ IMPLEMENTATION_     │───▶│ TEST │
└────────────────┘    │ REVIEW              │    └──────┘
                      └─────────────────────┘         │
                                                      ▼
                      ┌──────────┐    ┌───────────────┐
                      │ COMPLETE │◀───│  POST_REVIEW  │
                      └──────────┘    └───────────────┘
```

### Stage Details

| Stage | Description | Allowed Personas | Optional |
|-------|-------------|------------------|----------|
| `SETUP` | Initialize project and configuration | PM | No |
| `BUSINESS_PROBLEM` | Define business problem and goals | BA, PM | **Yes** |
| `SPEC` | Create feature specification | BA, Writer | No |
| `SPEC_REVIEW` | Review and approve spec | Reviewer, PM | No |
| `RESEARCH` | Research technical approaches | Builder, Writer | No |
| `TEST_STRATEGY` | Define testing approach | Builder, Reviewer | No |
| `PLAN` | Create implementation plan | PM, Builder | No |
| `PLAN_REVIEW` | Review and approve plan | Reviewer, PM | No |
| `IMPLEMENTATION` | Execute the plan | Builder | No |
| `IMPLEMENTATION_REVIEW` | Review changes | Reviewer | No |
| `TEST` | Execute tests and validate | Builder, Reviewer | No |
| `POST_REVIEW` | Final review and retrospective | PM, Reviewer | No |
| `COMPLETE` | Workflow complete | - | No |

### Workflow State Persistence

Workflow state is persisted to `.teambot/workflow_state.json`:

```json
{
  "current_stage": "IMPLEMENTATION",
  "started_at": "2026-01-22T08:00:00",
  "objective": "Build chatbot SPA",
  "history": [
    {
      "stage": "SETUP",
      "started_at": "2026-01-22T08:00:00",
      "completed_at": "2026-01-22T08:05:00",
      "artifacts": ["teambot.json"]
    }
  ]
}
```

---

## Configuration

### teambot.json

The configuration file defines agents and workflow settings:

```json
{
  "teambot_dir": ".teambot",
  "agents": [
    {
      "id": "pm",
      "persona": "project_manager",
      "display_name": "Project Manager",
      "parallel_capable": false,
      "workflow_stages": ["setup", "planning", "coordination"]
    },
    {
      "id": "builder-1",
      "persona": "builder",
      "display_name": "Builder (Primary)",
      "parallel_capable": true,
      "workflow_stages": ["implementation", "testing"]
    },
    {
      "id": "builder-2",
      "persona": "builder",
      "display_name": "Builder (Secondary)",
      "parallel_capable": true,
      "workflow_stages": ["implementation", "testing"]
    }
  ],
  "workflow": {
    "stages": [
      "setup",
      "business_problem",
      "spec",
      "review",
      "research",
      "test_strategy",
      "plan",
      "implementation",
      "test",
      "post_review"
    ],
    "parallel_stages": ["implementation"]
  }
}
```

### Agent Configuration Options

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique agent identifier |
| `persona` | string | Persona type (`project_manager`, `business_analyst`, `technical_writer`, `builder`, `reviewer`) |
| `display_name` | string | Human-readable name for UI display |
| `parallel_capable` | boolean | Whether agent can run in parallel with others |
| `workflow_stages` | array | Stages this agent participates in |

### Copilot CLI Configuration

The Copilot CLI client can be configured with:

| Setting | Default | Description |
|---------|---------|-------------|
| `allow_all_tools` | `true` | Enable all tools for autonomous operation |
| `allow_all_paths` | `false` | Allow access to any file path |
| `additional_dirs` | `[]` | Extra directories to allow access |
| `model` | `null` | Specific model to use (e.g., `gpt-5`) |
| `timeout` | `300` | Execution timeout in seconds |

---

## Objective Files

Define your day's work in a markdown file:

```markdown
# Objective: Build Chatbot SPA

## Description
Build a basic chatbot single-page application that integrates 
with a FastAPI backend.

## Definition of Done
- [ ] Frontend SPA with React
- [ ] FastAPI backend with /chat endpoint
- [ ] WebSocket support for real-time messages
- [ ] Basic conversation history

## Success Criteria
- User can send messages and receive responses
- Conversation persists during session
- Response time < 2 seconds

## Implementation Specifics
- Use React 18 with TypeScript
- FastAPI with Python 3.12
- SQLite for development database
```

### Objective Schema

| Section | Required | Description |
|---------|----------|-------------|
| `Description` | Yes | What you're building |
| `Definition of Done` | Yes | Checklist of deliverables |
| `Success Criteria` | Yes | How to measure success |
| `Implementation Specifics` | No | Technical constraints/preferences |

---

## Shared Workspace

All agents share the `.teambot/` directory for collaboration:

```
.teambot/
├── workflow_state.json     # Current workflow state
├── history/                # Agent action history
│   ├── 2026-01-22-083000-task-complete.md
│   ├── 2026-01-22-084500-review-complete.md
│   └── 2026-01-22-090000-spec-created.md
└── artifacts/              # Generated artifacts
    ├── spec.md
    ├── plan.md
    └── test-strategy.md
```

### History Files

Each agent action creates a history file with YAML frontmatter:

```markdown
---
title: Implemented user authentication
description: Builder-1 completed auth module implementation
timestamp: 2026-01-22T08:30:00
agent_id: builder-1
action_type: task-complete
files_affected:
  - src/auth/login.py
  - tests/test_auth.py
---

## Task
Implement user authentication module with JWT tokens.

## Output
Created login endpoint with password hashing and JWT generation.

### Files Created
- `src/auth/login.py` - Login endpoint with JWT generation
- `src/auth/hash.py` - Password hashing utilities

### Tests Added
- `tests/test_auth.py` - 12 tests for auth module
```

### History File Naming

Files are named with timestamp and action type:
```
YYYY-MM-DD-HHMMSS-<action-type>.md
```

Examples:
- `2026-01-22-083000-task-complete.md`
- `2026-01-22-090000-spec-created.md`
- `2026-01-22-100000-review-approved.md`

### Context Management

Agents automatically load relevant history based on frontmatter metadata. When files approach context limits (80% of 150k tokens), TeamBot offers compaction options:

| Level | Description |
|-------|-------------|
| **Little** | Light summarization, preserves most detail |
| **Medium** | Moderate compression, keeps key information |
| **High** | Aggressive summarization, essentials only |

---

## Inter-Agent Communication

Agents communicate via multiprocessing queues managed by the orchestrator:

```
┌─────────────┐
│ Orchestrator│
│  (Parent)   │
└──────┬──────┘
       │
   ┌───┴───┐
   │ Main  │
   │ Queue │
   └───┬───┘
       │
┌──────┼──────┬──────┬──────┬──────┐
│      │      │      │      │      │
▼      ▼      ▼      ▼      ▼      ▼
┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐
│PM│  │BA│  │WR│  │B1│  │B2│  │RV│
└──┘  └──┘  └──┘  └──┘  └──┘  └──┘
```

### Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `TASK_ASSIGN` | Orchestrator → Agent | Assign task to an agent |
| `TASK_COMPLETE` | Agent → Orchestrator | Agent completed task |
| `TASK_FAILED` | Agent → Orchestrator | Agent failed task |
| `STATUS_UPDATE` | Agent → Orchestrator | Agent status change |
| `CONTEXT_SHARE` | Agent → Agent | Share context between agents |
| `SHUTDOWN` | Orchestrator → All | Graceful shutdown signal |

### Session Isolation

By default, each agent operates in an isolated session:
- Separate Copilot CLI invocation per agent
- No shared context unless explicitly configured
- Independent working memory

To share context explicitly, agents write to `.teambot/` and other agents read the history files based on frontmatter relevance.

---

## Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `python-frontmatter` | ≥1.0.0 | YAML frontmatter parsing for history files |
| `rich` | ≥13.0.0 | Console UI, tables, colors, and progress bars |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | ≥7.4.0 | Testing framework |
| `pytest-cov` | ≥4.1.0 | Coverage reporting |
| `pytest-mock` | ≥3.12.0 | Mocking utilities |
| `ruff` | ≥0.4.0 | Linting and formatting |

### External Dependencies

| Tool | Required | Purpose |
|------|----------|---------|
| [GitHub Copilot CLI](https://githubnext.com/projects/copilot-cli/) | Yes | AI task execution (`copilot` command) |
| [uv](https://github.com/astral-sh/uv) | Yes | Python package management |

### Installing External Dependencies

**uv (package manager):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**GitHub Copilot CLI:**
Follow instructions at https://githubnext.com/projects/copilot-cli/

---

## Development

### Setup Development Environment

```bash
# Install all dependencies including dev
uv sync --group dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/teambot --cov-report=term-missing

# Lint and format
uv run ruff check .
uv run ruff format .
```

### Project Structure

```
teambot/
├── src/teambot/
│   ├── __init__.py           # Package version (0.1.0)
│   ├── cli.py                # CLI entry point (init/run/status)
│   ├── orchestrator.py       # Agent lifecycle management
│   ├── agent_runner.py       # Individual agent process
│   ├── window_manager.py     # Cross-platform window spawning
│   ├── config/
│   │   ├── loader.py         # JSON config loading
│   │   └── schema.py         # Config validation
│   ├── copilot/
│   │   └── client.py         # Copilot CLI wrapper
│   ├── history/
│   │   ├── frontmatter.py    # YAML frontmatter parsing
│   │   ├── manager.py        # History file management
│   │   └── compactor.py      # Context compaction
│   ├── messaging/
│   │   ├── protocol.py       # Message types and format
│   │   └── router.py         # Message routing
│   ├── prompts/
│   │   └── templates.py      # Persona prompt templates
│   ├── visualization/
│   │   └── console.py        # Rich console display
│   └── workflow/
│       ├── stages.py         # Workflow stage enum
│       └── state_machine.py  # Workflow state management
├── tests/                    # Test suite (192 tests)
│   ├── test_cli.py
│   ├── test_orchestrator.py
│   ├── test_agent_runner.py
│   ├── test_copilot/
│   ├── test_workflow/
│   └── ...
├── docs/
│   └── feature-specs/
│       └── teambot.md        # Feature specification
├── .agent-tracking/          # SDD workflow artifacts
├── teambot.json              # Default configuration
├── pyproject.toml            # Project metadata
└── README.md                 # This file
```

### Running Tests

```bash
# All tests
uv run pytest

# Specific module
uv run pytest tests/test_workflow/

# Specific test
uv run pytest tests/test_cli.py::test_init_command

# With verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x

# With coverage report
uv run pytest --cov=src/teambot --cov-report=html
```

### Test Coverage

Current coverage: **88%** with **192 tests**

| Module | Coverage |
|--------|----------|
| `workflow/stages.py` | 100% |
| `workflow/state_machine.py` | 96% |
| `prompts/templates.py` | 100% |
| `history/manager.py` | 100% |
| `messaging/router.py` | 100% |
| `config/loader.py` | 96% |

---

## Troubleshooting

### Copilot CLI Not Found

```
Error: Copilot CLI not found in PATH
```

**Solution:** Install the GitHub Copilot CLI:
```bash
# Follow instructions at https://githubnext.com/projects/copilot-cli/
# Verify installation:
copilot --version
```

### Configuration Already Exists

```
Error: Configuration already exists: teambot.json
```

**Solution:** Use `--force` to overwrite:
```bash
teambot init --force
```

### Agent Persona Not Allowed

```
Error: Agent 'builder-1' (persona: builder) is not allowed in stage SETUP
```

**Cause:** The current workflow stage doesn't permit this persona to work.

**Solution:** Check which personas are allowed:
```bash
teambot status
```

Or advance the workflow to an appropriate stage.

### Workflow State Corrupted

If `.teambot/workflow_state.json` becomes corrupted:

```bash
# Remove corrupted state (will restart workflow)
rm .teambot/workflow_state.json

# Re-run
teambot run
```

### Task Execution Timeout

```
Error: Timeout after 300 seconds
```

**Solution:** Increase the timeout in your code or break the task into smaller pieces.

### Permission Denied on Files

```
Error: Permission denied: /some/path
```

**Solution:** Add the directory to allowed paths in the Copilot client configuration or use `--allow-all-paths` flag.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                         TeamBot CLI                         │
│                     (teambot command)                       │
└─────────────────────────┬──────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────┐
│                      Orchestrator                           │
│  • Agent lifecycle management                               │
│  • Workflow state machine                                   │
│  • Message routing                                          │
└─────────────────────────┬──────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
│  AgentRunner  │ │  AgentRunner  │ │  AgentRunner  │
│     (PM)      │ │  (Builder-1)  │ │  (Reviewer)   │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
│ CopilotClient │ │ CopilotClient │ │ CopilotClient │
│               │ │               │ │               │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  Copilot CLI  │
                  │  (copilot -p) │
                  └───────────────┘
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with tests
4. Run tests and linting:
   ```bash
   uv run pytest
   uv run ruff check .
   ```
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Acknowledgments

- Built on [GitHub Copilot CLI](https://githubnext.com/projects/copilot-cli/)
- Uses [Rich](https://github.com/Textualize/rich) for beautiful console output
- Package management by [uv](https://github.com/astral-sh/uv)
- Developed using the Spec-Driven Development (SDD) workflow

---

<p align="center">
  Made with 🤖 by TeamBot
</p>
