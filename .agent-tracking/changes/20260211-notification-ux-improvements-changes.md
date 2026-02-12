<!-- markdownlint-disable-file -->
# Release Changes: Notification UX Improvements

**Related Plan**: 20260211-notification-ux-improvements-plan.instructions.md
**Implementation Date**: 2026-02-11

## Summary

Add header/footer notifications when starting and completing orchestration runs, and implement a `/notify <msg>` REPL command for testing notification configuration.

## Changes

### Added

* `tests/test_notifications/test_templates.py` - Added TestOrchestrationStartedTemplate, TestOrchestrationCompletedTemplate, and TestCustomMessageTemplate test classes with 13 new tests for lifecycle and custom message event rendering

### Modified

* `src/teambot/notifications/templates.py` - Added orchestration_started, orchestration_completed, and custom_message templates to TEMPLATES dict; updated render() with fallback logic for missing objective_name and duration formatting

* `src/teambot/orchestration/execution_loop.py` - Added orchestration_started event emission at run() entry; added orchestration_completed event emission at all exit points (complete, cancelled, timeout, error); added _emit_completed_event() helper method

* `src/teambot/cli.py` - Added orchestration_started and orchestration_completed event handlers to on_progress callbacks in _run_orchestration() and _run_orchestration_resume()

* `tests/test_orchestration/test_execution_loop.py` - Added TestOrchestrationLifecycleEvents class with 8 tests for lifecycle event emission

* `src/teambot/repl/commands.py` - Added config parameter to SystemCommands.__init__(); implemented notify() method for /notify command; registered notify in dispatch handlers; updated /help output to include /notify

* `src/teambot/repl/loop.py` - Updated REPLLoop to pass config to SystemCommands

* `tests/test_repl/test_commands.py` - Added TestNotifyCommand class with 12 tests for /notify command functionality

### Removed

(None)

## Release Summary

**Total Files Affected**: 7

### Files Created (0)

(None - all changes were extensions to existing files)

### Files Modified (7)

* `src/teambot/notifications/templates.py` - Added 3 new templates and render logic
* `src/teambot/orchestration/execution_loop.py` - Added lifecycle event emission
* `src/teambot/cli.py` - Added event handlers for terminal display
* `src/teambot/repl/commands.py` - Added /notify command and config parameter
* `src/teambot/repl/loop.py` - Wired config to SystemCommands
* `tests/test_notifications/test_templates.py` - Added 13 template tests
* `tests/test_orchestration/test_execution_loop.py` - Added 8 lifecycle event tests
* `tests/test_repl/test_commands.py` - Added 12 /notify command tests

### Files Removed (0)

(None)

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No special deployment considerations. The feature works with existing notification configuration.

### Test Results

* **Total Tests**: 1374 passed (33 new tests added)
* **Coverage**: 81% overall
* **New Code Coverage**: 100% on templates.py, 93% on commands.py