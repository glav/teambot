# Test Strategy: Parallel Stage Groups

**Date**: 2026-02-10  
**Approach**: TDD (Test-Driven Development)  
**Full Document**: `.agent-tracking/test-strategies/20260210-parallel-stage-groups-test-strategy.md`

---

## Summary

**Decision Matrix Score**: TDD 9 vs Code-First 0 → **TDD**

### Key Factors
- ✅ Requirements are well-defined (10 success criteria)
- ✅ High complexity (asyncio concurrency, state management)
- ✅ Critical risk (core workflow orchestration)
- ❌ Not exploratory, not simple, not time-pressured

---

## Component Test Approaches

| Component | Approach | Coverage Target | Priority |
|-----------|----------|-----------------|----------|
| `ParallelStageExecutor` | TDD | 95% | CRITICAL |
| Config parsing (`parallel_groups`) | TDD | 90% | HIGH |
| `ExecutionLoop` integration | TDD | 85% | CRITICAL |
| State persistence & resume | TDD | 90% | CRITICAL |
| `stages.py` transitions | TDD | 100% | HIGH |
| Progress events | Code-First | 80% | MEDIUM |
| `stages.yaml` config | Code-First | N/A | LOW |

---

## Critical Test Scenarios

1. **Parallel Group Execution** — RESEARCH + TEST_STRATEGY run concurrently
2. **Partial Failure Handling** — One stage fails, others complete
3. **Resume Mid-Parallel-Group** — Only incomplete stages re-run
4. **Backward Compatibility** — Old state files without `parallel_group_status`
5. **Sequential Regression** — Non-parallel stages unchanged

---

## Test Infrastructure

- **Framework**: pytest with pytest-asyncio
- **Coverage**: pytest-cov, 85% target
- **Runner**: `uv run pytest`
- **New Test File**: `tests/test_orchestration/test_parallel_stage_executor.py`

---

## Next Steps

1. ✅ Test strategy approved
2. ➡️ Proceed to **Step 5** (`sdd.5-task-planner-for-feature.prompt.md`)
