"""Exceptions for worktree operations."""


class WorktreeError(Exception):
    """Base exception for worktree operations."""

    pass


class GitNotFoundError(WorktreeError):
    """Git CLI is not available."""

    def __init__(self, message: str = "Git is required for --worktree mode but was not found"):
        super().__init__(message)


class BranchExistsError(WorktreeError):
    """Branch already exists in repository."""

    def __init__(self, branch_name: str):
        self.branch_name = branch_name
        message = (
            f"Branch '{branch_name}' already exists. Use --branch to specify a different name."
        )
        super().__init__(message)


class WorktreeExistsError(WorktreeError):
    """Worktree path already exists."""

    def __init__(self, path: str):
        self.path = path
        message = (
            f"Worktree path already exists: {path}\nRemove it or use a different --branch name."
        )
        super().__init__(message)


class GitVersionError(WorktreeError):
    """Git version is too old."""

    def __init__(self, version: str, required: str = "2.5"):
        self.version = version
        self.required = required
        message = (
            f"Git version {version} is too old. Git {required}+ is required for worktree support."
        )
        super().__init__(message)


class PathTooLongError(WorktreeError):
    """Path exceeds system limits (Windows 260 chars)."""

    def __init__(self, path: str, length: int, limit: int = 260):
        self.path = path
        self.length = length
        self.limit = limit
        message = (
            f"Path length ({length}) exceeds limit ({limit}): {path}\n"
            f"Use --branch to specify a shorter branch name."
        )
        super().__init__(message)
