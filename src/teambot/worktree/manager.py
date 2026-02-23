"""Git worktree management for TeamBot."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from teambot.worktree.errors import (
    BranchExistsError,
    GitNotFoundError,
    GitVersionError,
    PathTooLongError,
    WorktreeError,
    WorktreeExistsError,
)

WORKTREE_BASE_DIR = ".teambot-worktrees"


@dataclass
class WorktreeContext:
    """Context for worktree execution.

    Attributes:
        worktree_path: Path to the worktree directory
        branch_name: Name of the branch (e.g., "feat/foo")
        repo_root: Path to the main repository root
        is_worktree: Whether this is a worktree (vs main working tree)
    """

    worktree_path: Path
    branch_name: str
    repo_root: Path
    is_worktree: bool = True


def derive_branch_name(objective_path: Path, explicit_branch: str | None = None) -> str:
    """Derive branch name from objective file.

    Priority:
    1. Explicit --branch argument
    2. Derived from objective filename

    Examples:
        objective-foo.md → feat/foo
        sdd-objective-auth.md → feat/auth
        my-feature.md → feat/my-feature

    Args:
        objective_path: Path to the objective file
        explicit_branch: Optional explicit branch name from --branch flag

    Returns:
        Branch name (e.g., "feat/foo")
    """
    if explicit_branch:
        # Ensure it has feat/ prefix if not already prefixed
        if "/" not in explicit_branch:
            return f"feat/{explicit_branch}"
        return explicit_branch

    filename = objective_path.stem.lower()
    # Remove common prefixes
    filename = re.sub(r"^(sdd-)?objective-?", "", filename)
    # Sanitize: replace spaces with hyphens, remove special chars
    filename = re.sub(r"[^a-z0-9-]", "", filename.replace(" ", "-"))
    # Remove consecutive hyphens
    filename = re.sub(r"-+", "-", filename).strip("-")

    if not filename:
        filename = "feature"

    return f"feat/{filename}"


class WorktreeManager:
    """Manages Git worktree operations."""

    # Windows MAX_PATH limit
    WINDOWS_MAX_PATH = 260

    @staticmethod
    def is_git_available() -> bool:
        """Check if Git CLI is available."""
        return shutil.which("git") is not None

    @staticmethod
    def validate_path_length(path: Path) -> None:
        """Validate path length for Windows compatibility.

        Args:
            path: Path to validate

        Raises:
            PathTooLongError: If path exceeds 260 characters on Windows
        """
        if platform.system() == "Windows":
            path_str = str(path.resolve())
            if len(path_str) > WorktreeManager.WINDOWS_MAX_PATH:
                raise PathTooLongError(path_str, len(path_str), WorktreeManager.WINDOWS_MAX_PATH)

    @staticmethod
    def check_git_version(min_version: str = "2.5") -> None:
        """Check Git version meets minimum requirement.

        Git worktrees require Git 2.5+.

        Args:
            min_version: Minimum required version (default: "2.5")

        Raises:
            GitNotFoundError: Git not available
            GitVersionError: Git version too old
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise GitNotFoundError()

            # Parse version: "git version 2.39.2"
            match = re.search(r"(\d+)\.(\d+)", result.stdout)
            if match:
                major, minor = int(match.group(1)), int(match.group(2))
                min_major, min_minor = map(int, min_version.split("."))
                if (major, minor) < (min_major, min_minor):
                    raise GitVersionError(f"{major}.{minor}", min_version)
        except FileNotFoundError as err:
            raise GitNotFoundError() from err

    @staticmethod
    def get_repo_root() -> Path | None:
        """Get the Git repository root, or None if not in a repo."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    @classmethod
    def create_worktree(
        cls,
        repo_root: Path,
        branch_name: str,
        base_dir: str = WORKTREE_BASE_DIR,
    ) -> WorktreeContext:
        """Create a Git worktree with a new branch.

        Args:
            repo_root: Repository root directory
            branch_name: Name of branch to create (e.g., "feat/foo")
            base_dir: Base directory for worktrees (default: .teambot-worktrees)

        Returns:
            WorktreeContext with paths and branch info

        Raises:
            GitNotFoundError: Git CLI not available
            GitVersionError: Git version too old (requires 2.5+)
            PathTooLongError: Path exceeds Windows 260-char limit
            BranchExistsError: Branch already exists
            WorktreeExistsError: Worktree path already exists
            WorktreeError: Other Git errors
        """
        if not cls.is_git_available():
            raise GitNotFoundError()

        # Check Git version before proceeding
        cls.check_git_version()

        # Sanitize branch name for directory (feat/foo → feat-foo)
        dir_name = branch_name.replace("/", "-")
        worktree_path = repo_root / base_dir / dir_name

        # Validate path length on Windows
        cls.validate_path_length(worktree_path)

        if worktree_path.exists():
            raise WorktreeExistsError(str(worktree_path))

        # Ensure base directory exists
        (repo_root / base_dir).mkdir(exist_ok=True)

        result = subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, str(worktree_path)],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "already exists" in stderr:
                raise BranchExistsError(branch_name)
            raise WorktreeError(f"Failed to create worktree: {stderr}")

        return WorktreeContext(
            worktree_path=worktree_path,
            branch_name=branch_name,
            repo_root=repo_root,
        )

    @classmethod
    def detect_worktree_context(cls) -> WorktreeContext | None:
        """Detect if currently running in a worktree.

        Returns:
            WorktreeContext if in a worktree, None otherwise.
        """
        try:
            # Check if we're in a Git work tree
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return None

            # Get the git dir and common dir to detect worktree
            git_dir_result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            common_dir_result = subprocess.run(
                ["git", "rev-parse", "--git-common-dir"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if git_dir_result.returncode != 0 or common_dir_result.returncode != 0:
                return None

            git_dir = Path(git_dir_result.stdout.strip()).resolve()
            common_dir = Path(common_dir_result.stdout.strip()).resolve()

            # If git-dir != common-dir, we're in a worktree
            if git_dir != common_dir:
                # Get branch name
                branch_result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                branch_name = (
                    branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
                )

                # Get worktree root
                toplevel_result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                worktree_path = (
                    Path(toplevel_result.stdout.strip())
                    if toplevel_result.returncode == 0
                    else Path.cwd()
                )

                return WorktreeContext(
                    worktree_path=worktree_path,
                    branch_name=branch_name,
                    repo_root=common_dir.parent,
                    is_worktree=True,
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None
