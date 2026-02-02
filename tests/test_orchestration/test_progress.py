"""Tests for progress callback utilities."""

from __future__ import annotations

from unittest.mock import Mock

from teambot.orchestration.progress import create_progress_callback
from teambot.ui.agent_state import AgentState, AgentStatusManager


class TestCreateProgressCallback:
    """Tests for create_progress_callback function."""

    def test_agent_running_event(self) -> None:
        """agent_running event sets agent to running state with task."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        callback("agent_running", {"agent_id": "pm", "task": "Planning project"})

        status = manager.get("pm")
        assert status is not None
        assert status.state == AgentState.RUNNING
        assert status.task == "Planning project"

    def test_agent_running_truncates_long_task(self) -> None:
        """agent_running event truncates task to 40 chars."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        long_task = "A" * 50
        callback("agent_running", {"agent_id": "pm", "task": long_task})

        status = manager.get("pm")
        assert status is not None
        assert len(status.task) == 43  # 40 chars + "..."
        assert status.task.endswith("...")

    def test_agent_streaming_event(self) -> None:
        """agent_streaming event sets agent to streaming state."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        # First set running with a task
        callback("agent_running", {"agent_id": "ba", "task": "Analyzing requirements"})
        # Then switch to streaming
        callback("agent_streaming", {"agent_id": "ba"})

        status = manager.get("ba")
        assert status is not None
        assert status.state == AgentState.STREAMING
        # Task should be preserved from running state
        assert status.task == "Analyzing requirements"

    def test_agent_complete_event(self) -> None:
        """agent_complete event sets agent to completed state."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        callback("agent_complete", {"agent_id": "writer"})

        status = manager.get("writer")
        assert status is not None
        assert status.state == AgentState.COMPLETED

    def test_agent_failed_event(self) -> None:
        """agent_failed event sets agent to failed state."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        callback("agent_failed", {"agent_id": "builder-1"})

        status = manager.get("builder-1")
        assert status is not None
        assert status.state == AgentState.FAILED

    def test_agent_cancelled_event(self) -> None:
        """agent_cancelled event sets agent to idle state."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        # First set to running
        callback("agent_running", {"agent_id": "builder-2", "task": "Building"})
        # Then cancel
        callback("agent_cancelled", {"agent_id": "builder-2"})

        status = manager.get("builder-2")
        assert status is not None
        assert status.state == AgentState.IDLE
        assert status.task is None

    def test_agent_idle_event(self) -> None:
        """agent_idle event sets agent to idle state."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        # First set to running
        callback("agent_running", {"agent_id": "reviewer", "task": "Reviewing code"})
        # Then idle
        callback("agent_idle", {"agent_id": "reviewer"})

        status = manager.get("reviewer")
        assert status is not None
        assert status.state == AgentState.IDLE
        assert status.task is None

    def test_stage_changed_event_with_callback(self) -> None:
        """stage_changed event calls on_stage callback when provided."""
        manager = AgentStatusManager()
        on_stage_mock = Mock()
        callback = create_progress_callback(manager, on_stage=on_stage_mock)

        callback("stage_changed", {"stage": "IMPLEMENTATION"})

        on_stage_mock.assert_called_once_with("IMPLEMENTATION")

    def test_stage_changed_event_without_callback(self) -> None:
        """stage_changed event does nothing when on_stage is None."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        # Should not raise an error
        callback("stage_changed", {"stage": "IMPLEMENTATION"})

    def test_time_update_event_with_callback(self) -> None:
        """time_update event calls on_time callback when provided."""
        manager = AgentStatusManager()
        on_time_mock = Mock()
        callback = create_progress_callback(manager, on_time=on_time_mock)

        callback("time_update", {"elapsed": "00:15:30", "remaining": "07:44:30"})

        on_time_mock.assert_called_once_with("00:15:30", "07:44:30")

    def test_time_update_event_without_callback(self) -> None:
        """time_update event does nothing when on_time is None."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        # Should not raise an error
        callback("time_update", {"elapsed": "00:15:30", "remaining": "07:44:30"})

    def test_unknown_event_type_ignored(self) -> None:
        """Unknown event types are safely ignored."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        # Should not raise an error
        callback("unknown_event", {"some": "data"})

    def test_multiple_events_in_sequence(self) -> None:
        """Progress callback handles sequence of events correctly."""
        manager = AgentStatusManager()
        on_stage_mock = Mock()
        on_time_mock = Mock()
        callback = create_progress_callback(
            manager, on_stage=on_stage_mock, on_time=on_time_mock
        )

        # Simulate a complete workflow
        callback("stage_changed", {"stage": "SETUP"})
        callback("agent_running", {"agent_id": "pm", "task": "Planning"})
        callback("agent_streaming", {"agent_id": "pm"})
        callback("time_update", {"elapsed": "00:01:00", "remaining": "07:59:00"})
        callback("agent_complete", {"agent_id": "pm"})
        callback("agent_idle", {"agent_id": "pm"})

        # Verify all callbacks were invoked
        on_stage_mock.assert_called_once_with("SETUP")
        on_time_mock.assert_called_once_with("00:01:00", "07:59:00")

        # Verify final state
        status = manager.get("pm")
        assert status is not None
        assert status.state == AgentState.IDLE

    def test_callback_returns_callable(self) -> None:
        """create_progress_callback returns a callable function."""
        manager = AgentStatusManager()
        callback = create_progress_callback(manager)

        assert callable(callback)
