<!-- markdownlint-disable-file -->
# Test Strategy: SDD Prompt Sync

**Strategy Date**: 2026-03-02
**Feature Specification**: .teambot/sdd-prompt-sync/artifacts/feature_spec.md
**Research Reference**: N/A (research phase skipped per workflow)
**Strategist**: Builder-2 Agent (Test Strategy)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Assessment | TDD Points | Code-First Points |
|--------|----------|------------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES - 8 FRs with explicit acceptance criteria, 6 AT scenarios | 3 | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM - file sync logic, YAML parsing, validation | 2 | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | HIGH - file overwrites could destroy user customizations | 3 | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO - well-defined feature with clear scope | 0 | 0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | NO - multiple components with validation | 0 | 0 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO - quality over speed for file operations | 0 | 0 |
| **Requirements Stability** | Are requirements likely to change during development? | NO - spec is complete and approved | 0 | 0 |

### Decision Thresholds

| TDD Score | Code-First Score | Recommendation |
|-----------|------------------|----------------|
| **8** | **0** | **TDD** ✅ |

**Decision**: TDD (score 8 >> threshold 6)

## Recommended Testing Approach

**Primary Approach**: TDD

### Rationale

The SDD Prompt Sync feature is an excellent candidate for TDD because it involves critical file system operations where incorrect behavior could destroy user customizations. The specification provides 8 functional requirements (FR-001 through FR-008) with explicit acceptance criteria and 6 acceptance test scenarios (AT-001 through AT-006) that serve as natural test cases.

The feature's core value proposition is preserving user files during sync operations - a property that is trivially verifiable through tests but catastrophic if broken in production. TDD ensures this critical invariant is validated before any implementation code is written.

Additionally, the codebase already demonstrates strong TDD patterns (see `tests/test_scaffolds.py` with 46 tests following TDD style) and the project explicitly states "TDD" as the testing preference in the constraints.

**Key Factors:**
* Complexity: **MEDIUM** - File sync, YAML parsing, validation logic
* Risk: **HIGH** - File operations that could overwrite user customizations
* Requirements Clarity: **CLEAR** - 8 FRs with acceptance criteria, 6 AT scenarios
* Time Pressure: **LOW** - Quality is priority per NFR-005 (80%+ coverage)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Medium - file comparison, YAML parsing, pattern matching (`sdd.*.prompt.md`)
* **Integration Depth**: Medium - integrates with `scaffolds.py`, `cli.py`, `workflow/stages.py`
* **State Management**: Low - stateless operations, no complex state transitions
* **Error Scenarios**: Medium - missing files, permission errors, malformed YAML

### Risk Profile
* **Business Criticality**: HIGH - core upgrade experience for users
* **User Impact**: HIGH - affects all users who upgrade TeamBot
* **Data Sensitivity**: LOW - configuration files only, no PII
* **Failure Cost**: HIGH - could overwrite user's customized prompt files

### Requirements Clarity
* **Specification Completeness**: COMPLETE - all sections filled, no TBDs
* **Acceptance Criteria Quality**: PRECISE - 8 FRs with testable criteria
* **Edge Cases Identified**: 6 documented in acceptance tests
* **Dependencies Status**: STABLE - scaffolds.py and cli.py are mature

## Test Strategy by Component

### Component 1: `sync_prompt_files()` - TDD

**Approach**: TDD
**Rationale**: Core sync function that directly handles user files. Must guarantee existing files are never overwritten without `--force` flag. This is the most critical safety property.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit tests
* Critical Scenarios:
  * Sync adds missing files only (AT-001)
  * Sync skips existing files (preserves customizations)
  * Force flag overwrites all files (AT-005)
  * Empty target directory gets populated
  * Source files missing handled gracefully
* Edge Cases:
  * `.agent/commands/sdd/` directory doesn't exist (create it)
  * Pattern `sdd.*.prompt.md` filters correctly
  * File permissions preserved (shutil.copy2)

**Testing Sequence** (TDD):
1. Write test: `test_sync_returns_empty_list_when_no_scaffold_prompts`
2. Write test: `test_sync_adds_missing_file_when_target_empty`
3. Write test: `test_sync_skips_existing_file_without_force` (CRITICAL safety test)
4. Write test: `test_sync_overwrites_with_force_flag`
5. Implement minimal code to pass each test
6. Refactor for quality

### Component 2: `get_prompt_mappings()` - TDD

**Approach**: TDD
**Rationale**: Parses `stages.yaml` to extract `prompt_template` paths. Incorrect parsing could cause false validation failures.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit tests
* Critical Scenarios:
  * Extract all prompt_template values from stages.yaml
  * Handle stages with `prompt_template: null`
  * Return mapping of stage name → prompt path
  * Handle missing or malformed stages.yaml
* Edge Cases:
  * Empty stages.yaml
  * stages.yaml with no prompt_template fields
  * Stage with prompt_template pointing outside .agent/

**Testing Sequence** (TDD):
1. Write test: `test_returns_empty_dict_for_stages_with_no_prompts`
2. Write test: `test_extracts_prompt_template_from_stage`
3. Write test: `test_skips_null_prompt_templates`
4. Write test: `test_handles_missing_stages_yaml`
5. Implement minimal code to pass each test

### Component 3: `validate_prompt_files()` - TDD

**Approach**: TDD
**Rationale**: Validation runs on every `teambot run` - must be fast, accurate, and provide actionable errors.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit tests
* Critical Scenarios:
  * All referenced prompts exist → validation passes
  * Missing prompt file → error with stage name (AT-002)
  * Error message includes remediation command (FR-005)
  * Validation handles missing `.agent/` directory gracefully
* Edge Cases:
  * stages.yaml references non-SDD prompt file
  * Symlink in prompt path
  * Empty stages.yaml

**Testing Sequence** (TDD):
1. Write test: `test_validation_passes_when_all_prompts_exist`
2. Write test: `test_validation_fails_with_missing_prompt`
3. Write test: `test_error_includes_missing_file_path`
4. Write test: `test_error_includes_stage_name`
5. Write test: `test_error_includes_remediation_command` (FR-005)
6. Implement minimal code to pass each test

### Component 4: `detect_orphaned_prompts()` - TDD

**Approach**: TDD
**Rationale**: Warning-only feature (FR-004, P2) but must avoid false positives per R-002.

**Test Requirements:**
* Coverage Target: 85%
* Test Types: Unit tests
* Critical Scenarios:
  * No orphaned files → empty list (AT-003 inverse)
  * Orphaned file detected → warning only (AT-003)
  * README.md files ignored (not orphaned)
* Edge Cases:
  * Only `sdd.*.prompt.md` pattern matched
  * Non-.md files in directory ignored
  * Directory doesn't exist → empty list

**Testing Sequence** (TDD):
1. Write test: `test_returns_empty_when_all_prompts_referenced`
2. Write test: `test_detects_orphaned_sdd_prompt`
3. Write test: `test_ignores_readme_files`
4. Write test: `test_only_matches_sdd_pattern`
5. Implement minimal code to pass each test

### Component 5: CLI Integration (`cli.py` changes) - TDD

**Approach**: TDD
**Rationale**: Must integrate cleanly with existing CLI patterns without breaking backward compatibility.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit + Integration tests
* Critical Scenarios:
  * `teambot init` displays sync summary (FR-002)
  * `teambot run` validates prompts before starting (FR-003)
  * `--skip-prompt-validation` flag bypasses check (FR-008)
  * `teambot status` shows prompt sync health (FR-007)
* Edge Cases:
  * Validation error display formatting
  * Multiple missing files in error message

**Testing Sequence** (TDD):
1. Write test: `test_parser_accepts_skip_prompt_validation_flag`
2. Write test: `test_init_displays_sync_summary`
3. Write test: `test_run_validates_prompts_before_workflow`
4. Write test: `test_run_skips_validation_with_flag`
5. Implement minimal code to pass each test

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: As specified in pyproject.toml
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` - Use `MagicMock`, `patch` for external dependencies only
* **Assertions**: pytest built-in `assert` - Clear, readable assertions
* **Coverage**: pytest-cov - Target: 80%+ overall, 90%+ for core sync
* **Test Data**: tmp_path fixture for file system isolation

### Test Organization
* **Test Location**: `tests/test_prompt_sync.py` (new file)
* **Acceptance Tests**: `tests/test_prompt_sync_acceptance.py` (new file, marked with `@pytest.mark.acceptance`)
* **Naming Convention**: `test_{function_name}_{scenario}`
* **Fixture Strategy**: Use `tmp_path` for isolated file system tests
* **Setup/Teardown**: pytest fixtures in test file or conftest.py

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% (minimum)
* **Integration Coverage**: 80%
* **Critical Path Coverage**: 100% (sync safety, validation blocking)
* **Error Path Coverage**: 85%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `sync_prompt_files()` | 95% | 90% | CRITICAL | File safety is paramount |
| `get_prompt_mappings()` | 90% | 80% | HIGH | YAML parsing must be robust |
| `validate_prompt_files()` | 95% | 90% | CRITICAL | Blocks workflow on failure |
| `detect_orphaned_prompts()` | 85% | 70% | MEDIUM | Warning only, P2 priority |
| CLI integration | 90% | 85% | HIGH | User-facing commands |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Sync Preserves Existing Files** (Priority: CRITICAL)
   * **Description**: Verify existing prompt files are never overwritten without `--force`
   * **Test Type**: Unit + Acceptance
   * **Success Criteria**: Original file content unchanged after sync
   * **Test Approach**: TDD - write test first, fail, then implement

2. **Validation Blocks Missing Prompts** (Priority: CRITICAL)
   * **Description**: `teambot run` fails before workflow when prompt file missing
   * **Test Type**: Unit + Integration
   * **Success Criteria**: Non-zero exit, error message with file path and remediation
   * **Test Approach**: TDD

3. **Actionable Error Messages** (Priority: CRITICAL)
   * **Description**: All validation errors include `teambot init` remediation command
   * **Test Type**: Unit
   * **Success Criteria**: Error string contains "teambot init"
   * **Test Approach**: TDD

4. **Incremental Sync Adds Missing Only** (Priority: HIGH)
   * **Description**: Only missing files are added; existing files skipped
   * **Test Type**: Unit + Acceptance
   * **Success Criteria**: Added count = new files, skipped count = existing files
   * **Test Approach**: TDD

5. **Force Flag Overwrites All** (Priority: HIGH)
   * **Description**: `--force` replaces all prompt files with scaffold versions
   * **Test Type**: Unit + Acceptance
   * **Success Criteria**: All files match scaffold content after force sync
   * **Test Approach**: TDD

6. **Orphaned File Warning Non-Blocking** (Priority: MEDIUM)
   * **Description**: Orphaned files produce warning but workflow proceeds
   * **Test Type**: Unit + Acceptance
   * **Success Criteria**: Warning in output, exit code 0
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Missing `.agent/commands/sdd/` directory**: Create parent directories during sync
* **Empty stages.yaml**: Return empty prompt mappings, no validation errors
* **Symlink in path**: Use `Path.resolve()` before operations (security)
* **Permission denied**: Catch `PermissionError`, include file path in error
* **Non-UTF8 file content**: Handle encoding errors gracefully

### Error Scenarios

* **FileNotFoundError on stages.yaml**: Clear error "stages.yaml not found at repo root"
* **YAML parse error**: Clear error with line number if possible
* **Permission error on write**: List specific files that failed
* **Multiple missing prompts**: List all missing files, not just first

## Test Data Strategy

### Test Data Requirements
* **stages.yaml samples**: Minimal valid config, config with multiple stages, config with null prompt_templates
* **Prompt files**: Sample `.prompt.md` files for sync testing
* **Directory structures**: Empty, partial, full `.agent/commands/sdd/` directories

### Test Data Management
* **Storage**: Created dynamically using `tmp_path` fixture
* **Generation**: Helper functions in test file (e.g., `create_stages_yaml()`)
* **Isolation**: Each test gets fresh `tmp_path` directory
* **Cleanup**: Automatic via pytest `tmp_path` fixture

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_scaffolds.py`
**Pattern**: TDD-style unit tests with clear arrange-act-assert structure

```python
class TestCopyScaffoldFile:
    """Tests for copy_scaffold_file() function."""

    def test_copies_file_when_target_missing(self, tmp_path):
        """Copies file when target doesn't exist."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "stages.yaml"

        result = copy_scaffold_file("stages.yaml", target)

        assert result.copied is True
        assert result.reason == "copied"
        assert target.exists()

    def test_skips_when_target_exists(self, tmp_path):
        """Skips copy when target already exists - CRITICAL safety test."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "stages.yaml"
        target.write_text("existing content")
        original_content = target.read_text()

        result = copy_scaffold_file("stages.yaml", target)

        assert result.copied is False
        assert result.reason == "skipped_exists"
        assert target.read_text() == original_content  # Unchanged!
```

**Key Conventions:**
* Class-based test organization by function/component
* Docstrings describe expected behavior
* `tmp_path` fixture for file system isolation
* Clear assertions on both return value and side effects
* Critical safety tests explicitly marked in docstring

### Recommended Test Structure

```python
"""Unit tests for SDD prompt sync operations - TDD approach."""

from pathlib import Path
from typing import NamedTuple

import pytest


class TestSyncPromptFiles:
    """Tests for sync_prompt_files() function."""

    def test_returns_empty_list_when_no_scaffold_prompts(self, tmp_path):
        """Returns empty list when scaffold has no prompt files."""
        from teambot.prompt_sync import sync_prompt_files
        
        # Arrange: empty scaffold (would need mock)
        
        # Act
        results = sync_prompt_files(tmp_path)
        
        # Assert
        assert results == []

    def test_adds_missing_file_when_target_empty(self, tmp_path):
        """Adds prompt file when target directory is empty."""
        from teambot.prompt_sync import sync_prompt_files
        
        # Arrange: create target directory
        target_dir = tmp_path / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        
        # Act
        results = sync_prompt_files(tmp_path)
        
        # Assert
        added = [r for r in results if r.status == "added"]
        assert len(added) > 0

    def test_skips_existing_file_without_force(self, tmp_path):
        """Skips existing files - CRITICAL safety test."""
        from teambot.prompt_sync import sync_prompt_files
        
        # Arrange: create existing file with custom content
        target_dir = tmp_path / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        existing_file = target_dir / "sdd.0-initialize.prompt.md"
        existing_file.write_text("# My Custom Prompt\nDo not overwrite!")
        original_content = existing_file.read_text()
        
        # Act
        results = sync_prompt_files(tmp_path, force=False)
        
        # Assert
        assert existing_file.read_text() == original_content  # UNCHANGED!
        skipped = [r for r in results if r.status == "skipped"]
        assert any("sdd.0-initialize" in r.filename for r in skipped)
```

## Success Criteria

### Test Implementation Complete When:
* [x] All critical scenarios have tests (6 acceptance tests)
* [x] Coverage targets are met per component (90%+ unit, 80%+ integration)
* [x] All edge cases are tested
* [x] Error paths are validated
* [x] Tests follow codebase conventions (see test_scaffolds.py)
* [x] Tests are maintainable and clear
* [x] CI/CD integration is working (`uv run pytest`)

### Test Quality Indicators:
* Tests are readable and self-documenting (clear docstrings)
* Tests are fast and reliable (no flakiness - use tmp_path, not real fs)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem (specific assertions)
* Mock/stub usage is appropriate and minimal (only for external deps)

## Implementation Guidance

### For TDD Components:
1. Start with simplest test case (e.g., empty input)
2. Write minimal code to pass
3. Add next test case (happy path)
4. Add critical safety tests early (file preservation)
5. Add edge cases and error scenarios
6. Refactor when all tests pass
7. Focus on behavior, not implementation

### Test File Organization:
```
tests/
├── test_prompt_sync.py              # Unit tests (TDD)
│   ├── TestSyncPromptFiles          # sync_prompt_files() tests
│   ├── TestGetPromptMappings        # get_prompt_mappings() tests
│   ├── TestValidatePromptFiles      # validate_prompt_files() tests
│   └── TestDetectOrphanedPrompts    # detect_orphaned_prompts() tests
├── test_prompt_sync_acceptance.py   # Acceptance tests (AT-001 through AT-006)
│   └── TestPromptSyncAcceptance     # @pytest.mark.acceptance
└── test_cli.py                      # Extend with CLI integration tests
```

### Running Tests:
```bash
# Run unit tests only (default, excludes acceptance)
uv run pytest tests/test_prompt_sync.py

# Run acceptance tests
uv run pytest tests/test_prompt_sync_acceptance.py -m acceptance

# Run with coverage
uv run pytest tests/test_prompt_sync.py --cov=src/teambot/prompt_sync --cov-report=term-missing

# Run all tests
uv run pytest
```

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures file safety invariants are validated before code is written
* High test coverage catches edge cases early
* Tests serve as documentation of expected behavior
* Refactoring is safe with comprehensive test suite

### Accepted Trade-offs:
* Initial development pace is slower (writing tests first)
* Test infrastructure needs to be set up for new module
* May need to refactor tests if implementation approach changes

### Risk Mitigation:
* R-001 (Users unaware): Tests validate sync summary display
* R-002 (False positives in orphan): Tests validate pattern matching
* R-004 (Breaking stages.yaml): Tests validate graceful YAML error handling
* R-005 (Permission issues): Tests validate error message includes file path

## References

* **Feature Spec**: [.teambot/sdd-prompt-sync/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/sdd-prompt-sync/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: `tests/test_scaffolds.py`, `tests/test_scaffold_acceptance_validation.py`
* **Test Standards**: `pyproject.toml` [tool.pytest.ini_options]

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate TDD approach into implementation phases
4. 🔍 Implementation will follow TDD per component with 90%+ coverage targets

---

**Strategy Status**: APPROVED
**Approved By**: Builder-2 Agent
**Ready for Planning**: YES

---

## TEST_STRATEGY_VALIDATION: PASS

| Check | Status |
|-------|--------|
| Document | CREATED |
| Decision Matrix | COMPLETE |
| Approach | **TDD** (score 8, threshold 6) |
| Coverage Targets | SPECIFIED (90%+ unit, 80%+ integration) |
| Components Covered | 5/5 |
| Acceptance Tests Mapped | 6/6 (AT-001 through AT-006) |
| Example Patterns | INCLUDED (test_scaffolds.py) |
