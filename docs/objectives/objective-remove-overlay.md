# Objective: Remove Overlay Feature

## Summary

Remove the `/overlay` feature, functionality, and tests from TeamBot. This feature is no longer needed or used.

---

## Problem Statement

The persistent status overlay feature was implemented to display real-time agent and task status in a fixed terminal position. However, this feature is no longer required and should be removed to:

- Reduce codebase complexity and maintenance burden
- Simplify the REPL interface
- Remove unused terminal rendering code

---

## Scope

### Files to Remove

| File | Description |
|------|-------------|
| `src/teambot/visualization/overlay.py` | Core overlay renderer module (~603 lines) |
| `tests/test_visualization/test_overlay.py` | Overlay unit tests |
| `tests/test_repl/test_commands_overlay.py` | REPL overlay command tests |
| `docs/feature-specs/persistent-status-overlay.md` | Feature specification |

### Files to Modify

| File | Changes Required |
|------|------------------|
| `src/teambot/visualization/__init__.py` | Remove overlay exports |
| `src/teambot/repl/commands.py` | Remove `/overlay` command handler, related code, and `/overlay` entry from `/help` output |
| `src/teambot/repl/loop.py` | Remove overlay integration in REPL loop |
| `src/teambot/config/loader.py` | Remove `overlay` config validation and defaults |
| `src/teambot/tasks/executor.py` | Remove overlay event callbacks |
| `docs/guides/architecture.md` | Remove overlay references |
| `docs/guides/development.md` | Remove overlay references |

### Test Files to Update

| File | Changes Required |
|------|------------------|
| `tests/test_config/test_loader.py` | Remove overlay config tests |

---

## Acceptance Criteria

- [ ] `src/teambot/visualization/overlay.py` is deleted
- [ ] `tests/test_visualization/test_overlay.py` is deleted
- [ ] `tests/test_repl/test_commands_overlay.py` is deleted
- [ ] `docs/feature-specs/persistent-status-overlay.md` is deleted
- [ ] `/overlay` command is removed from REPL command handler
- [ ] Overlay configuration validation removed from config loader
- [ ] Overlay defaults removed from config loader
- [ ] All overlay imports and references removed from codebase
- [ ] REPL loop no longer initializes or references overlay renderer
- [ ] TaskExecutor no longer references overlay callbacks
- [ ] All existing tests pass (`uv run pytest`)
- [ ] No regressions in existing REPL commands
- [ ] Linting passes (`uv run ruff check .`)
- [ ] Documentation updated to remove overlay references

---

## Technical Notes

### Overlay Feature Components

1. **OverlayRenderer** (`overlay.py`): ANSI-based terminal overlay with:
   - Fixed-position rendering (top-right, top-left, bottom-right, bottom-left)
   - Spinner animation for active tasks
   - Task count display (running, pending, completed, failed)
   - Scroll region management
   - Terminal resize handling

2. **REPL Integration** (`commands.py`):
   - `/overlay` - Show status
   - `/overlay on` - Enable overlay
   - `/overlay off` - Disable overlay
   - `/overlay position <pos>` - Set position

3. **Configuration** (`loader.py`):
   - `overlay.enabled` (boolean, default: true)
   - `overlay.position` (string, default: "top-right")

4. **Event Hooks** (integrated with TaskExecutor):
   - `on_task_started`
   - `on_task_completed`
   - `on_task_pending`
   - `set_pipeline_progress`

### Dependencies

The overlay uses the Rich library for console output but has no external dependencies beyond what TeamBot already uses.

---

## Out of Scope

- Removing any other visualization features (startup animation, console, etc.)
- Refactoring the REPL beyond overlay removal
- Changes to the task execution system beyond removing overlay hooks

---

## Related Artifacts

- Original feature spec: `docs/feature-specs/persistent-status-overlay.md`
- Post-review: `.agent-tracking/post-reviews/20260123-persistent-overlay-post-review.md`
- Spec review: `.agent-tracking/spec-reviews/20260123-persistent-status-overlay-spec-review.md`
- Plan review: `.agent-tracking/plan-reviews/20260123-persistent-overlay-plan-review.md`

---
