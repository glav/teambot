<!-- markdownlint-disable-file -->
# Test Strategy: Notification Frequency Control

**Strategy Date**: 2026-02-17
**Feature Specification**: .teambot/notification-frequency-control/artifacts/feature_spec.md
**Specification Review**: .teambot/notification-frequency-control/artifacts/spec_review.md
**Strategist**: Builder-2 (Test Strategy Agent)

## Testing Approach Decision Matrix

### Factor Scoring

| Factor | Question | Assessment | TDD Points | Code-First Points |
|--------|----------|------------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES - 7 concrete acceptance tests in spec, precise mode-to-events mapping | 3 | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM - Precedence logic, validation, mode expansion | 2 | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | MEDIUM - Backwards compatibility critical but well-defined | 2 | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO - Clear requirements, known patterns | 0 | 0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | PARTIAL - Some components simple (constant lookup), others need validation | 0 | 1 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO - Quality and backwards compatibility are priorities | 0 | 0 |
| **Requirements Stability** | Are requirements likely to change during development? | NO - Spec is approved and stable | 0 | 0 |

### Decision Calculation

```
TDD Score: 3 + 2 + 2 + 0 + 0 + 0 + 0 = 7
Code-First Score: 0 + 0 + 0 + 0 + 1 + 0 + 0 = 1

Decision: TDD (score 7 ≥ threshold 6)
```

## Recommended Testing Approach

**Primary Approach**: **TDD** (Test-Driven Development)

### Rationale

The Notification Frequency Control feature is an excellent candidate for TDD because it has **well-defined acceptance criteria** (7 concrete test scenarios in the spec), **clear input-output mappings** (mode names → event sets), and **critical backwards compatibility requirements** that must be validated before implementation.

The feature involves **configuration parsing and validation** with specific precedence rules (`events` > `notification_mode` > default `all`), which are ideally suited for test-first development. Writing tests first will ensure the precedence logic is correct from the start and prevent regressions in existing notification behavior.

Additionally, the implementation is **isolated to two files** (`config.py` and `cli.py`) with minimal integration complexity, making test-first development efficient and low-risk.

**Key Factors:**
* Complexity: **MEDIUM** — Precedence logic and validation require careful testing
* Risk: **MEDIUM** — Backwards compatibility is critical; existing configs must work unchanged
* Requirements Clarity: **CLEAR** — 7 acceptance scenarios, explicit mode-to-events mapping
* Time Pressure: **LOW** — Quality and compatibility prioritized over speed

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Low — Simple dictionary lookups and set operations
* **Integration Depth**: Low — Changes isolated to `config.py` and `cli.py`; no channel infrastructure changes
* **State Management**: None — Stateless configuration expansion
* **Error Scenarios**: Medium — Invalid mode validation, missing config fields, precedence edge cases

### Risk Profile
* **Business Criticality**: MEDIUM — Notifications are a v0.2.0 feature; backwards compatibility is essential
* **User Impact**: Medium — Affects all users with notifications enabled
* **Data Sensitivity**: Low — Configuration values only, no secrets involved in new logic
* **Failure Cost**: Medium — Breaking existing configs would cause user friction

### Requirements Clarity
* **Specification Completeness**: COMPLETE — 100% progress on all spec sections
* **Acceptance Criteria Quality**: PRECISE — 7 executable test scenarios with explicit verification steps
* **Edge Cases Identified**: 4 documented (precedence, defaults, validation, per-channel)
* **Dependencies Status**: STABLE — Uses existing `subscribed_events` infrastructure unchanged

## Test Strategy by Component

### Component 1: NOTIFICATION_MODES Constant — TDD

**Approach**: TDD
**Rationale**: The mode-to-events mapping is the foundation of the feature. Tests first will define the expected behavior and serve as documentation.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `stages_only` maps to exactly 3 events: `stage_changed`, `orchestration_started`, `orchestration_completed`
  * `agent_status` maps to 6 events: stages_only events + `agent_running`, `agent_complete`, `agent_failed`
  * `all` maps to `None` (no filtering)
  * Constant is immutable/not mutated during use
* Edge Cases:
  * Verify no typos in event names (match `MessageTemplates.TEMPLATES` keys)
  * Verify `agent_status` is a strict superset of `stages_only`

**Testing Sequence** (TDD):
1. Write test asserting `NOTIFICATION_MODES` exists and has 3 keys
2. Write tests asserting each mode's event set
3. Implement `NOTIFICATION_MODES` constant
4. Write test asserting superset relationship
5. Refactor if needed

### Component 2: Mode Expansion Logic — TDD

**Approach**: TDD
**Rationale**: The `_expand_notification_mode()` function and its integration into `_create_channel()` have specific precedence rules that must be tested first.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * `notification_mode: "stages_only"` → `subscribed_events` = stages_only set
  * `notification_mode: "agent_status"` → `subscribed_events` = agent_status set
  * `notification_mode: "all"` → `subscribed_events` = `None` (all events)
  * `events` array takes precedence over `notification_mode`
  * Neither specified → defaults to `None` (all events)
  * Both specified → `events` wins (AT-NFC-003)
* Edge Cases:
  * Empty `events` array with `notification_mode` set
  * `notification_mode` with empty string
  * Case sensitivity of mode names

**Testing Sequence** (TDD):
1. Write test for valid mode expansion (each mode)
2. Write test for invalid mode raising `ValueError`
3. Write test for `events` precedence over `notification_mode`
4. Write test for default behavior (neither specified)
5. Implement `_expand_notification_mode()` helper
6. Integrate into `_create_channel()`
7. Run all tests, refactor

### Component 3: Mode Validation — TDD

**Approach**: TDD
**Rationale**: Error messages must be clear and actionable (NFR-NFC-003). Test first ensures the error format is correct.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Invalid mode `"invalid"` raises `ValueError`
  * Error message lists all valid modes (`stages_only`, `agent_status`, `all`)
  * Error message includes the invalid value for debugging
* Edge Cases:
  * Mode value is `None` type
  * Mode value is integer instead of string
  * Mode value is empty string `""`

**Testing Sequence** (TDD):
1. Write test for `ValueError` on invalid mode
2. Write test asserting error message content
3. Implement validation in `_expand_notification_mode()`
4. Refactor error message format if needed

### Component 4: Init Wizard Mode Selection — Code-First

**Approach**: Code-First
**Rationale**: The init wizard is interactive CLI code that requires UI integration. It's lower risk and easier to implement first, then add integration tests.

**Test Requirements:**
* Coverage Target: 70%
* Test Types: Integration (CLI behavior)
* Critical Scenarios:
  * Mode selection prompt appears after channel configuration
  * User can select from 3 modes
  * Selected mode is written to `teambot.json` correctly
  * Default behavior when no selection made
* Edge Cases:
  * User cancels during mode selection
  * Init with `--force` includes mode selection

**Testing Sequence** (Code-First):
1. Implement mode selection step in init wizard
2. Add integration test for mode selection flow
3. Add test for generated config file content
4. Validate with manual testing

### Component 5: Backwards Compatibility — TDD

**Approach**: TDD
**Rationale**: Existing configurations must work unchanged. Tests first guarantee no regressions.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit + Integration
* Critical Scenarios:
  * Config with `events: [...]` only → behavior unchanged
  * Config with no `events` or `notification_mode` → all events (current default)
  * Existing test suite passes without modification
* Edge Cases:
  * Old config format from v0.2.0

**Testing Sequence** (TDD):
1. Write test for existing `events`-only config behavior
2. Write test for no-filter default behavior
3. Verify existing tests pass
4. Implement changes
5. Re-run all existing notification tests

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest
* **Version**: >=7.4.0
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (MagicMock, AsyncMock, patch)
* **Assertions**: Built-in pytest assertions
* **Coverage**: pytest-cov — Target: 90% for new code
* **Test Data**: In-line config fixtures matching production schema
* **Async Testing**: pytest-asyncio (asyncio_mode = "auto")

### Test Organization
* **Test Location**: `tests/test_notifications/` (existing directory)
* **Naming Convention**: `test_*.py` files, `Test*` classes, `test_*` functions
* **Fixture Strategy**: `conftest.py` for shared fixtures, class-level fixtures where needed
* **Setup/Teardown**: pytest fixtures with `monkeypatch` for env vars

### New Test Files Required
* `tests/test_notifications/test_config.py` — **Extend existing file** with new tests
* No new test files needed — all tests fit in existing structure

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% (minimum) for new code
* **Integration Coverage**: 80% for init wizard changes
* **Critical Path Coverage**: 100% for mode expansion and precedence logic
* **Error Path Coverage**: 100% for validation errors

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `NOTIFICATION_MODES` constant | 100% | — | CRITICAL | Foundation of feature |
| `_expand_notification_mode()` | 100% | — | CRITICAL | Core logic |
| `_create_channel()` integration | 95% | — | CRITICAL | Precedence logic |
| Mode validation | 100% | — | HIGH | Error message quality |
| Init wizard mode step | 60% | 80% | MEDIUM | UI/interactive |
| Backwards compatibility | 100% | 100% | CRITICAL | Non-negotiable |

### Critical Test Scenarios (from AT-NFC-* in spec)

1. **AT-NFC-001: Stages Only Mode Filters Correctly** (Priority: CRITICAL)
   * **Description**: `stages_only` mode filters to exactly 3 events
   * **Test Type**: Unit
   * **Success Criteria**: `supports_event()` returns `True` only for `stage_changed`, `orchestration_started`, `orchestration_completed`
   * **Test Approach**: TDD

2. **AT-NFC-002: Agent Status Mode Includes Agent Events** (Priority: CRITICAL)
   * **Description**: `agent_status` mode includes 6 events (stages + agent lifecycle)
   * **Test Type**: Unit
   * **Success Criteria**: `supports_event()` returns `True` for all 6 events
   * **Test Approach**: TDD

3. **AT-NFC-003: Events Array Overrides Mode** (Priority: CRITICAL)
   * **Description**: Explicit `events` takes precedence over `notification_mode`
   * **Test Type**: Unit
   * **Success Criteria**: Channel uses `events` array when both specified
   * **Test Approach**: TDD

4. **AT-NFC-004: Backwards Compatibility — No Mode Specified** (Priority: CRITICAL)
   * **Description**: No `notification_mode` or `events` → all events received
   * **Test Type**: Unit
   * **Success Criteria**: `subscribed_events` is `None` (no filtering)
   * **Test Approach**: TDD

5. **AT-NFC-005: Invalid Mode Produces Clear Error** (Priority: HIGH)
   * **Description**: Invalid mode value raises actionable `ValueError`
   * **Test Type**: Unit
   * **Success Criteria**: Error message lists valid modes
   * **Test Approach**: TDD

6. **AT-NFC-006: Init Wizard Mode Selection** (Priority: MEDIUM)
   * **Description**: `teambot init` offers mode selection step
   * **Test Type**: Integration
   * **Success Criteria**: Generated config includes `notification_mode`
   * **Test Approach**: Code-First

7. **AT-NFC-007: Per-Channel Independent Modes** (Priority: HIGH)
   * **Description**: Different channels can have different modes
   * **Test Type**: Unit
   * **Success Criteria**: Two channels with different modes receive different events
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Empty events array with mode**: `{"events": [], "notification_mode": "all"}` → empty events wins (no notifications)
* **Mode case sensitivity**: `"STAGES_ONLY"` should be invalid (lowercase only)
* **Unknown event in events array**: Should pass through unchanged (existing behavior)
* **Multiple channels with mixed configs**: One with mode, one with events, one with neither

### Error Scenarios

* **Invalid mode value**: Must raise `ValueError` with helpful message
* **Non-string mode value**: Handle gracefully (type error or validation error)
* **Config loading failure**: Existing error handling should not be affected

## Test Data Strategy

### Test Data Requirements
* **Config dictionaries**: In-line Python dicts mimicking `teambot.json` structure
* **Environment variables**: Use `monkeypatch.setenv()` for token/chat_id mocking
* **Event types**: String literals matching `MessageTemplates.TEMPLATES` keys

### Test Data Management
* **Storage**: In-line in test functions, fixtures for reusable configs
* **Generation**: Manual — configs are small and well-defined
* **Isolation**: Each test uses fresh config dict; no shared mutable state
* **Cleanup**: `monkeypatch` auto-cleanup for env vars

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_notifications/test_config.py`
**Pattern**: Unit tests for config functions with monkeypatch env vars

```python
class TestCreateEventBusFromConfig:
    """Tests for create_event_bus_from_config function."""

    def test_applies_event_filter(self, monkeypatch) -> None:
        """Applies event filter from config."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "events": ["stage_changed"],
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_failed") is False
```

**Key Conventions:**
* Class-based test organization (`Test*` prefix)
* Descriptive docstrings
* Arrange-Act-Assert pattern
* Direct assertions (no assertion libraries)
* Use `monkeypatch` for environment variables

### Recommended Test Structure for New Tests

```python
class TestNotificationModeExpansion:
    """Tests for notification_mode expansion in config."""

    def test_stages_only_mode_expands_to_stage_events(self, monkeypatch) -> None:
        """notification_mode: 'stages_only' expands to stage event set."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "notification_mode": "stages_only",
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("orchestration_started") is True
        assert channel.supports_event("orchestration_completed") is True
        assert channel.supports_event("agent_running") is False
        assert channel.supports_event("agent_failed") is False

    def test_events_array_takes_precedence_over_mode(self, monkeypatch) -> None:
        """Explicit events array overrides notification_mode."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "notification_mode": "all",
                        "events": ["agent_failed"],
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        assert channel.supports_event("agent_failed") is True
        assert channel.supports_event("stage_changed") is False


class TestNotificationModeValidation:
    """Tests for notification_mode validation."""

    def test_invalid_mode_raises_value_error(self, monkeypatch) -> None:
        """Invalid notification_mode raises ValueError with valid modes listed."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "notification_mode": "invalid_mode",
                    }
                ],
            }
        }

        with pytest.raises(ValueError) as exc_info:
            create_event_bus_from_config(config)

        error_message = str(exc_info.value)
        assert "invalid_mode" in error_message
        assert "stages_only" in error_message
        assert "agent_status" in error_message
        assert "all" in error_message
```

## Success Criteria

### Test Implementation Complete When:
- [ ] All 7 acceptance test scenarios have corresponding tests
- [ ] Coverage targets met: 90% unit, 80% integration
- [ ] All edge cases tested (empty arrays, case sensitivity, type errors)
- [ ] Error paths validated with specific message assertions
- [ ] Tests follow codebase conventions (class-based, docstrings, AAA pattern)
- [ ] Tests are maintainable and self-documenting
- [ ] Existing notification tests still pass (no regressions)

### Test Quality Indicators:
* Tests are readable and explain the "why" in docstrings
* Tests are fast (no network calls, minimal async waits)
* Tests are reliable (no flakiness, deterministic assertions)
* Tests are independent (no test order dependencies, isolated fixtures)
* Failures clearly indicate the problem (specific assertions, good error messages)
* Mock/stub usage is minimal (only for TelegramChannel HTTP calls)

## Implementation Guidance

### For TDD Components (Mode Expansion, Validation, Backwards Compat):
1. Start with simplest test case (e.g., `stages_only` mode expansion)
2. Write minimal code to pass
3. Add next test case (e.g., `agent_status` mode)
4. Refactor when all tests pass
5. Focus on behavior, not implementation (test via `create_event_bus_from_config`, not internal helpers)

### For Code-First Components (Init Wizard):
1. Implement mode selection prompt in CLI
2. Add integration test verifying generated config
3. Identify edge cases from implementation
4. Add edge case tests
5. Verify coverage meets 70% target

### For Backwards Compatibility:
1. Run existing test suite first (`uv run pytest tests/test_notifications/`)
2. Implement changes
3. Re-run existing tests — must all pass
4. Add explicit backwards compatibility tests if any edge cases found

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures precedence logic is correct from the start
* Tests serve as living documentation of mode behavior
* High confidence in backwards compatibility before release
* Clear acceptance criteria make test writing straightforward

### Accepted Trade-offs:
* Slightly slower initial development (tests first)
* Init wizard testing is less comprehensive (interactive CLI is harder to test)
* Some tests may be verbose due to config dict boilerplate

### Risk Mitigation:
* **Backwards compatibility risk**: Mitigated by running existing tests first and writing explicit regression tests
* **Precedence logic bugs**: Mitigated by TDD with explicit test for each precedence case
* **Missing edge cases**: Mitigated by comprehensive edge case list in spec and strategy

## References

* **Feature Spec**: [.teambot/notification-frequency-control/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/notification-frequency-control/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: `tests/test_notifications/test_config.py`, `tests/test_notifications/test_event_bus.py`
* **Test Fixtures**: `tests/test_notifications/conftest.py`
* **Implementation Target**: `src/teambot/notifications/config.py`

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow TDD for core logic, Code-First for init wizard

---

**Strategy Status**: APPROVED
**Approved By**: PENDING USER REVIEW
**Ready for Planning**: YES

---

## Output Validation

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE (TDD Score: 7, Code-First Score: 1)
- Approach: TDD (with Code-First for init wizard)
- Coverage Targets: SPECIFIED (90% unit, 80% integration, 100% critical paths)
- Components Covered: 5/5
```
