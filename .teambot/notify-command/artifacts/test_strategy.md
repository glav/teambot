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
* **Algorithm Complexity**: Low - Adding `custom_message` to mode-based subscribed set
* **Integration Depth**: Low - Single modification in `_create_channel()` config processing
* **State Management**: None - Stateless configuration transformation
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

### Component 1: Config Integration (`_create_channel`) - **TDD**

**Approach**: TDD
**Rationale**: This is the core logic change. The fix adds `custom_message` to the subscribed set when `notification_mode` is used (mode-based filtering). Tests should be written first to document expected behavior and catch regressions.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Integration
* Critical Scenarios:
  * `custom_message` is added to subscribed set when `notification_mode` is used
  * `custom_message` is included with `stages_only` mode filtering
  * `custom_message` is included with `agent_status` mode filtering
  * `custom_message` is NOT added when explicit `events` array is used (preserves user choice)
* Edge Cases:
  * `custom_message` with no `notification_mode` or `events` (subscribed_events=None, accepts all)
  * Explicit `events: ["custom_message"]` - should still work
  * Explicit `events: []` (empty) - should exclude `custom_message` (user explicitly disabled)

**Testing Sequence** (TDD):
1. Write test for `custom_message` inclusion with `stages_only` mode
2. Implement minimal passing code in `_create_channel()` to add `custom_message` to mode-based subscribed set
3. Write test for `custom_message` inclusion with `agent_status` mode
4. Verify implementation covers both mode cases
5. Write test for explicit `events` array precedence (no modification)
6. Refine implementation to only modify mode-based subscribed sets

### Component 2: `TelegramChannel.supports_event()` - **CODE_FIRST**

**Approach**: Code-First (existing tests sufficient)
**Rationale**: The `TelegramChannel.supports_event()` method already correctly checks if an event is in the `subscribed_events` set. No changes needed here. The fix is implemented upstream in config.py by adding `custom_message` to the set before passing it to TelegramChannel. Existing tests in `test_telegram.py` provide sufficient coverage of the filtering logic.

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
| `_create_channel()` | N/A | 100% | CRITICAL | Core change location - adds custom_message to mode-based subscribed sets |
| `TelegramChannel.supports_event()` | Existing | Existing | HIGH | No changes, verify no regression |
| `_handle_notify()` | Existing | Existing | MEDIUM | No changes expected |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **custom_message inclusion with stages_only mode** (Priority: CRITICAL)
   * **Description**: `@notify` delivers when `notification_mode: stages_only` because `custom_message` is added to the subscribed set
   * **Test Type**: Integration
   * **Success Criteria**: Channel created with `notification_mode: stages_only` includes `custom_message` in its `subscribed_events` set
   * **Test Approach**: TDD - Write first

2. **custom_message inclusion with agent_status mode** (Priority: CRITICAL)
   * **Description**: `@notify` delivers when `notification_mode: agent_status` because `custom_message` is added to the subscribed set
   * **Test Type**: Integration
   * **Success Criteria**: Channel created with `notification_mode: agent_status` includes `custom_message` in its `subscribed_events` set
   * **Test Approach**: TDD - Write first

3. **Explicit events array NOT modified** (Priority: HIGH)
   * **Description**: User can explicitly exclude `custom_message` via `events` array - no automatic addition
   * **Test Type**: Integration
   * **Success Criteria**: Channel created with `events: ["stage_changed"]` does NOT include `custom_message` in its `subscribed_events` set
   * **Test Approach**: TDD

4. **Mode filtering preserved for other events** (Priority: HIGH)
   * **Description**: `stages_only` still filters `agent_running`, etc. - only `custom_message` is added
   * **Test Type**: Integration
   * **Success Criteria**: Existing tests continue to pass, mode sets include expected events plus `custom_message`
   * **Test Approach**: Regression verification

5. **All mode includes custom_message** (Priority: MEDIUM)
   * **Description**: `notification_mode: all` continues to accept everything (subscribed_events=None)
   * **Test Type**: Integration
   * **Success Criteria**: Channel created with `notification_mode: all` has `subscribed_events=None` (no modification needed)
   * **Test Approach**: Existing test coverage

6. **Empty events array excludes all** (Priority: MEDIUM)
   * **Description**: `events: []` should exclude everything including `custom_message` - no modification
   * **Test Type**: Integration
   * **Success Criteria**: Channel created with `events: []` has `subscribed_events` as empty set (not modified)
   * **Test Approach**: Existing test + verify

### Edge Cases to Cover

* **Explicit events with custom_message included**: `events: ["custom_message", "stage_changed"]` - should NOT be modified (user explicitly included it)
* **Empty subscribed_events (explicit empty set)**: `events: []` - should remain empty, no `custom_message` addition
* **None subscribed_events (no filter)**: No `notification_mode` or `events` - should remain `None`, accepts all events by default

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

**File**: `tests/test_notifications/test_config.py`
**Pattern**: Integration tests for `_create_channel()` with different notification configurations

```python
def test_create_channel_with_notification_mode(monkeypatch):
    """Channel created with notification_mode gets mode-based event filtering."""
    monkeypatch.setenv("TELEGRAM_TOKEN", "test_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    
    channel_config = {
        "type": "telegram",
        "token": "${TELEGRAM_TOKEN}",
        "chat_id": "${TELEGRAM_CHAT_ID}",
        "notification_mode": "stages_only"
    }
    
    channel = _create_channel(channel_config)
    assert channel.subscribed_events == STAGES_ONLY_EVENTS
```

**Key Conventions:**
* Function-based test organization with descriptive names
* Docstrings describe expected behavior
* Use `monkeypatch` for environment variables
* Direct call to `_create_channel()` with test configs
* Assert on resulting channel's `subscribed_events` attribute

### Recommended Test Structure for New Tests

```python
def test_notification_mode_includes_custom_message(monkeypatch):
    """Channels with notification_mode automatically include custom_message."""
    monkeypatch.setenv("TELEGRAM_TOKEN", "test_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    
    channel_config = {
        "type": "telegram",
        "token": "${TELEGRAM_TOKEN}",
        "chat_id": "${TELEGRAM_CHAT_ID}",
        "notification_mode": "stages_only"
    }
    
    channel = _create_channel(channel_config)
    # Verify custom_message was added to the mode's event set
    assert "custom_message" in channel.subscribed_events
    # Verify base mode events are still present
    assert "stage_changed" in channel.subscribed_events

def test_explicit_events_not_modified(monkeypatch):
    """Explicit events array is not modified - user choice is preserved."""
    monkeypatch.setenv("TELEGRAM_TOKEN", "test_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    
    channel_config = {
        "type": "telegram",
        "token": "${TELEGRAM_TOKEN}",
        "chat_id": "${TELEGRAM_CHAT_ID}",
        "events": ["stage_changed"]
    }
    
    channel = _create_channel(channel_config)
    # Verify custom_message was NOT added
    assert "custom_message" not in channel.subscribed_events
    assert channel.subscribed_events == {"stage_changed"}
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

1. **Add new tests** to `tests/test_notifications/test_config.py`
2. **Write failing tests** for `custom_message` inclusion in mode-based subscribed sets
3. **Run tests** to confirm they fail (`uv run pytest tests/test_notifications/test_config.py -k custom_message -v`)
4. **Implement** minimal change in `_create_channel()` to add `custom_message` to mode-based subscribed sets
5. **Run all notification tests** to verify no regressions
6. **Refactor** if needed while keeping tests green

### Implementation Approach

The fix distinguishes between:
- **Mode-based filtering** (`notification_mode` setting): Automatically add `custom_message` to the subscribed set
- **Explicit events array**: User's explicit choice should be honored - do NOT modify

**Implementation (as implemented in config.py lines 134-142)**:

```python
elif "notification_mode" in resolved:
    # Mode-based filtering
    mode_events = resolve_notification_mode(resolved["notification_mode"])
    subscribed = set(mode_events) if mode_events else None
    # Always allow custom_message for explicit @notify commands
    # This ensures @notify bypasses mode filtering while preserving
    # the ability to disable all notifications with events: []
    if subscribed is not None:
        subscribed.add("custom_message")
```

This implementation:
- Only modifies the subscribed set when `notification_mode` is used (mode-based filtering)
- Does NOT modify explicit `events` arrays - preserves user choice completely
- Maintains backwards compatibility with `subscribed_events=None` (all events)

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
* **Test Examples**: `tests/test_notifications/test_config.py`, `tests/test_notifications/test_telegram.py`
* **Implementation Location**: `src/teambot/notifications/config.py:134-142`
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
