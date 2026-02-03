"""Integration tests for file-based orchestration."""

from __future__ import annotations

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from teambot.orchestration import (
    ExecutionLoop,
    ExecutionResult,
    ReviewStatus,
    parse_objective_file,
    ParallelExecutor,
    AgentTask,
    partition_tasks,
)
from teambot.workflow.stages import WorkflowStage


class TestFullWorkflowExecution:
    """Integration tests for complete workflow execution."""

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client that approves all reviews."""
        client = AsyncMock()
        client.execute_streaming.return_value = "APPROVED: Work completed successfully."
        return client

    @pytest.mark.asyncio
    async def test_full_workflow_completes(
        self, objective_file: Path, teambot_dir_with_spec: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Full workflow execution completes all stages."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir_with_spec,
        )

        result = await loop.run(mock_sdk_client)

        assert result == ExecutionResult.COMPLETE
        assert loop.current_stage == WorkflowStage.COMPLETE

    @pytest.mark.asyncio
    async def test_workflow_tracks_stage_progression(
        self, objective_file: Path, teambot_dir_with_spec: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Workflow progresses through expected stages."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir_with_spec,
        )

        stages_visited: list[str] = []

        def on_progress(event: str, data: dict) -> None:
            if event == "stage_changed":
                stages_visited.append(data["stage"])

        result = await loop.run(mock_sdk_client, on_progress=on_progress)

        assert result == ExecutionResult.COMPLETE
        assert "SETUP" in stages_visited
        assert "SPEC" in stages_visited
        assert "IMPLEMENTATION" in stages_visited


class TestResumeAfterCancellation:
    """Tests for resume functionality."""

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client."""
        client = AsyncMock()
        client.execute_streaming.return_value = "APPROVED: Done."
        return client

    @pytest.mark.asyncio
    async def test_resume_continues_from_saved_stage(
        self, objective_file: Path, teambot_dir_with_spec: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Resume continues execution from saved stage."""
        # The feature name from the objective is "user-authentication"
        feature_dir = teambot_dir_with_spec / "user-authentication"
        # Feature dir should already exist from the fixture

        # Create initial state at PLAN stage
        state = {
            "objective_file": str(objective_file),
            "current_stage": "PLAN",
            "elapsed_seconds": 100.0,
            "max_seconds": 28800,
            "status": "paused",
            "stage_outputs": {
                "SETUP": "Setup complete",
                "BUSINESS_PROBLEM": "Problem defined",
                "SPEC": "Specification written",
            },
        }
        state_file = feature_dir / "orchestration_state.json"
        state_file.write_text(json.dumps(state))

        # Resume execution from the feature directory
        loop = ExecutionLoop.resume(feature_dir, {})

        assert loop.current_stage == WorkflowStage.PLAN
        assert loop.time_manager._prior_elapsed == 100.0

        # Continue execution
        result = await loop.run(mock_sdk_client)
        assert result == ExecutionResult.COMPLETE

    @pytest.mark.asyncio
    async def test_cancellation_saves_state(
        self, objective_file: Path, teambot_dir: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Cancellation saves current state."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        # Cancel immediately
        loop.cancel()
        await loop.run(mock_sdk_client)

        # Verify state file exists in feature subdirectory
        state_file = loop.teambot_dir / "orchestration_state.json"
        assert state_file.exists()

        state = json.loads(state_file.read_text())
        assert state["status"] == "cancelled"


class TestParallelBuilderExecution:
    """Tests for parallel builder execution."""

    @pytest.mark.asyncio
    async def test_builders_execute_concurrently(self) -> None:
        """Builder-1 and builder-2 execute tasks concurrently."""
        mock_client = AsyncMock()
        execution_times: dict[str, float] = {}

        async def track_execution(
            agent_id: str, prompt: str, callback: object
        ) -> str:
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.05)  # Simulate work
            end = asyncio.get_event_loop().time()
            execution_times[agent_id] = (start, end)
            return f"Output from {agent_id}"

        mock_client.execute_streaming.side_effect = track_execution

        executor = ParallelExecutor(mock_client, max_concurrent=2)
        tasks = [
            AgentTask(agent_id="builder-1", prompt="Task 1"),
            AgentTask(agent_id="builder-2", prompt="Task 2"),
        ]

        results = await executor.execute_parallel(tasks)

        # Both should succeed
        assert results["builder-1"].success
        assert results["builder-2"].success

        # Verify concurrent execution (overlapping times)
        b1_start, b1_end = execution_times["builder-1"]
        b2_start, b2_end = execution_times["builder-2"]

        # If concurrent, one should start before the other ends
        assert b1_start < b2_end and b2_start < b1_end

    def test_partition_tasks_distributes_evenly(self) -> None:
        """Tasks are distributed evenly between builders."""
        tasks = ["Task A", "Task B", "Task C", "Task D"]
        partitioned = partition_tasks(tasks)

        builder1_tasks = [t for t in partitioned if t.agent_id == "builder-1"]
        builder2_tasks = [t for t in partitioned if t.agent_id == "builder-2"]

        assert len(builder1_tasks) == 2
        assert len(builder2_tasks) == 2


class TestReviewIterationWithFeedback:
    """Tests for review iteration with feedback."""

    @pytest.mark.asyncio
    async def test_review_incorporates_feedback(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Review feedback is incorporated into next iteration."""
        mock_client = AsyncMock()
        call_count = 0

        async def mock_execute(agent_id: str, prompt: str, callback: object) -> str:
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return "First attempt"
            elif call_count == 2:
                return "REJECTED: Add error handling"
            elif call_count == 3:
                # Verify feedback was incorporated
                assert "error handling" in prompt.lower()
                return "Second attempt with error handling"
            else:
                return "APPROVED: Good!"

        mock_client.execute_streaming.side_effect = mock_execute

        from teambot.orchestration.review_iterator import ReviewIterator

        iterator = ReviewIterator(mock_client, teambot_dir)
        result = await iterator.execute(
            stage=WorkflowStage.SPEC_REVIEW,
            work_agent="ba",
            review_agent="reviewer",
            context="Create specification",
        )

        assert result.status == ReviewStatus.APPROVED
        assert result.iterations_used == 2


class TestTimeoutEnforcement:
    """Tests for time limit enforcement."""

    @pytest.mark.asyncio
    async def test_timeout_stops_execution(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Execution stops when time limit is reached."""
        mock_client = AsyncMock()
        mock_client.execute_streaming.return_value = "APPROVED: Done."

        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=0,  # Immediate timeout
        )

        result = await loop.run(mock_client)

        assert result == ExecutionResult.TIMEOUT


class TestObjectiveFileFormats:
    """Tests for various objective file formats."""

    def test_parse_full_objective(self, objective_file: Path) -> None:
        """Full objective file is parsed correctly."""
        objective = parse_objective_file(objective_file)

        assert objective.title == "Implement User Authentication"
        assert len(objective.goals) == 3
        assert len(objective.success_criteria) == 3
        assert len(objective.constraints) == 2
        assert objective.context is not None

    def test_parse_minimal_objective(self, minimal_objective_file: Path) -> None:
        """Minimal objective file is parsed correctly."""
        objective = parse_objective_file(minimal_objective_file)

        assert objective.title == "My Task"
        assert len(objective.goals) == 1
        assert len(objective.success_criteria) == 1
        assert objective.constraints == []
        assert objective.context is None

    def test_parse_objective_with_completed_criteria(self, tmp_path: Path) -> None:
        """Objective with pre-completed criteria is parsed correctly."""
        content = """# Objective: Partial Progress

## Goals
1. Complete remaining work

## Success Criteria
- [x] First criterion done
- [x] Second criterion done
- [ ] Third criterion pending
"""
        obj_file = tmp_path / "partial.md"
        obj_file.write_text(content)

        objective = parse_objective_file(obj_file)

        completed = [c for c in objective.success_criteria if c.completed]
        pending = [c for c in objective.success_criteria if not c.completed]

        assert len(completed) == 2
        assert len(pending) == 1


class TestEndToEndScenarios:
    """End-to-end scenario tests."""

    @pytest.mark.asyncio
    async def test_complete_feature_implementation_scenario(
        self, tmp_path: Path
    ) -> None:
        """Simulate a complete feature implementation scenario."""
        # Create objective
        objective_content = """# Objective: Add User Profile Feature

## Goals
1. Create user profile page
2. Add profile editing capability
3. Implement avatar upload

## Success Criteria
- [ ] Profile page displays user information
- [ ] Users can edit their profile
- [ ] Avatar images can be uploaded

## Constraints
- Must work with existing authentication
- Maximum avatar size 5MB

## Context
The application uses React for frontend and Express for backend.
"""
        objective_file = tmp_path / "objectives" / "profile.md"
        objective_file.parent.mkdir(parents=True, exist_ok=True)
        objective_file.write_text(objective_content)

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create feature-specific directory with feature spec (no acceptance tests)
        # Feature name from "Add User Profile" -> "user-profile"
        feature_dir = teambot_dir / "user-profile"
        feature_dir.mkdir()
        artifacts_dir = feature_dir / "artifacts"
        artifacts_dir.mkdir()
        feature_spec = """# Feature Specification: User Profile

## Overview
Implements user profile functionality.

## Technical Design
Uses React components with Express API endpoints.
"""
        (artifacts_dir / "feature_spec.md").write_text(feature_spec)

        # Mock successful execution
        mock_client = AsyncMock()
        mock_client.execute_streaming.return_value = "APPROVED: Implementation complete."

        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        stages_visited: list[str] = []

        def on_progress(event: str, data: dict) -> None:
            if event == "stage_changed":
                stages_visited.append(data["stage"])

        result = await loop.run(mock_client, on_progress=on_progress)

        # Verify complete execution
        assert result == ExecutionResult.COMPLETE

        # Verify all major stages were visited
        expected_stages = ["SETUP", "SPEC", "PLAN", "IMPLEMENTATION", "TEST"]
        for stage in expected_stages:
            assert stage in stages_visited, f"Expected {stage} to be visited"

        # Verify state was saved in feature subdirectory
        state_file = loop.teambot_dir / "orchestration_state.json"
        assert state_file.exists()

    @pytest.mark.asyncio
    async def test_review_failure_scenario(self, tmp_path: Path) -> None:
        """Simulate a review failure after max iterations."""
        objective_content = """# Objective: Complex Feature

## Goals
1. Implement complex logic

## Success Criteria
- [ ] Logic is correct
"""
        objective_file = tmp_path / "objective.md"
        objective_file.write_text(objective_content)

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Mock rejection on all iterations
        mock_client = AsyncMock()
        mock_client.execute_streaming.return_value = "REJECTED: Not acceptable."

        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        result = await loop.run(mock_client)

        # Verify failure
        assert result == ExecutionResult.REVIEW_FAILED

        # Verify failure report was created in feature subdirectory
        failures_dir = loop.teambot_dir / "failures"
        assert failures_dir.exists()
        failure_reports = list(failures_dir.glob("*.md"))
        assert len(failure_reports) > 0
