"""Tests for MessageTemplates."""

from __future__ import annotations

import pytest

from teambot.notifications.events import NotificationEvent
from teambot.notifications.templates import STATUS_EMOJI, MessageTemplates


class TestMessageTemplates:
    """Tests for MessageTemplates.render()."""

    @pytest.fixture
    def templates(self) -> MessageTemplates:
        """Create MessageTemplates instance."""
        return MessageTemplates()

    def test_render_stage_changed(self, templates: MessageTemplates) -> None:
        """Render stage_changed event."""
        event = NotificationEvent(
            event_type="stage_changed",
            data={"stage": "IMPLEMENTATION"},
            feature_name="my-feature",
        )

        result = templates.render(event)

        assert "Stage: IMPLEMENTATION" in result
        assert "my-feature" in result

    def test_render_agent_complete(self, templates: MessageTemplates) -> None:
        """Render agent_complete event."""
        event = NotificationEvent(
            event_type="agent_complete",
            data={"agent_id": "builder-1"},
        )

        result = templates.render(event)

        assert "builder-1" in result
        assert "completed" in result

    def test_render_agent_failed(self, templates: MessageTemplates) -> None:
        """Render agent_failed event."""
        event = NotificationEvent(
            event_type="agent_failed",
            data={"agent_id": "pm"},
            feature_name="test-feature",
        )

        result = templates.render(event)

        assert "pm" in result
        assert "FAILED" in result

    def test_render_parallel_group_complete_success(self, templates: MessageTemplates) -> None:
        """Render parallel_group_complete with all_success=True."""
        event = NotificationEvent(
            event_type="parallel_group_complete",
            data={"group": "post_spec", "all_success": True},
        )

        result = templates.render(event)

        assert STATUS_EMOJI["success"] in result
        assert "All passed" in result

    def test_render_parallel_group_complete_failure(self, templates: MessageTemplates) -> None:
        """Render parallel_group_complete with all_success=False."""
        event = NotificationEvent(
            event_type="parallel_group_complete",
            data={"group": "post_spec", "all_success": False},
        )

        result = templates.render(event)

        assert STATUS_EMOJI["warning"] in result
        assert "Some failed" in result

    def test_render_acceptance_test_passed(self, templates: MessageTemplates) -> None:
        """Render acceptance_test_stage_complete with no failures."""
        event = NotificationEvent(
            event_type="acceptance_test_stage_complete",
            data={"passed": 10, "failed": 0, "total": 10},
            feature_name="test",
        )

        result = templates.render(event)

        assert STATUS_EMOJI["success"] in result
        assert "10/10" in result

    def test_render_acceptance_test_failed(self, templates: MessageTemplates) -> None:
        """Render acceptance_test_stage_complete with failures."""
        event = NotificationEvent(
            event_type="acceptance_test_stage_complete",
            data={"passed": 7, "failed": 3, "total": 10},
            feature_name="test",
        )

        result = templates.render(event)

        assert STATUS_EMOJI["failure"] in result

    def test_render_stages_list(self, templates: MessageTemplates) -> None:
        """Render event with stages list."""
        event = NotificationEvent(
            event_type="parallel_group_start",
            data={"group": "test", "stages": ["RESEARCH", "TEST_STRATEGY"]},
        )

        result = templates.render(event)

        assert "RESEARCH, TEST_STRATEGY" in result

    def test_render_unknown_event_fallback(self, templates: MessageTemplates) -> None:
        """Unknown event type uses fallback template."""
        event = NotificationEvent(
            event_type="unknown_event",
            data={"custom": "data"},
            feature_name="test",
        )

        result = templates.render(event)

        assert "unknown_event" in result
        assert "test" in result

    def test_render_missing_key_handled(self, templates: MessageTemplates) -> None:
        """Missing template keys are handled gracefully."""
        event = NotificationEvent(
            event_type="agent_running",
            data={},  # Missing agent_id and task
        )

        result = templates.render(event)

        # Should not raise, should include "Missing" info
        assert "Missing" in result or "Event:" in result
