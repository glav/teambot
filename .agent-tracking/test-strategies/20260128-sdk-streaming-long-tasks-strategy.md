# Test Strategy: SDK Streaming for Long-Running Tasks

**Date**: 2026-01-28
**Feature Spec**: docs/feature-specs/sdk-streaming-long-tasks.md
**Research**: .agent-tracking/research/20260128-sdk-streaming-long-tasks-research.md

---

## Executive Summary

**Recommendation: TDD (Test-Driven Development)**

This feature is ideal for TDD because:
1. **Clear Contracts**: The SDK event API has well-defined event types and data structures
2. **Mockable Dependencies**: SDK can be fully mocked with AsyncMock patterns already established
3. **Isolated Units**: New methods (`execute_streaming`, `cancel_current_request`) have clear inputs/outputs
4. **Existing Patterns**: The codebase already has comprehensive mock fixtures for SDK testing
5. **Critical Feature**: Streaming reliability is essential - tests ensure correctness before implementation

---

## Test Categories

### 1. Unit Tests - CopilotSDKClient (TDD - Write First)

| Test | Description | Priority |
|------|-------------|----------|
| `test_execute_streaming_receives_delta_events` | Verify callback receives each delta chunk | P0 |
| `test_execute_streaming_completes_on_session_idle` | Verify SESSION_IDLE ends the stream | P0 |
| `test_execute_streaming_handles_session_error` | Verify SESSION_ERROR raises SDKClientError | P0 |
| `test_execute_streaming_accumulates_content` | Verify chunks accumulated into final result | P0 |
| `test_execute_streaming_unsubscribes_on_complete` | Verify event listener cleaned up | P0 |
| `test_execute_streaming_unsubscribes_on_error` | Verify cleanup even on error | P0 |
| `test_execute_streaming_handles_abort_event` | Verify ABORT event handled after cancel | P1 |
| `test_execute_streaming_filters_empty_deltas` | Verify None/empty delta_content skipped | P1 |
| `test_backward_compatible_execute_uses_streaming` | Verify `execute()` works unchanged | P0 |
| `test_cancel_current_request_calls_abort` | Verify `cancel_current_request()` calls `session.abort()` | P1 |
| `test_cancel_returns_false_if_no_session` | Verify cancel returns False for unknown agent | P1 |

### 2. Unit Tests - TaskExecutor Integration (TDD - Write First)

| Test | Description | Priority |
|------|-------------|----------|
| `test_executor_with_streaming_callback` | Verify executor passes on_chunk to SDK | P0 |
| `test_executor_streaming_result_matches_sync` | Verify streaming and sync return same content | P0 |

### 3. Unit Tests - OutputPane Streaming (Code-First)

| Test | Description | Priority |
|------|-------------|----------|
| `test_write_streaming_chunk_appends_content` | Verify chunks displayed incrementally | P1 |
| `test_finish_streaming_clears_state` | Verify streaming state cleaned up | P1 |
| `test_multiple_agents_stream_independently` | Verify concurrent streams don't interfere | P2 |

### 4. Integration Tests (Code-First)

| Test | Description | Priority |
|------|-------------|----------|
| `test_end_to_end_streaming_display` | User command → streaming chunks → completion | P1 |
| `test_cancel_command_stops_streaming` | /cancel stops active stream | P2 |

---

## TDD Test Specifications

### Test File: `tests/test_copilot/test_sdk_streaming.py`

```python
"""TDD tests for SDK streaming execution - WRITE THESE FIRST."""

import pytest
from unittest.mock import AsyncMock, MagicMock, call
import asyncio


class TestExecuteStreaming:
    """Tests for execute_streaming method."""

    @pytest.mark.asyncio
    async def test_receives_delta_events(self):
        """Verify on_chunk callback receives each delta."""
        # Setup: Mock session that fires delta events
        # Action: Call execute_streaming with on_chunk callback
        # Assert: Callback called for each delta with correct content
        pass

    @pytest.mark.asyncio
    async def test_completes_on_session_idle(self):
        """Verify streaming completes when SESSION_IDLE received."""
        # Setup: Mock session that fires deltas then IDLE
        # Action: Call execute_streaming
        # Assert: Method returns, accumulated content correct
        pass

    @pytest.mark.asyncio
    async def test_handles_session_error(self):
        """Verify SESSION_ERROR raises SDKClientError."""
        # Setup: Mock session that fires SESSION_ERROR
        # Action: Call execute_streaming
        # Assert: SDKClientError raised with error message
        pass

    @pytest.mark.asyncio
    async def test_accumulates_content(self):
        """Verify all chunks accumulated into return value."""
        # Setup: Mock session with multiple deltas
        # Action: Call execute_streaming
        # Assert: Return value = all chunks joined
        pass

    @pytest.mark.asyncio
    async def test_unsubscribes_on_complete(self):
        """Verify event listener unsubscribed after completion."""
        # Setup: Mock session with unsubscribe function
        # Action: Call execute_streaming to completion
        # Assert: Unsubscribe called
        pass

    @pytest.mark.asyncio
    async def test_unsubscribes_on_error(self):
        """Verify event listener unsubscribed even on error."""
        # Setup: Mock session that errors
        # Action: Call execute_streaming (expect error)
        # Assert: Unsubscribe still called
        pass

    @pytest.mark.asyncio
    async def test_filters_empty_deltas(self):
        """Verify None or empty delta_content is skipped."""
        # Setup: Mock with some empty deltas
        # Action: Call execute_streaming
        # Assert: Empty deltas not in result, callback not called for them
        pass


class TestBackwardCompatibility:
    """Tests for backward compatible execute()."""

    @pytest.mark.asyncio
    async def test_execute_uses_streaming_internally(self):
        """Verify execute() uses execute_streaming under the hood."""
        # Setup: Mock execute_streaming
        # Action: Call execute()
        # Assert: execute_streaming called, same result returned
        pass

    @pytest.mark.asyncio
    async def test_execute_api_unchanged(self):
        """Verify execute() signature and behavior unchanged."""
        # Setup: Same as existing tests
        # Action: Call execute(agent_id, prompt)
        # Assert: Returns string, works as before
        pass


class TestCancelRequest:
    """Tests for cancel_current_request."""

    @pytest.mark.asyncio
    async def test_cancel_calls_abort(self):
        """Verify cancel calls session.abort()."""
        # Setup: Client with active session
        # Action: Call cancel_current_request
        # Assert: session.abort() called
        pass

    @pytest.mark.asyncio
    async def test_cancel_returns_true_on_success(self):
        """Verify cancel returns True when aborted."""
        # Setup: Client with active session
        # Action: Call cancel_current_request
        # Assert: Returns True
        pass

    @pytest.mark.asyncio
    async def test_cancel_returns_false_no_session(self):
        """Verify cancel returns False if no session exists."""
        # Setup: Client without session for agent
        # Action: Call cancel_current_request("unknown")
        # Assert: Returns False
        pass

    @pytest.mark.asyncio
    async def test_handles_abort_event(self):
        """Verify ABORT event is handled gracefully."""
        # Setup: Mock that fires ABORT after cancel
        # Action: Start streaming, cancel, observe
        # Assert: Stream ends, error indicates cancelled
        pass
```

---

## Mock Fixtures Required

### New Fixture: `mock_streaming_session`

```python
@pytest.fixture
def mock_streaming_session():
    """Mock session that supports streaming events."""
    session = MagicMock()
    
    # Track registered handlers
    handlers = []
    
    def on(handler):
        handlers.append(handler)
        def unsubscribe():
            handlers.remove(handler)
        return unsubscribe
    
    session.on = on
    session.send = AsyncMock(return_value="msg-123")
    session.abort = AsyncMock()
    session.destroy = AsyncMock()
    session._handlers = handlers  # Expose for test manipulation
    
    return session


def fire_event(session, event_type, data=None):
    """Helper to fire events to registered handlers."""
    from types import SimpleNamespace
    event = SimpleNamespace(type=event_type, data=data)
    for handler in session._handlers:
        handler(event)
```

### New Fixture: `mock_event_types`

```python
@pytest.fixture
def mock_event_types():
    """Mock SessionEventType enum."""
    from types import SimpleNamespace
    return SimpleNamespace(
        ASSISTANT_MESSAGE_DELTA="ASSISTANT_MESSAGE_DELTA",
        SESSION_IDLE="SESSION_IDLE",
        SESSION_ERROR="SESSION_ERROR",
        ABORT="ABORT",
    )
```

---

## Test Execution Order

### Phase 1: Write TDD Tests (Before Implementation)
1. Create `tests/test_copilot/test_sdk_streaming.py`
2. Write test stubs with clear docstrings
3. Run tests - all should fail (no implementation)

### Phase 2: Implement to Pass Tests
1. Add `execute_streaming()` to `sdk_client.py`
2. Add `cancel_current_request()` to `sdk_client.py`
3. Update `execute()` to use streaming internally
4. Run tests - all should pass

### Phase 3: Code-First Tests (After Implementation)
1. Add OutputPane streaming tests
2. Add integration tests for UI flow
3. Manual testing for UX validation

---

## Coverage Targets

| Component | Target | Notes |
|-----------|--------|-------|
| `sdk_client.py` streaming methods | 95%+ | All branches covered |
| `executor.py` streaming integration | 90%+ | Main paths covered |
| `output_pane.py` streaming display | 80%+ | UI display is less critical |

---

## Risk Mitigation

| Risk | Test Coverage |
|------|---------------|
| Events arrive out of order | Test with various event sequences |
| Empty deltas cause issues | Test with None and "" deltas |
| Error during cleanup | Test error + unsubscribe |
| Cancel doesn't stop SDK | Test abort() called, handle ABORT event |
| Memory leak from handlers | Verify unsubscribe always called |

---

## Approval

**TDD Approach Selected**: Yes

**Rationale**:
- SDK streaming is a critical reliability feature
- Contracts are well-defined from research
- Existing mock patterns support this approach
- Tests will drive correct implementation

**Next Step**: `/sdd.5-task-planner-for-feature` to create implementation plan

---

Generated 2026-01-28T03:53:00Z by sdd.4-determine-test-strategy
