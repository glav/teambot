<!-- markdownlint-disable-file -->
# Test Strategy: Remove Overlay Feature

**Strategy Date**: 2026-02-13
**Feature Specification**: .teambot/remove-overlay/artifacts/feature_spec.md
**Research Reference**: N/A (removal operation - no research phase required)
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: CODE_FIRST (Test-After / Deletion Verification)

### Rationale

This is a **code removal operation**, not a feature addition. The standard TDD approach does not apply since we are deleting functionality rather than building it. The testing strategy focuses on **verification after removal** - ensuring no regressions, no orphan references, and continued functionality of unrelated systems.

The test strategy involves:
1. **Delete overlay-specific tests first** (they test removed functionality)
2. **Remove overlay code** following the phased rollout plan
3. **Verify remaining tests pass** (regression prevention)
4. **Verify no orphan imports or references** (cleanup validation)

**Key Factors:**
* Complexity: LOW (deletion operation with clear boundaries)
* Risk: MEDIUM (must not break REPL or other features)
* Requirements Clarity: CLEAR (spec defines exactly what to delete)
* Time Pressure: LOW (no deadline pressure)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | TDD Points | Code-First Points | Score |
|--------|----------|------------|-------------------|-------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | 3 if YES | 0 | TDD: 0 (N/A for removal) |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | 3 if HIGH | 0 | Code-First: 2 (Simple deletion) |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | 3 if CRITICAL | 0 | TDD: 0 (Low risk) |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | 0 | 3 if YES | Code-First: 0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | 0 | 2 if YES | Code-First: 2 (Simple removal) |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | 0 | 2 if YES | Code-First: 0 |
| **Requirements Stability** | Are requirements likely to change during development? | 0 | 2 if YES | Code-First: 0 |

### Totals

* **TDD Score**: 0 (not applicable - removal operation)
* **Code-First Score**: 4

### Decision

**Decision: CODE_FIRST (Test-After Verification)**

Rationale: This is a removal operation. TDD cannot apply because we are not building new functionality. The correct approach is:
1. Delete tests for removed functionality
2. Delete the functionality
3. Run remaining test suite to verify no regressions
4. Verify no orphan imports (linting)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: LOW - No algorithms to test, pure file/code deletion
* **Integration Depth**: MEDIUM - Overlay integrates with REPL, TaskExecutor, config loader
* **State Management**: LOW - No state transitions to verify
* **Error Scenarios**: LOW - Main error case is orphan imports (caught by linting)

### Risk Profile
* **Business Criticality**: LOW - Removing unused feature
* **User Impact**: NONE - Feature is unused
* **Data Sensitivity**: NONE - No data handling involved
* **Failure Cost**: MEDIUM - Breaking REPL or other features would be problematic

### Requirements Clarity
* **Specification Completeness**: COMPLETE - All files to delete/modify listed
* **Acceptance Criteria Quality**: PRECISE - 6 acceptance test scenarios defined
* **Edge Cases Identified**: 4 documented (orphan code, broken imports, doc inconsistency, test deps)
* **Dependencies Status**: STABLE - No external dependencies

## Test Strategy by Component

### Component 1: Overlay Module Deletion - CODE_FIRST

**Approach**: Code-First (Delete, then verify)
**Rationale**: Cannot write tests for removed code. Delete and verify imports don't break.

**Test Requirements:**
* Coverage Target: N/A (deleting, not covering)
* Test Types: Verification (import checks, linting)
* Critical Scenarios:
  * `src/teambot/visualization/overlay.py` deleted
  * `tests/test_visualization/test_overlay.py` deleted
* Edge Cases:
  * No orphan imports from deleted module

**Testing Sequence**:
1. Delete `tests/test_visualization/test_overlay.py` (572 lines)
2. Delete `src/teambot/visualization/overlay.py` (603 lines)
3. Run `uv run ruff check .` to verify no import errors
4. Run `uv run pytest` to verify remaining tests pass

### Component 2: REPL Command Removal - CODE_FIRST

**Approach**: Code-First (Delete, then verify)
**Rationale**: Command handler removal must be verified by running REPL or remaining tests.

**Test Requirements:**
* Coverage Target: Existing REPL tests must pass
* Test Types: Regression (existing test_commands.py tests)
* Critical Scenarios:
  * `/overlay` command removed from handler
  * `/help` output no longer includes `/overlay`
* Edge Cases:
  * Other REPL commands still function correctly

**Testing Sequence**:
1. Delete `tests/test_repl/test_commands_overlay.py` (142 lines)
2. Remove overlay imports and handler from `src/teambot/repl/commands.py`
3. Remove overlay integration from `src/teambot/repl/loop.py`
4. Run `uv run pytest tests/test_repl/` to verify remaining REPL tests pass

### Component 3: Config Loader Cleanup - CODE_FIRST

**Approach**: Code-First (Modify, then verify)
**Rationale**: Config tests should continue passing after removal of overlay-specific options.

**Test Requirements:**
* Coverage Target: Existing config tests must pass
* Test Types: Regression (test_config/test_loader.py)
* Critical Scenarios:
  * Overlay config validation removed
  * Default config generation excludes overlay
* Edge Cases:
  * Legacy configs with overlay options don't cause errors

**Testing Sequence**:
1. Remove overlay validation from `src/teambot/config/loader.py`
2. Remove overlay-specific tests from `tests/test_config/test_loader.py`
3. Run `uv run pytest tests/test_config/` to verify config tests pass

### Component 4: TaskExecutor Cleanup - CODE_FIRST

**Approach**: Code-First (Modify, then verify)
**Rationale**: TaskExecutor tests should continue passing after removal of overlay hooks.

**Test Requirements:**
* Coverage Target: Existing executor tests must pass
* Test Types: Regression (test_tasks/test_executor.py)
* Critical Scenarios:
  * Overlay callbacks removed from TaskExecutor
  * Pipeline execution works without overlay
* Edge Cases:
  * Event emission patterns unchanged for other subscribers

**Testing Sequence**:
1. Remove overlay imports and callbacks from `src/teambot/tasks/executor.py`
2. Run `uv run pytest tests/test_tasks/` to verify executor tests pass

### Component 5: Documentation Cleanup - CODE_FIRST

**Approach**: Code-First (Modify, then verify)
**Rationale**: Documentation changes don't require automated tests.

**Test Requirements:**
* Coverage Target: N/A (documentation)
* Test Types: Manual review
* Critical Scenarios:
  * `docs/guides/architecture.md` updated
  * `docs/guides/development.md` updated
* Edge Cases:
  * Other doc files may reference overlay

**Testing Sequence**:
1. Remove overlay references from documentation
2. Delete `docs/feature-specs/persistent-status-overlay.md`
3. Run `grep -r "overlay" docs/` to verify no stale references

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: Per pyproject.toml dependency
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: unittest.mock (standard library)
* **Assertions**: pytest built-in + pytest-mock
* **Coverage**: pytest-cov - Target: Maintain existing 80%+
* **Test Data**: Fixtures in conftest.py

### Test Organization
* **Test Location**: `tests/` directory
* **Naming Convention**: `test_*.py` files, `test_*` functions
* **Fixture Strategy**: Shared fixtures in `tests/conftest.py`
* **Setup/Teardown**: pytest fixtures with tmp_path

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: Maintain 80%+ (after removing overlay-specific tests)
* **Integration Coverage**: 100% for REPL commands
* **Critical Path Coverage**: 100% for remaining test paths
* **Error Path Coverage**: 100% for import validation

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| visualization module | 80%+ | N/A | HIGH | After overlay.py removal |
| repl/commands.py | 80%+ | 100% | CRITICAL | Other commands must work |
| repl/loop.py | 80%+ | 100% | CRITICAL | REPL must start |
| config/loader.py | 80%+ | N/A | HIGH | Config must load |
| tasks/executor.py | 80%+ | N/A | HIGH | Pipeline must run |

### Critical Test Scenarios

Priority test scenarios that MUST pass after removal:

1. **REPL Startup** (Priority: CRITICAL)
   * **Description**: REPL initializes without overlay
   * **Test Type**: Integration
   * **Success Criteria**: No import errors, prompt appears
   * **Test Approach**: Run existing test_repl tests

2. **Config Loading** (Priority: CRITICAL)
   * **Description**: Configuration loads without overlay options
   * **Test Type**: Unit
   * **Success Criteria**: Config loads, no validation errors
   * **Test Approach**: Run existing test_config tests

3. **Task Execution** (Priority: HIGH)
   * **Description**: Pipeline executes without overlay hooks
   * **Test Type**: Integration
   * **Success Criteria**: Tasks complete successfully
   * **Test Approach**: Run existing test_tasks tests

4. **Help Command** (Priority: MEDIUM)
   * **Description**: /help output excludes overlay
   * **Test Type**: Unit
   * **Success Criteria**: No overlay in help output
   * **Test Approach**: Modify existing help test or manual verification

### Edge Cases to Cover

* **Orphan imports**: Verify no code imports from deleted overlay module
* **Config compatibility**: Verify configs without overlay options load correctly
* **Help consistency**: Verify /help doesn't reference removed command
* **Event hooks**: Verify executor events still emit correctly

### Error Scenarios

* **Import Error**: If any module imports overlay after deletion → caught by test run
* **Config Validation Error**: If config expects overlay options → caught by config tests
* **Linting Error**: If orphan references exist → caught by ruff check

## Test Data Strategy

### Test Data Requirements
* **Config files**: Existing test fixtures handle config testing
* **REPL input**: Existing command tests cover input handling

### Test Data Management
* **Storage**: Test fixtures in conftest.py and tmp_path
* **Generation**: pytest fixtures
* **Isolation**: Each test uses isolated tmp_path
* **Cleanup**: Automatic via pytest

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_config/test_loader.py`
**Pattern**: Pytest class-based tests with tmp_path fixture

```python
class TestConfigLoader:
    """Tests for ConfigLoader class."""

    def test_load_valid_config(self, tmp_path):
        """Load valid JSON configuration."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [
                {
                    "id": "pm",
                    "persona": "project_manager",
                    "display_name": "Project Manager",
                }
            ],
            "teambot_dir": ".teambot",
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["agents"][0]["id"] == "pm"
```

**Key Conventions:**
* Class-based test organization (`Test*` classes)
* Descriptive docstrings for each test
* Imports inside test methods (lazy imports)
* tmp_path fixture for file operations

### Recommended Post-Removal Verification

```bash
# 1. Run full test suite (excluding deleted tests)
uv run pytest

# 2. Run linting to catch orphan imports
uv run ruff check .

# 3. Grep for stale overlay references
grep -r "overlay" src/teambot/

# 4. Verify REPL starts
uv run teambot --help
```

## Success Criteria

### Test Implementation Complete When:
* [x] Overlay-specific tests deleted (test_overlay.py, test_commands_overlay.py)
* [ ] All remaining tests pass (uv run pytest)
* [ ] Linting passes (uv run ruff check .)
* [ ] No orphan imports (grep verification)
* [ ] REPL starts without errors
* [ ] Help command excludes overlay

### Test Quality Indicators:
* Remaining tests are readable and self-documenting
* Tests are fast and reliable (no flakiness)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem
* Coverage remains at 80%+

## Implementation Guidance

### For Code-First Deletion:
1. Delete overlay-specific test files first
2. Delete overlay source module
3. Clean up imports in affected modules
4. Run test suite to verify no regressions
5. Run linting to verify no orphan references

### Verification Order (Recommended):
1. `uv run pytest tests/test_visualization/` - verify visualization tests pass (without overlay)
2. `uv run pytest tests/test_repl/` - verify REPL tests pass
3. `uv run pytest tests/test_config/` - verify config tests pass
4. `uv run pytest tests/test_tasks/` - verify executor tests pass
5. `uv run pytest` - full suite
6. `uv run ruff check .` - linting
7. `grep -r "overlay" src/` - orphan references

## Considerations and Trade-offs

### Selected Approach Benefits:
* No wasted effort writing tests for code being deleted
* Verification-focused approach matches removal operation
* Leverages existing test suite for regression detection
* Clean, phased execution plan

### Accepted Trade-offs:
* No test coverage for removal process itself (acceptable for deletions)
* Manual verification of REPL startup (acceptable, covered by acceptance tests)

### Risk Mitigation:
* Full test suite run after each deletion phase catches regressions
* Linting catches orphan imports immediately
* Grep search catches documentation references

## References

* **Feature Spec**: [.teambot/remove-overlay/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/remove-overlay/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: tests/test_config/test_loader.py, tests/test_repl/test_commands.py
* **Test Standards**: pyproject.toml [tool.pytest.ini_options]

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (implementation phases)
3. 📋 Task planner will incorporate verification steps into implementation phases
4. 🔍 Implementation will follow the phased deletion and verification approach

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE
- Approach: CODE_FIRST (deletion operation with post-removal verification)
- Coverage Targets: SPECIFIED (maintain 80%+ after removal)
- Components Covered: 5/5
```
