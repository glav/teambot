<!-- markdownlint-disable-file -->
# Release Changes: Model Tier Classification Fix

**Related Plan**: 20260216-model-tier-classification-plan.instructions.md
**Implementation Date**: 2026-02-16

## Summary

Fix model tier classification to derive tier from `billing.multiplier` instead of the non-existent `capabilities.tier` attribute. Adds multiplier display to `/models` command and eliminates warning spam.

## Changes

### Added

* `tests/test_copilot/test_sdk_client.py` - Added `test_adapt_model_info_tier_boundaries` parametrized test for all tier boundary values
* `src/teambot/copilot/sdk_client.py` - Added `multiplier` field to `TeamBotModelInfo` dataclass
* `src/teambot/copilot/sdk_client.py` - Added `_extract_multiplier()` helper function for billing.multiplier extraction
* `src/teambot/copilot/sdk_client.py` - Added `_get_tier_from_multiplier()` helper function for tier mapping

### Modified

* `tests/test_copilot/test_sdk_client.py` - Replaced `test_adapt_model_info_with_dict_capabilities` with `test_adapt_model_info_with_dict_billing`
* `tests/test_copilot/test_sdk_client.py` - Replaced `test_adapt_model_info_with_object_capabilities` with `test_adapt_model_info_with_object_billing`
* `src/teambot/config/model_cache.py` - Added `multiplier` field to `CachedModel` dataclass
* `src/teambot/config/model_cache.py` - Updated `load_cache()` to read multiplier from cache
* `src/teambot/config/model_cache.py` - Updated `save_cache()` to write multiplier to cache
* `src/teambot/config/schema.py` - Updated `_ensure_models_loaded()` to include multiplier in cached model dict
* `src/teambot/config/schema.py` - Updated `refresh_models()` to include multiplier in cached model dict
* `src/teambot/repl/commands.py` - Updated `handle_models()` to display `[{multiplier}x]` suffix for each model
* `tests/test_dynamic_model_discovery_acceptance.py` - Updated `mock_sdk_models` fixture to include multiplier values
* `tests/test_dynamic_model_discovery_acceptance.py` - Updated `TestTierWarningLogging` to `TestTierMultiplierClassification` with new test behavior
* `tests/test_dynamic_model_discovery_acceptance.py` - Added `test_at_007_multiplier_display` acceptance test
* `tests/test_copilot/test_sdk_client.py` - Updated `test_list_models_returns_adapted_models` to use billing.multiplier

### Removed

* `tests/test_copilot/test_sdk_client.py` - Deleted `test_adapt_model_info_logs_warning_for_missing_tier`
* `tests/test_copilot/test_sdk_client.py` - Deleted `test_adapt_model_info_logs_warning_for_invalid_tier`

## Release Summary

**Total Files Affected**: 6

### Files Created (0)

None

### Files Modified (6)

* `src/teambot/copilot/sdk_client.py` - Added multiplier field, helper functions, rewrote _adapt_model_info
* `src/teambot/config/model_cache.py` - Added multiplier to CachedModel and cache load/save
* `src/teambot/config/schema.py` - Added multiplier to cached model dicts
* `src/teambot/repl/commands.py` - Added multiplier display in /models output
* `tests/test_copilot/test_sdk_client.py` - Updated tier tests to use billing.multiplier
* `tests/test_dynamic_model_discovery_acceptance.py` - Updated fixtures and added multiplier display test

### Files Removed (0)

None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No special deployment considerations. All changes are backward compatible:
- `TeamBotModelInfo.multiplier` is optional (default None)
- `CachedModel.multiplier` is optional (default None)
- Old cache files without multiplier load correctly
