<!-- markdownlint-disable-file -->
# Release Changes: Runtime Default Agent Switching

**Related Plan**: 20260209-default-agent-switching-plan.instructions.md
**Implementation Date**: 2026-02-09

## Summary

Add `/use-agent` and `/reset-agent` slash commands to change the default agent at runtime, with UI visibility of the current default, without persisting to `teambot.json`.

## Changes

### Added

* `src/teambot/repl/router.py` — Added `_config_default_agent` attribute, `set_default_agent()` method with validation, `get_config_default_agent()` method
* `src/teambot/repl/commands.py` — Added `handle_use_agent()` and `handle_reset_agent()` module-level handler functions
* `src/teambot/repl/commands.py` — Added `_router` param, `set_router()`, dispatch entries for `use-agent`/`reset-agent`, and wrapper methods on `SystemCommands`
* `src/teambot/ui/agent_state.py` — Added `_default_agent` field, `set_default_agent()`, `get_default_agent()` to `AgentStatusManager`
* `tests/test_repl/test_router.py` — Added `TestRouterDefaultAgentMutation` class (6 tests)
* `tests/test_repl/test_commands.py` — Added `TestUseAgentCommand` (5 tests), `TestResetAgentCommand` (3 tests), dispatch integration tests (2 tests), help/status enhancement tests (3 tests)
* `tests/test_ui/test_agent_state.py` — Added `TestAgentStatusManagerDefaultAgent` class (4 tests)
* `tests/test_ui/test_status_panel.py` — Added `TestStatusPanelDefaultIndicator` class (4 tests)
* `tests/test_repl/test_loop.py` — Added `test_system_commands_has_router` test
* `tests/test_ui/test_app.py` — Added `TestAppRouterWiring` class (2 tests)

### Modified

* `src/teambot/repl/commands.py` — Updated `handle_help()` with `/use-agent` and `/reset-agent` entries; updated `handle_status()` to accept router and show default agent info; updated `SystemCommands.status()` to pass router
* `src/teambot/ui/widgets/status_panel.py` — Updated `_format_status()` to show `★` indicator and `default` label for the current default agent
* `src/teambot/repl/loop.py` — Passed `router=self._router` to `SystemCommands` constructor
* `src/teambot/ui/app.py` — Passed router to `SystemCommands`; initialized `AgentStatusManager` default from router; added post-dispatch update for use-agent/reset-agent; added default agent info to `_get_status()`

### Removed

*None*

## Release Summary

**Total Files Affected**: 10

### Files Created (0)

*No new files created*

### Files Modified (10)

* `src/teambot/repl/router.py` — Added runtime default agent mutation methods
* `src/teambot/repl/commands.py` — Added use-agent/reset-agent handlers and dispatch
* `src/teambot/ui/agent_state.py` — Added default agent tracking to AgentStatusManager
* `src/teambot/ui/widgets/status_panel.py` — Added default agent indicator in status panel
* `src/teambot/repl/loop.py` — Wired router to SystemCommands
* `src/teambot/ui/app.py` — Wired router to SystemCommands and UI components
* `tests/test_repl/test_router.py` — Added router mutation tests
* `tests/test_repl/test_commands.py` — Added command handler and integration tests
* `tests/test_ui/test_agent_state.py` — Added default agent tracking tests
* `tests/test_ui/test_status_panel.py` — Added default indicator tests
* `tests/test_repl/test_loop.py` — Added router wiring test
* `tests/test_ui/test_app.py` — Added app router wiring tests

### Files Removed (0)

*None*

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No deployment changes required. Feature is session-scoped only — no configuration file changes needed.

