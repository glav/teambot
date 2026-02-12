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

    def test_render_escapes_html_in_feature_name(self, templates: MessageTemplates) -> None:
        """HTML characters in feature_name are escaped."""
        event = NotificationEvent(
            event_type="stage_changed",
            data={"stage": "IMPLEMENTATION"},
            feature_name="<script>alert('xss')</script>",
        )

        result = templates.render(event)

        # HTML should be escaped
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_render_escapes_html_in_agent_id(self, templates: MessageTemplates) -> None:
        """HTML characters in agent_id are escaped."""
        event = NotificationEvent(
            event_type="agent_running",
            data={"agent_id": "builder<>&", "task": "test"},
        )

        result = templates.render(event)

        # HTML should be escaped
        assert "&lt;&gt;&amp;" in result
        assert "builder<>&" not in result

    def test_render_escapes_html_in_task(self, templates: MessageTemplates) -> None:
        """HTML characters in task are escaped."""
        event = NotificationEvent(
            event_type="agent_running",
            data={"agent_id": "builder", "task": "Fix <bug> & test"},
        )

        result = templates.render(event)

        # HTML should be escaped
        assert "&lt;bug&gt; &amp;" in result
        assert "<bug> &" not in result

    def test_render_escapes_html_in_stage(self, templates: MessageTemplates) -> None:
        """HTML characters in stage are escaped."""
        event = NotificationEvent(
            event_type="stage_changed",
            data={},
            stage="TEST<>STAGE",
            feature_name="test",
        )

        result = templates.render(event)

        # HTML should be escaped
        assert "TEST&lt;&gt;STAGE" in result
        assert "TEST<>STAGE" not in result

    def test_render_escapes_html_in_stages_list(self, templates: MessageTemplates) -> None:
        """HTML characters in stages list are escaped."""
        event = NotificationEvent(
            event_type="parallel_group_start",
            data={"group": "test", "stages": ["STAGE<1>", "STAGE&2"]},
        )

        result = templates.render(event)

        # HTML should be escaped
        assert "STAGE&lt;1&gt;" in result
        assert "STAGE&amp;2" in result
        assert "STAGE<1>" not in result

    def test_render_escapes_html_in_message(self, templates: MessageTemplates) -> None:
        """HTML characters in message are escaped."""
        event = NotificationEvent(
            event_type="review_progress",
            data={"message": "Found <issue> & fixed it"},
            stage="REVIEW",
        )

        result = templates.render(event)

        # HTML should be escaped
        assert "&lt;issue&gt; &amp;" in result
        assert "<issue> &" not in result

    def test_render_preserves_numeric_values(self, templates: MessageTemplates) -> None:
        """Numeric values are not affected by escaping."""
        event = NotificationEvent(
            event_type="acceptance_test_stage_complete",
            data={"passed": 10, "failed": 0, "total": 10},
            feature_name="test",
        )

        result = templates.render(event)

        # Numeric values should work fine
        assert "10/10" in result


class TestOrchestrationStartedTemplate:
    """Tests for orchestration_started template rendering."""

    @pytest.fixture
    def templates(self) -> MessageTemplates:
        return MessageTemplates()

    def test_render_with_objective_name(self, templates: MessageTemplates) -> None:
        """Renders with objective name when provided."""
        event = NotificationEvent(
            event_type="orchestration_started",
            data={"objective_name": "my-feature", "objective_path": "/path/to/obj.md"},
        )
        result = templates.render(event)
        assert "🚀" in result
        assert "Starting" in result
        assert "my-feature" in result

    def test_render_fallback_when_name_missing(self, templates: MessageTemplates) -> None:
        """Falls back to generic text when objective_name missing."""
        event = NotificationEvent(
            event_type="orchestration_started",
            data={"objective_path": "/path/to/obj.md"},
        )
        result = templates.render(event)
        assert "orchestration run" in result.lower()

    def test_render_fallback_when_name_empty(self, templates: MessageTemplates) -> None:
        """Falls back to generic text when objective_name is empty string."""
        event = NotificationEvent(
            event_type="orchestration_started",
            data={"objective_name": "", "objective_path": "/path/to/obj.md"},
        )
        result = templates.render(event)
        assert "orchestration run" in result.lower()

    def test_escapes_html_in_objective_name(self, templates: MessageTemplates) -> None:
        """HTML characters in objective_name are escaped."""
        event = NotificationEvent(
            event_type="orchestration_started",
            data={"objective_name": "<script>alert('xss')</script>"},
        )
        result = templates.render(event)
        assert "&lt;script&gt;" in result
        assert "<script>" not in result


class TestOrchestrationCompletedTemplate:
    """Tests for orchestration_completed template rendering."""

    @pytest.fixture
    def templates(self) -> MessageTemplates:
        return MessageTemplates()

    def test_render_with_duration(self, templates: MessageTemplates) -> None:
        """Renders with formatted duration."""
        event = NotificationEvent(
            event_type="orchestration_completed",
            data={
                "objective_name": "my-feature",
                "duration_seconds": 125,  # 2m 5s
            },
        )
        result = templates.render(event)
        assert "✅" in result
        assert "Completed" in result
        assert "my-feature" in result
        assert "2m 5s" in result

    def test_render_fallback_when_name_missing(self, templates: MessageTemplates) -> None:
        """Falls back to generic text when objective_name missing."""
        event = NotificationEvent(
            event_type="orchestration_completed",
            data={"duration_seconds": 60},
        )
        result = templates.render(event)
        assert "orchestration run" in result.lower()

    def test_render_fallback_when_name_empty(self, templates: MessageTemplates) -> None:
        """Falls back to generic text when objective_name is empty string."""
        event = NotificationEvent(
            event_type="orchestration_completed",
            data={"objective_name": "", "duration_seconds": 60},
        )
        result = templates.render(event)
        assert "orchestration run" in result.lower()

    def test_duration_zero_seconds(self, templates: MessageTemplates) -> None:
        """Handles zero duration gracefully."""
        event = NotificationEvent(
            event_type="orchestration_completed",
            data={"objective_name": "test", "duration_seconds": 0},
        )
        result = templates.render(event)
        assert "0m 0s" in result

    def test_duration_large_value(self, templates: MessageTemplates) -> None:
        """Handles large duration values."""
        event = NotificationEvent(
            event_type="orchestration_completed",
            data={"objective_name": "test", "duration_seconds": 7265},  # 2h 1m 5s
        )
        result = templates.render(event)
        # Should show 121m 5s (minutes only, no hours)
        assert "121m 5s" in result

    def test_escapes_html_in_objective_name(self, templates: MessageTemplates) -> None:
        """HTML characters in objective_name are escaped."""
        event = NotificationEvent(
            event_type="orchestration_completed",
            data={"objective_name": "<b>test</b>", "duration_seconds": 60},
        )
        result = templates.render(event)
        assert "&lt;b&gt;test&lt;/b&gt;" in result
        assert "<b>test</b>" not in result


class TestCustomMessageTemplate:
    """Tests for custom_message template rendering."""

    @pytest.fixture
    def templates(self) -> MessageTemplates:
        return MessageTemplates()

    def test_render_user_message(self, templates: MessageTemplates) -> None:
        """Renders user message."""
        event = NotificationEvent(
            event_type="custom_message",
            data={"message": "Hello from TeamBot!"},
        )
        result = templates.render(event)
        assert "📢" in result
        assert "Hello from TeamBot!" in result

    def test_escapes_html_in_message(self, templates: MessageTemplates) -> None:
        """HTML in user message is escaped."""
        event = NotificationEvent(
            event_type="custom_message",
            data={"message": "<b>bold</b>"},
        )
        result = templates.render(event)
        assert "&lt;b&gt;bold&lt;/b&gt;" in result
        assert "<b>bold</b>" not in result

    def test_multiword_message(self, templates: MessageTemplates) -> None:
        """Renders multi-word message correctly."""
        event = NotificationEvent(
            event_type="custom_message",
            data={"message": "This is a test notification with multiple words"},
        )
        result = templates.render(event)
        assert "This is a test notification with multiple words" in result
