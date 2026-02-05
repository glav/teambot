# Feature Specification: Real-Time Handoff Operator UI Updates

## Overview

**Feature:** Update visual indication during pipeline handoff operations  
**Status:** Draft  
**Author:** Business Analyst  
**Date:** 2026-02-04

---

## Business Problem

When users execute pipeline commands using the `->` (handoff) operator, the current UI does not accurately reflect which agent is actively processing. The visual indicator remains on the **starting agent** until all pipeline stages complete and output is displayed.

This creates confusion about:
- Which agent is currently working
- Whether the handoff has occurred
- The progress through multi-stage pipelines

### Example Scenario

**Command:** `@pm analyze requirements -> @builder implement -> @reviewer check`

**Current Behavior:**
- Visual indicator shows `@pm` as active throughout entire pipeline
- User sees no feedback when `@builder` or `@reviewer` start working
- All output appears at once when pipeline completes

**Impact:**
- Users cannot gauge pipeline progress
- Difficult to identify which stage is slow or stuck
- Reduced confidence in the handoff mechanism

---

## Desired Behavior

The UI should update **in real-time** to reflect which agent is currently executing:

1. When `@pm` starts processing → Show `@pm` as active
2. When `@pm` completes and hands off → Show `@builder` as active
3. When `@builder` completes and hands off → Show `@reviewer` as active
4. When `@reviewer` completes → Show completion state

---

## User Stories

### US-1: Real-Time Agent Status During Handoff

**As a** user executing a pipeline command  
**I want** the UI to show which agent is currently active  
**So that** I can understand the progress through my pipeline

**Acceptance Criteria:**
- [ ] Active agent indicator updates when each pipeline stage begins
- [ ] Previous agent shows as completed (not active) after handoff
- [ ] Transition occurs immediately when handoff happens
- [ ] Works for pipelines with 2+ stages

### US-2: Visual Handoff Transition

**As a** user watching a pipeline execute  
**I want** to see a clear visual transition between agents  
**So that** I know when a handoff has occurred

**Acceptance Criteria:**
- [ ] User can visually distinguish when one agent stops and another starts
- [ ] The `⏳` waiting indicator accurately reflects waiting states
- [ ] The `→` notation in overlay shows current handoff in progress

### US-3: Incremental Output Display

**As a** user running a multi-stage pipeline  
**I want** to see output from each stage as it completes  
**So that** I don't have to wait for the entire pipeline to finish

**Acceptance Criteria:**
- [ ] Output from completed stages displays before later stages finish
- [ ] Each output section is clearly attributed to its source agent
- [ ] User can review early outputs while later stages process

---

## Functional Requirements

### FR-1: Active Agent Tracking
The system SHALL update the active agent indicator when each pipeline stage begins execution.

### FR-2: Stage Transition Events
The system SHALL emit progress events when:
- A pipeline stage begins
- A pipeline stage completes
- A handoff occurs between stages

### FR-3: Overlay Updates
The overlay display SHALL reflect the currently executing agent within 500ms of a stage transition.

### FR-4: Completed Stage Indication
The system SHALL visually indicate which pipeline stages have completed while others continue.

---

## Non-Functional Requirements

### NFR-1: Performance
UI updates must not introduce perceptible lag in pipeline execution.

### NFR-2: Backwards Compatibility
Single-agent commands (without `->`) must continue to work unchanged.

### NFR-3: Consistency
Visual behavior should be consistent across all terminal types and sizes.

---

## Assumptions

1. The underlying pipeline execution already processes stages sequentially
2. Progress events are already emitted at stage boundaries (needs verification)
3. The overlay renderer can receive and process mid-pipeline updates

---

## Dependencies

- `src/teambot/visualization/overlay.py` - Overlay rendering
- `src/teambot/visualization/console.py` - Agent status display
- `src/teambot/tasks/executor.py` - Pipeline execution and events
- `src/teambot/cli.py` - Progress event handling

---

## Out of Scope

- Parallel pipeline execution (future feature)
- Cancellation of in-progress pipelines
- Retry logic for failed stages

---

## Open Questions

1. Should intermediate output be streamed or shown only after each stage completes?
2. What visual treatment for the "handoff in progress" moment?
3. Should completed stages remain visible in the overlay or fade out?

---

## Implementation Plan

**Author:** Builder-1  
**Date:** 2026-02-04

### Technical Approach

The existing codebase already has callback hooks (`on_task_started`, `on_task_complete`) wired into `TaskExecutor` and event handlers in `OverlayRenderer`. The issue is that **pipeline execution** (`_execute_pipeline`) calls `execute_all()` on the TaskManager, which processes tasks sequentially but does **not** emit per-task events back to the UI.

**Root Cause:** In `_execute_pipeline()` (line 367), `await self._manager.execute_all()` is called without callback hooks, unlike `_execute_simple()` which properly calls `on_task_started`/`on_task_complete`.

### Implementation Tasks

#### Task 1: Emit Task Started Events in Pipeline Execution

**File:** `src/teambot/tasks/executor.py`

**Change:** Modify `_execute_pipeline()` to emit `on_task_started` for each task as it begins execution.

**Approach:** Instead of calling `execute_all()` directly, iterate over tasks in topological order and call `execute_task()` with proper callbacks (similar to how `_run_task_with_callback` works).

```python
# Replace: await self._manager.execute_all()
# With: Loop that calls on_task_started before each task executes
```

#### Task 2: Emit Task Completed Events Per Stage

**File:** `src/teambot/tasks/executor.py`

**Change:** Call `on_task_complete` after each pipeline stage completes (before the next stage starts).

**Benefit:** Output from early stages can display before later stages finish (US-3).

#### Task 3: Update OverlayRenderer for Stage Transitions

**File:** `src/teambot/visualization/overlay.py`

**Change:** Ensure `on_task_started` removes the previous agent from `active_agents` if the new task is part of a pipeline stage transition.

**Note:** `OverlayRenderer.on_task_started()` already adds agents to `active_agents`, but doesn't handle the "this replaces the previous active agent" case for pipelines.

#### Task 4: Show Pipeline Progress in Overlay

**File:** `src/teambot/visualization/overlay.py`

**Change:** Add pipeline progress tracking (e.g., "Stage 2/3") in `OverlayState` and display it in `_build_content()`.

**New state field:**
```python
pipeline_stage: tuple[int, int] | None = None  # (current, total)
```

### File Changes Summary

| File | Change |
|------|--------|
| `src/teambot/tasks/executor.py` | Refactor `_execute_pipeline()` to emit per-task events |
| `src/teambot/visualization/overlay.py` | Add pipeline stage tracking, update `on_task_started` for transitions |

### Test Strategy

1. **Unit Tests:**
   - Verify `on_task_started` called for each pipeline stage
   - Verify `on_task_complete` called after each stage
   - Verify overlay state updates on stage transitions

2. **Integration Test:**
   - Execute a 3-stage pipeline and verify overlay updates 3 times
   - Verify active agent changes at each stage boundary

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Performance impact from frequent UI updates | Updates are already throttled by spinner interval (100ms) |
| Breaking non-pipeline commands | Only modify pipeline execution path; single-agent path unchanged |
| Race conditions in async callbacks | Callbacks are invoked synchronously within task execution flow |

### Estimate

- **Task 1-2:** ~30 lines of code in executor.py
- **Task 3-4:** ~20 lines of code in overlay.py
- **Tests:** ~50 lines across test files

---

## Next Steps

1. ~~**Builder Agent:** Create implementation plan with technical approach~~ ✓
2. **Builder Agent:** Implement changes to event emission and overlay rendering
3. **Reviewer Agent:** Code review and testing verification

---

*This specification defines the requirements. Implementation plan added by Builder-1 agent.*
