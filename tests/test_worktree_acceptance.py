"""Acceptance tests for worktree isolation feature.

Core logic is tested directly; selective mocking is used for external dependencies.
These tests use real Git operations in temporary repositories.
"""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def temp_git_repo(tmp_path: Path):
    """Create a temporary Git repository for testing."""
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
        ["git", "config", "user.name", "Test"],
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
class TestWorktreeIsolationAcceptance:
    """Acceptance tests for worktree isolation feature."""

    def test_at_001_worktree_creation_happy_path(self, temp_git_repo: Path):
        """AT-001: Worktree created at expected path with new branch."""
        from teambot.worktree import WorktreeManager

        context = WorktreeManager.create_worktree(temp_git_repo, "feat/test-feature")

        # Verify worktree path exists
        assert context.worktree_path.exists()
        assert context.branch_name == "feat/test-feature"
        assert context.is_worktree is True
        assert context.repo_root == temp_git_repo

        # Verify branch exists in git
        result = subprocess.run(
            ["git", "branch", "--list", "feat/test-feature"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "feat/test-feature" in result.stdout

        # Verify worktree is registered
        result = subprocess.run(
            ["git", "worktree", "list"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "feat-test-feature" in result.stdout

    def test_at_002_state_isolation(self, temp_git_repo: Path):
        """AT-002: State files scoped to worktree directory."""
        from teambot.worktree import WorktreeManager

        # Create main .teambot directory
        main_teambot = temp_git_repo / ".teambot"
        main_teambot.mkdir()
        (main_teambot / "main_state.json").write_text("{}")

        # Create worktree
        context = WorktreeManager.create_worktree(temp_git_repo, "feat/isolation-test")

        # Create .teambot in worktree
        worktree_teambot = context.worktree_path / ".teambot"
        worktree_teambot.mkdir()
        (worktree_teambot / "worktree_state.json").write_text("{}")

        # Verify isolation - files don't cross over
        assert (main_teambot / "main_state.json").exists()
        assert not (main_teambot / "worktree_state.json").exists()
        assert (worktree_teambot / "worktree_state.json").exists()
        assert not (worktree_teambot / "main_state.json").exists()

    def test_at_003_branch_name_derivation(self, temp_git_repo: Path):
        """AT-003: Branch name correctly derived from objective path."""
        from teambot.worktree import derive_branch_name

        # Test various objective filenames
        assert derive_branch_name(Path("objectives/foo.md")) == "feat/foo"
        assert derive_branch_name(Path("objective-auth.md")) == "feat/auth"
        assert derive_branch_name(Path("sdd-objective-feature.md")) == "feat/feature"
        assert derive_branch_name(Path("my-cool-feature.md")) == "feat/my-cool-feature"

        # Test explicit branch override
        assert derive_branch_name(Path("any.md"), explicit_branch="custom") == "feat/custom"
        assert derive_branch_name(Path("any.md"), explicit_branch="fix/bug") == "fix/bug"

    def test_at_004_worktree_directory_structure(self, temp_git_repo: Path):
        """AT-004: Worktree created in correct directory structure."""
        from teambot.worktree import WorktreeManager

        context = WorktreeManager.create_worktree(temp_git_repo, "feat/my-branch")

        # Verify directory structure
        expected_base = temp_git_repo / ".teambot-worktrees"
        expected_path = expected_base / "feat-my-branch"

        assert expected_base.exists()
        assert expected_path.exists()
        assert context.worktree_path == expected_path

        # Verify it's a valid git worktree
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=expected_path,
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "true"

    def test_at_005_detect_worktree_context(self, temp_git_repo: Path, monkeypatch):
        """AT-005: Worktree context correctly detected."""
        from teambot.worktree import WorktreeManager

        # Create worktree
        context = WorktreeManager.create_worktree(temp_git_repo, "feat/detect-test")

        # Change to worktree directory and detect context
        monkeypatch.chdir(context.worktree_path)
        detected = WorktreeManager.detect_worktree_context()

        assert detected is not None
        assert detected.is_worktree is True
        assert detected.branch_name == "feat/detect-test"

    def test_at_006_main_repo_not_worktree(self, temp_git_repo: Path, monkeypatch):
        """AT-006: Main repository not detected as worktree."""
        from teambot.worktree import WorktreeManager

        monkeypatch.chdir(temp_git_repo)
        detected = WorktreeManager.detect_worktree_context()

        # Main repo should return None (not a worktree)
        assert detected is None

    def test_at_007_branch_exists_error(self, temp_git_repo: Path):
        """AT-007: Clear error when branch already exists."""
        from teambot.worktree import WorktreeManager
        from teambot.worktree.errors import BranchExistsError

        # Create first worktree - this creates the branch
        WorktreeManager.create_worktree(temp_git_repo, "feat/existing")

        # Try to create another worktree with same branch but different path
        # This tests the case where branch exists but path doesn't
        with pytest.raises(BranchExistsError) as exc_info:
            WorktreeManager.create_worktree(
                temp_git_repo, "feat/existing", base_dir=".teambot-worktrees-2"
            )

        assert "feat/existing" in str(exc_info.value)
        assert "already exists" in str(exc_info.value)

    def test_at_008_worktree_path_exists_error(self, temp_git_repo: Path):
        """AT-008: Clear error when worktree path already exists."""
        from teambot.worktree import WorktreeManager
        from teambot.worktree.errors import WorktreeExistsError

        # Pre-create the worktree directory
        worktree_path = temp_git_repo / ".teambot-worktrees" / "feat-blocked"
        worktree_path.mkdir(parents=True)

        # Try to create worktree at same path
        with pytest.raises(WorktreeExistsError) as exc_info:
            WorktreeManager.create_worktree(temp_git_repo, "feat/blocked")

        assert "feat-blocked" in str(exc_info.value)


@pytest.mark.acceptance
class TestWorktreeResumeAcceptance:
    """Acceptance tests for resume behavior in worktree context."""

    def test_at_009_resume_detects_worktree(self, temp_git_repo: Path, monkeypatch):
        """AT-009: Resume correctly detects worktree context."""
        from teambot.worktree import WorktreeManager

        # Create worktree
        context = WorktreeManager.create_worktree(temp_git_repo, "feat/resume-test")

        # Simulate being in the worktree
        monkeypatch.chdir(context.worktree_path)

        # Create state file in worktree
        worktree_teambot = context.worktree_path / ".teambot"
        worktree_teambot.mkdir()
        (worktree_teambot / "workflow_state.json").write_text('{"stage": "PLAN"}')

        # Detect context
        detected = WorktreeManager.detect_worktree_context()

        assert detected is not None
        assert detected.branch_name == "feat/resume-test"
        # State file is in worktree
        assert (detected.worktree_path / ".teambot" / "workflow_state.json").exists()

    def test_at_010_worktree_contains_correct_files(self, temp_git_repo: Path):
        """AT-010: Worktree contains repository files."""
        from teambot.worktree import WorktreeManager

        # Add some files to the repo
        (temp_git_repo / "src").mkdir()
        (temp_git_repo / "src" / "main.py").write_text("print('hello')")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add src"],
            cwd=temp_git_repo,
            capture_output=True,
        )

        # Create worktree
        context = WorktreeManager.create_worktree(temp_git_repo, "feat/files-test")

        # Verify files exist in worktree
        assert (context.worktree_path / "README.md").exists()
        assert (context.worktree_path / "src" / "main.py").exists()
        assert (context.worktree_path / "src" / "main.py").read_text() == "print('hello')"


@pytest.mark.acceptance
class TestWorktreeEnhancementAcceptance:
    """Acceptance tests for worktree workflow enhancement (objective copy and base-branch)."""

    def test_at_011_base_branch_creates_from_specified_branch(self, temp_git_repo: Path):
        """AT-011: --base-branch main creates worktree from main branch."""
        from teambot.worktree import WorktreeManager

        # Get the default branch name (usually main or master)
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        default_branch = result.stdout.strip()

        # Create a develop branch with different content
        subprocess.run(
            ["git", "checkout", "-b", "develop"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )
        (temp_git_repo / "develop-only.txt").write_text("develop content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Add develop content"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )

        # Stay on develop but create worktree from the default branch
        # The worktree should NOT have develop-only.txt since we're branching from main
        context = WorktreeManager.create_worktree(
            temp_git_repo, "feat/from-main", base_branch=default_branch
        )

        # Verify worktree was created from main (no develop-only.txt)
        assert context.worktree_path.exists()
        assert not (context.worktree_path / "develop-only.txt").exists()
        assert (context.worktree_path / "README.md").exists()

    def test_at_012_base_branch_from_develop_includes_develop_content(self, temp_git_repo: Path):
        """AT-012: --base-branch develop creates worktree with develop content."""
        from teambot.worktree import WorktreeManager

        # Create a develop branch with different content
        subprocess.run(
            ["git", "checkout", "-b", "develop"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )
        (temp_git_repo / "develop-feature.txt").write_text("feature content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Add feature on develop"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )

        # Create worktree from develop branch
        context = WorktreeManager.create_worktree(
            temp_git_repo, "feat/from-develop", base_branch="develop"
        )

        # Verify worktree has develop content
        assert context.worktree_path.exists()
        assert (context.worktree_path / "develop-feature.txt").exists()
        assert (context.worktree_path / "develop-feature.txt").read_text() == "feature content"

    def test_at_013_invalid_base_branch_raises_error(self, temp_git_repo: Path):
        """AT-013: Non-existent base branch produces clear error."""
        from teambot.worktree import WorktreeManager
        from teambot.worktree.errors import WorktreeError

        with pytest.raises(WorktreeError) as exc_info:
            WorktreeManager.create_worktree(
                temp_git_repo, "feat/test", base_branch="nonexistent-branch"
            )

        assert (
            "nonexistent-branch" in str(exc_info.value)
            or "not found" in str(exc_info.value).lower()
        )

    def test_at_014_base_branch_none_preserves_current_behavior(self, temp_git_repo: Path):
        """AT-014: No --base-branch defaults to current HEAD (backward compatible)."""
        from teambot.worktree import WorktreeManager

        # Create a feature branch
        subprocess.run(
            ["git", "checkout", "-b", "feature/existing"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )
        (temp_git_repo / "feature-file.txt").write_text("feature content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Add feature file"],
            cwd=temp_git_repo,
            capture_output=True,
            check=True,
        )

        # Create worktree without base_branch (should branch from current HEAD = feature/existing)
        context = WorktreeManager.create_worktree(temp_git_repo, "feat/new-work")

        # Worktree should have content from feature/existing
        assert (context.worktree_path / "feature-file.txt").exists()

    def test_at_015_worktree_with_branch_name_containing_slash(self, temp_git_repo: Path):
        """AT-015: Branch names with slashes handled correctly."""
        from teambot.worktree import WorktreeManager

        # Create worktree with branch containing multiple slashes
        context = WorktreeManager.create_worktree(
            temp_git_repo, "feature/auth/login", base_branch=None
        )

        # Verify directory name sanitized correctly
        assert context.worktree_path.name == "feature-auth-login"
        assert context.branch_name == "feature/auth/login"

        # Verify branch was created correctly
        result = subprocess.run(
            ["git", "branch", "--list", "feature/auth/login"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "feature/auth/login" in result.stdout
