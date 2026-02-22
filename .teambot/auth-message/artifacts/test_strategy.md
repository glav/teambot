<!-- markdownlint-disable-file -->
# Test Strategy: Fix Authentication Command Message

**Strategy Date**: 2026-02-22
**Feature Specification**: .teambot/auth-message/artifacts/feature_spec.md
**Research Reference**: N/A (straightforward string replacement)
**Strategist**: Test Strategy Agent

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Answer | TDD Points | Code-First Points |
|--------|----------|--------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES - exact line numbers and strings specified | 3 | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | NO - pure string replacement | 0 | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | LOW - cosmetic user-facing strings | 0 | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO | 0 | 0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | YES - direct string replacement | 0 | 2 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | YES - quick fix needed | 0 | 2 |
| **Requirements Stability** | Are requirements likely to change during development? | NO - stable (copilot login command is fixed) | 0 | 0 |

### Score Summary

| Approach | Score |
|----------|-------|
| **TDD** | 3 |
| **Code-First** | 4 |

### Decision

**TDD Score: 3** (below threshold of 6)
**Code-First Score: 4** (meets threshold of 4)

**Decision: CODE-FIRST** (score 4 meets Code-First threshold)

## Recommended Testing Approach

**Primary Approach**: CODE_FIRST

### Rationale

This is a straightforward string replacement task with no algorithmic complexity. The existing tests already validate the error message content—they just assert the *wrong* string (`copilot auth` instead of `copilot login`). The most efficient approach is to update the source strings first, then update the test assertions to match.

TDD would be overkill for this change because: (1) the tests already exist and validate the message structure, (2) there is zero business logic to design, and (3) the change is purely cosmetic with no risk of introducing bugs.

**Key Factors:**
* Complexity: **LOW** — Simple string replacement in 5 source locations
* Risk: **LOW** — User-facing strings with no functional impact
* Requirements Clarity: **CLEAR** — Exact file/line locations documented
* Time Pressure: **MODERATE** — Users currently seeing incorrect guidance

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: None — no logic changes
* **Integration Depth**: Standalone — string literals in a single file
* **State Management**: None — stateless string changes
* **Error Scenarios**: Existing — tests already cover error message display

### Risk Profile
* **Business Criticality**: LOW — cosmetic fix
* **User Impact**: Positive — improves first-run experience
* **Data Sensitivity**: None — no data handling
* **Failure Cost**: Minimal — test failures would catch regressions immediately

### Requirements Clarity
* **Specification Completeness**: COMPLETE — all 17 occurrences mapped
* **Acceptance Criteria Quality**: PRECISE — exact strings and locations
* **Edge Cases Identified**: 0 — no edge cases for string replacement
* **Dependencies Status**: STABLE — Copilot CLI `login` command is documented

## Test Strategy by Component

### Source Code (`src/teambot/cli.py`) - CODE_FIRST

**Approach**: Code-First
**Rationale**: Direct string replacement with existing test coverage. Tests already validate message content structure.

**Test Requirements:**
* Coverage Target: 100% (all 5 occurrences)
* Test Types: Unit tests (existing)
* Critical Scenarios:
  * `teambot run` unauthenticated message (lines 139, 144)
  * `teambot init` unauthenticated message (lines 108, 114)
  * Copilot CLI installation warning (line 239)
* Edge Cases:
  * None — simple string replacement

**Testing Sequence** (Code-First):
1. Update all 5 string literals in `cli.py`
2. Run existing tests — they will FAIL (expected)
3. Update test assertions to verify `copilot login`
4. Run tests — they will PASS
5. Validate via grep that no `copilot auth` remains in scope

### Test Files - ASSERTION UPDATES ONLY

**Approach**: Code-First (assertion updates)
**Rationale**: Tests already validate correct behavior; only assertions need to change to match new strings.

**Test Requirements:**
* Coverage Target: 100% (all 9 assertions)
* Test Types: Unit + Acceptance
* Files to Update:
  * `tests/test_cli.py` (2 assertions)
  * `tests/test_acceptance_validation.py` (3 assertions + 1 docstring)
  * `tests/test_init_model_config_acceptance.py` (2 assertions)
  * `tests/test_model_cache_auto_acceptance.py` (1 assertion)

### Documentation - NO TESTS REQUIRED

**Approach**: Manual verification
**Rationale**: Documentation changes are validated via manual review (AT-004), not automated tests.

**Files to Update:**
* `README.md` (line 17)
* `docs/guides/installation.md` (lines 17, 227)

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest (with pytest-cov, pytest-mock)
* **Version**: Per pyproject.toml
* **Configuration**: `pyproject.toml [tool.pytest.ini_options]`
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: unittest.mock (AsyncMock, patch) - already in use
* **Assertions**: pytest standard assertions - `assert "string" in output`
* **Coverage**: pytest-cov - Target: 80%+ (existing baseline)
* **Test Data**: None required - tests use capsys for output capture

### Test Organization
* **Test Location**: `tests/`
* **Naming Convention**: `test_*.py` with `Test*` classes
* **Fixture Strategy**: `conftest.py` shared fixtures
* **Setup/Teardown**: pytest fixtures with `tmp_path`, `monkeypatch`

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: Maintain existing 80%+ baseline
* **Integration Coverage**: N/A for this change
* **Critical Path Coverage**: 100% — all auth error messages
* **Error Path Coverage**: Existing tests already cover error paths

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `cli.py` auth messages | 100% | N/A | CRITICAL | All 5 occurrences must be tested |
| Test assertions | 100% | N/A | CRITICAL | All 9 assertions must be updated |
| Documentation | N/A | N/A | HIGH | Manual verification |

### Critical Test Scenarios

Priority test scenarios that MUST pass:

1. **AT-002: Unauthenticated User Blocks with Guidance** (Priority: CRITICAL)
   * **Description**: `teambot run` shows `copilot login` when unauthenticated
   * **Test Type**: Unit (TestRunAuthCheck in test_cli.py)
   * **Success Criteria**: Output contains `copilot login`, NOT `copilot auth`
   * **Test Approach**: Code-First (update assertion)

2. **AT-002: Init Auth Guidance** (Priority: CRITICAL)
   * **Description**: `teambot init` shows `copilot login` guidance
   * **Test Type**: Unit (test_init_model_config_acceptance.py)
   * **Success Criteria**: Output contains `copilot login`
   * **Test Approach**: Code-First (update assertion)

3. **AT-003: Test Suite Passes** (Priority: CRITICAL)
   * **Description**: All tests pass after changes
   * **Test Type**: Full suite
   * **Success Criteria**: `uv run pytest` returns 0 failures
   * **Test Approach**: Post-implementation validation

### Edge Cases to Cover

* None — string replacement has no edge cases

### Error Scenarios

* **Authentication failure display**: Already tested via existing tests; assertions just need updating

## Test Data Strategy

### Test Data Requirements
* None — tests use mocked Copilot CLI responses

### Test Data Management
* **Storage**: Inline in test methods
* **Generation**: Hardcoded mock return values
* **Isolation**: Each test uses fresh `tmp_path`
* **Cleanup**: pytest handles via fixtures

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_cli.py:600-609`
**Pattern**: Mock async function, call sync wrapper, assert output contains string

```python
def test_auth_check_blocking_returns_false_when_not_authenticated(self, capsys):
    """Blocking auth check returns False when not authenticated."""
    from unittest.mock import AsyncMock, patch

    from teambot.cli import _check_copilot_authentication_blocking
    from teambot.visualization.console import ConsoleDisplay

    with patch(
        "teambot.cli._check_auth_async", AsyncMock(return_value=(False, "Not authenticated"))
    ):
        display = ConsoleDisplay()
        result = _check_copilot_authentication_blocking(display)

    assert result is False
    captured = capsys.readouterr()
    assert "not authenticated" in captured.out.lower()
    assert "copilot login" in captured.out.lower()  # <-- UPDATE THIS LINE
```

**Key Conventions:**
* Use `capsys` fixture to capture stdout
* Assert on `captured.out.lower()` for case-insensitive matching
* Use `unittest.mock.patch` as context manager

### Recommended Test Structure

No new tests required. Update existing assertions:

```python
# BEFORE:
assert "copilot auth" in captured.out.lower()

# AFTER:
assert "copilot login" in captured.out.lower()
```

## Success Criteria

### Test Implementation Complete When:
* [x] All critical scenarios have tests (already exist)
* [ ] All 5 source strings updated to `copilot login`
* [ ] All 9 test assertions updated to `copilot login`
* [ ] `uv run pytest` passes with 0 failures
* [ ] `grep -r "copilot auth" src/ tests/` returns no matches in scope
* [ ] Documentation updated and manually verified

### Test Quality Indicators:
* Tests remain readable and self-documenting
* Tests are fast and reliable (no changes to test logic)
* Tests are independent (no new dependencies)
* Failures clearly indicate the problem (string mismatch)
* Mock/stub usage is unchanged

## Implementation Guidance

### For Code-First Components (ALL):
1. Update all 5 strings in `src/teambot/cli.py`
2. Run `uv run pytest` — expect failures in 9 tests
3. Update assertions in 4 test files
4. Run `uv run pytest` — all should pass
5. Run `uv run ruff check .` and `uv run ruff format .`
6. Update documentation files (README.md, installation.md)
7. Manual verification of documentation
8. Run `grep -r "copilot auth" src/ tests/` to verify no scope misses

## Considerations and Trade-offs

### Selected Approach Benefits:
* Fastest path to completion (no test infrastructure setup)
* Leverages existing test coverage
* Minimal risk of introducing new bugs

### Accepted Trade-offs:
* No TDD "test-first" discipline (not needed for string changes)
* Tests will temporarily fail during implementation window

### Risk Mitigation:
* Existing tests catch any typos or incomplete updates immediately
* Grep verification ensures no occurrences are missed

## References

* **Feature Spec**: [.teambot/auth-message/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/auth-message/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: `tests/test_cli.py`, `tests/test_acceptance_validation.py`
* **Test Standards**: `pyproject.toml [tool.pytest.ini_options]`

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow Code-First approach for all components

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

## Approval Request

I've analyzed **Fix Authentication Command Message** and recommend **CODE-FIRST**.

**Do you:**
1. ✅ Approve this strategy and proceed to planning
2. 🔄 Want to adjust the approach (please specify)
3. ❓ Have questions or concerns about the recommendation
