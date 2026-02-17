"""Acceptance test validation for default agent context reference extraction.

These tests exercise the REAL implementation code to validate
each acceptance scenario from the feature specification.
"""

import pytest

from teambot.repl.parser import (
    Command,
    CommandType,
    extract_references,
    needs_default_agent_for_pipeline,
    parse_command,
    prepend_default_agent,
)
from teambot.tasks.executor import TaskExecutor


class TestAcceptanceScenarios:
    """Integration tests validating real acceptance scenarios."""

    # ── AT-001: Single Reference with Default Agent ──

    def test_at_001_single_reference_with_default_agent(self):
        """User types command with single $agent reference using default agent routing.

        Scenario:
        1. Default agent is configured (pm)
        2. Reviewer has previously run
        3. User enters: "Incorporate the feedback from $reviewer" (no @pm prefix)

        Expected:
        - $reviewer is extracted as a reference
        - Command.references contains ["reviewer"]
        """
        # This simulates what loop.py and app.py now do when routing to default agent
        raw_content = "Incorporate the feedback from $reviewer"
        default_agent = "pm"

        # Extract references using the REAL implementation
        references = extract_references(raw_content)

        # Create command as the fixed loop.py/app.py would
        command = Command(
            type=CommandType.AGENT,
            agent_id=default_agent,
            agent_ids=[default_agent],
            content=raw_content,
            references=references,
        )

        # Verify the reference was extracted
        assert references == ["reviewer"], f"Expected ['reviewer'], got {references}"
        assert command.references == ["reviewer"]
        assert command.agent_id == "pm"
        assert command.content == raw_content

    # ── AT-002: Multiple References with Default Agent ──

    def test_at_002_multiple_references_with_default_agent(self):
        """User types command with multiple $agent references using default agent routing.

        Scenario:
        1. Default agent is configured (pm)
        2. Reviewer and BA have previously run
        3. User enters: "Combine insights from $reviewer and $ba"

        Expected:
        - Both $reviewer and $ba are extracted as references
        - References maintain order of appearance
        """
        raw_content = "Combine insights from $reviewer and $ba"
        default_agent = "pm"

        # Extract references using the REAL implementation
        references = extract_references(raw_content)

        # Create command as the fixed loop.py/app.py would
        command = Command(
            type=CommandType.AGENT,
            agent_id=default_agent,
            agent_ids=[default_agent],
            content=raw_content,
            references=references,
        )

        # Verify both references were extracted in order
        assert references == ["reviewer", "ba"], f"Expected ['reviewer', 'ba'], got {references}"
        assert command.references == ["reviewer", "ba"]
        assert len(command.references) == 2

    # ── AT-003: Escaped Reference Not Extracted ──

    def test_at_003_escaped_reference_not_extracted(self):
        r"""Escaped \$agent syntax should not be extracted as reference.

        Scenario:
        1. Default agent is configured (pm)
        2. User enters: "Explain what \$reviewer syntax means" (escaped)

        Expected:
        - No references extracted
        - \$reviewer passed literally to PM
        """
        raw_content = r"Explain what \$reviewer syntax means"
        default_agent = "pm"

        # Extract references using the REAL implementation
        references = extract_references(raw_content)

        # Create command as the fixed loop.py/app.py would
        command = Command(
            type=CommandType.AGENT,
            agent_id=default_agent,
            agent_ids=[default_agent],
            content=raw_content,
            references=references,
        )

        # Verify no references were extracted (escaped)
        assert references == [], f"Expected [], got {references}"
        assert command.references == []
        # Content should still contain the escaped reference literally
        assert r"\$reviewer" in command.content

    # ── AT-004: Pipeline with Default Agent Still Works ──

    def test_at_004_pipeline_with_default_agent_still_works(self):
        """Pipeline syntax continues to work with default agent.

        Scenario:
        1. Default agent is configured (pm)
        2. User enters: "tell a joke -> @notify"

        Expected:
        - Pipeline is correctly detected
        - needs_default_agent_for_pipeline returns True
        - After prepending default agent, parse_command extracts pipeline
        """
        raw_content = "tell a joke -> @notify"
        default_agent = "pm"

        # Check if this needs default agent prepended for pipeline
        needs_prepend = needs_default_agent_for_pipeline(raw_content)
        assert needs_prepend is True, "Pipeline should be detected"

        # Prepend default agent as loop.py/app.py would
        prefixed = prepend_default_agent(raw_content, default_agent)
        assert prefixed == "@pm tell a joke -> @notify"

        # Parse the prefixed command
        command = parse_command(prefixed)

        # Verify pipeline was correctly parsed
        assert command.type == CommandType.AGENT
        assert command.is_pipeline is True
        assert command.pipeline is not None
        assert len(command.pipeline) == 2

        # First stage should be pm with "tell a joke"
        assert command.pipeline[0].agent_ids == ["pm"]
        assert command.pipeline[0].content == "tell a joke"

        # Second stage should be notify
        assert command.pipeline[1].agent_ids == ["notify"]

    # ── AT-005: Explicit Agent Prefix Still Works ──

    def test_at_005_explicit_agent_prefix_still_works(self):
        """Explicit @agent prefix continues to extract references.

        Scenario:
        1. User enters: "@pm Incorporate $reviewer feedback"

        Expected:
        - $reviewer extracted correctly via parse_command
        - Works identically whether default agent is configured or not
        """
        input_text = "@pm Incorporate $reviewer feedback"

        # Parse using the REAL parse_command implementation
        command = parse_command(input_text)

        # Verify command was parsed correctly
        assert command.type == CommandType.AGENT
        assert command.agent_id == "pm"
        assert command.agent_ids == ["pm"]
        assert command.content == "Incorporate $reviewer feedback"

        # Verify reference was extracted by parse_command
        assert command.references == ["reviewer"], f"Expected ['reviewer'], got {command.references}"

    # ── Additional Edge Case Tests ──

    def test_at_001_reference_triggers_executor_check(self):
        """Verify that command.references being populated triggers executor logic.

        The TaskExecutor checks command.references to decide whether to inject
        prior agent outputs. This test verifies the command structure is correct.
        """
        raw_content = "Summarize $ba feedback"
        default_agent = "pm"

        references = extract_references(raw_content)
        command = Command(
            type=CommandType.AGENT,
            agent_id=default_agent,
            agent_ids=[default_agent],
            content=raw_content,
            references=references,
        )

        # TaskExecutor uses this condition to decide on injection
        # See executor.py line 316: if command.references:
        should_inject = bool(command.references)
        assert should_inject is True, "References should trigger injection logic"

    def test_at_002_order_preservation_multiple_refs(self):
        """Multiple references preserve discovery order."""
        content = "First $ba then $pm and finally $reviewer"
        references = extract_references(content)
        assert references == ["ba", "pm", "reviewer"]

    def test_at_003_mixed_escaped_and_real_refs(self):
        r"""Mix of escaped \$ref and real $ref correctly extracts only real ones."""
        content = r"\$pm escaped but $ba is real and \$reviewer also escaped"
        references = extract_references(content)
        assert references == ["ba"], f"Expected ['ba'], got {references}"

    def test_at_005_explicit_with_multiple_refs(self):
        """Explicit @agent with multiple references."""
        command = parse_command("@reviewer Check $ba work against $pm plan")
        assert command.references == ["ba", "pm"]
        assert command.agent_id == "reviewer"


class TestEndToEndIntegration:
    """End-to-end tests with TaskExecutor to verify complete flow."""

    @pytest.fixture
    def mock_sdk(self):
        """Create a mock SDK client for testing."""
        from unittest.mock import AsyncMock

        sdk = AsyncMock()
        sdk.execute = AsyncMock(return_value="Test response")
        return sdk

    @pytest.mark.asyncio
    async def test_at_001_full_flow_default_agent_with_reference(self, mock_sdk):
        """Full flow: default agent routing with reference injection.

        This tests the complete path from raw input -> Command -> TaskExecutor
        to verify references are properly used for output injection.
        """
        # Simulate BA's prior output
        outputs = {
            "ba": "Requirements: user authentication, dashboard",
        }

        call_history = []

        async def mock_execute(agent_id, prompt, model=None):
            call_history.append((agent_id, prompt))
            return outputs.get(agent_id, f"Response from {agent_id}")

        mock_sdk.execute = mock_execute
        executor = TaskExecutor(sdk_client=mock_sdk)

        # First: BA runs and stores output
        ba_command = parse_command("@ba Analyze requirements")
        await executor.execute(ba_command)

        # Now: Create command as loop.py would for default agent routing
        raw_content = "Create plan based on $ba"
        default_agent = "pm"
        references = extract_references(raw_content)

        command = Command(
            type=CommandType.AGENT,
            agent_id=default_agent,
            agent_ids=[default_agent],
            content=raw_content,
            references=references,
        )

        # Verify references populated
        assert command.references == ["ba"]

        # Execute - TaskExecutor should inject BA's output
        result = await executor.execute(command)
        assert result.success

        # Find PM's call and verify injection
        pm_calls = [c for c in call_history if c[0] == "pm"]
        assert len(pm_calls) == 1

        pm_prompt = pm_calls[0][1]
        # Verify BA's output was injected
        assert "=== Output from @ba ===" in pm_prompt
        assert "Requirements: user authentication, dashboard" in pm_prompt
        assert "=== Your Task ===" in pm_prompt
        assert "Create plan based on $ba" in pm_prompt

    @pytest.mark.asyncio
    async def test_at_002_full_flow_multiple_references(self, mock_sdk):
        """Full flow: multiple references injected."""
        outputs = {
            "ba": "Business requirements documented",
            "reviewer": "Code looks good with minor suggestions",
        }

        call_history = []

        async def mock_execute(agent_id, prompt, model=None):
            call_history.append((agent_id, prompt))
            return outputs.get(agent_id, f"Response from {agent_id}")

        mock_sdk.execute = mock_execute
        executor = TaskExecutor(sdk_client=mock_sdk)

        # Run BA and Reviewer first
        await executor.execute(parse_command("@ba Document requirements"))
        await executor.execute(parse_command("@reviewer Review the code"))

        # Default agent routing with multiple references
        raw_content = "Synthesize $ba and $reviewer into action plan"
        references = extract_references(raw_content)

        command = Command(
            type=CommandType.AGENT,
            agent_id="pm",
            agent_ids=["pm"],
            content=raw_content,
            references=references,
        )

        assert command.references == ["ba", "reviewer"]

        await executor.execute(command)

        # Verify PM received both outputs
        pm_calls = [c for c in call_history if c[0] == "pm"]
        assert len(pm_calls) == 1

        pm_prompt = pm_calls[0][1]
        assert "=== Output from @ba ===" in pm_prompt
        assert "=== Output from @reviewer ===" in pm_prompt
        assert "Business requirements documented" in pm_prompt
        assert "Code looks good with minor suggestions" in pm_prompt
