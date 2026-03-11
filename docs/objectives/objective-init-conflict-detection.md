---
feature_name: init-conflict-detection
language: python
framework: click
test_preference: tdd
scope: small
acceptance_scenarios:
  - name: "Detect conflicting file numbering in existing .agent/commands/sdd/"
    steps:
      - "Set up a repository with existing .agent/commands/sdd/ containing old SDD prompts (e.g., sdd.4-determine-test-strategy.prompt.md)"
      - "Run teambot init"
    expected: "Init detects overlapping/conflicting file names and presents interactive prompt with Replace/Backup/Skip options"
  - name: "Clean init with no conflicts"
    steps:
      - "Set up a fresh repository with no .agent/ directory"
      - "Run teambot init"
    expected: "All scaffold files copied without conflict warnings"
  - name: "Init with --force replaces conflicting files"
    steps:
      - "Set up a repository with existing .agent/commands/sdd/ containing old SDD prompts"
      - "Run teambot init --force"
    expected: "Entire .agent/ directory is replaced with current scaffolds, no stale files remain (--force is alias for --on-conflict=replace)"
  - name: "Interactive backup preserves original files"
    steps:
      - "Set up repo with existing .agent/commands/sdd/ with old prompts"
      - "Run teambot init, select option [2] Backup"
    expected: "Old files moved to .agent-tracking/backups/<timestamp>/.agent/, new scaffolds copied, backup directory created if needed"
  - name: "Non-interactive backup mode"
    steps:
      - "Set up repo with conflicts"
      - "Run teambot init --on-conflict=backup"
    expected: "Backup created silently, new scaffolds copied, no interactive prompt"
  - name: "Multiple backup operations create separate timestamped directories"
    steps:
      - "Set up repo with conflicts"
      - "Run teambot init --on-conflict=backup"
      - "Modify .agent/ files"
      - "Run teambot init --on-conflict=backup again"
    expected: "Two separate timestamped backup directories exist in .agent-tracking/backups/, each preserving the state at time of backup"
---

## Objective

**Goal**: Enhance `teambot init` to detect and warn about conflicting or stale files when the target directory already contains similarly-named files that would cause confusion.

**Problem Statement**: When `teambot init` runs on a repository that already has an `.agent/commands/sdd/` directory with files from a previous version (using different numbering), the current behavior of "skipped_not_empty" leaves both old and new files coexisting. This creates a confusing situation where:

- Old files like `sdd.4-determine-test-strategy.prompt.md` remain alongside new `sdd.4-task-planner-for-feature.prompt.md`
- Users see duplicate numbered steps (e.g., two `sdd.5-*`, two `sdd.6-*`, two `sdd.7-*`)
- It's unclear which files are actually used by the current workflow
- The SDD workflow references specific file names that may not match the old files

Example of the confusion (from user report):
```
-rw-r--r-- sdd.4-determine-test-strategy.prompt.md    ← OLD
-rw-r--r-- sdd.4-task-planner-for-feature.prompt.md   ← NEW
-rw-r--r-- sdd.5-task-planner-for-feature.prompt.md   ← OLD
-rw-r--r-- sdd.5-review-plan.prompt.md                ← NEW
-rw-r--r-- sdd.6-review-plan.prompt.md                ← OLD  
-rw-r--r-- sdd.6-task-implementer-for-feature.prompt.md ← NEW
...
```

**Success Criteria**:

- [ ] `teambot init` detects when target `.agent/` directory contains files that would conflict with scaffolds
- [ ] Conflict detection identifies files with same numbered prefix but different names (e.g., `sdd.4-*.prompt.md`)
- [ ] Clear warning message lists conflicting files and explains the issue
- [ ] Interactive prompt offers remediation options at detection time (not just CLI flags)
- [ ] Option 1: Replace - clear directory and copy new scaffolds (equivalent to `--force`)
- [ ] Option 2: Backup - move existing directory to `.agent-tracking/backups/<timestamp>/` then copy new scaffolds
- [ ] Option 3: Skip - keep existing files, continue with warning
- [ ] Backup directory is outside prompt reference paths to avoid AI confusion
- [ ] Documentation updated to explain conflict scenarios and resolution
- [ ] Existing "skipped_not_empty" behavior remains for truly unrelated content

**Non-Goals** (explicitly out of scope):

- Automatic merging of old and new prompt files
- Version detection of existing SDD prompts
- Migration tooling for old prompt content

---

## Technical Context

**Target Codebase**:

- `src/teambot/scaffolds.py` - Scaffold file/directory copying logic
- `src/teambot/cli.py` - CLI entry point, `cmd_init()` function

**Primary Language/Framework**: Python / Click CLI

**Testing Preference**: TDD - write tests for conflict detection logic first

**Key Constraints**:

- Must not break existing init behavior for non-conflicting scenarios
- Detection should be fast (file listing, not content parsing)
- Should handle various file naming patterns (not just SDD prompts)
- Cross-platform file path handling

---

## Technical Analysis

### Conflict Detection Strategy

The core issue is that `copy_scaffold_directory()` currently only checks if the target directory exists and is non-empty. It doesn't analyze whether the existing files would create confusion.

**Proposed approach**: Before copying a scaffold directory, compare the set of files in the source scaffold with the files in the target. If there are files with the same numbered prefix but different names, flag this as a potential conflict.

### Conflict Detection Algorithm

```python
def detect_sdd_conflicts(source_dir: Path, target_dir: Path) -> list[ConflictInfo]:
    """Detect SDD prompt file conflicts.
    
    Looks for files with same numbered prefix (e.g., 'sdd.4-') but different names.
    """
    if not target_dir.exists():
        return []
    
    source_prefixes = {}  # prefix -> filename
    target_prefixes = {}  # prefix -> filename
    
    # Build prefix maps
    for f in source_dir.glob("sdd.*.prompt.md"):
        prefix = extract_prefix(f.name)  # e.g., "sdd.4-"
        source_prefixes[prefix] = f.name
    
    for f in target_dir.glob("sdd.*.prompt.md"):
        prefix = extract_prefix(f.name)
        target_prefixes[prefix] = f.name
    
    # Find conflicts: same prefix, different name
    conflicts = []
    for prefix, source_name in source_prefixes.items():
        if prefix in target_prefixes:
            target_name = target_prefixes[prefix]
            if source_name != target_name:
                conflicts.append(ConflictInfo(prefix, source_name, target_name))
    
    return conflicts
```

### CopyResult Enhancement

Extend `CopyResult.reason` to include a new value:

```python
reason: str  # "copied", "skipped_exists", "source_missing", "skipped_not_empty", "conflict_detected"
```

Or add a new field for conflict details:

```python
class CopyResult(NamedTuple):
    source: str
    target: Path
    copied: bool
    reason: str
    conflicts: list[ConflictInfo] | None = None  # NEW
```

### CLI Output

When conflicts are detected, present an interactive prompt:

```
⚠ Conflict detected in .agent/commands/sdd/:
  
  The target directory contains files that may conflict with current scaffolds:
  
  sdd.4-*:
    - Existing: sdd.4-determine-test-strategy.prompt.md
    - New:      sdd.4-task-planner-for-feature.prompt.md
  
  sdd.5-*:
    - Existing: sdd.5-task-planner-for-feature.prompt.md  
    - New:      sdd.5-review-plan.prompt.md

How would you like to proceed?

  [1] Replace - Clear existing directory and copy new scaffolds
  [2] Backup  - Move existing to .agent-tracking/backups/ then copy new scaffolds
  [3] Skip    - Keep existing files (may cause workflow confusion)

Choice [1/2/3]: 
```

### Backup Directory Structure

When backup is selected, the existing `.agent/` directory is moved to:

```
.agent-tracking/
└── backups/
    └── 2026-03-10T22-11-00/
        └── .agent/
            ├── commands/
            │   └── sdd/
            │       ├── sdd.4-determine-test-strategy.prompt.md
            │       └── ...
            ├── instructions/
            └── standards/
```

**Why `.agent-tracking/backups/`?**
- `.agent-tracking/` is already used for SDD workflow artifacts
- It is NOT referenced in prompt instructions or agent context
- Keeps backups organized and discoverable
- Timestamp naming prevents collisions from multiple backup operations
- Multiple backups are acceptable and expected (each gets unique timestamp)

**Directory auto-creation**: The `.agent-tracking/backups/` directory is created automatically if it doesn't exist when a backup operation is triggered.

**Timestamp format**: Uses filesystem-safe ISO 8601 format with colons replaced by hyphens (e.g., `2026-03-10T22-11-00` instead of `2026-03-10T22:11:00`) for cross-platform compatibility.

### Non-Interactive Mode

For CI/CD or scripted usage, support flags:

```bash
teambot init --on-conflict=replace   # Same as --force (backwards compatible alias)
teambot init --on-conflict=backup    # Auto-backup without prompt
teambot init --on-conflict=skip      # Keep existing, no prompt
teambot init --force                 # Alias for --on-conflict=replace (existing behavior preserved)
```

**Flag precedence**: If both `--force` and `--on-conflict` are specified, `--on-conflict` takes precedence with a warning.

---

## Implementation Tasks

### Phase 1: Conflict Detection Core

- [ ] Define `ConflictInfo` data class for conflict metadata
- [ ] Implement `extract_numbered_prefix()` helper function
- [ ] Implement `detect_sdd_conflicts()` function
- [ ] Write unit tests for conflict detection logic

### Phase 2: Backup Infrastructure

- [ ] Create `backup_directory()` function in scaffolds.py
- [ ] Generate ISO 8601 timestamp for backup folder naming
- [ ] Implement move operation to `.agent-tracking/backups/<timestamp>/`
- [ ] Write tests for backup directory creation and file preservation

### Phase 3: Integrate with Scaffold Copy

- [ ] Extend `CopyResult` with optional conflict information
- [ ] Update `copy_scaffold_directory()` to detect conflicts before skipping
- [ ] Add new reason value or conflict field to results
- [ ] Write integration tests for scaffold copying with conflicts

### Phase 4: Interactive CLI Prompt

- [ ] Create `prompt_conflict_resolution()` function using Click's prompt utilities
- [ ] Implement three choices: Replace, Backup, Skip
- [ ] Update `cmd_init()` to invoke prompt on conflict detection
- [ ] Add `--on-conflict` flag for non-interactive mode (replace/backup/skip)
- [ ] Write tests for interactive prompt flow (mocked input)

### Phase 5: Documentation

- [ ] Update README with conflict scenario explanation
- [ ] Add troubleshooting section for SDD file conflicts
- [ ] Document `--on-conflict` flag options
- [ ] Document backup directory location and recovery

---

## Additional Context

The SDD workflow was recently renumbered, causing the file naming scheme to change:

| Old Numbering | New Numbering |
|---------------|---------------|
| sdd.4-determine-test-strategy | (removed/merged) |
| sdd.5-task-planner-for-feature | sdd.4-task-planner-for-feature |
| sdd.6-review-plan | sdd.5-review-plan |
| sdd.7-task-implementer | sdd.6-task-implementer |
| sdd.8-post-implementation-review | sdd.7-post-implementation-review |

This renumbering is the primary cause of the conflict scenario described.
