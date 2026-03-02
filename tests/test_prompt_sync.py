"""Unit tests for SDD prompt sync operations - TDD approach.

Core logic is tested directly; selective mocking is used only for
external dependencies (filesystem operations mocked via tmp_path fixture).
"""

from pathlib import Path

import pytest


class TestSyncResult:
    """Tests for SyncResult NamedTuple."""

    def test_sync_result_has_required_fields(self):
        """SyncResult has filename, target, copied, reason fields."""
        from teambot.prompt_sync import SyncResult

        result = SyncResult(
            filename="sdd.0-initialize.prompt.md",
            target=Path("/tmp/test"),
            copied=True,
            reason="added",
        )

        assert result.filename == "sdd.0-initialize.prompt.md"
        assert result.target == Path("/tmp/test")
        assert result.copied is True
        assert result.reason == "added"

    def test_sync_result_skipped_exists_reason(self):
        """SyncResult supports skipped_exists reason."""
        from teambot.prompt_sync import SyncResult

        result = SyncResult("test.md", Path("/tmp"), False, "skipped_exists")

        assert result.copied is False
        assert result.reason == "skipped_exists"

    def test_sync_result_is_namedtuple(self):
        """SyncResult is a NamedTuple with expected field order."""
        from teambot.prompt_sync import SyncResult

        result = SyncResult("file.md", Path("/tmp/target"), True, "added")

        # Verify can be unpacked like a tuple
        filename, target, copied, reason = result
        assert filename == "file.md"
        assert target == Path("/tmp/target")
        assert copied is True
        assert reason == "added"


class TestSyncSddPrompts:
    """Tests for sync_sdd_prompts() function."""

    def test_returns_empty_list_when_scaffold_dir_missing(self, tmp_path, mocker):
        """Returns empty list when scaffold directory doesn't exist."""
        from teambot.prompt_sync import sync_sdd_prompts

        # Mock get_scaffolds_dir to return non-existent path
        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "nonexistent",
        )

        results = sync_sdd_prompts(tmp_path)

        assert results == []

    def test_creates_target_directory_if_missing(self, tmp_path, mocker):
        """Creates .agent/commands/sdd/ if it doesn't exist."""
        from teambot.prompt_sync import sync_sdd_prompts

        # Setup scaffold with one file
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text("# Test")

        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds",
        )

        target_root = tmp_path / "project"
        target_root.mkdir()

        results = sync_sdd_prompts(target_root)

        assert (target_root / ".agent" / "commands" / "sdd").exists()
        assert len(results) == 1

    def test_adds_missing_file_when_target_empty(self, tmp_path, mocker):
        """Adds prompt file when target directory is empty."""
        from teambot.prompt_sync import sync_sdd_prompts

        # Setup scaffold with prompt file
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text("# Scaffold content")

        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds",
        )

        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)

        results = sync_sdd_prompts(target_root)

        assert len(results) == 1
        assert results[0].copied is True
        assert results[0].reason == "added"
        assert results[0].filename == "sdd.0-initialize.prompt.md"

        # Verify file was actually copied
        assert (target_dir / "sdd.0-initialize.prompt.md").read_text() == "# Scaffold content"

    def test_skips_existing_file_without_force(self, tmp_path, mocker):
        """Skips existing files - CRITICAL safety test."""
        from teambot.prompt_sync import sync_sdd_prompts

        # Setup scaffold
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text("# Scaffold version")

        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds",
        )

        # Setup existing customized file
        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        existing_file = target_dir / "sdd.0-initialize.prompt.md"
        existing_file.write_text("# My Custom Prompt - DO NOT OVERWRITE")
        original_content = existing_file.read_text()

        results = sync_sdd_prompts(target_root, force=False)

        assert len(results) == 1
        assert results[0].copied is False
        assert results[0].reason == "skipped_exists"

        # CRITICAL: Verify content unchanged
        assert existing_file.read_text() == original_content

    def test_overwrites_with_force_flag(self, tmp_path, mocker):
        """Overwrites existing files when force=True."""
        from teambot.prompt_sync import sync_sdd_prompts

        # Setup scaffold
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        scaffold_content = "# Scaffold version - SHOULD REPLACE"
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text(scaffold_content)

        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds",
        )

        # Setup existing file
        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        existing_file = target_dir / "sdd.0-initialize.prompt.md"
        existing_file.write_text("# Old content")

        results = sync_sdd_prompts(target_root, force=True)

        assert len(results) == 1
        assert results[0].copied is True
        assert results[0].reason == "added"

        # Verify content was overwritten
        assert existing_file.read_text() == scaffold_content

    def test_only_syncs_sdd_pattern_files(self, tmp_path, mocker):
        """Only syncs files matching sdd.*.prompt.md pattern."""
        from teambot.prompt_sync import sync_sdd_prompts

        # Setup scaffold with mixed files
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text("# SDD prompt")
        (scaffold_dir / "README.md").write_text("# README - should not sync")
        (scaffold_dir / "other.txt").write_text("Other file")

        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds",
        )

        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)

        results = sync_sdd_prompts(target_root)

        # Only sdd.*.prompt.md should be synced
        assert len(results) == 1
        assert results[0].filename == "sdd.0-initialize.prompt.md"

        # Verify README was NOT copied
        assert not (target_dir / "README.md").exists()

    def test_syncs_multiple_files_preserving_existing(self, tmp_path, mocker):
        """Syncs multiple files, preserving existing and adding new."""
        from teambot.prompt_sync import sync_sdd_prompts

        # Setup scaffold with 3 files
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.0-initialize.prompt.md").write_text("# Init")
        (scaffold_dir / "sdd.1-create-spec.prompt.md").write_text("# Spec")
        (scaffold_dir / "sdd.2-review.prompt.md").write_text("# Review")

        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds",
        )

        # Setup target with 1 existing file
        target_root = tmp_path / "project"
        target_dir = target_root / ".agent" / "commands" / "sdd"
        target_dir.mkdir(parents=True)
        (target_dir / "sdd.0-initialize.prompt.md").write_text("# Custom init")

        results = sync_sdd_prompts(target_root)

        added = [r for r in results if r.copied]
        skipped = [r for r in results if not r.copied]

        assert len(added) == 2
        assert len(skipped) == 1
        assert skipped[0].filename == "sdd.0-initialize.prompt.md"

    def test_results_are_sorted_by_filename(self, tmp_path, mocker):
        """Results are returned sorted by filename for predictable output."""
        from teambot.prompt_sync import sync_sdd_prompts

        # Setup scaffold with files in non-alphabetical order
        scaffold_dir = tmp_path / "scaffolds" / ".agent" / "commands" / "sdd"
        scaffold_dir.mkdir(parents=True)
        (scaffold_dir / "sdd.5-task.prompt.md").write_text("# 5")
        (scaffold_dir / "sdd.1-spec.prompt.md").write_text("# 1")
        (scaffold_dir / "sdd.3-research.prompt.md").write_text("# 3")

        mocker.patch(
            "teambot.prompt_sync.get_scaffolds_dir",
            return_value=tmp_path / "scaffolds",
        )

        target_root = tmp_path / "project"
        target_root.mkdir()

        results = sync_sdd_prompts(target_root)

        filenames = [r.filename for r in results]
        assert filenames == sorted(filenames)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_has_required_fields(self):
        """ValidationResult has valid, missing, orphaned fields."""
        from teambot.prompt_sync import ValidationResult

        result = ValidationResult(valid=True, missing=[], orphaned=[])

        assert result.valid is True
        assert result.missing == []
        assert result.orphaned == []

    def test_validation_result_with_missing_files(self):
        """ValidationResult can hold missing file tuples."""
        from teambot.prompt_sync import ValidationResult

        result = ValidationResult(
            valid=False,
            missing=[(".agent/commands/sdd/sdd.9-missing.prompt.md", "CLEANUP")],
            orphaned=[],
        )

        assert result.valid is False
        assert len(result.missing) == 1
        assert result.missing[0] == (
            ".agent/commands/sdd/sdd.9-missing.prompt.md",
            "CLEANUP",
        )


class TestPromptValidationError:
    """Tests for PromptValidationError exception."""

    def test_error_message_includes_missing_files(self):
        """Error message lists all missing files."""
        from teambot.prompt_sync import PromptValidationError

        error = PromptValidationError(
            [
                (".agent/commands/sdd/sdd.9-missing.prompt.md", "CLEANUP"),
                (".agent/commands/sdd/sdd.10-other.prompt.md", "DEPLOY"),
            ]
        )

        msg = str(error)
        assert "sdd.9-missing.prompt.md" in msg
        assert "sdd.10-other.prompt.md" in msg
        assert "CLEANUP" in msg
        assert "DEPLOY" in msg

    def test_error_message_includes_remediation_command(self):
        """Error message includes 'teambot init' remediation - FR-005."""
        from teambot.prompt_sync import PromptValidationError

        error = PromptValidationError(
            [
                (".agent/commands/sdd/sdd.9-missing.prompt.md", "CLEANUP"),
            ]
        )

        msg = str(error)
        assert "teambot init" in msg


class TestValidatePromptFiles:
    """Tests for validate_prompt_files() function."""

    def test_validation_passes_when_all_prompts_exist(self, tmp_path):
        """Validation passes when all referenced prompts exist."""
        from teambot.prompt_sync import validate_prompt_files

        # Setup stages.yaml referencing one prompt
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    prompt_template: .agent/commands/sdd/sdd.0-initialize.prompt.md
""")

        # Create the referenced prompt file
        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "sdd.0-initialize.prompt.md").write_text("# Test")

        result = validate_prompt_files(tmp_path)

        assert result.valid is True
        assert result.missing == []

    def test_validation_fails_with_missing_prompt(self, tmp_path):
        """Validation fails when referenced prompt is missing."""
        from teambot.prompt_sync import PromptValidationError, validate_prompt_files

        # Setup stages.yaml referencing non-existent prompt
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    prompt_template: .agent/commands/sdd/sdd.99-missing.prompt.md
""")

        with pytest.raises(PromptValidationError) as exc_info:
            validate_prompt_files(tmp_path)

        assert "sdd.99-missing.prompt.md" in str(exc_info.value)

    def test_validation_skips_null_prompt_template(self, tmp_path):
        """Validation ignores stages with null prompt_template."""
        from teambot.prompt_sync import validate_prompt_files

        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  COMPLETE:
    prompt_template: null
""")

        result = validate_prompt_files(tmp_path)

        assert result.valid is True

    def test_validation_returns_valid_when_no_stages_yaml(self, tmp_path):
        """Validation returns valid when stages.yaml doesn't exist."""
        from teambot.prompt_sync import validate_prompt_files

        # No stages.yaml in tmp_path
        result = validate_prompt_files(tmp_path)

        assert result.valid is True
        assert result.missing == []

    def test_error_includes_stage_name(self, tmp_path):
        """Error message includes the stage that requires the missing file."""
        from teambot.prompt_sync import PromptValidationError, validate_prompt_files

        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  RESEARCH:
    prompt_template: .agent/commands/sdd/sdd.3-research.prompt.md
""")

        with pytest.raises(PromptValidationError) as exc_info:
            validate_prompt_files(tmp_path)

        assert "RESEARCH" in str(exc_info.value)

    def test_validation_reports_multiple_missing_files(self, tmp_path):
        """Validation reports all missing files, not just first."""
        from teambot.prompt_sync import PromptValidationError, validate_prompt_files

        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    prompt_template: .agent/commands/sdd/sdd.0-init.prompt.md
  SPEC:
    prompt_template: .agent/commands/sdd/sdd.1-spec.prompt.md
""")

        with pytest.raises(PromptValidationError) as exc_info:
            validate_prompt_files(tmp_path)

        msg = str(exc_info.value)
        assert "sdd.0-init.prompt.md" in msg
        assert "sdd.1-spec.prompt.md" in msg


class TestDetectOrphanedPrompts:
    """Tests for detect_orphaned_prompts() function."""

    def test_returns_empty_when_all_prompts_referenced(self, tmp_path):
        """Returns empty list when all prompt files are referenced."""
        from teambot.prompt_sync import detect_orphaned_prompts

        # Setup stages.yaml referencing the prompt
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    prompt_template: .agent/commands/sdd/sdd.0-initialize.prompt.md
""")

        # Create the referenced prompt file
        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "sdd.0-initialize.prompt.md").write_text("# Test")

        orphaned = detect_orphaned_prompts(tmp_path)

        assert orphaned == []

    def test_detects_orphaned_sdd_prompt(self, tmp_path):
        """Detects SDD prompt files not referenced by any stage."""
        from teambot.prompt_sync import detect_orphaned_prompts

        # Setup stages.yaml with no prompts
        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  COMPLETE:
    prompt_template: null
""")

        # Create orphaned prompt file
        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "sdd.legacy.prompt.md").write_text("# Orphan")

        orphaned = detect_orphaned_prompts(tmp_path)

        assert len(orphaned) == 1
        assert ".agent/commands/sdd/sdd.legacy.prompt.md" in orphaned[0]

    def test_ignores_readme_files(self, tmp_path):
        """Does not report README.md as orphaned."""
        from teambot.prompt_sync import detect_orphaned_prompts

        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  COMPLETE:
    prompt_template: null
""")

        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "README.md").write_text("# SDD Commands")

        orphaned = detect_orphaned_prompts(tmp_path)

        assert orphaned == []

    def test_only_matches_sdd_pattern(self, tmp_path):
        """Only matches files with sdd.*.prompt.md pattern."""
        from teambot.prompt_sync import detect_orphaned_prompts

        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  COMPLETE:
    prompt_template: null
""")

        prompt_dir = tmp_path / ".agent" / "commands" / "sdd"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "other.prompt.md").write_text("# Not SDD pattern")
        (prompt_dir / "sdd.legacy.prompt.md").write_text("# SDD pattern")

        orphaned = detect_orphaned_prompts(tmp_path)

        assert len(orphaned) == 1
        assert "sdd.legacy.prompt.md" in orphaned[0]
        assert "other.prompt.md" not in str(orphaned)

    def test_returns_empty_when_sdd_dir_missing(self, tmp_path):
        """Returns empty list when .agent/commands/sdd/ doesn't exist."""
        from teambot.prompt_sync import detect_orphaned_prompts

        stages_yaml = tmp_path / "stages.yaml"
        stages_yaml.write_text("""
stages:
  SETUP:
    prompt_template: .agent/commands/sdd/sdd.0-init.prompt.md
""")

        # No .agent directory
        orphaned = detect_orphaned_prompts(tmp_path)

        assert orphaned == []
