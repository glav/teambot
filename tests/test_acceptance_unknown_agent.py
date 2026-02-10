"""Acceptance test validation for unknown agent ID validation feature.

These tests exercise the REAL implementation code — no mocks on the
core validation logic. Only the SDK client is mocked (network boundary).
"""

from unittest.mock import AsyncMock

import pytest

from teambot.repl.parser import Command, CommandType, ParseError, parse_command
from teambot.repl.router import AGENT_ALIASES, VALID_AGENTS, AgentRouter, RouterError
from teambot.tasks.executor import TaskExecutor
from teambot.ui.agent_state import AgentStatusManager


class TestAcceptanceUnknownAgentValidation:
    """Acceptance tests for unknown agent ID validation."""

    # ------------------------------------------------------------------
    # AT-001: Simple Unknown Agent Command (Simple Path)
    # ------------------------------------------------------------------
    def test_at_001_simple_unknown_agent_rejected_by_router(self):
        """Simple path: router rejects unknown agent with helpful error."""
        router = AgentRouter()
        router.register_agent_handler(AsyncMock(return_value="ok"))

        command = parse_command("@unknown-agent do something")
        with pytest.raises(RouterError, match="Unknown agent"):
            import asyncio

            asyncio.get_event_loop().run_until_complete(router.route(command))

    def test_at_001_simple_unknown_agent_not_valid(self):
        """Router's is_valid_agent returns False for unknown agent."""
        router = AgentRouter()
        assert not router.is_valid_agent("unknown-agent")

    def test_at_001_no_status_entry_for_unknown_agent(self):
        """AgentStatusManager does not create entry for unknown agent."""
        manager = AgentStatusManager()
        manager.set_running("unknown-agent", "do something")
        assert manager.get("unknown-agent") is None

    # ------------------------------------------------------------------
    # AT-002: Unknown Agent in Background Command (Advanced Path)
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_002_background_unknown_agent_rejected_by_executor(self):
        """Background command with unknown agent is rejected by TaskExecutor."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@unknown-agent do something &")
        result = await executor.execute(command)

        assert not result.success
        assert "Unknown agent: 'unknown-agent'" in result.error
        assert "Valid agents:" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_at_002_no_background_task_created(self):
        """No background task is spawned for unknown agent."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@unknown-agent do something &")
        result = await executor.execute(command)

        assert not result.background
        assert result.task_id is None
        assert executor.task_count == 0

    @pytest.mark.asyncio
    async def test_at_002_no_status_entry_created(self):
        """No status entry is created for unknown agent on background path."""
        mock_sdk = AsyncMock()
        status_manager = AgentStatusManager()
        executor = TaskExecutor(
            sdk_client=mock_sdk,
            agent_status_manager=status_manager,
        )

        command = parse_command("@unknown-agent do something &")
        await executor.execute(command)

        assert status_manager.get("unknown-agent") is None

    # ------------------------------------------------------------------
    # AT-003: Multi-Agent Command with One Invalid ID
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_003_multiagent_with_invalid_id_rejects_all(self):
        """Multi-agent command with one invalid ID rejects entire command."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@builder-1,fake-agent implement the feature")
        result = await executor.execute(command)

        assert not result.success
        assert "fake-agent" in result.error
        assert "Unknown agent:" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_at_003_no_tasks_dispatched_for_either_agent(self):
        """No tasks created for any agent when one is invalid."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@builder-1,fake-agent implement the feature")
        result = await executor.execute(command)

        assert executor.task_count == 0
        assert result.task_ids == []

    # ------------------------------------------------------------------
    # AT-004: Pipeline Command with Unknown Agent
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_004_pipeline_with_unknown_agent_rejects(self):
        """Pipeline with unknown agent rejects entire pipeline at parse time."""
        with pytest.raises(ParseError, match="Unknown agent: 'fake'"):
            parse_command("@fake -> @pm create a plan")

    @pytest.mark.asyncio
    async def test_at_004_pm_does_not_receive_input(self):
        """PM agent does not execute when pipeline has unknown agent."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        with pytest.raises(ParseError, match="Unknown agent: 'fake'"):
            parse_command("@fake -> @pm create a plan")

        # Parser rejects before executor, so no tasks dispatched
        assert executor.task_count == 0
        mock_sdk.execute.assert_not_called()

    # ------------------------------------------------------------------
    # AT-005: Valid Alias Continues to Work
    # ------------------------------------------------------------------
    def test_at_005_alias_resolves_in_router(self):
        """Router resolves project_manager alias to pm."""
        router = AgentRouter()
        assert router.is_valid_agent("project_manager")
        assert router.resolve_agent_id("project_manager") == "pm"

    @pytest.mark.asyncio
    async def test_at_005_alias_accepted_by_executor(self):
        """Executor accepts alias agent ID (project_manager -> pm)."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Plan created")
        executor = TaskExecutor(sdk_client=mock_sdk)

        # Parser regex doesn't support underscores, so construct directly
        command = Command(
            type=CommandType.AGENT,
            agent_id="project_manager",
            agent_ids=["project_manager"],
            content="create a project plan",
            background=True,
        )
        result = await executor.execute(command)

        assert result.error is None or "Unknown agent" not in (result.error or "")

    def test_at_005_all_aliases_are_valid(self):
        """All defined aliases resolve to valid agents."""
        router = AgentRouter()
        for alias, canonical in AGENT_ALIASES.items():
            assert router.is_valid_agent(alias), f"Alias '{alias}' not valid"
            assert router.resolve_agent_id(alias) == canonical

    # ------------------------------------------------------------------
    # AT-006: All Six Valid Agents Work (Regression)
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_006_all_six_agents_accepted_by_executor(self):
        """All 6 valid agents are accepted by TaskExecutor."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")

        for agent_id in sorted(VALID_AGENTS):
            executor = TaskExecutor(sdk_client=mock_sdk)
            command = parse_command(f"@{agent_id} do work &")
            result = await executor.execute(command)

            assert result.error is None or "Unknown agent" not in (result.error or ""), (
                f"Valid agent '{agent_id}' was rejected"
            )

    def test_at_006_all_six_agents_valid_in_router(self):
        """All 6 agents pass router validation."""
        router = AgentRouter()
        for agent_id in sorted(VALID_AGENTS):
            assert router.is_valid_agent(agent_id), f"'{agent_id}' not valid"

    @pytest.mark.asyncio
    async def test_at_006_each_agent_dispatches_to_sdk(self):
        """Each valid agent command dispatches to SDK."""
        for agent_id in sorted(VALID_AGENTS):
            mock_sdk = AsyncMock()
            mock_sdk.execute = AsyncMock(return_value=f"{agent_id} output")
            executor = TaskExecutor(sdk_client=mock_sdk)

            command = parse_command(f"@{agent_id} do work")
            result = await executor.execute(command)

            assert result.success, f"Agent '{agent_id}' failed: {result.error}"
            mock_sdk.execute.assert_called_once()

    # ------------------------------------------------------------------
    # AT-007: Typo Near Valid Agent ID
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_007_typo_agent_rejected(self):
        """Typo 'buidler-1' is rejected with helpful error."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@buidler-1 implement login &")
        result = await executor.execute(command)

        assert not result.success
        assert "Unknown agent: 'buidler-1'" in result.error
        assert "ba, builder-1, builder-2, pm, reviewer, writer" in result.error
        mock_sdk.execute.assert_not_called()

    def test_at_007_typo_not_valid_in_router(self):
        """Router correctly identifies typo as invalid."""
        router = AgentRouter()
        assert not router.is_valid_agent("buidler-1")

    @pytest.mark.asyncio
    async def test_at_007_no_task_dispatched_for_typo(self):
        """No task is created for a typo agent."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@buidler-1 implement login &")
        result = await executor.execute(command)

        assert executor.task_count == 0
        assert result.task_id is None
