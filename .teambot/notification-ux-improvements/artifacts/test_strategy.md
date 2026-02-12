<!-- markdownlint-disable-file -->
# Test Strategy: Notification UX Improvements

**Strategy Date**: 2026-02-11
**Feature Specification**: .teambot/notification-ux-improvements/artifacts/feature_spec.md
**Research Reference**: .agent-tracking/research/20260211-realtime-notifications-research.md
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: HYBRID

### Rationale

This feature involves two distinct component types: event infrastructure (well-defined, high-impact) and REPL command handlers (simpler, pattern-following). The event emission and template rendering components are critical to the notification system's reliability and should use TDD to ensure all edge cases are covered before implementation. The `/notify` command handler follows established patterns in `commands.py` and can use a code-first approach since the pattern is well-established and the implementation is straightforward.

The hybrid approach optimizes development velocity while ensuring comprehensive coverage where it matters most. TDD for the templates and event emission guarantees correct behavior for lifecycle notifications, while code-first for the command handler allows rapid implementation following existing patterns.

**Key Factors:**
* Complexity: MEDIUM (new event types + templates + command handler)
* Risk: MEDIUM (extends existing notification system; must not break current functionality)
* Requirements Clarity: CLEAR (well-defined FRs with specific acceptance criteria)
* Time Pressure: MODERATE (incremental feature, not urgent)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | TDD Points | Code-First Points | Justification |
|--------|----------|-------|------------|-------------------|---------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES | 3 | 0 | 14 FRs with specific acceptance criteria in spec |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM | 1 | 0 | Template rendering with fallbacks, event emission timing |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | MEDIUM | 2 | 0 | Extends existing notification system; regression would break all notifications |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO | 0 | 0 | Well-defined feature with clear patterns |
| **Simplicity** | Is this straightforward CRUD or simple logic? | PARTIAL | 0 | 1 | Command handler is simple; templates/events are more complex |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO | 0 | 0 | Quality over speed |
| **Requirements Stability** | Are requirements likely to change during development? | STABLE | 0 | 0 | Spec is finalized and approved |

### Decision Calculation

| Category | Score |
|----------|-------|
| **TDD Score** | 6 |
| **Code-First Score** | 1 |

**Decision**: TDD Score (6) ≥ threshold (6) AND Code-First Score (1) < threshold (4) suggests **TDD**.

However, component-level analysis reveals:
- **Templates/Events**: High complexity, critical path → **TDD**
- **Command Handler**: Low complexity, follows existing pattern → **Code-First**

**Final Decision**: **HYBRID** (TDD for core, Code-First for command handler)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: LOW-MEDIUM - Template string formatting with conditional fallbacks and HTML escaping
* **Integration Depth**: MEDIUM - Integrates with EventBus, REPL dispatcher, and ExecutionLoop
* **State Management**: LOW - Stateless event emission; no complex state transitions
* **Error Scenarios**: MEDIUM - Missing config, missing objective info, delivery failures

### Risk Profile
* **Business Criticality**: MEDIUM - User-facing notification feature for run visibility
* **User Impact**: MEDIUM - All TeamBot users with notifications configured
* **Data Sensitivity**: LOW - Objective names only; no PII
* **Failure Cost**: MEDIUM - Broken notifications reduce trust but don't break core workflow

### Requirements Clarity
* **Specification Completeness**: COMPLETE - All 14 FRs documented with acceptance criteria
* **Acceptance Criteria Quality**: PRECISE - 7 detailed acceptance test scenarios
* **Edge Cases Identified**: 3 documented (missing objective name, missing config, delivery failure)
* **Dependencies Status**: STABLE - EventBus, templates, commands all stable

## Test Strategy by Component

### Event Types (events.py) - TDD

**Approach**: TDD
**Rationale**: New event type constants are simple but foundational. TDD ensures they're defined correctly before other components depend on them.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `orchestration_started` event creation with all required fields
  * `orchestration_completed` event creation with duration calculation
  * `custom_message` event creation with user message
* Edge Cases:
  * Missing optional fields use defaults
  * Event timestamp auto-generation

**Testing Sequence** (TDD):
1. Write test for `orchestration_started` event constant existence
2. Add constant to events.py
3. Write test for event creation with objective_name/objective_path
4. Verify event structure

### Templates (templates.py) - TDD

**Approach**: TDD
**Rationale**: Template rendering is critical for user-facing notification quality. HTML escaping and fallback behavior must be tested first to prevent XSS and ensure graceful degradation.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `orchestration_started` renders "🚀 Starting: {objective_name}"
  * `orchestration_completed` renders "✅ Completed: {objective_name}" with duration
  * `custom_message` renders user message with HTML escaping
* Edge Cases:
  * Missing objective_name falls back to "orchestration run"
  * HTML characters in objective name are escaped
  * HTML characters in custom message are escaped
  * Duration formatted correctly (human-readable)

**Testing Sequence** (TDD):
1. Write test for `orchestration_started` template output format
2. Add template to TEMPLATES dict
3. Write test for fallback when objective_name missing
4. Implement fallback logic
5. Write test for HTML escaping in objective_name
6. Verify escaping in context building
7. Repeat for `orchestration_completed` and `custom_message`

### ExecutionLoop Event Emission (execution_loop.py) - TDD

**Approach**: TDD
**Rationale**: Event emission at run start/end is the core feature. Getting the timing and data payload right is critical for user experience.

**Test Requirements:**
* Coverage Target: 90% (existing code already tested)
* Test Types: Unit + Integration
* Critical Scenarios:
  * `orchestration_started` emitted at run() entry
  * `orchestration_completed` emitted at successful run() exit
  * Events include objective_name from parsed objective
  * Progress callback receives both events
* Edge Cases:
  * Objective without name uses filename as fallback
  * Duration calculated correctly
  * Events emitted even if notification channels fail

**Testing Sequence** (TDD):
1. Write test: run() calls progress callback with "orchestration_started"
2. Add emit at run() entry
3. Write test: started event includes objective_name
4. Add objective context to event data
5. Write test: run() calls progress callback with "orchestration_completed" on success
6. Add emit at run() exit
7. Write test: completed event includes duration_seconds
8. Calculate and include duration

### /notify Command Handler (commands.py) - Code-First

**Approach**: Code-First
**Rationale**: Command handlers in this codebase follow a well-established pattern (see `handle_help`, `handle_status`, etc.). The implementation is straightforward: parse args, check config, emit event, return result.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `/notify Hello` sends "Hello" through EventBus
  * `/notify` without args returns usage help
  * `/notify` returns success feedback on delivery
* Edge Cases:
  * No EventBus available returns config error
  * Notification channels not configured returns helpful error
  * Multi-word messages preserved correctly

**Testing Sequence** (Code-First):
1. Implement `handle_notify` following existing handler pattern
2. Add dispatch routing for "notify" command
3. Add happy path tests (message sent, success feedback)
4. Add edge case tests (no args, no config)
5. Add `/notify` to help output
6. Add test for `/help` including `/notify`

### /help Update (commands.py) - Code-First

**Approach**: Code-First
**Rationale**: Simple string addition to existing help text. Pattern is already established.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `/help` output includes `/notify <message>`
* Edge Cases: None

**Testing Sequence** (Code-First):
1. Add `/notify` line to help output
2. Write test verifying `/notify` in help output

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: As specified in pyproject.toml
* **Configuration**: pyproject.toml `[tool.pytest.ini_options]`
* **Runner**: `uv run pytest` or `pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (MagicMock, AsyncMock) - Used extensively in notification tests
* **Assertions**: pytest built-in assertions
* **Coverage**: pytest-cov - Target coverage via `--cov=src/teambot`
* **Test Data**: Fixtures in conftest.py (sample_event, mock_channel, etc.)
* **Async**: pytest-asyncio with `asyncio_mode = "auto"`

### Test Organization
* **Test Location**: `tests/test_notifications/` for templates/events, `tests/test_repl/` for commands, `tests/test_orchestration/` for execution_loop
* **Naming Convention**: `test_*.py` files, `Test*` classes, `test_*` functions
* **Fixture Strategy**: Module-level conftest.py for shared fixtures
* **Setup/Teardown**: pytest fixtures with function scope

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 100% (new code)
* **Integration Coverage**: 80% (event emission through callback)
* **Critical Path Coverage**: 100%
* **Error Path Coverage**: 100%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| templates.py additions | 100% | N/A | CRITICAL | All 3 new templates |
| events.py additions | 100% | N/A | HIGH | Event type constants |
| execution_loop.py changes | 90% | 80% | CRITICAL | Start/complete events |
| commands.py additions | 100% | N/A | HIGH | /notify handler |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Orchestration Started Event** (Priority: CRITICAL)
   * **Description**: ExecutionLoop.run() emits orchestration_started with objective info
   * **Test Type**: Unit
   * **Success Criteria**: progress_callback receives event_type="orchestration_started" with data containing objective_name
   * **Test Approach**: TDD

2. **Orchestration Completed Event** (Priority: CRITICAL)
   * **Description**: ExecutionLoop.run() emits orchestration_completed on success
   * **Test Type**: Unit
   * **Success Criteria**: progress_callback receives event_type="orchestration_completed" with duration_seconds
   * **Test Approach**: TDD

3. **Started Template Rendering** (Priority: CRITICAL)
   * **Description**: orchestration_started renders as "🚀 Starting: {name}"
   * **Test Type**: Unit
   * **Success Criteria**: Output matches "🚀 <b>Starting</b>: {objective_name}"
   * **Test Approach**: TDD

4. **Completed Template Rendering** (Priority: CRITICAL)
   * **Description**: orchestration_completed renders with duration
   * **Test Type**: Unit
   * **Success Criteria**: Output includes "✅ <b>Completed</b>: {name}" and duration
   * **Test Approach**: TDD

5. **Custom Message Template Escaping** (Priority: HIGH)
   * **Description**: HTML in user messages is escaped
   * **Test Type**: Unit
   * **Success Criteria**: `<script>` becomes `&lt;script&gt;`
   * **Test Approach**: TDD

6. **/notify Command Success** (Priority: HIGH)
   * **Description**: /notify sends message through EventBus
   * **Test Type**: Unit
   * **Success Criteria**: EventBus.emit_sync called with custom_message event
   * **Test Approach**: Code-First

7. **/notify Usage Help** (Priority: MEDIUM)
   * **Description**: /notify without args shows usage
   * **Test Type**: Unit
   * **Success Criteria**: Returns CommandResult with "Usage: /notify <message>"
   * **Test Approach**: Code-First

8. **Missing Config Error** (Priority: HIGH)
   * **Description**: /notify with no EventBus shows helpful error
   * **Test Type**: Unit
   * **Success Criteria**: Returns error mentioning "teambot init" or "notifications"
   * **Test Approach**: Code-First

### Edge Cases to Cover

* **Missing objective_name**: Templates fall back to "orchestration run" text
* **HTML injection in objective_name**: Characters escaped via html.escape()
* **HTML injection in custom_message**: Characters escaped via html.escape()
* **No args to /notify**: Returns usage help, success=False
* **EventBus not available**: Returns config error with guidance
* **Duration calculation**: duration_seconds computed from start time

### Error Scenarios

* **EventBus.emit_sync raises**: Error logged but command returns success (fire-and-forget)
* **No notification channels configured**: /notify returns error with "teambot init" guidance
* **Objective file has no title**: Use filename stem as fallback

## Test Data Strategy

### Test Data Requirements
* **NotificationEvent fixtures**: Already available in tests/test_notifications/conftest.py
* **Mock EventBus**: Create mock with emit_sync method
* **Mock channel**: Already available (mock_channel fixture)
* **Sample objective**: Already available in tests/conftest.py

### Test Data Management
* **Storage**: Inline fixtures or conftest.py
* **Generation**: Manual definition with realistic values
* **Isolation**: Each test creates its own instances
* **Cleanup**: pytest fixtures handle teardown

## Example Test Patterns

### Example from Codebase

**File**: tests/test_notifications/test_templates.py
**Pattern**: Template rendering with event fixtures

```python
class TestMessageTemplates:
    """Tests for MessageTemplates.render()."""

    @pytest.fixture
    def templates(self) -> MessageTemplates:
        """Create MessageTemplates instance."""
        return MessageTemplates()

    def test_render_stage_changed(self, templates: MessageTemplates) -> None:
        """Render stage_changed event."""
        event = NotificationEvent(
            event_type="stage_changed",
            data={"stage": "IMPLEMENTATION"},
            feature_name="my-feature",
        )

        result = templates.render(event)

        assert "Stage: IMPLEMENTATION" in result
        assert "my-feature" in result
```

**Key Conventions:**
* Class-based test organization with descriptive names
* pytest fixtures for shared setup
* Direct assertion with descriptive messages
* Test docstrings describe intent

### Recommended Test Structure

```python
"""Tests for orchestration lifecycle notifications."""

from teambot.notifications.events import NotificationEvent
from teambot.notifications.templates import MessageTemplates


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
```

## Success Criteria

### Test Implementation Complete When:
- [ ] All critical scenarios have tests
- [ ] Coverage targets are met per component
- [ ] All edge cases are tested
- [ ] Error paths are validated
- [ ] Tests follow codebase conventions (class-based, fixtures, docstrings)
- [ ] Tests are maintainable and clear
- [ ] `uv run pytest tests/test_notifications/test_templates.py` passes
- [ ] `uv run pytest tests/test_repl/test_commands.py` passes
- [ ] `uv run pytest tests/test_orchestration/test_execution_loop.py` passes

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast and reliable (no flakiness)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem
* Mock/stub usage is appropriate and minimal

## Implementation Guidance

### For TDD Components (Templates, Events, ExecutionLoop):
1. Start with simplest test case (e.g., event type constant exists)
2. Write minimal code to pass
3. Add next test case (e.g., template renders with basic data)
4. Refactor when all tests pass
5. Focus on behavior, not implementation

### For Code-First Components (/notify handler):
1. Implement `handle_notify` following `handle_help` pattern
2. Add dispatch routing in SystemCommands.dispatch()
3. Add happy path test
4. Add edge case tests (no args, no config)
5. Verify coverage meets target

### For Hybrid Approach:
1. Start with TDD components (templates, events, execution_loop)
2. Proceed to Code-First components (/notify handler)
3. Ensure integration tests cover boundaries (event emission → template rendering)
4. Validate overall feature behavior with acceptance scenarios

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures template correctness and edge case coverage
* Code-first for handler enables rapid implementation following proven patterns
* Hybrid balances quality with velocity

### Accepted Trade-offs:
* Slightly more upfront time for TDD components
* Code-first for handler may miss edge cases (mitigated by explicit edge case list)

### Risk Mitigation:
* Regression tests ensure existing notifications continue working
* HTML escaping tests prevent XSS vulnerabilities
* Fallback tests ensure graceful degradation

## References

* **Feature Spec**: [.teambot/notification-ux-improvements/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/notification-ux-improvements/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: 
  - tests/test_notifications/test_templates.py
  - tests/test_notifications/test_events.py
  - tests/test_repl/test_commands.py
  - tests/test_orchestration/test_execution_loop.py
* **Test Standards**: pyproject.toml `[tool.pytest.ini_options]`

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow:
   - TDD for templates.py additions
   - TDD for events.py additions
   - TDD for execution_loop.py event emission
   - Code-First for commands.py /notify handler

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES
