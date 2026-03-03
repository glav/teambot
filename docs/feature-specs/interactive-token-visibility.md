# Interactive Token Visibility Enhancement

## Overview

**Status**: Implemented  
**Priority**: High  
**Parent Feature**: Operation Cost Visibility  
**Related Objective**: `docs/objectives/operation-cost-visibility.md`  
**Last Updated**: 2026-03-03 (post-review revision)

## Problem Statement

The operation-cost-visibility feature tracks tokens in the REPL but there's no way to view them during a session. Token usage is only shown on exit, which doesn't meet the spec requirement that session-level tracking "must be easily visible."

The objective file (line 43) states:
> **Per-call tracking required?** No — session-level is sufficient for MVP, **but must be easily visible**

Additionally, the objective lists as future enhancements (lines 85-88):
> - On-demand display via a `/tokens` or `/cost` command

This `/tokens` command was not implemented, leaving users unable to see token usage without exiting the session.

## Objective

Add `/tokens` command to display session token usage on-demand in interactive mode.

## Implementation Tasks

### Task 1: Add `handle_tokens` function to `commands.py`

**File**: `src/teambot/repl/commands.py`

**Requirements**:
- Create `handle_tokens(args, token_tracker)` function
- Accept optional `TokenTracker` instance (may be None if tracking disabled)
- Return `CommandResult` with formatted token summary
- When tracker is None: return "Token tracking is disabled"
- When tracker has no data: return "No token usage recorded yet"
- When tracker has data: use `render_session_summary()` from `teambot.tokens.display`
- Support `/tokens --detailed` flag to show per-agent breakdown

**Output Format**:

`/tokens` (basic) — single line showing session total:
```
Session Token Usage: 12,450 tokens (prompt: 9,200 | completion: 3,250)
```

`/tokens --detailed` — Rich panel with total + per-agent breakdown:
```
╭──────────────────── 📊 Token Usage Summary ────────────────────╮
│ Total Tokens: 12,450 (prompt: 9,200 | completion: 3,250)       │
│                                                                │
│ By Agent:                                                      │
│   pm           │ ████████░░ │    4,500 (36.1%)                 │
│   builder-1    │ ██████░░░░ │    3,200 (25.7%)                 │
│   ba           │ ████░░░░░░ │    2,100 (16.9%)                 │
│   reviewer     │ ████░░░░░░ │    1,650 (13.3%)                 │
│   writer       │ ██░░░░░░░░ │    1,000 (8.0%)                  │
╰────────────────────────────────────────────────────────────────╯
```

When no data available:
```
Session Token Usage: n/a
```

**Data presence check** (TokenTracker has no `has_data()` method):
```python
total = tracker.get_total()
if total.total_tokens is None or total.total_tokens == 0:
    return CommandResult(output="No token usage recorded yet")
```

**Output type handling**:
- `render_session_summary(total)` returns `str` — use directly in `CommandResult.output`
- `render_token_summary(total, by_agent)` returns `rich.panel.Panel` — convert to string for CommandResult, or print separately before returning

**Argument parsing** (follow simple pattern like `/task` command):
```python
detailed = "--detailed" in args or "-d" in args
```

**Pattern to follow**: See `handle_status()` or `handle_tasks()` for similar structure

---

### Task 2: Register `/tokens` and `/cost` commands in `SystemCommands.dispatch()`

**File**: `src/teambot/repl/commands.py`

**Requirements**:
- Add `"tokens": self.tokens` to the `handlers` dict in the `dispatch()` method
- Add `"cost": self.tokens` as an alias (objective mentions both `/tokens` and `/cost`)
- Add `self.tokens(args)` method that calls `handle_tokens(args, self._token_tracker)`

---

### Task 3: Pass `TokenTracker` to `SystemCommands`

**File**: `src/teambot/repl/loop.py`

**Requirements**:
- Modify `SystemCommands` initialization to accept `token_tracker` parameter
- Pass `self._token_tracker` when creating `SystemCommands`
- Update `SystemCommands.__init__` to store the tracker as `self._token_tracker`

---

### Task 4: Update `/help` output

**File**: `src/teambot/repl/commands.py`

**Requirements**:
- Add `/tokens` to the help text in `handle_help()` function
- Description: "Show session token usage (`/cost` is an alias)"

---

### Task 5: Add unit tests

**File**: `tests/test_repl/test_commands.py` (new tests)

**Requirements**:
- Test `/tokens` with no tracker (disabled)
- Test `/tokens` with empty tracker (no usage yet)
- Test `/tokens` with recorded usage (shows summary)
- Test `/tokens --detailed` shows per-agent breakdown

---

### Task 6: Update acceptance tests

**File**: `tests/test_token_tracking_acceptance.py`

**Requirements**:
- Add acceptance test for `/tokens` command in interactive mode
- Verify it shows accumulated session tokens

---

## Acceptance Criteria

- [ ] `/tokens` command exists and is listed in `/help`
- [ ] `/cost` alias works identically to `/tokens`
- [ ] Running `/tokens` with no interactions shows "No token usage recorded"
- [ ] Running `/tokens` after `@pm` commands shows accumulated tokens
- [ ] `/tokens --detailed` shows per-agent breakdown
- [ ] `/tokens --detailed` with only one agent shows correct output (edge case)
- [ ] Token tracking disabled shows "Token tracking is disabled"
- [ ] All existing tests pass
- [ ] New tests cover the `/tokens` command

---

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/teambot/repl/commands.py` | Modify | Add `handle_tokens` function and register command |
| `src/teambot/repl/loop.py` | Modify | Pass TokenTracker to SystemCommands |
| `tests/test_repl/test_commands.py` | Modify | Add unit tests for /tokens |
| `tests/test_token_tracking_acceptance.py` | Modify | Add acceptance test |

---

## Dependencies

- `src/teambot/tokens/tracker.py` - TokenTracker class (already implemented)
  - Key method: `get_total()` returns `TokenUsage` with `total_tokens`, `input_tokens`, `output_tokens`
  - Key method: `get_by_agent()` returns `dict[str, TokenUsage]`
- `src/teambot/tokens/display.py` - Display functions (already implemented)
  - `render_session_summary(total: TokenUsage) -> str` — returns plain string
  - `render_token_summary(total, by_agent, by_stage) -> Panel` — returns Rich Panel

---

## Out of Scope

- Per-command token display (future enhancement)
- Status bar token indicator (future enhancement)
- Split-pane UI token integration (separate task)

---

## References

- Original objective: `docs/objectives/operation-cost-visibility.md`
- Token tracking implementation: `src/teambot/tokens/`
- REPL commands pattern: `src/teambot/repl/commands.py`

---

## Review History

| Date | Reviewer | Decision | Notes |
|------|----------|----------|-------|
| 2026-03-03 | @reviewer | NEEDS_REVISION | Added data presence check, output type handling, `/cost` alias, edge cases |
