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
            stage="ACCEPTANCE_TEST",
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
            stage="ACCEPTANCE_TEST",
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
                    # prerequisite_artifacts = inputs required before the stage runs
                    prerequisite_artifacts=["implementation_plan.md"],
                    # artifacts = outputs produced by the stage (not used for pre-stage checks)
                    artifacts=[],
                ),
                WorkflowStage.IMPLEMENTATION: StageConfig(
                    name="Implementation",
                    description="Execute the plan",
                    work_agent="builder-1",
                    review_agent="reviewer",
                    prerequisite_artifacts=[],
                    artifacts=[],
                ),
                WorkflowStage.RESEARCH: StageConfig(
                    name="Research",
                    description="Research technical approach",
                    work_agent="builder-1",
                    review_agent=None,
                    # No prerequisites for research; it produces research.md as output
                    prerequisite_artifacts=[],
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
        """Returns list of prerequisite artifacts required before a stage from config."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        validator = ArtifactValidator(
            teambot_dir=tmp_path,
            stages_config=stages_config,
            feature_name="test-feature",
        )

        artifacts = validator.get_required_artifacts(WorkflowStage.PLAN)
        assert artifacts == ["implementation_plan.md"]

        # Stage with no prerequisite artifacts
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
                    prerequisites=["feature_spec.md"],
                ),
                WorkflowStage.RESEARCH: StageConfig(
                    name="Research",
                    description="Research technical approach",
                    work_agent="builder-1",
                    review_agent=None,
                    prerequisites=["research.md"],
                ),
                WorkflowStage.PLAN: StageConfig(
                    name="Plan",
                    description="Create implementation plan",
                    work_agent="pm",
                    review_agent="reviewer",
                    prerequisites=["implementation_plan.md"],
                ),
            },
            stage_order=[
                WorkflowStage.SPEC,
                WorkflowStage.RESEARCH,
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


class TestCrossFeatureIsolation:
    """Tests for cross-feature artifact isolation (glob pattern safety)."""

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
                    prerequisite_artifacts=["research.md"],
                ),
            },
            stage_order=[WorkflowStage.PLAN],
            work_to_review_mapping={},
        )

    def test_glob_filters_by_feature_name_research(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Glob patterns filter by feature name to prevent cross-feature contamination."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create research files for TWO different features
        research_dir = tmp_path / ".agent-tracking" / "research"
        research_dir.mkdir(parents=True)

        # Feature A's research (older)
        feature_a_file = research_dir / "20260305-feature-a-research.md"
        feature_a_file.write_text("# Feature A Research")
        feature_a_file.touch()  # Ensure it exists with timestamp

        # Feature B's research (newer - higher mtime)
        import time

        time.sleep(0.01)  # Small delay to ensure different mtime
        feature_b_file = research_dir / "20260305-feature-b-research.md"
        feature_b_file.write_text("# Feature B Research")
        feature_b_file.touch()

        # Validator for Feature A
        validator_a = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="feature-a",
        )

        # Should find Feature A's research, NOT Feature B's (even though B is newer)
        result_a = validator_a.find_artifact("research.md")
        assert result_a is not None
        assert "feature-a" in result_a.name
        assert "feature-b" not in result_a.name

        # Validator for Feature B
        validator_b = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="feature-b",
        )

        # Should find Feature B's research
        result_b = validator_b.find_artifact("research.md")
        assert result_b is not None
        assert "feature-b" in result_b.name
        assert "feature-a" not in result_b.name

    def test_glob_filters_by_feature_name_plan(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Glob patterns filter plan files by feature name."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create plan files for two features
        plans_dir = tmp_path / ".agent-tracking" / "plans"
        plans_dir.mkdir(parents=True)

        (plans_dir / "20260305-mobile-app-plan.instructions.md").write_text("# Mobile Plan")
        (plans_dir / "20260305-web-app-plan.instructions.md").write_text("# Web Plan")

        # Validator for mobile-app
        validator_mobile = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="mobile-app",
        )

        result_mobile = validator_mobile.find_artifact("implementation_plan.md")
        assert result_mobile is not None
        assert "mobile-app" in result_mobile.name
        assert "web-app" not in result_mobile.name

    def test_glob_filters_by_feature_name_spec(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Glob patterns filter spec files by feature name."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create spec files for two features
        specs_dir = tmp_path / "docs" / "feature-specs"
        specs_dir.mkdir(parents=True)

        (specs_dir / "user-authentication.md").write_text("# Auth Spec")
        (specs_dir / "user-profile.md").write_text("# Profile Spec")

        # Validator for user-authentication
        validator_auth = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="user-authentication",
        )

        result_auth = validator_auth.find_artifact("feature_spec.md")
        assert result_auth is not None
        assert "authentication" in result_auth.name
        assert "profile" not in result_auth.name

    def test_glob_returns_none_without_feature_name(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Glob fallback returns None when feature_name is not set (safety check)."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create a research file
        research_dir = tmp_path / ".agent-tracking" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "20260305-some-feature-research.md").write_text("# Research")

        # Validator WITHOUT feature_name
        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name=None,  # No feature name!
        )

        # Should NOT find artifact via glob (returns None for safety)
        result = validator.find_artifact("research.md")
        assert result is None

    def test_glob_prefers_most_recent_within_same_feature(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """When multiple files match same feature, returns most recent."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create multiple research files for SAME feature
        research_dir = tmp_path / ".agent-tracking" / "research"
        research_dir.mkdir(parents=True)

        import time

        # Older file
        older_file = research_dir / "20260301-my-feature-research.md"
        older_file.write_text("# Old Research")
        older_file.touch()

        time.sleep(0.01)

        # Newer file
        newer_file = research_dir / "20260305-my-feature-research.md"
        newer_file.write_text("# New Research")
        newer_file.touch()

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        result = validator.find_artifact("research.md")
        assert result is not None
        assert "20260305" in result.name  # Should find newer file


class TestSearchOrderAndPrecedence:
    """Tests for artifact search order and precedence rules."""

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
                    prerequisite_artifacts=["research.md", "implementation_plan.md"],
                ),
            },
            stage_order=[WorkflowStage.PLAN],
            work_to_review_mapping={},
        )

    def test_search_order_prioritizes_feature_artifacts(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Search order: 1. Feature artifacts, 2. .agent-tracking subdirs."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create research.md in BOTH locations with different content
        # Primary location (should win)
        feature_dir = teambot_dir / "my-feature" / "artifacts"
        feature_dir.mkdir(parents=True)
        (feature_dir / "research.md").write_text("# Primary Research")

        # Fallback location (should be ignored)
        research_dir = tmp_path / ".agent-tracking" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "research.md").write_text("# Fallback Research")

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        result = validator.find_artifact("research.md")
        assert result is not None
        # Should find in feature artifacts first
        assert "my-feature/artifacts" in result.as_posix()
        # Verify content to confirm correct file
        assert "Primary Research" in result.read_text()

    def test_search_locations_documented_order(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """_get_search_locations returns paths in documented precedence order."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        locations = validator._get_search_locations("research.md")

        # First location should be feature artifacts directory
        assert locations[0] == teambot_dir / "my-feature" / "artifacts" / "research.md"

        # Second location should be .agent-tracking/research/
        assert any(".agent-tracking/research" in str(loc) for loc in locations)

    def test_case_sensitivity_matches_filesystem(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Artifact names respect filesystem case sensitivity."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create artifact with specific case
        feature_dir = teambot_dir / "my-feature" / "artifacts"
        feature_dir.mkdir(parents=True)
        (feature_dir / "Research.md").write_text("# Research")  # Capital R

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        # Search with lowercase (common case)
        result = validator.find_artifact("research.md")

        # On case-insensitive filesystems (Windows, macOS), this may find it
        # On case-sensitive filesystems (Linux), this will NOT find it
        # We document this behavior rather than enforce a specific outcome
        import platform

        if platform.system() == "Windows" or platform.system() == "Darwin":
            # Case-insensitive filesystem - may find it
            if result:
                assert result.exists()
        else:
            # Case-sensitive filesystem (Linux) - should NOT find it with wrong case
            assert result is None

        # Searching with correct case should ALWAYS work
        correct_result = validator.find_artifact("Research.md")  # Exact case
        assert correct_result is not None
        assert correct_result.exists()

    def test_precedence_with_multiple_artifact_types(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Precedence works consistently across different artifact types."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        # Create artifacts in feature dir (primary)
        feature_dir = teambot_dir / "my-feature" / "artifacts"
        feature_dir.mkdir(parents=True)
        (feature_dir / "research.md").write_text("# Feature Research")
        (feature_dir / "implementation_plan.md").write_text("# Feature Plan")

        # Create same artifacts in fallback locations
        research_dir = tmp_path / ".agent-tracking" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "20260305-my-feature-research.md").write_text("# Fallback Research")

        plans_dir = tmp_path / ".agent-tracking" / "plans"
        plans_dir.mkdir(parents=True)
        (plans_dir / "20260305-my-feature-plan.instructions.md").write_text("# Fallback Plan")

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        # Both should find in feature artifacts (primary location)
        research_result = validator.find_artifact("research.md")
        plan_result = validator.find_artifact("implementation_plan.md")

        assert research_result is not None
        assert plan_result is not None
        assert "my-feature/artifacts" in research_result.as_posix()
        assert "my-feature/artifacts" in plan_result.as_posix()

    def test_path_calculation_stable_across_directory_depths(
        self, tmp_path: Path, stages_config: StagesConfiguration
    ) -> None:
        """Path calculation works correctly regardless of directory depth."""
        from teambot.orchestration.artifact_validator import ArtifactValidator

        # Test case 1: Normal depth (.teambot/feature)
        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()

        validator = ArtifactValidator(
            teambot_dir=teambot_dir,
            stages_config=stages_config,
            feature_name="my-feature",
        )

        # Verify _agent_tracking_dir resolves to repository root
        assert validator._agent_tracking_dir == tmp_path / ".agent-tracking"

        # Test case 2: Deeper nesting (simulating worktree or nested project)
        nested_teambot_dir = tmp_path / "subproject" / ".teambot"
        nested_teambot_dir.mkdir(parents=True)

        nested_validator = ArtifactValidator(
            teambot_dir=nested_teambot_dir,
            stages_config=stages_config,
            feature_name="nested-feature",
        )

        # Should resolve relative to the base teambot dir's parent
        assert nested_validator._agent_tracking_dir == tmp_path / "subproject" / ".agent-tracking"
