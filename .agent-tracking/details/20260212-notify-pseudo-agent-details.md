<!-- markdownlint-disable-file -->
# Implementation Details: @notify Pseudo-Agent

## Research Reference

- **Primary Research**: `.teambot/simple-notification-end/artifacts/research.md`
- **Test Strategy**: `.teambot/simple-notification-end/artifacts/test_strategy.md`
- **Feature Spec**: `.teambot/simple-notification-end/artifacts/feature_spec.md`

---

## Phase 1: Foundation - Tests First

### Task 1.1: Write Router Recognition Tests (Lines 35-55)

**File**: `tests/test_repl/test_router.py`
**Research Reference**: research.md Lines 107-119

**Test Cases to Add**:

```python
class TestNotifyAgentRecognition:
    """Tests for @notify pseudo-agent recognition."""

    def test_notify_is_valid_agent(self):
        """Test that 'notify' is recognized as valid agent ID."""
        from teambot.repl.router import VALID_AGENTS
        
        assert "notify" in VALID_AGENTS

    def test_existing_agents_still_valid(self):
        """Regression: existing agents remain valid."""
        from teambot.repl.router import VALID_AGENTS
        
        expected = {"pm", "ba", "writer", "builder-1", "builder-2", "reviewer", "notify"}
        assert VALID_AGENTS == expected

    def test_invalid_agents_rejected(self):
        """Test that invalid agent IDs are still rejected."""
        from teambot.repl.router import VALID_AGENTS
        
        for invalid in ["unknown", "admin", "builder-3", "Notify", "NOTIFY"]:
            assert invalid not in VALID_AGENTS
```

**Success Criteria**:
- Tests initially fail (notify not in VALID_AGENTS)
- Tests pass after Task 1.2

---

### Task 1.2: Add "notify" to VALID_AGENTS (Lines 57-70)

**File**: `src/teambot/repl/router.py`
**Line**: 20
**Research Reference**: research.md Lines 107-110

**Current Code**:
```python
VALID_AGENTS = {"pm", "ba", "writer", "builder-1", "builder-2", "reviewer"}
```

**Updated Code**:
```python
VALID_AGENTS = {"pm", "ba", "writer", "builder-1", "builder-2", "reviewer", "notify"}
```

**Success Criteria**:
- `@notify` commands no longer raise "unknown agent" error
- Task 1.1 tests pass

---

### Task 1.3: Write Pseudo-Agent Detection Tests (Lines 72-85)

**File**: `tests/test_tasks/test_executor.py`
**Research Reference**: research.md Lines 112-119

**Test Cases to Add**:

```python
class TestPseudoAgentDetection:
    """Tests for pseudo-agent detection."""

    def test_notify_is_pseudo_agent(self):
        """Test that 'notify' is identified as pseudo-agent."""
        from teambot.tasks.executor import is_pseudo_agent
        
        assert is_pseudo_agent("notify") is True

    def test_regular_agents_not_pseudo(self):
        """Test that regular agents are not pseudo-agents."""
        from teambot.tasks.executor import is_pseudo_agent
        
        for agent in ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]:
            assert is_pseudo_agent(agent) is False
```

---

### Task 1.4: Add PSEUDO_AGENTS Constant and Helper (Lines 87-95)

**File**: `src/teambot/tasks/executor.py`
**Insert After**: Line 19 (after logger definition)
**Research Reference**: research.md Lines 112-119

**Code to Add**:

```python
# Pseudo-agents that bypass Copilot SDK execution
PSEUDO_AGENTS = {"notify"}


def is_pseudo_agent(agent_id: str) -> bool:
    """Check if agent is a pseudo-agent (not using SDK).
    
    Args:
        agent_id: The agent identifier to check.
        
    Returns:
        True if agent is a pseudo-agent, False otherwise.
    """
    return agent_id in PSEUDO_AGENTS
```

---

## Phase 2: Core Execution - TDD

### Task 2.1: Write Notify Handler Tests (Lines 97-125)

**File**: `tests/test_tasks/test_executor.py`
**Research Reference**: research.md Lines 293-352

**Test Cases to Add**:

```python
class TestNotifyHandler:
    """Tests for @notify pseudo-agent handler."""

    @pytest.fixture
    def mock_config(self):
        return {
            "notifications": {
                "enabled": True,
                "channels": [{"type": "telegram", "token": "test", "chat_id": "123"}]
            }
        }

    @pytest.mark.asyncio
    async def test_handle_notify_returns_confirmation(self, mock_config):
        """Test that _handle_notify returns confirmation message."""
        executor = TaskExecutor(sdk_client=AsyncMock(), config=mock_config)
        
        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus
            
            result = await executor._handle_notify("Test message", background=False)
            
            assert result.success
            assert "Notification sent" in result.output
            assert "✅" in result.output

    @pytest.mark.asyncio
    async def test_handle_notify_calls_event_bus(self, mock_config):
        """Test that EventBus.emit_sync is called."""
        executor = TaskExecutor(sdk_client=AsyncMock(), config=mock_config)
        
        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus
            
            await executor._handle_notify("Test message", background=False)
            
            mock_bus.emit_sync.assert_called_once_with(
                "custom_message", {"message": "Test message"}
            )

    @pytest.mark.asyncio
    async def test_handle_notify_no_sdk_call(self, mock_config):
        """Test that SDK is not called for @notify."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk, config=mock_config)
        
        with patch("teambot.tasks.executor.create_event_bus_from_config"):
            await executor._handle_notify("Test", background=False)
            
            mock_sdk.execute.assert_not_called()
```

---

### Task 2.2: Implement `_handle_notify()` Method (Lines 127-155)

**File**: `src/teambot/tasks/executor.py`
**Add To**: `TaskExecutor` class
**Research Reference**: research.md Lines 293-352

**Constructor Update** - add `config` parameter:

```python
def __init__(
    self,
    sdk_client,
    max_concurrent: int = 3,
    default_timeout: float = 120.0,
    on_task_complete: Callable | None = None,
    on_task_started: Callable | None = None,
    on_streaming_chunk: Callable | None = None,
    on_stage_change: Callable | None = None,
    on_stage_output: Callable | None = None,
    on_pipeline_complete: Callable | None = None,
    agent_status_manager: AgentStatusManager | None = None,
    config: dict | None = None,  # ADD THIS
):
    # ... existing code ...
    self._config = config  # ADD THIS
```

**Method to Add**:

```python
async def _handle_notify(self, message: str, background: bool) -> ExecutionResult:
    """Handle @notify pseudo-agent.
    
    Sends notification to all configured channels without invoking Copilot SDK.
    
    Args:
        message: Notification message (may include interpolated $ref content).
        background: Whether running in background mode.
        
    Returns:
        ExecutionResult with confirmation output.
    """
    from teambot.notifications.config import create_event_bus_from_config
    from teambot.tasks.models import TaskResult
    
    # Truncate if message too long
    message = truncate_for_notification(message)
    
    try:
        if self._config:
            event_bus = create_event_bus_from_config(self._config)
            if event_bus and event_bus._channels:
                event_bus.emit_sync("custom_message", {"message": message})
                output = "Notification sent ✅"
            else:
                output = "⚠️ No notification channels configured"
                logger.warning("@notify: No notification channels configured")
        else:
            output = "⚠️ No notification configuration available"
            logger.warning("@notify: No config available")
    except Exception as e:
        output = f"⚠️ Notification failed: {e}"
        logger.warning(f"@notify failed: {e}")
    
    # Store result for potential $notify references
    synthetic_result = TaskResult(success=True, output=output)
    self._manager._agent_results["notify"] = synthetic_result
    
    return ExecutionResult(
        success=True,  # Always succeed to not break pipeline
        output=output,
        task_id=None,
        task_ids=[],
        background=background,
    )
```

---

### Task 2.3: Write Truncation Tests (Lines 157-167)

**File**: `tests/test_tasks/test_executor.py`
**Research Reference**: research.md Lines 206-218

**Test Cases to Add**:

```python
class TestTruncationForNotification:
    """Tests for output truncation helper."""

    def test_short_text_unchanged(self):
        """Text under limit is unchanged."""
        from teambot.tasks.executor import truncate_for_notification
        
        text = "a" * 400
        assert truncate_for_notification(text) == text

    def test_long_text_truncated(self):
        """Text over limit is truncated with suffix."""
        from teambot.tasks.executor import truncate_for_notification
        
        text = "a" * 600
        result = truncate_for_notification(text)
        assert len(result) == 500 + len("...")
        assert result.endswith("...")

    def test_exactly_at_limit_unchanged(self):
        """Text exactly at limit is unchanged."""
        from teambot.tasks.executor import truncate_for_notification
        
        text = "a" * 500
        assert truncate_for_notification(text) == text

    def test_one_over_limit_truncated(self):
        """Text one char over limit is truncated."""
        from teambot.tasks.executor import truncate_for_notification
        
        text = "a" * 501
        result = truncate_for_notification(text)
        assert len(result) == 500 + len("...")
```

---

### Task 2.4: Implement Truncation Helper (Lines 169-175)

**File**: `src/teambot/tasks/executor.py`
**Insert After**: `is_pseudo_agent()` function
**Research Reference**: research.md Lines 206-218

**Code to Add**:

```python
MAX_NOTIFICATION_LENGTH = 500
TRUNCATION_SUFFIX = "..."


def truncate_for_notification(text: str, max_length: int = MAX_NOTIFICATION_LENGTH) -> str:
    """Truncate text for notification readability.
    
    Args:
        text: Text to potentially truncate.
        max_length: Maximum length before truncation.
        
    Returns:
        Original text if under limit, otherwise truncated with suffix.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + TRUNCATION_SUFFIX
```

---

### Task 2.5: Write Result Storage Tests (Lines 177-187)

**File**: `tests/test_tasks/test_executor.py`

**Test Cases to Add**:

```python
class TestNotifyResultStorage:
    """Tests for @notify result storage."""

    @pytest.mark.asyncio
    async def test_result_stored_after_notify(self):
        """Test that result is stored in _agent_results."""
        executor = TaskExecutor(sdk_client=AsyncMock(), config={"notifications": {"enabled": True}})
        
        with patch("teambot.tasks.executor.create_event_bus_from_config"):
            await executor._handle_notify("Test", background=False)
            
            result = executor._manager.get_agent_result("notify")
            assert result is not None
            assert result.success is True

    @pytest.mark.asyncio
    async def test_result_output_matches(self):
        """Test that stored result contains confirmation."""
        executor = TaskExecutor(sdk_client=AsyncMock(), config={"notifications": {"enabled": True}})
        
        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock.return_value = mock_bus
            
            await executor._handle_notify("Test", background=False)
            
            result = executor._manager.get_agent_result("notify")
            assert "Notification sent" in result.output
```

---

### Task 2.6: Implement Result Storage (Lines 189-195)

**Implementation**: Already included in Task 2.2 `_handle_notify()` method.

The key lines are:
```python
synthetic_result = TaskResult(success=True, output=output)
self._manager._agent_results["notify"] = synthetic_result
```

---

## Phase 3: Pipeline Integration - TDD

### Task 3.1: Write Simple Execution Intercept Tests (Lines 197-220)

**File**: `tests/test_tasks/test_executor.py`

**Test Cases to Add**:

```python
class TestNotifySimpleExecution:
    """Tests for @notify in simple execution."""

    @pytest.mark.asyncio
    async def test_notify_command_no_sdk(self):
        """@notify command does not call SDK."""
        from teambot.repl.parser import parse_command
        
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk, config={"notifications": {"enabled": True}})
        
        with patch("teambot.tasks.executor.create_event_bus_from_config"):
            cmd = parse_command('@notify "Test message"')
            result = await executor.execute(cmd)
            
            mock_sdk.execute.assert_not_called()
            assert result.success

    @pytest.mark.asyncio
    async def test_notify_with_ref_interpolation(self):
        """@notify interpolates $ref tokens."""
        from teambot.repl.parser import parse_command
        from teambot.tasks.models import TaskResult
        
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk, config={"notifications": {"enabled": True}})
        
        # Pre-populate pm result
        executor._manager._agent_results["pm"] = TaskResult(success=True, output="PM output here")
        
        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock.return_value = mock_bus
            
            cmd = parse_command('@notify "Result: $pm"')
            await executor.execute(cmd)
            
            # Verify interpolated message was sent
            call_args = mock_bus.emit_sync.call_args
            assert "PM output here" in call_args[0][1]["message"]
```

---

### Task 3.2: Add Intercept to `_execute_simple()` (Lines 222-245)

**File**: `src/teambot/tasks/executor.py`
**Location**: Inside `_execute_simple()` method, after line 238 (after prompt is set)
**Research Reference**: research.md Lines 293-311

**Code to Insert** (after `prompt = command.content` or `prompt = self._inject_references(...)`):

```python
        # Handle @notify pseudo-agent
        if is_pseudo_agent(agent_id):
            return await self._handle_notify(prompt, command.background)
```

**Full Context** - the section should look like:

```python
        if command.references:
            # ... existing reference validation and injection ...
            prompt = self._inject_references(command.content, command.references)
        else:
            prompt = command.content

        # Handle @notify pseudo-agent (ADD THIS BLOCK)
        if is_pseudo_agent(agent_id):
            return await self._handle_notify(prompt, command.background)

        # Custom agents in .github/agents/ handle persona context
        task = self._manager.create_task(
            # ... existing code ...
        )
```

---

### Task 3.3: Write Pipeline Intercept Tests (Lines 247-265)

**File**: `tests/test_tasks/test_executor.py`

**Test Cases to Add**:

```python
class TestNotifyInPipeline:
    """Tests for @notify in pipeline execution."""

    @pytest.mark.asyncio
    async def test_notify_at_pipeline_end(self):
        """@notify executes at end of pipeline."""
        from teambot.repl.parser import parse_command
        
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="SDK output")
        executor = TaskExecutor(sdk_client=mock_sdk, config={"notifications": {"enabled": True}})
        
        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock.return_value = mock_bus
            
            cmd = parse_command('@pm plan, @notify "Plan done: $pm"')
            result = await executor.execute(cmd)
            
            assert result.success
            mock_bus.emit_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_at_pipeline_start(self):
        """@notify executes at start of pipeline."""
        from teambot.repl.parser import parse_command
        
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk, config={"notifications": {"enabled": True}})
        
        with patch("teambot.tasks.executor.create_event_bus_from_config"):
            cmd = parse_command('@notify "Starting", @pm plan')
            result = await executor.execute(cmd)
            
            assert result.success

    @pytest.mark.asyncio
    async def test_notify_in_pipeline_middle(self):
        """@notify executes in middle of pipeline."""
        from teambot.repl.parser import parse_command
        
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk, config={"notifications": {"enabled": True}})
        
        with patch("teambot.tasks.executor.create_event_bus_from_config"):
            cmd = parse_command('@pm plan, @notify "Middle", @reviewer review $pm')
            result = await executor.execute(cmd)
            
            assert result.success
```

---

### Task 3.4: Add Intercept to `_execute_pipeline()` (Lines 267-280)

**File**: `src/teambot/tasks/executor.py`
**Location**: Inside `_execute_pipeline()` method, in the stage execution loop
**Research Reference**: research.md Lines 354-376

The pipeline executor needs to detect @notify stages and handle them specially without creating SDK tasks.

**Implementation Note**: The exact location depends on pipeline structure. Add check before task creation in the stage loop.

---

### Task 3.5: Write Multi-Agent Intercept Tests (Lines 282-290)

**File**: `tests/test_tasks/test_executor.py`

**Test Cases**:

```python
class TestNotifyMultiAgent:
    """Tests for @notify with multi-agent syntax."""

    @pytest.mark.asyncio
    async def test_notify_with_comma_syntax(self):
        """@notify works with multi-agent comma syntax."""
        from teambot.repl.parser import parse_command
        
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk, config={"notifications": {"enabled": True}})
        
        with patch("teambot.tasks.executor.create_event_bus_from_config"):
            # Note: This may parse differently - verify parser behavior
            cmd = parse_command('@pm,notify do task')
            # Test execution based on actual parser output
```

---

### Task 3.6: Add Intercept to `_execute_multiagent()` (Lines 292-300)

**File**: `src/teambot/tasks/executor.py`
**Location**: Inside `_execute_multiagent()` method

Filter out pseudo-agents before parallel SDK execution and handle separately.

---

## Phase 4: Failure Handling - TDD

### Task 4.1: Write Failure Non-Blocking Tests (Lines 302-325)

**File**: `tests/test_tasks/test_executor.py`

**Test Cases to Add**:

```python
class TestNotifyFailureHandling:
    """Tests for @notify failure scenarios."""

    @pytest.mark.asyncio
    async def test_channel_failure_pipeline_continues(self):
        """Notification failure doesn't break pipeline."""
        from teambot.repl.parser import parse_command
        
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="SDK output")
        executor = TaskExecutor(sdk_client=mock_sdk, config={"notifications": {"enabled": True}})
        
        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_bus.emit_sync.side_effect = Exception("Network error")
            mock.return_value = mock_bus
            
            cmd = parse_command('@pm plan, @notify "Test", @reviewer review')
            result = await executor.execute(cmd)
            
            # Pipeline should still succeed
            assert result.success

    @pytest.mark.asyncio
    async def test_failure_logged_as_warning(self, caplog):
        """Notification failure is logged as warning."""
        import logging
        
        executor = TaskExecutor(sdk_client=AsyncMock(), config={"notifications": {"enabled": True}})
        
        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_bus.emit_sync.side_effect = Exception("Test error")
            mock.return_value = mock_bus
            
            with caplog.at_level(logging.WARNING):
                await executor._handle_notify("Test", background=False)
            
            assert "notify" in caplog.text.lower() or "failed" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_failure_output_contains_warning(self):
        """Failure output indicates warning."""
        executor = TaskExecutor(sdk_client=AsyncMock(), config={"notifications": {"enabled": True}})
        
        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_bus.emit_sync.side_effect = Exception("Test error")
            mock.return_value = mock_bus
            
            result = await executor._handle_notify("Test", background=False)
            
            assert "⚠️" in result.output or "failed" in result.output.lower()
```

---

### Task 4.2: Implement Failure Handling (Lines 327-345)

**Implementation**: Already included in Task 2.2 `_handle_notify()` method.

Key aspects:
- Try/except wrapping EventBus operations
- `logger.warning()` on failure
- Return warning output instead of raising
- Always return `success=True` to not break pipeline

---

## Phase 5: Legacy Removal

### Task 5.1: Write Legacy Removal Tests (Lines 347-365)

**File**: `tests/test_repl/test_commands.py`

**Test Cases to Add**:

```python
class TestLegacyNotifyRemoved:
    """Tests for legacy /notify removal."""

    def test_notify_command_unknown(self):
        """Test /notify returns unknown command error."""
        commands = SystemCommands()
        result = commands.dispatch("notify", ["test", "message"])
        
        assert result.success is False
        assert "Unknown command" in result.output or "unknown" in result.output.lower()

    def test_error_suggests_at_notify(self):
        """Test error message suggests using @notify."""
        # This may require updating the unknown command message
        commands = SystemCommands()
        result = commands.dispatch("notify", ["test"])
        
        # Verify appropriate guidance is given
        assert result.success is False
```

---

### Task 5.2: Remove `/notify` Command (Lines 367-385)

**File**: `src/teambot/repl/commands.py`

**Changes**:

1. Remove from handlers dict (Line 691):
```python
# REMOVE THIS LINE:
"notify": self.notify,
```

2. Delete the `notify()` method (Lines 762-828):
```python
# DELETE THIS ENTIRE METHOD:
def notify(self, args: list[str]) -> CommandResult:
    """Handle /notify command - send test notification.
    ...
    """
```

---

### Task 5.3: Update Help Text (Lines 387-395)

**File**: `src/teambot/repl/commands.py`

In the `handle_help()` function, ensure `/notify` is not listed. If it's in the help output, remove it.

Also update `/help` to mention `@notify`:
```
Use @notify "message" to send notifications in pipelines.
```

---

## Phase 6: UI Integration

### Task 6.1: Write Status Display Tests (Lines 397-420)

**File**: `tests/test_ui/test_agent_state.py`

**Test Cases to Add**:

```python
class TestNotifyStatusDisplay:
    """Tests for @notify in status display."""

    def test_notify_in_default_agents(self):
        """Test 'notify' is in DEFAULT_AGENTS list."""
        from teambot.ui.agent_state import DEFAULT_AGENTS
        
        assert "notify" in DEFAULT_AGENTS

    def test_notify_status_initialized(self):
        """Test notify agent status is initialized."""
        from teambot.ui.agent_state import AgentStatusManager
        
        manager = AgentStatusManager()
        status = manager.get("notify")
        
        assert status is not None
        assert status.agent_id == "notify"

    def test_notify_model_is_na(self):
        """Test notify model displays as (n/a)."""
        from teambot.ui.agent_state import AgentStatusManager
        
        manager = AgentStatusManager()
        status = manager.get("notify")
        
        # Model should be None or special marker for (n/a) display
        assert status.model is None or status.model == "(n/a)"
```

---

### Task 6.2: Add "notify" to DEFAULT_AGENTS (Lines 422-435)

**File**: `src/teambot/ui/agent_state.py`
**Line**: 73

**Current Code**:
```python
DEFAULT_AGENTS = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]
```

**Updated Code**:
```python
DEFAULT_AGENTS = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer", "notify"]
```

---

### Task 6.3: Update StatusPanel for "(n/a)" Model (Lines 437-450)

**File**: `src/teambot/ui/widgets/status_panel.py`

In the status formatting logic, add special handling:

```python
# When displaying model for an agent:
if agent_id == "notify":
    model_display = "(n/a)"
else:
    model_display = status.model or "default"
```

Or set the model to "(n/a)" during initialization in `AgentStatusManager.__post_init__()`:

```python
for agent_id in DEFAULT_AGENTS:
    model = "(n/a)" if agent_id == "notify" else None
    self._statuses[agent_id] = AgentStatus(agent_id=agent_id, model=model)
```

---

## Phase 7: Validation

### Task 7.1: Write End-to-End Integration Tests (Lines 452-475)

**File**: `tests/test_tasks/test_executor.py` or new `tests/test_integration/test_notify_e2e.py`

Implement tests for AT-001 through AT-010 from feature spec.

Key scenarios:
- AT-001: Simple notification
- AT-002: Notification with $ref
- AT-003: Large output truncation
- AT-004: Pipeline middle
- AT-005: Pipeline end
- AT-006: Failure non-blocking
- AT-007: Status display
- AT-008: Background execution
- AT-009: $notify reference
- AT-010: Legacy /notify removed

---

### Task 7.2: Run Full Test Suite (Lines 477-485)

**Command**:
```bash
uv run pytest --cov=src/teambot --cov-report=term-missing
```

**Targets**:
- All tests pass
- Coverage ≥ 80%
- No regressions in existing tests

---

### Task 7.3: Lint and Format (Lines 487-490)

**Commands**:
```bash
uv run ruff format -- .
uv run ruff check . --fix
```

**Targets**:
- No lint errors
- Consistent formatting

---

## File Summary

| File | Changes |
|------|---------|
| `src/teambot/repl/router.py` | Add "notify" to VALID_AGENTS |
| `src/teambot/tasks/executor.py` | Add PSEUDO_AGENTS, is_pseudo_agent(), truncate_for_notification(), _handle_notify(), intercepts |
| `src/teambot/repl/commands.py` | Remove /notify handler and method |
| `src/teambot/ui/agent_state.py` | Add "notify" to DEFAULT_AGENTS |
| `src/teambot/ui/widgets/status_panel.py` | Handle "(n/a)" model display |
| `tests/test_repl/test_router.py` | Add notify recognition tests |
| `tests/test_tasks/test_executor.py` | Add pseudo-agent and notify tests |
| `tests/test_repl/test_commands.py` | Add legacy removal tests |
| `tests/test_ui/test_agent_state.py` | Add status display tests |
