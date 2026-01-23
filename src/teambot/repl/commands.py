"""System commands for TeamBot REPL.

Provides /help, /status, /history, /quit, /tasks commands.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from teambot.tasks.executor import TaskExecutor


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

    if args and args[0] == "parallel":
        return CommandResult(
            output="""Parallel Execution:

Background tasks (fire and forget):
  @pm Create a project plan &
  @builder-1 Set up the project structure &

Multi-agent fan-out (parallel, same prompt):
  @pm,ba,writer Analyze the new feature requirements

Task dependencies (sequential with output passing):
  @pm Create plan -> @builder-1 Implement based on this plan

Combined (parallel groups with dependencies):
  @pm,ba Analyze feature & -> @builder-1,builder-2 Implement

Task management:
  /tasks         - List all tasks
  /task <id>     - View task details
  /cancel <id>   - Cancel a pending task"""
        )

    return CommandResult(
        output="""TeamBot Interactive Mode

Available commands:
  @agent <task>  - Send task to agent (pm, ba, writer, builder-1, builder-2, reviewer)
  /help          - Show this help message
  /help agent    - Show agent-specific help
  /help parallel - Show parallel execution help
  /status        - Show agent status
  /tasks         - List running/completed tasks
  /task <id>     - View task details
  /cancel <id>   - Cancel pending task
  /history       - Show command history
  /quit          - Exit interactive mode

Examples:
  @pm Create a project plan
  @builder-1 Implement the login feature
  @pm,ba Analyze requirements        # Multi-agent
  @pm Plan -> @builder-1 Build       # Pipeline
  @pm Create plan &                  # Background
  /tasks"""
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


def handle_tasks(args: list[str], executor: Optional["TaskExecutor"]) -> CommandResult:
    """Handle /tasks command.

    Args:
        args: Optional filter args (status).
        executor: TaskExecutor with task state.

    Returns:
        CommandResult with task list.
    """
    if executor is None:
        return CommandResult(
            output="Task executor not available.",
            success=False,
        )

    from teambot.tasks.models import TaskStatus

    # Parse optional status filter
    status_filter = None
    if args:
        status_name = args[0].upper()
        try:
            status_filter = TaskStatus[status_name]
        except KeyError:
            valid = ", ".join([s.name.lower() for s in TaskStatus])
            return CommandResult(
                output=f"Invalid status: {args[0]}. Valid: {valid}",
                success=False,
            )

    tasks = executor.list_tasks(status=status_filter)

    if not tasks:
        return CommandResult(output="No tasks.")

    lines = ["Tasks:", ""]
    for task in tasks:
        status_icon = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.RUNNING: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.SKIPPED: "⏭️",
            TaskStatus.CANCELLED: "🚫",
        }.get(task.status, "?")

        prompt = task.prompt[:40] + "..." if len(task.prompt) > 40 else task.prompt
        lines.append(f"  {status_icon} #{task.id:4} @{task.agent_id:12} {task.status.value:10} {prompt}")

    return CommandResult(output="\n".join(lines))


def handle_task(args: list[str], executor: Optional["TaskExecutor"]) -> CommandResult:
    """Handle /task <id> command.

    Args:
        args: Task ID argument.
        executor: TaskExecutor with task state.

    Returns:
        CommandResult with task details.
    """
    if executor is None:
        return CommandResult(
            output="Task executor not available.",
            success=False,
        )

    if not args:
        return CommandResult(
            output="Usage: /task <id>",
            success=False,
        )

    task_id = args[0]
    task = executor.get_task(task_id)

    if task is None:
        return CommandResult(
            output=f"Task not found: {task_id}",
            success=False,
        )

    from teambot.tasks.models import TaskStatus

    lines = [
        f"Task #{task.id}",
        f"  Agent:   @{task.agent_id}",
        f"  Status:  {task.status.value}",
        f"  Prompt:  {task.prompt}",
    ]

    if task.dependencies:
        lines.append(f"  Depends: {', '.join(task.dependencies)}")

    # Get result if complete
    from teambot.tasks.manager import TaskManager

    # Access manager through executor
    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED):
        result = executor._manager.get_result(task.id)
        if result:
            lines.append("")
            if result.success:
                output = result.output if len(result.output) < 500 else result.output[:500] + "..."
                lines.append(f"Output:\n{output}")
            else:
                lines.append(f"Error: {result.error}")

    return CommandResult(output="\n".join(lines))


def handle_cancel(args: list[str], executor: Optional["TaskExecutor"]) -> CommandResult:
    """Handle /cancel <id> command.

    Args:
        args: Task ID argument.
        executor: TaskExecutor with task state.

    Returns:
        CommandResult with cancellation result.
    """
    if executor is None:
        return CommandResult(
            output="Task executor not available.",
            success=False,
        )

    if not args:
        return CommandResult(
            output="Usage: /cancel <id>",
            success=False,
        )

    task_id = args[0]
    cancelled = executor.cancel_task(task_id)

    if cancelled:
        return CommandResult(output=f"Cancelled task #{task_id}")
    else:
        return CommandResult(
            output=f"Could not cancel task {task_id} (not found or already complete)",
            success=False,
        )


class SystemCommands:
    """Handler for system commands in REPL.

    Provides dispatch and state management for system commands.
    """

    def __init__(self, orchestrator: Any = None, executor: Optional["TaskExecutor"] = None):
        """Initialize system commands.

        Args:
            orchestrator: Optional orchestrator for status info.
            executor: Optional task executor for task commands.
        """
        self._orchestrator = orchestrator
        self._executor: Optional["TaskExecutor"] = executor
        self._history: list[dict[str, Any]] = []

    def set_history(self, history: list[dict[str, Any]]) -> None:
        """Set history reference.

        Args:
            history: List to use for history.
        """
        self._history = history

    def set_executor(self, executor: "TaskExecutor") -> None:
        """Set task executor.

        Args:
            executor: Task executor for task commands.
        """
        self._executor = executor

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
            "tasks": self.tasks,
            "task": self.task,
            "cancel": self.cancel,
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

    def tasks(self, args: list[str]) -> CommandResult:
        """Handle /tasks command."""
        return handle_tasks(args, self._executor)

    def task(self, args: list[str]) -> CommandResult:
        """Handle /task <id> command."""
        return handle_task(args, self._executor)

    def cancel(self, args: list[str]) -> CommandResult:
        """Handle /cancel <id> command."""
        return handle_cancel(args, self._executor)
