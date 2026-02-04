<!-- markdownlint-disable-file -->
# Release Changes: Model Selection Support

**Related Plan**: 20260204-model-selection-plan.instructions.md
**Implementation Date**: 2026-02-04

## Summary

Enable TeamBot agents to use configurable AI models with visibility in the terminal UI, support for per-agent defaults in configuration, runtime model override via inline flags and session commands, and clear validation/error handling.

## Changes

### Added

* `tests/test_config/test_schema.py` - TDD tests for model validation (11 tests)
* Tests for `/models` and `/model` commands in `tests/test_repl/test_commands.py`
* Tests for `--model` flag parsing in `tests/test_repl/test_parser.py`
* Tests for model field in `AgentStatus` in `tests/test_ui/test_agent_state.py`
* Tests for model field in `Task` in `tests/test_tasks/test_models.py`
* Tests for SDK client model support in `tests/test_copilot/test_sdk_client.py`

### Modified

* `src/teambot/config/schema.py` - Added VALID_MODELS (14 models), MODEL_INFO dict, validate_model(), get_available_models(), get_model_info()
* `src/teambot/config/loader.py` - Added model validation in _validate_agent() and _validate_default_model()
* `src/teambot/ui/agent_state.py` - Added model field to AgentStatus, with_model() method, set_model() in AgentStatusManager
* `src/teambot/tasks/models.py` - Added model field to Task dataclass
* `src/teambot/copilot/sdk_client.py` - Added resolve_model() function, updated get_or_create_session() to accept model parameter
* `src/teambot/repl/parser.py` - Added model and is_session_model_set fields to Command, --model/-m flag parsing
* `src/teambot/repl/commands.py` - Added handle_models() and handle_model() functions, updated /help, /status, /tasks, /task output
* `src/teambot/ui/widgets/status_panel.py` - Updated _format_status() to show model indicator
* `src/teambot/tasks/manager.py` - Updated create_task() to accept model parameter, executor signature updated
* `src/teambot/tasks/executor.py` - Updated to pass model through task creation and SDK calls
* `tests/test_tasks/test_manager.py` - Updated mock executors to accept model parameter

### Removed

None

## Release Summary

**Total Files Affected**: 14

### Files Created (1)

* `tests/test_config/test_schema.py` - Model validation tests

### Files Modified (13)

* `src/teambot/config/schema.py` - Model constants and validation
* `src/teambot/config/loader.py` - Config model validation
* `src/teambot/ui/agent_state.py` - AgentStatus model field
* `src/teambot/tasks/models.py` - Task model field
* `src/teambot/copilot/sdk_client.py` - Model resolution and session creation
* `src/teambot/repl/parser.py` - --model flag parsing
* `src/teambot/repl/commands.py` - /models and /model commands
* `src/teambot/ui/widgets/status_panel.py` - Model display
* `src/teambot/tasks/manager.py` - Model in task creation
* `src/teambot/tasks/executor.py` - Model propagation
* `tests/test_repl/test_commands.py` - Command tests
* `tests/test_repl/test_parser.py` - Parser tests
* `tests/test_tasks/test_manager.py` - Manager tests

### Files Removed (0)

None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: Optional `model` field added to agent config, optional `default_model` at config root

### Deployment Notes

No special deployment considerations. Existing configs without model fields continue to work (backward compatible).
