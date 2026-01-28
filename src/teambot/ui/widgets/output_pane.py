"""Output pane widget for displaying agent responses."""

from datetime import datetime

from textual.widgets import RichLog


class OutputPane(RichLog):
    """Output pane for displaying agent responses with timestamps."""

    def write_command(self, command: str) -> None:
        """Write echoed command."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/dim] [bold]>[/bold] {command}")
        self.scroll_end()

    def write_task_complete(self, agent_id: str, result: str) -> None:
        """Write task completion message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/dim] [green]✓[/green] @{agent_id}: {result}")
        self.scroll_end()

    def write_task_error(self, agent_id: str, error: str) -> None:
        """Write task error message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/dim] [red]✗[/red] @{agent_id}: {error}")
        self.scroll_end()

    def write_info(self, message: str) -> None:
        """Write info message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/dim] [blue]ℹ[/blue] {message}")
        self.scroll_end()

    def write_system(self, output: str) -> None:
        """Write system command output."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/dim]\n{output}")
        self.scroll_end()
