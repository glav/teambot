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

    def __init__(self, executor=None, router=None, **kwargs):
        super().__init__(**kwargs)
        self._executor = executor
        self._router = router
        self._commands = SystemCommands()
        self._pending_tasks: set[asyncio.Task] = set()

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
            self._handle_system_command(command, output)
        else:
            output.write_info("Tip: Use @agent for tasks or /help for commands")

        event.input.clear()

    async def _handle_agent_command(self, command, output):
        """Route agent command to executor and display result."""
        if not self._executor:
            output.write_info("No executor available")
            return

        try:
            result = await self._executor.execute(command)
            if result.background:
                output.write_info(result.output)
            elif result.success:
                output.write_task_complete(command.agent_id, result.output)
            else:
                output.write_task_error(command.agent_id, result.error or "Failed")
        except Exception as e:
            output.write_task_error(command.agent_id or "agent", str(e))

    def _handle_system_command(self, command, output):
        """Route system command to SystemCommands and display result."""
        if command.command == "clear":
            output.clear()
            return

        if command.command == "quit":
            self.exit()
            return

        # Use SystemCommands.dispatch for other commands
        result = self._commands.dispatch(command.command, command.args or [])
        output.write_system(result.output)

        if result.should_exit:
            self.exit()
