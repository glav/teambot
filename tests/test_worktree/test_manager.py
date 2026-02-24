"""Tests for WorktreeManager class."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from teambot.worktree.errors import (
    BranchExistsError,
    GitNotFoundError,
    WorktreeExistsError,
)
from teambot.worktree.manager import WorktreeContext, WorktreeManager


class TestIsGitAvailable:
    """Tests for Git availability check."""

    def test_git_available(self, mocker):
        """Returns True when git is on PATH."""
        mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
        assert WorktreeManager.is_git_available() is True

    def test_git_not_available(self, mocker):
        """Returns False when git is not on PATH."""
        mocker.patch("teambot.worktree.manager.shutil.which", return_value=None)
        assert WorktreeManager.is_git_available() is False


class TestGetRepoRoot:
    """Tests for repository root detection."""

    def test_get_repo_root_success(self, mocker):
        """Returns Path when in a Git repository."""
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.return_value = MagicMock(returncode=0, stdout="/path/to/repo\n")
        result = WorktreeManager.get_repo_root()
        assert result == Path("/path/to/repo")

    def test_get_repo_root_not_in_repo(self, mocker):
        """Returns None when not in a Git repository."""
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.return_value = MagicMock(returncode=128, stdout="")
        result = WorktreeManager.get_repo_root()
        assert result is None

    def test_get_repo_root_timeout(self, mocker):
        """Returns None on timeout."""
        import subprocess

        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)
        result = WorktreeManager.get_repo_root()
        assert result is None


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
        assert result.is_worktree is True
        assert result.repo_root == tmp_path

    def test_create_worktree_creates_base_directory(self, tmp_path, mocker, mock_git_version_check):
        """Creates base directory if it doesn't exist."""
        mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        WorktreeManager.create_worktree(tmp_path, "feat/test")

        assert (tmp_path / ".teambot-worktrees").exists()

    def test_create_worktree_git_not_found(self, mocker):
        """Raises GitNotFoundError when Git not available."""
        mocker.patch("teambot.worktree.manager.shutil.which", return_value=None)

        with pytest.raises(GitNotFoundError):
            WorktreeManager.create_worktree(Path("/repo"), "feat/test")

    def test_create_worktree_branch_exists(self, tmp_path, mocker, mock_git_version_check):
        """Raises BranchExistsError when branch already exists."""
        mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.return_value = MagicMock(
            returncode=128, stderr="fatal: a branch named 'feat/test' already exists"
        )

        with pytest.raises(BranchExistsError) as exc_info:
            WorktreeManager.create_worktree(tmp_path, "feat/test")

        assert "feat/test" in str(exc_info.value)

    def test_create_worktree_path_exists(self, tmp_path, mocker, mock_git_version_check):
        """Raises WorktreeExistsError when path already exists."""
        mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
        worktree_path = tmp_path / ".teambot-worktrees" / "feat-test"
        worktree_path.mkdir(parents=True)

        with pytest.raises(WorktreeExistsError):
            WorktreeManager.create_worktree(tmp_path, "feat/test")

    def test_create_worktree_git_error(self, tmp_path, mocker, mock_git_version_check):
        """Raises WorktreeError on generic Git error."""
        from teambot.worktree.errors import WorktreeError

        mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal: some other git error")

        with pytest.raises(WorktreeError) as exc_info:
            WorktreeManager.create_worktree(tmp_path, "feat/test")

        assert "some other git error" in str(exc_info.value)

    def test_create_worktree_calls_git_correctly(self, tmp_path, mocker, mock_git_version_check):
        """Verifies correct Git command is called."""
        mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        WorktreeManager.create_worktree(tmp_path, "feat/my-feature")

        expected_path = str(tmp_path / ".teambot-worktrees" / "feat-my-feature")
        mock_run.assert_called_once_with(
            ["git", "worktree", "add", "-b", "feat/my-feature", expected_path],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

    def test_create_worktree_with_base_branch(self, tmp_path, mocker, mock_git_version_check):
        """Creates worktree from specified base branch."""
        mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        WorktreeManager.create_worktree(tmp_path, "feat/task", base_branch="main")

        expected_path = str(tmp_path / ".teambot-worktrees" / "feat-task")
        mock_run.assert_called_once_with(
            ["git", "worktree", "add", "-b", "feat/task", expected_path, "main"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

    def test_create_worktree_base_branch_none_preserves_behavior(
        self, tmp_path, mocker, mock_git_version_check
    ):
        """When base_branch is None, git command unchanged (backward compatible)."""
        mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        WorktreeManager.create_worktree(tmp_path, "feat/task", base_branch=None)

        expected_path = str(tmp_path / ".teambot-worktrees" / "feat-task")
        call_args = mock_run.call_args[0][0]
        # Should NOT include base branch at the end
        assert call_args == ["git", "worktree", "add", "-b", "feat/task", expected_path]

    def test_create_worktree_invalid_base_branch_raises_error(
        self, tmp_path, mocker, mock_git_version_check
    ):
        """Raises WorktreeError when base branch doesn't exist."""
        from teambot.worktree.errors import WorktreeError

        mocker.patch("teambot.worktree.manager.shutil.which", return_value="/usr/bin/git")
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.return_value = MagicMock(
            returncode=128, stdout="", stderr="fatal: invalid reference: nonexistent"
        )

        with pytest.raises(WorktreeError) as exc_info:
            WorktreeManager.create_worktree(tmp_path, "feat/task", base_branch="nonexistent")

        assert "nonexistent" in str(exc_info.value) or "invalid" in str(exc_info.value).lower()


class TestDetectWorktreeContext:
    """Tests for worktree context detection."""

    def test_detect_not_in_repo(self, mocker):
        """Returns None when not in a Git repository."""
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.return_value = MagicMock(returncode=128, stdout="")

        result = WorktreeManager.detect_worktree_context()
        assert result is None

    def test_detect_not_in_worktree(self, mocker, tmp_path):
        """Returns None when in main worktree (not a linked worktree)."""
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        # git-dir equals common-dir means main worktree
        git_path = str(tmp_path / ".git")
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="true"),  # is-inside-work-tree
            MagicMock(returncode=0, stdout=git_path),  # git-dir
            MagicMock(returncode=0, stdout=git_path),  # git-common-dir
        ]

        result = WorktreeManager.detect_worktree_context()
        assert result is None

    def test_detect_in_worktree(self, mocker, tmp_path):
        """Returns WorktreeContext when in a worktree."""
        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        repo_git = str(tmp_path / ".git")
        wt_git = str(tmp_path / ".teambot-worktrees" / "feat-test" / ".git")
        wt_path = str(tmp_path / ".teambot-worktrees" / "feat-test")
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="true"),  # is-inside-work-tree
            MagicMock(returncode=0, stdout=wt_git),  # git-dir
            MagicMock(returncode=0, stdout=repo_git),  # git-common-dir
            MagicMock(returncode=0, stdout="feat/test"),  # branch name
            MagicMock(returncode=0, stdout=wt_path),  # toplevel
        ]

        result = WorktreeManager.detect_worktree_context()
        assert result is not None
        assert result.branch_name == "feat/test"
        assert result.is_worktree is True

    def test_detect_worktree_timeout(self, mocker):
        """Returns None on timeout."""
        import subprocess

        mock_run = mocker.patch("teambot.worktree.manager.subprocess.run")
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)

        result = WorktreeManager.detect_worktree_context()
        assert result is None


class TestWorktreeContext:
    """Tests for WorktreeContext dataclass."""

    def test_worktree_context_creation(self, tmp_path):
        """WorktreeContext can be created with required fields."""
        context = WorktreeContext(
            worktree_path=tmp_path / "worktree",
            branch_name="feat/test",
            repo_root=tmp_path,
        )
        assert context.worktree_path == tmp_path / "worktree"
        assert context.branch_name == "feat/test"
        assert context.repo_root == tmp_path
        assert context.is_worktree is True

    def test_worktree_context_is_worktree_default(self, tmp_path):
        """WorktreeContext.is_worktree defaults to True."""
        context = WorktreeContext(
            worktree_path=tmp_path,
            branch_name="test",
            repo_root=tmp_path,
        )
        assert context.is_worktree is True
