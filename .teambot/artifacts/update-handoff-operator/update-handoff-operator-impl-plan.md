# Implementation Plan: Real-Time Handoff Operator UI Updates

**Spec:** [update-handoff-operator-ui.md](./update-handoff-operator-ui.md)  
**Author:** Builder-1  
**Date:** 2026-02-04  
**Status:** In Progress  
**Revision:** 2 (addressed reviewer feedback)

---

## Summary

Update the pipeline execution to emit per-task events so the overlay UI reflects which agent is currently active during handoff operations.

**Root Cause:** `_execute_pipeline()` calls `execute_all()` which doesn't emit `on_task_started`/`on_task_complete` callbacks, unlike single-agent execution.

---

## Tasks

### Phase 1: Executor Changes

- [ ] **Task 1.1:** Refactor `_execute_pipeline()` to iterate tasks with callbacks
  - File: `src/teambot/tasks/executor.py`
  - Replace `await self._manager.execute_all()` (line 368) with a loop that:
    - Gets tasks in topological order via `self._manager._graph.get_topological_order()`
    - Calls `on_task_started` before each task executes
    - Executes the task via `self._manager.execute_task(task_id)`
    - Calls `on_task_complete` after each task completes
  - Preserve existing dependency/skip logic from `TaskManager.execute_all()`

- [ ] **Task 1.2:** Refactor `_run_pipeline_with_callback()` for background pipelines
  - File: `src/teambot/tasks/executor.py`
  - Currently calls `execute_all()` without per-task events (line 428)
  - Apply same pattern as Task 1.1 to emit events for background pipelines

- [ ] **Task 1.3:** Emit intermediate output after each stage completes (US-3)
  - File: `src/teambot/tasks/executor.py`
  - After each `on_task_complete`, output that stage's result immediately
  - Add optional `on_stage_output` callback to `TaskExecutor.__init__`
  - Call it with `(agent_id, output)` after each stage

### Phase 2: Overlay Enhancements

- [ ] **Task 2.1:** Track pipeline stage in OverlayState
  - File: `src/teambot/visualization/overlay.py`
  - Add field: `pipeline_stage: tuple[int, int] | None = None` (current, total)
  - Add field: `pipeline_stage_agents: list[str] = []` (agents in current stage)
  - Update `_build_content()` to display "Stage X/Y" when pipeline active

- [ ] **Task 2.2:** Handle multi-agent stage transitions
  - File: `src/teambot/visualization/overlay.py`
  - When a new pipeline stage starts:
    - Clear all agents from the *previous stage* (not just one agent)
    - Add all agents from the *new stage*
  - This handles fan-out stages like `@pm, @ba analyze`
  - Add method: `on_pipeline_stage_change(stage_num: int, total: int, agents: list[str])`

- [ ] **Task 2.3:** Add pipeline progress methods
  - File: `src/teambot/visualization/overlay.py`
  - Add: `set_pipeline_progress(current: int, total: int, agents: list[str])`
  - Add: `clear_pipeline_progress()`
  - These update `pipeline_stage` and `pipeline_stage_agents`

- [ ] **Task 2.4:** Add handoff transition indicator (US-2)
  - File: `src/teambot/visualization/overlay.py`
  - When transitioning between stages, briefly show `→` between agent names
  - Example: `@pm → @builder` during handoff moment
  - Add field: `handoff_in_progress: bool = False`

### Phase 3: Wire Up Events

- [ ] **Task 3.1:** Add stage change callback to TaskExecutor
  - File: `src/teambot/tasks/executor.py`
  - Add optional `on_stage_change` callback to `__init__`
  - Signature: `Callable[[int, int, list[str]], None]` (stage, total, agents)
  - Call when transitioning between pipeline stages

- [ ] **Task 3.2:** Connect callbacks in REPL loop
  - File: `src/teambot/repl/loop.py` (lines 242, 381)
  - Pass overlay's `set_pipeline_progress` as `on_stage_change`
  - Pass output handler as `on_stage_output` for intermediate display

- [ ] **Task 3.3:** Connect callbacks in acceptance test executor
  - File: `src/teambot/orchestration/acceptance_test_executor.py` (line 324)
  - Pass appropriate callbacks or None for test context

### Phase 4: Testing

- [ ] **Task 4.1:** Unit test - sync pipeline emits events
  - File: `tests/test_tasks/test_executor.py`
  - Verify `on_task_started` called for each pipeline stage
  - Verify `on_task_complete` called after each stage
  - Verify `on_stage_change` called at stage boundaries

- [ ] **Task 4.2:** Unit test - background pipeline emits events
  - File: `tests/test_tasks/test_executor.py`
  - Verify `_run_pipeline_with_callback` emits `on_task_started` per-task
  - Test with `@a -> @b &` background syntax

- [ ] **Task 4.3:** Unit test - overlay state updates on transitions
  - File: `tests/test_visualization/test_overlay.py`
  - Verify `active_agents` clears previous stage agents
  - Verify `pipeline_stage` displays correctly
  - Verify multi-agent stages handled properly

- [ ] **Task 4.4:** Unit test - intermediate output emission
  - File: `tests/test_tasks/test_executor.py`
  - Verify `on_stage_output` called after each stage
  - Verify output content matches stage result

- [ ] **Task 4.5:** Run full test suite
  - Command: `uv run pytest`
  - Ensure no regressions

### Phase 5: Validation

- [ ] **Task 5.1:** Manual test with 2-stage pipeline
  - Command: `@pm analyze -> @builder implement`
  - Verify overlay shows `@pm` then `@builder`
  - Verify `@pm` output displays before `@builder` finishes

- [ ] **Task 5.2:** Manual test with 3-stage pipeline
  - Command: `@pm plan -> @builder build -> @reviewer check`
  - Verify overlay updates 3 times
  - Verify "Stage 1/3", "Stage 2/3", "Stage 3/3" shown

- [ ] **Task 5.3:** Manual test with multi-agent stage
  - Command: `@pm, @ba analyze -> @builder implement`
  - Verify both `@pm` and `@ba` shown as active in stage 1
  - Verify both cleared when stage 2 starts

- [ ] **Task 5.4:** Verify single-agent commands unchanged
  - Command: `@pm analyze the codebase`
  - Verify no regression in non-pipeline behavior

- [ ] **Task 5.5:** Test background pipeline
  - Command: `@pm -> @builder &`
  - Verify overlay updates even for background execution

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/teambot/tasks/executor.py` | Refactor `_execute_pipeline()` and `_run_pipeline_with_callback()`, add `on_stage_change` and `on_stage_output` callbacks |
| `src/teambot/visualization/overlay.py` | Add `pipeline_stage` state, handle multi-agent stage transitions, add handoff indicator |
| `src/teambot/repl/loop.py` | Connect stage callbacks at TaskExecutor instantiation (lines 242, 381) |
| `src/teambot/orchestration/acceptance_test_executor.py` | Update TaskExecutor instantiation (line 324) |
| `tests/test_tasks/test_executor.py` | Add sync/background pipeline event emission tests |
| `tests/test_visualization/test_overlay.py` | Add pipeline state transition tests |

*Note: `src/teambot/tasks/manager.py` does NOT need changes — `TaskGraph.get_topological_order()` already public.*

---

## Acceptance Criteria

### From US-1 (Real-Time Agent Status):
- [ ] Active agent indicator updates when each pipeline stage begins
- [ ] Previous agent shows as completed (not active) after handoff
- [ ] Transition occurs immediately when handoff happens
- [ ] Works for pipelines with 2+ stages

### From US-2 (Visual Handoff Transition):
- [ ] User can visually distinguish when one agent stops and another starts
- [ ] The `→` notation in overlay shows current handoff in progress

### From US-3 (Incremental Output Display):
- [ ] Output from completed stages displays before later stages finish
- [ ] Each output section is clearly attributed to its source agent

---

## Notes

- Non-pipeline commands (`@agent do something`) must remain unchanged
- Background pipelines (`@a -> @b &`) must also emit events
- Performance: UI updates are throttled by spinner interval (100ms)
- Multi-agent stages (fan-out) must be handled correctly
