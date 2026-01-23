"""System commands for TeamBot REPL.

Provides /help, /status, /history, /quit commands.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CommandResult:
    """Result from a system command.

    Attributes:
        output: Text output to display.
        success: Whether command succeeded.
        should_exit: Whether REPL should exit.
    """

    output: str
    success: bool = True
    should_exit: bool = False


def handle_help(args: list[str]) -> CommandResult:
    """Handle /help command.

    Args:
        args: Optional topic arguments.

    Returns:
        CommandResult with help text.
    """
    if args and args[0] == "agent":
        return CommandResult(
            output="""Agent Commands:
Use @agent to send tasks to specific agents.

Available Agents:
  @pm        - Project Manager: planning, coordination
  @ba        - Business Analyst: requirements, analysis
  @writer    - Technical Writer: documentation
  @builder-1 - Primary Builder: implementation
  @builder-2 - Secondary Builder: parallel tasks
  @reviewer  - Reviewer: code review, quality

Example:
  @pm Create a project plan for the new feature
  @builder-1 Implement the user authentication module"""
        )

    return CommandResult(
        output="""TeamBot Interactive Mode

Available commands:
  @agent <task>  - Send task to agent (pm, ba, writer, builder-1, builder-2, reviewer)
  /help          - Show this help message
  /help agent    - Show agent-specific help
  /status        - Show agent status
  /history       - Show command history
  /quit          - Exit interactive mode

Examples:
  @pm Create a project plan
  @builder-1 Implement the login feature
  /status
  /history pm"""
    )


def handle_status(args: list[str]) -> CommandResult:
    """Handle /status command.

    Args:
        args: Command arguments (unused).

    Returns:
        CommandResult with status.
    """
    # Basic status without orchestrator
    agents = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]
    lines = ["Agent Status:", ""]
    for agent in agents:
        lines.append(f"  {agent:12} - idle")

    return CommandResult(output="\n".join(lines))


def handle_history(args: list[str], history: list[dict[str, Any]]) -> CommandResult:
    """Handle /history command.

    Args:
        args: Optional agent filter.
        history: Command history list.

    Returns:
        CommandResult with history.
    """
    if not history:
        return CommandResult(output="No command history.")

    # Filter by agent if specified
    if args:
        agent_filter = args[0]
        history = [h for h in history if h.get("agent_id") == agent_filter]
        if not history:
            return CommandResult(output=f"No history for agent: {agent_filter}")

    # Show last 20 entries
    entries = history[-20:]
    lines = ["Command History:", ""]
    for entry in entries:
        agent = entry.get("agent_id", "?")
        content = entry.get("content", "")
        # Truncate long content
        if len(content) > 50:
            content = content[:47] + "..."
        lines.append(f"  @{agent:12} {content}")

    return CommandResult(output="\n".join(lines))


def handle_quit(args: list[str]) -> CommandResult:
    """Handle /quit command.

    Args:
        args: Command arguments (unused).

    Returns:
        CommandResult with exit flag.
    """
    return CommandResult(output="Goodbye!", should_exit=True)


class SystemCommands:
    """Handler for system commands in REPL.

    Provides dispatch and state management for system commands.
    """

    def __init__(self, orchestrator: Any = None):
        """Initialize system commands.

        Args:
            orchestrator: Optional orchestrator for status info.
        """
        self._orchestrator = orchestrator
        self._history: list[dict[str, Any]] = []

    def set_history(self, history: list[dict[str, Any]]) -> None:
        """Set history reference.

        Args:
            history: List to use for history.
        """
        self._history = history

    def dispatch(self, command: str, args: list[str]) -> CommandResult:
        """Dispatch a system command.

        Args:
            command: The command name (without /).
            args: Command arguments.

        Returns:
            CommandResult from handler.
        """
        handlers = {
            "help": self.help,
            "status": self.status,
            "history": self.history,
            "quit": self.quit,
            "exit": self.quit,  # Alias
        }

        handler = handlers.get(command)
        if handler is None:
            return CommandResult(
                output=f"Unknown command: /{command}. Type /help for available commands.",
                success=False,
            )

        return handler(args)

    def help(self, args: list[str]) -> CommandResult:
        """Handle /help command."""
        return handle_help(args)

    def status(self, args: list[str]) -> CommandResult:
        """Handle /status command."""
        if self._orchestrator:
            try:
                states = self._orchestrator.get_agent_states()
                lines = ["Agent Status:", ""]
                for agent_id, state in states.items():
                    status = state.get("status", "unknown")
                    lines.append(f"  {agent_id:12} - {status}")
                return CommandResult(output="\n".join(lines))
            except Exception:
                pass

        return handle_status(args)

    def history(self, args: list[str]) -> CommandResult:
        """Handle /history command."""
        return handle_history(args, self._history)

    def quit(self, args: list[str]) -> CommandResult:
        """Handle /quit command."""
        return handle_quit(args)
