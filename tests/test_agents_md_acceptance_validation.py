"""Acceptance Validation Tests - AGENTS.md Objective Template Reference.

STRICT MODE: All tests call REAL implementation code - no mocking of core functionality.
Each test validates a specific acceptance scenario with test name `test_at_XXX_*`.
"""

import argparse

import pytest


@pytest.mark.acceptance
class TestAgentsMdAcceptanceValidation:
    """Strict validation of all acceptance scenarios for AGENTS.md update feature."""

    def test_at_001_fresh_init_no_existing_agents_md(self, tmp_path, monkeypatch):
        """AT-001: Fresh Init with No Existing AGENTS.md.

        Description: User runs `teambot init` in a new repository with no AGENTS.md

        Steps:
        1. Run `teambot init`
        2. Observe scaffold copy messages
        3. Check `AGENTS.md` content

        Expected: AGENTS.md is copied from scaffold (includes Objective Template section)
        """
        from teambot.cli import ConsoleDisplay, cmd_init

        # Arrange: Empty directory, no AGENTS.md
        monkeypatch.chdir(tmp_path)
        agents_md_path = tmp_path / "AGENTS.md"
        assert not agents_md_path.exists(), "Precondition: AGENTS.md should not exist"

        # Act: Run init
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()
        result = cmd_init(args, display)

        # Assert: AGENTS.md created with Objective Template section from scaffold
        assert result == 0, "cmd_init should succeed"
        assert agents_md_path.exists(), "AGENTS.md should be created"
        content = agents_md_path.read_text()
        assert "## Objective Template" in content, "Should have Objective Template section"
        assert "docs/sdd-objective-template.md" in content, "Should reference template path"

    def test_at_002_init_with_existing_agents_md_and_template_copied(self, tmp_path, monkeypatch):
        """AT-002: Init with Existing AGENTS.md and Template Copied.

        Description: User runs `teambot init` in repository with existing AGENTS.md
                     that doesn't mention the template

        Steps:
        1. Run `teambot init`
        2. Observe that AGENTS.md is skipped (exists)
        3. Observe that `docs/sdd-objective-template.md` is copied
        4. Check `AGENTS.md` content

        Expected: Original content preserved, new section appended
        """
        from teambot.cli import ConsoleDisplay, cmd_init

        # Arrange: Create existing AGENTS.md without reference
        monkeypatch.chdir(tmp_path)
        agents_md_path = tmp_path / "AGENTS.md"
        original_content = "# My Project\n\n## Development\n\nSome development notes.\n"
        agents_md_path.write_text(original_content)

        # Act: Run init
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()
        result = cmd_init(args, display)

        # Assert: Original preserved, reference appended
        assert result == 0, "cmd_init should succeed"
        content = agents_md_path.read_text()
        # Original content preserved exactly at start
        assert content.startswith(original_content.rstrip("\n")), (
            "Original content should be preserved"
        )
        # Reference added
        assert "## Objective Template" in content, "Should have Objective Template section"
        assert "docs/sdd-objective-template.md" in content, "Should reference template path"
        # Template file should exist
        assert (tmp_path / "docs" / "sdd-objective-template.md").exists(), (
            "Template should be copied"
        )

    def test_at_003_idempotent_run_reference_already_exists(self, tmp_path, monkeypatch):
        """AT-003: Idempotent Run - Reference Already Exists.

        Description: User runs `teambot init` multiple times

        Steps:
        1. Run `teambot init` (first time - adds reference)
        2. Run `teambot init` again (second time)
        3. Run `teambot init` again (third time)
        4. Check `AGENTS.md` content

        Expected: Only ONE Objective Template section, no duplicates
        """
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)
        agents_md_path = tmp_path / "AGENTS.md"
        agents_md_path.write_text("# My Project\n")

        args = argparse.Namespace(force=False)

        # First run - creates config and adds reference
        result1 = cmd_init(args, ConsoleDisplay())
        assert result1 == 0, "First init should succeed"

        # Second run - remove config to allow re-init
        (tmp_path / "teambot.json").unlink()
        result2 = cmd_init(args, ConsoleDisplay())
        assert result2 == 0, "Second init should succeed"

        # Third run - remove config to allow re-init
        (tmp_path / "teambot.json").unlink()
        result3 = cmd_init(args, ConsoleDisplay())
        assert result3 == 0, "Third init should succeed"

        # Assert: Exactly one reference
        content = agents_md_path.read_text()
        count = content.count("## Objective Template")
        assert count == 1, f"Expected exactly 1 Objective Template section, found {count}"

        # Also check docs/sdd-objective-template.md reference count
        ref_count = content.count("docs/sdd-objective-template.md")
        assert ref_count == 1, f"Expected exactly 1 template reference, found {ref_count}"

    def test_at_004_template_not_copied_already_exists(self, tmp_path, monkeypatch):
        """AT-004: Template Not Copied (Already Exists).

        Description: User runs `teambot init` when template already exists

        Steps:
        1. Run `teambot init`
        2. Observe that template is skipped (exists)
        3. Check `AGENTS.md` content

        Expected: AGENTS.md is NOT updated (template wasn't copied this run)
        """
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Arrange: Create AGENTS.md without reference
        agents_md_path = tmp_path / "AGENTS.md"
        original_content = "# My Project\n"
        agents_md_path.write_text(original_content)

        # Create pre-existing template file
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "sdd-objective-template.md").write_text("# Existing template")

        # Act: Run init
        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        # Assert: AGENTS.md unchanged (template wasn't newly copied)
        content = agents_md_path.read_text()
        assert content == original_content, "AGENTS.md should be unchanged"
        assert "## Objective Template" not in content, "Should NOT have section added"

    def test_at_005_empty_agents_md_file(self, tmp_path, monkeypatch):
        """AT-005: Empty AGENTS.md File.

        Description: User has an empty AGENTS.md file

        Steps:
        1. Run `teambot init`
        2. Check `AGENTS.md` content

        Expected: Objective Template section appended, file contains section
        """
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Arrange: Create empty AGENTS.md
        agents_md_path = tmp_path / "AGENTS.md"
        agents_md_path.write_text("")

        # Act: Run init
        args = argparse.Namespace(force=False)
        result = cmd_init(args, ConsoleDisplay())

        # Assert: Section appended to empty file
        assert result == 0, "cmd_init should succeed"
        content = agents_md_path.read_text()
        assert "## Objective Template" in content, "Should have Objective Template section"
        assert len(content) > 0, "File should no longer be empty"

    def test_at_006_force_flag_behavior(self, tmp_path, monkeypatch):
        """AT-006: Force Flag Behavior.

        Description: User runs `teambot init --force` with existing AGENTS.md

        Steps:
        1. Run `teambot init --force`
        2. Check `AGENTS.md` content

        Expected: AGENTS.md OVERWRITTEN with scaffold template, no update logic runs
        """
        from teambot.cli import ConsoleDisplay, cmd_init
        from teambot.scaffolds import get_scaffolds_dir

        monkeypatch.chdir(tmp_path)

        # Arrange: Create AGENTS.md with custom content
        agents_md_path = tmp_path / "AGENTS.md"
        agents_md_path.write_text("# Custom content that should be replaced")

        # First init (without force)
        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        # Act: Force re-init
        args = argparse.Namespace(force=True)
        result = cmd_init(args, ConsoleDisplay())

        # Assert: AGENTS.md matches scaffold template
        assert result == 0, "cmd_init --force should succeed"
        content = agents_md_path.read_text()

        # Custom content should be gone
        assert "Custom content" not in content, "Custom content should be replaced"

        # Should have exactly one Objective Template section (from scaffold)
        assert "## Objective Template" in content, "Should have Objective Template section"
        count = content.count("## Objective Template")
        assert count == 1, f"Expected 1 Objective Template section, found {count}"

        # Verify matches scaffold
        scaffold_agents_md = get_scaffolds_dir() / "AGENTS.md"
        scaffold_content = scaffold_agents_md.read_text()
        assert content == scaffold_content, "Should match scaffold template exactly"
