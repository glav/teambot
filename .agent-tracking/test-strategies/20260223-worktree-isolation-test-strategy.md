<!-- markdownlint-disable-file -->
# Test Strategy: TeamBot Worktree Isolation

**Strategy Date**: 2026-02-23
**Feature Specification**: .teambot/worktree-isolation/artifacts/feature_spec.md
**Research Reference**: .agent-tracking/spec-reviews/20260223-worktree-isolation-review.md
**Strategist**: Builder-2 (Test Strategy)

## Recommended Testing Approach

**Primary Approach**: **TDD** — Test-Driven Development for all components

### Rationale

This feature introduces critical filesystem and Git repository operations that create isolated working environments. Incorrect behavior could corrupt the user's repository state, create orphaned branches, or leave partial worktree directories that require manual cleanup. The clear specification (13 FRs with precise acceptance criteria) and high-risk nature of Git operations strongly favor TDD.

The feature has well-defined requirements with 7 acceptance test scenarios already documented. Each component (worktree creation, branch naming, state isolation, error handling) has explicit expected behaviors that translate directly to test cases. TDD ensures the Git subprocess calls are validated before any real repository operations occur.

Additionally, this is foundational infrastructure for future multi-objective execution—getting the isolation semantics wrong would compound errors in later features. The specification is stable with zero open questions, making TDD's upfront design cost minimal.

**Key Factors:**
* Complexity: **HIGH** — Cross-platform Git operations, path handling, state isolation
* Risk: **CRITICAL** — Repository corruption, orphaned branches, partial state on failure
* Requirements Clarity: **CLEAR** — 13 FRs, 7 acceptance tests, 9 NFRs
* Time Pressure: **LOW** — Foundation feature, quality over speed

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | Points To |
|--------|----------|-------|-----------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | 3 | TDD |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | 3 | TDD |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | 3 | TDD |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | 0 | Code-First |
| **Simplicity** | Is this straightforward CRUD or simple logic? | 0 | Code-First |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | 0 | Code-First |
| **Requirements Stability** | Are requirements likely to change during development? | 0 | Code-First |

**TDD Score: 9** | **Code-First Score: 0**

**Decision**: TDD (score 9 >> threshold 6)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: MEDIUM — Branch name derivation from filenames, path sanitization, length validation
* **Integration Depth**: HIGH — CLI argument parsing, Git subprocess, orchestration execution context, REPL prompt, stage headers
* **State Management**: HIGH — Worktree directory lifecycle, branch state, `.teambot/` isolation, resume context detection
* **Error Scenarios**: HIGH — Git unavailable, branch conflicts, path length limits, creation failures, rollback requirements

### Risk Profile
* **Business Criticality**: CRITICAL — Repository corruption or orphaned state if operations fail partially
* **User Impact**: HIGH — Main working directory protection is the core value proposition
* **Data Sensitivity**: LOW — No PII; only filesystem paths and Git branch names
* **Failure Cost**: HIGH — Orphaned worktrees require manual Git cleanup; failed rollback leaves inconsistent state

### Requirements Clarity
* **Specification Completeness**: COMPLETE — All 13 FRs defined with acceptance criteria
* **Acceptance Criteria Quality**: PRECISE — 7 concrete acceptance test scenarios with verification steps
* **Edge Cases Identified**: 8 documented (branch conflicts, path limits, Git unavailable, nested repos, resume context, etc.)
* **Dependencies Status**: STABLE — Git CLI is external but versioned (2.5+); internal dependencies clearly mapped

## Test Strategy by Component

### Component 1: `WorktreeManager` Core Module — **TDD** 🔴

**Approach**: TDD
**Rationale**: All Git subprocess calls (worktree add, branch create, path validation) must be mocked and verified before real execution. This is the highest-risk component—incorrect commands or missing rollback could corrupt repository state.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit (mocked subprocess)
* Critical Scenarios:
  * `create_worktree(objective, branch)` calls correct Git commands in sequence
  * Worktree path is constructed correctly at `.teambot-worktrees/<branch>/`
  * Branch name derivation from objective filename works correctly
  * Validation rejects existing branches with clear error
  * Rollback removes worktree and branch on creation failure
* Edge Cases:
  * Branch name with special characters (sanitization)
  * Path length approaching 260 chars on Windows
  * Objective filename with `objective-` prefix stripped
  * Worktree directory already exists (conflict)

**Testing Sequence (TDD):**
1. Write test: `test_derive_branch_name_from_objective` → implement name derivation
2. Write test: `test_derive_branch_name_strips_prefix` → handle `objective-` prefix
3. Write test: `test_sanitize_branch_name_special_chars` → implement sanitization
4. Write test: `test_validate_path_length_windows` → implement path validation
5. Write test: `test_check_git_available_success` → implement Git availability check
6. Write test: `test_check_git_available_not_found` → verify error handling
7. Write test: `test_check_branch_exists_true` → implement branch existence check
8. Write test: `test_check_branch_exists_false` → verify non-existent branch
9. Write test: `test_create_worktree_success` → implement full creation flow
10. Write test: `test_create_worktree_branch_conflict` → verify conflict error
11. Write test: `test_create_worktree_rollback_on_failure` → implement rollback

### Component 2: CLI Argument Parsing (`--worktree`, `--branch`) — **TDD** 🔴

**Approach**: TDD
**Rationale**: Argument parsing is well-defined and testable in isolation. The existing `TestCLIParser` class provides an exact template. New flags must not break existing flag combinations.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `teambot run obj.md --worktree` parses with `args.worktree = True`
  * `teambot run obj.md --worktree --branch feat/custom` parses both flags
  * `--branch` without `--worktree` raises error or is ignored (define behavior)
  * Backward compatibility: existing commands parse identically
* Edge Cases:
  * `--worktree` with no objective (interactive mode — define behavior per spec review)
  * `--branch ""` (empty branch name)

**Testing Sequence (TDD):**
1. Write test: `test_parser_worktree_flag` → add `--worktree` argument
2. Write test: `test_parser_worktree_flag_default_false` → verify default
3. Write test: `test_parser_branch_flag` → add `--branch` argument
4. Write test: `test_parser_branch_with_worktree` → verify combination
5. Write test: `test_parser_branch_without_worktree_error` → define and test behavior
6. Write test: `test_parser_backward_compatibility` → verify existing commands unchanged

### Component 3: `cmd_run` Worktree Integration — **TDD** 🔴

**Approach**: TDD
**Rationale**: This is the main orchestration point where worktree mode branches execution flow. Must verify correct sequencing: validation → worktree creation → context switch → execution → preserve worktree.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit (with mocked WorktreeManager and ExecutionLoop)
* Critical Scenarios:
  * `--worktree` triggers WorktreeManager creation before execution
  * Execution runs with `teambot_dir` pointing to worktree's `.teambot/`
  * Main directory's `.teambot/` is never modified
  * Worktree persists after success
  * Worktree persists after failure (no cleanup)
  * Without `--worktree`, behavior is unchanged (regression test)
* Edge Cases:
  * Resume in worktree context detected correctly
  * Objective path resolution from worktree directory

**Testing Sequence (TDD):**
1. Write test: `test_cmd_run_no_worktree_unchanged` → regression baseline
2. Write test: `test_cmd_run_worktree_creates_worktree` → verify WorktreeManager called
3. Write test: `test_cmd_run_worktree_uses_isolated_teambot_dir` → verify path isolation
4. Write test: `test_cmd_run_worktree_persists_after_success` → verify no cleanup
5. Write test: `test_cmd_run_worktree_persists_after_failure` → verify no cleanup
6. Write test: `test_cmd_run_worktree_git_unavailable_error` → verify fast-fail

### Component 4: REPL Prompt Indicator — **TDD** 🔴

**Approach**: TDD
**Rationale**: The prompt modification affects every user interaction in interactive mode. Clear specification (FR-009) with defined output format makes TDD appropriate.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Prompt includes `[feat/branch-name]` when in worktree mode
  * Prompt is unchanged when not in worktree mode
* Edge Cases:
  * Long branch names (truncation?)
  * Branch names with special characters

**Testing Sequence (TDD):**
1. Write test: `test_repl_prompt_without_worktree` → baseline
2. Write test: `test_repl_prompt_with_worktree_context` → implement indicator
3. Write test: `test_repl_prompt_long_branch_name` → define truncation behavior

### Component 5: Stage Header Indicator — **TDD** 🔴

**Approach**: TDD
**Rationale**: File-based orchestration headers must show worktree context (FR-010). Formatting changes are well-defined and low-risk but benefit from TDD for consistency.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Stage header includes `[worktree: feat/branch-name]` when in worktree mode
  * Stage header unchanged when not in worktree mode
* Edge Cases:
  * Header width considerations with long branch names

**Testing Sequence (TDD):**
1. Write test: `test_stage_header_without_worktree` → baseline
2. Write test: `test_stage_header_with_worktree_context` → implement indicator

### Component 6: Error Handling Module — **TDD** 🔴

**Approach**: TDD
**Rationale**: Error messages must be clear and actionable (FR-011, FR-012, FR-013). Each error condition has specified message content.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Git not found → "Git is required for --worktree mode but was not found"
  * Branch exists → "Branch 'feat/foo' already exists. Use --branch to specify a different name"
  * Path too long → Clear guidance on Windows 260-char limit
* Edge Cases:
  * Git version too old (< 2.5)

**Testing Sequence (TDD):**
1. Write test: `test_error_git_not_found` → define error class/message
2. Write test: `test_error_branch_exists` → define conflict error
3. Write test: `test_error_path_too_long` → define path error
4. Write test: `test_error_git_version_too_old` → define version error

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: As specified in pyproject.toml
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest` or `pytest`

### Testing Tools Required
* **Mocking**: `pytest-mock` (MagicMock, patch) — mock subprocess calls to Git
* **Assertions**: Built-in pytest assertions with clear error messages
* **Coverage**: `pytest-cov` — Target: 90%+ for new worktree module
* **Test Data**: Temporary directories via `tmp_path` fixture; mock Git repos

### Test Organization
* **Test Location**: `tests/test_worktree/` (new directory for worktree module)
* **Naming Convention**: `test_*.py`, `Test*` classes, `test_*` functions
* **Fixture Strategy**: Use `conftest.py` fixtures; extend with worktree-specific fixtures
* **Setup/Teardown**: `tmp_path` for isolation; no persistent state

### New Fixtures Required

```python
@pytest.fixture
def mock_git_subprocess(mocker):
    """Mock subprocess.run for Git commands."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="",
        stderr="",
    )
    return mock_run

@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary Git repository for testing."""
    import subprocess
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
    # Create initial commit
    (repo / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo, capture_output=True)
    return repo

@pytest.fixture
def worktree_context():
    """Provide worktree context for tests."""
    return {
        "branch_name": "feat/test-feature",
        "worktree_path": ".teambot-worktrees/feat/test-feature",
        "objective_file": "objectives/test-feature.md",
    }
```

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% (minimum for new worktree module)
* **Integration Coverage**: 80% (CLI integration tests)
* **Critical Path Coverage**: 100% (worktree creation, branch naming, error handling)
* **Error Path Coverage**: 100% (all error conditions explicitly tested)

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| WorktreeManager | 95% | 80% | CRITICAL | Core Git operations |
| CLI parsing | 100% | N/A | CRITICAL | Argument handling |
| cmd_run integration | 90% | 80% | CRITICAL | Orchestration flow |
| REPL prompt | 90% | N/A | HIGH | User visibility |
| Stage headers | 90% | N/A | HIGH | User visibility |
| Error handling | 100% | N/A | CRITICAL | User guidance |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Worktree Creation Happy Path** (Priority: CRITICAL)
   * **Description**: `teambot run obj.md --worktree` creates worktree and runs objective
   * **Test Type**: Integration (mocked subprocess)
   * **Success Criteria**: WorktreeManager called, execution uses worktree `.teambot/`, worktree persists
   * **Test Approach**: TDD

2. **Branch Name Derivation** (Priority: CRITICAL)
   * **Description**: Objective filename correctly derives branch name
   * **Test Type**: Unit
   * **Success Criteria**: `objective-foo.md` → `feat/foo`, `my-feature.md` → `feat/my-feature`
   * **Test Approach**: TDD

3. **Branch Conflict Error** (Priority: CRITICAL)
   * **Description**: Existing branch triggers clear error with guidance
   * **Test Type**: Unit
   * **Success Criteria**: Error message matches FR-012 specification
   * **Test Approach**: TDD

4. **Git Unavailable Error** (Priority: CRITICAL)
   * **Description**: Missing Git triggers fast-fail with clear message
   * **Test Type**: Unit
   * **Success Criteria**: Error message matches FR-011 specification
   * **Test Approach**: TDD

5. **Backward Compatibility** (Priority: CRITICAL)
   * **Description**: Running without `--worktree` behaves exactly as before
   * **Test Type**: Regression
   * **Success Criteria**: All existing `cmd_run` tests pass unchanged
   * **Test Approach**: TDD (baseline first)

6. **State Isolation** (Priority: CRITICAL)
   * **Description**: Worktree `.teambot/` is independent of main directory
   * **Test Type**: Integration
   * **Success Criteria**: Main `.teambot/` unchanged after worktree execution
   * **Test Approach**: TDD

7. **Resume in Worktree Context** (Priority: HIGH)
   * **Description**: `teambot run --resume` from worktree directory works correctly
   * **Test Type**: Integration
   * **Success Criteria**: Resumes from worktree's saved state
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Branch name sanitization**: Spaces → hyphens, special chars removed
* **Path length validation**: 260-char limit on Windows
* **Existing worktree directory**: Conflict detection and error
* **Nested Git repositories**: Detection and warning (per R-003)
* **Uncommitted changes in main**: Behavior documented and tested
* **Empty objective filename**: Validation error
* **`--branch` with invalid characters**: Validation error

### Error Scenarios

* **Git not installed**: Clear error message, no partial state
* **Git version < 2.5**: Clear error message with version requirement
* **Branch already exists**: Error with `--branch` suggestion
* **Worktree creation fails mid-operation**: Rollback cleans up partial state
* **Permission denied on worktree path**: Clear error message
* **Disk full during worktree creation**: Graceful error handling

## Test Data Strategy

### Test Data Requirements
* **Objective files**: Simple markdown content via fixtures
* **Git repositories**: Temporary repos via `temp_git_repo` fixture
* **Branch names**: Parameterized test data for edge cases
* **Path lengths**: Programmatically generated long paths for Windows tests

### Test Data Management
* **Storage**: In-memory fixtures and `tmp_path` directories
* **Generation**: Fixtures create fresh data per test
* **Isolation**: Each test gets isolated `tmp_path`; no shared state
* **Cleanup**: pytest handles `tmp_path` cleanup automatically

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_cli.py`
**Pattern**: Argument parsing tests with clear assertions

```python
class TestCLIParser:
    """Tests for CLI argument parsing."""

    def test_parser_run_command(self):
        """Parser recognizes run command with objective."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "objective.md"])

        assert args.command == "run"
        assert args.objective == "objective.md"
```

**Key Conventions:**
* Test classes group related tests
* Clear docstrings describe test purpose
* Single assertion focus per test
* Import within test for isolation

### Example from Acceptance Tests

**File**: `tests/test_init_scaffolds_acceptance.py`
**Pattern**: Acceptance test with filesystem setup and verification

```python
@pytest.mark.acceptance
class TestInitScaffoldingAcceptance:
    """Acceptance tests matching spec acceptance criteria."""

    def test_at_001_fresh_repository_initialization(self, tmp_path, monkeypatch):
        """AT-001: Fresh init copies all scaffolding files."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / "stages.yaml").exists()
```

### Recommended Test Structure for Worktree Module

```python
"""Tests for worktree management module."""

import pytest
from unittest.mock import MagicMock, patch


class TestBranchNameDerivation:
    """Tests for deriving branch names from objective filenames."""

    @pytest.mark.parametrize("filename,expected", [
        ("my-feature.md", "feat/my-feature"),
        ("objective-foo.md", "feat/foo"),
        ("add-login-page.md", "feat/add-login-page"),
        ("fix-bug-123.md", "feat/fix-bug-123"),
    ])
    def test_derive_branch_name(self, filename, expected):
        """Branch name derived correctly from objective filename."""
        from teambot.worktree.manager import derive_branch_name

        result = derive_branch_name(filename)

        assert result == expected


class TestWorktreeCreation:
    """Tests for worktree creation operations."""

    def test_create_worktree_success(self, mock_git_subprocess, tmp_path):
        """Worktree created successfully with correct Git commands."""
        from teambot.worktree.manager import WorktreeManager

        manager = WorktreeManager(repo_root=tmp_path)
        result = manager.create_worktree("my-feature.md", branch=None)

        assert result.success
        assert result.worktree_path == tmp_path / ".teambot-worktrees" / "feat/my-feature"
        mock_git_subprocess.assert_any_call(
            ["git", "worktree", "add", "-b", "feat/my-feature", str(result.worktree_path)],
            capture_output=True,
            text=True,
        )

    def test_create_worktree_branch_conflict(self, mock_git_subprocess, tmp_path):
        """Branch conflict raises clear error."""
        from teambot.worktree.manager import WorktreeManager, WorktreeError

        mock_git_subprocess.return_value.returncode = 128
        mock_git_subprocess.return_value.stderr = "branch 'feat/my-feature' already exists"

        manager = WorktreeManager(repo_root=tmp_path)

        with pytest.raises(WorktreeError) as exc:
            manager.create_worktree("my-feature.md", branch=None)

        assert "already exists" in str(exc.value)
        assert "--branch" in str(exc.value)
```

## Success Criteria

### Test Implementation Complete When:
* [ ] All critical scenarios have tests (6 CRITICAL, 1 HIGH minimum)
* [ ] Coverage targets met: 90%+ for worktree module
* [ ] All edge cases tested (8 identified)
* [ ] Error paths validated (6 error scenarios)
* [ ] Tests follow codebase conventions (pytest classes, clear docstrings)
* [ ] Tests are maintainable and clear
* [ ] Acceptance tests marked with `@pytest.mark.acceptance`
* [ ] CI integration working (tests pass in pipeline)

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast (< 5s for unit suite, subprocess mocked)
* Tests are reliable (no flakiness, no wall-clock timing assertions)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem (assert messages)
* Mock/stub usage is appropriate (subprocess mocked, not over-mocked)

## Implementation Guidance

### For TDD Components (All):
1. Start with simplest test case (branch name derivation)
2. Write minimal code to pass
3. Add next test case (error handling)
4. Refactor when all tests pass
5. Focus on behavior, not implementation details
6. Mock subprocess.run, not internal methods

### Test File Organization:
```
tests/
├── test_worktree/
│   ├── __init__.py
│   ├── conftest.py              # Worktree-specific fixtures
│   ├── test_manager.py          # WorktreeManager unit tests
│   ├── test_branch_naming.py    # Branch derivation/sanitization
│   ├── test_validation.py       # Error conditions
│   └── test_integration.py      # cmd_run integration
├── test_cli.py                  # Add worktree flag parsing tests
└── test_worktree_acceptance.py  # Acceptance tests with real Git
```

### Acceptance Test Approach:
One acceptance test file exercising real Git operations in a temporary repository:
* Creates actual Git repo with `git init`
* Runs `teambot run --worktree` (or simulates via function call)
* Verifies actual worktree directory exists
* Verifies branch created in repository
* Marked with `@pytest.mark.acceptance` (excluded from default run)

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD catches Git command errors before any real repository operations
* Mocked subprocess tests run fast (no actual Git operations in unit tests)
* Clear test-to-requirement traceability (each FR has corresponding tests)
* Acceptance test validates end-to-end with real Git (catches subprocess API mismatches)

### Accepted Trade-offs:
* More upfront test writing before implementation
* Mock-heavy tests may miss subprocess API changes (mitigated by acceptance test)
* Acceptance test requires Git installed in CI (already true per AGENTS.md)

### Risk Mitigation:
* **Subprocess API mismatches**: Acceptance test with real Git catches these
* **Platform-specific issues**: Parameterized tests for Windows paths; CI matrix if available
* **Flaky tests**: No wall-clock timing assertions; mock subprocess responses deterministically

## References

* **Feature Spec**: [.teambot/worktree-isolation/artifacts/feature_spec.md]
* **Spec Review**: [.agent-tracking/spec-reviews/20260223-worktree-isolation-review.md]
* **Test Examples**: `tests/test_cli.py`, `tests/test_init_scaffolds_acceptance.py`
* **Subprocess Pattern**: `src/teambot/orchestration/review_iterator.py:60-73`
* **Test Standards**: `pyproject.toml` [tool.pytest.ini_options]

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate TDD sequence into implementation phases
4. 🔍 Implementation will follow TDD for all components

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

## 🔐 Approval Request

I have completed the test strategy analysis for **TeamBot Worktree Isolation**.

**Summary:**
- **Approach**: TDD (Score: 9, Code-First: 0)
- **Coverage Target**: 90%+ for new worktree module
- **Components**: 6 (all TDD)
- **Critical Scenarios**: 7
- **Edge Cases**: 8
- **Error Scenarios**: 6

**Decision: TDD for all components**

The feature's high-risk Git operations, clear requirements (13 FRs, 7 acceptance tests), and critical nature of repository state management make TDD the optimal approach.

### ✅ Ready for Task Planning

Please confirm:

- [ ] I have reviewed the test strategy
- [ ] I agree with the TDD approach for all components
- [ ] I approve proceeding to Task Planning phase

**Type "APPROVED" to proceed, or describe any concerns.**

---

## Validation Checklist

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE (TDD: 9, Code-First: 0)
- Approach: TDD (with score justification: 9 >> threshold 6)
- Coverage Targets: SPECIFIED (90% overall, 100% for critical paths)
- Components Covered: 6/6
```
