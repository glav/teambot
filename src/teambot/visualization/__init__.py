"""Visualization package for console output."""

from teambot.visualization.animation import StartupAnimation, play_startup_animation
from teambot.visualization.console import PERSONA_COLORS, AgentStatus, ConsoleDisplay

__all__ = [
    "ConsoleDisplay",
    "AgentStatus",
    "PERSONA_COLORS",
    "StartupAnimation",
    "play_startup_animation",
]
