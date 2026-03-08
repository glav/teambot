"""Acceptance tests for Critical Failure Handling feature.

These tests validate the real implementation against acceptance scenarios.
Core logic is tested directly; selective mocking is used only for external
dependencies (SDK client, notifications).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from teambot.orchestration.artifact_validator import ArtifactValidator
from teambot.orchestration.execution_loop import ExecutionLoop, ExecutionResult
from teambot.orchestration.stage_config import StagesConfiguration
from teambot.workflow.stages import WorkflowStage


@pytest.mark.acceptance
class TestCriticalFailureAcceptance:
    """Acceptance tests for critical failure handling feature."""

    @pytest.fixture
    def objective_content(self) -> str:
        """Sample objective content."""
        return """# Objective: Test Feature

## Goals
1. Implement test feature

## Success Criteria
- [ ] Feature works
"""

    @pytest.fixture
    def objective_file(self, tmp_path: Path, objective_content: str) -> Path:
        """Create objective file."""
        obj_path = tmp_path / "objective.md"
        obj_path.write_text(objective_content, encoding="utf-8")
        return obj_path

    @pytest.fixture
    def teambot_dir(self, tmp_path: Path) -> Path:
        """Create .teambot directory structure."""
        dir_path = tmp_path / ".teambot"
        dir_path.mkdir()
        return dir_path

    @pytest.fixture
    def stages_config_with_plan_requirement(self) -> StagesConfiguration:
        """Create stages config requiring implementation_plan.md for IMPLEMENTATION."""
        from teambot.orchestration.stage_config import load_stages_config

        # Load defaults and clear all artifacts first
        config = load_stages_config()
        for stage_config in config.stages.values():
            stage_config.artifacts = []
            # Disable acceptance test stages for testing
            stage_config.is_acceptance_test_stage = False
            stage_config.requires_acceptance_tests_passed = False
        config.acceptance_test_stages = set()

        # Modify stage_order to skip ACCEPTANCE_TEST and POST_REVIEW
        # (they would fail without proper acceptance test setup)
        config.stage_order = [
            stage
            for stage in config.stage_order
            if stage not in (WorkflowStage.ACCEPTANCE_TEST, WorkflowStage.POST_REVIEW)
        ]

        # Add specific artifact requirement for IMPLEMENTATION
        config.stages[WorkflowStage.IMPLEMENTATION].artifacts = ["implementation_plan.md"]

        return config

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Mock SDK client that approves all work."""
        client = AsyncMock()
        client.execute_streaming.return_value = "VERIFIED_APPROVED: Work completed."
        return client

    # =========================================================================
    # AT-001: Missing Implementation Plan Halts IMPLEMENTATION Stage
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_001_missing_plan_halts_implementation_stage(
        self,
        objective_file: Path,
        teambot_dir: Path,
        stages_config_with_plan_requirement: StagesConfiguration,
        mock_sdk_client: AsyncMock,
    ) -> None:
        """AT-001: Workflow halts before agent execution when artifact missing."""
        # Setup: Create feature directory but NO implementation_plan.md
        feature_dir = teambot_dir / "test-feature"
        feature_dir.mkdir()
        (feature_dir / "artifacts").mkdir()
        # Note: implementation_plan.md is NOT created

        # Create ExecutionLoop with artifact requirement
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=8.0,
            stages_config=stages_config_with_plan_requirement,
        )

        # Track events
        progress_events: list[tuple[str, dict]] = []

        # Execute workflow
        result = await loop.run(
            mock_sdk_client,
            on_progress=lambda e, d: progress_events.append((e, d)),
        )

        # VERIFY: Workflow halts with CRITICAL_FAILURE
        assert result == ExecutionResult.CRITICAL_FAILURE

        # VERIFY: critical_failure event emitted
        failure_events = [e for e in progress_events if e[0] == "critical_failure"]
        assert len(failure_events) >= 1, "Expected critical_failure event to be emitted"

        # VERIFY: Event contains required information
        event_data = failure_events[0][1]
        assert "artifact" in event_data
        assert "stage" in event_data
        assert "recovery_steps" in event_data

        # VERIFY: No agent execution for IMPLEMENTATION stage
        impl_agent_calls = [
            e
            for e in progress_events
            if e[0] == "agent_running" and "IMPLEMENTATION" in str(e[1].get("task", ""))
        ]
        assert len(impl_agent_calls) == 0, "Agent should NOT run for IMPLEMENTATION"

    # =========================================================================
    # AT-002: Error Message Contains All Required Elements
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_002_error_message_contains_required_elements(
        self,
        objective_file: Path,
        teambot_dir: Path,
        stages_config_with_plan_requirement: StagesConfiguration,
        mock_sdk_client: AsyncMock,
    ) -> None:
        """AT-002: Error message contains artifact path, stage, and guidance."""
        # Setup: Create feature directory but NO implementation_plan.md
        feature_dir = teambot_dir / "test-feature"
        feature_dir.mkdir()
        (feature_dir / "artifacts").mkdir()

        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=8.0,
            stages_config=stages_config_with_plan_requirement,
        )

        progress_events: list[tuple[str, dict]] = []

        await loop.run(
            mock_sdk_client,
            on_progress=lambda e, d: progress_events.append((e, d)),
        )

        # Get critical_failure event
        failure_events = [e for e in progress_events if e[0] == "critical_failure"]
        assert len(failure_events) >= 1

        event_data = failure_events[0][1]

        # VERIFY: Artifact path present
        assert "artifact" in event_data
        artifact_path = event_data["artifact"]
        assert "implementation_plan.md" in artifact_path

        # VERIFY: Stage name present
        assert "stage" in event_data
        assert "IMPLEMENTATION" in event_data["stage"]

        # VERIFY: Recovery steps/guidance present
        assert "recovery_steps" in event_data
        recovery_steps = event_data["recovery_steps"]
        assert len(recovery_steps) > 0

        # VERIFY: Recovery guidance mentions SDD or manual creation
        all_steps = " ".join(recovery_steps).lower()
        assert "sdd" in all_steps or "create" in all_steps or "manually" in all_steps

    # =========================================================================
    # AT-003: Critical Failure Triggers Notification
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_003_critical_failure_triggers_notification_event(
        self,
        objective_file: Path,
        teambot_dir: Path,
        stages_config_with_plan_requirement: StagesConfiguration,
        mock_sdk_client: AsyncMock,
    ) -> None:
        """AT-003: critical_failure event emitted with correct payload."""
        # Setup
        feature_dir = teambot_dir / "test-feature"
        feature_dir.mkdir()
        (feature_dir / "artifacts").mkdir()

        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=8.0,
            stages_config=stages_config_with_plan_requirement,
        )

        received_events: list[tuple[str, dict]] = []

        await loop.run(
            mock_sdk_client,
            on_progress=lambda event_type, data: received_events.append((event_type, data)),
        )

        # VERIFY: critical_failure event was emitted
        critical_events = [e for e in received_events if e[0] == "critical_failure"]
        assert len(critical_events) >= 1, "critical_failure event should be emitted"

        # VERIFY: Payload structure
        payload = critical_events[0][1]
        assert "artifact" in payload, "Payload must contain artifact"
        assert "stage" in payload, "Payload must contain stage"
        assert "recovery_steps" in payload, "Payload must contain recovery_steps"

    # =========================================================================
    # AT-004: Orchestration State Persists Failure Reason
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_004_state_persists_failure_status(
        self,
        objective_file: Path,
        teambot_dir: Path,
        stages_config_with_plan_requirement: StagesConfiguration,
        mock_sdk_client: AsyncMock,
    ) -> None:
        """AT-004: orchestration_state.json contains failure status."""
        # Setup
        feature_dir = teambot_dir / "test-feature"
        feature_dir.mkdir()
        (feature_dir / "artifacts").mkdir()

        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=8.0,
            stages_config=stages_config_with_plan_requirement,
        )

        await loop.run(mock_sdk_client)

        # Read state file
        state_file = loop.teambot_dir / "orchestration_state.json"
        assert state_file.exists(), "orchestration_state.json should exist"

        state = json.loads(state_file.read_text(encoding="utf-8"))

        # VERIFY: Status is critical_failure
        assert state.get("status") == "critical_failure", (
            f"Expected status 'critical_failure', got '{state.get('status')}'"
        )

    # =========================================================================
    # AT-005: Resume Workflow After Artifact Provided
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_005_resume_succeeds_after_artifact_provided(
        self,
        objective_file: Path,
        teambot_dir: Path,
        stages_config_with_plan_requirement: StagesConfiguration,
        mock_sdk_client: AsyncMock,
    ) -> None:
        """AT-005: Workflow completes after missing artifact is created."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=8.0,
            stages_config=stages_config_with_plan_requirement,
        )

        # First run: should fail (artifact doesn't exist)
        result1 = await loop.run(mock_sdk_client)
        assert result1 == ExecutionResult.CRITICAL_FAILURE

        # NOW create the missing artifact in the CORRECT location
        # The loop creates teambot_dir/feature_name/artifacts/
        artifacts_dir = loop.teambot_dir / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        (artifacts_dir / "implementation_plan.md").write_text(
            "# Implementation Plan\n\n## Tasks\n1. Task 1",
            encoding="utf-8",
        )

        # Create new loop instance (simulating resume)
        loop2 = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=8.0,
            stages_config=stages_config_with_plan_requirement,
        )

        # Second run: should complete
        result2 = await loop2.run(mock_sdk_client)
        assert result2 == ExecutionResult.COMPLETE, (
            f"Expected COMPLETE after artifact provided, got {result2}"
        )

    # =========================================================================
    # AT-006: Existing Workflows With All Artifacts Pass Validation
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_006_workflow_passes_when_artifacts_exist(
        self,
        objective_file: Path,
        teambot_dir: Path,
        mock_sdk_client: AsyncMock,
    ) -> None:
        """AT-006: No regression - workflow completes when artifacts exist."""
        from teambot.orchestration.stage_config import load_stages_config

        # Use default config with no artifact requirements (backward compatible)
        # AND disable acceptance test stages that would fail
        config = load_stages_config()
        for stage_config in config.stages.values():
            stage_config.artifacts = []
            stage_config.is_acceptance_test_stage = False
            stage_config.requires_acceptance_tests_passed = False
        config.acceptance_test_stages = set()

        # Modify stage_order to skip ACCEPTANCE_TEST and POST_REVIEW
        config.stage_order = [
            stage
            for stage in config.stage_order
            if stage not in (WorkflowStage.ACCEPTANCE_TEST, WorkflowStage.POST_REVIEW)
        ]

        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=8.0,
            stages_config=config,
        )

        # Run workflow
        result = await loop.run(mock_sdk_client)

        # VERIFY: Workflow completes successfully
        assert result == ExecutionResult.COMPLETE
        assert loop.current_stage == WorkflowStage.COMPLETE

    # =========================================================================
    # AT-007: Unified Path Resolver Finds Artifacts in All Expected Locations
    # =========================================================================
    def test_at_007_path_resolver_finds_artifacts_in_multiple_locations(
        self,
        tmp_path: Path,
    ) -> None:
        """AT-007: Resolver checks all configured paths consistently."""
        from teambot.orchestration.stage_config import load_stages_config

        # Setup directory structure
        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create artifact in .agent-tracking/specs/ (preferred SDD spec location)
        specs_dir = tmp_path / ".agent-tracking" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "feature_spec.md").write_text(
            "# Feature Spec from .agent-tracking/specs",
            encoding="utf-8",
        )

        # Create artifact in .agent-tracking location
        agent_tracking = tmp_path / ".agent-tracking" / "research"
        agent_tracking.mkdir(parents=True)
        (agent_tracking / "research.md").write_text(
            "# Research from .agent-tracking",
            encoding="utf-8",
        )

        # Create validator
        config = load_stages_config()
        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=config,
            feature_name="test-feature",
        )

        # VERIFY: Finds feature_spec.md in .agent-tracking/specs location
        spec_path = validator.find_artifact("feature_spec.md")
        assert spec_path is not None, "Should find feature_spec.md in .agent-tracking/specs/"
        assert spec_path.exists()
        assert ".agent-tracking" in str(spec_path) and "specs" in str(spec_path)

        # VERIFY: Finds research.md in .agent-tracking location
        research_path = validator.find_artifact("research.md")
        assert research_path is not None, "Should find research.md in .agent-tracking/"
        assert research_path.exists()
        assert ".agent-tracking" in str(research_path)

        # VERIFY: Primary location takes precedence
        primary_dir = teambot_dir / "test-feature" / "artifacts"
        primary_dir.mkdir(parents=True)
        (primary_dir / "feature_spec.md").write_text(
            "# Feature Spec from PRIMARY",
            encoding="utf-8",
        )

        # Re-create validator to refresh paths
        validator2 = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=config,
            feature_name="test-feature",
        )

        spec_path2 = validator2.find_artifact("feature_spec.md")
        assert spec_path2 is not None
        # Primary location should be preferred
        assert "test-feature" in str(spec_path2) and "artifacts" in str(spec_path2)
