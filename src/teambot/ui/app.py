"""Main TeamBot application with split-pane interface."""

import asyncio
import os
import shutil
import sys
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from teambot.repl.commands import SystemCommands
from teambot.repl.parser import Command, CommandType, parse_command
from teambot.ui.agent_state import AgentState, AgentStatusManager
from teambot.ui.widgets import InputPane, OutputPane, StatusPanel


def should_use_split_pane() -> bool:
    """Check if split-pane mode should be used.

    Returns False (legacy mode) if:
    - TEAMBOT_LEGACY_MODE=true
    - stdout is not a TTY
    - Terminal width < 80 columns
    """
    # Check legacy mode flag
    if os.environ.get("TEAMBOT_LEGACY_MODE", "").lower() == "true":
        return False

    # Check TTY
    if not sys.stdout.isatty():
        return False

    # Check terminal width
    size = shutil.get_terminal_size()
    if size.columns < 80:
        return False

    return True


class TeamBotApp(App):
    """Split-pane terminal interface for TeamBot."""

    CSS_PATH = Path(__file__).parent / "styles.css"

    def __init__(self, executor=None, router=None, sdk_client=None, config=None, **kwargs):
        super().__init__(**kwargs)
        self._executor = executor
        self._router = router
        self._sdk_client = sdk_client
        self._config = config
        self._commands = SystemCommands(executor=executor, router=router)
        self._pending_tasks: set[asyncio.Task] = set()
        # Centralized agent status manager
        self._agent_status = AgentStatusManager()
        # Initialize default agent from router
        if self._router:
            self._agent_status.set_default_agent(self._router.get_default_agent())
        # Wire status manager to executor if provided
        if self._executor:
            self._executor.set_agent_status_manager(self._agent_status)
        # Legacy: Track which agents have running tasks (kept for backward compat)
        self._running_agents: dict[str, str] = {}
        # Initialize agent models from config
        self._init_agent_models()

    def _init_agent_models(self) -> None:
        """Initialize agent models from config.

        Sets the model display for each agent based on:
        1. Agent-specific model in config
        2. Global default_model in config
        """
        if not self._config:
            return

        default_model = self._config.get("default_model")

        for agent in self._config.get("agents", []):
            agent_id = agent.get("id")
            if not agent_id:
                continue
            # Agent-specific model takes priority over default
            model = agent.get("model") or default_model
            if model:
                self._agent_status.set_model(agent_id, model)

    def compose(self) -> ComposeResult:
        """Create the split-pane layout."""
        with Horizontal():
            with Vertical(id="input-pane"):
                yield Static("[bold green]TeamBot[/bold green]", id="header")
                yield StatusPanel(self._agent_status, id="status-panel")
                yield InputPane(placeholder="@agent task or /command", id="prompt")
            yield OutputPane(id="output", highlight=True, markup=True)

    @on(InputPane.Submitted)
    async def handle_input(self, event) -> None:
        """Handle submitted input from InputPane."""
        command_text = event.value.strip()
        if not command_text:
            event.input.clear()
            return

        output = self.query_one("#output", OutputPane)

        # Echo command
        output.write_command(command_text)

        # Parse and route
        command = parse_command(command_text)

        if command.type == CommandType.AGENT:
            # Run agent command in background so input remains available
            task = asyncio.create_task(self._handle_agent_command(command, output))
            self._pending_tasks.add(task)
            task.add_done_callback(self._pending_tasks.discard)
        elif command.type == CommandType.SYSTEM:
            await self._handle_system_command(command, output)
        else:
            # Handle raw input - check if default agent is configured
            default_agent = self._router.get_default_agent() if self._router else None
            if default_agent:
                # Route to default agent
                agent_command = Command(
                    type=CommandType.AGENT,
                    agent_id=default_agent,
                    agent_ids=[default_agent],
                    content=command.content,
                )
                task = asyncio.create_task(self._handle_agent_command(agent_command, output))
                self._pending_tasks.add(task)
                task.add_done_callback(self._pending_tasks.discard)
            else:
                # Show helpful tip
                output.write_info("Tip: Use @agent for tasks or /help for commands")

        event.input.clear()

    async def _handle_agent_command(self, command, output):
        """Route agent command to executor and display streaming result."""
        if not self._executor:
            output.write_info("No executor available")
            return

        content = command.content or ""

        # Handle multi-agent commands with parallel streaming
        if (
            self._sdk_client
            and hasattr(self._sdk_client, "execute_streaming")
            and not command.is_pipeline
            and len(command.agent_ids) > 1
        ):
            await self._handle_multiagent_streaming(command, output)
            return

        agent_id = command.agent_id

        # Update centralized state: agent is now running
        self._agent_status.set_running(agent_id, content)
        # Legacy compatibility
        self._running_agents[agent_id] = content[:40] + "..." if len(content) > 40 else content

        # Start streaming indicator
        output.write_streaming_start(agent_id)

        try:
            # For simple single-agent commands WITHOUT references, use direct SDK
            # streaming for better UX but still track the task via executor's manager.
            # Commands WITH references ($agent) must go through executor for injection.
            if (
                self._sdk_client
                and hasattr(self._sdk_client, "execute_streaming")
                and not command.is_pipeline
                and len(command.agent_ids) == 1
                and not command.references  # Don't bypass executor if has $refs
            ):
                # Mark as streaming in centralized state
                self._agent_status.set_streaming(agent_id)

                # Create task for tracking (but don't execute via manager)
                task = self._executor._manager.create_task(
                    agent_id=agent_id,
                    prompt=content,
                    background=False,
                )
                task.mark_running()

                # Direct streaming for responsive output
                def on_chunk(chunk: str):
                    output.write_streaming_chunk(agent_id, chunk)

                try:
                    result_text = await self._sdk_client.execute_streaming(
                        agent_id, content, on_chunk
                    )
                    task.mark_completed(result_text)
                    # Store result by agent_id for $ref lookups
                    self._executor._manager._agent_results[agent_id] = task.result
                    self._agent_status.set_completed(agent_id)
                    output.finish_streaming(agent_id, success=True)
                except Exception as e:
                    task.mark_failed(str(e))
                    # Store failed result too for $ref lookups
                    self._executor._manager._agent_results[agent_id] = task.result
                    self._agent_status.set_failed(agent_id)
                    output.finish_streaming(agent_id, success=False)
                    output.write_task_error(agent_id, str(e))
            else:
                # Use executor for pipelines, references, and complex commands
                result = await self._executor.execute(command)
                if result.background:
                    output.finish_streaming(agent_id)
                    output.write_info(result.output)
                elif result.success:
                    self._agent_status.set_completed(agent_id)
                    output.finish_streaming(agent_id, success=True)
                    # Show the result since we didn't stream it
                    if result.output:
                        output.write_task_complete(agent_id, result.output)
                else:
                    self._agent_status.set_failed(agent_id)
                    output.finish_streaming(agent_id, success=False)
                    output.write_task_error(agent_id, result.error or "Failed")
        except Exception as e:
            self._agent_status.set_failed(agent_id)
            output.finish_streaming(agent_id, success=False)
            output.write_task_error(agent_id or "agent", str(e))
        finally:
            # Return to idle state
            self._agent_status.set_idle(agent_id)
            # Legacy compatibility
            self._running_agents.pop(agent_id, None)

    async def _handle_multiagent_streaming(self, command, output):
        """Handle multi-agent commands with parallel streaming.

        Args:
            command: Parsed command with multiple agents.
            output: OutputPane for displaying results.
        """
        content = command.content or ""
        agent_ids = command.agent_ids

        # Set up all agents as running
        for agent_id in agent_ids:
            self._agent_status.set_running(agent_id, content)
            self._running_agents[agent_id] = content[:40] + "..." if len(content) > 40 else content
            output.write_streaming_start(agent_id)
            self._agent_status.set_streaming(agent_id)

        async def stream_agent(agent_id: str):
            """Stream a single agent's response."""
            # Create task for tracking
            task = self._executor._manager.create_task(
                agent_id=agent_id,
                prompt=content,
                background=False,
            )
            task.mark_running()

            def on_chunk(chunk: str):
                output.write_streaming_chunk(agent_id, chunk)

            try:
                result_text = await self._sdk_client.execute_streaming(agent_id, content, on_chunk)
                task.mark_completed(result_text)
                self._agent_status.set_completed(agent_id)
                output.finish_streaming(agent_id, success=True)
            except Exception as e:
                task.mark_failed(str(e))
                self._agent_status.set_failed(agent_id)
                output.finish_streaming(agent_id, success=False)
                output.write_task_error(agent_id, str(e))
            finally:
                self._agent_status.set_idle(agent_id)
                self._running_agents.pop(agent_id, None)

        # Run all agents in parallel
        await asyncio.gather(
            *[stream_agent(agent_id) for agent_id in agent_ids],
            return_exceptions=True,
        )

    async def _handle_system_command(self, command, output):
        """Route system command to SystemCommands and display result."""
        if command.command == "clear":
            output.clear()
            return

        if command.command == "quit":
            self.exit()
            return

        if command.command == "status":
            # Custom status that shows running tasks and streaming
            output.write_system(self._get_status(output))
            return

        if command.command == "cancel":
            # Handle cancel command
            await self._handle_cancel_command(command.args or [], output)
            return

        # Use SystemCommands.dispatch for other commands
        result = self._commands.dispatch(command.command, command.args or [])
        output.write_system(result.output)

        # Update status panel if /model command succeeded
        if command.command == "model" and result.success:
            self._update_model_display(command.args or [])

        # Update status panel if /use-agent or /reset-agent command succeeded
        if command.command in ("use-agent", "reset-agent") and result.success:
            new_default = self._router.get_default_agent() if self._router else None
            self._agent_status.set_default_agent(new_default)

        if result.should_exit:
            self.exit()

    def _update_model_display(self, args: list[str]) -> None:
        """Update agent status model display after /model command.

        Args:
            args: Command args [agent_id, model] or [agent_id, 'clear'].
        """
        if len(args) < 2:
            return

        agent_id = args[0].lstrip("@")  # Strip @ prefix if present
        model = args[1]

        if model.lower() == "clear":
            # Restore from config
            config_model = self._get_config_model(agent_id)
            self._agent_status.set_model(agent_id, config_model)
        else:
            self._agent_status.set_model(agent_id, model)

    def _get_config_model(self, agent_id: str) -> str | None:
        """Get model for agent from config.

        Args:
            agent_id: Agent identifier.

        Returns:
            Model from agent config or default_model, or None.
        """
        if not self._config:
            return None

        # Check agent-specific model
        for agent in self._config.get("agents", []):
            if agent.get("id") == agent_id:
                if agent.get("model"):
                    return agent["model"]
                break

        # Fall back to default_model
        return self._config.get("default_model")

    async def _handle_cancel_command(self, args: list[str], output) -> None:
        """Handle /cancel command to stop streaming tasks.

        Args:
            args: Command arguments (optional agent_id or task_id).
            output: OutputPane for displaying results.
        """
        if not args:
            # Cancel all streaming agents
            streaming_agents = output.get_streaming_agents()
            if not streaming_agents:
                output.write_info("No active streaming tasks to cancel")
                return

            cancelled = 0
            for agent_id in streaming_agents:
                if await self._cancel_agent(agent_id, output):
                    cancelled += 1

            output.write_info(f"Cancelled {cancelled} streaming task(s)")
        else:
            # Cancel specific agent
            agent_id = args[0]
            if await self._cancel_agent(agent_id, output):
                output.write_info(f"Cancelled @{agent_id}")
            else:
                output.write_info(f"Could not cancel @{agent_id} (not streaming)")

    async def _cancel_agent(self, agent_id: str, output) -> bool:
        """Cancel streaming for a specific agent.

        Args:
            agent_id: Agent to cancel.
            output: OutputPane for finishing streaming.

        Returns:
            True if cancelled successfully.
        """
        if self._sdk_client and hasattr(self._sdk_client, "cancel_current_request"):
            cancelled = await self._sdk_client.cancel_current_request(agent_id)
            if cancelled:
                self._agent_status.set_idle(agent_id)
                output.finish_streaming(agent_id, success=False)
                self._running_agents.pop(agent_id, None)
                return True
        return False

    def _get_status(self, output: OutputPane | None = None) -> str:
        """Get agent status including running and streaming tasks.

        Args:
            output: Optional OutputPane (unused, kept for compatibility).

        Returns:
            Formatted status string.
        """
        lines = ["Agent Status:", ""]

        # Show default agent info
        if self._router:
            current_default = self._router.get_default_agent()
            config_default = self._router.get_config_default_agent()
            if current_default != config_default:
                lines.append(
                    f"  Default Agent: {current_default} "
                    f"(session override; config: {config_default or 'none'})"
                )
            else:
                lines.append(f"  Default Agent: {current_default or 'none'}")
            lines.append("")

        for agent_id, status in self._agent_status.get_all().items():
            if status.state == AgentState.STREAMING:
                task_info = status.task or ""
                lines.append(f"  {agent_id:12} - [cyan]streaming[/cyan]: {task_info}")
            elif status.state == AgentState.RUNNING:
                task_info = status.task or ""
                lines.append(f"  {agent_id:12} - [yellow]running[/yellow]: {task_info}")
            elif status.state == AgentState.COMPLETED:
                lines.append(f"  {agent_id:12} - [green]completed[/green]")
            elif status.state == AgentState.FAILED:
                lines.append(f"  {agent_id:12} - [red]failed[/red]")
            else:
                lines.append(f"  {agent_id:12} - [dim]idle[/dim]")

        return "\n".join(lines)
