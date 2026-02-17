"""Acceptance tests for init scaffolding feature."""

import argparse

import pytest


@pytest.mark.acceptance
class TestInitScaffoldingAcceptance:
    """Acceptance tests matching spec acceptance criteria."""

    def test_at_001_fresh_repository_initialization(self, tmp_path, monkeypatch):
        """AT-001: Fresh init copies all scaffolding files."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0

        # All 5 scaffold items exist
        assert (tmp_path / "stages.yaml").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / "docs" / "sdd-objective-template.md").exists()
        assert (tmp_path / ".github" / "agents" / "pm.agent.md").exists()
        assert (tmp_path / ".agent" / "commands").exists()

    def test_at_002_reinit_preserves_existing_files(self, tmp_path, monkeypatch):
        """AT-002: Re-init never overwrites existing files."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # First init
        cmd_init(argparse.Namespace(force=False), ConsoleDisplay())

        # Modify files
        (tmp_path / "stages.yaml").write_text("MODIFIED")

        # Re-init without force (need to remove config first since it blocks)
        (tmp_path / "teambot.json").unlink()

        cmd_init(argparse.Namespace(force=False), ConsoleDisplay())

        # File should still have modified content
        assert (tmp_path / "stages.yaml").read_text() == "MODIFIED"

    def test_at_003_partial_state_fills_gaps(self, tmp_path, monkeypatch):
        """AT-003: Partial init copies only missing resources."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create only some files manually
        (tmp_path / "AGENTS.md").write_text("custom")

        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        # Custom file preserved
        assert (tmp_path / "AGENTS.md").read_text() == "custom"
        # Missing files created
        assert (tmp_path / "stages.yaml").exists()
        assert (tmp_path / ".agent").exists()

    def test_at_004_empty_directory_handling(self, tmp_path, monkeypatch):
        """AT-004: Empty .github/agents/ gets populated."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create empty directory
        (tmp_path / ".github" / "agents").mkdir(parents=True)

        args = argparse.Namespace(force=False)
        cmd_init(args, ConsoleDisplay())

        # Directory should be populated
        assert (tmp_path / ".github" / "agents" / "pm.agent.md").exists()
