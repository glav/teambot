"""Agent router for TeamBot REPL.

Routes parsed commands to appropriate handlers based on type.
"""

from collections.abc import Callable, Awaitable
from datetime import datetime
from typing import Any, Optional

from teambot.repl.parser import Command, CommandType


class RouterError(Exception):
    """Error raised by router operations."""

    pass


# Valid agent IDs
VALID_AGENTS = {"pm", "ba", "writer", "builder-1", "builder-2", "reviewer"}

# Aliases that map to canonical agent IDs
AGENT_ALIASES = {
    "project_manager": "pm",
    "business_analyst": "ba",
    "technical_writer": "writer",
}


class AgentRouter:
    """Routes commands to appropriate handlers.

    Supports:
    - Agent commands routed to SDK client
    - System commands routed to command handlers
    - Raw input routed to default handler or default agent (if configured)
    """

    def __init__(self, history_limit: int = 100, default_agent: Optional[str] = None):
        """Initialize the router.

        Args:
            history_limit: Maximum number of commands to keep in history.
            default_agent: Optional agent ID to route raw input to. If None,
                          raw input is handled by the raw handler.
        """
        self._agent_handler: Optional[Callable[[str, str], Awaitable[str]]] = None
        self._system_handler: Optional[Callable[[str, list[str]], str]] = None
        self._raw_handler: Optional[Callable[[str], str]] = None
        self._history: list[dict[str, Any]] = []
        self._history_limit = history_limit
        self._default_agent = default_agent

    def is_valid_agent(self, agent_id: str) -> bool:
        """Check if agent ID is valid.

        Args:
            agent_id: The agent identifier to check.

        Returns:
            True if valid, False otherwise.
        """
        canonical = self.resolve_agent_id(agent_id)
        return canonical in VALID_AGENTS

    def resolve_agent_id(self, agent_id: str) -> str:
        """Resolve an agent ID or alias to canonical form.

        Args:
            agent_id: The agent ID or alias.

        Returns:
            Canonical agent ID.
        """
        return AGENT_ALIASES.get(agent_id, agent_id)

    def get_all_agents(self) -> list[str]:
        """Get list of all valid agent IDs.

        Returns:
            List of agent IDs.
        """
        return list(VALID_AGENTS)

    def register_agent_handler(
        self, handler: Callable[[str, str], Awaitable[str]]
    ) -> None:
        """Register handler for agent commands.

        Args:
            handler: Async function(agent_id, content) -> response.
        """
        self._agent_handler = handler

    def register_system_handler(
        self, handler: Callable[[str, list[str]], str]
    ) -> None:
        """Register handler for system commands.

        Args:
            handler: Function(command, args) -> response.
        """
        self._system_handler = handler

    def register_raw_handler(self, handler: Callable[[str], str]) -> None:
        """Register handler for raw input.

        Args:
            handler: Function(content) -> response.
        """
        self._raw_handler = handler

    async def route(self, command: Command) -> str:
        """Route a command to appropriate handler.

        Args:
            command: Parsed command to route.

        Returns:
            Response from handler.

        Raises:
            RouterError: If no handler or invalid agent.
        """
        if command.type == CommandType.AGENT:
            return await self._route_agent(command)
        elif command.type == CommandType.SYSTEM:
            return self._route_system(command)
        else:
            return await self._route_raw(command)

    async def _route_agent(self, command: Command) -> str:
        """Route agent command."""
        if self._agent_handler is None:
            raise RouterError("No handler registered for agent commands")

        # Resolve alias to canonical ID
        agent_id = self.resolve_agent_id(command.agent_id)

        if not self.is_valid_agent(agent_id):
            raise RouterError(f"Unknown agent: {command.agent_id}")

        # Record in history
        self._record_history(agent_id, command.content)

        return await self._agent_handler(agent_id, command.content)

    def _route_system(self, command: Command) -> str:
        """Route system command."""
        if self._system_handler is None:
            raise RouterError("No handler registered for system commands")

        return self._system_handler(command.command, command.args or [])

    async def _route_raw(self, command: Command) -> str:
        """Route raw input.
        
        If a default agent is configured, routes raw input to that agent.
        Otherwise, uses the raw handler.
        """
        # If default agent is configured and content is not empty, route to agent
        if self._default_agent and command.content and command.content.strip():
            # Validate the default agent
            if not self.is_valid_agent(self._default_agent):
                # Fallback to raw handler if default agent is invalid
                if self._raw_handler is None:
                    raise RouterError("No handler registered for raw input")
                return self._raw_handler(command.content)
            
            # Convert to agent command and route
            agent_command = Command(
                type=CommandType.AGENT,
                agent_id=self._default_agent,
                agent_ids=[self._default_agent],
                content=command.content,
            )
            # Route to agent handler
            return await self._route_agent(agent_command)
        
        # Use raw handler for empty input or when no default agent configured
        if self._raw_handler is None:
            raise RouterError("No handler registered for raw input")

        return self._raw_handler(command.content)

    def _record_history(self, agent_id: str, content: str) -> None:
        """Record command in history."""
        entry = {
            "agent_id": agent_id,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self._history.append(entry)

        # Trim history if over limit
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit :]

    def get_history(self) -> list[dict[str, Any]]:
        """Get command history.

        Returns:
            List of history entries.
        """
        return list(self._history)

    def clear_history(self) -> None:
        """Clear command history."""
        self._history.clear()
