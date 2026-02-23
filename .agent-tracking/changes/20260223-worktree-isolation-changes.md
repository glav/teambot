<!-- markdownlint-disable-file -->
# Release Changes: TeamBot Worktree Isolation

**Related Plan**: 20260223-worktree-isolation-plan.instructions.md
**Implementation Date**: 2026-02-23

## Summary

Implementation of Git worktree isolation feature for TeamBot, enabling parallel feature development with automatic Git worktree creation and state file isolation. The feature adds `--worktree` and `--branch` flags to `teambot run`, allowing objectives to execute in isolated Git worktrees with automatic branch creation.

## Changes

### Added

* `src/teambot/worktree/__init__.py` - Module exports for worktree management
* `src/teambot/worktree/errors.py` - Custom exception hierarchy (WorktreeError, GitNotFoundError, BranchExistsError, WorktreeExistsError, GitVersionError, PathTooLongError)
* `src/teambot/worktree/manager.py` - WorktreeManager class with create_worktree(), detect_worktree_context(), derive_branch_name(), validate_path_length(), check_git_version() functions
* `tests/test_worktree/__init__.py` - Test module initialization
* `tests/test_worktree/conftest.py` - Worktree-specific test fixtures (mock_git_subprocess, mock_shutil_which, mock_git_version_check, worktree_context)
* `tests/test_worktree/test_errors.py` - 20 unit tests for error classes
* `tests/test_worktree/test_branch_naming.py` - 16 tests for branch name derivation
* `tests/test_worktree/test_manager.py` - 17 tests for WorktreeManager class
* `tests/test_worktree/test_validation.py` - 17 tests for path length validation and Git version checking
* `tests/test_worktree_acceptance.py` - 10 acceptance tests with real Git operations
* `tests/test_repl/test_worktree_indicator.py` - 3 tests for REPL worktree indicator
* `docs/guides/worktree-isolation.md` - Comprehensive usage guide for worktree isolation feature

### Modified

* `src/teambot/cli.py` - Added --worktree and --branch CLI flags; integrated worktree creation into cmd_run(); updated _run_orchestration() for worktree context in stage headers
* `src/teambot/repl/loop.py` - Added worktree_context parameter to REPLLoop; updated _get_input() for [wt:branch] prompt indicator; updated run_interactive_mode() to pass context
* `tests/test_cli.py` - Added TestCLIParserWorktree (6 tests) and TestCmdRunWorktree (4 tests) classes
* `README.md` - Added Worktree Isolation section and guide link in documentation table

### Removed

(None)

## Release Summary

**Total Files Affected**: 16

### Files Created (12)

* `src/teambot/worktree/__init__.py` - Module exports
* `src/teambot/worktree/errors.py` - Exception hierarchy (6 error classes)
* `src/teambot/worktree/manager.py` - WorktreeManager implementation
* `tests/test_worktree/__init__.py` - Test module
* `tests/test_worktree/conftest.py` - Test fixtures
* `tests/test_worktree/test_errors.py` - Error class tests (20 tests)
* `tests/test_worktree/test_branch_naming.py` - Branch naming tests (16 tests)
* `tests/test_worktree/test_manager.py` - Manager tests (17 tests)
* `tests/test_worktree/test_validation.py` - Validation tests (17 tests)
* `tests/test_worktree_acceptance.py` - Acceptance tests (10 tests)
* `tests/test_repl/test_worktree_indicator.py` - REPL indicator tests (3 tests)
* `docs/guides/worktree-isolation.md` - Usage guide

### Files Modified (4)

* `src/teambot/cli.py` - CLI integration with worktree creation and stage header indicators
* `src/teambot/repl/loop.py` - REPL prompt indicator for worktree context
* `tests/test_cli.py` - CLI worktree tests
* `README.md` - Documentation updates

### Files Removed (0)

(None)

### Dependencies & Infrastructure

* **New Dependencies**: None (uses Python standard library subprocess and platform modules)
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

All 6 phases complete with 93 new tests and 1704 total tests passing at 82% coverage.

**Key Features Implemented**:
- `--worktree` flag creates isolated Git worktree for objective execution
- `--branch` flag allows custom branch naming
- Automatic branch name derivation from objective filename
- Visual indicators in REPL prompt (`[wt:branch]`) and stage headers
- State file isolation (`.teambot/` scoped per worktree)
- Windows path length validation (260-char limit)
- Git version checking (requires 2.5+)
- Clear error messages with actionable guidance
