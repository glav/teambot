"""Token usage display functions using Rich library."""

from __future__ import annotations

from rich.panel import Panel

from teambot.tokens.models import TokenUsage


def render_token_summary(
    total: TokenUsage,
    by_agent: dict[str, TokenUsage],
    by_stage: dict[str, TokenUsage] | None = None,
) -> Panel:
    """Render token usage summary as Rich Panel.

    Args:
        total: Total aggregated usage.
        by_agent: Usage per agent.
        by_stage: Optional usage per workflow stage.

    Returns:
        Rich Panel ready for console.print().
    """
    if total.total_tokens is None:
        return Panel(
            "[yellow]Token Usage Summary: n/a (token data unavailable from Copilot)[/yellow]",
            title="📊 Token Usage",
        )

    lines = []

    # Total line
    total_str = f"[bold]Total Tokens:[/bold] {total.total_tokens:,}"
    if total.input_tokens is not None and total.output_tokens is not None:
        total_str += f" (prompt: {total.input_tokens:,} | completion: {total.output_tokens:,})"
    lines.append(total_str)
    lines.append("")

    # By agent breakdown
    if by_agent:
        lines.append("[bold]By Agent:[/bold]")
        max_tokens = max((u.total_tokens or 0) for u in by_agent.values()) or 1
        for agent_id, usage in sorted(by_agent.items(), key=lambda x: -(x[1].total_tokens or 0)):
            tokens = usage.total_tokens or 0
            bar_width = int((tokens / max_tokens) * 10)
            bar = "█" * bar_width + "░" * (10 - bar_width)
            pct = (tokens / (total.total_tokens or 1)) * 100
            lines.append(f"  {agent_id:12} │ {bar} │ {tokens:>8,} ({pct:.1f}%)")

    # By stage breakdown (if provided)
    if by_stage:
        lines.append("")
        lines.append("[bold]By Stage:[/bold]")
        for stage_name, usage in by_stage.items():
            tokens = usage.total_tokens or 0
            lines.append(f"  {stage_name:20} │ {tokens:>8,}")

    return Panel("\n".join(lines), title="📊 Token Usage Summary")


def render_session_summary(total: TokenUsage) -> str:
    """Render brief session summary line.

    Args:
        total: Session total usage.

    Returns:
        Formatted string for console output.
    """
    if total.total_tokens is None:
        return "Session Token Usage: n/a"

    result = f"Session Token Usage: {total.total_tokens:,} tokens"
    if total.input_tokens is not None and total.output_tokens is not None:
        result += f" (prompt: {total.input_tokens:,} | completion: {total.output_tokens:,})"
    return result
