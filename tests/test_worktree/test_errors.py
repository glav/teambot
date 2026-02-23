"""Tests for worktree error classes."""

import pytest

from teambot.worktree.errors import (
    BranchExistsError,
    GitNotFoundError,
    GitVersionError,
    PathTooLongError,
    WorktreeError,
    WorktreeExistsError,
)


class TestWorktreeErrors:
    """Tests for worktree exception hierarchy."""

    def test_worktree_error_is_exception(self):
        """WorktreeError is a proper exception."""
        with pytest.raises(WorktreeError):
            raise WorktreeError("test error")

    def test_worktree_error_message(self):
        """WorktreeError stores message."""
        error = WorktreeError("custom message")
        assert str(error) == "custom message"

    def test_git_not_found_error_default_message(self):
        """GitNotFoundError has default message matching FR-011."""
        error = GitNotFoundError()
        assert "Git is required for --worktree mode" in str(error)

    def test_git_not_found_error_custom_message(self):
        """GitNotFoundError accepts custom message."""
        error = GitNotFoundError("Custom git error")
        assert "Custom git error" in str(error)

    def test_git_not_found_inherits_worktree_error(self):
        """GitNotFoundError inherits from WorktreeError."""
        error = GitNotFoundError()
        assert isinstance(error, WorktreeError)

    def test_branch_exists_error_message(self):
        """BranchExistsError includes branch name and guidance matching FR-012."""
        error = BranchExistsError("feat/my-feature")
        assert "feat/my-feature" in str(error)
        assert "already exists" in str(error)
        assert "--branch" in str(error)

    def test_branch_exists_error_stores_branch_name(self):
        """BranchExistsError stores branch_name attribute."""
        error = BranchExistsError("feat/test")
        assert error.branch_name == "feat/test"

    def test_branch_exists_inherits_worktree_error(self):
        """BranchExistsError inherits from WorktreeError."""
        error = BranchExistsError("feat/test")
        assert isinstance(error, WorktreeError)

    def test_worktree_exists_error_message(self):
        """WorktreeExistsError includes path and guidance."""
        error = WorktreeExistsError("/path/to/worktree")
        assert "/path/to/worktree" in str(error)
        assert "--branch" in str(error)

    def test_worktree_exists_error_stores_path(self):
        """WorktreeExistsError stores path attribute."""
        error = WorktreeExistsError("/some/path")
        assert error.path == "/some/path"

    def test_worktree_exists_inherits_worktree_error(self):
        """WorktreeExistsError inherits from WorktreeError."""
        error = WorktreeExistsError("/path")
        assert isinstance(error, WorktreeError)

    def test_git_version_error_message(self):
        """GitVersionError includes version info."""
        error = GitVersionError("2.3.0", "2.5")
        assert "2.3.0" in str(error)
        assert "2.5" in str(error)
        assert "too old" in str(error)

    def test_git_version_error_stores_versions(self):
        """GitVersionError stores version attributes."""
        error = GitVersionError("2.3.0", "2.5")
        assert error.version == "2.3.0"
        assert error.required == "2.5"

    def test_git_version_error_default_required(self):
        """GitVersionError has default required version."""
        error = GitVersionError("2.3.0")
        assert error.required == "2.5"

    def test_git_version_inherits_worktree_error(self):
        """GitVersionError inherits from WorktreeError."""
        error = GitVersionError("2.3.0")
        assert isinstance(error, WorktreeError)

    def test_path_too_long_error_message(self):
        """PathTooLongError includes length details matching FR-013."""
        error = PathTooLongError("/very/long/path", 275, 260)
        assert "275" in str(error)
        assert "260" in str(error)
        assert "--branch" in str(error)

    def test_path_too_long_error_stores_attributes(self):
        """PathTooLongError stores path, length, limit attributes."""
        error = PathTooLongError("/path", 275, 260)
        assert error.path == "/path"
        assert error.length == 275
        assert error.limit == 260

    def test_path_too_long_error_default_limit(self):
        """PathTooLongError has default 260 char limit."""
        error = PathTooLongError("/path", 275)
        assert error.limit == 260

    def test_path_too_long_inherits_worktree_error(self):
        """PathTooLongError inherits from WorktreeError."""
        error = PathTooLongError("/path", 275)
        assert isinstance(error, WorktreeError)
