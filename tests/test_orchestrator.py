"""Tests for orchestrator - TDD approach."""

from multiprocessing import Queue
from unittest.mock import MagicMock, patch


class TestOrchestrator:
    """Tests for Orchestrator class."""

    def test_create_orchestrator_with_config(self, sample_agent_config):
        """Orchestrator initializes with configuration."""
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        assert orch.config == config
        assert orch.agents == {}
        assert orch.main_queue is not None

    def test_orchestrator_has_router(self, sample_agent_config):
        """Orchestrator should have a MessageRouter."""
        from teambot.messaging.router import MessageRouter
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        assert hasattr(orch, "router")
        assert isinstance(orch.router, MessageRouter)

    def test_spawn_agent_creates_queue(self, sample_agent_config):
        """Spawning agent creates dedicated queue."""
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        # Mock the actual process spawning
        with patch.object(orch, "_create_agent_process") as mock_create:
            mock_create.return_value = MagicMock()
            orch.spawn_agent(sample_agent_config)

        assert "builder-1" in orch.router.agent_queues

    def test_spawn_agent_tracks_process(self, sample_agent_config):
        """Spawning agent tracks the process object."""
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        mock_process = MagicMock()
        with patch.object(orch, "_create_agent_process", return_value=mock_process):
            orch.spawn_agent(sample_agent_config)

        assert "builder-1" in orch.agents
        assert orch.agents["builder-1"] == mock_process

    def test_send_to_agent_uses_router(self, sample_agent_config):
        """send_to_agent delegates to router."""
        from teambot.messaging.protocol import AgentMessage, MessageType
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        # Setup mock queue
        mock_queue = Queue()
        orch.router.register_agent("builder-1", mock_queue)

        msg = AgentMessage(
            type=MessageType.TASK_ASSIGN,
            source_agent="orchestrator",
            target_agent="builder-1",
        )

        orch.send_to_agent("builder-1", msg)

        received = mock_queue.get(timeout=1)
        assert received.type == MessageType.TASK_ASSIGN

    def test_shutdown_sends_sentinel_to_all(self, sample_agent_config):
        """Shutdown broadcasts SHUTDOWN message."""
        from teambot.messaging.protocol import MessageType
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        # Setup mock queues for multiple agents
        queues = {}
        for agent_id in ["pm", "builder-1", "reviewer"]:
            q = Queue()
            orch.router.register_agent(agent_id, q)
            queues[agent_id] = q

        orch.shutdown()

        for _agent_id, q in queues.items():
            msg = q.get(timeout=1)
            assert msg.type == MessageType.SHUTDOWN

    def test_get_agent_ids(self, sample_agent_config):
        """Should return list of spawned agent IDs."""
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        # Manually add agents for testing
        orch.agents["pm"] = MagicMock()
        orch.agents["builder-1"] = MagicMock()

        agent_ids = orch.get_agent_ids()

        assert "pm" in agent_ids
        assert "builder-1" in agent_ids

    def test_is_running_initially_false(self, sample_agent_config):
        """Orchestrator is not running when created."""
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        assert not orch.is_running

    def test_orchestrator_initializes_teambot_dir(self, sample_agent_config, tmp_path):
        """Orchestrator should create .teambot directory if specified."""
        from teambot.orchestrator import Orchestrator

        teambot_dir = tmp_path / ".teambot"
        config = {"agents": [sample_agent_config], "teambot_dir": str(teambot_dir)}
        orch = Orchestrator(config)

        # Orchestrator should track the teambot directory
        assert orch.teambot_dir == teambot_dir


class TestOrchestratorMessageHandling:
    """Tests for orchestrator message handling."""

    def test_handle_task_complete(self, sample_agent_config):
        """Orchestrator processes TASK_COMPLETE messages."""
        from teambot.messaging.protocol import AgentMessage, MessageType
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        msg = AgentMessage(
            type=MessageType.TASK_COMPLETE,
            source_agent="builder-1",
            target_agent="orchestrator",
            payload={"result": "success"},
        )

        # Handler should not raise
        orch.handle_message(msg)

    def test_handle_task_failed(self, sample_agent_config):
        """Orchestrator processes TASK_FAILED messages."""
        from teambot.messaging.protocol import AgentMessage, MessageType
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        msg = AgentMessage(
            type=MessageType.TASK_FAILED,
            source_agent="builder-1",
            target_agent="orchestrator",
            payload={"error": "compilation failed"},
        )

        # Handler should not raise
        orch.handle_message(msg)

    def test_handle_status_update(self, sample_agent_config):
        """Orchestrator processes STATUS_UPDATE messages."""
        from teambot.messaging.protocol import AgentMessage, MessageType
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        msg = AgentMessage(
            type=MessageType.STATUS_UPDATE,
            source_agent="pm",
            target_agent="orchestrator",
            payload={"status": "planning"},
        )

        # Handler should not raise
        orch.handle_message(msg)


class TestOrchestratorLifecycle:
    """Tests for orchestrator lifecycle management."""

    def test_spawn_all_agents_from_config(self, sample_agent_config):
        """spawn_all spawns all agents in config."""
        from teambot.orchestrator import Orchestrator

        config = {
            "agents": [
                sample_agent_config,
                {
                    "id": "reviewer",
                    "persona": "reviewer",
                    "display_name": "Reviewer",
                    "parallel_capable": False,
                    "workflow_stages": ["review"],
                },
            ]
        }
        orch = Orchestrator(config)

        with patch.object(orch, "spawn_agent") as mock_spawn:
            orch.spawn_all()

        assert mock_spawn.call_count == 2

    def test_terminate_agent(self, sample_agent_config):
        """terminate_agent stops specific agent."""
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        mock_process = MagicMock()
        orch.agents["builder-1"] = mock_process
        orch.router.register_agent("builder-1", Queue())

        orch.terminate_agent("builder-1")

        mock_process.terminate.assert_called_once()
        assert "builder-1" not in orch.agents
