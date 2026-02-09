"""Acceptance test validation for default agent switching feature.

These tests exercise the REAL implementation code to validate
each acceptance scenario from the feature specification.
"""

import pytest
from unittest.mock import AsyncMock

from teambot.repl.commands import (
    CommandResult,
    SystemCommands,
    handle_help,
    handle_reset_agent,
    handle_status,
    handle_use_agent,
)
from teambot.repl.parser import Command, CommandType, parse_command
from teambot.repl.router import AgentRouter, VALID_AGENTS
from teambot.ui.agent_state import AgentStatusManager
from teambot.ui.widgets.status_panel import StatusPanel


class TestAcceptanceScenarios:
    """Integration tests validating real acceptance scenarios."""

    # ── AT-001: Switch Default Agent and Send Plain Text ──

    @pytest.mark.asyncio
    async def test_at_001_switch_default_and_route_plain_text(self):
        """After /use-agent builder-1, plain text routes to builder-1."""
        # Set up router with pm as default (like teambot.json)
        router = AgentRouter(default_agent="pm")
        agent_calls = []

        async def mock_agent_handler(agent_id: str, content: str) -> str:
            agent_calls.append((agent_id, content))
            return f"Response from {agent_id}"

        router.register_agent_handler(mock_agent_handler)

        # Step 1-2: Plain text "hello" routed to pm (default)
        cmd1 = parse_command("hello")
        assert cmd1.type == CommandType.RAW
        await router.route(cmd1)
        assert agent_calls[-1] == ("pm", "hello")

        # Step 3-4: Switch default via /use-agent builder-1
        result = handle_use_agent(["builder-1"], router)
        assert result.success is True
        assert "builder-1" in result.output
        assert router.get_default_agent() == "builder-1"

        # Step 5-6: Plain text "build the feature" routed to builder-1
        cmd2 = parse_command("build the feature")
        assert cmd2.type == CommandType.RAW
        await router.route(cmd2)
        assert agent_calls[-1] == ("builder-1", "build the feature")

    # ── AT-002: Explicit @agent Directive Overrides Default ──

    @pytest.mark.asyncio
    async def test_at_002_explicit_agent_overrides_default(self):
        """@reviewer routes to reviewer even when default is builder-1."""
        router = AgentRouter(default_agent="builder-1")
        agent_calls = []

        async def mock_agent_handler(agent_id: str, content: str) -> str:
            agent_calls.append((agent_id, content))
            return f"Response from {agent_id}"

        router.register_agent_handler(mock_agent_handler)

        # Step 1-2: Explicit @reviewer directive
        cmd1 = parse_command("@reviewer check the code")
        assert cmd1.type == CommandType.AGENT
        await router.route(cmd1)
        assert agent_calls[-1] == ("reviewer", "check the code")

        # Step 3-4: Plain text still routes to default (builder-1)
        cmd2 = parse_command("continue building")
        assert cmd2.type == CommandType.RAW
        await router.route(cmd2)
        assert agent_calls[-1] == ("builder-1", "continue building")

    # ── AT-003: Reset Agent to Configuration Default ──

    @pytest.mark.asyncio
    async def test_at_003_reset_agent_to_config_default(self):
        """After /reset-agent, plain text routes back to pm (config value)."""
        router = AgentRouter(default_agent="pm")
        agent_calls = []

        async def mock_agent_handler(agent_id: str, content: str) -> str:
            agent_calls.append((agent_id, content))
            return f"Response from {agent_id}"

        router.register_agent_handler(mock_agent_handler)

        # Pre-condition: switch away from config default
        router.set_default_agent("builder-1")
        assert router.get_default_agent() == "builder-1"

        # Step 1-2: Reset to config default
        result = handle_reset_agent([], router)
        assert result.success is True
        assert "pm" in result.output
        assert "configuration" in result.output.lower()

        # Step 3: Verify router state
        assert router.get_default_agent() == "pm"

        # Step 4: Plain text routes to pm
        cmd = parse_command("plan the next sprint")
        await router.route(cmd)
        assert agent_calls[-1] == ("pm", "plan the next sprint")

    # ── AT-004: Invalid Agent ID Produces Error ──

    def test_at_004_invalid_agent_id_error(self):
        """Invalid agent ID returns error with available agents list."""
        router = AgentRouter(default_agent="pm")

        result = handle_use_agent(["foo"], router)

        # Verify error
        assert result.success is False
        assert "foo" in result.output
        # Verify all 6 valid agents listed
        for agent in sorted(VALID_AGENTS):
            assert agent in result.output
        # Default unchanged
        assert router.get_default_agent() == "pm"

    # ── AT-005: /use-agent Without Arguments Shows Info ──

    def test_at_005_use_agent_no_args_shows_info(self):
        """/use-agent with no args shows current default and available agents."""
        router = AgentRouter(default_agent="builder-1")

        result = handle_use_agent([], router)

        assert result.success is True
        assert "builder-1" in result.output
        # All 6 agent IDs listed
        for agent in sorted(VALID_AGENTS):
            assert agent in result.output

    # ── AT-006: /status Shows Default Agent ──

    def test_at_006_status_shows_default_agent(self):
        """/status output includes default agent with session override info."""
        router = AgentRouter(default_agent="pm")
        router.set_default_agent("builder-1")

        result = handle_status([], router)

        assert result.success is True
        assert "Default Agent" in result.output
        assert "builder-1" in result.output
        # Shows it's a session override
        assert "session override" in result.output
        assert "pm" in result.output  # config default also shown

    def test_at_006_status_via_system_commands_dispatch(self):
        """/status dispatched through SystemCommands includes default agent."""
        router = AgentRouter(default_agent="pm")
        router.set_default_agent("builder-1")
        commands = SystemCommands(router=router)

        result = commands.dispatch("status", [])

        assert result.success is True
        assert "Default Agent" in result.output
        assert "builder-1" in result.output

    # ── AT-007: Status Panel Shows Default Indicator ──

    def test_at_007_status_panel_default_indicator(self):
        """Status panel marks the default agent with ★ and 'default' label."""
        manager = AgentStatusManager()

        # Step 1: pm is the default
        manager.set_default_agent("pm")
        panel = StatusPanel(manager)
        content = panel._format_status()

        # Verify pm row has default indicator
        lines = content.split("\n")
        pm_line = [line for line in lines if "pm" in line and "★" in line]
        assert len(pm_line) > 0, f"pm should have ★ indicator, got:\n{content}"
        assert "default" in pm_line[0]

        # Step 2: Switch to writer
        manager.set_default_agent("writer")
        content2 = panel._format_status()

        lines2 = content2.split("\n")
        # writer now has the indicator
        writer_line = [line for line in lines2 if "writer" in line and "★" in line]
        assert len(writer_line) > 0, f"writer should have ★ indicator, got:\n{content2}"
        assert "default" in writer_line[0]

        # pm no longer has it
        pm_line2 = [line for line in lines2 if "pm" in line]
        assert len(pm_line2) > 0
        assert "★" not in pm_line2[0]
        assert "idle" in pm_line2[0]

    # ── AT-008: Session Restart Resets Default ──

    def test_at_008_session_restart_resets_default(self):
        """New AgentRouter instance starts with config default, not runtime value."""
        # Simulate first session
        router1 = AgentRouter(default_agent="pm")
        router1.set_default_agent("builder-2")
        assert router1.get_default_agent() == "builder-2"

        # Simulate session restart — new router with same config
        router2 = AgentRouter(default_agent="pm")
        assert router2.get_default_agent() == "pm"
        assert router2.get_config_default_agent() == "pm"

    # ── AT-009: /help Documents New Commands ──

    def test_at_009_help_documents_new_commands(self):
        """/help output contains /use-agent and /reset-agent entries."""
        result = handle_help([])

        assert result.success is True
        assert "/use-agent" in result.output
        assert "/reset-agent" in result.output

    def test_at_009_help_via_system_commands_dispatch(self):
        """/help dispatched through SystemCommands includes new commands."""
        commands = SystemCommands()
        result = commands.dispatch("help", [])

        assert result.success is True
        assert "/use-agent" in result.output
        assert "/reset-agent" in result.output


class TestAcceptanceEndToEnd:
    """End-to-end integration testing the full dispatch chain."""

    @pytest.mark.asyncio
    async def test_at_e2e_full_workflow(self):
        """Full workflow: start → switch → use → explicit → reset → use."""
        router = AgentRouter(default_agent="pm")
        commands = SystemCommands(router=router)
        agent_calls = []

        async def agent_handler(agent_id: str, content: str) -> str:
            agent_calls.append((agent_id, content))
            return f"OK from {agent_id}"

        router.register_agent_handler(agent_handler)
        router.register_system_handler(commands.dispatch)

        # 1. Plain text → pm (default)
        await router.route(parse_command("hello"))
        assert agent_calls[-1] == ("pm", "hello")

        # 2. /use-agent builder-1 via dispatch
        cmd_switch = parse_command("/use-agent builder-1")
        result = await router.route(cmd_switch)
        assert result.success is True

        # 3. Plain text → builder-1 (new default)
        await router.route(parse_command("build it"))
        assert agent_calls[-1] == ("builder-1", "build it")

        # 4. @reviewer explicit → reviewer
        await router.route(parse_command("@reviewer review this"))
        assert agent_calls[-1] == ("reviewer", "review this")

        # 5. Plain text → still builder-1
        await router.route(parse_command("keep going"))
        assert agent_calls[-1] == ("builder-1", "keep going")

        # 6. /reset-agent via dispatch
        cmd_reset = parse_command("/reset-agent")
        result = await router.route(cmd_reset)
        assert result.success is True

        # 7. Plain text → pm (restored)
        await router.route(parse_command("plan stuff"))
        assert agent_calls[-1] == ("pm", "plan stuff")
