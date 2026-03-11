<!-- markdownlint-disable-file -->
# Release Changes: Init Conflict Detection

**Related Plan**: 20260310-init-conflict-detection-plan.instructions.md
**Implementation Date**: 2026-03-10

## Summary

Enhanced `teambot init` to detect numbered prefix conflicts in `.agent/commands/sdd/` and provide interactive remediation options (Replace/Backup/Skip). Implemented conflict detection algorithm, backup infrastructure, interactive CLI prompt, and `--on-conflict` flag for non-interactive mode.

## Changes

### Added

* `tests/test_scaffolds.py` - Added `TestExtractNumberedPrefix` class (6 tests for prefix extraction)
* `tests/test_scaffolds.py` - Added `TestConflictInfo` class (2 tests for dataclass structure)
* `tests/test_scaffolds.py` - Added `TestDetectSddConflicts` class (7 tests for conflict detection)
* `tests/test_scaffolds.py` - Added `TestBackupDirectory` class (5 tests for backup operations)
* `tests/test_cli.py` - Added `TestInitConflictHandling` class (7 integration tests)
* `tests/test_cli.py` - Added `TestPromptConflictResolution` class (5 tests for prompt function)

### Modified

* `src/teambot/scaffolds.py` - Added `ConflictInfo` dataclass, `extract_numbered_prefix()`, `detect_sdd_conflicts()`, and `backup_directory()` functions
* `src/teambot/cli.py` - Added `prompt_conflict_resolution()` function, `--on-conflict` flag, and conflict detection in `cmd_init()`

### Removed

## Release Summary

**Total Files Affected**: 4

### Files Created (0)

### Files Modified (4)

* `src/teambot/scaffolds.py` - Added conflict detection and backup infrastructure
* `src/teambot/cli.py` - Added interactive prompt and CLI integration
* `tests/test_scaffolds.py` - Added 20 new tests for conflict detection and backup
* `tests/test_cli.py` - Added 12 new tests for CLI integration

### Files Removed (0)

### Dependencies & Infrastructure

* **New Dependencies**: None (uses stdlib only: re, dataclasses, datetime, shutil)
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: Added `--on-conflict` CLI flag

### Deployment Notes

No special deployment steps required. Feature is available immediately after package update.

