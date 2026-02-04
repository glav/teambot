"""Tests for REPL agent router."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from teambot.repl.parser import Command, CommandType
from teambot.repl.router import AgentRouter, RouterError


class TestAgentRouterValidation:
    """Tests for agent ID validation."""

    def test_valid_agent_ids(self):
        """Test that valid agent IDs are accepted."""
        router = AgentRouter()

        for agent_id in ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]:
            assert router.is_valid_agent(agent_id) is True

    def test_invalid_agent_ids(self):
        """Test that invalid agent IDs are rejected."""
        router = AgentRouter()

        for agent_id in ["unknown", "admin", "builder-3", "PM", "Ba"]:
            assert router.is_valid_agent(agent_id) is False

    def test_agent_aliases_resolved(self):
        """Test that agent aliases are resolved."""
        router = AgentRouter()

        # Aliases should map to canonical IDs
        assert router.resolve_agent_id("pm") == "pm"
        assert router.resolve_agent_id("ba") == "ba"
        assert router.resolve_agent_id("project_manager") == "pm"
        assert router.resolve_agent_id("business_analyst") == "ba"
        assert router.resolve_agent_id("technical_writer") == "writer"

    def test_get_all_agents(self):
        """Test getting list of all agents."""
        router = AgentRouter()
        agents = router.get_all_agents()

        assert "pm" in agents
        assert "ba" in agents
        assert "writer" in agents
        assert "builder-1" in agents
        assert "builder-2" in agents
        assert "reviewer" in agents
        assert len(agents) == 6


class TestAgentRouterRouting:
    """Tests for command routing."""

    @pytest.mark.asyncio
    async def test_route_agent_command(self):
        """Test routing an agent command."""
        router = AgentRouter()
        mock_handler = AsyncMock(return_value="Response from PM")

        router.register_agent_handler(mock_handler)

        cmd = Command(type=CommandType.AGENT, agent_id="pm", content="Create plan")
        result = await router.route(cmd)

        mock_handler.assert_called_once_with("pm", "Create plan")
        assert result == "Response from PM"

    @pytest.mark.asyncio
    async def test_route_system_command(self):
        """Test routing a system command."""
        router = AgentRouter()
        mock_handler = MagicMock(return_value="Help text")

        router.register_system_handler(mock_handler)

        cmd = Command(type=CommandType.SYSTEM, command="help", args=[])
        result = await router.route(cmd)

        mock_handler.assert_called_once_with("help", [])
        assert result == "Help text"

    @pytest.mark.asyncio
    async def test_route_raw_command(self):
        """Test routing raw input."""
        router = AgentRouter()
        mock_handler = MagicMock(return_value="Default response")

        router.register_raw_handler(mock_handler)

        cmd = Command(type=CommandType.RAW, content="Hello there")
        result = await router.route(cmd)

        mock_handler.assert_called_once_with("Hello there")
        assert result == "Default response"

    @pytest.mark.asyncio
    async def test_route_invalid_agent_raises(self):
        """Test routing to invalid agent raises error."""
        router = AgentRouter()
        mock_handler = AsyncMock()
        router.register_agent_handler(mock_handler)

        cmd = Command(type=CommandType.AGENT, agent_id="unknown", content="Task")

        with pytest.raises(RouterError, match="Unknown agent"):
            await router.route(cmd)

    @pytest.mark.asyncio
    async def test_route_without_handler_raises(self):
        """Test routing without registered handler raises error."""
        router = AgentRouter()

        cmd = Command(type=CommandType.AGENT, agent_id="pm", content="Task")

        with pytest.raises(RouterError, match="No handler"):
            await router.route(cmd)


class TestAgentRouterWithAliases:
    """Tests for routing with agent aliases."""

    @pytest.mark.asyncio
    async def test_route_alias_resolves_to_canonical(self):
        """Test that alias is resolved to canonical ID."""
        router = AgentRouter()
        captured_agent = None

        async def capture_handler(agent_id, content):
            nonlocal captured_agent
            captured_agent = agent_id
            return "OK"

        router.register_agent_handler(capture_handler)

        # Use full name alias
        cmd = Command(type=CommandType.AGENT, agent_id="project_manager", content="Task")
        await router.route(cmd)

        # Should be resolved to canonical "pm"
        assert captured_agent == "pm"


class TestRouterHistory:
    """Tests for command history tracking."""

    @pytest.mark.asyncio
    async def test_history_recorded(self):
        """Test that commands are recorded in history."""
        router = AgentRouter()
        router.register_agent_handler(AsyncMock(return_value="OK"))

        cmd = Command(type=CommandType.AGENT, agent_id="pm", content="Task 1")
        await router.route(cmd)

        history = router.get_history()
        assert len(history) == 1
        assert history[0]["agent_id"] == "pm"
        assert history[0]["content"] == "Task 1"

    @pytest.mark.asyncio
    async def test_history_multiple_commands(self):
        """Test history with multiple commands."""
        router = AgentRouter()
        router.register_agent_handler(AsyncMock(return_value="OK"))

        await router.route(Command(type=CommandType.AGENT, agent_id="pm", content="Task 1"))
        await router.route(Command(type=CommandType.AGENT, agent_id="ba", content="Task 2"))

        history = router.get_history()
        assert len(history) == 2
        assert history[0]["agent_id"] == "pm"
        assert history[1]["agent_id"] == "ba"

    def test_clear_history(self):
        """Test clearing command history."""
        router = AgentRouter()
        router._history = [{"agent_id": "pm", "content": "Task"}]

        router.clear_history()

        assert len(router.get_history()) == 0

    @pytest.mark.asyncio
    async def test_history_limit(self):
        """Test history respects limit."""
        router = AgentRouter(history_limit=5)
        router.register_agent_handler(AsyncMock(return_value="OK"))

        for i in range(10):
            await router.route(Command(type=CommandType.AGENT, agent_id="pm", content=f"Task {i}"))

        history = router.get_history()
        assert len(history) == 5
        # Should have last 5 (5-9)
        assert history[0]["content"] == "Task 5"
        assert history[4]["content"] == "Task 9"
