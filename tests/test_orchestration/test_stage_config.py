"""Tests for stage configuration loader."""

from __future__ import annotations

import pytest
from pathlib import Path

from teambot.orchestration.stage_config import (
    StageConfig,
    StagesConfiguration,
    load_stages_config,
    _parse_configuration,
    _get_default_configuration,
)
from teambot.workflow.stages import WorkflowStage


class TestLoadStagesConfig:
    """Tests for load_stages_config function."""

    def test_load_from_yaml_file(self, tmp_path: Path) -> None:
        """Load configuration from YAML file."""
        yaml_content = """
stages:
  SETUP:
    name: Setup
    description: Initialize project
    work_agent: pm
    review_agent: null
    allowed_personas:
      - pm
    artifacts: []
    exit_criteria:
      - Environment ready
    optional: false
  COMPLETE:
    name: Complete
    description: Workflow complete
    work_agent: null
    review_agent: null
    allowed_personas: []
    artifacts: []
    exit_criteria: []
    optional: false

stage_order:
  - SETUP
  - COMPLETE

work_to_review_mapping: {}
"""
        config_file = tmp_path / "stages.yaml"
        config_file.write_text(yaml_content)

        config = load_stages_config(config_file)

        assert WorkflowStage.SETUP in config.stages
        assert config.stages[WorkflowStage.SETUP].name == "Setup"
        assert config.stages[WorkflowStage.SETUP].work_agent == "pm"

    def test_load_missing_file_raises_error(self, tmp_path: Path) -> None:
        """Loading missing file raises FileNotFoundError."""
        missing_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError, match="Stages config not found"):
            load_stages_config(missing_file)

    def test_load_default_when_no_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Load default configuration when no path provided and no stages.yaml exists."""
        # Change to temp directory without stages.yaml
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.chdir(tmpdir)
            config = load_stages_config(None)

        # Should get default configuration
        assert WorkflowStage.SETUP in config.stages
        assert len(config.stage_order) == 13

    def test_load_from_cwd_stages_yaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Load from stages.yaml in current directory."""
        yaml_content = """
stages:
  SETUP:
    name: Custom Setup
    description: Custom initialization
    work_agent: custom-pm
    review_agent: null
    allowed_personas: [pm]
    artifacts: []
    exit_criteria: []
    optional: false
  COMPLETE:
    name: Complete
    description: Done
    work_agent: null
    review_agent: null
    allowed_personas: []
    artifacts: []
    exit_criteria: []
    optional: false

stage_order:
  - SETUP
  - COMPLETE

work_to_review_mapping: {}
"""
        stages_file = tmp_path / "stages.yaml"
        stages_file.write_text(yaml_content)
        monkeypatch.chdir(tmp_path)

        config = load_stages_config(None)

        assert config.stages[WorkflowStage.SETUP].name == "Custom Setup"
        assert config.stages[WorkflowStage.SETUP].work_agent == "custom-pm"


class TestParseConfiguration:
    """Tests for configuration parsing."""

    def test_parse_empty_raises_error(self) -> None:
        """Parsing empty config raises ValueError."""
        with pytest.raises(ValueError, match="Empty stages configuration"):
            _parse_configuration({})

    def test_parse_no_stages_raises_error(self) -> None:
        """Parsing config without stages raises ValueError."""
        with pytest.raises(ValueError, match="No stages defined"):
            _parse_configuration({"stage_order": []})

    def test_parse_unknown_stage_raises_error(self) -> None:
        """Parsing config with unknown stage raises ValueError."""
        data = {
            "stages": {
                "UNKNOWN_STAGE": {
                    "name": "Unknown",
                    "description": "test",
                }
            }
        }
        with pytest.raises(ValueError, match="Unknown stage: UNKNOWN_STAGE"):
            _parse_configuration(data)

    def test_parse_unknown_stage_in_order_raises_error(self) -> None:
        """Parsing config with unknown stage in order raises ValueError."""
        data = {
            "stages": {
                "SETUP": {
                    "name": "Setup",
                    "description": "test",
                }
            },
            "stage_order": ["SETUP", "INVALID"],
        }
        with pytest.raises(ValueError, match="Unknown stage in stage_order: INVALID"):
            _parse_configuration(data)

    def test_parse_review_stages_identified(self) -> None:
        """Review stages are correctly identified."""
        data = {
            "stages": {
                "SPEC": {
                    "name": "Spec",
                    "description": "Create spec",
                    "is_review_stage": False,
                },
                "SPEC_REVIEW": {
                    "name": "Spec Review",
                    "description": "Review spec",
                    "is_review_stage": True,
                },
            },
            "stage_order": ["SPEC", "SPEC_REVIEW"],
            "work_to_review_mapping": {"SPEC": "SPEC_REVIEW"},
        }

        config = _parse_configuration(data)

        assert WorkflowStage.SPEC_REVIEW in config.review_stages
        assert WorkflowStage.SPEC not in config.review_stages

    def test_parse_work_to_review_mapping(self) -> None:
        """Work to review mapping is correctly parsed."""
        data = {
            "stages": {
                "SPEC": {"name": "Spec", "description": "test"},
                "SPEC_REVIEW": {"name": "Spec Review", "description": "test"},
            },
            "stage_order": ["SPEC", "SPEC_REVIEW"],
            "work_to_review_mapping": {"SPEC": "SPEC_REVIEW"},
        }

        config = _parse_configuration(data)

        assert config.work_to_review_mapping[WorkflowStage.SPEC] == WorkflowStage.SPEC_REVIEW


class TestStagesConfiguration:
    """Tests for StagesConfiguration methods."""

    @pytest.fixture
    def sample_config(self) -> StagesConfiguration:
        """Create sample configuration."""
        stages = {
            WorkflowStage.SETUP: StageConfig(
                name="Setup",
                description="Initialize",
                work_agent="pm",
                review_agent=None,
                allowed_personas=["pm", "project_manager"],
                exit_criteria=["Environment ready"],
                optional=False,
            ),
            WorkflowStage.SPEC: StageConfig(
                name="Spec",
                description="Create spec",
                work_agent="ba",
                review_agent="reviewer",
                allowed_personas=["ba"],
                optional=False,
            ),
        }
        return StagesConfiguration(
            stages=stages,
            stage_order=[WorkflowStage.SETUP, WorkflowStage.SPEC],
            work_to_review_mapping={},
            review_stages=set(),
        )

    def test_get_stage_agents(self, sample_config: StagesConfiguration) -> None:
        """Get work and review agents for stage."""
        agents = sample_config.get_stage_agents(WorkflowStage.SETUP)

        assert agents["work"] == "pm"
        assert agents["review"] is None

    def test_get_stage_agents_unknown_stage(self, sample_config: StagesConfiguration) -> None:
        """Get agents for unknown stage returns None."""
        agents = sample_config.get_stage_agents(WorkflowStage.COMPLETE)

        assert agents["work"] is None
        assert agents["review"] is None

    def test_get_allowed_personas(self, sample_config: StagesConfiguration) -> None:
        """Get allowed personas for stage."""
        personas = sample_config.get_allowed_personas(WorkflowStage.SETUP)

        assert "pm" in personas
        assert "project_manager" in personas

    def test_is_optional(self, sample_config: StagesConfiguration) -> None:
        """Check if stage is optional."""
        assert not sample_config.is_optional(WorkflowStage.SETUP)

    def test_get_exit_criteria(self, sample_config: StagesConfiguration) -> None:
        """Get exit criteria for stage."""
        criteria = sample_config.get_exit_criteria(WorkflowStage.SETUP)

        assert "Environment ready" in criteria


class TestDefaultConfiguration:
    """Tests for default configuration."""

    def test_default_has_all_stages(self) -> None:
        """Default configuration has all 13 stages."""
        config = _get_default_configuration()

        assert len(config.stages) == 13
        assert WorkflowStage.SETUP in config.stages
        assert WorkflowStage.COMPLETE in config.stages

    def test_default_has_correct_order(self) -> None:
        """Default configuration has correct stage order."""
        config = _get_default_configuration()

        assert config.stage_order[0] == WorkflowStage.SETUP
        assert config.stage_order[-1] == WorkflowStage.COMPLETE
        assert len(config.stage_order) == 13

    def test_default_has_review_stages(self) -> None:
        """Default configuration identifies review stages."""
        config = _get_default_configuration()

        assert WorkflowStage.SPEC_REVIEW in config.review_stages
        assert WorkflowStage.PLAN_REVIEW in config.review_stages
        assert WorkflowStage.IMPLEMENTATION_REVIEW in config.review_stages
        assert WorkflowStage.POST_REVIEW in config.review_stages
        assert len(config.review_stages) == 4

    def test_default_has_work_to_review_mapping(self) -> None:
        """Default configuration has work to review mapping."""
        config = _get_default_configuration()

        assert config.work_to_review_mapping[WorkflowStage.SPEC] == WorkflowStage.SPEC_REVIEW
        assert config.work_to_review_mapping[WorkflowStage.PLAN] == WorkflowStage.PLAN_REVIEW

    def test_default_implementation_has_parallel_agents(self) -> None:
        """Default configuration has parallel agents for IMPLEMENTATION."""
        config = _get_default_configuration()

        impl_config = config.stages[WorkflowStage.IMPLEMENTATION]
        assert impl_config.parallel_agents == ["builder-1", "builder-2"]


class TestStageConfigDataclass:
    """Tests for StageConfig dataclass."""

    def test_defaults(self) -> None:
        """StageConfig has correct defaults."""
        config = StageConfig(
            name="Test",
            description="Test stage",
            work_agent="test",
            review_agent=None,
        )

        assert config.allowed_personas == []
        assert config.artifacts == []
        assert config.exit_criteria == []
        assert config.optional is False
        assert config.is_review_stage is False
        assert config.parallel_agents is None
        assert config.prompt_template is None
