"""Fixtures for worktree tests."""

from unittest.mock import MagicMock

import pytest


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
def mock_shutil_which(mocker):
    """Mock shutil.which for Git availability check."""
    return mocker.patch("shutil.which", return_value="/usr/bin/git")


@pytest.fixture
def mock_git_version_check(mocker):
    """Mock Git version check to always pass."""
    return mocker.patch(
        "teambot.worktree.manager.WorktreeManager.check_git_version",
        return_value=None,
    )


@pytest.fixture
def worktree_context():
    """Provide worktree context for tests."""
    return {
        "branch_name": "feat/test-feature",
        "worktree_path": ".teambot-worktrees/feat-test-feature",
        "objective_file": "objectives/test-feature.md",
    }
