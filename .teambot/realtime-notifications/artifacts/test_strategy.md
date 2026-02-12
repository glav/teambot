<!-- markdownlint-disable-file -->
# Test Strategy: Real-Time Notification System

**Strategy Date**: 2026-02-11
**Feature Specification**: docs/objectives/realtime-notifications.md
**Research Reference**: .agent-tracking/research/20260211-realtime-notifications-research.md
**Strategist**: Test Strategy Agent

---

## Testing Approach Decision Matrix

### Factor Scoring

| Factor | Question | Answer | TDD Points | Code-First Points |
|--------|----------|--------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES - 18 success criteria defined | **3** | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM - EventBus routing, retry logic, async sends | **2** | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | MEDIUM - Failures must be graceful, not block workflow | **2** | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO - Well-defined protocol and implementation | 0 | **0** |
| **Simplicity** | Is this straightforward CRUD or simple logic? | NO - Async event routing, HTTP integration | 0 | **0** |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO - Quality is priority | 0 | **0** |
| **Requirements Stability** | Are requirements likely to change during development? | NO - Protocol designed for extensibility | 0 | **0** |

### Score Calculation

```
TDD Score: 3 + 2 + 2 = 7
Code-First Score: 0

Decision: TDD (score 7 ≥ threshold 6)
```

### Decision: **HYBRID** (TDD Primary with Code-First for External Integration)

**Rationale**: While the TDD score is high (7), the Telegram HTTP integration benefits from a Code-First approach due to external API dependency. Core protocol and EventBus use TDD; TelegramChannel uses Code-First with mocked HTTP.

---

## Recommended Testing Approach

**Primary Approach**: **HYBRID** (TDD for core, Code-First for HTTP integration)

### Rationale

The real-time notification system has well-defined requirements with 18 explicit success criteria, making it an excellent candidate for TDD. The `NotificationChannel` protocol and `EventBus` are pure logic with clear behavioral contracts that benefit from test-first development.

However, the `TelegramChannel` HTTP integration is better suited to Code-First because:
1. External API behavior needs to be understood during implementation
2. Mocking httpx responses is more natural after understanding the implementation
3. HTTP edge cases (rate limits, timeouts) are discovered during coding

The configuration validation and CLI init flow follow existing patterns and can use either approach effectively, but TDD provides better regression safety.

**Key Factors:**
* Complexity: **MEDIUM** - Multiple components with async coordination
* Risk: **MEDIUM** - Must not block workflows, graceful degradation required
* Requirements Clarity: **HIGH** - 18 success criteria explicitly defined
* Time Pressure: **LOW** - Quality over speed

---

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Medium - EventBus routing, exponential backoff retry, template rendering
* **Integration Depth**: Medium - Wraps existing `on_progress` callback, adds HTTP layer
* **State Management**: Low - Stateless channels, fire-and-forget semantics
* **Error Scenarios**: High - Network failures, rate limits, missing credentials, malformed responses

### Risk Profile
* **Business Criticality**: MEDIUM - User experience feature, not core workflow
* **User Impact**: LOW-MEDIUM - Failure means no notifications, not broken builds
* **Data Sensitivity**: MEDIUM - Tokens stored in env vars, never logged
* **Failure Cost**: LOW - Graceful degradation by design

### Requirements Clarity
* **Specification Completeness**: COMPLETE - 18 success criteria
* **Acceptance Criteria Quality**: PRECISE - Each criterion is testable
* **Edge Cases Identified**: 12+ documented (rate limits, missing creds, dry_run, etc.)
* **Dependencies Status**: STABLE - Telegram API is mature, httpx is well-tested

---

## Test Strategy by Component

### 1. NotificationEvent Dataclass - **TDD**

**Approach**: TDD
**Rationale**: Pure data structure with clear fields from research. Tests define the contract.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Create event with all required fields
  * Create event with optional fields
  * Default timestamp generation
  * Serialization/deserialization if needed
* Edge Cases:
  * Empty data dict
  * None values for optional fields

**Testing Sequence (TDD)**:
1. Write test for creating event with required fields
2. Implement minimal NotificationEvent dataclass
3. Write test for optional fields and defaults
4. Add default_factory for timestamp
5. Refactor if needed

---

### 2. NotificationChannel Protocol - **TDD**

**Approach**: TDD
**Rationale**: Protocol defines the contract for all channels. Tests ensure protocol is implementable and consistent.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Protocol has required methods: `send()`, `format()`, `supports_event()`, `poll()`
  * Protocol has required properties: `name`, `enabled`
  * Mock implementation satisfies protocol
  * `@runtime_checkable` works correctly
* Edge Cases:
  * Partial implementation fails isinstance check

**Testing Sequence (TDD)**:
1. Write test that mock class satisfies Protocol
2. Define Protocol with method signatures
3. Write test for each method signature
4. Verify runtime_checkable decorator works

---

### 3. EventBus - **TDD**

**Approach**: TDD
**Rationale**: Core infrastructure with complex async behavior. TDD ensures reliability.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit, async
* Critical Scenarios:
  * `subscribe()` adds channel to list
  * `unsubscribe()` removes channel by name
  * `emit()` sends to channels that support event type
  * `emit()` skips disabled channels
  * `emit()` is non-blocking (fire and forget)
  * Retry on RateLimitError with exponential backoff
  * Max retries exceeded logs error, doesn't raise
  * Multiple channels receive same event
* Edge Cases:
  * No channels subscribed
  * Channel throws unexpected exception
  * All channels fail

**Testing Sequence (TDD)**:
1. Write test: `subscribe()` adds channel
2. Implement subscribe method
3. Write test: `emit()` calls channel.send()
4. Implement emit with asyncio.create_task
5. Write test: retry on RateLimitError
6. Implement retry logic with exponential backoff
7. Write test: max retries exceeded
8. Implement max retry limit
9. Refactor for clarity

---

### 4. MessageTemplates - **TDD**

**Approach**: TDD
**Rationale**: Template rendering is pure logic with clear inputs/outputs. Perfect for TDD.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Render template for each event type
  * Template substitutes event data correctly
  * Missing template falls back to default
  * Emoji status indicators based on success/failure
  * HTML formatting preserved
* Edge Cases:
  * Event data missing expected keys
  * Event type not in templates dict
  * Empty event data

**Testing Sequence (TDD)**:
1. Write test: render stage_changed template
2. Implement TEMPLATES dict with stage_changed
3. Write test: render agent_failed template
4. Add agent_failed template
5. Write test: fallback for unknown event
6. Implement fallback logic
7. Write test: emoji substitution
8. Implement conditional emoji logic

---

### 5. TelegramChannel - **CODE-FIRST**

**Approach**: Code-First
**Rationale**: External HTTP integration. Implementation reveals edge cases. Mock httpx after understanding response patterns.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit with mocked httpx
* Critical Scenarios:
  * Successful send returns True
  * dry_run logs message, doesn't send
  * Missing credentials returns False
  * HTTP 429 raises RateLimitError with retry_after
  * HTTP 4xx/5xx logs error, returns False
  * Network error logs error, returns False
  * format() uses MessageTemplates
  * supports_event() checks subscribed events
  * poll() returns None (stub for future)
* Edge Cases:
  * Empty chat_id env var
  * Malformed API response
  * Timeout during send

**Testing Sequence (Code-First)**:
1. Implement TelegramChannel with httpx
2. Test successful send with mocked response
3. Test dry_run mode
4. Test missing credentials
5. Test rate limit handling
6. Test error responses
7. Test timeout handling

---

### 6. Environment Variable Resolver - **TDD**

**Approach**: TDD
**Rationale**: Pure function with clear input/output. Regex pattern matching is well-suited to TDD.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Resolve single env var: `${VAR}` → value
  * Resolve multiple env vars in one string
  * Missing env var resolves to empty string
  * Non-string values pass through unchanged
  * Nested dict/list resolution
* Edge Cases:
  * Malformed pattern: `${` without closing `}`
  * Empty env var name: `${}`
  * Non-env-var dollar sign: `$notavar`

**Testing Sequence (TDD)**:
1. Write test: resolve single var
2. Implement regex pattern and replacement
3. Write test: resolve multiple vars
4. Verify regex handles multiple matches
5. Write test: nested dict resolution
6. Implement recursive resolution

---

### 7. Notification Config Validation - **TDD**

**Approach**: TDD
**Rationale**: Follows existing ConfigLoader validation pattern. Clear error cases.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Valid notifications config loads successfully
  * Missing `type` field raises ConfigError
  * Invalid channel type raises ConfigError
  * Invalid events list raises ConfigError
  * `dry_run` must be boolean
  * Env var references in token/chat_id accepted
* Edge Cases:
  * Empty channels array
  * Notifications disabled (enabled: false)
  * Unknown fields ignored

**Testing Sequence (TDD)**:
1. Write test: valid config loads
2. Implement `_validate_notifications()`
3. Write test: missing type raises error
4. Add type validation
5. Write test: invalid type raises error
6. Add valid types check
7. Continue for each validation rule

---

### 8. CLI Init Notification Setup - **CODE-FIRST**

**Approach**: Code-First
**Rationale**: Interactive console I/O is harder to test. Implement then verify behavior.

**Test Requirements:**
* Coverage Target: 80%
* Test Types: Unit with mocked input/output
* Critical Scenarios:
  * User declines setup → no notifications config
  * User provides token and chat_id → config written
  * User skips token → no config
  * Instructions for env vars printed
* Edge Cases:
  * Empty input on token prompt
  * Interrupt during setup

**Testing Sequence (Code-First)**:
1. Implement `_setup_telegram_notifications()`
2. Test with mocked input returning "n"
3. Test with mocked input providing credentials
4. Verify config structure matches expected

---

### 9. Integration: EventBus + ExecutionLoop - **CODE-FIRST**

**Approach**: Code-First
**Rationale**: Integration tests verify wiring. Implementation-dependent.

**Test Requirements:**
* Coverage Target: 80%
* Test Types: Integration
* Critical Scenarios:
  * EventBus receives events from on_progress
  * Notifications sent when workflow advances
  * Notification failures don't block workflow
* Edge Cases:
  * No notification config → no EventBus created

---

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0
* **Async Support**: pytest-asyncio 0.23.0 (asyncio_mode = "auto")
* **Mocking**: pytest-mock 3.12.0, unittest.mock (AsyncMock, MagicMock)
* **Coverage**: pytest-cov 4.1.0
* **Configuration**: pyproject.toml [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking HTTP**: `pytest-httpx` or manual `AsyncMock` on httpx.AsyncClient
* **Assertions**: pytest built-in (assert statements)
* **Coverage**: pytest-cov with 80% target (existing)
* **Test Data**: Inline fixtures, conftest.py patterns

### Test Organization
* **Test Location**: `tests/test_notifications/`
* **Naming Convention**: `test_*.py` files, `Test*` classes, `test_*` functions
* **Fixture Strategy**: Module-level conftest.py, shared fixtures in root conftest.py
* **Setup/Teardown**: pytest fixtures with function/class scope

---

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% (minimum)
* **Integration Coverage**: 80%
* **Critical Path Coverage**: 100% (EventBus.emit, TelegramChannel.send)
* **Error Path Coverage**: 95%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| NotificationEvent | 100% | N/A | HIGH | Pure dataclass |
| NotificationChannel Protocol | 100% | N/A | CRITICAL | Contract definition |
| EventBus | 95% | 80% | CRITICAL | Core routing |
| MessageTemplates | 100% | N/A | HIGH | Template rendering |
| TelegramChannel | 90% | 80% | HIGH | HTTP integration |
| Env Var Resolver | 100% | N/A | MEDIUM | Pure function |
| Config Validation | 95% | N/A | HIGH | Follows existing pattern |
| CLI Init Setup | 80% | N/A | MEDIUM | Interactive I/O |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **EventBus Emit Non-Blocking** (Priority: CRITICAL)
   * **Description**: Verify emit() returns immediately without waiting for channel sends
   * **Test Type**: Unit (async)
   * **Success Criteria**: emit() completes in <1ms even if channel.send() would take 5s
   * **Test Approach**: TDD

2. **Graceful Failure on Network Error** (Priority: CRITICAL)
   * **Description**: Network errors in TelegramChannel are logged but don't raise
   * **Test Type**: Unit (mocked httpx)
   * **Success Criteria**: send() returns False, logs error, no exception propagates
   * **Test Approach**: Code-First

3. **Rate Limit Retry with Backoff** (Priority: HIGH)
   * **Description**: HTTP 429 triggers exponential backoff retry (up to 3 attempts)
   * **Test Type**: Unit (async)
   * **Success Criteria**: Retry delays double each attempt (1s, 2s, 4s)
   * **Test Approach**: TDD

4. **Dry Run Mode** (Priority: HIGH)
   * **Description**: dry_run=True logs formatted message without HTTP call
   * **Test Type**: Unit
   * **Success Criteria**: No HTTP request made, log contains formatted message
   * **Test Approach**: Code-First

5. **Environment Variable Resolution** (Priority: HIGH)
   * **Description**: `${VAR}` patterns resolve to env var values at runtime
   * **Test Type**: Unit
   * **Success Criteria**: Config with `${TOKEN}` resolves to os.environ["TOKEN"]
   * **Test Approach**: TDD

6. **Config Validation Errors** (Priority: HIGH)
   * **Description**: Invalid notification config raises ConfigError with clear message
   * **Test Type**: Unit
   * **Success Criteria**: Error message identifies the invalid field
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Missing env var**: `${UNDEFINED}` resolves to empty string, send() returns False
* **Empty channels list**: EventBus created but emit() is no-op
* **All channels disabled**: emit() skips all channels gracefully
* **Malformed API response**: TelegramChannel handles non-JSON response
* **Concurrent emit calls**: Multiple events emitted simultaneously don't interfere
* **Long message truncation**: Messages over 4096 chars are truncated (Telegram limit)

### Error Scenarios

* **HTTP 401 Unauthorized**: Invalid token → log critical, return False
* **HTTP 403 Forbidden**: Bot blocked → log warning, return False
* **HTTP 429 Rate Limited**: Retry with backoff → retry_after from response
* **HTTP 500+ Server Error**: Retry once → then log error, return False
* **Connection Timeout**: httpx.TimeoutException → log error, return False
* **DNS Resolution Failure**: httpx.ConnectError → log error, return False

---

## Test Data Strategy

### Test Data Requirements
* **NotificationEvent samples**: Pre-built events for each event type
* **Config fixtures**: Valid and invalid notification configs
* **HTTP responses**: Mocked Telegram API responses (success, errors)

### Test Data Management
* **Storage**: Inline in test files or conftest.py fixtures
* **Generation**: Factory functions for event creation
* **Isolation**: Each test uses fresh event/config instances
* **Cleanup**: No cleanup needed (no persistent state)

---

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_orchestration/test_progress.py`
**Pattern**: Event handling tests with Mock

```python
class TestCreateProgressCallback:
    """Tests for create_progress_callback function."""

    def test_agent_running_event(self) -> None:
        """agent_running event sets agent to running state with task."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        callback("agent_running", {"agent_id": "pm", "task": "Planning project"})

        status = manager.get("pm")
        assert status is not None
        assert status.state == AgentState.RUNNING
        assert status.task == "Planning project"
```

**Key Conventions:**
* Class per component/function
* Descriptive test method names
* Arrange-Act-Assert structure
* Type hints on test methods

### Async Test Pattern

**File**: `tests/test_orchestration/test_parallel_executor.py`

```python
class TestParallelExecutor:
    @pytest.mark.asyncio
    async def test_execute_single_task(self) -> None:
        """Execute a single task successfully."""
        executor = ParallelExecutor(max_concurrent=2)
        mock_client = AsyncMock()
        mock_client.execute_streaming.return_value = "Task done"
        
        # ... test logic
```

### Recommended Test Structure for Notifications

```python
# tests/test_notifications/test_event_bus.py

import pytest
from unittest.mock import AsyncMock, MagicMock

from teambot.notifications.event_bus import EventBus, RateLimitError
from teambot.notifications.events import NotificationEvent


class TestEventBusSubscribe:
    """Tests for EventBus.subscribe()."""

    def test_subscribe_adds_channel(self) -> None:
        """subscribe() adds channel to internal list."""
        bus = EventBus()
        channel = MagicMock()
        channel.name = "test-channel"

        bus.subscribe(channel)

        assert len(bus._channels) == 1
        assert bus._channels[0].name == "test-channel"


class TestEventBusEmit:
    """Tests for EventBus.emit()."""

    @pytest.mark.asyncio
    async def test_emit_calls_channel_send(self) -> None:
        """emit() calls send() on subscribed channels."""
        bus = EventBus()
        channel = MagicMock()
        channel.name = "test"
        channel.enabled = True
        channel.supports_event.return_value = True
        channel.send = AsyncMock(return_value=True)
        bus.subscribe(channel)

        event = NotificationEvent(event_type="stage_changed", data={"stage": "SETUP"})
        await bus.emit(event)

        # Allow async task to complete
        await asyncio.sleep(0.01)
        channel.send.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_skips_disabled_channel(self) -> None:
        """emit() does not call send() on disabled channels."""
        bus = EventBus()
        channel = MagicMock()
        channel.name = "disabled"
        channel.enabled = False
        channel.send = AsyncMock()
        bus.subscribe(channel)

        event = NotificationEvent(event_type="stage_changed", data={})
        await bus.emit(event)

        await asyncio.sleep(0.01)
        channel.send.assert_not_called()
```

---

## Success Criteria

### Test Implementation Complete When:
* [x] All critical scenarios have tests
* [x] Coverage targets are met per component
* [x] All edge cases are tested
* [x] Error paths are validated
* [x] Tests follow codebase conventions
* [x] Tests are maintainable and clear
* [x] CI/CD integration is working

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast (<100ms for unit tests)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem
* Mock/stub usage is appropriate and minimal
* Async tests use `@pytest.mark.asyncio` decorator

---

## Implementation Guidance

### For TDD Components (Protocol, EventBus, Templates, Env Resolver, Config):
1. Start with simplest test case
2. Write minimal code to pass
3. Add next test case
4. Refactor when all tests pass
5. Focus on behavior, not implementation

### For Code-First Components (TelegramChannel, CLI Init):
1. Implement core functionality
2. Add happy path test with mocked HTTP
3. Identify edge cases from implementation
4. Add edge case tests
5. Verify coverage meets target

### For Hybrid Approach:
1. Start with TDD components (Protocol, EventBus, Templates)
2. These provide stable foundation for integration
3. Implement TelegramChannel with Code-First
4. Use TDD EventBus tests to verify integration
5. CLI init is last (depends on config validation)

---

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD for core ensures reliable event routing
* Code-First for HTTP avoids over-mocking before understanding API
* High coverage targets match project standards
* Existing test patterns reduce learning curve

### Accepted Trade-offs:
* TelegramChannel tests require httpx mocking (slightly more complex)
* CLI init tests need input mocking (less natural)
* Async tests add slight complexity vs sync

### Risk Mitigation:
* EventBus non-blocking test ensures workflow can't be stalled
* Retry logic tests ensure rate limits are handled correctly
* Error path tests ensure graceful degradation

---

## References

* **Feature Spec**: Objective document in working directory
* **Research Doc**: [.agent-tracking/research/20260211-realtime-notifications-research.md](../research/20260211-realtime-notifications-research.md)
* **Test Examples**: tests/test_orchestration/test_progress.py, tests/test_messaging/test_protocol.py
* **Test Config**: pyproject.toml [tool.pytest.ini_options]
* **Async Patterns**: tests/test_orchestration/test_parallel_executor.py

---

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow TDD for core, Code-First for HTTP integration

---

**Strategy Status**: DRAFT
**Approved By**: PENDING
**Ready for Planning**: YES
