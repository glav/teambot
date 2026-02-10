<!-- markdownlint-disable-file -->
# Release Changes: Unknown Agent ID Validation

**Related Plan**: 20260209-unknown-agent-validation-plan.instructions.md
**Implementation Date**: 2026-02-09

## Summary

Closed all validation gaps so that unknown agent IDs are rejected immediately with a clear error message, regardless of which code path handles the command. Added defence-in-depth guards to prevent ghost agent status entries. Added 11 new tests covering all validation paths.

## Changes

### Added

* `tests/test_tasks/test_executor.py` - Added `TestTaskExecutorAgentValidation` class with 7 tests covering unknown agent rejection for background, multi-agent, pipeline, alias, and error message format
* `tests/test_ui/test_agent_state.py` - Added `TestAgentStatusManagerGuard` class with 4 tests covering ghost agent prevention in set_running, set_idle, set_model, and regression guard for valid agents

### Modified

* `src/teambot/tasks/executor.py` - Added agent ID validation block at top of `execute()` method that checks all agent IDs (including pipeline stages) against VALID_AGENTS with alias resolution before dispatching any task
* `src/teambot/ui/app.py` - Added agent ID validation at top of `_handle_agent_command()` in split-pane UI to reject unknown agents before any status updates or streaming begins
* `src/teambot/ui/agent_state.py` - Added DEFAULT_AGENTS guard in `_update()`, `set_idle()`, and `set_model()` methods to prevent auto-creation of status entries for unknown agent IDs

### Removed

* None

## Release Summary

**Total Files Affected**: 5

### Files Created (0)

* None

### Files Modified (5)

* `src/teambot/tasks/executor.py` - Added 15-line validation block in execute() with local import, alias resolution, and error return
* `src/teambot/ui/app.py` - Added 10-line validation block in _handle_agent_command() with local import and error display
* `src/teambot/ui/agent_state.py` - Added 3 guard clauses (2 lines each) in _update(), set_idle(), set_model()
* `tests/test_tasks/test_executor.py` - Added TestTaskExecutorAgentValidation class with 7 async test methods
* `tests/test_ui/test_agent_state.py` - Added TestAgentStatusManagerGuard class with 4 sync test methods

### Files Removed (0)

* None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No special deployment steps. Standard release — validation is synchronous and local.
