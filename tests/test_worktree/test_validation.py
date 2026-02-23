"""Tests for worktree path validation and Git version checking."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from teambot.worktree.errors import GitNotFoundError, GitVersionError, PathTooLongError
from teambot.worktree.manager import WorktreeManager


class TestValidatePathLength:
    """Tests for WorktreeManager.validate_path_length()."""

    def test_no_validation_on_non_windows(self, tmp_path: Path):
        """Path length not validated on non-Windows platforms."""
        long_path = tmp_path / ("a" * 300)

        with patch("teambot.worktree.manager.platform.system", return_value="Linux"):
            # Should not raise
            WorktreeManager.validate_path_length(long_path)

    def test_no_validation_on_macos(self, tmp_path: Path):
        """Path length not validated on macOS."""
        long_path = tmp_path / ("a" * 300)

        with patch("teambot.worktree.manager.platform.system", return_value="Darwin"):
            # Should not raise
            WorktreeManager.validate_path_length(long_path)

    def test_raises_on_windows_long_path(self, tmp_path: Path):
        """Raises PathTooLongError for paths exceeding 260 chars on Windows."""
        # Create a path that when resolved exceeds 260 chars
        long_component = "a" * 200
        long_path = tmp_path / long_component / long_component

        with patch("teambot.worktree.manager.platform.system", return_value="Windows"):
            with pytest.raises(PathTooLongError) as exc_info:
                WorktreeManager.validate_path_length(long_path)

        assert exc_info.value.path is not None
        assert exc_info.value.limit == 260

    def test_accepts_short_path_on_windows(self, tmp_path: Path):
        """Accepts paths under 260 chars on Windows."""
        short_path = tmp_path / "short"

        with patch("teambot.worktree.manager.platform.system", return_value="Windows"):
            # Should not raise
            WorktreeManager.validate_path_length(short_path)

    def test_exact_260_char_path_ok(self):
        """Path of exactly 260 chars is OK."""
        # Create a mock path that resolves to exactly 260 chars
        mock_path = MagicMock(spec=Path)
        mock_path.resolve.return_value = MagicMock(__str__=lambda self: "a" * 260)

        with patch("teambot.worktree.manager.platform.system", return_value="Windows"):
            # Should not raise
            WorktreeManager.validate_path_length(mock_path)


class TestCheckGitVersion:
    """Tests for WorktreeManager.check_git_version()."""

    def test_accepts_git_2_39(self):
        """Accepts Git 2.39 (current common version)."""
        mock_result = MagicMock(returncode=0, stdout="git version 2.39.2")

        with patch("teambot.worktree.manager.subprocess.run", return_value=mock_result):
            # Should not raise
            WorktreeManager.check_git_version()

    def test_accepts_git_2_5(self):
        """Accepts Git 2.5 (minimum required)."""
        mock_result = MagicMock(returncode=0, stdout="git version 2.5.0")

        with patch("teambot.worktree.manager.subprocess.run", return_value=mock_result):
            # Should not raise
            WorktreeManager.check_git_version()

    def test_rejects_git_2_4(self):
        """Rejects Git 2.4 (too old)."""
        mock_result = MagicMock(returncode=0, stdout="git version 2.4.0")

        with patch("teambot.worktree.manager.subprocess.run", return_value=mock_result):
            with pytest.raises(GitVersionError) as exc_info:
                WorktreeManager.check_git_version()

        assert exc_info.value.version == "2.4"
        assert exc_info.value.required == "2.5"

    def test_rejects_git_1_x(self):
        """Rejects Git 1.x (ancient)."""
        mock_result = MagicMock(returncode=0, stdout="git version 1.9.5")

        with patch("teambot.worktree.manager.subprocess.run", return_value=mock_result):
            with pytest.raises(GitVersionError) as exc_info:
                WorktreeManager.check_git_version()

        assert exc_info.value.version == "1.9"

    def test_accepts_git_3_0(self):
        """Accepts Git 3.0 (future version)."""
        mock_result = MagicMock(returncode=0, stdout="git version 3.0.0")

        with patch("teambot.worktree.manager.subprocess.run", return_value=mock_result):
            # Should not raise
            WorktreeManager.check_git_version()

    def test_raises_git_not_found_on_error(self):
        """Raises GitNotFoundError when git command fails."""
        mock_result = MagicMock(returncode=128, stdout="", stderr="command not found")

        with patch("teambot.worktree.manager.subprocess.run", return_value=mock_result):
            with pytest.raises(GitNotFoundError):
                WorktreeManager.check_git_version()

    def test_raises_git_not_found_on_file_not_found(self):
        """Raises GitNotFoundError when git binary missing."""
        with patch(
            "teambot.worktree.manager.subprocess.run",
            side_effect=FileNotFoundError("git"),
        ):
            with pytest.raises(GitNotFoundError):
                WorktreeManager.check_git_version()

    def test_custom_min_version(self):
        """Supports custom minimum version requirement."""
        mock_result = MagicMock(returncode=0, stdout="git version 2.20.0")

        with patch("teambot.worktree.manager.subprocess.run", return_value=mock_result):
            # Should reject when requiring 2.30+
            with pytest.raises(GitVersionError) as exc_info:
                WorktreeManager.check_git_version("2.30")

        assert exc_info.value.required == "2.30"

    def test_parses_version_with_windows_suffix(self):
        """Handles Windows Git version format."""
        mock_result = MagicMock(returncode=0, stdout="git version 2.39.2.windows.1")

        with patch("teambot.worktree.manager.subprocess.run", return_value=mock_result):
            # Should not raise
            WorktreeManager.check_git_version()


class TestCreateWorktreeValidation:
    """Tests for validation in create_worktree()."""

    @pytest.fixture
    def mock_git_available(self):
        """Mock Git being available."""
        with patch.object(WorktreeManager, "is_git_available", return_value=True):
            yield

    @pytest.fixture
    def mock_git_version_ok(self):
        """Mock Git version check passing."""
        with patch.object(WorktreeManager, "check_git_version"):
            yield

    @pytest.fixture
    def mock_subprocess(self):
        """Mock subprocess.run for Git commands."""
        with patch("teambot.worktree.manager.subprocess.run") as mock:
            yield mock

    def test_checks_git_version_before_creating(
        self, mock_git_available, tmp_path: Path, mock_subprocess
    ):
        """Verifies Git version check happens before worktree creation."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="git version 2.4.0")

        with pytest.raises(GitVersionError):
            WorktreeManager.create_worktree(tmp_path, "feat/test")

    def test_validates_path_length_before_creating(
        self, mock_git_available, mock_git_version_ok, tmp_path: Path
    ):
        """Validates path length before creating worktree."""
        long_branch = "a" * 300

        with patch("teambot.worktree.manager.platform.system", return_value="Windows"):
            with pytest.raises(PathTooLongError):
                WorktreeManager.create_worktree(tmp_path, long_branch)

    def test_version_check_before_path_validation(self, mock_git_available, tmp_path: Path):
        """Git version is checked before path length validation."""
        # This ensures proper error ordering - version check first
        with patch("teambot.worktree.manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="git version 2.4.0")

            with pytest.raises(GitVersionError):
                # Even with a long path, version error comes first
                WorktreeManager.create_worktree(tmp_path, "a" * 300)
