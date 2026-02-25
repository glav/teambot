"""Tests for artifact validation and MissingArtifactError (TDD).

These tests are critical safety mechanisms for file-based orchestration.
TDD approach: Tests written first, implementation follows.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from teambot.orchestration.exceptions import MissingArtifactError
from teambot.orchestration.stage_config import StageConfig, StagesConfiguration
from teambot.workflow.stages import WorkflowStage


class TestMissingArtifactError:
    """Tests for MissingArtifactError exception."""

    def test_error_has_artifact_path(self) -> None:
        """Exception stores the missing artifact path."""
        error = MissingArtifactError(
            artifact_path=Path(".teambot/feature/artifacts/implementation_plan.md"),
            stage="PLAN",
            recovery_steps=["Create the plan manually"],
        )
        assert error.artifact_path == Path(".teambot/feature/artifacts/implementation_plan.md")

    def test_error_has_stage_name(self) -> None:
        """Exception stores which stage required the artifact."""
        error = MissingArtifactError(
            artifact_path=Path("some/path.md"),
            stage="IMPLEMENTATION",
            recovery_steps=["Fix it"],
        )
        assert error.stage == "IMPLEMENTATION"

    def test_error_has_recovery_steps(self) -> None:
        """Exception includes actionable recovery steps."""
        steps = [
            "Run /sdd:5-task-planner-for-feature to create the plan",
            "Or manually create the file at the expected path",
        ]
        error = MissingArtifactError(
            artifact_path=Path("path.md"),
            stage="PLAN",
            recovery_steps=steps,
        )
        assert error.recovery_steps == steps
        assert len(error.recovery_steps) == 2

    def test_error_message_is_actionable(self) -> None:
        """String representation includes all context for user action."""
        error = MissingArtifactError(
            artifact_path=Path(".teambot/user-auth/artifacts/implementation_plan.md"),
            stage="PLAN",
            recovery_steps=[
                "Run /sdd:5-task-planner-for-feature",
                "Create file manually at expected path",
            ],
        )
        message = str(error)

        # Must include the artifact path (check key parts, platform-agnostic)
        assert "implementation_plan.md" in message
        assert "user-auth" in message
        # Must include the stage name
        assert "PLAN" in message
        # Must include recovery steps
        assert "/sdd:5-task-planner-for-feature" in message
        assert "Create file manually" in message
        # Should be formatted for readability
        assert "Critical" in message or "Missing" in message

    def test_error_inherits_from_exception(self) -> None:
        """MissingArtifactError is a proper Exception subclass."""
        error = MissingArtifactError(
            artifact_path=Path("test.md"),
            stage="TEST",
            recovery_steps=["Step 1"],
        )
        assert isinstance(error, Exception)

    def test_error_can_be_raised_and_caught(self) -> None:
        """Exception can be raised and caught in try/except."""
        with pytest.raises(MissingArtifactError) as exc_info:
            raise MissingArtifactError(
                artifact_path=Path("missing.md"),
                stage="SPEC",
                recovery_steps=["Create the spec"],
            )

        assert exc_info.value.stage == "SPEC"
        assert exc_info.value.artifact_path == Path("missing.md")

    def test_error_with_empty_recovery_steps(self) -> None:
        """Exception handles empty recovery steps gracefully."""
        error = MissingArtifactError(
            artifact_path=Path("file.md"),
            stage="SETUP",
            recovery_steps=[],
        )
        # Should not crash when converting to string
        message = str(error)
        assert "SETUP" in message

    def test_error_with_path_object_and_string(self) -> None:
        """Exception accepts Path objects for artifact_path."""
        error = MissingArtifactError(
            artifact_path=Path("/absolute/path/to/file.md"),
            stage="TEST",
            recovery_steps=["Do something"],
        )
        assert isinstance(error.artifact_path, Path)
        # Use as_posix() for cross-platform comparison
        assert error.artifact_path.as_posix() == "/absolute/path/to/file.md"


class TestArtifactValidator:
    """Tests for ArtifactValidator class."""

    @pytest.fixture
    def stages_config(self) -> StagesConfiguration:
        """Create a minimal stages configuration for testing."""
        return StagesConfiguration(
            stages={
                WorkflowStage.PLAN: StageConfig(
                    name="Plan",
                    description="Create implementation plan",
                    work_agent="pm",
                    review_agent="reviewer",
                    artifacts=["implementation_plan.md"],
                ),
                WorkflowStage.IMPLEMENTATION: StageConfig(
                    name="Implementation",
                    description="Execute the plan",
                    work_agent="builder-1",
                    review_agent="reviewer",
                    artifacts=[],
                ),
                WorkflowStage.RESEARCH: StageConfig(
                    name="Research",
                    description="Research technical approach",
                    work_agent="builder-1",
                    review_agent=None,
                    artifacts=["research.md"],
                ),
            },
            stage_order=[
                WorkflowStage.PLAN,
                WorkflowStage.IMPLEMENTATION,
                WorkflowStage.RESEARCH,
            ],
            work_to_review_mapping={},
        )

    def test_validate_passes_when_artifact_exists(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Validation passes if artifact file exists."""
        # Import here to allow TDD red phase
        from teambot.orchestration.artifact_validator import ArtifactValidator

        # Create the artifact file
        feature_dir = tmp_path / "test-feature"
        artifacts_dir = feature_dir / "artifacts"
        artifacts_dir.mkdir(parents=True)
        (artifacts_dir / "implementation_plan.md").write_text("# Plan")

        validator = ArtifactValidator(
            teambot_dir=tmp_path,
            stages_config=stages_config,
            feature_name="test-feature",
        )

        # Should not raise
        result = validator.validate_artifact("implementation_plan.md", WorkflowStage.PLAN)
        assert result is not None
        assert result.exists()

    def test_validate_raises_when_artifact_missing(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Validation raises MissingArtifactError if artifact missing."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        validator = ArtifactValidator(
            teambot_dir=tmp_path,
            stages_config=stages_config,
            feature_name="test-feature",
        )

        with pytest.raises(MissingArtifactError) as exc_info:
            validator.validate_artifact("implementation_plan.md", WorkflowStage.PLAN)

        assert exc_info.value.stage == "PLAN"
        assert "implementation_plan.md" in str(exc_info.value.artifact_path)

    def test_validate_checks_multiple_locations(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Validator checks fallback locations for artifacts."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        # Create artifact in fallback location (.agent-tracking/plans/)
        # The validator looks at teambot_dir.parent / ".agent-tracking"
        # So if teambot_dir is tmp_path/.teambot, it looks at tmp_path/.agent-tracking
        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        agent_tracking = tmp_path / ".agent-tracking" / "plans"
        agent_tracking.mkdir(parents=True)
        (agent_tracking / "implementation_plan.md").write_text("# Plan")

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="test-feature",
        )

        # Should find in fallback location
        result = validator.find_artifact("implementation_plan.md")
        assert result is not None
        assert result.exists()

    def test_validate_returns_actual_path_found(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Validator returns the path where artifact was found."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        # Create artifact in primary location
        feature_dir = tmp_path / "test-feature" / "artifacts"
        feature_dir.mkdir(parents=True)
        expected_path = feature_dir / "research.md"
        expected_path.write_text("# Research")

        validator = ArtifactValidator(
            teambot_dir=tmp_path,
            stages_config=stages_config,
            feature_name="test-feature",
        )

        result = validator.validate_artifact("research.md", WorkflowStage.RESEARCH)
        assert result == expected_path

    def test_get_required_artifacts_for_stage(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Returns list of artifacts required for a stage from config."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        validator = ArtifactValidator(
            teambot_dir=tmp_path,
            stages_config=stages_config,
            feature_name="test-feature",
        )

        artifacts = validator.get_required_artifacts(WorkflowStage.PLAN)
        assert artifacts == ["implementation_plan.md"]

        # Stage with no artifacts
        artifacts = validator.get_required_artifacts(WorkflowStage.IMPLEMENTATION)
        assert artifacts == []

    def test_validate_all_for_stage_checks_each_artifact(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """validate_all_for_stage checks all required artifacts."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        # Create the required artifact
        feature_dir = tmp_path / "test-feature" / "artifacts"
        feature_dir.mkdir(parents=True)
        (feature_dir / "implementation_plan.md").write_text("# Plan")

        validator = ArtifactValidator(
            teambot_dir=tmp_path,
            stages_config=stages_config,
            feature_name="test-feature",
        )

        # Should pass - all artifacts exist
        result = validator.validate_all_for_stage(WorkflowStage.PLAN)
        assert "implementation_plan.md" in result
        assert result["implementation_plan.md"].exists()

    def test_validate_all_raises_on_first_missing(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """validate_all_for_stage raises on first missing artifact."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        validator = ArtifactValidator(
            teambot_dir=tmp_path,
            stages_config=stages_config,
            feature_name="test-feature",
        )

        with pytest.raises(MissingArtifactError):
            validator.validate_all_for_stage(WorkflowStage.PLAN)

    def test_error_includes_recovery_steps(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """MissingArtifactError includes actionable recovery steps."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        validator = ArtifactValidator(
            teambot_dir=tmp_path,
            stages_config=stages_config,
            feature_name="test-feature",
        )

        with pytest.raises(MissingArtifactError) as exc_info:
            validator.validate_artifact("implementation_plan.md", WorkflowStage.PLAN)

        # Should have recovery steps
        assert len(exc_info.value.recovery_steps) > 0
        # Recovery steps should be actionable (mention what to do)
        steps_text = " ".join(exc_info.value.recovery_steps)
        assert "create" in steps_text.lower() or "run" in steps_text.lower()


class TestArtifactPathResolution:
    """Tests for artifact path resolution across locations (Phase 2)."""

    @pytest.fixture
    def stages_config(self) -> StagesConfiguration:
        """Create a stages configuration with various artifact types."""
        return StagesConfiguration(
            stages={
                WorkflowStage.SPEC: StageConfig(
                    name="Spec",
                    description="Create specification",
                    work_agent="ba",
                    review_agent="reviewer",
                    artifacts=["feature_spec.md"],
                ),
                WorkflowStage.RESEARCH: StageConfig(
                    name="Research",
                    description="Research technical approach",
                    work_agent="builder-1",
                    review_agent=None,
                    artifacts=["research.md"],
                ),
                WorkflowStage.TEST_STRATEGY: StageConfig(
                    name="Test Strategy",
                    description="Define test strategy",
                    work_agent="builder-1",
                    review_agent=None,
                    artifacts=["test_strategy.md"],
                ),
                WorkflowStage.PLAN: StageConfig(
                    name="Plan",
                    description="Create implementation plan",
                    work_agent="pm",
                    review_agent="reviewer",
                    artifacts=["implementation_plan.md"],
                ),
            },
            stage_order=[
                WorkflowStage.SPEC,
                WorkflowStage.RESEARCH,
                WorkflowStage.TEST_STRATEGY,
                WorkflowStage.PLAN,
            ],
            work_to_review_mapping={},
        )

    def test_finds_artifact_in_feature_artifacts_dir(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Finds artifact in .teambot/{feature}/artifacts/."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        # Create teambot directory structure
        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create artifact in primary location
        feature_dir = teambot_dir / "my-feature" / "artifacts"
        feature_dir.mkdir(parents=True)
        (feature_dir / "feature_spec.md").write_text("# Spec")

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        result = validator.find_artifact("feature_spec.md")
        assert result is not None
        assert result == feature_dir / "feature_spec.md"

    def test_finds_spec_in_docs_feature_specs(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Falls back to docs/feature-specs/ for spec artifacts."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        # Create teambot directory (but NO artifact in primary location)
        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create artifact in fallback location
        docs_dir = tmp_path / "docs" / "feature-specs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "feature_spec.md").write_text("# Feature Spec")

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        result = validator.find_artifact("feature_spec.md")
        assert result is not None
        assert "docs/feature-specs" in result.as_posix()

    def test_finds_research_in_agent_tracking(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Falls back to .agent-tracking/research/ for research docs."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create in .agent-tracking/research/
        research_dir = tmp_path / ".agent-tracking" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "research.md").write_text("# Research")

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        result = validator.find_artifact("research.md")
        assert result is not None
        assert ".agent-tracking/research" in result.as_posix()

    def test_prioritizes_feature_dir_over_fallback(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Feature-specific location takes precedence over fallbacks."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create artifact in BOTH locations
        # Primary location
        feature_dir = teambot_dir / "my-feature" / "artifacts"
        feature_dir.mkdir(parents=True)
        (feature_dir / "implementation_plan.md").write_text("# Primary Plan")

        # Fallback location
        plans_dir = tmp_path / ".agent-tracking" / "plans"
        plans_dir.mkdir(parents=True)
        (plans_dir / "implementation_plan.md").write_text("# Fallback Plan")

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        result = validator.find_artifact("implementation_plan.md")
        assert result is not None
        # Should find primary location first
        assert "my-feature/artifacts" in result.as_posix()

    def test_handles_implementation_plan_locations(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Checks .agent-tracking/plans/ for implementation_plan.md."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Only create in .agent-tracking/plans/
        plans_dir = tmp_path / ".agent-tracking" / "plans"
        plans_dir.mkdir(parents=True)
        (plans_dir / "implementation_plan.md").write_text("# Plan")

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        result = validator.find_artifact("implementation_plan.md")
        assert result is not None
        assert ".agent-tracking/plans" in result.as_posix()

    def test_handles_test_strategy_locations(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Checks .agent-tracking/test-strategies/ for test_strategy.md."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create in .agent-tracking/test-strategies/
        strategy_dir = tmp_path / ".agent-tracking" / "test-strategies"
        strategy_dir.mkdir(parents=True)
        (strategy_dir / "test_strategy.md").write_text("# Test Strategy")

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        result = validator.find_artifact("test_strategy.md")
        assert result is not None
        assert ".agent-tracking/test-strategies" in result.as_posix()

    def test_returns_none_when_artifact_not_found(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Returns None when artifact cannot be found in any location."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        result = validator.find_artifact("nonexistent.md")
        assert result is None
