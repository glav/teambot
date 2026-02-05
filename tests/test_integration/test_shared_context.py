"""Integration tests for shared context ($agent) feature.

Tests the complete workflow from parsing through execution.
"""

from unittest.mock import AsyncMock

import pytest

from teambot.repl.parser import parse_command
from teambot.tasks.executor import TaskExecutor


class TestSharedContextIntegration:
    """Integration tests for shared context feature."""

    @pytest.fixture
    def mock_sdk(self):
        """Create a mock SDK client."""
        sdk = AsyncMock()
        sdk.execute = AsyncMock()
        return sdk

    @pytest.mark.asyncio
    async def test_full_workflow_with_references(self, mock_sdk):
        """Test complete workflow: BA → PM references BA → Builder references PM."""
        outputs = {
            "ba": "Requirements: login, dashboard",
            "pm": "Plan: 1. Build login 2. Build dashboard",
            "builder-1": "Implementation complete",
        }

        call_history = []

        async def mock_execute(agent_id, prompt, model=None):
            call_history.append((agent_id, prompt))
            return outputs.get(agent_id, "default")

        mock_sdk.execute = mock_execute
        executor = TaskExecutor(sdk_client=mock_sdk)

        # BA analyzes
        result1 = await executor.execute(parse_command("@ba Analyze requirements"))
        assert result1.success
        assert "Requirements" in result1.output

        # PM references BA
        result2 = await executor.execute(parse_command("@pm Create plan based on $ba"))
        assert result2.success
        assert "Plan" in result2.output

        # Verify PM received BA's output in prompt
        pm_call = [c for c in call_history if c[0] == "pm"][0]
        assert "=== Output from @ba ===" in pm_call[1]
        assert "Requirements: login, dashboard" in pm_call[1]
        assert "=== Your Task ===" in pm_call[1]

        # Builder references PM
        result3 = await executor.execute(parse_command("@builder-1 Implement $pm"))
        assert result3.success
        assert "Implementation" in result3.output

        # Verify Builder received PM's output
        builder_call = [c for c in call_history if c[0] == "builder-1"][0]
        assert "=== Output from @pm ===" in builder_call[1]
        assert "Plan:" in builder_call[1]

    @pytest.mark.asyncio
    async def test_multiple_references_in_single_command(self, mock_sdk):
        """Test referencing multiple agents in one command."""
        outputs = {
            "ba": "Business requirements: user auth",
            "writer": "Technical spec: JWT tokens",
            "reviewer": "Looks good",
        }

        call_history = []

        async def mock_execute(agent_id, prompt, model=None):
            call_history.append((agent_id, prompt))
            return outputs.get(agent_id, "default")

        mock_sdk.execute = mock_execute
        executor = TaskExecutor(sdk_client=mock_sdk)

        # BA and Writer produce outputs
        await executor.execute(parse_command("@ba Analyze requirements"))
        await executor.execute(parse_command("@writer Document approach"))

        # Reviewer references both
        result = await executor.execute(parse_command("@reviewer Check $ba against $writer"))
        assert result.success

        # Verify reviewer received both outputs
        reviewer_call = [c for c in call_history if c[0] == "reviewer"][0]
        assert "=== Output from @ba ===" in reviewer_call[1]
        assert "=== Output from @writer ===" in reviewer_call[1]
        assert "Business requirements" in reviewer_call[1]
        assert "Technical spec" in reviewer_call[1]

    @pytest.mark.asyncio
    async def test_reference_no_prior_output(self, mock_sdk):
        """Test graceful handling when referenced agent has no prior output."""
        mock_sdk.execute = AsyncMock(return_value="Result")
        executor = TaskExecutor(sdk_client=mock_sdk)

        # PM references BA that hasn't run
        result = await executor.execute(parse_command("@pm Summarize $ba"))
        assert result.success

        # Verify placeholder was used
        call_args = mock_sdk.execute.call_args
        prompt = call_args[0][1]
        assert "[No output available]" in prompt

    @pytest.mark.asyncio
    async def test_reference_preserves_original_prompt(self, mock_sdk):
        """Test that original prompt is preserved in 'Your Task' section."""
        mock_sdk.execute = AsyncMock(return_value="Done")
        executor = TaskExecutor(sdk_client=mock_sdk)

        # First run BA
        await executor.execute(parse_command("@ba Analyze"))

        # PM references BA with specific task
        original_prompt = "Create a detailed plan based on $ba"
        await executor.execute(parse_command(f"@pm {original_prompt}"))

        # Verify original prompt preserved
        call_args = mock_sdk.execute.call_args
        prompt = call_args[0][1]
        assert "=== Your Task ===" in prompt
        assert original_prompt in prompt

    @pytest.mark.asyncio
    async def test_command_routing_with_reference(self, mock_sdk):
        """Test that commands with references route through TaskExecutor."""
        mock_sdk.execute = AsyncMock(return_value="Result")
        executor = TaskExecutor(sdk_client=mock_sdk)

        # Command with reference should work
        command = parse_command("@pm Summarize $ba")
        assert command.references == ["ba"]

        result = await executor.execute(command)
        assert result.success

    @pytest.mark.asyncio
    async def test_reference_with_pipeline(self, mock_sdk):
        """Test references work with pipeline syntax."""
        outputs = {
            "ba": "Requirements from BA",
            "pm": "Plan from PM",
            "builder-1": "Implementation",
        }

        call_history = []

        async def mock_execute(agent_id, prompt, model=None):
            call_history.append((agent_id, prompt))
            return outputs.get(agent_id, "default")

        mock_sdk.execute = mock_execute
        executor = TaskExecutor(sdk_client=mock_sdk)

        # Run BA first to have output to reference
        await executor.execute(parse_command("@ba Define requirements"))

        # Pipeline that references BA in first stage
        result = await executor.execute(
            parse_command("@pm Plan based on $ba -> @builder-1 Implement")
        )
        assert result.success

        # Verify PM got BA's output
        pm_calls = [c for c in call_history if c[0] == "pm"]
        assert len(pm_calls) >= 1
        assert "=== Output from @ba ===" in pm_calls[-1][1]

    @pytest.mark.asyncio
    async def test_latest_output_used_after_multiple_runs(self, mock_sdk):
        """Test that most recent output is used when agent runs multiple times."""
        run_count = 0

        async def mock_execute(agent_id, prompt, model=None):
            nonlocal run_count
            run_count += 1
            return f"BA output #{run_count}"

        mock_sdk.execute = mock_execute
        executor = TaskExecutor(sdk_client=mock_sdk)

        # Run BA twice
        await executor.execute(parse_command("@ba First task"))
        await executor.execute(parse_command("@ba Second task"))

        # PM references BA
        await executor.execute(parse_command("@pm Use $ba"))

        # Verify latest (second) output is used
        # The last call to execute should have been for PM
        # and should contain BA output #2
        assert run_count == 3  # 2 BA + 1 PM
