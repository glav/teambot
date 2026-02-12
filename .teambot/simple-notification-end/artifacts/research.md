<!-- markdownlint-disable-file -->
# Research: @notify Pseudo-Agent for Pipeline Notifications

## Overview

**Research Date**: 2026-02-12  
**Feature**: Simple notification at end of pipeline via `@notify` pseudo-agent  
**Objective**: Enable `@notify` as a first-class participant in agent pipelines that sends messages to configured notification channels without invoking the Copilot SDK

## Scope and Objectives

### Research Questions

1. How should `@notify` integrate with the existing `VALID_AGENTS` pattern?
2. How do commands flow through different entry points (legacy REPL vs split-pane UI)?
3. How can `@notify` bypass SDK execution while still participating in pipelines?
4. How should `$ref` syntax work with `@notify`?
5. How should the UI status display handle `@notify`?
6. What testing patterns should be followed?

### Success Criteria

- ✅ Technical approach validated
- ✅ Code patterns documented
- ✅ Entry point analysis complete
- ✅ Testing infrastructure researched

---

## Entry Point Analysis (CRITICAL)

### User Input Entry Points

| Entry Point | Code Path | Reaches @notify? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `@notify "msg"` (simple) | `loop.py → router._route_agent()` | YES (after changes) | YES - Add to VALID_AGENTS, handle in router |
| `@notify "msg"` (simple, split-pane) | `app.py → _handle_agent_command()` | YES (after changes) | YES - Add check before SDK call |
| `@pm task -> @notify "done"` (pipeline) | `executor.py → _execute_pipeline()` | YES (after changes) | YES - Intercept in executor |
| `@notify "msg" &` (background) | `executor.py → _execute_simple()` | YES (after changes) | YES - Handle in executor |
| `@notify "$pm" msg` (with $ref) | `executor.py → _execute_simple()` | YES (after changes) | YES - Inject refs then send |
| `@pm,notify task` (multi-agent) | `executor.py → _execute_multiagent()` | YES (after changes) | YES - Split handling |

### Code Path Trace

#### Entry Point 1: Simple @notify Command (Legacy REPL)
1. User enters: `@notify "Build complete!"`
2. Parsed by: `parser.py:parse_command()` (Lines 95-122) → Returns `Command(type=AGENT, agent_id="notify", ...)`
3. Routed by: `loop.py:run()` (Lines 323-331) → Checks if simple agent command
4. **Current gap**: Goes to `router._route_agent()` (Lines 160-175) which validates against `VALID_AGENTS`
5. **Fix needed**: Add "notify" to `VALID_AGENTS` OR intercept before validation

#### Entry Point 2: Simple @notify Command (Split-pane UI)
1. User enters: `@notify "Build complete!"`
2. Parsed by: `app.py:handle_input()` (Line 114)
3. Dispatched to: `app.py:_handle_agent_command()` (Lines 143-257)
4. Validates: Line 150-167 checks `VALID_AGENTS`
5. **Current gap**: Would fail validation
6. **Fix needed**: Add early intercept for "notify" before validation

#### Entry Point 3: Pipeline with @notify
1. User enters: `@pm plan -> @notify "Planning done!"`
2. Parsed by: `parser.py:_parse_pipeline()` (Lines 206-289)
3. Validated: Lines 257-262 check each stage agent against `VALID_AGENTS`
4. Executed by: `executor.py:_execute_pipeline()` (Lines 405-562)
5. **Current gap**: Validation fails at parse time
6. **Fix needed**: Add "notify" to VALID_AGENTS + special handling in executor

#### Entry Point 4: @notify with $ref
1. User enters: `@notify "Review done: $reviewer"`
2. Parsed with references: `parser.py` extracts `references=["reviewer"]`
3. Executor waits for refs: `executor.py:_wait_for_references()` (Lines 286-297)
4. Injects outputs: `executor.py:_inject_references()` (Lines 299-318)
5. **Fix needed**: After injection, send to notification system instead of SDK

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| `VALID_AGENTS` doesn't include "notify" | All @notify commands fail validation | Add "notify" to set |
| Router calls SDK handler for all agent commands | @notify would call Copilot API | Add intercept before SDK call |
| UI validates before handling | Split-pane UI rejects @notify | Add early check in `_handle_agent_command` |
| Parser pipeline validation | Pipelines with @notify fail at parse | Already uses VALID_AGENTS (will work once added) |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## Technical Approach

### Recommended Architecture: Pseudo-Agent in Executor

**Approach**: Add `"notify"` to `VALID_AGENTS` and handle it specially in the `TaskExecutor` before any SDK call is made.

#### Why This Approach

1. **Minimal code changes** - Only modify `router.py` (add to set) and `executor.py` (add intercept)
2. **Works with all pipeline features** - Background, $ref, multi-agent all flow through executor
3. **Consistent with existing patterns** - Similar to how agent validation already works
4. **Non-breaking** - All existing functionality preserved

#### Implementation Steps

1. **Add "notify" to VALID_AGENTS** (`router.py:20`)
   ```python
   VALID_AGENTS = {"pm", "ba", "writer", "builder-1", "builder-2", "reviewer", "notify"}
   ```

2. **Add pseudo-agent detection helper** (new in `executor.py`)
   ```python
   PSEUDO_AGENTS = {"notify"}
   
   def is_pseudo_agent(agent_id: str) -> bool:
       """Check if agent is a pseudo-agent (not using SDK)."""
       return agent_id in PSEUDO_AGENTS
   ```

3. **Intercept in `_execute_simple()`** (`executor.py:205-284`)
   - After $ref injection but before task creation
   - Handle notification sending directly
   - Return synthetic result for downstream $ref

4. **Intercept in `_execute_pipeline()`** (`executor.py:405-562`)
   - Check each stage's agent_ids for "notify"
   - Handle notification stages inline
   - Continue pipeline execution

5. **Intercept in `_execute_multiagent()`** (`executor.py:320-403`)
   - Filter out "notify" from parallel execution
   - Handle separately from SDK-based agents

6. **Intercept in UI** (`app.py:143-257`)
   - Check for "notify" before SDK streaming
   - Handle inline without SDK call

### Alternative Approaches (Not Recommended)

#### Alternative A: Separate Command Type
- Add `NOTIFICATION` to `CommandType` enum
- Parse `@notify` differently than other agents
- **Rejected**: Too invasive, breaks pipeline syntax consistency

#### Alternative B: System Command Extension  
- Make notification a `/notify` pipeline participant
- Use special syntax like `@pm plan -> /notify "done"`
- **Rejected**: Mixes system and agent command paradigms

---

## Notification Integration

### Existing Infrastructure

The notification system is well-established:

| Component | Location | Purpose |
|-----------|----------|---------|
| `EventBus` | `notifications/event_bus.py` | Fire-and-forget message dispatch |
| `NotificationChannel` | `notifications/protocol.py` | Channel interface |
| `TelegramChannel` | `notifications/channels/telegram.py` | Telegram implementation |
| `MessageTemplates` | `notifications/templates.py` | Event→message formatting |
| `create_event_bus_from_config` | `notifications/config.py` | Config-based bus creation |

### Current /notify Implementation

The existing `/notify` system command (`commands.py:762-828`) provides a pattern:

```python
def notify(self, args: list[str]) -> CommandResult:
    # 1. Validate message exists
    if not args:
        return CommandResult(output="Usage: /notify <message>", success=False)
    
    # 2. Validate config
    if not self._config:
        return CommandResult(output="❌ Notifications not configured", success=False)
    
    # 3. Check notifications enabled
    notifications = self._config.get("notifications", {})
    if not notifications.get("enabled", False):
        return CommandResult(output="❌ Notifications not enabled", success=False)
    
    # 4. Create EventBus and send
    message = " ".join(args)
    event_bus = create_event_bus_from_config(self._config)
    event_bus.emit_sync("custom_message", {"message": message})
    
    return CommandResult(output=f"✅ Notification sent: {message}")
```

### @notify Implementation Pattern

The `@notify` handler should:

1. **Accept message from prompt** - `@notify "Build complete!"`
2. **Support $ref interpolation** - `@notify "Review: $reviewer"` 
3. **Truncate large outputs** - Limit referenced content to ~500 chars
4. **Use EventBus.emit_sync()** - Fire-and-forget, non-blocking
5. **Return confirmation** - Store "Notification sent ✅" as result
6. **Handle failures gracefully** - Log warning, continue pipeline

### $ref Truncation Strategy

When `$ref` outputs are interpolated:

```python
MAX_REF_LENGTH = 500
TRUNCATION_SUFFIX = "... [truncated]"

def truncate_for_notification(text: str) -> str:
    """Truncate text for notification readability."""
    if len(text) <= MAX_REF_LENGTH:
        return text
    return text[:MAX_REF_LENGTH - len(TRUNCATION_SUFFIX)] + TRUNCATION_SUFFIX
```

---

## UI Status Panel Integration

### Current Agent Status Display

The `StatusPanel` (`ui/widgets/status_panel.py:101-151`) displays:

```
Agents
● pm          idle
● ba          idle
● writer      idle
● builder-1   idle
● builder-2   idle
● reviewer    idle
```

### Adding @notify

Include `"notify"` in `DEFAULT_AGENTS` (`ui/agent_state.py:73`):

```python
DEFAULT_AGENTS = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer", "notify"]
```

Display with special model indicator:

```python
# In StatusPanel._format_status()
if agent_id == "notify":
    # Show (n/a) instead of model name
    line += f" [dim italic](n/a)[/dim italic]"
```

Expected display:
```
Agents
● pm          idle
● ba          idle
● writer      idle
● builder-1   idle
● builder-2   idle
● reviewer    idle
● notify      (n/a) idle
```

---

## Legacy /notify Removal

### Current State
- `/notify` command in `SystemCommands.dispatch()` handlers dict (Line 691)
- Handler at `SystemCommands.notify()` (Lines 762-828)

### Removal Steps
1. Remove `"notify": self.notify` from handlers dict
2. Delete `notify()` method from `SystemCommands`
3. Update `/help` output to remove `/notify` reference
4. Update tests to remove `/notify` test cases

### Migration Note
Users attempting `/notify` after removal will see:
```
Unknown command: /notify. Type /help for available commands.
```

---

## Code Patterns and Examples

### Executor Pattern for Pseudo-Agent

```python
# In executor.py

async def _execute_simple(self, command: Command) -> ExecutionResult:
    agent_id = command.agent_ids[0]
    
    # Check for $ref dependencies (works for @notify too)
    if command.references:
        await self._wait_for_references(command.references)
        prompt = self._inject_references(command.content, command.references)
    else:
        prompt = command.content
    
    # === NEW: Handle @notify pseudo-agent ===
    if agent_id == "notify":
        return await self._handle_notify(prompt, command.background)
    
    # Continue with normal SDK execution...
    task = self._manager.create_task(...)


async def _handle_notify(self, message: str, background: bool) -> ExecutionResult:
    """Handle @notify pseudo-agent.
    
    Args:
        message: Notification message (may include interpolated $ref content)
        background: Whether running in background mode
        
    Returns:
        ExecutionResult with confirmation output
    """
    # Truncate if message too long
    if len(message) > 1000:
        message = message[:997] + "..."
    
    try:
        # Get config from somewhere accessible
        event_bus = create_event_bus_from_config(self._config)
        if event_bus and event_bus._channels:
            event_bus.emit_sync("custom_message", {"message": message})
            output = "Notification sent ✅"
        else:
            output = "⚠️ No notification channels configured"
            logger.warning("@notify: No notification channels configured")
    except Exception as e:
        output = f"⚠️ Notification failed: {e}"
        logger.warning(f"@notify failed: {e}")
    
    # Store result for potential $notify references
    synthetic_result = TaskResult(success=True, output=output)
    self._manager._agent_results["notify"] = synthetic_result
    
    return ExecutionResult(
        success=True,
        output=output,
        task_id=None,  # No task created
        task_ids=[],
        background=background,
    )
```

### Pipeline Stage Check Pattern

```python
# In executor.py:_execute_pipeline()

for i, stage in enumerate(command.pipeline):
    # ... existing setup ...
    
    for agent_id in stage.agent_ids:
        # === NEW: Handle @notify in pipeline ===
        if agent_id == "notify":
            # Inject refs from previous stages
            if i > 0:
                prompt = self._inject_references(stage.content, ...)
            else:
                prompt = stage.content
            
            notify_result = await self._handle_notify(prompt, command.background)
            # Continue pipeline...
            continue
        
        # Normal agent handling...
```

---

## Testing Strategy Research

### Existing Test Framework

| Item | Value |
|------|-------|
| **Framework** | pytest 7.x with pytest-mock |
| **Location** | `tests/` directory (mirrors `src/` structure) |
| **Naming** | `test_*.py` pattern |
| **Runner** | `uv run pytest` |
| **Coverage** | pytest-cov with 80% target |

### Test Patterns Found

#### Test File: `tests/test_repl/test_commands.py`
- Uses `MagicMock` for dependencies
- Uses `@patch` decorator for module mocking
- Clear arrange-act-assert structure
- Tests both success and failure cases

Example pattern (Lines 495-526):
```python
@patch("teambot.notifications.config.create_event_bus_from_config")
def test_notify_success(self, mock_create_bus):
    """Test /notify successfully sends message."""
    mock_bus = MagicMock()
    mock_bus._channels = [MagicMock()]
    mock_create_bus.return_value = mock_bus

    commands = SystemCommands(
        config={"notifications": {"enabled": True, "channels": [{"type": "telegram"}]}}
    )
    result = commands.notify(["Hello", "World"])

    assert result.success is True
    assert "✅" in result.output
    mock_bus.emit_sync.assert_called_once_with("custom_message", {"message": "Hello World"})
```

#### Test File: `tests/test_tasks/test_executor.py`
- Uses `AsyncMock` for async SDK client
- Uses `pytest.mark.asyncio` for async tests
- Tests command parsing through `parse_command()`

Example pattern (Lines 24-36):
```python
@pytest.mark.asyncio
async def test_execute_simple_command(self):
    """Test executing simple @agent command."""
    mock_sdk = AsyncMock()
    mock_sdk.execute = AsyncMock(return_value="Task completed")

    executor = TaskExecutor(sdk_client=mock_sdk)
    cmd = parse_command("@pm Create a plan")

    result = await executor.execute(cmd)

    assert result.success
    assert "Task completed" in result.output
    mock_sdk.execute.assert_called_once()
```

### Test Coverage Requirements

| Component | Coverage Target | Approach |
|-----------|-----------------|----------|
| @notify parsing | 100% | Unit tests in `test_parser.py` |
| @notify execution | 100% | Async tests in `test_executor.py` |
| @notify with $ref | 100% | Integration tests |
| @notify in pipeline | 100% | Integration tests |
| Notification failure handling | 100% | Mock failure scenarios |
| UI status display | 80% | Snapshot/component tests |
| Legacy /notify removal | 100% | Verify command removed |

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| Parser changes | TDD | Well-defined input/output |
| Executor @notify handling | TDD | Critical business logic |
| UI status panel | Code-First | UI changes, simpler logic |
| Integration (pipeline) | Code-First | Complex setup, verify end-to-end |

---

## Task Implementation Requests

### 1. Add "notify" to VALID_AGENTS
- File: `src/teambot/repl/router.py:20`
- Change: Add "notify" to the set
- Impact: Enables @notify parsing

### 2. Add "notify" to DEFAULT_AGENTS for UI
- File: `src/teambot/ui/agent_state.py:73`
- Change: Add "notify" to the list
- Impact: Shows @notify in status panel

### 3. Implement @notify handler in TaskExecutor
- File: `src/teambot/tasks/executor.py`
- Add: `_handle_notify()` method
- Add: Check for "notify" in `_execute_simple()`, `_execute_pipeline()`, `_execute_multiagent()`
- Impact: Core notification functionality

### 4. Add config access to TaskExecutor
- File: `src/teambot/tasks/executor.py`
- Change: Add `config` parameter to `__init__`
- Impact: Enables notification channel access

### 5. Update UI to bypass SDK for @notify
- File: `src/teambot/ui/app.py`
- Change: Check for "notify" before SDK calls
- Impact: UI won't attempt SDK streaming for @notify

### 6. Update StatusPanel for @notify display
- File: `src/teambot/ui/widgets/status_panel.py`
- Change: Show "(n/a)" as model for notify
- Impact: Clear UI indication of pseudo-agent

### 7. Remove legacy /notify command
- File: `src/teambot/repl/commands.py`
- Remove: `notify` from handlers dict and method
- Update: `/help` output
- Impact: Single notification interface

### 8. Add comprehensive tests
- Files: `tests/test_repl/test_parser.py`, `tests/test_tasks/test_executor.py`, etc.
- Add: Unit and integration tests for all @notify scenarios
- Impact: Ensure correctness and prevent regressions

---

## Potential Next Research

### Completed ✅
- Entry point analysis
- Notification system integration
- Testing infrastructure analysis
- UI status panel patterns
- $ref interpolation handling

### No Additional Research Needed
The implementation path is clear. All technical questions have been answered through code analysis.

---

## References

| File | Lines | Content |
|------|-------|---------|
| `src/teambot/repl/router.py` | 20 | `VALID_AGENTS` definition |
| `src/teambot/repl/parser.py` | 87-89 | `$ref` pattern matching |
| `src/teambot/tasks/executor.py` | 205-284 | `_execute_simple()` implementation |
| `src/teambot/tasks/executor.py` | 405-562 | `_execute_pipeline()` implementation |
| `src/teambot/tasks/manager.py` | 46 | `_agent_results` storage |
| `src/teambot/notifications/config.py` | 79-107 | `create_event_bus_from_config()` |
| `src/teambot/notifications/event_bus.py` | 127-161 | `emit_sync()` implementation |
| `src/teambot/repl/commands.py` | 762-828 | Existing `/notify` implementation |
| `src/teambot/ui/agent_state.py` | 73 | `DEFAULT_AGENTS` list |
| `src/teambot/ui/widgets/status_panel.py` | 101-151 | Status formatting |
| `tests/test_repl/test_commands.py` | 421-555 | `/notify` test patterns |
| `tests/test_tasks/test_executor.py` | 1-200 | Executor test patterns |
