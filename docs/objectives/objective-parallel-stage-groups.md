## Objective

- Enable parallel execution of independent workflow stages during file-based orchestration to reduce overall execution time.

**Goal**:

- File-based orchestration currently executes all 14 workflow stages strictly sequentially, even when stages have no data dependencies on each other.
- Introduce the concept of **parallel stage groups** — a set of stages that execute concurrently before the workflow advances to the next sequential stage.
- The first parallel group should be the post-spec stages: `RESEARCH` and `TEST_STRATEGY` should run in parallel after `SPEC_REVIEW` completes, since both consume the spec output but do not depend on each other's artifacts. `SPEC_REVIEW` is intentionally excluded from this group because it is a review stage with a `ReviewIterator` loop (up to 4 rejection/revision cycles) — running it concurrently with stages that consume the spec would risk those stages operating against a spec that is subsequently revised.
- Create a **new `ParallelStageExecutor`** to handle concurrent stage execution. The existing `ParallelExecutor` operates on `AgentTask` objects (multiple agents within a single stage) and its interface (`execute_parallel(tasks: list[AgentTask])`) is not suited for orchestrating parallel *stages*, which involve dispatching to `_execute_work_stage()` / `_execute_review_stage()` with full stage lifecycle management. The new executor wraps stage-level dispatch callables and manages concurrent stage lifecycles independently from the existing agent-level parallelism.
- The sequential backbone of the workflow must remain intact — parallel groups are simply batches of stages that run concurrently at a defined point in the pipeline.
- Parallel groups should be configurable in `stages.yaml` so that new groups can be added without code changes.
- If any stage in a parallel group fails, the remaining stages in the group should be allowed to complete (no early cancellation), and the failure should be surfaced clearly before blocking progression.
- State persistence must support resuming mid-parallel-group — only incomplete stages within the group should re-run on resume.

**Problem Statement**:

- The current sequential execution model means each stage waits for the previous one to fully complete before starting, even when there are no data dependencies between them.
- For stages like `RESEARCH` and `TEST_STRATEGY`, this creates unnecessary wait time since they both only require the reviewed `SPEC` artifact as input.
- Running these two stages in parallel could significantly reduce pre-implementation time by eliminating unnecessary sequential waiting.
- As more stages are identified as parallelisable, the configurable group model allows incremental improvements without architectural rewrites.

**Success Criteria**:
- [ ] `RESEARCH` and `TEST_STRATEGY` execute concurrently after `SPEC_REVIEW` completes during file-based orchestration.
- [ ] Parallel stage groups are defined in `stages.yaml` configuration, not hardcoded.
- [ ] A new `ParallelStageExecutor` is created to handle concurrent stage execution, separate from the existing agent-level `ParallelExecutor`.
- [ ] Workflow state machine correctly tracks the status of individual stages within a parallel group.
- [ ] Resuming an interrupted run mid-parallel-group only re-executes incomplete stages, not the entire group. The resume state model must be updated to track a *set* of in-progress stages with individual completion status (architectural change to `orchestration_state.json` and the `resume()` classmethod).
- [ ] Backward compatibility: old `orchestration_state.json` files (without parallel group tracking) must still load correctly via `resume()`.
- [ ] The Rich console visualization clearly shows parallel stages running concurrently (e.g., multi-row display or concurrent status indicators).
- [ ] If a stage in a parallel group fails, other stages in the group still complete and the failure is clearly reported.
- [ ] All existing tests pass — no regressions to sequential workflow behaviour.
- [ ] New tests cover parallel group execution, partial failure, resume, and configuration parsing.

---

## Technical Context

**Target Codebase**:

- TeamBot — primarily `src/teambot/workflow/`, `src/teambot/orchestrator.py`, and `stages.yaml`

**Primary Language/Framework**:

- Python (asyncio for concurrent execution)

**Testing Preference**:

- Follow current pattern (pytest with pytest-mock)

**Key Constraints**:
- Must not break existing sequential workflow behaviour — parallel groups are an enhancement, not a replacement
- Must create a new `ParallelStageExecutor` for stage-level concurrency; the existing `ParallelExecutor` (agent-level) remains unchanged
- Stage-level persona validation must still be enforced for each stage in a parallel group
- Review-work pairings (e.g., `SPEC` → `SPEC_REVIEW`) must still function correctly — `SPEC_REVIEW` completes before the parallel group begins
- Artifact paths must remain unique per stage to avoid write conflicts during concurrent execution
- **Stage ordering clarification**: The codebase has two stage-ordering mechanisms: (1) `stages.py` → `STAGE_METADATA[stage].next_stages` (directed graph for state machine transition validation), and (2) `stages.yaml` → `stage_order` (linear list for execution loop progression). The new `parallel_groups` config in `stages.yaml` **augments** the linear `stage_order` — when the execution loop reaches a stage that is part of a parallel group, it executes the entire group concurrently before advancing. `next_stages` in `stages.py` should be updated to reflect the fan-out (e.g., `SPEC_REVIEW.next_stages = [RESEARCH, TEST_STRATEGY]`) so the state machine validates the parallel transitions correctly.

---

## Additional Context

- **Candidate parallel groups** (implement the first, document the others for future):
  - Post-Spec-Review: `[RESEARCH, TEST_STRATEGY]` — both depend only on the reviewed `SPEC` output. `SPEC_REVIEW` is intentionally excluded to avoid the complexity of review-iteration-during-parallel-execution (see Design Decisions below).
  - Post-Implementation: `[IMPLEMENTATION_REVIEW, TEST]` — both depend on implementation output (evaluate feasibility). Note: this group carries the same review-rejection hazard as SPEC_REVIEW — if `IMPLEMENTATION_REVIEW` rejects and triggers revisions, concurrent `TEST` results become invalid. Must be addressed before enabling this group.
- **Visualization consideration**: The current Rich console display assumes linear stage progression. The parallel group display should show concurrent stages side-by-side or stacked with clear "running in parallel" indicators.
- **Configuration format suggestion** for `stages.yaml`:
  ```yaml
  parallel_groups:
    - after: SPEC_REVIEW
      stages: [RESEARCH, TEST_STRATEGY]
  ```
  Note: `resume_to` is intentionally omitted — it is auto-derived from `stage_order` as the next stage after the last member of the parallel group. This avoids maintenance risk from divergence between `resume_to` and `stage_order`.
- **Incremental path**: This approach (Parallel Stage Groups) was chosen over a full DAG-based execution model for simplicity. If more complex dependency patterns are needed in future, the group concept can be evolved into a DAG without discarding this work.

---

## Design Decisions Required

The following decisions must be explicitly addressed during the PLAN stage:

1. **ParallelStageExecutor design**: A new `ParallelStageExecutor` will be created (not an extension of the existing `ParallelExecutor`). The existing `ParallelExecutor` operates on `AgentTask` objects within a single stage; stage-level parallelism requires wrapping `_execute_work_stage()` / `_execute_review_stage()` callables with full stage lifecycle management. The builder should define the interface, error aggregation strategy, and how it integrates with the execution loop.

2. **Resume state model change**: The current resume mechanism (`execution_loop.py`) persists `current_stage` as a single `WorkflowStage` value. Supporting mid-parallel-group resume requires changing this to track a *set* of in-progress stages with individual completion status. This is an architectural change to `orchestration_state.json` and the `resume()` classmethod. The builder must ensure backward compatibility — old state files without parallel group tracking must still load correctly.

3. **File placement**: `ParallelStageExecutor` should live in `src/teambot/orchestration/` alongside the existing `ParallelExecutor`.

4. **SPEC_REVIEW exclusion from parallel group**: `SPEC_REVIEW` is excluded from the first parallel group because it runs a `ReviewIterator` loop (up to 4 rejection/revision cycles). Running it concurrently with `RESEARCH` and `TEST_STRATEGY` would risk those stages operating against a spec that is subsequently revised. `SPEC_REVIEW` may be added to a parallel group in a future iteration once the infrastructure is proven and a strategy for invalidating/re-queuing concurrent stages on review rejection is designed.

---
