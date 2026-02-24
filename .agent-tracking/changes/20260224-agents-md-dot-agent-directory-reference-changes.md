<!-- markdownlint-disable-file -->
# Release Changes: AGENTS.md `.agent` Directory Reference Update

**Related Plan**: .agent-tracking/plans/20260224-agents-md-dot-agent-directory-reference-plan.instructions.md
**Implementation Date**: 2026-02-24

## Summary

Enhanced `teambot init` to update existing AGENTS.md files with a reference section describing the `.agent` directory structure when the `.agent/` directory is newly copied. The implementation follows the existing pattern established by `_update_agents_md_with_template_reference()`.

## Changes

### Added

* `src/teambot/cli.py` - Added `AGENT_DIRECTORY_MARKER` constant for detecting existing `.agent` directory references
* `src/teambot/cli.py` - Added `AGENT_DIRECTORY_SECTION` constant containing the full `.agent` directory documentation (25 entries across 4 tables)
* `src/teambot/cli.py` - Added `_agents_md_has_agent_directory_reference()` function for case-insensitive detection
* `src/teambot/cli.py` - Added `_should_update_agents_md_with_agent_directory()` function for trigger condition logic
* `src/teambot/cli.py` - Added `_update_agents_md_with_agent_directory_reference()` function for safe file updates
* `tests/test_agents_md_update.py` - Added fixture `agents_md_with_agent_dir_reference` for test content
* `tests/test_agents_md_update.py` - Added fixture `agents_md_without_agent_dir_reference` for test content
* `tests/test_agents_md_update.py` - Added `TestAgentsMdHasAgentDirectoryReference` class with 5 unit tests
* `tests/test_agents_md_update.py` - Added `TestShouldUpdateAgentsMdWithAgentDirectory` class with 5 unit tests
* `tests/test_agents_md_update.py` - Added `TestUpdateAgentsMdWithAgentDirectoryReference` class with 8 unit tests
* `tests/test_agents_md_update_acceptance.py` - Added `test_at_007_appends_agent_dir_reference_when_newly_copied` acceptance test
* `tests/test_agents_md_update_acceptance.py` - Added `test_at_008_no_agent_dir_reference_when_dir_exists` acceptance test
* `tests/test_agents_md_update_acceptance.py` - Added `test_at_009_no_duplicate_agent_dir_reference` acceptance test
* `tests/test_agents_md_update_acceptance.py` - Added `test_at_010_both_references_added_on_fresh_existing_agents` acceptance test

### Modified

* `src/teambot/cli.py` - Added call to `_update_agents_md_with_agent_directory_reference()` in `cmd_init()` after existing template reference update
* `tests/test_agents_md_update_acceptance.py` - Updated `test_at_004_template_exists_no_update` to account for new `.agent` directory reference behavior
* `pyproject.toml` - Added per-file-ignores for E501 on cli.py to allow markdown table content in string constants

### Removed

* None

## Release Summary

**Total Files Affected**: 4

### Files Created (0)

* None

### Files Modified (4)

* `src/teambot/cli.py` - Added 3 new functions and 2 constants for `.agent` directory reference functionality
* `tests/test_agents_md_update.py` - Added 18 new unit tests across 3 test classes
* `tests/test_agents_md_update_acceptance.py` - Added 4 new acceptance tests, updated 1 existing test
* `pyproject.toml` - Added per-file-ignores configuration for ruff

### Files Removed (0)

* None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: Added ruff per-file-ignores for E501 in cli.py

### Deployment Notes

No special deployment considerations. The feature is automatically active when `teambot init` is run.
