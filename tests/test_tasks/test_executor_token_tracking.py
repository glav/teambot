"""Regression tests for token tracking in TaskExecutor.

These tests ensure tokens are recorded correctly when using:
- Pipelines (->): @pm "task" -> @builder-1
- References ($): @pm "task with $ba context"
- Fan-out (,): @pm,@ba "task"

Prior to the fix, token recording only happened in simple @agent commands
via loop.py._handle_agent_command. Pipeline/reference/fan-out commands
went through TaskExecutor._execute_agent_task which did not record tokens.
"""

from unittest.mock import AsyncMock

import pytest

from teambot.repl.parser import parse_command
from teambot.tasks.executor import TaskExecutor
from teambot.tokens.models import TokenUsage
from teambot.tokens.tracker import TokenTracker


class TestExecutorTokenTrackingPipelines:
    """Tests for token tracking in pipeline commands."""

    @pytest.mark.asyncio
    async def test_pipeline_records_tokens_for_all_stages(self):
        """Pipeline (-> operator) records tokens for each stage.

        Regression test: Previously, pipelines through TaskExecutor
        did not record tokens because _execute_agent_task didn't handle
        the tuple return from execute_streaming.
        """
        token_tracker = TokenTracker()

        # Mock SDK that returns tuple (response, token_usage)
        mock_sdk = AsyncMock()
        mock_sdk.execute_streaming = AsyncMock(
            side_effect=[
                ("Stage 1 output", TokenUsage(input_tokens=100, output_tokens=150)),
                ("Stage 2 output", TokenUsage(input_tokens=200, output_tokens=250)),
            ]
        )

        def on_chunk(agent_id, chunk):
            pass

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
            token_tracker=token_tracker,
        )

        # Execute pipeline: @pm -> @builder-1
        cmd = parse_command("@pm Create a plan -> @builder-1 implement it")
        result = await executor.execute(cmd)

        assert result.success

        # Verify tokens were recorded for both agents
        total = token_tracker.get_total()
        assert total.input_tokens == 300  # 100 + 200
        assert total.output_tokens == 400  # 150 + 250
        assert total.total_tokens == 700

        by_agent = token_tracker.get_by_agent()
        assert "pm" in by_agent
        assert "builder-1" in by_agent
        assert by_agent["pm"].total_tokens == 250  # 100 + 150
        assert by_agent["builder-1"].total_tokens == 450  # 200 + 250

    @pytest.mark.asyncio
    async def test_pipeline_handles_none_token_usage(self):
        """Pipeline handles None token_usage gracefully (SDK didn't return tokens)."""
        token_tracker = TokenTracker()

        mock_sdk = AsyncMock()
        mock_sdk.execute_streaming = AsyncMock(
            side_effect=[
                ("Stage 1 output", TokenUsage(input_tokens=100, output_tokens=150)),
                ("Stage 2 output", None),  # No token data for second stage
            ]
        )

        def on_chunk(agent_id, chunk):
            pass

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
            token_tracker=token_tracker,
        )

        cmd = parse_command("@pm Create plan -> @builder-1 implement")
        result = await executor.execute(cmd)

        assert result.success

        # Should only record tokens from first stage
        total = token_tracker.get_total()
        assert total.input_tokens == 100
        assert total.output_tokens == 150


class TestExecutorTokenTrackingReferences:
    """Tests for token tracking with reference injection ($)."""

    @pytest.mark.asyncio
    async def test_reference_command_records_tokens(self):
        """Command with $ref records tokens for the execution.

        Regression test: Commands with references went through advanced
        command handling and didn't record tokens.
        """
        token_tracker = TokenTracker()

        mock_sdk = AsyncMock()
        call_count = 0

        async def mock_execute_streaming(agent_id, prompt, on_chunk=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ("BA analysis", TokenUsage(input_tokens=50, output_tokens=100))
            else:
                return (
                    "PM summary with BA context",
                    TokenUsage(input_tokens=150, output_tokens=200),
                )

        mock_sdk.execute_streaming = mock_execute_streaming

        def on_chunk(agent_id, chunk):
            pass

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
            token_tracker=token_tracker,
        )

        # First command to generate output for BA
        cmd1 = parse_command("@ba Analyze requirements")
        await executor.execute(cmd1)

        # Second command references BA's output
        cmd2 = parse_command("@pm Summarize $ba")
        await executor.execute(cmd2)

        # Both commands should have recorded tokens
        total = token_tracker.get_total()
        assert total.input_tokens == 200  # 50 + 150
        assert total.output_tokens == 300  # 100 + 200

        by_agent = token_tracker.get_by_agent()
        assert "ba" in by_agent
        assert "pm" in by_agent


class TestExecutorTokenTrackingFanOut:
    """Tests for token tracking with multi-agent fan-out (,)."""

    @pytest.mark.asyncio
    async def test_fanout_records_tokens_for_all_agents(self):
        """Fan-out (@pm,@ba) records tokens for each parallel agent.

        Regression test: Multi-agent commands went through TaskExecutor
        without proper token recording.
        """
        token_tracker = TokenTracker()

        mock_sdk = AsyncMock()
        mock_sdk.execute_streaming = AsyncMock(
            side_effect=[
                ("PM output", TokenUsage(input_tokens=100, output_tokens=150)),
                ("BA output", TokenUsage(input_tokens=120, output_tokens=180)),
            ]
        )

        def on_chunk(agent_id, chunk):
            pass

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
            token_tracker=token_tracker,
        )

        cmd = parse_command("@pm,ba Analyze this together")
        result = await executor.execute(cmd)

        assert result.success

        total = token_tracker.get_total()
        assert total.input_tokens == 220  # 100 + 120
        assert total.output_tokens == 330  # 150 + 180

        by_agent = token_tracker.get_by_agent()
        assert "pm" in by_agent
        assert "ba" in by_agent


class TestExecutorTokenTrackingNoTracker:
    """Tests verifying graceful behavior when no token tracker is provided."""

    @pytest.mark.asyncio
    async def test_pipeline_works_without_tracker(self):
        """Pipeline executes successfully without token tracker."""
        mock_sdk = AsyncMock()
        mock_sdk.execute_streaming = AsyncMock(
            side_effect=[
                ("Stage 1", TokenUsage(input_tokens=100, output_tokens=150)),
                ("Stage 2", TokenUsage(input_tokens=200, output_tokens=250)),
            ]
        )

        def on_chunk(agent_id, chunk):
            pass

        # No token_tracker provided
        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
        )

        cmd = parse_command("@pm plan -> @builder-1 implement")
        result = await executor.execute(cmd)

        # Should complete without errors
        assert result.success

    @pytest.mark.asyncio
    async def test_fanout_works_without_tracker(self):
        """Fan-out executes successfully without token tracker."""
        mock_sdk = AsyncMock()
        mock_sdk.execute_streaming = AsyncMock(
            return_value=("Output", TokenUsage(input_tokens=100, output_tokens=150))
        )

        def on_chunk(agent_id, chunk):
            pass

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
        )

        cmd = parse_command("@pm,ba Collaborate")
        result = await executor.execute(cmd)

        assert result.success


class TestExecutorTokenTrackingIntegration:
    """Integration tests combining multiple features."""

    @pytest.mark.asyncio
    async def test_complex_pipeline_with_fanout_records_all_tokens(self):
        """Complex pipeline with fan-out records tokens for all executions."""
        token_tracker = TokenTracker()

        mock_sdk = AsyncMock()
        mock_sdk.execute_streaming = AsyncMock(
            side_effect=[
                # Stage 1: @pm
                ("PM planning", TokenUsage(input_tokens=100, output_tokens=150)),
                # Stage 2: @builder-1,@builder-2 (fan-out)
                ("Builder-1 impl", TokenUsage(input_tokens=200, output_tokens=300)),
                ("Builder-2 impl", TokenUsage(input_tokens=250, output_tokens=350)),
            ]
        )

        def on_chunk(agent_id, chunk):
            pass

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
            token_tracker=token_tracker,
        )

        cmd = parse_command("@pm Create plan -> @builder-1,builder-2 Implement in parallel")
        result = await executor.execute(cmd)

        assert result.success

        total = token_tracker.get_total()
        # 100+200+250 input, 150+300+350 output
        assert total.input_tokens == 550
        assert total.output_tokens == 800
        assert total.total_tokens == 1350

        by_agent = token_tracker.get_by_agent()
        assert len(by_agent) == 3
        assert "pm" in by_agent
        assert "builder-1" in by_agent
        assert "builder-2" in by_agent

    @pytest.mark.asyncio
    async def test_execute_agent_task_unpacks_tuple_correctly(self):
        """Direct test of _execute_agent_task tuple unpacking.

        Regression test: The core bug was that _execute_agent_task returned
        the raw tuple from execute_streaming instead of unpacking it and
        recording the token_usage.
        """
        token_tracker = TokenTracker()

        mock_sdk = AsyncMock()
        expected_response = "Agent response text"
        expected_tokens = TokenUsage(input_tokens=500, output_tokens=750)
        mock_sdk.execute_streaming = AsyncMock(return_value=(expected_response, expected_tokens))

        def on_chunk(agent_id, chunk):
            pass

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
            token_tracker=token_tracker,
        )

        # Call _execute_agent_task directly (internal method)
        result = await executor._execute_agent_task("pm", "Test prompt")

        # Should return string, not tuple
        assert isinstance(result, str)
        assert result == expected_response

        # Tokens should be recorded
        total = token_tracker.get_total()
        assert total.input_tokens == 500
        assert total.output_tokens == 750

    @pytest.mark.asyncio
    async def test_execute_agent_task_handles_raw_string_return(self):
        """_execute_agent_task handles legacy string-only return.

        Some SDK versions might return just a string. The implementation
        should handle both tuple and string returns.
        """
        token_tracker = TokenTracker()

        mock_sdk = AsyncMock()
        # SDK returns just a string (legacy behavior)
        mock_sdk.execute_streaming = AsyncMock(return_value="Just a string")

        def on_chunk(agent_id, chunk):
            pass

        executor = TaskExecutor(
            sdk_client=mock_sdk,
            on_streaming_chunk=on_chunk,
            token_tracker=token_tracker,
        )

        result = await executor._execute_agent_task("pm", "Test prompt")

        # Should return the string directly
        assert result == "Just a string"

        # No tokens recorded (none returned) - total_tokens is None when no data
        total = token_tracker.get_total()
        assert total.total_tokens is None
