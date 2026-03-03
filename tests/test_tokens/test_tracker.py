"""Tests for TokenTracker class."""

from teambot.tokens.models import TokenUsage


class TestTokenTracker:
    """Tests for TokenTracker aggregation class."""

    def test_record_task_usage(self):
        """TokenTracker records a single task's token usage."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        usage = TokenUsage(input_tokens=100, output_tokens=50)

        tracker.record(usage, agent_id="pm")

        total = tracker.get_total()
        assert total.input_tokens == 100
        assert total.output_tokens == 50

    def test_record_multiple_tasks(self):
        """TokenTracker accumulates multiple task usages."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=100, output_tokens=50), agent_id="pm")
        tracker.record(TokenUsage(input_tokens=200, output_tokens=100), agent_id="builder-1")

        total = tracker.get_total()
        assert total.input_tokens == 300
        assert total.output_tokens == 150
        assert total.total_tokens == 450

    def test_record_with_agent_id(self):
        """TokenTracker tracks usage by agent_id."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=100, output_tokens=50), agent_id="pm")
        tracker.record(TokenUsage(input_tokens=200, output_tokens=100), agent_id="builder-1")
        tracker.record(TokenUsage(input_tokens=50, output_tokens=25), agent_id="pm")

        by_agent = tracker.get_by_agent()

        assert "pm" in by_agent
        assert "builder-1" in by_agent
        assert by_agent["pm"].input_tokens == 150  # 100 + 50
        assert by_agent["pm"].output_tokens == 75  # 50 + 25
        assert by_agent["builder-1"].input_tokens == 200

    def test_record_with_stage(self):
        """TokenTracker tracks usage by workflow stage."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=100, output_tokens=50), agent_id="pm", stage="SPEC")
        tracker.record(
            TokenUsage(input_tokens=200, output_tokens=100),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )
        tracker.record(TokenUsage(input_tokens=50, output_tokens=25), agent_id="ba", stage="SPEC")

        by_stage = tracker.get_by_stage()

        assert "SPEC" in by_stage
        assert "IMPLEMENTATION" in by_stage
        assert by_stage["SPEC"].input_tokens == 150  # 100 + 50
        assert by_stage["IMPLEMENTATION"].input_tokens == 200

    def test_get_total(self):
        """get_total returns grand total across all tasks."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=100, output_tokens=50), agent_id="pm")
        tracker.record(TokenUsage(input_tokens=200, output_tokens=100), agent_id="builder-1")

        total = tracker.get_total()

        assert total.total_tokens == 450
        assert total.input_tokens == 300
        assert total.output_tokens == 150

    def test_get_by_agent(self):
        """get_by_agent returns dict of usage by agent_id."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=100, output_tokens=50), agent_id="pm")
        tracker.record(TokenUsage(input_tokens=200, output_tokens=100), agent_id="builder-1")

        by_agent = tracker.get_by_agent()

        assert isinstance(by_agent, dict)
        assert len(by_agent) == 2
        assert all(isinstance(v, TokenUsage) for v in by_agent.values())

    def test_get_by_stage(self):
        """get_by_stage returns dict of usage by stage name."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=100, output_tokens=50), agent_id="pm", stage="SPEC")
        tracker.record(
            TokenUsage(input_tokens=200, output_tokens=100),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )

        by_stage = tracker.get_by_stage()

        assert isinstance(by_stage, dict)
        assert len(by_stage) == 2
        assert "SPEC" in by_stage
        assert "IMPLEMENTATION" in by_stage

    def test_empty_tracker(self):
        """Empty tracker returns empty aggregations."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()

        total = tracker.get_total()
        by_agent = tracker.get_by_agent()
        by_stage = tracker.get_by_stage()

        # Total should be empty TokenUsage (all None)
        assert total.input_tokens is None
        assert total.output_tokens is None
        assert total.total_tokens is None
        assert by_agent == {}
        assert by_stage == {}

    def test_all_none_usage(self):
        """TokenTracker handles all tasks with None tokens."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(), agent_id="pm")  # All None
        tracker.record(TokenUsage(), agent_id="builder-1")  # All None

        total = tracker.get_total()
        assert total.total_tokens is None

    def test_mixed_availability(self):
        """TokenTracker handles mix of available and unavailable tokens."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=100, output_tokens=50), agent_id="pm")
        tracker.record(TokenUsage(), agent_id="builder-1")  # None tokens
        tracker.record(TokenUsage(input_tokens=200, output_tokens=100), agent_id="reviewer")

        total = tracker.get_total()
        # Should sum available tokens, ignore None
        assert total.input_tokens == 300  # 100 + 0 + 200
        assert total.output_tokens == 150  # 50 + 0 + 100

    def test_reset(self):
        """reset() clears all recorded data."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=100, output_tokens=50), agent_id="pm")

        tracker.reset()

        total = tracker.get_total()
        by_agent = tracker.get_by_agent()

        assert total.total_tokens is None
        assert by_agent == {}

    def test_record_with_none_usage(self):
        """record() handles None usage gracefully."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()

        # Should not raise
        tracker.record(None, agent_id="pm")

        total = tracker.get_total()
        assert total.total_tokens is None

    def test_record_without_stage(self):
        """record() works without stage parameter."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=100, output_tokens=50), agent_id="pm")

        by_stage = tracker.get_by_stage()
        # Without stage, no stage breakdown
        assert by_stage == {}

    def test_to_dict_serialization(self):
        """to_dict() produces serializable dict for persistence."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=100, output_tokens=50), agent_id="pm", stage="SPEC")
        tracker.record(
            TokenUsage(input_tokens=200, output_tokens=100),
            agent_id="builder-1",
            stage="IMPLEMENTATION",
        )

        result = tracker.to_dict()

        assert "schema_version" in result
        assert result["schema_version"] == "1.0"
        assert "total" in result
        assert "by_agent" in result
        assert "by_stage" in result
        assert result["total"]["total_tokens"] == 450
        assert "pm" in result["by_agent"]
        assert "SPEC" in result["by_stage"]

    def test_warning_flag_tracks_single_warning(self):
        """_warning_logged flag prevents duplicate warnings."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()

        assert tracker._warning_logged is False

        # Simulate recording with unavailable data
        tracker.record(None, agent_id="pm")

        # The flag doesn't auto-set, but can be set externally
        tracker._warning_logged = True
        assert tracker._warning_logged is True

    def test_multiple_agents_same_stage(self):
        """Multiple agents can contribute to same stage."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(TokenUsage(input_tokens=100, output_tokens=50), agent_id="pm", stage="SPEC")
        tracker.record(TokenUsage(input_tokens=200, output_tokens=100), agent_id="ba", stage="SPEC")

        by_stage = tracker.get_by_stage()

        assert by_stage["SPEC"].input_tokens == 300
        assert by_stage["SPEC"].output_tokens == 150

    def test_cache_tokens_aggregation(self):
        """Cache tokens are tracked and aggregated."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()
        tracker.record(
            TokenUsage(
                input_tokens=100, output_tokens=50, cache_read_tokens=10, cache_write_tokens=5
            ),
            agent_id="pm",
        )
        tracker.record(
            TokenUsage(
                input_tokens=200, output_tokens=100, cache_read_tokens=20, cache_write_tokens=10
            ),
            agent_id="builder-1",
        )

        total = tracker.get_total()

        assert total.cache_read_tokens == 30
        assert total.cache_write_tokens == 15

    def test_should_warn_unavailable_returns_true_first_time(self):
        """should_warn_unavailable() returns True the first time."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()

        # First call should return True
        assert tracker.should_warn_unavailable() is True

    def test_should_warn_unavailable_returns_false_after_first(self):
        """should_warn_unavailable() returns False on subsequent calls."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()

        # First call
        tracker.should_warn_unavailable()

        # Second and subsequent calls should return False
        assert tracker.should_warn_unavailable() is False
        assert tracker.should_warn_unavailable() is False

    def test_should_warn_unavailable_resets_with_reset(self):
        """should_warn_unavailable() flag resets when reset() is called."""
        from teambot.tokens.tracker import TokenTracker

        tracker = TokenTracker()

        # Use up the warning
        tracker.should_warn_unavailable()
        assert tracker.should_warn_unavailable() is False

        # Reset the tracker
        tracker.reset()

        # Warning should be available again
        assert tracker.should_warn_unavailable() is True
