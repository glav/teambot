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
        """AT-004: No update when template already exists."""
        from teambot.cli import ConsoleDisplay, cmd_init

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
        # Reference should NOT be added (template was not newly copied)
        assert "## Objective Template" not in content
        # Original content preserved
        assert content == "# My Project\n"

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
