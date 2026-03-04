"""Acceptance test validation for pipeline parse error fix.

Tests validate real implementation behavior without mocks for core parsing logic.
"""

import pytest

from teambot.repl.parser import ParseError, parse_command


class TestPipelineParseErrorAcceptance:
    """Acceptance tests for quote-aware pipeline parsing."""

    def test_at_001_discussing_pipeline_syntax(self):
        """AT-001: User asks an agent to explain the pipeline operator.

        Steps:
            1. User enters: `@pm explain how the '->' operator works in TeamBot`
            2. Parser processes the input
            3. Command is routed to PM agent

        Expected Result:
            Command parsed as single agent command, PM receives full content including `'->'`
        """
        # Call REAL implementation
        result = parse_command("@pm explain how the '->' operator works in TeamBot")

        # Verify: result.is_pipeline == False and '->' appears in result.content
        assert result.is_pipeline is False, "Should NOT be parsed as pipeline"
        assert result.agent_id == "pm", "Should route to PM agent"
        assert "'->'".replace("'", "'") in result.content or "'->" in result.content, (
            "Content should include the quoted arrow operator"
        )

    def test_at_002_mixed_quoted_and_unquoted_pipeline(self):
        """AT-002: User explains syntax and then actually uses a pipeline.

        Steps:
            1. User enters: `@pm document the "->" syntax -> @writer format it nicely`
            2. Parser processes the input
            3. Command is routed as pipeline

        Expected Result:
            Parsed as 2-stage pipeline; first stage content includes `"->"`,
            second stage goes to writer
        """
        # Call REAL implementation
        result = parse_command('@pm document the "->" syntax -> @writer format it nicely')

        # Verify: is_pipeline == True, len(pipeline) == 2, '"->"' in first stage
        assert result.is_pipeline is True, "Should be parsed as pipeline"
        assert len(result.pipeline) == 2, "Should have 2 stages"
        assert '"->"' in result.pipeline[0].content, (
            "First stage content should include quoted arrow"
        )
        assert result.pipeline[1].agent_ids == ["writer"], "Second stage should go to writer"

    def test_at_003_valid_pipeline_still_works(self):
        """AT-003: Standard pipeline usage continues to work.

        Steps:
            1. User enters: `@pm create a plan -> @builder-1 implement it -> @reviewer check it`
            2. Parser processes the input

        Expected Result:
            Parsed as 3-stage pipeline
        """
        # Call REAL implementation
        result = parse_command("@pm create a plan -> @builder-1 implement it -> @reviewer check it")

        # Verify: is_pipeline == True, len(pipeline) == 3, agents correct
        assert result.is_pipeline is True, "Should be parsed as pipeline"
        assert len(result.pipeline) == 3, "Should have 3 stages"

        agents = [stage.agent_ids[0] for stage in result.pipeline]
        assert agents == ["pm", "builder-1", "reviewer"], (
            f"Agents should be ['pm', 'builder-1', 'reviewer'], got {agents}"
        )

    def test_at_004_nested_quotes_edge_case(self):
        """AT-004: User uses nested quotes around arrow.

        Steps:
            1. User enters: `@pm the syntax is "use '->' between agents"`
            2. Parser processes the input

        Expected Result:
            Parsed as single command, no pipeline
        """
        # Call REAL implementation
        result = parse_command("@pm the syntax is \"use '->' between agents\"")

        # Verify: is_pipeline == False, full quoted string preserved in content
        assert result.is_pipeline is False, "Should NOT be parsed as pipeline"
        assert result.agent_id == "pm", "Should route to PM agent"
        assert "'->'".replace("'", "'") in result.content or "'->" in result.content, (
            "Content should preserve the nested quoted arrow"
        )

    def test_at_005_error_message_quality_preserved(self):
        """AT-005: Malformed pipeline still produces helpful error.

        Steps:
            1. User enters: `@pm task -> @invalid-agent-xyz do something`
            2. Parser processes the input

        Expected Result:
            ParseError raised with helpful message about unknown agent
        """
        # Call REAL implementation - expect ParseError
        with pytest.raises(ParseError) as exc_info:
            parse_command("@pm task -> @invalid-agent-xyz do something")

        # Verify: Exception message includes "Unknown agent" and lists valid agents
        error_message = str(exc_info.value)
        assert "Unknown agent" in error_message, (
            f"Error should mention 'Unknown agent', got: {error_message}"
        )
        assert "invalid-agent-xyz" in error_message, (
            f"Error should mention the invalid agent name, got: {error_message}"
        )
        # Should list valid agents
        assert "pm" in error_message or "builder" in error_message, (
            f"Error should list valid agents, got: {error_message}"
        )
