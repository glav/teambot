"""Tests for ExecutionLoop (Code-First)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from teambot.orchestration.execution_loop import (
    REVIEW_STAGES,
    ExecutionLoop,
    ExecutionResult,
)
from teambot.workflow.stages import WorkflowStage


class TestExecutionLoopInit:
    """Tests for ExecutionLoop initialization."""

    def test_init_parses_objective_file(self, objective_file: Path, teambot_dir: Path) -> None:
        """Initialization parses the objective file."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )
        assert loop.objective.title == "Implement User Authentication"

    def test_init_sets_max_hours(self, objective_file: Path, teambot_dir: Path) -> None:
        """Initialization sets max hours."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=4.0,
        )
        assert loop.time_manager.max_seconds == 4 * 3600

    def test_init_starts_at_setup_stage(self, objective_file: Path, teambot_dir: Path) -> None:
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
        client.execute_streaming.return_value = "VERIFIED_APPROVED: Work completed successfully."
        return client

    @pytest.fixture
    def loop(self, objective_file: Path, teambot_dir_with_spec: Path) -> ExecutionLoop:
        """Create ExecutionLoop instance with feature spec."""
        return ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir_with_spec,
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
    async def test_run_review_failure_returns_review_failed(self, loop: ExecutionLoop) -> None:
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
        client.execute_streaming.return_value = "VERIFIED_APPROVED: Done."
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

    def test_resume_loads_state(self, objective_file: Path, teambot_dir: Path) -> None:
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

    def test_resume_restores_stage_outputs(self, objective_file: Path, teambot_dir: Path) -> None:
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

    def test_resume_from_root_dir_finds_feature_state(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Resume from root .teambot/ dir discovers feature subdirectory state."""
        feature_dir = teambot_dir / "user-authentication"
        feature_dir.mkdir(parents=True, exist_ok=True)

        state = {
            "objective_file": str(objective_file),
            "current_stage": "IMPLEMENTATION",
            "elapsed_seconds": 200.0,
            "max_seconds": 28800,
            "status": "error",
            "feature_name": "user-authentication",
            "stage_outputs": {"SPEC": "Spec content"},
            "acceptance_tests_passed": True,
            "acceptance_test_iterations": 2,
            "acceptance_test_history": [
                {"iteration": 1, "passed": 0, "failed": 3},
                {"iteration": 2, "passed": 3, "failed": 0},
            ],
        }
        state_file = feature_dir / "orchestration_state.json"
        state_file.write_text(json.dumps(state))

        # Pass root teambot dir (not feature dir) — this is what the CLI does
        loop = ExecutionLoop.resume(teambot_dir, {})

        assert loop.current_stage == WorkflowStage.IMPLEMENTATION
        assert loop.time_manager._prior_elapsed == 200.0
        assert WorkflowStage.SPEC in loop.stage_outputs
        # Verify acceptance test fields are restored
        assert loop.acceptance_tests_passed is True
        assert loop.acceptance_test_iterations == 2
        assert len(loop._acceptance_test_history) == 2
        assert loop._acceptance_test_history[0]["iteration"] == 1
        assert loop._acceptance_test_history[1]["passed"] == 3

    def test_resume_from_root_dir_picks_latest(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Resume from root dir picks the most recently modified state file."""
        # Create two feature directories with state files
        old_dir = teambot_dir / "old-feature"
        old_dir.mkdir(parents=True, exist_ok=True)
        old_state = {
            "objective_file": str(objective_file),
            "current_stage": "SPEC",
            "elapsed_seconds": 10.0,
            "max_seconds": 28800,
            "status": "paused",
            "stage_outputs": {},
        }
        old_state_file = old_dir / "orchestration_state.json"
        old_state_file.write_text(json.dumps(old_state))

        new_dir = teambot_dir / "user-authentication"
        new_dir.mkdir(parents=True, exist_ok=True)
        new_state = {
            "objective_file": str(objective_file),
            "current_stage": "PLAN",
            "elapsed_seconds": 50.0,
            "max_seconds": 28800,
            "status": "paused",
            "stage_outputs": {},
        }
        new_state_file = new_dir / "orchestration_state.json"
        new_state_file.write_text(json.dumps(new_state))

        # Explicitly set mtimes to ensure old_state_file is older than new_state_file
        current_time = time.time()
        os.utime(old_state_file, (current_time - 100, current_time - 100))
        os.utime(new_state_file, (current_time, current_time))

        loop = ExecutionLoop.resume(teambot_dir, {})
        assert loop.current_stage == WorkflowStage.PLAN

    def test_resume_restores_acceptance_test_fields(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Resume restores acceptance test fields from state."""
        feature_dir = teambot_dir / "user-authentication"
        feature_dir.mkdir(parents=True, exist_ok=True)

        # Create state with acceptance test data
        state = {
            "objective_file": str(objective_file),
            "current_stage": "POST_REVIEW",
            "elapsed_seconds": 300.0,
            "max_seconds": 28800,
            "status": "paused",
            "stage_outputs": {},
            "acceptance_tests_passed": True,
            "acceptance_test_iterations": 3,
            "acceptance_test_history": [
                {"iteration": 1, "passed": 2, "failed": 1, "total": 3, "all_passed": False},
                {"iteration": 2, "passed": 2, "failed": 1, "total": 3, "all_passed": False},
                {"iteration": 3, "passed": 3, "failed": 0, "total": 3, "all_passed": True},
            ],
        }
        state_file = feature_dir / "orchestration_state.json"
        state_file.write_text(json.dumps(state))

        loop = ExecutionLoop.resume(feature_dir, {})

        # Assert acceptance test fields are properly restored
        assert loop.acceptance_tests_passed is True
        assert loop.acceptance_test_iterations == 3
        assert len(loop._acceptance_test_history) == 3
        assert loop._acceptance_test_history[0]["iteration"] == 1
        assert loop._acceptance_test_history[0]["all_passed"] is False
        assert loop._acceptance_test_history[2]["iteration"] == 3
        assert loop._acceptance_test_history[2]["all_passed"] is True

    def test_resume_defaults_acceptance_test_fields_when_missing(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Resume sets default values for acceptance test fields if not in state."""
        feature_dir = teambot_dir / "user-authentication"
        feature_dir.mkdir(parents=True, exist_ok=True)

        # Create state without acceptance test fields (old state file format)
        state = {
            "objective_file": str(objective_file),
            "current_stage": "IMPLEMENTATION",
            "elapsed_seconds": 100.0,
            "max_seconds": 28800,
            "status": "paused",
            "stage_outputs": {},
        }
        state_file = feature_dir / "orchestration_state.json"
        state_file.write_text(json.dumps(state))

        loop = ExecutionLoop.resume(feature_dir, {})

        # Assert acceptance test fields have default values
        assert loop.acceptance_tests_passed is False
        assert loop.acceptance_test_iterations == 0
        assert loop._acceptance_test_history == []

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
        self, objective_file: Path, teambot_dir_with_spec: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Saved state has status 'complete' when execution completes."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir_with_spec,
        )

        result = await loop.run(mock_sdk_client)

        assert result == ExecutionResult.COMPLETE
        state_file = loop.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text())
        assert state["status"] == "complete"

    @pytest.mark.asyncio
    async def test_save_state_status_error(self, objective_file: Path, teambot_dir: Path) -> None:
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

    def test_get_next_stage_follows_order(self, objective_file: Path, teambot_dir: Path) -> None:
        """_get_next_stage follows the configured stage order."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        # Use the loop's actual stage order from config
        stage_order = loop.stages_config.stage_order
        for i, stage in enumerate(stage_order[:-1]):
            next_stage = loop._get_next_stage(stage)
            assert next_stage == stage_order[i + 1]

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
        self, objective_file: Path, teambot_dir_with_spec: Path
    ) -> None:
        """Review stage outputs are stored in orchestration_state.json."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir_with_spec,
        )

        # Mock client that returns approval with output
        mock_client = AsyncMock()
        mock_client.execute_streaming.return_value = "VERIFIED_APPROVED: Spec looks great!"

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
        self, objective_file: Path, teambot_dir_with_spec: Path
    ) -> None:
        """All review stages have their outputs stored."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir_with_spec,
        )

        mock_client = AsyncMock()
        mock_client.execute_streaming.return_value = "VERIFIED_APPROVED: All good!"

        await loop.run(mock_client)

        state_file = loop.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text())
        stage_outputs = state.get("stage_outputs", {})

        # Check all review stages are stored
        for review_stage in REVIEW_STAGES:
            assert review_stage.name in stage_outputs, f"Missing output for {review_stage.name}"


class TestPromptTemplateLoading:
    """Tests for prompt template loading functionality."""

    def test_load_prompt_template_when_file_exists(
        self, objective_file: Path, teambot_dir: Path, tmp_path: Path
    ) -> None:
        """Prompt template content is loaded when file exists."""
        # Create a prompt template file
        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        prompt_file = prompt_dir / "sdd.1-create-feature-spec.prompt.md"
        prompt_file.write_text("# Create Feature Spec\n\nYou are creating a spec...")

        # Create stages.yaml pointing to this prompt
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SPEC:
    name: Specification
    description: Create detailed feature specification
    work_agent: ba
    review_agent: reviewer
    prompt_template: .agent/commands/sdd/sdd.1-create-feature-spec.prompt.md
    include_objective: true
stage_order:
  - SPEC
work_to_review_mapping: {}
""")

        loop = ExecutionLoop(
            objective_path=objective_file,
            config={"stages_config": str(stages_yaml)},
            teambot_dir=teambot_dir,
        )

        context = loop._build_stage_context(WorkflowStage.SPEC)

        assert "# Create Feature Spec" in context
        assert "You are creating a spec..." in context

    def test_context_excludes_objective_when_include_objective_false(
        self, objective_file: Path, teambot_dir: Path, tmp_path: Path
    ) -> None:
        """Objective is not included when include_objective is false."""
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    name: Setup
    description: Initialize project
    work_agent: pm
    review_agent: null
    prompt_template: null
    include_objective: false
stage_order:
  - SETUP
work_to_review_mapping: {}
""")

        loop = ExecutionLoop(
            objective_path=objective_file,
            config={"stages_config": str(stages_yaml)},
            teambot_dir=teambot_dir,
        )

        context = loop._build_stage_context(WorkflowStage.SETUP)

        # Objective should not be in context
        assert "# Objective:" not in context
        assert "Implement User Authentication" not in context
        # But stage info should still be there
        assert "Setup" in context

    def test_context_includes_objective_by_default(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Objective is included when include_objective is not specified (default True)."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        context = loop._build_stage_context(WorkflowStage.SPEC)

        assert "# Objective:" in context
        assert "Implement User Authentication" in context

    def test_load_prompt_template_returns_none_when_file_missing(
        self, objective_file: Path, teambot_dir: Path, tmp_path: Path
    ) -> None:
        """Returns None when prompt template file doesn't exist."""
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SPEC:
    name: Specification
    description: Create detailed feature specification
    work_agent: ba
    review_agent: reviewer
    prompt_template: nonexistent/prompt.md
    include_objective: true
stage_order:
  - SPEC
work_to_review_mapping: {}
""")

        loop = ExecutionLoop(
            objective_path=objective_file,
            config={"stages_config": str(stages_yaml)},
            teambot_dir=teambot_dir,
        )

        context = loop._build_stage_context(WorkflowStage.SPEC)

        # Should not have the nonexistent prompt, but should have objective
        assert "nonexistent/prompt.md" not in context
        assert "# Objective:" in context


class TestFeatureSpecFinding:
    """Tests for finding and loading feature specifications."""

    def test_find_feature_spec_from_artifacts(
        self, objective_file: Path, teambot_dir: Path, sample_feature_spec_content: str
    ) -> None:
        """Feature spec is loaded from artifacts directory."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        # Create artifacts directory with feature spec
        feature_dir = teambot_dir / loop.feature_name
        feature_dir.mkdir(exist_ok=True)
        artifacts_dir = feature_dir / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        (artifacts_dir / "feature_spec.md").write_text(sample_feature_spec_content)

        spec_content = loop._find_feature_spec_content()

        assert spec_content is not None
        assert "User Authentication" in spec_content

    def test_find_feature_spec_from_docs_case_insensitive(
        self, objective_file: Path, teambot_dir: Path, sample_feature_spec_content: str
    ) -> None:
        """Feature spec is found with case-insensitive matching."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        # Create docs/feature-specs directory with various case variations
        docs_dir = teambot_dir.parent / "docs" / "feature-specs"
        docs_dir.mkdir(parents=True)

        # Feature name is "user-authentication" from objective
        # Test with uppercase variation
        (docs_dir / "User-Authentication-Spec.md").write_text(sample_feature_spec_content)

        spec_content = loop._find_feature_spec_content()

        assert spec_content is not None
        assert "User Authentication" in spec_content

    def test_find_feature_spec_from_docs_hyphen_variations(
        self, objective_file: Path, teambot_dir: Path, sample_feature_spec_content: str
    ) -> None:
        """Feature spec matching ignores hyphens."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        # Create docs/feature-specs directory
        docs_dir = teambot_dir.parent / "docs" / "feature-specs"
        docs_dir.mkdir(parents=True)

        # Feature name is "user-authentication"
        # Test with different hyphenation
        (docs_dir / "userauthentication-spec.md").write_text(sample_feature_spec_content)

        spec_content = loop._find_feature_spec_content()

        assert spec_content is not None
        assert "User Authentication" in spec_content

    def test_find_feature_spec_prefers_artifacts_over_docs(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Artifacts directory is checked before docs directory."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        # Create both artifacts and docs specs with different content
        feature_dir = teambot_dir / loop.feature_name
        feature_dir.mkdir(exist_ok=True)
        artifacts_dir = feature_dir / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        (artifacts_dir / "feature_spec.md").write_text("Artifacts spec content")

        docs_dir = teambot_dir.parent / "docs" / "feature-specs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "user-authentication.md").write_text("Docs spec content")

        spec_content = loop._find_feature_spec_content()

        assert spec_content == "Artifacts spec content"

    def test_find_feature_spec_returns_none_when_not_found(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Returns None when no feature spec is found."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        spec_content = loop._find_feature_spec_content()

        assert spec_content is None


class TestParallelGroupExecution:
    """Tests for parallel stage group execution (TDD)."""

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client that approves all reviews."""
        client = AsyncMock()
        client.execute_streaming.return_value = "VERIFIED_APPROVED: Work completed successfully."
        return client

    @pytest.fixture
    def loop_with_parallel_groups(
        self, objective_file: Path, teambot_dir_with_spec: Path
    ) -> ExecutionLoop:
        """Create ExecutionLoop with parallel groups configured."""
        from teambot.orchestration.stage_config import (
            load_stages_config,
        )

        # Load default config and ensure parallel groups exist
        config = load_stages_config()
        assert len(config.parallel_groups) > 0, "Expected parallel groups from stages.yaml"

        return ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir_with_spec,
            max_hours=8.0,
            stages_config=config,
        )

    def test_get_parallel_group_for_stage_returns_group(
        self, loop_with_parallel_groups: ExecutionLoop
    ) -> None:
        """Returns parallel group when stage is first in group."""
        # RESEARCH is first stage in post_spec_review group
        group = loop_with_parallel_groups._get_parallel_group_for_stage(WorkflowStage.RESEARCH)

        assert group is not None
        assert group.name == "post_spec_review"
        assert WorkflowStage.RESEARCH in group.stages
        assert WorkflowStage.TEST_STRATEGY in group.stages

    def test_get_parallel_group_for_stage_returns_none_for_non_first(
        self, loop_with_parallel_groups: ExecutionLoop
    ) -> None:
        """Returns None for stages that are not first in parallel group."""
        # TEST_STRATEGY is second in the group, should not trigger parallel execution
        group = loop_with_parallel_groups._get_parallel_group_for_stage(WorkflowStage.TEST_STRATEGY)

        assert group is None

    def test_get_parallel_group_for_stage_returns_none_for_non_parallel(
        self, loop_with_parallel_groups: ExecutionLoop
    ) -> None:
        """Returns None for stages not in any parallel group."""
        group = loop_with_parallel_groups._get_parallel_group_for_stage(WorkflowStage.SPEC)

        assert group is None

    @pytest.mark.asyncio
    async def test_execute_parallel_group_runs_all_stages(
        self, loop_with_parallel_groups: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Parallel group execution runs all stages in the group."""
        loop_with_parallel_groups.sdk_client = mock_sdk_client
        loop_with_parallel_groups.review_iterator = None  # Not needed for work stages

        group = loop_with_parallel_groups.stages_config.parallel_groups[0]
        progress_events: list[tuple[str, dict]] = []

        success = await loop_with_parallel_groups._execute_parallel_group(
            group=group,
            on_progress=lambda e, d: progress_events.append((e, d)),
        )

        assert success is True
        # Both stages should have outputs
        assert WorkflowStage.RESEARCH in loop_with_parallel_groups.stage_outputs
        assert WorkflowStage.TEST_STRATEGY in loop_with_parallel_groups.stage_outputs

    @pytest.mark.asyncio
    async def test_execute_parallel_group_reports_progress(
        self, loop_with_parallel_groups: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Parallel group execution sends progress events."""
        loop_with_parallel_groups.sdk_client = mock_sdk_client

        group = loop_with_parallel_groups.stages_config.parallel_groups[0]
        progress_events: list[tuple[str, dict]] = []

        await loop_with_parallel_groups._execute_parallel_group(
            group=group,
            on_progress=lambda e, d: progress_events.append((e, d)),
        )

        event_types = [e[0] for e in progress_events]
        assert "parallel_group_start" in event_types
        assert "parallel_group_complete" in event_types

    @pytest.mark.asyncio
    async def test_execute_parallel_group_handles_failure(
        self, loop_with_parallel_groups: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Parallel group allows all stages to complete even if one fails."""
        # Make RESEARCH fail
        call_count = 0

        async def fail_then_succeed(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First call (RESEARCH)
                raise RuntimeError("Simulated failure")
            return "VERIFIED_APPROVED: Work completed."

        mock_sdk_client.execute_streaming.side_effect = fail_then_succeed
        loop_with_parallel_groups.sdk_client = mock_sdk_client

        group = loop_with_parallel_groups.stages_config.parallel_groups[0]
        progress_events: list[tuple[str, dict]] = []

        success = await loop_with_parallel_groups._execute_parallel_group(
            group=group,
            on_progress=lambda e, d: progress_events.append((e, d)),
        )

        # Overall should fail, but both stages should have been attempted
        assert success is False
        # Check that group status tracks failure
        assert loop_with_parallel_groups.parallel_group_status.get("post_spec_review") is not None

    @pytest.mark.asyncio
    async def test_run_executes_parallel_group_and_skips_to_plan(
        self, loop_with_parallel_groups: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Run loop executes parallel group and skips to PLAN stage."""
        # Start from SPEC_REVIEW (which completes, then triggers parallel group)
        loop_with_parallel_groups.current_stage = WorkflowStage.SPEC_REVIEW

        # Track stage changes
        stage_changes: list[str] = []

        def track_progress(event: str, data: dict) -> None:
            if event == "stage_changed":
                stage_changes.append(data["stage"])
            elif event == "parallel_group_start":
                stage_changes.append(f"PARALLEL_START:{data['group']}")
            elif event == "parallel_group_complete":
                stage_changes.append(f"PARALLEL_END:{data['group']}")

        result = await loop_with_parallel_groups.run(
            mock_sdk_client,
            on_progress=track_progress,
        )

        assert result == ExecutionResult.COMPLETE

        # Verify parallel group was triggered (RESEARCH triggers it)
        assert "PARALLEL_START:post_spec_review" in stage_changes
        assert "PARALLEL_END:post_spec_review" in stage_changes

        # After parallel group, should be at PLAN (not through sequential stages)
        assert "PLAN" in stage_changes


class TestStatePersistenceWithParallelGroups:
    """Tests for state persistence with parallel group status (TDD)."""

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client."""
        client = AsyncMock()
        client.execute_streaming.return_value = "VERIFIED_APPROVED: Work completed successfully."
        return client

    @pytest.fixture
    def loop_with_parallel_groups(
        self, objective_file: Path, teambot_dir_with_spec: Path
    ) -> ExecutionLoop:
        """Create ExecutionLoop with parallel groups configured."""
        from teambot.orchestration.stage_config import load_stages_config

        config = load_stages_config()
        return ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir_with_spec,
            max_hours=8.0,
            stages_config=config,
        )

    def test_save_state_includes_parallel_group_status(
        self, loop_with_parallel_groups: ExecutionLoop
    ) -> None:
        """Save state includes parallel_group_status field."""
        # Set up some parallel group status
        loop_with_parallel_groups.parallel_group_status = {
            "post_spec_review": {
                "stages": {
                    "RESEARCH": {"status": "completed", "error": None},
                    "TEST_STRATEGY": {"status": "in_progress", "error": None},
                }
            }
        }

        loop_with_parallel_groups._save_state()

        state_file = loop_with_parallel_groups.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text())

        assert "parallel_group_status" in state
        pgs = state["parallel_group_status"]["post_spec_review"]["stages"]
        assert pgs["RESEARCH"]["status"] == "completed"
        assert pgs["TEST_STRATEGY"]["status"] == "in_progress"

    def test_resume_loads_parallel_group_status(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Resume loads parallel_group_status from saved state."""
        # Create feature directory and state file
        feature_dir = teambot_dir / "user-authentication"
        feature_dir.mkdir(parents=True, exist_ok=True)

        state_file = feature_dir / "orchestration_state.json"
        state_file.write_text(
            json.dumps(
                {
                    "objective_file": str(objective_file),
                    "current_stage": "PLAN",
                    "elapsed_seconds": 100,
                    "max_seconds": 28800,
                    "status": "in_progress",
                    "stage_outputs": {},
                    "parallel_group_status": {
                        "post_spec_review": {
                            "stages": {
                                "RESEARCH": {"status": "completed", "error": None},
                                "TEST_STRATEGY": {"status": "completed", "error": None},
                            }
                        }
                    },
                }
            )
        )

        loop = ExecutionLoop.resume(teambot_dir, {})

        assert loop.parallel_group_status == {
            "post_spec_review": {
                "stages": {
                    "RESEARCH": {"status": "completed", "error": None},
                    "TEST_STRATEGY": {"status": "completed", "error": None},
                }
            }
        }

    def test_resume_backward_compat_missing_parallel_status(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """Old state files without parallel_group_status load correctly."""
        # Create feature directory and state file WITHOUT parallel_group_status
        feature_dir = teambot_dir / "user-authentication"
        feature_dir.mkdir(parents=True, exist_ok=True)

        state_file = feature_dir / "orchestration_state.json"
        state_file.write_text(
            json.dumps(
                {
                    "objective_file": str(objective_file),
                    "current_stage": "RESEARCH",
                    "elapsed_seconds": 50,
                    "max_seconds": 28800,
                    "status": "in_progress",
                    "stage_outputs": {},
                    # NO parallel_group_status field - old format
                }
            )
        )

        loop = ExecutionLoop.resume(teambot_dir, {})

        # Should default to empty dict for backward compatibility
        assert loop.parallel_group_status == {}

    @pytest.mark.asyncio
    async def test_resume_mid_parallel_group_skips_completed_stages(
        self, objective_file: Path, teambot_dir_with_spec: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Resume mid-parallel-group only re-runs incomplete stages."""
        from teambot.orchestration.stage_config import load_stages_config

        # Create state where RESEARCH is complete but TEST_STRATEGY is not
        feature_dir = teambot_dir_with_spec / "user-authentication"
        feature_dir.mkdir(parents=True, exist_ok=True)
        (feature_dir / "artifacts").mkdir(exist_ok=True)

        state_file = feature_dir / "orchestration_state.json"
        state_file.write_text(
            json.dumps(
                {
                    "objective_file": str(objective_file),
                    "current_stage": "RESEARCH",  # Still at first stage of parallel group
                    "elapsed_seconds": 100,
                    "max_seconds": 28800,
                    "status": "in_progress",
                    "stage_outputs": {"RESEARCH": "Research completed."},
                    "parallel_group_status": {
                        "post_spec_review": {
                            "stages": {
                                "RESEARCH": {"status": "completed", "error": None},
                                # TEST_STRATEGY not present = not completed
                            }
                        }
                    },
                }
            )
        )

        loop = ExecutionLoop.resume(teambot_dir_with_spec, {})
        loop.stages_config = load_stages_config()

        # Check that filter_incomplete_stages correctly identifies TEST_STRATEGY
        group = loop.stages_config.parallel_groups[0]
        incomplete = loop._filter_incomplete_stages(group)

        assert len(incomplete) == 1
        assert WorkflowStage.TEST_STRATEGY in incomplete
        assert WorkflowStage.RESEARCH not in incomplete  # Already completed


class TestOrchestrationLifecycleEvents:
    """Tests for orchestration lifecycle event emission."""

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client that approves all reviews."""
        client = AsyncMock()
        client.execute_streaming.return_value = "VERIFIED_APPROVED: Work completed successfully."
        return client

    @pytest.fixture
    def loop(self, objective_file: Path, teambot_dir_with_spec: Path) -> ExecutionLoop:
        """Create ExecutionLoop instance with feature spec."""
        return ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir_with_spec,
            max_hours=8.0,
        )

    @pytest.mark.asyncio
    async def test_emits_started_event_at_run_entry(
        self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Emits orchestration_started at run() entry."""
        progress_calls: list[tuple[str, dict]] = []

        await loop.run(
            mock_sdk_client,
            on_progress=lambda e, d: progress_calls.append((e, d)),
        )

        # First event should be orchestration_started
        started_events = [c for c in progress_calls if c[0] == "orchestration_started"]
        assert len(started_events) == 1
        assert started_events[0][0] == "orchestration_started"

    @pytest.mark.asyncio
    async def test_started_event_includes_objective_name(
        self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Started event includes objective_name from objective."""
        progress_calls: list[tuple[str, dict]] = []

        await loop.run(
            mock_sdk_client,
            on_progress=lambda e, d: progress_calls.append((e, d)),
        )

        started_events = [c for c in progress_calls if c[0] == "orchestration_started"]
        assert len(started_events) == 1
        data = started_events[0][1]
        assert "objective_name" in data
        # Should have a non-empty objective name
        assert data["objective_name"]

    @pytest.mark.asyncio
    async def test_started_event_includes_objective_path(
        self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Started event includes objective_path."""
        progress_calls: list[tuple[str, dict]] = []

        await loop.run(
            mock_sdk_client,
            on_progress=lambda e, d: progress_calls.append((e, d)),
        )

        started_events = [c for c in progress_calls if c[0] == "orchestration_started"]
        data = started_events[0][1]
        assert "objective_path" in data
        assert data["objective_path"] is not None

    @pytest.mark.asyncio
    async def test_emits_completed_event_on_success(
        self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Emits orchestration_completed on successful completion."""
        progress_calls: list[tuple[str, dict]] = []

        result = await loop.run(
            mock_sdk_client,
            on_progress=lambda e, d: progress_calls.append((e, d)),
        )

        assert result == ExecutionResult.COMPLETE
        completed_events = [c for c in progress_calls if c[0] == "orchestration_completed"]
        assert len(completed_events) == 1
        data = completed_events[0][1]
        assert data["status"] == "complete"

    @pytest.mark.asyncio
    async def test_completed_event_includes_duration(
        self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Completed event includes duration_seconds."""
        progress_calls: list[tuple[str, dict]] = []

        await loop.run(
            mock_sdk_client,
            on_progress=lambda e, d: progress_calls.append((e, d)),
        )

        completed_events = [c for c in progress_calls if c[0] == "orchestration_completed"]
        data = completed_events[0][1]
        assert "duration_seconds" in data
        # Duration should be a non-negative number
        assert data["duration_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_completed_event_on_cancellation(
        self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """Emits orchestration_completed with cancelled status."""
        progress_calls: list[tuple[str, dict]] = []

        # Cancel immediately
        loop.cancel()

        result = await loop.run(
            mock_sdk_client,
            on_progress=lambda e, d: progress_calls.append((e, d)),
        )

        assert result == ExecutionResult.CANCELLED
        completed_events = [c for c in progress_calls if c[0] == "orchestration_completed"]
        assert len(completed_events) == 1
        data = completed_events[0][1]
        assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_completed_event_on_timeout(
        self, objective_file: Path, teambot_dir: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Emits orchestration_completed with timeout status."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=0,  # Immediately expired
        )
        progress_calls: list[tuple[str, dict]] = []

        result = await loop.run(
            mock_sdk_client,
            on_progress=lambda e, d: progress_calls.append((e, d)),
        )

        assert result == ExecutionResult.TIMEOUT
        completed_events = [c for c in progress_calls if c[0] == "orchestration_completed"]
        assert len(completed_events) == 1
        data = completed_events[0][1]
        assert data["status"] == "timeout"

    @pytest.mark.asyncio
    async def test_lifecycle_events_order(
        self, loop: ExecutionLoop, mock_sdk_client: AsyncMock
    ) -> None:
        """orchestration_started comes before completed."""
        progress_calls: list[tuple[str, dict]] = []

        await loop.run(
            mock_sdk_client,
            on_progress=lambda e, d: progress_calls.append((e, d)),
        )

        # Find indices of lifecycle events
        started_idx = next(
            i for i, c in enumerate(progress_calls) if c[0] == "orchestration_started"
        )
        completed_idx = next(
            i for i, c in enumerate(progress_calls) if c[0] == "orchestration_completed"
        )

        # Started should come before completed
        assert started_idx < completed_idx
        # Started should be first event
        assert started_idx == 0
