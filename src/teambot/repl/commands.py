"""System commands for TeamBot REPL.

Provides /help, /status, /quit, /tasks, /models, /model commands.
"""

import importlib.metadata
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from rich.console import Console

from teambot import __version__
from teambot.config.schema import (
    get_available_models,
    get_model_info,
    is_using_cached_models,
    validate_model,
)
from teambot.repl.router import VALID_AGENTS

if TYPE_CHECKING:
    from teambot.repl.router import AgentRouter
    from teambot.tasks.executor import TaskExecutor
    from teambot.tokens.tracker import TokenTracker


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

    try:
        sdk_version = importlib.metadata.version("github-copilot-sdk")
    except importlib.metadata.PackageNotFoundError:
        sdk_version = "unknown"

    return CommandResult(
        output=f"""TeamBot v{__version__} (Copilot SDK: {sdk_version})

Available commands:
  @agent <task>  - Send task to agent (pm, ba, writer, builder-1, builder-2, reviewer)
  @notify <msg>  - Send notification to all channels (use in pipelines)
  /help          - Show this help message
  /help agent    - Show agent-specific help
  /help parallel - Show parallel execution help
  /status        - Show agent status with models
  /models        - List available AI models
  /model <a> <m> - Set model for agent in session
  /tasks         - List running/completed tasks
  /task <id>     - View task details
  /cancel <id>   - Cancel pending task
  /use-agent <id> - Set default agent for plain text input
  /reset-agent   - Reset default agent to config value
  /tokens        - Show session token usage (`/cost` is alias, `-d` for details)
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


def handle_status(args: list[str], router: "AgentRouter | None" = None) -> CommandResult:
    """Handle /status command.

    Args:
        args: Command arguments (unused).
        router: Optional AgentRouter for default agent info.

    Returns:
        CommandResult with status.
    """
    # Basic status without orchestrator
    agents = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]
    lines = ["Agent Status:", ""]

    if router:
        current_default = router.get_default_agent()
        config_default = router.get_config_default_agent()
        if current_default != config_default:
            lines.append(
                f"  Default Agent: {current_default} "
                f"(session override; config: {config_default or 'none'})"
            )
        else:
            lines.append(f"  Default Agent: {current_default or 'none'}")
        lines.append("")

    lines.append(f"  {'Agent':<12} {'Status':<10} {'Model':<20}")
    lines.append(f"  {'-' * 12} {'-' * 10} {'-' * 20}")
    for agent in agents:
        lines.append(f"  {agent:<12} {'idle':<10} {'(default)':<20}")

    return CommandResult(output="\n".join(lines))


def handle_quit(args: list[str]) -> CommandResult:
    """Handle /quit command.

    Args:
        args: Command arguments (unused).

    Returns:
        CommandResult with exit flag.
    """
    return CommandResult(output="Goodbye!", should_exit=True)


async def handle_models(args: list[str]) -> CommandResult:
    """Handle /models command - list all available models.

    Args:
        args: Command arguments. Supports --refresh to force cache update.

    Returns:
        CommandResult with list of available models.
    """
    # Check for --refresh flag
    if args and args[0] == "--refresh":
        return await _handle_models_refresh()

    models = get_available_models()

    # Handle no models available
    if not models:
        return CommandResult(
            output=(
                "[red]✗ No models available[/red]\n"
                "[yellow]Model cache is empty or expired.[/yellow]\n"
                "[dim]Run '/models --refresh' to fetch from SDK.[/dim]"
            ),
            success=False,
        )

    lines = ["Available Models:", ""]

    # Group by category
    categories: dict[str, list[tuple[str, str, float | None]]] = {
        "standard": [],
        "fast": [],
        "premium": [],
    }

    for model_id in models:
        info = get_model_info(model_id)
        if info:
            display_name = info.get("display", model_id)
            category = info.get("category", "standard")
            multiplier = info.get("multiplier")
        else:
            display_name = model_id
            category = "standard"
            multiplier = None
        categories.setdefault(category, []).append((model_id, display_name, multiplier))

    for category in ["standard", "fast", "premium"]:
        if categories.get(category):
            lines.append(f"  {category.upper()}:")
            for model_id, display_name, multiplier in categories[category]:
                if multiplier is not None:
                    lines.append(f"    {model_id:25} ({display_name}) [dim]\\[{multiplier}x][/dim]")
                else:
                    lines.append(f"    {model_id:25} ({display_name})")
            lines.append("")

    # Add cache status
    if is_using_cached_models():
        import time

        from teambot.config.model_cache import get_cache_timestamp

        ts = get_cache_timestamp()
        if ts:
            age_hours = (time.time() - ts) / 3600
            if age_hours < 1:
                age_str = f"{int(age_hours * 60)} minutes ago"
            else:
                age_str = f"{age_hours:.1f} hours ago"
            lines.append(f"  (Cached: {age_str})")
    lines.append("")

    lines.append("Usage: @pm --model <model> <task>")
    lines.append("       /model <agent> <model>  - Set session model for agent")
    lines.append("       /models --refresh       - Refresh from SDK")

    return CommandResult(output="\n".join(lines))


async def _handle_models_refresh() -> CommandResult:
    """Handle /models --refresh to force cache update.

    Returns:
        CommandResult with refresh status.
    """
    from teambot.config.schema import refresh_models

    try:
        success = await refresh_models()

        if success:
            count = len(get_available_models())
            return CommandResult(output=f"✓ Model cache refreshed: {count} models available.")
        else:
            return CommandResult(
                output=(
                    "[red]✗ Failed to refresh models[/red]\n"
                    "[dim]Check network connectivity and SDK installation.[/dim]\n"
                    "[dim]Run 'copilot --version' to verify SDK.[/dim]"
                ),
                success=False,
            )
    except Exception as e:
        return CommandResult(
            output=(
                f"[red]✗ Error refreshing models: {type(e).__name__}[/red]\n"
                "[dim]Run 'copilot --version' to verify SDK installation.[/dim]"
            ),
            success=False,
        )


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

    # Validate agent ID exists
    if agent_id not in VALID_AGENTS:
        valid_agents = ", ".join(sorted(VALID_AGENTS))
        return CommandResult(
            output=f"Invalid agent '{agent_id}'. Valid agents: {valid_agents}",
            success=False,
        )

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


def handle_use_agent(args: list[str], router: "AgentRouter | None" = None) -> CommandResult:
    """Handle /use-agent command - view or set default agent.

    Args:
        args: [agent_id] or [] to view current default.
        router: AgentRouter instance for mutation.

    Returns:
        CommandResult with agent info or confirmation.
    """
    if router is None:
        return CommandResult(output="Router not available.", success=False)

    if not args:
        current = router.get_default_agent() or "none"
        agents = ", ".join(sorted(router.get_all_agents()))
        return CommandResult(output=f"Current default agent: {current}\nAvailable agents: {agents}")

    raw_id = args[0]
    if not router.is_valid_agent(raw_id):
        agents = ", ".join(sorted(router.get_all_agents()))
        return CommandResult(
            output=f"Unknown agent '{raw_id}'. Available agents: {agents}",
            success=False,
        )

    agent_id = router.resolve_agent_id(raw_id)
    current = router.get_default_agent()
    if current == agent_id:
        return CommandResult(output=f"Default agent is already set to {agent_id}.")

    router.set_default_agent(agent_id)
    return CommandResult(
        output=f"Default agent set to {agent_id}. "
        f"Plain text input will now be routed to @{agent_id}."
    )


def handle_reset_agent(args: list[str], router: "AgentRouter | None" = None) -> CommandResult:
    """Handle /reset-agent command - reset default agent to config value.

    Args:
        args: Command arguments (unused).
        router: Optional AgentRouter instance for mutation.

    Returns:
        CommandResult with confirmation.
    """
    if router is None:
        return CommandResult(output="Router not available.", success=False)

    config_default = router.get_config_default_agent()
    current = router.get_default_agent()

    if current == config_default:
        label = config_default or "none"
        return CommandResult(
            output=f"Default agent is already set to {label} (from configuration)."
        )

    router.set_default_agent(config_default)
    label = config_default or "none"
    return CommandResult(output=f"Default agent reset to {label} (from configuration).")


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
    lines.append(f"  {'ID':<10} {'Agent':<12} {'Model':<15} {'Status':<11} {'Task'}")
    lines.append(f"  {'-' * 10} {'-' * 12} {'-' * 15} {'-' * 11} {'-' * 20}")
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
        status_text = task.status.name.replace("_", " ").title()
        # Truncate status text if needed (icon=1 + space=1 leaves 9 chars for text)
        if len(status_text) > 9:
            status_text = status_text[:8] + "…"
        status_display = f"{status_icon} {status_text}"

        prompt = task.prompt[:30] + "..." if len(task.prompt) > 30 else task.prompt
        model_display = task.model if task.model else "(default)"
        if len(model_display) > 15:
            model_display = model_display[:12] + "..."

        agent_id = f"@{task.agent_id}"
        line = f"  {task.id:<10} {agent_id:<12} {model_display:<15} {status_display:<11} {prompt}"
        lines.append(line)

    lines.append("")
    lines.append("Use: /task <id> to view details")

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


def handle_tokens(args: list[str], token_tracker: Optional["TokenTracker"] = None) -> CommandResult:
    """Handle /tokens command - show session token usage.

    Args:
        args: Command arguments. Supports --detailed or -d for per-agent breakdown.
        token_tracker: Optional TokenTracker instance (may be None if tracking disabled).

    Returns:
        CommandResult with token usage summary.
    """
    if token_tracker is None:
        return CommandResult(output="Token tracking is disabled")

    total = token_tracker.get_total()
    if total.total_tokens is None or total.total_tokens == 0:
        return CommandResult(output="No token usage recorded yet")

    # Check for --detailed flag
    detailed = "--detailed" in args or "-d" in args

    if detailed:
        from teambot.tokens.display import render_token_summary

        by_agent = token_tracker.get_by_agent()
        panel = render_token_summary(total, by_agent)
        # Convert Rich Panel to string for CommandResult
        console = Console(force_terminal=False, no_color=True, width=80)
        with console.capture() as capture:
            console.print(panel)
        return CommandResult(output=capture.get().strip())
    else:
        from teambot.tokens.display import render_session_summary

        summary = render_session_summary(total)
        return CommandResult(output=summary)


class SystemCommands:
    """Handler for system commands in REPL.

    Provides dispatch and state management for system commands.
    """

    def __init__(
        self,
        orchestrator: Any = None,
        executor: Optional["TaskExecutor"] = None,
        router: Optional["AgentRouter"] = None,
        config: dict | None = None,
        token_tracker: Optional["TokenTracker"] = None,
    ):
        """Initialize system commands.

        Args:
            orchestrator: Optional orchestrator for status info.
            executor: Optional task executor for task commands.
            router: Optional agent router for default agent commands.
            config: Optional configuration dict for notification settings.
            token_tracker: Optional TokenTracker for session token usage.
        """
        self._orchestrator = orchestrator
        self._executor: TaskExecutor | None = executor
        self._router = router
        self._config = config
        self._token_tracker = token_tracker
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

    def set_router(self, router: Optional["AgentRouter"]) -> None:
        """Set agent router for agent switching commands.

        Args:
            router: Agent router for default agent management.
        """
        self._router = router

    async def dispatch(self, command: str, args: list[str]) -> CommandResult:
        """Dispatch a system command.

        Args:
            command: The command name (without /).
            args: Command arguments.

        Returns:
            CommandResult from handler.
        """
        import asyncio

        handlers = {
            "help": self.help,
            "status": self.status,
            "quit": self.quit,
            "exit": self.quit,  # Alias
            "tasks": self.tasks,
            "task": self.task,
            "cancel": self.cancel,
            "models": self.models,
            "model": self.model,
            "use-agent": self.use_agent,
            "reset-agent": self.reset_agent,
            "tokens": self.tokens,
            "cost": self.tokens,  # Alias
        }

        handler = handlers.get(command)
        if handler is None:
            return CommandResult(
                output=f"Unknown command: /{command}. Type /help for available commands.",
                success=False,
            )

        result = handler(args)
        # Handle both sync and async handlers
        if asyncio.iscoroutine(result):
            return await result
        return result

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

        return handle_status(args, self._router)

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

    async def models(self, args: list[str]) -> CommandResult:
        """Handle /models command."""
        return await handle_models(args)

    def model(self, args: list[str]) -> CommandResult:
        """Handle /model command."""
        return handle_model(args, self._session_model_overrides)

    def use_agent(self, args: list[str]) -> CommandResult:
        """Handle /use-agent command."""
        return handle_use_agent(args, self._router)

    def reset_agent(self, args: list[str]) -> CommandResult:
        """Handle /reset-agent command."""
        return handle_reset_agent(args, self._router)

    def tokens(self, args: list[str]) -> CommandResult:
        """Handle /tokens command."""
        return handle_tokens(args, self._token_tracker)
