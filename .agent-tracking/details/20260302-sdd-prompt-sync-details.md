<!-- markdownlint-disable-file -->
# Task Details: SDD Prompt Sync

## Research Reference

**Source Research**: .agent-tracking/research/20260302-sdd-prompt-sync-research.md
**Test Strategy**: .teambot/sdd-prompt-sync/artifacts/test_strategy.md
**Feature Spec**: .teambot/sdd-prompt-sync/artifacts/feature_spec.md

---

## Phase 1: TDD - Core Sync Function Tests

### Task 1.1: Create test file structure

Create the test file for prompt sync module following existing test patterns.

* **Files**:
  * `tests/test_prompt_sync.py` - New test file for prompt_sync module
* **Success**:
  * File created with proper imports and docstring
  * File passes `uv run ruff check tests/test_prompt_sync.py`
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 119-150) - Test patterns from test_scaffolds.py
  * .teambot/sdd-prompt-sync/artifacts/test_strategy.md (Lines 349-408) - Recommended test structure
* **Dependencies**:
  * None

**Implementation**:
```python
"""Unit tests for SDD prompt sync operations - TDD approach.

Core logic is tested directly; selective mocking is used only for
external dependencies (filesystem operations mocked via tmp_path fixture).
"""

from pathlib import Path

import pytest


class TestSyncResult:
    """Tests for SyncResult NamedTuple."""
    pass


class TestSyncSddPrompts:
    """Tests for sync_sdd_prompts() function."""
    pass
```

---

### Task 1.2: Write SyncResult tests

Write tests for the SyncResult NamedTuple structure.

* **Files**:
  * `tests/test_prompt_sync.py` - Add TestSyncResult class tests
* **Success**:
  * Tests verify SyncResult fields: filename, target, copied, reason
  * Tests run (will fail until implementation exists)
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 247-266) - CopyResult pattern from scaffolds.py
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 288-294) - SyncResult definition
* **Dependencies**:
  * Task 1.1 completion

**Test Cases**:
```python
class TestSyncResult:
    """Tests for SyncResult NamedTuple."""

    def test_sync_result_has_required_fields(self):
        """SyncResult has filename, target, copied, reason fields."""
        from teambot.prompt_sync import SyncResult
        
        result = SyncResult(
            filename="sdd.0-initialize.prompt.md",
            target=Path("/tmp/test"),
            copied=True,
            reason="added"
        )
        
        assert result.filename == "sdd.0-initialize.prompt.md"
        assert result.target == Path("/tmp/test")
        assert result.copied is True
        assert result.reason == "added"

    def test_sync_result_skipped_exists_reason(self):
        """SyncResult supports skipped_exists reason."""
        from teambot.prompt_sync import SyncResult
        
        result = SyncResult("test.md", Path("/tmp"), False, "skipped_exists")
        
        assert result.copied is False
        assert result.reason == "skipped_exists"
```

---

### Task 1.3: Write sync_sdd_prompts() tests

Write comprehensive tests for the sync_sdd_prompts() function covering all scenarios.

* **Files**:
  * `tests/test_prompt_sync.py` - Add TestSyncSddPrompts class tests
* **Success**:
  * Tests cover: empty scaffold, adding missing files, skipping existing, force mode
  * Tests follow TDD pattern (written before implementation)
  * Critical safety test: existing files never overwritten without force
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 301-344) - sync_sdd_prompts implementation
  * .teambot/sdd-prompt-sync/artifacts/test_strategy.md (Lines 71-97) - Component 1 test requirements
* **Dependencies**:
  * Task 1.2 completion

**Test Cases** (8 tests):
```python
class TestSyncSddPrompts:
    """Tests for sync_sdd_prompts() function."""

    def test_returns_empty_list_when_scaffold_dir_missing(self, tmp_path, mocker):
        """Returns empty list when scaffold directory doesn't exist."""
        from teambot.prompt_sync import sync_sdd_prompts
        
        # Mock get_scaffolds_dir to return non-existent path
        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "nonexistent"
        )
        
        results = sync_sdd_prompts(tmp_path)
        
        assert results == []

    def test_creates_target_directory_if_missing(self, tmp_path, mocker):
        """Creates .agent/commands/sdd/ if it doesn't exist."""
        from teambot.prompt_sync import sync_sdd_prompts
        
        # Setup scaffold with one file
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text("# Test")
        
        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds"
        )
        
        target_root = tmp_path / "project"
        target_root.mkdir()
        
        results = sync_sdd_prompts(target_root)
        
        assert (target_root / ".agent" / "commands" / "sdd").exists()
        assert len(results) == 1

    def test_adds_missing_file_when_target_empty(self, tmp_path, mocker):
        """Adds prompt file when target directory is empty."""
        from teambot.prompt_sync import sync_sdd_prompts
        
        # Setup scaffold with prompt file
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text("# Scaffold content")
        
        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds"
        )
        
        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        
        results = sync_sdd_prompts(target_root)
        
        assert len(results) == 1
        assert results[0].copied is True
        assert results[0].reason == "added"
        assert results[0].filename == "sdd.0-initialize.prompt.md"
        
        # Verify file was actually copied
        assert (target_dir / "sdd.0-initialize.prompt.md").read_text() == "# Scaffold content"

    def test_skips_existing_file_without_force(self, tmp_path, mocker):
        """Skips existing files - CRITICAL safety test."""
        from teambot.prompt_sync import sync_sdd_prompts
        
        # Setup scaffold
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text("# Scaffold version")
        
        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds"
        )
        
        # Setup existing customized file
        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        existing_file = target_dir / "sdd.0-initialize.prompt.md"
        existing_file.write_text("# My Custom Prompt - DO NOT OVERWRITE")
        original_content = existing_file.read_text()
        
        results = sync_sdd_prompts(target_root, force=False)
        
        assert len(results) == 1
        assert results[0].copied is False
        assert results[0].reason == "skipped_exists"
        
        # CRITICAL: Verify content unchanged
        assert existing_file.read_text() == original_content

    def test_overwrites_with_force_flag(self, tmp_path, mocker):
        """Overwrites existing files when force=True."""
        from teambot.prompt_sync import sync_sdd_prompts
        
        # Setup scaffold
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        scaffold_content = "# Scaffold version - SHOULD REPLACE"
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text(scaffold_content)
        
        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds"
        )
        
        # Setup existing file
        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        existing_file = target_dir / "sdd.0-initialize.prompt.md"
        existing_file.write_text("# Old content")
        
        results = sync_sdd_prompts(target_root, force=True)
        
        assert len(results) == 1
        assert results[0].copied is True
        assert results[0].reason == "added"
        
        # Verify content was overwritten
        assert existing_file.read_text() == scaffold_content

    def test_only_syncs_sdd_pattern_files(self, tmp_path, mocker):
        """Only syncs files matching sdd.*.prompt.md pattern."""
        from teambot.prompt_sync import sync_sdd_prompts
        
        # Setup scaffold with mixed files
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text("# SDD prompt")
        (scaffold_dir / "README.md").write_text("# README - should not sync")
        (scaffold_dir / "other.txt").write_text("Other file")
        
        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds"
        )
        
        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        
        results = sync_sdd_prompts(target_root)
        
        # Only sdd.*.prompt.md should be synced
        assert len(results) == 1
        assert results[0].filename == "sdd.0-initialize.prompt.md"
        
        # Verify README was NOT copied
        assert not (target_dir / "README.md").exists()

    def test_syncs_multiple_files_preserving_existing(self, tmp_path, mocker):
        """Syncs multiple files, preserving existing and adding new."""
        from teambot.prompt_sync import sync_sdd_prompts
        
        # Setup scaffold with 3 files
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text("# Init")
        (scaffold_dir / "sdd.1-create-spec.prompt.md").write_text("# Spec")
        (scaffold_dir / "sdd.2-review.prompt.md").write_text("# Review")
        
        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds"
        )
        
        # Setup target with 1 existing file
        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        (target_dir / "sdd.0-initialize.prompt.md").write_text("# Custom init")
        
        results = sync_sdd_prompts(target_root)
        
        added = [r for r in results if r.copied]
        skipped = [r for r in results if not r.copied]
        
        assert len(added) == 2
        assert len(skipped) == 1
        assert skipped[0].filename == "sdd.0-initialize.prompt.md"

    def test_results_are_sorted_by_filename(self, tmp_path, mocker):
        """Results are returned sorted by filename for predictable output."""
        from teambot.prompt_sync import sync_sdd_prompts
        
        # Setup scaffold with files in non-alphabetical order
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.5-task.prompt.md").write_text("# 5")
        (scaffold_dir / "sdd.1-spec.prompt.md").write_text("# 1")
        (scaffold_dir / "sdd.3-research.prompt.md").write_text("# 3")
        
        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds"
        )
        
        target_root = tmp_path / "project"
        target_root.mkdir()
        
        results = sync_sdd_prompts(target_root)
        
        filenames = [r.filename for r in results]
        assert filenames == sorted(filenames)
```

---

## Phase 2: Sync Function Implementation

### Task 2.1: Create prompt_sync.py module

Create the new module file with module docstring and imports.

* **Files**:
  * `src/teambot/prompt_sync.py` - New module file
* **Success**:
  * File created with proper docstring and imports
  * File passes ruff check
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 529-550) - Module structure
* **Dependencies**:
  * Phase 1 completion

**Implementation**:
```python
"""SDD prompt file synchronization and validation.

This module provides functions for:
- Incrementally syncing SDD prompt files during `teambot init`
- Validating prompt file references before workflow execution
- Detecting orphaned prompt files not referenced by any stage
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from teambot.scaffolds import get_scaffolds_dir
```

---

### Task 2.2: Implement SyncResult NamedTuple

Implement the SyncResult type following CopyResult pattern from scaffolds.py.

* **Files**:
  * `src/teambot/prompt_sync.py` - Add SyncResult class
* **Success**:
  * SyncResult has: filename, target, copied, reason fields
  * TestSyncResult tests pass
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 247-266) - CopyResult pattern
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 288-294) - SyncResult definition
* **Dependencies**:
  * Task 2.1 completion

**Implementation**:
```python
class SyncResult(NamedTuple):
    """Result of a prompt file sync operation.
    
    Attributes:
        filename: Name of the prompt file (e.g., 'sdd.0-initialize.prompt.md')
        target: Full path to target file location
        copied: True if file was copied, False if skipped
        reason: Explanation - 'added', 'skipped_exists', or 'source_missing'
    """
    filename: str
    target: Path
    copied: bool
    reason: str
```

---

### Task 2.3: Implement sync_sdd_prompts() function

Implement the core sync function to pass all TestSyncSddPrompts tests.

* **Files**:
  * `src/teambot/prompt_sync.py` - Add sync_sdd_prompts function
* **Success**:
  * All TestSyncSddPrompts tests pass
  * Function syncs only sdd.*.prompt.md files
  * Preserves existing files unless force=True
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 553-584) - Complete implementation
* **Dependencies**:
  * Task 2.2 completion

**Implementation**:
```python
def get_sdd_prompt_dir() -> Path:
    """Get path to bundled SDD prompt files."""
    return get_scaffolds_dir() / ".agent" / "commands" / "sdd"


def sync_sdd_prompts(
    target_root: Path,
    *,
    force: bool = False,
) -> list[SyncResult]:
    """Sync SDD prompt files from scaffolds to target directory.
    
    Only syncs files matching 'sdd.*.prompt.md' pattern.
    Existing files are preserved unless force=True.
    
    Args:
        target_root: Root directory of user's repository
        force: If True, overwrite existing files
        
    Returns:
        List of SyncResult for each prompt file processed
    """
    results: list[SyncResult] = []
    
    scaffold_dir = get_sdd_prompt_dir()
    target_dir = target_root / ".agent" / "commands" / "sdd"
    
    if not scaffold_dir.exists():
        return results
    
    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Sync each SDD prompt file (sorted for predictable output)
    for scaffold_file in sorted(scaffold_dir.glob("sdd.*.prompt.md")):
        target_file = target_dir / scaffold_file.name
        
        if target_file.exists() and not force:
            results.append(SyncResult(
                scaffold_file.name, target_file, False, "skipped_exists"
            ))
        else:
            shutil.copy2(scaffold_file, target_file)
            results.append(SyncResult(
                scaffold_file.name, target_file, True, "added"
            ))
    
    return results
```

---

## Phase 3: TDD - Validation Function Tests

### Task 3.1: Write ValidationResult and PromptValidationError tests

Write tests for validation result types and error formatting.

* **Files**:
  * `tests/test_prompt_sync.py` - Add TestValidationResult, TestPromptValidationError classes
* **Success**:
  * Tests verify ValidationResult fields
  * Tests verify PromptValidationError message includes remediation command
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 356-379) - ValidationResult and error definition
  * .teambot/sdd-prompt-sync/artifacts/test_strategy.md (Lines 126-141) - Component 3 test requirements
* **Dependencies**:
  * Phase 2 completion

**Test Cases**:
```python
class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_has_required_fields(self):
        """ValidationResult has valid, missing, orphaned fields."""
        from teambot.prompt_sync import ValidationResult
        
        result = ValidationResult(
            valid=True,
            missing=[],
            orphaned=[]
        )
        
        assert result.valid is True
        assert result.missing == []
        assert result.orphaned == []

    def test_validation_result_with_missing_files(self):
        """ValidationResult can hold missing file tuples."""
        from teambot.prompt_sync import ValidationResult
        
        result = ValidationResult(
            valid=False,
            missing=[(".agent/commands/sdd/sdd.9-missing.prompt.md", "CLEANUP")],
            orphaned=[]
        )
        
        assert result.valid is False
        assert len(result.missing) == 1
        assert result.missing[0] == (".agent/commands/sdd/sdd.9-missing.prompt.md", "CLEANUP")


class TestPromptValidationError:
    """Tests for PromptValidationError exception."""

    def test_error_message_includes_missing_files(self):
        """Error message lists all missing files."""
        from teambot.prompt_sync import PromptValidationError
        
        error = PromptValidationError([
            (".agent/commands/sdd/sdd.9-missing.prompt.md", "CLEANUP"),
            (".agent/commands/sdd/sdd.10-other.prompt.md", "DEPLOY"),
        ])
        
        msg = str(error)
        assert "sdd.9-missing.prompt.md" in msg
        assert "sdd.10-other.prompt.md" in msg
        assert "CLEANUP" in msg
        assert "DEPLOY" in msg

    def test_error_message_includes_remediation_command(self):
        """Error message includes 'teambot init' remediation - FR-005."""
        from teambot.prompt_sync import PromptValidationError
        
        error = PromptValidationError([
            (".agent/commands/sdd/sdd.9-missing.prompt.md", "CLEANUP"),
        ])
        
        msg = str(error)
        assert "teambot init" in msg
```

---

### Task 3.2: Write validate_prompt_files() tests

Write comprehensive tests for the validate_prompt_files() function.

* **Files**:
  * `tests/test_prompt_sync.py` - Add TestValidatePromptFiles class
* **Success**:
  * Tests cover: all prompts exist, missing prompts, null prompt_template
  * Tests verify PromptValidationError raised when files missing
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 381-412) - validate_prompt_files implementation
  * .teambot/sdd-prompt-sync/artifacts/test_strategy.md (Lines 126-141) - Component 3 test requirements
* **Dependencies**:
  * Task 3.1 completion

**Test Cases** (6 tests):
```python
class TestValidatePromptFiles:
    """Tests for validate_prompt_files() function."""

    def test_validation_passes_when_all_prompts_exist(self, tmp_path):
        """Validation passes when all referenced prompts exist."""
        from teambot.prompt_sync import validate_prompt_files
        
        # Setup stages.yaml referencing one prompt
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    prompt_template: .agent/commands/sdd/sdd.0-initialize.prompt.md
""")
        
        # Create the referenced prompt file
        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "sdd.0-initialize.prompt.md").write_text("# Test")
        
        result = validate_prompt_files(tmp_path)
        
        assert result.valid is True
        assert result.missing == []

    def test_validation_fails_with_missing_prompt(self, tmp_path):
        """Validation fails when referenced prompt is missing."""
        from teambot.prompt_sync import PromptValidationError, validate_prompt_files
        
        # Setup stages.yaml referencing non-existent prompt
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    prompt_template: .agent/commands/sdd/sdd.99-missing.prompt.md
""")
        
        with pytest.raises(PromptValidationError) as exc_info:
            validate_prompt_files(tmp_path)
        
        assert "sdd.99-missing.prompt.md" in str(exc_info.value)

    def test_validation_skips_null_prompt_template(self, tmp_path):
        """Validation ignores stages with null prompt_template."""
        from teambot.prompt_sync import validate_prompt_files
        
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  COMPLETE:
    prompt_template: null
""")
        
        result = validate_prompt_files(tmp_path)
        
        assert result.valid is True

    def test_validation_returns_valid_when_no_stages_yaml(self, tmp_path):
        """Validation returns valid when stages.yaml doesn't exist."""
        from teambot.prompt_sync import validate_prompt_files
        
        # No stages.yaml in tmp_path
        result = validate_prompt_files(tmp_path)
        
        assert result.valid is True
        assert result.missing == []

    def test_error_includes_stage_name(self, tmp_path):
        """Error message includes the stage that requires the missing file."""
        from teambot.prompt_sync import PromptValidationError, validate_prompt_files
        
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  RESEARCH:
    prompt_template: .agent/commands/sdd/sdd.3-research.prompt.md
""")
        
        with pytest.raises(PromptValidationError) as exc_info:
            validate_prompt_files(tmp_path)
        
        assert "RESEARCH" in str(exc_info.value)

    def test_validation_reports_multiple_missing_files(self, tmp_path):
        """Validation reports all missing files, not just first."""
        from teambot.prompt_sync import PromptValidationError, validate_prompt_files
        
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    prompt_template: .agent/commands/sdd/sdd.0-init.prompt.md
  SPEC:
    prompt_template: .agent/commands/sdd/sdd.1-spec.prompt.md
""")
        
        with pytest.raises(PromptValidationError) as exc_info:
            validate_prompt_files(tmp_path)
        
        msg = str(exc_info.value)
        assert "sdd.0-init.prompt.md" in msg
        assert "sdd.1-spec.prompt.md" in msg
```

---

### Task 3.3: Write detect_orphaned_prompts() tests

Write tests for orphaned file detection.

* **Files**:
  * `tests/test_prompt_sync.py` - Add TestDetectOrphanedPrompts class
* **Success**:
  * Tests cover: no orphans, orphan detected, README ignored
  * Tests verify only sdd.*.prompt.md pattern matched
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 734-763) - detect_orphaned_prompts implementation
  * .teambot/sdd-prompt-sync/artifacts/test_strategy.md (Lines 149-171) - Component 4 test requirements
* **Dependencies**:
  * Task 3.2 completion

**Test Cases** (5 tests):
```python
class TestDetectOrphanedPrompts:
    """Tests for detect_orphaned_prompts() function."""

    def test_returns_empty_when_all_prompts_referenced(self, tmp_path):
        """Returns empty list when all prompt files are referenced."""
        from teambot.prompt_sync import detect_orphaned_prompts
        
        # Setup stages.yaml referencing the prompt
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    prompt_template: .agent/commands/sdd/sdd.0-initialize.prompt.md
""")
        
        # Create the referenced prompt file
        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "sdd.0-initialize.prompt.md").write_text("# Test")
        
        orphaned = detect_orphaned_prompts(tmp_path)
        
        assert orphaned == []

    def test_detects_orphaned_sdd_prompt(self, tmp_path):
        """Detects SDD prompt files not referenced by any stage."""
        from teambot.prompt_sync import detect_orphaned_prompts
        
        # Setup stages.yaml with no prompts
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  COMPLETE:
    prompt_template: null
""")
        
        # Create orphaned prompt file
        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "sdd.legacy.prompt.md").write_text("# Orphan")
        
        orphaned = detect_orphaned_prompts(tmp_path)
        
        assert len(orphaned) == 1
        assert ".agent/commands/sdd/sdd.legacy.prompt.md" in orphaned[0]

    def test_ignores_readme_files(self, tmp_path):
        """Does not report README.md as orphaned."""
        from teambot.prompt_sync import detect_orphaned_prompts
        
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  COMPLETE:
    prompt_template: null
""")
        
        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "README.md").write_text("# SDD Commands")
        
        orphaned = detect_orphaned_prompts(tmp_path)
        
        assert orphaned == []

    def test_only_matches_sdd_pattern(self, tmp_path):
        """Only matches files with sdd.*.prompt.md pattern."""
        from teambot.prompt_sync import detect_orphaned_prompts
        
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  COMPLETE:
    prompt_template: null
""")
        
        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "other.prompt.md").write_text("# Not SDD pattern")
        (prompt_dir / "sdd.legacy.prompt.md").write_text("# SDD pattern")
        
        orphaned = detect_orphaned_prompts(tmp_path)
        
        assert len(orphaned) == 1
        assert "sdd.legacy.prompt.md" in orphaned[0]
        assert "other.prompt.md" not in str(orphaned)

    def test_returns_empty_when_sdd_dir_missing(self, tmp_path):
        """Returns empty list when .agent/commands/sdd/ doesn't exist."""
        from teambot.prompt_sync import detect_orphaned_prompts
        
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    prompt_template: .agent/commands/sdd/sdd.0-init.prompt.md
""")
        
        # No .agent directory
        orphaned = detect_orphaned_prompts(tmp_path)
        
        assert orphaned == []
```

---

## Phase 4: Validation Function Implementation

### Task 4.1: Implement ValidationResult and PromptValidationError

Implement the validation result types.

* **Files**:
  * `src/teambot/prompt_sync.py` - Add ValidationResult and PromptValidationError
* **Success**:
  * TestValidationResult tests pass
  * TestPromptValidationError tests pass
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 356-379) - Implementation
* **Dependencies**:
  * Phase 3 completion

**Implementation**:
```python
@dataclass
class ValidationResult:
    """Result of prompt file validation.
    
    Attributes:
        valid: True if all referenced prompt files exist
        missing: List of (path, stage_name) tuples for missing files
        orphaned: List of file paths not referenced by any stage
    """
    valid: bool
    missing: list[tuple[str, str]]
    orphaned: list[str]


class PromptValidationError(Exception):
    """Raised when prompt file validation fails.
    
    Contains actionable error message with remediation steps.
    """
    
    def __init__(self, missing: list[tuple[str, str]]):
        self.missing = missing
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        lines = ["Missing prompt file(s) referenced in stages.yaml:"]
        for path, stage in self.missing:
            lines.append(f"  - {path} (stage: {stage})")
        lines.append("")
        lines.append("Run 'teambot init' to sync missing SDD prompt files.")
        return "\n".join(lines)
```

---

### Task 4.2: Implement validate_prompt_files() function

Implement the validation function to pass all TestValidatePromptFiles tests.

* **Files**:
  * `src/teambot/prompt_sync.py` - Add validate_prompt_files function
* **Success**:
  * All TestValidatePromptFiles tests pass
  * Raises PromptValidationError when files missing
  * Includes actionable remediation in error message
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 709-731) - Implementation
* **Dependencies**:
  * Task 4.1 completion

**Implementation**:
```python
from teambot.orchestration.stage_config import StagesConfiguration, load_stages_config


def validate_prompt_files(
    project_root: Path,
    stages_config: StagesConfiguration | None = None,
) -> ValidationResult:
    """Validate all prompt_template paths in stages.yaml exist.
    
    Args:
        project_root: Root directory containing stages.yaml
        stages_config: Pre-loaded stages configuration, or None to load
        
    Returns:
        ValidationResult with validation status and details
        
    Raises:
        PromptValidationError: If any referenced prompt files are missing
    """
    stages_yaml = project_root / "stages.yaml"
    if not stages_yaml.exists():
        return ValidationResult(valid=True, missing=[], orphaned=[])
    
    if stages_config is None:
        stages_config = load_stages_config(stages_yaml)
    
    missing: list[tuple[str, str]] = []
    
    for stage, config in stages_config.stages.items():
        if config.prompt_template:
            template_path = project_root / config.prompt_template
            if not template_path.exists():
                missing.append((config.prompt_template, stage.name))
    
    if missing:
        raise PromptValidationError(missing)
    
    return ValidationResult(valid=True, missing=[], orphaned=[])
```

---

### Task 4.3: Implement detect_orphaned_prompts() function

Implement the orphan detection function to pass all TestDetectOrphanedPrompts tests.

* **Files**:
  * `src/teambot/prompt_sync.py` - Add detect_orphaned_prompts function
* **Success**:
  * All TestDetectOrphanedPrompts tests pass
  * Only matches sdd.*.prompt.md pattern
  * Returns empty list for missing directories
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 734-763) - Implementation
* **Dependencies**:
  * Task 4.2 completion

**Implementation**:
```python
def detect_orphaned_prompts(
    project_root: Path,
    stages_config: StagesConfiguration | None = None,
) -> list[str]:
    """Find SDD prompt files not referenced by any stage.
    
    Args:
        project_root: Root directory containing stages.yaml
        stages_config: Pre-loaded stages configuration, or None to load
        
    Returns:
        List of file paths (relative to project_root) for orphaned prompt files
    """
    stages_yaml = project_root / "stages.yaml"
    if not stages_yaml.exists():
        return []
    
    if stages_config is None:
        stages_config = load_stages_config(stages_yaml)
    
    # Get all referenced prompts
    referenced = {
        config.prompt_template
        for config in stages_config.stages.values()
        if config.prompt_template
    }
    
    # Get all SDD prompt files
    sdd_dir = project_root / ".agent" / "commands" / "sdd"
    if not sdd_dir.exists():
        return []
    
    orphaned = []
    for prompt_file in sdd_dir.glob("sdd.*.prompt.md"):
        relative_path = f".agent/commands/sdd/{prompt_file.name}"
        if relative_path not in referenced:
            orphaned.append(relative_path)
    
    return sorted(orphaned)
```

---

## Phase 5: CLI Integration

### Task 5.1: Integrate sync_sdd_prompts() with cmd_init()

Add sync call after scaffold copy in cmd_init() with summary display.

* **Files**:
  * `src/teambot/cli.py` - Modify cmd_init() function
* **Success**:
  * `teambot init` calls sync_sdd_prompts() after copy_all_scaffolds()
  * Summary displayed: "X added, Y skipped"
  * Force flag passed through correctly
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 586-606) - CLI integration
  * .teambot/sdd-prompt-sync/artifacts/feature_spec.md (Lines 133-154) - UX output format
* **Dependencies**:
  * Phase 4 completion

**Integration Point**: After Line 737 in cmd_init() (after scaffold copy results processing)

**Implementation**:
```python
# Import at top of file
from teambot.prompt_sync import sync_sdd_prompts

# In cmd_init(), after scaffold copy results display:
# Sync SDD prompt files incrementally
console.print()
console.print("[bold]Syncing SDD prompt files...[/bold]")

sync_results = sync_sdd_prompts(Path.cwd(), force=force)

if sync_results:
    added = [r for r in sync_results if r.copied]
    skipped = [r for r in sync_results if not r.copied]
    
    for result in sync_results:
        if result.copied:
            console.print(f"  [green]Added:[/green] {result.filename}")
        else:
            console.print(f"  [dim]Skipped (exists):[/dim] {result.filename}")
    
    console.print(f"  [bold]Summary:[/bold] {len(added)} added, {len(skipped)} skipped")
else:
    console.print("  [dim]No SDD prompt files to sync[/dim]")
```

---

### Task 5.2: Integrate validate_prompt_files() with cmd_run()

Add validation call before orchestration start in cmd_run().

* **Files**:
  * `src/teambot/cli.py` - Modify cmd_run() function
* **Success**:
  * Validation runs after config load, before orchestration
  * PromptValidationError caught and displayed with non-zero exit
  * Orphaned files produce warning but don't block
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 766-788) - CLI integration
  * .teambot/sdd-prompt-sync/artifacts/feature_spec.md (Lines 143-153) - Error output format
* **Dependencies**:
  * Task 5.1 completion

**Integration Point**: After config load (~Line 912), before orchestration start

**Implementation**:
```python
# Import at top of file
from teambot.prompt_sync import (
    PromptValidationError,
    detect_orphaned_prompts,
    validate_prompt_files,
)

# In cmd_run(), after config load, before orchestration:
# Validate prompt files (unless skipped)
if not skip_prompt_validation:
    try:
        validate_prompt_files(Path.cwd())
    except PromptValidationError as e:
        console.print(f"[red]✗ Validation failed:[/red]")
        console.print(str(e))
        raise SystemExit(1)
    
    # Warn about orphaned files (non-blocking)
    orphaned = detect_orphaned_prompts(Path.cwd())
    if orphaned:
        console.print("[yellow]⚠ Orphaned prompt files (not referenced by any stage):[/yellow]")
        for path in orphaned:
            console.print(f"  [yellow]⚠[/yellow] {path}")
        console.print()
```

---

### Task 5.3: Add --skip-prompt-validation flag

Add command-line argument to bypass validation.

* **Files**:
  * `src/teambot/cli.py` - Add argument to run command
* **Success**:
  * `--skip-prompt-validation` flag accepted
  * Flag bypasses validate_prompt_files() call
* **Research References**:
  * .agent-tracking/research/20260302-sdd-prompt-sync-research.md (Lines 790-798) - Argument definition
  * .teambot/sdd-prompt-sync/artifacts/feature_spec.md (Line 168) - FR-008 acceptance criteria
* **Dependencies**:
  * Task 5.2 completion

**Implementation**: In the run command definition (Click decorator):

```python
@click.option(
    "--skip-prompt-validation",
    is_flag=True,
    default=False,
    help="Skip validation of prompt file references in stages.yaml",
)
def cmd_run(
    ...,
    skip_prompt_validation: bool,
    ...
):
    ...
```

---

## Phase 6: Acceptance Tests & Coverage

### Task 6.1: Create acceptance test file with AT-001 through AT-006

Create comprehensive acceptance tests matching spec scenarios.

* **Files**:
  * `tests/test_prompt_sync_acceptance.py` - New acceptance test file
* **Success**:
  * All 6 acceptance tests implemented
  * Tests marked with @pytest.mark.acceptance
  * Tests follow existing acceptance test patterns
* **Research References**:
  * .teambot/sdd-prompt-sync/artifacts/feature_spec.md (Lines 289-388) - AT scenarios
  * .teambot/sdd-prompt-sync/artifacts/test_strategy.md (Lines 236-290) - Critical test scenarios
* **Dependencies**:
  * Phase 5 completion

**Acceptance Tests**:
```python
"""Acceptance tests for SDD prompt sync feature (AT-001 through AT-006).

Core logic is tested directly; selective mocking is used only for
external dependencies (filesystem operations via tmp_path fixture).
"""

import pytest


@pytest.mark.acceptance
class TestPromptSyncAcceptance:
    """Acceptance tests for SDD prompt sync feature."""

    def test_at_001_incremental_sync_adds_missing_files(self, tmp_path, mocker):
        """AT-001: Incremental sync adds missing files while preserving existing."""
        # Implementation tests FR-001
        ...

    def test_at_002_validation_blocks_run_when_prompt_missing(self, tmp_path):
        """AT-002: Validation blocks run when prompt file is missing."""
        # Implementation tests FR-003, FR-005
        ...

    def test_at_003_orphaned_files_warning_non_blocking(self, tmp_path):
        """AT-003: Orphaned files produce warning but don't block workflow."""
        # Implementation tests FR-004
        ...

    def test_at_004_status_command_shows_sync_health(self, tmp_path):
        """AT-004: Status command shows prompt sync health."""
        # Implementation tests FR-007 (if implemented)
        ...

    def test_at_005_force_flag_resets_all_prompt_files(self, tmp_path, mocker):
        """AT-005: Force flag resets all prompt files to defaults."""
        # Implementation tests FR-006
        ...

    def test_at_006_skip_validation_flag_bypasses_check(self, tmp_path):
        """AT-006: Skip validation flag bypasses prompt check."""
        # Implementation tests FR-008
        ...
```

---

### Task 6.2: Validate coverage and run final test suite

Run full test suite with coverage validation.

* **Files**:
  * All test files
* **Success**:
  * Coverage >= 90% for prompt_sync.py
  * All tests pass
  * Ruff check passes
* **Research References**:
  * .teambot/sdd-prompt-sync/artifacts/test_strategy.md (Lines 219-234) - Coverage targets
* **Dependencies**:
  * Task 6.1 completion

**Validation Commands**:
```bash
# Run all prompt sync tests with coverage
uv run pytest tests/test_prompt_sync.py tests/test_prompt_sync_acceptance.py \
    --cov=src/teambot/prompt_sync --cov-report=term-missing -v

# Run linting
uv run ruff check . && uv run ruff format --check .

# Run full test suite to ensure no regressions
uv run pytest
```

**Coverage Targets**:
* `sync_sdd_prompts()`: 95%
* `validate_prompt_files()`: 95%
* `detect_orphaned_prompts()`: 85%
* Overall `prompt_sync.py`: 90%+

---

## Dependencies

* pytest >= 7.4.0 (existing)
* pytest-cov >= 4.1.0 (existing)
* pytest-mock >= 3.12.0 (existing)
* pathlib (stdlib)
* shutil (stdlib)
* teambot.scaffolds.get_scaffolds_dir
* teambot.orchestration.stage_config.load_stages_config

## Success Criteria

* All 6 acceptance tests (AT-001 through AT-006) pass
* Unit test coverage >= 90% for prompt_sync.py
* `teambot init` displays sync summary showing added/skipped files
* `teambot run` blocks with actionable error when prompt files missing
* Orphaned files produce warning but don't block workflow
* `--skip-prompt-validation` flag bypasses validation
* All existing tests continue to pass
* `uv run ruff check .` and `uv run ruff format --check .` pass
