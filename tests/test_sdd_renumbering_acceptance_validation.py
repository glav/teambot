"""
Acceptance test validation for SDD prompt renumbering feature.

Tests validate the REAL implementation against acceptance criteria:
- Repository and scaffold files correctly renumbered (9 files, no sdd.4 or sdd.6c)
- Configuration files reference correct paths
- Full workflow can execute
- All existing tests pass
- teambot init creates correct structure
- Documentation is accurate

NOTE: These tests call REAL implementation code, not mocks.
"""

import argparse
import os
import subprocess
from pathlib import Path

import pytest
import yaml

# Repository root for all tests
REPO_ROOT = Path(__file__).parent.parent.absolute()
AGENT_DIR = REPO_ROOT / ".agent" / "commands" / "sdd"
SCAFFOLD_DIR = REPO_ROOT / "src" / "teambot" / "scaffolds" / ".agent" / "commands" / "sdd"
STAGES_YAML = REPO_ROOT / "stages.yaml"
SCAFFOLD_STAGES_YAML = REPO_ROOT / "src" / "teambot" / "scaffolds" / "stages.yaml"


@pytest.mark.acceptance
class TestSDDPromptRenumberingAcceptance:
    """Acceptance tests for SDD prompt renumbering feature."""

    def test_at_001_repository_file_renumbering(self):
        """
        AT-001: Verify all SDD prompt files in .agent/commands/sdd/ are correctly renumbered.

        Expected: 9 prompt files (sdd.0-7 with sdd.6b), no sdd.4-determine-test-strategy,
                  no sdd.6c (ACCEPTANCE_TEST is code-driven, not prompt-based)
        """
        # List all prompt files
        prompt_files = sorted(AGENT_DIR.glob("sdd.*.prompt.md"))
        prompt_names = [f.name for f in prompt_files]

        # Verify count: should be 9 files
        assert len(prompt_files) == 9, (
            f"Expected 9 prompt files, found {len(prompt_files)}: {prompt_names}"
        )

        # Verify sdd.4-determine-test-strategy does NOT exist
        assert not (AGENT_DIR / "sdd.4-determine-test-strategy.prompt.md").exists(), (
            "sdd.4-determine-test-strategy.prompt.md should be deleted"
        )

        # Verify sdd.6c does NOT exist (ACCEPTANCE_TEST is code-driven)
        assert not (AGENT_DIR / "sdd.6c-acceptance-test.prompt.md").exists(), (
            "sdd.6c-acceptance-test.prompt.md should not exist (ACCEPTANCE_TEST is code-driven)"
        )

        # Verify expected files DO exist (renamed correctly)
        expected_files = [
            "sdd.0-initialize.prompt.md",
            "sdd.1-create-feature-spec.prompt.md",
            "sdd.2-review-spec.prompt.md",
            "sdd.3-research-feature.prompt.md",
            "sdd.4-task-planner-for-feature.prompt.md",  # Was sdd.5
            "sdd.5-review-plan.prompt.md",  # Was sdd.6
            "sdd.6-task-implementer-for-feature.prompt.md",  # Was sdd.7
            "sdd.6b-implementation-review.prompt.md",  # Was sdd.7b
            "sdd.7-post-implementation-review.prompt.md",  # Was sdd.8
        ]

        for expected_file in expected_files:
            file_path = AGENT_DIR / expected_file
            assert file_path.exists(), f"Expected file {expected_file} does not exist"

        # Verify the actual list matches expected
        assert prompt_names == expected_files, (
            f"File list mismatch.\nExpected: {expected_files}\nActual: {prompt_names}"
        )

    def test_at_002_scaffold_file_renumbering(self):
        """
        AT-002: Verify scaffold directory mirrors repository structure with new numbering.

        Expected: Scaffold has identical structure to repository (9 files, no sdd.4 or sdd.6c)
        """
        # List files in both directories
        repo_files = sorted([f.name for f in AGENT_DIR.glob("sdd.*.prompt.md")])
        scaffold_files = sorted([f.name for f in SCAFFOLD_DIR.glob("sdd.*.prompt.md")])

        # Verify counts match
        assert len(scaffold_files) == 9, (
            f"Expected 9 scaffold files, found {len(scaffold_files)}: {scaffold_files}"
        )
        assert len(repo_files) == len(scaffold_files), (
            f"Repository has {len(repo_files)} files but scaffold has {len(scaffold_files)}"
        )

        # Verify file lists are identical
        assert repo_files == scaffold_files, (
            f"Scaffold files don't match repository.\n"
            f"Repo: {repo_files}\nScaffold: {scaffold_files}"
        )

        # Verify sdd.4-determine-test-strategy does NOT exist in scaffold
        assert not (SCAFFOLD_DIR / "sdd.4-determine-test-strategy.prompt.md").exists(), (
            "sdd.4-determine-test-strategy.prompt.md should be deleted from scaffold"
        )

        # Verify sdd.6c does NOT exist in scaffold
        assert not (SCAFFOLD_DIR / "sdd.6c-acceptance-test.prompt.md").exists(), (
            "sdd.6c-acceptance-test.prompt.md should not exist in scaffold"
        )

    def test_at_003_stages_yaml_configuration_validation(self):
        """
        AT-003: Verify stages.yaml references correct new prompt file paths.

        Expected: All prompt_template paths point to existing files with new numbering;
                  no references to old sdd.4-determine-test-strategy
        """
        # Load stages.yaml
        with open(STAGES_YAML) as f:
            stages_config = yaml.safe_load(f)

        # Extract all prompt_template values
        prompt_templates = {}
        for stage_name, stage_config in stages_config.get("stages", {}).items():
            if "prompt_template" in stage_config:
                prompt_templates[stage_name] = stage_config["prompt_template"]

        # Verify specific stage mappings
        expected_mappings = {
            "PLAN": ".agent/commands/sdd/sdd.4-task-planner-for-feature.prompt.md",
            "PLAN_REVIEW": ".agent/commands/sdd/sdd.5-review-plan.prompt.md",
            "IMPLEMENTATION": ".agent/commands/sdd/sdd.6-task-implementer-for-feature.prompt.md",
            "IMPLEMENTATION_REVIEW": ".agent/commands/sdd/sdd.6b-implementation-review.prompt.md",
            "POST_REVIEW": ".agent/commands/sdd/sdd.7-post-implementation-review.prompt.md",
        }

        for stage_name, expected_path in expected_mappings.items():
            actual_path = prompt_templates.get(stage_name)
            assert actual_path == expected_path, (
                f"Stage {stage_name}: expected '{expected_path}', got '{actual_path}'"
            )

            # Verify file actually exists
            full_path = REPO_ROOT / expected_path
            assert full_path.exists(), (
                f"Prompt file referenced by {stage_name} does not exist: {expected_path}"
            )

        # Verify no references to old sdd.4-determine-test-strategy
        stages_yaml_content = STAGES_YAML.read_text(encoding="utf-8")
        assert "sdd.4-determine-test-strategy" not in stages_yaml_content, (
            "Found reference to old sdd.4-determine-test-strategy in stages.yaml"
        )

        # Also check scaffold stages.yaml
        with open(SCAFFOLD_STAGES_YAML) as f:
            scaffold_stages_config = yaml.safe_load(f)

        scaffold_prompt_templates = {}
        for stage_name, stage_config in scaffold_stages_config.get("stages", {}).items():
            if "prompt_template" in stage_config:
                scaffold_prompt_templates[stage_name] = stage_config["prompt_template"]

        # Verify scaffold matches repository
        for stage_name, expected_path in expected_mappings.items():
            scaffold_path = scaffold_prompt_templates.get(stage_name)
            assert scaffold_path == expected_path, (
                f"Scaffold stage {stage_name}: expected '{expected_path}', got '{scaffold_path}'"
            )

    def test_at_004_full_workflow_execution_simulation(self):
        """
        AT-004: Verify workflow can load all prompt files correctly.

        This is a simulation test - we verify all prompt files referenced in stages.yaml
        can be loaded and are valid markdown files.
        """
        # Load stages.yaml
        with open(STAGES_YAML) as f:
            stages_config = yaml.safe_load(f)

        # For each stage with a prompt_template, verify the file can be loaded
        stages_with_prompts = [
            "PLAN",
            "PLAN_REVIEW",
            "IMPLEMENTATION",
            "IMPLEMENTATION_REVIEW",
            "POST_REVIEW",
        ]

        for stage_name in stages_with_prompts:
            stage_config = stages_config["stages"][stage_name]
            prompt_path = stage_config.get("prompt_template")

            assert prompt_path is not None, f"Stage {stage_name} missing prompt_template"

            full_path = REPO_ROOT / prompt_path
            assert full_path.exists(), f"Prompt file for {stage_name} does not exist: {prompt_path}"

            # Verify file can be read and contains content
            content = full_path.read_text(encoding="utf-8")
            assert len(content) > 0, f"Prompt file {prompt_path} is empty"
            # Prompt files may start with YAML frontmatter (---) or markdown heading (#)
            assert content.strip().startswith(("---", "#")), (
                f"Prompt file {prompt_path} doesn't appear to be valid "
                f"(no YAML frontmatter or markdown heading)"
            )

    def test_at_005_test_suite_validation(self):
        """
        AT-005: Verify post-renumbering invariants hold for the prompt configuration.

        Validates directly using the underlying helpers:
        - All prompt templates in stages.yaml reference existing files
        - No orphaned (old-numbered) prompts remain
        - tests/test_prompt_sync.py contains no references to old file names
        """
        from teambot.prompt_sync import (
            PromptValidationError,
            detect_orphaned_prompts,
            validate_prompt_files,
        )

        # Verify all prompt templates referenced in stages.yaml exist
        try:
            validate_prompt_files(REPO_ROOT)
        except PromptValidationError as exc:
            pytest.fail(f"Prompt validation failed after renumbering:\n{exc}")

        # Verify no orphaned prompts (old-numbered files left behind)
        orphaned = detect_orphaned_prompts(REPO_ROOT)
        assert orphaned == [], (
            f"Found orphaned prompt files after renumbering (old files not deleted): {orphaned}"
        )

        # Verify tests/test_prompt_sync.py does not reference old file names
        test_file_content = (REPO_ROOT / "tests" / "test_prompt_sync.py").read_text(
            encoding="utf-8"
        )
        old_patterns = [
            "sdd.4-determine-test-strategy",
            "sdd.5-task-planner",  # Old name
            "sdd.6-review-plan",  # Old name
            "sdd.7-task-implementer",  # Old name
            "sdd.7b-implementation",  # Old name
            "sdd.8-post",  # Old name
        ]

        for pattern in old_patterns:
            assert pattern not in test_file_content, (
                f"Found old file name pattern '{pattern}' in tests/test_prompt_sync.py"
            )

    def test_at_006_scaffold_initialization_test(self, tmp_path, monkeypatch):
        """
        AT-006: Verify `teambot init` creates correctly numbered prompt files.

        Expected: 9 prompt files created (sdd.0-7 with sdd.6b); no sdd.4-test-strategy or sdd.6c
        """
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Run teambot init directly (faster and hermetic — no subprocess/uv dependency)
        args = argparse.Namespace(force=False)
        return_code = cmd_init(args, ConsoleDisplay())

        # Check command succeeded
        assert return_code == 0, "teambot init returned non-zero exit code"

        # Check created prompt files
        sdd_dir = tmp_path / ".agent" / "commands" / "sdd"
        assert sdd_dir.exists(), ".agent/commands/sdd directory was not created"

        prompt_files = sorted(sdd_dir.glob("sdd.*.prompt.md"))
        prompt_names = [f.name for f in prompt_files]

        # Verify count: 9 files
        assert len(prompt_files) == 9, (
            f"Expected 9 prompt files, found {len(prompt_files)}: {prompt_names}"
        )

        # Verify sdd.4-determine-test-strategy does NOT exist
        assert not (sdd_dir / "sdd.4-determine-test-strategy.prompt.md").exists(), (
            "sdd.4-determine-test-strategy.prompt.md should not be created"
        )

        # Verify sdd.6c does NOT exist
        assert not (sdd_dir / "sdd.6c-acceptance-test.prompt.md").exists(), (
            "sdd.6c-acceptance-test.prompt.md should not be created"
        )

        # Verify sdd.4-task-planner DOES exist
        assert (sdd_dir / "sdd.4-task-planner-for-feature.prompt.md").exists(), (
            "sdd.4-task-planner-for-feature.prompt.md should be created"
        )

        # Verify all expected files exist
        expected_files = [
            "sdd.0-initialize.prompt.md",
            "sdd.1-create-feature-spec.prompt.md",
            "sdd.2-review-spec.prompt.md",
            "sdd.3-research-feature.prompt.md",
            "sdd.4-task-planner-for-feature.prompt.md",
            "sdd.5-review-plan.prompt.md",
            "sdd.6-task-implementer-for-feature.prompt.md",
            "sdd.6b-implementation-review.prompt.md",
            "sdd.7-post-implementation-review.prompt.md",
        ]

        assert prompt_names == expected_files, (
            f"Created files don't match expected.\n"
            f"Expected: {expected_files}\nActual: {prompt_names}"
        )

    def test_at_007_documentation_accuracy_validation(self):
        """
        AT-007: Verify all documentation reflects new numbering scheme.

        Expected: No references to old file names; workflow diagrams show 9-step process
        """
        # Check README.md
        readme_path = AGENT_DIR / "README.md"
        readme_content = readme_path.read_text(encoding="utf-8")

        # Verify no references to old sdd.4-determine-test-strategy
        assert "sdd.4-determine-test-strategy" not in readme_content, (
            "Found reference to old sdd.4-determine-test-strategy in README.md"
        )

        # Verify sdd.6c is not listed as an actual file (it's okay to mention it doesn't exist)
        # Check the workflow diagram doesn't list sdd.6c as a step
        lines = readme_content.split("\n")
        workflow_diagram_started = False
        for line in lines:
            if "```" in line and not workflow_diagram_started:
                workflow_diagram_started = True
                continue
            if workflow_diagram_started and "```" in line:
                break
            if workflow_diagram_started and "sdd.6c-acceptance-test.prompt.md" in line:
                pytest.fail(
                    "Workflow diagram incorrectly lists sdd.6c-acceptance-test.prompt.md as a step"
                )

        # Check AGENTS.md
        agents_md_path = REPO_ROOT / "AGENTS.md"
        agents_content = agents_md_path.read_text(encoding="utf-8")

        # Count SDD entries in table
        sdd_entries = agents_content.count("| `commands/sdd/sdd.")
        assert sdd_entries == 9, f"Expected 9 SDD entries in AGENTS.md, found {sdd_entries}"

        # Verify no references to old files
        assert "sdd.4-determine-test-strategy" not in agents_content, (
            "Found reference to old sdd.4-determine-test-strategy in AGENTS.md"
        )

        # Verify no references to sdd.6c
        assert "sdd.6c-acceptance-test" not in agents_content, (
            "Found reference to sdd.6c-acceptance-test in AGENTS.md"
        )

        # Verify correct new file names are present
        assert "sdd.4-task-planner-for-feature" in agents_content, (
            "Missing reference to sdd.4-task-planner-for-feature in AGENTS.md"
        )
        assert "sdd.5-review-plan" in agents_content, (
            "Missing reference to sdd.5-review-plan in AGENTS.md"
        )
        assert "sdd.6-task-implementer-for-feature" in agents_content, (
            "Missing reference to sdd.6-task-implementer-for-feature in AGENTS.md"
        )
        assert "sdd.6b-implementation-review" in agents_content, (
            "Missing reference to sdd.6b-implementation-review in AGENTS.md"
        )
        assert "sdd.7-post-implementation-review" in agents_content, (
            "Missing reference to sdd.7-post-implementation-review in AGENTS.md"
        )

        # Check scaffold AGENTS.md too
        scaffold_agents_md = REPO_ROOT / "src" / "teambot" / "scaffolds" / "AGENTS.md"
        scaffold_agents_content = scaffold_agents_md.read_text(encoding="utf-8")

        sdd_entries_scaffold = scaffold_agents_content.count("| `commands/sdd/sdd.")
        assert sdd_entries_scaffold == 9, (
            f"Expected 9 SDD entries in scaffold AGENTS.md, found {sdd_entries_scaffold}"
        )

        assert "sdd.4-determine-test-strategy" not in scaffold_agents_content, (
            "Found reference to old sdd.4-determine-test-strategy in scaffold AGENTS.md"
        )
        assert "sdd.6c-acceptance-test" not in scaffold_agents_content, (
            "Found reference to sdd.6c-acceptance-test in scaffold AGENTS.md"
        )
