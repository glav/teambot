## Objective

- Validate agent IDs when a user types `@<agent_id> <query>` in the TeamBot REPL, and reject unrecognised agent IDs with a clear error message.

**Goal**:

- When a user types `@some-agent query` and `some-agent` is not one of the 6 defined agents (`pm`, `ba`, `writer`, `builder-1`, `builder-2`, `reviewer`), TeamBot should reject the command immediately with a helpful error message.
- Currently, unrecognised agent IDs are accepted and executed via the TaskExecutor code path, bypassing the validation that exists in the simple router path.
- The unknown agent silently falls back to the generic "builder" persona, which is confusing and misleading.
- The AgentStatusManager auto-creates status entries for unknown agents, causing them to appear in the status window as if they are real agents.

**Problem Statement**:

- The REPL parser (`repl/parser.py`) accepts any agent ID matching the regex pattern without validating against the known agent set.
- The TaskExecutor (`executor.py`) dispatches commands to agents without checking if the agent ID is valid, bypassing the `VALID_AGENTS` check that exists in the router's simple path.
- The AgentStatusManager (`agent_state.py`) auto-creates status entries for any agent ID it encounters, which means unknown agents appear in the `/status` display and status window.
- This can occur from a simple typo (e.g., `@buidler-1` instead of `@builder-1`) and gives no feedback to the user that something is wrong.
- The query runs under the generic "builder" persona fallback in AgentRunner, so the user gets a response but from an unintended persona with no specialised context.

**Success Criteria**:
- [ ] Typing `@unknown-agent query` returns a clear error message listing the valid agent IDs.
- [ ] The error message is user-friendly, e.g., `Unknown agent: 'unknown-agent'. Valid agents: pm, ba, writer, builder-1, builder-2, reviewer`.
- [ ] Validation occurs early enough that no task is dispatched and no agent status entry is created.
- [ ] The TaskExecutor path validates agent IDs before executing, closing the bypass around the router's existing validation.
- [ ] The AgentStatusManager does not auto-create entries for invalid agent IDs.
- [ ] Multi-agent commands (e.g., `@builder-1,unknown query`) also validate all agent IDs before execution.
- [ ] Existing valid agent commands (`@pm`, `@ba`, `@writer`, `@builder-1`, `@builder-2`, `@reviewer`) continue to work as before.
- [ ] All existing tests pass; new tests cover the unknown agent rejection for both simple and multi-agent command paths.

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically `src/teambot/repl/` (parser, router, executor, agent_state)

**Primary Language/Framework**:

- Python

**Testing Preference**:

- Follow current pattern (pytest)

**Key Constraints**:
- The set of valid agents should come from a single source of truth (e.g., the existing `VALID_AGENTS` set in `router.py` or from configuration) — do not duplicate the list.
- Validation should be added at the earliest sensible point (TaskExecutor entry or parser) to fail fast.
- Must not break the existing simple router validation path which already works correctly.
- Minimal changes — this is a targeted bug fix, not a refactor.

---

## Additional Context

- The bug was identified by tracing the code path from REPL input through to agent execution.
- The simple router path (`router.py` `_route_agent`) already validates via `is_valid_agent()` and `VALID_AGENTS` — the fix should reuse this mechanism rather than creating a parallel one.
- The `AgentRunner` fallback to "builder" persona for unknown agents (`agent_runner.py`) is a secondary issue — with proper validation upstream, this fallback should never be reached for user-initiated `@agent` commands. However, consider whether the fallback itself should raise an error instead of silently degrading.
- Pipeline and multi-agent execution paths in TaskExecutor should also be checked.

---
