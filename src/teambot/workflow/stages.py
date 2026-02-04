"""Workflow stages and metadata for TeamBot's prescriptive workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class WorkflowStage(Enum):
    """Prescriptive workflow stages.

    Workflow:
    Setup → Business Problem → Spec → Review → Research →
    Test Strategy → Plan → Review → Task Implementation →
    Review → Test → Acceptance Test → Post Implementation Review
    """

    SETUP = auto()
    BUSINESS_PROBLEM = auto()
    SPEC = auto()
    SPEC_REVIEW = auto()
    RESEARCH = auto()
    TEST_STRATEGY = auto()
    PLAN = auto()
    PLAN_REVIEW = auto()
    IMPLEMENTATION = auto()
    IMPLEMENTATION_REVIEW = auto()
    TEST = auto()
    ACCEPTANCE_TEST = auto()
    POST_REVIEW = auto()
    COMPLETE = auto()


@dataclass
class StageMetadata:
    """Metadata for a workflow stage."""

    name: str
    description: str
    allowed_personas: list[str]
    required_artifacts: list[str] = field(default_factory=list)
    optional: bool = False
    next_stages: list[WorkflowStage] = field(default_factory=list)


# Stage metadata definitions
STAGE_METADATA: dict[WorkflowStage, StageMetadata] = {
    WorkflowStage.SETUP: StageMetadata(
        name="Setup",
        description="Initialize project, configure agents, and establish working directory",
        allowed_personas=["project_manager", "pm"],
        required_artifacts=[],
        optional=False,
        next_stages=[WorkflowStage.BUSINESS_PROBLEM, WorkflowStage.SPEC],
    ),
    WorkflowStage.BUSINESS_PROBLEM: StageMetadata(
        name="Business Problem",
        description="Define the business problem, goals, and success criteria",
        allowed_personas=["business_analyst", "ba", "project_manager", "pm"],
        required_artifacts=["problem_statement.md"],
        optional=True,  # Skip for small changes
        next_stages=[WorkflowStage.SPEC],
    ),
    WorkflowStage.SPEC: StageMetadata(
        name="Specification",
        description="Create detailed feature specification",
        allowed_personas=["business_analyst", "ba", "technical_writer", "writer"],
        required_artifacts=["feature_spec.md"],
        optional=False,
        next_stages=[WorkflowStage.SPEC_REVIEW],
    ),
    WorkflowStage.SPEC_REVIEW: StageMetadata(
        name="Spec Review",
        description="Review and approve the feature specification",
        allowed_personas=["reviewer", "project_manager", "pm"],
        required_artifacts=["spec_review.md"],
        optional=False,
        next_stages=[WorkflowStage.RESEARCH],
    ),
    WorkflowStage.RESEARCH: StageMetadata(
        name="Research",
        description="Research technical approaches and dependencies",
        allowed_personas=["builder", "developer", "technical_writer", "writer"],
        required_artifacts=["research.md"],
        optional=False,
        next_stages=[WorkflowStage.TEST_STRATEGY],
    ),
    WorkflowStage.TEST_STRATEGY: StageMetadata(
        name="Test Strategy",
        description="Define testing approach and criteria",
        allowed_personas=["builder", "developer", "reviewer"],
        required_artifacts=["test_strategy.md"],
        optional=False,
        next_stages=[WorkflowStage.PLAN],
    ),
    WorkflowStage.PLAN: StageMetadata(
        name="Plan",
        description="Create implementation plan with task breakdown",
        allowed_personas=["project_manager", "pm", "builder", "developer"],
        required_artifacts=["implementation_plan.md"],
        optional=False,
        next_stages=[WorkflowStage.PLAN_REVIEW],
    ),
    WorkflowStage.PLAN_REVIEW: StageMetadata(
        name="Plan Review",
        description="Review and approve the implementation plan",
        allowed_personas=["reviewer", "project_manager", "pm"],
        required_artifacts=["plan_review.md"],
        optional=False,
        next_stages=[WorkflowStage.IMPLEMENTATION],
    ),
    WorkflowStage.IMPLEMENTATION: StageMetadata(
        name="Implementation",
        description="Execute the implementation plan",
        allowed_personas=["builder", "developer"],
        required_artifacts=[],  # Dynamic based on plan
        optional=False,
        next_stages=[WorkflowStage.IMPLEMENTATION_REVIEW],
    ),
    WorkflowStage.IMPLEMENTATION_REVIEW: StageMetadata(
        name="Implementation Review",
        description="Review implemented changes",
        allowed_personas=["reviewer"],
        required_artifacts=["impl_review.md"],
        optional=False,
        next_stages=[WorkflowStage.TEST],
    ),
    WorkflowStage.TEST: StageMetadata(
        name="Test",
        description="Execute tests and validate implementation",
        allowed_personas=["builder", "developer", "reviewer"],
        required_artifacts=["test_results.md"],
        optional=False,
        next_stages=[WorkflowStage.ACCEPTANCE_TEST],
    ),
    WorkflowStage.ACCEPTANCE_TEST: StageMetadata(
        name="Acceptance Test",
        description="Execute acceptance test scenarios to validate end-to-end functionality",
        allowed_personas=["builder", "developer"],
        required_artifacts=["acceptance_test_results.md"],
        optional=False,
        next_stages=[WorkflowStage.POST_REVIEW],
    ),
    WorkflowStage.POST_REVIEW: StageMetadata(
        name="Post Implementation Review",
        description="Final review and retrospective",
        allowed_personas=["project_manager", "pm", "reviewer"],
        required_artifacts=["post_review.md"],
        optional=False,
        next_stages=[WorkflowStage.COMPLETE],
    ),
    WorkflowStage.COMPLETE: StageMetadata(
        name="Complete",
        description="Workflow complete",
        allowed_personas=[],
        required_artifacts=[],
        optional=False,
        next_stages=[],
    ),
}


def get_stage_metadata(stage: WorkflowStage) -> StageMetadata:
    """Get metadata for a workflow stage.

    Args:
        stage: The workflow stage

    Returns:
        StageMetadata for the stage

    Raises:
        KeyError: If stage not found in metadata
    """
    return STAGE_METADATA[stage]


def get_allowed_personas(stage: WorkflowStage) -> list[str]:
    """Get list of personas allowed to work on a stage.

    Args:
        stage: The workflow stage

    Returns:
        List of allowed persona identifiers
    """
    return STAGE_METADATA[stage].allowed_personas


def can_skip_stage(stage: WorkflowStage) -> bool:
    """Check if a stage can be skipped.

    Args:
        stage: The workflow stage

    Returns:
        True if stage is optional
    """
    return STAGE_METADATA[stage].optional


def get_next_stages(stage: WorkflowStage) -> list[WorkflowStage]:
    """Get valid next stages from current stage.

    Args:
        stage: The current workflow stage

    Returns:
        List of valid next stages
    """
    return STAGE_METADATA[stage].next_stages
