<!-- markdownlint-disable-file -->
# Release Changes: Dynamic Model Discovery

**Related Plan**: 20260216-dynamic-model-discovery-plan.instructions.md
**Implementation Date**: 2026-02-16

## Summary

Remove static model fallback lists from `schema.py` to ensure all model data comes exclusively from the SDK via cache. Update error handling to produce user-visible errors when SDK is unavailable instead of silently falling back. Add tier warning logging when SDK response is missing tier information.

## Changes

### Added

* `tests/test_copilot/test_sdk_client.py` - Added `test_adapt_model_info_logs_warning_for_missing_tier` and `test_adapt_model_info_logs_warning_for_invalid_tier` tests

### Modified

* `src/teambot/config/schema.py` - Removed `_FALLBACK_MODELS`, `_FALLBACK_MODEL_INFO`, `VALID_MODELS`, `MODEL_INFO` static constants; updated `_ensure_models_loaded()` to use expired cache with warning instead of static fallback; updated `validate_model()`, `get_available_models()`, and `get_model_info()` to return empty/False when no cache
* `src/teambot/copilot/sdk_client.py` - Updated `_adapt_model_info()` to log warnings when tier is missing or invalid
* `src/teambot/repl/commands.py` - Updated `handle_models()` to show error message when no models available; updated `_handle_models_refresh()` with improved error messages using Rich markup; removed "Using fallback list" message
* `tests/test_config/test_schema.py` - Updated tests to use cached data via `mock_model_cache` fixture; added tests for new no-fallback behavior (`test_validate_model_returns_false_without_cache`, `test_returns_empty_list_without_cache`, `test_returns_none_without_cache`)

### Removed

* Static fallback constants from `src/teambot/config/schema.py`: `_FALLBACK_MODELS`, `_FALLBACK_MODEL_INFO`, `VALID_MODELS`, `MODEL_INFO`

## Release Summary

**Total Files Affected**: 5

### Files Created (0)

### Files Modified (5)

* `src/teambot/config/schema.py` - Removed static fallback, SDK-only model discovery
* `src/teambot/copilot/sdk_client.py` - Added tier warning logging
* `src/teambot/repl/commands.py` - Improved error handling for model commands
* `tests/test_config/test_schema.py` - Updated tests for no-fallback behavior
* `tests/test_copilot/test_sdk_client.py` - Added tier warning logging tests

### Files Removed (0)

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

Model data now comes exclusively from SDK cache. Users must run `/models --refresh` on first use or when cache is empty/expired. SDK failures produce visible error messages instead of silently falling back to outdated static lists. Expired cache can still be used with a warning.
