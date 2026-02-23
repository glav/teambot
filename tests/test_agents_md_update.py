"""Tests for AGENTS.md update functionality in teambot init."""

from pathlib import Path

import pytest

from teambot.scaffolds import CopyResult

# === Test Fixtures ===


@pytest.fixture
def agents_md_without_reference():
    """AGENTS.md content without objective template reference."""
    return """# AGENTS.md

## Project Overview
This is a sample project.

## Development Guidelines
- Follow coding standards
- Write tests
"""


@pytest.fixture
def agents_md_with_reference():
    """AGENTS.md content that already has the reference."""
    return """# AGENTS.md

## Project Overview
This is a sample project.

## Objective Template

TeamBot provides an objective template for defining development tasks:

| File | Description |
|------|-------------|
| `docs/sdd-objective-template.md` | Template for creating TeamBot objectives. |
"""


@pytest.fixture
def empty_agents_md():
    """Empty AGENTS.md file."""
    return ""


# === Test Classes ===


class TestAgentsMdHasTemplateReference:
    """Tests for _agents_md_has_template_reference() function."""

    def test_returns_true_when_reference_exists(self, tmp_path, agents_md_with_reference):
        """Returns True when AGENTS.md contains the reference section."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_with_reference)

        from teambot.cli import _agents_md_has_template_reference

        result = _agents_md_has_template_reference(agents_md)

        assert result is True

    def test_returns_false_when_no_reference(self, tmp_path, agents_md_without_reference):
        """Returns False when AGENTS.md lacks the reference section."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_without_reference)

        from teambot.cli import _agents_md_has_template_reference

        result = _agents_md_has_template_reference(agents_md)

        assert result is False

    def test_returns_false_for_empty_file(self, tmp_path):
        """Returns False for empty AGENTS.md."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("")

        from teambot.cli import _agents_md_has_template_reference

        result = _agents_md_has_template_reference(agents_md)

        assert result is False

    def test_returns_false_for_missing_file(self, tmp_path):
        """Returns False when file doesn't exist."""
        agents_md = tmp_path / "AGENTS.md"

        from teambot.cli import _agents_md_has_template_reference

        result = _agents_md_has_template_reference(agents_md)

        assert result is False


class TestShouldUpdateAgentsMd:
    """Tests for _should_update_agents_md() function."""

    def test_returns_true_when_template_copied_and_agents_skipped(self):
        """Returns True when template copied AND AGENTS.md skipped."""
        from teambot.cli import _should_update_agents_md

        results = [
            CopyResult(
                "sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]

        assert _should_update_agents_md(results) is True

    def test_returns_false_when_template_not_copied(self):
        """Returns False when template was not copied (already exists)."""
        from teambot.cli import _should_update_agents_md

        results = [
            CopyResult(
                "sdd-objective-template.md",
                Path("docs/sdd-objective-template.md"),
                False,
                "skipped_exists",
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]

        assert _should_update_agents_md(results) is False

    def test_returns_false_when_agents_freshly_copied(self):
        """Returns False when AGENTS.md was freshly copied (has reference)."""
        from teambot.cli import _should_update_agents_md

        results = [
            CopyResult(
                "sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), True, "copied"),
        ]

        assert _should_update_agents_md(results) is False

    def test_returns_false_when_both_skipped(self):
        """Returns False when both files already existed."""
        from teambot.cli import _should_update_agents_md

        results = [
            CopyResult(
                "sdd-objective-template.md",
                Path("docs/sdd-objective-template.md"),
                False,
                "skipped_exists",
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]

        assert _should_update_agents_md(results) is False

    def test_handles_missing_results(self):
        """Returns False when neither result is present."""
        from teambot.cli import _should_update_agents_md

        results = [
            CopyResult("stages.yaml", Path("stages.yaml"), True, "copied"),
        ]

        assert _should_update_agents_md(results) is False


class TestUpdateAgentsMdWithTemplateReference:
    """Tests for _update_agents_md_with_template_reference() function."""

    def test_appends_reference_when_conditions_met(self, tmp_path, agents_md_without_reference):
        """Appends reference section when all conditions are met."""
        from teambot.cli import _update_agents_md_with_template_reference

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_without_reference)

        results = [
            CopyResult(
                "sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]

        updated = _update_agents_md_with_template_reference(results, tmp_path, display=None)

        assert updated is True
        content = agents_md.read_text()
        assert "## Objective Template" in content
        assert "docs/sdd-objective-template.md" in content

    def test_skips_when_reference_exists(self, tmp_path, agents_md_with_reference):
        """Skips update when reference already exists."""
        from teambot.cli import _update_agents_md_with_template_reference

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_with_reference)
        original_content = agents_md.read_text()

        results = [
            CopyResult(
                "sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]

        updated = _update_agents_md_with_template_reference(results, tmp_path, display=None)

        assert updated is False
        assert agents_md.read_text() == original_content

    def test_preserves_existing_content_exactly(self, tmp_path):
        """Original content is preserved exactly after update."""
        from teambot.cli import _update_agents_md_with_template_reference

        agents_md = tmp_path / "AGENTS.md"
        original = "# AGENTS\n\n## Section 1\n\nContent with special chars: 日本語\n"
        agents_md.write_text(original)

        results = [
            CopyResult(
                "sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]

        _update_agents_md_with_template_reference(results, tmp_path, display=None)

        content = agents_md.read_text()
        assert content.startswith(original.rstrip("\n"))

    def test_returns_false_when_conditions_not_met(self, tmp_path, agents_md_without_reference):
        """Returns False when trigger conditions are not met."""
        from teambot.cli import _update_agents_md_with_template_reference

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_without_reference)

        # Template was not copied
        results = [
            CopyResult(
                "sdd-objective-template.md",
                Path("docs/sdd-objective-template.md"),
                False,
                "skipped_exists",
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]

        updated = _update_agents_md_with_template_reference(results, tmp_path, display=None)

        assert updated is False

    def test_idempotent_multiple_runs(self, tmp_path, agents_md_without_reference):
        """Running update multiple times produces exactly one reference."""
        from teambot.cli import _update_agents_md_with_template_reference

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_without_reference)

        results = [
            CopyResult(
                "sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]

        # Run multiple times
        _update_agents_md_with_template_reference(results, tmp_path, display=None)
        _update_agents_md_with_template_reference(results, tmp_path, display=None)
        _update_agents_md_with_template_reference(results, tmp_path, display=None)

        content = agents_md.read_text()
        count = content.count("## Objective Template")
        assert count == 1, f"Expected 1 reference, found {count}"

    def test_handles_empty_file(self, tmp_path):
        """Appends reference to empty AGENTS.md."""
        from teambot.cli import _update_agents_md_with_template_reference

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("")

        results = [
            CopyResult(
                "sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]

        updated = _update_agents_md_with_template_reference(results, tmp_path, display=None)

        assert updated is True
        content = agents_md.read_text()
        assert "## Objective Template" in content

    def test_handles_no_trailing_newline(self, tmp_path):
        """Handles AGENTS.md without trailing newline."""
        from teambot.cli import _update_agents_md_with_template_reference

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# AGENTS\n\nSome content")  # No trailing newline

        results = [
            CopyResult(
                "sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]

        _update_agents_md_with_template_reference(results, tmp_path, display=None)

        content = agents_md.read_text()
        # Should have proper separation (at least one newline before section)
        assert "## Objective Template" in content
        # Verify original content is preserved
        assert content.startswith("# AGENTS\n\nSome content")

    def test_handles_whitespace_only_file(self, tmp_path):
        """Appends reference to whitespace-only AGENTS.md."""
        from teambot.cli import _update_agents_md_with_template_reference

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("   \n\n   ")

        results = [
            CopyResult(
                "sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"
            ),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]

        updated = _update_agents_md_with_template_reference(results, tmp_path, display=None)

        assert updated is True
        content = agents_md.read_text()
        assert "## Objective Template" in content
