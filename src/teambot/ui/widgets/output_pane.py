"""Output pane widget for displaying agent responses."""

from datetime import datetime
from typing import Optional

from textual.widgets import RichLog


class OutputPane(RichLog):
    """Output pane for displaying agent responses with timestamps."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track streaming state per agent: {agent_id: accumulated_chunks}
        self._streaming_buffers: dict[str, list[str]] = {}
        # Track start timestamps for streaming sessions
        self._streaming_starts: dict[str, str] = {}

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

    def write_streaming_start(self, agent_id: str) -> None:
        """Start a streaming output for an agent.

        Args:
            agent_id: The agent that started streaming.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._streaming_buffers[agent_id] = []
        self._streaming_starts[agent_id] = timestamp
        # Write initial streaming indicator (note: RichLog doesn't support 'end=' so this is a full line)
        self.write(f"[dim]{timestamp}[/dim] [yellow]⟳[/yellow] @{agent_id}: [dim]streaming...[/dim]")
        self.scroll_end()

    def write_streaming_chunk(self, agent_id: str, chunk: str) -> None:
        """Append a streaming chunk to the current agent output.

        If streaming hasn't started for this agent, starts it automatically.

        Args:
            agent_id: The agent sending the chunk.
            chunk: The content chunk to append.
        """
        if agent_id not in self._streaming_buffers:
            self.write_streaming_start(agent_id)

        # Accumulate chunk
        self._streaming_buffers[agent_id].append(chunk)

        # Append chunk to current line (RichLog doesn't have direct append,
        # so we rewrite the full accumulated content)
        self._update_streaming_line(agent_id)

    def _update_streaming_line(self, agent_id: str) -> None:
        """Update the streaming line with accumulated content."""
        # For now, just scroll to end - the full line rewrite is complex in RichLog
        # The chunks are accumulated and shown on finish
        self.scroll_end()

    def finish_streaming(self, agent_id: str, success: bool = True) -> None:
        """Mark streaming complete for an agent.

        Args:
            agent_id: The agent that finished streaming.
            success: Whether the streaming completed successfully.
        """
        if agent_id not in self._streaming_buffers:
            return

        # Get accumulated content
        content = "".join(self._streaming_buffers[agent_id])
        timestamp = self._streaming_starts.get(agent_id, datetime.now().strftime("%H:%M:%S"))

        # Clean up state
        del self._streaming_buffers[agent_id]
        if agent_id in self._streaming_starts:
            del self._streaming_starts[agent_id]

        # Write final complete line
        if success:
            self.write(f"[dim]{timestamp}[/dim] [green]✓[/green] @{agent_id}: {content}")
        else:
            self.write(f"[dim]{timestamp}[/dim] [red]✗[/red] @{agent_id}: {content}")

        self.scroll_end()

    def is_streaming(self, agent_id: Optional[str] = None) -> bool:
        """Check if an agent (or any agent) is currently streaming.

        Args:
            agent_id: Specific agent to check, or None for any agent.

        Returns:
            True if streaming is active.
        """
        if agent_id:
            return agent_id in self._streaming_buffers
        return len(self._streaming_buffers) > 0

    def get_streaming_agents(self) -> list[str]:
        """Get list of agents currently streaming.

        Returns:
            List of agent IDs with active streams.
        """
        return list(self._streaming_buffers.keys())
