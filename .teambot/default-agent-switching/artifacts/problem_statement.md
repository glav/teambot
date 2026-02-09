# Problem Statement: Runtime Default Agent Switching

## Business Problem

TeamBot routes plain-text input (without an `@agent` directive) to a single default agent configured in `teambot.json`. Today that default is `pm` (Project Manager). Users who spend the majority of a session interacting with a different agent — for example, `builder-1` during an implementation-heavy session — must prefix every message with `@builder-1`, creating repetitive friction that slows down their workflow.

There is no mechanism to change the default agent at runtime. The only way to change it is to edit `teambot.json` and restart the session, which is disruptive and permanently alters the project configuration.

## Who Is Affected

- **All interactive REPL users** — anyone working in the standard REPL or the split-pane UI who sends multiple consecutive messages to the same non-default agent.
- **Power users running long sessions** — users who shift focus between agents across workflow stages (e.g., starting with `pm` for planning, then switching to `builder-1` for implementation) are most impacted.

## Current Behavior

| Scenario | What Happens Today |
|---|---|
| User types plain text (no `@agent`) | Routed to the configured `default_agent` (`pm`) via `AgentRouter` |
| User wants to talk to `builder-1` | Must type `@builder-1 <message>` every time |
| User wants to change the default | Must edit `teambot.json`, restart session |
| UI display | No indication of which agent receives plain-text input |

## Desired Behavior

| Scenario | What Should Happen |
|---|---|
| User types plain text (no `@agent`) | Routed to the **current session default** agent |
| User runs `/use-agent builder-1` | Session default changes to `builder-1`; subsequent plain text goes to `builder-1` |
| User runs `/use-agent` (no args) | Displays current default agent and lists available agents |
| User runs `/reset-agent` | Reverts session default to the original `teambot.json` value |
| UI display | Current default agent is **visibly indicated** in the Agent Display panel and `/status` output |
| Session restarts | Default reverts to `teambot.json` configuration (no persistence of runtime change) |
| User types `@reviewer <message>` | Still routed to `reviewer` regardless of session default (existing behavior preserved) |

## Goals

1. **Reduce input friction** — Eliminate repetitive `@agent` prefixes when a user is focused on one agent for an extended period.
2. **Provide runtime flexibility** — Allow switching the default agent without editing configuration or restarting.
3. **Maintain visibility** — Ensure users always know which agent will receive their plain-text input.
4. **Preserve session scoping** — Runtime changes must not alter `teambot.json`; defaults reset on session restart.
5. **Maintain backward compatibility** — Existing `@agent` directives, slash commands, and all other routing behavior must continue to work unchanged.

## Success Criteria

| # | Criterion | Measurable Outcome |
|---|---|---|
| SC-1 | Default agent visibility | Current default agent is indicated in the terminal UI Agent Display panel and in `/status` output |
| SC-2 | `/use-agent <id>` command | Running `/use-agent builder-1` causes subsequent plain text to route to `builder-1` |
| SC-3 | `/use-agent` (no args) | Displays current default and lists available agents |
| SC-4 | `/reset-agent` command | Reverts session default to the `teambot.json` configured value |
| SC-5 | Invalid agent error | Running `/use-agent foo` produces: `"Unknown agent 'foo'. Available agents: pm, ba, writer, builder-1, builder-2, reviewer"` |
| SC-6 | `/status` integration | `/status` output includes which agent is the current session default |
| SC-7 | No config mutation | `teambot.json` is never written to; runtime default is session-scoped only |
| SC-8 | `/help` updated | `/help` output documents `/use-agent` and `/reset-agent` commands |
| SC-9 | `@agent` unaffected | Explicit `@agent` directives route to the named agent regardless of the current default |
| SC-10 | Test coverage | All new functionality has test coverage following existing `pytest` + `pytest-mock` patterns |

## Assumptions

1. The existing `AgentRouter.get_default_agent()` method and `default_agent` constructor parameter provide the foundation for this feature — the implementation should extend this mechanism rather than introduce a parallel routing system.
2. The `ConfigLoader._validate_default_agent()` validation logic can be reused for runtime agent-ID validation.
3. The set of valid agent IDs is the 6 MVP agents: `pm`, `ba`, `writer`, `builder-1`, `builder-2`, `reviewer`.
4. Both the standard REPL mode (`loop.py`) and the split-pane UI mode (`app.py`) must support this feature.
5. The `/use-agent` and `/reset-agent` commands will be registered in the `SystemCommands` dispatch table alongside existing slash commands.

## Dependencies

| Dependency | Component | Impact |
|---|---|---|
| `AgentRouter` | `src/teambot/repl/router.py` | Needs a mutable `default_agent` property or setter method |
| `SystemCommands` | `src/teambot/repl/commands.py` | Needs two new command handlers registered in dispatch |
| `StatusPanel` / `/status` | `src/teambot/ui/widgets/status_panel.py`, `commands.py` | Must reflect current session default |
| Agent Display panel | `src/teambot/ui/app.py` | Must visually indicate the current default agent |
| `/help` output | `src/teambot/repl/commands.py` | Must document the new commands |
| Config validation | `src/teambot/config/loader.py` | Validation logic reused (not modified) at runtime |

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Accidental config file mutation | Low | High | Implementation must only mutate in-memory state; no file I/O for this feature |
| User confusion about current default | Medium | Medium | Clear UI indicator + `/status` integration + confirmation message on switch |
| Inconsistency between REPL and UI modes | Medium | Medium | Both modes share `AgentRouter`; changes propagate via the same instance |
| Breaking existing `@agent` routing | Low | High | Explicit agent directives bypass default agent logic entirely (existing behavior) |

## Out of Scope

- Persisting runtime default agent changes across sessions (e.g., to a session state file).
- Changing the default agent via the `teambot.json` configuration file as part of this feature.
- Adding new agent personas or modifying existing ones.
- Changing how `@agent` directive routing works.
- Multi-default or per-stage default agent configuration.
