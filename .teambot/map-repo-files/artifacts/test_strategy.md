<!-- markdownlint-disable-file -->
# Test Strategy: TeamBot Init Scaffolding

**Strategy Date**: 2026-02-17
**Feature Specification**: .teambot/map-repo-files/artifacts/feature_spec.md
**Specification Review**: .teambot/map-repo-files/artifacts/spec_review.md
**Strategist**: Builder-2 Agent

## Recommended Testing Approach

**Primary Approach**: TDD (Test-Driven Development)

### Testing Approach Decision Matrix

| Factor | Question | Score | Points |
|--------|----------|-------|--------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES | TDD +3 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM (file operations, path handling, conditional logic) | TDD +2 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | HIGH (data integrity - must never overwrite existing files) | TDD +3 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO | Code-First +0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | NO (conditional copying, directory traversal, cross-platform) | Code-First +0 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO | Code-First +0 |
| **Requirements Stability** | Are requirements likely to change during development? | NO (spec approved, requirements clear) | Code-First +0 |

### Decision Calculation

```
TDD Score: 8 (3 + 2 + 3)
Code-First Score: 0

Decision: TDD (score 8 ≥ threshold 6)
```

### Rationale

TDD is the optimal approach for this feature because:

1. **Data Integrity is Critical**: The feature must never overwrite existing user files. TDD forces us to write tests that explicitly verify this safety guarantee before writing any implementation code. This ensures the "never overwrite" behavior is baked into the design from the start.

2. **Well-Defined Requirements**: The specification provides precise acceptance criteria for each functional requirement (FR-001 through FR-010). Each can be translated directly into a test case.

3. **Cross-Platform File Operations**: Path handling must work correctly on Windows, Linux, and macOS. TDD allows us to write platform-agnostic tests using `pathlib.Path` that validate correct behavior across all platforms.

**Key Factors:**
* Complexity: MEDIUM (file operations with conditional logic)
* Risk: HIGH (data integrity - existing files must be preserved)
* Requirements Clarity: CLEAR (6 acceptance tests, 10 functional requirements)
* Time Pressure: LOW (feature can follow proper TDD cycle)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: LOW - No complex algorithms, primarily file I/O operations
* **Integration Depth**: MEDIUM - Integrates with `importlib.resources`, `shutil`, existing `cmd_init()`
* **State Management**: LOW - No persistent state; file existence checks are stateless
* **Error Scenarios**: MEDIUM - Permission errors, disk full, partial copies, missing resources

### Risk Profile
* **Business Criticality**: HIGH - Core onboarding experience for new users
* **User Impact**: WIDESPREAD - Every new user runs `teambot init`
* **Data Sensitivity**: LOW - Only public documentation/configuration files
* **Failure Cost**: HIGH - Overwriting user files would destroy customizations and break trust

### Requirements Clarity
* **Specification Completeness**: COMPLETE (17 sections, all placeholders resolved)
* **Acceptance Criteria Quality**: PRECISE (6 detailed acceptance test scenarios)
* **Edge Cases Identified**: 5+ documented (empty directories, partial state, re-init)
* **Dependencies Status**: STABLE (Python stdlib only: shutil, pathlib, importlib.resources)

## Test Strategy by Component

### Component 1: Resource Locator - TDD

**Approach**: TDD
**Rationale**: Package resource access via `importlib.resources` must work for both development (source) and installed (pip/uvx) scenarios. Tests first ensure we handle both cases correctly.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Locate resources when installed via pip/uvx
  * Locate resources when running from source/development
  * Handle missing resources gracefully with clear error
* Edge Cases:
  * Resource file exists but is empty
  * Resource directory exists but is empty

**Testing Sequence (TDD)**:
1. Write test: `test_get_resource_path_returns_path_for_existing_resource()`
2. Write test: `test_get_resource_path_raises_for_missing_resource()`
3. Implement `get_resource_path()` function
4. Refactor for clean interface

### Component 2: Single File Copier - TDD

**Approach**: TDD
**Rationale**: File copying with existence checks is the core safety mechanism. Must be tested exhaustively before implementation.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Copy file when destination doesn't exist
  * Skip copy when destination exists (CRITICAL)
  * Create parent directories if needed
  * Return status indicating copied vs. skipped
* Edge Cases:
  * Source file is empty
  * Destination parent directory doesn't exist
  * Permission denied on destination

**Testing Sequence (TDD)**:
1. Write test: `test_copy_file_creates_file_when_not_exists()`
2. Write test: `test_copy_file_skips_when_exists()` (CRITICAL)
3. Write test: `test_copy_file_creates_parent_directories()`
4. Write test: `test_copy_file_returns_copy_status()`
5. Implement `copy_file_if_missing()` function
6. Add error handling tests
7. Refactor

### Component 3: Directory Tree Copier - TDD

**Approach**: TDD
**Rationale**: Recursive directory copying with conditional logic for `.agent/` and `.github/agents/` directories. Complex enough to benefit from test-first design.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit, Integration
* Critical Scenarios:
  * Copy entire directory tree when destination doesn't exist
  * Skip directory entirely when destination exists
  * Handle empty source directory
* Edge Cases:
  * Destination is empty directory (special case per FR-007)
  * Partial destination directory (some files exist)
  * Nested directory structure

**Testing Sequence (TDD)**:
1. Write test: `test_copy_directory_creates_when_not_exists()`
2. Write test: `test_copy_directory_skips_when_exists()`
3. Write test: `test_copy_directory_populates_when_empty()`
4. Implement `copy_directory_if_missing()` function
5. Add nested directory tests
6. Refactor

### Component 4: Scaffolding Orchestrator - TDD

**Approach**: TDD
**Rationale**: Orchestrates all copy operations and console output. Must be tested to ensure correct sequencing and status reporting.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit, Integration
* Critical Scenarios:
  * Fresh init copies all 5 resource sets
  * Re-init skips all existing resources
  * Partial state copies only missing resources
  * Console output shows correct copied/skipped status
* Edge Cases:
  * Some resources exist, others don't
  * Package resources not found (installation error)

**Testing Sequence (TDD)**:
1. Write test: `test_copy_scaffolding_fresh_init_copies_all()`
2. Write test: `test_copy_scaffolding_reinit_skips_all()`
3. Write test: `test_copy_scaffolding_partial_copies_missing()`
4. Write test: `test_copy_scaffolding_reports_status_per_resource()`
5. Implement `copy_scaffolding()` function
6. Integrate with `cmd_init()`
7. Refactor

### Component 5: cmd_init Integration - TDD

**Approach**: TDD
**Rationale**: Integration with existing `cmd_init()` must be additive-only and not break existing behavior.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Integration
* Critical Scenarios:
  * Existing init tests continue to pass
  * New scaffolding copied after config creation
  * Console output format matches spec (Appendix B)
* Edge Cases:
  * Init with --force flag behavior unchanged
  * Init error handling preserved

**Testing Sequence (TDD)**:
1. Run existing `TestCLIInit` tests - ensure they pass
2. Write test: `test_init_copies_scaffolding_files()`
3. Write test: `test_init_skips_existing_scaffolding()`
4. Integrate `copy_scaffolding()` into `cmd_init()`
5. Verify existing tests still pass

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`
* **Coverage**: pytest-cov with `--cov=src/teambot --cov-report=term-missing`

### Testing Tools Required
* **Mocking**: `unittest.mock`, `pytest-mock` (existing dependency)
* **Assertions**: pytest built-in assertions
* **Coverage**: pytest-cov - Target: 90%+ for new code
* **Test Data**: In-memory file structures using `tmp_path` fixture

### Test Organization
* **Test Location**: `tests/test_scaffolding.py` (new file)
* **Acceptance Tests**: `tests/test_init_scaffolding_acceptance.py` (new file)
* **Naming Convention**: `test_<function>_<scenario>()` pattern
* **Fixture Strategy**: Use pytest's `tmp_path` and `monkeypatch` fixtures
* **Setup/Teardown**: pytest fixtures handle setup; tmp_path auto-cleans

### Example Test Patterns from Codebase

**File**: `tests/test_cli.py`
**Pattern**: Testing CLI commands with `tmp_path` and `monkeypatch.chdir()`

```python
def test_init_creates_config(self, tmp_path, monkeypatch):
    """Init creates configuration file."""
    import argparse

    from teambot.cli import ConsoleDisplay, cmd_init

    monkeypatch.chdir(tmp_path)

    args = argparse.Namespace(force=False)
    display = ConsoleDisplay()

    result = cmd_init(args, display)

    assert result == 0
    assert (tmp_path / "teambot.json").exists()
    assert (tmp_path / ".teambot").exists()
```

**Key Conventions:**
* Use `tmp_path` fixture for file operations (auto-cleanup)
* Use `monkeypatch.chdir()` to change working directory
* Import inside test functions for isolation
* Assert file existence with `Path.exists()`
* Test return codes for CLI commands

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% minimum for new code
* **Integration Coverage**: 80%
* **Critical Path Coverage**: 100% (file existence checks, never-overwrite logic)
* **Error Path Coverage**: 80%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| Resource Locator | 100% | - | HIGH | Must work for pip and source installs |
| Single File Copier | 100% | - | CRITICAL | Never-overwrite guarantee |
| Directory Tree Copier | 100% | - | CRITICAL | Never-overwrite guarantee |
| Scaffolding Orchestrator | 90% | 80% | HIGH | Coordinates all operations |
| cmd_init Integration | 80% | 90% | HIGH | Additive-only changes |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Never Overwrite Existing Files** (Priority: CRITICAL)
   * **Description**: Verify that existing files are never modified or overwritten
   * **Test Type**: Unit + Integration
   * **Success Criteria**: File content and mtime unchanged after init
   * **Test Approach**: TDD

2. **Fresh Init Copies All Resources** (Priority: CRITICAL)
   * **Description**: All 5 resource sets copied to empty repository
   * **Test Type**: Integration
   * **Success Criteria**: stages.yaml, .github/agents/, .agent/, docs/, AGENTS.md all created
   * **Test Approach**: TDD

3. **Package Resource Access** (Priority: HIGH)
   * **Description**: Resources accessible via `importlib.resources` when pip-installed
   * **Test Type**: Unit
   * **Success Criteria**: `get_resource_path()` returns valid paths
   * **Test Approach**: TDD

4. **Cross-Platform Path Handling** (Priority: HIGH)
   * **Description**: Paths work correctly on Windows, Linux, macOS
   * **Test Type**: Unit
   * **Success Criteria**: Tests pass using `pathlib.Path` (platform-agnostic)
   * **Test Approach**: TDD

5. **Empty Directory Handling** (Priority: MEDIUM)
   * **Description**: Empty `.github/agents/` directory treated as non-existent
   * **Test Type**: Unit
   * **Success Criteria**: Empty directory populated with agent files
   * **Test Approach**: TDD

6. **Console Status Output** (Priority: MEDIUM)
   * **Description**: Console shows "Copied" vs "Skipped" for each resource
   * **Test Type**: Integration
   * **Success Criteria**: Output matches Appendix B format
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Partial `.agent/` directory**: Only some subdirectories exist - should copy missing ones
* **Read-only destination**: PermissionError caught and reported clearly
* **Very long paths**: Windows path length limits (use short test names)
* **Unicode filenames**: Agent files with special characters in content
* **Concurrent init**: Two processes running init simultaneously (document as unsupported)

### Error Scenarios

* **PermissionError**: User lacks write access - clear error message
* **Resource not found**: Package installed incorrectly - helpful diagnostic
* **Disk full**: OSError during copy - cleanup partial state if possible
* **Invalid package structure**: Resources missing from distribution - clear error

## Test Data Strategy

### Test Data Requirements
* **Source resources**: Mock package resources using `tmp_path`
* **Target repository**: Empty `tmp_path` directory simulating fresh repo
* **Existing files**: Pre-created files in `tmp_path` for skip tests

### Test Data Management
* **Storage**: In-memory via `tmp_path` fixture (no persistent test data)
* **Generation**: Programmatic creation in test fixtures
* **Isolation**: Each test gets fresh `tmp_path` (pytest handles isolation)
* **Cleanup**: Automatic via pytest `tmp_path` fixture

## Recommended Test Structure

### Unit Test File: `tests/test_scaffolding.py`

```python
"""Unit tests for scaffolding copy operations - TDD approach."""

from pathlib import Path

import pytest


class TestResourceLocator:
    """Tests for package resource location."""

    def test_get_resource_path_returns_path_for_existing(self):
        """Resource locator returns path for existing resource."""
        # Arrange: (setup in fixture)
        # Act: call get_resource_path("stages.yaml")
        # Assert: returns Path object, path exists
        pass

    def test_get_resource_path_raises_for_missing(self):
        """Resource locator raises error for missing resource."""
        pass


class TestCopyFileIfMissing:
    """Tests for single file conditional copy."""

    def test_copies_when_destination_not_exists(self, tmp_path):
        """Copy file when destination doesn't exist."""
        pass

    def test_skips_when_destination_exists(self, tmp_path):
        """Skip copy when destination already exists."""
        pass

    def test_creates_parent_directories(self, tmp_path):
        """Create parent directories if they don't exist."""
        pass

    def test_returns_copied_status(self, tmp_path):
        """Return CopyStatus.COPIED when file was copied."""
        pass

    def test_returns_skipped_status(self, tmp_path):
        """Return CopyStatus.SKIPPED when file existed."""
        pass


class TestCopyDirectoryIfMissing:
    """Tests for directory tree conditional copy."""

    def test_copies_when_destination_not_exists(self, tmp_path):
        """Copy directory tree when destination doesn't exist."""
        pass

    def test_skips_when_destination_exists(self, tmp_path):
        """Skip copy when destination directory exists."""
        pass

    def test_populates_when_destination_empty(self, tmp_path):
        """Populate directory when it exists but is empty."""
        pass


class TestCopyScaffolding:
    """Tests for scaffolding orchestration."""

    def test_copies_all_resources_on_fresh_init(self, tmp_path):
        """Copy all scaffolding resources to empty repository."""
        pass

    def test_skips_all_on_reinit(self, tmp_path):
        """Skip all resources when repository already initialized."""
        pass

    def test_copies_only_missing_resources(self, tmp_path):
        """Copy only missing resources in partial state."""
        pass
```

### Acceptance Test File: `tests/test_init_scaffolding_acceptance.py`

```python
"""Acceptance tests for init scaffolding feature."""

import pytest


@pytest.mark.acceptance
class TestInitScaffoldingAcceptance:
    """Acceptance tests matching AT-001 through AT-006."""

    def test_at_001_fresh_repository_initialization(self, tmp_path, monkeypatch):
        """AT-001: Fresh init copies all scaffolding files."""
        pass

    def test_at_002_reinit_preserves_existing_files(self, tmp_path, monkeypatch):
        """AT-002: Re-init never overwrites existing files."""
        pass

    def test_at_003_partial_state_fills_gaps(self, tmp_path, monkeypatch):
        """AT-003: Partial init copies only missing resources."""
        pass

    def test_at_005_empty_directory_handling(self, tmp_path, monkeypatch):
        """AT-005: Empty .github/agents/ gets populated."""
        pass
```

## Success Criteria

### Test Implementation Complete When:
- [ ] All unit tests for 4 components written (TDD: tests first, then code)
- [ ] Coverage targets met: 90%+ unit, 80%+ integration
- [ ] All 6 acceptance test scenarios have passing tests
- [ ] All 5 edge cases have explicit tests
- [ ] Error scenarios (permission, disk full) have tests
- [ ] Tests follow codebase conventions (tmp_path, monkeypatch)
- [ ] Tests are maintainable and clear
- [ ] All tests pass: `uv run pytest tests/test_scaffolding.py tests/test_init_scaffolding_acceptance.py`

### Test Quality Indicators:
* Tests are readable and self-documenting (clear names, docstrings)
* Tests are fast: < 1 second per test (file I/O to tmp_path is fast)
* Tests are reliable: no flakiness (no timing dependencies)
* Tests are independent: no test order dependencies
* Failures clearly indicate the problem (specific assertions)
* Mock/stub usage is minimal (prefer real file I/O to tmp_path)

## Implementation Guidance

### For TDD Components (All):
1. Write the simplest failing test case first
2. Run test to confirm it fails for the right reason
3. Write minimal code to pass the test
4. Run test to confirm it passes
5. Add next test case
6. Refactor when all tests pass (extract helpers, clean naming)
7. Focus on behavior, not implementation details

### TDD Workflow Example:

```bash
# Cycle 1: First test
uv run pytest tests/test_scaffolding.py::TestCopyFileIfMissing::test_copies_when_destination_not_exists -v
# → FAILS (function doesn't exist)

# Implement minimal function
# ...

uv run pytest tests/test_scaffolding.py::TestCopyFileIfMissing::test_copies_when_destination_not_exists -v
# → PASSES

# Cycle 2: Add "skip if exists" test
uv run pytest tests/test_scaffolding.py::TestCopyFileIfMissing -v
# → 1 PASS, 1 FAIL

# Implement skip logic
# ...

uv run pytest tests/test_scaffolding.py::TestCopyFileIfMissing -v
# → 2 PASS
```

### Test File Organization:

```
tests/
├── test_scaffolding.py              # Unit tests (TDD)
│   ├── TestResourceLocator
│   ├── TestCopyFileIfMissing
│   ├── TestCopyDirectoryIfMissing
│   └── TestCopyScaffolding
├── test_init_scaffolding_acceptance.py  # Acceptance tests
│   └── TestInitScaffoldingAcceptance
└── test_cli.py                       # Existing (verify unchanged)
    └── TestCLIInit
```

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures never-overwrite guarantee is tested before implemented
* Tests document expected behavior clearly
* Regression safety for future changes
* Forces clear API design (testable functions)

### Accepted Trade-offs:
* Slower initial development pace (tests first)
* More upfront test infrastructure setup
* May need to refactor tests if API changes

### Risk Mitigation:
* **Never-overwrite risk**: TDD ensures this is tested first
* **Cross-platform risk**: Use `pathlib.Path` exclusively; tests run on all platforms
* **Package resource risk**: Test both source and installed scenarios
* **Integration risk**: Run existing `TestCLIInit` tests throughout development

## References

* **Feature Spec**: [.teambot/map-repo-files/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/map-repo-files/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: `tests/test_cli.py`, `tests/test_config/test_loader.py`
* **Acceptance Test Patterns**: `tests/test_stages_yaml_acceptance.py`
* **pytest Configuration**: `pyproject.toml` [tool.pytest.ini_options]

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate TDD approach into implementation phases
4. 🔍 Implementation will follow RED-GREEN-REFACTOR cycle per component

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE
- Approach: TDD (score 8 ≥ threshold 6)
- Coverage Targets: SPECIFIED (90%+ unit, 80%+ integration)
- Components Covered: 5/5 (Resource Locator, Single File Copier, Directory Tree Copier, Scaffolding Orchestrator, cmd_init Integration)
