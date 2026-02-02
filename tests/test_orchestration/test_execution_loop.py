"""Tests for ExecutionLoop (Code-First)."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from teambot.orchestration.execution_loop import (
    ExecutionLoop,
    ExecutionResult,
    STAGE_ORDER,
    REVIEW_STAGES,
)
from teambot.workflow.stages import WorkflowStage


class TestExecutionLoopInit:
    """Tests for ExecutionLoop initialization."""

    def test_init_parses_objective_file(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Initialization parses the objective file."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )
        assert loop.objective.title == "Implement User Authentication"

    def test_init_sets_max_hours(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Initialization sets max hours."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=4.0,
        )
        assert loop.time_manager.max_seconds == 4 * 3600

    def test_init_starts_at_setup_stage(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Initialization starts at SETUP stage."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )
        assert loop.current_stage == WorkflowStage.SETUP


class TestExecutionLoopRun:
    """Tests for ExecutionLoop.run() method."""

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client that approves all reviews."""
        client = AsyncMock()
        # Return work output, then approval for each stage
        client.execute_streaming.return_value = "APPROVED: Work completed successfully."
        return client

    @pytest.fixture
    def loop(self, objective_file: Path, teambot_dir: Path) -> ExecutionLoop:
        """Create ExecutionLoop instance."""
        return ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=8.0,
        )

    @pytest.mark.asyncio
    async def test_run_completes_all_stages(
        self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Run progresses through all stages to completion."""
        result = await loop.run(mock_sdk_client)
        assert result == ExecutionResult.COMPLETE
        assert loop.current_stage == WorkflowStage.COMPLETE

    @pytest.mark.asyncio
    async def test_run_calls_progress_callback(
        self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Run calls progress callback for stage changes."""
        progress_calls = []

        result = await loop.run(
            mock_sdk_client,
            on_progress=lambda e, d: progress_calls.append((e, d)),
        )

        assert result == ExecutionResult.COMPLETE
        stage_changes = [c for c in progress_calls if c[0] == "stage_changed"]
        assert len(stage_changes) > 0

    @pytest.mark.asyncio
    async def test_run_cancellation_returns_cancelled(
        self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Run returns CANCELLED when cancelled."""
        # Cancel immediately
        loop.cancel()

        result = await loop.run(mock_sdk_client)
        assert result == ExecutionResult.CANCELLED

    @pytest.mark.asyncio
    async def test_run_timeout_returns_timeout(
        self, objective_file: Path, teambot_dir: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Run returns TIMEOUT when time expires."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=0,  # Immediately expired
        )

        result = await loop.run(mock_sdk_client)
        assert result == ExecutionResult.TIMEOUT

    @pytest.mark.asyncio
    async def test_run_review_failure_returns_review_failed(
        self, loop: ExecutionLoop
    ) -> None:
        """Run returns REVIEW_FAILED when review fails."""
        # Create a client that always rejects
        mock_client = AsyncMock()
        mock_client.execute_streaming.return_value = "REJECTED: Not good enough."

        result = await loop.run(mock_client)
        assert result == ExecutionResult.REVIEW_FAILED


class TestExecutionLoopStatePersistence:
    """Tests for state persistence and resume."""

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client."""
        client = AsyncMock()
        client.execute_streaming.return_value = "APPROVED: Done."
        return client

    @pytest.mark.asyncio
    async def test_save_state_creates_file(
        self, objective_file: Path, teambot_dir: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Save state creates orchestration_state.json in feature directory."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        loop.cancel()
        await loop.run(mock_sdk_client)

        # State file is in feature-specific subdirectory
        state_file = loop.teambot_dir / "orchestration_state.json"
        assert state_file.exists()

    @pytest.mark.asyncio
    async def test_save_state_contains_required_fields(
        self, objective_file: Path, teambot_dir: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Saved state contains all required fields."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        loop.cancel()
        await loop.run(mock_sdk_client)

        # State file is in feature-specific subdirectory
        state_file = loop.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text())

        assert "objective_file" in state
        assert "current_stage" in state
        assert "elapsed_seconds" in state
        assert "status" in state

    def test_resume_loads_state(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Resume loads state from file in feature directory."""
        # Create feature subdirectory with state file
        # The objective file has title "Implement User Authentication" -> "user-authentication"
        feature_dir = teambot_dir / "user-authentication"
        feature_dir.mkdir(parents=True, exist_ok=True)

        state = {
            "objective_file": str(objective_file),
            "current_stage": "RESEARCH",
            "elapsed_seconds": 100.0,
            "max_seconds": 28800,
            "status": "paused",
            "stage_outputs": {},
        }
        state_file = feature_dir / "orchestration_state.json"
        state_file.write_text(json.dumps(state))

        loop = ExecutionLoop.resume(feature_dir, {})

        assert loop.current_stage == WorkflowStage.RESEARCH
        assert loop.time_manager._prior_elapsed == 100.0

    def test_resume_raises_if_no_state(self, teambot_dir: Path) -> None:
        """Resume raises ValueError if no state file."""
        with pytest.raises(ValueError, match="No orchestration state"):
            ExecutionLoop.resume(teambot_dir, {})

    def test_resume_restores_stage_outputs(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Resume restores stage outputs."""
        # Create feature subdirectory with state file
        feature_dir = teambot_dir / "user-authentication"
        feature_dir.mkdir(parents=True, exist_ok=True)

        state = {
            "objective_file": str(objective_file),
            "current_stage": "PLAN",
            "elapsed_seconds": 50.0,
            "max_seconds": 28800,
            "status": "paused",
            "stage_outputs": {
                "SPEC": "Feature specification content",
            },
        }
        state_file = feature_dir / "orchestration_state.json"
        state_file.write_text(json.dumps(state))

        loop = ExecutionLoop.resume(feature_dir, {})

        assert WorkflowStage.SPEC in loop.stage_outputs
        assert "Feature specification" in loop.stage_outputs[WorkflowStage.SPEC]

    @pytest.mark.asyncio
    async def test_save_state_status_cancelled(
        self, objective_file: Path, teambot_dir: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Saved state has status 'cancelled' when execution is cancelled."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        loop.cancel()
        result = await loop.run(mock_sdk_client)

        assert result == ExecutionResult.CANCELLED
        state_file = loop.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text())
        assert state["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_save_state_status_timeout(
        self, objective_file: Path, teambot_dir: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Saved state has status 'timeout' when execution times out."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=0,  # Immediately expired
        )

        result = await loop.run(mock_sdk_client)

        assert result == ExecutionResult.TIMEOUT
        state_file = loop.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text())
        assert state["status"] == "timeout"

    @pytest.mark.asyncio
    async def test_save_state_status_review_failed(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Saved state has status 'review_failed' when review fails."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        # Create a client that always rejects
        mock_client = AsyncMock()
        mock_client.execute_streaming.return_value = "REJECTED: Not good enough."

        result = await loop.run(mock_client)

        assert result == ExecutionResult.REVIEW_FAILED
        state_file = loop.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text())
        assert state["status"] == "review_failed"

    @pytest.mark.asyncio
    async def test_save_state_status_complete(
        self, objective_file: Path, teambot_dir: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Saved state has status 'complete' when execution completes."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        result = await loop.run(mock_sdk_client)

        assert result == ExecutionResult.COMPLETE
        state_file = loop.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text())
        assert state["status"] == "complete"

    @pytest.mark.asyncio
    async def test_save_state_status_error(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Saved state has status 'error' when execution raises an exception."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        # Create a client that raises an exception
        mock_client = AsyncMock()
        mock_client.execute_streaming.side_effect = RuntimeError("Test error")

        with pytest.raises(RuntimeError, match="Test error"):
            await loop.run(mock_client)

        state_file = loop.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text())
        assert state["status"] == "error"


class TestExecutionLoopStageProgression:
    """Tests for stage progression logic."""

    def test_get_next_stage_follows_order(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """_get_next_stage follows STAGE_ORDER."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        for i, stage in enumerate(STAGE_ORDER[:-1]):
            next_stage = loop._get_next_stage(stage)
            assert next_stage == STAGE_ORDER[i + 1]

    def test_get_next_stage_returns_complete_at_end(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """_get_next_stage returns COMPLETE for last stage."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        # POST_REVIEW -> COMPLETE
        assert loop._get_next_stage(WorkflowStage.POST_REVIEW) == WorkflowStage.COMPLETE
        # COMPLETE -> COMPLETE
        assert loop._get_next_stage(WorkflowStage.COMPLETE) == WorkflowStage.COMPLETE


class TestExecutionLoopContextBuilding:
    """Tests for context building."""

    def test_build_stage_context_includes_objective(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Context includes objective details."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        context = loop._build_stage_context(WorkflowStage.SPEC)

        assert "Implement User Authentication" in context
        assert "Goals" in context
        assert "Success Criteria" in context

    def test_build_stage_context_includes_stage_info(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Context includes stage information."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        context = loop._build_stage_context(WorkflowStage.SPEC)

        assert "Specification" in context
        assert "detailed feature specification" in context.lower()

    def test_build_stage_context_for_review_includes_work(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Review stage context includes work to review."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )
        loop.stage_outputs[WorkflowStage.SPEC] = "This is the spec content."

        context = loop._build_stage_context(WorkflowStage.SPEC_REVIEW)

        assert "Work to Review" in context
        assert "This is the spec content" in context


class TestExecutionLoopReviewOutputs:
    """Tests for review stage output storage."""

    @pytest.mark.asyncio
    async def test_review_stage_outputs_stored_in_state(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Review stage outputs are stored in orchestration_state.json."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        # Mock client that returns approval with output
        mock_client = AsyncMock()
        mock_client.execute_streaming.return_value = "APPROVED: Spec looks great!"

        result = await loop.run(mock_client)

        assert result == ExecutionResult.COMPLETE
        state_file = loop.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text())

        # Verify review stage outputs are in state
        stage_outputs = state.get("stage_outputs", {})
        assert "SPEC_REVIEW" in stage_outputs
        assert "APPROVED" in stage_outputs["SPEC_REVIEW"]

    @pytest.mark.asyncio
    async def test_all_review_stages_stored(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """All review stages have their outputs stored."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        mock_client = AsyncMock()
        mock_client.execute_streaming.return_value = "APPROVED: All good!"

        await loop.run(mock_client)

        state_file = loop.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text())
        stage_outputs = state.get("stage_outputs", {})

        # Check all review stages are stored
        for review_stage in REVIEW_STAGES:
            assert review_stage.name in stage_outputs, f"Missing output for {review_stage.name}"
