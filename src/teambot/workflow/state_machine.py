"""Workflow state machine for managing stage transitions."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from teambot.workflow.stages import (
    WorkflowStage,
    can_skip_stage,
    get_next_stages,
    get_stage_metadata,
)

logger = logging.getLogger(__name__)


@dataclass
class StageHistory:
    """History entry for a stage transition."""

    stage: WorkflowStage
    started_at: datetime
    completed_at: datetime | None = None
    skipped: bool = False
    artifacts: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class WorkflowState:
    """Current state of the workflow."""

    current_stage: WorkflowStage
    started_at: datetime
    history: list[StageHistory] = field(default_factory=list)
    objective: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            "current_stage": self.current_stage.name,
            "started_at": self.started_at.isoformat(),
            "history": [
                {
                    "stage": h.stage.name,
                    "started_at": h.started_at.isoformat(),
                    "completed_at": h.completed_at.isoformat() if h.completed_at else None,
                    "skipped": h.skipped,
                    "artifacts": h.artifacts,
                    "notes": h.notes,
                }
                for h in self.history
            ],
            "objective": self.objective,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowState:
        """Deserialize state from dictionary."""
        history = [
            StageHistory(
                stage=WorkflowStage[h["stage"]],
                started_at=datetime.fromisoformat(h["started_at"]),
                completed_at=(
                    datetime.fromisoformat(h["completed_at"]) if h["completed_at"] else None
                ),
                skipped=h.get("skipped", False),
                artifacts=h.get("artifacts", []),
                notes=h.get("notes", ""),
            )
            for h in data.get("history", [])
        ]
        return cls(
            current_stage=WorkflowStage[data["current_stage"]],
            started_at=datetime.fromisoformat(data["started_at"]),
            history=history,
            objective=data.get("objective", ""),
            metadata=data.get("metadata", {}),
        )


class WorkflowStateMachine:
    """State machine for managing workflow stage transitions."""

    def __init__(self, teambot_dir: Path, objective: str = ""):
        self.teambot_dir = teambot_dir
        self.state_file = teambot_dir / "workflow_state.json"
        self._state: WorkflowState | None = None
        self._objective = objective

    @property
    def state(self) -> WorkflowState:
        """Get current workflow state, loading or creating as needed."""
        if self._state is None:
            self._state = self._load_or_create_state()
        return self._state

    @property
    def current_stage(self) -> WorkflowStage:
        """Get the current workflow stage."""
        return self.state.current_stage

    @property
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.current_stage == WorkflowStage.COMPLETE

    def _load_or_create_state(self) -> WorkflowState:
        """Load existing state or create new state."""
        if self.state_file.exists():
            return self._load_state()
        return self._create_initial_state()

    def _load_state(self) -> WorkflowState:
        """Load state from file."""
        try:
            data = json.loads(self.state_file.read_text())
            return WorkflowState.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load workflow state: {e}")
            return self._create_initial_state()

    def _create_initial_state(self) -> WorkflowState:
        """Create initial workflow state."""
        return WorkflowState(
            current_stage=WorkflowStage.SETUP,
            started_at=datetime.now(),
            objective=self._objective,
        )

    def save_state(self) -> None:
        """Save current state to file."""
        self.state_file.write_text(json.dumps(self.state.to_dict(), indent=2))
        logger.debug(f"Workflow state saved to {self.state_file}")

    def can_transition_to(self, target_stage: WorkflowStage) -> bool:
        """Check if transition to target stage is valid.

        Args:
            target_stage: The stage to transition to

        Returns:
            True if transition is valid
        """
        valid_next = get_next_stages(self.current_stage)
        return target_stage in valid_next

    def transition_to(
        self,
        target_stage: WorkflowStage,
        artifacts: list[str] | None = None,
        notes: str = "",
    ) -> bool:
        """Transition to a new workflow stage.

        Args:
            target_stage: The stage to transition to
            artifacts: List of artifact paths created during this stage
            notes: Optional notes about the transition

        Returns:
            True if transition succeeded

        Raises:
            ValueError: If transition is not valid
        """
        if not self.can_transition_to(target_stage):
            valid = [s.name for s in get_next_stages(self.current_stage)]
            raise ValueError(
                f"Cannot transition from {self.current_stage.name} to "
                f"{target_stage.name}. Valid transitions: {valid}"
            )

        # Complete current stage
        self._complete_current_stage(artifacts or [], notes)

        # Start new stage
        self._start_stage(target_stage)

        # Save state
        self.save_state()

        logger.info(f"Workflow transitioned to {target_stage.name}")
        return True

    def skip_stage(self, stage: WorkflowStage) -> bool:
        """Skip an optional stage.

        Args:
            stage: The stage to skip

        Returns:
            True if stage was skipped

        Raises:
            ValueError: If stage is not skippable or not the current stage
        """
        if stage != self.current_stage:
            raise ValueError(f"Can only skip current stage, not {stage.name}")

        if not can_skip_stage(stage):
            raise ValueError(f"Stage {stage.name} is not optional and cannot be skipped")

        # Mark as skipped and move to next
        self._complete_current_stage([], "Skipped", skipped=True)

        # Move to first valid next stage
        next_stages = get_next_stages(stage)
        if next_stages:
            self._start_stage(next_stages[0])
            self.save_state()
            logger.info(f"Skipped {stage.name}, moved to {next_stages[0].name}")
            return True

        return False

    def _complete_current_stage(
        self,
        artifacts: list[str],
        notes: str,
        skipped: bool = False,
    ) -> None:
        """Mark current stage as complete."""
        # Find or create history entry for current stage
        current_history = None
        for h in self.state.history:
            if h.stage == self.current_stage and h.completed_at is None:
                current_history = h
                break

        if current_history:
            current_history.completed_at = datetime.now()
            current_history.artifacts = artifacts
            current_history.notes = notes
            current_history.skipped = skipped

    def _start_stage(self, stage: WorkflowStage) -> None:
        """Start a new stage."""
        self.state.history.append(
            StageHistory(
                stage=stage,
                started_at=datetime.now(),
            )
        )
        self.state.current_stage = stage

    def get_stage_info(self) -> dict[str, Any]:
        """Get information about current stage.

        Returns:
            Dictionary with stage information
        """
        metadata = get_stage_metadata(self.current_stage)
        return {
            "stage": self.current_stage.name,
            "name": metadata.name,
            "description": metadata.description,
            "allowed_personas": metadata.allowed_personas,
            "required_artifacts": metadata.required_artifacts,
            "optional": metadata.optional,
            "next_stages": [s.name for s in metadata.next_stages],
        }

    def get_progress(self) -> dict[str, Any]:
        """Get workflow progress summary.

        Returns:
            Dictionary with progress information
        """
        total_stages = len(WorkflowStage) - 1  # Exclude COMPLETE
        completed = sum(1 for h in self.state.history if h.completed_at is not None)
        skipped = sum(1 for h in self.state.history if h.skipped)

        return {
            "current_stage": self.current_stage.name,
            "total_stages": total_stages,
            "completed_stages": completed,
            "skipped_stages": skipped,
            "progress_percent": round(completed / total_stages * 100, 1),
            "is_complete": self.is_complete,
            "started_at": self.state.started_at.isoformat(),
            "objective": self.state.objective,
        }

    def is_persona_allowed(self, persona: str) -> bool:
        """Check if a persona is allowed to work on current stage.

        Args:
            persona: The persona identifier

        Returns:
            True if persona is allowed
        """
        metadata = get_stage_metadata(self.current_stage)
        return persona.lower() in [p.lower() for p in metadata.allowed_personas]
