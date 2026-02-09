## Objective

- Provide visibility into which agent is the current default (fallback) agent and allow users to change the default agent at runtime without restarting TeamBot.

**Goal**:

- When a user types plain text without an `@agent` directive, it is routed to a default agent. Currently this defaults to the `pm` agent via configuration (`teambot.json`).
- Users should be able to clearly see which agent is the current default/fallback agent in the UI at all times.
- Users should be able to switch the default agent at runtime using a slash command (e.g., `/use-agent builder-1`) so that subsequent plain text input is routed to the newly selected agent.
- The runtime change should persist for the duration of the session but not alter the `teambot.json` configuration file.
- If the session is restarted, the default agent should revert to whatever is configured in `teambot.json`.

**Problem Statement**:

- Currently, the default agent is set in configuration and cannot be changed at runtime.
- Users who want to have an extended conversation with a specific agent (e.g., `builder-1`) must prefix every message with `@builder-1`, which is tedious and error-prone.
- There is no visual indicator in the UI showing which agent will receive plain text input, leading to confusion about where messages are being routed.
- A runtime switching mechanism would significantly improve the interactive workflow, especially when a user is focused on a particular phase of work (e.g., implementation with a builder agent).

**Success Criteria**:
- [ ] The current default/fallback agent is visibly indicated in the terminal UI Agent display panel, as well as part of the `/status` output.
- [ ] A `/use-agent <agent-id>` slash command (or similar) is available to change the default agent at runtime.
- [ ] After running `/use-agent builder-1`, plain text input (without `@agent`) is routed to `builder-1` instead of the previous default.
- [ ] Running `/use-agent` without arguments displays the current default agent and lists available agents to switch to.
- [ ] Invalid agent IDs produce a clear, helpful error message (e.g., "Unknown agent 'foo'. Available agents: pm, ba, writer, builder-1, builder-2, reviewer").
- [ ] The `/status` command reflects which agent is the current default.
- [ ] The runtime default agent change does not persist to `teambot.json` — it is session-scoped only.
- [ ] The `/help` command includes documentation for the new `/use-agent` command.
- [ ] Existing `@agent` directives continue to work as before, regardless of the current default agent setting.
- [ ] Running `/reset-agent` command  will allow users to easily revert to the original configuration default.
- [ ] All new functionality has test coverage following existing test patterns.

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically the REPL router (`src/teambot/repl/router.py`), REPL loop (`src/teambot/repl/loop.py`), UI app (`src/teambot/ui/app.py`), and related modules.

**Primary Language/Framework**:

- Python

**Testing Preference**:

- Follow current pattern (`pytest` with `pytest-mock`)

**Key Constraints**:
- Must not break existing `@agent` directive routing or any other slash commands.
- Must work in both the standard REPL and the split-pane UI modes.
- The `AgentRouter` already accepts a `default_agent` parameter and handles fallback routing — the implementation should extend this existing mechanism rather than introducing a parallel system.
- Configuration validation in `config/loader.py` already validates `default_agent` — runtime switching should use the same validation logic where possible.

---

## Additional Context

- The `AgentRouter` class in `src/teambot/repl/router.py` already has infrastructure for default agent routing (see `_route_raw` method and `_default_agent` attribute). The runtime switching feature should add a method to update `_default_agent` and expose it via a new slash command.
- The prompt or status display should make it obvious which agent is the default. For example, the input prompt could show `[pm] > ` or `[builder-1] > ` to indicate the current default agent.
- The `/agents` or `/status` command output should distinguish the current default agent from other agents (e.g., with a marker like `(default)` or `*`).
- This change should incrementally bump the version number to the next minor version number.

---
