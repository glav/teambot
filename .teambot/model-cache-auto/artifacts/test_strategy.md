<!-- markdownlint-disable-file -->
# Test Strategy: Model Cache Auto-Setup and Login Validation

**Strategy Date**: 2026-02-19
**Feature Specification**: .teambot/model-cache-auto/artifacts/feature_spec.md
**Research Reference**: N/A (leveraging existing code patterns)
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: TDD (Test-Driven Development)

### Rationale

This feature involves critical startup flow modifications to `cmd_run()` that must not break existing behavior. The requirements are well-defined with 5 explicit acceptance test scenarios in the specification. TDD is optimal because:

1. **Requirements are crystal clear**: The spec includes precise acceptance criteria (AT-001 through AT-005) with specific expected outputs and exit codes
2. **High risk of regression**: Changes to `cmd_run()` flow could break existing users - tests must be written first to capture current behavior
3. **Existing patterns to follow**: The `cmd_init()` flow already uses `_check_copilot_authentication()` and `_refresh_model_cache()` with well-tested patterns

**Key Factors:**
* Complexity: MEDIUM (orchestration of existing functions in new flow)
* Risk: HIGH (startup flow changes affect all users)
* Requirements Clarity: CLEAR (5 detailed acceptance scenarios)
* Time Pressure: LOW (quality is priority)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Assessment | TDD Points | Code-First Points |
|--------|----------|------------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES - 5 AT scenarios with precise criteria | 3 | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM - flow orchestration, not algorithm | 2 | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | HIGH - affects all `teambot run` users | 3 | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO - well-defined integration | 0 | 0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | NO - conditional flow with multiple paths | 0 | 0 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO - quality is priority | 0 | 0 |
| **Requirements Stability** | Are requirements likely to change during development? | STABLE - spec approved | 0 | 0 |

### Score Summary

| Score Type | Points |
|------------|--------|
| **TDD Score** | **8** |
| **Code-First Score** | **0** |

### Decision Thresholds

| TDD Score | Code-First Score | Recommendation |
|-----------|------------------|----------------|
| ≥ 6 | < 4 | **TDD** |

**Decision**: TDD (score 8 >> threshold 6)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: LOW - No complex algorithms; orchestration of existing functions
* **Integration Depth**: MEDIUM - Integrates auth check and cache refresh into `cmd_run()` flow
* **State Management**: LOW - Stateless checks with simple boolean returns
* **Error Scenarios**: MEDIUM - Auth failure, network failure, cache states

### Risk Profile
* **Business Criticality**: HIGH - First-run user experience
* **User Impact**: HIGH - All users running `teambot run` for first time
* **Data Sensitivity**: LOW - No sensitive data; only model cache
* **Failure Cost**: MEDIUM - Confusing errors, not data loss

### Requirements Clarity
* **Specification Completeness**: COMPLETE - All 8 FRs documented
* **Acceptance Criteria Quality**: PRECISE - 5 detailed AT scenarios
* **Edge Cases Identified**: 5 documented (missing cache, empty cache, network failure, auth failure, valid cache)
* **Dependencies Status**: STABLE - Reuses existing tested functions

## Test Strategy by Component

### Component 1: Authentication Check Flow - TDD

**Approach**: TDD
**Rationale**: Auth check is a critical gate that must work correctly before any workflow execution. Well-defined success/failure behaviors with clear acceptance criteria.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit, Integration
* Critical Scenarios:
  * Authenticated user passes check silently
  * Unauthenticated user receives clear error with "copilot auth" guidance
  * Auth check failure stops execution with exit code 1
  * Auth check timeout doesn't block indefinitely (< 5s)
* Edge Cases:
  * SDK not available
  * Network timeout during auth check
  * Exception handling during auth verification

**Testing Sequence (TDD)**:
1. Write test for auth check success returning True
2. Write test for auth check failure returning False with guidance message
3. Write test for `cmd_run()` calling auth check before config load
4. Write test for `cmd_run()` exiting with code 1 on auth failure
5. Implement minimal code to pass each test
6. Refactor for quality

### Component 2: Cache Missing Detection - TDD

**Approach**: TDD
**Rationale**: Cache detection logic must correctly identify missing vs empty vs valid cache states. Clear testable states.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Cache file doesn't exist → detected as missing
  * Cache file exists but empty (`{}`) → detected as missing
  * Cache file exists with models → detected as valid
* Edge Cases:
  * Corrupted JSON in cache file
  * Empty models array `{"models": []}`

**Testing Sequence (TDD)**:
1. Write test for `_is_cache_missing()` returning True when file doesn't exist
2. Write test for `_is_cache_missing()` returning True when cache is empty
3. Write test for `_is_cache_missing()` returning False when cache is valid
4. Implement minimal code to pass
5. Integrate into `cmd_run()` flow

### Component 3: Auto Cache Refresh Flow - TDD

**Approach**: TDD
**Rationale**: Auto-refresh is the key feature enabling seamless first-run. Must show user feedback and handle failures gracefully.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit, Integration
* Critical Scenarios:
  * Missing cache triggers refresh
  * Refresh displays "Refreshing model cache..." message
  * Successful refresh continues to workflow execution
  * Failed refresh shows clear error with guidance
  * Failed refresh exits with code 1
* Edge Cases:
  * Network failure during refresh
  * SDK returns empty model list
  * Timeout during refresh

**Testing Sequence (TDD)**:
1. Write test for refresh displaying status message
2. Write test for successful refresh allowing workflow to continue
3. Write test for failed refresh showing error guidance
4. Write test for failed refresh returning exit code 1
5. Implement minimal code to pass each test

### Component 4: No-Op When Cache Valid - TDD

**Approach**: TDD
**Rationale**: Must ensure existing users see zero performance degradation. Critical for backward compatibility.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit, Integration
* Critical Scenarios:
  * Valid cache skips auth display and refresh
  * No "Refreshing model cache..." output when cache valid
  * Startup time unchanged when cache exists
* Edge Cases:
  * Cache just created (0 seconds old)
  * Cache at TTL boundary (23 hours 59 minutes)

**Testing Sequence (TDD)**:
1. Write test verifying no refresh message when cache valid
2. Write test verifying normal workflow execution with valid cache
3. Implement conditional bypass logic

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest
* **Version**: >=7.4.0
* **Configuration**: pyproject.toml `[tool.pytest.ini_options]`
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (AsyncMock, patch) - Mock async SDK calls
* **Assertions**: pytest built-in assertions
* **Coverage**: pytest-cov - Target: 80%+ overall, 90%+ for new code
* **Test Data**: Fixtures in conftest.py, tmp_path for cache files

### Test Organization
* **Test Location**: `tests/`
* **Naming Convention**: `test_*.py`, functions `test_*`
* **Fixture Strategy**: `conftest.py` shared fixtures, class fixtures for test groups
* **Setup/Teardown**: pytest fixtures with `tmp_path`, `monkeypatch`

### Async Testing
* **Mode**: `asyncio_mode = "auto"` (from pyproject.toml)
* **Mocking**: `AsyncMock` for SDK calls
* **Pattern**: Mock `_check_auth_async` and `_refresh_model_cache_async`

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% (minimum for new code)
* **Integration Coverage**: 80%
* **Critical Path Coverage**: 100%
* **Error Path Coverage**: 90%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| Auth Check in cmd_run | 95% | 90% | CRITICAL | Must not break existing flow |
| Cache Missing Detection | 90% | 80% | HIGH | Multiple state conditions |
| Auto Cache Refresh | 90% | 85% | CRITICAL | Key user experience |
| No-Op Valid Cache | 90% | 80% | HIGH | Backward compatibility |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **AT-001: First Run After Installation** (Priority: CRITICAL)
   * **Description**: User with auth but no cache runs `teambot run`, cache auto-refreshes
   * **Test Type**: Integration
   * **Success Criteria**: Exit code 0, "Refreshing model cache..." displayed, workflow starts
   * **Test Approach**: TDD

2. **AT-002: Unauthenticated User** (Priority: CRITICAL)
   * **Description**: User without auth runs `teambot run`, receives clear error
   * **Test Type**: Integration
   * **Success Criteria**: Exit code 1, message contains "copilot auth"
   * **Test Approach**: TDD

3. **AT-003: Network Failure During Cache Refresh** (Priority: HIGH)
   * **Description**: Cache refresh fails due to network, user sees guidance
   * **Test Type**: Integration
   * **Success Criteria**: Exit code 1, message suggests network check
   * **Test Approach**: TDD

4. **AT-004: Returning User With Valid Cache** (Priority: HIGH)
   * **Description**: User with valid cache sees no delay or refresh messages
   * **Test Type**: Integration
   * **Success Criteria**: Exit code 0, no "Refreshing" output, normal startup
   * **Test Approach**: TDD

5. **AT-005: Cache Exists But Empty** (Priority: MEDIUM)
   * **Description**: Empty cache treated same as missing cache
   * **Test Type**: Unit + Integration
   * **Success Criteria**: Exit code 0 after refresh, cache populated
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Empty models array**: `{"models": []}` should trigger refresh
* **Corrupted cache JSON**: Should be treated as missing, trigger refresh
* **SDK not available**: Clear error about Copilot SDK
* **Auth check timeout**: Should fail gracefully within 5 seconds
* **Refresh timeout**: Should fail with network guidance

### Error Scenarios

* **Auth not available**: Exit code 1, message: "Run 'copilot auth' first"
* **Network failure**: Exit code 1, message: "Check network connection and try again"
* **SDK exception**: Exit code 1, logged at debug level, user sees actionable guidance
* **Cache write failure**: Proceed with warning, don't block workflow

## Test Data Strategy

### Test Data Requirements
* **Cache files**: Generated via fixtures in `tmp_path`
* **Config files**: Created via `create_default_config()` or manual JSON
* **Auth states**: Mocked via `AsyncMock` return values

### Test Data Management
* **Storage**: `tmp_path` pytest fixture (auto-cleanup)
* **Generation**: Programmatic fixture creation
* **Isolation**: Each test uses fresh `tmp_path`
* **Cleanup**: Automatic via pytest fixtures

## Example Test Patterns

### Example from Codebase

**File**: tests/test_init_model_config_acceptance.py
**Pattern**: Acceptance test with mocked async operations

```python
def test_at_001_init_creates_config_with_correct_model(self, tmp_path, monkeypatch):
    """AT-001: Running init creates teambot.json with correct default model."""
    from teambot.cli import ConsoleDisplay, cmd_init

    monkeypatch.chdir(tmp_path)

    # Mock async operations to avoid network calls
    with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
        with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
            args = argparse.Namespace(force=False, no_animation=True)
            display = ConsoleDisplay()

            # Call REAL cmd_init
            result = cmd_init(args, display)

    # Verify init succeeded
    assert result == 0
```

**Key Conventions:**
* Mock async SDK operations with `AsyncMock`
* Use `tmp_path` and `monkeypatch.chdir()` for isolation
* Call REAL implementations, only mock external dependencies
* Use `capsys` to capture console output for verification

### Recommended Test Structure

```python
"""Acceptance tests for Model Cache Auto-Setup and Login Validation.

Core logic is tested directly; selective mocking is used for external dependencies.
"""

import argparse
from unittest.mock import AsyncMock, patch

import pytest


class TestModelCacheAutoSetupAcceptance:
    """Acceptance test scenarios for model cache auto-setup."""

    # =========================================================================
    # AT-001: First Run After Installation (Happy Path)
    # =========================================================================

    def test_at_001_missing_cache_triggers_refresh(self, tmp_path, monkeypatch, capsys):
        """AT-001: Missing cache triggers auto-refresh during teambot run."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)
        # Setup: create config but no cache
        # ...
        
        # Mock auth success, refresh success
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(config="teambot.json", objective=None)
                display = ConsoleDisplay()
                
                result = cmd_run(args, display)

        # Verify refresh message displayed
        captured = capsys.readouterr()
        assert "Refreshing model cache" in captured.out
        assert result == 0

    # =========================================================================
    # AT-002: Unauthenticated User
    # =========================================================================

    def test_at_002_unauthenticated_stops_with_clear_error(self, tmp_path, monkeypatch, capsys):
        """AT-002: Unauthenticated user gets clear error with guidance."""
        # ...
```

## Success Criteria

### Test Implementation Complete When:
* [ ] All 5 acceptance test scenarios have tests
* [ ] Coverage targets are met per component (90%+ unit)
* [ ] All edge cases are tested
* [ ] Error paths are validated
* [ ] Tests follow existing `tests/test_cli.py` conventions
* [ ] Tests are maintainable and clear
* [ ] CI passes (ruff check, ruff format, pytest)

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast and reliable (no flakiness from async)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem
* Mock/stub usage is appropriate and minimal (only mock async SDK)

## Implementation Guidance

### For TDD Components:
1. Start with simplest test case (AT-004: valid cache no-op)
2. Write test for auth check integration
3. Write test for cache missing detection
4. Write tests for auto-refresh flow
5. Write tests for error scenarios
6. Implement minimal code to pass each test
7. Refactor when all tests pass
8. Focus on behavior, not implementation

### Recommended Test Order:
1. **Unit tests for cache detection** (easiest, foundation)
2. **Unit tests for auth check integration** (existing function)
3. **Integration tests for AT-004** (valid cache - establishes baseline)
4. **Integration tests for AT-001** (happy path auto-refresh)
5. **Integration tests for AT-002** (auth failure)
6. **Integration tests for AT-003** (network failure)
7. **Integration tests for AT-005** (empty cache)

### Test File Organization:
```
tests/
├── test_cli.py                               # Add unit tests for new functions
├── test_model_cache_auto_acceptance.py       # NEW: Acceptance tests AT-001 to AT-005
└── test_config/
    └── test_model_cache.py                   # Add cache missing detection tests
```

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures no regression in `cmd_run()` behavior
* Tests document expected behavior for future maintenance
* High coverage provides confidence for refactoring
* Acceptance tests directly validate spec requirements

### Accepted Trade-offs:
* Slightly slower initial development (tests first)
* Need to mock async SDK operations (adds test complexity)
* More test code to maintain

### Risk Mitigation:
* Test patterns from `test_init_model_config_acceptance.py` reduce learning curve
* Existing fixtures (conftest.py) provide reusable mocking infrastructure
* TDD catches integration issues early

## References

* **Feature Spec**: [.teambot/model-cache-auto/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/model-cache-auto/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: tests/test_init_model_config_acceptance.py, tests/test_cli.py
* **Model Cache Tests**: tests/test_config/test_model_cache.py

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow TDD approach per component

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

## Output Validation

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE
- Approach: TDD (score 8 vs threshold 6)
- Coverage Targets: SPECIFIED (90% unit, 80% integration)
- Components Covered: 4/4
```
