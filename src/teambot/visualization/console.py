"""Console visualization using Rich library."""

from __future__ import annotations

from enum import Enum
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table


class AgentStatus(Enum):
    """Status of an agent."""

    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


# Color mapping for personas (legacy - used by ConsoleDisplay.render_table)
PERSONA_COLORS = {
    "project_manager": "blue",
    "business_analyst": "cyan",
    "technical_writer": "magenta",
    "builder_primary": "green",
    "builder_secondary": "yellow",
    "reviewer": "red",
}

# Agent ID to persona mapping
AGENT_PERSONAS = {
    "pm": "project_manager",
    "ba": "business_analyst",
    "writer": "technical_writer",
    "builder-1": "builder_primary",
    "builder-2": "builder_secondary",
    "reviewer": "reviewer",
}

# Direct agent ID to color mapping (preferred for output formatting)
AGENT_COLORS = {
    "pm": "blue",
    "ba": "cyan",
    "writer": "magenta",
    "builder-1": "green",
    "builder-2": "yellow",
    "reviewer": "red",
}

# Indent characters for output formatting
INDENT_CHAR = "│"  # U+2502 Box Drawings Light Vertical
INDENT_CHAR_ASCII = "|"


def get_agent_color(agent_id: str) -> str:
    """Get color for agent's indent bar.

    Args:
        agent_id: The agent identifier (e.g., 'pm', 'builder-1').

    Returns:
        Color name for the agent.
    """
    return AGENT_COLORS.get(agent_id, "white")


def _should_use_ascii() -> bool:
    """Check if ASCII fallback should be used for indent chars.

    Returns:
        True if ASCII fallback should be used.
    """
    import os

    return os.environ.get("TEAMBOT_ASCII_INDENT", "").lower() in ("1", "true", "yes")


def format_indented_line(
    line: str,
    agent_id: str | list[str],
    use_ascii: bool | None = None,
) -> str:
    """Apply colored indent prefix to a single line.

    Args:
        line: Single line of text.
        agent_id: Agent identifier for color lookup, or list of agent IDs
            for nested indentation (e.g., ["pm", "ba"] for pm -> ba handoff).
        use_ascii: Use ASCII pipe instead of Unicode. Auto-detected if None.

    Returns:
        Line with colored indent prefix(es).
    """
    if use_ascii is None:
        use_ascii = _should_use_ascii()

    char = INDENT_CHAR_ASCII if use_ascii else INDENT_CHAR

    # Handle list of agents for nested indentation
    if isinstance(agent_id, list):
        prefix_parts = []
        for aid in agent_id:
            color = get_agent_color(aid)
            prefix_parts.append(f"[{color}]{char}[/{color}]")
        prefix = " ".join(prefix_parts)
        return f"{prefix} {line}"
    else:
        color = get_agent_color(agent_id)
        return f"[{color}]{char}[/{color}] {line}"


def format_indented_content(
    content: str,
    agent_id: str | list[str],
    use_ascii: bool | None = None,
) -> str:
    """Apply colored indent prefix to each line of content.

    Detects agent headers (━━━ @agent_id) in the content and switches
    the indent color accordingly. This supports pipeline outputs where
    multiple agents' outputs are combined.

    Args:
        content: Multi-line text content.
        agent_id: Agent identifier for color lookup, or list of agent IDs
            for nested indentation.
        use_ascii: Use ASCII pipe instead of Unicode. Auto-detected if None.

    Returns:
        Content with colored indent prefix on each line.
    """
    import re

    if use_ascii is None:
        use_ascii = _should_use_ascii()

    lines = content.split("\n")
    result_lines = []

    # Track current agent(s) for indentation
    # Start with the provided agent_id (could be str or list)
    if isinstance(agent_id, list):
        current_agents = agent_id.copy()
    else:
        current_agents = [agent_id]

    # Pattern to detect agent headers: ━━━ 📊 @ba or ━━━ @pm etc.
    header_pattern = re.compile(r"━━━.*@([\w-]+)")

    for line in lines:
        # Check if this line is an agent header
        match = header_pattern.search(line)
        if match:
            new_agent = match.group(1)
            # Update current agents to include the new agent (nested)
            if new_agent not in current_agents:
                current_agents.append(new_agent)

        # Apply indentation with current agent stack
        result_lines.append(format_indented_line(line, current_agents, use_ascii))

    return "\n".join(result_lines)


# Agent-specific icons for visual identification
AGENT_ICONS = {
    "pm": "📋",
    "ba": "📊",
    "writer": "📝",
    "builder-1": "🔨",
    "builder-2": "🔨",
    "reviewer": "🔍",
}


def get_agent_style(agent_id: str) -> tuple[str, str]:
    """Get color and icon for an agent.

    Args:
        agent_id: The agent identifier (e.g., 'pm', 'builder-1').

    Returns:
        Tuple of (color, icon) for the agent.

    Example:
        >>> color, icon = get_agent_style("pm")
        >>> color
        'blue'
        >>> icon
        '📋'
    """
    persona = AGENT_PERSONAS.get(agent_id)
    if persona:
        color = PERSONA_COLORS.get(persona, "white")
    else:
        color = "white"
    icon = AGENT_ICONS.get(agent_id, "●")
    return color, icon


class ConsoleDisplay:
    """Rich-based console display for agent status."""

    def __init__(self):
        self.console = Console()
        self.agents: dict[str, dict[str, Any]] = {}
        self._live: Live | None = None

    def add_agent(
        self, agent_id: str, persona: str, display_name: str | None = None, model: str | None = None
    ) -> None:
        """Register an agent for display."""
        self.agents[agent_id] = {
            "persona": persona,
            "display_name": display_name or agent_id,
            "status": AgentStatus.IDLE,
            "current_task": None,
            "progress": 0,
            "message": "",
            "model": model,
        }

    def update_status(
        self,
        agent_id: str,
        status: AgentStatus,
        task: str | None = None,
        message: str | None = None,
        progress: int | None = None,
    ) -> None:
        """Update an agent's status."""
        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]
        agent["status"] = status
        if task is not None:
            agent["current_task"] = task
        if message is not None:
            agent["message"] = message
        if progress is not None:
            agent["progress"] = min(100, max(0, progress))

    def get_status(self, agent_id: str) -> AgentStatus | None:
        """Get current status of an agent."""
        if agent_id in self.agents:
            return self.agents[agent_id]["status"]
        return None

    def render_table(self) -> Table:
        """Render agents as a Rich table."""
        table = Table(title="TeamBot Agents", show_header=True)
        table.add_column("Agent", style="bold")
        table.add_column("Persona")
        table.add_column("Model", style="dim italic")

        for _agent_id, info in self.agents.items():
            color = PERSONA_COLORS.get(info["persona"], "white")
            model_display = info.get("model") or "-"

            table.add_row(
                f"[{color}]{info['display_name']}[/]",
                info["persona"],
                model_display,
            )

        return table

    def _make_progress_bar(self, progress: int) -> str:
        """Create a simple text progress bar."""
        filled = progress // 10
        empty = 10 - filled
        return f"[green]{'█' * filled}[/][dim]{'░' * empty}[/] {progress}%"

    def print_status(self) -> None:
        """Print current status table to console."""
        self.console.print(self.render_table())

    def print_message(self, agent_id: str, message: str, level: str = "info") -> None:
        """Print a message from an agent."""
        if agent_id in self.agents:
            info = self.agents[agent_id]
            color = PERSONA_COLORS.get(info["persona"], "white")
            level_color = {"info": "white", "warning": "yellow", "error": "red"}.get(level, "white")
            self.console.print(f"[{color}][{info['display_name']}][/] [{level_color}]{message}[/]")

    def print_header(self, title: str) -> None:
        """Print a styled header."""
        self.console.print(Panel(title, style="bold blue"))

    def print_success(self, message: str) -> None:
        """Print a success message."""
        self.console.print(f"[bold green]✓[/] {message}")

    def print_error(self, message: str) -> None:
        """Print an error message."""
        self.console.print(f"[bold red]✗[/] {message}")

    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        self.console.print(f"[bold yellow]![/] {message}")
