<!-- markdownlint-disable-file -->
# Release Changes: Model Cache Auto-Setup and Login Validation

**Related Plan**: 20260219-model-cache-auto-setup-plan.instructions.md
**Implementation Date**: 2026-02-19

## Summary

Enable `teambot run` to automatically validate Copilot CLI authentication and refresh the model cache when missing, providing a seamless first-run experience.

## Changes

### Added

* `tests/test_cli.py` - Added `TestRunAuthCheck` class with 4 unit tests for blocking auth check behavior
* `tests/test_cli.py` - Added `TestRunModelCache` class with 5 unit tests for cache detection and auto-refresh
* `tests/test_model_cache_auto_acceptance.py` - New file with 8 acceptance tests covering AT-001 through AT-005 scenarios

### Modified

* `src/teambot/cli.py` - Added `_check_copilot_authentication_blocking()` function for blocking auth check in cmd_run
* `src/teambot/cli.py` - Added `_ensure_model_cache()` function for auto-refresh when cache missing/expired
* `src/teambot/cli.py` - Modified `cmd_run()` to call auth check and cache ensure before config loading
* `tests/test_config/test_loader.py` - Added validate_model mock to test_agent_with_valid_model to fix pre-existing test
* `tests/test_repl/test_commands.py` - Added validate_model mock to test_model_sets_agent_model to fix pre-existing test

### Removed

## Release Summary

**Total Files Affected**: 5

### Files Created (1)

* `tests/test_model_cache_auto_acceptance.py` - 8 acceptance tests for model cache auto-setup feature

### Files Modified (4)

* `tests/test_cli.py` - Added 9 new unit tests (Phase 1 TDD + Phase 2 validation)
* `src/teambot/cli.py` - Added 2 new helper functions and integrated into cmd_run()
* `tests/test_config/test_loader.py` - Fixed pre-existing test with proper model validation mock
* `tests/test_repl/test_commands.py` - Fixed pre-existing test with proper model validation mock

### Files Removed (0)

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No deployment considerations - internal CLI behavior change only.
