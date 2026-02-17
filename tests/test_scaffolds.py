"""Unit tests for scaffolding copy operations - TDD approach."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class TestGetScaffoldsDir:
    """Tests for get_scaffolds_dir() function."""

    def test_returns_path_object(self):
        """Function returns a Path object."""
        from teambot.scaffolds import get_scaffolds_dir

        result = get_scaffolds_dir()

        assert isinstance(result, Path)

    def test_scaffolds_dir_exists(self):
        """Scaffolds directory exists in package."""
        from teambot.scaffolds import get_scaffolds_dir

        result = get_scaffolds_dir()

        assert result.exists()

    def test_scaffolds_contains_stages_yaml(self):
        """Scaffolds directory contains stages.yaml."""
        from teambot.scaffolds import get_scaffolds_dir

        result = get_scaffolds_dir()

        assert (result / "stages.yaml").exists()

    def test_scaffolds_contains_agents_md(self):
        """Scaffolds directory contains AGENTS.md."""
        from teambot.scaffolds import get_scaffolds_dir

        result = get_scaffolds_dir()

        assert (result / "AGENTS.md").exists()


class TestCopyScaffoldFile:
    """Tests for copy_scaffold_file() function."""

    def test_copies_file_when_target_missing(self, tmp_path):
        """Copies file when target doesn't exist."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "stages.yaml"

        result = copy_scaffold_file("stages.yaml", target)

        assert result.copied is True
        assert result.reason == "copied"
        assert target.exists()

    def test_skips_when_target_exists(self, tmp_path):
        """Skips copy when target already exists - CRITICAL safety test."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "stages.yaml"
        target.write_text("existing content")
        original_content = target.read_text()

        result = copy_scaffold_file("stages.yaml", target)

        assert result.copied is False
        assert result.reason == "skipped_exists"
        assert target.read_text() == original_content  # Unchanged!

    def test_force_overwrites_existing(self, tmp_path):
        """Force flag overwrites existing file."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "stages.yaml"
        target.write_text("existing content")

        result = copy_scaffold_file("stages.yaml", target, force=True)

        assert result.copied is True
        assert result.reason == "copied"
        assert target.read_text() != "existing content"

    def test_creates_parent_directories(self, tmp_path):
        """Creates parent directories if needed."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "docs" / "nested" / "file.md"

        result = copy_scaffold_file("sdd-objective-template.md", target)

        assert result.copied is True
        assert target.parent.exists()
        assert target.exists()

    def test_returns_source_missing_for_invalid_source(self, tmp_path):
        """Returns source_missing for non-existent source."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "nonexistent.md"

        result = copy_scaffold_file("does-not-exist.md", target)

        assert result.copied is False
        assert result.reason == "source_missing"


class TestCopyScaffoldDirectory:
    """Tests for copy_scaffold_directory() function."""

    def test_copies_directory_when_target_missing(self, tmp_path):
        """Copies directory when target doesn't exist."""
        from teambot.scaffolds import copy_scaffold_directory

        target = tmp_path / ".github" / "agents"

        result = copy_scaffold_directory("agents", target)

        assert result.copied is True
        assert result.reason == "copied"
        assert target.exists()
        assert (target / "pm.agent.md").exists()

    def test_skips_when_directory_not_empty(self, tmp_path):
        """Skips when target directory exists and not empty - CRITICAL."""
        from teambot.scaffolds import copy_scaffold_directory

        target = tmp_path / ".github" / "agents"
        target.mkdir(parents=True)
        (target / "custom.agent.md").write_text("custom agent")

        result = copy_scaffold_directory("agents", target)

        assert result.copied is False
        assert result.reason == "skipped_not_empty"
        # Verify original content preserved
        assert (target / "custom.agent.md").exists()

    def test_copies_into_empty_directory(self, tmp_path):
        """Copies into existing empty directory."""
        from teambot.scaffolds import copy_scaffold_directory

        target = tmp_path / ".github" / "agents"
        target.mkdir(parents=True)
        # Directory exists but is empty

        result = copy_scaffold_directory("agents", target)

        assert result.copied is True
        assert result.reason == "copied"

    def test_force_overwrites_existing_directory(self, tmp_path):
        """Force flag replaces existing directory."""
        from teambot.scaffolds import copy_scaffold_directory

        target = tmp_path / ".github" / "agents"
        target.mkdir(parents=True)
        (target / "custom.agent.md").write_text("custom")

        result = copy_scaffold_directory("agents", target, force=True)

        assert result.copied is True
        # Custom file should be gone, replaced by scaffold
        assert not (target / "custom.agent.md").exists()
        assert (target / "pm.agent.md").exists()

    def test_returns_source_missing_for_invalid_source(self, tmp_path):
        """Returns source_missing for non-existent source directory."""
        from teambot.scaffolds import copy_scaffold_directory

        target = tmp_path / "nonexistent"

        result = copy_scaffold_directory("does-not-exist", target)

        assert result.copied is False
        assert result.reason == "source_missing"


class TestCopyAllScaffolds:
    """Tests for copy_all_scaffolds() function."""

    def test_copies_all_files_to_empty_repo(self, tmp_path):
        """Copies all scaffolds to empty repository."""
        from teambot.scaffolds import copy_all_scaffolds

        results = copy_all_scaffolds(tmp_path)

        copied = [r for r in results if r.copied]
        assert len(copied) == 5  # 3 files + 2 directories

        # Verify all expected files exist
        assert (tmp_path / "stages.yaml").exists()
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / "docs" / "sdd-objective-template.md").exists()
        assert (tmp_path / ".github" / "agents" / "pm.agent.md").exists()
        assert (tmp_path / ".agent" / "commands").exists()

    def test_skips_existing_files(self, tmp_path):
        """Skips files that already exist."""
        from teambot.scaffolds import copy_all_scaffolds

        # Pre-create some files
        (tmp_path / "stages.yaml").write_text("custom stages")
        (tmp_path / "AGENTS.md").write_text("custom AGENTS")

        results = copy_all_scaffolds(tmp_path)

        skipped = [r for r in results if r.reason == "skipped_exists"]
        assert len(skipped) == 2

        # Verify content unchanged
        assert (tmp_path / "stages.yaml").read_text() == "custom stages"

    def test_handles_mixed_state(self, tmp_path):
        """Copies only missing resources in partial state."""
        from teambot.scaffolds import copy_all_scaffolds

        # Pre-create one file
        (tmp_path / "AGENTS.md").write_text("custom")
        # Pre-create one directory with content
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "custom.md").write_text("custom agent")

        results = copy_all_scaffolds(tmp_path)

        # Should have 2 skipped, 3 copied
        skipped = [r for r in results if not r.copied]
        copied = [r for r in results if r.copied]
        assert len(skipped) == 2  # AGENTS.md and .github/agents/
        assert len(copied) == 3  # stages.yaml, docs/template, .agent/

    def test_force_overwrites_all(self, tmp_path):
        """Force flag overwrites all existing files."""
        from teambot.scaffolds import copy_all_scaffolds

        # Pre-create files
        (tmp_path / "stages.yaml").write_text("custom")
        (tmp_path / "AGENTS.md").write_text("custom")

        results = copy_all_scaffolds(tmp_path, force=True)

        # All should be copied
        copied = [r for r in results if r.copied]
        assert len(copied) == 5

        # Verify overwritten
        assert (tmp_path / "stages.yaml").read_text() != "custom"

    def test_returns_list_of_copy_results(self, tmp_path):
        """Returns list of CopyResult for each scaffold item."""
        from teambot.scaffolds import CopyResult, copy_all_scaffolds

        results = copy_all_scaffolds(tmp_path)

        assert isinstance(results, list)
        assert len(results) == 5
        assert all(isinstance(r, CopyResult) for r in results)
