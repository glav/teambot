<!-- markdownlint-disable-file -->
# Test Strategy: @notify Command Mode Bypass

**Strategy Date**: 2026-02-18
**Feature Specification**: .teambot/notify-command/artifacts/feature_spec.md
**Specification Review**: .teambot/notify-command/artifacts/spec_review.md
**Strategist**: Builder-2 (Test Strategy Agent)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Assessment | TDD Points | Code-First Points |
|--------|----------|------------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES - 6 AT scenarios, precise FR IDs | 3 | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | LOW - Single conditional check in `supports_event()` | 0 | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | MEDIUM - User experience issue, but not data loss | 2 | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO - Well-understood fix | 0 | 0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | YES - Simple bypass condition | 0 | 2 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | LOW - Surgical fix, tests first is appropriate | 0 | 0 |
| **Requirements Stability** | Are requirements likely to change during development? | NO - Stable, well-defined spec | 0 | 0 |

### Scoring Summary

| Score Type | Total |
|------------|-------|
| **TDD Score** | 5 |
| **Code-First Score** | 2 |

### Decision Thresholds

| TDD Score | Code-First Score | Recommendation |
|-----------|------------------|----------------|
| ≥ 6 | < 4 | TDD |
| < 4 | ≥ 5 | Code-First |
| 4-5 | 4-5 | Hybrid |

**Decision: Hybrid (TDD Score 5 in threshold 4-5)**

However, given the extremely small scope (≤20 lines per NFR-001) and clear regression requirements, we **recommend TDD** as the primary approach since:
- Clear acceptance test scenarios are already defined (6 in spec)
- Regression prevention is critical (FR-002, FR-003, FR-004)
- Tests will validate behavior before implementation

## Recommended Testing Approach

**Primary Approach**: **TDD** (Test-Driven Development)

### Rationale

This feature is a surgical fix with well-defined requirements and clear acceptance criteria. The specification includes 6 acceptance test scenarios that map directly to testable behaviors. TDD is appropriate because:

1. **Clear requirements**: The spec defines exactly what should happen with `custom_message` events vs other events
2. **Regression risk**: The change must not break existing `notification_mode` filtering for automated events
3. **Small scope**: ≤20 lines of production code makes TDD overhead minimal
4. **Behavior validation**: Tests document the expected distinction between explicit user requests and automated events

**Key Factors:**
* Complexity: **LOW** - Single conditional check addition
* Risk: **MEDIUM** - User-facing behavior, regression possible
* Requirements Clarity: **CLEAR** - 6 acceptance scenarios defined
* Time Pressure: **LOW** - No urgent deadline

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Low - Adding `event_type == "custom_message"` check
* **Integration Depth**: Low - Single method modification in `TelegramChannel.supports_event()`
* **State Management**: None - Stateless filtering logic
* **Error Scenarios**: Minimal - Only existing guards (disabled, no channels)

### Risk Profile
* **Business Criticality**: MEDIUM - Affects user trust in @notify command
* **User Impact**: High for users of `notification_mode` settings who also use `@notify`
* **Data Sensitivity**: None - Message content is user-provided and transient
* **Failure Cost**: LOW - Bug causes silent message drop, not data corruption

### Requirements Clarity
* **Specification Completeness**: COMPLETE - Full spec with acceptance tests
* **Acceptance Criteria Quality**: PRECISE - 6 scenarios with clear verification
* **Edge Cases Identified**: 2 documented (explicit events array, disabled state)
* **Dependencies Status**: STABLE - No external dependencies

## Test Strategy by Component

### Component 1: `TelegramChannel.supports_event()` - **TDD**

**Approach**: TDD
**Rationale**: This is the core logic change. Tests should be written first to document expected behavior and catch regressions.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `custom_message` returns `True` when `subscribed_events` is mode-based (from `notification_mode`)
  * `custom_message` returns `True` with `stages_only` mode filtering
  * `custom_message` returns `True` with `agent_status` mode filtering
  * `custom_message` returns `False` when explicit `events` array excludes it
* Edge Cases:
  * `custom_message` with `subscribed_events=None` (already returns `True`)
  * Explicit `events: ["custom_message"]` - should still work
  * Explicit `events: []` (empty) - should return `False` (user explicitly disabled)

**Testing Sequence** (TDD):
1. Write test for `custom_message` bypass with `stages_only` mode
2. Implement minimal passing code in `supports_event()`
3. Write test for `custom_message` bypass with `agent_status` mode
4. Verify implementation covers both cases
5. Write test for explicit `events` array precedence
6. Refine implementation to respect explicit configuration

### Component 2: Config Integration (`_create_channel`) - **CODE_FIRST**

**Approach**: Code-First (existing tests sufficient)
**Rationale**: The `_create_channel` function already correctly passes `subscribed_events` to `TelegramChannel`. No changes expected here. Existing tests in `test_config.py` provide sufficient coverage.

**Test Requirements:**
* Coverage Target: No new tests needed
* Test Types: Integration (existing)
* Critical Scenarios:
  * Mode-based filtering continues to work (existing tests)
  * Explicit events array takes precedence (existing tests)
* Edge Cases:
  * Empty events array behavior (existing test)

### Component 3: Executor `_handle_notify()` - **CODE_FIRST**

**Approach**: Code-First (existing tests sufficient)
**Rationale**: The executor correctly emits `custom_message` event type. No changes needed in executor. Existing tests in `test_executor.py` cover the notification flow.

**Test Requirements:**
* Coverage Target: No new tests needed
* Test Types: Unit (existing)
* Verification: Ensure `@notify` emits `custom_message` event (already tested)

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 9.0.2
* **Version**: Python 3.12
* **Configuration**: `pyproject.toml`
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (MagicMock, AsyncMock) - Standard usage
* **Assertions**: pytest built-in assertions
* **Coverage**: `pytest-cov` - Target: maintain existing + new cases
* **Test Data**: In-memory fixtures, no external data needed

### Test Organization
* **Test Location**: `tests/test_notifications/`
* **Naming Convention**: `test_*.py` files, `test_*` methods
* **Fixture Strategy**: Use `conftest.py` shared fixtures
* **Setup/Teardown**: `monkeypatch` for env vars, no complex teardown

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 100% for new code
* **Integration Coverage**: Existing tests sufficient
* **Critical Path Coverage**: 100% (`custom_message` bypass logic)
* **Error Path Coverage**: N/A (no new error paths)

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `TelegramChannel.supports_event()` | 100% | N/A | CRITICAL | Core change location |
| `_create_channel()` | Existing | Existing | HIGH | No changes, verify no regression |
| `_handle_notify()` | Existing | Existing | MEDIUM | No changes expected |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **custom_message bypass with stages_only mode** (Priority: CRITICAL)
   * **Description**: `@notify` delivers when `notification_mode: stages_only`
   * **Test Type**: Unit
   * **Success Criteria**: `supports_event("custom_message")` returns `True` when `subscribed_events` is `STAGES_ONLY_EVENTS`
   * **Test Approach**: TDD - Write first

2. **custom_message bypass with agent_status mode** (Priority: CRITICAL)
   * **Description**: `@notify` delivers when `notification_mode: agent_status`
   * **Test Type**: Unit
   * **Success Criteria**: `supports_event("custom_message")` returns `True` when `subscribed_events` is `AGENT_STATUS_EVENTS`
   * **Test Approach**: TDD - Write first

3. **Explicit events array excludes custom_message** (Priority: HIGH)
   * **Description**: User can explicitly exclude `custom_message` via `events` array
   * **Test Type**: Unit
   * **Success Criteria**: `supports_event("custom_message")` returns `False` when `events: ["stage_changed"]`
   * **Test Approach**: TDD

4. **Mode filtering preserved for other events** (Priority: HIGH)
   * **Description**: `stages_only` still filters `agent_running`, etc.
   * **Test Type**: Unit
   * **Success Criteria**: Existing tests continue to pass
   * **Test Approach**: Regression verification

5. **All mode includes custom_message** (Priority: MEDIUM)
   * **Description**: `notification_mode: all` continues to accept everything
   * **Test Type**: Unit
   * **Success Criteria**: `supports_event("custom_message")` returns `True` when `subscribed_events` is `None`
   * **Test Approach**: Existing test coverage

6. **Empty events array excludes all** (Priority: MEDIUM)
   * **Description**: `events: []` should exclude everything including `custom_message`
   * **Test Type**: Unit
   * **Success Criteria**: `supports_event("custom_message")` returns `False` when `subscribed_events` is empty set
   * **Test Approach**: Existing test + verify

### Edge Cases to Cover

* **Explicit events with custom_message included**: `events: ["custom_message", "stage_changed"]` - should accept `custom_message`
* **Empty subscribed_events (explicit empty set)**: Should return `False` for all including `custom_message`
* **None subscribed_events (no filter)**: Should return `True` for all including `custom_message`

### Error Scenarios

* **N/A**: No new error paths introduced. Existing guards (`notifications.enabled: false`, no channels) remain unchanged.

## Test Data Strategy

### Test Data Requirements
* `TelegramChannel` instances: Create with different `subscribed_events` configurations
* Mode event sets: Import `STAGES_ONLY_EVENTS`, `AGENT_STATUS_EVENTS` from `modes.py`

### Test Data Management
* **Storage**: In-memory test fixtures
* **Generation**: Programmatic in test setup
* **Isolation**: Each test creates its own channel instance
* **Cleanup**: None needed (no persistent state)

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_notifications/test_telegram.py`
**Pattern**: Unit tests for `TelegramChannel.supports_event()`

```python
class TestTelegramChannelSupportsEvent:
    """Tests for TelegramChannel.supports_event()."""

    def test_supports_all_when_no_filter(self) -> None:
        """With no filter, supports all events."""
        channel = TelegramChannel()
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_failed") is True
        assert channel.supports_event("any_event") is True

    def test_supports_only_subscribed_events(self) -> None:
        """With filter, supports only listed events."""
        channel = TelegramChannel(subscribed_events={"stage_changed", "agent_failed"})
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_failed") is True
        assert channel.supports_event("agent_complete") is False
```

**Key Conventions:**
* Class-based test organization with descriptive names
* Docstrings describe expected behavior
* Multiple assertions per test for related checks
* Direct construction of `TelegramChannel` with test configs

### Recommended Test Structure for New Tests

```python
class TestCustomMessageBypass:
    """Tests for custom_message event type bypass behavior."""

    def test_custom_message_bypasses_stages_only_mode(self) -> None:
        """custom_message is delivered even with stages_only mode filtering."""
        channel = TelegramChannel(subscribed_events=STAGES_ONLY_EVENTS)
        assert channel.supports_event("custom_message") is True
        # Verify other events still filtered
        assert channel.supports_event("agent_running") is False

    def test_custom_message_bypasses_agent_status_mode(self) -> None:
        """custom_message is delivered even with agent_status mode filtering."""
        channel = TelegramChannel(subscribed_events=AGENT_STATUS_EVENTS)
        assert channel.supports_event("custom_message") is True
        # Verify unrelated events still filtered
        assert channel.supports_event("parallel_group_start") is False

    def test_explicit_events_can_exclude_custom_message(self) -> None:
        """Explicit events array takes precedence over bypass."""
        channel = TelegramChannel(subscribed_events={"stage_changed"})
        assert channel.supports_event("custom_message") is False
        assert channel.supports_event("stage_changed") is True

    def test_empty_events_excludes_custom_message(self) -> None:
        """Empty events set excludes all events including custom_message."""
        channel = TelegramChannel(subscribed_events=set())
        assert channel.supports_event("custom_message") is False
```

## Success Criteria

### Test Implementation Complete When:
- [ ] All critical scenarios have tests (4 new tests minimum)
- [ ] Coverage targets met (100% for new code paths)
- [ ] All edge cases tested (explicit events, empty set)
- [ ] Error paths validated (N/A - no new paths)
- [ ] Tests follow codebase conventions (class-based, descriptive)
- [ ] Tests are maintainable and clear
- [ ] CI/CD passes (all existing + new tests)

### Test Quality Indicators:
* Tests are readable and self-documenting (docstrings present)
* Tests are fast and reliable (no external dependencies)
* Tests are independent (each creates own channel instance)
* Failures clearly indicate the problem (specific assertions)
* Mock/stub usage is minimal (direct TelegramChannel construction)

## Implementation Guidance

### For TDD Components:

1. **Add new test class** `TestCustomMessageBypass` to `tests/test_notifications/test_telegram.py`
2. **Write failing tests** for `custom_message` bypass scenarios
3. **Run tests** to confirm they fail (`uv run pytest tests/test_notifications/test_telegram.py::TestCustomMessageBypass -v`)
4. **Implement** minimal change in `TelegramChannel.supports_event()` to pass tests
5. **Run all notification tests** to verify no regressions
6. **Refactor** if needed while keeping tests green

### Implementation Approach

The fix requires distinguishing between:
- **Mode-based filtering** (`notification_mode` setting): `custom_message` should bypass
- **Explicit events array**: User's explicit choice should be honored

Two implementation options:

**Option A (Preferred)**: Modify `supports_event()` to always return `True` for `custom_message` UNLESS the channel has an explicit events filter that doesn't include it. This requires tracking whether `subscribed_events` came from a mode or explicit config.

**Option B**: Add `custom_message` to all mode event sets (`STAGES_ONLY_EVENTS`, `AGENT_STATUS_EVENTS`). Simpler but changes the mode definitions.

**Option C (Simplest)**: In `supports_event()`, check if `event_type == "custom_message"` and return `True` before checking subscribed_events, UNLESS we need to respect explicit exclusion. This requires knowing if events came from explicit config.

The implementation should be guided by maintaining backwards compatibility and respecting FR-005 (explicit events array precedence).

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures regression prevention - tests document expected behavior
* Clear acceptance criteria make test writing straightforward
* Small scope means TDD overhead is minimal (4-6 tests)

### Accepted Trade-offs:
* Slight increase in test file size (adding new test class)
* Implementation requires understanding mode vs explicit events distinction

### Risk Mitigation:
* Running full notification test suite after changes catches regressions
* TDD approach documents expected behavior before implementation
* Existing tests for mode filtering remain unchanged

## References

* **Feature Spec**: [.teambot/notify-command/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/notify-command/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: `tests/test_notifications/test_telegram.py`, `tests/test_notifications/test_config.py`
* **Implementation Location**: `src/teambot/notifications/channels/telegram.py:71-75`
* **Mode Definitions**: `src/teambot/notifications/modes.py`

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow TDD approach per component

---

**Strategy Status**: DRAFT
**Approved By**: PENDING
**Ready for Planning**: YES

---

## Output Validation Checklist

TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE
- Approach: TDD (score 5, clear requirements favor TDD despite threshold)
- Coverage Targets: SPECIFIED (100% for new code)
- Components Covered: 3/3 (TelegramChannel core, config integration, executor)
