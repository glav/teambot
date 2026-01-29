"""Tests for ParallelExecutor (Code-First)."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock

from teambot.orchestration.parallel_executor import (
    ParallelExecutor,
    AgentTask,
    TaskResult,
    partition_tasks,
)


class TestParallelExecutor:
    """Tests for ParallelExecutor class."""

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client."""
        client = AsyncMock()
        client.execute_streaming.return_value = "Task completed"
        return client

    @pytest.fixture
    def executor(self, mock_sdk_client: AsyncMock) -> ParallelExecutor:
        """Create ParallelExecutor instance."""
        return ParallelExecutor(mock_sdk_client, max_concurrent=2)

    @pytest.mark.asyncio
    async def test_execute_parallel_empty_tasks(
        self, executor: ParallelExecutor
    ) -> None:
        """Empty task list returns empty dict."""
        result = await executor.execute_parallel([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_execute_parallel_single_task(
        self, executor: ParallelExecutor, mock_sdk_client: AsyncMock
    ) -> None:
        """Single task executes successfully."""
        tasks = [AgentTask(agent_id="builder-1", prompt="Do task 1")]

        results = await executor.execute_parallel(tasks)

        assert "builder-1" in results
        assert results["builder-1"].success is True
        assert results["builder-1"].output == "Task completed"

    @pytest.mark.asyncio
    async def test_execute_parallel_multiple_tasks(
        self, executor: ParallelExecutor, mock_sdk_client: AsyncMock
    ) -> None:
        """Multiple tasks execute in parallel."""
        mock_sdk_client.execute_streaming.side_effect = [
            "Output 1",
            "Output 2",
        ]
        tasks = [
            AgentTask(agent_id="builder-1", prompt="Task 1"),
            AgentTask(agent_id="builder-2", prompt="Task 2"),
        ]

        results = await executor.execute_parallel(tasks)

        assert len(results) == 2
        assert results["builder-1"].success is True
        assert results["builder-2"].success is True

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

    @pytest.mark.asyncio
    async def test_execute_parallel_respects_concurrency_limit(
        self, mock_sdk_client: AsyncMock
    ) -> None:
        """Concurrency limit is respected."""
        executor = ParallelExecutor(mock_sdk_client, max_concurrent=1)
        execution_order: list[str] = []

        async def track_execution(agent_id: str, prompt: str, callback: None) -> str:
            execution_order.append(f"start-{agent_id}")
            await asyncio.sleep(0.01)  # Simulate work
            execution_order.append(f"end-{agent_id}")
            return "Done"

        mock_sdk_client.execute_streaming.side_effect = track_execution

        tasks = [
            AgentTask(agent_id="builder-1", prompt="Task 1"),
            AgentTask(agent_id="builder-2", prompt="Task 2"),
        ]

        await executor.execute_parallel(tasks)

        # With max_concurrent=1, tasks should be sequential
        # Start and end of first should come before start of second
        assert execution_order.index("end-builder-1") < execution_order.index(
            "start-builder-2"
        )

    @pytest.mark.asyncio
    async def test_execute_parallel_progress_callback(
        self, executor: ParallelExecutor, mock_sdk_client: AsyncMock
    ) -> None:
        """Progress callback is called for each event."""
        progress_calls: list[tuple[str, dict]] = []

        def on_progress(event_type: str, data: dict) -> None:
            progress_calls.append((event_type, data))

        tasks = [AgentTask(agent_id="builder-1", prompt="Task", description="Test")]

        await executor.execute_parallel(tasks, on_progress=on_progress)

        # Should have "agent_running" and "agent_complete" events
        events = [c[0] for c in progress_calls]
        assert "agent_running" in events
        assert "agent_complete" in events
        
        # Verify data structure
        running_event = next(c for c in progress_calls if c[0] == "agent_running")
        assert running_event[1]["agent_id"] == "builder-1"
        assert running_event[1]["task"] == "Test"

    @pytest.mark.asyncio
    async def test_execute_parallel_cancellation_handled(
        self, mock_sdk_client: AsyncMock
    ) -> None:
        """Cancellation is handled - returns empty result for cancelled tasks."""
        executor = ParallelExecutor(mock_sdk_client, max_concurrent=2)
        progress_calls: list[tuple[str, dict]] = []

        def on_progress(event_type: str, data: dict) -> None:
            progress_calls.append((event_type, data))

        async def cancel_after_delay(*args: object, **kwargs: object) -> str:
            await asyncio.sleep(0.01)
            raise asyncio.CancelledError()

        mock_sdk_client.execute_streaming.side_effect = cancel_after_delay

        tasks = [AgentTask(agent_id="builder-1", prompt="Task")]

        # CancelledError is re-raised from execute_parallel
        with pytest.raises(asyncio.CancelledError):
            await executor.execute_parallel(tasks, on_progress=on_progress)

        # Progress callback should have been called
        events = [c[0] for c in progress_calls]
        assert "agent_running" in events
        assert "agent_cancelled" in events


class TestPartitionTasks:
    """Tests for partition_tasks function."""

    def test_partition_empty_tasks(self) -> None:
        """Empty task list returns empty result."""
        result = partition_tasks([])
        assert result == []

    def test_partition_single_task(self) -> None:
        """Single task goes to first agent."""
        result = partition_tasks(["Task 1"])
        assert len(result) == 1
        assert result[0].agent_id == "builder-1"
        assert result[0].prompt == "Task 1"

    def test_partition_two_tasks(self) -> None:
        """Two tasks distributed to two agents."""
        result = partition_tasks(["Task 1", "Task 2"])
        assert len(result) == 2
        assert result[0].agent_id == "builder-1"
        assert result[1].agent_id == "builder-2"

    def test_partition_three_tasks_round_robin(self) -> None:
        """Three tasks distributed round-robin."""
        result = partition_tasks(["Task 1", "Task 2", "Task 3"])
        assert len(result) == 3
        assert result[0].agent_id == "builder-1"
        assert result[1].agent_id == "builder-2"
        assert result[2].agent_id == "builder-1"  # Round robin back

    def test_partition_custom_agents(self) -> None:
        """Custom agents can be specified."""
        result = partition_tasks(
            ["Task 1", "Task 2", "Task 3"], agents=["agent-a", "agent-b", "agent-c"]
        )
        assert result[0].agent_id == "agent-a"
        assert result[1].agent_id == "agent-b"
        assert result[2].agent_id == "agent-c"

    def test_partition_truncates_long_descriptions(self) -> None:
        """Long task descriptions are truncated."""
        long_task = "A" * 100
        result = partition_tasks([long_task])
        assert len(result[0].description) <= 53  # 50 + "..."
        assert result[0].description.endswith("...")


class TestAgentTask:
    """Tests for AgentTask dataclass."""

    def test_default_description_is_empty(self) -> None:
        """Default description is empty string."""
        task = AgentTask(agent_id="test", prompt="prompt")
        assert task.description == ""


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_default_output_is_empty(self) -> None:
        """Default output is empty string."""
        result = TaskResult(success=True)
        assert result.output == ""
        assert result.error is None

    def test_failure_with_error(self) -> None:
        """Failure result with error message."""
        result = TaskResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.error == "Something went wrong"
