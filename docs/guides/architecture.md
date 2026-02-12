# Architecture

This guide describes TeamBot's internal architecture for contributors and advanced users.

## System Overview

TeamBot has two primary execution modes, each with a distinct component stack:

```
┌──────────────────────────────────────────────────────┐
│                    CLI (cli.py)                       │
│              init / run / status                      │
└──────────┬─────────────────────┬─────────────────────┘
           │                     │
     Objective file         No objective
           │                     │
           ▼                     ▼
┌─────────────────────┐  ┌─────────────────────┐
│  File-Based Mode    │  │  Interactive Mode    │
│  (ExecutionLoop)    │  │  (REPLLoop)          │
│                     │  │                      │
│  14-stage workflow   │  │  Ad-hoc tasks,      │
│  Autonomous agents  │  │  pipelines, multi-   │
│  Review iterations  │  │  agent commands      │
└────────┬────────────┘  └─────────┬────────────┘
         │                         │
         ▼                         ▼
┌──────────────────────────────────────────────────────┐
│              Copilot SDK Client                       │
│       Session management, streaming, personas         │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│              GitHub Copilot SDK                       │
└──────────────────────────────────────────────────────┘
```

## Core Components

### CLI Entry Point (`cli.py`)

The CLI provides three commands:

| Command | Description |
|---------|-------------|
| `teambot init` | Initialize `.teambot/` workspace |
| `teambot run [objective]` | Start file-based or interactive mode |
| `teambot status` | Show workflow state and agent status |

When an objective file is provided, `cmd_run()` launches the **ExecutionLoop**. Otherwise, it starts the **REPLLoop**.

### Copilot SDK Client (`copilot/sdk_client.py`)

The central integration point with GitHub Copilot. Wraps the SDK with:

- **Session caching** — one session per agent, reused across tasks
- **Streaming execution** — event-based callbacks (`on_chunk`) for real-time output
- **Blocking execution** — single-response mode with retry on session expiry
- **Persona injection** — agent persona prompts prepended to every request
- **Model routing** — per-agent model overrides (configured in `teambot.json`)

```
execute_streaming(agent_id, prompt, on_chunk)
  → get_or_create_session(agent_id, model)
  → SDK.ask(prompt)
  → on_event(ASSISTANT_MESSAGE_DELTA) → on_chunk(text)
  → on_event(SESSION_IDLE) → return full response
```

### Agent Loader (`copilot/agent_loader.py`)

Loads custom agent definitions from `.github/agents/*.agent.md` files. Each file contains YAML frontmatter (name, description, tools) and a markdown prompt body. Agent IDs support alias fallback (e.g., `builder-1` → `builder`).

## File-Based Orchestration

### Execution Loop (`orchestration/execution_loop.py`)

Drives the 14-stage workflow autonomously:

```
for each stage in stage_order:
    if stage.is_review_stage:
        ReviewIterator.execute(work_agent, review_agent)
    elif stage.is_acceptance_test_stage:
        AcceptanceTestExecutor.execute_all()
    else:
        execute_work_stage(work_agent, prompt)
    
    advance to next stage
```

**Key behaviors:**
- Reads stage configuration from `stages.yaml`
- Injects objective content and prior artifacts into prompts
- Saves state on completion, cancellation (`Ctrl+C`), or timeout
- Supports resume via `--resume` flag

### Review Iterator (`orchestration/review_iterator.py`)

Manages the review loop for stages marked `is_review_stage: true`:

1. **Work agent** produces or revises output
2. **Review agent** evaluates and approves or rejects
3. If rejected, feedback is incorporated and the cycle repeats
4. After **4 failed iterations**, execution stops with a failure report

### Acceptance Test Executor (`orchestration/acceptance_test_executor.py`)

Parses acceptance test scenarios from the feature specification (sections matching `## Acceptance Test Scenarios` with structured `AT-XXX` entries). Prompts the builder agent to write and run pytest tests for each scenario. Results gate the `POST_REVIEW` stage — the workflow **cannot complete** if acceptance tests fail.

Supports **expected-error scenarios**: when a scenario's expected result describes an error (e.g., "error message listing valid agents"), command failures are treated as correct behavior rather than test failures. Error indicators include phrases like "error message", "rejected", and "unknown agent".

### Parallel Executor (`orchestration/parallel_executor.py`)

During the `IMPLEMENTATION` stage, `builder-1` and `builder-2` execute concurrently. Tasks are split from the implementation plan and assigned to parallel agents via `asyncio.gather()`.

### Parallel Stage Executor (`orchestration/parallel_stage_executor.py`)

Executes entire workflow stages concurrently when configured in `parallel_groups` (e.g., `RESEARCH` and `TEST_STRATEGY` run in parallel after `SPEC_REVIEW`). Each parallel stage must use a **different work_agent** — sharing the same agent across parallel stages causes SDK session conflicts and is rejected at startup.

### Time Manager (`orchestration/time_manager.py`)

Enforces a wall-clock time limit (default: 8 hours, configurable via `--max-hours`). Triggers graceful shutdown when the limit is reached.

## Interactive Mode

### REPL Loop (`repl/loop.py`)

The interactive read-eval-print loop:

```
User Input → Parser → Router/Executor → SDK Client → Output
                                              ↓
                                     Status Overlay Updates
```

**Features:**
- Rich console output with formatted agent responses
- Signal handling for graceful shutdown (`Ctrl+C`)
- Persistent status overlay showing running tasks

### Command Parser (`repl/parser.py`)

Parses user input into structured commands:

| Syntax | Meaning | Example |
|--------|---------|---------|
| `@agent prompt` | Direct agent task | `@builder-1 add login endpoint` |
| `prompt` | Default agent task | `fix the bug in auth.py` |
| `a -> b` | Pipeline (sequential) | `@ba write spec -> @reviewer review` |
| `a, b` | Multi-agent (parallel) | `@builder-1, @builder-2 implement auth` |
| `$agent` | Reference prior output | `@reviewer review $builder-1` |
| `command &` | Background execution | `@builder-1 refactor utils &` |
| `/command` | System command | `/status`, `/help`, `/models` |

### Task Executor (`tasks/executor.py`)

Bridges parsed commands to parallel task execution:

- **Simple tasks** — single agent via `AgentRouter`
- **Multi-agent** — fan-out to multiple agents via `asyncio.gather()`
- **Pipelines** — sequential stages with output injection between steps
- **Background** — stored in a background task registry for later retrieval

### Task Manager & Graph (`tasks/manager.py`, `tasks/graph.py`)

Manages concurrent task execution with:
- Semaphore-based concurrency control (default: 3 max concurrent tasks)
- DAG-based dependency tracking between pipeline stages
- Status tracking per task (pending → running → complete/failed)

## Multiprocessing Architecture

When running in orchestrated mode, TeamBot uses Python multiprocessing:

```
┌─────────────────────────────────────┐
│           Main Process              │
│                                     │
│  Orchestrator                       │
│    ├── MessageRouter                │
│    ├── WorkflowStateMachine         │
│    └── Agent Queues                 │
└────┬──────────┬──────────┬──────────┘
     │          │          │
     ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Agent   │ │ Agent   │ │ Agent   │
│ Process │ │ Process │ │ Process │
│ (pm)    │ │(bldr-1) │ │(review) │
│         │ │         │ │         │
│ Runner  │ │ Runner  │ │ Runner  │
│ Copilot │ │ Copilot │ │ Copilot │
│ History │ │ History │ │ History │
└─────────┘ └─────────┘ └─────────┘
```

### Message Protocol (`messaging/protocol.py`)

All inter-agent communication uses `AgentMessage`:

| Field | Type | Description |
|-------|------|-------------|
| `type` | `MessageType` | TASK_ASSIGN, TASK_COMPLETE, TASK_FAILED, STATUS_UPDATE, CONTEXT_SHARE, SHUTDOWN |
| `source_agent` | `str` | Sending agent ID |
| `target_agent` | `str` | Receiving agent ID (or `"all"` for broadcast) |
| `payload` | `dict` | Message-type-specific data |
| `correlation_id` | `str` | For tracing related messages |
| `timestamp` | `float` | Creation time |

### Message Router (`messaging/router.py`)

Routes messages between agent processes via registered queues:
- **Point-to-point** — message delivered to one agent's queue
- **Broadcast** — `target_agent="all"` sends to every registered queue

### Agent Runner (`agent_runner.py`)

Each agent process runs an `AgentRunner` with a blocking message loop:

```python
while self.running:
    message = self.agent_queue.get(timeout=1.0)
    match message.type:
        case TASK_ASSIGN:  self._execute_task(message.payload)
        case SHUTDOWN:     self.running = False
        case CONTEXT_SHARE: self._update_context(message.payload)
```

Task execution calls the Copilot SDK client and reports results back via the main queue.

## Workflow State Machine (`workflow/state_machine.py`)

Enforces valid stage transitions and persona access:

- **Stage order** — defined in `stages.yaml`, loaded at startup
- **Persona validation** — only allowed personas can act in each stage
- **Transition rules** — stages progress forward; no backward jumps
- **State persistence** — serialized to `.teambot/orchestration_state.json`

## UI Layer

### Split-Pane Interface (`ui/app.py`)

Textual-based terminal interface with:
- **Input pane** (left) — command entry
- **Output pane** (right) — agent response streaming
- **Status panel** — agent state and model assignments
- Falls back to single-pane mode if terminal < 80 columns

### Status Overlay (`visualization/overlay.py`)

Persistent overlay showing real-time agent status during execution. Renders agent states (idle, working, reviewing) with progress indicators.

### Agent State Manager (`ui/agent_state.py`)

Tracks per-agent status, model assignments, and activity. Provides the data model for status panel and overlay rendering.

## Configuration

### `teambot.json`

Project-level configuration:
- `teambot_dir` — workspace directory (default: `.teambot`)
- `default_model` — fallback model for all agents
- `agents[]` — per-agent config (id, persona, model, parallel capability)

### `stages.yaml`

Workflow stage definitions:
- Stage order, descriptions, and exit criteria
- Agent assignments (`work_agent`, `review_agent`)
- Review/acceptance test flags
- Parallel stage groups (stages in a group must use different `work_agent` values)
- Artifact output paths
- SDD prompt template paths

See [Configuration Guide](configuration.md) for full details.

## History Management (`history/`)

All agent interactions are logged as timestamped markdown files with YAML frontmatter:

```
.teambot/{feature}/history/
  2025-01-15T10-30-00_pm_setup.md
  2025-01-15T10-35-00_ba_spec.md
  ...
```

Each file contains the agent ID, stage, prompt, and response. The `HistoryManager` handles creation, retrieval, and ordering. A `ContextCompactor` can reduce history size for long-running executions.

---

## Next Steps

- [Configuration](configuration.md) - Customizing TeamBot behavior
- [Workflow Stages](workflow-stages.md) - The 14-stage workflow
- [Development](development.md) - Contributing to TeamBot
