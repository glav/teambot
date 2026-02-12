"""Integration acceptance tests for unknown-agent-validation feature.

These tests exercise the REAL implementation code to validate each
acceptance scenario (AT-001 through AT-007) from the feature spec.
No core functionality is mocked — only external dependencies (SDK client)
that are unreachable in test environments.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from teambot.repl.parser import CommandType, ParseError, parse_command
from teambot.repl.router import AGENT_ALIASES, VALID_AGENTS, AgentRouter, RouterError
from teambot.tasks.executor import TaskExecutor
from teambot.ui.agent_state import AgentStatusManager


# ---------------------------------------------------------------------------
# AT-001: Simple Unknown Agent Command (Simple Path)
# ---------------------------------------------------------------------------
class TestAT001SimpleUnknownAgent:
    """User sends `@unknown-agent do something` — must be rejected."""

    def test_at_001_parse_produces_agent_command(self):
        """Parser accepts syntax and creates an agent command."""
        cmd = parse_command("@unknown-agent do something")
        assert cmd.type == CommandType.AGENT
        assert cmd.agent_ids == ["unknown-agent"]
        assert "do something" in cmd.content

    def test_at_001_router_rejects_unknown_agent(self):
        """Router.is_valid_agent returns False for unknown-agent."""
        router = AgentRouter()
        assert router.is_valid_agent("unknown-agent") is False

    @pytest.mark.asyncio
    async def test_at_001_route_raises_error(self):
        """Router.route raises RouterError with correct message."""
        router = AgentRouter()
        router.register_agent_handler(AsyncMock())
        cmd = parse_command("@unknown-agent do something")
        with pytest.raises(RouterError, match=r"Unknown agent: 'unknown-agent'"):
            await router.route(cmd)

    @pytest.mark.asyncio
    async def test_at_001_executor_rejects_unknown_agent(self):
        """TaskExecutor.execute rejects unknown agent before dispatch."""
        executor = TaskExecutor(sdk_client=MagicMock())
        cmd = parse_command("@unknown-agent do something")
        result = await executor.execute(cmd)
        assert result.success is False
        assert "Unknown agent: 'unknown-agent'" in result.error
        assert "Valid agents:" in result.error

    def test_at_001_no_status_entry_created(self):
        """AgentStatusManager does not create entry for unknown-agent."""
        manager = AgentStatusManager()
        manager.set_running("unknown-agent", "do something")
        assert manager.get("unknown-agent") is None


# ---------------------------------------------------------------------------
# AT-002: Unknown Agent in Background Command (Advanced Path)
# ---------------------------------------------------------------------------
class TestAT002BackgroundUnknownAgent:
    """User sends `@unknown-agent do something &` — must be rejected."""

    def test_at_002_parse_produces_background_command(self):
        """Parser recognises background operator for unknown agent."""
        cmd = parse_command("@unknown-agent do something &")
        assert cmd.type == CommandType.AGENT
        assert cmd.background is True
        assert cmd.agent_ids == ["unknown-agent"]

    @pytest.mark.asyncio
    async def test_at_002_executor_rejects_background_unknown(self):
        """TaskExecutor rejects background command for unknown agent."""
        executor = TaskExecutor(sdk_client=MagicMock())
        cmd = parse_command("@unknown-agent do something &")
        result = await executor.execute(cmd)
        assert result.success is False
        assert "Unknown agent: 'unknown-agent'" in result.error

    @pytest.mark.asyncio
    async def test_at_002_router_rejects_background_unknown(self):
        """Router rejects background unknown agent command."""
        router = AgentRouter()
        router.register_agent_handler(AsyncMock())
        cmd = parse_command("@unknown-agent do something &")
        with pytest.raises(RouterError, match=r"Unknown agent: 'unknown-agent'"):
            await router.route(cmd)

    def test_at_002_no_status_entry_for_background(self):
        """AgentStatusManager ignores unknown agent from background path."""
        manager = AgentStatusManager()
        manager.set_running("unknown-agent", "bg task")
        manager.set_failed("unknown-agent")
        assert manager.get("unknown-agent") is None


# ---------------------------------------------------------------------------
# AT-003: Multi-Agent Command with One Invalid ID
# ---------------------------------------------------------------------------
class TestAT003MultiAgentOneInvalid:
    """User sends `@builder-1,fake-agent implement the feature` — entire command rejected."""

    def test_at_003_parse_extracts_both_agents(self):
        """Parser extracts both agent IDs from comma-separated list."""
        cmd = parse_command("@builder-1,fake-agent implement the feature")
        assert cmd.type == CommandType.AGENT
        assert "builder-1" in cmd.agent_ids
        assert "fake-agent" in cmd.agent_ids

    @pytest.mark.asyncio
    async def test_at_003_executor_rejects_entire_command(self):
        """TaskExecutor rejects entire multi-agent command when one ID is invalid."""
        executor = TaskExecutor(sdk_client=MagicMock())
        cmd = parse_command("@builder-1,fake-agent implement the feature")
        result = await executor.execute(cmd)
        assert result.success is False
        assert "fake-agent" in result.error
        assert "Unknown agent" in result.error

    def test_at_003_no_status_entries_created(self):
        """Neither agent gets a status entry created."""
        manager = AgentStatusManager()
        initial_states = {aid: manager.get(aid).state for aid in VALID_AGENTS}
        # Attempt to set running for fake-agent (should be ignored)
        manager.set_running("fake-agent", "task")
        assert manager.get("fake-agent") is None
        # Verify valid agents are untouched
        for aid in VALID_AGENTS:
            assert manager.get(aid).state == initial_states[aid]


# ---------------------------------------------------------------------------
# AT-004: Pipeline Command with Unknown Agent
# ---------------------------------------------------------------------------
class TestAT004PipelineUnknownAgent:
    """User sends `@fake -> @pm create a plan` — rejected at parse time."""

    def test_at_004_parser_rejects_pipeline_with_unknown_agent(self):
        """Parser raises ParseError for pipeline containing unknown agent."""
        with pytest.raises(ParseError, match=r"Unknown agent: 'fake'"):
            parse_command("@fake -> @pm create a plan")

    def test_at_004_valid_agents_unaffected(self):
        """PM does not receive any input — pipeline never constructed."""
        # If ParseError is raised, no Command object is created,
        # so no downstream dispatch is possible.
        try:
            cmd = parse_command("@fake -> @pm create a plan")
            pytest.fail(f"Expected ParseError but got command: {cmd}")
        except ParseError:
            pass  # Correct — pipeline rejected

    @pytest.mark.asyncio
    async def test_at_004_executor_also_rejects_pipeline_unknown(self):
        """If a pipeline command somehow reaches executor, it rejects it."""
        executor = TaskExecutor(sdk_client=MagicMock())
        # Construct a pipeline command manually with an invalid agent
        cmd = parse_command("@pm plan -> @ba analyze")  # valid pipeline
        assert cmd.is_pipeline is True
        # Tamper one stage to inject invalid agent (PipelineStage is a dataclass)
        cmd.pipeline[1].agent_ids = ["fake-agent"]
        result = await executor.execute(cmd)
        assert result.success is False
        assert "fake-agent" in result.error


# ---------------------------------------------------------------------------
# AT-005: Valid Alias Continues to Work
# ---------------------------------------------------------------------------
class TestAT005ValidAlias:
    """User sends `@project_manager create a project plan` — resolves to pm."""

    def test_at_005_parse_recognises_underscore_alias(self):
        """Parser handles underscore in alias (project_manager)."""
        cmd = parse_command("@project_manager create a project plan")
        assert cmd.type == CommandType.AGENT
        assert cmd.agent_ids == ["project_manager"]
        assert "create a project plan" in cmd.content

    def test_at_005_router_resolves_alias(self):
        """Router resolves project_manager alias to pm."""
        router = AgentRouter()
        assert router.resolve_agent_id("project_manager") == "pm"
        assert router.is_valid_agent("project_manager") is True

    def test_at_005_all_aliases_resolve(self):
        """All defined aliases resolve to valid canonical agents."""
        router = AgentRouter()
        for alias, canonical in AGENT_ALIASES.items():
            assert router.resolve_agent_id(alias) == canonical
            assert router.is_valid_agent(alias) is True
            assert canonical in VALID_AGENTS

    @pytest.mark.asyncio
    async def test_at_005_route_alias_calls_handler(self):
        """Router routes alias command to handler with canonical ID."""
        router = AgentRouter()
        handler = AsyncMock(return_value="plan created")
        router.register_agent_handler(handler)
        cmd = parse_command("@project_manager create a project plan")
        result = await router.route(cmd)
        assert result == "plan created"
        handler.assert_called_once_with("pm", "create a project plan")

    @pytest.mark.asyncio
    async def test_at_005_executor_accepts_alias(self):
        """TaskExecutor accepts alias — validation passes."""
        sdk = AsyncMock()
        sdk.execute = AsyncMock(return_value="plan output")
        executor = TaskExecutor(sdk_client=sdk)
        cmd = parse_command("@project_manager create a project plan")
        result = await executor.execute(cmd)
        # Validation passes (no error about unknown agent)
        assert result.error is None or "Unknown agent" not in (result.error or "")


# ---------------------------------------------------------------------------
# AT-006: All Six Valid Agents Work (Regression)
# ---------------------------------------------------------------------------
class TestAT006AllValidAgents:
    """Verify all 6 valid agents continue to accept commands."""

    AGENT_COMMANDS = [
        ("@pm plan this", "pm"),
        ("@ba analyze this", "ba"),
        ("@writer document this", "writer"),
        ("@builder-1 build this", "builder-1"),
        ("@builder-2 build that", "builder-2"),
        ("@reviewer review this", "reviewer"),
    ]

    @pytest.mark.parametrize("input_text,expected_agent", AGENT_COMMANDS)
    def test_at_006_parse_valid_agent(self, input_text, expected_agent):
        """Parser correctly parses command for each valid agent."""
        cmd = parse_command(input_text)
        assert cmd.type == CommandType.AGENT
        assert expected_agent in cmd.agent_ids

    @pytest.mark.parametrize("input_text,expected_agent", AGENT_COMMANDS)
    def test_at_006_router_accepts_valid_agent(self, input_text, expected_agent):
        """Router accepts each valid agent."""
        router = AgentRouter()
        assert router.is_valid_agent(expected_agent) is True

    @pytest.mark.parametrize("input_text,expected_agent", AGENT_COMMANDS)
    @pytest.mark.asyncio
    async def test_at_006_route_dispatches_to_handler(self, input_text, expected_agent):
        """Router dispatches command to registered handler for each valid agent."""
        router = AgentRouter()
        handler = AsyncMock(return_value="output")
        router.register_agent_handler(handler)
        cmd = parse_command(input_text)
        await router.route(cmd)
        handler.assert_called_once()
        call_agent = handler.call_args[0][0]
        assert call_agent == expected_agent

    @pytest.mark.parametrize("input_text,expected_agent", AGENT_COMMANDS)
    @pytest.mark.asyncio
    async def test_at_006_executor_passes_validation(self, input_text, expected_agent):
        """TaskExecutor passes validation for each valid agent."""
        sdk = AsyncMock()
        sdk.execute = AsyncMock(return_value="done")
        executor = TaskExecutor(sdk_client=sdk)
        cmd = parse_command(input_text)
        result = await executor.execute(cmd)
        # No unknown-agent error
        assert result.error is None or "Unknown agent" not in (result.error or "")

    def test_at_006_all_seven_agents_in_valid_set(self):
        """VALID_AGENTS contains exactly the expected 7 agents (including notify)."""
        expected = {"pm", "ba", "writer", "builder-1", "builder-2", "reviewer", "notify"}
        assert VALID_AGENTS == expected

    def test_at_006_status_manager_initialises_all_six(self):
        """AgentStatusManager initialises entries for all 6 valid agents."""
        manager = AgentStatusManager()
        for agent_id in VALID_AGENTS:
            status = manager.get(agent_id)
            assert status is not None, f"Missing status for {agent_id}"
            assert status.agent_id == agent_id


# ---------------------------------------------------------------------------
# AT-007: Typo Near Valid Agent ID
# ---------------------------------------------------------------------------
class TestAT007TypoNearValidAgent:
    """User sends `@buidler-1 implement login` — rejected with helpful error."""

    def test_at_007_parse_produces_agent_command(self):
        """Parser accepts syntax (typo is a valid identifier format)."""
        cmd = parse_command("@buidler-1 implement login")
        assert cmd.type == CommandType.AGENT
        assert cmd.agent_ids == ["buidler-1"]

    def test_at_007_router_rejects_typo(self):
        """Router rejects buidler-1 as invalid."""
        router = AgentRouter()
        assert router.is_valid_agent("buidler-1") is False

    @pytest.mark.asyncio
    async def test_at_007_route_raises_with_valid_agents_list(self):
        """Router error includes the full list of valid agents."""
        router = AgentRouter()
        router.register_agent_handler(AsyncMock())
        cmd = parse_command("@buidler-1 implement login")
        with pytest.raises(RouterError, match=r"Unknown agent: 'buidler-1'") as exc_info:
            await router.route(cmd)
        error_msg = str(exc_info.value)
        # Verify valid agents are listed for user to correct typo
        for agent in sorted(VALID_AGENTS):
            assert agent in error_msg, f"Missing '{agent}' in error message"

    @pytest.mark.asyncio
    async def test_at_007_executor_rejects_typo(self):
        """TaskExecutor rejects typo with correct error."""
        executor = TaskExecutor(sdk_client=MagicMock())
        cmd = parse_command("@buidler-1 implement login")
        result = await executor.execute(cmd)
        assert result.success is False
        assert "Unknown agent: 'buidler-1'" in result.error
        assert "builder-1" in result.error  # correct agent listed

    def test_at_007_no_status_entry_for_typo(self):
        """AgentStatusManager does not create entry for typo agent."""
        manager = AgentStatusManager()
        manager.set_running("buidler-1", "implement login")
        assert manager.get("buidler-1") is None

    def test_at_007_user_can_correct_and_resubmit(self):
        """After typo rejection, corrected command parses and validates."""
        # Typo — rejected
        router = AgentRouter()
        assert router.is_valid_agent("buidler-1") is False
        # Corrected — accepted
        cmd = parse_command("@builder-1 implement login")
        assert cmd.agent_ids == ["builder-1"]
        assert router.is_valid_agent("builder-1") is True
