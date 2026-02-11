"""Tests for ParallelStageExecutor (TDD)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor
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
        loop.stages_config.get_stage_agents = MagicMock(return_value={"work": "builder-1", "review": None})
        loop.stage_outputs = {}
        return loop

    @pytest.fixture
    def executor(self) -> ParallelStageExecutor:
        """Create ParallelStageExecutor instance."""
        return ParallelStageExecutor(max_concurrent=2)

    @pytest.mark.asyncio
    async def test_execute_parallel_empty_stages(self, mock_execution_loop: MagicMock) -> None:
        """Empty stage list returns empty dict."""
        from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor

        executor = ParallelStageExecutor(max_concurrent=2)
        result = await executor.execute_parallel([], mock_execution_loop)

        assert result == {}
        mock_execution_loop._execute_work_stage.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_parallel_single_stage(self, mock_execution_loop: MagicMock) -> None:
        """Single stage executes and returns result."""
        from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor

        executor = ParallelStageExecutor(max_concurrent=2)
        stages = [WorkflowStage.RESEARCH]

        results = await executor.execute_parallel(stages, mock_execution_loop)

        assert len(results) == 1
        assert results[WorkflowStage.RESEARCH].success is True
        assert results[WorkflowStage.RESEARCH].output == "Stage output"

    @pytest.mark.asyncio
    async def test_execute_parallel_multiple_stages(self, mock_execution_loop: MagicMock) -> None:
        """Multiple stages execute concurrently."""
        from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor

        executor = ParallelStageExecutor(max_concurrent=2)
        stages = [WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY]

        results = await executor.execute_parallel(stages, mock_execution_loop)

        assert len(results) == 2
        assert results[WorkflowStage.RESEARCH].success is True
        assert results[WorkflowStage.TEST_STRATEGY].success is True
        assert mock_execution_loop._execute_work_stage.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_parallel_partial_failure(self, mock_execution_loop: MagicMock) -> None:
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

    @pytest.mark.asyncio
    async def test_execute_parallel_failed_event_includes_agent(
        self, mock_execution_loop: MagicMock
    ) -> None:
        """Failed stage event includes agent information."""
        from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor

        mock_execution_loop._execute_work_stage.side_effect = Exception("Stage failed")
        
        events: list[tuple[str, dict]] = []

        def on_progress(event_type: str, data: dict) -> None:
            events.append((event_type, data))

        executor = ParallelStageExecutor(max_concurrent=2)
        stages = [WorkflowStage.RESEARCH]

        await executor.execute_parallel(stages, mock_execution_loop, on_progress)

        # Check for failed event
        failed_events = [e for e in events if e[0] == "parallel_stage_failed"]
        assert len(failed_events) == 2  # One during execution, one after gathering
        # Verify agent field is present in both
        for event_type, data in failed_events:
            assert "agent" in data
            assert data["agent"] == "builder-1"
            assert "error" in data

    @pytest.mark.asyncio
    async def test_execute_parallel_respects_concurrency(
        self, mock_execution_loop: MagicMock
    ) -> None:
        """Executor respects max_concurrent limit."""
        from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor

        concurrent_count = 0
        max_observed = 0

        async def track_concurrency(stage: WorkflowStage, on_progress: object = None) -> str:
            nonlocal concurrent_count, max_observed
            concurrent_count += 1
            max_observed = max(max_observed, concurrent_count)
            await asyncio.sleep(0.05)  # Simulate work
            concurrent_count -= 1
            return "output"

        mock_execution_loop._execute_work_stage = track_concurrency

        executor = ParallelStageExecutor(max_concurrent=1)  # Limit to 1
        stages = [WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY]

        await executor.execute_parallel(stages, mock_execution_loop)

        assert max_observed == 1  # Never more than 1 concurrent

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
        # Verify agent field is present
        for event_type, data in start_events:
            assert "agent" in data
            assert data["agent"] == "builder-1"

        # Check for complete events
        complete_events = [e for e in events if e[0] == "parallel_stage_complete"]
        assert len(complete_events) == 2
        # Verify agent field is present
        for event_type, data in complete_events:
            assert "agent" in data
            assert data["agent"] == "builder-1"

    @pytest.mark.asyncio
    async def test_execute_parallel_failure_events_fire_once(
        self, mock_execution_loop: MagicMock
    ) -> None:
        """Failed stages fire parallel_stage_failed event exactly once."""
        from teambot.orchestration.parallel_stage_executor import ParallelStageExecutor

        events: list[tuple[str, dict]] = []

        def on_progress(event_type: str, data: dict) -> None:
            events.append((event_type, data))

        # First call succeeds, second fails
        mock_execution_loop._execute_work_stage.side_effect = [
            "Success output",
            Exception("Stage failed"),
        ]

        executor = ParallelStageExecutor(max_concurrent=2)
        stages = [WorkflowStage.RESEARCH, WorkflowStage.TEST_STRATEGY]

        await executor.execute_parallel(stages, mock_execution_loop, on_progress)

        # Check start events - should be 2 (one per stage)
        start_events = [e for e in events if e[0] == "parallel_stage_start"]
        assert len(start_events) == 2

        # Check complete events - should be 1 (only for successful stage)
        complete_events = [e for e in events if e[0] == "parallel_stage_complete"]
        assert len(complete_events) == 1

        # Check failed events - should be 1 (only for failed stage, NOT duplicated)
        failed_events = [e for e in events if e[0] == "parallel_stage_failed"]
        assert len(failed_events) == 1

        # Verify the failed event has correct stage info
        assert failed_events[0][1]["stage"] in ["RESEARCH", "TEST_STRATEGY"]


class TestStageResult:
    """Tests for StageResult dataclass."""

    def test_stage_result_success(self) -> None:
        """StageResult with success state."""
        from teambot.orchestration.parallel_stage_executor import StageResult

        result = StageResult(
            stage=WorkflowStage.RESEARCH,
            success=True,
            output="Test output",
        )

        assert result.stage == WorkflowStage.RESEARCH
        assert result.success is True
        assert result.output == "Test output"
        assert result.error is None

    def test_stage_result_failure(self) -> None:
        """StageResult with failure state."""
        from teambot.orchestration.parallel_stage_executor import StageResult

        result = StageResult(
            stage=WorkflowStage.RESEARCH,
            success=False,
            error="Something went wrong",
        )

        assert result.success is False
        assert result.error == "Something went wrong"
