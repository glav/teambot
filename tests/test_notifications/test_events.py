"""Tests for NotificationEvent dataclass."""

from __future__ import annotations

from datetime import datetime

from teambot.notifications.events import NotificationEvent


class TestNotificationEvent:
    """Tests for NotificationEvent creation and defaults."""

    def test_create_with_required_fields(self) -> None:
        """Event can be created with just required fields."""
        event = NotificationEvent(
            event_type="stage_changed",
            data={"stage": "SETUP"},
        )

        assert event.event_type == "stage_changed"
        assert event.data == {"stage": "SETUP"}
        assert event.timestamp is not None
        assert event.stage is None
        assert event.agent is None
        assert event.feature_name is None

    def test_create_with_all_fields(self) -> None:
        """Event can be created with all optional fields."""
        ts = datetime(2026, 2, 11, 12, 0, 0)
        event = NotificationEvent(
            event_type="agent_failed",
            data={"agent_id": "builder-1", "error": "Test error"},
            timestamp=ts,
            stage="IMPLEMENTATION",
            agent="builder-1",
            feature_name="my-feature",
        )

        assert event.event_type == "agent_failed"
        assert event.data["agent_id"] == "builder-1"
        assert event.timestamp == ts
        assert event.stage == "IMPLEMENTATION"
        assert event.agent == "builder-1"
        assert event.feature_name == "my-feature"

    def test_default_timestamp_generated(self) -> None:
        """Timestamp is auto-generated when not provided."""
        before = datetime.now()
        event = NotificationEvent(event_type="test", data={})
        after = datetime.now()

        assert before <= event.timestamp <= after

    def test_empty_data_dict(self) -> None:
        """Event handles empty data dict."""
        event = NotificationEvent(event_type="test", data={})

        assert event.data == {}
