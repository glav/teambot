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
        references: Agent IDs from $ref syntax (e.g., $pm -> ["pm"]).
        model: AI model override for this command (--model or -m).
        is_session_model_set: True if command is setting session model only.
    """

    type: CommandType
    agent_id: str | None = None
    agent_ids: list[str] = field(default_factory=list)
    content: str | None = None
    command: str | None = None
    args: list[str] | None = None
    background: bool = False
    is_pipeline: bool = False
    pipeline: list[PipelineStage] | None = None
    references: list[str] = field(default_factory=list)
    model: str | None = None
    is_session_model_set: bool = False


# Pattern for agent commands: @agent-id or @agent1,agent2
AGENT_PATTERN = re.compile(r"^@([a-zA-Z][a-zA-Z0-9,_-]*)\s*(.*)", re.DOTALL)

# Pattern for system commands: /command args
SYSTEM_PATTERN = re.compile(r"^/([a-zA-Z][a-zA-Z0-9-]*)\s*(.*)", re.DOTALL)

# Pattern for pipeline separator (requires @ after ->)
PIPELINE_PATTERN = re.compile(r"\s*->\s*@")

# Pattern for detecting raw input -> @agent (no @ prefix before ->)
# Used to detect when default agent should be prepended
RAW_PIPELINE_PATTERN = re.compile(r"^([^@/][^>]*?)\s*->\s*@")

# Pattern for agent references in content: $pm, $ba, $builder-1
# Uses negative lookbehind to exclude escaped \$
REFERENCE_PATTERN = re.compile(r"(?<!\\)\$([a-zA-Z][a-zA-Z0-9_-]*)")

# Pattern for model flag: --model <value> or -m <value>
MODEL_FLAG_PATTERN = re.compile(r"(?:--model|-m)\s+([^\s]+)")


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


def needs_default_agent_for_pipeline(input_text: str) -> bool:
    """Check if raw input needs default agent prepended for pipeline.

    Detects patterns like "tell joke -> @notify" where raw input
    is followed by pipeline operator to an agent.

    Args:
        input_text: Raw user input string.

    Returns:
        True if input needs default agent for pipeline parsing.
    """
    return RAW_PIPELINE_PATTERN.match(input_text) is not None


def prepend_default_agent(input_text: str, default_agent: str) -> str:
    """Prepend default agent to raw pipeline input.

    Converts "tell joke -> @notify" to "@pm tell joke -> @notify".

    Args:
        input_text: Raw user input string.
        default_agent: Agent ID to prepend.

    Returns:
        Input text with default agent prepended.
    """
    return f"@{default_agent} {input_text}"


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

    # Extract model flag if present
    model = None
    is_session_model_set = False
    if content:
        model_match = MODEL_FLAG_PATTERN.search(content)
        if model_match:
            model = model_match.group(1)
            # Remove model flag from content
            content = MODEL_FLAG_PATTERN.sub("", content)

    # Check for missing model value (--model or -m at end without value)
    if content and ("--model" in content or re.search(r"-m\s*$", content)):
        raise ParseError("--model flag requires a model name")

    # Check for background operator (&)
    background = False
    if content:
        content = content.strip()
        if content.endswith("&"):
            background = True
            content = content[:-1].strip()

    # Determine if this is just setting session model (no task)
    if model and not content:
        is_session_model_set = True

    if not content and not is_session_model_set:
        raise ParseError(f"Agent command requires task: @{agents_str} <task required>")

    # Remove exactly one leading space if present (for original content)
    if content and agent_match.group(2).startswith(" "):
        raw_content = agent_match.group(2)[1:]
        # Remove model flag from raw content if present
        if model:
            raw_content = MODEL_FLAG_PATTERN.sub("", raw_content)
        if raw_content.endswith("&"):
            raw_content = raw_content[:-1].rstrip()
        content = raw_content.strip()

    # Detect $agent references in content
    references = []
    if content:
        matches = REFERENCE_PATTERN.findall(content)
        # Deduplicate while preserving order
        seen = set()
        references = [r for r in matches if not (r in seen or seen.add(r))]

    return Command(
        type=CommandType.AGENT,
        agent_id=agent_ids[0] if agent_ids else None,
        agent_ids=agent_ids,
        content=content,
        background=background,
        is_pipeline=False,
        references=references,
        model=model,
        is_session_model_set=is_session_model_set,
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

    # Validate agent IDs before checking content
    from teambot.repl.router import AGENT_ALIASES, VALID_AGENTS

    for stage in stages:
        for agent_id in stage.agent_ids:
            canonical = AGENT_ALIASES.get(agent_id, agent_id)
            if canonical not in VALID_AGENTS:
                valid_list = ", ".join(sorted(VALID_AGENTS))
                raise ParseError(f"Unknown agent: '{agent_id}'. Valid agents: {valid_list}")

    # Validate all stages have content except possibly last
    for i, stage in enumerate(stages[:-1]):
        if not stage.content:
            raise ParseError(f"Pipeline stage {i + 1} requires task content")

    # Extract references from all stages
    all_content = " ".join(stage.content for stage in stages)
    ref_matches = REFERENCE_PATTERN.findall(all_content)
    # Deduplicate while preserving order
    seen = set()
    references = []
    for ref in ref_matches:
        if ref not in seen:
            seen.add(ref)
            references.append(ref)

    return Command(
        type=CommandType.AGENT,
        agent_id=stages[0].agent_ids[0] if stages and stages[0].agent_ids else None,
        agent_ids=stages[0].agent_ids if stages else [],
        content=stages[0].content if stages else "",
        background=background,
        is_pipeline=True,
        pipeline=stages,
        references=references,
    )
