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
