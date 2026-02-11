<!-- markdownlint-disable-file -->
# 🔬 Research Document: Parallel Stage Groups

**Date**: 2026-02-10  
**Feature**: Parallel Stage Group Execution for File-Based Orchestration  
**Status**: ✅ Research Complete  
**Related Spec**: `docs/objectives/parallel-stage-groups.md`

---

## 📋 Executive Summary

This research document analyzes the implementation approach for introducing **parallel stage groups** to TeamBot's file-based orchestration. The feature enables concurrent execution of independent workflow stages (starting with `RESEARCH` and `TEST_STRATEGY` post-`SPEC_REVIEW`) while maintaining the sequential backbone of the 14-stage workflow.

### Key Findings

1. **Dual Stage-Ordering Mechanisms**: The codebase uses two stage-ordering systems:
   - `stages.py` → `STAGE_METADATA[stage].next_stages` (directed graph for state machine validation)
   - `stages.yaml` → `stage_order` (linear list for execution loop progression)
   
2. **Existing ParallelExecutor Limitation**: The current `ParallelExecutor` operates on `AgentTask` objects (agent-level parallelism within a single stage) and is unsuitable for stage-level parallelism.

3. **State Persistence Gap**: Current `orchestration_state.json` tracks only `current_stage` (single value) — insufficient for parallel group tracking.

4. **Clean Entry Point**: The execution loop in `_run()` is the ideal integration point for parallel groups.

---

## 📊 Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `teambot run objective.md` | cli.py → `cmd_run()` → `_run_orchestration()` → `ExecutionLoop.run()` | ✅ YES | YES - Main execution loop |
| `teambot run --resume` | cli.py → `cmd_run()` → `_run_orchestration_resume()` → `ExecutionLoop.resume()` → `run()` | ✅ YES | YES - Resume must handle parallel groups |
| Interactive mode (`@agent task`) | cli.py → `run_interactive_mode()` | ❌ NO | NO - Not file-based orchestration |

### Code Path Trace

#### Entry Point 1: New Workflow Execution
1. User runs: `teambot run objectives/feature.md`
2. Handled by: `cli.py:cmd_run()` (lines 107-178)
3. Routes to: `cli.py:_run_orchestration()` (lines 201-280)
4. Creates: `ExecutionLoop(objective_path, config, teambot_dir, max_hours)`
5. Executes: `ExecutionLoop.run(sdk_client, on_progress)` (lines 131-208)
6. Stage loop: `while self.current_stage != WorkflowStage.COMPLETE:` (line 150)
7. **Integration Point**: Stage execution logic (lines 166-198) ✅

#### Entry Point 2: Resume Interrupted Workflow
1. User runs: `teambot run --resume`
2. Handled by: `cli.py:cmd_run()` → `_run_orchestration_resume()`
3. Calls: `ExecutionLoop.resume(teambot_dir, config)` (lines 897-950)
4. Restores: `current_stage`, `stage_outputs`, `acceptance_test*` fields
5. Continues: `run()` method with restored state
6. **Integration Point**: State restoration must include parallel group status ✅

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| `orchestration_state.json` lacks parallel group tracking | Resume fails mid-parallel-group | Add `parallel_group_status` field with per-stage completion |
| `stages.py:STAGE_METADATA` shows sequential next_stages | State machine validation rejects parallel transitions | Update `SPEC_REVIEW.next_stages = [RESEARCH, TEST_STRATEGY]` |
| `_get_next_stage()` assumes linear progression | Cannot express "both completed" semantics | Refactor to check parallel group completion |

---

## 🏗️ Architecture Analysis

### Current Workflow Execution Model

```
┌─────────────────────────────────────────────────────────────────┐
│                      ExecutionLoop.run()                        │
├─────────────────────────────────────────────────────────────────┤
│  while current_stage != COMPLETE:                               │
│    ├── Check cancellation/timeout                               │
│    ├── Execute stage:                                           │
│    │     ├── acceptance_test_stage → _execute_acceptance_test   │
│    │     ├── review_stage → _execute_review_stage               │
│    │     └── work_stage → _execute_work_stage                   │
│    ├── Advance: current_stage = _get_next_stage(current)        │
│    └── Save state                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Proposed Parallel Execution Model

```
┌─────────────────────────────────────────────────────────────────┐
│                      ExecutionLoop.run()                        │
├─────────────────────────────────────────────────────────────────┤
│  while current_stage != COMPLETE:                               │
│    ├── Check cancellation/timeout                               │
│    ├── Check if current_stage is part of parallel_group         │
│    │     ├── YES: Execute parallel group via ParallelStageExec  │
│    │     │        ├── asyncio.gather() all stages               │
│    │     │        ├── Track per-stage completion                │
│    │     │        ├── Allow failures (no early cancel)          │
│    │     │        └── Report all results                        │
│    │     └── NO: Execute single stage (existing logic)          │
│    ├── Advance: _get_next_stage() (parallel-aware)              │
│    └── Save state (parallel group status)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Key File Analysis

### 1. `stages.yaml` - Configuration (Lines 372-387)

**Current State:**
```yaml
stage_order:
  - SETUP
  - BUSINESS_PROBLEM
  - SPEC
  - SPEC_REVIEW
  - RESEARCH       # Currently sequential
  - TEST_STRATEGY  # Currently sequential
  - PLAN
  # ... rest
```

**Required Addition:**
```yaml
# New section for parallel stage groups
parallel_groups:
  post_spec_review:
    after: SPEC_REVIEW
    stages:
      - RESEARCH
      - TEST_STRATEGY
    before: PLAN  # All must complete before PLAN starts
```

**Why This Design:**
- Groups are named for documentation/logging
- `after` specifies the trigger stage
- `stages` lists concurrent stages
- `before` specifies the gate stage (waits for all)

### 2. `stages.py` - State Machine Transitions (Lines 46-160)

**Current `SPEC_REVIEW` Definition:**
```python
WorkflowStage.SPEC_REVIEW: StageMetadata(
    name="Spec Review",
    # ...
    next_stages=[WorkflowStage.RESEARCH],  # Only RESEARCH
),
```

**Required Change:**
```python
WorkflowStage.SPEC_REVIEW: StageMetadata(
    name="Spec Review",
    # ...
    next_stages=[WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY],  # Fan-out
),
```

**Why This Matters:**
- `can_transition_to()` in `state_machine.py` validates against `next_stages`
- Without this change, transition to `TEST_STRATEGY` from `SPEC_REVIEW` would be rejected
- Both stages must be valid next stages for parallel execution

### 3. `parallel_executor.py` - Existing Agent-Level Parallelism (Lines 29-102)

**Current Interface:**
```python
class ParallelExecutor:
    async def execute_parallel(
        self,
        tasks: list[AgentTask],  # Agent-level tasks
        on_progress: Callable[[str, dict], None] | None = None,
    ) -> dict[str, TaskResult]:
```

**Why This Is Unsuitable for Stage Parallelism:**
- `AgentTask` represents a single agent prompt/response
- No stage lifecycle management (context building, output storage)
- No review iteration support for review stages in the group
- Callback signature doesn't support stage-level events

**Recommended Approach: New `ParallelStageExecutor`:**
```python
@dataclass
class StageTask:
    """A stage to be executed in a parallel group."""
    stage: WorkflowStage
    is_review: bool = False

@dataclass
class StageResult:
    """Result of stage execution."""
    stage: WorkflowStage
    success: bool
    output: str = ""
    error: str | None = None
    review_status: ReviewStatus | None = None

class ParallelStageExecutor:
    """Execute multiple workflow stages in parallel."""
    
    async def execute_parallel(
        self,
        stages: list[StageTask],
        execution_loop: ExecutionLoop,
        on_progress: Callable[[str, Any], None] | None = None,
    ) -> dict[WorkflowStage, StageResult]:
        """Execute stages concurrently, delegating to ExecutionLoop methods."""
```

### 4. `execution_loop.py` - Main Execution (Lines 131-208)

**Integration Point (Lines 166-198):**
```python
# Current: Sequential stage execution
if stage in self.stages_config.acceptance_test_stages:
    await self._execute_acceptance_test_with_retry(stage, on_progress)
elif stage in self.stages_config.review_stages:
    result = await self._execute_review_stage(stage, on_progress)
else:
    await self._execute_work_stage(stage, on_progress)
```

**Proposed Integration:**
```python
# New: Check for parallel groups first
parallel_group = self._get_parallel_group(stage)
if parallel_group:
    await self._execute_parallel_group(parallel_group, on_progress)
else:
    # Existing sequential logic
    if stage in self.stages_config.acceptance_test_stages:
        await self._execute_acceptance_test_with_retry(stage, on_progress)
    elif stage in self.stages_config.review_stages:
        result = await self._execute_review_stage(stage, on_progress)
    else:
        await self._execute_work_stage(stage, on_progress)
```

### 5. `stage_config.py` - Configuration Loading (Lines 108-180)

**Required Additions:**
```python
@dataclass
class ParallelGroupConfig:
    """Configuration for a parallel stage group."""
    name: str
    after: WorkflowStage  # Trigger stage
    stages: list[WorkflowStage]
    before: WorkflowStage  # Gate stage

@dataclass
class StagesConfiguration:
    # ... existing fields ...
    parallel_groups: list[ParallelGroupConfig] = field(default_factory=list)
```

**Parsing Addition in `_parse_configuration()`:**
```python
# Parse parallel groups
parallel_groups_data = data.get("parallel_groups", {})
parallel_groups = []
for group_name, group_data in parallel_groups_data.items():
    parallel_groups.append(ParallelGroupConfig(
        name=group_name,
        after=WorkflowStage[group_data["after"]],
        stages=[WorkflowStage[s] for s in group_data["stages"]],
        before=WorkflowStage[group_data["before"]],
    ))
```

---

## 🔄 State Persistence Changes

### Current State Structure (`orchestration_state.json`)

```json
{
  "objective_file": "objectives/feature.md",
  "current_stage": "RESEARCH",  // Single stage
  "elapsed_seconds": 1234.5,
  "max_seconds": 28800,
  "status": "in_progress",
  "stage_outputs": { "SPEC": "...", "SPEC_REVIEW": "..." },
  "acceptance_tests_passed": false,
  // ...
}
```

### Required State Changes

```json
{
  "objective_file": "objectives/feature.md",
  "current_stage": "RESEARCH",  // Primary tracking (first in group)
  "parallel_group_status": {    // NEW: Per-stage tracking
    "post_spec_review": {
      "active": true,
      "stages": {
        "RESEARCH": { "status": "completed", "output_key": "RESEARCH" },
        "TEST_STRATEGY": { "status": "in_progress", "output_key": null }
      }
    }
  },
  "elapsed_seconds": 1234.5,
  "stage_outputs": { "SPEC": "...", "SPEC_REVIEW": "...", "RESEARCH": "..." },
  // ...
}
```

### Backward Compatibility

**Requirement:** Old state files without `parallel_group_status` must still load.

**Solution in `resume()` method:**
```python
# Load with defaults for missing parallel group data
loop.parallel_group_status = state.get("parallel_group_status", {})
# If resuming in the middle of a parallel group, detect from current_stage
if loop.current_stage in [s for pg in config.parallel_groups for s in pg.stages]:
    # Reconstruct partial group status from stage_outputs
    loop._reconstruct_parallel_group_status()
```

---

## 🧪 Testing Strategy Research

### Existing Test Infrastructure

| Aspect | Details |
|--------|---------|
| **Framework** | pytest 7.x with pytest-asyncio, pytest-mock, pytest-cov |
| **Location** | `tests/test_orchestration/` (mirrors `src/teambot/orchestration/`) |
| **Naming** | `test_*.py` with `Test*` classes |
| **Runner** | `uv run pytest` |
| **Coverage** | 80% target, `--cov=src/teambot` |
| **Async Tests** | `@pytest.mark.asyncio` with `asyncio_mode = "auto"` |

### Relevant Test Files

1. **`test_parallel_executor.py`** (Lines 1-240)
   - Tests for existing agent-level `ParallelExecutor`
   - Good patterns for: concurrency limits, progress callbacks, partial failures
   - Use as template for `ParallelStageExecutor` tests

2. **`test_execution_loop.py`** (Lines 1-400+)
   - Tests for `ExecutionLoop` lifecycle
   - Fixtures: `mock_sdk_client`, `objective_file`, `teambot_dir_with_spec`
   - Tests state persistence, resume, stage transitions
   - Add tests for parallel group execution here

3. **`test_stage_config.py`** (Lines 1-250+)
   - Tests for `load_stages_config()` and `StagesConfiguration`
   - Add tests for `parallel_groups` parsing

4. **`conftest.py`** - Shared fixtures
   - `sample_objective_content`, `teambot_dir`, `mock_sdk_client`

### Test Patterns Identified

**1. Async Test Pattern:**
```python
@pytest.mark.asyncio
async def test_run_completes_all_stages(
    self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
) -> None:
    result = await loop.run(mock_sdk_client)
    assert result == ExecutionResult.COMPLETE
```

**2. Progress Callback Testing:**
```python
@pytest.mark.asyncio
async def test_run_calls_progress_callback(
    self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
) -> None:
    progress_calls = []
    result = await loop.run(
        mock_sdk_client,
        on_progress=lambda e, d: progress_calls.append((e, d)),
    )
    stage_changes = [c for c in progress_calls if c[0] == "stage_changed"]
    assert len(stage_changes) > 0
```

**3. Partial Failure Testing:**
```python
@pytest.mark.asyncio
async def test_execute_parallel_partial_failure(
    self, executor: ParallelExecutor, mock_sdk_client: AsyncMock
) -> None:
    mock_sdk_client.execute_streaming.side_effect = [
        "Success output",
        Exception("Task failed"),
    ]
    results = await executor.execute_parallel(tasks)
    assert results["builder-1"].success is True
    assert results["builder-2"].success is False
```

### Required Test Coverage

| Test Category | Test Cases |
|---------------|------------|
| **Config Parsing** | Valid parallel_groups, missing fields, invalid stage names |
| **Stage Execution** | Parallel stages complete, one fails, all fail |
| **Resume** | Mid-group resume, partial completion detection |
| **Progress Callbacks** | Parallel stage events, concurrent status updates |
| **Backward Compat** | Old state files load, groups disabled by default |
| **Integration** | Full workflow with parallel groups enabled |

---

## 🎨 Visualization Requirements

### Current Console Display

The `ConsoleDisplay` class in `visualization/console.py` shows agent status via `render_table()`. Stage changes are logged via progress callbacks:

```python
def on_progress(event_type: str, data: dict) -> None:
    if event_type == "stage_changed":
        display.print_success(f"Stage: {data.get('stage', 'unknown')}")
```

### Required Enhancements

**Option A: Multi-Row Parallel Display (Recommended)**
```
Stage: Running Parallel Group [post_spec_review]
  ├── RESEARCH ............... ⏳ builder-1 working
  └── TEST_STRATEGY .......... ⏳ builder-1 working
```

**Option B: Inline Concurrent Indicators**
```
Stage: RESEARCH || TEST_STRATEGY (parallel)
```

**Implementation Approach:**
1. Add new progress event types:
   - `parallel_group_start` - Group initiated
   - `parallel_stage_start` - Individual stage in group started
   - `parallel_stage_complete` - Individual stage complete
   - `parallel_group_complete` - All stages in group complete

2. Update `progress.py:create_progress_callback()` to handle new events

---

## ⚡ Recommended Technical Approach

### Single Recommended Architecture

Based on evidence analysis, the following approach is recommended:

#### 1. Configuration Schema (`stages.yaml`)

```yaml
parallel_groups:
  post_spec_review:
    after: SPEC_REVIEW
    stages:
      - RESEARCH
      - TEST_STRATEGY
    before: PLAN
```

**Rationale:**
- Declarative, no code changes needed to add new groups
- `after/before` semantics match mental model of "gates"
- Group names enable clear logging/debugging

#### 2. New `ParallelStageExecutor` Class

**Location:** `src/teambot/orchestration/parallel_stage_executor.py`

```python
"""Parallel execution for workflow stages."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from teambot.orchestration.review_iterator import ReviewStatus
from teambot.workflow.stages import WorkflowStage

if TYPE_CHECKING:
    from teambot.orchestration.execution_loop import ExecutionLoop


@dataclass
class StageResult:
    """Result of stage execution in parallel group."""
    stage: WorkflowStage
    success: bool
    output: str = ""
    error: str | None = None
    review_status: ReviewStatus | None = None


class ParallelStageExecutor:
    """Execute multiple workflow stages in parallel."""

    def __init__(self, max_concurrent: int = 2):
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
                            output=output,
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

        # Convert to dict
        output: dict[WorkflowStage, StageResult] = {}
        for result in results:
            if isinstance(result, Exception):
                continue
            stage, stage_result = result
            output[stage] = stage_result

            if on_progress:
                event = "parallel_stage_complete" if stage_result.success else "parallel_stage_failed"
                on_progress(event, {"stage": stage.name})

        return output
```

#### 3. ExecutionLoop Integration

**Changes to `execution_loop.py`:**

```python
# Add import
from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor, StageResult

class ExecutionLoop:
    def __init__(self, ...):
        # ... existing init ...
        self.parallel_executor = ParallelStageExecutor(max_concurrent=2)
        self.parallel_group_status: dict[str, dict] = {}

    async def run(self, sdk_client, on_progress=None) -> ExecutionResult:
        # ... existing setup ...
        
        while self.current_stage != WorkflowStage.COMPLETE:
            # ... cancellation/timeout checks ...
            
            stage = self.current_stage
            
            # NEW: Check for parallel group
            parallel_group = self._get_parallel_group_for_stage(stage)
            if parallel_group:
                result = await self._execute_parallel_group(parallel_group, on_progress)
                if not result:
                    self._save_state(ExecutionResult.ERROR)
                    return ExecutionResult.ERROR
            else:
                # Existing sequential execution
                # ... unchanged ...
            
            self.current_stage = self._get_next_stage(stage)
            self._save_state()

    def _get_parallel_group_for_stage(
        self, stage: WorkflowStage
    ) -> ParallelGroupConfig | None:
        """Find parallel group that starts with this stage."""
        for group in self.stages_config.parallel_groups:
            if stage == group.stages[0]:
                return group
        return None

    async def _execute_parallel_group(
        self,
        group: ParallelGroupConfig,
        on_progress: Callable[[str, Any], None] | None,
    ) -> bool:
        """Execute all stages in a parallel group."""
        if on_progress:
            on_progress("parallel_group_start", {
                "group": group.name,
                "stages": [s.name for s in group.stages],
            })

        results = await self.parallel_executor.execute_parallel(
            stages=group.stages,
            execution_loop=self,
            on_progress=on_progress,
        )

        # Track results
        self.parallel_group_status[group.name] = {
            "stages": {
                stage.name: {
                    "status": "completed" if r.success else "failed",
                    "error": r.error,
                }
                for stage, r in results.items()
            }
        }

        if on_progress:
            on_progress("parallel_group_complete", {
                "group": group.name,
                "all_success": all(r.success for r in results.values()),
            })

        # Return True if all succeeded
        return all(r.success for r in results.values())
```

#### 4. State Machine Update (`stages.py`)

```python
WorkflowStage.SPEC_REVIEW: StageMetadata(
    name="Spec Review",
    description="Review and approve the feature specification",
    allowed_personas=["reviewer", "project_manager", "pm"],
    required_artifacts=["spec_review.md"],
    optional=False,
    next_stages=[WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY],  # CHANGED: Fan-out
),
WorkflowStage.RESEARCH: StageMetadata(
    name="Research",
    description="Research technical approaches and dependencies",
    allowed_personas=["builder", "developer", "technical_writer", "writer"],
    required_artifacts=["research.md"],
    optional=False,
    next_stages=[WorkflowStage.PLAN],  # CHANGED: Skip TEST_STRATEGY (parallel)
),
WorkflowStage.TEST_STRATEGY: StageMetadata(
    name="Test Strategy",
    description="Define testing approach and criteria",
    allowed_personas=["builder", "developer", "reviewer"],
    required_artifacts=["test_strategy.md"],
    optional=False,
    next_stages=[WorkflowStage.PLAN],  # UNCHANGED: Both converge at PLAN
),
```

---

## 🚫 Rejected Alternatives

### Alternative 1: Extend Existing `ParallelExecutor`

**Approach:** Add stage-level methods to the existing `ParallelExecutor`.

**Why Rejected:**
- Violates single responsibility principle
- `AgentTask` interface doesn't fit stage lifecycle
- Review iteration integration would be awkward
- Risk of breaking existing agent-level parallelism

### Alternative 2: Hardcoded Parallel Groups

**Approach:** Hardcode `RESEARCH || TEST_STRATEGY` in `execution_loop.py`.

**Why Rejected:**
- Specification requires configurable groups via `stages.yaml`
- Harder to add new groups in future
- Less maintainable

### Alternative 3: Thread-Based Parallelism

**Approach:** Use `concurrent.futures.ThreadPoolExecutor` instead of `asyncio`.

**Why Rejected:**
- Inconsistent with codebase's async patterns
- SDK client is async-native
- Would require sync→async bridging

---

## 📝 Task Implementation Requests

### High Priority (Core Feature)

1. **Create `ParallelStageExecutor` class**
   - File: `src/teambot/orchestration/parallel_stage_executor.py`
   - Implement concurrent stage execution with failure isolation
   - Delegate to `ExecutionLoop` stage methods

2. **Update `stages.yaml` schema**
   - Add `parallel_groups` section
   - Configure `post_spec_review` group with `RESEARCH` + `TEST_STRATEGY`

3. **Update `stage_config.py` parsing**
   - Add `ParallelGroupConfig` dataclass
   - Parse `parallel_groups` in `_parse_configuration()`
   - Add `parallel_groups` field to `StagesConfiguration`

4. **Integrate into `ExecutionLoop`**
   - Add `_get_parallel_group_for_stage()` method
   - Add `_execute_parallel_group()` method
   - Modify main loop to check for parallel groups

5. **Update `stages.py` transitions**
   - Modify `SPEC_REVIEW.next_stages` to include both `RESEARCH` and `TEST_STRATEGY`
   - Ensure `RESEARCH` and `TEST_STRATEGY` both converge at `PLAN`

### Medium Priority (State & Resume)

6. **Update state persistence**
   - Add `parallel_group_status` to saved state
   - Update `_save_state()` to include group tracking
   - Update `resume()` for backward compatibility

7. **Implement resume mid-group**
   - Detect incomplete groups on resume
   - Only re-execute incomplete stages
   - Reconstruct group status from `stage_outputs`

### Lower Priority (Polish)

8. **Add progress events**
   - New event types: `parallel_group_start`, `parallel_stage_start`, etc.
   - Update `progress.py` callback handler

9. **Update visualization**
   - Modify console display for concurrent stages
   - Show parallel group progress

### Testing Tasks

10. **Unit tests for `ParallelStageExecutor`**
    - Test concurrent execution
    - Test partial failures (one stage fails)
    - Test all failures
    - Test progress callbacks

11. **Integration tests**
    - Full workflow with parallel groups
    - Resume mid-parallel-group
    - Backward compatibility (old state files)

12. **Config parsing tests**
    - Valid `parallel_groups` config
    - Missing/invalid fields
    - Empty groups

---

## 🔍 Potential Next Research

1. **Performance Benchmarking**: Measure actual time savings from parallel execution
2. **Additional Parallel Groups**: Research other stage combinations that could run in parallel (e.g., `TEST` || `ACCEPTANCE_TEST` if tests are independent)
3. **Max Concurrency Tuning**: Research optimal `max_concurrent` value based on typical LLM rate limits
4. **Failure Recovery**: Research partial retry strategies (re-run only failed stages)

---

## 📌 References

### File References with Line Numbers

| File | Lines | Purpose |
|------|-------|---------|
| `stages.yaml` | 372-387 | Stage order definition |
| `stages.py` | 46-160 | `STAGE_METADATA` definitions |
| `stage_config.py` | 37-45, 108-180 | Config dataclasses, parsing |
| `execution_loop.py` | 131-208, 857-950 | Main loop, state persistence |
| `parallel_executor.py` | 29-102 | Existing agent-level parallelism |
| `review_iterator.py` | 48-208 | Review iteration loop |
| `test_parallel_executor.py` | 1-240 | Test patterns reference |
| `test_execution_loop.py` | 1-350 | State/resume test patterns |

### External References

- Python asyncio documentation: https://docs.python.org/3/library/asyncio.html
- asyncio.gather() behavior with exceptions: return_exceptions=True pattern

---

## ✅ Research Validation

```
RESEARCH_VALIDATION: PASS
- Document: CREATED ✅
- Placeholders: 0 remaining ✅
- Technical Approach: DOCUMENTED ✅
- Entry Points: 2 traced, 2 covered ✅
- Test Infrastructure: RESEARCHED ✅
- Implementation Ready: YES ✅
```

