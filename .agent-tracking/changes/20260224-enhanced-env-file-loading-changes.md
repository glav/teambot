<!-- markdownlint-disable-file -->
# Release Changes: Enhanced .env File Loading

**Related Plan**: 20260224-enhanced-env-file-loading-plan.instructions.md
**Implementation Date**: 2026-02-24

## Summary

Implementing enhanced `.env` file loading for TeamBot with support for `uvx` invocations, subdirectory execution, explicit path specification (`--env-file`), and loading disablement (`--no-env`).

## Changes

### Added

* `tests/test_env_loader.py` - Unit tests for env_loader module (29 tests) following TDD approach
* `src/teambot/env_loader.py` - Environment file loading utilities with extract_env_args, find_env_files, load_environment functions
* `tests/test_env_loading_acceptance.py` - Acceptance tests for AT-001 through AT-007 plus edge cases (14 tests)

### Modified

* `src/teambot/cli.py` - Replaced load_dotenv import with env_loader, added --env-file and --no-env arguments, updated main() function to use load_environment()
* `tests/test_cli.py` - Added TestEnvArguments and TestEnvLoadingIntegration test classes (12 new tests)
* `README.md` - Added Environment Configuration section documenting --env-file and --no-env options

### Removed

* None

## Release Summary

**Total Files Affected**: 6

### Files Created (3)

* `src/teambot/env_loader.py` - Core environment file loading module with hierarchical .env discovery
* `tests/test_env_loader.py` - Unit tests for env_loader functions (29 tests)
* `tests/test_env_loading_acceptance.py` - Acceptance tests validating AT scenarios (14 tests)

### Files Modified (3)

* `src/teambot/cli.py` - Added --env-file and --no-env CLI arguments, integrated load_environment()
* `tests/test_cli.py` - Added 12 new tests for env argument parsing and integration
* `README.md` - Added Environment Configuration documentation section

### Files Removed (0)

* None

### Dependencies & Infrastructure

* **New Dependencies**: None (uses existing python-dotenv v1.0.0+)
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: New CLI global arguments available

### Deployment Notes

* Backward compatible - existing behavior preserved when no new arguments are used
* Manual verification of AT-008 (uvx invocation) recommended before release