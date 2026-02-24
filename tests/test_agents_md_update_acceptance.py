"""Acceptance tests for AGENTS.md objective template reference update.

Core logic is tested directly; selective mocking is used for external dependencies.
"""

import argparse

import pytest


@pytest.mark.acceptance
class TestAgentsMdUpdateAcceptance:
    """Acceptance tests for AGENTS.md update during teambot init."""

    def test_at_001_appends_reference_when_template_copied_to_existing_agents(
        self, tmp_path, monkeypatch
    ):
        """AT-001: Section appended when template newly copied and AGENTS.md exists."""
        from teambot.cli import ConsoleDisplay, cmd_init

        # Arrange: Create existing AGENTS.md without reference
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n\n## Development\n")

        # Act: Run init
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()
        result = cmd_init(args, display)

        # Assert: Reference added
        assert result == 0
        content = agents_md.read_text()
        assert "## Objective Template" in content
        assert "docs/sdd-objective-template.md" in content
        # Original content preserved
        assert content.startswith("# My Project\n\n## Development\n")

    def test_at_002_no_duplicate_on_rerun(self, tmp_path, monkeypatch):
        """AT-002: Running init twice produces exactly one reference."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n")

        args = argparse.Namespace(force=False)

        # First run - creates config and adds reference
        cmd_init(args, ConsoleDisplay())

        # Re-run requires removing config first (init blocks on existing config)
        (tmp_path / "teambot.json").unlink()

        # Second run - should not add duplicate
        cmd_init(args, ConsoleDisplay())

        content = agents_md.read_text()
        count = content.count("## Objective Template")
        assert count == 1, f"Expected 1 reference, found {count}"

    def test_at_003_force_init_uses_bundled_agents_md(self, tmp_path, monkeypatch):
        """AT-003: Force init replaces AGENTS.md with bundled version (has reference)."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# Custom content without reference")

        # First init
        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        # Force re-init
        args = argparse.Namespace(force=True)
        cmd_init(args, ConsoleDisplay())

        content = agents_md.read_text()
        # Should have exactly one reference (from bundled AGENTS.md)
        assert "## Objective Template" in content
        count = content.count("## Objective Template")
        assert count == 1, f"Expected 1 reference, found {count}"
        # Custom content should be gone (replaced)
        assert "Custom content" not in content

    def test_at_004_template_exists_no_update(self, tmp_path, monkeypatch):
        """AT-004: No template update when template already exists."""
        from teambot.cli import AGENT_DIRECTORY_MARKER, ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create AGENTS.md without reference
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n")

        # Create template file (pre-existing)
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "sdd-objective-template.md").write_text("# Existing template")

        # Run init
        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        content = agents_md.read_text()
        # Template reference should NOT be added (template was not newly copied)
        assert "## Objective Template" not in content
        # But .agent directory reference IS added (.agent was newly copied)
        assert AGENT_DIRECTORY_MARKER in content
        # Original content preserved at start
        assert content.startswith("# My Project\n")

    def test_at_005_existing_reference_not_duplicated(self, tmp_path, monkeypatch):
        """AT-005: No duplicate when AGENTS.md already has reference."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create AGENTS.md WITH reference already
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n\n## Objective Template\n\nTemplate info here.\n")

        # Run init
        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        content = agents_md.read_text()
        count = content.count("## Objective Template")
        assert count == 1, f"Expected 1 reference, found {count}"

    def test_at_006_preserves_complex_content(self, tmp_path, monkeypatch):
        """AT-006: Complex AGENTS.md content is preserved exactly."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create complex AGENTS.md with special characters
        complex_content = """# AGENTS.md

## Overview

This project uses special characters: 日本語 中文 한국어

## Code Examples

```python
def hello():
    print("Hello, World!")
```

## Tables

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |

---

End of file.
"""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(complex_content)

        # Run init
        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        content = agents_md.read_text()
        # Original complex content preserved
        assert "日本語 中文 한국어" in content
        assert 'print("Hello, World!")' in content
        assert "| Column 1 | Column 2 |" in content
        # Reference added
        assert "## Objective Template" in content

    # === Acceptance tests for .agent directory reference ===

    def test_at_007_appends_agent_dir_reference_when_newly_copied(self, tmp_path, monkeypatch):
        """AT-007: .agent dir reference appended when .agent copied and AGENTS.md exists."""
        from teambot.cli import AGENT_DIRECTORY_MARKER, ConsoleDisplay, cmd_init

        # Arrange: Create existing AGENTS.md without .agent reference
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n\n## Development\n")
        # Note: .agent directory does NOT exist yet - will be copied

        # Act
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()
        result = cmd_init(args, display)

        # Assert
        assert result == 0
        content = agents_md.read_text()
        assert AGENT_DIRECTORY_MARKER in content
        # Original content preserved
        assert content.startswith("# My Project\n\n## Development\n")
        # Verify full section content (25 entries across 4 tables)
        assert "commands/sdd/sdd.0-initialize.prompt.md" in content
        assert "instructions/prompt.instructions.md" in content
        assert "standards/feature-spec-template.md" in content

    def test_at_008_no_agent_dir_reference_when_dir_exists(self, tmp_path, monkeypatch):
        """AT-008: No .agent reference added when .agent directory already existed."""
        from teambot.cli import AGENT_DIRECTORY_MARKER, ConsoleDisplay, cmd_init

        # Arrange: Create existing AGENTS.md and .agent directory
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n")

        # Create non-empty .agent directory (will be skipped)
        agent_dir = tmp_path / ".agent"
        agent_dir.mkdir()
        (agent_dir / "custom.md").write_text("Custom content")

        # Act
        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        # Assert: .agent reference NOT added (directory was skipped)
        content = agents_md.read_text()
        assert AGENT_DIRECTORY_MARKER not in content

    def test_at_009_no_duplicate_agent_dir_reference(self, tmp_path, monkeypatch):
        """AT-009: No duplicate .agent reference when running init twice."""
        from teambot.cli import AGENT_DIRECTORY_MARKER, ConsoleDisplay, cmd_init

        # Arrange
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n")

        # First init - adds .agent reference
        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        # Re-run requires removing config first
        (tmp_path / "teambot.json").unlink()

        # Second init - should NOT add duplicate
        cmd_init(args, ConsoleDisplay())

        # Assert
        content = agents_md.read_text()
        count = content.count(AGENT_DIRECTORY_MARKER)
        assert count == 1, f"Expected 1 .agent reference, found {count}"

    def test_at_010_both_references_added_on_fresh_existing_agents(self, tmp_path, monkeypatch):
        """AT-010: Both template AND .agent references added when applicable."""
        from teambot.cli import (
            AGENT_DIRECTORY_MARKER,
            ConsoleDisplay,
            cmd_init,
        )

        # Arrange: Create existing AGENTS.md without either reference
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n")
        # No .agent directory, no template file

        # Act
        args = argparse.Namespace(force=False)
        result = cmd_init(args, ConsoleDisplay())

        # Assert: Both references added
        assert result == 0
        content = agents_md.read_text()
        assert "## Objective Template" in content
        assert AGENT_DIRECTORY_MARKER in content
        # Original content preserved at start
        assert content.startswith("# My Project\n")

    def test_at_011_agent_dir_reference_contains_all_entries(self, tmp_path, monkeypatch):
        """AT-011: .agent reference section contains all expected table entries."""
        from teambot.cli import AGENT_DIRECTORY_MARKER, ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n\n## Overview\n\nThis is my project.\n")

        args = argparse.Namespace(force=False)
        result = cmd_init(args, ConsoleDisplay())

        assert result == 0
        content = agents_md.read_text()
        assert AGENT_DIRECTORY_MARKER in content

        # Commands table (4 entries)
        assert "commands/azdo/azdo.generate-pr-description.prompt.md" in content
        assert "commands/docs/docs.create-adr.prompt.md" in content
        assert "commands/project/proj.sprint-planning.prompt.md" in content
        assert "commands/setup/setup.agents-md-creation.prompt.md" in content

        # SDD workflow table (10 entries)
        assert "commands/sdd/README.md" in content
        assert "commands/sdd/sdd.0-initialize.prompt.md" in content
        assert "commands/sdd/sdd.1-create-feature-spec.prompt.md" in content
        assert "commands/sdd/sdd.8-post-implementation-review.prompt.md" in content

        # Instructions table (6 entries)
        assert "instructions/prompt.instructions.md" in content
        assert "instructions/bash/bash.instructions.md" in content
        assert "instructions/bicep/bicep.instructions.md" in content

        # Standards table (5 entries)
        assert "standards/decision-record-standards.md" in content
        assert "standards/feature-spec-template.md" in content
        assert "standards/task-planning-template.md" in content

    def test_at_012_permission_error_logged_and_init_continues(
        self, tmp_path, monkeypatch, mocker
    ):
        """AT-012: PermissionError on AGENTS.md write is logged; init does not crash."""
        import logging
        from pathlib import Path

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n")

        original_write = Path.write_text

        def mock_write_text(self, content, encoding=None):
            if self.name == "AGENTS.md":
                raise PermissionError("Access denied")
            return original_write(self, content, encoding=encoding)

        mocker.patch.object(Path, "write_text", mock_write_text)

        debug_logs = []
        original_debug = logging.debug

        def capture_debug(msg, *args, **kwargs):
            debug_logs.append(msg)
            return original_debug(msg, *args, **kwargs)

        mocker.patch("teambot.cli.logging.debug", capture_debug)

        args = argparse.Namespace(force=False)
        try:
            result = cmd_init(args, ConsoleDisplay())
            assert result is not None
        except PermissionError:
            pytest.fail("PermissionError should be caught, not raised")

        assert any(".agent reference" in log or "Failed to update" in log for log in debug_logs), (
            f"Expected debug log about permission error, got: {debug_logs}"
        )

    def test_at_013_case_insensitive_agent_dir_reference_detection(
        self, tmp_path, monkeypatch
    ):
        """AT-013: Existing .agent reference detected case-insensitively; no duplicate added."""
        from teambot.cli import AGENT_DIRECTORY_MARKER, ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        lowercase_marker = AGENT_DIRECTORY_MARKER.lower()
        agents_md.write_text(f"# My Project\n\n{lowercase_marker}\n\nSome content here.\n")

        args = argparse.Namespace(force=False)
        result = cmd_init(args, ConsoleDisplay())

        assert result == 0
        content = agents_md.read_text()
        count = content.lower().count(AGENT_DIRECTORY_MARKER.lower())
        assert count == 1, f"Expected 1 reference (case-insensitive), found {count}"
        assert lowercase_marker in content

    def test_at_014_empty_agents_md_gets_agent_dir_reference(self, tmp_path, monkeypatch):
        """AT-014: Empty AGENTS.md receives the .agent directory reference section."""
        from teambot.cli import AGENT_DIRECTORY_MARKER, ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("")

        args = argparse.Namespace(force=False)
        result = cmd_init(args, ConsoleDisplay())

        assert result == 0
        content = agents_md.read_text()
        assert AGENT_DIRECTORY_MARKER in content
        assert "## Copilot / AI Assisted Workflow" in content
        assert "| Path | Description |" in content
        assert "commands/sdd/" in content
        assert "instructions/" in content
        assert "standards/" in content
