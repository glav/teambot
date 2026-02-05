"""Shared formatting utilities for task output headers."""

from teambot.visualization.console import get_agent_style


def format_agent_header(agent_id: str, task_id: str) -> str:
    """Format a styled header for agent output.

    Args:
        agent_id: The agent identifier (e.g., 'pm', 'builder-1').
        task_id: The task identifier.

    Returns:
        Formatted header string with color markup, icon, and delimiter.
    """
    color, icon = get_agent_style(agent_id)
    content = f"{icon} @{agent_id} (task {task_id})"
    # Use heavy horizontal line (U+2501) as delimiter
    # Pad to ~50 chars total width for consistency
    padding_len = max(1, 50 - len(content) - 8)  # 8 = prefix "━━━ " + suffix " "
    padding = "━" * padding_len
    return f"[{color}]━━━ {content} {padding}[/{color}]"


def format_your_task_header() -> str:
    """Format the 'Your Task' section header.

    Returns:
        Formatted header string with distinct styling.
    """
    content = "🎯 Your Task"
    padding_len = max(1, 50 - len(content) - 8)
    padding = "━" * padding_len
    return f"[bold white]━━━ {content} {padding}[/bold white]"
