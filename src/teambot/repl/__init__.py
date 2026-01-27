"""REPL module for TeamBot interactive mode."""

from teambot.repl.commands import CommandResult, SystemCommands
from teambot.repl.parser import Command, CommandType, ParseError, PipelineStage, parse_command
from teambot.repl.router import AgentRouter, RouterError


# Lazy imports to avoid circular dependency with tasks module
def __getattr__(name):
    if name == "REPLLoop":
        from teambot.repl.loop import REPLLoop
        return REPLLoop
    elif name == "run_interactive_mode":
        from teambot.repl.loop import run_interactive_mode
        return run_interactive_mode
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Command",
    "CommandType",
    "parse_command",
    "ParseError",
    "PipelineStage",
    "AgentRouter",
    "RouterError",
    "SystemCommands",
    "CommandResult",
    "REPLLoop",
    "run_interactive_mode",
]
