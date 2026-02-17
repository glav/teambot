<!-- markdownlint-disable-file -->
# Research: Map Repo Files to Package Location

**Date**: 2026-02-17  
**Feature**: Enhanced `teambot init` with scaffolding file copying  
**Status**: ✅ Research Complete

---

## 📋 Executive Summary

This research documents the technical approach for enhancing `teambot init` to automatically copy scaffolding files from the installed package to user repositories. The goal is a seamless first-run experience where all required files are in place without manual copying.

### Key Findings

| Aspect | Finding |
|--------|---------|
| **Package Bundling** | Use Hatchling `force-include` to bundle files into `src/teambot/scaffolds/` |
| **File Access** | Use `importlib.resources.files()` (Python 3.9+) for accessing package data |
| **Copy Strategy** | Use `shutil.copytree()` with `dirs_exist_ok=False` for safe conditional copying |
| **Entry Point** | Single entry via `cmd_init()` in `src/teambot/cli.py` (Lines 190-231) |

---

## 🎯 Scope & Requirements

### Success Criteria (from Objective)

- [x] `teambot init` copies `stages.yaml` to repository root if not present
- [x] `teambot init` copies `.github/agents/` directory if not present/empty
- [x] `teambot init` copies `.agent/` directory (commands, instructions, standards) if not present
- [x] `teambot init` copies `docs/sdd-objective-template.md` if not present
- [x] `teambot init` copies `AGENTS.md` to repository root if not present
- [x] Each copy operation is conditional (only if target doesn't exist)
- [x] Existing files are never overwritten (safe re-run)
- [x] Clear console output for copied vs. skipped files

### Files to Bundle

| Source Path (repo root) | Target Path (user repo) | Size | Type |
|------------------------|------------------------|------|------|
| `stages.yaml` | `stages.yaml` | 16K | File |
| `.github/agents/*.agent.md` | `.github/agents/` | 28K | Directory (6 files) |
| `.agent/` | `.agent/` | 316K | Directory tree |
| `docs/sdd-objective-template.md` | `docs/sdd-objective-template.md` | 4K | File |
| `AGENTS.md` | `AGENTS.md` | 8K | File |

**Total bundle size**: ~372K

---

## 🔍 Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches `cmd_init()`? | Implementation Required? |
|-------------|-----------|----------------------|-------------------------|
| `teambot init` | `cli.py:main()` → `cmd_init()` | ✅ YES | ✅ YES |
| `teambot init --force` | `cli.py:main()` → `cmd_init()` | ✅ YES | ✅ YES |
| `uvx teambot init` | Same as above (via entry point) | ✅ YES | ✅ YES |
| `uv run teambot init` | Same as above (via entry point) | ✅ YES | ✅ YES |

### Code Path Trace

#### Entry Point: `teambot init`

1. User runs: `teambot init` or `teambot init --force`
2. Entry point: `teambot.cli:main` (pyproject.toml Line 37)
3. Handled by: `cli.py:main()` (Lines 608-635)
4. Dispatched to: `cli.py:cmd_init()` (Lines 190-231) ✅

```python
# cli.py:620-621
if args.command == "init":
    return cmd_init(args, display)
```

### Coverage Verification

- ✅ All entry points trace to single function: `cmd_init()`
- ✅ No additional entry points needed
- ✅ `--force` flag already handled for config overwrite (extend for scaffold files)

---

## 🏗️ Technical Approach

### Selected Approach: Hatchling `force-include` + `importlib.resources`

#### Why This Approach

| Criteria | force-include | pkg_resources | __file__ approach |
|----------|--------------|---------------|-------------------|
| Works with pip install | ✅ | ✅ | ⚠️ Editable only |
| Works with uvx | ✅ | ✅ | ⚠️ Editable only |
| Modern Python (3.10+) | ✅ | ❌ Deprecated | N/A |
| No runtime dependencies | ✅ | ❌ setuptools | ✅ |
| Supports directories | ✅ | ⚠️ Complex | ✅ |

**Selected**: Hatchling `force-include` for bundling + `importlib.resources.files()` for access

### Package Structure

```
src/teambot/
├── scaffolds/                    # NEW: Bundled scaffold files
│   ├── stages.yaml
│   ├── AGENTS.md
│   ├── sdd-objective-template.md
│   ├── agents/                   # Renamed from .github/agents/
│   │   ├── ba.agent.md
│   │   ├── builder-1.agent.md
│   │   ├── builder-2.agent.md
│   │   ├── pm.agent.md
│   │   ├── reviewer.agent.md
│   │   └── writer.agent.md
│   └── agent/                    # Contents of .agent/ directory
│       ├── commands/
│       ├── instructions/
│       └── standards/
├── __init__.py
├── cli.py                        # MODIFIED: Add scaffold copying
└── ...
```

### pyproject.toml Changes

```toml
[tool.hatch.build.targets.wheel.force-include]
# Bundle scaffold files into package
"stages.yaml" = "src/teambot/scaffolds/stages.yaml"
"AGENTS.md" = "src/teambot/scaffolds/AGENTS.md"
"docs/sdd-objective-template.md" = "src/teambot/scaffolds/sdd-objective-template.md"
".github/agents" = "src/teambot/scaffolds/agents"
".agent" = "src/teambot/scaffolds/agent"
```

### File Access Pattern

```python
from importlib.resources import files, as_file
from pathlib import Path
import shutil

def get_scaffold_path() -> Path:
    """Get path to bundled scaffold files."""
    pkg = files("teambot")
    scaffolds = pkg / "scaffolds"
    
    # For installed packages, we need to extract to temp location
    # But for development (editable install), it's already a real path
    if isinstance(scaffolds, Path):
        return scaffolds
    
    # For zip-imported packages (rare), use traversable API
    return Path(scaffolds._path) if hasattr(scaffolds, '_path') else scaffolds
```

---

## 📁 Implementation Design

### New Module: `src/teambot/scaffolds.py`

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
    reason: str  # "copied", "skipped_exists", "skipped_not_empty"


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
    return Path(scaffolds)


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
            # Empty directory - safe to copy into
    
    # Use copytree with dirs_exist_ok for merging if needed
    if target_path.exists() and force:
        shutil.rmtree(target_path)
    
    shutil.copytree(source_path, target_path, dirs_exist_ok=False)
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

### CLI Integration: `src/teambot/cli.py`

```python
# In cmd_init(), after creating .teambot directory:

def cmd_init(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    """Initialize TeamBot configuration."""
    config_path = Path("teambot.json")
    force = getattr(args, "force", False)

    # Existing config check...
    if config_path.exists() and not force:
        display.print_error(f"Configuration already exists: {config_path}")
        display.print_warning("Use --force to overwrite")
        return 1

    # Create default config (existing code)
    config = create_default_config()
    
    # Optional notification setup (existing code)
    if _should_setup_notifications(display):
        _setup_telegram_notifications(config, display)

    loader = ConfigLoader()
    loader.save(config, config_path)

    # Create .teambot directory (existing code)
    teambot_dir = Path(".teambot")
    teambot_dir.mkdir(exist_ok=True)
    (teambot_dir / "history").mkdir(exist_ok=True)
    (teambot_dir / "state").mkdir(exist_ok=True)

    display.print_success(f"Created configuration: {config_path}")
    display.print_success(f"Created directory: {teambot_dir}")

    # NEW: Copy scaffold files
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

    # Show agents (existing code)
    play_startup_animation(...)
    # ...rest of existing code
```

---

## 🧪 Testing Strategy Research

### Existing Test Infrastructure

| Aspect | Details |
|--------|---------|
| **Framework** | pytest 7.4.0+ with pytest-cov, pytest-mock, pytest-asyncio |
| **Location** | `tests/` directory (mirrors `src/teambot/` structure) |
| **Naming** | `test_*.py` files, `Test*` classes, `test_*` functions |
| **Runner** | `uv run pytest` |
| **Coverage** | 80% target, `--cov=src/teambot --cov-report=term-missing` |

### Existing Test Patterns

**File**: `tests/test_cli.py` (Lines 76-134)

```python
class TestCLIInit:
    """Tests for init command."""

    def test_init_creates_config(self, tmp_path, monkeypatch):
        """Init creates configuration file."""
        import argparse
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / "teambot.json").exists()
        assert (tmp_path / ".teambot").exists()
```

**Key patterns observed**:
- Use `tmp_path` fixture for isolated file operations
- Use `monkeypatch.chdir(tmp_path)` to change working directory
- Use `argparse.Namespace` to create args objects
- Test both success paths and failure paths
- Assert file existence and content

### Recommended Test Structure

```python
# tests/test_scaffolds.py

import pytest
from pathlib import Path

from teambot.scaffolds import (
    CopyResult,
    copy_all_scaffolds,
    copy_scaffold_directory,
    copy_scaffold_file,
    get_scaffolds_dir,
)


class TestGetScaffoldsDir:
    """Tests for get_scaffolds_dir()."""

    def test_returns_path_object(self):
        """Function returns a Path object."""
        result = get_scaffolds_dir()
        assert isinstance(result, Path)

    def test_scaffolds_dir_exists(self):
        """Scaffolds directory exists in package."""
        result = get_scaffolds_dir()
        assert result.exists()

    def test_scaffolds_contains_stages_yaml(self):
        """Scaffolds directory contains stages.yaml."""
        result = get_scaffolds_dir()
        assert (result / "stages.yaml").exists()


class TestCopyScaffoldFile:
    """Tests for copy_scaffold_file()."""

    def test_copies_file_when_target_missing(self, tmp_path):
        """Copies file when target doesn't exist."""
        target = tmp_path / "stages.yaml"
        
        result = copy_scaffold_file("stages.yaml", target)
        
        assert result.copied is True
        assert result.reason == "copied"
        assert target.exists()

    def test_skips_when_target_exists(self, tmp_path):
        """Skips copy when target already exists."""
        target = tmp_path / "stages.yaml"
        target.write_text("existing content")
        
        result = copy_scaffold_file("stages.yaml", target)
        
        assert result.copied is False
        assert result.reason == "skipped_exists"
        assert target.read_text() == "existing content"  # Unchanged

    def test_force_overwrites_existing(self, tmp_path):
        """Force flag overwrites existing file."""
        target = tmp_path / "stages.yaml"
        target.write_text("existing content")
        
        result = copy_scaffold_file("stages.yaml", target, force=True)
        
        assert result.copied is True
        assert result.reason == "copied"
        assert target.read_text() != "existing content"

    def test_creates_parent_directories(self, tmp_path):
        """Creates parent directories if needed."""
        target = tmp_path / "docs" / "sdd-objective-template.md"
        
        result = copy_scaffold_file("sdd-objective-template.md", target)
        
        assert result.copied is True
        assert target.parent.exists()


class TestCopyScaffoldDirectory:
    """Tests for copy_scaffold_directory()."""

    def test_copies_directory_when_target_missing(self, tmp_path):
        """Copies directory when target doesn't exist."""
        target = tmp_path / ".github" / "agents"
        
        result = copy_scaffold_directory("agents", target)
        
        assert result.copied is True
        assert target.exists()
        assert (target / "pm.agent.md").exists()

    def test_skips_when_directory_not_empty(self, tmp_path):
        """Skips when target directory exists and not empty."""
        target = tmp_path / ".github" / "agents"
        target.mkdir(parents=True)
        (target / "custom.md").write_text("custom agent")
        
        result = copy_scaffold_directory("agents", target)
        
        assert result.copied is False
        assert result.reason == "skipped_not_empty"

    def test_copies_into_empty_directory(self, tmp_path):
        """Copies into existing empty directory."""
        target = tmp_path / ".github" / "agents"
        target.mkdir(parents=True)
        
        result = copy_scaffold_directory("agents", target)
        
        assert result.copied is True


class TestCopyAllScaffolds:
    """Tests for copy_all_scaffolds()."""

    def test_copies_all_files_to_empty_repo(self, tmp_path):
        """Copies all scaffolds to empty repository."""
        results = copy_all_scaffolds(tmp_path)
        
        copied = [r for r in results if r.copied]
        assert len(copied) == 5  # 3 files + 2 directories
        
        assert (tmp_path / "stages.yaml").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / "docs" / "sdd-objective-template.md").exists()
        assert (tmp_path / ".github" / "agents" / "pm.agent.md").exists()
        assert (tmp_path / ".agent" / "commands").exists()

    def test_skips_existing_files(self, tmp_path):
        """Skips files that already exist."""
        # Pre-create some files
        (tmp_path / "stages.yaml").write_text("custom stages")
        (tmp_path / "AGENTS.md").write_text("custom AGENTS")
        
        results = copy_all_scaffolds(tmp_path)
        
        skipped = [r for r in results if r.reason == "skipped_exists"]
        assert len(skipped) == 2

    def test_force_overwrites_all(self, tmp_path):
        """Force flag overwrites all existing files."""
        # Pre-create files
        (tmp_path / "stages.yaml").write_text("custom")
        
        results = copy_all_scaffolds(tmp_path, force=True)
        
        # stages.yaml should be copied (overwritten)
        stages_result = next(r for r in results if r.source == "stages.yaml")
        assert stages_result.copied is True


class TestCLIInitWithScaffolds:
    """Tests for init command with scaffold copying."""

    def test_init_copies_scaffolds(self, tmp_path, monkeypatch):
        """Init copies scaffold files."""
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

    def test_init_skips_existing_scaffolds(self, tmp_path, monkeypatch):
        """Init doesn't overwrite existing scaffold files."""
        import argparse
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)
        
        # Create existing files
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

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `scaffolds.py` module | TDD | Core logic with well-defined requirements |
| CLI integration | Code-First | Simple integration into existing function |
| pyproject.toml changes | Manual verification | Build configuration, not code |

---

## 📦 pyproject.toml Full Changes

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/teambot"]

[tool.hatch.build]
include = ["src/teambot/**/*.css"]

# NEW: Bundle scaffold files into package
[tool.hatch.build.targets.wheel.force-include]
"stages.yaml" = "src/teambot/scaffolds/stages.yaml"
"AGENTS.md" = "src/teambot/scaffolds/AGENTS.md"
"docs/sdd-objective-template.md" = "src/teambot/scaffolds/sdd-objective-template.md"
".github/agents" = "src/teambot/scaffolds/agents"
".agent" = "src/teambot/scaffolds/agent"

# ... rest of existing config unchanged
```

---

## ⚠️ Implementation Considerations

### Cross-Platform Compatibility

| Issue | Solution |
|-------|----------|
| Path separators | Use `pathlib.Path` throughout |
| File permissions | `shutil.copy2()` preserves permissions |
| Hidden files (`.agent/`) | Works on all platforms |
| Symlinks | Not expected in scaffold files |

### Edge Cases

| Case | Handling |
|------|----------|
| Running in read-only directory | `shutil.copytree` will raise `PermissionError` - let it propagate |
| Package installed as wheel | `importlib.resources` handles extraction automatically |
| Editable install (development) | `files()` returns real paths directly |
| Empty target directory | Copy into it (not "not empty") |
| Partial scaffold in target | `dirs_exist_ok=False` prevents merging |

### Console Output Design

```
=== Copying Scaffold Files ===
  ✅ Copied: stages.yaml
  ✅ Copied: AGENTS.md
  ✅ Copied: docs/sdd-objective-template.md
  ✅ Copied: .github/agents/ (6 files)
  ⏭️  Skipped (exists): .agent/

Created configuration: teambot.json
Created directory: .teambot
```

---

## 📋 Task Implementation Requests

### Task 1: Update pyproject.toml

**Priority**: High (must be done first for bundling)  
**Files**: `pyproject.toml`  
**Changes**: Add `[tool.hatch.build.targets.wheel.force-include]` section

### Task 2: Create scaffolds module

**Priority**: High  
**Files**: `src/teambot/scaffolds.py` (new)  
**Changes**: Implement `get_scaffolds_dir()`, `copy_scaffold_file()`, `copy_scaffold_directory()`, `copy_all_scaffolds()`

### Task 3: Update CLI init command

**Priority**: High  
**Files**: `src/teambot/cli.py`  
**Changes**: Add scaffold copying after creating `.teambot` directory

### Task 4: Create scaffolds tests

**Priority**: High  
**Files**: `tests/test_scaffolds.py` (new)  
**Changes**: Unit tests for all scaffolds module functions

### Task 5: Update CLI tests

**Priority**: Medium  
**Files**: `tests/test_cli.py`  
**Changes**: Add tests for scaffold copying in `TestCLIInit`

### Task 6: Update documentation

**Priority**: Low  
**Files**: `docs/guides/installation.md`, `README.md`  
**Changes**: Document new init behavior

---

## 🔮 Potential Next Research

| Topic | Why | Priority |
|-------|-----|----------|
| Scaffold versioning | Track which version of scaffolds a repo has | Low |
| `teambot update-scaffolds` | Command to update scaffolds without full init | Low |
| Selective copying | Allow `--no-agents` or `--only stages.yaml` flags | Low |

---

## ✅ Research Validation

```
RESEARCH_VALIDATION: PASS
- Document: CREATED
- Placeholders: 0 remaining
- Technical Approach: DOCUMENTED (Hatchling force-include + importlib.resources)
- Entry Points: 1 traced (cmd_init), 1 covered
- Test Infrastructure: RESEARCHED (pytest, patterns documented)
- Implementation Ready: YES
```

---

## 📚 References

| Source | URL/Path |
|--------|----------|
| Hatchling Build Docs | https://hatch.pypa.io/latest/config/build/#forced-inclusion |
| importlib.resources | Python stdlib, available 3.9+ |
| Current CLI implementation | `src/teambot/cli.py` Lines 190-231 |
| Existing test patterns | `tests/test_cli.py` Lines 76-134 |
| Package config | `pyproject.toml` Lines 1-15 |
