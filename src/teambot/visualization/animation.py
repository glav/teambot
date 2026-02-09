"""Startup animation for TeamBot CLI."""

from __future__ import annotations

import os
import shutil
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from teambot.visualization.console import AGENT_COLORS

# Ordered agent list for consistent color cycling
AGENT_ORDER = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]

# Color map for logo letter sections: (start_col, end_col, agent_id)
# Columns are 0-indexed within each logo line
LOGO_COLOR_MAP = [
    (0, 9, "pm"),  # T → blue
    (9, 18, "ba"),  # E → cyan
    (18, 25, "writer"),  # A → magenta
    (25, 39, "builder-1"),  # M → green
    (39, 48, "builder-2"),  # B → yellow
    (48, 57, "reviewer"),  # O → red
    (57, 66, "pm"),  # T → blue (cyclical)
]

# Unicode box-drawing wordmark (~6 lines, ≤65 cols)
TEAMBOT_LOGO = [
    " ████████╗███████╗ █████╗ ███╗   ███╗██████╗  ██████╗ ████████╗",
    " ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██╔══██╗██╔═══██╗╚══██╔══╝",
    "    ██║   █████╗  ███████║██╔████╔██║██████╔╝██║   ██║   ██║   ",
    "    ██║   ██╔══╝  ██╔══██║██║╚██╔╝██║██╔══██╗██║   ██║   ██║   ",
    "    ██║   ███████╗██║  ██║██║ ╚═╝ ██║██████╔╝╚██████╔╝   ██║   ",
    "    ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═════╝  ╚═════╝    ╚═╝   ",
]

# Pure ASCII fallback wordmark (~4 lines)
TEAMBOT_LOGO_ASCII = [
    " _____ ___   _   __  __ ___  ___ _____",
    "|_   _| __| /_\\ |  \\/  | _ )/ _ \\_   _|",
    "  | | | _| / _ \\| |\\/| | _ \\ (_) || |  ",
    "  |_| |___/_/ \\_\\_|  |_|___/\\___/ |_|  ",
]

# ASCII logo color map (narrower columns)
LOGO_ASCII_COLOR_MAP = [
    (0, 6, "pm"),  # T
    (6, 10, "ba"),  # E
    (10, 15, "writer"),  # A
    (15, 22, "builder-1"),  # M
    (22, 27, "builder-2"),  # B
    (27, 32, "reviewer"),  # O
    (32, 38, "pm"),  # T
]


class StartupAnimation:
    """Branded startup animation for TeamBot CLI.

    Renders a team assembly animation where agent-colored elements
    converge to form the TeamBot wordmark, using Rich for rendering.
    """

    def __init__(self, console: Console, version: str = "0.1.0") -> None:
        self.console = console
        self.version = version

    def should_animate(self, config: dict | None = None, no_animation_flag: bool = False) -> bool:
        """Determine whether the animated sequence should play.

        Returns True only if all conditions for animation are met.
        """
        if no_animation_flag:
            return False
        if config is not None and not config.get("show_startup_animation", True):
            return False
        if os.environ.get("TEAMBOT_NO_ANIMATION"):
            return False
        if not sys.stdout.isatty():
            return False
        if os.environ.get("TERM", "") == "dumb":
            return False
        try:
            cols, rows = shutil.get_terminal_size()
            if cols < 60 or rows < 10:
                return False
        except (ValueError, OSError):
            return False
        return True

    def _is_explicitly_disabled(
        self, config: dict | None = None, no_animation_flag: bool = False
    ) -> bool:
        """Check if animation is explicitly disabled by user preference."""
        if no_animation_flag:
            return True
        if config is not None and not config.get("show_startup_animation", True):
            return True
        if os.environ.get("TEAMBOT_NO_ANIMATION"):
            return True
        return False

    def _supports_animation(self) -> bool:
        """Check if terminal environment supports animation."""
        if not sys.stdout.isatty():
            return False
        if os.environ.get("TERM", "") == "dumb":
            return False
        try:
            cols, rows = shutil.get_terminal_size()
            if cols < 60 or rows < 10:
                return False
        except (ValueError, OSError):
            return False
        return True

    def _supports_unicode(self) -> bool:
        """Check if console supports Unicode output."""
        encoding = getattr(self.console, "encoding", "utf-8") or "utf-8"
        return encoding.lower().replace("-", "") in ("utf8",)

    def _colorize_logo_line(self, line: str, color_map: list[tuple[int, int, str]]) -> Text:
        """Apply agent colors to a single logo line."""
        text = Text()
        if self.console.color_system is None:
            text.append(line)
            return text

        last_end = 0
        for start, end, agent_id in color_map:
            if last_end < start:
                text.append(line[last_end:start])
            color = AGENT_COLORS.get(agent_id, "white")
            segment = line[start:end] if end <= len(line) else line[start:]
            text.append(segment, style=f"bold {color}")
            last_end = end
        if last_end < len(line):
            text.append(line[last_end:])
        return text

    def _final_banner(self) -> Panel:
        """Build the persistent final banner with colored TeamBot wordmark."""
        width = self.console.size.width if self.console.size else 80

        # Compact banner for narrow terminals
        if width < 60:
            return Panel(
                f"[bold blue]TeamBot[/bold blue] v{self.version}",
                style="bold blue",
            )

        # Choose logo variant
        if self._supports_unicode():
            logo_lines = TEAMBOT_LOGO
            color_map = LOGO_COLOR_MAP
        else:
            logo_lines = TEAMBOT_LOGO_ASCII
            color_map = LOGO_ASCII_COLOR_MAP

        # Build colored logo
        parts: list[Text | str] = []
        for i, line in enumerate(logo_lines):
            colored_line = self._colorize_logo_line(line, color_map)
            parts.append(colored_line)
            if i < len(logo_lines) - 1:
                parts.append(Text("\n"))

        # Compose full banner
        result = Text()
        for part in parts:
            if isinstance(part, str):
                result.append(part)
            else:
                result.append_text(part)

        # Add tagline
        tagline = Text(f"\n\n  v{self.version} — AI agents working together")
        tagline.stylize("dim")
        result.append_text(tagline)

        return Panel(result, style="bold blue", padding=(1, 2))

    def _show_static_banner(self) -> None:
        """Display the static (non-animated) banner."""
        self.console.print(self._final_banner())

    def _generate_convergence_frames(self) -> list[tuple[Text, float]]:
        """Generate frames showing agent dots converging to center.

        Returns list of (renderable, delay_seconds) tuples.
        """
        num_frames = 20
        grid_width = 50
        grid_height = 7
        center_x = grid_width // 2
        center_y = grid_height // 2

        # Starting positions for 6 agents (scattered around edges)
        start_positions = [
            (2, 0),  # pm: top-left
            (grid_width - 3, 0),  # ba: top-right
            (0, center_y),  # writer: mid-left
            (grid_width - 1, center_y),  # builder-1: mid-right
            (5, grid_height - 1),  # builder-2: bottom-left
            (grid_width - 6, grid_height - 1),  # reviewer: bottom-right
        ]

        frames = []
        for frame_idx in range(num_frames):
            t = frame_idx / max(num_frames - 1, 1)
            # Ease-out deceleration
            t_eased = t * (2 - t)

            grid = [[" " for _ in range(grid_width)] for _ in range(grid_height)]
            text = Text()

            for agent_idx, agent_id in enumerate(AGENT_ORDER):
                sx, sy = start_positions[agent_idx]
                # Interpolate position
                x = int(sx + (center_x - sx) * t_eased)
                y = int(sy + (center_y - sy) * t_eased)
                x = max(0, min(grid_width - 1, x))
                y = max(0, min(grid_height - 1, y))
                grid[y][x] = agent_id

            for row_idx, row in enumerate(grid):
                for _col_idx, cell in enumerate(row):
                    if cell != " ":
                        color = AGENT_COLORS.get(cell, "white")
                        text.append("●", style=f"bold {color}")
                    else:
                        text.append(" ")
                if row_idx < grid_height - 1:
                    text.append("\n")

            frames.append((text, 0.1))

        return frames

    def _generate_logo_frames(self) -> list[tuple[Text, float]]:
        """Generate frames progressively revealing the logo left-to-right.

        Returns list of (renderable, delay_seconds) tuples.
        """
        if self._supports_unicode():
            logo_lines = TEAMBOT_LOGO
            color_map = LOGO_COLOR_MAP
        else:
            logo_lines = TEAMBOT_LOGO_ASCII
            color_map = LOGO_ASCII_COLOR_MAP

        max_width = max(len(line) for line in logo_lines)
        num_frames = 10
        frames = []

        for frame_idx in range(num_frames):
            reveal_cols = int((frame_idx + 1) / num_frames * max_width)
            text = Text()

            for row_idx, line in enumerate(logo_lines):
                visible = line[:reveal_cols]
                colored = self._colorize_logo_line(visible.ljust(max_width), color_map)
                # Trim trailing spaces from the colorized line
                text.append_text(colored)
                if row_idx < len(logo_lines) - 1:
                    text.append("\n")

            frames.append((text, 0.1))

        return frames

    def _play_animated(self) -> None:
        """Render the full animated startup sequence using Rich Live."""
        try:
            from rich.live import Live

            convergence = self._generate_convergence_frames()
            logo = self._generate_logo_frames()
            all_frames = convergence + logo

            with Live(
                console=self.console,
                transient=True,
                refresh_per_second=15,
            ) as live:
                for renderable, delay in all_frames:
                    live.update(renderable)
                    time.sleep(delay)

            # Print persistent final banner
            self.console.print(self._final_banner())
        except Exception:
            # Any rendering error falls back to static banner
            self._show_static_banner()

    def play(self, config: dict | None = None, no_animation_flag: bool = False) -> None:
        """Play the startup animation with three-way dispatch.

        1. Explicitly disabled (flag/config/env) → static banner (instant)
        2. Environment limitations (non-TTY/dumb/narrow) → static banner
        3. All checks pass → animated sequence
        """
        if self._is_explicitly_disabled(config, no_animation_flag):
            self._show_static_banner()
            return

        if not self._supports_animation():
            self._show_static_banner()
            return

        self._play_animated()


def play_startup_animation(
    console: Console,
    config: dict | None = None,
    no_animation_flag: bool = False,
    version: str = "0.1.0",
) -> None:
    """Convenience function to play the startup animation.

    Args:
        console: Rich Console instance for output.
        config: TeamBot configuration dict (may be None).
        no_animation_flag: True if --no-animation CLI flag was passed.
        version: TeamBot version string to display.
    """
    animation = StartupAnimation(console, version)
    animation.play(config, no_animation_flag)
