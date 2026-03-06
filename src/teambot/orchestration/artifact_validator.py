"""Artifact validation for file-based orchestration.

Validates that prerequisite artifacts exist before stage execution,
checking multiple possible locations for artifact files.

Note: The 'artifacts' field on StageConfig lists outputs produced by a stage.
      The 'prerequisite_artifacts' field lists inputs required before a stage runs.
      This module validates prerequisite_artifacts (pre-stage checks only).
"""

from __future__ import annotations

import logging
from pathlib import Path

from teambot.orchestration.exceptions import MissingArtifactError
from teambot.orchestration.stage_config import StagesConfiguration
from teambot.workflow.stages import WorkflowStage

logger = logging.getLogger(__name__)


class ArtifactValidator:
    """Validates prerequisite artifacts exist before stage execution.

    Checks that files listed in StageConfig.prerequisites are present
    before a stage begins. These are distinct from StageConfig.artifacts,
    which are files *produced by* the stage (outputs).

    Only validates 'prerequisite_artifacts' (inputs required before a stage runs),
    not 'artifacts' (outputs produced by a stage).

    Search order:
    1. .teambot/{feature}/artifacts/{artifact_name} (exact match)
    2. .agent-tracking/plans/ (exact match for *plan*.md)
    3. .agent-tracking/research/ (exact match for *research*.md)
    4. .agent-tracking/test-strategies/ (exact match for *test_strategy*.md)
    5. .agent-tracking/specs/ (exact match for *spec*.md)
    6. Glob patterns in .agent-tracking subdirectories (handles dated filenames):
       - .agent-tracking/research/*research*.md
       - .agent-tracking/plans/*plan*.md
       - .agent-tracking/test-strategies/*test*strategy*.md
       - .agent-tracking/specs/*.md

    Note: Glob patterns return the most recently modified file when multiple matches exist.
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
                logger.debug(f"Found artifact '{artifact_name}' at exact path: {location}")
                return location

        # If not found with exact name, try glob patterns in .agent-tracking subdirectories
        glob_result = self._find_artifact_with_glob(artifact_name)
        if glob_result:
            logger.debug(
                f"Found artifact '{artifact_name}' via glob pattern: {glob_result} "
                f"(feature: {self.feature_name})"
            )
            return glob_result

        logger.debug(f"Artifact '{artifact_name}' not found (feature: {self.feature_name})")
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
            # Check .agent-tracking/specs (preferred SDD spec location)
            locations.append(self._agent_tracking_dir / "specs" / artifact_name)

        return locations

    def _find_artifact_with_glob(self, artifact_name: str) -> Path | None:
        """Find artifact using glob patterns in .agent-tracking subdirectories.

        This handles cases where prompts create dated files like:
        - YYYYMMDD-{name}-research.md instead of research.md
        - YYYYMMDD-{name}-plan.instructions.md instead of implementation_plan.md
        - {name}.md instead of feature_spec.md

        IMPORTANT: When multiple features exist, glob patterns include feature_name
        to prevent cross-feature contamination. Returns None if feature_name is not
        set to maintain safety (cannot safely glob without risk of wrong feature match).

        Args:
            artifact_name: Name of the artifact file (e.g., "research.md")

        Returns:
            Path to the most recent matching file, or None if not found
        """
        # Safety check: Cannot safely use glob without feature name (risk of cross-contamination)
        if not self.feature_name:
            return None

        artifact_lower = artifact_name.lower()
        glob_patterns: list[tuple[Path, str]] = []

        # Map artifact names to .agent-tracking subdirectories and patterns
        # CRITICAL: Include feature_name in patterns to prevent cross-feature contamination
        if "research" in artifact_lower:
            # Look for files containing both feature name and "research"
            pattern = f"*{self.feature_name}*research*.md"
            glob_patterns.append((self._agent_tracking_dir / "research", pattern))

        if "plan" in artifact_lower or "implementation_plan" in artifact_lower:
            # Look for files containing both feature name and "plan"
            pattern = f"*{self.feature_name}*plan*.md"
            glob_patterns.append((self._agent_tracking_dir / "plans", pattern))

        if "test_strategy" in artifact_lower or "test-strategy" in artifact_lower:
            # Look for files containing both feature name and "strategy"
            pattern = f"*{self.feature_name}*strategy*.md"
            glob_patterns.append((self._agent_tracking_dir / "test-strategies", pattern))

        if "spec" in artifact_lower or "feature_spec" in artifact_lower:
            # Look for spec files containing feature name in .agent-tracking/specs/
            # Note: SPEC prompts create files like {name}.md, not feature_spec.md
            pattern = f"*{self.feature_name}*.md"
            glob_patterns.append((self._agent_tracking_dir / "specs", pattern))

        # Search each location with its pattern
        candidates = []
        for directory, pattern in glob_patterns:
            if directory.exists():
                matches = list(directory.glob(pattern))
                candidates.extend(matches)

        # Return the most recent file if multiple matches found
        if candidates:
            # Sort by modification time, newest first
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return candidates[0]

        return None

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
