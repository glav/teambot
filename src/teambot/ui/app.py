"""Main TeamBot application with split-pane interface."""

import asyncio
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from teambot.repl.commands import SystemCommands
from teambot.repl.parser import CommandType, parse_command
from teambot.ui.widgets import InputPane, OutputPane


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

    def __init__(self, executor=None, router=None, sdk_client=None, **kwargs):
        super().__init__(**kwargs)
        self._executor = executor
        self._router = router
        self._sdk_client = sdk_client
        self._commands = SystemCommands()
        self._pending_tasks: set[asyncio.Task] = set()
        # Track which agents have running tasks: {agent_id: task_content}
        self._running_agents: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        """Create the split-pane layout."""
        with Horizontal():
            with Vertical(id="input-pane"):
                yield Static("[bold green]TeamBot[/bold green]", id="header")
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
            output.write_info("Tip: Use @agent for tasks or /help for commands")

        event.input.clear()

    async def _handle_agent_command(self, command, output):
        """Route agent command to executor and display streaming result."""
        if not self._executor:
            output.write_info("No executor available")
            return

        agent_id = command.agent_id
        content = command.content or ""

        # Track this agent as running
        self._running_agents[agent_id] = content[:40] + "..." if len(content) > 40 else content

        # Start streaming indicator
        output.write_streaming_start(agent_id)

        try:
            # Check if we can use direct streaming with SDK client
            if (
                self._sdk_client
                and hasattr(self._sdk_client, "execute_streaming")
                and not command.is_pipeline
                and len(command.agent_ids) == 1
            ):
                # Direct streaming for simple commands
                def on_chunk(chunk: str):
                    output.write_streaming_chunk(agent_id, chunk)

                try:
                    result_content = await self._sdk_client.execute_streaming(
                        agent_id, content, on_chunk
                    )
                    output.finish_streaming(agent_id, success=True)
                except Exception as e:
                    output.finish_streaming(agent_id, success=False)
                    output.write_task_error(agent_id, str(e))
            else:
                # Use executor for complex commands (pipelines, multi-agent)
                result = await self._executor.execute(command)
                if result.background:
                    output.finish_streaming(agent_id)
                    output.write_info(result.output)
                elif result.success:
                    # Show the result since we didn't stream it
                    output.finish_streaming(agent_id, success=True)
                    if result.output:
                        output.write_task_complete(agent_id, result.output)
                else:
                    output.finish_streaming(agent_id, success=False)
                    output.write_task_error(agent_id, result.error or "Failed")
        except Exception as e:
            output.finish_streaming(agent_id, success=False)
            output.write_task_error(agent_id or "agent", str(e))
        finally:
            # Remove from running agents
            self._running_agents.pop(agent_id, None)

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

        if result.should_exit:
            self.exit()

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
                output.finish_streaming(agent_id, success=False)
                self._running_agents.pop(agent_id, None)
                return True
        return False

    def _get_status(self, output: Optional[OutputPane] = None) -> str:
        """Get agent status including running and streaming tasks.

        Args:
            output: Optional OutputPane to check streaming status.

        Returns:
            Formatted status string.
        """
        agents = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]
        lines = ["Agent Status:", ""]

        streaming_agents = output.get_streaming_agents() if output else []

        for agent in agents:
            if agent in streaming_agents:
                task_info = self._running_agents.get(agent, "")
                lines.append(f"  {agent:12} - [cyan]streaming[/cyan]: {task_info}")
            elif agent in self._running_agents:
                task_info = self._running_agents[agent]
                lines.append(f"  {agent:12} - [yellow]running[/yellow]: {task_info}")
            else:
                lines.append(f"  {agent:12} - [dim]idle[/dim]")

        return "\n".join(lines)
