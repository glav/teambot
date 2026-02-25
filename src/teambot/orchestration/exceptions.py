"""Orchestration exceptions for critical failure handling.

These exceptions provide actionable error messages when orchestration
encounters critical failures that require immediate halt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MissingArtifactError(Exception):
    """Raised when a required artifact is missing for a stage.

    This is a critical failure that should halt the workflow immediately.
    The error includes recovery steps to help users resolve the issue.

    Attributes:
        artifact_path: Path to the missing artifact file
        stage: Name of the workflow stage that requires the artifact
        recovery_steps: List of actionable steps to resolve the issue
    """

    artifact_path: Path
    stage: str
    recovery_steps: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize the exception with a formatted message."""
        # Ensure artifact_path is a Path object
        if isinstance(self.artifact_path, str):
            self.artifact_path = Path(self.artifact_path)
        # Initialize the Exception base class with our message
        super().__init__(str(self))

    def __str__(self) -> str:
        """Format an actionable error message."""
        lines = [
            "",
            "❌ Critical Failure: Missing required artifact",
            "",
            f"Stage: {self.stage}",
            f"Expected artifact: {self.artifact_path}",
            "",
        ]

        if self.recovery_steps:
            lines.append("To resolve:")
            for i, step in enumerate(self.recovery_steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """Return a string representation for debugging."""
        return (
            f"MissingArtifactError("
            f"artifact_path={self.artifact_path!r}, "
            f"stage={self.stage!r}, "
            f"recovery_steps={self.recovery_steps!r})"
        )
