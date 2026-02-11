<!-- markdownlint-disable-file -->
# Release Changes: Parallel Stage Groups

**Related Plan**: 20260210-parallel-stage-groups-plan.instructions.md
**Implementation Date**: 2026-02-10

## Summary

Implementing parallel stage group execution for file-based orchestration, enabling `RESEARCH` and `TEST_STRATEGY` to run concurrently after `SPEC_REVIEW` completes.

## Changes

### Added

* `tests/test_orchestration/test_stage_config.py` - Added `TestParallelGroupsConfig` class with 4 tests for parallel group parsing
* `src/teambot/orchestration/parallel_stage_executor.py` - New `ParallelStageExecutor` class and `StageResult` dataclass for concurrent stage execution
* `tests/test_orchestration/test_parallel_stage_executor.py` - 8 tests for ParallelStageExecutor (TDD)
* `tests/test_workflow/test_stages.py` - Added `TestParallelStageTransitions` class with 3 tests for parallel fan-out transitions
* `tests/test_workflow/test_state_machine.py` - Updated `test_full_workflow_path` to use RESEARCH path through parallel group; added `test_full_workflow_path_via_test_strategy` for alternate path
* `tests/test_orchestration/test_execution_loop.py` - Added `TestParallelGroupExecution` class with 7 tests for parallel group integration; added `TestStatePersistenceWithParallelGroups` class with 4 tests for state persistence

### Modified

* `src/teambot/orchestration/stage_config.py` - Added `ParallelGroupConfig` dataclass and `parallel_groups` field to `StagesConfiguration`, added parsing logic in `_parse_configuration()`
* `stages.yaml` - Added `parallel_groups` section with `post_spec_review` group defining RESEARCH and TEST_STRATEGY as parallel stages
* `src/teambot/workflow/stages.py` - Updated `SPEC_REVIEW.next_stages` to fan out to both RESEARCH and TEST_STRATEGY; updated RESEARCH to converge at PLAN
* `src/teambot/orchestration/execution_loop.py` - Added `parallel_group_status` field, `_get_parallel_group_for_stage()`, `_execute_parallel_group()`, `_filter_incomplete_stages()` methods, and parallel group detection in `run()` loop; updated `_save_state()` and `resume()` for parallel group state persistence
* `src/teambot/orchestration/progress.py` - Added handling for parallel group progress events
* `tests/test_orchestration/test_progress.py` - Added `TestParallelGroupProgressEvents` class with 5 tests for parallel progress events

### Removed

* None

## Release Summary

**Total Files Affected**: 10

### Files Created (2)

* `src/teambot/orchestration/parallel_stage_executor.py` - Concurrent stage execution for parallel groups
* `tests/test_orchestration/test_parallel_stage_executor.py` - Tests for ParallelStageExecutor

### Files Modified (8)

* `src/teambot/orchestration/stage_config.py` - Added ParallelGroupConfig and parsing
* `src/teambot/orchestration/execution_loop.py` - Parallel group integration in main loop
* `src/teambot/orchestration/progress.py` - Parallel group progress events
* `src/teambot/workflow/stages.py` - Updated state machine for parallel transitions
* `stages.yaml` - Added parallel_groups configuration
* `tests/test_orchestration/test_stage_config.py` - Parallel config tests
* `tests/test_orchestration/test_execution_loop.py` - Parallel execution tests
* `tests/test_workflow/test_stages.py` - Parallel transition tests
* `tests/test_workflow/test_state_machine.py` - Updated for parallel paths
* `tests/test_orchestration/test_progress.py` - Parallel progress event tests

### Files Removed (0)

* None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: `stages.yaml` extended with `parallel_groups` section

### Deployment Notes

No deployment changes required. Parallel stage groups are backward compatible - old state files without `parallel_group_status` load correctly with empty status.