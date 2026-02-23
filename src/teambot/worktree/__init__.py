"""Git worktree management for TeamBot."""

from teambot.worktree.errors import (
    BranchExistsError,
    GitNotFoundError,
    GitVersionError,
    PathTooLongError,
    WorktreeError,
    WorktreeExistsError,
)
from teambot.worktree.manager import WorktreeContext, WorktreeManager, derive_branch_name

__all__ = [
    "WorktreeManager",
    "WorktreeContext",
    "WorktreeError",
    "GitNotFoundError",
    "BranchExistsError",
    "WorktreeExistsError",
    "GitVersionError",
    "PathTooLongError",
    "derive_branch_name",
]
