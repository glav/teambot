<!-- markdownlint-disable-file -->
# Release Changes: Remove Overlay Feature

**Related Plan**: 20260213-remove-overlay-plan.instructions.md
**Implementation Date**: 2026-02-13

## Summary

Remove the unused persistent status overlay feature from TeamBot to reduce codebase complexity and maintenance burden. This involves deleting ~1,315 lines of code and cleaning up all integration points.

## Changes

### Added

* (None for removal task)

### Modified

* `src/teambot/visualization/__init__.py` - Removed overlay imports and exports
* `src/teambot/repl/commands.py` - Removed /overlay command handler, help text, and SystemCommands overlay parameter
* `src/teambot/repl/loop.py` - Removed overlay initialization, callbacks, and cleanup
* `src/teambot/config/loader.py` - Removed VALID_OVERLAY_POSITIONS, _validate_overlay(), and overlay defaults
* `tests/test_config/test_loader.py` - Removed TestOverlayConfig class (5 tests)
* `docs/guides/architecture.md` - Removed overlay references from REPL and UI sections
* `docs/guides/development.md` - Updated visualization package description
* `src/teambot/tasks/executor.py` - Updated docstring to remove overlay reference
* `tests/test_acceptance_validation.py` - Updated comment to remove overlay reference

### Removed

* `tests/test_visualization/test_overlay.py` - Deleted overlay unit tests (571 lines, 47 tests)
* `tests/test_repl/test_commands_overlay.py` - Deleted /overlay command tests (141 lines, 12 tests)
* `src/teambot/visualization/overlay.py` - Deleted core overlay renderer module (603 lines)
* `docs/feature-specs/persistent-status-overlay.md` - Deleted feature specification

## Release Summary

**Total Files Affected**: 13

### Files Created (0)

* (None)

### Files Modified (9)

* `src/teambot/visualization/__init__.py` - Removed overlay exports
* `src/teambot/repl/commands.py` - Removed /overlay command
* `src/teambot/repl/loop.py` - Removed overlay integration
* `src/teambot/config/loader.py` - Removed overlay config validation
* `src/teambot/tasks/executor.py` - Updated docstring
* `tests/test_config/test_loader.py` - Removed overlay tests
* `tests/test_acceptance_validation.py` - Updated comment
* `docs/guides/architecture.md` - Removed overlay sections
* `docs/guides/development.md` - Updated package description

### Files Removed (4)

* `tests/test_visualization/test_overlay.py` - Overlay unit tests no longer needed
* `tests/test_repl/test_commands_overlay.py` - Command tests no longer needed
* `src/teambot/visualization/overlay.py` - Feature removed
* `docs/feature-specs/persistent-status-overlay.md` - Feature spec obsolete

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: Overlay configuration options (`overlay.enabled`, `overlay.position`) are no longer validated or applied

### Deployment Notes

No special deployment considerations. The overlay feature was optional and its removal does not affect any external interfaces.

### Test Results

* **Total Tests**: 1391 passed
* **Tests Removed**: 64 (59 overlay tests + 5 config tests)
* **Coverage**: 82% (above 80% target)
