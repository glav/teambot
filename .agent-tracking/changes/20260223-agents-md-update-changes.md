<!-- markdownlint-disable-file -->
# Release Changes: AGENTS.md Objective Template Reference Update

**Related Plan**: 20260223-agents-md-update-plan.instructions.md
**Implementation Date**: 2026-02-23

## Summary

Enhanced `teambot init` to update existing AGENTS.md files with a reference to the SDD objective template when the template is copied. The update is idempotent, preserves existing content, and provides user feedback via console messages.

## Changes

### Added

* `tests/test_agents_md_update.py` - Unit tests for AGENTS.md update functionality (17 tests)
* `tests/test_agents_md_update_acceptance.py` - Acceptance tests for end-to-end validation (6 tests)
* `src/teambot/cli.py` - Constants `OBJECTIVE_TEMPLATE_MARKER` and `OBJECTIVE_TEMPLATE_SECTION`
* `src/teambot/cli.py` - Function `_agents_md_has_template_reference()` for detection
* `src/teambot/cli.py` - Function `_should_update_agents_md()` for trigger conditions
* `src/teambot/cli.py` - Function `_update_agents_md_with_template_reference()` for update logic

### Modified

* `src/teambot/cli.py` - `cmd_init()` now calls update function after scaffold copying
* `tests/test_cli.py` - Updated `test_init_skips_existing_scaffolds` to account for template reference append

### Removed

* None

## Release Summary

**Total Files Affected**: 4

### Files Created (2)

* `tests/test_agents_md_update.py` - Unit tests for new AGENTS.md update functions
* `tests/test_agents_md_update_acceptance.py` - Acceptance tests for init scenarios

### Files Modified (2)

* `src/teambot/cli.py` - Added 3 functions, 2 constants, and integration in cmd_init()
* `tests/test_cli.py` - Updated one test assertion to account for new behavior

### Files Removed (0)

* None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No special deployment considerations. All changes are backward compatible.
