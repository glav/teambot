"""Tests for AgentStatusManager and related classes."""

from teambot.ui.agent_state import (
    DEFAULT_AGENTS,
    AgentState,
    AgentStatus,
    AgentStatusManager,
)


class TestAgentStatus:
    """Tests for AgentStatus dataclass."""

    def test_default_state_is_idle(self):
        """New AgentStatus defaults to idle state."""
        status = AgentStatus(agent_id="pm")
        assert status.state == AgentState.IDLE
        assert status.task is None

    def test_with_state_creates_new_instance(self):
        """with_state returns new instance, doesn't mutate original."""
        original = AgentStatus(agent_id="pm", state=AgentState.IDLE)
        updated = original.with_state(AgentState.RUNNING, "test task")

        assert original.state == AgentState.IDLE
        assert original.task is None
        assert updated.state == AgentState.RUNNING
        assert updated.task == "test task"
        assert updated.agent_id == "pm"

    def test_with_state_preserves_task_if_not_provided(self):
        """with_state keeps existing task when new task is None."""
        original = AgentStatus(agent_id="pm", state=AgentState.RUNNING, task="old task")
        updated = original.with_state(AgentState.STREAMING)

        assert updated.task == "old task"


class TestAgentStatusManager:
    """Tests for AgentStatusManager."""

    def test_initializes_with_default_agents(self):
        """Manager initializes all default agents as idle."""
        manager = AgentStatusManager()

        for agent_id in DEFAULT_AGENTS:
            status = manager.get(agent_id)
            assert status is not None
            assert status.state == AgentState.IDLE

    def test_get_returns_none_for_unknown_agent(self):
        """get() returns None for non-existent agent."""
        manager = AgentStatusManager()
        assert manager.get("unknown-agent") is None

    def test_set_running_updates_state(self):
        """set_running changes agent to running state with task."""
        manager = AgentStatusManager()
        manager.set_running("pm", "plan authentication")

        status = manager.get("pm")
        assert status.state == AgentState.RUNNING
        assert status.task == "plan authentication"

    def test_set_running_truncates_long_task(self):
        """set_running truncates task to 40 chars + ellipsis."""
        manager = AgentStatusManager()
        long_task = "a" * 50
        manager.set_running("pm", long_task)

        status = manager.get("pm")
        assert status.task == "a" * 40 + "..."
        assert len(status.task) == 43

    def test_set_streaming_updates_state(self):
        """set_streaming changes agent to streaming state."""
        manager = AgentStatusManager()
        manager.set_running("pm", "some task")
        manager.set_streaming("pm")

        status = manager.get("pm")
        assert status.state == AgentState.STREAMING
        # Task should be preserved
        assert status.task == "some task"

    def test_set_completed_updates_state(self):
        """set_completed changes agent to completed state."""
        manager = AgentStatusManager()
        manager.set_running("pm", "task")
        manager.set_completed("pm")

        status = manager.get("pm")
        assert status.state == AgentState.COMPLETED

    def test_set_failed_updates_state(self):
        """set_failed changes agent to failed state."""
        manager = AgentStatusManager()
        manager.set_running("pm", "task")
        manager.set_failed("pm")

        status = manager.get("pm")
        assert status.state == AgentState.FAILED

    def test_set_idle_resets_state(self):
        """set_idle returns agent to idle state."""
        manager = AgentStatusManager()
        manager.set_running("pm", "task")
        manager.set_idle("pm")

        status = manager.get("pm")
        assert status.state == AgentState.IDLE
        assert status.task is None

    def test_get_all_returns_copy(self):
        """get_all returns dict copy, not internal reference."""
        manager = AgentStatusManager()
        all_statuses = manager.get_all()

        # Modifying returned dict shouldn't affect manager
        all_statuses["pm"] = AgentStatus(agent_id="pm", state=AgentState.FAILED)

        assert manager.get("pm").state == AgentState.IDLE

    def test_get_streaming_agents(self):
        """get_streaming_agents returns only streaming agents."""
        manager = AgentStatusManager()
        manager.set_streaming("pm")
        manager.set_running("ba", "task")
        manager.set_streaming("builder-1")

        streaming = manager.get_streaming_agents()
        assert set(streaming) == {"pm", "builder-1"}

    def test_get_running_agents(self):
        """get_running_agents returns only running (not streaming) agents."""
        manager = AgentStatusManager()
        manager.set_running("pm", "task")
        manager.set_running("ba", "task")
        manager.set_streaming("ba")  # ba transitions to streaming

        running = manager.get_running_agents()
        assert running == ["pm"]

    def test_get_active_agents(self):
        """get_active_agents returns running and streaming agents."""
        manager = AgentStatusManager()
        manager.set_running("pm", "task")
        manager.set_streaming("ba")

        active = manager.get_active_agents()
        assert set(active) == {"pm", "ba"}


class TestAgentStatusManagerListeners:
    """Tests for listener/callback functionality."""

    def test_listener_called_on_state_change(self):
        """Listener is called when agent state changes."""
        manager = AgentStatusManager()
        calls = []

        def listener(mgr):
            calls.append(mgr.get("pm").state)

        manager.add_listener(listener)
        manager.set_running("pm", "task")

        assert len(calls) == 1
        assert calls[0] == AgentState.RUNNING

    def test_listener_not_called_when_no_change(self):
        """Listener is not called if state doesn't actually change."""
        manager = AgentStatusManager()
        calls = []

        manager.set_idle("pm")  # Already idle

        def listener(mgr):
            calls.append(True)

        manager.add_listener(listener)
        manager.set_idle("pm")  # No change

        assert len(calls) == 0

    def test_multiple_listeners_called(self):
        """All registered listeners are called on change."""
        manager = AgentStatusManager()
        calls1 = []
        calls2 = []

        manager.add_listener(lambda m: calls1.append(1))
        manager.add_listener(lambda m: calls2.append(2))

        manager.set_running("pm", "task")

        assert calls1 == [1]
        assert calls2 == [2]

    def test_remove_listener(self):
        """Removed listener is no longer called."""
        manager = AgentStatusManager()
        calls = []

        def listener(mgr):
            calls.append(1)

        manager.add_listener(listener)
        manager.set_running("pm", "task")
        assert len(calls) == 1

        manager.remove_listener(listener)
        manager.set_streaming("pm")
        assert len(calls) == 1  # Still 1, not called again

    def test_listener_error_doesnt_break_manager(self):
        """Listener exception doesn't prevent state updates."""
        manager = AgentStatusManager()

        def bad_listener(mgr):
            raise ValueError("Oops")

        manager.add_listener(bad_listener)
        manager.set_running("pm", "task")  # Should not raise

        # State should still be updated
        assert manager.get("pm").state == AgentState.RUNNING

    def test_add_same_listener_twice_only_registers_once(self):
        """Adding same listener twice doesn't duplicate calls."""
        manager = AgentStatusManager()
        calls = []

        def listener(mgr):
            calls.append(1)

        manager.add_listener(listener)
        manager.add_listener(listener)

        manager.set_running("pm", "task")
        assert calls == [1]  # Only one call


class TestAgentStatusModel:
    """Tests for model field in AgentStatus."""

    def test_agent_status_with_model(self):
        """AgentStatus can be created with model."""
        status = AgentStatus(agent_id="pm", model="gpt-5")
        assert status.model == "gpt-5"

    def test_agent_status_model_defaults_to_none(self):
        """AgentStatus.model defaults to None."""
        status = AgentStatus(agent_id="pm")
        assert status.model is None

    def test_with_state_preserves_model(self):
        """with_state() preserves model field."""
        status = AgentStatus(agent_id="pm", model="gpt-5")
        new_status = status.with_state(AgentState.RUNNING, task="test")
        assert new_status.model == "gpt-5"

    def test_with_model_creates_new_status(self):
        """with_model() creates new status with different model."""
        status = AgentStatus(agent_id="pm", model="gpt-5")
        new_status = status.with_model("claude-opus-4.5")
        assert new_status.model == "claude-opus-4.5"
        assert status.model == "gpt-5"  # Original unchanged


class TestAgentStatusManagerModel:
    """Tests for model in AgentStatusManager."""

    def test_set_model_updates_agent(self):
        """set_model() updates agent's model."""
        manager = AgentStatusManager()
        manager.set_model("pm", "claude-opus-4.5")
        assert manager.get("pm").model == "claude-opus-4.5"

    def test_set_model_notifies_listeners(self):
        """set_model() triggers listener notification."""
        manager = AgentStatusManager()
        notified = []
        manager.add_listener(lambda m: notified.append(True))

        manager.set_model("pm", "gpt-5")
        assert len(notified) == 1
