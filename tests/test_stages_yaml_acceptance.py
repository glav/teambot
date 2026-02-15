"""Acceptance test validation for stages.yaml schema improvement feature.

These tests validate the acceptance scenarios AT-001 through AT-005 using
the REAL implementation code.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from teambot.orchestration.stage_config import load_stages_config
from teambot.workflow.stages import WorkflowStage
from teambot.workflow.state_machine import WorkflowStateMachine


class TestStagesYamlAcceptanceScenarios:
    """Acceptance tests for stages.yaml schema improvement."""

    @pytest.fixture
    def stages_yaml_content(self) -> str:
        """Load the actual stages.yaml content."""
        stages_path = Path("stages.yaml")
        return stages_path.read_text(encoding="utf-8")

    @pytest.fixture
    def stages_config(self):
        """Load the actual stages configuration."""
        return load_stages_config(Path("stages.yaml"))

    def test_at_001_allowed_personas_documentation_accuracy(
        self, stages_yaml_content: str, tmp_path: Path
    ) -> None:
        """AT-001: Verify allowed_personas documentation matches enforcement behavior.

        The documentation should state that allowed_personas is enforced via
        is_persona_allowed() in state_machine.py, not just "informational".
        """
        # Step 1-2: Find allowed_personas field description in header
        pattern = r"#\s*allowed_personas\s*-.*"
        match = re.search(pattern, stages_yaml_content)
        assert match is not None, "allowed_personas field not found in schema reference"

        allowed_personas_line = match.group(0)

        # Step 3: Verify it mentions enforcement, not "informational"
        assert "enforced" in allowed_personas_line.lower(), (
            f"Documentation should mention 'enforced'. Found: {allowed_personas_line}"
        )
        assert "informational" not in allowed_personas_line.lower(), (
            f"Documentation should NOT say 'informational'. Found: {allowed_personas_line}"
        )

        # Step 4: Cross-reference with state_machine.py - verify is_persona_allowed exists
        assert (
            "is_persona_allowed" in allowed_personas_line
            or "state_machine" in allowed_personas_line
        ), (
            "Should reference is_persona_allowed() or state_machine.py. "
            f"Found: {allowed_personas_line}"
        )

        # Verify the actual method exists in the real implementation
        state_machine = WorkflowStateMachine(teambot_dir=tmp_path)
        assert hasattr(state_machine, "is_persona_allowed"), (
            "is_persona_allowed method should exist"
        )
        assert callable(state_machine.is_persona_allowed), "is_persona_allowed should be callable"

    def test_at_002_inline_artifact_path_comments(self, stages_yaml_content: str) -> None:
        """AT-002: Verify all stages with artifacts have consistent path comments.

        All stages with non-empty artifacts should have inline comments
        in the format: # → .teambot/{feature}/artifacts/{filename}
        """
        # Count inline artifact path comments with → arrow
        artifact_pattern = r"# → \.teambot/\{feature\}/artifacts/"
        matches = re.findall(artifact_pattern, stages_yaml_content)

        # Per AT-002: Should find 10+ inline artifact path comments
        assert len(matches) >= 10, (
            f"Expected at least 10 inline artifact path comments, found {len(matches)}"
        )

    def test_at_003_default_values_complete(self, stages_yaml_content: str) -> None:
        """AT-003: Verify all 13 stage fields have documented defaults.

        Each field in SCHEMA REFERENCE should have "(default: ...)" noted.
        """
        # Count "(default:" occurrences in the file
        default_pattern = r"\(default:"
        matches = re.findall(default_pattern, stages_yaml_content)

        # At least 13 fields should have defaults documented
        assert len(matches) >= 13, (
            f"Expected at least 13 fields with (default:) documentation, found {len(matches)}"
        )

    def test_at_004_validation_rules_section_exists(self, stages_yaml_content: str) -> None:
        """AT-004: Verify new validation rules section is present.

        The header should contain a VALIDATION RULES section with rules for:
        - WORK STAGES
        - REVIEW STAGES
        - TERMINAL STAGE
        """
        # Step 1: Search for VALIDATION RULES header
        assert "VALIDATION RULES" in stages_yaml_content, (
            "VALIDATION RULES section header not found"
        )

        # Step 2: Verify section contains required rule categories
        assert "WORK STAGES" in stages_yaml_content, (
            "WORK STAGES rule category not found in VALIDATION RULES"
        )
        assert "REVIEW STAGES" in stages_yaml_content, (
            "REVIEW STAGES rule category not found in VALIDATION RULES"
        )
        assert "TERMINAL STAGE" in stages_yaml_content, (
            "TERMINAL STAGE rule category not found in VALIDATION RULES"
        )

    def test_at_005_backward_compatibility(self, stages_config) -> None:
        """AT-005: Verify all existing tests pass with updated stages.yaml.

        Verify the stages.yaml loads correctly and has expected structure.
        """
        # Verify expected structure
        assert len(stages_config.stages) == 14, (
            f"Expected 14 stages, got {len(stages_config.stages)}"
        )
        assert len(stages_config.stage_order) == 14, (
            f"Expected 14 stages in order, got {len(stages_config.stage_order)}"
        )
        assert len(stages_config.review_stages) == 4, (
            f"Expected 4 review stages, got {len(stages_config.review_stages)}"
        )

        # Verify key stages exist
        assert WorkflowStage.SETUP in stages_config.stages
        assert WorkflowStage.SPEC in stages_config.stages
        assert WorkflowStage.IMPLEMENTATION in stages_config.stages
        assert WorkflowStage.COMPLETE in stages_config.stages

        # Verify review stage detection
        assert WorkflowStage.SPEC_REVIEW in stages_config.review_stages
        assert WorkflowStage.PLAN_REVIEW in stages_config.review_stages
        assert WorkflowStage.IMPLEMENTATION_REVIEW in stages_config.review_stages
        assert WorkflowStage.POST_REVIEW in stages_config.review_stages

        # Verify work_to_review_mapping
        assert stages_config.work_to_review_mapping[WorkflowStage.SPEC] == WorkflowStage.SPEC_REVIEW
        assert stages_config.work_to_review_mapping[WorkflowStage.PLAN] == WorkflowStage.PLAN_REVIEW
