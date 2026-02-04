"""System commands for TeamBot REPL.

Provides /help, /status, /history, /quit, /tasks, /overlay, /models, /model commands.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from teambot.config.schema import MODEL_INFO, VALID_MODELS, validate_model

if TYPE_CHECKING:
    from teambot.tasks.executor import TaskExecutor
    from teambot.visualization.overlay import OverlayRenderer


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
  /status        - Show agent status with models
  /models        - List available AI models
  /model <a> <m> - Set model for agent in session
  /tasks         - List running/completed tasks
  /task <id>     - View task details
  /cancel <id>   - Cancel pending task
  /overlay       - Show/toggle status overlay
  /history       - Show command history
  /quit          - Exit interactive mode

Model Selection:
  @pm --model gpt-5 Create plan     # Inline model override
  @pm -m claude-opus-4.5 Review     # Short form
  /model pm gpt-5                    # Set for session

Examples:
  @pm Create a project plan
  @builder-1 --model gpt-5 Implement the login feature
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
    lines.append(f"  {'Agent':<12} {'Status':<10} {'Model':<20}")
    lines.append(f"  {'-' * 12} {'-' * 10} {'-' * 20}")
    for agent in agents:
        lines.append(f"  {agent:<12} {'idle':<10} {'(default)':<20}")

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


def handle_models(args: list[str]) -> CommandResult:
    """Handle /models command - list all available models.

    Args:
        args: Command arguments (unused).

    Returns:
        CommandResult with list of available models.
    """
    lines = ["Available Models:", ""]

    # Group by category
    categories: dict[str, list[tuple[str, str]]] = {
        "standard": [],
        "fast": [],
        "premium": [],
    }

    for model_id in sorted(VALID_MODELS):
        info = MODEL_INFO.get(model_id, {})
        display_name = info.get("display_name", model_id)
        category = info.get("category", "standard")
        categories.setdefault(category, []).append((model_id, display_name))

    for category in ["standard", "fast", "premium"]:
        if categories.get(category):
            lines.append(f"  {category.upper()}:")
            for model_id, display_name in categories[category]:
                lines.append(f"    {model_id:25} ({display_name})")
            lines.append("")

    lines.append("Usage: @pm --model <model> <task>")
    lines.append("       /model <agent> <model>  - Set session model for agent")

    return CommandResult(output="\n".join(lines))


def handle_model(args: list[str], session_overrides: dict[str, str]) -> CommandResult:
    """Handle /model command - view or set session model overrides.

    Args:
        args: [agent_id, model] or [] to view current overrides.
        session_overrides: Dict to modify with session model settings.

    Returns:
        CommandResult with model info or confirmation.
    """
    if not args:
        # Show current session overrides
        if not session_overrides:
            return CommandResult(
                output="No session model overrides set.\n"
                "Use: /model <agent> <model> to set a model for an agent."
            )

        lines = ["Session Model Overrides:", ""]
        for agent_id, model in sorted(session_overrides.items()):
            lines.append(f"  {agent_id:12} -> {model}")
        lines.append("")
        lines.append("Use: /model <agent> clear  - to clear an override")
        return CommandResult(output="\n".join(lines))

    if len(args) < 2:
        return CommandResult(
            output="Usage: /model <agent> <model>\n"
            "       /model <agent> clear  - clear override\n"
            "       /model                - show current overrides",
            success=False,
        )

    agent_id = args[0]
    model = args[1]

    # Handle clear command
    if model.lower() == "clear":
        if agent_id in session_overrides:
            del session_overrides[agent_id]
            return CommandResult(output=f"Cleared model override for {agent_id}")
        return CommandResult(output=f"No model override set for {agent_id}")

    # Validate model
    if not validate_model(model):
        return CommandResult(
            output=f"Invalid model '{model}'. Use /models to see available models.",
            success=False,
        )

    session_overrides[agent_id] = model
    return CommandResult(output=f"Set model for {agent_id} to {model} for this session.")


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
    lines.append(f"  {'ID':<6} {'Agent':<12} {'Model':<15} {'Status':<11} {'Task'}")
    lines.append(f"  {'-' * 6} {'-' * 12} {'-' * 15} {'-' * 11} {'-' * 20}")
    for task in tasks:
        status_icon = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.RUNNING: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.SKIPPED: "⏭️",
            TaskStatus.CANCELLED: "🚫",
        }.get(task.status, "?")

        # Format status with icon and text
        status_text = task.status.name.replace('_', ' ').title()
        status_display = f"{status_icon} {status_text}"
        
        prompt = task.prompt[:30] + "..." if len(task.prompt) > 30 else task.prompt
        model_display = task.model if task.model else "(default)"
        if len(model_display) > 15:
            model_display = model_display[:12] + "..."
        
        # Format line with proper column widths matching header
        task_id = f"#{task.id}"
        agent_id = f"@{task.agent_id}"
        line = f"  {task_id:<6} {agent_id:<12} {model_display:<15} {status_display:<11} {prompt}"
        lines.append(line)

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

    model_display = task.model if task.model else "(default)"
    lines = [
        f"Task #{task.id}",
        f"  Agent:   @{task.agent_id}",
        f"  Model:   {model_display}",
        f"  Status:  {task.status.value}",
        f"  Prompt:  {task.prompt}",
    ]

    if task.dependencies:
        lines.append(f"  Depends: {', '.join(task.dependencies)}")

    # Get result if complete

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


def handle_overlay(args: list[str], overlay: Optional["OverlayRenderer"]) -> CommandResult:
    """Handle /overlay command.

    Args:
        args: Subcommand and arguments.
        overlay: OverlayRenderer instance.

    Returns:
        CommandResult with overlay status or action result.
    """
    if overlay is None:
        return CommandResult(
            output="Overlay not available.",
            success=False,
        )

    if not overlay.is_supported:
        return CommandResult(
            output="Overlay not supported in this terminal.",
            success=False,
        )

    # No args - show status
    if not args:
        status = "enabled" if overlay.is_enabled else "disabled"
        position = overlay.state.position.value
        return CommandResult(
            output=f"Overlay: {status}, position: {position}\n"
            f"Use /overlay on|off to toggle, /overlay position <pos> to move."
        )

    subcommand = args[0].lower()

    if subcommand == "on":
        overlay.enable()
        return CommandResult(output="Overlay enabled.")

    elif subcommand == "off":
        overlay.disable()
        return CommandResult(output="Overlay disabled. Use /overlay on to re-enable.")

    elif subcommand == "position":
        if len(args) < 2:
            return CommandResult(
                output="Usage: /overlay position <top-right|top-left|bottom-right|bottom-left>",
                success=False,
            )

        from teambot.visualization.overlay import OverlayPosition

        pos_name = args[1].lower()
        try:
            position = OverlayPosition(pos_name)
            overlay.set_position(position)
            return CommandResult(output=f"Overlay position set to {pos_name}.")
        except ValueError:
            valid = ", ".join([p.value for p in OverlayPosition])
            return CommandResult(
                output=f"Invalid position: {pos_name}. Valid: {valid}",
                success=False,
            )

    else:
        return CommandResult(
            output=f"Unknown overlay subcommand: {subcommand}. Use on, off, or position.",
            success=False,
        )


class SystemCommands:
    """Handler for system commands in REPL.

    Provides dispatch and state management for system commands.
    """

    def __init__(
        self,
        orchestrator: Any = None,
        executor: Optional["TaskExecutor"] = None,
        overlay: Optional["OverlayRenderer"] = None,
    ):
        """Initialize system commands.

        Args:
            orchestrator: Optional orchestrator for status info.
            executor: Optional task executor for task commands.
            overlay: Optional overlay renderer for overlay commands.
        """
        self._orchestrator = orchestrator
        self._executor: TaskExecutor | None = executor
        self._overlay: OverlayRenderer | None = overlay
        self._history: list[dict[str, Any]] = []
        self._session_model_overrides: dict[str, str] = {}

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

    def set_overlay(self, overlay: "OverlayRenderer") -> None:
        """Set overlay renderer.

        Args:
            overlay: Overlay renderer for overlay commands.
        """
        self._overlay = overlay

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
            "overlay": self.overlay,
            "models": self.models,
            "model": self.model,
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

    def overlay(self, args: list[str]) -> CommandResult:
        """Handle /overlay command."""
        return handle_overlay(args, self._overlay)

    def models(self, args: list[str]) -> CommandResult:
        """Handle /models command."""
        return handle_models(args)

    def model(self, args: list[str]) -> CommandResult:
        """Handle /model command."""
        return handle_model(args, self._session_model_overrides)
