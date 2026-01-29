"""Centralized agent state management for TeamBot UI.

Provides a single source of truth for agent status, enabling reactive
updates across UI components.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class AgentState(Enum):
    """Possible states for an agent."""

    IDLE = "idle"
    RUNNING = "running"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentStatus:
    """Status information for a single agent.

    Attributes:
        agent_id: Unique identifier for the agent.
        state: Current state of the agent.
        task: Current task description (truncated for display).
    """

    agent_id: str
    state: AgentState = AgentState.IDLE
    task: str | None = None

    def with_state(self, state: AgentState, task: str | None = None) -> "AgentStatus":
        """Create a new AgentStatus with updated state.

        Args:
            state: New state for the agent.
            task: Optional task description. If None, preserves existing task.

        Returns:
            New AgentStatus instance with updated values.
        """
        return AgentStatus(
            agent_id=self.agent_id,
            state=state,
            task=task if task is not None else self.task,
        )


# Default agent IDs
DEFAULT_AGENTS = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]


@dataclass
class AgentStatusManager:
    """Manages agent status with change notification support.

    Provides a centralized state store that can notify listeners
    when agent status changes, enabling reactive UI updates.

    Attributes:
        _statuses: Internal dict mapping agent_id to AgentStatus.
        _listeners: Callbacks invoked on status changes.
    """

    _statuses: dict[str, AgentStatus] = field(default_factory=dict)
    _listeners: list[Callable[["AgentStatusManager"], None]] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default agent statuses."""
        if not self._statuses:
            for agent_id in DEFAULT_AGENTS:
                self._statuses[agent_id] = AgentStatus(agent_id=agent_id)

    def get(self, agent_id: str) -> AgentStatus | None:
        """Get status for a specific agent.

        Args:
            agent_id: The agent to look up.

        Returns:
            AgentStatus if found, None otherwise.
        """
        return self._statuses.get(agent_id)

    def get_all(self) -> dict[str, AgentStatus]:
        """Get all agent statuses.

        Returns:
            Dict mapping agent_id to AgentStatus.
        """
        return self._statuses.copy()

    def set_running(self, agent_id: str, task: str) -> None:
        """Mark an agent as running a task.

        Args:
            agent_id: The agent starting a task.
            task: Description of the task (will be truncated to 40 chars).
        """
        truncated_task = task[:40] + "..." if len(task) > 40 else task
        self._update(agent_id, AgentState.RUNNING, truncated_task)

    def set_streaming(self, agent_id: str) -> None:
        """Mark an agent as streaming output.

        Args:
            agent_id: The agent that started streaming.
        """
        current = self._statuses.get(agent_id)
        task = current.task if current else None
        self._update(agent_id, AgentState.STREAMING, task)

    def set_completed(self, agent_id: str) -> None:
        """Mark an agent as completed.

        Args:
            agent_id: The agent that completed its task.
        """
        self._update(agent_id, AgentState.COMPLETED, None)

    def set_failed(self, agent_id: str) -> None:
        """Mark an agent as failed.

        Args:
            agent_id: The agent that failed.
        """
        self._update(agent_id, AgentState.FAILED, None)

    def set_idle(self, agent_id: str) -> None:
        """Mark an agent as idle and clear its task.

        Args:
            agent_id: The agent to mark idle.
        """
        if agent_id not in self._statuses:
            self._statuses[agent_id] = AgentStatus(agent_id=agent_id)
            return

        old_status = self._statuses[agent_id]
        # Explicitly create new status with cleared task
        new_status = AgentStatus(
            agent_id=agent_id,
            state=AgentState.IDLE,
            task=None,
        )

        if old_status.state != new_status.state or old_status.task != new_status.task:
            self._statuses[agent_id] = new_status
            self._notify()

    def _update(self, agent_id: str, state: AgentState, task: str | None) -> None:
        """Update agent status and notify listeners.

        Args:
            agent_id: The agent to update.
            state: New state.
            task: Task description or None.
        """
        if agent_id not in self._statuses:
            self._statuses[agent_id] = AgentStatus(agent_id=agent_id)

        old_status = self._statuses[agent_id]
        new_status = old_status.with_state(state, task)

        # Only notify if something changed
        if old_status.state != new_status.state or old_status.task != new_status.task:
            self._statuses[agent_id] = new_status
            self._notify()

    def _notify(self) -> None:
        """Notify all listeners of state change."""
        for listener in self._listeners:
            try:
                listener(self)
            except Exception:
                pass  # Don't let listener errors break state management

    def add_listener(self, callback: Callable[["AgentStatusManager"], None]) -> None:
        """Register a callback for status changes.

        Args:
            callback: Function called with this manager when status changes.
        """
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[["AgentStatusManager"], None]) -> None:
        """Unregister a status change callback.

        Args:
            callback: Previously registered callback to remove.
        """
        if callback in self._listeners:
            self._listeners.remove(callback)

    def get_streaming_agents(self) -> list[str]:
        """Get list of agents currently streaming.

        Returns:
            List of agent IDs with streaming state.
        """
        return [
            agent_id
            for agent_id, status in self._statuses.items()
            if status.state == AgentState.STREAMING
        ]

    def get_running_agents(self) -> list[str]:
        """Get list of agents currently running (not streaming).

        Returns:
            List of agent IDs with running state.
        """
        return [
            agent_id
            for agent_id, status in self._statuses.items()
            if status.state == AgentState.RUNNING
        ]

    def get_active_agents(self) -> list[str]:
        """Get list of agents that are running or streaming.

        Returns:
            List of agent IDs with running or streaming state.
        """
        return [
            agent_id
            for agent_id, status in self._statuses.items()
            if status.state in (AgentState.RUNNING, AgentState.STREAMING)
        ]
