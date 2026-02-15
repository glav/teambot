"""Integration tests for TeamBot."""

from multiprocessing import Queue


class TestFullWorkflow:
    """End-to-end workflow integration tests."""

    def test_config_to_orchestrator(self, tmp_path):
        """Configuration loads and creates valid orchestrator."""
        from teambot.config.loader import ConfigLoader, create_default_config
        from teambot.orchestrator import Orchestrator

        # Create and save config
        config = create_default_config()
        config["teambot_dir"] = str(tmp_path / ".teambot")
        config_file = tmp_path / "teambot.json"
        loader = ConfigLoader()
        loader.save(config, config_file)

        # Load and create orchestrator
        loaded_config = loader.load(config_file)
        orchestrator = Orchestrator(loaded_config)

        assert orchestrator.config == loaded_config
        assert len(loaded_config["agents"]) == 6

    def test_orchestrator_message_routing(self, tmp_path):
        """Orchestrator can route messages between agents."""
        from teambot.messaging.protocol import AgentMessage, MessageType
        from teambot.orchestrator import Orchestrator

        config = {
            "agents": [
                {"id": "pm", "persona": "project_manager"},
                {"id": "builder-1", "persona": "builder"},
            ],
            "teambot_dir": str(tmp_path / ".teambot"),
        }

        orchestrator = Orchestrator(config)

        # Register mock queues
        q1 = Queue()
        q2 = Queue()
        orchestrator.router.register_agent("pm", q1)
        orchestrator.router.register_agent("builder-1", q2)

        # Send message to specific agent
        msg = AgentMessage(
            type=MessageType.TASK_ASSIGN,
            source_agent="orchestrator",
            target_agent="builder-1",
            payload={"task": "Build feature"},
        )
        orchestrator.send_to_agent("builder-1", msg)

        # Verify message received
        received = q2.get(timeout=1)
        assert received.type == MessageType.TASK_ASSIGN
        assert received.payload["task"] == "Build feature"

    def test_history_with_frontmatter(self, tmp_path):
        """History files created with valid frontmatter."""
        from datetime import datetime

        from teambot.history.frontmatter import HistoryMetadata, parse_frontmatter
        from teambot.history.manager import HistoryFileManager

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        manager = HistoryFileManager(teambot_dir)

        # Create history entry
        metadata = HistoryMetadata(
            title="Integration Test",
            description="Testing full flow",
            timestamp=datetime.now(),
            agent_id="test-agent",
            action_type="test-action",
        )
        filepath = manager.create_history_file(metadata, "## Test Content\n\nThis is a test.")

        # Load and verify
        loaded_meta, content = parse_frontmatter(filepath)
        assert loaded_meta["title"] == "Integration Test"
        assert loaded_meta["agent_id"] == "test-agent"
        assert "Test Content" in content


class TestAgentCommunication:
    """Tests for agent-to-orchestrator communication."""

    def test_agent_sends_status_to_orchestrator(self, tmp_path):
        """Agent can send status updates to orchestrator."""
        from teambot.agent_runner import AgentRunner
        from teambot.messaging.protocol import AgentMessage, MessageType

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()
        (teambot_dir / "history").mkdir()

        agent_queue: Queue[AgentMessage] = Queue()
        main_queue: Queue[AgentMessage] = Queue()

        runner = AgentRunner(
            agent_id="builder-1",
            persona="builder",
            agent_queue=agent_queue,
            main_queue=main_queue,
            teambot_dir=teambot_dir,
        )

        # Agent sends status
        runner._send_status("working", task="Building feature")

        # Orchestrator receives it
        msg = main_queue.get(timeout=1)
        assert msg.type == MessageType.STATUS_UPDATE
        assert msg.source_agent == "builder-1"
        assert msg.payload["status"] == "working"

    def test_shutdown_propagates(self, tmp_path):
        """Shutdown message stops agent."""
        from teambot.agent_runner import AgentRunner
        from teambot.messaging.protocol import AgentMessage, MessageType

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()
        (teambot_dir / "history").mkdir()

        agent_queue: Queue[AgentMessage] = Queue()
        main_queue: Queue[AgentMessage] = Queue()

        runner = AgentRunner(
            agent_id="builder-1",
            persona="builder",
            agent_queue=agent_queue,
            main_queue=main_queue,
            teambot_dir=teambot_dir,
        )
        runner.running = True

        # Send shutdown
        shutdown = AgentMessage(
            type=MessageType.SHUTDOWN,
            source_agent="orchestrator",
            target_agent="builder-1",
        )
        runner._handle_message(shutdown)

        assert not runner.running


class TestVisualizationIntegration:
    """Tests for visualization with real data."""

    def test_display_with_config_agents(self):
        """Display can show agents from config."""
        from teambot.config.loader import create_default_config
        from teambot.visualization.console import AgentStatus, ConsoleDisplay

        config = create_default_config()
        display = ConsoleDisplay()

        # Add agents from config
        for agent in config["agents"]:
            display.add_agent(agent["id"], agent["persona"], agent.get("display_name"))

        # All 6 MVP agents should be displayed
        assert len(display.agents) == 6

        # Update status
        display.update_status("pm", AgentStatus.WORKING, task="Planning")

        assert display.get_status("pm") == AgentStatus.WORKING


class TestModuleImports:
    """Verify all modules can be imported cleanly."""

    def test_import_all_modules(self):
        """All TeamBot modules import without errors."""
        import teambot
        import teambot.agent_runner
        import teambot.cli
        import teambot.config
        import teambot.config.loader
        import teambot.history
        import teambot.history.compactor
        import teambot.history.frontmatter
        import teambot.history.manager
        import teambot.messaging
        import teambot.messaging.protocol
        import teambot.messaging.router
        import teambot.orchestrator
        import teambot.visualization
        import teambot.visualization.console
        import teambot.window_manager

        assert teambot.__version__ == "0.2.1"
