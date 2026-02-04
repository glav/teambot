"""Acceptance test validation for shared context reference feature.

These tests validate the acceptance scenarios using the REAL implementation code.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock

from teambot.repl.parser import parse_command, Command, CommandType, REFERENCE_PATTERN
from teambot.tasks.executor import TaskExecutor, ExecutionResult
from teambot.tasks.manager import TaskManager
from teambot.tasks.models import Task, TaskResult, TaskStatus


class TestAcceptanceScenarios:
    """Integration tests for acceptance scenarios."""

    # AT-001: Simple Reference After Completion
    @pytest.mark.asyncio
    async def test_at_001_simple_reference_after_completion(self):
        """User references an agent's output after that agent has completed."""
        # Setup: Create executor with mock SDK
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(side_effect=[
            "Project Plan:\n1. Setup environment\n2. Create database\n3. Build API",
            "I will implement based on the plan:\n- Setup environment first\n- Then create database",
        ])

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Step 1: PM creates a plan
        cmd1 = parse_command("@pm Create a simple project plan")
        result1 = await executor.execute(cmd1)
        assert result1.success
        assert "Project Plan" in result1.output

        # Step 2: Builder-1 references PM's output
        cmd2 = parse_command("@builder-1 Implement based on $pm")
        assert cmd2.references == ["pm"]

        result2 = await executor.execute(cmd2)
        assert result2.success

        # Verify: Builder-1 received PM's output in context
        call_args = mock_sdk.execute.call_args_list[1]
        prompt_sent = call_args[0][1]  # Second positional arg is prompt
        assert "=== Output from @pm ===" in prompt_sent
        assert "Project Plan" in prompt_sent
        assert "=== Your Task ===" in prompt_sent

    # AT-002: Reference Triggers Wait
    @pytest.mark.asyncio
    async def test_at_002_reference_triggers_wait(self):
        """User references an agent that is still executing."""
        call_order = []

        async def slow_pm_execute(agent_id, prompt):
            if agent_id == "pm":
                call_order.append("pm_start")
                await asyncio.sleep(0.2)  # Simulate slow execution
                call_order.append("pm_end")
                return "PM Plan: Build the feature"
            else:
                call_order.append("builder_start")
                return "Implementing based on plan"

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(side_effect=slow_pm_execute)

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Step 1: PM starts in background
        cmd1 = parse_command("@pm Create a detailed project plan &")
        assert cmd1.background is True

        # Start PM in background
        result1 = await executor.execute(cmd1)
        assert result1.background
        assert "background" in result1.output.lower()

        # Small delay to ensure PM has started
        await asyncio.sleep(0.05)

        # Step 2: Builder-1 references PM (should wait)
        cmd2 = parse_command("@builder-1 Implement $pm")
        assert cmd2.references == ["pm"]

        result2 = await executor.execute(cmd2)

        # Verify: PM completed before builder started
        assert "pm_end" in call_order
        pm_end_idx = call_order.index("pm_end")
        builder_start_idx = call_order.index("builder_start")
        assert pm_end_idx < builder_start_idx, "PM should complete before builder starts"

    # AT-003: Multiple References
    @pytest.mark.asyncio
    async def test_at_003_multiple_references(self):
        """User references multiple agents in one prompt."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(side_effect=[
            "PM Plan: Create user module",
            "BA Requirements:\n- User login\n- User registration",
            "Implementing with PM plan and BA requirements",
        ])

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Step 1: PM creates a plan
        cmd1 = parse_command("@pm Create a plan")
        await executor.execute(cmd1)

        # Step 2: BA writes requirements
        cmd2 = parse_command("@ba Write requirements")
        await executor.execute(cmd2)

        # Step 3: Builder references both
        cmd3 = parse_command("@builder-1 Implement using $pm plan and $ba requirements")
        assert "pm" in cmd3.references
        assert "ba" in cmd3.references

        result3 = await executor.execute(cmd3)
        assert result3.success

        # Verify: Builder received both outputs
        call_args = mock_sdk.execute.call_args_list[2]
        prompt_sent = call_args[0][1]
        assert "=== Output from @pm ===" in prompt_sent
        assert "=== Output from @ba ===" in prompt_sent
        assert "PM Plan" in prompt_sent
        assert "BA Requirements" in prompt_sent

    # AT-004: Invalid Agent Reference - Now validates against VALID_AGENTS
    @pytest.mark.asyncio
    async def test_at_004_invalid_agent_reference_error(self):
        """Referenced unknown agent shows error with valid agents list."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Reference a non-existent agent
        cmd = parse_command("@builder-1 Implement based on $nonexistent")
        result = await executor.execute(cmd)

        # Should fail with helpful error
        assert not result.success
        assert "Unknown agent reference: $nonexistent" in result.error
        assert "Valid agents:" in result.error
        assert "pm" in result.error
        assert "ba" in result.error

    # AT-005: Reference Agent With No Output
    @pytest.mark.asyncio
    async def test_at_005_reference_agent_with_no_output(self):
        """User references a valid agent that has no output yet."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Implementing...")

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Reference PM (valid agent) before PM has run anything
        cmd = parse_command("@builder-1 Implement $pm")
        result = await executor.execute(cmd)

        # Verify: Execution continues with helpful placeholder
        assert result.success
        call_args = mock_sdk.execute.call_args
        prompt_sent = call_args[0][1]
        assert "=== Output from @pm ===" in prompt_sent
        assert "[No output available]" in prompt_sent
        assert "=== Your Task ===" in prompt_sent

    # AT-006: Circular Dependency Detection
    # Current implementation doesn't detect circular deps at parse/execution time
    # This documents the current behavior
    @pytest.mark.asyncio
    async def test_at_006_circular_dependency_behavior(self):
        """
        Current behavior: Circular dependencies are not explicitly detected.
        If agent A waits for B and B waits for A, both would wait indefinitely.
        This test verifies the reference parsing works correctly.
        """
        # Parse commands with potential circular refs
        cmd1 = parse_command("@pm Create plan based on $builder-1")
        cmd2 = parse_command("@builder-1 Implement $pm")

        # Both commands parse successfully
        assert cmd1.references == ["builder-1"]
        assert cmd2.references == ["pm"]

        # Note: Circular dep detection would need to be added at execution time
        # Current implementation will cause indefinite waiting

    # AT-007: Combined Pipeline and Reference
    @pytest.mark.asyncio
    async def test_at_007_combined_pipeline_and_reference(self):
        """User combines -> pipeline with $agent reference."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(side_effect=[
            "BA Requirements: User authentication feature",
            "PM Plan based on BA: 1. Setup auth 2. Create endpoints",
            "Builder implementing from PM plan",
        ])

        executor = TaskExecutor(sdk_client=mock_sdk)

        # Step 1: BA writes requirements
        cmd1 = parse_command("@ba Write requirements")
        await executor.execute(cmd1)

        # Step 2: PM with reference to BA, then pipeline to builder
        cmd2 = parse_command("@pm Create plan for $ba -> @builder-1 Implement")
        assert cmd2.is_pipeline is True
        assert "ba" in cmd2.references

        result2 = await executor.execute(cmd2)
        assert result2.success

        # Verify: PM received BA's output
        pm_call = mock_sdk.execute.call_args_list[1]
        pm_prompt = pm_call[0][1]
        assert "=== Output from @ba ===" in pm_prompt
        assert "BA Requirements" in pm_prompt

    # AT-008: Escape Sequence - backslash prevents reference detection
    def test_at_008_escape_sequence_parsing(self):
        """User wants literal $pm in prompt without reference using backslash escape."""
        # Test with escaped dollar sign
        cmd = parse_command(r"@pm Explain what \$pm means in shell scripting")

        # Escaped $pm should NOT be extracted as a reference
        assert cmd.references == []
        assert cmd.type == CommandType.AGENT
        assert cmd.agent_ids == ["pm"]
        # Content should still contain the escaped form
        assert r"\$pm" in cmd.content

    # AT-008 (alternative): Test that literal $ followed by non-alpha is not a ref
    def test_at_008_dollar_non_alpha_not_reference(self):
        """Dollar sign followed by non-alpha is not treated as reference."""
        cmd = parse_command("@pm Explain what $100 costs in budget")

        # $100 should NOT be extracted as a reference
        assert "100" not in cmd.references
        assert cmd.references == []


class TestReferencePatternValidation:
    """Test the reference pattern regex directly."""

    def test_pattern_matches_simple_agent(self):
        """Pattern matches simple agent names."""
        matches = REFERENCE_PATTERN.findall("Use $pm output")
        assert matches == ["pm"]

    def test_pattern_matches_hyphenated_agent(self):
        """Pattern matches hyphenated agent names."""
        matches = REFERENCE_PATTERN.findall("Use $builder-1 output")
        assert matches == ["builder-1"]

    def test_pattern_ignores_dollar_numbers(self):
        """Pattern does not match dollar followed by numbers."""
        matches = REFERENCE_PATTERN.findall("Cost is $100")
        assert matches == []

    def test_pattern_multiple_refs(self):
        """Pattern finds multiple references."""
        matches = REFERENCE_PATTERN.findall("Combine $pm and $ba and $writer")
        assert matches == ["pm", "ba", "writer"]


class TestExecutorReferenceIntegration:
    """Integration tests for executor reference handling."""

    @pytest.mark.asyncio
    async def test_reference_injection_format(self):
        """Verify the exact format of injected references."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(side_effect=[
            "First output from PM",
            "Response with context",
        ])

        executor = TaskExecutor(sdk_client=mock_sdk)

        # First task
        await executor.execute(parse_command("@pm Do something"))

        # Second task with reference
        await executor.execute(parse_command("@builder-1 Use $pm"))

        # Check exact format
        call_args = mock_sdk.execute.call_args
        prompt = call_args[0][1]

        # Verify structure
        assert prompt.startswith("=== Output from @pm ===")
        assert "First output from PM" in prompt
        assert "=== Your Task ===" in prompt
        assert "Use $pm" in prompt

    @pytest.mark.asyncio
    async def test_multiple_tasks_same_agent_uses_latest(self):
        """When agent runs multiple times, reference gets latest output."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(side_effect=[
            "First PM output",
            "Second PM output",
            "Builder response",
        ])

        executor = TaskExecutor(sdk_client=mock_sdk)

        # PM runs twice
        await executor.execute(parse_command("@pm First task"))
        await executor.execute(parse_command("@pm Second task"))

        # Builder references PM
        await executor.execute(parse_command("@builder-1 Use $pm"))

        # Should get the LATEST output
        call_args = mock_sdk.execute.call_args
        prompt = call_args[0][1]
        assert "Second PM output" in prompt
        assert "First PM output" not in prompt
