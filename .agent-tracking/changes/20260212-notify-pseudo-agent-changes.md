<!-- markdownlint-disable-file -->
# Release Changes: @notify Pseudo-Agent

**Related Plan**: 20260212-notify-pseudo-agent-plan.instructions.md
**Implementation Date**: 2026-02-12

## Summary

Implement `@notify` as a first-class pseudo-agent that enables sending notifications within agent pipelines without invoking the Copilot SDK. Supports `$ref` syntax, output truncation, and non-blocking failure handling.

## Changes

### Added

* `tests/test_repl/test_router.py` - Added TestNotifyAgentRecognition test class for @notify validation
* `tests/test_tasks/test_executor.py` - Added TestPseudoAgentDetection, TestNotifyHandler, TestTruncationForNotification, TestNotifyResultStorage, TestNotifySimpleExecution, TestNotifyInPipeline, TestNotifyFailureHandling, TestNotifyInMultiagent test classes
* `tests/test_ui/test_status_panel.py` - Added TestStatusPanelNotifyAgent test class
* `tests/test_repl/test_commands.py` - Added TestLegacyNotifyCommandRemoved test class

### Modified

* `src/teambot/repl/router.py:20` - Added "notify" to VALID_AGENTS set
* `src/teambot/tasks/executor.py` - Added PSEUDO_AGENTS constant, is_pseudo_agent(), truncate_for_notification(), _handle_notify() method, config parameter to __init__, pseudo-agent intercepts in _execute_simple(), _execute_pipeline(), _execute_multiagent()
* `src/teambot/repl/commands.py` - Updated help text to include @notify, removed /notify command handler and method
* `src/teambot/ui/agent_state.py:73` - Added "notify" to DEFAULT_AGENTS list
* `src/teambot/ui/widgets/status_panel.py` - Added (n/a) model display for notify agent
* `tests/test_repl/test_router.py` - Updated test_get_all_agents to expect 7 agents
* `tests/test_tasks/test_executor.py` - Updated test_execute_error_message_lists_valid_agents to include notify
* `tests/test_acceptance_validation.py` - Updated AT-003 through AT-007 tests for @notify pseudo-agent (removed /notify command tests)
* `tests/test_acceptance_unknown_agent.py` - Updated to exclude pseudo-agents from SDK dispatch test
* `tests/test_acceptance_unknown_agent_validation.py` - Updated to expect 7 agents
* `tests/test_ui/test_status_panel.py` - Updated test_renders_all_agents to expect 7 agents

### Removed

* `src/teambot/repl/commands.py` - Removed notify() method and /notify handler (superseded by @notify)

## Release Summary

**Total Files Affected**: 12

### Files Created (0)

(No new files created)

### Files Modified (12)

* `src/teambot/repl/router.py` - Added notify to VALID_AGENTS
* `src/teambot/tasks/executor.py` - Core @notify implementation
* `src/teambot/repl/commands.py` - Removed /notify, updated help
* `src/teambot/ui/agent_state.py` - Added notify to DEFAULT_AGENTS
* `src/teambot/ui/widgets/status_panel.py` - Added (n/a) display
* `tests/test_repl/test_router.py` - Added @notify tests
* `tests/test_tasks/test_executor.py` - Added @notify tests
* `tests/test_repl/test_commands.py` - Updated for /notify removal
* `tests/test_ui/test_status_panel.py` - Added @notify UI tests
* `tests/test_acceptance_validation.py` - Updated acceptance tests
* `tests/test_acceptance_unknown_agent.py` - Updated for pseudo-agents
* `tests/test_acceptance_unknown_agent_validation.py` - Updated agent count

### Files Removed (0)

(No files removed)

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No special deployment considerations. The @notify pseudo-agent is a drop-in replacement for the /notify command and works with existing notification configuration.

