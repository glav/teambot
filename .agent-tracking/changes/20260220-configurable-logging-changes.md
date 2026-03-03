<!-- markdownlint-disable-file -->
# Release Changes: Configurable Logging Output

**Related Plan**: 20260220-configurable-logging-plan.instructions.md
**Implementation Date**: 2026-02-20

## Summary

Implement configuration-based logging output control to prevent log messages from interfering with the Rich/Textual interactive terminal UI while preserving debugging capability via file logging. Interactive mode now defaults to file-only logging, while file-based orchestration mode defaults to console + file logging.

## Changes

### Added

* `tests/test_config/test_loader.py` - Added `TestLoggingConfigValidation` class with 11 tests for logging config validation and defaults
* `tests/test_config/test_logging_config.py` - Created new test file with 15 tests for `is_interactive_mode()` and `setup_logging()` functions
* `src/teambot/config/logging_config.py` - Created new module with `is_interactive_mode()` and `setup_logging()` functions for mode-aware logging
* `docs/guides/configuration.md` - Added "Logging and Debugging" section with configuration options, CLI override, and examples
* `docs/guides/cli-reference.md` - Added `--log-to-console`, `--worktree`, `--branch`, `--base-branch` flags to options table

### Modified

* `src/teambot/config/loader.py` - Added `VALID_LOG_LEVELS` constant, `_validate_logging()` method, and logging defaults in `_apply_defaults()`
* `src/teambot/cli.py` - Added `--log-to-console` CLI flag and integrated mode-aware logging in `cmd_run()`

### Removed

(none)

## Release Summary

**Total Files Affected**: 7

### Files Created (2)

* `src/teambot/config/logging_config.py` - Mode-aware logging configuration module
* `tests/test_config/test_logging_config.py` - Tests for logging configuration module

### Files Modified (5)

* `src/teambot/config/loader.py` - Added logging validation and defaults
* `src/teambot/cli.py` - Added --log-to-console flag and mode-aware logging setup
* `tests/test_config/test_loader.py` - Added logging config validation tests
* `docs/guides/configuration.md` - Added "Logging and Debugging" documentation section
* `docs/guides/cli-reference.md` - Added --log-to-console and worktree flags to options table

### Files Removed (0)

(none)

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: New `logging` section in `teambot.json` schema with fields: `console_output`, `file_output`, `log_file`, `level`

### Deployment Notes

No deployment changes required. Backwards compatible with existing configurations - configs without `logging` section will use defaults:
- `file_output: true`
- `log_file: ".teambot/logs/teambot.log"`
- `level: "INFO"`
- `console_output: null` (auto-detected based on execution mode)
