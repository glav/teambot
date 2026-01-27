"""Tests for message router - TDD approach."""

from multiprocessing import Queue

import pytest


class TestMessageRouter:
    """Tests for MessageRouter class."""

    def test_create_router(self):
        """Router should be instantiable."""
        from teambot.messaging.router import MessageRouter

        router = MessageRouter()
        assert router is not None
        assert hasattr(router, "agent_queues")

    def test_register_agent_queue(self):
        """Router should track agent queues."""
        from teambot.messaging.router import MessageRouter

        router = MessageRouter()
        queue = Queue()

        router.register_agent("builder-1", queue)

        assert "builder-1" in router.agent_queues
        assert router.agent_queues["builder-1"] is queue

    def test_route_to_specific_agent(self):
        """Messages with target should go to that agent's queue."""
        from teambot.messaging.protocol import AgentMessage, MessageType
        from teambot.messaging.router import MessageRouter

        router = MessageRouter()
        queue = Queue()
        router.register_agent("builder-1", queue)

        msg = AgentMessage(
            type=MessageType.TASK_ASSIGN,
            source_agent="orchestrator",
            target_agent="builder-1",
            payload={"task": "test"},
        )

        router.route(msg)

        received = queue.get(timeout=1)
        assert received.payload["task"] == "test"

    def test_broadcast_to_all_agents(self):
        """Messages with 'all' target should broadcast to all agents."""
        from teambot.messaging.protocol import AgentMessage, MessageType
        from teambot.messaging.router import MessageRouter

        router = MessageRouter()
        q1, q2 = Queue(), Queue()
        router.register_agent("agent-1", q1)
        router.register_agent("agent-2", q2)

        msg = AgentMessage(
            type=MessageType.SHUTDOWN,
            source_agent="orchestrator",
            target_agent="all",  # Broadcast
        )

        router.route(msg)

        assert q1.get(timeout=1).type == MessageType.SHUTDOWN
        assert q2.get(timeout=1).type == MessageType.SHUTDOWN

    def test_unregister_agent(self):
        """Should remove agent from routing."""
        from teambot.messaging.router import MessageRouter

        router = MessageRouter()
        queue = Queue()
        router.register_agent("builder-1", queue)
        router.unregister_agent("builder-1")

        assert "builder-1" not in router.agent_queues

    def test_route_to_unknown_agent_raises(self):
        """Routing to unregistered agent should raise."""
        from teambot.messaging.protocol import AgentMessage, MessageType
        from teambot.messaging.router import MessageRouter, RoutingError

        router = MessageRouter()

        msg = AgentMessage(
            type=MessageType.TASK_ASSIGN,
            source_agent="orchestrator",
            target_agent="unknown-agent",
            payload={},
        )

        with pytest.raises(RoutingError):
            router.route(msg)

    def test_get_registered_agents(self):
        """Should return list of registered agent IDs."""
        from teambot.messaging.router import MessageRouter

        router = MessageRouter()
        q1, q2 = Queue(), Queue()
        router.register_agent("pm", q1)
        router.register_agent("builder-1", q2)

        agents = router.get_registered_agents()

        assert "pm" in agents
        assert "builder-1" in agents
        assert len(agents) == 2

    def test_route_preserves_message_integrity(self):
        """Routed message should preserve all fields."""
        from teambot.messaging.protocol import AgentMessage, MessageType
        from teambot.messaging.router import MessageRouter

        router = MessageRouter()
        queue = Queue()
        router.register_agent("builder-1", queue)

        original = AgentMessage(
            type=MessageType.TASK_ASSIGN,
            source_agent="orchestrator",
            target_agent="builder-1",
            payload={"task": "test", "priority": 1},
            correlation_id="preserve-test",
        )

        router.route(original)

        received = queue.get(timeout=1)
        assert received.type == original.type
        assert received.source_agent == original.source_agent
        assert received.target_agent == original.target_agent
        assert received.payload == original.payload
        assert received.correlation_id == original.correlation_id
