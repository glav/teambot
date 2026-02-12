<!-- markdownlint-disable-file -->
# Implementation Details: Notification UX Improvements

**Research Reference**: `.teambot/notification-ux-improvements/artifacts/research.md`
**Test Strategy Reference**: `.teambot/notification-ux-improvements/artifacts/test_strategy.md`
**Plan Reference**: `.agent-tracking/plans/20260211-notification-ux-improvements-plan.instructions.md`

---

## Phase 1: Templates & Events (TDD)

### Task 1.1: Add new templates to TEMPLATES dict

**File**: `src/teambot/notifications/templates.py`
**Research Reference**: Lines 150-178 of research.md

**Current State** (Lines 24-43 of templates.py):
```python
TEMPLATES: dict[str, str] = {
    "stage_changed": "📌 <b>Stage: {stage}</b>...",
    "agent_running": "🔄 <b>{agent_id}</b> started...",
    # ... existing templates
}
```

**Implementation**:
Add three new templates after Line 43:
```python
    # Orchestration lifecycle events
    "orchestration_started": "🚀 <b>Starting</b>: {objective_name}",
    "orchestration_completed": "✅ <b>Completed</b>: {objective_name}\n⏱️ Duration: {duration}",
    "custom_message": "📢 {message}",
```

**Success Criteria**:
- [ ] Templates added to TEMPLATES dict
- [ ] Template strings use correct placeholders
- [ ] Templates follow existing format pattern (emoji + HTML bold)

---

### Task 1.2: Update render() method for new event types

**File**: `src/teambot/notifications/templates.py`
**Research Reference**: Lines 167-181 of research.md

**Current State** (render method around Lines 45-89):
The render() method builds context from event.data with HTML escaping.

**Implementation**:
Add handling for new event types in the context building section (around Line 78):

```python
# Handle orchestration lifecycle events
if event.event_type == "orchestration_started":
    # Fallback for missing objective_name
    if "objective_name" not in context or not context["objective_name"]:
        context["objective_name"] = "orchestration run"

elif event.event_type == "orchestration_completed":
    # Fallback for missing objective_name
    if "objective_name" not in context or not context["objective_name"]:
        context["objective_name"] = "orchestration run"
    # Format duration from seconds
    duration_secs = event.data.get("duration_seconds", 0)
    minutes = int(duration_secs // 60)
    seconds = int(duration_secs % 60)
    context["duration"] = f"{minutes}m {seconds}s"

elif event.event_type == "custom_message":
    # Message should already be HTML-escaped via context building
    pass
```

**Success Criteria**:
- [ ] Missing objective_name falls back to "orchestration run"
- [ ] Duration formatted as "Xm Ys"
- [ ] HTML escaping applied to objective_name and message
- [ ] Render returns formatted string for all three event types

---

### Task 1.3: Template unit tests

**File**: `tests/test_notifications/test_templates.py` (extend existing)
**Research Reference**: Lines 504-591 of research.md

**Test Cases to Add**:

```python
class TestOrchestrationStartedTemplate:
    """Tests for orchestration_started template rendering."""

    @pytest.fixture
    def templates(self) -> MessageTemplates:
        return MessageTemplates()

    def test_render_with_objective_name(self, templates: MessageTemplates) -> None:
        """Renders with objective name when provided."""
        event = NotificationEvent(
            event_type="orchestration_started",
            data={"objective_name": "my-feature", "objective_path": "/path/to/obj.md"},
        )
        result = templates.render(event)
        assert "🚀" in result
        assert "Starting" in result
        assert "my-feature" in result

    def test_render_fallback_when_name_missing(self, templates: MessageTemplates) -> None:
        """Falls back to generic text when objective_name missing."""
        event = NotificationEvent(
            event_type="orchestration_started",
            data={"objective_path": "/path/to/obj.md"},
        )
        result = templates.render(event)
        assert "orchestration run" in result.lower()

    def test_escapes_html_in_objective_name(self, templates: MessageTemplates) -> None:
        """HTML characters in objective_name are escaped."""
        event = NotificationEvent(
            event_type="orchestration_started",
            data={"objective_name": "<script>alert('xss')</script>"},
        )
        result = templates.render(event)
        assert "&lt;script&gt;" in result
        assert "<script>" not in result


class TestOrchestrationCompletedTemplate:
    """Tests for orchestration_completed template rendering."""

    @pytest.fixture
    def templates(self) -> MessageTemplates:
        return MessageTemplates()

    def test_render_with_duration(self, templates: MessageTemplates) -> None:
        """Renders with formatted duration."""
        event = NotificationEvent(
            event_type="orchestration_completed",
            data={
                "objective_name": "my-feature",
                "duration_seconds": 125,  # 2m 5s
            },
        )
        result = templates.render(event)
        assert "✅" in result
        assert "Completed" in result
        assert "my-feature" in result
        assert "2m 5s" in result

    def test_render_fallback_when_name_missing(self, templates: MessageTemplates) -> None:
        """Falls back to generic text when objective_name missing."""
        event = NotificationEvent(
            event_type="orchestration_completed",
            data={"duration_seconds": 60},
        )
        result = templates.render(event)
        assert "orchestration run" in result.lower()


class TestCustomMessageTemplate:
    """Tests for custom_message template rendering."""

    @pytest.fixture
    def templates(self) -> MessageTemplates:
        return MessageTemplates()

    def test_render_user_message(self, templates: MessageTemplates) -> None:
        """Renders user message."""
        event = NotificationEvent(
            event_type="custom_message",
            data={"message": "Hello from TeamBot!"},
        )
        result = templates.render(event)
        assert "📢" in result
        assert "Hello from TeamBot!" in result

    def test_escapes_html_in_message(self, templates: MessageTemplates) -> None:
        """HTML in user message is escaped."""
        event = NotificationEvent(
            event_type="custom_message",
            data={"message": "<b>bold</b>"},
        )
        result = templates.render(event)
        assert "&lt;b&gt;bold&lt;/b&gt;" in result
        assert "<b>bold</b>" not in result
```

**Success Criteria**:
- [ ] All template rendering tests pass
- [ ] Fallback behavior tested
- [ ] HTML escaping tested
- [ ] 100% coverage on new template code

---

## Phase 2: Event Emission (TDD)

### Task 2.1: Emit orchestration_started event at run() entry

**File**: `src/teambot/orchestration/execution_loop.py`
**Research Reference**: Lines 387-406 of research.md

**Current State** (around Lines 135-155):
```python
async def run(
    self,
    sdk_client: Any,
    on_progress: Callable[[str, Any], None] | None = None,
) -> ExecutionResult:
    self.sdk_client = sdk_client
    self.review_iterator = ReviewIterator(sdk_client, self.teambot_dir)
    self.time_manager.start()
    # ... existing code
```

**Implementation**:
Add event emission after `time_manager.start()` (around Line 151):

```python
    self.time_manager.start()

    # Emit orchestration started event
    if on_progress:
        objective_name = (
            self.objective.description
            if hasattr(self.objective, 'description') and self.objective.description
            else self.feature_name
        )
        on_progress("orchestration_started", {
            "objective_name": objective_name,
            "objective_path": str(self.objective_path) if self.objective_path else None,
        })
```

**Success Criteria**:
- [ ] Event emitted after time_manager.start()
- [ ] Event includes objective_name (with fallback to feature_name)
- [ ] Event includes objective_path
- [ ] No exception if on_progress is None

---

### Task 2.2: Emit orchestration_completed event at run() exit

**File**: `src/teambot/orchestration/execution_loop.py`
**Research Reference**: Lines 408-434 of research.md

**Current State** (around Lines 215-225):
```python
            # Successful completion
            self._save_state(ExecutionResult.COMPLETE)
            return ExecutionResult.COMPLETE
```

**Implementation**:
Add event emission before save_state for COMPLETE path (around Line 220):

```python
            # Emit orchestration completed event
            if on_progress:
                objective_name = (
                    self.objective.description
                    if hasattr(self.objective, 'description') and self.objective.description
                    else self.feature_name
                )
                on_progress("orchestration_completed", {
                    "objective_name": objective_name,
                    "status": "complete",
                    "duration_seconds": self.time_manager.elapsed_seconds(),
                })

            self._save_state(ExecutionResult.COMPLETE)
            return ExecutionResult.COMPLETE
```

**Also handle other exit paths**:
- CANCELLED (around Line 157-158)
- TIMEOUT (if applicable)
- ERROR paths

For each exit path, emit with appropriate status:
```python
on_progress("orchestration_completed", {
    "objective_name": objective_name,
    "status": "cancelled",  # or "timeout", "error"
    "duration_seconds": self.time_manager.elapsed_seconds(),
})
```

**Success Criteria**:
- [ ] Event emitted before _save_state()
- [ ] Event includes objective_name, status, duration_seconds
- [ ] All exit paths emit completion event
- [ ] Duration calculated correctly

---

### Task 2.3: Handle new events in CLI on_progress callback

**File**: `src/teambot/cli.py`
**Research Reference**: Lines 436-457 of research.md

**Current State** (on_progress callback around Lines 330-380):
```python
def on_progress(event_type: str, data: dict) -> None:
    if event_type == "stage_changed":
        display.print_success(f"Stage: {data.get('stage', 'unknown')}")
    elif event_type == "agent_running":
        # ... existing handlers
```

**Implementation**:
Add handlers for new event types:

```python
def on_progress(event_type: str, data: dict) -> None:
    if event_type == "stage_changed":
        display.print_success(f"Stage: {data.get('stage', 'unknown')}")
    elif event_type == "orchestration_started":
        objective = data.get("objective_name", "orchestration run")
        display.print_success(f"🚀 Starting: {objective}")
    elif event_type == "orchestration_completed":
        objective = data.get("objective_name", "orchestration run")
        status = data.get("status", "complete")
        duration = data.get("duration_seconds", 0)
        duration_str = f"{int(duration // 60)}m {int(duration % 60)}s"
        emoji = "✅" if status == "complete" else "⚠️"
        display.print_success(f"{emoji} Completed: {objective} ({duration_str})")
    elif event_type == "agent_running":
        # ... existing code
```

**Success Criteria**:
- [ ] Started event displays "🚀 Starting: {name}"
- [ ] Completed event displays "✅ Completed: {name} ({duration})"
- [ ] Fallback to "orchestration run" if name missing
- [ ] Different emoji for non-complete status

---

### Task 2.4: Add event emission tests

**File**: `tests/test_orchestration/test_execution_loop.py` (extend)
**Research Reference**: Lines 622-627 of research.md

**Test Cases to Add**:

```python
class TestOrchestrationLifecycleEvents:
    """Tests for orchestration lifecycle event emission."""

    @pytest.fixture
    def mock_progress_callback(self) -> MagicMock:
        return MagicMock()

    @pytest.mark.asyncio
    async def test_emits_started_event_at_run_entry(
        self, mock_progress_callback: MagicMock
    ) -> None:
        """Emits orchestration_started at run() entry."""
        # Setup execution loop with mock sdk_client
        # Call run() with on_progress=mock_progress_callback
        # Assert orchestration_started was called first
        mock_progress_callback.assert_any_call(
            "orchestration_started",
            {
                "objective_name": "test-objective",
                "objective_path": "/path/to/objective.md",
            },
        )

    @pytest.mark.asyncio
    async def test_started_event_includes_objective_name(
        self, mock_progress_callback: MagicMock
    ) -> None:
        """Started event includes objective_name from objective."""
        # Test that objective.description is used when available
        pass

    @pytest.mark.asyncio
    async def test_emits_completed_event_on_success(
        self, mock_progress_callback: MagicMock
    ) -> None:
        """Emits orchestration_completed on successful completion."""
        # Assert orchestration_completed was called
        # Assert includes duration_seconds > 0
        pass

    @pytest.mark.asyncio
    async def test_completed_event_includes_duration(
        self, mock_progress_callback: MagicMock
    ) -> None:
        """Completed event includes duration_seconds."""
        # Verify duration is reasonable (matches elapsed time)
        pass
```

**Success Criteria**:
- [ ] Test verifies started event emitted at entry
- [ ] Test verifies completed event emitted at exit
- [ ] Test verifies event data contains required fields
- [ ] Tests follow existing patterns in test file

---

## Phase 3: /notify Command (Code-First)

### Task 3.1: Add config parameter to SystemCommands

**File**: `src/teambot/repl/commands.py`
**Research Reference**: Lines 269-290 of research.md

**Current State** (Lines 609-629):
```python
def __init__(
    self,
    orchestrator: Any = None,
    executor: Optional["TaskExecutor"] = None,
    overlay: Optional["OverlayRenderer"] = None,
    router: Optional["AgentRouter"] = None,
):
    self._orchestrator = orchestrator
    self._executor = executor
    self._overlay = overlay
    self._router = router
```

**Implementation**:
Add config parameter:

```python
def __init__(
    self,
    orchestrator: Any = None,
    executor: Optional["TaskExecutor"] = None,
    overlay: Optional["OverlayRenderer"] = None,
    router: Optional["AgentRouter"] = None,
    config: dict | None = None,
):
    self._orchestrator = orchestrator
    self._executor = executor
    self._overlay = overlay
    self._router = router
    self._config = config
```

**Also update** `src/teambot/repl/loop.py` (around Line 58):
```python
# Current
self._commands = SystemCommands(router=self._router)

# Change to
self._commands = SystemCommands(router=self._router, config=config)
```

**Success Criteria**:
- [ ] SystemCommands.__init__() accepts config parameter
- [ ] Config stored as self._config
- [ ] REPLLoop passes config to SystemCommands

---

### Task 3.2: Implement notify() handler method

**File**: `src/teambot/repl/commands.py`
**Research Reference**: Lines 292-337 of research.md

**Implementation**:
Add notify() method to SystemCommands class:

```python
def notify(self, args: list[str]) -> CommandResult:
    """Handle /notify command - send test notification."""
    # Check for missing message argument
    if not args:
        return CommandResult(
            output="Usage: /notify <message>\n\nSend a test notification to all configured channels.",
            success=False,
        )

    # Check if config available
    if not self._config:
        return CommandResult(
            output="❌ Notifications not configured.\n"
                   "Run `teambot init` or add `notifications` section to teambot.json.",
            success=False,
        )

    # Check if notifications enabled
    notifications = self._config.get("notifications", {})
    if not notifications.get("enabled", False):
        return CommandResult(
            output="❌ Notifications not enabled.\n"
                   "Set `notifications.enabled: true` in teambot.json.",
            success=False,
        )

    # Check for channels
    if not notifications.get("channels"):
        return CommandResult(
            output="❌ No notification channels configured.\n"
                   "Add channels to `notifications.channels` in teambot.json.",
            success=False,
        )

    message = " ".join(args)

    # Create EventBus and send
    try:
        from teambot.notifications.config import create_event_bus_from_config

        event_bus = create_event_bus_from_config(self._config)
        if not event_bus or not event_bus._channels:
            return CommandResult(
                output="❌ Failed to create notification channels.\n"
                       "Check your notification configuration.",
                success=False,
            )

        # Emit custom message event (synchronously schedule)
        event_bus.emit_sync("custom_message", {"message": message})

        return CommandResult(
            output=f"✅ Notification sent: {message}"
        )
    except Exception as e:
        return CommandResult(
            output=f"❌ Failed to send notification: {e}",
            success=False,
        )
```

**Success Criteria**:
- [ ] Returns usage help when no args
- [ ] Returns helpful error when config missing
- [ ] Returns helpful error when notifications disabled
- [ ] Returns helpful error when no channels configured
- [ ] Successfully sends message via EventBus
- [ ] Returns success confirmation with message

---

### Task 3.3: Register notify in dispatch handlers

**File**: `src/teambot/repl/commands.py`
**Research Reference**: Lines 339-345 of research.md

**Current State** (Lines 673-687):
```python
def dispatch(self, command: str, args: list[str]) -> CommandResult:
    handlers = {
        "help": self.help,
        "status": self.status,
        # ... other handlers
        "reset-agent": self.reset_agent,
    }
```

**Implementation**:
Add notify to handlers dict:

```python
    handlers = {
        "help": self.help,
        "status": self.status,
        # ... existing handlers
        "reset-agent": self.reset_agent,
        "notify": self.notify,  # NEW
    }
```

**Success Criteria**:
- [ ] "notify" key added to handlers dict
- [ ] Maps to self.notify method
- [ ] Command dispatches correctly

---

### Task 3.4: Update /help output

**File**: `src/teambot/repl/commands.py`
**Research Reference**: Lines 347-351 of research.md

**Current State** (handle_help around Lines 90-120):
The help text lists available commands.

**Implementation**:
Add /notify to the command list:

```python
# In the help output string, add:
"  /notify <msg>  - Send test notification to all channels"
```

**Success Criteria**:
- [ ] /notify listed in /help output
- [ ] Description is clear and concise
- [ ] Follows existing format pattern

---

### Task 3.5: Add command unit tests

**File**: `tests/test_repl/test_commands.py` (extend) or new `tests/test_repl/test_commands_notify.py`
**Research Reference**: Lines 629-685 of research.md

**Test Cases**:

```python
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

    def test_notify_with_no_channels_shows_error(self):
        """Test /notify with no channels shows error."""
        commands = SystemCommands(config={"notifications": {"enabled": True, "channels": []}})
        result = commands.notify(["test"])

        assert result.success is False
        assert "No notification channels" in result.output

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

    def test_help_includes_notify(self):
        """Test /help output includes /notify command."""
        commands = SystemCommands()
        result = commands.help([])

        assert result.success is True
        assert "/notify" in result.output
```

**Success Criteria**:
- [ ] All test cases pass
- [ ] Tests cover happy path and error paths
- [ ] Tests follow existing patterns
- [ ] 100% coverage on notify() method

---

## Phase 4: Validation

### Task 4.1: Run full test suite

**Command**:
```bash
uv run pytest --cov=src/teambot --cov-report=term-missing
```

**Verification**:
- [ ] All tests pass
- [ ] No regressions in existing tests
- [ ] Coverage >= 80% overall
- [ ] Coverage = 100% on new code

---

### Task 4.2: Lint and format code

**Commands**:
```bash
uv run ruff format .
uv run ruff check . --fix
```

**Verification**:
- [ ] No formatting changes needed
- [ ] No linting errors
- [ ] All files pass ruff check

---

### Task 4.3: Manual verification

**Steps**:

1. **Start REPL**:
```bash
uv run teambot
```

2. **Test /help**:
```
> /help
```
Verify: `/notify` is listed

3. **Test /notify without args**:
```
> /notify
```
Verify: Usage help shown

4. **Test /notify with message** (if Telegram configured):
```
> /notify Test notification from TeamBot!
```
Verify: "✅ Notification sent" shown, message received on Telegram

5. **Test orchestration run** (if time permits):
```bash
uv run teambot run objectives/test.md
```
Verify: Header "🚀 Starting: ..." and footer "✅ Completed: ..." shown

**Success Criteria**:
- [ ] All manual tests pass
- [ ] No errors or unexpected behavior
- [ ] Terminal output matches specification

---

## References

| Ref ID | Type | File | Lines |
|--------|------|------|-------|
| REF-001 | Code | `src/teambot/notifications/templates.py` | 24-89 |
| REF-002 | Code | `src/teambot/notifications/event_bus.py` | 127-161 |
| REF-003 | Code | `src/teambot/repl/commands.py` | 609-696 |
| REF-004 | Code | `src/teambot/orchestration/execution_loop.py` | 135-225 |
| REF-005 | Code | `src/teambot/cli.py` | 330-380 |
| REF-006 | Test | `tests/test_notifications/test_templates.py` | All |
| REF-007 | Test | `tests/test_repl/test_commands.py` | All |
