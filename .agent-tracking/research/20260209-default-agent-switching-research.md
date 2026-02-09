<!-- markdownlint-disable-file -->

# 🔬 Research: Runtime Default Agent Switching

**Date**: 2026-02-09
**Feature**: Runtime Default Agent Switching
**Spec**: `.teambot/default-agent-switching/artifacts/feature_spec.md`
**Status**: ✅ Complete

---

## Table of Contents

1. [Research Scope](#1-research-scope)
2. [Entry Point Analysis](#2-entry-point-analysis)
3. [Technical Approach](#3-technical-approach)
4. [Code Patterns & References](#4-code-patterns--references)
5. [Testing Strategy Research](#5-testing-strategy-research)
6. [Implementation Guidance](#6-implementation-guidance)
7. [Task Implementation Requests](#7-task-implementation-requests)
8. [Potential Next Research](#8-potential-next-research)

---

## 1. Research Scope

### Objective

Research the implementation approach for adding runtime default agent switching to TeamBot, enabling users to change which agent receives plain-text input via `/use-agent <id>` and `/reset-agent` commands without modifying `teambot.json`.

### Key Questions Answered

| # | Question | Answer |
|---|----------|--------|
| 1 | How does raw input currently route to the default agent? | `AgentRouter._route_raw()` checks `_default_agent` and converts RAW commands to AGENT commands (router.py:159-188) |
| 2 | What mutation is needed on `AgentRouter`? | Add `set_default_agent(agent_id)` method and `_config_default_agent` attribute to store original value |
| 3 | How are slash commands dispatched? | `SystemCommands.dispatch()` uses a dict mapping command names to handler methods (commands.py:574-586) |
| 4 | How does the UI status panel update? | `AgentStatusManager` listener pattern triggers `StatusPanel._format_status()` re-render (status_panel.py:69-75) |
| 5 | How does agent validation work? | `VALID_AGENTS` set in router.py:20 and `ConfigLoader._validate_default_agent()` in loader.py:182-190 |
| 6 | Does the split-pane UI share the router with REPL? | No — each mode creates its own `AgentRouter` instance; both extract `default_agent` from config independently |

### Assumptions

- The 6 MVP agent IDs are the valid set: `pm`, `ba`, `writer`, `builder-1`, `builder-2`, `reviewer`
- Session-scoped only — no file I/O
- Both REPL and split-pane UI modes must be supported

---

## 2. Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| Plain text (REPL) | `loop.py:316` → `parse_command()` → `router.route()` → `_route_raw()` | ✅ YES | ✅ YES — `_route_raw()` reads `_default_agent` |
| Plain text (UI) | `app.py:120-136` → `router.get_default_agent()` → creates AGENT command | ✅ YES | ✅ YES — reads `router.get_default_agent()` |
| `/use-agent builder-1` (REPL) | `loop.py:316` → `parse_command()` → `CommandType.SYSTEM` → `router.route()` → `_route_system()` → `commands.dispatch()` | ❌ NO — handler doesn't exist yet | ✅ YES — new handler in `SystemCommands` |
| `/use-agent builder-1` (UI) | `app.py:118-119` → `_handle_system_command()` → `commands.dispatch()` | ❌ NO — handler doesn't exist yet | ✅ YES — same handler path as REPL |
| `/reset-agent` (REPL) | Same as `/use-agent` but with different args | ❌ NO | ✅ YES — new handler |
| `/reset-agent` (UI) | Same as `/use-agent` but with different args | ❌ NO | ✅ YES — new handler |
| `/status` (REPL) | `commands.py:601-614` → `handle_status()` | ✅ YES | ✅ YES — needs default agent info |
| `/status` (UI) | `app.py:296-299` → `_get_status()` | ✅ YES | ✅ YES — needs default agent info |
| `@agent task` (REPL) | `loop.py:324-331` → `router._route_agent()` | ✅ Already works | ❌ NO — explicit directives unchanged |
| `@agent task` (UI) | `app.py:113-117` → `_handle_agent_command()` | ✅ Already works | ❌ NO — unchanged |
| Status panel (UI) | `status_panel.py:101-142` → `_format_status()` | ✅ YES | ✅ YES — needs default indicator |

### Code Path Traces

#### Entry Point 1: Plain Text in REPL (loop.py)

1. User enters: `build the feature` (no `@agent` prefix)
2. Parsed by: `parse_command()` → `Command(type=CommandType.RAW, content="build the feature")`
3. Routed by: `loop.py:335` → `router.route(command)`
4. Reaches: `router._route_raw()` (router.py:159-188)
5. Checks: `self._default_agent` → if set, converts to AGENT command and calls `_route_agent()`
6. ✅ **Feature reached**: Changing `_default_agent` at runtime directly affects routing

#### Entry Point 2: Plain Text in Split-Pane UI (app.py)

1. User enters: `build the feature` (no `@agent` prefix)
2. Parsed by: `parse_command()` → `Command(type=CommandType.RAW, ...)`
3. Handled by: `app.py:120-136` — checks `self._router.get_default_agent()`
4. If default agent set: Creates `Command(type=AGENT, agent_id=default_agent, ...)` and calls `_handle_agent_command()`
5. ✅ **Feature reached**: Changing router's `_default_agent` affects UI routing

#### Entry Point 3: `/use-agent` Command (both modes)

1. User enters: `/use-agent builder-1`
2. Parsed by: `parse_command()` → `Command(type=SYSTEM, command="use-agent", args=["builder-1"])`
3. REPL path: `loop.py:335` → `router.route()` → `_route_system()` → `commands.dispatch("use-agent", ["builder-1"])`
4. UI path: `app.py:306-307` → `commands.dispatch("use-agent", ["builder-1"])`
5. ❌ **Not implemented yet**: Need new entry in dispatch table and handler function

#### Entry Point 4: `/status` in REPL

1. `commands.py:601-614` → `SystemCommands.status()` → if orchestrator, use it; else `handle_status()`
2. `handle_status()` (commands.py:115-132) → static agent list, no default agent info
3. ✅ **Needs enhancement**: Add default agent line to output

#### Entry Point 5: `/status` in Split-Pane UI

1. `app.py:296-299` → `_get_status()` (app.py:405-430)
2. Uses `self._agent_status.get_all()` to render status
3. ✅ **Needs enhancement**: Add default agent line and indicator

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| No `set_default_agent()` on `AgentRouter` | Cannot change default at runtime | Add setter method + `_config_default_agent` attribute |
| No `/use-agent` in dispatch table | Command not recognized | Add to `SystemCommands.dispatch()` handlers dict |
| No `/reset-agent` in dispatch table | Command not recognized | Add to `SystemCommands.dispatch()` handlers dict |
| `SystemCommands` has no reference to router | Cannot call `set_default_agent()` | Pass router reference to `SystemCommands.__init__()` or add setter |
| `/status` in REPL has no default agent info | User can't see current default | Enhance `handle_status()` to accept and display default agent |
| `/status` in UI has no default agent info | User can't see current default | Enhance `_get_status()` in `app.py` |
| Status panel has no default indicator | User can't see current default visually | Enhance `_format_status()` in `StatusPanel` |
| `SystemCommands` needs config_default for reset | `/reset-agent` needs original value | Store `_config_default_agent` in `SystemCommands` |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## 3. Technical Approach

### Selected Approach: Extend Existing Router + SystemCommands Pattern

**Rationale**: The feature fits cleanly into the existing architecture. The `AgentRouter` already has the `_default_agent` attribute and `get_default_agent()` method. The `SystemCommands` class already provides the dispatch pattern for slash commands. No new abstractions or parallel systems are needed.

### Architecture Overview

```
User Input → parse_command() → CommandType.SYSTEM
                                    ↓
                          SystemCommands.dispatch()
                                    ↓
                          "use-agent" → handle_use_agent()
                                    ↓
                          AgentRouter.set_default_agent(id)
                                    ↓
                          StatusPanel listener notified (UI mode)
```

### Component Changes

| Component | File | Change Type | Description |
|-----------|------|-------------|-------------|
| **AgentRouter** | `router.py` | Extend | Add `set_default_agent()`, `_config_default_agent`, `get_config_default_agent()` |
| **handle_use_agent** | `commands.py` | New function | Handler for `/use-agent [agent-id]` |
| **handle_reset_agent** | `commands.py` | New function | Handler for `/reset-agent` |
| **SystemCommands** | `commands.py` | Extend | Add router reference, add dispatch entries, add `_config_default_agent` |
| **handle_status** | `commands.py` | Enhance | Accept default_agent info, add "Default Agent:" line |
| **handle_help** | `commands.py` | Enhance | Add `/use-agent` and `/reset-agent` to help text |
| **StatusPanel** | `status_panel.py` | Enhance | Add default agent indicator; accept router or default_agent callback |
| **TeamBotApp._get_status** | `app.py` | Enhance | Add default agent line to status output |
| **REPLLoop.__init__** | `loop.py` | Extend | Pass router to SystemCommands |
| **TeamBotApp.__init__** | `app.py` | Extend | Pass router to SystemCommands; handle `/use-agent` in system command routing |

---

## 4. Code Patterns & References

### Pattern 1: AgentRouter Attribute + Getter (Existing)

📁 `src/teambot/repl/router.py` (Lines 39-91)

```python
class AgentRouter:
    def __init__(self, history_limit: int = 100, default_agent: str | None = None):
        self._default_agent = default_agent
        # ... other init

    def get_default_agent(self) -> str | None:
        return self._default_agent
```

**Extension needed**: Add `_config_default_agent` to preserve original, and `set_default_agent()` for runtime mutation.

```python
# Proposed addition to AgentRouter
def __init__(self, history_limit: int = 100, default_agent: str | None = None):
    self._default_agent = default_agent
    self._config_default_agent = default_agent  # Store original for /reset-agent
    # ... existing init

def set_default_agent(self, agent_id: str | None) -> None:
    """Set the default agent for routing raw input.

    Args:
        agent_id: Agent ID to set as default, or None to clear.

    Raises:
        RouterError: If agent_id is not valid.
    """
    if agent_id is not None and not self.is_valid_agent(agent_id):
        raise RouterError(
            f"Unknown agent '{agent_id}'. "
            f"Available agents: {', '.join(sorted(VALID_AGENTS))}"
        )
    self._default_agent = agent_id

def get_config_default_agent(self) -> str | None:
    """Get the original config default agent."""
    return self._config_default_agent
```

### Pattern 2: SystemCommands Dispatch Table (Existing)

📁 `src/teambot/repl/commands.py` (Lines 574-586)

```python
handlers = {
    "help": self.help,
    "status": self.status,
    "history": self.history,
    "quit": self.quit,
    "exit": self.quit,
    "tasks": self.tasks,
    "task": self.task,
    "cancel": self.cancel,
    "overlay": self.overlay,
    "models": self.models,
    "model": self.model,
}
```

**Extension needed**: Add `"use-agent"` and `"reset-agent"` entries.

### Pattern 3: SystemCommands with External Dependencies (Existing)

📁 `src/teambot/repl/commands.py` (Lines 521-562)

The `SystemCommands` class already accepts external dependencies (`orchestrator`, `executor`, `overlay`) via constructor and setter methods:

```python
class SystemCommands:
    def __init__(self, orchestrator=None, executor=None, overlay=None):
        self._orchestrator = orchestrator
        self._executor = executor
        self._overlay = overlay

    def set_executor(self, executor):
        self._executor = executor

    def set_overlay(self, overlay):
        self._overlay = overlay
```

**Extension needed**: Add `router` parameter to constructor and `set_router()` setter.

### Pattern 4: handle_model as Template for handle_use_agent (Existing)

📁 `src/teambot/repl/commands.py` (Lines 218-277)

The `/model` command follows the exact pattern needed: validate input, mutate state, return confirmation. This is the best template for `/use-agent`:

```python
def handle_model(args, session_overrides):
    if not args:  # No args → show current state
        ...
    agent_id = args[0]
    if agent_id not in VALID_AGENTS:  # Validate
        return CommandResult(output=f"Invalid agent ...", success=False)
    session_overrides[agent_id] = model  # Mutate state
    return CommandResult(output=f"Set model ...")  # Confirm
```

### Pattern 5: StatusPanel Listener + Format (Existing)

📁 `src/teambot/ui/widgets/status_panel.py` (Lines 101-142)

The `_format_status()` method renders each agent row. The "default" indicator should be added here, similar to how model info is appended:

```python
# Existing: model display
if status.model:
    model_display = self._format_model_name(status.model)
    line += f" [dim italic]({model_display})[/dim italic]"

# Proposed: default indicator
# if agent_id == default_agent:
#     line += " [bold cyan]⬤ default[/bold cyan]"
```

**Challenge**: `StatusPanel` currently only has access to `AgentStatusManager`, not the router. Need a way to pass the default agent info.

**Solution**: Add `default_agent` tracking to `AgentStatusManager` (keeps single source of truth pattern) or pass a callback to `StatusPanel`.

**Recommended**: Extend `AgentStatusManager` with `_default_agent` and `set_default_agent()`/`get_default_agent()` since it's already the centralized state for the UI. This avoids adding router dependency to the widget.

### Pattern 6: UI System Command Routing (Existing)

📁 `src/teambot/ui/app.py` (Lines 286-315)

The UI handles some system commands specially (clear, quit, status, cancel) and delegates the rest:

```python
async def _handle_system_command(self, command, output):
    if command.command == "clear": ...
    if command.command == "quit": ...
    if command.command == "status": ...
    if command.command == "cancel": ...
    # Use SystemCommands.dispatch for other commands
    result = self._commands.dispatch(command.command, command.args or [])
```

**For `/use-agent`**: The command can flow through the default dispatch path. After dispatch, the UI should update the status panel. Follow the pattern of `/model` which updates model display after success (app.py:310-312):

```python
# Existing pattern for /model
if command.command == "model" and result.success:
    self._update_model_display(command.args or [])
```

**Proposed addition**:
```python
# After dispatch
if command.command in ("use-agent", "reset-agent") and result.success:
    # Update status panel default agent indicator
    self._agent_status.set_default_agent(self._router.get_default_agent())
```

---

## 5. Testing Strategy Research

### Existing Test Infrastructure

| Aspect | Detail |
|--------|--------|
| **Framework** | pytest 7.x with pytest-mock, pytest-cov, pytest-asyncio |
| **Location** | `tests/` directory (mirrors `src/` structure) |
| **Naming** | `test_*.py` files, `Test*` classes, `test_*` methods |
| **Runner** | `uv run pytest` |
| **Coverage** | ~80% (943 tests as of recent run) |
| **Async** | `@pytest.mark.asyncio` decorator for async tests |

### Test Patterns Found

#### Pattern A: Router Tests — `tests/test_repl/test_router.py`

- Uses `AsyncMock` for agent handlers, `MagicMock` for sync handlers
- Creates `Command` objects directly with `CommandType` enum
- Tests grouped by class: `TestAgentRouterValidation`, `TestRouterWithDefaultAgent`, etc.
- Asserts handler call arguments and return values
- Tests error cases with `pytest.raises(RouterError, match=...)`

**Example** (Lines 201-300): `TestRouterWithDefaultAgent` — 6 tests covering default agent routing, empty input, whitespace, invalid default, history recording.

#### Pattern B: Command Tests — `tests/test_repl/test_commands.py`

- Tests standalone handler functions (`handle_help`, `handle_status`, etc.)
- Tests `SystemCommands.dispatch()` integration
- Checks `result.success`, `result.output`, `result.should_exit`
- Uses string assertions on output content

**Example** (Lines 254-299): `TestModelCommand` — tests viewing, setting, invalid agent, invalid model, clearing.

#### Pattern C: Status Panel Tests — `tests/test_ui/test_status_panel.py`

- Creates `AgentStatusManager` and `StatusPanel` directly
- Tests `_format_status()` output content
- Uses `patch.object` for `update` and `set_interval` methods
- Checks Rich markup strings in output

#### Pattern D: REPL Loop Tests — `tests/test_repl/test_loop.py`

- Mocks `Console`, `sdk_client`, and `_get_input`
- Tests initialization, handler wiring, signal handling, cleanup
- Uses `@pytest.mark.asyncio` for async test methods

### Coverage Requirements

- All new handler functions: 100%
- Router setter method: 100%
- Status panel default indicator: 100%
- Error paths (invalid agent, already-at-default): 100%

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `AgentRouter.set_default_agent()` | **TDD** | Core logic, well-defined behavior, follows existing `TestRouterWithDefaultAgent` |
| `handle_use_agent()` | **TDD** | Multiple code paths (no args, valid, invalid, idempotent), follows `TestModelCommand` |
| `handle_reset_agent()` | **TDD** | Clear spec, follows same pattern |
| `SystemCommands` dispatch integration | **Code-First** | Straightforward dict addition, verified by dispatch tests |
| `StatusPanel` default indicator | **Code-First** | UI rendering, test after implementation |
| `handle_status` enhancement | **Code-First** | Additive text change, simple assertion |
| `handle_help` enhancement | **Code-First** | Text-only change |
| Wiring in `loop.py` / `app.py` | **Code-First** | Constructor changes, integration verified by existing patterns |

---

## 6. Implementation Guidance

### Change Order (Recommended)

1. **`router.py`** — Add `_config_default_agent`, `set_default_agent()`, `get_config_default_agent()`
2. **`commands.py`** — Add `handle_use_agent()`, `handle_reset_agent()`, update `SystemCommands` (router reference, dispatch entries, handler methods)
3. **`commands.py`** — Update `handle_help()` with new command documentation
4. **`commands.py`** — Update `handle_status()` to show default agent info
5. **`agent_state.py`** — Add `_default_agent` to `AgentStatusManager` for UI reactivity
6. **`status_panel.py`** — Add default agent indicator in `_format_status()`
7. **`loop.py`** — Pass router to `SystemCommands`
8. **`app.py`** — Pass router to `SystemCommands`; handle status panel update after `/use-agent`; update `_get_status()` with default agent info
9. **Tests** — Add tests following patterns described above

### Detailed Change Specifications

#### 1. `src/teambot/repl/router.py`

**Add to `__init__`** (after line 52):
```python
self._config_default_agent = default_agent
```

**Add new methods** (after `get_default_agent`, ~line 91):
```python
def set_default_agent(self, agent_id: str | None) -> None:
    if agent_id is not None and not self.is_valid_agent(agent_id):
        raise RouterError(
            f"Unknown agent '{agent_id}'. "
            f"Available agents: {', '.join(sorted(VALID_AGENTS))}"
        )
    self._default_agent = agent_id

def get_config_default_agent(self) -> str | None:
    return self._config_default_agent
```

#### 2. `src/teambot/repl/commands.py`

**Add `router` parameter to `SystemCommands.__init__`**:
```python
def __init__(self, orchestrator=None, executor=None, overlay=None, router=None):
    # ... existing
    self._router = router
```

**Add `set_router` setter**:
```python
def set_router(self, router):
    self._router = router
```

**Add to dispatch dict** (after "model" entry):
```python
"use-agent": self.use_agent,
"reset-agent": self.reset_agent,
```

**Add handler functions** (module-level, following `handle_model` pattern):

```python
def handle_use_agent(args: list[str], router) -> CommandResult:
    if router is None:
        return CommandResult(output="Router not available.", success=False)

    if not args:
        # Show current default and available agents
        current = router.get_default_agent() or "none"
        agents = ", ".join(sorted(router.get_all_agents()))
        return CommandResult(
            output=f"Current default agent: {current}\nAvailable agents: {agents}"
        )

    agent_id = args[0]
    if not router.is_valid_agent(agent_id):
        agents = ", ".join(sorted(router.get_all_agents()))
        return CommandResult(
            output=f"Unknown agent '{agent_id}'. Available agents: {agents}",
            success=False,
        )

    current = router.get_default_agent()
    if current == agent_id:
        return CommandResult(
            output=f"Default agent is already set to {agent_id}."
        )

    router.set_default_agent(agent_id)
    return CommandResult(
        output=f"Default agent set to {agent_id}. "
        f"Plain text input will now be routed to @{agent_id}."
    )


def handle_reset_agent(args: list[str], router) -> CommandResult:
    if router is None:
        return CommandResult(output="Router not available.", success=False)

    config_default = router.get_config_default_agent()
    current = router.get_default_agent()

    if current == config_default:
        return CommandResult(
            output=f"Default agent is already set to {config_default or 'none'} (from configuration)."
        )

    router.set_default_agent(config_default)
    return CommandResult(
        output=f"Default agent reset to {config_default or 'none'} (from configuration)."
    )
```

**Update `handle_help`**: Add to the command list in the main help output:
```
  /use-agent     - Set default agent for plain text
  /reset-agent   - Reset default agent to config value
```

**Update `handle_status`**: Accept optional `default_agent` and `config_default_agent` params and prepend:
```
  Default Agent: builder-1 (session override; config default: pm)
```

#### 3. `src/teambot/ui/agent_state.py`

**Add `_default_agent` tracking to `AgentStatusManager`**:
```python
@dataclass
class AgentStatusManager:
    _statuses: dict[str, AgentStatus] = field(default_factory=dict)
    _listeners: list[...] = field(default_factory=list)
    _default_agent: str | None = field(default=None)

    def set_default_agent(self, agent_id: str | None) -> None:
        if self._default_agent != agent_id:
            self._default_agent = agent_id
            self._notify()

    def get_default_agent(self) -> str | None:
        return self._default_agent
```

#### 4. `src/teambot/ui/widgets/status_panel.py`

**In `_format_status()`**, add default indicator after idle label:
```python
if status.state == AgentState.IDLE:
    if agent_id == self._status_manager.get_default_agent():
        lines.append(f"{line} [bold cyan]⬤ default[/bold cyan]")
    else:
        lines.append(f"{line} [dim]idle[/dim]")
```

Also show for non-idle agents (when the default agent is running/streaming):
```python
if agent_id == self._status_manager.get_default_agent():
    line += " [bold cyan]⬤ default[/bold cyan]"
```

#### 5. `src/teambot/repl/loop.py`

**In `__init__`**, pass router to SystemCommands:
```python
self._commands = SystemCommands(router=self._router)
```

Or use setter (if created after router):
```python
self._commands.set_router(self._router)
```

#### 6. `src/teambot/ui/app.py`

**In `__init__`**, pass router to SystemCommands:
```python
self._commands = SystemCommands(executor=executor, router=router)
```

**In `_handle_system_command`**, after dispatch for use-agent/reset-agent:
```python
if command.command in ("use-agent", "reset-agent") and result.success:
    new_default = self._router.get_default_agent() if self._router else None
    self._agent_status.set_default_agent(new_default)
```

**In `_get_status`**, add default agent line:
```python
# After "Agent Status:" header
if self._router:
    current_default = self._router.get_default_agent()
    config_default = self._router.get_config_default_agent()
    if current_default != config_default:
        lines.append(f"  Default Agent: {current_default} (session override; config default: {config_default})")
    else:
        lines.append(f"  Default Agent: {current_default or 'none'}")
    lines.append("")
```

**Initialize default agent on AgentStatusManager** in `__init__`:
```python
default_agent = self._router.get_default_agent() if self._router else None
self._agent_status.set_default_agent(default_agent)
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Where to store config default | `AgentRouter._config_default_agent` | Router is the source of truth for routing; keeps config value close to usage |
| How to pass router to commands | Constructor param + setter | Follows existing `executor`/`overlay` pattern in `SystemCommands` |
| How to update status panel | Via `AgentStatusManager._default_agent` | Keeps listener pattern; avoids direct router dependency in widget |
| Validation in setter vs handler | Both — setter validates and raises, handler catches and returns CommandResult | Defense in depth; handler provides user-friendly error |
| Idempotency messages | Informational (success=True) | Not an error; P2 UX polish per spec |

### ⚠️ Pitfalls to Avoid

1. **Don't forget both REPL and UI paths** — The `/status` command has TWO implementations: `handle_status()` for REPL and `_get_status()` for UI. Both need the default agent info.
2. **Don't couple StatusPanel to router** — Use `AgentStatusManager` as intermediary to maintain the listener pattern.
3. **Don't forget to initialize `_default_agent` on `AgentStatusManager`** in `app.py` — Otherwise the status panel won't show the initial default.
4. **Don't break the `_route_raw()` flow** — The setter must only change `_default_agent`, not `_config_default_agent`.
5. **Watch the UI dispatch path** — `/use-agent` needs to go through `self._commands.dispatch()` (line 307 in app.py) rather than being intercepted specially, unless there's a reason to.

---

## 7. Task Implementation Requests

### Task 1: Extend AgentRouter with Runtime Mutation

**Files**: `src/teambot/repl/router.py`
**Changes**:
- Add `_config_default_agent` attribute in `__init__`
- Add `set_default_agent(agent_id)` method with validation
- Add `get_config_default_agent()` method
**Tests**: `tests/test_repl/test_router.py` — new class `TestRouterDefaultAgentMutation`

### Task 2: Implement `/use-agent` and `/reset-agent` Command Handlers

**Files**: `src/teambot/repl/commands.py`
**Changes**:
- Add `handle_use_agent()` function
- Add `handle_reset_agent()` function
- Add `_router` to `SystemCommands.__init__` + `set_router()` setter
- Add dispatch entries for `use-agent` and `reset-agent`
- Add `SystemCommands.use_agent()` and `SystemCommands.reset_agent()` methods
**Tests**: `tests/test_repl/test_commands.py` — new classes `TestUseAgentCommand`, `TestResetAgentCommand`

### Task 3: Update `/help` Command Documentation

**Files**: `src/teambot/repl/commands.py`
**Changes**:
- Add `/use-agent` and `/reset-agent` entries to main help output (line ~86-98)
**Tests**: `tests/test_repl/test_commands.py` — update `TestHelpCommand.test_help_returns_command_list`

### Task 4: Update `/status` Command Output

**Files**: `src/teambot/repl/commands.py`, `src/teambot/ui/app.py`
**Changes**:
- Enhance `handle_status()` to accept and show default agent info
- Enhance `TeamBotApp._get_status()` to show default agent info
**Tests**: `tests/test_repl/test_commands.py`, `tests/test_ui/test_app.py`

### Task 5: Add Default Agent Tracking to AgentStatusManager

**Files**: `src/teambot/ui/agent_state.py`
**Changes**:
- Add `_default_agent` field, `set_default_agent()`, `get_default_agent()`
**Tests**: `tests/test_ui/test_agent_state.py`

### Task 6: Add Default Agent Indicator to StatusPanel

**Files**: `src/teambot/ui/widgets/status_panel.py`
**Changes**:
- Show `⬤ default` indicator for the current default agent in `_format_status()`
**Tests**: `tests/test_ui/test_status_panel.py`

### Task 7: Wire Router to SystemCommands in REPL and UI

**Files**: `src/teambot/repl/loop.py`, `src/teambot/ui/app.py`
**Changes**:
- Pass router to `SystemCommands` in both modes
- Initialize `AgentStatusManager._default_agent` in UI mode
- Update status panel after `/use-agent` and `/reset-agent` in UI
**Tests**: `tests/test_repl/test_loop.py`, `tests/test_ui/test_app.py`

---

## 8. Potential Next Research

| Topic | Priority | Reason |
|-------|----------|--------|
| Agent alias support in `/use-agent` | Low | Spec marks as out of scope; could be added later via `resolve_agent_id()` |
| Per-stage default agent automation | Low | Future feature — auto-switch default based on workflow stage |
| Persist runtime defaults across sessions | Low | Explicitly excluded by spec; could use `.teambot/session.json` if needed later |
