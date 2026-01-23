"""Persistent status overlay for TeamBot REPL.

Provides a fixed-position terminal overlay showing agent and task status.
"""

import asyncio
import os
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum

from rich.console import Console


class OverlayPosition(Enum):
    """Valid overlay positions."""

    TOP_RIGHT = "top-right"
    TOP_LEFT = "top-left"
    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-left"


# ANSI escape sequences
SAVE_CURSOR = "\033[s"
RESTORE_CURSOR = "\033[u"
MOVE_TO = "\033[{row};{col}H"
CLEAR_LINE = "\033[K"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

# Spinner frames (Braille pattern)
SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# Overlay dimensions
OVERLAY_WIDTH = 25
OVERLAY_HEIGHT = 3


@dataclass
class OverlayState:
    """State for the overlay display.

    Attributes:
        enabled: Whether overlay is visible.
        position: Position on screen.
        active_agents: List of currently active agent IDs.
        running_count: Number of running tasks.
        pending_count: Number of pending tasks.
        completed_count: Number of completed tasks.
        failed_count: Number of failed tasks.
        spinner_frame: Current spinner animation frame.
    """

    enabled: bool = True
    position: OverlayPosition = OverlayPosition.TOP_RIGHT
    active_agents: list[str] = field(default_factory=list)
    running_count: int = 0
    pending_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    spinner_frame: int = 0

    def is_idle(self) -> bool:
        """Check if no tasks are running."""
        return self.running_count == 0 and len(self.active_agents) == 0

    def total_tasks(self) -> int:
        """Get total task count."""
        return self.running_count + self.pending_count + self.completed_count + self.failed_count


class OverlayRenderer:
    """Renders persistent status overlay in terminal.

    Uses ANSI escape sequences to position overlay at fixed location
    that doesn't scroll with output.
    """

    def __init__(
        self,
        console: Console | None = None,
        position: OverlayPosition = OverlayPosition.TOP_RIGHT,
        enabled: bool = True,
    ):
        """Initialize overlay renderer.

        Args:
            console: Rich console for fallback output.
            position: Initial overlay position.
            enabled: Whether overlay starts enabled.
        """
        self._console = console or Console()
        self._state = OverlayState(enabled=enabled, position=position)
        self._spinner_task: asyncio.Task | None = None
        self._supported = self._check_terminal_support()

    def _check_terminal_support(self) -> bool:
        """Check if terminal supports ANSI positioning.

        Returns:
            True if terminal is capable.
        """
        # Check if we're in a real terminal
        if not sys.stdout.isatty():
            return False

        # Check terminal size
        try:
            width, height = shutil.get_terminal_size()
            if width < 30 or height < 10:
                return False
        except Exception:
            return False

        # Check for dumb terminal
        term = os.environ.get("TERM", "")
        if term in ("dumb", ""):
            return False

        return True

    @property
    def is_supported(self) -> bool:
        """Check if overlay is supported on this terminal."""
        return self._supported

    @property
    def is_enabled(self) -> bool:
        """Check if overlay is enabled."""
        return self._state.enabled and self._supported

    @property
    def state(self) -> OverlayState:
        """Get current overlay state."""
        return self._state

    def enable(self) -> None:
        """Enable the overlay."""
        self._state.enabled = True
        if self._supported:
            self.render()

    def disable(self) -> None:
        """Disable the overlay."""
        self._state.enabled = False
        self.clear()

    def set_position(self, position: OverlayPosition) -> None:
        """Set overlay position.

        Args:
            position: New position.
        """
        self._state.position = position
        if self.is_enabled:
            self.render()

    def _calculate_position(self) -> tuple[int, int]:
        """Calculate row, col for overlay based on position setting.

        Returns:
            Tuple of (row, col) for top-left of overlay.
        """
        width, height = shutil.get_terminal_size()

        positions = {
            OverlayPosition.TOP_RIGHT: (1, width - OVERLAY_WIDTH),
            OverlayPosition.TOP_LEFT: (1, 1),
            OverlayPosition.BOTTOM_RIGHT: (height - OVERLAY_HEIGHT - 1, width - OVERLAY_WIDTH),
            OverlayPosition.BOTTOM_LEFT: (height - OVERLAY_HEIGHT - 1, 1),
        }

        return positions.get(self._state.position, positions[OverlayPosition.TOP_RIGHT])

    def _build_content(self) -> list[str]:
        """Build overlay content lines.

        Returns:
            List of content lines (without borders).
        """
        lines = []

        # Line 1: Active agents with spinner or idle
        if self._state.is_idle():
            lines.append("✓ Idle")
        else:
            spinner = SPINNER_FRAMES[self._state.spinner_frame % len(SPINNER_FRAMES)]
            agents = ", ".join(f"@{a}" for a in self._state.active_agents[:3])
            if len(self._state.active_agents) > 3:
                agents += f" +{len(self._state.active_agents) - 3}"
            lines.append(f"{spinner} {agents}"[:OVERLAY_WIDTH - 4])

        # Line 2: Task counts
        running = self._state.running_count
        pending = self._state.pending_count
        completed = self._state.completed_count
        counts = f"{running}⏳ {pending}⏸ {completed}✓"
        if self._state.failed_count > 0:
            counts += f" {self._state.failed_count}✗"
        lines.append(f"Tasks: {counts}"[:OVERLAY_WIDTH - 4])

        return lines

    def _render_box(self, row: int, col: int, lines: list[str]) -> str:
        """Render content in a box at position.

        Args:
            row: Starting row.
            col: Starting column.
            lines: Content lines.

        Returns:
            ANSI string to render box.
        """
        output = []
        inner_width = OVERLAY_WIDTH - 2  # Account for borders

        # Top border
        output.append(MOVE_TO.format(row=row, col=col))
        output.append("┌" + "─" * inner_width + "┐")

        # Content lines
        for i, line in enumerate(lines):
            output.append(MOVE_TO.format(row=row + 1 + i, col=col))
            padded = line.ljust(inner_width)[:inner_width]
            output.append(f"│{padded}│")

        # Bottom border
        output.append(MOVE_TO.format(row=row + len(lines) + 1, col=col))
        output.append("└" + "─" * inner_width + "┘")

        return "".join(output)

    def render(self) -> None:
        """Render the overlay to terminal."""
        if not self.is_enabled:
            return

        row, col = self._calculate_position()
        lines = self._build_content()

        # Save cursor, render, restore cursor
        output = SAVE_CURSOR
        output += self._render_box(row, col, lines)
        output += RESTORE_CURSOR

        sys.stdout.write(output)
        sys.stdout.flush()

    def clear(self) -> None:
        """Clear the overlay from terminal."""
        if not self._supported:
            return

        row, col = self._calculate_position()

        output = SAVE_CURSOR
        for i in range(OVERLAY_HEIGHT + 1):
            output += MOVE_TO.format(row=row + i, col=col)
            output += " " * OVERLAY_WIDTH
        output += RESTORE_CURSOR

        sys.stdout.write(output)
        sys.stdout.flush()

    def update_state(
        self,
        active_agents: list[str] | None = None,
        running_count: int | None = None,
        pending_count: int | None = None,
        completed_count: int | None = None,
        failed_count: int | None = None,
    ) -> None:
        """Update overlay state and re-render.

        Args:
            active_agents: New list of active agents.
            running_count: New running count.
            pending_count: New pending count.
            completed_count: New completed count.
            failed_count: New failed count.
        """
        if active_agents is not None:
            self._state.active_agents = active_agents
        if running_count is not None:
            self._state.running_count = running_count
        if pending_count is not None:
            self._state.pending_count = pending_count
        if completed_count is not None:
            self._state.completed_count = completed_count
        if failed_count is not None:
            self._state.failed_count = failed_count

        if self.is_enabled:
            self.render()

    def advance_spinner(self) -> None:
        """Advance spinner to next frame and re-render."""
        self._state.spinner_frame = (self._state.spinner_frame + 1) % len(SPINNER_FRAMES)
        if self.is_enabled and not self._state.is_idle():
            self.render()

    async def start_spinner(self) -> None:
        """Start the spinner animation timer."""
        if self._spinner_task is not None:
            return

        async def spinner_loop():
            try:
                while True:
                    await asyncio.sleep(0.1)
                    if not self._state.is_idle():
                        self.advance_spinner()
            except asyncio.CancelledError:
                pass

        self._spinner_task = asyncio.create_task(spinner_loop())

    async def stop_spinner(self) -> None:
        """Stop the spinner animation timer."""
        if self._spinner_task is not None:
            self._spinner_task.cancel()
            try:
                await self._spinner_task
            except asyncio.CancelledError:
                pass
            self._spinner_task = None

    def print_with_overlay(self, *args, **kwargs) -> None:
        """Print while preserving overlay.

        Clears overlay, prints, then redraws overlay.
        """
        if self.is_enabled:
            self.clear()

        self._console.print(*args, **kwargs)

        if self.is_enabled:
            self.render()

    # Event handlers for TaskExecutor integration
    def on_task_started(self, task) -> None:
        """Handle task started event.

        Args:
            task: The started task.
        """
        if task.agent_id not in self._state.active_agents:
            self._state.active_agents.append(task.agent_id)
        self._state.running_count += 1
        if self._state.pending_count > 0:
            self._state.pending_count -= 1
        self.render()

    def on_task_completed(self, task, result) -> None:
        """Handle task completed event.

        Args:
            task: The completed task.
            result: Task result.
        """
        if task.agent_id in self._state.active_agents:
            self._state.active_agents.remove(task.agent_id)
        self._state.running_count = max(0, self._state.running_count - 1)

        if result.success:
            self._state.completed_count += 1
        else:
            self._state.failed_count += 1

        self.render()

    def on_task_pending(self, task) -> None:
        """Handle task added to pending queue.

        Args:
            task: The pending task.
        """
        self._state.pending_count += 1
        self.render()
