<!-- markdownlint-disable-file -->
# Release Changes: Fix Authentication Command Message

**Related Plan**: 20260222-auth-message-fix-plan.instructions.md
**Implementation Date**: 2026-02-22

## Summary

Updated all error messages from incorrect `copilot auth` to correct `copilot login` command across source code, documentation, and test assertions. The GitHub Copilot CLI uses `copilot login` for OAuth device flow authentication.

## Changes

### Added

* None

### Modified

* `src/teambot/cli.py` - Updated 5 authentication error messages from `copilot auth` to `copilot login` (lines 108, 114, 139, 144, 239)
* `README.md` - Updated installation instructions to reference `copilot login` (line 17)
* `docs/guides/installation.md` - Updated authentication commands to `copilot login` (lines 17, 227)
* `tests/test_cli.py` - Updated 2 test assertions to verify `copilot login` output (lines 609, 629)
* `tests/test_acceptance_validation.py` - Updated 3 occurrences: docstring and 2 assertions (lines 118, 155-156, 408)
* `tests/test_init_model_config_acceptance.py` - Updated 2 assertions to verify `copilot login` (lines 115, 135)
* `tests/test_model_cache_auto_acceptance.py` - Updated 1 assertion to verify `copilot login` (line 110)

### Removed

* None

## Release Summary

**Total Files Affected**: 7

### Files Created (0)

* None

### Files Modified (7)

* `src/teambot/cli.py` - 5 string replacements in authentication error messages
* `README.md` - 1 string replacement in prerequisites section
* `docs/guides/installation.md` - 2 string replacements in authentication examples
* `tests/test_cli.py` - 2 assertion updates
* `tests/test_acceptance_validation.py` - 3 updates (1 docstring, 2 assertions)
* `tests/test_init_model_config_acceptance.py` - 2 assertion updates + refactored for line length
* `tests/test_model_cache_auto_acceptance.py` - 1 assertion update

### Files Removed (0)

* None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No deployment considerations. This is a documentation/message text fix with no logic changes.

### Verification

* All 78 affected tests pass
* Linting passes (ruff check + format)
* Zero matches for `copilot auth` in target files
