"""Tests for agent runner - Code-First approach."""

from multiprocessing import Queue


class TestAgentRunner:
    """Tests for AgentRunner class."""

    def test_create_runner(self, temp_teambot_dir):
        """Runner initializes with required parameters."""
        from teambot.agent_runner import AgentRunner
        from teambot.messaging.protocol import AgentMessage

        agent_queue: Queue[AgentMessage] = Queue()
        main_queue: Queue[AgentMessage] = Queue()

        runner = AgentRunner(
            agent_id="builder-1",
            persona="builder",
            agent_queue=agent_queue,
            main_queue=main_queue,
            teambot_dir=temp_teambot_dir,
        )

        assert runner.agent_id == "builder-1"
        assert runner.persona == "builder"
        assert not runner.running

    def test_handle_shutdown_message(self, temp_teambot_dir):
        """Shutdown message stops the runner."""
        from teambot.agent_runner import AgentRunner
        from teambot.messaging.protocol import AgentMessage, MessageType

        agent_queue: Queue[AgentMessage] = Queue()
        main_queue: Queue[AgentMessage] = Queue()

        runner = AgentRunner(
            agent_id="builder-1",
            persona="builder",
            agent_queue=agent_queue,
            main_queue=main_queue,
            teambot_dir=temp_teambot_dir,
        )
        runner.running = True

        shutdown_msg = AgentMessage(
            type=MessageType.SHUTDOWN,
            source_agent="orchestrator",
            target_agent="builder-1",
        )

        runner._handle_message(shutdown_msg)

        assert not runner.running

    def test_handle_task_assign(self, temp_teambot_dir):
        """Task assignment triggers execution."""
        import time

        from teambot.agent_runner import AgentRunner
        from teambot.messaging.protocol import AgentMessage, MessageType

        agent_queue: Queue[AgentMessage] = Queue()
        main_queue: Queue[AgentMessage] = Queue()

        runner = AgentRunner(
            agent_id="builder-1",
            persona="builder",
            agent_queue=agent_queue,
            main_queue=main_queue,
            teambot_dir=temp_teambot_dir,
        )

        task_msg = AgentMessage(
            type=MessageType.TASK_ASSIGN,
            source_agent="orchestrator",
            target_agent="builder-1",
            payload={"task": "Implement feature X"},
        )

        runner._handle_message(task_msg)

        # Give time for messages to be queued
        time.sleep(0.1)

        # Should have sent status update and completion
        messages = []
        while not main_queue.empty():
            messages.append(main_queue.get(timeout=1))

        # At minimum we get a status update
        assert len(messages) >= 1
        # First is status "working"
        assert messages[0].type == MessageType.STATUS_UPDATE
        assert messages[0].payload["status"] == "working"
        # Last is task complete (if more than 1 message)
        if len(messages) > 1:
            assert messages[-1].type == MessageType.TASK_COMPLETE

    def test_send_status(self, temp_teambot_dir):
        """Send status update to orchestrator."""
        from teambot.agent_runner import AgentRunner
        from teambot.messaging.protocol import AgentMessage, MessageType

        agent_queue: Queue[AgentMessage] = Queue()
        main_queue: Queue[AgentMessage] = Queue()

        runner = AgentRunner(
            agent_id="pm",
            persona="project_manager",
            agent_queue=agent_queue,
            main_queue=main_queue,
            teambot_dir=temp_teambot_dir,
        )

        runner._send_status("ready")

        msg = main_queue.get(timeout=1)
        assert msg.type == MessageType.STATUS_UPDATE
        assert msg.source_agent == "pm"
        assert msg.payload["status"] == "ready"

    def test_send_task_complete(self, temp_teambot_dir):
        """Send task completion to orchestrator."""
        from teambot.agent_runner import AgentRunner
        from teambot.messaging.protocol import AgentMessage, MessageType

        agent_queue: Queue[AgentMessage] = Queue()
        main_queue: Queue[AgentMessage] = Queue()

        runner = AgentRunner(
            agent_id="builder-1",
            persona="builder",
            agent_queue=agent_queue,
            main_queue=main_queue,
            teambot_dir=temp_teambot_dir,
        )
        runner.current_task = "Test task"

        runner._send_task_complete({"status": "ok"})

        msg = main_queue.get(timeout=1)
        assert msg.type == MessageType.TASK_COMPLETE
        assert msg.payload["result"]["status"] == "ok"
        assert runner.current_task is None  # Cleared after completion

    def test_send_task_failed(self, temp_teambot_dir):
        """Send task failure to orchestrator."""
        from teambot.agent_runner import AgentRunner
        from teambot.messaging.protocol import AgentMessage, MessageType

        agent_queue: Queue[AgentMessage] = Queue()
        main_queue: Queue[AgentMessage] = Queue()

        runner = AgentRunner(
            agent_id="builder-1",
            persona="builder",
            agent_queue=agent_queue,
            main_queue=main_queue,
            teambot_dir=temp_teambot_dir,
        )
        runner.current_task = "Failing task"

        runner._send_task_failed("Something went wrong")

        msg = main_queue.get(timeout=1)
        assert msg.type == MessageType.TASK_FAILED
        assert "Something went wrong" in msg.payload["error"]

    def test_create_history_entry(self, temp_teambot_dir):
        """Create history file for agent action."""
        from teambot.agent_runner import AgentRunner
        from teambot.messaging.protocol import AgentMessage

        agent_queue: Queue[AgentMessage] = Queue()
        main_queue: Queue[AgentMessage] = Queue()

        runner = AgentRunner(
            agent_id="builder-1",
            persona="builder",
            agent_queue=agent_queue,
            main_queue=main_queue,
            teambot_dir=temp_teambot_dir,
        )

        filepath = runner.create_history_entry(
            title="Implemented feature",
            description="Added new feature X",
            action_type="code-created",
            content="## Changes\n\nImplemented feature X.",
        )

        assert filepath.exists()
        assert "code-created" in filepath.name


class TestAgentRunnerContextHandling:
    """Tests for context handling in agent runner."""

    def test_handle_context_share(self, temp_teambot_dir):
        """Handle shared context from another agent."""
        from teambot.agent_runner import AgentRunner
        from teambot.messaging.protocol import AgentMessage, MessageType

        agent_queue: Queue[AgentMessage] = Queue()
        main_queue: Queue[AgentMessage] = Queue()

        runner = AgentRunner(
            agent_id="builder-1",
            persona="builder",
            agent_queue=agent_queue,
            main_queue=main_queue,
            teambot_dir=temp_teambot_dir,
        )

        context_msg = AgentMessage(
            type=MessageType.CONTEXT_SHARE,
            source_agent="reviewer",
            target_agent="builder-1",
            payload={"review_notes": "Please fix the bug in line 42"},
        )

        # Should not raise
        runner._handle_message(context_msg)
