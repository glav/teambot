<!-- markdownlint-disable-file -->
# Task Details: Map Repo Files to Package Location

**Research Reference**: `.agent-tracking/research/20260217-map-repo-files-research.md`
**Test Strategy**: `.teambot/map-repo-files/artifacts/test_strategy.md`
**Plan File**: `.agent-tracking/plans/20260217-map-repo-files-plan.instructions.md`

---

## Phase 1: Test Infrastructure Setup
*(Plan Reference: Lines 57-67)*

### Task 1.1: Create Test File with Fixtures

**File**: `tests/test_scaffolds.py` (NEW)

**Implementation**:

```python
"""Unit tests for scaffolding copy operations - TDD approach."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from teambot.scaffolds import CopyResult


class TestGetScaffoldsDir:
    """Tests for get_scaffolds_dir() function."""

    pass  # Tests added in Phase 2


class TestCopyScaffoldFile:
    """Tests for copy_scaffold_file() function."""

    pass  # Tests added in Phase 3


class TestCopyScaffoldDirectory:
    """Tests for copy_scaffold_directory() function."""

    pass  # Tests added in Phase 4


class TestCopyAllScaffolds:
    """Tests for copy_all_scaffolds() function."""

    pass  # Tests added in Phase 5
```

**Success Criteria**:
- [ ] File created at `tests/test_scaffolds.py`
- [ ] File imports successfully
- [ ] No syntax errors

---

### Task 1.2: Create Acceptance Test File

**File**: `tests/test_init_scaffolds_acceptance.py` (NEW)

**Implementation**:

```python
"""Acceptance tests for init scaffolding feature."""

import pytest


@pytest.mark.acceptance
class TestInitScaffoldingAcceptance:
    """Acceptance tests matching AT-001 through AT-006 from spec."""

    def test_at_001_fresh_repository_initialization(self, tmp_path, monkeypatch):
        """AT-001: Fresh init copies all scaffolding files."""
        pass  # Implemented in Phase 8

    def test_at_002_reinit_preserves_existing_files(self, tmp_path, monkeypatch):
        """AT-002: Re-init never overwrites existing files."""
        pass  # Implemented in Phase 8

    def test_at_003_partial_state_fills_gaps(self, tmp_path, monkeypatch):
        """AT-003: Partial init copies only missing resources."""
        pass  # Implemented in Phase 8

    def test_at_004_empty_directory_handling(self, tmp_path, monkeypatch):
        """AT-004: Empty .github/agents/ gets populated."""
        pass  # Implemented in Phase 8
```

**Success Criteria**:
- [ ] File created at `tests/test_init_scaffolds_acceptance.py`
- [ ] File imports successfully

---

## Phase 2: Resource Locator (TDD)
*(Plan Reference: Lines 69-82)*
*(Research Reference: Lines 139-157)*

### Task 2.1: Write Resource Locator Tests

**File**: `tests/test_scaffolds.py` - Update `TestGetScaffoldsDir` class

**Tests to Add**:

```python
class TestGetScaffoldsDir:
    """Tests for get_scaffolds_dir() function."""

    def test_returns_path_object(self):
        """Function returns a Path object."""
        from teambot.scaffolds import get_scaffolds_dir

        result = get_scaffolds_dir()

        assert isinstance(result, Path)

    def test_scaffolds_dir_exists(self):
        """Scaffolds directory exists in package."""
        from teambot.scaffolds import get_scaffolds_dir

        result = get_scaffolds_dir()

        assert result.exists()

    def test_scaffolds_contains_stages_yaml(self):
        """Scaffolds directory contains stages.yaml."""
        from teambot.scaffolds import get_scaffolds_dir

        result = get_scaffolds_dir()

        assert (result / "stages.yaml").exists()

    def test_scaffolds_contains_agents_md(self):
        """Scaffolds directory contains AGENTS.md."""
        from teambot.scaffolds import get_scaffolds_dir

        result = get_scaffolds_dir()

        assert (result / "AGENTS.md").exists()
```

**Run Command**: `uv run pytest tests/test_scaffolds.py::TestGetScaffoldsDir -v`
**Expected**: All tests FAIL (function not implemented yet)

---

### Task 2.2: Implement get_scaffolds_dir()

**File**: `src/teambot/scaffolds.py` (NEW)

**Implementation** (from Research Lines 163-197):

```python
"""Scaffold file management for teambot init."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def get_scaffolds_dir() -> Path:
    """Get path to bundled scaffold files.

    Returns:
        Path to the scaffolds directory within the installed package.
    """
    pkg = files("teambot")
    scaffolds = pkg.joinpath("scaffolds")

    # Handle both real paths (editable install) and traversable (wheel)
    if hasattr(scaffolds, "_path"):
        return Path(scaffolds._path)
    return Path(str(scaffolds))
```

**Run Command**: `uv run pytest tests/test_scaffolds.py::TestGetScaffoldsDir -v`
**Expected**: All tests PASS

**Success Criteria**:
- [ ] `get_scaffolds_dir()` returns Path object
- [ ] Path exists when package is installed
- [ ] Path contains expected scaffold files

---

## Phase 3: Single File Copier (TDD)
*(Plan Reference: Lines 84-99)*
*(Research Reference: Lines 200-228)*

### Task 3.1: Write File Copier Tests

**File**: `tests/test_scaffolds.py` - Update `TestCopyScaffoldFile` class

**Tests to Add**:

```python
class TestCopyScaffoldFile:
    """Tests for copy_scaffold_file() function."""

    def test_copies_file_when_target_missing(self, tmp_path):
        """Copies file when target doesn't exist."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "stages.yaml"

        result = copy_scaffold_file("stages.yaml", target)

        assert result.copied is True
        assert result.reason == "copied"
        assert target.exists()

    def test_skips_when_target_exists(self, tmp_path):
        """Skips copy when target already exists - CRITICAL safety test."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "stages.yaml"
        target.write_text("existing content")
        original_content = target.read_text()

        result = copy_scaffold_file("stages.yaml", target)

        assert result.copied is False
        assert result.reason == "skipped_exists"
        assert target.read_text() == original_content  # Unchanged!

    def test_force_overwrites_existing(self, tmp_path):
        """Force flag overwrites existing file."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "stages.yaml"
        target.write_text("existing content")

        result = copy_scaffold_file("stages.yaml", target, force=True)

        assert result.copied is True
        assert result.reason == "copied"
        assert target.read_text() != "existing content"

    def test_creates_parent_directories(self, tmp_path):
        """Creates parent directories if needed."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "docs" / "nested" / "file.md"

        result = copy_scaffold_file("sdd-objective-template.md", target)

        assert result.copied is True
        assert target.parent.exists()
        assert target.exists()

    def test_returns_source_missing_for_invalid_source(self, tmp_path):
        """Returns source_missing for non-existent source."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "nonexistent.md"

        result = copy_scaffold_file("does-not-exist.md", target)

        assert result.copied is False
        assert result.reason == "source_missing"
```

**Run Command**: `uv run pytest tests/test_scaffolds.py::TestCopyScaffoldFile -v`
**Expected**: All tests FAIL (function not implemented yet)

---

### Task 3.2: Implement copy_scaffold_file()

**File**: `src/teambot/scaffolds.py` - Add to existing file

**Implementation** (from Research Lines 176-228):

```python
import shutil
from typing import NamedTuple


class CopyResult(NamedTuple):
    """Result of a scaffold copy operation."""

    source: str
    target: Path
    copied: bool
    reason: str  # "copied", "skipped_exists", "source_missing"


def copy_scaffold_file(
    scaffold_name: str,
    target_path: Path,
    *,
    force: bool = False,
) -> CopyResult:
    """Copy a single scaffold file to target location.

    Args:
        scaffold_name: Name of file within scaffolds directory
        target_path: Destination path in user's repository
        force: If True, overwrite existing files

    Returns:
        CopyResult indicating what happened
    """
    source_path = get_scaffolds_dir() / scaffold_name

    if not source_path.exists():
        return CopyResult(scaffold_name, target_path, False, "source_missing")

    if target_path.exists() and not force:
        return CopyResult(scaffold_name, target_path, False, "skipped_exists")

    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source_path, target_path)
    return CopyResult(scaffold_name, target_path, True, "copied")
```

**Run Command**: `uv run pytest tests/test_scaffolds.py::TestCopyScaffoldFile -v`
**Expected**: All tests PASS

**Success Criteria**:
- [ ] File copied when target doesn't exist
- [ ] File NOT copied when target exists (without force)
- [ ] File overwritten when force=True
- [ ] Parent directories created as needed

---

## Phase 4: Directory Tree Copier (TDD)
*(Plan Reference: Lines 101-116)*
*(Research Reference: Lines 231-267)*

### Task 4.1: Write Directory Copier Tests

**File**: `tests/test_scaffolds.py` - Update `TestCopyScaffoldDirectory` class

**Tests to Add**:

```python
class TestCopyScaffoldDirectory:
    """Tests for copy_scaffold_directory() function."""

    def test_copies_directory_when_target_missing(self, tmp_path):
        """Copies directory when target doesn't exist."""
        from teambot.scaffolds import copy_scaffold_directory

        target = tmp_path / ".github" / "agents"

        result = copy_scaffold_directory("agents", target)

        assert result.copied is True
        assert result.reason == "copied"
        assert target.exists()
        assert (target / "pm.agent.md").exists()

    def test_skips_when_directory_not_empty(self, tmp_path):
        """Skips when target directory exists and not empty - CRITICAL."""
        from teambot.scaffolds import copy_scaffold_directory

        target = tmp_path / ".github" / "agents"
        target.mkdir(parents=True)
        (target / "custom.agent.md").write_text("custom agent")

        result = copy_scaffold_directory("agents", target)

        assert result.copied is False
        assert result.reason == "skipped_not_empty"
        # Verify original content preserved
        assert (target / "custom.agent.md").exists()

    def test_copies_into_empty_directory(self, tmp_path):
        """Copies into existing empty directory."""
        from teambot.scaffolds import copy_scaffold_directory

        target = tmp_path / ".github" / "agents"
        target.mkdir(parents=True)
        # Directory exists but is empty

        result = copy_scaffold_directory("agents", target)

        assert result.copied is True
        assert result.reason == "copied"

    def test_force_overwrites_existing_directory(self, tmp_path):
        """Force flag replaces existing directory."""
        from teambot.scaffolds import copy_scaffold_directory

        target = tmp_path / ".github" / "agents"
        target.mkdir(parents=True)
        (target / "custom.agent.md").write_text("custom")

        result = copy_scaffold_directory("agents", target, force=True)

        assert result.copied is True
        # Custom file should be gone, replaced by scaffold
        assert not (target / "custom.agent.md").exists()
        assert (target / "pm.agent.md").exists()

    def test_returns_source_missing_for_invalid_source(self, tmp_path):
        """Returns source_missing for non-existent source directory."""
        from teambot.scaffolds import copy_scaffold_directory

        target = tmp_path / "nonexistent"

        result = copy_scaffold_directory("does-not-exist", target)

        assert result.copied is False
        assert result.reason == "source_missing"
```

**Run Command**: `uv run pytest tests/test_scaffolds.py::TestCopyScaffoldDirectory -v`
**Expected**: All tests FAIL (function not implemented yet)

---

### Task 4.2: Implement copy_scaffold_directory()

**File**: `src/teambot/scaffolds.py` - Add to existing file

**Implementation** (from Research Lines 231-267):

```python
def copy_scaffold_directory(
    scaffold_name: str,
    target_path: Path,
    *,
    force: bool = False,
) -> CopyResult:
    """Copy a scaffold directory to target location.

    Only copies if target doesn't exist or is empty.

    Args:
        scaffold_name: Name of directory within scaffolds
        target_path: Destination path in user's repository
        force: If True, overwrite existing directory

    Returns:
        CopyResult indicating what happened
    """
    source_path = get_scaffolds_dir() / scaffold_name

    if not source_path.exists():
        return CopyResult(scaffold_name, target_path, False, "source_missing")

    # Check if target exists and is non-empty
    if target_path.exists():
        if not force:
            # Check if directory is empty
            if any(target_path.iterdir()):
                return CopyResult(scaffold_name, target_path, False, "skipped_not_empty")
            # Empty directory - remove it so copytree works
            target_path.rmdir()

    # Force mode: remove existing directory
    if target_path.exists() and force:
        shutil.rmtree(target_path)

    # Ensure parent exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copytree(source_path, target_path)
    return CopyResult(scaffold_name, target_path, True, "copied")
```

**Run Command**: `uv run pytest tests/test_scaffolds.py::TestCopyScaffoldDirectory -v`
**Expected**: All tests PASS

**Success Criteria**:
- [ ] Directory copied when target doesn't exist
- [ ] Directory NOT copied when target exists with content
- [ ] Empty directory gets populated
- [ ] Force flag removes and replaces directory

---

## Phase 5: Scaffolding Orchestrator (TDD)
*(Plan Reference: Lines 118-133)*
*(Research Reference: Lines 270-318)*

### Task 5.1: Write Orchestrator Tests

**File**: `tests/test_scaffolds.py` - Update `TestCopyAllScaffolds` class

**Tests to Add**:

```python
class TestCopyAllScaffolds:
    """Tests for copy_all_scaffolds() function."""

    def test_copies_all_files_to_empty_repo(self, tmp_path):
        """Copies all scaffolds to empty repository."""
        from teambot.scaffolds import copy_all_scaffolds

        results = copy_all_scaffolds(tmp_path)

        copied = [r for r in results if r.copied]
        assert len(copied) == 5  # 3 files + 2 directories

        # Verify all expected files exist
        assert (tmp_path / "stages.yaml").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / "docs" / "sdd-objective-template.md").exists()
        assert (tmp_path / ".github" / "agents" / "pm.agent.md").exists()
        assert (tmp_path / ".agent" / "commands").exists()

    def test_skips_existing_files(self, tmp_path):
        """Skips files that already exist."""
        from teambot.scaffolds import copy_all_scaffolds

        # Pre-create some files
        (tmp_path / "stages.yaml").write_text("custom stages")
        (tmp_path / "AGENTS.md").write_text("custom AGENTS")

        results = copy_all_scaffolds(tmp_path)

        skipped = [r for r in results if r.reason == "skipped_exists"]
        assert len(skipped) == 2

        # Verify content unchanged
        assert (tmp_path / "stages.yaml").read_text() == "custom stages"

    def test_handles_mixed_state(self, tmp_path):
        """Copies only missing resources in partial state."""
        from teambot.scaffolds import copy_all_scaffolds

        # Pre-create one file
        (tmp_path / "AGENTS.md").write_text("custom")
        # Pre-create one directory with content
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "custom.md").write_text("custom agent")

        results = copy_all_scaffolds(tmp_path)

        # Should have 2 skipped, 3 copied
        skipped = [r for r in results if not r.copied]
        copied = [r for r in results if r.copied]
        assert len(skipped) == 2  # AGENTS.md and .github/agents/
        assert len(copied) == 3   # stages.yaml, docs/template, .agent/

    def test_force_overwrites_all(self, tmp_path):
        """Force flag overwrites all existing files."""
        from teambot.scaffolds import copy_all_scaffolds

        # Pre-create files
        (tmp_path / "stages.yaml").write_text("custom")
        (tmp_path / "AGENTS.md").write_text("custom")

        results = copy_all_scaffolds(tmp_path, force=True)

        # All should be copied
        copied = [r for r in results if r.copied]
        assert len(copied) == 5

        # Verify overwritten
        assert (tmp_path / "stages.yaml").read_text() != "custom"

    def test_returns_list_of_copy_results(self, tmp_path):
        """Returns list of CopyResult for each scaffold item."""
        from teambot.scaffolds import CopyResult, copy_all_scaffolds

        results = copy_all_scaffolds(tmp_path)

        assert isinstance(results, list)
        assert len(results) == 5
        assert all(isinstance(r, CopyResult) for r in results)
```

**Run Command**: `uv run pytest tests/test_scaffolds.py::TestCopyAllScaffolds -v`
**Expected**: All tests FAIL (function not implemented yet)

---

### Task 5.2: Implement copy_all_scaffolds()

**File**: `src/teambot/scaffolds.py` - Add to existing file

**Implementation** (from Research Lines 270-318):

```python
def copy_all_scaffolds(
    target_root: Path,
    *,
    force: bool = False,
) -> list[CopyResult]:
    """Copy all scaffold files to target repository.

    Args:
        target_root: Root directory of user's repository
        force: If True, overwrite existing files

    Returns:
        List of CopyResult for each scaffold item
    """
    results = []

    # Single files
    results.append(copy_scaffold_file(
        "stages.yaml",
        target_root / "stages.yaml",
        force=force,
    ))

    results.append(copy_scaffold_file(
        "AGENTS.md",
        target_root / "AGENTS.md",
        force=force,
    ))

    results.append(copy_scaffold_file(
        "sdd-objective-template.md",
        target_root / "docs" / "sdd-objective-template.md",
        force=force,
    ))

    # Directories
    results.append(copy_scaffold_directory(
        "agents",
        target_root / ".github" / "agents",
        force=force,
    ))

    results.append(copy_scaffold_directory(
        "agent",
        target_root / ".agent",
        force=force,
    ))

    return results
```

**Run Command**: `uv run pytest tests/test_scaffolds.py::TestCopyAllScaffolds -v`
**Expected**: All tests PASS

**Success Criteria**:
- [ ] All 5 scaffold items processed
- [ ] Returns accurate CopyResult for each
- [ ] Force flag propagates to all operations

---

## Phase 6: Package Bundling
*(Plan Reference: Lines 135-150)*
*(Research Reference: Lines 646-668)*

### Task 6.1: Update pyproject.toml

**File**: `pyproject.toml`

**Changes** - Add after `[tool.hatch.build]` section (around Line 15):

```toml
# Bundle scaffold files into package for teambot init
[tool.hatch.build.targets.wheel.force-include]
"stages.yaml" = "src/teambot/scaffolds/stages.yaml"
"AGENTS.md" = "src/teambot/scaffolds/AGENTS.md"
"docs/sdd-objective-template.md" = "src/teambot/scaffolds/sdd-objective-template.md"
".github/agents" = "src/teambot/scaffolds/agents"
".agent" = "src/teambot/scaffolds/agent"
```

**Location**: Insert after Line 15 (after `include = ["src/teambot/**/*.css"]`)

---

### Task 6.2: Verify Bundle Contents

**Commands**:

```bash
# Build the wheel
uv build

# List wheel contents
unzip -l dist/teambot-*.whl | grep scaffolds

# Expected output should include:
#   src/teambot/scaffolds/stages.yaml
#   src/teambot/scaffolds/AGENTS.md
#   src/teambot/scaffolds/sdd-objective-template.md
#   src/teambot/scaffolds/agents/pm.agent.md
#   src/teambot/scaffolds/agent/commands/
```

**Success Criteria**:
- [ ] Build completes without errors
- [ ] Wheel contains all scaffold files
- [ ] Scaffold directory structure preserved

---

## Phase 7: CLI Integration
*(Plan Reference: Lines 152-167)*
*(Research Reference: Lines 321-377)*

### Task 7.1: Write CLI Integration Tests

**File**: `tests/test_cli.py` - Add to existing `TestCLIInit` class

**Tests to Add** (after existing tests, around Line 134):

```python
def test_init_copies_scaffolds(self, tmp_path, monkeypatch):
    """Init copies scaffold files to new repository."""
    import argparse

    from teambot.cli import ConsoleDisplay, cmd_init

    monkeypatch.chdir(tmp_path)

    args = argparse.Namespace(force=False)
    display = ConsoleDisplay()

    result = cmd_init(args, display)

    assert result == 0
    assert (tmp_path / "stages.yaml").exists()
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / ".github" / "agents").exists()
    assert (tmp_path / ".agent").exists()

def test_init_skips_existing_scaffolds(self, tmp_path, monkeypatch):
    """Init doesn't overwrite existing scaffold files."""
    import argparse

    from teambot.cli import ConsoleDisplay, cmd_init

    monkeypatch.chdir(tmp_path)

    # Create existing file
    (tmp_path / "AGENTS.md").write_text("My custom AGENTS")

    args = argparse.Namespace(force=False)
    display = ConsoleDisplay()

    cmd_init(args, display)

    # Should preserve existing content
    assert (tmp_path / "AGENTS.md").read_text() == "My custom AGENTS"

def test_init_force_overwrites_scaffolds(self, tmp_path, monkeypatch):
    """Init with --force overwrites scaffold files."""
    import argparse

    from teambot.cli import ConsoleDisplay, cmd_init

    monkeypatch.chdir(tmp_path)

    # First init
    cmd_init(argparse.Namespace(force=False), ConsoleDisplay())

    # Modify a file
    (tmp_path / "AGENTS.md").write_text("Modified")

    # Force re-init
    cmd_init(argparse.Namespace(force=True), ConsoleDisplay())

    # Should be overwritten with package version
    assert (tmp_path / "AGENTS.md").read_text() != "Modified"
```

**Run Command**: `uv run pytest tests/test_cli.py::TestCLIInit -v`

---

### Task 7.2: Integrate into cmd_init()

**File**: `src/teambot/cli.py`

**Changes** - Modify `cmd_init()` function (Lines 190-231)

**Add after creating `.teambot` directories** (around Line 222):

```python
    # Copy scaffold files
    from teambot.scaffolds import copy_all_scaffolds

    display.print_success("")
    display.print_success("=== Copying Scaffold Files ===")

    results = copy_all_scaffolds(Path.cwd(), force=force)

    for result in results:
        if result.copied:
            display.print_success(f"  ✅ Copied: {result.target}")
        elif result.reason == "skipped_exists":
            display.print_warning(f"  ⏭️  Skipped (exists): {result.target}")
        elif result.reason == "skipped_not_empty":
            display.print_warning(f"  ⏭️  Skipped (not empty): {result.target}")
        elif result.reason == "source_missing":
            display.print_error(f"  ❌ Missing from package: {result.source}")
```

**Success Criteria**:
- [ ] Scaffold copying happens after directory creation
- [ ] Console output shows status for each item
- [ ] Force flag properly propagates
- [ ] Existing CLI tests still pass

---

## Phase 8: Acceptance Testing & Documentation
*(Plan Reference: Lines 169-184)*

### Task 8.1: Run Acceptance Tests

**File**: `tests/test_init_scaffolds_acceptance.py` - Update with full implementations

**Implementation**:

```python
"""Acceptance tests for init scaffolding feature."""

import argparse

import pytest


@pytest.mark.acceptance
class TestInitScaffoldingAcceptance:
    """Acceptance tests matching spec acceptance criteria."""

    def test_at_001_fresh_repository_initialization(self, tmp_path, monkeypatch):
        """AT-001: Fresh init copies all scaffolding files."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0

        # All 5 scaffold items exist
        assert (tmp_path / "stages.yaml").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / "docs" / "sdd-objective-template.md").exists()
        assert (tmp_path / ".github" / "agents" / "pm.agent.md").exists()
        assert (tmp_path / ".agent" / "commands").exists()

    def test_at_002_reinit_preserves_existing_files(self, tmp_path, monkeypatch):
        """AT-002: Re-init never overwrites existing files."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # First init
        cmd_init(argparse.Namespace(force=False), ConsoleDisplay())

        # Modify files
        original_stages = (tmp_path / "stages.yaml").read_text()
        (tmp_path / "stages.yaml").write_text("MODIFIED")

        # Re-init without force
        cmd_init(argparse.Namespace(force=False), ConsoleDisplay())

        # File should still have modified content
        assert (tmp_path / "stages.yaml").read_text() == "MODIFIED"

    def test_at_003_partial_state_fills_gaps(self, tmp_path, monkeypatch):
        """AT-003: Partial init copies only missing resources."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create only some files manually
        (tmp_path / "AGENTS.md").write_text("custom")

        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        # Custom file preserved
        assert (tmp_path / "AGENTS.md").read_text() == "custom"
        # Missing files created
        assert (tmp_path / "stages.yaml").exists()
        assert (tmp_path / ".agent").exists()

    def test_at_004_empty_directory_handling(self, tmp_path, monkeypatch):
        """AT-004: Empty .github/agents/ gets populated."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create empty directory
        (tmp_path / ".github" / "agents").mkdir(parents=True)

        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        # Directory should be populated
        assert (tmp_path / ".github" / "agents" / "pm.agent.md").exists()
```

**Run Command**: `uv run pytest tests/test_init_scaffolds_acceptance.py -v`
**Expected**: All tests PASS

---

### Task 8.2: Update Documentation

**Files to Update**:
1. `README.md` - Add section about scaffold files
2. `docs/guides/installation.md` - Update init command documentation

**README.md Changes** (add to "Getting Started" section):

```markdown
### Initialize a Repository

```bash
teambot init
```

This command:
- Creates `teambot.json` configuration file
- Creates `.teambot/` directory for workflow state
- Copies scaffold files if they don't exist:
  - `stages.yaml` - Workflow stage definitions
  - `AGENTS.md` - Agent documentation
  - `.github/agents/` - Agent persona definitions
  - `.agent/` - Commands, instructions, and standards
  - `docs/sdd-objective-template.md` - Objective template

Existing files are never overwritten. Use `teambot init --force` to reset all scaffold files.
```

**Success Criteria**:
- [ ] README.md documents new init behavior
- [ ] Installation guide updated
- [ ] Example output shown

---

## Complete Module: src/teambot/scaffolds.py

**Final Implementation** (combining all phases):

```python
"""Scaffold file management for teambot init."""

from __future__ import annotations

import shutil
from importlib.resources import files
from pathlib import Path
from typing import NamedTuple


class CopyResult(NamedTuple):
    """Result of a scaffold copy operation."""

    source: str
    target: Path
    copied: bool
    reason: str  # "copied", "skipped_exists", "skipped_not_empty", "source_missing"


def get_scaffolds_dir() -> Path:
    """Get path to bundled scaffold files.

    Returns:
        Path to the scaffolds directory within the installed package.
    """
    pkg = files("teambot")
    scaffolds = pkg.joinpath("scaffolds")

    # Handle both real paths (editable install) and traversable (wheel)
    if hasattr(scaffolds, "_path"):
        return Path(scaffolds._path)
    return Path(str(scaffolds))


def copy_scaffold_file(
    scaffold_name: str,
    target_path: Path,
    *,
    force: bool = False,
) -> CopyResult:
    """Copy a single scaffold file to target location.

    Args:
        scaffold_name: Name of file within scaffolds directory
        target_path: Destination path in user's repository
        force: If True, overwrite existing files

    Returns:
        CopyResult indicating what happened
    """
    source_path = get_scaffolds_dir() / scaffold_name

    if not source_path.exists():
        return CopyResult(scaffold_name, target_path, False, "source_missing")

    if target_path.exists() and not force:
        return CopyResult(scaffold_name, target_path, False, "skipped_exists")

    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source_path, target_path)
    return CopyResult(scaffold_name, target_path, True, "copied")


def copy_scaffold_directory(
    scaffold_name: str,
    target_path: Path,
    *,
    force: bool = False,
) -> CopyResult:
    """Copy a scaffold directory to target location.

    Only copies if target doesn't exist or is empty.

    Args:
        scaffold_name: Name of directory within scaffolds
        target_path: Destination path in user's repository
        force: If True, overwrite existing directory

    Returns:
        CopyResult indicating what happened
    """
    source_path = get_scaffolds_dir() / scaffold_name

    if not source_path.exists():
        return CopyResult(scaffold_name, target_path, False, "source_missing")

    # Check if target exists and is non-empty
    if target_path.exists():
        if not force:
            # Check if directory is empty
            if any(target_path.iterdir()):
                return CopyResult(scaffold_name, target_path, False, "skipped_not_empty")
            # Empty directory - remove it so copytree works
            target_path.rmdir()

    # Force mode: remove existing directory
    if target_path.exists() and force:
        shutil.rmtree(target_path)

    # Ensure parent exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copytree(source_path, target_path)
    return CopyResult(scaffold_name, target_path, True, "copied")


def copy_all_scaffolds(
    target_root: Path,
    *,
    force: bool = False,
) -> list[CopyResult]:
    """Copy all scaffold files to target repository.

    Args:
        target_root: Root directory of user's repository
        force: If True, overwrite existing files

    Returns:
        List of CopyResult for each scaffold item
    """
    results = []

    # Single files
    results.append(copy_scaffold_file(
        "stages.yaml",
        target_root / "stages.yaml",
        force=force,
    ))

    results.append(copy_scaffold_file(
        "AGENTS.md",
        target_root / "AGENTS.md",
        force=force,
    ))

    results.append(copy_scaffold_file(
        "sdd-objective-template.md",
        target_root / "docs" / "sdd-objective-template.md",
        force=force,
    ))

    # Directories
    results.append(copy_scaffold_directory(
        "agents",
        target_root / ".github" / "agents",
        force=force,
    ))

    results.append(copy_scaffold_directory(
        "agent",
        target_root / ".agent",
        force=force,
    ))

    return results
```

---

## References

| Reference | Location |
|-----------|----------|
| Research Document | `.agent-tracking/research/20260217-map-repo-files-research.md` |
| Test Strategy | `.teambot/map-repo-files/artifacts/test_strategy.md` |
| Feature Spec | `.teambot/map-repo-files/artifacts/feature_spec.md` |
| Existing CLI Code | `src/teambot/cli.py` Lines 190-231 |
| Existing CLI Tests | `tests/test_cli.py` Lines 76-134 |
| pyproject.toml | `pyproject.toml` Lines 1-15 |
