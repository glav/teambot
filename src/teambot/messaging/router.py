"""Message router for directing messages between agents."""

from __future__ import annotations

from multiprocessing import Queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from teambot.messaging.protocol import AgentMessage


class RoutingError(Exception):
    """Raised when message routing fails."""

    pass


class MessageRouter:
    """Routes messages between agents via their queues."""

    def __init__(self):
        self.agent_queues: dict[str, Queue] = {}
        self._timeout = 5.0

    def register_agent(self, agent_id: str, queue: Queue) -> None:
        """Register an agent's queue for message delivery."""
        self.agent_queues[agent_id] = queue

    def unregister_agent(self, agent_id: str) -> None:
        """Remove an agent from routing."""
        self.agent_queues.pop(agent_id, None)

    def get_registered_agents(self) -> list[str]:
        """Return list of registered agent IDs."""
        return list(self.agent_queues.keys())

    def route(self, message: AgentMessage) -> None:
        """Route a message to the target agent(s)."""
        target = message.target_agent

        if target == "all":
            # Broadcast to all agents
            for queue in self.agent_queues.values():
                queue.put(message)
        elif target in self.agent_queues:
            # Route to specific agent
            self.agent_queues[target].put(message)
        else:
            raise RoutingError(f"Unknown target agent: {target}")
