"""Parent orchestrator process for managing agent queues and lifecycle."""

from __future__ import annotations

import logging
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Any

from teambot.messaging.protocol import AgentMessage, MessageType
from teambot.messaging.router import MessageRouter
from teambot.workflow.stages import WorkflowStage
from teambot.workflow.state_machine import WorkflowStateMachine

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates multiple AI agent processes."""

    def __init__(self, config: dict[str, Any], objective: str = ""):
        self.config = config
        self.agents: dict[str, Process] = {}
        self.agent_personas: dict[str, str] = {}  # agent_id -> persona
        self.main_queue: Queue[AgentMessage] = Queue()
        self.router = MessageRouter()
        self.is_running = False

        # Setup teambot directory
        teambot_dir = config.get("teambot_dir")
        self.teambot_dir = Path(teambot_dir) if teambot_dir else Path(".teambot")

        # Initialize workflow state machine
        self.workflow = WorkflowStateMachine(self.teambot_dir, objective)

    @property
    def current_stage(self) -> WorkflowStage:
        """Get current workflow stage."""
        return self.workflow.current_stage

    @property
    def workflow_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.workflow.is_complete

    def spawn_agent(self, agent_config: dict[str, Any]) -> None:
        """Spawn a single agent process."""
        agent_id = agent_config["id"]
        persona = agent_config.get("persona", "builder")

        # Create dedicated queue for this agent
        agent_queue: Queue[AgentMessage] = Queue()
        self.router.register_agent(agent_id, agent_queue)

        # Track persona for workflow validation
        self.agent_personas[agent_id] = persona

        # Create and start the process
        process = self._create_agent_process(agent_config, agent_queue)
        self.agents[agent_id] = process

        logger.info(f"Spawned agent: {agent_id} (persona: {persona})")

    def _create_agent_process(
        self, agent_config: dict[str, Any], agent_queue: Queue[AgentMessage]
    ) -> Process:
        """Create the actual process for an agent."""
        # This will be implemented with actual agent runner
        process = Process(
            target=self._agent_entry_point,
            args=(agent_config, agent_queue, self.main_queue),
        )
        process.start()
        return process

    def _agent_entry_point(
        self,
        agent_config: dict[str, Any],
        agent_queue: Queue[AgentMessage],
        main_queue: Queue[AgentMessage],
    ) -> None:
        """Entry point for agent subprocess."""
        # Placeholder - will be replaced by AgentRunner
        pass

    def spawn_all(self) -> None:
        """Spawn all agents defined in config."""
        for agent_config in self.config.get("agents", []):
            self.spawn_agent(agent_config)

    def send_to_agent(self, agent_id: str, message: AgentMessage) -> None:
        """Send a message to a specific agent."""
        self.router.route(message)

    def shutdown(self) -> None:
        """Send shutdown signal to all agents."""
        shutdown_msg = AgentMessage(
            type=MessageType.SHUTDOWN,
            source_agent="orchestrator",
            target_agent="all",
        )
        self.router.route(shutdown_msg)
        self.is_running = False

    def terminate_agent(self, agent_id: str) -> None:
        """Terminate a specific agent."""
        if agent_id in self.agents:
            process = self.agents[agent_id]
            process.terminate()
            del self.agents[agent_id]
            if agent_id in self.agent_personas:
                del self.agent_personas[agent_id]
            self.router.unregister_agent(agent_id)
            logger.info(f"Terminated agent: {agent_id}")

    def get_agent_ids(self) -> list[str]:
        """Return list of spawned agent IDs."""
        return list(self.agents.keys())

    def assign_task(self, agent_id: str, task: str, context: str | None = None) -> bool:
        """Assign a task to an agent with workflow validation.

        Args:
            agent_id: The agent to assign the task to
            task: The task description
            context: Optional context for the task

        Returns:
            True if task was assigned successfully

        Raises:
            ValueError: If agent persona not allowed for current stage
        """
        persona = self.agent_personas.get(agent_id, "")

        # Validate persona is allowed for current workflow stage
        if not self.workflow.is_persona_allowed(persona):
            stage_info = self.workflow.get_stage_info()
            raise ValueError(
                f"Agent '{agent_id}' (persona: {persona}) is not allowed "
                f"in stage {stage_info['name']}. "
                f"Allowed personas: {stage_info['allowed_personas']}"
            )

        # Create and send task message
        payload = {"task": task}
        if context:
            payload["context"] = context

        message = AgentMessage(
            type=MessageType.TASK_ASSIGN,
            source_agent="orchestrator",
            target_agent=agent_id,
            payload=payload,
        )
        self.router.route(message)
        logger.info(f"Assigned task to {agent_id}: {task[:50]}...")
        return True

    def advance_workflow(
        self, target_stage: WorkflowStage, artifacts: list[str] | None = None
    ) -> bool:
        """Advance workflow to next stage.

        Args:
            target_stage: The stage to transition to
            artifacts: Artifacts produced during current stage

        Returns:
            True if transition succeeded
        """
        return self.workflow.transition_to(target_stage, artifacts)

    def skip_current_stage(self) -> bool:
        """Skip the current workflow stage if optional.

        Returns:
            True if stage was skipped
        """
        return self.workflow.skip_stage(self.current_stage)

    def get_workflow_status(self) -> dict[str, Any]:
        """Get current workflow status.

        Returns:
            Dictionary with workflow progress and stage info
        """
        return {
            **self.workflow.get_progress(),
            "stage_info": self.workflow.get_stage_info(),
        }

    def get_agents_for_current_stage(self) -> list[str]:
        """Get agents allowed to work on current workflow stage.

        Returns:
            List of agent IDs whose personas are allowed
        """
        allowed = []
        for agent_id, persona in self.agent_personas.items():
            if self.workflow.is_persona_allowed(persona):
                allowed.append(agent_id)
        return allowed

    def handle_message(self, message: AgentMessage) -> None:
        """Handle a message received on the main queue."""
        msg_type = message.type
        source = message.source_agent
        payload = message.payload

        if msg_type == MessageType.TASK_COMPLETE:
            logger.info(f"Agent {source} completed task: {payload}")
        elif msg_type == MessageType.TASK_FAILED:
            logger.warning(f"Agent {source} failed task: {payload}")
        elif msg_type == MessageType.STATUS_UPDATE:
            logger.debug(f"Agent {source} status: {payload}")
        else:
            logger.debug(f"Received {msg_type} from {source}")
