"""Live agent status panel widget for TeamBot UI.

Displays persistent agent status in the left pane with live updates.
"""

import subprocess
from typing import TYPE_CHECKING

from textual.widgets import Static

from teambot.ui.agent_state import AgentState

if TYPE_CHECKING:
    from teambot.ui.agent_state import AgentStatusManager


class StatusPanel(Static):
    """Displays live agent status in left pane.

    Shows all 6 agents with their current status (idle/running/streaming)
    and task information for active agents. Updates automatically when
    agent status changes via the AgentStatusManager listener pattern.
    """

    DEFAULT_CSS = """
    StatusPanel {
        height: 1fr;
        overflow-y: hidden;
        text-overflow: ellipsis;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        status_manager: "AgentStatusManager",
        **kwargs,
    ):
        """Initialize the status panel.

        Args:
            status_manager: The AgentStatusManager to observe for status changes.
            **kwargs: Additional arguments passed to Static.
        """
        super().__init__(**kwargs)
        self._status_manager = status_manager
        self._git_branch: str = ""
        self._git_refresh_timer = None

    def on_mount(self) -> None:
        """Called when widget is mounted to the DOM."""
        # Register for status updates
        self._status_manager.add_listener(self._on_status_change)
        # Get initial git branch
        self._git_branch = self._get_git_branch()
        # Refresh git branch periodically (every 30 seconds)
        self._git_refresh_timer = self.set_interval(30, self._refresh_git_branch)
        # Initial render
        self.update(self._format_status())

    def on_unmount(self) -> None:
        """Called when widget is unmounted from the DOM."""
        # Clean up listener to prevent memory leaks
        self._status_manager.remove_listener(self._on_status_change)
        # Stop the git refresh timer
        if self._git_refresh_timer:
            self._git_refresh_timer.stop()

    def _on_status_change(self, manager: "AgentStatusManager") -> None:
        """Called when any agent status changes.

        Args:
            manager: The AgentStatusManager that triggered the update.
        """
        self.update(self._format_status())

    def _refresh_git_branch(self) -> None:
        """Refresh the git branch name."""
        self._git_branch = self._get_git_branch()
        self.update(self._format_status())

    def _get_git_branch(self) -> str:
        """Get current git branch name.

        Returns:
            Branch name if in a git repo, empty string otherwise.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return ""

    def _format_status(self) -> str:
        """Format the status panel content.

        Returns:
            Rich markup string for display.
        """
        lines = []

        # Git branch header (if available)
        if self._git_branch:
            branch_display = self._git_branch
            if len(branch_display) > 25:
                branch_display = branch_display[:22] + "..."
            lines.append(f"[dim]Branch:[/dim] [white]{branch_display}[/white]")
            lines.append("")

        # Agent status list
        lines.append("[bold]Agents[/bold]")
        default_agent = self._status_manager.get_default_agent()
        for agent_id, status in self._status_manager.get_all().items():
            indicator = self._get_indicator(status.state)
            line = f"{indicator} {agent_id}"

            # Add default agent indicator
            is_default = agent_id == default_agent
            if is_default:
                line += " [bold cyan]★[/bold cyan]"

            # Add model indicator if set - with nice abbreviated display
            # Pseudo-agents like "notify" show "(n/a)" instead of model
            if agent_id == "notify":
                line += " [dim italic](n/a)[/dim italic]"
            elif status.model:
                model_display = self._format_model_name(status.model)
                line += f" [dim italic]({model_display})[/dim italic]"

            # Add task info for active agents (indented on next line)
            if status.state in (AgentState.RUNNING, AgentState.STREAMING):
                lines.append(line)
                if status.task:
                    # Truncate task for display
                    task_display = status.task
                    if len(task_display) > 30:
                        task_display = task_display[:27] + "..."
                    lines.append(f"  [dim]→ {task_display}[/dim]")
            elif status.state == AgentState.IDLE:
                if is_default:
                    lines.append(f"{line} [bold cyan]default[/bold cyan]")
                else:
                    lines.append(f"{line} [dim]idle[/dim]")
            else:
                lines.append(line)

        return "\n".join(lines)

    def _format_model_name(self, model: str) -> str:
        """Format model name for compact display.

        Args:
            model: Full model name (e.g., 'claude-sonnet-4', 'gpt-4o-mini').

        Returns:
            Abbreviated display name (e.g., 'sonnet-4', 'gpt-4o-mini').
        """
        # Common abbreviations for cleaner display
        abbreviations = {
            "claude-sonnet-4": "sonnet-4",
            "claude-sonnet-4.5": "sonnet-4.5",
            "claude-haiku-4": "haiku-4",
            "claude-haiku-4.5": "haiku-4.5",
            "claude-opus-4": "opus-4",
            "claude-opus-4.5": "opus-4.5",
        }

        if model in abbreviations:
            return abbreviations[model]

        # For other models, truncate if too long
        if len(model) > 18:
            return model[:15] + "..."

        return model

    def _get_indicator(self, state: AgentState) -> str:
        """Get colored indicator for agent state.

        Args:
            state: The agent's current state.

        Returns:
            Rich markup string for the state indicator.
        """
        indicators = {
            AgentState.IDLE: "[dim]●[/dim]",
            AgentState.RUNNING: "[yellow]●[/yellow]",
            AgentState.STREAMING: "[cyan]◉[/cyan]",
            AgentState.COMPLETED: "[green]✓[/green]",
            AgentState.FAILED: "[red]✗[/red]",
        }
        return indicators.get(state, "●")
