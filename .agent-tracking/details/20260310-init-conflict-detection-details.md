<!-- markdownlint-disable-file -->
# Task Details: Init Conflict Detection

## Research Reference

**Source Research**: .agent-tracking/research/20260310-init-conflict-detection-research.md

---

## Phase 1: Test Core Logic (TDD)

### Task 1.1: Create tests for `extract_numbered_prefix()` function

Add test class `TestExtractNumberedPrefix` to `tests/test_scaffolds.py`.

* **Files**:
  * `tests/test_scaffolds.py` - Add new test class after existing scaffold tests
* **Success**:
  * Tests exist for valid SDD prefix extraction
  * Tests exist for invalid/non-matching filenames
  * Tests fail initially (TDD red phase)
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 234-244) - Regex pattern and test cases
* **Dependencies**:
  * None

**Test Cases**:
```python
class TestExtractNumberedPrefix:
    def test_extracts_valid_sdd_prefix(self):
        from teambot.scaffolds import extract_numbered_prefix
        assert extract_numbered_prefix("sdd.4-task-planner.prompt.md") == "sdd.4-"
        
    def test_extracts_multi_digit_prefix(self):
        from teambot.scaffolds import extract_numbered_prefix
        assert extract_numbered_prefix("sdd.10-something.prompt.md") == "sdd.10-"
        
    def test_returns_none_for_non_sdd_file(self):
        from teambot.scaffolds import extract_numbered_prefix
        assert extract_numbered_prefix("README.md") is None
        
    def test_returns_none_for_partial_match(self):
        from teambot.scaffolds import extract_numbered_prefix
        assert extract_numbered_prefix("sdd-without-number.md") is None
```

---

### Task 1.2: Create tests for `detect_sdd_conflicts()` function

Add test class `TestDetectSddConflicts` to `tests/test_scaffolds.py`.

* **Files**:
  * `tests/test_scaffolds.py` - Add new test class
* **Success**:
  * Tests exist for conflict detection (same prefix, different name)
  * Tests exist for no-conflict scenarios (same file, no overlap)
  * Tests exist for missing directories (graceful handling)
  * Tests fail initially (TDD red phase)
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 246-292) - Detection logic and test cases
* **Dependencies**:
  * None

**Test Cases**:
```python
class TestDetectSddConflicts:
    def test_detects_conflict_same_prefix_different_name(self, tmp_path):
        from teambot.scaffolds import detect_sdd_conflicts
        
        # Setup scaffold with sdd.4-new.prompt.md
        scaffold_sdd = tmp_path / "scaffold" / ".agent" / "commands" / "sdd"
        scaffold_sdd.mkdir(parents=True)
        (scaffold_sdd / "sdd.4-task-planner.prompt.md").write_text("new")
        
        # Setup target with sdd.4-old.prompt.md
        target_sdd = tmp_path / "target" / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-determine-test.prompt.md").write_text("old")
        
        conflicts = detect_sdd_conflicts(tmp_path / "scaffold", tmp_path / "target")
        
        assert len(conflicts) == 1
        assert conflicts[0].prefix == "sdd.4-"
        
    def test_no_conflict_when_same_filename(self, tmp_path):
        # Same file = no conflict
        ...
        
    def test_no_conflict_when_different_prefixes(self, tmp_path):
        # Different prefix numbers = no conflict
        ...
        
    def test_returns_empty_when_target_missing(self, tmp_path):
        # Target dir doesn't exist = empty list
        ...
```

---

### Task 1.3: Create tests for `ConflictInfo` dataclass

Add basic tests for `ConflictInfo` structure.

* **Files**:
  * `tests/test_scaffolds.py` - Add within conflict detection tests
* **Success**:
  * ConflictInfo has prefix, scaffold_name, existing_name fields
  * Tests fail initially (TDD red phase)
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 226-232) - ConflictInfo dataclass
* **Dependencies**:
  * None

**Test Cases**:
```python
def test_conflict_info_has_required_fields(self):
    from teambot.scaffolds import ConflictInfo
    
    conflict = ConflictInfo(
        prefix="sdd.4-",
        scaffold_name="sdd.4-new.prompt.md",
        existing_name="sdd.4-old.prompt.md",
    )
    
    assert conflict.prefix == "sdd.4-"
    assert conflict.scaffold_name == "sdd.4-new.prompt.md"
    assert conflict.existing_name == "sdd.4-old.prompt.md"
```

---

## Phase 2: Implement Core Logic

### Task 2.1: Implement `ConflictInfo` dataclass and `extract_numbered_prefix()` function

Add to `src/teambot/scaffolds.py` after existing imports.

* **Files**:
  * `src/teambot/scaffolds.py` - Add imports, ConflictInfo dataclass, and extract function
* **Success**:
  * `ConflictInfo` dataclass importable from scaffolds
  * `extract_numbered_prefix()` correctly parses `sdd.N-` patterns
  * Task 1.1 and Task 1.3 tests pass
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 222-244) - Implementation code
* **Dependencies**:
  * Task 1.1 and Task 1.3 tests exist

**Implementation**:
```python
# Add at top of scaffolds.py after existing imports
import re
from dataclasses import dataclass

@dataclass
class ConflictInfo:
    """Information about a file conflict."""
    prefix: str           # e.g., "sdd.4-"
    scaffold_name: str    # e.g., "sdd.4-task-planner-for-feature.prompt.md"
    existing_name: str    # e.g., "sdd.4-determine-test-strategy.prompt.md"

def extract_numbered_prefix(filename: str) -> str | None:
    """Extract numbered prefix from SDD prompt filename.
    
    Args:
        filename: e.g., "sdd.4-task-planner-for-feature.prompt.md"
    
    Returns:
        Prefix like "sdd.4-" or None if not matching pattern
    """
    match = re.match(r'^(sdd\.\d+-)', filename)
    return match.group(1) if match else None
```

---

### Task 2.2: Implement `detect_sdd_conflicts()` function

Add to `src/teambot/scaffolds.py` after `extract_numbered_prefix`.

* **Files**:
  * `src/teambot/scaffolds.py` - Add detect function
* **Success**:
  * `detect_sdd_conflicts()` returns list of conflicts
  * Returns empty list when no conflicts or directories missing
  * Task 1.2 tests pass
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 246-292) - Implementation code
* **Dependencies**:
  * Task 2.1 complete

**Implementation**:
```python
def detect_sdd_conflicts(
    scaffold_dir: Path,
    target_dir: Path,
) -> list[ConflictInfo]:
    """Detect SDD prompt file conflicts.
    
    Looks for files with same numbered prefix but different names.
    
    Args:
        scaffold_dir: Path to scaffold root directory
        target_dir: Path to target root directory
        
    Returns:
        List of ConflictInfo for each detected conflict
    """
    scaffold_sdd = scaffold_dir / ".agent" / "commands" / "sdd"
    target_sdd = target_dir / ".agent" / "commands" / "sdd"
    
    if not scaffold_sdd.exists() or not target_sdd.exists():
        return []
    
    # Build prefix -> filename maps
    scaffold_prefixes: dict[str, str] = {}
    for f in scaffold_sdd.glob("sdd.*.prompt.md"):
        prefix = extract_numbered_prefix(f.name)
        if prefix:
            scaffold_prefixes[prefix] = f.name
    
    target_prefixes: dict[str, str] = {}
    for f in target_sdd.glob("sdd.*.prompt.md"):
        prefix = extract_numbered_prefix(f.name)
        if prefix:
            target_prefixes[prefix] = f.name
    
    # Find conflicts: same prefix, different name
    conflicts = []
    for prefix, scaffold_name in scaffold_prefixes.items():
        if prefix in target_prefixes:
            existing_name = target_prefixes[prefix]
            if scaffold_name != existing_name:
                conflicts.append(ConflictInfo(prefix, scaffold_name, existing_name))
    
    return sorted(conflicts, key=lambda c: c.prefix)
```

---

## Phase 3: Test Backup Infrastructure (TDD)

### Task 3.1: Create tests for `backup_directory()` function

Add test class `TestBackupDirectory` to `tests/test_scaffolds.py`.

* **Files**:
  * `tests/test_scaffolds.py` - Add new test class
* **Success**:
  * Tests exist for successful backup with timestamp
  * Tests exist for source not existing (raises FileNotFoundError)
  * Tests exist for move operation (source removed, backup exists)
  * Tests fail initially (TDD red phase)
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 296-330) - Backup function and test cases
* **Dependencies**:
  * None (can run parallel to Phase 2)

**Test Cases**:
```python
import re

class TestBackupDirectory:
    def test_creates_timestamped_backup(self, tmp_path):
        from teambot.scaffolds import backup_directory
        
        source = tmp_path / ".agent"
        source.mkdir()
        (source / "test.txt").write_text("content")
        backup_root = tmp_path / ".agent-tracking" / "backups"
        
        result = backup_directory(source, backup_root)
        
        assert not source.exists()  # Moved, not copied
        assert result.exists()
        assert (result / "test.txt").exists()
        # Timestamp folder format: YYYYMMDD-HHMMSS
        assert re.match(r"\d{8}-\d{6}", result.parent.name)
        
    def test_raises_for_missing_source(self, tmp_path):
        from teambot.scaffolds import backup_directory
        import pytest
        
        with pytest.raises(FileNotFoundError):
            backup_directory(tmp_path / "nonexistent", tmp_path / "backups")
            
    def test_preserves_directory_structure(self, tmp_path):
        from teambot.scaffolds import backup_directory
        
        source = tmp_path / ".agent"
        (source / "commands" / "sdd").mkdir(parents=True)
        (source / "commands" / "sdd" / "test.prompt.md").write_text("content")
        backup_root = tmp_path / "backups"
        
        result = backup_directory(source, backup_root)
        
        assert (result / "commands" / "sdd" / "test.prompt.md").exists()
```

---

## Phase 4: Implement Backup Infrastructure

### Task 4.1: Implement `backup_directory()` function

Add to `src/teambot/scaffolds.py`.

* **Files**:
  * `src/teambot/scaffolds.py` - Add backup function and datetime import
* **Success**:
  * `backup_directory()` moves source to timestamped backup location
  * Creates parent directories as needed
  * Returns path to created backup
  * Task 3.1 tests pass
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 296-330) - Implementation code
* **Dependencies**:
  * Task 3.1 tests exist

**Implementation**:
```python
from datetime import datetime

def backup_directory(source: Path, backup_root: Path) -> Path:
    """Move directory to timestamped backup location.
    
    Args:
        source: Directory to back up (e.g., .agent/)
        backup_root: Parent for backups (e.g., .agent-tracking/backups/)
        
    Returns:
        Path to created backup directory
        
    Raises:
        FileNotFoundError: If source doesn't exist
    """
    if not source.exists():
        raise FileNotFoundError(f"Cannot backup: {source} does not exist")
    
    # Generate filesystem-safe timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = backup_root / timestamp / source.name
    
    # Ensure backup parent exists
    backup_dir.parent.mkdir(parents=True, exist_ok=True)
    
    # Move source to backup
    shutil.move(str(source), str(backup_dir))
    
    return backup_dir
```

---

## Phase 5: CLI Integration

### Task 5.1: Implement `prompt_conflict_resolution()` function

Add to `src/teambot/cli.py`.

* **Files**:
  * `src/teambot/cli.py` - Add new function after existing prompt functions
* **Success**:
  * Function displays conflict summary with clear formatting
  * Accepts 1/2/3 input and returns "replace"/"backup"/"skip"
  * Handles EOF/KeyboardInterrupt gracefully (returns "skip")
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 339-385) - Implementation code
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 203-210) - Input pattern reference
* **Dependencies**:
  * Phase 2 complete (ConflictInfo available)

**Implementation**:
```python
from typing import Literal
from teambot.scaffolds import ConflictInfo

ConflictResolution = Literal["replace", "backup", "skip"]

def prompt_conflict_resolution(
    conflicts: list[ConflictInfo],
    display: ConsoleDisplay,
) -> ConflictResolution:
    """Prompt user to resolve scaffold conflicts."""
    display.print_warning("")
    display.print_warning("⚠ Conflict detected in .agent/commands/sdd/:")
    display.print_warning("")
    display.print_info("  The target directory contains files with conflicting prefixes:")
    display.print_info("")
    
    for conflict in conflicts:
        display.print_info(f"  {conflict.prefix}*:")
        display.print_warning(f"    - Existing: {conflict.existing_name}")
        display.print_success(f"    - New:      {conflict.scaffold_name}")
    
    display.print_info("")
    display.print_info("How would you like to proceed?")
    display.print_info("")
    display.print_info("  [1] Replace - Clear existing directory and copy new scaffolds")
    display.print_info("  [2] Backup  - Move existing to .agent-tracking/backups/ then copy new")
    display.print_info("  [3] Skip    - Keep existing files (may cause workflow confusion)")
    display.print_info("")
    
    try:
        while True:
            response = input("Choice [1/2/3]: ").strip()
            if response == "1":
                return "replace"
            elif response == "2":
                return "backup"
            elif response == "3":
                return "skip"
            else:
                display.print_warning("Please enter 1, 2, or 3")
    except (EOFError, KeyboardInterrupt):
        display.print_warning("\nOperation cancelled, keeping existing files")
        return "skip"
```

---

### Task 5.2: Add `--on-conflict` CLI flag to init parser

Modify `create_parser()` in `src/teambot/cli.py`.

* **Files**:
  * `src/teambot/cli.py` - Add argument to init subparser (after line 550)
* **Success**:
  * `--on-conflict` flag accepts replace/backup/skip values
  * Flag is optional with None default
  * Help text explains each option
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 407-415) - Parser addition
* **Dependencies**:
  * None

**Implementation**:
```python
# Add after line 550 (after --force argument)
init_parser.add_argument(
    "--on-conflict",
    choices=["replace", "backup", "skip"],
    default=None,
    help="How to handle scaffold conflicts: replace (clear and copy), backup (preserve to .agent-tracking/backups/), skip (keep existing)",
)
```

---

### Task 5.3: Update `cmd_init()` to invoke conflict detection and prompt

Modify `cmd_init()` in `src/teambot/cli.py`.

* **Files**:
  * `src/teambot/cli.py` - Modify cmd_init function (lines 691-790)
* **Success**:
  * Conflict detection runs before scaffold copying
  * Interactive prompt displayed when conflicts found (and no flags)
  * `--on-conflict` flag bypasses prompt
  * `--force` bypasses all conflict detection (existing behavior)
  * Replace action clears directory
  * Backup action moves to `.agent-tracking/backups/` then copies
  * Skip action keeps existing (current `skipped_not_empty` behavior)
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 109-156) - Code path trace
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 596-624) - CLI usage examples
* **Dependencies**:
  * Tasks 5.1, 5.2, Phase 2, Phase 4 complete

**Implementation Approach**:

1. After `force = getattr(args, "force", False)`, add `on_conflict = getattr(args, "on_conflict", None)`
2. Before `copy_all_scaffolds()` call (before line 726), add conflict detection:
   ```python
   # Check for conflicts in .agent directory
   from teambot.scaffolds import detect_sdd_conflicts, get_scaffolds_dir, backup_directory
   
   target_agent = Path.cwd() / ".agent"
   if target_agent.exists() and not force:
       conflicts = detect_sdd_conflicts(get_scaffolds_dir(), Path.cwd())
       if conflicts:
           # Determine resolution
           if on_conflict:
               resolution = on_conflict
           else:
               import sys
               if sys.stdin.isatty():
                   resolution = prompt_conflict_resolution(conflicts, display)
               else:
                   resolution = "skip"
           
           # Apply resolution
           if resolution == "replace":
               shutil.rmtree(target_agent)
               display.print_info("Cleared existing .agent directory")
           elif resolution == "backup":
               backup_root = Path.cwd() / ".agent-tracking" / "backups"
               backup_path = backup_directory(target_agent, backup_root)
               display.print_success(f"Backed up to: {backup_path}")
           elif resolution == "skip":
               display.print_warning("Keeping existing .agent directory")
   ```

3. Add `import shutil` if not already present in cli.py imports

---

## Phase 6: Integration Tests and Validation

### Task 6.1: Create CLI integration tests for conflict scenarios

Add test class `TestInitConflictHandling` to `tests/test_cli.py`.

* **Files**:
  * `tests/test_cli.py` - Add new test class
* **Success**:
  * Test conflict detection triggers prompt
  * Test `--on-conflict=replace` clears and copies
  * Test `--on-conflict=backup` creates backup
  * Test `--on-conflict=skip` keeps existing
  * Test `--force` bypasses conflict detection
  * Test non-interactive mode defaults to skip
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 79-88) - Test markers
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 574-588) - Input mocking pattern
* **Dependencies**:
  * Phase 5 complete

**Test Cases**:
```python
class TestInitConflictHandling:
    def test_on_conflict_replace_clears_directory(self, tmp_path, monkeypatch):
        """--on-conflict=replace clears existing .agent directory."""
        monkeypatch.chdir(tmp_path)
        # Setup: create conflicting .agent directory
        ...
        # Run init with --on-conflict=replace
        ...
        # Assert: new scaffolds in place
        
    def test_on_conflict_backup_preserves_existing(self, tmp_path, monkeypatch):
        """--on-conflict=backup moves to backups directory."""
        ...
        
    def test_on_conflict_skip_keeps_existing(self, tmp_path, monkeypatch):
        """--on-conflict=skip leaves existing files unchanged."""
        ...
        
    def test_force_bypasses_conflict_detection(self, tmp_path, monkeypatch):
        """--force replaces without conflict prompt."""
        ...
        
    def test_interactive_prompt_shows_on_conflict(self, tmp_path, monkeypatch):
        """Interactive prompt appears when conflicts detected."""
        inputs = iter(["2"])  # Choose backup
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        ...
```

---

### Task 6.2: End-to-end validation of all acceptance scenarios

Validate all 6 acceptance test scenarios from specification.

* **Files**:
  * Manual validation (or add `@pytest.mark.acceptance` tests)
* **Success**:
  * AT-001: Fresh init works unchanged
  * AT-002: Init with different content (no prompt files) works unchanged
  * AT-003: Conflict detection displays warning
  * AT-004: Replace option clears and copies
  * AT-005: Backup option preserves to timestamped directory
  * AT-006: Skip option keeps existing with warning
* **Research References**:
  * .agent-tracking/research/20260310-init-conflict-detection-research.md (Lines 93-94) - Acceptance test markers
* **Dependencies**:
  * Task 6.1 complete

**Validation Commands**:
```bash
# Run all new tests
uv run pytest tests/test_scaffolds.py tests/test_cli.py -v -k "conflict or backup or prefix" --no-header

# Run full test suite to check for regressions
uv run pytest --cov=src/teambot --cov-report=term-missing

# Manual E2E validation
cd /tmp && mkdir test-repo && cd test-repo && git init
# Create conflicting .agent directory
mkdir -p .agent/commands/sdd
echo "old" > .agent/commands/sdd/sdd.4-old-name.prompt.md
# Run init and verify prompt
uv run teambot init
```

---

## Dependencies

* pytest (existing)
* Python 3.10+ (for `|` union types)
* shutil (stdlib)
* re (stdlib)
* dataclasses (stdlib)
* datetime (stdlib)

## Success Criteria

* All TDD tests pass (Phases 1-4)
* CLI integration tests pass (Phase 6)
* Interactive prompt displays clearly with 3 options
* `--on-conflict` flag works in all modes
* `--force` continues to work as before
* Backup creates timestamped directories
* No regression in existing init behavior
* Code passes `uv run ruff check . && uv run ruff format --check .`
