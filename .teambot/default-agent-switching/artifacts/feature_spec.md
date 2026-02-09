<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Runtime Default Agent Switching - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target v0.2.0 | Lifecycle Design

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-09 |
| Problem & Users | ✅ | None | 2026-02-09 |
| Scope | ✅ | None | 2026-02-09 |
| Requirements | ✅ | None | 2026-02-09 |
| Metrics & Risks | ✅ | None | 2026-02-09 |
| Operationalization | ✅ | None | 2026-02-09 |
| Finalization | ✅ | None | 2026-02-09 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot is a CLI tool that orchestrates 6 specialized AI agent personas (`pm`, `ba`, `writer`, `builder-1`, `builder-2`, `reviewer`) through a REPL interface. When users type plain text without an `@agent` directive, it is routed to a configurable default agent — currently `pm` via `teambot.json`. This default agent acts as the "conversational home" for unaddressed input.

### Core Opportunity
Users frequently shift focus to a single agent for extended periods (e.g., `builder-1` during implementation). Today, every message to a non-default agent requires an explicit `@agent` prefix, creating repetitive friction. Allowing runtime switching of the default agent eliminates this overhead without requiring configuration file edits or session restarts.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Reduce input friction for users focused on a single non-default agent | UX | Every non-default message requires `@agent` prefix | Plain text routes to user-chosen agent | Immediate on switch | P0 |
| G-002 | Provide runtime default agent switching without config mutation | Functionality | Must edit `teambot.json` and restart | `/use-agent` command switches in-session | Immediate | P0 |
| G-003 | Ensure current default agent is always visible in the UI | UX | No visibility of which agent receives plain text | Indicated in status panel and `/status` output | Immediate | P0 |
| G-004 | Maintain session-scoped changes that reset on restart | Data Integrity | N/A | Runtime changes never persist to `teambot.json` | Always | P0 |
| G-005 | Preserve backward compatibility with all existing routing | Stability | All `@agent` directives and slash commands work | No regressions | Always | P0 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Ship `/use-agent` and `/reset-agent` commands | Commands registered, dispatched, and tested in both REPL and UI modes | P0 | Builder |
| Integrate default agent visibility into UI | Status panel and `/status` output show current default | P0 | Builder |
| Achieve full test coverage | All new paths covered by pytest tests following existing patterns | P0 | Builder |

## 2. Problem Definition

### Current Situation
The `AgentRouter` class (`src/teambot/repl/router.py`) accepts a `default_agent` parameter at construction time and uses it to route raw (unaddressed) input to the specified agent. This value is extracted from the `teambot.json` configuration file during `REPLLoop.__init__()` and `TeamBotApp.__init__()`, and cannot be changed after initialization.

The `SystemCommands` class (`src/teambot/repl/commands.py`) provides 10 slash commands (e.g., `/help`, `/status`, `/model`) but none that modify the default agent. The `/status` output shows agent states and models but does not indicate which agent is the current default.

### Problem Statement
Users who work extensively with a non-default agent (e.g., `builder-1` during implementation phases) must prefix every single message with `@builder-1`, which is repetitive and slows down the workflow. There is no way to change the default agent without editing the configuration file and restarting the session — a disruptive action that also permanently alters the project-level configuration.

### Root Causes
* The `AgentRouter._default_agent` attribute is set once at construction and has no setter or mutation method.
* No slash command exists to modify the default agent at runtime.
* The UI (status panel and `/status` output) does not display which agent is the current default/fallback.

### Impact of Inaction
* Users continue to experience repetitive input friction during focused work with non-default agents.
* Power users who shift between agents across workflow stages are most affected, reducing their productivity.
* Users may resort to editing `teambot.json` mid-session, creating unintended persistent configuration changes.

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| **REPL User** — Developer using the standard REPL (`loop.py`) for interactive sessions | Send messages to agents quickly; minimize typing overhead | Must prefix every non-default message with `@agent` | High — directly reduces input speed |
| **Split-Pane UI User** — Developer using the Textual-based split-pane interface (`app.py`) | Monitor agent activity while interacting; see which agent is "active" | No visual indicator of which agent receives plain text; same prefix overhead | High — both input friction and visibility gap |
| **Power User** — Developer running long sessions that span multiple workflow stages | Switch focus between agents fluidly as work progresses (plan → build → review) | Must either keep typing prefixes or edit config and restart | Very High — repeated friction across stage transitions |

### Journeys

**Journey: Implementation-Focused Session**
1. User starts TeamBot → default is `pm` (from config)
2. User sends planning messages as plain text → routed to `pm` ✅
3. User shifts to implementation → types `/use-agent builder-1`
4. User sees confirmation: "Default agent set to builder-1"
5. User sends implementation messages as plain text → routed to `builder-1` ✅
6. User occasionally sends `@reviewer check this` → routed to `reviewer` (explicit directive) ✅
7. User finishes implementation → types `/reset-agent`
8. User sees confirmation: "Default agent reset to pm (from configuration)"
9. Plain text routes to `pm` again ✅

## 4. Scope

### In Scope
* New `/use-agent <agent-id>` slash command to switch the session default agent
* New `/reset-agent` slash command to revert to the `teambot.json` configured default
* `AgentRouter` mutation method (setter or `set_default_agent()`) for runtime changes
* Default agent visibility in the status panel widget (`StatusPanel`)
* Default agent visibility in `/status` command output (both REPL and UI modes)
* `/help` documentation for both new commands
* Agent ID validation reusing logic consistent with `ConfigLoader._validate_default_agent()`
* Confirmation messages on successful switch and reset
* Error messages for invalid agent IDs
* Test coverage for all new functionality

### Out of Scope (justify if empty)
* Persisting runtime default changes across sessions (session-scoped by design)
* Modifying `teambot.json` at any point (session-scoped by design)
* Adding new agent personas or modifying existing ones
* Changing how explicit `@agent` directive routing works
* Multi-default or per-stage default agent configuration
* Agent alias support in `/use-agent` (e.g., `/use-agent project_manager`) — may be added later

### Assumptions
* The 6 MVP agent IDs (`pm`, `ba`, `writer`, `builder-1`, `builder-2`, `reviewer`) are the valid set for switching.
* Both REPL mode and split-pane UI mode share or independently manage an `AgentRouter` instance — the feature must work in both.
* The `SystemCommands` dispatch pattern (dict mapping command name → handler) is the correct extension point for new commands.
* The `AgentRouter.VALID_AGENTS` set (or equivalent) is the authoritative source for valid agent IDs at runtime.

### Constraints
* Must not break any existing `@agent` directive routing or slash commands.
* Must not introduce file I/O for this feature — all state is in-memory.
* Must work in both standard REPL and split-pane UI modes.
* Must follow existing code patterns and testing conventions (`pytest` + `pytest-mock`).

## 5. Product Overview

### Value Proposition
Runtime default agent switching lets users focus on one agent at a time without repetitive `@agent` prefixes, while maintaining full visibility of which agent is receiving their input. It respects configuration integrity by keeping changes session-scoped.

### UX / UI

**Slash Command Interactions:**

```
# Switch default agent
> /use-agent builder-1
✓ Default agent set to builder-1. Plain text input will now be routed to @builder-1.

# View current default and available agents
> /use-agent
Current default agent: builder-1
Available agents: pm, ba, writer, builder-1, builder-2, reviewer

# Invalid agent
> /use-agent foo
✗ Unknown agent 'foo'. Available agents: pm, ba, writer, builder-1, builder-2, reviewer

# Reset to config default
> /reset-agent
✓ Default agent reset to pm (from configuration).

# Reset when already at config default
> /reset-agent
Default agent is already set to pm (from configuration).
```

**Status Panel Indicator (split-pane UI):**
The `StatusPanel` widget should annotate the current default agent. Example:

```
● pm (sonnet-4) default ← indicator
● ba (sonnet-4) idle
● writer (sonnet-4) idle
● builder-1 (sonnet-4) idle
● builder-2 (sonnet-4) idle
● reviewer (sonnet-4) idle
```

When switched to `builder-1`:
```
● pm (sonnet-4) idle
● ba (sonnet-4) idle
● writer (sonnet-4) idle
● builder-1 (sonnet-4) default ← moved
● builder-2 (sonnet-4) idle
● reviewer (sonnet-4) idle
```

**`/status` Output Enhancement:**

```
Agent Status:

  Default Agent: builder-1 (session override; config default: pm)

  Agent        Status     Model
  ----------- ---------- --------------------
  pm           idle       (default)
  ba           idle       (default)
  writer       idle       (default)
  builder-1    idle       (default)      ← default
  builder-2    idle       (default)
  reviewer     idle       (default)
```

| UX Status: Complete |

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|-------------|-------|----------|----------|------------|-------|
| FR-DAS-001 | `/use-agent` with argument | Running `/use-agent <agent-id>` sets the session default agent to `<agent-id>`. Subsequent plain text (RAW) input routes to the new default. | G-001, G-002 | All | P0 | After `/use-agent builder-1`, a `Command(type=RAW, content="hello")` routes to `builder-1` | Extends `AgentRouter` |
| FR-DAS-002 | `/use-agent` without argument | Running `/use-agent` with no arguments displays the current default agent and lists all available agents. | G-003 | All | P0 | Output contains current default ID and all 6 agent IDs | Informational only |
| FR-DAS-003 | `/reset-agent` command | Running `/reset-agent` reverts the session default agent to the value from `teambot.json`. | G-002, G-004 | All | P0 | After reset, `AgentRouter.get_default_agent()` returns original config value | Must store original value |
| FR-DAS-004 | Invalid agent ID error | Running `/use-agent <invalid>` returns a clear error listing valid agents. Does not change the current default. | G-002 | All | P0 | Error message contains the invalid ID and all valid agent IDs | No state change on error |
| FR-DAS-005 | Default agent in `/status` | The `/status` command output includes a line indicating the current default agent. If overridden, shows both current and config default. | G-003 | All | P0 | `/status` output contains "Default Agent: <id>" | Both REPL and UI modes |
| FR-DAS-006 | Default agent in status panel | The split-pane UI `StatusPanel` widget annotates the current default agent in the agent list. | G-003 | Split-Pane UI User | P0 | Default agent row displays a "default" indicator | Reactive to changes |
| FR-DAS-007 | `/help` documentation | The `/help` output includes usage documentation for `/use-agent` and `/reset-agent`. | G-002 | All | P0 | `/help` output contains both command names with descriptions | |
| FR-DAS-008 | Confirmation on switch | After a successful `/use-agent <id>`, a confirmation message is displayed indicating the new default. | G-003 | All | P1 | Output contains the agent ID and confirms routing change | |
| FR-DAS-009 | Confirmation on reset | After a successful `/reset-agent`, a confirmation message is displayed indicating the restored default. | G-003 | All | P1 | Output contains the config default agent ID | |
| FR-DAS-010 | Session scoping | The runtime default agent change exists only in memory. `teambot.json` is never read from or written to by these commands. | G-004 | All | P0 | No file I/O occurs during `/use-agent` or `/reset-agent` | Critical constraint |
| FR-DAS-011 | Explicit `@agent` unaffected | Explicit `@agent` directives continue to route to the named agent regardless of the current session default. | G-005 | All | P0 | `@reviewer task` routes to `reviewer` even when default is `builder-1` | Existing behavior preserved |
| FR-DAS-012 | Already-at-target idempotency | Running `/use-agent pm` when `pm` is already the default produces an informational message (not an error). | G-002 | All | P2 | Output indicates agent is already the default | Nice-to-have UX polish |
| FR-DAS-013 | Reset when already at config default | Running `/reset-agent` when the default is already the config value produces an informational message. | G-002 | All | P2 | Output indicates already at config default | Nice-to-have UX polish |

### Feature Hierarchy
```plain
Runtime Default Agent Switching
├── /use-agent command
│   ├── FR-DAS-001: Switch with argument
│   ├── FR-DAS-002: Info without argument
│   ├── FR-DAS-004: Invalid ID error
│   ├── FR-DAS-008: Confirmation message
│   └── FR-DAS-012: Idempotency message
├── /reset-agent command
│   ├── FR-DAS-003: Reset to config default
│   ├── FR-DAS-009: Confirmation message
│   └── FR-DAS-013: Already-at-default message
├── UI Integration
│   ├── FR-DAS-005: /status output
│   └── FR-DAS-006: Status panel indicator
├── Documentation
│   └── FR-DAS-007: /help updated
└── Constraints
    ├── FR-DAS-010: Session scoping (no file I/O)
    └── FR-DAS-011: @agent directives unaffected
```

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-DAS-001 | Performance | `/use-agent` and `/reset-agent` must execute with no perceptible delay | < 10ms response time | P0 | Manual testing; in-memory operation only | No I/O involved |
| NFR-DAS-002 | Reliability | Default agent state must be consistent across the router and all UI surfaces after a switch | Router, status panel, and `/status` all reflect same value | P0 | Test assertions on state after switch | Single source of truth in router |
| NFR-DAS-003 | Maintainability | New commands must follow existing `SystemCommands` dispatch pattern exactly | Code review; pattern matches `/model`, `/overlay` | P0 | Review; no new dispatch mechanisms | |
| NFR-DAS-004 | Maintainability | Test coverage for all new code paths | 100% of new lines covered | P0 | `pytest --cov` delta check | Follow existing test patterns |
| NFR-DAS-005 | Security | No file write operations for this feature | Zero file I/O in `/use-agent` and `/reset-agent` code paths | P0 | Code review; no `open()` or path writes | Prevents accidental config mutation |
| NFR-DAS-006 | Accessibility | Confirmation and error messages must be clear text (not just color-coded) | Messages contain descriptive text independent of styling | P1 | Manual review of output strings | |

## 8. Data & Analytics

### Inputs
* User input: `/use-agent <agent-id>` or `/reset-agent` (parsed by `parse_command()` as `CommandType.SYSTEM`)
* Configuration: `teambot.json` `default_agent` value (read once at startup, stored as original default)
* Runtime state: `AgentRouter._default_agent` (mutable in-memory attribute)

### Outputs / Events
* Command result: `CommandResult` object with success/failure status and display message
* State change: `AgentRouter._default_agent` updated in memory
* UI update: `StatusPanel` re-renders with updated default indicator (via listener pattern)

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| All existing tests pass | Quality | 100% pass | 100% pass | Per commit | `uv run pytest` |
| New feature test count | Quality | 0 | ≥ 15 tests | Feature complete | `uv run pytest tests/test_repl/` |
| Ruff lint clean | Quality | 0 violations | 0 violations | Per commit | `uv run ruff check .` |

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| `AgentRouter` (`router.py`) | Internal | High | Builder | Mutation method needed; must not break existing routing | Extend with setter; preserve constructor behavior |
| `SystemCommands` (`commands.py`) | Internal | High | Builder | Two new handlers in dispatch table | Follow exact pattern of existing commands |
| `StatusPanel` (`status_panel.py`) | Internal | Medium | Builder | Must access router's default agent state | Use existing listener pattern from `AgentStatusManager` |
| `/status` handler (`commands.py`) | Internal | Medium | Builder | Output format change | Additive only — prepend default agent info |
| `/help` handler (`commands.py`) | Internal | Low | Builder | Text addition | Append new commands to existing help text |
| `AgentRouter.VALID_AGENTS` | Internal | Low | Builder | Used for validation | Already exists; no changes needed |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Accidental mutation of `teambot.json` | High | Low | Feature is purely in-memory; code review enforces no file I/O | Builder/Reviewer | Open |
| R-002 | Router and UI show inconsistent default after switch | Medium | Medium | Single source of truth in `AgentRouter`; UI reads from router | Builder | Open |
| R-003 | Breaking existing `@agent` routing | High | Low | Explicit directives bypass default logic entirely (existing behavior); regression tests | Builder | Open |
| R-004 | `/use-agent` conflicts with future command names | Low | Low | Name is descriptive and follows `/model` pattern; can alias later | PM | Open |
| R-005 | Split-pane UI does not update status panel after switch | Medium | Medium | Use existing `AgentStatusManager` listener pattern to trigger re-render | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
Internal / Non-Sensitive — Agent IDs and routing preferences are not user data.

### PII Handling
No PII is involved in this feature. Agent IDs are system-defined constants.

### Threat Considerations
* **Config mutation**: The only threat vector is accidental writes to `teambot.json`. Mitigated by design (in-memory only) and code review.
* **Agent ID injection**: Invalid agent IDs are validated against the fixed `VALID_AGENTS` set. No arbitrary string execution occurs.

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard package update via `uv sync` | No new dependencies |
| Rollback | Revert to previous version; feature is additive | No data migration needed |
| Monitoring | N/A — CLI tool, no telemetry | |
| Alerting | N/A | |
| Support | `/help` documentation covers usage | Self-documenting |
| Capacity Planning | N/A — in-memory state only | |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Gate Criteria | Owner |
|-------|--------------|-------|
| Implementation | All FRs implemented, all tests pass | Builder |
| Code Review | Review passes, no regressions | Reviewer |
| Merge | CI green, documentation updated | PM |

## 14. Acceptance Test Scenarios

### AT-001: Switch Default Agent and Send Plain Text
**Description**: User switches default agent and verifies plain text routes to the new default.
**Preconditions**: REPL is running with `default_agent: pm` from configuration.
**Steps**:
1. User types `hello` (plain text, no `@agent` prefix)
2. Observe output — message is handled by `pm`
3. User types `/use-agent builder-1`
4. Observe confirmation message
5. User types `build the feature` (plain text, no `@agent` prefix)
6. Observe output — message is handled by `builder-1`
**Expected Result**: After switching, plain text input routes to `builder-1` instead of `pm`.
**Verification**: Agent handler receives `("builder-1", "build the feature")` as arguments.

### AT-002: Explicit `@agent` Directive Overrides Default
**Description**: Explicit `@agent` directives work regardless of current default.
**Preconditions**: REPL running, default switched to `builder-1` via `/use-agent builder-1`.
**Steps**:
1. User types `@reviewer check the code` (explicit directive)
2. Observe output — message is handled by `reviewer`
3. User types `continue building` (plain text)
4. Observe output — message is handled by `builder-1` (still the default)
**Expected Result**: `@reviewer` directive routes to reviewer; plain text still routes to current default `builder-1`.
**Verification**: Agent handler called with `("reviewer", "check the code")` then `("builder-1", "continue building")`.

### AT-003: Reset Agent to Configuration Default
**Description**: User resets the default agent back to the config-defined value.
**Preconditions**: REPL running, default switched to `builder-1`.
**Steps**:
1. User types `/reset-agent`
2. Observe confirmation: "Default agent reset to pm (from configuration)."
3. User types `plan the next sprint` (plain text)
4. Observe output — message is handled by `pm`
**Expected Result**: After reset, plain text routes to `pm` (original config value).
**Verification**: `AgentRouter.get_default_agent()` returns `"pm"`.

### AT-004: Invalid Agent ID Produces Error
**Description**: Attempting to switch to a non-existent agent shows an error.
**Preconditions**: REPL running, any default agent.
**Steps**:
1. User types `/use-agent foo`
2. Observe error message
**Expected Result**: Error message: "Unknown agent 'foo'. Available agents: pm, ba, writer, builder-1, builder-2, reviewer"
**Verification**: Default agent is unchanged. `CommandResult.success` is `False`.

### AT-005: `/use-agent` Without Arguments Shows Info
**Description**: Running `/use-agent` with no arguments displays current default and available agents.
**Preconditions**: REPL running, default is `builder-1` (switched from `pm`).
**Steps**:
1. User types `/use-agent`
2. Observe output
**Expected Result**: Output shows "Current default agent: builder-1" and lists all available agents.
**Verification**: Output contains `builder-1` as current and all 6 agent IDs.

### AT-006: `/status` Shows Default Agent
**Description**: The `/status` command reflects the current session default agent.
**Preconditions**: REPL running, default switched to `builder-1`.
**Steps**:
1. User types `/status`
2. Observe output
**Expected Result**: Status output includes a line such as "Default Agent: builder-1 (session override; config default: pm)".
**Verification**: Output string contains "Default Agent" and "builder-1".

### AT-007: Status Panel Shows Default Indicator (Split-Pane UI)
**Description**: In the split-pane UI, the status panel visually marks the current default agent.
**Preconditions**: Split-pane UI running, default is `pm`.
**Steps**:
1. Observe the status panel — `pm` row has a "default" indicator
2. User types `/use-agent writer`
3. Observe the status panel — `writer` row now has the "default" indicator; `pm` does not
**Expected Result**: The "default" indicator moves from `pm` to `writer` in the status panel.
**Verification**: `StatusPanel` render output for the `writer` row contains "default".

### AT-008: Session Restart Resets Default
**Description**: After restarting the session, the default agent reverts to the config value.
**Preconditions**: Previous session had `/use-agent builder-1` executed.
**Steps**:
1. Restart TeamBot session
2. User types `hello` (plain text)
3. Observe output — message is handled by `pm`
**Expected Result**: Default reverts to `pm` from `teambot.json` — no persistence of runtime change.
**Verification**: `AgentRouter.get_default_agent()` returns `"pm"` on fresh init.

### AT-009: `/help` Documents New Commands
**Description**: The `/help` command includes `/use-agent` and `/reset-agent`.
**Preconditions**: REPL running.
**Steps**:
1. User types `/help`
2. Observe output
**Expected Result**: Help text includes entries for `/use-agent` and `/reset-agent` with descriptions.
**Verification**: Output contains strings `/use-agent` and `/reset-agent`.

## 15. Open Questions

| Q ID | Question | Owner | Status |
|------|----------|-------|--------|
| — | None | — | — |

## 16. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-09 | BA Agent | Initial specification | Creation |

## 17. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Code | `src/teambot/repl/router.py` | `AgentRouter` class with `default_agent` parameter, `get_default_agent()`, `_route_raw()` default routing logic | N/A |
| REF-002 | Code | `src/teambot/repl/commands.py` | `SystemCommands` dispatch pattern, existing `/help`, `/status`, `/model` handlers | N/A |
| REF-003 | Code | `src/teambot/repl/parser.py` | `parse_command()` function, `Command` dataclass, `CommandType` enum | N/A |
| REF-004 | Code | `src/teambot/config/loader.py` | `_validate_default_agent()` validation against `seen_ids` set | N/A |
| REF-005 | Code | `src/teambot/repl/loop.py` | `REPLLoop.__init__` config extraction and router creation | N/A |
| REF-006 | Code | `src/teambot/ui/app.py` | `TeamBotApp._get_status()`, system command routing, router integration | N/A |
| REF-007 | Code | `src/teambot/ui/widgets/status_panel.py` | `StatusPanel` rendering, `AgentStatusManager` listener pattern | N/A |
| REF-008 | Code | `src/teambot/ui/agent_state.py` | `AgentStatusManager`, `AgentStatus`, `AgentState` | N/A |
| REF-009 | Artifact | `.teambot/default-agent-switching/artifacts/problem_statement.md` | Problem statement from Business Problem stage | N/A |

### Citation Usage
All code references verified against the current codebase as of 2026-02-09. The `AgentRouter` default agent mechanism (REF-001), `SystemCommands` dispatch pattern (REF-002), and `StatusPanel` listener pattern (REF-007) are the primary extension points for this feature.

## 18. Appendices

### Glossary
| Term | Definition |
|------|------------|
| Default agent | The agent that receives plain-text input (no `@agent` prefix); configurable in `teambot.json` and overridable at runtime |
| Session default | The current in-memory default agent, which may differ from the configuration default after `/use-agent` |
| Config default | The `default_agent` value from `teambot.json`, used at startup and restored by `/reset-agent` |
| Raw input | User input that does not match `@agent` or `/command` patterns; parsed as `CommandType.RAW` |
| Agent directive | An explicit `@agent-id` prefix on user input that overrides the default agent |

### Technical Notes

**Extension Points Summary:**

| Component | What Changes | How |
|-----------|-------------|-----|
| `AgentRouter` | Add `set_default_agent(agent_id)` method; store `_config_default_agent` | New method + new attribute |
| `SystemCommands` | Add `use-agent` and `reset-agent` to dispatch dict and handler methods | Two new entries + two new methods |
| `handle_status()` | Prepend "Default Agent: ..." line to output | Additive text change |
| `handle_help()` | Add `/use-agent` and `/reset-agent` to command list | Additive text change |
| `StatusPanel` | Add "default" indicator to the current default agent row | Conditional label in render |
| `REPLLoop` / `TeamBotApp` | Pass router reference to `SystemCommands` so it can call `set_default_agent()` | Constructor wiring |

**Validation Logic:**
The `/use-agent` handler should validate the agent ID against `AgentRouter.VALID_AGENTS` (or equivalent set). This mirrors the `ConfigLoader._validate_default_agent()` approach but uses the router's own constant rather than coupling to the config loader at runtime.

Generated 2026-02-09T03:29:00Z by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
