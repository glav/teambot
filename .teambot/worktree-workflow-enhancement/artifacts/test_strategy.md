<!-- markdownlint-disable-file -->
# Test Strategy: Worktree Workflow Enhancement

**Strategy Date**: 2026-02-24
**Feature Specification**: .teambot/worktree-workflow-enhancement/artifacts/feature_spec.md
**Research Reference**: N/A (no research document produced for this feature)
**Strategist**: Test Strategy Agent (Builder-2)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | TDD Points | Code-First Points | Rationale |
|--------|----------|-------|------------|-------------------|-----------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES | 3 | 0 | 8 FRs with detailed acceptance criteria, 6 acceptance test scenarios defined |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM | 2 | 0 | File copy logic is simple, but cross-platform path handling and Git worktree integration requires careful handling |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | HIGH | 3 | 0 | Worktree creation failure can corrupt developer workflows; file copy must preserve content integrity |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO | 0 | 0 | Well-defined enhancement to existing functionality |
| **Simplicity** | Is this straightforward CRUD or simple logic? | PARTIAL | 0 | 1 | Core file copy is simple, but edge cases with staged files require care |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO | 0 | 0 | Quality is prioritized; user specified TDD preference |
| **Requirements Stability** | Are requirements likely to change during development? | NO | 0 | 0 | Requirements are finalized and approved in spec review |

### Score Summary

| Category | Score |
|----------|-------|
| **TDD Score** | 8 |
| **Code-First Score** | 1 |

### Decision Thresholds

| TDD Score | Code-First Score | Recommendation |
|-----------|------------------|----------------|
| ≥ 6 | < 4 | **TDD** |
| < 4 | ≥ 5 | Code-First |
| 4-5 | 4-5 | Hybrid |

**Decision: TDD (score 8 >> threshold 6)**

## Recommended Testing Approach

**Primary Approach**: TDD (Test-Driven Development)

### Rationale

The Worktree Workflow Enhancement feature is well-suited for TDD due to three key factors:

1. **Clear Requirements**: The specification defines 8 functional requirements with precise acceptance criteria, and 6 acceptance test scenarios (AT-001 through AT-006). This clarity allows writing tests before implementation.

2. **High Risk Profile**: Worktree operations touch Git internals and file systems. A bug in file copying could corrupt objective files or cause silent workflow failures. TDD provides a safety net for these critical operations.

3. **User Preference**: The objective explicitly states "Testing Preference: TDD - Write tests first, then implement", which aligns with the scoring outcome.

**Key Factors:**
* Complexity: MEDIUM (cross-platform paths, Git integration)
* Risk: HIGH (file integrity, workflow disruption)
* Requirements Clarity: CLEAR (8 FRs with acceptance criteria)
* Time Pressure: LOW (quality prioritized)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: LOW - Core operations are file existence checks and `shutil.copy2` calls
* **Integration Depth**: MEDIUM - Integrates with Git CLI, worktree manager, CLI argument parsing
* **State Management**: LOW - Stateless file operations; no workflow state affected
* **Error Scenarios**: MEDIUM - Must handle missing files, permission errors, cross-platform paths

### Risk Profile
* **Business Criticality**: HIGH - Worktree is a key productivity feature for parallel development
* **User Impact**: HIGH - All worktree users affected; failures block development workflows
* **Data Sensitivity**: LOW - Objective files are user-generated project documentation, not PII
* **Failure Cost**: MEDIUM - File copy failures are recoverable but cause workflow disruption

### Requirements Clarity
* **Specification Completeness**: COMPLETE - All FRs defined with acceptance criteria
* **Acceptance Criteria Quality**: PRECISE - 6 detailed acceptance test scenarios with verification steps
* **Edge Cases Identified**: 5 documented (staged files, subdirectories, cross-platform, missing branch, existing file)
* **Dependencies Status**: STABLE - Git CLI and pathlib are well-understood dependencies

## Test Strategy by Component

### Component 1: Objective File Detection (FR-001) - TDD

**Approach**: TDD
**Rationale**: Simple boolean check with clear expected behavior; test cases are obvious from specification.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * File exists in worktree → returns True, no copy needed
  * File missing in worktree → returns False, triggers copy
* Edge Cases:
  * Path with subdirectories (e.g., `objectives/features/task.md`)
  * Relative vs absolute path handling after `os.chdir()`

**Testing Sequence** (TDD):
1. Write test for file exists case → expect no copy triggered
2. Write test for file missing case → expect copy triggered
3. Implement minimal `_detect_missing_objective()` function
4. Refactor: extract path resolution logic

### Component 2: Objective File Copy (FR-002, FR-003, FR-008) - TDD

**Approach**: TDD
**Rationale**: File integrity is critical; tests ensure byte-for-byte correctness and parent directory creation.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit, Integration (with real filesystem in tmp_path)
* Critical Scenarios:
  * Copy committed file from source repo to worktree
  * Copy staged (uncommitted) file using working directory content
  * Create parent directories if they don't exist
* Edge Cases:
  * File with Unicode content
  * File with special characters in path
  * Empty objective file
  * Large file (>1MB - verify no size limit)

**Testing Sequence** (TDD):
1. Write test: copy simple file → verify content matches
2. Write test: copy file with subdirectory → verify parent dirs created
3. Write test: copy staged file (working directory version) → verify latest content
4. Implement `_copy_objective_to_worktree()` function
5. Refactor for error handling (permission errors, disk full)

### Component 3: --base-branch CLI Option (FR-005, FR-006, FR-007) - TDD

**Approach**: TDD
**Rationale**: CLI argument parsing is straightforward; branch validation has clear success/failure paths.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit (parser tests), Integration (Git operations)
* Critical Scenarios:
  * `--base-branch main` specified → worktree branches from main
  * Invalid branch name → clear error message, no worktree created
  * No `--base-branch` → current behavior preserved (branch from HEAD)
* Edge Cases:
  * Branch name with `/` (e.g., `feature/base`)
  * Remote tracking branch name (should fail - out of scope)

**Testing Sequence** (TDD):
1. Write test: parser accepts `--base-branch` argument
2. Write test: `--base-branch` defaults to None
3. Write test: branch validation rejects non-existent branch
4. Write test: worktree created from specified base branch
5. Implement CLI option and branch validation
6. Refactor to integrate with WorktreeManager

### Component 4: Logging and Output (FR-004) - TDD

**Approach**: TDD
**Rationale**: Log messages are part of user contract; tests ensure consistent messaging.

**Test Requirements:**
* Coverage Target: 80%
* Test Types: Unit (with log capture)
* Critical Scenarios:
  * File copied → INFO log with source and destination paths
  * File already exists → No copy log message
* Edge Cases:
  * Very long path names in log message

**Testing Sequence** (TDD):
1. Write test: copy operation logs INFO message
2. Write test: log message includes source and destination paths
3. Write test: no log when file already exists
4. Implement logging in copy function

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: As specified in pyproject.toml dev dependencies
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `pytest-mock` (mocker fixture) - Mock subprocess calls, filesystem operations
* **Assertions**: pytest built-in assertions with descriptive messages
* **Coverage**: `pytest-cov` - Target: ≥80% on new code
* **Test Data**: pytest `tmp_path` fixture for isolated filesystem operations
* **Async**: `pytest-asyncio` (not required for this feature - sync operations only)

### Test Organization
* **Test Location**: `tests/test_worktree/` for unit tests, `tests/test_worktree_enhancement_acceptance.py` for acceptance tests
* **Naming Convention**: `test_<function>_<scenario>` for unit tests, `test_at_xxx_<description>` for acceptance tests
* **Fixture Strategy**: Use existing `conftest.py` fixtures; add `temp_git_repo` fixture for real Git operations
* **Setup/Teardown**: pytest `tmp_path` fixture handles cleanup automatically

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% (minimum on new code)
* **Integration Coverage**: 80%
* **Critical Path Coverage**: 100% (file copy, branch validation)
* **Error Path Coverage**: 85%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| Objective detection (`_detect_missing_objective`) | 95% | N/A | CRITICAL | Must never give false positive |
| File copy (`_copy_objective_to_worktree`) | 95% | 90% | CRITICAL | Data integrity |
| `--base-branch` CLI option | 90% | 80% | HIGH | User-facing feature |
| Branch validation | 90% | 85% | HIGH | Error handling quality |
| Logging | 80% | N/A | MEDIUM | User feedback |
| Backward compatibility | N/A | 100% | CRITICAL | Regression prevention |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **AT-001: Copy Committed Objective File** (Priority: CRITICAL)
   * **Description**: Committed objective file is copied to worktree when missing
   * **Test Type**: Acceptance (real Git operations)
   * **Success Criteria**: File exists in worktree with identical content (hash match)
   * **Test Approach**: TDD - write test first in `test_worktree_enhancement_acceptance.py`

2. **AT-002: Copy Staged Objective File** (Priority: CRITICAL)
   * **Description**: Staged but uncommitted objective file is copied from working directory
   * **Test Type**: Acceptance (real Git operations)
   * **Success Criteria**: Worktree contains working directory version, not index version
   * **Test Approach**: TDD - create file, stage, verify copy uses filesystem content

3. **AT-003: Base Branch Specification** (Priority: HIGH)
   * **Description**: `--base-branch main` creates worktree from main branch
   * **Test Type**: Acceptance (real Git operations)
   * **Success Criteria**: `git merge-base` confirms correct ancestry
   * **Test Approach**: TDD - setup repo with multiple branches, verify ancestry

4. **AT-004: Invalid Base Branch Error** (Priority: HIGH)
   * **Description**: Non-existent base branch produces clear error
   * **Test Type**: Unit + Acceptance
   * **Success Criteria**: Non-zero exit code, no worktree created, error message includes branch name
   * **Test Approach**: TDD - mock or real Git to verify error path

5. **AT-005: Backward Compatibility** (Priority: CRITICAL)
   * **Description**: Existing worktree commands work unchanged
   * **Test Type**: Acceptance
   * **Success Criteria**: All existing `test_worktree_acceptance.py` tests pass
   * **Test Approach**: Run existing test suite after implementation

6. **AT-006: Cross-Platform Path Handling** (Priority: HIGH)
   * **Description**: Subdirectories created correctly with platform-appropriate separators
   * **Test Type**: Unit + Integration
   * **Success Criteria**: `objectives/features/task.md` structure preserved in worktree
   * **Test Approach**: TDD - use `pathlib` throughout, test with nested paths

### Edge Cases to Cover

* **Empty objective file**: 0-byte file copies without error
* **Large objective file**: 10MB file copies successfully (no size limit enforced)
* **Unicode filename**: `objectives/功能-task.md` handled correctly
* **Symlink in path**: Resolved to canonical path before copy (security)
* **Read-only source**: Copy fails gracefully with clear error
* **Destination exists but different content**: Does not overwrite (skip with log)

### Error Scenarios

* **Permission denied on copy**: Clear error message, no partial file left behind
* **Disk full during copy**: Error caught, partial file cleaned up
* **Git worktree add fails**: Original behavior preserved, no file copy attempted
* **Source file deleted after validation**: Race condition handled gracefully
* **Invalid branch name for --base-branch**: User-friendly error with suggestion

## Test Data Strategy

### Test Data Requirements
* **Git repository**: Created fresh in `tmp_path` per test using `git init`
* **Objective files**: Generated inline with known content for hash verification
* **Branch structure**: Created programmatically with `git checkout -b`

### Test Data Management
* **Storage**: Generated in-memory/tmp_path per test (no committed fixtures)
* **Generation**: Programmatic using subprocess `git` commands
* **Isolation**: Each test gets fresh `tmp_path` directory
* **Cleanup**: Automatic via pytest tmp_path fixture

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_worktree/test_manager.py`
**Pattern**: Unit test with mocking for Git subprocess calls

```python
class TestCreateWorktree:
    """Tests for worktree creation."""

    def test_create_worktree_success(self, tmp_path, mocker, mock_git_version_check):
        """Creates worktree successfully."""
        mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = WorktreeManager.create_worktree(tmp_path, "feat/my-feature")

        assert result.branch_name == "feat/my-feature"
        assert result.worktree_path == tmp_path / ".teambot-worktrees" / "feat-my-feature"
```

**Key Conventions:**
* Use `mocker.patch` for subprocess isolation
* Use `tmp_path` fixture for filesystem isolation
* Assert on return values and side effects
* Descriptive docstrings for each test

### Example from Acceptance Tests

**File**: `tests/test_worktree_acceptance.py`
**Pattern**: Acceptance test with real Git operations

```python
@pytest.fixture
def temp_git_repo(tmp_path: Path):
    """Create a temporary Git repository for testing."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True, check=True)
    (repo / "README.md").write_text("# Test Repository")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, capture_output=True, check=True)
    return repo


@pytest.mark.acceptance
class TestWorktreeEnhancementAcceptance:
    """Acceptance tests for worktree workflow enhancement."""

    def test_at_001_objective_copied_to_worktree(self, temp_git_repo: Path):
        """AT-001: Committed objective file copied to worktree when missing."""
        # Setup: Create and commit objective file
        objectives_dir = temp_git_repo / "objectives"
        objectives_dir.mkdir()
        objective_file = objectives_dir / "task.md"
        objective_file.write_text("# Test Objective\n\nGoals here.")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Add objective"], cwd=temp_git_repo, capture_output=True, check=True)

        # Act: Create worktree (file won't exist initially because worktree branches from HEAD)
        from teambot.worktree import WorktreeManager
        context = WorktreeManager.create_worktree(temp_git_repo, "feat/task")

        # Note: After enhancement, file copy happens in CLI run command, not WorktreeManager
        # This test validates the worktree is created; full acceptance test validates copy

        assert context.worktree_path.exists()
        # After implementation: assert (context.worktree_path / "objectives" / "task.md").exists()
```

### Recommended Test Structure for New Tests

```python
"""Tests for objective file migration in worktree workflow."""

import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestDetectMissingObjective:
    """Tests for detecting missing objective files in worktree."""

    def test_returns_false_when_file_exists(self, tmp_path: Path):
        """Returns False (not missing) when objective exists in worktree."""
        objective = tmp_path / "objectives" / "task.md"
        objective.parent.mkdir(parents=True)
        objective.write_text("# Task")

        from teambot.worktree.objective_migration import detect_missing_objective

        result = detect_missing_objective(objective, tmp_path)
        assert result is False

    def test_returns_true_when_file_missing(self, tmp_path: Path):
        """Returns True (missing) when objective does not exist in worktree."""
        objective = tmp_path / "objectives" / "task.md"

        from teambot.worktree.objective_migration import detect_missing_objective

        result = detect_missing_objective(objective, tmp_path)
        assert result is True


class TestCopyObjectiveToWorktree:
    """Tests for copying objective files to worktree."""

    def test_copies_file_with_identical_content(self, tmp_path: Path):
        """File content is byte-for-byte identical after copy."""
        source_dir = tmp_path / "source"
        worktree_dir = tmp_path / "worktree"
        source_dir.mkdir()
        worktree_dir.mkdir()

        source_file = source_dir / "objectives" / "task.md"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("# Objective Content\n\n## Goals\n- Goal 1")

        from teambot.worktree.objective_migration import copy_objective_to_worktree

        copy_objective_to_worktree(
            source_file, worktree_dir / "objectives" / "task.md", source_dir
        )

        dest_file = worktree_dir / "objectives" / "task.md"
        assert dest_file.exists()
        assert dest_file.read_text() == source_file.read_text()

    def test_creates_parent_directories(self, tmp_path: Path):
        """Parent directories are created if they don't exist."""
        source_dir = tmp_path / "source"
        worktree_dir = tmp_path / "worktree"
        source_dir.mkdir()
        worktree_dir.mkdir()

        source_file = source_dir / "objectives" / "features" / "task.md"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("# Nested Task")

        from teambot.worktree.objective_migration import copy_objective_to_worktree

        copy_objective_to_worktree(
            source_file, worktree_dir / "objectives" / "features" / "task.md", source_dir
        )

        dest_file = worktree_dir / "objectives" / "features" / "task.md"
        assert dest_file.exists()
```

## Success Criteria

### Test Implementation Complete When:
* [ ] All 6 acceptance test scenarios have tests (AT-001 through AT-006)
* [ ] Unit test coverage ≥90% on new code
* [ ] All critical scenarios tested (file copy, branch validation)
* [ ] All edge cases are tested (empty file, Unicode, nested paths)
* [ ] Error paths are validated (permission denied, invalid branch)
* [ ] Tests follow existing codebase conventions (test_worktree/ patterns)
* [ ] Tests are maintainable and self-documenting
* [ ] Existing test suite passes (backward compatibility)

### Test Quality Indicators:
* Tests are readable and self-documenting (descriptive names + docstrings)
* Tests are fast and reliable (no flakiness from real Git operations)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem (specific assertions)
* Mock/stub usage is appropriate and minimal (real Git for acceptance tests)

## Implementation Guidance

### For TDD Components:
1. Start with simplest test case (file exists → no copy)
2. Write minimal code to pass
3. Add next test case (file missing → copy triggered)
4. Refactor when all tests pass
5. Focus on behavior, not implementation details

### TDD Cycle for This Feature:

**Phase 1: CLI Parser Tests**
```bash
# 1. Write failing test
def test_parser_base_branch_flag():
    parser = create_parser()
    args = parser.parse_args(["run", "obj.md", "--base-branch", "main"])
    assert args.base_branch == "main"

# 2. Run test (RED)
uv run pytest tests/test_cli.py::TestCLIParserWorktree -v

# 3. Implement minimal code to pass
# 4. Run test (GREEN)
# 5. Refactor if needed
```

**Phase 2: WorktreeManager Enhancement Tests**
```bash
# 1. Write failing test for base branch support
# 2. Implement WorktreeManager.create_worktree() enhancement
# 3. Write failing test for objective migration
# 4. Implement migration logic
```

**Phase 3: Acceptance Tests**
```bash
# 1. Write AT-001 acceptance test
# 2. Run full integration
# 3. Verify end-to-end behavior
```

### Test File Organization:

```
tests/
├── test_worktree/
│   ├── test_manager.py           # Existing - add base_branch tests
│   ├── test_branch_naming.py     # Existing - no changes needed
│   ├── test_validation.py        # Existing - no changes needed
│   ├── test_errors.py            # Existing - add InvalidBaseBranchError
│   └── test_objective_migration.py  # NEW - TDD tests for file copy
├── test_worktree_acceptance.py   # Existing - add AT-001 through AT-006
└── test_cli.py                   # Existing - add --base-branch parser tests
```

## Considerations and Trade-offs

### Selected Approach Benefits:
* **Regression Safety**: TDD ensures new functionality doesn't break existing worktree features
* **Documentation**: Tests serve as executable specification for new behavior
* **Confidence**: High coverage enables safe refactoring of file copy logic
* **Fast Feedback**: Unit tests run in milliseconds, catching bugs early

### Accepted Trade-offs:
* **Initial Velocity**: Writing tests first takes longer initially but saves debugging time
* **Test Maintenance**: More tests mean more code to maintain, but TDD tests are typically well-scoped
* **Real Git Operations in Acceptance Tests**: Slower than mocking, but provides true integration validation

### Risk Mitigation:
* **Cross-platform issues**: Use `pathlib` throughout; run tests on Linux (CI covers other platforms)
* **Git version differences**: Check minimum Git version (2.5+) before operations
* **Flaky tests**: Use `tmp_path` fixture for isolation; avoid timing-dependent assertions

## References

* **Feature Spec**: [.teambot/worktree-workflow-enhancement/artifacts/feature_spec.md](../../.teambot/worktree-workflow-enhancement/artifacts/feature_spec.md)
* **Spec Review**: [.teambot/worktree-workflow-enhancement/artifacts/spec_review.md](../../.teambot/worktree-workflow-enhancement/artifacts/spec_review.md)
* **Test Examples**: 
  * `tests/test_worktree/test_manager.py` - Unit test patterns
  * `tests/test_worktree_acceptance.py` - Acceptance test patterns with real Git
  * `tests/conftest.py` - Shared fixtures
* **Test Standards**: `pyproject.toml` [tool.pytest.ini_options] for pytest configuration

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate TDD approach into implementation phases:
   - Phase 1: CLI parser tests for `--base-branch`
   - Phase 2: Unit tests for objective migration
   - Phase 3: Acceptance tests AT-001 through AT-006
   - Phase 4: Implementation to make all tests pass
4. 🔍 Implementation will follow strict TDD: RED → GREEN → REFACTOR

---

**Strategy Status**: APPROVED
**Approved By**: PENDING USER CONFIRMATION
**Ready for Planning**: YES

---

## Approval Request

I've analyzed the **Worktree Workflow Enhancement** feature and recommend **TDD** approach.

**Decision Matrix Summary**:
- TDD Score: **8** (threshold: 6)
- Code-First Score: **1** (threshold: 5)

**Key Factors**:
- Clear requirements with 8 FRs and 6 acceptance scenarios
- High risk due to file integrity and Git workflow impact
- User explicitly requested TDD preference

**Coverage Targets**:
- Unit tests: 90%+ on new code
- Acceptance tests: All 6 scenarios (AT-001 through AT-006)

**Do you:**
1. ✅ Approve this strategy and proceed to planning
2. 🔄 Want to adjust the approach (please specify)
3. ❓ Have questions or concerns about the recommendation

---

## Output Validation Checklist

TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE (TDD=8, Code-First=1)
- Approach: TDD (score 8 >> threshold 6)
- Coverage Targets: SPECIFIED (90% unit, 80% integration)
- Components Covered: 4/4 (detection, copy, CLI option, logging)
