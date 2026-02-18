<!-- markdownlint-disable-file -->
# Release Changes: Init Command Model Configuration and Prerequisites

**Related Plan**: init-command-model-configuration
**Implementation Date**: 2026-02-18

## Summary

Enhanced the `teambot init` command with improved model configuration defaults, automatic model cache refresh, authentication status checking, and post-init guidance display. These changes improve the first-run experience by ensuring users have the latest models available and clear guidance on next steps.

## Changes

### Added

* `src/teambot/scaffolds/init-next-steps.md` - Configurable guidance text displayed after init completes, containing recommended next steps for users
* `src/teambot/cli.py:_refresh_model_cache()` - Helper function to refresh model cache during init with graceful error handling
* `src/teambot/cli.py:_refresh_model_cache_async()` - Async implementation of model cache refresh
* `src/teambot/cli.py:_check_copilot_authentication()` - Helper function to check and display Copilot authentication status
* `src/teambot/cli.py:_check_auth_async()` - Async implementation of authentication check
* `src/teambot/cli.py:_display_post_init_guidance()` - Function to load and display post-init guidance from package file
* `tests/test_cli.py:TestInitModelCacheRefresh` - Test class for model cache refresh functionality (3 tests)
* `tests/test_cli.py:TestInitAuthenticationCheck` - Test class for authentication check functionality (3 tests)
* `tests/test_cli.py:TestInitPostGuidance` - Test class for post-init guidance display (4 tests)
* `tests/test_config/test_loader.py:test_default_config_agents_have_explicit_model_field` - Test for explicit agent model fields

### Modified

* `src/teambot/config/loader.py:create_default_config()` - Updated default_model from "claude-sonnet-4" to "claude-sonnet-4.5" and added explicit "model" field to each agent
* `src/teambot/cli.py:cmd_init()` - Integrated authentication check, model cache refresh, and guidance display
* `tests/test_config/test_loader.py:test_default_config_has_default_model` - Updated assertion to expect "claude-sonnet-4.5"

### Removed

* None

## Release Summary

**Total Files Affected**: 5

### Files Created (1)

* `src/teambot/scaffolds/init-next-steps.md` - Post-init guidance text file

### Files Modified (4)

* `src/teambot/config/loader.py` - Default model update and explicit agent model fields
* `src/teambot/cli.py` - Added helper functions and enhanced cmd_init
* `tests/test_cli.py` - Added 10 new tests for init enhancements
* `tests/test_config/test_loader.py` - Updated and added tests for config changes

### Files Removed (0)

* None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: Default model changed from claude-sonnet-4 to claude-sonnet-4.5

### Deployment Notes

No special deployment considerations. The changes are backwards compatible - existing teambot.json files will continue to work. New init runs will use the updated default model.
