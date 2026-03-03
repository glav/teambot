<!-- markdownlint-disable-file -->
# Release Changes: SDD Prompt Sync

**Related Plan**: 20260302-sdd-prompt-sync-plan.instructions.md
**Implementation Date**: 2026-03-02

## Summary

Implement incremental SDD prompt file synchronization during `teambot init` and runtime validation to ensure `stages.yaml` and SDD prompt files stay in sync. This feature enables seamless TeamBot upgrades by adding missing prompt files without overwriting user customizations.

## Changes

### Added

* `src/teambot/prompt_sync.py` - New module for SDD prompt sync with sync_sdd_prompts(), validate_prompt_files(), detect_orphaned_prompts()
* `tests/test_prompt_sync.py` - 26 unit tests for prompt_sync module (TDD approach)
* `tests/test_prompt_sync_acceptance.py` - 6 acceptance tests (AT-001 through AT-006)

### Modified

* `src/teambot/cli.py` - Integrated sync_sdd_prompts() in cmd_init(), added validate_prompt_files() in cmd_run(), added --skip-prompt-validation flag

### Removed

None

## Release Summary

**Total Files Affected**: 4

### Files Created (3)

* `src/teambot/prompt_sync.py` - Core sync and validation logic
* `tests/test_prompt_sync.py` - Unit tests (26 tests)
* `tests/test_prompt_sync_acceptance.py` - Acceptance tests (6 tests)

### Files Modified (1)

* `src/teambot/cli.py` - CLI integration for sync and validation

### Files Removed (0)

None

### Dependencies & Infrastructure

* **New Dependencies**: None (uses stdlib only)
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

* Feature is automatically enabled when TeamBot is upgraded
* `teambot init` will now display SDD prompt sync summary
* `teambot run` will validate prompt files before workflow execution
* Use `--skip-prompt-validation` flag to bypass validation if needed

