"""Tests for notification mode definitions."""

from __future__ import annotations

import pytest

from teambot.notifications.modes import (
    AGENT_STATUS_EVENTS,
    NOTIFICATION_MODES,
    STAGES_ONLY_EVENTS,
    resolve_notification_mode,
)


class TestNotificationModeConstants:
    """Tests for notification mode constant definitions."""

    def test_notification_modes_has_three_modes(self) -> None:
        """NOTIFICATION_MODES contains exactly three mode definitions."""
        assert len(NOTIFICATION_MODES) == 3
        assert "stages_only" in NOTIFICATION_MODES
        assert "agent_status" in NOTIFICATION_MODES
        assert "all" in NOTIFICATION_MODES

    def test_stages_only_contains_stage_events(self) -> None:
        """stages_only mode contains exactly 3 stage lifecycle events."""
        assert "stage_changed" in STAGES_ONLY_EVENTS
        assert "orchestration_started" in STAGES_ONLY_EVENTS
        assert "orchestration_completed" in STAGES_ONLY_EVENTS
        assert len(STAGES_ONLY_EVENTS) == 3

    def test_agent_status_is_superset_of_stages_only(self) -> None:
        """agent_status mode includes all stages_only events plus agent events."""
        assert STAGES_ONLY_EVENTS.issubset(AGENT_STATUS_EVENTS)
        assert "agent_running" in AGENT_STATUS_EVENTS
        assert "agent_complete" in AGENT_STATUS_EVENTS
        assert "agent_failed" in AGENT_STATUS_EVENTS
        assert len(AGENT_STATUS_EVENTS) == 6

    def test_all_mode_is_none(self) -> None:
        """all mode maps to None (no filtering)."""
        assert NOTIFICATION_MODES["all"] is None


class TestResolveNotificationMode:
    """Tests for resolve_notification_mode function."""

    def test_resolve_stages_only_returns_event_set(self) -> None:
        """resolve_notification_mode('stages_only') returns stage events."""
        result = resolve_notification_mode("stages_only")

        assert result is not None
        assert "stage_changed" in result
        assert len(result) == 3

    def test_resolve_agent_status_returns_event_set(self) -> None:
        """resolve_notification_mode('agent_status') returns agent events."""
        result = resolve_notification_mode("agent_status")

        assert result is not None
        assert "agent_running" in result
        assert len(result) == 6

    def test_resolve_all_returns_none(self) -> None:
        """resolve_notification_mode('all') returns None (no filter)."""
        result = resolve_notification_mode("all")

        assert result is None

    def test_invalid_mode_raises_value_error(self) -> None:
        """Invalid mode raises ValueError with valid modes listed."""
        with pytest.raises(ValueError) as exc_info:
            resolve_notification_mode("invalid_mode")

        error_msg = str(exc_info.value)
        assert "invalid_mode" in error_msg
        assert "stages_only" in error_msg
        assert "agent_status" in error_msg
        assert "all" in error_msg

    def test_non_string_mode_raises_value_error(self) -> None:
        """Non-string mode raises ValueError with helpful message."""
        with pytest.raises(ValueError) as exc_info:
            resolve_notification_mode(123)  # type: ignore[arg-type]

        error_msg = str(exc_info.value)
        assert "must be a string" in error_msg
        assert "int" in error_msg
        assert "Valid modes:" in error_msg

    def test_list_mode_raises_value_error(self) -> None:
        """List mode raises ValueError with type information."""
        with pytest.raises(ValueError) as exc_info:
            resolve_notification_mode(["stages_only"])  # type: ignore[arg-type]

        error_msg = str(exc_info.value)
        assert "must be a string" in error_msg
        assert "list" in error_msg

    def test_dict_mode_raises_value_error(self) -> None:
        """Dict mode raises ValueError with type information."""
        with pytest.raises(ValueError) as exc_info:
            resolve_notification_mode({"mode": "all"})  # type: ignore[arg-type]

        error_msg = str(exc_info.value)
        assert "must be a string" in error_msg
        assert "dict" in error_msg

    def test_bool_mode_raises_value_error(self) -> None:
        """Boolean mode raises ValueError with type information."""
        with pytest.raises(ValueError) as exc_info:
            resolve_notification_mode(True)  # type: ignore[arg-type]

        error_msg = str(exc_info.value)
        assert "must be a string" in error_msg
        assert "bool" in error_msg

    def test_none_mode_raises_value_error(self) -> None:
        """None mode raises ValueError with type information."""
        with pytest.raises(ValueError) as exc_info:
            resolve_notification_mode(None)  # type: ignore[arg-type]

        error_msg = str(exc_info.value)
        assert "must be a string" in error_msg
        assert "NoneType" in error_msg
