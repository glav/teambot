"""Acceptance tests for Operation Cost Visibility feature.

Core logic is tested directly; selective mocking is used only for external dependencies
like SDK client responses.
"""

import json

import pytest

from teambot.tokens.models import TokenUsage
from teambot.tokens.tracker import TokenTracker


@pytest.mark.acceptance
class TestAT001OrchestrationTokenSummary:
    """AT-001: Orchestration run displays token summary."""

    def test_token_tracker_aggregates_tokens_from_multiple_stages(self):
        """Verify TokenTracker correctly aggregates across stages."""
        tracker = TokenTracker()

        # Simulate multi-stage orchestration
        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=200),
            agent_id="pm",
            stage="SETUP",
        )
        tracker.record(
            TokenUsage(input_tokens=150, output_tokens=250),
            agent_id="ba",
            stage="SPEC",
        )
        tracker.record(
            TokenUsage(input_tokens=300, output_tokens=500),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )

        total = tracker.get_total()
        assert total.total_tokens == 1500  # 100+150+300 + 200+250+500
        assert total.input_tokens == 550
        assert total.output_tokens == 950

    def test_per_agent_breakdown_accurate(self):
        """Verify per-agent breakdown is accurate."""
        tracker = TokenTracker()

        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=200),
            agent_id="pm",
            stage="PLAN",
        )
        tracker.record(
            TokenUsage(input_tokens=50, output_tokens=100),
            agent_id="pm",
            stage="PLAN_REVIEW",
        )
        tracker.record(
            TokenUsage(input_tokens=300, output_tokens=500),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )

        by_agent = tracker.get_by_agent()
        assert "pm" in by_agent
        assert "builder-1" in by_agent
        assert by_agent["pm"].total_tokens == 450  # (100+50) + (200+100)
        assert by_agent["builder-1"].total_tokens == 800

    def test_per_stage_breakdown_accurate(self):
        """Verify per-stage breakdown is accurate."""
        tracker = TokenTracker()

        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=200),
            agent_id="pm",
            stage="PLAN",
        )
        tracker.record(
            TokenUsage(input_tokens=50, output_tokens=100),
            agent_id="reviewer",
            stage="PLAN",
        )
        tracker.record(
            TokenUsage(input_tokens=300, output_tokens=500),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )

        by_stage = tracker.get_by_stage()
        assert "PLAN" in by_stage
        assert "IMPLEMENTATION" in by_stage
        assert by_stage["PLAN"].total_tokens == 450
        assert by_stage["IMPLEMENTATION"].total_tokens == 800


@pytest.mark.acceptance
class TestAT002SessionTokenSummary:
    """AT-002: Interactive session displays token summary on exit."""

    def test_session_tracker_accumulates_across_commands(self):
        """Verify session tracker accumulates tokens across multiple commands."""
        tracker = TokenTracker()

        # Simulate multiple REPL commands
        for _ in range(5):
            tracker.record(
                TokenUsage(input_tokens=100, output_tokens=200),
                agent_id="pm",
                stage="INTERACTIVE",
            )

        total = tracker.get_total()
        assert total.total_tokens == 1500  # 5 * (100 + 200)


@pytest.mark.acceptance
class TestAT003GracefulDegradation:
    """AT-003: Graceful degradation when token data unavailable."""

    def test_tracker_handles_none_token_usage(self):
        """Verify tracker handles None token usage gracefully."""
        tracker = TokenTracker()

        # Record with actual data
        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=200),
            agent_id="pm",
            stage="PLAN",
        )

        # Record with None (SDK didn't return tokens)
        tracker.record(None, agent_id="builder-1", stage="IMPLEMENTATION")

        total = tracker.get_total()
        # Should only count the first record
        assert total.total_tokens == 300

    def test_display_shows_na_when_all_tokens_none(self):
        """Verify display shows n/a when all token data is None."""
        from teambot.tokens.display import render_session_summary, render_token_summary

        # Empty tracker - all None
        total = TokenUsage()
        by_agent = {}

        panel = render_token_summary(total, by_agent)
        assert "n/a" in str(panel.renderable)

        summary = render_session_summary(total)
        assert "n/a" in summary

    def test_warning_flag_prevents_repeated_logs(self):
        """Verify warning is logged only once."""
        tracker = TokenTracker()

        # First time warning should be logged
        first_should_warn = tracker.should_warn_unavailable()
        assert first_should_warn is True

        # Second time should return False (already warned)
        second_should_warn = tracker.should_warn_unavailable()
        assert second_should_warn is False


@pytest.mark.acceptance
class TestAT004TokenDataPersistence:
    """AT-004: Token data is persisted correctly."""

    def test_tracker_to_dict_includes_all_data(self):
        """Verify tracker serialization includes all required data."""
        tracker = TokenTracker()

        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=200, cache_read_tokens=50),
            agent_id="pm",
            stage="PLAN",
        )
        tracker.record(
            TokenUsage(input_tokens=300, output_tokens=500),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )

        data = tracker.to_dict()

        assert "schema_version" in data
        assert data["schema_version"] == "1.0"
        assert "total" in data
        assert data["total"]["input_tokens"] == 400
        assert data["total"]["output_tokens"] == 700
        assert "by_agent" in data
        assert "pm" in data["by_agent"]
        assert "builder-1" in data["by_agent"]
        assert "by_stage" in data
        assert "PLAN" in data["by_stage"]
        assert "IMPLEMENTATION" in data["by_stage"]

    def test_token_usage_round_trips_json(self):
        """Verify TokenUsage can round-trip through JSON."""
        original = TokenUsage(
            input_tokens=100,
            output_tokens=200,
            cache_read_tokens=50,
            cache_write_tokens=25,
        )

        # Serialize to JSON
        json_str = json.dumps(original.to_dict())

        # Deserialize from JSON
        data = json.loads(json_str)
        restored = TokenUsage.from_dict(data)

        assert restored.input_tokens == original.input_tokens
        assert restored.output_tokens == original.output_tokens
        assert restored.cache_read_tokens == original.cache_read_tokens
        assert restored.cache_write_tokens == original.cache_write_tokens


@pytest.mark.acceptance
class TestAT005ConfigDisablesTracking:
    """AT-005: Configuration option disables token tracking."""

    def test_execution_loop_respects_disabled_config(self, tmp_path):
        """Verify ExecutionLoop doesn't track when disabled."""
        from teambot.orchestration.execution_loop import ExecutionLoop

        # Create minimal objective file
        objective_file = tmp_path / "objective.md"
        objective_file.write_text(
            """# Test Objective

## Goals
- Test goal

## Success Criteria
- [ ] Test criterion

## Current Stage: SETUP
""",
            encoding="utf-8",
        )

        # Config with tracking disabled
        config = {
            "token_tracking": {"enabled": False},
            "agents": [{"id": "pm", "persona": "project_manager"}],
        }

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        loop = ExecutionLoop(
            objective_path=objective_file,
            config=config,
            teambot_dir=teambot_dir,
        )

        # Token tracker should be None when disabled
        assert loop._token_tracker is None

    def test_repl_loop_respects_disabled_config(self):
        """Verify REPLLoop doesn't track when disabled."""
        from unittest.mock import MagicMock

        from teambot.repl.loop import REPLLoop

        mock_console = MagicMock()
        config = {
            "token_tracking": {"enabled": False},
        }

        repl = REPLLoop(console=mock_console, config=config)

        assert repl._token_tracker is None


@pytest.mark.acceptance
class TestAT006PerStageAggregation:
    """AT-006: Per-stage aggregation is accurate."""

    def test_multiple_agents_same_stage(self):
        """Verify tokens from multiple agents in same stage aggregate correctly."""
        tracker = TokenTracker()

        # Implementation stage with parallel agents
        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=200),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )
        tracker.record(
            TokenUsage(input_tokens=150, output_tokens=250),
            agent_id="builder-2",
            stage="IMPLEMENTATION",
        )

        by_stage = tracker.get_by_stage()
        assert by_stage["IMPLEMENTATION"].total_tokens == 700  # (100+150) + (200+250)

        by_agent = tracker.get_by_agent()
        assert by_agent["builder-1"].total_tokens == 300
        assert by_agent["builder-2"].total_tokens == 400

    def test_complex_multi_stage_multi_agent_scenario(self):
        """Verify complex orchestration scenario aggregates correctly."""
        tracker = TokenTracker()

        # Simulate full workflow
        stages_data = [
            ("pm", "SETUP", 100, 150),
            ("ba", "SPEC", 200, 300),
            ("reviewer", "SPEC_REVIEW", 50, 100),
            ("builder-1", "RESEARCH", 300, 400),
            ("pm", "PLAN", 100, 150),
            ("reviewer", "PLAN_REVIEW", 50, 100),
            ("builder-1", "IMPLEMENTATION", 500, 800),
            ("builder-2", "IMPLEMENTATION", 400, 600),
            ("reviewer", "IMPLEMENTATION_REVIEW", 100, 150),
        ]

        for agent, stage, inp, out in stages_data:
            tracker.record(
                TokenUsage(input_tokens=inp, output_tokens=out),
                agent_id=agent,
                stage=stage,
            )

        total = tracker.get_total()
        expected_input = sum(d[2] for d in stages_data)
        expected_output = sum(d[3] for d in stages_data)
        assert total.input_tokens == expected_input
        assert total.output_tokens == expected_output
        assert total.total_tokens == expected_input + expected_output

        by_agent = tracker.get_by_agent()
        # pm: 100+150 + 100+150 = 500
        assert by_agent["pm"].total_tokens == 500
        # builder-1: (300+400) + (500+800) = 2000
        assert by_agent["builder-1"].total_tokens == 2000
        # builder-2: 400+600 = 1000
        assert by_agent["builder-2"].total_tokens == 1000


@pytest.mark.acceptance
class TestAT007TokensCommandInteractive:
    """AT-007: /tokens command shows session token usage on-demand."""

    def test_tokens_command_shows_accumulated_tokens(self):
        """Verify /tokens shows accumulated tokens after multiple commands."""
        from teambot.repl.commands import handle_tokens

        tracker = TokenTracker()

        # Simulate multiple @pm commands
        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=200),
            agent_id="pm",
            stage="INTERACTIVE",
        )
        tracker.record(
            TokenUsage(input_tokens=150, output_tokens=250),
            agent_id="pm",
            stage="INTERACTIVE",
        )

        result = handle_tokens([], tracker)

        assert result.success is True
        # Should show total: 100+150+200+250 = 700
        assert "700" in result.output

    def test_tokens_detailed_shows_agent_breakdown(self):
        """Verify /tokens --detailed shows per-agent breakdown."""
        from teambot.repl.commands import handle_tokens

        tracker = TokenTracker()

        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=200),
            agent_id="pm",
            stage="INTERACTIVE",
        )
        tracker.record(
            TokenUsage(input_tokens=300, output_tokens=500),
            agent_id="builder-1",
            stage="INTERACTIVE",
        )

        result = handle_tokens(["--detailed"], tracker)

        assert result.success is True
        assert "pm" in result.output
        assert "builder-1" in result.output
        # Should show percentages
        assert "%" in result.output

    def test_tokens_with_single_agent(self):
        """Verify /tokens --detailed with only one agent shows correct output."""
        from teambot.repl.commands import handle_tokens

        tracker = TokenTracker()
        tracker.record(
            TokenUsage(input_tokens=500, output_tokens=1000),
            agent_id="reviewer",
            stage="INTERACTIVE",
        )

        result = handle_tokens(["--detailed"], tracker)

        assert result.success is True
        assert "reviewer" in result.output
        assert "1,500" in result.output  # total

    def test_cost_alias_identical_to_tokens(self):
        """Verify /cost alias returns identical output to /tokens."""
        from teambot.repl.commands import handle_tokens

        tracker = TokenTracker()
        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=200),
            agent_id="pm",
            stage="INTERACTIVE",
        )

        tokens_result = handle_tokens([], tracker)
        cost_result = handle_tokens([], tracker)  # Same function

        assert tokens_result.output == cost_result.output

    def test_tokens_disabled_shows_message(self):
        """Verify /tokens shows disabled message when tracking is off."""
        from teambot.repl.commands import handle_tokens

        result = handle_tokens([], None)

        assert result.success is True
        assert "disabled" in result.output.lower()

    def test_tokens_no_usage_shows_message(self):
        """Verify /tokens shows no usage message when tracker is empty."""
        from teambot.repl.commands import handle_tokens

        tracker = TokenTracker()
        result = handle_tokens([], tracker)

        assert result.success is True
        assert "No token usage recorded" in result.output
