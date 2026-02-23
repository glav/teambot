"""Acceptance Validation Tests - Integration tests exercising REAL implementation.

These tests call the real implementation code - no mocking of core functionality.
Each test validates a specific acceptance scenario for AGENTS.md update feature.
"""

import argparse

import pytest


@pytest.mark.acceptance
class TestAcceptanceScenarios:
    """Strict acceptance validation tests calling real implementation."""

    def test_at_001_fresh_init_with_no_existing_agents_md(self, tmp_path, monkeypatch):
        """AT-001: Fresh init with no existing AGENTS.md.

        User runs `teambot init` in a new repository with no AGENTS.md.
        Expected: AGENTS.md is copied from scaffold (includes Objective Template section).
        """
        from teambot.cli import ConsoleDisplay, cmd_init

        # Arrange: Empty directory (no AGENTS.md)
        monkeypatch.chdir(tmp_path)
        assert not (tmp_path / "AGENTS.md").exists()

        # Act: Run real cmd_init
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()
        result = cmd_init(args, display)

        # Assert: AGENTS.md created from scaffold with Objective Template section
        assert result == 0
        agents_md = tmp_path / "AGENTS.md"
        assert agents_md.exists()
        content = agents_md.read_text()
        assert "## Objective Template" in content
        # Verify it's the scaffold template (has specific content)
        assert "TeamBot provides an objective template" in content

    def test_at_002_init_with_existing_agents_md_and_template_copied(self, tmp_path, monkeypatch):
        """AT-002: Init with existing AGENTS.md and template copied.

        User runs `teambot init` in repo with existing AGENTS.md that doesn't
        mention the template.
        Expected: Original content preserved, new section appended.
        """
        from teambot.cli import ConsoleDisplay, cmd_init

        # Arrange: Create existing AGENTS.md without template reference
        monkeypatch.chdir(tmp_path)
        original_content = """# My Project AGENTS.md

## Overview

This is my custom project documentation.

## Guidelines

- Follow coding standards
- Write tests
"""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(original_content)

        # Act: Run real cmd_init
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()
        result = cmd_init(args, display)

        # Assert
        assert result == 0
        content = agents_md.read_text()

        # Original content preserved exactly at the start
        assert content.startswith("# My Project AGENTS.md")
        assert "This is my custom project documentation." in content
        assert "Follow coding standards" in content

        # New section appended
        assert "## Objective Template" in content
        assert "docs/sdd-objective-template.md" in content

        # Verify template was copied
        assert (tmp_path / "docs" / "sdd-objective-template.md").exists()

    def test_at_003_idempotent_run_reference_already_exists(self, tmp_path, monkeypatch):
        """AT-003: Idempotent run - reference already exists.

        User runs `teambot init` multiple times.
        Expected: Only ONE "Objective Template" section exists.
        """
        from teambot.cli import ConsoleDisplay, cmd_init

        # Arrange: Create existing AGENTS.md without reference
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n\n## Development\n")

        # Act: Run init THREE times
        args = argparse.Namespace(force=False)

        # First run - adds reference
        cmd_init(args, ConsoleDisplay())

        # Need to remove config to allow re-init
        (tmp_path / "teambot.json").unlink()

        # Second run
        cmd_init(args, ConsoleDisplay())
        (tmp_path / "teambot.json").unlink()

        # Third run
        cmd_init(args, ConsoleDisplay())

        # Assert: Exactly ONE Objective Template section
        content = agents_md.read_text()
        count = content.count("## Objective Template")
        assert count == 1, f"Expected 1 'Objective Template' section, found {count}"

        # Also verify the template reference appears once
        ref_count = content.count("docs/sdd-objective-template.md")
        assert ref_count == 1, f"Expected 1 reference to template, found {ref_count}"

    def test_at_004_template_not_copied_already_exists(self, tmp_path, monkeypatch):
        """AT-004: Template not copied (already exists).

        User runs `teambot init` when template already exists.
        Expected: AGENTS.md is NOT updated (template wasn't copied this run).
        """
        from teambot.cli import ConsoleDisplay, cmd_init

        # Arrange: Create AGENTS.md AND template file (both pre-existing)
        monkeypatch.chdir(tmp_path)
        original_content = "# My Existing AGENTS.md\n\n## Section\n"
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(original_content)

        # Pre-create the template file
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "sdd-objective-template.md").write_text("# Pre-existing template")

        # Act: Run real cmd_init
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()
        result = cmd_init(args, display)

        # Assert: AGENTS.md unchanged (template wasn't copied, so no update)
        assert result == 0
        content = agents_md.read_text()
        assert content == original_content, "AGENTS.md should be unchanged"
        assert "## Objective Template" not in content

    def test_at_005_empty_agents_md_file(self, tmp_path, monkeypatch):
        """AT-005: Empty AGENTS.md file.

        User has an empty AGENTS.md file.
        Expected: Objective Template section appended.
        """
        from teambot.cli import ConsoleDisplay, cmd_init

        # Arrange: Create empty AGENTS.md
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("")

        # Act: Run real cmd_init
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()
        result = cmd_init(args, display)

        # Assert: File now contains the section
        assert result == 0
        content = agents_md.read_text()
        assert "## Objective Template" in content
        assert "docs/sdd-objective-template.md" in content

    def test_at_006_force_flag_behavior(self, tmp_path, monkeypatch):
        """AT-006: Force flag behavior.

        User runs `teambot init --force` with existing AGENTS.md.
        Expected: AGENTS.md is OVERWRITTEN with scaffold template.
        """
        from teambot.cli import ConsoleDisplay, cmd_init
        from teambot.scaffolds import get_scaffolds_dir

        # Arrange: Create custom AGENTS.md
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Custom Content That Should Be Replaced\n")

        # Get expected scaffold content
        scaffold_agents_md = get_scaffolds_dir() / "AGENTS.md"
        expected_content = scaffold_agents_md.read_text()

        # Act: Run with force=True
        args = argparse.Namespace(force=True)
        display = ConsoleDisplay()
        result = cmd_init(args, display)

        # Assert: AGENTS.md matches scaffold exactly (was overwritten)
        assert result == 0
        content = agents_md.read_text()

        # Custom content should be GONE
        assert "My Custom Content That Should Be Replaced" not in content

        # Should match scaffold template
        assert content == expected_content

        # Scaffold has Objective Template section
        assert "## Objective Template" in content
