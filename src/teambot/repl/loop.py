"""REPL loop for TeamBot interactive mode.

Provides the main read-eval-print loop for interactive commands.
"""

import asyncio
import signal

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError
from teambot.repl.commands import SystemCommands
from teambot.repl.parser import CommandType, ParseError, parse_command
from teambot.repl.router import AgentRouter, RouterError
from teambot.tasks.executor import TaskExecutor, is_pseudo_agent
from teambot.tasks.models import Task, TaskResult
from teambot.ui.agent_state import AgentStatusManager
from teambot.visualization.overlay import OverlayPosition, OverlayRenderer


class REPLLoop:
    """Interactive REPL loop for TeamBot.

    Provides:
    - Command input with rich prompt
    - Agent command routing to SDK
    - System command handling
    - Signal handling (Ctrl+C)
    - Persistent status overlay
    """

    def __init__(
        self,
        console: Console | None = None,
        sdk_client: CopilotSDKClient | None = None,
        enable_overlay: bool = True,
        config: dict | None = None,
    ):
        """Initialize the REPL loop.

        Args:
            console: Rich console for output.
            sdk_client: Copilot SDK client (created if not provided).
            enable_overlay: Whether to enable status overlay.
            config: Optional configuration dict with default_agent setting.
        """
        self._console = console or Console()
        self._sdk_client = sdk_client or CopilotSDKClient()
        self._config = config

        # Extract default agent from config if provided
        default_agent = None
        if config and "default_agent" in config:
            default_agent = config["default_agent"]

        self._router = AgentRouter(default_agent=default_agent)
        self._commands = SystemCommands(router=self._router, config=config)
        self._running = False
        self._interrupted = False
        self._sdk_connected = False

        # Task executor for parallel execution
        self._executor: TaskExecutor | None = None

        # Status overlay - load position from config if provided
        overlay_position = OverlayPosition.TOP_RIGHT  # default
        if config and "overlay" in config:
            overlay_config = config["overlay"]
            if "position" in overlay_config:
                try:
                    overlay_position = OverlayPosition(overlay_config["position"])
                except ValueError:
                    pass  # Use default if invalid
            if "enabled" in overlay_config:
                enable_overlay = overlay_config["enabled"]

        self._overlay = OverlayRenderer(
            console=self._console, position=overlay_position, enabled=enable_overlay
        )
        self._commands.set_overlay(self._overlay)

        # Wire up handlers
        self._router.register_agent_handler(self._handle_agent_command)
        self._router.register_system_handler(self._commands.dispatch)
        self._router.register_raw_handler(self._handle_raw_input)

        # Share history with commands
        self._commands.set_history(self._router._history)

    async def _handle_agent_command(self, agent_id: str, content: str) -> str:
        """Handle an agent command via SDK.

        Args:
            agent_id: The agent identifier.
            content: The task content.

        Returns:
            Response from SDK.
        """
        self._console.print(f"[dim]Sending to @{agent_id}...[/dim]")

        if not self._sdk_connected:
            return "[red]SDK not connected. Please rebuild the devcontainer.[/red]"

        try:
            response = await self._sdk_client.execute(agent_id, content)
            return response
        except SDKClientError as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower():
                return (
                    "[red]Request timed out.[/red]\n"
                    "[yellow]This usually means Copilot is not authenticated.[/yellow]\n"
                    "[dim]Run 'copilot' then '/login' to authenticate, or set GITHUB_TOKEN.[/dim]"
                )
            return f"[red]SDK Error: {e}[/red]"

    async def _handle_advanced_command(self, command) -> str:
        """Handle multi-agent, pipeline, or background commands.

        Args:
            command: Parsed command with advanced features.

        Returns:
            Result message.
        """
        if not self._executor:
            return "[red]Task executor not available.[/red]"

        # Check SDK connection before executing
        if not self._sdk_connected:
            return "[red]SDK not connected. Please rebuild the devcontainer.[/red]"

        # Execute via TaskExecutor
        result = await self._executor.execute(command)

        if result.background:
            # Background task - just return the start message
            return f"[green]{result.output}[/green]"

        if result.success:
            return result.output
        else:
            return f"[red]{result.error or 'Execution failed'}[/red]\n{result.output}"

    def _on_task_complete(self, task: Task, result: TaskResult) -> None:
        """Callback when background task completes.

        Args:
            task: The completed task.
            result: Task result.
        """
        # Update overlay
        self._overlay.on_task_completed(task, result)

        # Print notification
        if result.success:
            self._overlay.print_with_overlay(
                f"\n[green]✓ Task #{task.id} completed (@{task.agent_id})[/green]"
            )
        else:
            self._overlay.print_with_overlay(
                f"\n[red]✗ Task #{task.id} failed (@{task.agent_id}): {result.error}[/red]"
            )

    def _on_task_started(self, task: Task) -> None:
        """Callback when task starts.

        Args:
            task: The started task.
        """
        self._overlay.on_task_started(task)

    def _on_stage_change(self, current: int, total: int, agents: list[str]) -> None:
        """Callback when pipeline stage changes.

        Args:
            current: Current stage number (1-indexed).
            total: Total number of stages.
            agents: List of agent IDs in the current stage.
        """
        self._overlay.on_pipeline_stage_change(current, total, agents)

    def _on_pipeline_complete(self) -> None:
        """Callback when pipeline completes."""
        self._overlay.clear_pipeline_progress()

    def _on_stage_output(self, agent_id: str, output: str) -> None:
        """Callback for intermediate stage output.

        Args:
            agent_id: Agent that produced the output.
            output: The output text.
        """
        self._overlay.print_with_overlay(f"\n[dim]─── @{agent_id} ───[/dim]\n{output}")

    def _handle_raw_input(self, content: str) -> str:
        """Handle raw (non-command) input.

        Args:
            content: The raw input text.

        Returns:
            Help message.
        """
        if not content.strip():
            return ""

        return (
            "[yellow]Tip: Use @agent to send commands to agents, "
            "or /help for available commands.[/yellow]"
        )

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""

        def handle_interrupt(signum, frame):
            self._interrupted = True
            self._console.print("\n[yellow]Interrupted. Press Ctrl+C again to exit.[/yellow]")

        signal.signal(signal.SIGINT, handle_interrupt)

    def _restore_signal_handlers(self) -> None:
        """Restore default signal handlers."""
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    async def run(self) -> None:
        """Run the REPL loop.

        Main entry point for interactive mode.
        """
        self._running = True
        self._setup_signal_handlers()

        # Show welcome banner
        self._console.print(
            Panel(
                "[bold cyan]TeamBot Interactive Mode[/bold cyan]\n"
                "Type [green]@agent task[/green] to send commands, "
                "[green]/help[/green] for help, "
                "[green]/quit[/green] to exit.",
                title="Welcome",
            )
        )

        # Start SDK client
        self._sdk_connected = False
        try:
            if self._sdk_client.is_available():
                await self._sdk_client.start()
                self._console.print("[green]✓ SDK connected[/green]")
                self._sdk_connected = True
            else:
                self._console.print("[red]✗ Copilot SDK not installed[/red]")
                self._console.print("[dim]Run: uv add github-copilot-sdk[/dim]")
        except SDKClientError as e:
            self._console.print(f"[red]✗ SDK error: {e}[/red]")
        except Exception as e:
            self._console.print("[red]✗ SDK connection failed[/red]")
            self._console.print(f"[dim]{e}[/dim]")
            self._console.print(
                "[yellow]Tip: Rebuild the devcontainer to update Copilot CLI.[/yellow]"
            )

        # Check authentication status
        if self._sdk_connected:
            if self._sdk_client.is_authenticated():
                self._console.print("[green]✓ Copilot authenticated[/green]")
            else:
                self._console.print("[yellow]! Copilot not authenticated[/yellow]")
                self._console.print(
                    "[dim]Run 'copilot' then '/login' to authenticate, "
                    "or set GITHUB_TOKEN env var.[/dim]"
                )

        # Initialize task executor (always, even if SDK not connected)
        # This allows /tasks command to work for viewing task history
        self._agent_status = AgentStatusManager()
        self._executor = TaskExecutor(
            sdk_client=self._sdk_client,
            on_task_complete=self._on_task_complete,
            on_task_started=self._on_task_started,
            on_stage_change=self._on_stage_change,
            on_stage_output=self._on_stage_output,
            on_pipeline_complete=self._on_pipeline_complete,
            agent_status_manager=self._agent_status,
            config=self._config,
        )
        self._commands.set_executor(self._executor)

        # Start overlay if supported
        if self._overlay.is_supported:
            self._console.print("[green]✓ Status overlay enabled[/green]")
            await self._overlay.start_spinner()
            self._overlay.render()
        else:
            self._console.print("[dim]Status overlay not available in this terminal[/dim]")

        # Main loop
        try:
            while self._running:
                try:
                    # Get input
                    user_input = await self._get_input()

                    if user_input is None:
                        continue

                    # Check for interrupt
                    if self._interrupted:
                        self._interrupted = False
                        continue

                    # Parse command
                    try:
                        command = parse_command(user_input)
                    except ParseError as e:
                        self._console.print(f"[red]Parse error: {e}[/red]")
                        continue

                    # Route command
                    try:
                        # Check if this is an advanced agent command
                        if command.type == CommandType.AGENT and (
                            command.is_pipeline
                            or len(command.agent_ids) > 1
                            or command.background
                            or command.references  # Has $ref dependencies
                            or (command.agent_id and is_pseudo_agent(command.agent_id))
                        ):
                            # Use task executor for parallel/pipeline/background/references
                            result = await self._handle_advanced_command(command)
                            self._console.print(result)
                        else:
                            # Use existing router for system commands only
                            result = await self._router.route(command)

                            # Handle system command results
                            if command.type == CommandType.SYSTEM:
                                self._console.print(result.output)
                                if result.should_exit:
                                    self._running = False
                            elif result:
                                self._console.print(result)

                    except RouterError as e:
                        self._console.print(f"[red]Error: {e}[/red]")

                except KeyboardInterrupt:
                    # Double Ctrl+C to exit
                    if self._interrupted:
                        self._running = False
                    else:
                        self._interrupted = True
                        self._console.print("\n[yellow]Press Ctrl+C again to exit.[/yellow]")

        finally:
            await self._cleanup()

    async def _get_input(self) -> str | None:
        """Get input from user.

        Supports multi-line input via backslash continuation: end a line with
        ``\\`` to continue on the next line.

        Returns:
            User input string or None if cancelled.
        """
        try:
            loop = asyncio.get_running_loop()
            line = await loop.run_in_executor(
                None, lambda: Prompt.ask("[bold green]teambot[/bold green]")
            )
            # Backslash continuation for multi-line input in legacy mode
            lines = [line]
            while lines[-1].endswith("\\"):
                lines[-1] = lines[-1][:-1]
                cont = await loop.run_in_executor(
                    None, lambda: Prompt.ask("[bold green]   ...[/bold green]")
                )
                lines.append(cont)
            return "\n".join(lines)
        except EOFError:
            self._running = False
            return None
        except KeyboardInterrupt:
            return None

    async def _cleanup(self) -> None:
        """Clean up resources."""
        self._restore_signal_handlers()

        # Stop overlay spinner
        if self._overlay:
            await self._overlay.stop_spinner()
            self._overlay.clear()

        if self._sdk_client:
            try:
                await self._sdk_client.stop()
            except Exception:
                pass

        self._console.print("[dim]Session ended.[/dim]")


async def run_interactive_mode(console: Console | None = None, config: dict | None = None) -> None:
    """Run TeamBot in interactive mode.

    Args:
        console: Optional Rich console for output.
        config: Optional configuration dict with default_agent setting.

    Uses split-pane Textual interface when supported, falls back to legacy mode
    for narrow terminals or when TEAMBOT_LEGACY_MODE=true.
    """
    import os

    # Check if split-pane is explicitly enabled via env var
    split_pane_flag = os.environ.get("TEAMBOT_SPLIT_PANE", "").lower() == "true"

    # Import here to avoid circular imports
    from teambot.ui.app import TeamBotApp, should_use_split_pane

    if split_pane_flag or should_use_split_pane():
        # Use new Textual split-pane interface
        from teambot.repl.router import AgentRouter

        sdk_client = CopilotSDKClient()

        # Start SDK client
        try:
            if sdk_client.is_available():
                await sdk_client.start()
        except Exception:
            pass  # Will show error when command is executed

        executor = TaskExecutor(sdk_client=sdk_client, config=config)

        # Extract default agent from config if provided
        default_agent = None
        if config and "default_agent" in config:
            default_agent = config["default_agent"]

        router = AgentRouter(default_agent=default_agent)

        app = TeamBotApp(executor=executor, router=router, sdk_client=sdk_client, config=config)
        try:
            await app.run_async()
        finally:
            # Clean up SDK client
            try:
                await sdk_client.stop()
            except Exception:
                pass
    else:
        # Legacy mode with overlay
        repl = REPLLoop(console=console, config=config)
        await repl.run()
