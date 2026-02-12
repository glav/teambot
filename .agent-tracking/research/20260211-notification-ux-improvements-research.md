<!-- markdownlint-disable-file -->
# Research Document: Notification UX Improvements

**Date**: 2026-02-11  
**Feature**: Notification UX Improvements (Header/Footer + `/notify` Command)  
**Status**: ✅ Research Complete  
**Spec Reference**: `.teambot/notification-ux-improvements/artifacts/feature_spec.md`

---

## 📋 Table of Contents

1. [Research Scope](#research-scope)
2. [Entry Point Analysis](#entry-point-analysis)
3. [Notification System Architecture](#notification-system-architecture)
4. [REPL Command Infrastructure](#repl-command-infrastructure)
5. [Implementation Guidance](#implementation-guidance)
6. [Testing Strategy Research](#testing-strategy-research)
7. [Task Implementation Requests](#task-implementation-requests)
8. [Potential Next Research](#potential-next-research)

---

## 📌 Research Scope

### Questions to Answer

1. ✅ How does the existing notification system work (EventBus, templates, channels)?
2. ✅ Where in ExecutionLoop should header/footer events be emitted?
3. ✅ How can `/notify` command access the EventBus from REPL context?
4. ✅ What new event types and templates are needed?
5. ✅ How does the existing test infrastructure work?

### Success Criteria

- [x] EventBus architecture documented
- [x] Event emission points in ExecutionLoop identified
- [x] `/notify` command integration path determined
- [x] Template patterns documented
- [x] Test infrastructure patterns captured

---

## 🔍 Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `/notify <msg>` REPL command | `loop.py` → `router.py` → `commands.py` | YES | ✅ Add `handle_notify()` handler |
| Orchestration run start | `cli.py:_run_orchestration()` → `ExecutionLoop.run()` | YES | ✅ Add `orchestration_started` event |
| Orchestration run complete | `ExecutionLoop.run()` exit | YES | ✅ Add `orchestration_completed` event |
| Interactive mode REPL | `loop.py` → `run_interactive_mode()` | NO (no orchestration) | N/A |

### Code Path Trace

#### Entry Point 1: `/notify <msg>` Command

1. User enters: `/notify Hello World`
2. Parsed by: `parser.py:parse_command()` → `CommandType.SYSTEM`
3. Routed by: `router.py:_route_system()` (Lines 177-182)
4. Dispatched by: `commands.py:SystemCommands.dispatch()` (Lines 673-696)
5. **Gap**: No `notify` handler registered in `handlers` dict (Line 673-687)

**Required Fix**: Add `"notify": self.notify` to handlers dict and implement `notify()` method.

#### Entry Point 2: Orchestration Run Start

1. User runs: `teambot run objectives/my-feature.md`
2. Handled by: `cli.py:cmd_run()` (starts orchestration)
3. Routes to: `cli.py:_run_orchestration()` (Lines 288-389)
4. Reaches: `ExecutionLoop.run()` entry (Line 135)
5. **Gap**: No `orchestration_started` event emitted at run start

**Required Fix**: Add event emission after `time_manager.start()` (Line 151).

#### Entry Point 3: Orchestration Run Complete

1. ExecutionLoop completes successfully
2. Handled by: `ExecutionLoop.run()` (Lines 135-225)
3. Returns: `ExecutionResult.COMPLETE` (Line 221)
4. **Gap**: No `orchestration_completed` event emitted before return

**Required Fix**: Add event emission before `_save_state(ExecutionResult.COMPLETE)` (Line 220).

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| `/notify` handler missing | Command returns "Unknown command" | Add handler to `SystemCommands.dispatch()` |
| `orchestration_started` event missing | No notification at run start | Add `on_progress()` call at run entry |
| `orchestration_completed` event missing | No notification at run complete | Add `on_progress()` call before return |
| EventBus not accessible in REPL | `/notify` cannot send notifications | Pass config to `SystemCommands` constructor |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## 🏗️ Notification System Architecture

### EventBus (`src/teambot/notifications/event_bus.py`)

**Purpose**: Pub/sub event bus that routes notification events to channels.

**Key Methods**:

| Method | Purpose | Lines |
|--------|---------|-------|
| `subscribe(channel)` | Add channel to receive events | 46-54 |
| `emit(event)` | Async emit to all matching channels | 69-97 |
| `emit_sync(event_type, data)` | Sync wrapper for emit - safe from callbacks | 127-161 |
| `create_progress_callback()` | Create callback for `on_progress` | 163-173 |
| `drain(timeout)` | Wait for pending tasks (graceful shutdown) | 175-202 |

**Key Characteristics**:
- Fire-and-forget: Channel failures don't block workflow
- Retry logic: 3 retries with exponential backoff for rate limits
- Context injection: Adds `feature_name` and `stage` to events
- Task tracking: Tracks pending tasks for graceful shutdown

**Constructor** (Lines 35-44):
```python
def __init__(self, feature_name: str | None = None):
    self._channels: list[NotificationChannel] = []
    self._feature_name = feature_name
    self._current_stage: str | None = None
    self._pending_tasks: set[asyncio.Task] = set()
```

### NotificationEvent (`src/teambot/notifications/events.py`)

**Dataclass** (Lines 10-28):
```python
@dataclass
class NotificationEvent:
    event_type: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    stage: str | None = None
    agent: str | None = None
    feature_name: str | None = None
```

### MessageTemplates (`src/teambot/notifications/templates.py`)

**Existing Templates** (Lines 24-43):
```python
TEMPLATES: dict[str, str] = {
    "stage_changed": "📌 <b>Stage: {stage}</b>...",
    "agent_running": "🔄 <b>{agent_id}</b> started...",
    "agent_complete": "✅ <b>{agent_id}</b> completed",
    "agent_failed": "❌ <b>{agent_id}</b> FAILED...",
    "parallel_group_start": "🚀 <b>Parallel Group: {group}</b>...",
    "parallel_group_complete": "{emoji} <b>Parallel Group: {group}</b>...",
    "parallel_stage_complete": "✅ <b>{stage}</b> completed...",
    "parallel_stage_failed": "❌ <b>{stage}</b> FAILED...",
    "acceptance_test_stage_complete": "{emoji} <b>Acceptance Tests</b>...",
    "acceptance_test_max_iterations_reached": "⚠️ <b>Max Fix Iterations Reached</b>...",
    "review_progress": "📝 <b>Review Progress</b>...",
}
```

**Render Method Pattern** (Lines 45-89):
- Builds context from `event.data` (with HTML escaping)
- Adds computed fields (emojis, status)
- Falls back gracefully for missing keys

**New Templates Required**:
```python
# Add to TEMPLATES dict
"orchestration_started": "🚀 <b>Starting</b>: {objective_name}",
"orchestration_completed": "✅ <b>Completed</b>: {objective_name}\n⏱️ Duration: {duration}",
"custom_message": "📢 {message}",
```

### NotificationChannel Protocol (`src/teambot/notifications/protocol.py`)

**Required Interface** (Lines 12-73):
- `name: str` - Channel identifier
- `enabled: bool` - Whether channel is active
- `send(event)` - Async send method
- `format(event)` - Format event to message
- `supports_event(event_type)` - Filter events

### TelegramChannel (`src/teambot/notifications/channels/telegram.py`)

**Key Implementation Notes**:
- Uses `httpx` for async HTTP
- HTML format for messages (`parse_mode: "HTML"`)
- Token/chat_id from environment variables
- Supports event filtering via `subscribed_events`
- **Supports all event types by default** (Line 71-75)

### Config Loading (`src/teambot/notifications/config.py`)

**Factory Function** (Lines 79-106):
```python
def create_event_bus_from_config(config: dict[str, Any], feature_name: str | None = None):
    notifications = config.get("notifications", {})
    if not notifications.get("enabled", False):
        return None
    bus = EventBus(feature_name=feature_name)
    for channel_config in notifications.get("channels", []):
        channel = _create_channel(channel_config)
        if channel:
            bus.subscribe(channel)
    return bus
```

---

## 🔧 REPL Command Infrastructure

### SystemCommands (`src/teambot/repl/commands.py`)

**Dispatch Pattern** (Lines 673-696):
```python
def dispatch(self, command: str, args: list[str]) -> CommandResult:
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
        "use-agent": self.use_agent,
        "reset-agent": self.reset_agent,
    }
    handler = handlers.get(command)
    if handler is None:
        return CommandResult(output=f"Unknown command: /{command}...")
    return handler(args)
```

**Handler Pattern** (e.g., `handle_models`, Lines 204-238):
```python
def handle_models(args: list[str]) -> CommandResult:
    """Handle /models command - list all available models."""
    # ... implementation ...
    return CommandResult(output="\n".join(lines))
```

**CommandResult Dataclass** (Lines 19-32):
```python
@dataclass
class CommandResult:
    output: str
    success: bool = True
    should_exit: bool = False
```

### `/notify` Command Integration Path

**Current Challenge**: 
- `SystemCommands` doesn't have access to `EventBus` or notification config
- REPL is initialized in `loop.py:REPLLoop.__init__()` with config, but `SystemCommands` only receives `orchestrator`, `executor`, `overlay`, and `router`

**Recommended Solution**:

1. **Add `config` parameter to `SystemCommands.__init__()`** (Lines 609-629):
```python
def __init__(
    self,
    orchestrator: Any = None,
    executor: Optional["TaskExecutor"] = None,
    overlay: Optional["OverlayRenderer"] = None,
    router: Optional["AgentRouter"] = None,
    config: dict | None = None,  # NEW
):
    # ...existing code...
    self._config = config  # Store for /notify
```

2. **Wire config in `REPLLoop.__init__()`** (Line 58):
```python
# Current
self._commands = SystemCommands(router=self._router)

# Change to
self._commands = SystemCommands(router=self._router, config=config)
```

3. **Implement `handle_notify()` method**:
```python
def notify(self, args: list[str]) -> CommandResult:
    """Handle /notify command - send test notification."""
    if not args:
        return CommandResult(
            output="Usage: /notify <message>",
            success=False,
        )
    
    # Check if notifications configured
    if not self._config:
        return CommandResult(
            output="❌ Notifications not configured.\n"
                   "Run `teambot init` or add `notifications` section to teambot.json.",
            success=False,
        )
    
    notifications = self._config.get("notifications", {})
    if not notifications.get("enabled", False):
        return CommandResult(
            output="❌ Notifications not enabled.\n"
                   "Set `notifications.enabled: true` in teambot.json.",
            success=False,
        )
    
    message = " ".join(args)
    
    # Create EventBus and send
    from teambot.notifications.config import create_event_bus_from_config
    
    event_bus = create_event_bus_from_config(self._config)
    if not event_bus or not event_bus._channels:
        return CommandResult(
            output="❌ No notification channels configured.\n"
                   "Add channels to `notifications.channels` in teambot.json.",
            success=False,
        )
    
    # Emit custom message event (synchronously schedule)
    event_bus.emit_sync("custom_message", {"message": message})
    
    return CommandResult(
        output=f"✅ Notification sent: {message}"
    )
```

4. **Register in dispatch handlers** (Line 686):
```python
handlers = {
    # ...existing handlers...
    "notify": self.notify,  # NEW
}
```

5. **Update `/help` output** (Line 90-120):
```python
# Add to help text
"  /notify <msg>  - Send test notification to all channels"
```

---

## 🚀 Implementation Guidance

### Task 1: Add New Event Types and Templates

**File**: `src/teambot/notifications/templates.py`

**Changes**:
1. Add new templates to `TEMPLATES` dict (after Line 43):
```python
"orchestration_started": "🚀 <b>Starting</b>: {objective_name}",
"orchestration_completed": "✅ <b>Completed</b>: {objective_name}\n⏱️ Duration: {duration}",
"custom_message": "📢 {message}",
```

2. Update `render()` method to handle new events (after Line 78):
```python
# Add handling for orchestration events
elif event.event_type == "orchestration_started":
    if "objective_name" not in context or not context["objective_name"]:
        context["objective_name"] = "orchestration run"
elif event.event_type == "orchestration_completed":
    if "objective_name" not in context or not context["objective_name"]:
        context["objective_name"] = "orchestration run"
    # Format duration if present
    duration_secs = event.data.get("duration_seconds", 0)
    context["duration"] = f"{int(duration_secs // 60)}m {int(duration_secs % 60)}s"
```

### Task 2: Emit Header/Footer Events in ExecutionLoop

**File**: `src/teambot/orchestration/execution_loop.py`

**Changes at run() entry** (after Line 151):
```python
async def run(
    self,
    sdk_client: Any,
    on_progress: Callable[[str, Any], None] | None = None,
) -> ExecutionResult:
    self.sdk_client = sdk_client
    self.review_iterator = ReviewIterator(sdk_client, self.teambot_dir)
    self.time_manager.start()

    # Emit orchestration started event
    if on_progress:
        on_progress("orchestration_started", {
            "objective_name": self.objective.description or self.feature_name,
            "objective_path": str(self.objective_path),
        })

    try:
        # ... existing loop code ...
```

**Changes at run() exit** (before Line 220-221):
```python
            # Emit orchestration completed event
            if on_progress:
                on_progress("orchestration_completed", {
                    "objective_name": self.objective.description or self.feature_name,
                    "status": ExecutionResult.COMPLETE.value,
                    "duration_seconds": self.time_manager.elapsed_seconds(),
                })

            self._save_state(ExecutionResult.COMPLETE)
            return ExecutionResult.COMPLETE
```

**Also handle other exit paths** (CANCELLED, TIMEOUT, etc.):
```python
# For CANCELLED (Line 157-158):
if on_progress:
    on_progress("orchestration_completed", {
        "objective_name": self.objective.description or self.feature_name,
        "status": ExecutionResult.CANCELLED.value,
        "duration_seconds": self.time_manager.elapsed_seconds(),
    })

# Similar for TIMEOUT, ERROR, etc.
```

### Task 3: Update CLI on_progress Callback

**File**: `src/teambot/cli.py`

**Changes to on_progress** (after Line 338):
```python
def on_progress(event_type: str, data: dict) -> None:
    # Console display logic
    if event_type == "stage_changed":
        display.print_success(f"Stage: {data.get('stage', 'unknown')}")
    elif event_type == "orchestration_started":  # NEW
        objective = data.get("objective_name", "orchestration run")
        display.print_success(f"🚀 Starting: {objective}")
    elif event_type == "orchestration_completed":  # NEW
        objective = data.get("objective_name", "orchestration run")
        status = data.get("status", "complete")
        duration = data.get("duration_seconds", 0)
        duration_str = f"{int(duration // 60)}m {int(duration % 60)}s"
        display.print_success(f"✅ Completed: {objective} ({duration_str})")
    elif event_type == "agent_running":
        # ... existing code ...
```

### Task 4: Implement `/notify` Command

**File**: `src/teambot/repl/commands.py`

See detailed implementation in [REPL Command Infrastructure](#repl-command-infrastructure) section above.

**Summary of changes**:
1. Add `config` parameter to `SystemCommands.__init__()`
2. Add `"notify": self.notify` to `dispatch()` handlers
3. Implement `notify()` method
4. Update `/help` output

**File**: `src/teambot/repl/loop.py`

**Changes** (Line 58):
```python
self._commands = SystemCommands(router=self._router, config=config)
```

### Task 5: Update `/help` Command

**File**: `src/teambot/repl/commands.py`

**Changes to handle_help()** (around Line 99):
```python
return CommandResult(
    output=f"""TeamBot Interactive Mode (Copilot SDK: {sdk_version})

Available commands:
  @agent <task>  - Send task to agent (pm, ba, writer, builder-1, builder-2, reviewer)
  /help          - Show this help message
  /help agent    - Show agent-specific help
  /help parallel - Show parallel execution help
  /notify <msg>  - Send test notification  # NEW
  /status        - Show agent status with models
  ...
"""
)
```

---

## 🧪 Testing Strategy Research

### Existing Test Infrastructure

**Framework**: pytest 8.x with pytest-mock, pytest-asyncio
**Location**: `tests/` directory (mirrors `src/` structure)
**Naming**: `test_*.py` pattern
**Runner**: `uv run pytest`
**Coverage**: coverage.py

### Test Patterns Found

**File**: `tests/test_notifications/test_event_bus.py` (Lines 1-436)

**Pattern Examples**:

1. **Fixture-based mocking**:
```python
@pytest.fixture
def mock_channel() -> MagicMock:
    channel = MagicMock()
    channel.name = "test-channel"
    channel.enabled = True
    channel.supports_event.return_value = True
    channel.send = AsyncMock(return_value=True)
    return channel
```

2. **Async test pattern**:
```python
@pytest.mark.asyncio
async def test_emit_calls_channel_send(
    self, mock_channel: MagicMock, sample_event: NotificationEvent
) -> None:
    bus = EventBus()
    bus.subscribe(mock_channel)
    await bus.emit(sample_event)
    await asyncio.sleep(0.05)  # Allow async task to complete
    mock_channel.send.assert_called_once()
```

3. **Sync test pattern** (for `emit_sync`):
```python
@pytest.mark.asyncio
async def test_emit_sync_sends_to_channel(self, mock_channel: MagicMock) -> None:
    bus = EventBus()
    bus.subscribe(mock_channel)
    bus.emit_sync("stage_changed", {"stage": "SETUP"})
    await asyncio.sleep(0.05)
    mock_channel.send.assert_called_once()
```

**File**: `tests/test_repl/test_commands.py` (Lines 1-200)

**Pattern Examples**:

1. **Command handler test**:
```python
def test_help_returns_command_list(self):
    result = handle_help([])
    assert result.success is True
    assert "@agent" in result.output
```

2. **SystemCommands dispatch test**:
```python
def test_dispatch_help(self):
    commands = SystemCommands()
    result = commands.dispatch("help", [])
    assert result.success is True
```

**File**: `tests/test_notifications/conftest.py` (Lines 1-45)

**Shared Fixtures**:
```python
@pytest.fixture
def sample_event() -> NotificationEvent:
    return NotificationEvent(
        event_type="stage_changed",
        data={"stage": "IMPLEMENTATION"},
        timestamp=datetime(2026, 2, 11, 12, 0, 0),
        feature_name="test-feature",
    )

@pytest.fixture
def mock_channel() -> MagicMock:
    channel = MagicMock()
    channel.name = "test-channel"
    channel.enabled = True
    channel.supports_event.return_value = True
    channel.send = AsyncMock(return_value=True)
    channel.format.return_value = "Formatted message"
    return channel
```

### Test Coverage Requirements

| Component | Type | Coverage Target | TDD/Code-First |
|-----------|------|-----------------|----------------|
| `handle_notify()` | Command handler | 100% | TDD |
| New templates | Template rendering | 100% | TDD |
| `orchestration_started` emission | Integration | 80% | Code-First |
| `orchestration_completed` emission | Integration | 80% | Code-First |
| Error paths | Edge cases | 90% | TDD |

### Recommended Test Files

1. **`tests/test_repl/test_commands_notify.py`** (NEW)
   - Test `handle_notify()` with valid message
   - Test `/notify` without arguments (usage help)
   - Test `/notify` with missing config
   - Test `/notify` with disabled notifications
   - Test `/notify` with no channels configured

2. **`tests/test_notifications/test_templates.py`** (EXTEND)
   - Test `orchestration_started` template rendering
   - Test `orchestration_completed` template rendering
   - Test `custom_message` template rendering
   - Test fallback for missing objective name

3. **`tests/test_orchestration/test_execution_loop_notifications.py`** (NEW or EXTEND)
   - Test `orchestration_started` event emission at run start
   - Test `orchestration_completed` event emission at run complete
   - Test events include correct data fields

### Example Test Implementation

```python
# tests/test_repl/test_commands_notify.py

import pytest
from unittest.mock import MagicMock, patch

from teambot.repl.commands import SystemCommands, CommandResult


class TestNotifyCommand:
    """Tests for /notify command."""

    def test_notify_without_args_shows_usage(self):
        """Test /notify without arguments returns usage help."""
        commands = SystemCommands(config={"notifications": {"enabled": True}})
        result = commands.notify([])
        
        assert result.success is False
        assert "Usage:" in result.output
        assert "/notify" in result.output

    def test_notify_without_config_shows_error(self):
        """Test /notify without config shows helpful error."""
        commands = SystemCommands(config=None)
        result = commands.notify(["test"])
        
        assert result.success is False
        assert "not configured" in result.output
        assert "teambot init" in result.output

    def test_notify_with_disabled_notifications_shows_error(self):
        """Test /notify with disabled notifications shows error."""
        commands = SystemCommands(config={"notifications": {"enabled": False}})
        result = commands.notify(["test"])
        
        assert result.success is False
        assert "not enabled" in result.output

    @patch("teambot.repl.commands.create_event_bus_from_config")
    def test_notify_success(self, mock_create_bus):
        """Test /notify successfully sends message."""
        mock_bus = MagicMock()
        mock_bus._channels = [MagicMock()]
        mock_create_bus.return_value = mock_bus
        
        commands = SystemCommands(config={
            "notifications": {"enabled": True, "channels": [{"type": "telegram"}]}
        })
        result = commands.notify(["Hello", "World"])
        
        assert result.success is True
        assert "✅" in result.output
        assert "Hello World" in result.output
        mock_bus.emit_sync.assert_called_once_with(
            "custom_message", {"message": "Hello World"}
        )
```

---

## 📋 Task Implementation Requests

### High Priority

| Task | Description | Files | Estimate |
|------|-------------|-------|----------|
| T-001 | Add `orchestration_started` template | `templates.py` | Small |
| T-002 | Add `orchestration_completed` template | `templates.py` | Small |
| T-003 | Add `custom_message` template | `templates.py` | Small |
| T-004 | Emit header event at run start | `execution_loop.py` | Small |
| T-005 | Emit footer event at run complete | `execution_loop.py` | Medium |
| T-006 | Handle header/footer in CLI on_progress | `cli.py` | Small |
| T-007 | Add config param to SystemCommands | `commands.py` | Small |
| T-008 | Implement `/notify` command handler | `commands.py` | Medium |
| T-009 | Wire config to SystemCommands in REPL | `loop.py` | Small |
| T-010 | Update `/help` with `/notify` | `commands.py` | Small |

### Medium Priority

| Task | Description | Files | Estimate |
|------|-------------|-------|----------|
| T-011 | Add tests for `/notify` command | `test_commands_notify.py` | Medium |
| T-012 | Add tests for new templates | `test_templates.py` | Small |
| T-013 | Add tests for header/footer emission | `test_execution_loop.py` | Medium |

---

## 🔮 Potential Next Research

All research items have been addressed. The implementation is ready to proceed.

---

## ✅ Research Validation

```
RESEARCH_VALIDATION: PASS
- Document: CREATED ✅
- Placeholders: 0 remaining ✅
- Technical Approach: DOCUMENTED ✅
- Entry Points: 4 traced, 4 covered ✅
- Test Infrastructure: RESEARCHED ✅
- Implementation Ready: YES ✅
```

---

## 📚 References

| Ref ID | Type | Source | Summary |
|--------|------|--------|---------|
| REF-001 | Spec | `.teambot/notification-ux-improvements/artifacts/feature_spec.md` | Feature specification |
| REF-002 | Code | `src/teambot/notifications/event_bus.py` | EventBus implementation |
| REF-003 | Code | `src/teambot/notifications/templates.py` | MessageTemplates patterns |
| REF-004 | Code | `src/teambot/repl/commands.py` | SystemCommands dispatcher |
| REF-005 | Code | `src/teambot/orchestration/execution_loop.py` | ExecutionLoop run method |
| REF-006 | Code | `src/teambot/cli.py` | on_progress callback |
| REF-007 | Test | `tests/test_notifications/test_event_bus.py` | Test patterns |
| REF-008 | Test | `tests/test_repl/test_commands.py` | Command test patterns |
