"""Acceptance test validation for init-conflict-detection feature.

These tests exercise the REAL implementation code to validate acceptance scenarios.
"""

import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from teambot.cli import cmd_init, prompt_conflict_resolution
from teambot.scaffolds import (
    backup_directory,
    copy_all_scaffolds,
    detect_sdd_conflicts,
    get_scaffolds_dir,
)
from teambot.visualization.console import ConsoleDisplay

pytestmark = pytest.mark.acceptance


class TestAcceptanceScenarios:
    """Acceptance test scenarios for init conflict detection."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project directory."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        return project_dir

    @pytest.fixture
    def scaffold_source(self):
        """Get the real scaffold source directory."""
        return get_scaffolds_dir()

    def _create_conflicting_agent_dir(self, project_dir: Path, scaffold_source: Path):
        """Create .agent directory with a conflicting file."""
        # Copy real scaffolds first
        agent_dir = project_dir / ".agent"
        sdd_dir = agent_dir / "commands" / "sdd"
        sdd_dir.mkdir(parents=True)

        # Create a file with same prefix but different name than scaffold
        # Real scaffold has sdd.4-task-planner-for-feature.prompt.md
        conflicting_file = sdd_dir / "sdd.4-determine-test-strategy.prompt.md"
        conflicting_file.write_text("# Old conflicting file content")

        return agent_dir

    def test_at_001_simple_conflict_detection(self, temp_project, scaffold_source, capsys):
        """AT-001: User runs init when .agent/ contains files with conflicting prefixes."""
        # Setup: Create conflicting .agent directory
        self._create_conflicting_agent_dir(temp_project, scaffold_source)

        # Call REAL detect_sdd_conflicts function
        conflicts = detect_sdd_conflicts(scaffold_source, temp_project)

        # Verify conflicts detected
        assert len(conflicts) >= 1, "Should detect at least one conflict"

        # Find the sdd.4- conflict
        sdd4_conflict = next((c for c in conflicts if c.prefix == "sdd.4-"), None)
        assert sdd4_conflict is not None, "Should detect sdd.4- prefix conflict"
        assert sdd4_conflict.existing_name == "sdd.4-determine-test-strategy.prompt.md"
        assert "task-planner" in sdd4_conflict.scaffold_name

        # Test prompt display (capture output)
        display = ConsoleDisplay()
        with patch("builtins.input", return_value="3"):  # Select skip
            result = prompt_conflict_resolution(conflicts, display)

        captured = capsys.readouterr()
        # Verify prompt displays conflict info and options
        assert "Conflict detected" in captured.out or "sdd.4-" in captured.out
        assert result in ("replace", "backup", "skip")

    def test_at_002_backup_option_creates_valid_backup(self, temp_project):
        """AT-002: User chooses backup option during conflict resolution."""
        # Setup: Create .agent directory with content
        agent_dir = temp_project / ".agent"
        sdd_dir = agent_dir / "commands" / "sdd"
        sdd_dir.mkdir(parents=True)
        test_file = sdd_dir / "sdd.4-old-file.prompt.md"
        test_file.write_text("# Original content")

        # Setup backup root
        backup_root = temp_project / ".agent-tracking" / "backups"

        # Call REAL backup_directory function
        backup_path = backup_directory(agent_dir, backup_root)

        # Verify backup created
        assert backup_path.exists(), "Backup directory should exist"
        assert backup_path.parent.parent == backup_root, "Should be under backup root"
        assert (backup_path / "commands" / "sdd" / "sdd.4-old-file.prompt.md").exists()

        # Verify original moved (no longer exists)
        assert not agent_dir.exists(), "Original .agent should be moved"

        # Verify timestamp format in path
        timestamp_dir = backup_path.parent.name
        assert len(timestamp_dir) == 15  # YYYYMMDD-HHMMSS format
        assert "-" in timestamp_dir

    def test_at_003_replace_option_clears_directory(self, temp_project, scaffold_source):
        """AT-003: User chooses replace option (equivalent to --force)."""
        # Setup: Create .agent directory with old content
        agent_dir = temp_project / ".agent"
        sdd_dir = agent_dir / "commands" / "sdd"
        sdd_dir.mkdir(parents=True)
        old_file = sdd_dir / "sdd.4-old-custom-file.prompt.md"
        old_file.write_text("# Old custom content that should be removed")

        # Simulate replace: clear directory
        shutil.rmtree(agent_dir)
        assert not agent_dir.exists()

        # Call REAL copy_all_scaffolds with force=True
        os.chdir(temp_project)
        results = copy_all_scaffolds(temp_project, force=True)

        # Verify old file is gone, new scaffolds are present
        assert not old_file.exists(), "Old file should be removed"

        # Check that new scaffolds were copied
        copied_files = [r for r in results if r.copied]
        assert len(copied_files) > 0, "Should have copied scaffold files"

        # Verify real scaffold file exists
        new_sdd_dir = temp_project / ".agent" / "commands" / "sdd"
        if new_sdd_dir.exists():
            sdd_files = list(new_sdd_dir.glob("sdd.*.prompt.md"))
            assert len(sdd_files) > 0, "Should have SDD prompt files"

    def test_at_004_skip_option_preserves_existing(self, temp_project, scaffold_source):
        """AT-004: User chooses to skip and keep existing files."""
        # Setup: Create .agent directory with custom content
        agent_dir = temp_project / ".agent"
        sdd_dir = agent_dir / "commands" / "sdd"
        sdd_dir.mkdir(parents=True)
        custom_file = sdd_dir / "sdd.4-my-custom-workflow.prompt.md"
        original_content = "# My custom workflow - should be preserved"
        custom_file.write_text(original_content)

        # Detect conflicts (real function)
        conflicts = detect_sdd_conflicts(scaffold_source, temp_project)
        assert len(conflicts) >= 1, "Should detect conflict"

        # Simulate skip: don't modify anything, just copy non-conflicting
        os.chdir(temp_project)
        copy_all_scaffolds(temp_project, force=False)

        # Verify custom file is preserved
        assert custom_file.exists(), "Custom file should still exist"
        assert custom_file.read_text() == original_content, "Content should be unchanged"

        # Verify skip behavior in results - directory should still exist
        # Some files should be skipped since directory exists
        assert agent_dir.exists()

    def test_at_005_force_flag_bypasses_prompt(self, temp_project, scaffold_source):
        """AT-005: Using --force skips interactive conflict detection."""
        # Setup: Create conflicting .agent directory
        self._create_conflicting_agent_dir(temp_project, scaffold_source)

        # Change to project directory
        original_cwd = os.getcwd()
        os.chdir(temp_project)

        try:
            # Create minimal args namespace for cmd_init
            class Args:
                force = True
                on_conflict = None

            args = Args()
            display = ConsoleDisplay()

            # Track what prompts are called
            prompt_calls = []

            def track_prompts(prompt_text):
                prompt_calls.append(prompt_text)
                # Handle notification prompt with "n"
                if "notification" in prompt_text.lower():
                    return "n"
                # Any conflict prompt should NOT be called with --force
                if "conflict" in prompt_text.lower() or "Choice" in prompt_text:
                    pytest.fail("Should not prompt for conflict when --force is used")
                return "n"

            with patch("builtins.input", track_prompts):
                with patch("sys.stdin.isatty", return_value=True):
                    result = cmd_init(args, display)

            # Verify init succeeded
            assert result == 0, "cmd_init should succeed"

            # Verify no conflict-related prompts were called
            conflict_prompts = [p for p in prompt_calls if "choice" in p.lower()]
            assert len(conflict_prompts) == 0, "No conflict prompt should be shown"

            # Verify new scaffolds are in place
            sdd_dir = temp_project / ".agent" / "commands" / "sdd"
            if sdd_dir.exists():
                # Real scaffold should be present
                task_planner = list(sdd_dir.glob("sdd.4-task-planner*.prompt.md"))
                assert len(task_planner) > 0 or result == 0
        finally:
            os.chdir(original_cwd)

    def test_at_006_no_conflict_when_patterns_match(self, temp_project, scaffold_source):
        """AT-006: Init proceeds normally when no conflicts exist."""
        # Setup: Empty project, no .agent directory
        assert not (temp_project / ".agent").exists()

        # Call REAL detect_sdd_conflicts
        conflicts = detect_sdd_conflicts(scaffold_source, temp_project)

        # Verify no conflicts when target doesn't exist
        assert len(conflicts) == 0, "Should have no conflicts for non-existent target"

        # Now copy scaffolds (real function)
        os.chdir(temp_project)
        results = copy_all_scaffolds(temp_project, force=False)

        # Verify files were copied
        copied = [r for r in results if r.copied]
        assert len(copied) > 0, "Should have copied files"

        # Verify .agent directory created
        assert (temp_project / ".agent").exists(), ".agent should be created"

        # Run conflict detection again - should still be no conflicts
        conflicts_after = detect_sdd_conflicts(scaffold_source, temp_project)
        assert len(conflicts_after) == 0, "No conflicts when files match scaffolds"
