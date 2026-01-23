"""Command parser for TeamBot REPL.

Parses user input into structured Command objects for routing.
Supports:
- @agent commands: @pm, @builder-1, etc.
- Multi-agent: @pm,ba,writer task
- Background: @pm task &
- Pipeline: @pm task1 -> @builder task2
- System commands: /help, /status, /history, /quit
- Raw input: anything else
"""

import re
from dataclasses import dataclass, field
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
class PipelineStage:
    """A single stage in a pipeline.

    Attributes:
        agent_ids: List of agents for this stage.
        content: The task content for this stage.
    """

    agent_ids: list[str]
    content: str


@dataclass
class Command:
    """Parsed command from user input.

    Attributes:
        type: The type of command.
        agent_id: For AGENT type, the first agent identifier (backward compat).
        agent_ids: For AGENT type, list of all agent identifiers.
        content: For AGENT/RAW type, the content/task.
        command: For SYSTEM type, the command name.
        args: For SYSTEM type, command arguments.
        background: Whether to run in background (&).
        is_pipeline: Whether this is a pipeline (->).
        pipeline: List of pipeline stages if is_pipeline.
    """

    type: CommandType
    agent_id: Optional[str] = None
    agent_ids: list[str] = field(default_factory=list)
    content: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    background: bool = False
    is_pipeline: bool = False
    pipeline: Optional[list[PipelineStage]] = None


# Pattern for agent commands: @agent-id or @agent1,agent2
AGENT_PATTERN = re.compile(r"^@([a-zA-Z][a-zA-Z0-9,-]*)\s*(.*)", re.DOTALL)

# Pattern for system commands: /command args
SYSTEM_PATTERN = re.compile(r"^/([a-zA-Z][a-zA-Z0-9-]*)\s*(.*)", re.DOTALL)

# Pattern for pipeline separator
PIPELINE_PATTERN = re.compile(r"\s*->\s*@")


def parse_command(input_text: str) -> Command:
    """Parse user input into a Command object.

    Args:
        input_text: Raw user input string.

    Returns:
        Parsed Command object.

    Raises:
        ParseError: If command syntax is invalid.
    """
    # Try system command (/command args) first
    system_match = SYSTEM_PATTERN.match(input_text)
    if system_match:
        command = system_match.group(1)
        args_str = system_match.group(2).strip()
        args = args_str.split() if args_str else []

        return Command(type=CommandType.SYSTEM, command=command, args=args)

    # Try agent command (@agent task)
    agent_match = AGENT_PATTERN.match(input_text)
    if agent_match:
        return _parse_agent_command(input_text, agent_match)

    # Default to raw input
    return Command(type=CommandType.RAW, content=input_text)


def _parse_agent_command(input_text: str, agent_match: re.Match) -> Command:
    """Parse an agent command with potential operators.

    Args:
        input_text: Original input text.
        agent_match: Regex match for agent pattern.

    Returns:
        Parsed Command object.
    """
    # Check for pipeline (->)
    if PIPELINE_PATTERN.search(input_text):
        return _parse_pipeline(input_text)

    # Parse single stage
    agents_str = agent_match.group(1)
    content = agent_match.group(2)

    # Parse agent IDs (comma-separated)
    agent_ids = [a.strip() for a in agents_str.split(",") if a.strip()]

    # Check for background operator (&)
    background = False
    if content:
        content = content.strip()
        if content.endswith("&"):
            background = True
            content = content[:-1].strip()

    if not content:
        raise ParseError(f"Agent command requires task: @{agents_str} <task required>")

    # Remove exactly one leading space if present
    if agent_match.group(2).startswith(" "):
        raw_content = agent_match.group(2)[1:]
        if raw_content.endswith("&"):
            raw_content = raw_content[:-1].rstrip()
        content = raw_content

    return Command(
        type=CommandType.AGENT,
        agent_id=agent_ids[0] if agent_ids else None,
        agent_ids=agent_ids,
        content=content,
        background=background,
        is_pipeline=False,
    )


def _parse_pipeline(input_text: str) -> Command:
    """Parse a pipeline command with -> operators.

    Args:
        input_text: Full input text containing pipeline.

    Returns:
        Parsed Command with pipeline stages.
    """
    # Split by -> @
    # We need to preserve the @ for each stage after the split
    parts = re.split(r"\s*->\s*(?=@)", input_text)

    if len(parts) < 2:
        # Not actually a pipeline, treat as regular command
        agent_match = AGENT_PATTERN.match(input_text)
        if agent_match:
            return _parse_agent_command.__wrapped__(input_text, agent_match)  # type: ignore
        return Command(type=CommandType.RAW, content=input_text)

    stages: list[PipelineStage] = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Parse each stage
        stage_match = AGENT_PATTERN.match(part)
        if not stage_match:
            raise ParseError(f"Invalid pipeline stage: {part}")

        agents_str = stage_match.group(1)
        content = stage_match.group(2).strip() if stage_match.group(2) else ""

        agent_ids = [a.strip() for a in agents_str.split(",") if a.strip()]

        stages.append(PipelineStage(agent_ids=agent_ids, content=content))

    # Check for background on last stage
    background = False
    if stages and stages[-1].content.endswith("&"):
        background = True
        stages[-1] = PipelineStage(
            agent_ids=stages[-1].agent_ids,
            content=stages[-1].content[:-1].strip(),
        )

    # Validate all stages have content except possibly last
    for i, stage in enumerate(stages[:-1]):
        if not stage.content:
            raise ParseError(f"Pipeline stage {i+1} requires task content")

    return Command(
        type=CommandType.AGENT,
        agent_id=stages[0].agent_ids[0] if stages and stages[0].agent_ids else None,
        agent_ids=stages[0].agent_ids if stages else [],
        content=stages[0].content if stages else "",
        background=background,
        is_pipeline=True,
        pipeline=stages,
    )
