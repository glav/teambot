<!-- markdownlint-disable-file -->
# Task Details: TeamBot Worktree Isolation

## Research Reference

**Source Research**: .agent-tracking/research/20260223-worktree-isolation-research.md
**Test Strategy**: .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md
**Feature Spec**: .teambot/worktree-isolation/artifacts/feature_spec.md

---

## Phase 1: Worktree Module Foundation

### Task 1.1: Create worktree module directory structure

Create the new `src/teambot/worktree/` module with proper structure.

* **Files**:
  * `src/teambot/worktree/__init__.py` - Module exports
  * `src/teambot/worktree/errors.py` - Exception hierarchy
  * `src/teambot/worktree/manager.py` - WorktreeManager class
  * `tests/test_worktree/__init__.py` - Test module
  * `tests/test_worktree/conftest.py` - Worktree-specific fixtures
* **Success**:
  * Module importable: `from teambot.worktree import WorktreeManager`
  * Test directory exists with fixtures
* **Research References**:
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 200-215) - Project structure
* **Dependencies**:
  * None

**Implementation**:
```python
# src/teambot/worktree/__init__.py
"""Git worktree management for TeamBot."""

from teambot.worktree.errors import (
    BranchExistsError,
    GitNotFoundError,
    WorktreeError,
    WorktreeExistsError,
)
from teambot.worktree.manager import WorktreeContext, WorktreeManager

__all__ = [
    "WorktreeManager",
    "WorktreeContext",
    "WorktreeError",
    "GitNotFoundError",
    "BranchExistsError",
    "WorktreeExistsError",
]
```

---

### Task 1.2: Implement error exception hierarchy

Create custom exceptions for worktree operations.

* **Files**:
  * `src/teambot/worktree/errors.py` - Exception classes
* **Success**:
  * All exception classes defined: WorktreeError, GitNotFoundError, BranchExistsError, WorktreeExistsError
  * Exceptions have meaningful string representations
* **Research References**:
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 510-527) - Error class definitions
  * Feature spec FR-011, FR-012 - Error message requirements
* **Dependencies**:
  * Task 1.1 completion

**Implementation**:
```python
# src/teambot/worktree/errors.py
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
        message = f"Branch '{branch_name}' already exists. Use --branch to specify a different name."
        super().__init__(message)


class WorktreeExistsError(WorktreeError):
    """Worktree path already exists."""

    def __init__(self, path: str):
        self.path = path
        message = f"Worktree path already exists: {path}\nRemove it or use a different --branch name."
        super().__init__(message)


class GitVersionError(WorktreeError):
    """Git version is too old."""

    def __init__(self, version: str, required: str = "2.5"):
        self.version = version
        self.required = required
        message = f"Git version {version} is too old. Git {required}+ is required for worktree support."
        super().__init__(message)


class PathTooLongError(WorktreeError):
    """Path exceeds system limits (Windows 260 chars)."""

    def __init__(self, path: str, length: int, limit: int = 260):
        self.path = path
        self.length = length
        self.limit = limit
        message = f"Path length ({length}) exceeds limit ({limit}): {path}\nUse --branch to specify a shorter branch name."
        super().__init__(message)
```

---

### Task 1.3: Write tests for error classes

Write unit tests for all error exception classes.

* **Files**:
  * `tests/test_worktree/test_errors.py` - Error class tests
* **Success**:
  * All exception classes tested
  * Error messages match specification
  * 100% coverage on errors.py
* **Research References**:
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 193-209) - Error test requirements
* **Dependencies**:
  * Task 1.2 completion

**Test Cases**:
```python
# tests/test_worktree/test_errors.py
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

    def test_git_not_found_error_default_message(self):
        """GitNotFoundError has default message matching FR-011."""
        error = GitNotFoundError()
        assert "Git is required for --worktree mode" in str(error)

    def test_branch_exists_error_message(self):
        """BranchExistsError includes branch name and guidance matching FR-012."""
        error = BranchExistsError("feat/my-feature")
        assert "feat/my-feature" in str(error)
        assert "already exists" in str(error)
        assert "--branch" in str(error)

    def test_worktree_exists_error_message(self):
        """WorktreeExistsError includes path and guidance."""
        error = WorktreeExistsError("/path/to/worktree")
        assert "/path/to/worktree" in str(error)
        assert "--branch" in str(error)

    def test_git_version_error_message(self):
        """GitVersionError includes version info."""
        error = GitVersionError("2.3.0", "2.5")
        assert "2.3.0" in str(error)
        assert "2.5" in str(error)

    def test_path_too_long_error_message(self):
        """PathTooLongError includes length details matching FR-013."""
        error = PathTooLongError("/very/long/path", 275, 260)
        assert "275" in str(error)
        assert "260" in str(error)
```

---

### Task 1.4: Implement `derive_branch_name()` function

Implement branch name derivation from objective filename.

* **Files**:
  * `src/teambot/worktree/manager.py` - Add derive_branch_name function
* **Success**:
  * `objective-foo.md` → `feat/foo`
  * `sdd-objective-auth.md` → `feat/auth`
  * `my-feature.md` → `feat/my-feature`
  * Explicit branch overrides derivation
* **Research References**:
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 255-278) - Branch naming logic
  * Feature spec FR-003, FR-004 - Branch naming requirements
* **Dependencies**:
  * Task 1.1 completion

**Implementation**:
```python
import re
from pathlib import Path


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
```

---

### Task 1.5: Write tests for branch name derivation

Write comprehensive tests for branch name derivation.

* **Files**:
  * `tests/test_worktree/test_branch_naming.py` - Branch naming tests
* **Success**:
  * All derivation patterns tested
  * Edge cases covered (empty, special chars, long names)
  * 100% coverage on derive_branch_name
* **Research References**:
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 88-99) - Test sequence
* **Dependencies**:
  * Task 1.4 completion

**Test Cases**:
```python
# tests/test_worktree/test_branch_naming.py
"""Tests for branch name derivation."""

import pytest
from pathlib import Path

from teambot.worktree.manager import derive_branch_name


class TestBranchNameDerivation:
    """Tests for deriving branch names from objective filenames."""

    @pytest.mark.parametrize("filename,expected", [
        ("my-feature.md", "feat/my-feature"),
        ("objective-foo.md", "feat/foo"),
        ("sdd-objective-auth.md", "feat/auth"),
        ("add-login-page.md", "feat/add-login-page"),
        ("fix-bug-123.md", "feat/fix-bug-123"),
        ("UPPER-CASE.md", "feat/upper-case"),
    ])
    def test_derive_branch_name_patterns(self, filename, expected):
        """Branch name derived correctly from objective filename."""
        result = derive_branch_name(Path(filename))
        assert result == expected

    def test_derive_branch_name_strips_objective_prefix(self):
        """objective- prefix is stripped from filename."""
        result = derive_branch_name(Path("objective-my-feature.md"))
        assert result == "feat/my-feature"

    def test_derive_branch_name_strips_sdd_objective_prefix(self):
        """sdd-objective- prefix is stripped from filename."""
        result = derive_branch_name(Path("sdd-objective-auth.md"))
        assert result == "feat/auth"

    def test_derive_branch_name_explicit_override(self):
        """Explicit branch overrides derivation."""
        result = derive_branch_name(Path("foo.md"), explicit_branch="custom-branch")
        assert result == "feat/custom-branch"

    def test_derive_branch_name_explicit_with_prefix(self):
        """Explicit branch with prefix is preserved."""
        result = derive_branch_name(Path("foo.md"), explicit_branch="fix/bug-123")
        assert result == "fix/bug-123"

    def test_derive_branch_name_empty_after_strip(self):
        """Falls back to 'feature' if filename is empty after stripping."""
        result = derive_branch_name(Path("objective.md"))
        assert result == "feat/feature"

    def test_derive_branch_name_special_chars_removed(self):
        """Special characters are removed from branch name."""
        result = derive_branch_name(Path("my_feature@v2.md"))
        assert result == "feat/myfeaturev2"

    def test_derive_branch_name_spaces_to_hyphens(self):
        """Spaces are converted to hyphens."""
        result = derive_branch_name(Path("my feature name.md"))
        assert result == "feat/my-feature-name"
```

---

### Task 1.6: Implement WorktreeManager class

Implement the main WorktreeManager class with create_worktree and detect methods.

* **Files**:
  * `src/teambot/worktree/manager.py` - Complete WorktreeManager implementation
* **Success**:
  * `create_worktree()` creates Git worktree with new branch
  * `detect_worktree_context()` detects if running in a worktree
  * `is_git_available()` checks Git CLI availability
  * `get_repo_root()` returns repository root path
* **Research References**:
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 529-707) - Complete WorktreeManager implementation
  * Git worktree commands documentation (Lines 167-186)
* **Dependencies**:
  * Task 1.2, Task 1.4 completion

**Implementation**:
```python
# src/teambot/worktree/manager.py
"""Git worktree management for TeamBot."""

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from teambot.worktree.errors import (
    BranchExistsError,
    GitNotFoundError,
    WorktreeError,
    WorktreeExistsError,
)

WORKTREE_BASE_DIR = ".teambot-worktrees"


@dataclass
class WorktreeContext:
    """Context for worktree execution."""

    worktree_path: Path
    branch_name: str
    repo_root: Path
    is_worktree: bool = True


def derive_branch_name(objective_path: Path, explicit_branch: str | None = None) -> str:
    """Derive branch name from objective file."""
    # Implementation from Task 1.4
    ...


class WorktreeManager:
    """Manages Git worktree operations."""

    @staticmethod
    def is_git_available() -> bool:
        """Check if Git CLI is available."""
        return shutil.which("git") is not None

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
            BranchExistsError: Branch already exists
            WorktreeExistsError: Worktree path already exists
            WorktreeError: Other Git errors
        """
        if not cls.is_git_available():
            raise GitNotFoundError()

        # Sanitize branch name for directory (feat/foo → feat-foo)
        dir_name = branch_name.replace("/", "-")
        worktree_path = repo_root / base_dir / dir_name

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
                branch_name = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

                # Get worktree root
                toplevel_result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                worktree_path = Path(toplevel_result.stdout.strip()) if toplevel_result.returncode == 0 else Path.cwd()

                return WorktreeContext(
                    worktree_path=worktree_path,
                    branch_name=branch_name,
                    repo_root=common_dir.parent,
                    is_worktree=True,
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None
```

---

### Task 1.7: Write tests for WorktreeManager

Write comprehensive unit tests for WorktreeManager with mocked subprocess.

* **Files**:
  * `tests/test_worktree/test_manager.py` - WorktreeManager tests
  * `tests/test_worktree/conftest.py` - Add mock_git_subprocess fixture
* **Success**:
  * All WorktreeManager methods tested
  * Subprocess calls mocked
  * Error paths tested
  * 95%+ coverage
* **Research References**:
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 233-268) - Fixture definitions
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 423-479) - Test patterns
* **Dependencies**:
  * Task 1.6 completion

**Fixtures** (`tests/test_worktree/conftest.py`):
```python
"""Fixtures for worktree tests."""

import pytest
from unittest.mock import MagicMock


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
def worktree_context():
    """Provide worktree context for tests."""
    return {
        "branch_name": "feat/test-feature",
        "worktree_path": ".teambot-worktrees/feat-test-feature",
        "objective_file": "objectives/test-feature.md",
    }
```

**Test Cases** (`tests/test_worktree/test_manager.py`):
```python
"""Tests for WorktreeManager class."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from teambot.worktree.manager import WorktreeManager, WorktreeContext
from teambot.worktree.errors import (
    BranchExistsError,
    GitNotFoundError,
    WorktreeExistsError,
)


class TestIsGitAvailable:
    """Tests for Git availability check."""

    def test_git_available(self, mocker):
        """Returns True when git is on PATH."""
        mocker.patch("shutil.which", return_value="/usr/bin/git")
        assert WorktreeManager.is_git_available() is True

    def test_git_not_available(self, mocker):
        """Returns False when git is not on PATH."""
        mocker.patch("shutil.which", return_value=None)
        assert WorktreeManager.is_git_available() is False


class TestGetRepoRoot:
    """Tests for repository root detection."""

    def test_get_repo_root_success(self, mock_git_subprocess):
        """Returns Path when in a Git repository."""
        mock_git_subprocess.return_value.stdout = "/path/to/repo\n"
        result = WorktreeManager.get_repo_root()
        assert result == Path("/path/to/repo")

    def test_get_repo_root_not_in_repo(self, mock_git_subprocess):
        """Returns None when not in a Git repository."""
        mock_git_subprocess.return_value.returncode = 128
        result = WorktreeManager.get_repo_root()
        assert result is None


class TestCreateWorktree:
    """Tests for worktree creation."""

    def test_create_worktree_success(self, mock_git_subprocess, tmp_path, mocker):
        """Creates worktree successfully."""
        mocker.patch("shutil.which", return_value="/usr/bin/git")
        mock_git_subprocess.return_value.returncode = 0

        result = WorktreeManager.create_worktree(tmp_path, "feat/my-feature")

        assert result.branch_name == "feat/my-feature"
        assert result.worktree_path == tmp_path / ".teambot-worktrees" / "feat-my-feature"
        assert result.is_worktree is True

    def test_create_worktree_git_not_found(self, mocker):
        """Raises GitNotFoundError when Git not available."""
        mocker.patch("shutil.which", return_value=None)

        with pytest.raises(GitNotFoundError):
            WorktreeManager.create_worktree(Path("/repo"), "feat/test")

    def test_create_worktree_branch_exists(self, mock_git_subprocess, tmp_path, mocker):
        """Raises BranchExistsError when branch already exists."""
        mocker.patch("shutil.which", return_value="/usr/bin/git")
        mock_git_subprocess.return_value.returncode = 128
        mock_git_subprocess.return_value.stderr = "fatal: a branch named 'feat/test' already exists"

        with pytest.raises(BranchExistsError) as exc_info:
            WorktreeManager.create_worktree(tmp_path, "feat/test")
        
        assert "feat/test" in str(exc_info.value)

    def test_create_worktree_path_exists(self, tmp_path, mocker):
        """Raises WorktreeExistsError when path already exists."""
        mocker.patch("shutil.which", return_value="/usr/bin/git")
        worktree_path = tmp_path / ".teambot-worktrees" / "feat-test"
        worktree_path.mkdir(parents=True)

        with pytest.raises(WorktreeExistsError):
            WorktreeManager.create_worktree(tmp_path, "feat/test")


class TestDetectWorktreeContext:
    """Tests for worktree context detection."""

    def test_detect_not_in_worktree(self, mock_git_subprocess):
        """Returns None when not in a worktree."""
        # git-dir equals common-dir means main worktree
        mock_git_subprocess.side_effect = [
            MagicMock(returncode=0, stdout="true"),  # is-inside-work-tree
            MagicMock(returncode=0, stdout=".git"),  # git-dir
            MagicMock(returncode=0, stdout=".git"),  # git-common-dir
        ]
        
        result = WorktreeManager.detect_worktree_context()
        assert result is None

    def test_detect_in_worktree(self, mock_git_subprocess):
        """Returns WorktreeContext when in a worktree."""
        mock_git_subprocess.side_effect = [
            MagicMock(returncode=0, stdout="true"),  # is-inside-work-tree
            MagicMock(returncode=0, stdout="/repo/.teambot-worktrees/feat-test/.git"),  # git-dir
            MagicMock(returncode=0, stdout="/repo/.git"),  # git-common-dir
            MagicMock(returncode=0, stdout="feat/test"),  # branch name
            MagicMock(returncode=0, stdout="/repo/.teambot-worktrees/feat-test"),  # toplevel
        ]
        
        result = WorktreeManager.detect_worktree_context()
        assert result is not None
        assert result.branch_name == "feat/test"
        assert result.is_worktree is True
```

---

## Phase 2: CLI Integration

### Task 2.1: Add `--worktree` and `--branch` CLI arguments

Add the new flags to the `run` subparser in `create_parser()`.

* **Files**:
  * `src/teambot/cli.py` - Modify create_parser() function
* **Success**:
  * `--worktree` flag parses as boolean
  * `--branch` flag parses as optional string
  * Help text is clear and accurate
* **Research References**:
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 219-232) - CLI argument pattern
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 440-454) - Implementation details
* **Dependencies**:
  * Phase 1 completion

**Implementation** (in `create_parser()`, after existing `run_parser` arguments around line 396):
```python
run_parser.add_argument(
    "--worktree",
    action="store_true",
    help="Run in isolated Git worktree with feature branch",
)
run_parser.add_argument(
    "--branch",
    type=str,
    default=None,
    metavar="NAME",
    help="Branch name for worktree (default: feat/<objective-name>)",
)
```

---

### Task 2.2: Write tests for CLI argument parsing

Write tests for the new CLI flags.

* **Files**:
  * `tests/test_cli.py` - Add tests to TestCLIParser class
* **Success**:
  * `--worktree` flag parsed correctly
  * `--branch` flag parsed correctly
  * Default values correct
  * Backward compatibility verified
* **Research References**:
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 100-124) - CLI parsing tests
* **Dependencies**:
  * Task 2.1 completion

**Test Cases** (add to `tests/test_cli.py`):
```python
class TestCLIParserWorktree:
    """Tests for worktree CLI argument parsing."""

    def test_parser_worktree_flag(self):
        """Parser recognizes --worktree flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "objective.md", "--worktree"])

        assert args.worktree is True

    def test_parser_worktree_flag_default_false(self):
        """--worktree defaults to False."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "objective.md"])

        assert args.worktree is False

    def test_parser_branch_flag(self):
        """Parser recognizes --branch flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "objective.md", "--branch", "custom-name"])

        assert args.branch == "custom-name"

    def test_parser_branch_flag_default_none(self):
        """--branch defaults to None."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "objective.md"])

        assert args.branch is None

    def test_parser_worktree_with_branch(self):
        """Parser handles both --worktree and --branch."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "objective.md", "--worktree", "--branch", "feat/custom"])

        assert args.worktree is True
        assert args.branch == "feat/custom"

    def test_parser_backward_compatibility(self):
        """Existing run command still parses correctly."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "objective.md", "--max-hours", "2"])

        assert args.objective == "objective.md"
        assert args.max_hours == 2.0
        assert args.worktree is False
```

---

### Task 2.3: Integrate worktree creation into `cmd_run()`

Modify `cmd_run()` to handle `--worktree` flag and create worktree before execution.

* **Files**:
  * `src/teambot/cli.py` - Modify cmd_run() function
* **Success**:
  * `--worktree` triggers WorktreeManager.create_worktree()
  * Working directory changes to worktree
  * `teambot_dir` points to worktree's `.teambot/`
  * Error handling for all failure cases
  * Without `--worktree`, behavior unchanged
* **Research References**:
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 369-391) - Code path trace
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 740-754) - State isolation
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 842-875) - Error handling
* **Dependencies**:
  * Task 2.2, Phase 1 completion

**Implementation** (in `cmd_run()`, early in the function after argument validation):
```python
def cmd_run(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    """Run TeamBot with an objective."""
    # Existing validation...
    
    # Handle worktree mode
    worktree_context: WorktreeContext | None = None
    original_cwd = Path.cwd()
    
    if getattr(args, "worktree", False):
        from teambot.worktree import WorktreeManager, derive_branch_name
        from teambot.worktree.errors import (
            BranchExistsError,
            GitNotFoundError,
            WorktreeError,
            WorktreeExistsError,
        )
        
        # Validate Git is available
        if not WorktreeManager.is_git_available():
            display.print_error("Git is required for --worktree mode but was not found.")
            display.print_warning("Install Git and ensure it's on your PATH.")
            return 1
        
        # Get repository root
        repo_root = WorktreeManager.get_repo_root()
        if repo_root is None:
            display.print_error("Not in a Git repository.")
            display.print_warning("--worktree requires a Git repository.")
            return 1
        
        # Derive branch name
        objective_path = Path(args.objective)
        branch_name = derive_branch_name(objective_path, getattr(args, "branch", None))
        
        # Create worktree
        try:
            worktree_context = WorktreeManager.create_worktree(repo_root, branch_name)
            display.print_success(f"Created worktree: {worktree_context.worktree_path}")
            display.print_success(f"Branch: {worktree_context.branch_name}")
            
            # Change to worktree directory
            os.chdir(worktree_context.worktree_path)
            
        except BranchExistsError as e:
            display.print_error(str(e))
            return 1
        except WorktreeExistsError as e:
            display.print_error(str(e))
            return 1
        except WorktreeError as e:
            display.print_error(f"Worktree creation failed: {e}")
            return 1
    
    # ... rest of existing cmd_run() logic ...
    # Pass worktree_context to _run_orchestration() and run_interactive_mode()
```

---

### Task 2.4: Write tests for `cmd_run()` worktree integration

Write unit tests for worktree integration in `cmd_run()`.

* **Files**:
  * `tests/test_cli.py` - Add tests for cmd_run with worktree
* **Success**:
  * Worktree mode triggers WorktreeManager
  * Error cases return appropriate exit codes
  * Without `--worktree`, behavior unchanged (regression test)
  * Directory change verified
* **Research References**:
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 125-151) - cmd_run tests
* **Dependencies**:
  * Task 2.3 completion

**Test Cases**:
```python
class TestCmdRunWorktree:
    """Tests for cmd_run with --worktree flag."""

    def test_cmd_run_no_worktree_unchanged(self, tmp_path, mocker):
        """Running without --worktree behaves as before (regression)."""
        # Test that WorktreeManager is NOT called when --worktree is False
        mock_wm = mocker.patch("teambot.cli.WorktreeManager")
        # ... setup and run cmd_run without --worktree
        mock_wm.create_worktree.assert_not_called()

    def test_cmd_run_worktree_creates_worktree(self, tmp_path, mocker):
        """--worktree triggers worktree creation."""
        # Mock WorktreeManager and verify it's called
        ...

    def test_cmd_run_worktree_git_not_found_error(self, tmp_path, mocker):
        """Git not found returns exit code 1 with clear message."""
        mocker.patch("teambot.worktree.WorktreeManager.is_git_available", return_value=False)
        # ... verify error message and exit code

    def test_cmd_run_worktree_branch_conflict_error(self, tmp_path, mocker):
        """Branch conflict returns exit code 1 with guidance."""
        from teambot.worktree.errors import BranchExistsError
        mocker.patch(
            "teambot.worktree.WorktreeManager.create_worktree",
            side_effect=BranchExistsError("feat/test")
        )
        # ... verify error message includes --branch suggestion
```

---

## Phase 3: UI Indicators

### Task 3.1: Modify REPL prompt to show worktree indicator

Add worktree context display to the REPL prompt.

* **Files**:
  * `src/teambot/repl/loop.py` - Modify REPLLoop class
* **Success**:
  * Prompt shows `[wt:feat/branch]` when in worktree mode
  * Prompt unchanged when not in worktree mode
  * Long branch names truncated appropriately
* **Research References**:
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 779-807) - REPL prompt modification
  * Feature spec FR-009 - REPL indicator requirement
* **Dependencies**:
  * Phase 2 completion

**Implementation**:
```python
class REPLLoop:
    def __init__(
        self,
        console: Console | None = None,
        sdk_client: CopilotSDKClient | None = None,
        config: dict | None = None,
        worktree_context: WorktreeContext | None = None,  # NEW PARAMETER
    ):
        # ... existing init ...
        self._worktree_context = worktree_context

    async def _prompt_user(self) -> str | None:
        """Get user input with worktree indicator."""
        # Build prompt with worktree indicator
        if self._worktree_context:
            branch = self._worktree_context.branch_name
            if len(branch) > 20:
                branch = branch[:17] + "..."
            prompt = f"[bold cyan][wt:{branch}][/bold cyan] [bold green]teambot[/bold green]"
        else:
            prompt = "[bold green]teambot[/bold green]"
        
        loop = asyncio.get_running_loop()
        line = await loop.run_in_executor(
            None, lambda: Prompt.ask(prompt)
        )
        return line
```

---

### Task 3.2: Write tests for REPL prompt indicator

Write tests for the worktree indicator in REPL prompt.

* **Files**:
  * `tests/test_repl/test_loop.py` - Add worktree prompt tests
* **Success**:
  * Prompt includes worktree context when provided
  * Prompt unchanged when context is None
  * Long branch names handled correctly
* **Research References**:
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 152-172) - REPL tests
* **Dependencies**:
  * Task 3.1 completion

---

### Task 3.3: Modify stage header output for worktree context

Add worktree indicator to file-based orchestration stage headers.

* **Files**:
  * `src/teambot/cli.py` - Modify `on_progress` callback in `_run_orchestration()`
* **Success**:
  * Stage headers show `[worktree: feat/branch]` when in worktree mode
  * Headers unchanged when not in worktree mode
* **Research References**:
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 809-821) - Stage header modification
  * Feature spec FR-010 - Stage header indicator requirement
* **Dependencies**:
  * Task 3.2 completion

**Implementation** (modify `_run_orchestration()` to accept worktree_context and update `on_progress`):
```python
def _run_orchestration(
    ...,
    worktree_context: WorktreeContext | None = None,
):
    def on_progress(event_type: str, data: dict) -> None:
        if event_type == "stage_changed":
            stage = data.get("stage", "unknown")
            if worktree_context:
                display.print_success(f"Stage: {stage} [worktree: {worktree_context.branch_name}]")
            else:
                display.print_success(f"Stage: {stage}")
        # ... rest of on_progress
```

---

### Task 3.4: Write tests for stage header indicator

Write tests for worktree indicator in stage headers.

* **Files**:
  * `tests/test_cli.py` - Add stage header tests
* **Success**:
  * Stage header includes worktree context when provided
  * Stage header unchanged when context is None
* **Research References**:
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 173-189) - Stage header tests
* **Dependencies**:
  * Task 3.3 completion

---

## Phase 4: Error Handling Enhancement

### Task 4.1: Implement Windows path length validation

Add validation for Windows 260-character path limit.

* **Files**:
  * `src/teambot/worktree/manager.py` - Add path validation method
* **Success**:
  * Path length checked before worktree creation on Windows
  * PathTooLongError raised with clear message
  * Non-Windows platforms skip validation
* **Research References**:
  * Feature spec FR-013, NFR-004 - Path length requirements
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 59-61) - Path length research need
* **Dependencies**:
  * Phase 1 completion

**Implementation**:
```python
import platform

class WorktreeManager:
    @staticmethod
    def validate_path_length(path: Path) -> None:
        """Validate path length for Windows compatibility.
        
        Raises:
            PathTooLongError: If path exceeds 260 characters on Windows
        """
        if platform.system() == "Windows":
            path_str = str(path.resolve())
            if len(path_str) > 260:
                raise PathTooLongError(path_str, len(path_str), 260)
```

---

### Task 4.2: Implement Git version check (2.5+ required)

Add validation for Git version to ensure worktree support.

* **Files**:
  * `src/teambot/worktree/manager.py` - Add version check method
* **Success**:
  * Git version parsed correctly
  * GitVersionError raised if version < 2.5
  * Clear error message with version requirement
* **Research References**:
  * Feature spec assumption (Git 2.5+)
  * Risk R-005 - Git version check
* **Dependencies**:
  * Task 4.1 completion

**Implementation**:
```python
class WorktreeManager:
    @staticmethod
    def check_git_version(min_version: str = "2.5") -> None:
        """Check Git version meets minimum requirement.
        
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
        except FileNotFoundError:
            raise GitNotFoundError()
```

---

### Task 4.3: Write tests for error scenarios

Write comprehensive tests for all error handling paths.

* **Files**:
  * `tests/test_worktree/test_validation.py` - Error scenario tests
* **Success**:
  * Path length validation tested
  * Git version check tested
  * All error messages match specification
  * 100% coverage on error paths
* **Research References**:
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 193-209) - Error tests
* **Dependencies**:
  * Task 4.2 completion

---

## Phase 5: Acceptance Testing

### Task 5.1: Create acceptance test with real Git worktree operations

Create end-to-end acceptance test using real Git operations.

* **Files**:
  * `tests/test_worktree_acceptance.py` - Acceptance tests with real Git
* **Success**:
  * Test creates actual Git repository in temp directory
  * Worktree created at expected path
  * Branch exists after creation
  * State isolation verified
* **Research References**:
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 522-530) - Acceptance test approach
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 245-268) - temp_git_repo fixture
* **Dependencies**:
  * Phase 2, Phase 3, Phase 4 completion

**Test Structure**:
```python
# tests/test_worktree_acceptance.py
"""Acceptance tests for worktree isolation feature."""

import pytest
import subprocess
from pathlib import Path


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary Git repository for testing."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
    (repo / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo, capture_output=True)
    return repo


@pytest.mark.acceptance
class TestWorktreeIsolationAcceptance:
    """Acceptance tests for worktree isolation feature."""

    def test_at_001_worktree_creation_happy_path(self, temp_git_repo):
        """AT-001: Worktree created at expected path with new branch."""
        from teambot.worktree import WorktreeManager
        
        context = WorktreeManager.create_worktree(temp_git_repo, "feat/test-feature")
        
        assert context.worktree_path.exists()
        assert context.branch_name == "feat/test-feature"
        # Verify branch exists
        result = subprocess.run(
            ["git", "branch", "--list", "feat/test-feature"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )
        assert "feat/test-feature" in result.stdout

    def test_at_002_state_isolation(self, temp_git_repo, monkeypatch):
        """AT-002: State files scoped to worktree directory."""
        from teambot.worktree import WorktreeManager
        
        # Create main .teambot directory
        main_teambot = temp_git_repo / ".teambot"
        main_teambot.mkdir()
        (main_teambot / "main_state.json").write_text("{}")
        
        # Create worktree
        context = WorktreeManager.create_worktree(temp_git_repo, "feat/isolation-test")
        
        # Verify worktree has its own .teambot
        worktree_teambot = context.worktree_path / ".teambot"
        worktree_teambot.mkdir()
        (worktree_teambot / "worktree_state.json").write_text("{}")
        
        # Verify isolation
        assert (main_teambot / "main_state.json").exists()
        assert not (main_teambot / "worktree_state.json").exists()
        assert (worktree_teambot / "worktree_state.json").exists()
        assert not (worktree_teambot / "main_state.json").exists()
```

---

### Task 5.2: Test resume behavior within worktree context

Test that `--resume` works correctly in worktree context.

* **Files**:
  * `tests/test_worktree_acceptance.py` - Add resume tests
* **Success**:
  * Resume from worktree directory works
  * Correct state file loaded from worktree
  * Worktree context detected on resume
* **Research References**:
  * Feature spec FR-007 - Resume in worktree requirement
  * .agent-tracking/test-strategies/20260223-worktree-isolation-test-strategy.md (Lines 326-334) - Resume test
* **Dependencies**:
  * Task 5.1 completion

---

## Phase 6: Documentation

### Task 6.1: Update CLI help text for `--worktree` and `--branch`

Ensure CLI help text is clear and complete.

* **Files**:
  * `src/teambot/cli.py` - Verify help text in add_argument calls
* **Success**:
  * `teambot run --help` shows worktree flags
  * Help text explains purpose and behavior
  * Examples included where helpful
* **Research References**:
  * Feature spec (UX section) - Help text expectations
* **Dependencies**:
  * Phase 5 completion

---

### Task 6.2: Add worktree section to README.md

Add documentation for worktree feature to project README.

* **Files**:
  * `README.md` - Add Worktree Isolation section
* **Success**:
  * Clear explanation of feature purpose
  * Basic usage examples
  * Requirements noted (Git 2.5+)
* **Research References**:
  * .agent-tracking/research/20260223-worktree-isolation-research.md (Lines 344-355) - CLI usage examples
* **Dependencies**:
  * Task 6.1 completion

**Content**:
```markdown
## Worktree Isolation

TeamBot supports isolated execution using Git worktrees, enabling parallel feature development:

```bash
# Run objective in isolated worktree
teambot run objectives/my-feature.md --worktree

# With explicit branch name
teambot run objectives/my-feature.md --worktree --branch feat/custom-name
```

**Requirements**: Git 2.5+

**Behavior**:
- Creates worktree at `.teambot-worktrees/<branch-name>/`
- State files scoped to worktree (no cross-contamination)
- Visual indicators show current branch in REPL and stage headers
- Worktree persists after completion for user review
```

---

### Task 6.3: Create worktree usage guide

Create comprehensive usage guide for worktree feature.

* **Files**:
  * `docs/guides/worktree-isolation.md` - New guide document
* **Success**:
  * Complete feature documentation
  * Usage examples for all scenarios
  * Troubleshooting section
  * Cleanup instructions
* **Research References**:
  * Feature spec (all sections) - Requirements for documentation
* **Dependencies**:
  * Task 6.2 completion

---

## Dependencies

* Git CLI (version 2.5+) - External, user environment
* pytest, pytest-mock, pytest-cov - Dev dependencies (already installed)
* subprocess module - Python standard library

## Success Criteria

* All 6 phases completed with tests passing
* 90%+ coverage on new worktree module
* All acceptance tests pass with real Git operations
* Documentation complete and accurate
* `uv run ruff check . && uv run ruff format --check .` passes
