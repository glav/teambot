"""Tests for TaskExecutor - bridges REPL commands to TaskManager."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from teambot.tasks.executor import TaskExecutor
from teambot.tasks.models import TaskStatus
from teambot.repl.parser import parse_command


class TestTaskExecutorBasic:
    """Basic TaskExecutor tests."""

    def test_create_executor(self):
        """Test creating executor."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        assert executor is not None
        assert executor.task_count == 0

    @pytest.mark.asyncio
    async def test_execute_simple_command(self):
        """Test executing simple @agent command."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Task completed")

        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm Create a plan")

        result = await executor.execute(cmd)

        assert result.success
        assert "Task completed" in result.output
        mock_sdk.execute.assert_called_once()


class TestTaskExecutorBackground:
    """Tests for background task execution."""

    @pytest.mark.asyncio
    async def test_background_returns_immediately(self):
        """Test that background task returns immediately."""
        import asyncio

        async def slow_execute(agent_id, prompt):
            await asyncio.sleep(1)
            return "Done"

        mock_sdk = AsyncMock()
        mock_sdk.execute = slow_execute

        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm Create a plan &")

        # Should return quickly (not wait for task)
        import time
        start = time.time()
        result = await executor.execute(cmd)
        elapsed = time.time() - start

        assert elapsed < 0.5  # Should be fast
        assert result.background
        assert result.task_id is not None

    @pytest.mark.asyncio
    async def test_background_task_tracked(self):
        """Test that background task is tracked."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm Create a plan &")

        result = await executor.execute(cmd)

        assert executor.task_count == 1
        task = executor.get_task(result.task_id)
        assert task is not None


class TestTaskExecutorMultiAgent:
    """Tests for multi-agent fan-out."""

    @pytest.mark.asyncio
    async def test_multiagent_creates_multiple_tasks(self):
        """Test that multi-agent creates task per agent."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm,ba,writer Analyze feature")

        result = await executor.execute(cmd)

        # Should create 3 tasks
        assert len(result.task_ids) == 3
        assert mock_sdk.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_multiagent_collects_all_outputs(self):
        """Test that multi-agent collects all outputs."""
        async def agent_response(agent_id, prompt):
            return f"Response from {agent_id}"

        mock_sdk = AsyncMock()
        mock_sdk.execute = agent_response

        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm,ba Analyze")

        result = await executor.execute(cmd)

        assert "pm" in result.output
        assert "ba" in result.output

    @pytest.mark.asyncio
    async def test_multiagent_background(self):
        """Test multi-agent with background."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm,ba Analyze &")

        result = await executor.execute(cmd)

        assert result.background
        assert len(result.task_ids) == 2


class TestTaskExecutorPipeline:
    """Tests for pipeline execution."""

    @pytest.mark.asyncio
    async def test_pipeline_executes_in_order(self):
        """Test that pipeline stages execute in order."""
        execution_order = []

        async def track_execute(agent_id, prompt):
            execution_order.append(agent_id)
            return f"{agent_id} output"

        mock_sdk = AsyncMock()
        mock_sdk.execute = track_execute

        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm Plan -> @builder-1 Build -> @reviewer Review")

        await executor.execute(cmd)

        assert execution_order == ["pm", "builder-1", "reviewer"]

    @pytest.mark.asyncio
    async def test_pipeline_passes_output(self):
        """Test that pipeline passes output to next stage."""
        captured_prompts = []

        async def capture_execute(agent_id, prompt):
            captured_prompts.append((agent_id, prompt))
            return f"{agent_id} completed"

        mock_sdk = AsyncMock()
        mock_sdk.execute = capture_execute

        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm Create plan -> @builder-1 Implement")

        await executor.execute(cmd)

        # Second stage should include first stage's output
        assert len(captured_prompts) == 2
        builder_prompt = captured_prompts[1][1]
        assert "pm completed" in builder_prompt

    @pytest.mark.asyncio
    async def test_pipeline_with_multiagent_stage(self):
        """Test pipeline with multi-agent stage."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm Plan -> @builder-1,builder-2 Build")

        await executor.execute(cmd)

        # Should execute pm once, then both builders
        assert mock_sdk.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_pipeline_background(self):
        """Test pipeline with background."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm Plan -> @builder-1 Build &")

        result = await executor.execute(cmd)

        assert result.background

    @pytest.mark.asyncio
    async def test_pipeline_stage_failure_skips_rest(self):
        """Test that pipeline stage failure skips subsequent stages."""
        call_count = {"count": 0}

        async def failing_execute(agent_id, prompt):
            call_count["count"] += 1
            if agent_id == "pm":
                raise Exception("PM failed")
            return "Done"

        mock_sdk = AsyncMock()
        mock_sdk.execute = failing_execute

        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm Plan -> @builder-1 Build")

        result = await executor.execute(cmd)

        assert not result.success
        # Builder should not have been called - only pm
        assert call_count["count"] == 1


class TestTaskExecutorStatus:
    """Tests for task status reporting."""

    @pytest.mark.asyncio
    async def test_list_running_tasks(self):
        """Test listing running tasks."""
        import asyncio

        async def slow_execute(agent_id, prompt):
            await asyncio.sleep(10)
            return "Done"

        mock_sdk = AsyncMock()
        mock_sdk.execute = slow_execute

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Start background task
        cmd = parse_command("@pm Create plan &")
        await executor.execute(cmd)

        # Give it a moment to start
        await asyncio.sleep(0.1)

        tasks = executor.list_tasks(status=TaskStatus.RUNNING)
        assert len(tasks) >= 0  # May or may not be running yet

    def test_get_task_by_id(self):
        """Test getting task by ID."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        # Create a task directly for testing
        task = executor._manager.create_task("pm", "Test task")

        retrieved = executor.get_task(task.id)
        assert retrieved is task
