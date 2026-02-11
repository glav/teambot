# Problem Statement: Parallel Stage Groups

## Business Problem

### Current State

TeamBot's file-based orchestration executes all 14 workflow stages **strictly sequentially**, completing each stage fully before advancing to the next. This linear execution model was appropriate for the initial implementation but now presents an efficiency bottleneck.

**Current workflow execution:**
```
SETUP → BUSINESS_PROBLEM → SPEC → SPEC_REVIEW → RESEARCH → TEST_STRATEGY → PLAN → ...
        ↑                                         ↑            ↑
        Each stage waits for previous             These have no data
        stage to complete                         dependency on each other
```

### The Efficiency Gap

After `SPEC_REVIEW` completes:
- **RESEARCH** consumes the approved spec to analyze technical approaches
- **TEST_STRATEGY** consumes the approved spec to define testing patterns

Both stages operate **independently** on the same input (the spec) and produce **separate artifacts** (`research.md` and `test_strategy.md`). Neither depends on the other's output.

**Yet today they execute sequentially**, meaning:
- `TEST_STRATEGY` waits unnecessarily for `RESEARCH` to complete
- Total elapsed time = `RESEARCH` time + `TEST_STRATEGY` time
- Potential parallelism is wasted

### Business Impact

| Metric | Current State | With Parallel Groups |
|--------|---------------|---------------------|
| **Time for RESEARCH + TEST_STRATEGY** | Sum of both (~10-15 min) | Max of both (~5-8 min) |
| **Developer wait time** | Longer cycles | Reduced 30-40% for parallel stages |
| **Resource utilization** | Sequential (50% idle) | Concurrent (better utilization) |

---

## Goals

### Primary Goal

Enable **concurrent execution of independent workflow stages** to reduce overall orchestration time without compromising workflow integrity or sequential dependencies.

### Specific Goals

1. **Parallel Group Execution**: Execute `RESEARCH` and `TEST_STRATEGY` concurrently after `SPEC_REVIEW` completes
2. **Configuration-Driven**: Define parallel groups in `stages.yaml` so new groups can be added without code changes
3. **New Executor**: Create `ParallelStageExecutor` for stage-level concurrency (separate from existing agent-level `ParallelExecutor`)
4. **Robust State Management**: Support resuming mid-parallel-group with per-stage completion tracking
5. **Graceful Failure Handling**: Allow parallel stages to complete even if a sibling fails
6. **Clear Visualization**: Show parallel execution status in Rich console output

---

## Scope

### In Scope

| Item | Description |
|------|-------------|
| **ParallelStageExecutor** | New executor for concurrent stage execution with lifecycle management |
| **Configuration schema** | New `parallel_groups` section in `stages.yaml` |
| **State persistence update** | Track in-progress parallel stages with individual completion status |
| **Resume logic enhancement** | Re-execute only incomplete stages within a parallel group |
| **State machine updates** | Update `next_stages` in `stages.py` for fan-out transitions (e.g., `SPEC_REVIEW → [RESEARCH, TEST_STRATEGY]`) |
| **Visualization enhancement** | Multi-row or concurrent status indicators in Rich console |
| **Backward compatibility** | Old `orchestration_state.json` files must load correctly |
| **First parallel group** | `RESEARCH` and `TEST_STRATEGY` after `SPEC_REVIEW` |

### Out of Scope

| Item | Reason |
|------|--------|
| Refactoring existing `ParallelExecutor` | Agent-level parallelism is a different concern; keep separated |
| Review stage parallelism | `SPEC_REVIEW`, `PLAN_REVIEW`, etc. have `ReviewIterator` loops that must complete before consumers run |
| Dynamic dependency analysis | Parallel groups are statically configured, not inferred at runtime |
| Cross-parallel-group dependencies | Stages within a group are assumed independent; no DAG resolution |

---

## Success Criteria

| # | Criterion | Measurement |
|---|-----------|-------------|
| 1 | `RESEARCH` and `TEST_STRATEGY` execute concurrently | Execution logs show overlapping timestamps |
| 2 | Parallel groups defined in `stages.yaml` | Configuration parse succeeds; groups are not hardcoded |
| 3 | New `ParallelStageExecutor` created | Separate class from `ParallelExecutor`; handles stage dispatch |
| 4 | State machine tracks parallel stage status | `orchestration_state.json` contains per-stage completion flags |
| 5 | Resume re-executes only incomplete stages | Interrupted run resumes missing stages, skips completed |
| 6 | Backward compatibility maintained | Old state files load without error |
| 7 | Rich console shows parallel execution | Visual distinction for concurrent stages |
| 8 | Sibling stage failure doesn't cancel others | Failing stage logs error; siblings complete normally |
| 9 | All existing tests pass | `pytest` green with no regressions |
| 10 | New test coverage | Tests for parallel execution, partial failure, resume, config parsing |

---

## Assumptions

1. **Independence Guarantee**: Stages within a parallel group have no data dependencies on each other
2. **Artifact Isolation**: Each stage writes to unique artifact paths (enforced by existing `{stage}/artifacts/{file}` pattern)
3. **Persona Validation**: Each stage in a parallel group is validated independently
4. **Review Exclusion**: Review stages with `ReviewIterator` loops are never included in parallel groups
5. **Sequential Backbone**: The overall `stage_order` remains authoritative; parallel groups are "expanded" at specific points

---

## Dependencies

### Internal Dependencies

| Dependency | Impact |
|------------|--------|
| `stages.yaml` schema | New `parallel_groups` key must be parsed |
| `STAGE_METADATA.next_stages` | Must reflect fan-out for parallel transitions |
| `orchestration_state.json` | Schema evolves to track parallel stage set |
| `ExecutionLoop` | Must detect and dispatch parallel groups |
| `WorkflowStateMachine` | Must validate parallel transitions |

### External Dependencies

| Dependency | Impact |
|------------|--------|
| `asyncio` | Used for concurrent stage execution via `asyncio.gather()` |
| GitHub Copilot CLI | Each parallel stage spawns its own Copilot session |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Artifact write conflicts** | Low | High | Unique paths per stage already enforced |
| **State corruption mid-parallel** | Medium | High | Atomic per-stage status updates; resume handles partial state |
| **Increased complexity** | Medium | Medium | Clear separation between stage-level and agent-level parallelism |
| **Regression in sequential flow** | Low | High | Comprehensive existing test suite; new tests for parallel paths |
| **Configuration errors** | Medium | Medium | Validate parallel group definitions at load time |

---

## Constraints

1. **No Breaking Changes**: Existing sequential workflow must continue to function identically
2. **Separate Executors**: `ParallelStageExecutor` (stages) and `ParallelExecutor` (agents) remain distinct
3. **Review Stage Exclusion**: Stages with `is_review_stage: true` cannot be in parallel groups
4. **Acceptance Test Integrity**: Acceptance test stage execution is unaffected by this change
5. **Configuration Location**: Parallel groups are defined in `stages.yaml`, not code

---

## Stakeholders

| Role | Interest |
|------|----------|
| **Developers** | Faster orchestration cycles, reduced wait time |
| **Operators** | Clear status visibility, reliable resume behavior |
| **Maintainers** | Clean architecture, testable components, no regression risk |

---

## Appendix: Current vs. Proposed State Model

### Current State Model (`orchestration_state.json`)

```json
{
  "current_stage": "RESEARCH",
  "status": "in_progress",
  "stage_outputs": { "SPEC": "...", "SPEC_REVIEW": "..." }
}
```

**Limitation**: Single `current_stage` cannot represent multiple in-progress stages.

### Proposed State Model

```json
{
  "current_stage": "PARALLEL_GROUP:post_spec",
  "parallel_group_status": {
    "group_name": "post_spec",
    "stages": {
      "RESEARCH": { "status": "complete", "output": "..." },
      "TEST_STRATEGY": { "status": "in_progress", "output": null }
    }
  },
  "status": "in_progress",
  "stage_outputs": { "SPEC": "...", "SPEC_REVIEW": "..." }
}
```

**Enhancement**: Tracks individual stage completion within a parallel group, enabling targeted resume.
