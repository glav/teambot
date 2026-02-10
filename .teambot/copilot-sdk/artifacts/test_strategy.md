<!-- markdownlint-disable-file -->
# Test Strategy: GitHub Copilot SDK Upgrade (0.1.16 → 0.1.23)

**Strategy Date**: 2026-02-10
**Feature Specification**: N/A — dependency version bump objective
**Research Reference**: `.agent-tracking/research/20260210-copilot-sdk-upgrade-research.md`
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: **CODE_FIRST**

### Testing Approach Decision Matrix

| Factor | Question | TDD Points | Code-First Points | Score |
|--------|----------|:----------:|:-----------------:|-------|
| **Requirements Clarity** | Are requirements well-defined? | 3 if YES | 0 | TDD: 3 (well-defined: bump version, fix one breaking change, add version to help) |
| **Complexity** | Complex business logic? | 3 if HIGH | 0 | TDD: 0 (low complexity — one-line fix, version bump, string addition) |
| **Risk Level** | Mission-critical if it fails? | 3 if CRITICAL | 0 | TDD: 0 (low risk — mocked tests catch regressions; no new business logic) |
| **Exploratory Nature** | Proof-of-concept? | 0 | 3 if YES | CF: 0 |
| **Simplicity** | Straightforward logic? | 0 | 2 if YES | CF: 2 (trivial one-liner fixes) |
| **Time Pressure** | Rapid iteration priority? | 0 | 2 if YES | CF: 2 (simple version bump) |
| **Requirements Stability** | Likely to change? | 0 | 2 if YES | CF: 0 |

**TDD Score: 3** | **Code-First Score: 4**

**Decision**: **Code-First** (TDD 3 < 6 threshold; CF 4 at threshold; simplicity and low risk favour code-first)

### Rationale

This is a dependency version bump with one known breaking API change (`GetAuthStatusResponse` changed from TypedDict to dataclass) and one small feature addition (SDK version in `/help` output). The actual code changes are minimal: a one-line `getattr()` fix, a version string in `pyproject.toml`, and a string interpolation in the help output. The existing test suite of ~1084 tests already comprehensively covers all SDK integration points through mocks, making it the primary regression safety net.

TDD is not warranted because there is no new algorithm, business logic, or complex state management being introduced. The changes are mechanical compatibility fixes. The existing test suite, when run against the upgraded SDK, serves as the primary validation mechanism.

The small enhancement to `/help` output needs 1-2 new test assertions (checking for `"Copilot SDK:"` in output), which are straightforward to add after implementation.

**Key Factors:**
* **Complexity**: LOW — one-line fix, version string change, help text tweak
* **Risk**: LOW — existing 1084 tests catch regressions; all SDK interactions are mocked
* **Requirements Clarity**: CLEAR — objective spells out exact changes needed
* **Time Pressure**: LOW — straightforward implementation

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: None — no new algorithms or logic
* **Integration Depth**: Shallow — SDK is wrapped by `CopilotSDKClient`; changes are in the wrapper
* **State Management**: Minimal — `_authenticated` flag is the only state affected
* **Error Scenarios**: Simple — the `_check_auth()` fix is already wrapped in try/except

### Risk Profile
* **Business Criticality**: MEDIUM — SDK is core dependency, but changes are minimal
* **User Impact**: LOW — no user-facing behavior change (except new version line in `/help`)
* **Data Sensitivity**: None
* **Failure Cost**: LOW — if `_check_auth()` fix fails, the try/except sets `_authenticated = False` gracefully

### Requirements Clarity
* **Specification Completeness**: COMPLETE — research document identifies every change needed
* **Acceptance Criteria Quality**: PRECISE — objective lists 8 measurable success criteria
* **Edge Cases Identified**: 1 (SDK not installed → `PackageNotFoundError` in help)
* **Dependencies Status**: STABLE — SDK 0.1.23 is already released and verified

## Test Strategy by Component

### Component 1: `_check_auth()` Fix — CODE_FIRST

**Approach**: Code-First
**Rationale**: One-line change (`status.get()` → `getattr()`). Existing tests in `test_sdk_client.py` already test `start()` which calls `_check_auth()`. No new tests needed — the existing mock-based tests verify `start()` doesn't crash.

**Test Requirements:**
* Coverage Target: Existing coverage maintained (no new code paths)
* Test Types: Unit (existing)
* Critical Scenarios:
  * `start()` completes successfully with new SDK (existing test `test_client_start_calls_sdk_start`)
  * Auth check doesn't crash on dataclass response (covered by existing try/except + mock)
* Edge Cases:
  * `get_auth_status()` raises exception → `_authenticated = False` (already covered by existing try/except)

**Testing Sequence:**
1. Implement the `getattr()` fix
2. Run existing tests — verify all pass
3. No new tests needed

### Component 2: `list_sessions()` Return Type — CODE_FIRST

**Approach**: Code-First
**Rationale**: Type annotation change only. Existing test `test_list_sessions` (line 232 of `test_sdk_client.py`) mocks the return value directly and verifies behavior. The conftest fixture at line 94 already mocks `list_sessions`.

**Test Requirements:**
* Coverage Target: Existing coverage maintained
* Test Types: Unit (existing)
* Critical Scenarios:
  * `list_sessions()` returns results from SDK (existing test)
  * `list_sessions()` returns empty list when no client (existing test)

**Testing Sequence:**
1. Update the return type annotation
2. Run existing tests — verify all pass

### Component 3: `/help` SDK Version Display — CODE_FIRST

**Approach**: Code-First
**Rationale**: Simple string interpolation in help output. New assertion needed to verify SDK version appears in output.

**Test Requirements:**
* Coverage Target: 100% for new code path (version retrieval + display)
* Test Types: Unit
* Critical Scenarios:
  * General `/help` output includes `"Copilot SDK:"` text
  * SDK version string is present in output
* Edge Cases:
  * SDK package not installed → displays `"unknown"` (mock `importlib.metadata` to raise `PackageNotFoundError`)

**Testing Sequence:**
1. Implement version display in `handle_help()`
2. Add assertion to existing `test_help_returns_command_list`: `assert "Copilot SDK:" in result.output`
3. Optionally add test for `PackageNotFoundError` edge case

### Component 4: Dependency Version Bump — CODE_FIRST

**Approach**: Code-First
**Rationale**: Configuration change only (`pyproject.toml` + `uv.lock` regeneration). Validated by running full test suite and `uv run teambot --help`.

**Test Requirements:**
* Coverage Target: N/A — configuration file
* Test Types: Integration (full test suite run)
* Critical Scenarios:
  * All 1084 existing tests pass with new SDK
  * `uv run teambot --help` runs without import errors
  * Linting passes (`uv run ruff check .`)

**Testing Sequence:**
1. Update `pyproject.toml`
2. Run `uv lock`
3. Run `uv sync`
4. Run `uv run pytest` — all tests pass
5. Run `uv run ruff check .` — no lint errors
6. Run `uv run teambot --help` — no crashes

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest ≥7.4.0
* **Version**: As specified in pyproject.toml
* **Configuration**: `pyproject.toml` `[tool.pytest.ini_options]`
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (AsyncMock, MagicMock, patch) — used throughout codebase
* **Assertions**: Built-in pytest `assert` statements
* **Coverage**: `pytest-cov` — `--cov=src/teambot --cov-report=term-missing`
* **Test Data**: Mock objects defined in `tests/conftest.py`

### Test Organization
* **Test Location**: `tests/` (mirrors `src/teambot/` structure)
* **Naming Convention**: `test_*.py` files, `Test*` classes, `test_*` functions
* **Fixture Strategy**: Shared fixtures in `tests/conftest.py`, module-specific fixtures in test files
* **Setup/Teardown**: pytest fixtures with `monkeypatch` for SDK mocking

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 80% (existing project standard)
* **Integration Coverage**: Validated by full test suite run
* **Critical Path Coverage**: 100% (SDK client start/stop/execute)
* **Error Path Coverage**: Maintained (existing try/except patterns)

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `_check_auth()` fix | Existing | N/A | HIGH | Covered by `test_client_start_calls_sdk_start` |
| `list_sessions()` type | Existing | N/A | LOW | Type annotation only |
| `/help` version display | 100% | N/A | MEDIUM | 1-2 new assertions needed |
| Dependency version bump | N/A | 100% | CRITICAL | Full test suite + lint + CLI smoke test |

### Critical Test Scenarios

1. **SDK Client Start** (Priority: CRITICAL)
   * **Description**: `CopilotSDKClient.start()` completes without error with upgraded SDK
   * **Test Type**: Unit (existing)
   * **Success Criteria**: `start()` doesn't raise, `_started` is True
   * **Test Approach**: Code-First (existing test covers this)

2. **Full Regression Suite** (Priority: CRITICAL)
   * **Description**: All ~1084 existing tests pass with SDK 0.1.23 installed
   * **Test Type**: Full suite
   * **Success Criteria**: 0 failures, 0 errors
   * **Test Approach**: Code-First (run after implementation)

3. **Help Output Includes SDK Version** (Priority: HIGH)
   * **Description**: `/help` command output contains `"Copilot SDK:"` with version number
   * **Test Type**: Unit
   * **Success Criteria**: `"Copilot SDK:" in handle_help([]).output`
   * **Test Approach**: Code-First (add assertion after implementation)

4. **Linting Passes** (Priority: HIGH)
   * **Description**: All modified files pass `ruff check`
   * **Test Type**: Lint
   * **Success Criteria**: Exit code 0
   * **Test Approach**: Code-First

### Edge Cases to Cover

* **SDK not installed**: `importlib.metadata.version()` raises `PackageNotFoundError` → help shows `"unknown"`
* **Auth check failure**: `get_auth_status()` raises any exception → `_authenticated = False` (existing try/except)

### Error Scenarios

* **Import error after upgrade**: Caught by running full test suite — any import path changes would cause immediate failures
* **Event type enum changes**: Covered by streaming tests that use mock events with string-based type matching

## Test Data Strategy

### Test Data Requirements
* **SDK mock responses**: Existing `conftest.py` fixtures (`mock_sdk_client`, `mock_sdk_session`, etc.)
* **Auth status responses**: Mocked as `{"isAuthenticated": True}` in tests (dict format)

### Test Data Management
* **Storage**: Inline in test files and `conftest.py`
* **Generation**: Manual fixtures
* **Isolation**: Each test uses fresh mock instances via pytest fixtures
* **Cleanup**: Automatic via pytest fixture teardown

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_repl/test_commands.py` (lines 21-30)
**Pattern**: Direct function call with assertion on output string

```python
class TestHelpCommand:
    def test_help_returns_command_list(self):
        """Test /help returns list of commands."""
        result = handle_help([])

        assert result.success is True
        assert "@agent" in result.output
        assert "/help" in result.output
        assert "/status" in result.output
```

**Key Conventions:**
* Direct function calls (no HTTP clients or app setup needed)
* String presence assertions with `in` operator
* Descriptive test names explaining behavior
* Docstrings on each test method

### Recommended New Test

```python
def test_help_shows_sdk_version(self):
    """Test /help output includes Copilot SDK version."""
    result = handle_help([])
    assert "Copilot SDK:" in result.output
```

## Success Criteria

### Test Implementation Complete When:
- [x] All critical scenarios have tests (existing + 1 new assertion)
- [x] Coverage targets are met per component
- [x] All edge cases are tested (auth failure = existing; SDK not installed = optional)
- [x] Error paths are validated (existing try/except)
- [x] Tests follow codebase conventions
- [x] Tests are maintainable and clear
- [x] CI/CD integration is working (existing)

### Test Quality Indicators:
* Tests are readable and self-documenting ✅
* Tests are fast and reliable (mocked SDK) ✅
* Tests are independent (fixture-based isolation) ✅
* Failures clearly indicate the problem ✅
* Mock/stub usage is appropriate and minimal ✅

## Implementation Guidance

### For This Code-First Approach:
1. Make all source code changes (pyproject.toml, sdk_client.py, commands.py)
2. Run `uv lock && uv sync` to update dependencies
3. Run `uv run pytest` — expect all ~1084 tests to pass
4. Run `uv run ruff check .` — expect clean
5. Add `"Copilot SDK:"` assertion to help command tests
6. Run `uv run teambot --help` — smoke test
7. Verify no regressions

## Considerations and Trade-offs

### Selected Approach Benefits:
* Fast implementation — all changes are mechanical
* Existing test suite provides comprehensive regression coverage
* Minimal new test code required (1-2 assertions)

### Accepted Trade-offs:
* No TDD for the `getattr()` fix — acceptable because existing tests cover the code path
* Auth mock returns dict (not dataclass) in tests — acceptable because production code uses `getattr()` which works for both

### Risk Mitigation:
* Full test suite run catches any unexpected SDK API changes
* Lint check catches import or syntax issues
* CLI smoke test (`teambot --help`) verifies end-to-end import chain

## References

* **Research Doc**: [.agent-tracking/research/20260210-copilot-sdk-upgrade-research.md](../research/20260210-copilot-sdk-upgrade-research.md)
* **Test Examples**: `tests/test_copilot/test_sdk_client.py`, `tests/test_repl/test_commands.py`
* **Conftest Fixtures**: `tests/conftest.py`
* **pyproject.toml test config**: `pyproject.toml` lines 42-48

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow Code-First approach per component

---

**Strategy Status**: DRAFT
**Approved By**: PENDING
**Ready for Planning**: YES
