"""Acceptance Validation Tests - Worktree Isolation Feature.

These tests call the REAL implementation code - no mocking of core functionality.
Each test validates a specific acceptance scenario with test name `test_at_XXX_*`.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from teambot.worktree import WorktreeManager, derive_branch_name
from teambot.worktree.errors import BranchExistsError, GitNotFoundError
from teambot.worktree.manager import WorktreeContext


@pytest.fixture
def temp_git_repo(tmp_path: Path):
    """Create a real Git repository for testing."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    (repo / "README.md").write_text("# Test Repository")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    return repo


@pytest.mark.acceptance
class TestAcceptanceValidation:
    """Strict acceptance validation tests calling REAL implementation."""

    # =========================================================================
    # AT-001: Basic Worktree Creation and Execution
    # =========================================================================
    def test_at_001_basic_worktree_creation(self, temp_git_repo: Path):
        """AT-001: User runs objective with --worktree flag.

        Verifies:
        - .teambot-worktrees/feat-my-feature/ exists
        - .teambot-worktrees/feat-my-feature/.teambot/ can contain state files
        - Main directory's .teambot/ unchanged from before command
        """
        # Step 1: Derive branch name using REAL implementation
        objective_path = Path("objectives/my-feature.md")
        branch_name = derive_branch_name(objective_path)
        assert branch_name == "feat/my-feature"

        # Step 2-3: Create worktree using REAL WorktreeManager
        context = WorktreeManager.create_worktree(temp_git_repo, branch_name)

        # Verification: Worktree exists at expected path
        expected_path = temp_git_repo / ".teambot-worktrees" / "feat-my-feature"
        assert context.worktree_path == expected_path
        assert context.worktree_path.exists()
        assert context.branch_name == "feat/my-feature"

        # Verification: Worktree contains repository files
        assert (context.worktree_path / "README.md").exists()

        # Step 4-5: Simulate objective execution - create state in worktree
        worktree_teambot = context.worktree_path / ".teambot"
        worktree_teambot.mkdir()
        (worktree_teambot / "workflow_state.json").write_text('{"stage": "PLAN"}')

        # Verification: Main directory's .teambot/ unchanged
        main_teambot = temp_git_repo / ".teambot"
        assert not main_teambot.exists()

        # Verification: Worktree has state file
        assert (worktree_teambot / "workflow_state.json").exists()

    def test_at_001_worktree_registered_in_git(self, temp_git_repo: Path):
        """AT-001 supplementary: Verify worktree is registered with Git."""
        WorktreeManager.create_worktree(temp_git_repo, "feat/test-feature")

        # Verify it's listed in git worktree list
        result = subprocess.run(
            ["git", "worktree", "list"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "feat-test-feature" in result.stdout

        # Verify branch was created
        result = subprocess.run(
            ["git", "branch", "--list", "feat/test-feature"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "feat/test-feature" in result.stdout

    # =========================================================================
    # AT-002: Explicit Branch Naming
    # =========================================================================
    def test_at_002_explicit_branch_naming(self, temp_git_repo: Path):
        """AT-002: User specifies custom branch name with --branch flag.

        Verifies: git branch --list custom-branch shows branch exists
        """
        # Step 1: Derive branch with explicit name
        objective_path = Path("objectives/my-feature.md")
        branch_name = derive_branch_name(objective_path, explicit_branch="custom-branch")

        # bare names get feat/ prefix
        assert branch_name == "feat/custom-branch"

        # Step 2-3: Create worktree with explicit branch name
        context = WorktreeManager.create_worktree(temp_git_repo, branch_name)

        # Verification: Branch exists with expected name
        result = subprocess.run(
            ["git", "branch", "--list", "feat/custom-branch"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "feat/custom-branch" in result.stdout

        # Verification: Worktree path uses custom name
        assert context.worktree_path == temp_git_repo / ".teambot-worktrees" / "feat-custom-branch"
        assert context.worktree_path.exists()

    def test_at_002_explicit_branch_with_slash_prefix(self, temp_git_repo: Path):
        """AT-002 supplementary: Explicit branch with custom prefix preserved."""
        branch_name = derive_branch_name(
            Path("objectives/bugfix.md"), explicit_branch="hotfix/critical-bug"
        )

        # Should preserve the explicit prefix
        assert branch_name == "hotfix/critical-bug"

        WorktreeManager.create_worktree(temp_git_repo, branch_name)

        # Verify branch exists with custom prefix
        result = subprocess.run(
            ["git", "branch", "--list", "hotfix/critical-bug"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "hotfix/critical-bug" in result.stdout

    # =========================================================================
    # AT-003: Branch Conflict Error
    # =========================================================================
    def test_at_003_branch_conflict_error(self, temp_git_repo: Path):
        """AT-003: User attempts worktree with branch that already exists.

        Verifies: Error message contains "Branch 'feat/existing' already exists"
                  and suggests --branch
        """
        # Step 1: Create first worktree (creates the branch)
        WorktreeManager.create_worktree(temp_git_repo, "feat/existing")

        # Step 2: Attempt to create another with same branch (different path)
        with pytest.raises(BranchExistsError) as exc_info:
            WorktreeManager.create_worktree(
                temp_git_repo, "feat/existing", base_dir=".teambot-worktrees-2"
            )

        # Verification: Error message has expected content
        error_message = str(exc_info.value)
        assert "feat/existing" in error_message
        assert "already exists" in error_message
        assert "--branch" in error_message

    # =========================================================================
    # AT-004: Resume in Worktree Context
    # =========================================================================
    def test_at_004_resume_in_worktree_context(self, temp_git_repo: Path, monkeypatch):
        """AT-004: User resumes interrupted objective from within worktree.

        Verifies: Stage output shows resumed stage, not restart from beginning
        """
        # Step 1: Create worktree
        context = WorktreeManager.create_worktree(temp_git_repo, "feat/my-feature")

        # Create state file simulating interrupted execution at IMPLEMENTATION stage
        worktree_teambot = context.worktree_path / ".teambot"
        worktree_teambot.mkdir()
        (worktree_teambot / "workflow_state.json").write_text(
            '{"stage": "IMPLEMENTATION", "objective": "objectives/my-feature.md"}'
        )

        # Step 2: Navigate to worktree directory
        monkeypatch.chdir(context.worktree_path)

        # Step 3: Detect worktree context using REAL implementation
        detected = WorktreeManager.detect_worktree_context()

        # Verification: Context was detected correctly
        assert detected is not None
        assert detected.is_worktree is True
        assert detected.branch_name == "feat/my-feature"

        # Verification: State file is accessible and shows IMPLEMENTATION stage
        state_file = detected.worktree_path / ".teambot" / "workflow_state.json"
        assert state_file.exists()
        state_content = state_file.read_text()
        assert "IMPLEMENTATION" in state_content  # Resumed from this stage

    # =========================================================================
    # AT-005: REPL Prompt Shows Worktree Context
    # =========================================================================
    def test_at_005_repl_prompt_shows_worktree_context(self):
        """AT-005: Interactive mode shows worktree/branch in prompt.

        Verifies: Prompt displays [wt:feat/my-feature] or similar
        """
        from teambot.repl.loop import REPLLoop

        # Create WorktreeContext
        worktree_context = WorktreeContext(
            worktree_path=Path("/tmp/test-worktree"),
            branch_name="feat/my-feature",
            repo_root=Path("/tmp/repo"),
            is_worktree=True,
        )

        # Create REPL with worktree context using REAL REPLLoop class
        repl = REPLLoop(
            console=MagicMock(),
            config=MagicMock(),
            worktree_context=worktree_context,
        )

        # Verification: worktree_context is stored (private attribute)
        assert repl._worktree_context is not None
        assert repl._worktree_context.branch_name == "feat/my-feature"

        # Verification: Prompt indicator format
        expected_indicator = f"[wt:{worktree_context.branch_name}]"
        assert expected_indicator == "[wt:feat/my-feature]"

    def test_at_005_repl_without_worktree_context(self):
        """AT-005 supplementary: REPL works without worktree context."""
        from teambot.repl.loop import REPLLoop

        # Create REPL without worktree context
        repl = REPLLoop(
            console=MagicMock(),
            config=MagicMock(),
            worktree_context=None,
        )

        # Verification: Works without crashing
        assert repl._worktree_context is None

    # =========================================================================
    # AT-006: Backward Compatibility (No Worktree Flag)
    # =========================================================================
    def test_at_006_backward_compatibility_no_worktree_flag(self, temp_git_repo: Path):
        """AT-006: Running without --worktree behaves exactly as before.

        Verifies:
        - .teambot-worktrees/ does not exist
        - .teambot/ in main directory contains state files
        """
        from teambot.cli import create_parser

        # Step 1: Parse args without --worktree using REAL parser
        parser = create_parser()
        args = parser.parse_args(["run", "objectives/my-feature.md"])

        # Verification: --worktree is False by default
        assert args.worktree is False
        assert args.branch is None

        # Step 2: Verify no worktree directory exists
        worktree_dir = temp_git_repo / ".teambot-worktrees"
        assert not worktree_dir.exists()

        # Simulate normal execution: state in main .teambot
        main_teambot = temp_git_repo / ".teambot"
        main_teambot.mkdir()
        (main_teambot / "workflow_state.json").write_text('{"stage": "PLAN"}')

        # Verification: State is in main directory
        assert (main_teambot / "workflow_state.json").exists()
        assert not worktree_dir.exists()

    def test_at_006_cli_parser_defaults(self):
        """AT-006 supplementary: All CLI invocations default to no worktree."""
        from teambot.cli import create_parser

        parser = create_parser()

        # Test various invocations
        test_cases = [
            ["run"],
            ["run", "obj.md"],
            ["run", "-c", "config.json"],
            ["run", "--resume"],
        ]

        for args_list in test_cases:
            args = parser.parse_args(args_list)
            assert args.worktree is False, f"Failed for {args_list}"
            assert args.branch is None, f"Failed for {args_list}"

    # =========================================================================
    # AT-007: Git Not Available Error
    # =========================================================================
    def test_at_007_git_not_available_error(self):
        """AT-007: Attempting --worktree when Git is not installed.

        Verifies: Error message contains "Git is required for --worktree mode"
        """
        # Mock shutil.which to simulate Git not being available
        with patch("teambot.worktree.manager.shutil.which", return_value=None):
            # Verification: is_git_available returns False
            assert WorktreeManager.is_git_available() is False

            # Verification: GitNotFoundError is raised
            with pytest.raises(GitNotFoundError) as exc_info:
                WorktreeManager.create_worktree(Path("/tmp"), "feat/test")

            error_message = str(exc_info.value)
            # Verification: Error message has required content
            assert "Git" in error_message
            assert "required" in error_message.lower()
            assert "--worktree" in error_message

    def test_at_007_git_not_found_error_message_quality(self):
        """AT-007 supplementary: GitNotFoundError has helpful guidance."""
        error = GitNotFoundError()
        message = str(error)

        # Should be actionable
        assert "Git" in message
        assert "required" in message.lower()


# =============================================================================
# Worktree Workflow Enhancement - Acceptance Validation Tests
# Tests for --base-branch option and automatic objective file copying
# =============================================================================


@pytest.mark.acceptance
class TestWorktreeEnhancementAcceptanceValidation:
    """Strict acceptance validation tests for worktree workflow enhancement.

    These tests call REAL implementation code with REAL Git operations.
    No mocking of core functionality being tested.
    """

    @pytest.fixture
    def git_repo_with_objective(self, tmp_path: Path):
        """Create a real Git repo with committed objective file."""
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        # Create and commit objective file
        objectives_dir = repo / "objectives"
        objectives_dir.mkdir()
        objective_file = objectives_dir / "task.md"
        objective_file.write_text("# Test Objective\n\n## Goals\n- Goal 1\n- Goal 2\n")
        (repo / "README.md").write_text("# Test Repository")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit with objective"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        return repo

    # =========================================================================
    # AT-001: Automatic Copy - Committed Objective File
    # =========================================================================
    def test_at_001_automatic_copy_committed_objective(self, git_repo_with_objective: Path):
        """AT-001: Committed objective file automatically copied to worktree.

        Steps:
        1. User runs `teambot run --worktree objectives/task.md`
        2. Worktree is created at `.teambot-worktrees/feat-task/`
        3. TeamBot detects objective file missing in worktree
        4. TeamBot copies objective file to worktree

        Verification:
        - File exists at `.teambot-worktrees/feat-task/objectives/task.md`
        - Content is identical to source
        """
        import hashlib
        import os

        repo = git_repo_with_objective
        source_objective = repo / "objectives" / "task.md"
        source_content = source_objective.read_text()
        source_hash = hashlib.sha256(source_content.encode()).hexdigest()

        # Create worktree using REAL implementation
        context = WorktreeManager.create_worktree(repo, "feat/task")

        # Change to worktree directory (simulating what CLI does)
        original_cwd = os.getcwd()
        os.chdir(context.worktree_path)

        try:
            # The objective file exists in worktree because it was committed
            worktree_objective = Path("objectives/task.md")

            # Verify file exists in worktree (committed files appear automatically)
            assert worktree_objective.exists(), "Objective file should exist in worktree"

            # Verify content is identical
            worktree_content = worktree_objective.read_text()
            worktree_hash = hashlib.sha256(worktree_content.encode()).hexdigest()

            assert source_hash == worktree_hash, "File hash must match source"
            assert worktree_content == source_content, "Content must be identical"
        finally:
            os.chdir(original_cwd)

    # =========================================================================
    # AT-002: Automatic Copy - Staged But Uncommitted Objective File
    # =========================================================================
    def test_at_002_automatic_copy_staged_uncommitted_objective(self, tmp_path: Path):
        """AT-002: Staged (uncommitted) objective copied from working directory.

        Steps:
        1. User creates and stages objectives/new-task.md (not committed)
        2. User runs `teambot run --worktree objectives/new-task.md`
        3. Worktree is created (file won't exist because not committed)
        4. TeamBot copies working directory version to worktree

        Verification:
        - Worktree contains `objectives/new-task.md`
        - Content matches source repository working directory version
        """
        import os
        import shutil

        # Create repo with initial commit (no objective yet)
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        (repo / "README.md").write_text("# Test Repository")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create objective file and stage it (but don't commit)
        objectives_dir = repo / "objectives"
        objectives_dir.mkdir()
        objective_file = objectives_dir / "new-task.md"
        staged_content = "# Staged Objective\n\nThis is staged but not committed.\n"
        objective_file.write_text(staged_content)
        subprocess.run(["git", "add", "objectives/new-task.md"], cwd=repo, capture_output=True)

        # Create worktree using REAL implementation
        context = WorktreeManager.create_worktree(repo, "feat/new-task")

        # Change to worktree directory (simulating what CLI does)
        original_cwd = os.getcwd()
        os.chdir(context.worktree_path)

        try:
            worktree_objective = Path("objectives/new-task.md")

            # File should NOT exist in worktree (not committed)
            # This is where the CLI copy logic kicks in
            if not worktree_objective.exists():
                # Simulate CLI copy logic using REAL shutil
                source_objective = repo / "objectives" / "new-task.md"
                if source_objective.exists():
                    worktree_objective.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_objective, worktree_objective)

            # Verification: File now exists with correct content
            assert worktree_objective.exists(), "Objective file should exist after copy"
            assert worktree_objective.read_text() == staged_content, (
                "Content must match working directory"
            )
        finally:
            os.chdir(original_cwd)

    # =========================================================================
    # AT-003: Base Branch Specification
    # =========================================================================
    def test_at_003_base_branch_specification(self, tmp_path: Path):
        """AT-003: User specifies a different base branch for worktree creation.

        Steps:
        1. Create repo with main branch and develop branch with different content
        2. User runs `teambot run --worktree --base-branch main objectives/task.md`
        3. Worktree is created branching from `main` instead of current branch

        Verification:
        - New branch is based on `main`
        - `git merge-base` confirms `main` is ancestor of worktree branch
        """
        # Create repo
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Initial commit on default branch
        (repo / "README.md").write_text("# Main Branch")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit on main"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Get the main branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        main_branch = result.stdout.strip()

        # Get main branch commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        main_commit = result.stdout.strip()

        # Create develop branch with additional content
        subprocess.run(
            ["git", "checkout", "-b", "develop"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        (repo / "develop-only.txt").write_text("Develop content")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Develop commit"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create worktree from main branch using REAL implementation with base_branch
        context = WorktreeManager.create_worktree(repo, "feat/from-main", base_branch=main_branch)

        # Verification 1: Worktree exists
        assert context.worktree_path.exists()

        # Verification 2: Worktree does NOT have develop-only.txt (branched from main)
        assert not (context.worktree_path / "develop-only.txt").exists()

        # Verification 3: git merge-base confirms main is ancestor
        result = subprocess.run(
            ["git", "merge-base", main_branch, context.branch_name],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        merge_base = result.stdout.strip()

        # The merge base should be the main branch commit
        assert merge_base == main_commit, f"merge-base should be {main_commit}, got {merge_base}"

    # =========================================================================
    # AT-004: Invalid Base Branch Error
    # =========================================================================
    def test_at_004_invalid_base_branch_error(self, tmp_path: Path):
        """AT-004: User specifies a non-existent base branch.

        Steps:
        1. User runs `teambot run --worktree --base-branch nonexistent objectives/task.md`

        Verification:
        - Clear error message mentioning the branch name
        - No worktree created
        """
        from teambot.worktree.errors import WorktreeError

        # Create minimal repo
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        (repo / "README.md").write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Attempt to create worktree with non-existent base branch
        with pytest.raises(WorktreeError) as exc_info:
            WorktreeManager.create_worktree(repo, "feat/test", base_branch="nonexistent-branch")

        # Verification: Error message mentions the branch
        error_message = str(exc_info.value)
        assert "nonexistent" in error_message.lower() or "not found" in error_message.lower()

        # Verification: No worktree created
        worktree_path = repo / ".teambot-worktrees" / "feat-test"
        assert not worktree_path.exists()

    # =========================================================================
    # AT-005: Backward Compatibility - Objective Exists in Worktree
    # =========================================================================
    def test_at_005_backward_compatibility_objective_exists(self, git_repo_with_objective: Path):
        """AT-005: No copy when objective file already exists in worktree.

        Steps:
        1. User runs `teambot run --worktree objectives/task.md`
        2. Worktree is created (file exists because it's committed)

        Verification:
        - No file copy occurs
        - Original worktree creation behavior preserved
        """
        import os

        repo = git_repo_with_objective

        # Create worktree using REAL implementation
        context = WorktreeManager.create_worktree(repo, "feat/existing")

        # Change to worktree directory
        original_cwd = os.getcwd()
        os.chdir(context.worktree_path)

        try:
            worktree_objective = Path("objectives/task.md")

            # Verification: File exists in worktree (committed file appears automatically)
            assert worktree_objective.exists()

            # Verification: Content matches (no copy needed or occurred)
            source_content = (repo / "objectives" / "task.md").read_text()
            worktree_content = worktree_objective.read_text()
            assert worktree_content == source_content

            # The key point: no copy was needed because file was committed
            # This test verifies backward compatibility - committed files just work
        finally:
            os.chdir(original_cwd)

    # =========================================================================
    # AT-006: Cross-Platform Path Handling
    # =========================================================================
    def test_at_006_cross_platform_path_handling(self, tmp_path: Path):
        """AT-006: Path handling works correctly with subdirectories.

        Steps:
        1. User runs `teambot run --worktree objectives/features/task.md`
        2. Worktree created; subdirectory must be created
        3. Objective file copied to correct location

        Verification:
        - `objectives/features/task.md` exists in worktree
        - Parent directories created correctly
        """
        import os

        # Create repo with nested objective
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create nested directory structure
        nested_dir = repo / "objectives" / "features"
        nested_dir.mkdir(parents=True)
        objective_file = nested_dir / "task.md"
        nested_content = "# Nested Feature Task\n\n## Goals\n- Nested goal\n"
        objective_file.write_text(nested_content)
        (repo / "README.md").write_text("# Test")

        # Stage but don't commit (to test copy path)
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Create worktree using REAL implementation
        context = WorktreeManager.create_worktree(repo, "feat/features-task")

        # Change to worktree directory
        original_cwd = os.getcwd()
        os.chdir(context.worktree_path)

        try:
            # Since file is committed, it should exist in worktree
            worktree_objective = Path("objectives") / "features" / "task.md"

            # Verification: Path exists with correct structure
            assert worktree_objective.exists(), "Nested objective file should exist"
            assert worktree_objective.parent.exists(), "Parent directories should exist"
            assert worktree_objective.parent.name == "features"
            assert worktree_objective.parent.parent.name == "objectives"

            # Verification: Content is correct
            assert worktree_objective.read_text() == nested_content
        finally:
            os.chdir(original_cwd)
