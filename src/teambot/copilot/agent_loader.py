"""Agent definition loader for custom agents from .github/agents/."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class AgentDefinition:
    """Parsed agent definition from .agent.md file."""

    name: str
    description: str = ""
    prompt: str = ""
    tools: list[str] | None = None  # None means all tools, [] means no tools
    display_name: str = ""

    def __post_init__(self):
        if not self.display_name:
            # Convert name to display name (e.g., "pm" -> "PM", "builder-1" -> "Builder 1")
            self.display_name = self.name.replace("-", " ").title()


class AgentLoader:
    """Loads agent definitions from .github/agents/ directory."""

    AGENTS_DIR = ".github/agents"
    AGENT_FILE_PATTERN = "*.agent.md"

    def __init__(self, repo_root: Path | None = None):
        """Initialize the agent loader.

        Args:
            repo_root: Repository root directory. Defaults to current directory.
        """
        self._repo_root = repo_root or Path.cwd()
        self._agents_dir = self._repo_root / self.AGENTS_DIR
        self._cache: dict[str, AgentDefinition] = {}
        self._loaded = False

    @property
    def agents_dir(self) -> Path:
        """Get the agents directory path."""
        return self._agents_dir

    def load_all(self) -> dict[str, AgentDefinition]:
        """Load all agent definitions from the agents directory.

        Returns:
            Dictionary mapping agent names to their definitions.
        """
        if self._loaded:
            return self._cache

        if not self._agents_dir.exists():
            logger.warning(f"Agents directory not found: {self._agents_dir}")
            return {}

        for agent_file in self._agents_dir.glob(self.AGENT_FILE_PATTERN):
            try:
                agent = self._parse_agent_file(agent_file)
                if agent:
                    self._cache[agent.name] = agent
                    logger.debug(f"Loaded agent: {agent.name} from {agent_file}")
            except Exception as e:
                logger.error(f"Failed to parse agent file {agent_file}: {e}")

        self._loaded = True
        return self._cache

    def get_agent(self, agent_id: str) -> AgentDefinition | None:
        """Get an agent definition by ID.

        Handles aliases like builder-1 -> builder.

        Args:
            agent_id: The agent identifier (e.g., 'pm', 'builder-1').

        Returns:
            AgentDefinition or None if not found.
        """
        if not self._loaded:
            self.load_all()

        # Try exact match first
        if agent_id in self._cache:
            return self._cache[agent_id]

        # Try base name (e.g., builder-1 -> builder)
        base_name = agent_id.split("-")[0] if "-" in agent_id else None
        if base_name and base_name in self._cache:
            return self._cache[base_name]

        return None

    def _parse_agent_file(self, file_path: Path) -> AgentDefinition | None:
        """Parse a single agent file.

        Args:
            file_path: Path to the .agent.md file.

        Returns:
            AgentDefinition or None if parsing fails.
        """
        content = file_path.read_text(encoding="utf-8")

        # Extract YAML frontmatter
        frontmatter, prompt = self._extract_frontmatter(content)

        if not frontmatter:
            logger.warning(f"No frontmatter found in {file_path}")
            return None

        # Parse YAML
        try:
            metadata = yaml.safe_load(frontmatter)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {file_path}: {e}")
            return None

        if not isinstance(metadata, dict):
            logger.error(f"Frontmatter is not a dict in {file_path}")
            return None

        name = metadata.get("name")
        if not name:
            # Use filename as fallback
            name = file_path.stem.replace(".agent", "")

        # Parse tools - handle various formats
        tools = metadata.get("tools")
        if tools is not None:
            if isinstance(tools, str):
                # Handle string like '["read", "search"]' or '*'
                if tools == "*" or tools == '["*"]':
                    tools = None  # All tools
                else:
                    try:
                        tools = yaml.safe_load(tools)
                    except yaml.YAMLError:
                        tools = [tools]
            elif isinstance(tools, list):
                if tools == ["*"]:
                    tools = None  # All tools

        return AgentDefinition(
            name=name,
            description=metadata.get("description", ""),
            prompt=prompt.strip(),
            tools=tools,
            display_name=metadata.get("displayName", ""),
        )

    def _extract_frontmatter(self, content: str) -> tuple[str, str]:
        """Extract YAML frontmatter and content from markdown.

        Args:
            content: Full file content.

        Returns:
            Tuple of (frontmatter, remaining_content).
        """
        # Match YAML frontmatter delimited by ---
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)

        if match:
            return match.group(1), match.group(2)

        return "", content


# Singleton loader instance
_default_loader: AgentLoader | None = None


def get_agent_loader(repo_root: Path | None = None) -> AgentLoader:
    """Get the default agent loader instance.

    Args:
        repo_root: Repository root. If provided, creates/updates the loader.

    Returns:
        AgentLoader instance.
    """
    global _default_loader

    if repo_root is not None or _default_loader is None:
        _default_loader = AgentLoader(repo_root)

    return _default_loader


def get_agent_definition(agent_id: str) -> AgentDefinition | None:
    """Convenience function to get an agent definition.

    Args:
        agent_id: The agent identifier.

    Returns:
        AgentDefinition or None.
    """
    return get_agent_loader().get_agent(agent_id)
