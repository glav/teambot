"""Agent process entry point for individual AI agents."""

from __future__ import annotations

import logging
from multiprocessing import Queue
from pathlib import Path
from queue import Empty
from typing import Any

from teambot.copilot.client import CopilotClient, CopilotConfig
from teambot.history.frontmatter import HistoryMetadata
from teambot.history.manager import HistoryFileManager
from teambot.messaging.protocol import AgentMessage, MessageType
from teambot.prompts.templates import get_persona_template

logger = logging.getLogger(__name__)


class AgentRunner:
    """Runs an individual AI agent process."""

    def __init__(
        self,
        agent_id: str,
        persona: str,
        agent_queue: Queue[AgentMessage],
        main_queue: Queue[AgentMessage],
        teambot_dir: Path,
        copilot_client: CopilotClient | None = None,
    ):
        self.agent_id = agent_id
        self.persona = persona
        self.agent_queue = agent_queue
        self.main_queue = main_queue
        self.teambot_dir = teambot_dir
        self.history_manager = HistoryFileManager(teambot_dir)
        self.running = False
        self.current_task: str | None = None

        # Initialize Copilot client
        if copilot_client is None:
            config = CopilotConfig(
                allow_all_tools=True,
                additional_dirs=[str(teambot_dir.parent)],
            )
            self.copilot_client = CopilotClient(
                working_dir=teambot_dir.parent,
                config=config,
            )
        else:
            self.copilot_client = copilot_client

        # Get persona template for prompt building
        try:
            self.prompt_template = get_persona_template(persona)
        except ValueError:
            # Fall back to builder if persona not recognized
            self.prompt_template = get_persona_template("builder")

    def run(self) -> None:
        """Main agent loop - process messages from queue."""
        self.running = True
        logger.info(f"Agent {self.agent_id} ({self.persona}) started")

        self._send_status("ready")

        while self.running:
            try:
                message = self.agent_queue.get(timeout=1.0)
                self._handle_message(message)
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Agent {self.agent_id} error: {e}")
                self._send_error(str(e))

        logger.info(f"Agent {self.agent_id} stopped")

    def _handle_message(self, message: AgentMessage) -> None:
        """Handle an incoming message."""
        if message.type == MessageType.SHUTDOWN:
            logger.info(f"Agent {self.agent_id} received shutdown")
            self.running = False
        elif message.type == MessageType.TASK_ASSIGN:
            self._handle_task(message)
        elif message.type == MessageType.CONTEXT_SHARE:
            self._handle_context(message)
        else:
            logger.debug(f"Agent {self.agent_id} ignoring message type: {message.type}")

    def _handle_task(self, message: AgentMessage) -> None:
        """Handle a task assignment."""
        task = message.payload.get("task", "Unknown task")
        self.current_task = task

        self._send_status("working", task=task)

        try:
            # Execute the task (placeholder - would invoke Copilot CLI)
            result = self._execute_task(message.payload)

            # Send completion
            self._send_task_complete(result)
        except Exception as e:
            self._send_task_failed(str(e))

    def _execute_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a task using the Copilot CLI.

        Args:
            payload: Task payload containing 'task' and optional 'context'

        Returns:
            Result dictionary with status and output
        """
        task = payload.get("task", "")
        context = payload.get("context")

        # Build prompt using persona template
        prompt = self.prompt_template.build_prompt(task, context)

        # Check if Copilot CLI is available
        if not self.copilot_client.is_available():
            logger.warning("Copilot CLI not available, returning placeholder result")
            return {
                "status": "skipped",
                "message": "Copilot CLI not available",
                "task": task,
            }

        # Execute via Copilot CLI
        result = self.copilot_client.execute(prompt)

        # Create history entry for this execution
        self._create_task_history(task, result.output, result.success)

        if result.success:
            return {
                "status": "completed",
                "message": "Task executed successfully",
                "output": result.output,
                "task": task,
            }
        else:
            return {
                "status": "failed",
                "message": result.error or "Task execution failed",
                "output": result.output,
                "task": task,
            }

    def _create_task_history(self, task: str, output: str, success: bool) -> Path | None:
        """Create a history file for a completed task."""
        from datetime import datetime

        action_type = "task-complete" if success else "task-failed"
        status = "completed" if success else "failed"

        metadata = HistoryMetadata(
            title=f"Task: {task[:50]}{'...' if len(task) > 50 else ''}",
            description=f"Agent {self.agent_id} ({self.persona}) {status} task",
            timestamp=datetime.now(),
            agent_id=self.agent_id,
            action_type=action_type,
        )

        content = f"## Task\n\n{task}\n\n## Output\n\n{output}"
        return self.history_manager.create_history_file(metadata, content)

    def _handle_context(self, message: AgentMessage) -> None:
        """Handle shared context from another agent."""
        _ = message.payload  # Store context for use in future tasks
        logger.debug(f"Agent {self.agent_id} received context from {message.source_agent}")

    def _send_status(self, status: str, task: str | None = None) -> None:
        """Send status update to orchestrator."""
        msg = AgentMessage(
            type=MessageType.STATUS_UPDATE,
            source_agent=self.agent_id,
            target_agent="orchestrator",
            payload={"status": status, "task": task},
        )
        self.main_queue.put(msg)

    def _send_task_complete(self, result: dict[str, Any]) -> None:
        """Send task completion to orchestrator."""
        msg = AgentMessage(
            type=MessageType.TASK_COMPLETE,
            source_agent=self.agent_id,
            target_agent="orchestrator",
            payload={"result": result, "task": self.current_task},
        )
        self.main_queue.put(msg)
        self.current_task = None

    def _send_task_failed(self, error: str) -> None:
        """Send task failure to orchestrator."""
        msg = AgentMessage(
            type=MessageType.TASK_FAILED,
            source_agent=self.agent_id,
            target_agent="orchestrator",
            payload={"error": error, "task": self.current_task},
        )
        self.main_queue.put(msg)
        self.current_task = None

    def _send_error(self, error: str) -> None:
        """Send error message to orchestrator."""
        msg = AgentMessage(
            type=MessageType.TASK_FAILED,
            source_agent=self.agent_id,
            target_agent="orchestrator",
            payload={"error": error},
        )
        self.main_queue.put(msg)

    def create_history_entry(
        self, title: str, description: str, action_type: str, content: str
    ) -> Path:
        """Create a history file for this agent's action."""
        from datetime import datetime

        metadata = HistoryMetadata(
            title=title,
            description=description,
            timestamp=datetime.now(),
            agent_id=self.agent_id,
            action_type=action_type,
        )
        return self.history_manager.create_history_file(metadata, content)
