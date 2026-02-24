<!-- markdownlint-disable-file -->
# Task Details: Worktree Workflow Enhancement

## Research Reference

**Source Research**: .agent-tracking/research/20260224-worktree-workflow-enhancement-research.md
**Test Strategy**: .teambot/worktree-workflow-enhancement/artifacts/test_strategy.md
**Feature Spec**: .teambot/worktree-workflow-enhancement/artifacts/feature_spec.md

---

## Phase 1: TDD Tests - CLI Parser (`--base-branch`)

### Task 1.1: Write tests for `--base-branch` argument parsing

Write failing tests for the new `--base-branch` CLI argument before implementing it.

* **Files**:
  * `tests/test_cli.py` - Add new test class or extend existing parser tests

* **Test Cases to Implement**:
  ```python
  class TestBaseBranchArgument:
      """Tests for --base-branch CLI argument."""
      
      def test_parser_accepts_base_branch_argument(self):
          """Parser accepts --base-branch with branch name."""
          # Parse: ["run", "obj.md", "--worktree", "--base-branch", "main"]
          # Assert: args.base_branch == "main"
      
      def test_parser_base_branch_defaults_to_none(self):
          """Parser defaults --base-branch to None when not specified."""
          # Parse: ["run", "obj.md", "--worktree"]
          # Assert: args.base_branch is None
      
      def test_parser_base_branch_requires_worktree_flag(self):
          """--base-branch has no effect without --worktree (document behavior)."""
          # Parse: ["run", "obj.md", "--base-branch", "main"]
          # Assert: args.base_branch == "main" (still parsed, just unused)
  ```

* **Success**:
  * Tests are written and initially fail (RED state)
  * Tests follow existing patterns in `tests/test_cli.py`
  * Tests use existing fixtures and mocking patterns

* **Research References**:
  * .agent-tracking/research/20260224-worktree-workflow-enhancement-research.md (Lines 309-319) - CLI argument pattern
  * tests/test_cli.py - Existing parser test patterns

* **Dependencies**:
  * None - first task in TDD cycle

---

## Phase 2: TDD Tests - WorktreeManager Enhancement

### Task 2.1: Write tests for `create_worktree()` with `base_branch` parameter

Write failing tests for the `base_branch` parameter before modifying `WorktreeManager`.

* **Files**:
  * `tests/test_worktree/test_manager.py` - Add tests to existing `TestCreateWorktree` class

* **Test Cases to Implement**:
  ```python
  def test_create_worktree_with_base_branch(self, tmp_path, mocker, mock_git_version_check):
      """Creates worktree from specified base branch."""
      mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
      mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
      mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
      
      WorktreeManager.create_worktree(tmp_path, "feat/task", base_branch="main")
      
      # Assert git command includes "main" at the end
      call_args = mock_run.call_args[0][0]
      assert call_args[-1] == "main"  # base_branch appended
  
  def test_create_worktree_base_branch_none_preserves_behavior(self, tmp_path, mocker, mock_git_version_check):
      """When base_branch is None, git command unchanged (backward compatible)."""
      mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
      mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
      mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
      
      WorktreeManager.create_worktree(tmp_path, "feat/task")
      
      # Assert git command does NOT end with a branch name
      call_args = mock_run.call_args[0][0]
      assert call_args == ["git", "worktree", "add", "-b", "feat/task", str(tmp_path / ".teambot-worktrees" / "feat-task")]
  ```

* **Success**:
  * Tests fail because `base_branch` parameter doesn't exist yet
  * Tests follow existing patterns in `tests/test_worktree/test_manager.py`

* **Research References**:
  * .agent-tracking/research/20260224-worktree-workflow-enhancement-research.md (Lines 257-273) - Git command modification
  * tests/test_worktree/test_manager.py (Lines 1-220) - Existing test patterns

* **Dependencies**:
  * None - parallel with Phase 1

---

### Task 2.2: Write tests for invalid base branch error handling

Write tests to verify error handling when an invalid base branch is specified.

* **Files**:
  * `tests/test_worktree/test_manager.py` - Add error handling tests

* **Test Cases to Implement**:
  ```python
  def test_create_worktree_invalid_base_branch_raises_error(self, tmp_path, mocker, mock_git_version_check):
      """Raises WorktreeError when base branch doesn't exist."""
      mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
      mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
      mock_run.return_value = MagicMock(
          returncode=128,
          stdout="",
          stderr="fatal: invalid reference: nonexistent"
      )
      
      with pytest.raises(WorktreeError) as exc_info:
          WorktreeManager.create_worktree(tmp_path, "feat/task", base_branch="nonexistent")
      
      assert "Base branch not found" in str(exc_info.value) or "nonexistent" in str(exc_info.value)
  ```

* **Success**:
  * Test fails because error handling not yet implemented
  * Error message is user-friendly and includes branch name

* **Research References**:
  * .agent-tracking/research/20260224-worktree-workflow-enhancement-research.md (Lines 417-426) - Error handling pattern
  * src/teambot/worktree/errors.py - Existing exception hierarchy

* **Dependencies**:
  * Task 2.1 (builds on same test class)

---

## Phase 3: TDD Tests - Objective File Migration

### Task 3.1: Write tests for missing objective file detection

Write tests for detecting when objective file is missing in worktree.

* **Files**:
  * `tests/test_cli.py` - Integration tests for cmd_run behavior
  * OR `tests/test_worktree/test_objective_migration.py` - New module for focused unit tests

* **Test Cases to Implement**:
  ```python
  class TestObjectiveFileMigration:
      """Tests for objective file migration to worktree."""
      
      def test_detects_missing_objective_in_worktree(self, tmp_path):
          """Returns True when objective file missing in worktree."""
          worktree = tmp_path / "worktree"
          worktree.mkdir()
          objective_path = Path("objectives/task.md")  # relative
          
          # File doesn't exist in worktree
          result = _detect_missing_objective(objective_path, worktree)
          assert result is True
      
      def test_detects_existing_objective_in_worktree(self, tmp_path):
          """Returns False when objective file exists in worktree."""
          worktree = tmp_path / "worktree"
          worktree.mkdir()
          objective_file = worktree / "objectives" / "task.md"
          objective_file.parent.mkdir(parents=True)
          objective_file.write_text("# Task")
          
          result = _detect_missing_objective(Path("objectives/task.md"), worktree)
          assert result is False
  ```

* **Success**:
  * Tests fail because `_detect_missing_objective` doesn't exist
  * Tests cover both True and False cases

* **Research References**:
  * .agent-tracking/research/20260224-worktree-workflow-enhancement-research.md (Lines 476-490) - Detection logic
  * .teambot/worktree-workflow-enhancement/artifacts/test_strategy.md (Lines 82-100) - Component 1 tests

* **Dependencies**:
  * None - parallel with Phases 1-2

---

### Task 3.2: Write tests for objective file copy operation

Write tests for copying objective file from source to worktree.

* **Files**:
  * `tests/test_cli.py` or `tests/test_worktree/test_objective_migration.py`

* **Test Cases to Implement**:
  ```python
  def test_copies_objective_with_identical_content(self, tmp_path):
      """File content is byte-for-byte identical after copy."""
      source_dir = tmp_path / "source"
      worktree_dir = tmp_path / "worktree"
      source_dir.mkdir()
      worktree_dir.mkdir()
      
      source_file = source_dir / "objectives" / "task.md"
      source_file.parent.mkdir(parents=True)
      content = "# Objective\n\n## Goals\n- Goal 1\n- Goal 2"
      source_file.write_text(content)
      
      _copy_objective_to_worktree(
          source_path=source_file,
          dest_path=worktree_dir / "objectives" / "task.md",
          repo_root=source_dir
      )
      
      dest_file = worktree_dir / "objectives" / "task.md"
      assert dest_file.exists()
      assert dest_file.read_text() == content
  
  def test_copy_creates_parent_directories(self, tmp_path):
      """Parent directories created if they don't exist."""
      source_dir = tmp_path / "source"
      worktree_dir = tmp_path / "worktree"
      source_dir.mkdir()
      worktree_dir.mkdir()
      # Note: objectives/features/ doesn't exist in worktree yet
      
      source_file = source_dir / "objectives" / "features" / "task.md"
      source_file.parent.mkdir(parents=True)
      source_file.write_text("# Nested Task")
      
      _copy_objective_to_worktree(
          source_path=source_file,
          dest_path=worktree_dir / "objectives" / "features" / "task.md",
          repo_root=source_dir
      )
      
      assert (worktree_dir / "objectives" / "features" / "task.md").exists()
  ```

* **Success**:
  * Tests fail because `_copy_objective_to_worktree` doesn't exist
  * Tests verify content integrity and directory creation

* **Research References**:
  * .agent-tracking/research/20260224-worktree-workflow-enhancement-research.md (Lines 275-280) - File copy pattern from scaffolds.py
  * .teambot/worktree-workflow-enhancement/artifacts/test_strategy.md (Lines 103-127) - Component 2 tests

* **Dependencies**:
  * Task 3.1

---

### Task 3.3: Write tests for edge cases

Write tests for edge cases: file already exists, file not found anywhere, logging.

* **Files**:
  * `tests/test_cli.py` or `tests/test_worktree/test_objective_migration.py`

* **Test Cases to Implement**:
  ```python
  def test_no_copy_when_file_exists_in_worktree(self, tmp_path, mocker):
      """No copy operation when file already exists in worktree."""
      worktree_dir = tmp_path / "worktree"
      worktree_dir.mkdir()
      objective_file = worktree_dir / "objectives" / "task.md"
      objective_file.parent.mkdir(parents=True)
      objective_file.write_text("# Already exists")
      
      mock_copy = mocker.patch("shutil.copy2")
      
      # Function should detect file exists and skip copy
      # (Implementation decides exact behavior)
      
      mock_copy.assert_not_called()
  
  def test_error_when_file_not_found_anywhere(self, tmp_path, capsys):
      """Clear error message when file not in source or worktree."""
      source_dir = tmp_path / "source"
      worktree_dir = tmp_path / "worktree"
      source_dir.mkdir()
      worktree_dir.mkdir()
      
      # File doesn't exist in either location
      result = _migrate_objective_file(
          objective_path=Path("objectives/missing.md"),
          source_repo=source_dir,
          worktree_path=worktree_dir
      )
      
      assert result is False  # or raises appropriate error
      # Verify error message includes file path
  
  def test_logs_info_when_file_copied(self, tmp_path, caplog):
      """INFO log message when file is copied."""
      import logging
      caplog.set_level(logging.INFO)
      
      # Setup source and worktree
      # Copy file
      # Assert log contains source and dest paths
  ```

* **Success**:
  * Tests fail because migration functions don't exist
  * All edge cases documented in research are covered

* **Research References**:
  * .agent-tracking/research/20260224-worktree-workflow-enhancement-research.md (Lines 533-541) - Edge cases table
  * .teambot/worktree-workflow-enhancement/artifacts/test_strategy.md (Lines 153-170) - Component 4 tests

* **Dependencies**:
  * Task 3.2

---

## Phase 4: Implementation

### Task 4.1: Add `--base-branch` CLI argument

Implement the `--base-branch` CLI argument in argparse configuration.

* **Files**:
  * `src/teambot/cli.py` - Add argument near existing `--branch` argument (~L402-408)

* **Implementation**:
  ```python
  # Add after existing --branch argument (around line 408)
  run_parser.add_argument(
      "--base-branch",
      type=str,
      default=None,
      metavar="BRANCH",
      help="Branch to base the worktree on (default: current HEAD)",
  )
  ```

* **Success**:
  * Phase 1 tests pass (GREEN state)
  * `teambot run --help` shows `--base-branch` option
  * Backward compatible: existing commands unchanged

* **Research References**:
  * .agent-tracking/research/20260224-worktree-workflow-enhancement-research.md (Lines 377-386) - CLI argument pattern

* **Dependencies**:
  * Phase 1 complete (tests written)

---

### Task 4.2: Add `base_branch` parameter to `WorktreeManager.create_worktree()`

Modify the `create_worktree()` method to accept and use `base_branch` parameter.

* **Files**:
  * `src/teambot/worktree/manager.py` - Modify method signature and git command

* **Implementation Steps**:

  1. **Update method signature** (L156-161):
  ```python
  @classmethod
  def create_worktree(
      cls,
      repo_root: Path,
      branch_name: str,
      base_dir: str = WORKTREE_BASE_DIR,
      base_branch: str | None = None,  # NEW parameter
  ) -> WorktreeContext:
  ```

  2. **Modify git command** (~L199-204):
  ```python
  cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_path)]
  if base_branch:
      cmd.append(base_branch)
  result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_root)
  ```

  3. **Add error handling for invalid base branch** (~L206-216):
  ```python
  if result.returncode != 0:
      stderr = result.stderr.strip()
      if "already exists" in stderr:
          raise BranchExistsError(branch_name)
      if "invalid reference" in stderr or "not a valid ref" in stderr:
          raise WorktreeError(f"Base branch not found: {base_branch}")
      raise WorktreeError(f"Failed to create worktree: {stderr}")
  ```

* **Success**:
  * Phase 2 tests pass (GREEN state)
  * `git worktree add -b <new> <path> <base>` command generated correctly
  * Error handling works for invalid base branch

* **Research References**:
  * .agent-tracking/research/20260224-worktree-workflow-enhancement-research.md (Lines 388-426) - Implementation details

* **Dependencies**:
  * Phase 2 complete (tests written)

---

### Task 4.3: Implement objective file copy logic in `cmd_run()`

Add objective file migration logic to `cmd_run()` after worktree creation.

* **Files**:
  * `src/teambot/cli.py` - Add copy logic after `os.chdir()` (~L641)

* **Implementation Steps**:

  1. **Add import at top of file**:
  ```python
  import shutil
  ```

  2. **Pass base_branch to create_worktree** (~L636):
  ```python
  worktree_context = WorktreeManager.create_worktree(
      repo_root,
      branch_name,
      base_branch=getattr(args, "base_branch", None),
  )
  ```

  3. **Add file copy logic after chdir** (after L641):
  ```python
  # After: os.chdir(worktree_context.worktree_path)
  
  # Check if objective exists in worktree
  worktree_objective = Path(args.objective)
  if not worktree_objective.exists():
      # Check if objective exists in source repo (working directory)
      source_objective = repo_root / args.objective
      if source_objective.exists():
          # Create parent directories if needed
          worktree_objective.parent.mkdir(parents=True, exist_ok=True)
          # Copy file to worktree
          shutil.copy2(source_objective, worktree_objective)
          display.print_success(f"Copied objective file to worktree: {args.objective}")
      else:
          display.print_error(f"Objective file not found: {args.objective}")
          display.print_warning("File must exist in source repository or worktree")
          return 1
  ```

  4. **Remove or modify redundant pre-worktree check** (L627-630):
  ```python
  # REMOVE or MODIFY: This check is now handled after copy attempt
  # if not objective_path.exists():
  #     display.print_error(f"Objective file not found: {objective_path}")
  #     return 1
  ```
  
  Note: Keep validation that objective argument is provided, remove file existence check.

* **Success**:
  * Phase 3 tests pass (GREEN state)
  * Objective file copied when missing in worktree
  * Parent directories created automatically
  * Clear error when file doesn't exist anywhere

* **Research References**:
  * .agent-tracking/research/20260224-worktree-workflow-enhancement-research.md (Lines 472-520) - Complete implementation details

* **Dependencies**:
  * Tasks 4.1, 4.2, Phase 3 complete

---

### Task 4.4: Add logging for file copy operations

Ensure proper logging/output for file copy operations.

* **Files**:
  * `src/teambot/cli.py` - Use existing `display` object for output

* **Implementation**:
  The `display.print_success()` call in Task 4.3 handles this, but verify:
  
  ```python
  # Success message (already in Task 4.3)
  display.print_success(f"Copied objective file to worktree: {args.objective}")
  
  # Optional: Add debug logging
  import logging
  logger = logging.getLogger(__name__)
  logger.debug(f"Copied objective from {source_objective} to {worktree_objective}")
  ```

* **Success**:
  * User sees clear message when file is copied
  * No message when file already exists (normal operation)
  * Error message when file not found anywhere

* **Research References**:
  * .agent-tracking/research/20260224-worktree-workflow-enhancement-research.md (Lines 485-490) - Logging pattern
  * .teambot/worktree-workflow-enhancement/artifacts/test_strategy.md (Lines 153-170) - Logging tests

* **Dependencies**:
  * Task 4.3

---

## Phase 5: Acceptance Tests & Coverage Validation

### Task 5.1: Write acceptance tests AT-001 through AT-006

Write end-to-end acceptance tests validating complete workflow.

* **Files**:
  * `tests/test_worktree_enhancement_acceptance.py` - New file for acceptance tests

* **Test Scenarios** (from feature spec):

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
      
      def test_at_001_committed_objective_copied_to_worktree(self, temp_git_repo):
          """AT-001: Committed objective file copied to worktree when missing."""
          # Setup, act, assert per feature spec AT-001
      
      def test_at_002_staged_objective_copied_from_working_dir(self, temp_git_repo):
          """AT-002: Staged but uncommitted objective file copied."""
          # Setup, act, assert per feature spec AT-002
      
      def test_at_003_base_branch_creates_from_specified_branch(self, temp_git_repo):
          """AT-003: --base-branch main creates worktree from main."""
          # Setup, act, assert per feature spec AT-003
      
      def test_at_004_invalid_base_branch_shows_error(self, temp_git_repo):
          """AT-004: Non-existent base branch produces clear error."""
          # Setup, act, assert per feature spec AT-004
      
      def test_at_005_existing_file_not_overwritten(self, temp_git_repo):
          """AT-005: No copy when objective already exists in worktree."""
          # Setup, act, assert per feature spec AT-005
      
      def test_at_006_nested_path_handles_subdirectories(self, temp_git_repo):
          """AT-006: Subdirectories created correctly for nested paths."""
          # Setup, act, assert per feature spec AT-006
  ```

* **Success**:
  * All 6 acceptance tests pass
  * Tests use real Git operations (not mocked)
  * Tests are marked with `@pytest.mark.acceptance`

* **Research References**:
  * .teambot/worktree-workflow-enhancement/artifacts/feature_spec.md (Lines 313-373) - AT scenarios
  * .teambot/worktree-workflow-enhancement/artifacts/test_strategy.md (Lines 316-354) - Acceptance test patterns
  * tests/test_worktree_acceptance.py - Existing patterns

* **Dependencies**:
  * Phase 4 complete

---

### Task 5.2: Validate test coverage meets 80%+ target

Run coverage report and verify targets are met.

* **Files**:
  * No new files - validation task

* **Validation Steps**:
  
  1. Run full test suite with coverage:
  ```bash
  uv run pytest --cov=src/teambot --cov-report=term-missing
  ```
  
  2. Check coverage on modified files:
  ```bash
  uv run pytest --cov=src/teambot/cli --cov=src/teambot/worktree/manager --cov-report=term-missing
  ```
  
  3. Verify coverage targets:
  - Overall: maintain existing coverage level
  - New code in `cli.py`: ≥80%
  - New code in `manager.py`: ≥80%

* **Success**:
  * Coverage report shows ≥80% on new code
  * All existing tests still pass (no regressions)
  * `uv run pytest` exits with code 0

* **Research References**:
  * .teambot/worktree-workflow-enhancement/artifacts/test_strategy.md (Lines 191-211) - Coverage targets
  * pyproject.toml (Lines 53-63) - pytest configuration

* **Dependencies**:
  * Task 5.1

---

## Dependencies

* Python 3.11+ (already in project requirements)
* pytest 7.4.0+ with pytest-cov, pytest-mock (already in dev dependencies)
* Git CLI 2.5+ (existing validation in worktree manager)
* pathlib and shutil (Python stdlib)

## Success Criteria

* All TDD tests written and passing (Phases 1-4)
* All acceptance tests passing (Phase 5)
* Test coverage ≥80% on new code
* Existing test suite passes (backward compatibility)
* `--base-branch` option documented in `--help` output
* Clear user feedback when objective file is copied
* Cross-platform path handling with pathlib
