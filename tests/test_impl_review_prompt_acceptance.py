"""Acceptance tests for Implementation Review Completion Check feature.

These tests validate the prompt template file and stages.yaml configuration
against the feature acceptance criteria.
"""

import re
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def prompt_path() -> Path:
    """Path to the implementation review prompt file."""
    return Path(".agent/commands/sdd/sdd.6b-implementation-review.prompt.md")


@pytest.fixture
def prompt_content(prompt_path: Path) -> str:
    """Load the actual prompt file content."""
    return prompt_path.read_text(encoding="utf-8")


@pytest.fixture
def stages_config() -> dict:
    """Load the actual stages.yaml configuration."""
    stages_path = Path("stages.yaml")
    return yaml.safe_load(stages_path.read_text(encoding="utf-8"))


@pytest.fixture
def sample_incomplete_plan(tmp_path: Path) -> Path:
    """Create a sample plan file with incomplete tasks."""
    plan_content = """---
applyTo: '.agent-tracking/changes/20260302-test-changes.md'
---
<!-- markdownlint-disable-file -->
# Task Checklist: Test Feature

## Overview
Test feature implementation.

## Implementation Checklist

### [x] Phase 1: Setup
* [x] Task 1.1: Initialize project
* [x] Task 1.2: Configure environment

### [ ] Phase 2: Implementation
* [x] Task 2.1: Create module
* [ ] Task 2.2: Add validation logic
* [ ] Task 2.3: Write tests

### [ ] Phase 3: Documentation
* [ ] Task 3.1: Update README
"""
    plan_file = tmp_path / "20260302-test-plan.instructions.md"
    plan_file.write_text(plan_content, encoding="utf-8")
    return plan_file


@pytest.fixture
def sample_complete_plan(tmp_path: Path) -> Path:
    """Create a sample plan file with all tasks complete."""
    plan_content = """---
applyTo: '.agent-tracking/changes/20260302-test-changes.md'
---
<!-- markdownlint-disable-file -->
# Task Checklist: Test Feature

## Overview
Test feature implementation.

## Implementation Checklist

### [x] Phase 1: Setup
* [x] Task 1.1: Initialize project
* [x] Task 1.2: Configure environment

### [x] Phase 2: Implementation
* [x] Task 2.1: Create module
* [x] Task 2.2: Add validation logic
* [x] Task 2.3: Write tests

### [x] Phase 3: Documentation
* [x] Task 3.1: Update README
"""
    plan_file = tmp_path / "20260302-test-plan.instructions.md"
    plan_file.write_text(plan_content, encoding="utf-8")
    return plan_file


@pytest.mark.acceptance
class TestImplementationReviewAcceptance:
    """Acceptance tests for Implementation Review Completion Check feature."""

    def test_at_001_prompt_file_exists(self, prompt_path: Path) -> None:
        """AT-001: Prompt file exists at expected location.

        Validates that the implementation review prompt file was created
        in the correct location as specified in the feature spec.
        """
        assert prompt_path.exists(), f"Prompt file not found at {prompt_path}"
        assert prompt_path.is_file(), f"Path exists but is not a file: {prompt_path}"

    def test_at_001_yaml_frontmatter_valid(self, prompt_content: str) -> None:
        """AT-001: Prompt has valid YAML frontmatter with required fields.

        Validates the YAML frontmatter contains description, agent, and tools
        as required by the SDD prompt template pattern.
        """
        # Extract frontmatter between --- delimiters
        match = re.match(r"^---\n(.*?)\n---", prompt_content, re.DOTALL)
        assert match is not None, "YAML frontmatter not found (must start with ---)"

        frontmatter = yaml.safe_load(match.group(1))
        assert frontmatter is not None, "YAML frontmatter is empty"
        assert "description" in frontmatter, "Missing 'description' field in frontmatter"
        assert "agent" in frontmatter, "Missing 'agent' field in frontmatter"
        assert "tools" in frontmatter, "Missing 'tools' field in frontmatter"

        # Verify description mentions task completion verification
        assert (
            "task completion" in frontmatter["description"].lower()
            or "implementation review" in frontmatter["description"].lower()
        ), "Description should mention task completion or implementation review"

    def test_at_001_pre_check_section_exists(self, prompt_content: str) -> None:
        """AT-001: Prompt contains blocking pre-code-review checklist.

        Validates the prompt includes a pre-check section that blocks
        code review until all tasks are marked complete.
        """
        assert "Pre-Code-Review Checklist" in prompt_content, (
            "Missing 'Pre-Code-Review Checklist' section"
        )
        assert "BLOCKING" in prompt_content, "Pre-check should be marked as BLOCKING"

    def test_at_001_rejection_format_with_task_list(self, prompt_content: str) -> None:
        """AT-001: Prompt includes rejection format with incomplete task list.

        Validates the prompt defines a rejection format that lists
        incomplete tasks when implementation is not complete.
        """
        # Check for rejection format header
        assert "IMPLEMENTATION_REVIEW: REJECTED" in prompt_content, (
            "Missing REJECTED format template"
        )

        # Check for incomplete tasks section
        assert "Incomplete Tasks" in prompt_content, (
            "Rejection format should include 'Incomplete Tasks' section"
        )

        # Check for actionable feedback
        assert "Action Required" in prompt_content, (
            "Rejection format should include 'Action Required' section"
        )

    def test_at_001_approval_format_proceeds_to_review(self, prompt_content: str) -> None:
        """AT-001: Prompt includes approval format proceeding to code review.

        Validates the prompt defines an approval format that transitions
        to code quality review after pre-check passes.
        """
        # Check for approval format
        assert "VERIFIED_APPROVED" in prompt_content, "Missing VERIFIED_APPROVED format template"

        # Check for code review transition
        assert "Code Quality Review" in prompt_content, (
            "Should include 'Code Quality Review' section after approval"
        )

        # Check for pre-check verification
        assert (
            "TASK COMPLETION VERIFIED" in prompt_content or "Pre-Review Checklist" in prompt_content
        ), "Should confirm task completion before code review"

    def test_at_001_stages_yaml_references_prompt(self, stages_config: dict) -> None:
        """AT-001: stages.yaml IMPLEMENTATION_REVIEW references new prompt.

        Validates that stages.yaml has been updated to reference the
        new implementation review prompt template.
        """
        assert "stages" in stages_config, "stages.yaml missing 'stages' key"
        assert "IMPLEMENTATION_REVIEW" in stages_config["stages"], (
            "stages.yaml missing IMPLEMENTATION_REVIEW stage"
        )

        impl_review = stages_config["stages"]["IMPLEMENTATION_REVIEW"]
        expected_path = ".agent/commands/sdd/sdd.6b-implementation-review.prompt.md"

        assert impl_review.get("prompt_template") is not None, (
            "IMPLEMENTATION_REVIEW.prompt_template should not be null"
        )
        assert impl_review.get("prompt_template") == expected_path, (
            f"Expected prompt_template '{expected_path}', "
            f"got '{impl_review.get('prompt_template')}'"
        )

    def test_at_001_incomplete_plan_detection_logic(
        self, prompt_content: str, sample_incomplete_plan: Path
    ) -> None:
        """AT-001: Prompt defines logic to detect incomplete [ ] tasks.

        Validates the prompt includes instructions for parsing plan files
        and detecting unchecked [ ] items.
        """
        # Check prompt defines parsing rules
        assert "[ ]" in prompt_content, "Should reference [ ] marker for incomplete tasks"
        assert "[x]" in prompt_content, "Should reference [x] marker for complete tasks"

        # Verify sample plan has incomplete tasks (test data validation)
        plan_content = sample_incomplete_plan.read_text()
        incomplete_count = plan_content.count("[ ]")
        complete_count = plan_content.count("[x]")

        assert incomplete_count == 5, f"Expected 5 incomplete tasks, found {incomplete_count}"
        assert complete_count == 4, f"Expected 4 complete tasks, found {complete_count}"

    def test_at_001_complete_plan_approval_path(
        self, prompt_content: str, sample_complete_plan: Path
    ) -> None:
        """AT-001: Prompt approves when all tasks are [x] complete.

        Validates the prompt defines logic to proceed to code review
        when all tasks are marked complete.
        """
        # Verify sample plan has all tasks complete (test data validation)
        plan_content = sample_complete_plan.read_text()
        incomplete_count = plan_content.count("[ ]")
        complete_count = plan_content.count("[x]")

        assert incomplete_count == 0, f"Expected 0 incomplete tasks, found {incomplete_count}"
        assert complete_count == 9, f"Expected 9 complete tasks, found {complete_count}"

        # Check prompt defines approval condition
        assert "ALL" in prompt_content.upper() or "all" in prompt_content, (
            "Prompt should require ALL tasks complete"
        )
        assert "proceed" in prompt_content.lower(), "Prompt should mention proceeding to next phase"

    def test_at_001_review_iterator_integration(self, stages_config: dict) -> None:
        """AT-001: IMPLEMENTATION_REVIEW is configured as review stage with iteration.

        Validates the stage is configured with is_review_stage: true to
        enable the ReviewIterator's 4-iteration loop.
        """
        impl_review = stages_config["stages"]["IMPLEMENTATION_REVIEW"]

        assert impl_review.get("is_review_stage") is True, (
            "IMPLEMENTATION_REVIEW should have is_review_stage: true"
        )

        # Verify work_agent and review_agent are configured
        assert impl_review.get("work_agent") is not None, "Should have work_agent configured"
        assert impl_review.get("review_agent") is not None, "Should have review_agent configured"

    def test_at_001_iteration_status_in_rejection(self, prompt_content: str) -> None:
        """AT-001: Rejection format includes iteration status.

        Validates the rejection format tells the builder how many
        iterations have been used and how many remain.
        """
        assert "Iteration Status" in prompt_content, (
            "Rejection format should include 'Iteration Status'"
        )
        assert "/4" in prompt_content, "Should show iteration count out of 4 maximum"
