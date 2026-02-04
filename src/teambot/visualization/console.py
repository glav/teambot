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


# Color mapping for personas
PERSONA_COLORS = {
    "project_manager": "blue",
    "business_analyst": "cyan",
    "technical_writer": "green",
    "builder": "yellow",
    "reviewer": "magenta",
}


class ConsoleDisplay:
    """Rich-based console display for agent status."""

    def __init__(self):
        self.console = Console()
        self.agents: dict[str, dict[str, Any]] = {}
        self._live: Live | None = None

    def add_agent(
        self, agent_id: str, persona: str, display_name: str | None = None,
        model: str | None = None
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
