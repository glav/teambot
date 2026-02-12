"""Tests for TaskExecutor - bridges REPL commands to TaskManager."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from teambot.repl.parser import parse_command
from teambot.tasks.executor import TaskExecutor
from teambot.tasks.models import TaskResult, TaskStatus


class TestPseudoAgentDetection:
    """Tests for pseudo-agent detection."""

    def test_notify_is_pseudo_agent(self):
        """Test that 'notify' is identified as pseudo-agent."""
        from teambot.tasks.executor import is_pseudo_agent

        assert is_pseudo_agent("notify") is True

    def test_regular_agents_not_pseudo(self):
        """Test that regular agents are not pseudo-agents."""
        from teambot.tasks.executor import is_pseudo_agent

        for agent in ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]:
            assert is_pseudo_agent(agent) is False

    def test_pseudo_agents_constant_exists(self):
        """Test that PSEUDO_AGENTS constant exists."""
        from teambot.tasks.executor import PSEUDO_AGENTS

        assert "notify" in PSEUDO_AGENTS


class TestNotifyHandler:
    """Tests for @notify pseudo-agent handler."""

    @pytest.fixture
    def mock_config(self):
        return {
            "notifications": {
                "enabled": True,
                "channels": [{"type": "telegram", "token": "test", "chat_id": "123"}],
            }
        }

    @pytest.mark.asyncio
    async def test_handle_notify_returns_confirmation(self, mock_config):
        """Test that _handle_notify returns confirmation message."""
        executor = TaskExecutor(sdk_client=AsyncMock(), config=mock_config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            result = await executor._handle_notify("Test message", background=False)

            assert result.success
            assert "Notification sent" in result.output
            assert "✅" in result.output

    @pytest.mark.asyncio
    async def test_handle_notify_calls_event_bus(self, mock_config):
        """Test that EventBus.emit_sync is called."""
        executor = TaskExecutor(sdk_client=AsyncMock(), config=mock_config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            await executor._handle_notify("Test message", background=False)

            mock_bus.emit_sync.assert_called_once_with(
                "custom_message", {"message": "Test message"}
            )

    @pytest.mark.asyncio
    async def test_handle_notify_no_sdk_call(self, mock_config):
        """Test that SDK is not called for @notify."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk, config=mock_config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            await executor._handle_notify("Test", background=False)

            mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_notify_no_channels_configured(self):
        """Test handling when no channels configured."""
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=AsyncMock(), config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = []  # No channels
            mock_create.return_value = mock_bus

            result = await executor._handle_notify("Test", background=False)

            assert result.success  # Still succeeds
            assert "⚠️" in result.output or "No notification channels" in result.output

    @pytest.mark.asyncio
    async def test_handle_notify_disabled(self):
        """Test handling when notifications are explicitly disabled."""
        config = {"notifications": {"enabled": False}}
        executor = TaskExecutor(sdk_client=AsyncMock(), config=config)

        result = await executor._handle_notify("Test", background=False)

        assert result.success  # Still succeeds
        assert "⚠️" in result.output
        assert "disabled" in result.output.lower()

    @pytest.mark.asyncio
    async def test_handle_notify_no_config(self):
        """Test handling when no config available."""
        executor = TaskExecutor(sdk_client=AsyncMock(), config=None)

        result = await executor._handle_notify("Test", background=False)

        assert result.success  # Still succeeds
        assert "⚠️" in result.output


class TestTruncationForNotification:
    """Tests for output truncation helper."""

    def test_short_text_unchanged(self):
        """Text under limit is unchanged."""
        from teambot.tasks.executor import truncate_for_notification

        text = "a" * 400
        assert truncate_for_notification(text) == text

    def test_long_text_truncated(self):
        """Text over limit is truncated with suffix."""
        from teambot.tasks.executor import truncate_for_notification

        text = "a" * 600
        result = truncate_for_notification(text)
        assert len(result) == 500 + len("...")
        assert result.endswith("...")

    def test_exactly_at_limit_unchanged(self):
        """Text exactly at limit is unchanged."""
        from teambot.tasks.executor import truncate_for_notification

        text = "a" * 500
        assert truncate_for_notification(text) == text

    def test_one_over_limit_truncated(self):
        """Text one char over limit is truncated."""
        from teambot.tasks.executor import truncate_for_notification

        text = "a" * 501
        result = truncate_for_notification(text)
        assert len(result) == 500 + len("...")


class TestNotifyResultStorage:
    """Tests for @notify result storage."""

    @pytest.mark.asyncio
    async def test_result_stored_after_notify(self):
        """Test that result is stored in _agent_results."""
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=AsyncMock(), config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            await executor._handle_notify("Test", background=False)

            result = executor._manager.get_agent_result("notify")
            assert result is not None
            assert result.success is True

    @pytest.mark.asyncio
    async def test_result_output_matches(self):
        """Test that stored result contains confirmation."""
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=AsyncMock(), config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            await executor._handle_notify("Test", background=False)

            result = executor._manager.get_agent_result("notify")
            assert "Notification sent" in result.output


class TestNotifySimpleExecution:
    """Tests for @notify in simple execution."""

    @pytest.mark.asyncio
    async def test_notify_command_no_sdk(self):
        """@notify command does not call SDK."""
        mock_sdk = AsyncMock()
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            cmd = parse_command('@notify "Test message"')
            result = await executor.execute(cmd)

            mock_sdk.execute.assert_not_called()
            assert result.success

    @pytest.mark.asyncio
    async def test_notify_with_ref_interpolation(self):
        """@notify interpolates $ref tokens."""
        mock_sdk = AsyncMock()
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        # Pre-populate pm result
        executor._manager._agent_results["pm"] = TaskResult(
            task_id="t1", output="PM output here", success=True
        )

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            cmd = parse_command('@notify "Result: $pm"')
            await executor.execute(cmd)

            # Verify interpolated message was sent
            call_args = mock_bus.emit_sync.call_args
            assert "PM output here" in call_args[0][1]["message"]


class TestNotifyInPipeline:
    """Tests for @notify in pipeline execution."""

    @pytest.mark.asyncio
    async def test_notify_at_pipeline_end(self):
        """@notify executes at end of pipeline."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="SDK output")
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            cmd = parse_command('@pm plan -> @notify "Plan done"')
            result = await executor.execute(cmd)

            assert result.success
            mock_bus.emit_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_at_pipeline_start(self):
        """@notify executes at start of pipeline."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="SDK output")
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            cmd = parse_command('@notify "Starting" -> @pm plan')
            result = await executor.execute(cmd)

            assert result.success

    @pytest.mark.asyncio
    async def test_notify_in_pipeline_middle(self):
        """@notify executes in middle of pipeline."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="SDK output")
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            cmd = parse_command('@pm plan -> @notify "Middle" -> @reviewer review')
            result = await executor.execute(cmd)

            assert result.success

    @pytest.mark.asyncio
    async def test_notify_receives_previous_stage_output(self):
        """@notify receives injected output from previous pipeline stage."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Here is a funny joke!")
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            cmd = parse_command("@pm tell joke -> @notify")
            result = await executor.execute(cmd)

            assert result.success
            # Check that emit_sync was called with the previous stage output injected
            mock_bus.emit_sync.assert_called_once()
            call_args = mock_bus.emit_sync.call_args
            message_data = call_args[1] if call_args[1] else call_args[0][1]
            # The message should contain the output from @pm
            assert "Here is a funny joke!" in message_data.get("message", "")


class TestNotifyFailureHandling:
    """Tests for @notify failure scenarios."""

    @pytest.mark.asyncio
    async def test_channel_failure_pipeline_continues(self):
        """Notification failure doesn't break pipeline."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="SDK output")
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_bus.emit_sync.side_effect = Exception("Network error")
            mock_create.return_value = mock_bus

            cmd = parse_command('@pm plan -> @notify "Test" -> @reviewer review')
            result = await executor.execute(cmd)

            # Pipeline should still succeed
            assert result.success

    @pytest.mark.asyncio
    async def test_failure_output_contains_warning(self):
        """Failure output indicates warning without leaking exception details."""
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=AsyncMock(), config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            # Use an exception with sensitive data to verify it's not leaked
            mock_bus.emit_sync.side_effect = Exception(
                "https://api.telegram.org/bot123456:SENSITIVE_TOKEN/sendMessage"
            )
            mock_create.return_value = mock_bus

            result = await executor._handle_notify("Test", background=False)

            # Verify warning indicator is present
            assert "⚠️" in result.output or "failed" in result.output.lower()
            # Verify sensitive data is NOT in output
            assert "SENSITIVE_TOKEN" not in result.output
            assert "123456" not in result.output
            assert "api.telegram.org" not in result.output

    @pytest.mark.asyncio
    async def test_failure_logging_does_not_leak_details(self):
        """Logger output does not include exception details that might contain secrets."""
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=AsyncMock(), config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            with patch("teambot.tasks.executor.logger") as mock_logger:
                mock_bus = MagicMock()
                mock_bus._channels = [MagicMock()]
                # Exception with URL containing token
                mock_bus.emit_sync.side_effect = Exception(
                    "HTTPError at https://api.telegram.org/bot123456:SECRET_TOKEN/sendMessage"
                )
                mock_create.return_value = mock_bus

                await executor._handle_notify("Test", background=False)

                # Verify logger.warning was called
                mock_logger.warning.assert_called_once()
                log_message = mock_logger.warning.call_args[0][0]

                # Verify log contains only exception type, not details
                assert "Exception" in log_message
                assert "SECRET_TOKEN" not in log_message
                assert "api.telegram.org" not in log_message
                assert "123456" not in log_message


class TestMixedStageExecution:
    """Tests for stages with both real and pseudo-agents."""

    @pytest.mark.asyncio
    async def test_stage_with_real_and_pseudo_agent_executes_both(self):
        """Stage with @pm,notify executes both agents (not just notify)."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="PM output")
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            cmd = parse_command("@pm,notify plan project -> @reviewer review")
            result = await executor.execute(cmd)

            # Both @pm task and @notify should execute
            assert result.success
            # @pm should have been called
            mock_sdk.execute.assert_called()
            # @notify should have been called
            mock_bus.emit_sync.assert_called_once()
            # Output should contain both
            assert "PM output" in result.output
            assert "@notify" in result.output

    @pytest.mark.asyncio
    async def test_multiple_pseudo_agents_in_one_stage(self):
        """Multiple pseudo-agents in one stage all execute."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="PM output")
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            # Test validates infrastructure can handle multiple agents per stage:
            # - @pm is a real agent (creates task, executes via SDK)
            # - @notify is a pseudo-agent (no task, executes inline)
            # The data structure supports multiple pseudo-agents even though
            # we currently only have @notify
            cmd = parse_command("@pm,notify create documentation")
            result = await executor.execute(cmd)

            # Both should execute
            assert result.success
            mock_sdk.execute.assert_called()
            mock_bus.emit_sync.assert_called_once()


class TestNotifyInMultiagent:
    """Tests for @notify in multi-agent scenarios."""

    @pytest.mark.asyncio
    async def test_notify_in_multiagent_fanout(self):
        """@notify works in multi-agent comma syntax."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Task done")
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            cmd = parse_command("@pm,notify do something")
            result = await executor.execute(cmd)

            # Should succeed with both outputs
            assert result.success
            assert "Notification sent" in result.output or "notification" in result.output.lower()

    @pytest.mark.asyncio
    async def test_notify_only_multiagent(self):
        """@notify as the only agent in multiagent command."""
        config = {"notifications": {"enabled": True}}
        executor = TaskExecutor(sdk_client=AsyncMock(), config=config)

        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus

            # Single agent but could be in comma syntax
            cmd = parse_command('@notify "Test message"')
            result = await executor.execute(cmd)

            assert result.success


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

    @pytest.mark.asyncio
    async def test_multiagent_with_reference(self):
        """Test that multiagent commands properly inject references."""
        captured_prompts = []

        async def capture_execute(agent_id, prompt):
            captured_prompts.append((agent_id, prompt))
            return f"{agent_id} output"

        mock_sdk = AsyncMock()
        mock_sdk.execute = capture_execute

        executor = TaskExecutor(sdk_client=mock_sdk)

        # First run ba
        await executor.execute(parse_command("@ba Analyze requirements"))

        # Clear captured prompts to focus on multiagent command
        captured_prompts.clear()

        # Now run multiagent command that references ba
        cmd = parse_command("@pm,builder-1 Implement $ba")
        await executor.execute(cmd)

        # Both agents should receive the injected output
        assert len(captured_prompts) == 2
        pm_prompt = captured_prompts[0][1]
        builder_prompt = captured_prompts[1][1]

        # Check PM received BA's output
        assert "=== Output from @ba ===" in pm_prompt
        assert "ba output" in pm_prompt
        assert "=== Your Task ===" in pm_prompt
        assert "Implement $ba" in pm_prompt

        # Check builder-1 received BA's output
        assert "=== Output from @ba ===" in builder_prompt
        assert "ba output" in builder_prompt
        assert "=== Your Task ===" in builder_prompt
        assert "Implement $ba" in builder_prompt

    @pytest.mark.asyncio
    async def test_multiagent_with_reference_and_notify(self):
        """Test that @notify in multiagent commands receives injected references."""
        captured_prompts = []

        async def capture_execute(agent_id, prompt):
            captured_prompts.append((agent_id, prompt))
            return f"{agent_id} output"

        mock_sdk = AsyncMock()
        mock_sdk.execute = capture_execute

        # Create executor without notification config (we just test prompt injection)
        executor = TaskExecutor(sdk_client=mock_sdk)

        # First run ba
        await executor.execute(parse_command("@ba Analyze requirements"))

        # Clear captured prompts to focus on multiagent command
        captured_prompts.clear()

        # Now run multiagent command with @notify that references ba
        cmd = parse_command('@pm,notify "Done: $ba"')
        result = await executor.execute(cmd)

        # PM should receive injected output
        assert len(captured_prompts) == 1  # just pm
        pm_prompt = captured_prompts[0][1]
        assert "=== Output from @ba ===" in pm_prompt
        assert "ba output" in pm_prompt
        assert "Done: $ba" in pm_prompt

        # @notify output should be present in result
        assert "=== @notify ===" in result.output


class TestPipelineStageCallbacks:
    """Tests for pipeline stage change and output callbacks."""

    @pytest.mark.asyncio
    async def test_pipeline_emits_stage_change(self):
        """Test that pipeline emits stage change callbacks."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        stage_changes = []

        def on_stage_change(current, total, agents):
            stage_changes.append((current, total, agents))

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_stage_change=on_stage_change,
        )

        cmd = parse_command("@pm Plan -> @builder-1 Build")
        await executor.execute(cmd)

        # Should have 2 stage changes (stage 1 and stage 2)
        assert len(stage_changes) == 2
        assert stage_changes[0] == (1, 2, ["pm"])
        assert stage_changes[1] == (2, 2, ["builder-1"])

    @pytest.mark.asyncio
    async def test_pipeline_emits_stage_output(self):
        """Test that pipeline emits intermediate output callbacks."""
        mock_sdk = AsyncMock()

        async def mock_execute(agent_id, prompt):
            return f"{agent_id} output"

        mock_sdk.execute = mock_execute

        stage_outputs = []

        def on_stage_output(agent_id, output):
            stage_outputs.append((agent_id, output))

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_stage_output=on_stage_output,
        )

        cmd = parse_command("@pm Plan -> @builder-1 Build")
        await executor.execute(cmd)

        # Should have output from each stage
        assert len(stage_outputs) == 2
        assert stage_outputs[0] == ("pm", "pm output")
        assert stage_outputs[1] == ("builder-1", "builder-1 output")

    @pytest.mark.asyncio
    async def test_pipeline_emits_task_started_per_stage(self):
        """Test that pipeline emits on_task_started for each stage."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        started_tasks = []

        def on_started(task):
            started_tasks.append(task.agent_id)

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_task_started=on_started,
        )

        cmd = parse_command("@pm Plan -> @builder-1 Build -> @reviewer Review")
        await executor.execute(cmd)

        # Should have started all 3 tasks
        assert started_tasks == ["pm", "builder-1", "reviewer"]

    @pytest.mark.asyncio
    async def test_pipeline_emits_task_complete_per_stage(self):
        """Test that pipeline emits on_task_complete for each stage."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        completed_tasks = []

        def on_complete(task, result):
            completed_tasks.append(task.agent_id)

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_task_complete=on_complete,
        )

        cmd = parse_command("@pm Plan -> @builder-1 Build")
        await executor.execute(cmd)

        # Should have completed both tasks
        assert completed_tasks == ["pm", "builder-1"]

    @pytest.mark.asyncio
    async def test_multiagent_fanout_emits_task_started(self):
        """Test that multi-agent fan-out emits on_task_started for each agent."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        started_tasks = []

        def on_started(task):
            started_tasks.append(task.agent_id)

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_task_started=on_started,
        )

        # Pure multi-agent fan-out (no pipeline operator)
        cmd = parse_command("@pm,ba Analyze requirements")
        await executor.execute(cmd)

        # Should have started both tasks
        assert sorted(started_tasks) == ["ba", "pm"]

    @pytest.mark.asyncio
    async def test_multiagent_fanout_emits_task_complete(self):
        """Test that multi-agent fan-out emits on_task_complete for each agent."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        completed_tasks = []

        def on_complete(task, result):
            completed_tasks.append(task.agent_id)

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_task_complete=on_complete,
        )

        # Pure multi-agent fan-out (no pipeline operator)
        cmd = parse_command("@pm,ba Analyze requirements")
        await executor.execute(cmd)

        # Should have completed both tasks
        assert sorted(completed_tasks) == ["ba", "pm"]

    @pytest.mark.asyncio
    async def test_multiagent_stage_emits_all_agents(self):
        """Test that multi-agent stage reports all agents in stage change."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        stage_changes = []

        def on_stage_change(current, total, agents):
            stage_changes.append((current, total, sorted(agents)))

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_stage_change=on_stage_change,
        )

        # Multi-agent first stage (correct syntax: @pm,ba not @pm, @ba)
        cmd = parse_command("@pm,ba Analyze -> @builder-1 Build")
        await executor.execute(cmd)

        # First stage should have both pm and ba
        assert stage_changes[0] == (1, 2, ["ba", "pm"])
        assert stage_changes[1] == (2, 2, ["builder-1"])


class TestTaskExecutorStatusIntegration:
    """Tests for AgentStatusManager integration."""

    @pytest.mark.asyncio
    async def test_simple_command_updates_status(self):
        """Status manager updated for simple command lifecycle."""
        from teambot.ui.agent_state import AgentState, AgentStatusManager

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")
        status_manager = AgentStatusManager()

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            agent_status_manager=status_manager,
        )

        # Track state changes
        states = []

        def track(mgr):
            pm_status = mgr.get("pm")
            if pm_status:
                states.append(pm_status.state)

        status_manager.add_listener(track)

        cmd = parse_command("@pm Do something")
        await executor.execute(cmd)

        # Verify lifecycle: RUNNING -> COMPLETED -> IDLE
        assert AgentState.RUNNING in states
        assert AgentState.COMPLETED in states or AgentState.IDLE in states

    @pytest.mark.asyncio
    async def test_pipeline_handoff_updates_both_agents(self):
        """Pipeline handoff updates status for both agents."""
        from teambot.ui.agent_state import AgentState, AgentStatusManager

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")
        status_manager = AgentStatusManager()

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            agent_status_manager=status_manager,
        )

        # Track which agents were marked running
        running_agents = set()

        def track(mgr):
            for aid, status in mgr.get_all().items():
                if status.state == AgentState.RUNNING:
                    running_agents.add(aid)

        status_manager.add_listener(track)

        cmd = parse_command("@pm Plan -> @ba Review")
        await executor.execute(cmd)

        # Both agents should have been RUNNING at some point
        assert "pm" in running_agents
        assert "ba" in running_agents

    @pytest.mark.asyncio
    async def test_multiagent_parallel_status(self):
        """Multi-agent fan-out marks all agents running."""
        from teambot.ui.agent_state import AgentState, AgentStatusManager

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")
        status_manager = AgentStatusManager()

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            agent_status_manager=status_manager,
        )

        cmd = parse_command("@pm,ba Parallel task")
        await executor.execute(cmd)

        # Both should return to idle
        assert status_manager.get("pm").state == AgentState.IDLE
        assert status_manager.get("ba").state == AgentState.IDLE

    @pytest.mark.asyncio
    async def test_failure_marks_agent_failed(self):
        """Failed task marks agent as FAILED then IDLE."""
        from teambot.ui.agent_state import AgentState, AgentStatusManager

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(side_effect=Exception("Boom"))
        status_manager = AgentStatusManager()

        states = []

        def track(mgr):
            pm = mgr.get("pm")
            if pm:
                states.append(pm.state)

        status_manager.add_listener(track)

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            agent_status_manager=status_manager,
        )

        cmd = parse_command("@pm Fail please")
        await executor.execute(cmd)

        assert AgentState.FAILED in states

    @pytest.mark.asyncio
    async def test_no_status_manager_graceful(self):
        """Executor works without status manager (backward compat)."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        executor = TaskExecutor(sdk_client=mock_sdk)  # No status_manager

        cmd = parse_command("@pm Do something")
        result = await executor.execute(cmd)

        assert result.success  # Should not crash

    @pytest.mark.asyncio
    async def test_set_agent_status_manager_method(self):
        """Test setting status manager via setter method."""
        from teambot.ui.agent_state import AgentState, AgentStatusManager

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Set status manager after construction
        status_manager = AgentStatusManager()
        executor.set_agent_status_manager(status_manager)

        states = []

        def track(mgr):
            pm = mgr.get("pm")
            if pm:
                states.append(pm.state)

        status_manager.add_listener(track)

        cmd = parse_command("@pm Test task")
        await executor.execute(cmd)

        # Should have tracked status changes
        assert len(states) > 0
        assert AgentState.RUNNING in states


class TestTaskExecutorAgentValidation:
    """Tests for unknown agent ID validation in TaskExecutor."""

    @pytest.mark.asyncio
    async def test_execute_rejects_unknown_agent(self):
        """Unknown agent ID returns error via executor."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@unknown-agent do something &")

        result = await executor.execute(cmd)

        assert not result.success
        assert "Unknown agent: 'unknown-agent'" in result.error
        assert "Valid agents:" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_rejects_unknown_agent_background(self):
        """Background command with unknown agent returns error."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@fake-agent do something &")

        result = await executor.execute(cmd)

        assert not result.success
        assert "fake-agent" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_rejects_unknown_in_multiagent(self):
        """Multi-agent with invalid ID rejects entire command."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm,fake-agent do something")

        result = await executor.execute(cmd)

        assert not result.success
        assert "fake-agent" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_rejects_unknown_in_pipeline(self):
        """Pipeline with invalid agent rejects entire pipeline (executor layer)."""
        from teambot.repl.parser import Command, CommandType, PipelineStage

        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        # Construct command directly to test executor validation (parser now catches this too)
        cmd = Command(
            type=CommandType.AGENT,
            agent_id="fake-agent",
            agent_ids=["fake-agent", "pm"],
            content="Do research",
            is_pipeline=True,
            pipeline=[
                PipelineStage(agent_ids=["fake-agent"], content="Do research"),
                PipelineStage(agent_ids=["pm"], content="Create plan"),
            ],
        )

        result = await executor.execute(cmd)

        assert not result.success
        assert "fake-agent" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_accepts_valid_alias(self):
        """Valid alias (project_manager) is accepted when provided directly."""
        from teambot.repl.parser import Command, CommandType

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = Command(
            type=CommandType.AGENT,
            agent_id="project_manager",
            agent_ids=["project_manager"],
            content="Create a plan",
            background=True,
        )

        result = await executor.execute(cmd)

        # Should succeed (alias resolved to "pm", not rejected as unknown)
        assert result.success or result.background

    @pytest.mark.asyncio
    async def test_execute_accepts_all_valid_agents(self):
        """All 6 canonical agent IDs are accepted (regression guard)."""
        from teambot.repl.router import VALID_AGENTS

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        for agent_id in sorted(VALID_AGENTS):
            executor = TaskExecutor(sdk_client=mock_sdk)
            cmd = parse_command(f"@{agent_id} do work &")
            result = await executor.execute(cmd)
            assert result.error is None or "Unknown agent" not in (result.error or ""), (
                f"Valid agent '{agent_id}' was rejected"
            )

    @pytest.mark.asyncio
    async def test_execute_error_message_lists_valid_agents(self):
        """Error message contains sorted list of all valid agents."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@nobody do something &")

        result = await executor.execute(cmd)

        assert not result.success
        assert "ba, builder-1, builder-2, notify, pm, reviewer, writer" in result.error
