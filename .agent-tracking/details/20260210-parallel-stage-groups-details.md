<!-- markdownlint-disable-file -->
# Implementation Details: Parallel Stage Groups

**Research Reference**: `.agent-tracking/research/20260210-parallel-stage-groups-research.md`  
**Test Strategy Reference**: `.agent-tracking/test-strategies/20260210-parallel-stage-groups-test-strategy.md`

---

## Phase 1: Configuration Schema

### Task 1.1: Write tests for `ParallelGroupConfig` dataclass parsing (Lines 28-52)

**File**: `tests/test_orchestration/test_stage_config.py`

**Test Cases**:
```python
def test_parse_parallel_groups_valid():
    """Valid parallel_groups parses correctly."""
    # YAML with parallel_groups section
    # Assert ParallelGroupConfig created with correct fields
    
def test_parse_parallel_groups_invalid_stage_raises():
    """Invalid stage name in group raises ValueError."""
    # YAML with non-existent stage name
    # Assert ValueError raised with descriptive message
```

**Success Criteria**:
- Tests run and fail (no implementation yet)
- Test structure follows existing patterns in `test_stage_config.py`

---

### Task 1.2: Write tests for `parallel_groups` field in `StagesConfiguration` (Lines 53-68)

**File**: `tests/test_orchestration/test_stage_config.py`

**Test Cases**:
```python
def test_stages_config_has_parallel_groups_field():
    """StagesConfiguration has parallel_groups attribute."""
    config = load_stages_config()
    assert hasattr(config, 'parallel_groups')
    assert isinstance(config.parallel_groups, list)

def test_stages_config_parallel_groups_default_empty():
    """Missing parallel_groups defaults to empty list."""
    # YAML without parallel_groups section
    config = load_stages_config(yaml_without_groups)
    assert config.parallel_groups == []
```

**Success Criteria**:
- Tests define expected interface
- Tests fail initially (TDD)

---

### Task 1.3: Implement `ParallelGroupConfig` dataclass (Lines 69-95)

**File**: `src/teambot/orchestration/stage_config.py`

**Implementation**:
```python
@dataclass
class ParallelGroupConfig:
    """Configuration for a parallel stage group."""
    
    name: str  # Group identifier (e.g., "post_spec_review")
    after: WorkflowStage  # Trigger stage that must complete first
    stages: list[WorkflowStage]  # Stages to run in parallel
    before: WorkflowStage  # Gate stage - all must complete before this
```

**Location**: Add after `StageConfig` dataclass (around line 35)

**Success Criteria**:
- Dataclass defined with all required fields
- Type hints correct
- No runtime errors on import

---

### Task 1.4: Add `parallel_groups` parsing in `_parse_configuration()` (Lines 96-125)

**File**: `src/teambot/orchestration/stage_config.py`

**Implementation** (add to `_parse_configuration()` function):
```python
# Parse parallel groups (after existing parsing, before return)
parallel_groups_data = data.get("parallel_groups", {})
parallel_groups: list[ParallelGroupConfig] = []

for group_name, group_data in parallel_groups_data.items():
    try:
        after_stage = WorkflowStage[group_data["after"]]
        before_stage = WorkflowStage[group_data["before"]]
        stages = [WorkflowStage[s] for s in group_data["stages"]]
    except KeyError as e:
        raise ValueError(f"Invalid stage name in parallel group '{group_name}': {e}")
    
    parallel_groups.append(ParallelGroupConfig(
        name=group_name,
        after=after_stage,
        stages=stages,
        before=before_stage,
    ))
```

**Also update `StagesConfiguration` dataclass**:
```python
@dataclass
class StagesConfiguration:
    # ... existing fields ...
    parallel_groups: list[ParallelGroupConfig] = field(default_factory=list)
```

**Success Criteria**:
- Parsing handles valid YAML
- Parsing handles missing section (empty list)
- Parsing raises ValueError for invalid stage names

---

### Task 1.5: Add `parallel_groups` section to `stages.yaml` (Lines 126-145)

**File**: `stages.yaml`

**Add before `stage_order:` section (around line 372)**:
```yaml
# Parallel stage groups - stages that execute concurrently
# after: trigger stage that must complete first
# stages: list of stages to run in parallel
# before: gate stage - all parallel stages must complete before this
parallel_groups:
  post_spec_review:
    after: SPEC_REVIEW
    stages:
      - RESEARCH
      - TEST_STRATEGY
    before: PLAN
```

**Success Criteria**:
- YAML parses without error
- `load_stages_config()` returns config with parallel group

---

## Phase 2: ParallelStageExecutor

### Task 2.1: Create test file (Lines 148-180)

**File**: `tests/test_orchestration/test_parallel_stage_executor.py`

**Template**:
```python
"""Tests for ParallelStageExecutor (TDD)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from teambot.workflow.stages import WorkflowStage


class TestParallelStageExecutor:
    """Tests for ParallelStageExecutor class."""

    @pytest.fixture
    def mock_execution_loop(self) -> MagicMock:
        """Create mock ExecutionLoop with stage execution methods."""
        loop = MagicMock()
        loop._execute_work_stage = AsyncMock(return_value="Stage output")
        loop.stages_config = MagicMock()
        loop.stages_config.review_stages = set()
        loop.stage_outputs = {}
        return loop
```

**Success Criteria**:
- File created with proper imports
- Fixture defined for mock execution loop

---

### Task 2.2: Write test `test_execute_parallel_empty_stages` (Lines 181-195)

```python
@pytest.mark.asyncio
async def test_execute_parallel_empty_stages(
    self, mock_execution_loop: MagicMock
) -> None:
    """Empty stage list returns empty dict."""
    from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor
    
    executor = ParallelStageExecutor(max_concurrent=2)
    result = await executor.execute_parallel([], mock_execution_loop)
    
    assert result == {}
    mock_execution_loop._execute_work_stage.assert_not_called()
```

---

### Task 2.3: Write test `test_execute_parallel_single_stage` (Lines 196-215)

```python
@pytest.mark.asyncio
async def test_execute_parallel_single_stage(
    self, mock_execution_loop: MagicMock
) -> None:
    """Single stage executes and returns result."""
    from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor
    
    executor = ParallelStageExecutor(max_concurrent=2)
    stages = [WorkflowStage.RESEARCH]
    
    results = await executor.execute_parallel(stages, mock_execution_loop)
    
    assert len(results) == 1
    assert results[WorkflowStage.RESEARCH].success is True
    assert results[WorkflowStage.RESEARCH].output == "Stage output"
```

---

### Task 2.4: Write test `test_execute_parallel_multiple_stages` (Lines 216-240)

```python
@pytest.mark.asyncio
async def test_execute_parallel_multiple_stages(
    self, mock_execution_loop: MagicMock
) -> None:
    """Multiple stages execute concurrently."""
    from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor
    
    executor = ParallelStageExecutor(max_concurrent=2)
    stages = [WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY]
    
    results = await executor.execute_parallel(stages, mock_execution_loop)
    
    assert len(results) == 2
    assert results[WorkflowStage.RESEARCH].success is True
    assert results[WorkflowStage.TEST_STRATEGY].success is True
    assert mock_execution_loop._execute_work_stage.call_count == 2
```

---

### Task 2.5: Write test `test_execute_parallel_partial_failure` (Lines 241-270)

```python
@pytest.mark.asyncio
async def test_execute_parallel_partial_failure(
    self, mock_execution_loop: MagicMock
) -> None:
    """One stage fails, other completes successfully."""
    from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor
    
    # First call succeeds, second fails
    mock_execution_loop._execute_work_stage.side_effect = [
        "Success output",
        Exception("Stage failed"),
    ]
    
    executor = ParallelStageExecutor(max_concurrent=2)
    stages = [WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY]
    
    results = await executor.execute_parallel(stages, mock_execution_loop)
    
    # Both stages should have results
    assert len(results) == 2
    # One succeeded
    success_results = [r for r in results.values() if r.success]
    assert len(success_results) == 1
    # One failed
    failed_results = [r for r in results.values() if not r.success]
    assert len(failed_results) == 1
    assert "Stage failed" in failed_results[0].error
```

---

### Task 2.6: Write test `test_execute_parallel_respects_concurrency` (Lines 271-295)

```python
@pytest.mark.asyncio
async def test_execute_parallel_respects_concurrency(
    self, mock_execution_loop: MagicMock
) -> None:
    """Executor respects max_concurrent limit."""
    from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor
    
    concurrent_count = 0
    max_observed = 0
    
    async def track_concurrency(stage, on_progress=None):
        nonlocal concurrent_count, max_observed
        concurrent_count += 1
        max_observed = max(max_observed, concurrent_count)
        await asyncio.sleep(0.1)  # Simulate work
        concurrent_count -= 1
        return "output"
    
    mock_execution_loop._execute_work_stage = track_concurrency
    
    executor = ParallelStageExecutor(max_concurrent=1)  # Limit to 1
    stages = [WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY]
    
    await executor.execute_parallel(stages, mock_execution_loop)
    
    assert max_observed == 1  # Never more than 1 concurrent
```

---

### Task 2.7: Write test `test_execute_parallel_progress_callbacks` (Lines 296-320)

```python
@pytest.mark.asyncio
async def test_execute_parallel_progress_callbacks(
    self, mock_execution_loop: MagicMock
) -> None:
    """Progress callbacks fire for each stage."""
    from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor
    
    events: list[tuple[str, dict]] = []
    def on_progress(event_type: str, data: dict) -> None:
        events.append((event_type, data))
    
    executor = ParallelStageExecutor(max_concurrent=2)
    stages = [WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY]
    
    await executor.execute_parallel(stages, mock_execution_loop, on_progress)
    
    # Check for start events
    start_events = [e for e in events if e[0] == "parallel_stage_start"]
    assert len(start_events) == 2
    
    # Check for complete events
    complete_events = [e for e in events if e[0] == "parallel_stage_complete"]
    assert len(complete_events) == 2
```

---

### Task 2.8: Implement `StageResult` dataclass (Lines 321-340)

**File**: `src/teambot/orchestration/parallel_stage_executor.py`

```python
"""Parallel execution for workflow stages."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from teambot.workflow.stages import WorkflowStage

if TYPE_CHECKING:
    from teambot.orchestration.execution_loop import ExecutionLoop
    from teambot.orchestration.review_iterator import ReviewStatus


@dataclass
class StageResult:
    """Result of stage execution in parallel group."""
    
    stage: WorkflowStage
    success: bool
    output: str = ""
    error: str | None = None
    review_status: Any = None  # ReviewStatus | None, but avoid import cycle
```

---

### Task 2.9: Implement `ParallelStageExecutor` class (Lines 341-420)

**File**: `src/teambot/orchestration/parallel_stage_executor.py` (continue from 2.8)

```python
class ParallelStageExecutor:
    """Execute multiple workflow stages in parallel."""

    def __init__(self, max_concurrent: int = 2):
        """Initialize executor.
        
        Args:
            max_concurrent: Maximum stages to run concurrently
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_parallel(
        self,
        stages: list[WorkflowStage],
        execution_loop: "ExecutionLoop",
        on_progress: Callable[[str, Any], None] | None = None,
    ) -> dict[WorkflowStage, StageResult]:
        """Execute stages concurrently.

        Each stage is executed using the ExecutionLoop's existing
        _execute_work_stage or _execute_review_stage methods.

        Failures in one stage do not cancel others - all stages
        run to completion and results are collected.
        
        Args:
            stages: List of stages to execute in parallel
            execution_loop: ExecutionLoop instance for stage execution
            on_progress: Optional progress callback
            
        Returns:
            Dict mapping each stage to its result
        """
        if not stages:
            return {}

        async def execute_one(stage: WorkflowStage) -> tuple[WorkflowStage, StageResult]:
            async with self.semaphore:
                if on_progress:
                    on_progress("parallel_stage_start", {"stage": stage.name})

                try:
                    # Delegate to ExecutionLoop's existing stage execution
                    if stage in execution_loop.stages_config.review_stages:
                        status = await execution_loop._execute_review_stage(
                            stage, on_progress
                        )
                        # Import here to avoid cycle
                        from teambot.orchestration.review_iterator import ReviewStatus
                        success = status == ReviewStatus.APPROVED
                        return stage, StageResult(
                            stage=stage,
                            success=success,
                            output=execution_loop.stage_outputs.get(stage, ""),
                            review_status=status,
                        )
                    else:
                        output = await execution_loop._execute_work_stage(
                            stage, on_progress
                        )
                        return stage, StageResult(
                            stage=stage,
                            success=True,
                            output=output if output else "",
                        )

                except Exception as e:
                    if on_progress:
                        on_progress("parallel_stage_failed", {
                            "stage": stage.name,
                            "error": str(e),
                        })
                    return stage, StageResult(
                        stage=stage,
                        success=False,
                        error=str(e),
                    )

        # Execute all stages concurrently (no early cancellation)
        results = await asyncio.gather(
            *[execute_one(s) for s in stages],
            return_exceptions=True,
        )

        # Convert to dict, handling any unexpected exceptions
        output: dict[WorkflowStage, StageResult] = {}
        for result in results:
            if isinstance(result, Exception):
                # Shouldn't happen since we catch in execute_one, but handle it
                continue
            stage, stage_result = result
            output[stage] = stage_result

            if on_progress:
                event = "parallel_stage_complete" if stage_result.success else "parallel_stage_failed"
                on_progress(event, {"stage": stage.name})

        return output
```

---

### Task 2.10: Verify all executor tests pass (Lines 421-430)

**Command**:
```bash
uv run pytest tests/test_orchestration/test_parallel_stage_executor.py -v
```

**Success Criteria**:
- All tests pass
- No errors or warnings

---

## Phase 3: State Machine Updates

### Task 3.1: Write test for transition validation (Lines 433-450)

**File**: `tests/test_workflow/test_stages.py` (create if needed)

```python
def test_spec_review_next_stages_includes_research_and_test_strategy():
    """SPEC_REVIEW allows transition to both RESEARCH and TEST_STRATEGY."""
    from teambot.workflow.stages import STAGE_METADATA, WorkflowStage
    
    spec_review_meta = STAGE_METADATA[WorkflowStage.SPEC_REVIEW]
    
    assert WorkflowStage.RESEARCH in spec_review_meta.next_stages
    assert WorkflowStage.TEST_STRATEGY in spec_review_meta.next_stages
```

---

### Task 3.2: Update `SPEC_REVIEW.next_stages` (Lines 451-470)

**File**: `src/teambot/workflow/stages.py`

**Current** (line ~78):
```python
next_stages=[WorkflowStage.RESEARCH],
```

**Change to**:
```python
next_stages=[WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY],
```

**Success Criteria**:
- State machine validates transitions to both stages
- Existing tests still pass

---

### Task 3.3: Verify convergence at PLAN (Lines 471-485)

Verify that both `RESEARCH` and `TEST_STRATEGY` have `PLAN` as their next stage:

**File**: `src/teambot/workflow/stages.py`

Check lines ~86 and ~94:
```python
# RESEARCH
next_stages=[WorkflowStage.TEST_STRATEGY],  # CHANGE to [WorkflowStage.PLAN]

# TEST_STRATEGY  
next_stages=[WorkflowStage.PLAN],  # Already correct
```

**Note**: For parallel execution, RESEARCH should skip TEST_STRATEGY since they run together.

---

## Phase 4: ExecutionLoop Integration

### Task 4.1-4.5: Write integration tests (Lines 488-620)

**File**: `tests/test_orchestration/test_execution_loop.py`

Add to existing test class:

```python
@pytest.mark.asyncio
async def test_get_parallel_group_for_stage_returns_group(
    self, loop: ExecutionLoop
) -> None:
    """Returns parallel group when stage is first in group."""
    # Setup mock stages_config with parallel group
    group = loop._get_parallel_group_for_stage(WorkflowStage.RESEARCH)
    
    if loop.stages_config.parallel_groups:
        assert group is not None
        assert WorkflowStage.RESEARCH in group.stages

@pytest.mark.asyncio
async def test_get_parallel_group_for_stage_returns_none(
    self, loop: ExecutionLoop
) -> None:
    """Returns None for stages not in parallel group."""
    group = loop._get_parallel_group_for_stage(WorkflowStage.SPEC)
    assert group is None

@pytest.mark.asyncio
async def test_run_sequential_stages_unchanged(
    self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
) -> None:
    """Sequential stages still work correctly (regression test)."""
    # Run through SETUP -> BUSINESS_PROBLEM -> SPEC
    # Verify sequential execution unchanged
```

---

### Task 4.6: Implement `_get_parallel_group_for_stage()` (Lines 621-645)

**File**: `src/teambot/orchestration/execution_loop.py`

```python
def _get_parallel_group_for_stage(
    self, stage: WorkflowStage
) -> "ParallelGroupConfig | None":
    """Find parallel group that starts with this stage.
    
    Args:
        stage: Current stage to check
        
    Returns:
        ParallelGroupConfig if stage is first in a group, None otherwise
    """
    from teambot.orchestration.stage_config import ParallelGroupConfig
    
    for group in self.stages_config.parallel_groups:
        # Only trigger on the first stage in the group
        if stage == group.stages[0]:
            return group
    return None
```

---

### Task 4.7: Implement `_execute_parallel_group()` (Lines 646-700)

**File**: `src/teambot/orchestration/execution_loop.py`

```python
async def _execute_parallel_group(
    self,
    group: "ParallelGroupConfig",
    on_progress: Callable[[str, Any], None] | None,
) -> bool:
    """Execute all stages in a parallel group.
    
    Args:
        group: Parallel group configuration
        on_progress: Progress callback
        
    Returns:
        True if all stages succeeded, False if any failed
    """
    from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor
    
    if on_progress:
        on_progress("parallel_group_start", {
            "group": group.name,
            "stages": [s.name for s in group.stages],
        })

    # Filter to only incomplete stages (for resume support)
    stages_to_run = self._filter_incomplete_stages(group)
    
    if not stages_to_run:
        # All stages already complete
        return True

    executor = ParallelStageExecutor(max_concurrent=2)
    results = await executor.execute_parallel(
        stages=stages_to_run,
        execution_loop=self,
        on_progress=on_progress,
    )

    # Track results in parallel_group_status
    if group.name not in self.parallel_group_status:
        self.parallel_group_status[group.name] = {"stages": {}}
    
    for stage, result in results.items():
        self.parallel_group_status[group.name]["stages"][stage.name] = {
            "status": "completed" if result.success else "failed",
            "error": result.error,
        }

    if on_progress:
        all_success = all(r.success for r in results.values())
        on_progress("parallel_group_complete", {
            "group": group.name,
            "all_success": all_success,
        })

    return all(r.success for r in results.values())
```

---

### Task 4.8: Modify `run()` main loop (Lines 701-740)

**File**: `src/teambot/orchestration/execution_loop.py`

**Modify the stage execution block** (around line 166-196):

```python
# Execute stage based on type
stage_config = self.stages_config.stages.get(stage)

# NEW: Check for parallel group first
parallel_group = self._get_parallel_group_for_stage(stage)
if parallel_group:
    success = await self._execute_parallel_group(parallel_group, on_progress)
    if not success:
        self._save_state(ExecutionResult.ERROR)
        return ExecutionResult.ERROR
    # Skip to the 'before' stage (PLAN) after parallel group completes
    self.current_stage = parallel_group.before
    self._save_state()
    continue  # Skip normal advancement

elif stage in self.stages_config.acceptance_test_stages:
    # ... existing acceptance test logic ...
```

---

## Phase 5: State Persistence & Resume

### Task 5.1-5.4: Write state persistence tests (Lines 743-850)

**File**: `tests/test_orchestration/test_execution_loop.py`

```python
def test_save_state_includes_parallel_group_status(
    self, loop: ExecutionLoop, tmp_path: Path
) -> None:
    """Save state includes parallel_group_status field."""
    loop.parallel_group_status = {
        "post_spec_review": {
            "stages": {
                "RESEARCH": {"status": "completed"},
                "TEST_STRATEGY": {"status": "in_progress"},
            }
        }
    }
    loop._save_state()
    
    state_file = loop.teambot_dir / "orchestration_state.json"
    state = json.loads(state_file.read_text())
    
    assert "parallel_group_status" in state
    assert state["parallel_group_status"]["post_spec_review"]["stages"]["RESEARCH"]["status"] == "completed"

def test_resume_backward_compat_missing_parallel_status(
    self, tmp_path: Path
) -> None:
    """Old state files without parallel_group_status load correctly."""
    # Create state file without parallel_group_status
    state_file = tmp_path / ".teambot" / "orchestration_state.json"
    state_file.parent.mkdir(parents=True)
    state_file.write_text(json.dumps({
        "current_stage": "RESEARCH",
        "stage_outputs": {},
        "objective_file": "test.md",
    }))
    
    loop = ExecutionLoop.resume(tmp_path, config)
    
    assert loop.parallel_group_status == {}  # Defaults to empty
```

---

### Task 5.5: Add `parallel_group_status` field (Lines 851-865)

**File**: `src/teambot/orchestration/execution_loop.py`

In `__init__`:
```python
# Parallel group tracking (for resume)
self.parallel_group_status: dict[str, dict[str, Any]] = {}
```

---

### Task 5.6: Update `_save_state()` (Lines 866-890)

Add to state dict in `_save_state()`:
```python
state = {
    # ... existing fields ...
    "parallel_group_status": self.parallel_group_status,
}
```

---

### Task 5.7: Update `resume()` classmethod (Lines 891-930)

Add in `resume()` after loading existing fields:
```python
# Load parallel group status with backward compatibility
loop.parallel_group_status = state.get("parallel_group_status", {})
```

---

### Task 5.8: Implement `_filter_incomplete_stages()` (Lines 931-955)

**File**: `src/teambot/orchestration/execution_loop.py`

```python
def _filter_incomplete_stages(
    self, group: "ParallelGroupConfig"
) -> list[WorkflowStage]:
    """Filter parallel group to only incomplete stages.
    
    For resume support - only re-run stages that didn't complete.
    
    Args:
        group: Parallel group configuration
        
    Returns:
        List of stages that need to be executed
    """
    group_status = self.parallel_group_status.get(group.name, {})
    stages_status = group_status.get("stages", {})
    
    incomplete = []
    for stage in group.stages:
        stage_info = stages_status.get(stage.name, {})
        if stage_info.get("status") != "completed":
            incomplete.append(stage)
    
    return incomplete
```

---

## Phase 6: Progress Events

### Task 6.1-6.3: Add progress event handling (Lines 958-1030)

**File**: `src/teambot/orchestration/progress.py`

Add handling for new event types in the progress callback:

```python
# New parallel group events
if event_type == "parallel_group_start":
    group_name = data.get("group", "unknown")
    stages = data.get("stages", [])
    console.print(f"[bold]Starting parallel group:[/] {group_name}")
    console.print(f"  Stages: {', '.join(stages)}")

elif event_type == "parallel_stage_start":
    stage = data.get("stage", "unknown")
    console.print(f"  ├── [yellow]{stage}[/] starting...")

elif event_type == "parallel_stage_complete":
    stage = data.get("stage", "unknown")
    console.print(f"  ├── [green]{stage}[/] ✓")

elif event_type == "parallel_stage_failed":
    stage = data.get("stage", "unknown")
    error = data.get("error", "")
    console.print(f"  ├── [red]{stage}[/] ✗ {error}")

elif event_type == "parallel_group_complete":
    group_name = data.get("group", "unknown")
    all_success = data.get("all_success", False)
    status = "✓ complete" if all_success else "✗ failed"
    console.print(f"[bold]Parallel group {group_name}:[/] {status}")
```

---

## Phase 7: Integration Testing

### Task 7.1-7.4: Integration tests (Lines 1033-1155)

**File**: `tests/test_orchestration/test_execution_loop.py`

```python
@pytest.mark.asyncio
async def test_full_workflow_with_parallel_groups(
    self, tmp_path: Path, mock_sdk_client: AsyncMock
) -> None:
    """Full workflow executes parallel groups correctly."""
    # Setup objective and config with parallel groups
    # Run full workflow
    # Verify RESEARCH and TEST_STRATEGY both executed
    # Verify they completed before PLAN started

@pytest.mark.asyncio  
async def test_resume_mid_parallel_group(
    self, tmp_path: Path, mock_sdk_client: AsyncMock
) -> None:
    """Resume mid-parallel-group only re-runs incomplete stages."""
    # Create state with RESEARCH complete, TEST_STRATEGY incomplete
    # Resume
    # Verify only TEST_STRATEGY executes

@pytest.mark.asyncio
async def test_parallel_group_partial_failure(
    self, tmp_path: Path, mock_sdk_client: AsyncMock
) -> None:
    """Partial failure in parallel group - other stages complete."""
    # Setup one stage to fail
    # Run workflow
    # Verify failed stage error captured
    # Verify successful stage completed
```

---

## Phase 8: Final Validation

### Task 8.1-8.4: Validation commands (Lines 1158-1195)

```bash
# Linting
uv run ruff check . --fix

# Formatting
uv run ruff format .

# Full test suite
uv run pytest --cov=src/teambot --cov-report=term-missing

# Manual test
uv run teambot run docs/objectives/test-parallel-groups.md
```

**Success Criteria**:
- All linting passes
- All tests pass (1050+ tests)
- Coverage >= 80%
- Manual run shows parallel execution in output
