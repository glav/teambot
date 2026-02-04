"""Tests for agent loader."""

from pathlib import Path

import pytest

from teambot.copilot.agent_loader import AgentDefinition, AgentLoader


class TestAgentDefinition:
    """Tests for AgentDefinition dataclass."""

    def test_default_display_name_from_name(self):
        """Display name is generated from name if not provided."""
        agent = AgentDefinition(name="pm")
        assert agent.display_name == "Pm"

    def test_default_display_name_with_hyphen(self):
        """Display name handles hyphenated names."""
        agent = AgentDefinition(name="builder-1")
        assert agent.display_name == "Builder 1"

    def test_explicit_display_name_preserved(self):
        """Explicit display name is preserved."""
        agent = AgentDefinition(name="pm", display_name="Project Manager")
        assert agent.display_name == "Project Manager"


class TestAgentLoader:
    """Tests for AgentLoader."""

    @pytest.fixture
    def agents_dir(self, tmp_path: Path) -> Path:
        """Create a temporary agents directory."""
        agents = tmp_path / ".github" / "agents"
        agents.mkdir(parents=True)
        return agents

    @pytest.fixture
    def loader(self, tmp_path: Path) -> AgentLoader:
        """Create a loader pointing to temp directory."""
        return AgentLoader(repo_root=tmp_path)

    def test_load_empty_directory(self, loader: AgentLoader):
        """Loading from empty directory returns empty dict."""
        # agents_dir doesn't exist
        agents = loader.load_all()
        assert agents == {}

    def test_load_single_agent(self, agents_dir: Path, loader: AgentLoader):
        """Load a single agent definition."""
        agent_file = agents_dir / "test.agent.md"
        agent_file.write_text("""---
name: test
description: A test agent
tools: []
---

# Test Agent

This is a test agent prompt.
""")

        agents = loader.load_all()

        assert "test" in agents
        assert agents["test"].name == "test"
        assert agents["test"].description == "A test agent"
        assert agents["test"].tools == []
        assert "This is a test agent prompt" in agents["test"].prompt

    def test_load_agent_with_all_tools(self, agents_dir: Path, loader: AgentLoader):
        """Agent with tools: ["*"] gets None (all tools)."""
        agent_file = agents_dir / "builder.agent.md"
        agent_file.write_text("""---
name: builder
description: A builder agent
tools: ["*"]
---

Builder prompt.
""")

        agents = loader.load_all()

        assert "builder" in agents
        assert agents["builder"].tools is None  # All tools

    def test_get_agent_exact_match(self, agents_dir: Path, loader: AgentLoader):
        """get_agent returns exact match."""
        agent_file = agents_dir / "pm.agent.md"
        agent_file.write_text("""---
name: pm
description: Project Manager
---

PM prompt.
""")

        agent = loader.get_agent("pm")

        assert agent is not None
        assert agent.name == "pm"

    def test_get_agent_base_name_fallback(self, agents_dir: Path, loader: AgentLoader):
        """get_agent falls back to base name for numbered agents."""
        agent_file = agents_dir / "builder.agent.md"
        agent_file.write_text("""---
name: builder
description: Builder
---

Builder prompt.
""")

        # Request builder-1 but only builder.agent.md exists
        agent = loader.get_agent("builder-1")

        assert agent is not None
        assert agent.name == "builder"

    def test_get_agent_not_found(self, loader: AgentLoader):
        """get_agent returns None for unknown agent."""
        agent = loader.get_agent("nonexistent")
        assert agent is None

    def test_cached_results(self, agents_dir: Path, loader: AgentLoader):
        """Results are cached after first load."""
        agent_file = agents_dir / "test.agent.md"
        agent_file.write_text("""---
name: test
---

Prompt.
""")

        # First load
        agents1 = loader.load_all()
        assert "test" in agents1

        # Modify file
        agent_file.write_text("""---
name: modified
---

Modified.
""")

        # Second load returns cached
        agents2 = loader.load_all()
        assert "test" in agents2  # Still cached
        assert "modified" not in agents2
