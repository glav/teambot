"""Stage configuration loader for file-based orchestration.

Loads stage configuration from YAML file, with fallback to built-in defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from teambot.workflow.stages import WorkflowStage


@dataclass
class StageConfig:
    """Configuration for a single workflow stage."""

    name: str
    description: str
    work_agent: str | None
    review_agent: str | None
    allowed_personas: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    exit_criteria: list[str] = field(default_factory=list)
    optional: bool = False
    is_review_stage: bool = False
    parallel_agents: list[str] | None = None
    prompt_template: str | None = None


@dataclass
class StagesConfiguration:
    """Complete stages configuration."""

    stages: dict[WorkflowStage, StageConfig]
    stage_order: list[WorkflowStage]
    work_to_review_mapping: dict[WorkflowStage, WorkflowStage]
    review_stages: set[WorkflowStage] = field(default_factory=set)
    source: str = "built-in-defaults"  # Path to config file or "built-in-defaults"

    def get_stage_agents(self, stage: WorkflowStage) -> dict[str, str | None]:
        """Get work and review agents for a stage."""
        config = self.stages.get(stage)
        if not config:
            return {"work": None, "review": None}
        return {"work": config.work_agent, "review": config.review_agent}

    def get_allowed_personas(self, stage: WorkflowStage) -> list[str]:
        """Get allowed personas for a stage."""
        config = self.stages.get(stage)
        return config.allowed_personas if config else []

    def is_optional(self, stage: WorkflowStage) -> bool:
        """Check if stage is optional."""
        config = self.stages.get(stage)
        return config.optional if config else False

    def get_exit_criteria(self, stage: WorkflowStage) -> list[str]:
        """Get exit criteria for a stage."""
        config = self.stages.get(stage)
        return config.exit_criteria if config else []


def load_stages_config(config_path: Path | None = None) -> StagesConfiguration:
    """Load stages configuration from YAML file.

    Args:
        config_path: Path to stages.yaml file. If None, looks for stages.yaml
                    in current directory, then falls back to built-in defaults.

    Returns:
        StagesConfiguration with all stage definitions

    Raises:
        FileNotFoundError: If specified config_path doesn't exist
        ValueError: If configuration is invalid
    """
    # Determine config file path
    if config_path is not None:
        if not config_path.exists():
            raise FileNotFoundError(f"Stages config not found: {config_path}")
        yaml_path = config_path
    else:
        # Look for stages.yaml in current directory or use defaults
        default_path = Path("stages.yaml")
        if default_path.exists():
            yaml_path = default_path
        else:
            # Return built-in defaults
            return _get_default_configuration()

    # Load and parse YAML
    content = yaml_path.read_text()
    data = yaml.safe_load(content)

    config = _parse_configuration(data)
    config.source = str(yaml_path.resolve())
    return config


def _parse_configuration(data: dict[str, Any]) -> StagesConfiguration:
    """Parse configuration from loaded YAML data."""
    if not data:
        raise ValueError("Empty stages configuration")

    stages_data = data.get("stages", {})
    if not stages_data:
        raise ValueError("No stages defined in configuration")

    # Parse individual stages
    stages: dict[WorkflowStage, StageConfig] = {}
    review_stages: set[WorkflowStage] = set()

    for stage_name, stage_data in stages_data.items():
        try:
            workflow_stage = WorkflowStage[stage_name]
        except KeyError:
            raise ValueError(f"Unknown stage: {stage_name}")

        config = StageConfig(
            name=stage_data.get("name", stage_name),
            description=stage_data.get("description", ""),
            work_agent=stage_data.get("work_agent"),
            review_agent=stage_data.get("review_agent"),
            allowed_personas=stage_data.get("allowed_personas", []),
            artifacts=stage_data.get("artifacts", []),
            exit_criteria=stage_data.get("exit_criteria", []),
            optional=stage_data.get("optional", False),
            is_review_stage=stage_data.get("is_review_stage", False),
            parallel_agents=stage_data.get("parallel_agents"),
            prompt_template=stage_data.get("prompt_template"),
        )
        stages[workflow_stage] = config

        if config.is_review_stage:
            review_stages.add(workflow_stage)

    # Parse stage order
    stage_order_names = data.get("stage_order", [])
    stage_order = []
    for name in stage_order_names:
        try:
            stage_order.append(WorkflowStage[name])
        except KeyError:
            raise ValueError(f"Unknown stage in stage_order: {name}")

    # Parse work to review mapping
    mapping_data = data.get("work_to_review_mapping", {})
    work_to_review: dict[WorkflowStage, WorkflowStage] = {}
    for work_name, review_name in mapping_data.items():
        try:
            work_stage = WorkflowStage[work_name]
            review_stage = WorkflowStage[review_name]
            work_to_review[work_stage] = review_stage
        except KeyError as e:
            raise ValueError(f"Unknown stage in work_to_review_mapping: {e}")

    return StagesConfiguration(
        stages=stages,
        stage_order=stage_order,
        work_to_review_mapping=work_to_review,
        review_stages=review_stages,
    )


def _get_default_configuration() -> StagesConfiguration:
    """Return built-in default configuration.

    This provides backward compatibility when no stages.yaml exists.
    """
    # Import here to avoid circular dependency
    from teambot.workflow.stages import STAGE_METADATA

    stages: dict[WorkflowStage, StageConfig] = {}
    review_stages: set[WorkflowStage] = set()

    # Default agent assignments (from original execution_loop.py)
    default_agents = {
        WorkflowStage.SETUP: ("pm", None),
        WorkflowStage.BUSINESS_PROBLEM: ("ba", None),
        WorkflowStage.SPEC: ("ba", "reviewer"),
        WorkflowStage.SPEC_REVIEW: ("ba", "reviewer"),
        WorkflowStage.RESEARCH: ("builder-1", None),
        WorkflowStage.TEST_STRATEGY: ("builder-1", None),
        WorkflowStage.PLAN: ("pm", "reviewer"),
        WorkflowStage.PLAN_REVIEW: ("pm", "reviewer"),
        WorkflowStage.IMPLEMENTATION: ("builder-1", "reviewer"),
        WorkflowStage.IMPLEMENTATION_REVIEW: ("builder-1", "reviewer"),
        WorkflowStage.TEST: ("builder-1", None),
        WorkflowStage.POST_REVIEW: ("pm", "reviewer"),
        WorkflowStage.COMPLETE: (None, None),
    }

    review_stage_set = {
        WorkflowStage.SPEC_REVIEW,
        WorkflowStage.PLAN_REVIEW,
        WorkflowStage.IMPLEMENTATION_REVIEW,
        WorkflowStage.POST_REVIEW,
    }

    for stage, metadata in STAGE_METADATA.items():
        work_agent, review_agent = default_agents.get(stage, (None, None))
        is_review = stage in review_stage_set

        config = StageConfig(
            name=metadata.name,
            description=metadata.description,
            work_agent=work_agent,
            review_agent=review_agent,
            allowed_personas=metadata.allowed_personas,
            artifacts=metadata.required_artifacts,
            exit_criteria=[],  # Not defined in old metadata
            optional=metadata.optional,
            is_review_stage=is_review,
            parallel_agents=["builder-1", "builder-2"] if stage == WorkflowStage.IMPLEMENTATION else None,
            prompt_template=None,
        )
        stages[stage] = config

        if is_review:
            review_stages.add(stage)

    stage_order = [
        WorkflowStage.SETUP,
        WorkflowStage.BUSINESS_PROBLEM,
        WorkflowStage.SPEC,
        WorkflowStage.SPEC_REVIEW,
        WorkflowStage.RESEARCH,
        WorkflowStage.TEST_STRATEGY,
        WorkflowStage.PLAN,
        WorkflowStage.PLAN_REVIEW,
        WorkflowStage.IMPLEMENTATION,
        WorkflowStage.IMPLEMENTATION_REVIEW,
        WorkflowStage.TEST,
        WorkflowStage.POST_REVIEW,
        WorkflowStage.COMPLETE,
    ]

    work_to_review = {
        WorkflowStage.SPEC: WorkflowStage.SPEC_REVIEW,
        WorkflowStage.PLAN: WorkflowStage.PLAN_REVIEW,
        WorkflowStage.IMPLEMENTATION: WorkflowStage.IMPLEMENTATION_REVIEW,
        WorkflowStage.TEST: WorkflowStage.POST_REVIEW,
    }

    return StagesConfiguration(
        stages=stages,
        stage_order=stage_order,
        work_to_review_mapping=work_to_review,
        review_stages=review_stages,
    )
