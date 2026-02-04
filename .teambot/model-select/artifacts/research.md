<!-- markdownlint-disable-file -->
# Research Document: Model Selection Feature

**Date**: 2026-02-04  
**Feature**: Model Selection for TeamBot Agents  
**Status**: ✅ Research Complete

---

## 1. Research Scope

### 1.1 Objective

Enable TeamBot to support model selection for individual agents, allowing:
- Per-agent default model configuration in `teambot.json`
- Runtime model selection via user input
- Model visibility in terminal UI and status displays
- Listing available models from Copilot CLI

### 1.2 Success Criteria

| Criterion | Status |
|-----------|--------|
| Model visible in terminal UI and `/status` command | 📋 Researched |
| Model visible in `/tasks` command output | 📋 Researched |
| Inline model selection via user input | 📋 Researched |
| Session-level model override for agents | 📋 Researched |
| Configuration support for default model per agent | 📋 Researched |
| Error handling for invalid models | 📋 Researched |

### 1.3 Key Assumptions

- Only models supported by GitHub Copilot CLI/SDK are valid
- Model selection does not require authentication changes
- UI changes should be minimal and non-breaking

---

## 2. Entry Point Analysis

### 2.1 User Input Entry Points

| Entry Point | Code Path | Implementation Required? |
|-------------|-----------|-------------------------|
| `@pm task` (simple) | `loop.py → parser.py → router.py → app.py → sdk_client.py` | ✅ YES |
| `@pm task &` (background) | `loop.py → parser.py → executor.py → manager.py → sdk_client.py` | ✅ YES |
| `@pm,@ba task` (multi-agent) | `loop.py → parser.py → executor.py → sdk_client.py` | ✅ YES |
| `@pm -> @ba` (pipeline) | `loop.py → parser.py → executor.py → sdk_client.py` | ✅ YES |
| File-based orchestration | `cli.py → execution_loop.py → sdk_client.py` | ✅ YES |
| `/status` command | `commands.py → agent_state.py → status_panel.py` | ✅ YES |
| `/tasks` command | `commands.py → executor.py → models.py` | ✅ YES |

### 2.2 Code Path Trace

#### Entry Point 1: Interactive REPL Single Agent Command (`@pm task`)

1. User enters: `@pm Create a project plan`
2. Handled by: `repl/loop.py:REPLLoop._get_input()` (Lines 314-330)
3. Parsed by: `repl/parser.py:parse_command()` (Lines 88-115)
4. Routed through: `ui/app.py:TeamBotApp.handle_input()` (Lines 71-112)
5. Executed by: `copilot/sdk_client.py:CopilotSDKClient.execute_streaming()` (Lines 227-338)
6. **Model injection point**: `sdk_client.py` session creation (Lines 138-161)

#### Entry Point 2: File-Based Orchestration

1. User runs: `teambot run objectives/task.md`
2. Handled by: `cli.py:cmd_run()` (Lines 98-156)
3. Creates: `orchestration/execution_loop.py:ExecutionLoop` (Lines 84-99)
4. Executes via: `copilot/sdk_client.py:CopilotSDKClient.execute()` (Lines 190-225)
5. **Model injection point**: Same as above, plus config loading

### 2.3 Coverage Verification

- [x] All interactive REPL paths traced
- [x] File-based orchestration path traced
- [x] Background/async execution traced
- [x] UI display components identified

---

## 3. Technical Findings

### 3.1 Copilot CLI Model Support

The Copilot CLI provides built-in model selection via `--model` flag:

```bash
copilot --model <model>
```

**Available Models** (from `copilot --help`):
| Model ID | Description |
|----------|-------------|
| `claude-sonnet-4.5` | Claude Sonnet 4.5 |
| `claude-haiku-4.5` | Claude Haiku 4.5 |
| `claude-opus-4.5` | Claude Opus 4.5 |
| `claude-sonnet-4` | Claude Sonnet 4 |
| `gemini-3-pro-preview` | Gemini 3 Pro (Preview) |
| `gpt-5.2-codex` | GPT-5.2-Codex |
| `gpt-5.2` | GPT-5.2 |
| `gpt-5.1-codex-max` | GPT-5.1-Codex-Max |
| `gpt-5.1-codex` | GPT-5.1-Codex |
| `gpt-5.1` | GPT-5.1 |
| `gpt-5` | GPT-5 |
| `gpt-5.1-codex-mini` | GPT-5.1-Codex-Mini |
| `gpt-5-mini` | GPT-5 mini |
| `gpt-4.1` | GPT-4.1 |

**Source**: `copilot --help` output, verified 2026-02-04

### 3.2 Existing Model Support in Codebase

#### 3.2.1 CopilotClient (CLI wrapper) - Already Supports Model

**File**: `src/teambot/copilot/client.py` (Lines 26-34, 144-145)

```python
@dataclass
class CopilotConfig:
    """Configuration for Copilot CLI invocation."""
    allow_all_tools: bool = True
    allow_all_paths: bool = False
    additional_dirs: list[str] = field(default_factory=list)
    model: str | None = None  # ✅ Already exists!
    timeout: int = 300

# In _build_command() method:
if self.config.model:
    cmd.extend(["--model", self.config.model])
```

✅ **Key Finding**: The CLI wrapper `CopilotClient` already supports model selection via `CopilotConfig.model`. However, this is **NOT** used in the SDK client.

#### 3.2.2 CopilotSDKClient (SDK wrapper) - Does NOT Support Model

**File**: `src/teambot/copilot/sdk_client.py` (Lines 110-161)

```python
async def get_or_create_session(self, agent_id: str) -> Any:
    # ... session creation
    session_config: dict[str, Any] = {
        "session_id": session_id,
        "streaming": True,
    }
    # ❌ No model parameter passed!
```

⚠️ **Gap Identified**: The SDK client does not pass model configuration to session creation.

### 3.3 Configuration System

#### 3.3.1 Current Agent Configuration Schema

**File**: `src/teambot/config/loader.py` (Lines 32-94)

```python
def create_default_config() -> dict[str, Any]:
    return {
        "teambot_dir": ".teambot",
        "agents": [
            {
                "id": "pm",
                "persona": "project_manager",
                "display_name": "Project Manager",
                "parallel_capable": False,
                "workflow_stages": ["setup", "planning", "coordination"],
                # ❌ No model field exists
            },
            # ... other agents
        ],
    }
```

#### 3.3.2 Proposed Configuration Extension

```json
{
  "agents": [
    {
      "id": "pm",
      "persona": "project_manager",
      "display_name": "Project Manager",
      "model": "claude-opus-4.5"  // ✅ New field
    },
    {
      "id": "ba",
      "persona": "business_analyst",
      "display_name": "Business Analyst",
      "model": "gpt-5.2-codex"  // ✅ New field
    }
  ],
  "default_model": "claude-sonnet-4.5"  // ✅ Global default
}
```

### 3.4 UI Components Analysis

#### 3.4.1 Status Panel

**File**: `src/teambot/ui/widgets/status_panel.py` (Lines 101-137)

Current format:
```
Agents
● pm idle
● ba idle
```

Proposed format with model:
```
Agents
● pm idle (opus-4.5)
● ba idle (gpt-5.2)
```

#### 3.4.2 Agent State Manager

**File**: `src/teambot/ui/agent_state.py` (Lines 22-35)

```python
@dataclass
class AgentStatus:
    agent_id: str
    state: AgentState = AgentState.IDLE
    task: str | None = None
    # ❌ No model field
```

**Proposed Extension**:
```python
@dataclass
class AgentStatus:
    agent_id: str
    state: AgentState = AgentState.IDLE
    task: str | None = None
    model: str | None = None  # ✅ Add model field
```

#### 3.4.3 Console Display

**File**: `src/teambot/visualization/console.py` (Lines 80-110)

Current table:
```
| Agent | Persona | Status | Task | Progress |
```

Proposed table:
```
| Agent | Persona | Model | Status | Task | Progress |
```

### 3.5 Task Models

**File**: `src/teambot/tasks/models.py` (Lines 52-79)

```python
@dataclass
class Task:
    id: str
    agent_id: str
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    # ... other fields
    # ❌ No model field
```

**Proposed Extension**:
```python
@dataclass
class Task:
    id: str
    agent_id: str
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    model: str | None = None  # ✅ Add model field
```

---

## 4. Implementation Approach

### 4.1 Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Configuration Layer                       │
│  teambot.json → ConfigLoader → agent.model + default_model  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Model Registry                           │
│  VALID_MODELS constant + get_available_models() function    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SDK Client Layer                          │
│  CopilotSDKClient.execute(agent_id, prompt, model=None)     │
│  Session config includes model parameter                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      UI Layer                                │
│  AgentStatus.model + StatusPanel + ConsoleDisplay           │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Model Resolution Priority

1. **Inline specification** (highest): `@pm --model gpt-5 task`
2. **Session override**: `/model pm gpt-5` sets for session
3. **Agent config**: `teambot.json` agent's `model` field
4. **Global default**: `teambot.json` `default_model` field
5. **SDK default** (lowest): Whatever Copilot SDK uses

### 4.3 Command Syntax Proposals

#### 4.3.1 Inline Model Selection

```
@pm --model gpt-5 Create a project plan
@pm -m claude-opus-4.5 Review this code
```

**Parser modification required**: `src/teambot/repl/parser.py`

#### 4.3.2 Session Model Override

```
/model pm gpt-5           # Set pm's model for session
/model ba claude-opus-4.5 # Set ba's model for session
/model --reset pm         # Reset to configured default
```

**New system command**: `src/teambot/repl/commands.py`

#### 4.3.3 List Available Models

```
/models                   # List all available models
/models --json            # JSON output for scripting
```

**New system command**: `src/teambot/repl/commands.py`

---

## 5. Validation Requirements

### 5.1 Model Validation Function

```python
VALID_MODELS = {
    "claude-sonnet-4.5",
    "claude-haiku-4.5", 
    "claude-opus-4.5",
    "claude-sonnet-4",
    "gemini-3-pro-preview",
    "gpt-5.2-codex",
    "gpt-5.2",
    "gpt-5.1-codex-max",
    "gpt-5.1-codex",
    "gpt-5.1",
    "gpt-5",
    "gpt-5.1-codex-mini",
    "gpt-5-mini",
    "gpt-4.1",
}

def validate_model(model: str) -> bool:
    """Validate model is supported by Copilot CLI."""
    return model in VALID_MODELS
```

### 5.2 Error Messages

| Scenario | Error Message |
|----------|---------------|
| Invalid model in config | `ConfigError: Invalid model 'xyz' for agent 'pm'. Valid models: claude-sonnet-4.5, ...` |
| Invalid inline model | `[red]Invalid model: xyz. Use /models to see available options.[/red]` |
| Model not supported by SDK | `[red]Model gpt-5 not available. Check Copilot CLI authentication.[/red]` |

---

## 6. Testing Strategy Research

### 6.1 Existing Test Infrastructure

**Framework**: pytest 9.0.2 with pytest-cov, pytest-mock, pytest-asyncio  
**Location**: `tests/` directory (mirrors `src/` structure)  
**Naming**: `test_*.py` pattern  
**Runner**: `uv run pytest`  
**Coverage**: 88% current (801 tests)

### 6.2 Test Patterns Found

**File**: `tests/test_config/test_loader.py` (Lines 1-347)
- Uses `tmp_path` fixture for temp directories
- JSON config files created inline
- `pytest.raises` for error validation
- Class-based test organization

**File**: `tests/test_copilot/test_sdk_client.py` (Lines 1-453)
- Async tests with `@pytest.mark.asyncio`
- Mock fixtures from `conftest.py`
- Patch decorators for SDK mocking
- Session capture patterns for verification

### 6.3 Test Categories for Model Selection

| Category | Description | Approach |
|----------|-------------|----------|
| Config validation | Model field validation in config loader | TDD - clear requirements |
| SDK integration | Model passed to session creation | Code-First - SDK mocking complex |
| UI display | Model shown in status/tasks | Code-First - visual verification |
| Parser extension | Inline model syntax parsing | TDD - well-defined grammar |
| Command handlers | `/model`, `/models` commands | TDD - clear I/O |

---

## 7. Files Requiring Modification

| File | Changes | Priority |
|------|---------|----------|
| `src/teambot/copilot/sdk_client.py` | Add model parameter to session creation | 🔴 High |
| `src/teambot/config/loader.py` | Add model validation for agents | 🔴 High |
| `src/teambot/config/schema.py` | Add VALID_MODELS constant | 🔴 High |
| `src/teambot/tasks/models.py` | Add model field to Task | 🟡 Medium |
| `src/teambot/ui/agent_state.py` | Add model field to AgentStatus | 🟡 Medium |
| `src/teambot/ui/widgets/status_panel.py` | Display model in status | 🟡 Medium |
| `src/teambot/visualization/console.py` | Add Model column to table | 🟡 Medium |
| `src/teambot/repl/parser.py` | Parse `--model` inline option | 🟡 Medium |
| `src/teambot/repl/commands.py` | Add `/model` and `/models` commands | 🟡 Medium |
| `src/teambot/tasks/executor.py` | Pass model to task creation | 🟡 Medium |
| `src/teambot/tasks/manager.py` | Include model in task execution | 🟡 Medium |
| `teambot.json` | Document model configuration | 🟢 Low |

---

## 8. Task Implementation Requests

### 8.1 Core Implementation Tasks

- [ ] **TASK-1**: Add `VALID_MODELS` constant and `validate_model()` function to `config/schema.py`
- [ ] **TASK-2**: Extend `ConfigLoader` to validate and load agent `model` and global `default_model`
- [ ] **TASK-3**: Modify `CopilotSDKClient` to accept and pass model parameter to session creation
- [ ] **TASK-4**: Add `model` field to `Task` dataclass in `tasks/models.py`
- [ ] **TASK-5**: Add `model` field to `AgentStatus` dataclass in `ui/agent_state.py`

### 8.2 UI Implementation Tasks

- [ ] **TASK-6**: Update `StatusPanel` to display model alongside agent status
- [ ] **TASK-7**: Update `ConsoleDisplay.render_table()` to include Model column
- [ ] **TASK-8**: Update `/status` command output to show model
- [ ] **TASK-9**: Update `/tasks` command output to show model per task

### 8.3 Command Extension Tasks

- [ ] **TASK-10**: Extend parser to support `--model`/`-m` inline option
- [ ] **TASK-11**: Implement `/models` command to list available models
- [ ] **TASK-12**: Implement `/model <agent> <model>` command for session override

### 8.4 Integration Tasks

- [ ] **TASK-13**: Integrate model resolution in `TaskExecutor`
- [ ] **TASK-14**: Update file-based orchestration to use per-agent models
- [ ] **TASK-15**: Add model to progress/status callbacks

---

## 9. Potential Next Research

| Topic | Priority | Reason |
|-------|----------|--------|
| SDK model parameter format | 🟡 Medium | Verify SDK accepts model in session config |
| Model aliases/shortcuts | 🟢 Low | UX improvement (e.g., `opus` → `claude-opus-4.5`) |
| Model capability differences | 🟢 Low | Document which agents benefit from which models |
| Cost/token tracking per model | 🟢 Low | Future feature for usage monitoring |

---

## 10. Research Validation

```
RESEARCH_VALIDATION: PASS
- Document: CREATED ✅
- Placeholders: 0 remaining ✅
- Technical Approach: DOCUMENTED ✅
- Entry Points: 7 traced, 7 covered ✅
- Test Infrastructure: RESEARCHED ✅
- Implementation Ready: YES ✅
```

---

## 11. References

| Source | Location | Relevance |
|--------|----------|-----------|
| Copilot CLI help | `copilot --help` | Model list, flag syntax |
| CopilotConfig | `src/teambot/copilot/client.py:26-34` | Existing model support |
| CopilotSDKClient | `src/teambot/copilot/sdk_client.py:110-161` | Session creation |
| ConfigLoader | `src/teambot/config/loader.py:97-211` | Validation patterns |
| AgentStatus | `src/teambot/ui/agent_state.py:22-51` | Status dataclass |
| Task model | `src/teambot/tasks/models.py:52-79` | Task dataclass |
| StatusPanel | `src/teambot/ui/widgets/status_panel.py:101-137` | UI display |
| ConsoleDisplay | `src/teambot/visualization/console.py:80-110` | Table rendering |
| Command parser | `src/teambot/repl/parser.py:88-115` | Parse patterns |
| Test patterns | `tests/test_config/test_loader.py` | Testing conventions |
