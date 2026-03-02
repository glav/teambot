"""Acceptance tests for SDD prompt sync feature (AT-001 through AT-006).

Core logic is tested directly; selective mocking is used only for
external dependencies (filesystem operations via tmp_path fixture).
"""

import pytest


@pytest.mark.acceptance
class TestPromptSyncAcceptance:
    """Acceptance tests for SDD prompt sync feature."""

    def test_at_001_incremental_sync_adds_missing_files(self, tmp_path, mocker):
        """AT-001: Incremental sync adds missing files while preserving existing.

        Scenario: User upgrades TeamBot and runs init to get new prompt files
        while preserving their customizations.

        Expected: 2 new files copied, 1 existing file preserved unchanged.
        """
        from teambot.prompt_sync import sync_sdd_prompts

        # Setup scaffold with 3 files
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text("# Init v2")
        (scaffold_dir / "sdd.1-spec.prompt.md").write_text("# Spec v2")
        (scaffold_dir / "sdd.2-review.prompt.md").write_text("# Review v2")

        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds",
        )

        # Setup target with 1 existing customized file
        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        custom_content = "# My Custom Init - DO NOT OVERWRITE"
        (target_dir / "sdd.0-initialize.prompt.md").write_text(custom_content)

        # Execute sync
        results = sync_sdd_prompts(target_root, force=False)

        # Verify results
        added = [r for r in results if r.copied]
        skipped = [r for r in results if not r.copied]

        assert len(added) == 2, "Expected 2 files added"
        assert len(skipped) == 1, "Expected 1 file skipped"

        # Verify existing file preserved
        existing_file = target_dir / "sdd.0-initialize.prompt.md"
        assert existing_file.read_text() == custom_content, "Custom content was overwritten!"

        # Verify new files were copied
        assert (target_dir / "sdd.1-spec.prompt.md").exists()
        assert (target_dir / "sdd.2-review.prompt.md").exists()

    def test_at_002_validation_blocks_run_when_prompt_missing(self, tmp_path):
        """AT-002: Validation blocks run when prompt file is missing.

        Scenario: stages.yaml references a prompt file that doesn't exist.

        Expected: PromptValidationError raised with actionable message.
        """
        from teambot.prompt_sync import PromptValidationError, validate_prompt_files

        # Setup stages.yaml referencing non-existent prompt
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    name: Setup
    description: Test stage
    work_agent: pm
    review_agent: null
    allowed_personas:
      - pm
    prompt_template: .agent/commands/sdd/sdd.99-missing.prompt.md
stage_order:
  - SETUP
work_to_review_mapping: {}
""")

        # No prompt file exists - validation should fail
        with pytest.raises(PromptValidationError) as exc_info:
            validate_prompt_files(tmp_path)

        error_msg = str(exc_info.value)

        # Verify error includes file path
        assert "sdd.99-missing.prompt.md" in error_msg

        # Verify error includes stage name
        assert "SETUP" in error_msg

        # Verify error includes remediation command (FR-005)
        assert "teambot init" in error_msg

    def test_at_003_orphaned_files_warning_non_blocking(self, tmp_path):
        """AT-003: Orphaned files detected but don't block validation.

        Scenario: User has prompt files not referenced by any stage.

        Expected: Orphaned files returned, validation still passes.
        """
        from teambot.prompt_sync import detect_orphaned_prompts, validate_prompt_files

        # Setup stages.yaml with no prompt templates
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  COMPLETE:
    name: Complete
    description: Complete stage
    work_agent: null
    review_agent: null
    allowed_personas: []
    prompt_template: null
stage_order:
  - COMPLETE
work_to_review_mapping: {}
""")

        # Create orphaned prompt file
        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "sdd.legacy.prompt.md").write_text("# Legacy prompt")

        # Validation should pass
        result = validate_prompt_files(tmp_path)
        assert result.valid is True

        # Orphan detection should find the file
        orphaned = detect_orphaned_prompts(tmp_path)
        assert len(orphaned) == 1
        assert "sdd.legacy.prompt.md" in orphaned[0]

    def test_at_005_force_flag_resets_all_prompt_files(self, tmp_path, mocker):
        """AT-005: Force flag resets all prompt files to defaults.

        Scenario: User wants to reset all prompts to bundled defaults.

        Expected: All prompt files replaced with scaffold versions.
        """
        from teambot.prompt_sync import sync_sdd_prompts

        # Setup scaffold with default content
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        default_content = "# Default scaffold content"
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text(default_content)

        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds",
        )

        # Setup target with customized file
        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        custom_content = "# My Custom Content"
        target_file = target_dir / "sdd.0-initialize.prompt.md"
        target_file.write_text(custom_content)

        # Execute sync with force=True
        results = sync_sdd_prompts(target_root, force=True)

        # Verify file was overwritten
        assert len(results) == 1
        assert results[0].copied is True
        assert results[0].reason == "added"

        # Verify content was replaced
        assert target_file.read_text() == default_content

    def test_at_006_skip_validation_flag_concept(self, tmp_path):
        """AT-006: Skip validation flag concept - validates the bypass works.

        Scenario: User runs with --skip-prompt-validation to bypass checks.

        Expected: Validation function can be skipped (tested at integration level).

        Note: This tests the concept that validation can be skipped.
        The actual CLI flag is tested via CLI tests.
        """
        from teambot.prompt_sync import validate_prompt_files

        # Setup stages.yaml referencing missing prompt
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    name: Setup
    description: Test stage
    work_agent: pm
    review_agent: null
    allowed_personas:
      - pm
    prompt_template: .agent/commands/sdd/sdd.99-missing.prompt.md
stage_order:
  - SETUP
work_to_review_mapping: {}
""")

        # When skipping validation, we simply don't call validate_prompt_files()
        # This test verifies the function exists and would fail if called
        from teambot.prompt_sync import PromptValidationError

        with pytest.raises(PromptValidationError):
            validate_prompt_files(tmp_path)

        # If user passes --skip-prompt-validation, the CLI skips this call
        # The implementation in cmd_run checks: if not skip_prompt_validation:
        # This is an integration concern, verified here conceptually

    def test_at_004_validation_passes_when_all_prompts_exist(self, tmp_path):
        """AT-004: Validation passes when all referenced prompts exist.

        Scenario: All prompt files referenced in stages.yaml exist.

        Expected: Validation passes without error.
        """
        from teambot.prompt_sync import validate_prompt_files

        # Setup stages.yaml referencing one prompt
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    name: Setup
    description: Test stage
    work_agent: pm
    review_agent: null
    allowed_personas:
      - pm
    prompt_template: .agent/commands/sdd/sdd.0-initialize.prompt.md
stage_order:
  - SETUP
work_to_review_mapping: {}
""")

        # Create the referenced prompt file
        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "sdd.0-initialize.prompt.md").write_text("# Test prompt")

        # Validation should pass
        result = validate_prompt_files(tmp_path)
        assert result.valid is True
        assert result.missing == []
