<!-- markdownlint-disable-file -->
# Test Strategy: Parallel Stage Groups

**Strategy Date**: 2026-02-10  
**Feature Specification**: Objective document (parallel stage groups)  
**Research Reference**: `.agent-tracking/research/20260210-parallel-stage-groups-research.md`  
**Strategist**: Test Strategy Agent

---

## Testing Approach Decision Matrix

### Factor Scoring

| Factor | Question | Score | Justification |
|--------|----------|-------|---------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | TDD +3 | ✅ YES - 10 explicit success criteria in objective, clear behavioral expectations |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | TDD +3 | ✅ HIGH - Concurrent execution, state machine changes, resume logic |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | TDD +3 | ✅ CRITICAL - Core workflow orchestration, breakage affects all users |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | Code-First +0 | ❌ NO - Well-researched, clear implementation path |
| **Simplicity** | Is this straightforward CRUD or simple logic? | Code-First +0 | ❌ NO - Asyncio concurrency, state tracking, config parsing |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | Code-First +0 | ❌ NO - Quality over speed for core infrastructure |
| **Requirements Stability** | Are requirements likely to change during development? | Code-First +0 | ❌ NO - Requirements are locked in objective |

### Decision Calculation

```
TDD Score:        9 (3+3+3)
Code-First Score: 0

Decision Threshold: TDD ≥ 6, Code-First ≥ 5

Result: TDD (score 9 >> threshold 6)
```

---

## Recommended Testing Approach

**Primary Approach**: **TDD (Test-Driven Development)**

### Rationale

The parallel stage groups feature is a **critical infrastructure change** to TeamBot's core workflow orchestration. It modifies the execution loop that drives all file-based workflows, touches state persistence for resume functionality, and requires careful coordination between concurrent async operations. The high complexity and mission-critical nature make TDD essential.

The requirements are exceptionally well-defined with 10 explicit success criteria, clear behavioral expectations (e.g., "stages complete even if one fails"), and specific technical constraints (e.g., "backward compatibility with old state files"). This clarity makes TDD highly effective — tests can be written directly from requirements before implementation.

Additionally, the research document identified specific code paths and integration points, providing precise test targets. The existing test suite (`test_parallel_executor.py`, `test_execution_loop.py`) demonstrates mature testing patterns that can be extended for the new `ParallelStageExecutor`.

**Key Factors:**
* **Complexity**: HIGH — asyncio.gather, state machine fan-out, concurrent stage tracking
* **Risk**: CRITICAL — core orchestration, resume functionality, backward compatibility
* **Requirements Clarity**: CLEAR — 10 success criteria, detailed constraints
* **Time Pressure**: LOW — quality is priority for infrastructure

---

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: HIGH — asyncio concurrency patterns, semaphore-based throttling
* **Integration Depth**: HIGH — touches ExecutionLoop, StagesConfiguration, WorkflowStateMachine, state persistence
* **State Management**: HIGH — parallel group tracking, per-stage completion status, resume mid-group
* **Error Scenarios**: MEDIUM — partial failure handling, exception isolation between stages

### Risk Profile
* **Business Criticality**: CRITICAL — core workflow orchestration used by all file-based workflows
* **User Impact**: All users running `teambot run` with objectives
* **Data Sensitivity**: LOW — no PII, but workflow state is important
* **Failure Cost**: HIGH — broken orchestration = broken TeamBot

### Requirements Clarity
* **Specification Completeness**: COMPLETE — 10 success criteria, detailed constraints
* **Acceptance Criteria Quality**: PRECISE — measurable outcomes (e.g., "RESEARCH and TEST_STRATEGY execute concurrently")
* **Edge Cases Identified**: 5+ documented (resume mid-group, partial failure, backward compat)
* **Dependencies Status**: STABLE — asyncio, existing orchestration modules

---

## Test Strategy by Component

### 1. `ParallelStageExecutor` Class — **TDD**

**File**: `src/teambot/orchestration/parallel_stage_executor.py` (NEW)

**Approach**: TDD  
**Rationale**: Core new class with complex async behavior. Clear interface from research. High-risk, high-value component.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Execute empty stage list (returns empty dict)
  * Execute single stage successfully
  * Execute multiple stages concurrently
  * Partial failure: one stage fails, others complete
  * All stages fail — results collected
  * Cancellation propagation
  * Respects max_concurrent semaphore limit
* Edge Cases:
  * Review stage in parallel group (calls `_execute_review_stage`)
  * Work stage in parallel group (calls `_execute_work_stage`)
  * Progress callbacks fire for each stage

**Testing Sequence (TDD):**
1. Write test: `test_execute_parallel_empty_stages`
2. Write test: `test_execute_parallel_single_stage`
3. Write test: `test_execute_parallel_multiple_stages`
4. Write test: `test_execute_parallel_partial_failure`
5. Write test: `test_execute_parallel_respects_concurrency`
6. Write test: `test_execute_parallel_progress_callbacks`
7. Implement minimal `ParallelStageExecutor` to pass each test

---

### 2. `StagesConfiguration.parallel_groups` — **TDD**

**File**: `src/teambot/orchestration/stage_config.py` (MODIFY)

**Approach**: TDD  
**Rationale**: Configuration parsing with clear schema. Tests define expected structure.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Parse valid `parallel_groups` from YAML
  * Handle missing `parallel_groups` (default empty list)
  * Validate stage names in groups
  * Reject invalid stage names
* Edge Cases:
  * Empty groups list
  * Group with single stage (allowed but unusual)
  * Group references non-existent stage

**Testing Sequence (TDD):**
1. Write test: `test_parse_parallel_groups_valid`
2. Write test: `test_parse_parallel_groups_missing_defaults_empty`
3. Write test: `test_parse_parallel_groups_invalid_stage_raises`
4. Implement `ParallelGroupConfig` dataclass
5. Add parsing in `_parse_configuration()`

---

### 3. `ExecutionLoop` Integration — **TDD**

**File**: `src/teambot/orchestration/execution_loop.py` (MODIFY)

**Approach**: TDD  
**Rationale**: High-risk integration point. Tests ensure existing behavior preserved while adding parallel groups.

**Test Requirements:**
* Coverage Target: 85%
* Test Types: Unit + Integration
* Critical Scenarios:
  * Parallel group detected and executed
  * Sequential stages still work (no regression)
  * Parallel group completes before next stage
  * Partial failure in group — workflow continues to report
  * All stages in group fail — error surfaced
* Edge Cases:
  * Resume mid-parallel-group
  * Stage not in any parallel group
  * Parallel group at end of workflow (before COMPLETE)

**Testing Sequence (TDD):**
1. Write test: `test_get_parallel_group_for_stage_returns_group`
2. Write test: `test_get_parallel_group_for_stage_returns_none_for_sequential`
3. Write test: `test_execute_parallel_group_calls_executor`
4. Write test: `test_run_executes_parallel_group_when_detected`
5. Write test: `test_run_sequential_stages_unchanged` (regression)
6. Implement integration methods

---

### 4. State Persistence (`orchestration_state.json`) — **TDD**

**File**: `src/teambot/orchestration/execution_loop.py` (MODIFY `_save_state`, `resume`)

**Approach**: TDD  
**Rationale**: Critical for resume functionality. Backward compatibility required.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Save state includes `parallel_group_status`
  * Resume loads `parallel_group_status`
  * Old state file without `parallel_group_status` loads (backward compat)
  * Resume mid-parallel-group only re-runs incomplete stages
* Edge Cases:
  * State file with empty `parallel_group_status`
  * Corrupt `parallel_group_status` field

**Testing Sequence (TDD):**
1. Write test: `test_save_state_includes_parallel_group_status`
2. Write test: `test_resume_loads_parallel_group_status`
3. Write test: `test_resume_backward_compat_missing_parallel_status`
4. Write test: `test_resume_mid_parallel_group_skips_completed`
5. Implement state changes

---

### 5. `stages.py` Transition Updates — **TDD**

**File**: `src/teambot/workflow/stages.py` (MODIFY)

**Approach**: TDD  
**Rationale**: Simple change but critical for state machine validation.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `SPEC_REVIEW.next_stages` includes both `RESEARCH` and `TEST_STRATEGY`
  * `get_next_stages(SPEC_REVIEW)` returns both
  * State machine validates parallel transitions

**Testing Sequence (TDD):**
1. Write test: `test_spec_review_next_stages_includes_research_and_test_strategy`
2. Update `STAGE_METADATA[SPEC_REVIEW].next_stages`

---

### 6. `stages.yaml` Schema — **Code-First**

**File**: `stages.yaml` (MODIFY)

**Approach**: Code-First  
**Rationale**: Configuration file, not code. Validation happens via parsing tests.

**Test Requirements:**
* Coverage Target: N/A (config file)
* Test Types: Integration (via config parsing tests)
* Critical Scenarios:
  * File parses without error
  * `parallel_groups` section recognized

**Testing Sequence (Code-First):**
1. Add `parallel_groups` section to `stages.yaml`
2. Run config parsing tests to validate
3. Adjust if tests fail

---

### 7. Progress Events — **Code-First**

**File**: `src/teambot/orchestration/progress.py` (MODIFY)

**Approach**: Code-First  
**Rationale**: Simple callback handling. Low complexity, low risk.

**Test Requirements:**
* Coverage Target: 80%
* Test Types: Unit
* Critical Scenarios:
  * New event types handled (`parallel_group_start`, `parallel_stage_start`, etc.)
  * Unknown events don't crash

**Testing Sequence (Code-First):**
1. Implement new event handlers
2. Add tests for new event types
3. Verify integration with visualization

---

## Test Infrastructure

### Existing Test Framework

| Aspect | Value |
|--------|-------|
| **Framework** | pytest 7.x |
| **Async Support** | pytest-asyncio with `asyncio_mode = "auto"` |
| **Mocking** | unittest.mock (AsyncMock for async) |
| **Coverage** | pytest-cov, target 80% |
| **Runner** | `uv run pytest` |
| **Config** | `pyproject.toml` lines 42-52 |

### Testing Tools Required

* **Mocking**: `unittest.mock.AsyncMock` — for mocking SDK client and async methods
* **Assertions**: pytest built-in — `assert`, `pytest.raises`
* **Coverage**: pytest-cov — Target: 85%+
* **Fixtures**: Shared via `conftest.py` in `tests/test_orchestration/`
* **Markers**: `@pytest.mark.asyncio` for async tests

### Test Organization

* **Test Location**: `tests/test_orchestration/`
* **Naming Convention**: `test_*.py` files, `Test*` classes, `test_*` methods
* **New Test File**: `tests/test_orchestration/test_parallel_stage_executor.py`
* **Fixture Strategy**: Use existing fixtures from `conftest.py`, add new ones as needed
* **Setup/Teardown**: pytest fixtures with `tmp_path` for temp directories

---

## Coverage Requirements

### Overall Targets

| Metric | Target |
|--------|--------|
| **Unit Test Coverage** | 85% (minimum) |
| **Integration Coverage** | 70% |
| **Critical Path Coverage** | 100% |
| **Error Path Coverage** | 80% |

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Approach |
|-----------|--------|---------------|----------|----------|
| `ParallelStageExecutor` | 95% | 70% | CRITICAL | TDD |
| `StageConfig` parallel parsing | 90% | 80% | HIGH | TDD |
| `ExecutionLoop` integration | 85% | 90% | CRITICAL | TDD |
| State persistence | 90% | 80% | CRITICAL | TDD |
| `stages.py` transitions | 100% | N/A | HIGH | TDD |
| Progress events | 80% | 60% | MEDIUM | Code-First |

### Critical Test Scenarios

1. **Parallel Group Execution** (Priority: CRITICAL)
   * **Description**: RESEARCH and TEST_STRATEGY run concurrently after SPEC_REVIEW
   * **Test Type**: Integration
   * **Success Criteria**: Both stages complete, outputs stored, single transition to PLAN
   * **Test Approach**: TDD

2. **Partial Failure Handling** (Priority: CRITICAL)
   * **Description**: One stage fails, other stages complete
   * **Test Type**: Unit
   * **Success Criteria**: Failed stage error captured, successful stages have output, failure reported
   * **Test Approach**: TDD

3. **Resume Mid-Parallel-Group** (Priority: CRITICAL)
   * **Description**: Workflow interrupted during parallel group, only incomplete stages re-run
   * **Test Type**: Unit + Integration
   * **Success Criteria**: Completed stages skipped, incomplete re-executed
   * **Test Approach**: TDD

4. **Backward Compatibility** (Priority: HIGH)
   * **Description**: Old `orchestration_state.json` without `parallel_group_status` loads
   * **Test Type**: Unit
   * **Success Criteria**: Resume succeeds, defaults applied
   * **Test Approach**: TDD

5. **Sequential Stage Regression** (Priority: HIGH)
   * **Description**: Stages not in parallel groups still execute sequentially
   * **Test Type**: Integration
   * **Success Criteria**: No behavior change for non-parallel stages
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Empty parallel group**: Config with `stages: []` (should be no-op)
* **Single-stage group**: Only one stage in group (executes normally)
* **All stages fail**: Error reported, no false completion
* **Cancellation during parallel group**: All stages receive cancel signal
* **Review stage in parallel group**: `ReviewIterator` still works (though not expected in first group)

### Error Scenarios

* **SDK client exception during stage**: Exception captured, other stages continue
* **Timeout during parallel group**: Time manager expiration handled
* **Invalid stage in group config**: Parsing raises `ValueError`
* **State file corruption**: Graceful handling in `resume()`

---

## Test Data Strategy

### Test Data Requirements

* **Objective files**: Use existing `sample_objective_content` fixture
* **Feature specs**: Use existing `sample_feature_spec_content` fixture
* **State files**: Create JSON fixtures for resume tests
* **Config YAML**: Create minimal YAML with parallel groups for parsing tests

### Test Data Management

* **Storage**: Inline in tests or `conftest.py` fixtures
* **Generation**: pytest fixtures with `tmp_path`
* **Isolation**: Each test gets fresh temp directory
* **Cleanup**: Automatic via pytest temp path cleanup

---

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_orchestration/test_parallel_executor.py`  
**Pattern**: Async test with mock SDK client and progress callback

```python
@pytest.mark.asyncio
async def test_execute_parallel_partial_failure(
    self, executor: ParallelExecutor, mock_sdk_client: AsyncMock
) -> None:
    """Partial failure: one task fails, other succeeds."""
    mock_sdk_client.execute_streaming.side_effect = [
        "Success output",
        Exception("Task failed"),
    ]
    tasks = [
        AgentTask(agent_id="builder-1", prompt="Task 1"),
        AgentTask(agent_id="builder-2", prompt="Task 2"),
    ]

    results = await executor.execute_parallel(tasks)

    assert results["builder-1"].success is True
    assert results["builder-2"].success is False
    assert "Task failed" in results["builder-2"].error
```

**Key Conventions:**
* `@pytest.mark.asyncio` decorator for async tests
* `AsyncMock` for mocking async methods
* `.side_effect` for multiple return values or exceptions
* Clear assertion on both success and failure states

### Recommended Test Structure for ParallelStageExecutor

```python
"""Tests for ParallelStageExecutor (TDD)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from teambot.orchestration.parallel_stage_executor import (
    ParallelStageExecutor,
    StageResult,
)
from teambot.workflow.stages import WorkflowStage


class TestParallelStageExecutor:
    """Tests for ParallelStageExecutor class."""

    @pytest.fixture
    def mock_execution_loop(self) -> MagicMock:
        """Create mock ExecutionLoop with stage execution methods."""
        loop = MagicMock()
        loop._execute_work_stage = AsyncMock(return_value="Stage output")
        loop._execute_review_stage = AsyncMock(return_value=ReviewStatus.APPROVED)
        loop.stages_config.review_stages = set()
        loop.stage_outputs = {}
        return loop

    @pytest.fixture
    def executor(self) -> ParallelStageExecutor:
        """Create ParallelStageExecutor instance."""
        return ParallelStageExecutor(max_concurrent=2)

    @pytest.mark.asyncio
    async def test_execute_parallel_empty_stages(
        self, executor: ParallelStageExecutor, mock_execution_loop: MagicMock
    ) -> None:
        """Empty stage list returns empty dict."""
        result = await executor.execute_parallel([], mock_execution_loop)
        assert result == {}

    @pytest.mark.asyncio
    async def test_execute_parallel_multiple_stages(
        self, executor: ParallelStageExecutor, mock_execution_loop: MagicMock
    ) -> None:
        """Multiple stages execute concurrently."""
        stages = [WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY]
        
        results = await executor.execute_parallel(stages, mock_execution_loop)
        
        assert len(results) == 2
        assert results[WorkflowStage.RESEARCH].success is True
        assert results[WorkflowStage.TEST_STRATEGY].success is True

    @pytest.mark.asyncio
    async def test_execute_parallel_partial_failure(
        self, executor: ParallelStageExecutor, mock_execution_loop: MagicMock
    ) -> None:
        """One stage fails, other completes successfully."""
        mock_execution_loop._execute_work_stage.side_effect = [
            "Success output",
            Exception("Stage failed"),
        ]
        stages = [WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY]
        
        results = await executor.execute_parallel(stages, mock_execution_loop)
        
        assert results[WorkflowStage.RESEARCH].success is True
        assert results[WorkflowStage.TEST_STRATEGY].success is False
        assert "Stage failed" in results[WorkflowStage.TEST_STRATEGY].error
```

---

## Success Criteria

### Test Implementation Complete When:

- [ ] All critical scenarios have tests (5 identified)
- [ ] Coverage targets are met per component (85%+ overall)
- [ ] All edge cases are tested (5 identified)
- [ ] Error paths are validated (4 scenarios)
- [ ] Tests follow codebase conventions (pytest, async patterns)
- [ ] Tests are maintainable and clear (docstrings, assertions)
- [ ] CI/CD integration is working (existing pytest config)

### Test Quality Indicators:

* Tests are readable and self-documenting (clear docstrings)
* Tests are fast and reliable (no external dependencies, mocked SDK)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem (specific assertions)
* Mock/stub usage is appropriate and minimal (only SDK client)

---

## Implementation Guidance

### For TDD Components (ParallelStageExecutor, Config, ExecutionLoop, State):

1. **Start with simplest test case** (empty input)
2. **Write minimal code to pass** (stub implementation)
3. **Add next test case** (single item, then multiple)
4. **Refactor when all tests pass** (clean up, optimize)
5. **Focus on behavior, not implementation** (test outputs, not internals)

### For Code-First Components (Progress Events, stages.yaml):

1. **Implement core functionality** (add handlers, config)
2. **Add happy path test** (verify basic usage)
3. **Identify edge cases from implementation** (what could break?)
4. **Add edge case tests** (cover branches)
5. **Verify coverage meets target** (run with --cov)

### Test File Creation Order (TDD):

1. `tests/test_orchestration/test_parallel_stage_executor.py` — NEW
2. `tests/test_orchestration/test_stage_config.py` — ADD tests
3. `tests/test_orchestration/test_execution_loop.py` — ADD tests
4. `tests/test_workflow/test_stages.py` — ADD tests (if exists, else create)

---

## Considerations and Trade-offs

### Selected Approach Benefits:

* **Regression safety**: Tests catch breakages to existing workflow immediately
* **Clear requirements validation**: Each success criterion maps to specific tests
* **Confident refactoring**: Can restructure internals knowing tests protect behavior
* **Documentation**: Tests serve as executable specification of parallel groups

### Accepted Trade-offs:

* **Initial velocity slower**: Must write tests before implementation
* **Test maintenance**: More tests to maintain as feature evolves
* **Learning curve**: Team must understand TDD workflow

### Risk Mitigation:

* **Existing patterns**: Follow `test_parallel_executor.py` as template
* **Incremental approach**: Component-by-component test creation
* **Shared fixtures**: Leverage existing `conftest.py` fixtures

---

## References

* **Objective**: Parallel stage groups objective document
* **Research Doc**: `.agent-tracking/research/20260210-parallel-stage-groups-research.md`
* **Test Examples**: `tests/test_orchestration/test_parallel_executor.py` (lines 1-240)
* **Test Config**: `pyproject.toml` (lines 42-52)
* **Fixtures**: `tests/test_orchestration/conftest.py`

---

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate TDD approach into implementation phases
4. 🔍 Implementation will follow test-first approach per component

---

**Strategy Status**: DRAFT  
**Approved By**: PENDING  
**Ready for Planning**: YES (pending approval)
