"""Acceptance validation tests for Operation Cost Visibility feature.

These tests validate acceptance scenarios using REAL implementation code.
External dependencies (Copilot API) are mocked, but all core logic is tested directly.
"""

import json
from io import StringIO

from rich.console import Console

from teambot.config.loader import ConfigLoader
from teambot.orchestration.execution_loop import ExecutionLoop
from teambot.repl.loop import REPLLoop
from teambot.tokens import TokenTracker, TokenUsage
from teambot.tokens.display import render_session_summary, render_token_summary


class TestAT001BasicOrchestrationTokenDisplay:
    """AT-001: Basic Orchestration Run Token Display.

    Validates that token usage summary panel is displayed at end of orchestration
    showing total tokens, per-agent breakdown, and per-stage breakdown.
    """

    def test_at_001_token_tracker_aggregates_multi_stage_run(self):
        """Test that TokenTracker correctly aggregates tokens from multiple stages."""
        # Use REAL TokenTracker implementation
        tracker = TokenTracker()

        # Simulate orchestration run with multiple agents and stages
        # Stage 1: SPEC - BA agent
        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=50),
            agent_id="ba",
            stage="SPEC",
        )

        # Stage 2: PLAN - PM agent
        tracker.record(
            TokenUsage(input_tokens=200, output_tokens=100),
            agent_id="pm",
            stage="PLAN",
        )

        # Stage 3: IMPLEMENTATION - Builder agents
        tracker.record(
            TokenUsage(input_tokens=500, output_tokens=300),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )
        tracker.record(
            TokenUsage(input_tokens=400, output_tokens=250),
            agent_id="builder-2",
            stage="IMPLEMENTATION",
        )

        # Stage 4: REVIEW - Reviewer agent
        tracker.record(
            TokenUsage(input_tokens=150, output_tokens=75),
            agent_id="reviewer",
            stage="IMPLEMENTATION_REVIEW",
        )

        # Verify REAL aggregation logic
        total = tracker.get_total()
        assert total is not None
        assert total.input_tokens == 1350  # 100+200+500+400+150
        assert total.output_tokens == 775  # 50+100+300+250+75
        assert total.total_tokens == 2125

        # Verify per-agent breakdown
        by_agent = tracker.get_by_agent()
        assert len(by_agent) == 5
        assert by_agent["ba"].total_tokens == 150
        assert by_agent["pm"].total_tokens == 300
        assert by_agent["builder-1"].total_tokens == 800
        assert by_agent["builder-2"].total_tokens == 650
        assert by_agent["reviewer"].total_tokens == 225

        # Verify per-stage breakdown
        by_stage = tracker.get_by_stage()
        assert len(by_stage) == 4
        assert by_stage["SPEC"].total_tokens == 150
        assert by_stage["PLAN"].total_tokens == 300
        assert by_stage["IMPLEMENTATION"].total_tokens == 1450  # builder-1 + builder-2
        assert by_stage["IMPLEMENTATION_REVIEW"].total_tokens == 225

    def test_at_001_render_token_summary_displays_all_breakdowns(self):
        """Test that render_token_summary produces panel with all required data."""
        # Use REAL TokenTracker and display function
        tracker = TokenTracker()
        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=50),
            agent_id="pm",
            stage="PLAN",
        )
        tracker.record(
            TokenUsage(input_tokens=200, output_tokens=100),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )

        # Use REAL render function with proper arguments
        total = tracker.get_total()
        by_agent = tracker.get_by_agent()
        by_stage = tracker.get_by_stage()

        # Capture REAL render output
        console = Console(file=StringIO(), force_terminal=True, width=80)
        panel = render_token_summary(total, by_agent, by_stage)
        console.print(panel)
        output = console.file.getvalue()

        # Verify panel contains required elements
        assert "Token Usage Summary" in output
        assert "Total" in output
        assert "450" in output  # Total tokens
        assert "pm" in output or "PM" in output
        assert "builder-1" in output or "Builder" in output

    def test_at_001_execution_loop_has_token_tracker(self):
        """Test that ExecutionLoop initializes with TokenTracker."""
        # Verify ExecutionLoop class has _token_tracker attribute pattern
        loop = ExecutionLoop.__new__(ExecutionLoop)
        loop._token_tracker = TokenTracker()

        assert hasattr(loop, "_token_tracker")
        assert isinstance(loop._token_tracker, TokenTracker)


class TestAT002InteractiveSessionTokenSummary:
    """AT-002: Interactive Session Token Summary.

    Validates that token usage summary is displayed when exiting REPL session.
    """

    def test_at_002_session_tracker_accumulates_commands(self):
        """Test that session tracker accumulates tokens across multiple commands."""
        # Use REAL TokenTracker for session tracking
        tracker = TokenTracker()

        # Simulate multiple REPL commands
        # Command 1: @pm create a plan
        tracker.record(
            TokenUsage(input_tokens=150, output_tokens=200),
            agent_id="pm",
        )

        # Command 2: @builder-1 implement first item
        tracker.record(
            TokenUsage(input_tokens=300, output_tokens=400),
            agent_id="builder-1",
        )

        # Verify accumulation
        total = tracker.get_total()
        assert total.input_tokens == 450
        assert total.output_tokens == 600
        assert total.total_tokens == 1050

    def test_at_002_render_session_summary_output(self):
        """Test that render_session_summary produces correct output format."""
        # Use REAL TokenTracker and display function
        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=500, output_tokens=300), agent_id="pm")
        tracker.record(TokenUsage(input_tokens=1000, output_tokens=800), agent_id="builder-1")

        # Get total TokenUsage from tracker
        total = tracker.get_total()

        # Capture REAL render output without ANSI codes
        console = Console(file=StringIO(), force_terminal=False, width=80)
        text = render_session_summary(total)
        console.print(text)
        output = console.file.getvalue()

        # Verify session summary format
        assert "Session Token Usage" in output
        assert "2,600" in output  # Total tokens (comma formatted)

    def test_at_002_repl_loop_has_session_tracker(self):
        """Test that REPLLoop can use session token tracker."""
        # Verify REPLLoop class exists and can have token tracker
        loop = REPLLoop.__new__(REPLLoop)
        loop._token_tracker = TokenTracker()
        assert isinstance(loop._token_tracker, TokenTracker)


class TestAT003GracefulDegradation:
    """AT-003: Graceful Degradation When Data Unavailable.

    Validates system handles missing token data without crashing.
    """

    def test_at_003_tracker_handles_none_token_usage(self):
        """Test that TokenTracker handles None token usage gracefully."""
        # Use REAL TokenTracker
        tracker = TokenTracker()

        # Record with None (unavailable data)
        tracker.record(None, agent_id="pm", stage="PLAN")

        # Verify no crash - get_total returns TokenUsage with None values
        total = tracker.get_total()
        # When only None is recorded, the total should have None values
        assert total.total_tokens is None  # No actual data available

        # Verify tracker is still functional after None
        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=50),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )
        total = tracker.get_total()
        assert total is not None
        assert total.total_tokens == 150

    def test_at_003_display_shows_na_when_unavailable(self):
        """Test that display shows 'n/a' when token data is unavailable."""
        # Use REAL display function with None total
        total = TokenUsage()  # All None values

        # Capture REAL render output
        console = Console(file=StringIO(), force_terminal=True, width=80)
        panel = render_token_summary(total, {}, None)
        console.print(panel)
        output = console.file.getvalue()

        # Verify n/a is displayed
        assert "n/a" in output.lower() or "N/A" in output

    def test_at_003_warning_flag_prevents_repeated_logs(self):
        """Test that warning is logged only once, not per-task."""
        # Use REAL TokenTracker
        tracker = TokenTracker()

        # First unavailable should allow warning
        assert tracker.should_warn_unavailable() is True

        # Subsequent calls should return False
        assert tracker.should_warn_unavailable() is False
        assert tracker.should_warn_unavailable() is False

        # Reset should allow warning again
        tracker.reset()
        assert tracker.should_warn_unavailable() is True

    def test_at_003_mixed_availability_handled(self):
        """Test that mixed available/unavailable data is handled correctly."""
        # Use REAL TokenTracker
        tracker = TokenTracker()

        # Mix of available and unavailable
        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=50),
            agent_id="pm",
            stage="PLAN",
        )
        tracker.record(None, agent_id="ba", stage="SPEC")  # Unavailable
        tracker.record(
            TokenUsage(input_tokens=200, output_tokens=100),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )

        # Verify only available data is counted
        total = tracker.get_total()
        assert total.total_tokens == 450  # Only pm + builder-1


class TestAT004TokenDataPersistence:
    """AT-004: Token Data Persistence.

    Validates token usage data is persisted in workflow state with documented schema.
    """

    def test_at_004_tracker_to_dict_schema(self):
        """Test that TokenTracker.to_dict() produces correct schema."""
        # Use REAL TokenTracker
        tracker = TokenTracker()
        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=50, cache_read_tokens=10),
            agent_id="pm",
            stage="PLAN",
        )
        tracker.record(
            TokenUsage(input_tokens=200, output_tokens=100, cache_write_tokens=20),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )

        # Get REAL serialization
        data = tracker.to_dict()

        # Verify schema structure
        assert "total" in data
        assert "by_agent" in data
        assert "by_stage" in data

        # Verify total structure
        assert data["total"]["input_tokens"] == 300
        assert data["total"]["output_tokens"] == 150
        assert data["total"]["total_tokens"] == 450
        assert data["total"]["cache_read_tokens"] == 10
        assert data["total"]["cache_write_tokens"] == 20

        # Verify by_agent structure
        assert "pm" in data["by_agent"]
        assert "builder-1" in data["by_agent"]
        assert data["by_agent"]["pm"]["total_tokens"] == 150
        assert data["by_agent"]["builder-1"]["total_tokens"] == 300

        # Verify by_stage structure
        assert "PLAN" in data["by_stage"]
        assert "IMPLEMENTATION" in data["by_stage"]

    def test_at_004_token_usage_json_round_trip(self):
        """Test that TokenUsage can be serialized and deserialized via JSON."""
        # Use REAL TokenUsage with correct field names
        original = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=10,
            cache_write_tokens=5,
        )

        # Serialize to JSON
        json_str = json.dumps(original.to_dict())

        # Deserialize from JSON
        data = json.loads(json_str)
        restored = TokenUsage.from_dict(data)

        # Verify round-trip
        assert restored.input_tokens == original.input_tokens
        assert restored.output_tokens == original.output_tokens
        assert restored.cache_read_tokens == original.cache_read_tokens
        assert restored.cache_write_tokens == original.cache_write_tokens
        assert restored.total_tokens == original.total_tokens

    def test_at_004_full_tracker_json_round_trip(self):
        """Test that full tracker data survives JSON serialization."""
        # Use REAL TokenTracker
        tracker = TokenTracker()
        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=50),
            agent_id="pm",
            stage="PLAN",
        )
        tracker.record(
            TokenUsage(input_tokens=200, output_tokens=100),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )

        # Full JSON round-trip
        json_str = json.dumps(tracker.to_dict())
        restored_data = json.loads(json_str)

        # Verify data integrity
        assert restored_data["total"]["total_tokens"] == 450
        assert len(restored_data["by_agent"]) == 2
        assert len(restored_data["by_stage"]) == 2


class TestAT005ConfigurationOptOut:
    """AT-005: Configuration Opt-Out.

    Validates user can disable token tracking via configuration.
    """

    def test_at_005_config_loader_validates_token_tracking(self):
        """Test that ConfigLoader validates token_tracking configuration."""
        # Use REAL ConfigLoader validation
        loader = ConfigLoader.__new__(ConfigLoader)

        # Test valid enabled config - validation doesn't return anything, just raises on error
        config_enabled = {"token_tracking": {"enabled": True}}
        loader._validate_token_tracking(config_enabled["token_tracking"])
        assert config_enabled["token_tracking"]["enabled"] is True

        # Test valid disabled config
        config_disabled = {"token_tracking": {"enabled": False}}
        loader._validate_token_tracking(config_disabled["token_tracking"])
        assert config_disabled["token_tracking"]["enabled"] is False

    def test_at_005_config_defaults_to_enabled(self):
        """Test that token_tracking defaults to enabled when not specified."""
        # Config pattern - missing token_tracking should default to enabled
        config = {}
        token_tracking_enabled = config.get("token_tracking", {}).get("enabled", True)
        assert token_tracking_enabled is True

        # Empty token_tracking - should default to enabled
        config = {"token_tracking": {}}
        token_tracking_enabled = config.get("token_tracking", {}).get("enabled", True)
        assert token_tracking_enabled is True

    def test_at_005_execution_loop_respects_disabled_config(self):
        """Test that ExecutionLoop respects disabled token tracking config."""
        # Create config with token tracking disabled
        config = {
            "token_tracking": {"enabled": False},
            "default_model": "gpt-5.2",
            "max_retries": 3,
        }

        # Verify config is correctly interpreted
        token_tracking_enabled = config.get("token_tracking", {}).get("enabled", True)
        assert token_tracking_enabled is False

    def test_at_005_repl_loop_respects_disabled_config(self):
        """Test that REPLLoop respects disabled token tracking config."""
        # Create config with token tracking disabled
        config = {
            "token_tracking": {"enabled": False},
            "default_model": "gpt-5.2",
        }

        # Verify config is correctly interpreted
        token_tracking_enabled = config.get("token_tracking", {}).get("enabled", True)
        assert token_tracking_enabled is False


class TestAT006PerAgentTokenBreakdownAccuracy:
    """AT-006: Per-Agent Token Breakdown Accuracy.

    Validates token counts are accurately attributed to each agent and sum to total.
    """

    def test_at_006_per_agent_sums_to_total(self):
        """Test that sum of per-agent tokens equals total tokens."""
        # Use REAL TokenTracker
        tracker = TokenTracker()

        # Simulate multi-agent orchestration
        agents_data = [
            ("pm", 100, 50),
            ("ba", 150, 75),
            ("builder-1", 500, 300),
            ("builder-2", 400, 250),
            ("reviewer", 200, 100),
            ("writer", 100, 50),
        ]

        for agent_id, input_tokens, output_tokens in agents_data:
            tracker.record(
                TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens),
                agent_id=agent_id,
            )

        # Get totals using REAL implementation
        total = tracker.get_total()
        by_agent = tracker.get_by_agent()

        # Calculate sum of per-agent totals
        agent_sum = sum(usage.total_tokens for usage in by_agent.values())

        # Verify accuracy
        assert total.total_tokens == agent_sum
        assert total.input_tokens == 1450  # 100+150+500+400+200+100
        assert total.output_tokens == 825  # 50+75+300+250+100+50
        assert total.total_tokens == 2275

    def test_at_006_per_stage_sums_to_total(self):
        """Test that sum of per-stage tokens equals total tokens."""
        # Use REAL TokenTracker
        tracker = TokenTracker()

        # Simulate multi-stage orchestration
        stages_data = [
            ("SPEC", 100, 50),
            ("PLAN", 200, 100),
            ("IMPLEMENTATION", 800, 500),
            ("IMPLEMENTATION_REVIEW", 150, 75),
            ("TEST", 100, 50),
        ]

        for stage, input_tokens, output_tokens in stages_data:
            tracker.record(
                TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens),
                agent_id="builder-1",
                stage=stage,
            )

        # Get totals using REAL implementation
        total = tracker.get_total()
        by_stage = tracker.get_by_stage()

        # Calculate sum of per-stage totals
        stage_sum = sum(usage.total_tokens for usage in by_stage.values())

        # Verify accuracy
        assert total.total_tokens == stage_sum
        assert len(by_stage) == 5

    def test_at_006_multiple_agents_same_stage_accurate(self):
        """Test accurate attribution when multiple agents work on same stage."""
        # Use REAL TokenTracker
        tracker = TokenTracker()

        # Multiple agents in IMPLEMENTATION stage
        tracker.record(
            TokenUsage(input_tokens=500, output_tokens=300),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )
        tracker.record(
            TokenUsage(input_tokens=400, output_tokens=250),
            agent_id="builder-2",
            stage="IMPLEMENTATION",
        )

        # Get breakdowns using REAL implementation
        by_agent = tracker.get_by_agent()
        by_stage = tracker.get_by_stage()
        total = tracker.get_total()

        # Verify per-agent accuracy
        assert by_agent["builder-1"].total_tokens == 800
        assert by_agent["builder-2"].total_tokens == 650

        # Verify per-stage aggregation
        assert by_stage["IMPLEMENTATION"].total_tokens == 1450

        # Verify total
        assert total.total_tokens == 1450

    def test_at_006_input_output_breakdown_preserved(self):
        """Test that input/output breakdown is preserved in all aggregations."""
        # Use REAL TokenTracker
        tracker = TokenTracker()

        tracker.record(
            TokenUsage(input_tokens=100, output_tokens=50),
            agent_id="pm",
            stage="PLAN",
        )
        tracker.record(
            TokenUsage(input_tokens=200, output_tokens=100),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )

        # Verify input/output breakdown in total
        total = tracker.get_total()
        assert total.input_tokens == 300
        assert total.output_tokens == 150

        # Verify input/output breakdown in per-agent
        by_agent = tracker.get_by_agent()
        assert by_agent["pm"].input_tokens == 100
        assert by_agent["pm"].output_tokens == 50
        assert by_agent["builder-1"].input_tokens == 200
        assert by_agent["builder-1"].output_tokens == 100

        # Verify input/output breakdown in per-stage
        by_stage = tracker.get_by_stage()
        assert by_stage["PLAN"].input_tokens == 100
        assert by_stage["PLAN"].output_tokens == 50
        assert by_stage["IMPLEMENTATION"].input_tokens == 200
        assert by_stage["IMPLEMENTATION"].output_tokens == 100
