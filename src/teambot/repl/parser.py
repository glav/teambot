"""Command parser for TeamBot REPL.

Parses user input into structured Command objects for routing.
Supports:
- @agent commands: @pm, @builder-1, etc.
- System commands: /help, /status, /history, /quit
- Raw input: anything else
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class CommandType(Enum):
    """Types of commands in the REPL."""

    AGENT = auto()  # @agent commands
    SYSTEM = auto()  # /command system commands
    RAW = auto()  # Plain text input


class ParseError(Exception):
    """Error raised when parsing fails."""

    pass


@dataclass
class Command:
    """Parsed command from user input.

    Attributes:
        type: The type of command.
        agent_id: For AGENT type, the agent identifier.
        content: For AGENT/RAW type, the content/task.
        command: For SYSTEM type, the command name.
        args: For SYSTEM type, command arguments.
    """

    type: CommandType
    agent_id: Optional[str] = None
    content: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None


# Pattern for agent commands: @agent-id task
AGENT_PATTERN = re.compile(r"^@([a-zA-Z][a-zA-Z0-9-]*)\s*(.*)", re.DOTALL)

# Pattern for system commands: /command args
SYSTEM_PATTERN = re.compile(r"^/([a-zA-Z][a-zA-Z0-9-]*)\s*(.*)", re.DOTALL)


def parse_command(input_text: str) -> Command:
    """Parse user input into a Command object.

    Args:
        input_text: Raw user input string.

    Returns:
        Parsed Command object.

    Raises:
        ParseError: If command syntax is invalid.
    """
    # Try agent command (@agent task)
    agent_match = AGENT_PATTERN.match(input_text)
    if agent_match:
        agent_id = agent_match.group(1)
        content = agent_match.group(2).strip() if agent_match.group(2) else ""

        if not content:
            raise ParseError(f"Agent command requires task: @{agent_id} <task required>")

        # Preserve internal spacing in content but strip leading space
        content = agent_match.group(2)
        if content.startswith(" "):
            content = content[1:]  # Remove exactly one leading space

        if not content.strip():
            raise ParseError(f"Agent command requires task: @{agent_id} <task required>")

        return Command(type=CommandType.AGENT, agent_id=agent_id, content=content)

    # Try system command (/command args)
    system_match = SYSTEM_PATTERN.match(input_text)
    if system_match:
        command = system_match.group(1)
        args_str = system_match.group(2).strip()
        args = args_str.split() if args_str else []

        return Command(type=CommandType.SYSTEM, command=command, args=args)

    # Default to raw input
    return Command(type=CommandType.RAW, content=input_text)
