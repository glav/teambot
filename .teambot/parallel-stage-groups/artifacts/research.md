# Research: Parallel Stage Groups

**Date**: 2026-02-10  
**Feature**: Parallel Stage Group Execution  
**Full Research Document**: `.agent-tracking/research/20260210-parallel-stage-groups-research.md`

---

## Summary

Deep research completed for implementing parallel stage groups in TeamBot's file-based orchestration.

### Key Findings

1. **Dual Stage-Ordering Systems**: The codebase uses `stages.py:STAGE_METADATA[stage].next_stages` (state machine validation) and `stages.yaml:stage_order` (execution loop). Both need updates.

2. **New Executor Required**: Existing `ParallelExecutor` handles agent-level parallelism (`AgentTask` objects). A new `ParallelStageExecutor` is needed for stage-level parallelism.

3. **State Model Enhancement**: Current `orchestration_state.json` tracks single `current_stage`. Needs `parallel_group_status` field for per-stage completion tracking within groups.

### Recommended Architecture

- **Configuration**: Add `parallel_groups` section to `stages.yaml`
- **Executor**: New `ParallelStageExecutor` class using `asyncio.gather()`
- **Integration**: Modify `ExecutionLoop.run()` to detect and execute parallel groups
- **State**: Add `parallel_group_status` tracking with backward compatibility

### Implementation Priority

1. Create `ParallelStageExecutor` class
2. Update `stages.yaml` schema with `parallel_groups`
3. Modify `stage_config.py` to parse parallel groups
4. Integrate into `ExecutionLoop` main loop
5. Update `stages.py` transition graph
6. Add state persistence for parallel groups
7. Implement resume mid-group support
8. Add tests

### Entry Points Traced

| Entry Point | Coverage |
|-------------|----------|
| `teambot run objective.md` | ✅ Covered |
| `teambot run --resume` | ✅ Covered |

---

## Next Steps

1. Run **Step 4** (`sdd.4-determine-test-strategy.prompt.md`) to create formal test strategy
2. After test strategy approval, proceed to **Step 5** (`sdd.5-task-planner-for-feature.prompt.md`)
