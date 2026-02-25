"""Artifact validation for file-based orchestration.

Validates that prerequisite artifacts exist before stage execution,
checking multiple possible locations for artifact files.

Note: The 'artifacts' field on StageConfig lists outputs produced by a stage.
      The 'prerequisite_artifacts' field lists inputs required before a stage runs.
      This module validates prerequisite_artifacts (pre-stage checks only).
"""

from __future__ import annotations

from pathlib import Path

from teambot.orchestration.exceptions import MissingArtifactError
from teambot.orchestration.stage_config import StagesConfiguration
from teambot.workflow.stages import WorkflowStage


class ArtifactValidator:
    """Validates prerequisite artifacts exist before stage execution.

    Checks multiple locations for artifacts to handle path mismatches
    between where agents write and where stages expect to find files.

    Only validates 'prerequisite_artifacts' (inputs required before a stage runs),
    not 'artifacts' (outputs produced by a stage).

    Search order:
    1. .teambot/{feature}/artifacts/{artifact_name}
    2. .agent-tracking/plans/ (for *plan*.md)
    3. .agent-tracking/research/ (for *research*.md)
    4. .agent-tracking/test-strategies/ (for *test_strategy*.md)
    5. docs/feature-specs/ (for *spec*.md)
    """

    def __init__(
        self,
        teambot_dir: Path,
        stages_config: StagesConfiguration,
        feature_name: str | None = None,
    ):
        """Initialize the artifact validator.

        Args:
            teambot_dir: Base .teambot directory path
            stages_config: Stage configuration with artifact requirements
            feature_name: Feature name for feature-specific artifact paths
        """
        self.teambot_dir = Path(teambot_dir)
        self.stages_config = stages_config
        self.feature_name = feature_name

        # Compute base paths
        self._primary_artifacts_dir = (
            self.teambot_dir / feature_name / "artifacts" if feature_name else None
        )
        self._agent_tracking_dir = self.teambot_dir.parent / ".agent-tracking"

    def get_required_artifacts(self, stage: WorkflowStage) -> list[str]:
        """Get list of prerequisite artifact filenames required before a stage runs.

        These are artifacts that must exist before the stage can execute (inputs),
        distinct from the 'artifacts' field which lists outputs produced by the stage.

        Args:
            stage: The workflow stage to check

        Returns:
            List of artifact filenames required before the stage can run
        """
        stage_config = self.stages_config.stages.get(stage)
        if not stage_config:
            return []
        return stage_config.prerequisite_artifacts

    def find_artifact(self, artifact_name: str) -> Path | None:
        """Find artifact in possible locations.

        Args:
            artifact_name: Name of the artifact file to find

        Returns:
            Path to the artifact if found, None otherwise
        """
        search_locations = self._get_search_locations(artifact_name)

        for location in search_locations:
            if location.exists():
                return location

        return None

    def _get_search_locations(self, artifact_name: str) -> list[Path]:
        """Get ordered list of locations to search for an artifact.

        Args:
            artifact_name: Name of the artifact file

        Returns:
            List of paths to check, in priority order
        """
        locations: list[Path] = []
        artifact_lower = artifact_name.lower()

        # 1. Primary location: .teambot/{feature}/artifacts/
        if self._primary_artifacts_dir:
            locations.append(self._primary_artifacts_dir / artifact_name)

        # 2. Fallback locations based on artifact type
        if "plan" in artifact_lower:
            locations.append(self._agent_tracking_dir / "plans" / artifact_name)

        if "research" in artifact_lower:
            locations.append(self._agent_tracking_dir / "research" / artifact_name)

        if "test_strategy" in artifact_lower or "test-strategy" in artifact_lower:
            locations.append(self._agent_tracking_dir / "test-strategies" / artifact_name)

        if "spec" in artifact_lower:
            # Check both docs/feature-specs and .agent-tracking/specs
            locations.append(self.teambot_dir.parent / "docs" / "feature-specs" / artifact_name)
            locations.append(self._agent_tracking_dir / "specs" / artifact_name)

        return locations

    def validate_artifact(self, artifact_name: str, stage: WorkflowStage) -> Path:
        """Validate that a specific artifact exists.

        Args:
            artifact_name: Name of the artifact file to validate
            stage: The workflow stage that requires the artifact

        Returns:
            Path to the found artifact

        Raises:
            MissingArtifactError: If the artifact cannot be found
        """
        artifact_path = self.find_artifact(artifact_name)

        if artifact_path is None:
            # Build the expected primary path for error message
            if self._primary_artifacts_dir:
                expected_path = self._primary_artifacts_dir / artifact_name
            else:
                expected_path = self.teambot_dir / "artifacts" / artifact_name

            raise MissingArtifactError(
                artifact_path=expected_path,
                stage=stage.name,
                recovery_steps=self._get_recovery_steps(artifact_name, stage),
            )

        return artifact_path

    def validate_all_for_stage(self, stage: WorkflowStage) -> dict[str, Path]:
        """Validate all prerequisite artifacts exist before a stage runs.

        Args:
            stage: The workflow stage to validate

        Returns:
            Dict mapping artifact names to their found paths

        Raises:
            MissingArtifactError: If any prerequisite artifact is missing
        """
        required = self.get_required_artifacts(stage)
        found: dict[str, Path] = {}

        for artifact_name in required:
            path = self.validate_artifact(artifact_name, stage)
            found[artifact_name] = path

        return found

    def _get_recovery_steps(self, artifact_name: str, stage: WorkflowStage) -> list[str]:
        """Generate recovery steps for a missing artifact.

        Args:
            artifact_name: Name of the missing artifact
            stage: Stage that requires the artifact

        Returns:
            List of actionable recovery steps
        """
        artifact_lower = artifact_name.lower()
        steps: list[str] = []

        # Suggest running the appropriate SDD command
        if "plan" in artifact_lower:
            steps.append("Run /sdd:5-task-planner-for-feature to create the plan")
        elif "research" in artifact_lower:
            steps.append("Run /sdd:3-research-feature to create research document")
        elif "test_strategy" in artifact_lower or "test-strategy" in artifact_lower:
            steps.append("Run /sdd:4-determine-test-strategy to create test strategy")
        elif "spec" in artifact_lower:
            steps.append("Run /sdd:1-create-feature-spec to create the specification")
        else:
            steps.append(f"Create the required artifact: {artifact_name}")

        # Always suggest manual creation as fallback
        if self._primary_artifacts_dir:
            expected_path = self._primary_artifacts_dir / artifact_name
        else:
            expected_path = self.teambot_dir / "artifacts" / artifact_name

        steps.append(f"Or manually create the file at: {expected_path}")

        return steps
