<!-- markdownlint-disable-file -->

# Implementation Details: Runtime Default Agent Switching

**Research Reference**: `.agent-tracking/research/20260209-default-agent-switching-research.md`
**Test Strategy Reference**: `.agent-tracking/test-strategies/20260209-default-agent-switching-test-strategy.md`
**Plan Reference**: `.agent-tracking/plans/20260209-default-agent-switching-plan.instructions.md`

---

## Phase 1: Core Router Mutation (TDD)

### Task 1.1: Write Router Mutation Tests

**File**: `tests/test_repl/test_router.py`
**Action**: Add new test class `TestRouterDefaultAgentMutation` after existing `TestRouterWithDefaultAgent` class

**Test Cases** (6 tests):

```python
class TestRouterDefaultAgentMutation:
    """Tests for runtime default agent switching on AgentRouter."""

    def test_set_default_agent_changes_default(self):
        """set_default_agent() updates get_default_agent() return value."""
        router = AgentRouter(default_agent="pm")
        router.set_default_agent("builder-1")
        assert router.get_default_agent() == "builder-1"

    def test_set_default_agent_to_none_clears_default(self):
        """set_default_agent(None) clears the default agent."""
        router = AgentRouter(default_agent="pm")
        router.set_default_agent(None)
        assert router.get_default_agent() is None

    def test_set_default_agent_invalid_raises_router_error(self):
        """set_default_agent() with invalid ID raises RouterError."""
        router = AgentRouter(default_agent="pm")
        with pytest.raises(RouterError, match="Unknown agent 'invalid'"):
            router.set_default_agent("invalid")

    def test_config_default_preserved_after_set(self):
        """get_config_default_agent() returns original after set_default_agent()."""
        router = AgentRouter(default_agent="pm")
        router.set_default_agent("builder-1")
        assert router.get_config_default_agent() == "pm"

    async def test_raw_input_routes_to_new_default_after_set(self):
        """After set_default_agent(), raw input routes to new default."""
        router = AgentRouter(default_agent="pm")
        mock_handler = AsyncMock(return_value="OK")
        router.register_agent_handler(mock_handler)
        router.register_raw_handler(MagicMock())
        router.set_default_agent("builder-1")
        await router.route(Command(type=CommandType.RAW, content="hello"))
        mock_handler.assert_called_once_with("builder-1", "hello")

    async def test_explicit_agent_unaffected_by_default_change(self):
        """@agent directives still route to specified agent after set_default_agent()."""
        router = AgentRouter(default_agent="pm")
        mock_handler = AsyncMock(return_value="OK")
        router.register_agent_handler(mock_handler)
        router.set_default_agent("builder-1")
        cmd = Command(type=CommandType.AGENT, agent_id="reviewer", agent_ids=["reviewer"], content="check")
        await router.route(cmd)
        mock_handler.assert_called_once_with("reviewer", "check")
```

**Pattern Reference**: Follows `TestRouterWithDefaultAgent` pattern (research Lines 344-357)

### Task 1.2: Implement Router Mutation

**File**: `src/teambot/repl/router.py`

**Change 1 — Add `_config_default_agent` to `__init__`** (after line 52):

Insert after `self._default_agent = default_agent`:
```python
self._config_default_agent = default_agent
```

**Change 2 — Add `set_default_agent()` method** (after `get_default_agent` at line 91):

```python
def set_default_agent(self, agent_id: str | None) -> None:
    """Set the default agent for routing raw input at runtime.

    Args:
        agent_id: Agent ID to set as default, or None to clear.

    Raises:
        RouterError: If agent_id is not a valid agent.
    """
    if agent_id is not None and not self.is_valid_agent(agent_id):
        raise RouterError(
            f"Unknown agent '{agent_id}'. "
            f"Available agents: {', '.join(sorted(VALID_AGENTS))}"
        )
    self._default_agent = agent_id
```

**Change 3 — Add `get_config_default_agent()` method** (after `set_default_agent`):

```python
def get_config_default_agent(self) -> str | None:
    """Get the original configuration default agent.

    Returns:
        The default agent ID from configuration, or None.
    """
    return self._config_default_agent
```

**Verification**: `_route_raw()` (line 166) reads `self._default_agent` — no changes needed there since `set_default_agent()` mutates `_default_agent` directly.

---

## Phase 2: Command Handlers (TDD)

### Task 2.1: Write `handle_use_agent` Tests

**File**: `tests/test_repl/test_commands.py`
**Action**: Add new test class `TestUseAgentCommand`

**Test Cases** (5 tests):

```python
class TestUseAgentCommand:
    """Tests for /use-agent command handler."""

    def test_use_agent_no_args_shows_current_and_available(self):
        """No args shows current default and available agents."""
        router = AgentRouter(default_agent="pm")
        result = handle_use_agent([], router)
        assert result.success is True
        assert "pm" in result.output
        assert "builder-1" in result.output

    def test_use_agent_valid_switches_default(self):
        """Valid agent ID switches the default."""
        router = AgentRouter(default_agent="pm")
        result = handle_use_agent(["builder-1"], router)
        assert result.success is True
        assert router.get_default_agent() == "builder-1"
        assert "builder-1" in result.output

    def test_use_agent_invalid_shows_error(self):
        """Invalid agent ID returns error with available agents."""
        router = AgentRouter(default_agent="pm")
        result = handle_use_agent(["foo"], router)
        assert result.success is False
        assert "foo" in result.output
        assert router.get_default_agent() == "pm"  # Unchanged

    def test_use_agent_idempotent(self):
        """Setting same default returns informational message."""
        router = AgentRouter(default_agent="pm")
        result = handle_use_agent(["pm"], router)
        assert result.success is True
        assert "already" in result.output.lower()

    def test_use_agent_no_router_returns_error(self):
        """No router available returns graceful error."""
        result = handle_use_agent(["builder-1"], None)
        assert result.success is False
```

### Task 2.2: Implement `handle_use_agent()`

**File**: `src/teambot/repl/commands.py`
**Action**: Add module-level function after `handle_model()` (after line 277)

```python
def handle_use_agent(args: list[str], router) -> CommandResult:
    """Handle /use-agent command - view or set default agent.

    Args:
        args: [agent_id] or [] to view current default.
        router: AgentRouter instance for mutation.

    Returns:
        CommandResult with agent info or confirmation.
    """
    if router is None:
        return CommandResult(output="Router not available.", success=False)

    if not args:
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
```

### Task 2.3: Write `handle_reset_agent` Tests

**File**: `tests/test_repl/test_commands.py`
**Action**: Add new test class `TestResetAgentCommand`

**Test Cases** (3 tests):

```python
class TestResetAgentCommand:
    """Tests for /reset-agent command handler."""

    def test_reset_agent_restores_config_default(self):
        """Resets to config default after runtime switch."""
        router = AgentRouter(default_agent="pm")
        router.set_default_agent("builder-1")
        result = handle_reset_agent([], router)
        assert result.success is True
        assert router.get_default_agent() == "pm"
        assert "pm" in result.output

    def test_reset_agent_already_at_default(self):
        """Informational message when already at config default."""
        router = AgentRouter(default_agent="pm")
        result = handle_reset_agent([], router)
        assert result.success is True
        assert "already" in result.output.lower()

    def test_reset_agent_no_router_returns_error(self):
        """No router available returns graceful error."""
        result = handle_reset_agent([], None)
        assert result.success is False
```

### Task 2.4: Implement `handle_reset_agent()`

**File**: `src/teambot/repl/commands.py`
**Action**: Add module-level function after `handle_use_agent()`

```python
def handle_reset_agent(args: list[str], router) -> CommandResult:
    """Handle /reset-agent command - reset default agent to config value.

    Args:
        args: Command arguments (unused).
        router: AgentRouter instance for mutation.

    Returns:
        CommandResult with confirmation.
    """
    if router is None:
        return CommandResult(output="Router not available.", success=False)

    config_default = router.get_config_default_agent()
    current = router.get_default_agent()

    if current == config_default:
        label = config_default or "none"
        return CommandResult(
            output=f"Default agent is already set to {label} (from configuration)."
        )

    router.set_default_agent(config_default)
    label = config_default or "none"
    return CommandResult(
        output=f"Default agent reset to {label} (from configuration)."
    )
```

---

## Phase 3: SystemCommands Integration (Code-First)

### Task 3.1: Add Router to SystemCommands

**File**: `src/teambot/repl/commands.py`

**Change 1 — Add `router` parameter to `__init__`** (line 521-538):

Update the `__init__` signature to include `router=None`:
```python
def __init__(
    self,
    orchestrator: Any = None,
    executor: Optional["TaskExecutor"] = None,
    overlay: Optional["OverlayRenderer"] = None,
    router: Optional["AgentRouter"] = None,
):
```

Add after line 538:
```python
self._router: AgentRouter | None = router
```

**Change 2 — Add `set_router()` setter** (after `set_overlay` at line 562):

```python
def set_router(self, router: "AgentRouter") -> None:
    """Set agent router for agent switching commands.

    Args:
        router: Agent router for default agent management.
    """
    self._router = router
```

### Task 3.2: Add Dispatch Entries and Wrapper Methods

**File**: `src/teambot/repl/commands.py`

**Change 1 — Add dispatch entries** (after `"model": self.model` at line 585):

```python
"use-agent": self.use_agent,
"reset-agent": self.reset_agent,
```

**Change 2 — Add wrapper methods** (after `model()` method at line 646):

```python
def use_agent(self, args: list[str]) -> CommandResult:
    """Handle /use-agent command."""
    return handle_use_agent(args, self._router)

def reset_agent(self, args: list[str]) -> CommandResult:
    """Handle /reset-agent command."""
    return handle_reset_agent(args, self._router)
```

### Task 3.3: Dispatch Integration Tests

**File**: `tests/test_repl/test_commands.py`

Test that `dispatch("use-agent", ...)` and `dispatch("reset-agent", ...)` route correctly:

```python
def test_dispatch_use_agent(self):
    router = AgentRouter(default_agent="pm")
    commands = SystemCommands(router=router)
    result = commands.dispatch("use-agent", ["builder-1"])
    assert result.success is True
    assert router.get_default_agent() == "builder-1"

def test_dispatch_reset_agent(self):
    router = AgentRouter(default_agent="pm")
    commands = SystemCommands(router=router)
    commands.dispatch("use-agent", ["builder-1"])
    result = commands.dispatch("reset-agent", [])
    assert result.success is True
    assert router.get_default_agent() == "pm"
```

---

## Phase 4: Help and Status Updates (Code-First)

### Task 4.1: Update `handle_help()` Text

**File**: `src/teambot/repl/commands.py`

**Change**: Add two lines to the main help output (after line 96 `/overlay` entry):

```
  /use-agent <id> - Set default agent for plain text input
  /reset-agent    - Reset default agent to config value
```

Insert these after the `/overlay` line and before `/history` in the available commands list.

### Task 4.2: Update `handle_status()` to Show Default Agent

**File**: `src/teambot/repl/commands.py`

**Change**: Modify `handle_status()` (lines 115-132) to accept optional router parameter and show default agent info.

Update function signature:
```python
def handle_status(args: list[str], router=None) -> CommandResult:
```

Add after `lines = ["Agent Status:", ""]` (line 126):
```python
if router:
    current_default = router.get_default_agent()
    config_default = router.get_config_default_agent()
    if current_default != config_default:
        lines.append(
            f"  Default Agent: {current_default} "
            f"(session override; config: {config_default or 'none'})"
        )
    else:
        lines.append(f"  Default Agent: {current_default or 'none'}")
    lines.append("")
```

### Task 4.3: Wire `SystemCommands.status()` to Pass Router

**File**: `src/teambot/repl/commands.py`

**Change**: Update `status()` method (lines 601-614) to pass `self._router` to `handle_status()`:

Change line 614 from:
```python
return handle_status(args)
```
to:
```python
return handle_status(args, self._router)
```

### Task 4.4: Help and Status Tests

**File**: `tests/test_repl/test_commands.py`

```python
def test_help_contains_use_agent_and_reset_agent(self):
    result = handle_help([])
    assert "/use-agent" in result.output
    assert "/reset-agent" in result.output

def test_status_shows_default_agent(self):
    router = AgentRouter(default_agent="pm")
    result = handle_status([], router)
    assert "Default Agent" in result.output
    assert "pm" in result.output

def test_status_shows_session_override(self):
    router = AgentRouter(default_agent="pm")
    router.set_default_agent("builder-1")
    result = handle_status([], router)
    assert "builder-1" in result.output
    assert "session override" in result.output
```

---

## Phase 5: AgentStatusManager Default Tracking (Code-First)

### Task 5.1: Add Default Agent to AgentStatusManager

**File**: `src/teambot/ui/agent_state.py`

**Change 1 — Add `_default_agent` field** (after line 89):

```python
_default_agent: str | None = field(default=None)
```

**Change 2 — Add `set_default_agent()` method** (after `set_model` at line 209):

```python
def set_default_agent(self, agent_id: str | None) -> None:
    """Set the default agent and notify listeners.

    Args:
        agent_id: Agent ID to mark as default, or None to clear.
    """
    if self._default_agent != agent_id:
        self._default_agent = agent_id
        self._notify()

def get_default_agent(self) -> str | None:
    """Get the current default agent.

    Returns:
        Default agent ID or None.
    """
    return self._default_agent
```

**Pattern**: Follows `set_model()` (lines 194-209) — change detection before notify.

### Task 5.2: AgentStatusManager Default Agent Tests

**File**: `tests/test_ui/test_agent_state.py`

```python
class TestAgentStatusManagerDefaultAgent:
    def test_set_default_agent_stores_value(self):
        manager = AgentStatusManager()
        manager.set_default_agent("builder-1")
        assert manager.get_default_agent() == "builder-1"

    def test_set_default_agent_notifies_listeners(self):
        manager = AgentStatusManager()
        listener = MagicMock()
        manager.add_listener(listener)
        manager.set_default_agent("builder-1")
        listener.assert_called_once_with(manager)

    def test_set_same_default_does_not_notify(self):
        manager = AgentStatusManager()
        manager.set_default_agent("pm")
        listener = MagicMock()
        manager.add_listener(listener)
        manager.set_default_agent("pm")  # Same value
        listener.assert_not_called()

    def test_get_default_agent_initially_none(self):
        manager = AgentStatusManager()
        assert manager.get_default_agent() is None
```

---

## Phase 6: Status Panel Default Indicator (Code-First)

### Task 6.1: Add Default Indicator to StatusPanel

**File**: `src/teambot/ui/widgets/status_panel.py`

**Change**: Modify `_format_status()` (lines 101-142) to show `⬤ default` for the default agent.

In the agent iteration loop (starting at line 119), add default indicator logic. The indicator should appear regardless of agent state (idle, running, streaming).

After the line that builds the base `line` string (line 121: `line = f"{indicator} {agent_id}"`), add:

```python
# Add default agent indicator
is_default = agent_id == self._status_manager.get_default_agent()
if is_default:
    line += " [bold cyan]★[/bold cyan]"
```

This adds the indicator to the base line before any state-specific formatting, so it appears for idle, running, and streaming agents alike.

The `★` character is used instead of `⬤` for better terminal compatibility. If `⬤` is preferred per spec, substitute it.

**Alternative approach** — if the indicator should only appear after the idle label:

Replace line 138:
```python
elif status.state == AgentState.IDLE:
    lines.append(f"{line} [dim]idle[/dim]")
```
with:
```python
elif status.state == AgentState.IDLE:
    idle_label = "[bold cyan]⬤ default[/bold cyan]" if is_default else "[dim]idle[/dim]"
    lines.append(f"{line} {idle_label}")
```

**Recommendation**: Use the first approach (indicator on all states) since the default agent may be running when the panel is viewed.

### Task 6.2: Panel Indicator Tests

**File**: `tests/test_ui/test_status_panel.py`

```python
def test_default_agent_shows_indicator(self):
    manager = AgentStatusManager()
    manager.set_default_agent("pm")
    panel = StatusPanel(status_manager=manager)
    output = panel._format_status()
    # Find pm line and verify indicator
    assert "★" in output  # or "⬤ default"
    # Verify non-default agent does NOT have indicator
    # pm line should have indicator, builder-1 line should not

def test_indicator_moves_when_default_changes(self):
    manager = AgentStatusManager()
    manager.set_default_agent("pm")
    panel = StatusPanel(status_manager=manager)
    manager.set_default_agent("builder-1")
    output = panel._format_status()
    # builder-1 line should now have indicator
```

---

## Phase 7: Wiring — REPL and UI Integration (Code-First)

### Task 7.1: Wire Router in loop.py

**File**: `src/teambot/repl/loop.py`

**Change**: Update line 58 to pass router to SystemCommands:

From:
```python
self._commands = SystemCommands()
```
To:
```python
self._commands = SystemCommands(router=self._router)
```

**Alternative** — if SystemCommands is created before router is fully configured, use setter approach later:
```python
self._commands.set_router(self._router)
```

Since `self._router` is created on line 57 (before `SystemCommands` on line 58), the constructor approach is cleaner.

### Task 7.2: Wire Router in app.py

**File**: `src/teambot/ui/app.py`

**Change 1 — Pass router to SystemCommands** (line 55):

From:
```python
self._commands = SystemCommands(executor=executor)
```
To:
```python
self._commands = SystemCommands(executor=executor, router=router)
```

**Change 2 — Initialize default agent on AgentStatusManager** (after line 58):

```python
if self._router:
    self._agent_status.set_default_agent(self._router.get_default_agent())
```

### Task 7.3: UI Post-Dispatch Update

**File**: `src/teambot/ui/app.py`

**Change**: In `_handle_system_command()`, after the `/model` post-dispatch handler (after line 312), add:

```python
# Update status panel if /use-agent or /reset-agent command succeeded
if command.command in ("use-agent", "reset-agent") and result.success:
    new_default = self._router.get_default_agent() if self._router else None
    self._agent_status.set_default_agent(new_default)
```

### Task 7.4: UI `_get_status()` Update

**File**: `src/teambot/ui/app.py`

**Change**: In `_get_status()`, add default agent info after the header (after line 414):

```python
lines = ["Agent Status:", ""]

# Show default agent
if self._router:
    current_default = self._router.get_default_agent()
    config_default = self._router.get_config_default_agent()
    if current_default != config_default:
        lines.append(
            f"  Default Agent: {current_default} "
            f"(session override; config: {config_default or 'none'})"
        )
    else:
        lines.append(f"  Default Agent: {current_default or 'none'}")
    lines.append("")
```

### Task 7.5: Wiring Integration Tests

**Files**: `tests/test_repl/test_loop.py`, `tests/test_ui/test_app.py`

**REPL wiring test**:
```python
def test_system_commands_has_router(self):
    """SystemCommands receives router reference in REPL mode."""
    # Create REPLLoop with config containing default_agent
    loop = REPLLoop(config={"default_agent": "pm"})
    assert loop._commands._router is not None
    assert loop._commands._router.get_default_agent() == "pm"
```

**UI wiring test**:
```python
def test_system_commands_has_router_in_ui(self):
    """SystemCommands receives router reference in UI mode."""
    router = AgentRouter(default_agent="pm")
    app = TeamBotApp(router=router)
    assert app._commands._router is router

def test_agent_status_initialized_with_default(self):
    """AgentStatusManager initialized with router's default agent."""
    router = AgentRouter(default_agent="pm")
    app = TeamBotApp(router=router)
    assert app._agent_status.get_default_agent() == "pm"
```

---

## File Change Summary

| File | Changes | Type |
|------|---------|------|
| `src/teambot/repl/router.py` | Add `_config_default_agent`, `set_default_agent()`, `get_config_default_agent()` | Extend |
| `src/teambot/repl/commands.py` | Add `handle_use_agent()`, `handle_reset_agent()`, extend `SystemCommands`, update `handle_help()`, update `handle_status()` | Extend + New |
| `src/teambot/ui/agent_state.py` | Add `_default_agent`, `set_default_agent()`, `get_default_agent()` | Extend |
| `src/teambot/ui/widgets/status_panel.py` | Add default indicator in `_format_status()` | Extend |
| `src/teambot/repl/loop.py` | Pass router to `SystemCommands` | Wire |
| `src/teambot/ui/app.py` | Pass router to `SystemCommands`, init default on status manager, post-dispatch update, `_get_status()` update | Extend + Wire |
| `tests/test_repl/test_router.py` | Add `TestRouterDefaultAgentMutation` | New tests |
| `tests/test_repl/test_commands.py` | Add `TestUseAgentCommand`, `TestResetAgentCommand`, help/status tests | New tests |
| `tests/test_ui/test_agent_state.py` | Add `TestAgentStatusManagerDefaultAgent` | New tests |
| `tests/test_ui/test_status_panel.py` | Add default indicator tests | New tests |
| `tests/test_repl/test_loop.py` | Add router wiring test | New tests |
| `tests/test_ui/test_app.py` | Add router wiring + status init tests | New tests |
