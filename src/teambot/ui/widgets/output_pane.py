"""Output pane widget for displaying agent responses."""

from datetime import datetime

from textual.widgets import RichLog


class OutputPane(RichLog):
    """Output pane for displaying agent responses with timestamps."""

    def __init__(self, *args, **kwargs):
        # Enable word wrap to prevent horizontal scrolling
        kwargs.setdefault("wrap", True)
        super().__init__(*args, **kwargs)
        # Track streaming state per agent: {agent_id: accumulated_chunks}
        self._streaming_buffers: dict[str, list[str]] = {}
        # Track start timestamps for streaming sessions
        self._streaming_starts: dict[str, str] = {}
        # Track last agent for handoff detection
        self._last_agent_id: str | None = None
        # Track incomplete line per agent during streaming
        self._streaming_line_buffers: dict[str, str] = {}
        # Track indent stack for nested handoffs (e.g., pm -> ba shows [pm, ba])
        self._indent_stack: list[str] = []
        # Track if any output has been written (for blank line separation)
        self._has_output: bool = False

    def write_command(self, command: str) -> None:
        """Write echoed command.

        Adds a blank line before the command if there was previous output,
        to visually separate command blocks.
        """
        # Add blank line separator if there was previous output
        if self._has_output:
            self.write("")

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/dim] [bold]>[/bold] {command}")
        self.scroll_end()
        # Reset indent stack for new command
        self._indent_stack = []
        # Mark that we have output
        self._has_output = True

    def _check_handoff(self, agent_id: str) -> bool:
        """Check if this is a handoff from another agent.

        Args:
            agent_id: The current agent identifier.

        Returns:
            True if previous agent was different (and not None).
        """
        if self._last_agent_id and self._last_agent_id != agent_id:
            return True
        return False

    def _get_indent_agents(self, agent_id: str) -> list[str]:
        """Get the list of agents for nested indentation.

        Args:
            agent_id: Current agent identifier.

        Returns:
            List of agent IDs representing the indent stack.
        """
        if not self._indent_stack or self._indent_stack[-1] != agent_id:
            # Return current stack plus this agent
            return self._indent_stack + [agent_id]
        return self._indent_stack

    def _write_handoff_separator(self, from_agent: str, to_agent: str) -> None:
        """Write a visual separator for agent handoff.

        Args:
            from_agent: The agent that was previously active.
            to_agent: The agent that is now active.
        """
        from teambot.visualization.console import format_indented_line, get_agent_style

        to_color, to_icon = get_agent_style(to_agent)
        separator_line = f"[dim]{'─' * 40}[/dim]"
        label = f"[{to_color}]→ {to_icon} @{to_agent}[/{to_color}]"

        # Add to_agent to indent stack for nested display
        if to_agent not in self._indent_stack:
            self._indent_stack.append(to_agent)

        # Write separator with current indent stack (excluding new agent)
        if len(self._indent_stack) > 1:
            # Use parent agents for indent on separator
            parent_stack = self._indent_stack[:-1]
            indented = format_indented_line(f"{separator_line} {label}", parent_stack)
            self.write(indented)
        else:
            self.write(f"{separator_line} {label}")

    def write_task_complete(self, agent_id: str, result: str) -> None:
        """Write task completion message with persona styling."""
        from teambot.visualization.console import format_indented_content, get_agent_style

        timestamp = datetime.now().strftime("%H:%M:%S")
        color, icon = get_agent_style(agent_id)

        # Check for handoff
        if self._check_handoff(agent_id):
            self._write_handoff_separator(self._last_agent_id, agent_id)
        else:
            # First agent in chain - initialize indent stack
            if not self._indent_stack:
                self._indent_stack = [agent_id]
        self._last_agent_id = agent_id

        # Format header with persona color
        self.write(
            f"[dim]{timestamp}[/dim] [green]✓[/green] [{color}]{icon} @{agent_id}[/{color}]:"
        )
        # Format content with colored indent (using full stack for nesting)
        if result.strip():
            indent_agents = self._get_indent_agents(agent_id)
            indented = format_indented_content(result, indent_agents)
            self.write(indented)
        self.scroll_end()

    def write_task_error(self, agent_id: str, error: str) -> None:
        """Write task error message with persona styling."""
        from teambot.visualization.console import format_indented_content, get_agent_style

        timestamp = datetime.now().strftime("%H:%M:%S")
        color, icon = get_agent_style(agent_id)

        # Check for handoff
        if self._check_handoff(agent_id):
            self._write_handoff_separator(self._last_agent_id, agent_id)
        else:
            # First agent in chain - initialize indent stack
            if not self._indent_stack:
                self._indent_stack = [agent_id]
        self._last_agent_id = agent_id

        # Format header with persona color
        self.write(f"[dim]{timestamp}[/dim] [red]✗[/red] [{color}]{icon} @{agent_id}[/{color}]:")
        # Format error content with colored indent (using full stack for nesting)
        if error.strip():
            indent_agents = self._get_indent_agents(agent_id)
            indented = format_indented_content(error, indent_agents)
            self.write(indented)
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
        """Start a streaming output for an agent with persona styling.

        Args:
            agent_id: The agent that started streaming.
        """
        from teambot.visualization.console import get_agent_style

        timestamp = datetime.now().strftime("%H:%M:%S")
        color, icon = get_agent_style(agent_id)

        # Check for handoff
        if self._check_handoff(agent_id):
            self._write_handoff_separator(self._last_agent_id, agent_id)
        else:
            # First agent in chain - initialize indent stack
            if not self._indent_stack:
                self._indent_stack = [agent_id]
        self._last_agent_id = agent_id

        self._streaming_buffers[agent_id] = []
        self._streaming_starts[agent_id] = timestamp

        # Write initial streaming indicator with persona styling
        self.write(
            f"[dim]{timestamp}[/dim] [{color}]⟳ {icon} @{agent_id}[/{color}]: "
            f"[dim]streaming...[/dim]"
        )
        self.scroll_end()

    def write_streaming_chunk(self, agent_id: str, chunk: str) -> None:
        """Append a streaming chunk to the current agent output.

        If streaming hasn't started for this agent, starts it automatically.
        Handles partial lines at chunk boundaries by buffering incomplete lines.
        Detects agent transitions and inserts visual handoff separators.

        Args:
            agent_id: The agent sending the chunk.
            chunk: The content chunk to append.
        """
        from teambot.visualization.console import format_indented_line

        if agent_id not in self._streaming_buffers:
            self.write_streaming_start(agent_id)
            self._streaming_line_buffers[agent_id] = ""

        # Check for handoff - agent transition during streaming
        if self._check_handoff(agent_id):
            # Flush any pending incomplete line from previous agent
            prev_agent = self._last_agent_id
            if prev_agent and prev_agent in self._streaming_line_buffers:
                pending = self._streaming_line_buffers[prev_agent]
                if pending.strip():
                    # Use previous agent's indent stack
                    prev_indent = self._get_indent_agents(prev_agent)
                    indented = format_indented_line(pending, prev_indent)
                    self.write(indented)
                    self._streaming_line_buffers[prev_agent] = ""
            self._write_handoff_separator(self._last_agent_id, agent_id)
        self._last_agent_id = agent_id

        # Accumulate chunk for final display
        self._streaming_buffers[agent_id].append(chunk)

        # Handle line buffering for real-time indent
        buffer = self._streaming_line_buffers.get(agent_id, "") + chunk

        # Get indent agents for this agent (includes nesting)
        indent_agents = self._get_indent_agents(agent_id)

        if "\n" in buffer:
            lines = buffer.split("\n")
            complete_lines = lines[:-1]  # All except last
            remainder = lines[-1]  # May be partial

            # Write complete lines with nested indent
            for line in complete_lines:
                indented = format_indented_line(line, indent_agents)
                self.write(indented)

            # Store remainder for next chunk
            self._streaming_line_buffers[agent_id] = remainder
        else:
            # No newline yet, just buffer
            self._streaming_line_buffers[agent_id] = buffer

        self.scroll_end()

    def _update_streaming_line(self, agent_id: str) -> None:
        """Update the streaming line with accumulated content.

        Note: This method is kept for backwards compatibility but real-time
        indent handling is now done in write_streaming_chunk().
        """
        self.scroll_end()

    def finish_streaming(self, agent_id: str, success: bool = True) -> None:
        """Mark streaming complete for an agent with persona styling.

        Args:
            agent_id: The agent that finished streaming.
            success: Whether the streaming completed successfully.
        """
        from teambot.visualization.console import format_indented_line, get_agent_style

        if agent_id not in self._streaming_buffers:
            return

        # Get any remaining buffered line content (incomplete last line)
        remaining_line = ""
        if agent_id in self._streaming_line_buffers and self._streaming_line_buffers[agent_id]:
            remaining_line = self._streaming_line_buffers[agent_id]

        timestamp = self._streaming_starts.get(agent_id, datetime.now().strftime("%H:%M:%S"))

        # Clean up state
        del self._streaming_buffers[agent_id]
        if agent_id in self._streaming_starts:
            del self._streaming_starts[agent_id]
        if agent_id in self._streaming_line_buffers:
            del self._streaming_line_buffers[agent_id]

        color, icon = get_agent_style(agent_id)

        # Check for handoff (streaming may have interleaved)
        if self._check_handoff(agent_id):
            self._write_handoff_separator(self._last_agent_id, agent_id)
        self._last_agent_id = agent_id

        # Write any remaining incomplete line with nested indent
        if remaining_line.strip():
            indent_agents = self._get_indent_agents(agent_id)
            indented = format_indented_line(remaining_line, indent_agents)
            self.write(indented)

        # Write completion status
        status_icon = "[green]✓[/green]" if success else "[red]✗[/red]"
        self.write(
            f"[dim]{timestamp}[/dim] {status_icon} "
            f"[{color}]{icon} @{agent_id} streaming complete[/{color}]"
        )

        self.scroll_end()

    def is_streaming(self, agent_id: str | None = None) -> bool:
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
