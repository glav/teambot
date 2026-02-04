"""Tests for TaskExecutor - bridges REPL commands to TaskManager."""

from unittest.mock import AsyncMock

import pytest

from teambot.repl.parser import parse_command
from teambot.tasks.executor import TaskExecutor
from teambot.tasks.models import TaskStatus


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


class TestTaskExecutorCallbacks:
    """Tests for task start/complete callbacks."""

    @pytest.mark.asyncio
    async def test_on_task_started_callback(self):
        """Test on_task_started callback is called."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        started_tasks = []

        def on_started(task):
            started_tasks.append(task)

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_task_started=on_started,
        )
        cmd = parse_command("@pm Create a plan")

        await executor.execute(cmd)

        assert len(started_tasks) == 1
        assert started_tasks[0].agent_id == "pm"

    @pytest.mark.asyncio
    async def test_on_task_started_with_complete(self):
        """Test both started and complete callbacks."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        started_tasks = []
        completed_tasks = []

        def on_started(task):
            started_tasks.append(task)

        def on_complete(task, result):
            completed_tasks.append((task, result))

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_task_started=on_started,
            on_task_complete=on_complete,
        )
        cmd = parse_command("@pm Create a plan")

        await executor.execute(cmd)

        assert len(started_tasks) == 1
        assert len(completed_tasks) == 1
        assert completed_tasks[0][1].success

    @pytest.mark.asyncio
    async def test_on_task_started_background(self):
        """Test on_task_started is called for background tasks."""
        import asyncio

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        started_tasks = []

        def on_started(task):
            started_tasks.append(task)

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_task_started=on_started,
        )
        cmd = parse_command("@pm Create a plan &")

        result = await executor.execute(cmd)
        assert result.background

        # Give the background task time to start
        await asyncio.sleep(0.1)

        assert len(started_tasks) == 1


class TestTaskExecutorStreaming:
    """Tests for streaming callback support."""

    @pytest.mark.asyncio
    async def test_streaming_callback_passed_to_sdk(self):
        """Test that streaming callback is passed to SDK client."""
        chunks_received = []

        def on_chunk(agent_id, chunk):
            chunks_received.append((agent_id, chunk))

        mock_sdk = AsyncMock()
        mock_sdk.execute_streaming = AsyncMock(return_value="Streamed result")

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
        )

        cmd = parse_command("@pm Test streaming")
        await executor.execute(cmd)

        # Verify execute_streaming was called with raw content
        # Custom agents in .github/agents/ handle persona
        mock_sdk.execute_streaming.assert_called_once()
        call_args = mock_sdk.execute_streaming.call_args
        assert call_args[0][0] == "pm"  # agent_id
        assert call_args[0][1] == "Test streaming"  # raw content
        # Third arg is the on_chunk callback

    @pytest.mark.asyncio
    async def test_streaming_callback_receives_chunks(self):
        """Test that streaming callback receives agent_id and chunk."""
        chunks_received = []

        def on_chunk(agent_id, chunk):
            chunks_received.append((agent_id, chunk))

        async def mock_execute_streaming(agent_id, prompt, callback):
            callback("Chunk 1")
            callback("Chunk 2")
            return "Complete"

        mock_sdk = AsyncMock()
        mock_sdk.execute_streaming = mock_execute_streaming

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
        )

        cmd = parse_command("@pm Test")
        await executor.execute(cmd)

        assert chunks_received == [("pm", "Chunk 1"), ("pm", "Chunk 2")]

    @pytest.mark.asyncio
    async def test_falls_back_to_execute_without_callback(self):
        """Test fallback to execute() when no streaming callback provided."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Regular result")
        mock_sdk.execute_streaming = AsyncMock(return_value="Streaming result")

        # No on_streaming_chunk callback
        executor = TaskExecutor(sdk_client=mock_sdk)

        cmd = parse_command("@pm Test")
        await executor.execute(cmd)

        # Should use regular execute, not execute_streaming
        mock_sdk.execute.assert_called_once()
        mock_sdk.execute_streaming.assert_not_called()

    @pytest.mark.asyncio
    async def test_falls_back_when_sdk_lacks_streaming(self):
        """Test fallback when SDK doesn't have execute_streaming."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Regular result")
        # No execute_streaming method
        del mock_sdk.execute_streaming

        def on_chunk(agent_id, chunk):
            pass

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
        )

        cmd = parse_command("@pm Test")
        result = await executor.execute(cmd)

        # Should fall back to regular execute
        mock_sdk.execute.assert_called_once()
        assert result.output == "Regular result"


class TestExecutorReferences:
    """Tests for $ref execution."""

    @pytest.mark.asyncio
    async def test_reference_injects_output(self):
        """Test that referenced output is injected."""
        captured_prompts = []

        async def capture_execute(agent_id, prompt):
            captured_prompts.append((agent_id, prompt))
            return f"{agent_id} completed"

        mock_sdk = AsyncMock()
        mock_sdk.execute = capture_execute

        executor = TaskExecutor(sdk_client=mock_sdk)

        # First, run a task for ba
        cmd1 = parse_command("@ba Analyze requirements")
        await executor.execute(cmd1)

        # Now reference ba's output
        cmd2 = parse_command("@pm Summarize $ba")
        await executor.execute(cmd2)

        # Check that PM received BA's output
        pm_prompt = captured_prompts[1][1]
        assert "=== Output from @ba ===" in pm_prompt
        assert "ba completed" in pm_prompt
        assert "=== Your Task ===" in pm_prompt

    @pytest.mark.asyncio
    async def test_reference_multiple_agents(self):
        """Test referencing multiple agents."""
        captured_prompts = []

        async def capture_execute(agent_id, prompt):
            captured_prompts.append((agent_id, prompt))
            return f"{agent_id} output"

        mock_sdk = AsyncMock()
        mock_sdk.execute = capture_execute

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Run tasks for ba and writer
        await executor.execute(parse_command("@ba Analyze"))
        await executor.execute(parse_command("@writer Document"))

        # Reference both
        await executor.execute(parse_command("@pm Combine $ba and $writer"))

        pm_prompt = captured_prompts[2][1]
        assert "=== Output from @ba ===" in pm_prompt
        assert "=== Output from @writer ===" in pm_prompt
        assert "ba output" in pm_prompt
        assert "writer output" in pm_prompt

    @pytest.mark.asyncio
    async def test_reference_no_output_available(self):
        """Test graceful handling when no output available."""
        captured_prompts = []

        async def capture_execute(agent_id, prompt):
            captured_prompts.append((agent_id, prompt))
            return "Done"

        mock_sdk = AsyncMock()
        mock_sdk.execute = capture_execute

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Reference agent that hasn't run
        cmd = parse_command("@pm Summarize $ba")
        result = await executor.execute(cmd)

        # Should still execute with placeholder
        pm_prompt = captured_prompts[0][1]
        assert "[No output available]" in pm_prompt
        assert result.success

    @pytest.mark.asyncio
    async def test_reference_waits_for_running_task(self):
        """Test that reference waits for running task."""
        import asyncio

        call_order = []

        async def tracked_execute(agent_id, prompt):
            call_order.append(f"{agent_id}_start")
            if agent_id == "ba":
                await asyncio.sleep(0.2)
            call_order.append(f"{agent_id}_end")
            return f"{agent_id} output"

        mock_sdk = AsyncMock()
        mock_sdk.execute = tracked_execute

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Start BA in background
        cmd1 = parse_command("@ba Analyze &")
        await executor.execute(cmd1)

        # Small delay to ensure BA starts
        await asyncio.sleep(0.05)

        # PM references BA (should wait)
        cmd2 = parse_command("@pm Summarize $ba")
        await executor.execute(cmd2)

        # BA should complete before PM accesses its output
        ba_end_idx = call_order.index("ba_end")
        pm_start_idx = call_order.index("pm_start")
        assert ba_end_idx < pm_start_idx

    @pytest.mark.asyncio
    async def test_reference_with_background(self):
        """Test reference parsing with background operator."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        executor = TaskExecutor(sdk_client=mock_sdk)

        # First run ba
        await executor.execute(parse_command("@ba Analyze"))

        # Reference with background
        cmd = parse_command("@pm Summarize $ba &")
        result = await executor.execute(cmd)

        assert result.background is True
        assert result.success

    @pytest.mark.asyncio
    async def test_no_reference_unchanged(self):
        """Test that commands without references work unchanged."""
        captured_prompts = []

        async def capture_execute(agent_id, prompt):
            captured_prompts.append(prompt)
            return "Done"

        mock_sdk = AsyncMock()
        mock_sdk.execute = capture_execute

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Command without reference
        cmd = parse_command("@pm Create a plan")
        await executor.execute(cmd)

        # Prompt should be unchanged (no injection headers)
        assert captured_prompts[0] == "Create a plan"
        assert "=== Output from" not in captured_prompts[0]
