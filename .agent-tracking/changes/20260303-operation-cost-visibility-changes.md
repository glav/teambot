<!-- markdownlint-disable-file -->
# Release Changes: Operation Cost Visibility

**Related Plan**: 20260303-operation-cost-visibility-plan.instructions.md
**Implementation Date**: 2026-03-03

## Summary

Add comprehensive token usage and cost visibility to TeamBot interactions by capturing token data from SDK events, aggregating by agent/stage, and displaying summaries at run completion.

## Changes

### Added

* `src/teambot/tokens/__init__.py` - Token tracking module init with exports
* `src/teambot/tokens/models.py` - TokenUsage dataclass with serialization and aggregation support
* `src/teambot/tokens/tracker.py` - TokenTracker class for per-agent/per-stage aggregation
* `src/teambot/tokens/extraction.py` - SDK event data extraction function for ASSISTANT_USAGE events
* `src/teambot/tokens/display.py` - Rich-based token summary display functions
* `tests/test_tokens/__init__.py` - Token tracking test package init
* `tests/test_tokens/test_models.py` - 19 unit tests for TokenUsage dataclass (TDD)
* `tests/test_tokens/test_tracker.py` - 23 unit tests for TokenTracker class (TDD)
* `tests/test_tokens/test_extraction.py` - 8 unit tests for SDK extraction function (TDD)
* `tests/test_tokens/test_display.py` - 11 unit tests for display functions (Code-First)
* `tests/test_token_tracking_acceptance.py` - 13 acceptance tests for token tracking feature

### Modified

* `src/teambot/copilot/sdk_client.py` - Modified _execute_streaming_once() to capture ASSISTANT_USAGE events and return tuple[str, TokenUsage | None]
* `src/teambot/tasks/models.py` - Added token_usage field to TaskResult, added to_dict() and from_dict() methods
* `src/teambot/orchestration/execution_loop.py` - Added TokenTracker integration, token summary display, and persistence
* `src/teambot/repl/loop.py` - Added session token tracking and cleanup summary display
* `src/teambot/config/loader.py` - Added token_tracking validation and defaults (enabled by default)
* `tests/test_copilot/test_sdk_streaming.py` - Updated tests to handle tuple return from execute_streaming()
* `tests/test_copilot/test_sdk_client.py` - Updated streaming retry tests for tuple return
* `tests/test_tasks/test_models.py` - Added 6 tests for TaskResult token_usage field
* `tests/test_repl/test_loop.py` - Updated tests to use execute_streaming instead of execute
* `tests/test_config/test_loader.py` - Added 4 tests for token_tracking configuration

### Removed

None

## Release Summary

**Total Files Affected**: 21

### Files Created (11)

* `src/teambot/tokens/__init__.py` - Module init
* `src/teambot/tokens/models.py` - TokenUsage dataclass
* `src/teambot/tokens/tracker.py` - TokenTracker class
* `src/teambot/tokens/extraction.py` - SDK extraction
* `src/teambot/tokens/display.py` - Display functions
* `tests/test_tokens/__init__.py` - Test package init
* `tests/test_tokens/test_models.py` - TokenUsage tests
* `tests/test_tokens/test_tracker.py` - TokenTracker tests
* `tests/test_tokens/test_extraction.py` - Extraction tests
* `tests/test_tokens/test_display.py` - Display tests
* `tests/test_token_tracking_acceptance.py` - Acceptance tests

### Files Modified (10)

* `src/teambot/copilot/sdk_client.py` - SDK token capture
* `src/teambot/tasks/models.py` - TaskResult extension
* `src/teambot/orchestration/execution_loop.py` - ExecutionLoop integration
* `src/teambot/repl/loop.py` - REPL integration
* `src/teambot/config/loader.py` - Config validation
* `tests/test_copilot/test_sdk_streaming.py` - Updated for tuple return
* `tests/test_copilot/test_sdk_client.py` - Updated for tuple return
* `tests/test_tasks/test_models.py` - TaskResult tests
* `tests/test_repl/test_loop.py` - REPL tests
* `tests/test_config/test_loader.py` - Config tests

### Files Removed (0)

None

### Dependencies & Infrastructure

* **New Dependencies**: None (pure Python, using existing rich library)
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: token_tracking.enabled option added to teambot.json schema

### Deployment Notes

Feature is enabled by default. Users can disable via `token_tracking.enabled: false` in teambot.json.
