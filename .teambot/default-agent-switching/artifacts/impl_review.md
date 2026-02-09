# Implementation Review: Runtime Default Agent Switching

**Reviewer**: Builder-1 (self-review)
**Date**: 2026-02-09
**Status**: ⚠️ APPROVED WITH REVISIONS

---

## Overview

The implementation adds `/use-agent <id>` and `/reset-agent` slash commands to change the default agent at runtime, with UI visibility in the status panel, without persisting to `teambot.json`. The feature spans 6 source files and 6 test files, adding 30 new tests.

## Success Criteria Evaluation

| Criterion | Status | Notes |
|-----------|--------|-------|
| Default agent visible in status panel | ✅ Pass | `★` indicator + `default` label in StatusPanel |
| Default agent visible in `/status` | ✅ Pass | Both REPL and UI modes show "Default Agent:" line |
| `/use-agent <id>` switches default | ✅ Pass | Routes through SystemCommands dispatch |
| `/use-agent` (no args) shows info | ✅ Pass | Shows current default + available agents |
| Invalid agent ID error message | ✅ Pass | Clear error with available agents listed |
| `/status` reflects current default | ✅ Pass | Shows session override vs config distinction |
| Runtime-only (no config mutation) | ✅ Pass | `_config_default_agent` preserves original; no file writes |
| `/help` includes new commands | ✅ Pass | Both `/use-agent` and `/reset-agent` documented |
| `@agent` directives unaffected | ✅ Pass | `_route_agent()` path unchanged; test confirms |
| `/reset-agent` reverts to config | ✅ Pass | Reads `get_config_default_agent()` and restores |
| Test coverage | ✅ Pass | 30 new tests; 997 total pass; router.py at 96% |

## Architecture Review

### Strengths

1. **Clean separation of concerns**: Router owns mutation/validation, commands own UX/messaging, AgentStatusManager owns UI state propagation.
2. **Follows existing patterns**: `set_router()` matches `set_executor()`/`set_overlay()` pattern. `set_default_agent()` on AgentStatusManager matches `set_model()` pattern. Dispatch table extended cleanly.
3. **Immutable config default**: `_config_default_agent` is set once in `__init__` and never mutated — good defensive design for session-scoped changes.
4. **Dual-mode support**: Both REPL (`loop.py`) and split-pane UI (`app.py`) properly wired with consistent behavior.
5. **Validation reuse**: `handle_use_agent()` validates via `router.is_valid_agent()` before calling `set_default_agent()`, preventing redundant error paths.

### Issues Found

#### Issue 1: Agent alias not resolved before storage (Bug — Low Severity)

**File**: `src/teambot/repl/commands.py`, lines 314-326

**Problem**: `handle_use_agent()` validates the agent ID via `router.is_valid_agent()` (which internally resolves aliases), but passes the raw unresolved alias to `router.set_default_agent()`. If a user runs `/use-agent project_manager`, the stored default becomes `"project_manager"` instead of the canonical `"pm"`.

**Impact**: 
- Routing still works (because `_route_raw` → `_route_agent` resolves aliases again)
- But display is inconsistent: `/status` would show "Default Agent: project_manager" instead of "pm"
- Idempotency check fails: `/use-agent pm` after `/use-agent project_manager` would not detect they're the same agent

**Fix**:
```python
# In handle_use_agent(), before set_default_agent():
agent_id = router.resolve_agent_id(args[0])
```

**Severity**: Low — aliases are an edge case, but the fix is one line.

#### Issue 2: Redundant visual indicators in status panel (Cosmetic — Low Severity)

**File**: `src/teambot/ui/widgets/status_panel.py`, lines 126-145

**Problem**: When an idle agent is the default, two indicators are appended:
1. Line 127: `★` symbol appended to `line`  
2. Line 145: `default` label appended to the same `line`

This produces: `● pm ★ default` — which is intentional dual-indication (icon + text), but may be redundant.

**Assessment**: This is arguably by design (star for scanability, text label for clarity). The test `test_default_agent_shows_default_label` validates this exact format. **No action required** unless UX feedback says otherwise.

#### Issue 3: No alias resolution test coverage

**File**: `tests/test_repl/test_commands.py`

**Problem**: No test covers calling `/use-agent project_manager` (or other aliases). This is related to Issue 1.

**Fix**: Add a test case for alias input in `TestUseAgentCommand`.

### Minor Observations (Non-blocking)

1. **`handle_status()` router parameter is untyped**: Line 117 uses `router=None` without a type annotation. Should be `router: "AgentRouter | None" = None` for consistency with other typed parameters in the module.

2. **Coverage gap in app.py**: `app.py` is at 28% coverage overall, but this is pre-existing — the new lines (55, 59-61, 318-320, 425-435) are partially covered by the 2 `TestAppRouterWiring` tests. The post-dispatch update path (lines 318-320) is tested indirectly via the `test_agent_status_initialized_with_default` test but a more direct integration test would be ideal.

3. **`VALID_AGENTS` duplication**: Router uses `VALID_AGENTS` constant (line 20), while config loader validates against dynamically collected agent IDs from `teambot.json`. This is intentional per design (router is self-contained), but if agents become configurable in the future, this constant would need updating.

## Test Coverage Summary

| File | Coverage | New Lines Covered |
|------|----------|------------------|
| `src/teambot/repl/router.py` | 96% | `set_default_agent`, `get_config_default_agent`, `_config_default_agent` |
| `src/teambot/repl/commands.py` | 58% (pre-existing gap) | `handle_use_agent`, `handle_reset_agent`, dispatch entries, help text, status with router |
| `src/teambot/ui/agent_state.py` | 94% | `set_default_agent`, `get_default_agent` |
| `src/teambot/ui/widgets/status_panel.py` | 87% | Default indicator logic in `_format_status` |

**New tests**: 30 across 6 test files  
**Full suite**: 997 tests, 0 failures  
**Linting**: Clean (`ruff check .` passes)

## Recommendation

**APPROVED WITH REVISIONS** — The implementation is solid, well-tested, and follows existing patterns. Two minor revisions recommended before merge:

### Required Revisions

1. **Fix alias resolution in `handle_use_agent()`** — Resolve `agent_id` via `router.resolve_agent_id()` before passing to `set_default_agent()`. Add corresponding test.

### Optional Improvements

2. Add type annotation to `handle_status()` router parameter
3. Add test for alias-based `/use-agent` call

## Files Changed

### Source (6 files)
- `src/teambot/repl/router.py` — Core mutation methods
- `src/teambot/repl/commands.py` — Command handlers and dispatch
- `src/teambot/ui/agent_state.py` — Default agent tracking
- `src/teambot/ui/widgets/status_panel.py` — Visual indicator
- `src/teambot/repl/loop.py` — REPL wiring
- `src/teambot/ui/app.py` — UI wiring

### Tests (6 files)
- `tests/test_repl/test_router.py` — 6 new tests
- `tests/test_repl/test_commands.py` — 13 new tests
- `tests/test_ui/test_agent_state.py` — 4 new tests
- `tests/test_ui/test_status_panel.py` — 4 new tests
- `tests/test_repl/test_loop.py` — 1 new test
- `tests/test_ui/test_app.py` — 2 new tests
