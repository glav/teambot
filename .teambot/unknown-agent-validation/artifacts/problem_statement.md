# Problem Statement: Unknown Agent ID Validation

## Business Problem

When a user directs a command to a non-existent agent (e.g., `@unknown-agent do something`), TeamBot silently accepts the command instead of rejecting it. The unknown agent falls back to the generic **builder** persona, executes the task under a misleading identity, and appears in the status window as if it were a legitimate team member. This violates the user's expectation that the 6-agent team (`pm`, `ba`, `writer`, `builder-1`, `builder-2`, `reviewer`) is a closed, well-defined set.

## Root Cause Analysis

The defect stems from **two independent validation gaps** in the REPL command pipeline:

| # | Gap | Location | Detail |
|---|-----|----------|--------|
| 1 | **TaskExecutor bypass** | `loop.py:324-335` | Multi-agent, pipeline, background, and `$ref` commands are routed directly to `TaskExecutor.execute()`, skipping the router's `VALID_AGENTS` check entirely. |
| 2 | **AgentStatusManager auto-creation** | `agent_state.py:176-194` | `_update()`, `set_idle()`, and `set_model()` all auto-create status entries for any `agent_id` they receive, with no validation against the known agent set. |

**Validation that does exist** — the simple-route path through `AgentRouter._route_agent()` (`router.py:160-169`) correctly checks `VALID_AGENTS` and raises `RouterError` for unknown IDs — is only reached for single-agent, synchronous, non-reference commands. All other command shapes bypass it.

### Affected Code Paths

```
Parser (syntax only — no semantic check)
  └─► REPL Loop routing decision (loop.py:324-335)
        ├─► Simple path → AgentRouter._route_agent() ✅ validates VALID_AGENTS
        └─► Advanced path → TaskExecutor.execute() ❌ no agent ID validation
              ├─► _execute_simple()       — no check
              ├─► _execute_multiagent()   — no check
              └─► _execute_pipeline()     — no check
                    └─► AgentRunner falls back to BUILDER persona silently
                          └─► AgentStatusManager auto-creates ghost entry
```

## Impact

| Impact | Severity | Description |
|--------|----------|-------------|
| **Misleading execution** | High | User believes a specialist persona is handling the task; in reality, the generic builder persona runs it. Output quality and framing will not match the user's intent. |
| **Ghost agents in status** | Medium | The status window shows agents that don't exist in the team definition, creating confusion about what agents are active and what work is in progress. |
| **Silent failure** | Medium | No error or warning is surfaced. The user has no signal that a typo occurred (e.g., `@buidler-1` instead of `@builder-1`). |
| **Inconsistent behaviour** | Low | Simple `@unknown query` is correctly rejected, but `@unknown query &` (background) or `@pm,unknown query` (multi-agent) silently succeeds. Users cannot predict which commands will be validated. |

## Goals

1. **Reject unknown agent IDs early** — before any task is dispatched or status entry created.
2. **Return a clear, actionable error** listing the valid agent IDs so the user can self-correct.
3. **Cover all command shapes** — simple, multi-agent, pipeline, background, and `$ref` — through a single validation point.
4. **Preserve existing behaviour** for all 6 valid agents and their aliases (`project_manager`, `business_analyst`, `technical_writer`).

## Success Criteria

| # | Criterion | Measurable? |
|---|-----------|-------------|
| SC-1 | `@unknown-agent query` returns error: `Unknown agent: 'unknown-agent'. Valid agents: pm, ba, writer, builder-1, builder-2, reviewer` | Yes — string match |
| SC-2 | Validation occurs before `TaskExecutor` creates any task | Yes — no task dispatch observed |
| SC-3 | `AgentStatusManager` does not create entries for invalid agent IDs | Yes — status dict unchanged |
| SC-4 | Multi-agent commands (e.g., `@builder-1,unknown query`) validate **all** IDs before execution | Yes — error returned, no partial execution |
| SC-5 | Pipeline commands (e.g., `@unknown -> @pm query`) validate all IDs | Yes — error returned |
| SC-6 | Background commands (e.g., `@unknown query &`) validate agent ID | Yes — error returned |
| SC-7 | All 6 valid agents and 3 aliases continue to work unchanged | Yes — existing test suite passes |
| SC-8 | New tests cover unknown agent rejection for simple, multi-agent, pipeline, and background paths | Yes — test count increases |

## Constraints

- **Single source of truth**: The set of valid agents must be read from the existing `VALID_AGENTS` set in `router.py` (or resolved through `AGENT_ALIASES`). No duplication.
- **Minimal change**: This is a targeted bug fix. No architectural refactoring.
- **Fail fast**: Validation should occur at the earliest sensible point — ideally in `TaskExecutor.execute()` entry or in the REPL loop before dispatching.
- **Do not break the router path**: The existing simple-route validation in `AgentRouter._route_agent()` must remain untouched.

## Assumptions

1. The 6-agent set is static for the current release; dynamic agent registration is out of scope.
2. Agent aliases (`project_manager` → `pm`, etc.) should also be accepted as valid.
3. The error message format should be human-readable, not machine-parseable.
4. No changes to the parser's syntactic regex are needed — the parser's job is syntax, not semantics.

## Dependencies

- None — this is a self-contained fix within `src/teambot/repl/` and `src/teambot/tasks/`.

## Stakeholders

- **End users**: Directly affected — they receive confusing output today.
- **Agent personas**: Indirectly affected — builder persona is incorrectly invoked for non-builder work.
