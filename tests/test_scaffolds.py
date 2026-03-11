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


# === Conflict Detection Tests (TDD Phase 1) ===


class TestExtractNumberedPrefix:
    """Tests for extract_numbered_prefix() function."""

    def test_extracts_valid_sdd_prefix(self):
        """Extracts numbered prefix from valid SDD filename."""
        from teambot.scaffolds import extract_numbered_prefix

        assert extract_numbered_prefix("sdd.4-task-planner.prompt.md") == "sdd.4-"

    def test_extracts_single_digit_prefix(self):
        """Extracts single-digit prefix."""
        from teambot.scaffolds import extract_numbered_prefix

        assert extract_numbered_prefix("sdd.0-initialize.prompt.md") == "sdd.0-"

    def test_extracts_multi_digit_prefix(self):
        """Extracts multi-digit prefix (e.g., sdd.10-)."""
        from teambot.scaffolds import extract_numbered_prefix

        assert extract_numbered_prefix("sdd.10-something.prompt.md") == "sdd.10-"

    def test_returns_none_for_non_sdd_file(self):
        """Returns None for non-SDD files like README.md."""
        from teambot.scaffolds import extract_numbered_prefix

        assert extract_numbered_prefix("README.md") is None

    def test_returns_none_for_partial_match(self):
        """Returns None when pattern doesn't match completely."""
        from teambot.scaffolds import extract_numbered_prefix

        assert extract_numbered_prefix("sdd-without-number.md") is None

    def test_returns_none_for_sdd_without_dash(self):
        """Returns None for sdd.N without trailing dash."""
        from teambot.scaffolds import extract_numbered_prefix

        assert extract_numbered_prefix("sdd.4name.md") is None


class TestConflictInfo:
    """Tests for ConflictInfo dataclass."""

    def test_conflict_info_has_required_fields(self):
        """ConflictInfo has prefix, scaffold_name, existing_name fields."""
        from teambot.scaffolds import ConflictInfo

        conflict = ConflictInfo(
            prefix="sdd.4-",
            scaffold_name="sdd.4-task-planner.prompt.md",
            existing_name="sdd.4-determine-test.prompt.md",
        )

        assert conflict.prefix == "sdd.4-"
        assert conflict.scaffold_name == "sdd.4-task-planner.prompt.md"
        assert conflict.existing_name == "sdd.4-determine-test.prompt.md"

    def test_conflict_info_is_dataclass(self):
        """ConflictInfo is a dataclass (not NamedTuple)."""
        from dataclasses import is_dataclass

        from teambot.scaffolds import ConflictInfo

        assert is_dataclass(ConflictInfo)


class TestDetectSddConflicts:
    """Tests for detect_sdd_conflicts() function."""

    def test_detects_conflict_same_prefix_different_name(self, tmp_path):
        """Detects conflict when same prefix has different filename."""
        from teambot.scaffolds import detect_sdd_conflicts

        # Setup scaffold with sdd.4-new.prompt.md
        scaffold_sdd = tmp_path / "scaffold" / ".agent" / "commands" / "sdd"
        scaffold_sdd.mkdir(parents=True)
        (scaffold_sdd / "sdd.4-task-planner.prompt.md").write_text("new")

        # Setup target with sdd.4-old.prompt.md (same prefix, different name)
        target_sdd = tmp_path / "target" / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-determine-test.prompt.md").write_text("old")

        conflicts = detect_sdd_conflicts(tmp_path / "scaffold", tmp_path / "target")

        assert len(conflicts) == 1
        assert conflicts[0].prefix == "sdd.4-"
        assert conflicts[0].scaffold_name == "sdd.4-task-planner.prompt.md"
        assert conflicts[0].existing_name == "sdd.4-determine-test.prompt.md"

    def test_no_conflict_when_same_filename(self, tmp_path):
        """No conflict when files have identical names."""
        from teambot.scaffolds import detect_sdd_conflicts

        # Setup scaffold and target with same file
        scaffold_sdd = tmp_path / "scaffold" / ".agent" / "commands" / "sdd"
        scaffold_sdd.mkdir(parents=True)
        (scaffold_sdd / "sdd.4-task-planner.prompt.md").write_text("content")

        target_sdd = tmp_path / "target" / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-task-planner.prompt.md").write_text("content")

        conflicts = detect_sdd_conflicts(tmp_path / "scaffold", tmp_path / "target")

        assert len(conflicts) == 0

    def test_no_conflict_when_different_prefixes(self, tmp_path):
        """No conflict when files have different prefix numbers."""
        from teambot.scaffolds import detect_sdd_conflicts

        # Setup scaffold with sdd.4-
        scaffold_sdd = tmp_path / "scaffold" / ".agent" / "commands" / "sdd"
        scaffold_sdd.mkdir(parents=True)
        (scaffold_sdd / "sdd.4-task-planner.prompt.md").write_text("new")

        # Setup target with sdd.5- (different prefix)
        target_sdd = tmp_path / "target" / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.5-review-plan.prompt.md").write_text("old")

        conflicts = detect_sdd_conflicts(tmp_path / "scaffold", tmp_path / "target")

        assert len(conflicts) == 0

    def test_returns_empty_when_target_sdd_missing(self, tmp_path):
        """Returns empty list when target SDD directory doesn't exist."""
        from teambot.scaffolds import detect_sdd_conflicts

        # Setup scaffold only
        scaffold_sdd = tmp_path / "scaffold" / ".agent" / "commands" / "sdd"
        scaffold_sdd.mkdir(parents=True)
        (scaffold_sdd / "sdd.4-task-planner.prompt.md").write_text("new")

        # No target directory
        conflicts = detect_sdd_conflicts(tmp_path / "scaffold", tmp_path / "target")

        assert len(conflicts) == 0

    def test_returns_empty_when_scaffold_sdd_missing(self, tmp_path):
        """Returns empty list when scaffold SDD directory doesn't exist."""
        from teambot.scaffolds import detect_sdd_conflicts

        # No scaffold directory
        target_sdd = tmp_path / "target" / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-old.prompt.md").write_text("old")

        conflicts = detect_sdd_conflicts(tmp_path / "scaffold", tmp_path / "target")

        assert len(conflicts) == 0

    def test_detects_multiple_conflicts(self, tmp_path):
        """Detects multiple conflicts across different prefixes."""
        from teambot.scaffolds import detect_sdd_conflicts

        # Setup scaffold
        scaffold_sdd = tmp_path / "scaffold" / ".agent" / "commands" / "sdd"
        scaffold_sdd.mkdir(parents=True)
        (scaffold_sdd / "sdd.4-task-planner.prompt.md").write_text("new")
        (scaffold_sdd / "sdd.5-review-plan.prompt.md").write_text("new")
        (scaffold_sdd / "sdd.6-implementer.prompt.md").write_text("new")

        # Setup target with conflicts on 4 and 5, but same on 6
        target_sdd = tmp_path / "target" / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-determine-test.prompt.md").write_text("old")
        (target_sdd / "sdd.5-old-planner.prompt.md").write_text("old")
        (target_sdd / "sdd.6-implementer.prompt.md").write_text("old")  # Same name

        conflicts = detect_sdd_conflicts(tmp_path / "scaffold", tmp_path / "target")

        assert len(conflicts) == 2
        # Sorted by prefix
        assert conflicts[0].prefix == "sdd.4-"
        assert conflicts[1].prefix == "sdd.5-"

    def test_ignores_non_prompt_files(self, tmp_path):
        """Ignores files that don't match sdd.*.prompt.md pattern."""
        from teambot.scaffolds import detect_sdd_conflicts

        # Setup scaffold with README
        scaffold_sdd = tmp_path / "scaffold" / ".agent" / "commands" / "sdd"
        scaffold_sdd.mkdir(parents=True)
        (scaffold_sdd / "README.md").write_text("scaffold readme")

        # Setup target with README
        target_sdd = tmp_path / "target" / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "README.md").write_text("target readme")

        conflicts = detect_sdd_conflicts(tmp_path / "scaffold", tmp_path / "target")

        assert len(conflicts) == 0

    def test_multiple_target_files_same_prefix_all_conflicts(self, tmp_path):
        """Detects all conflicts when target has multiple files sharing a prefix."""
        from teambot.scaffolds import detect_sdd_conflicts

        scaffold_sdd = tmp_path / "scaffold" / ".agent" / "commands" / "sdd"
        scaffold_sdd.mkdir(parents=True)
        (scaffold_sdd / "sdd.4-task-planner.prompt.md").write_text("new")

        # Target has two files with the same sdd.4- prefix, neither matches scaffold
        target_sdd = tmp_path / "target" / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-old-a.prompt.md").write_text("old-a")
        (target_sdd / "sdd.4-old-b.prompt.md").write_text("old-b")

        conflicts = detect_sdd_conflicts(tmp_path / "scaffold", tmp_path / "target")

        # Both target files should be reported as conflicts
        assert len(conflicts) == 2
        existing_names = {c.existing_name for c in conflicts}
        assert existing_names == {"sdd.4-old-a.prompt.md", "sdd.4-old-b.prompt.md"}
        for c in conflicts:
            assert c.prefix == "sdd.4-"
            assert c.scaffold_name == "sdd.4-task-planner.prompt.md"

    def test_multiple_target_files_same_prefix_one_matches(self, tmp_path):
        """Reports conflict only for target files that differ from scaffold name."""
        from teambot.scaffolds import detect_sdd_conflicts

        scaffold_sdd = tmp_path / "scaffold" / ".agent" / "commands" / "sdd"
        scaffold_sdd.mkdir(parents=True)
        (scaffold_sdd / "sdd.4-task-planner.prompt.md").write_text("new")

        # Target has both the matching scaffold file AND an extra conflicting file
        target_sdd = tmp_path / "target" / ".agent" / "commands" / "sdd"
        target_sdd.mkdir(parents=True)
        (target_sdd / "sdd.4-task-planner.prompt.md").write_text("same")
        (target_sdd / "sdd.4-old-conflict.prompt.md").write_text("old")

        conflicts = detect_sdd_conflicts(tmp_path / "scaffold", tmp_path / "target")

        # Only the non-matching file should be reported
        assert len(conflicts) == 1
        assert conflicts[0].prefix == "sdd.4-"
        assert conflicts[0].scaffold_name == "sdd.4-task-planner.prompt.md"
        assert conflicts[0].existing_name == "sdd.4-old-conflict.prompt.md"


# === Backup Directory Tests (TDD Phase 3) ===


class TestBackupDirectory:
    """Tests for backup_directory() function."""

    def test_creates_timestamped_backup(self, tmp_path):
        """Creates backup directory with timestamp."""
        import re

        from teambot.scaffolds import backup_directory

        source = tmp_path / ".agent"
        source.mkdir()
        (source / "test.txt").write_text("content")
        backup_root = tmp_path / ".agent-tracking" / "backups"

        result = backup_directory(source, backup_root)

        assert not source.exists()  # Moved, not copied
        assert result.exists()
        assert (result / "test.txt").exists()
        # Timestamp folder format: YYYYMMDD-HHMMSS-ffffff (with microseconds)
        assert re.match(r"\d{8}-\d{6}-\d{6}", result.parent.name)

    def test_raises_for_missing_source(self, tmp_path):
        """Raises FileNotFoundError when source doesn't exist."""
        import pytest

        from teambot.scaffolds import backup_directory

        with pytest.raises(FileNotFoundError):
            backup_directory(tmp_path / "nonexistent", tmp_path / "backups")

    def test_preserves_directory_structure(self, tmp_path):
        """Preserves nested directory structure in backup."""
        from teambot.scaffolds import backup_directory

        source = tmp_path / ".agent"
        (source / "commands" / "sdd").mkdir(parents=True)
        (source / "commands" / "sdd" / "test.prompt.md").write_text("content")
        (source / "instructions").mkdir()
        (source / "instructions" / "bash.md").write_text("bash instructions")
        backup_root = tmp_path / "backups"

        result = backup_directory(source, backup_root)

        assert (result / "commands" / "sdd" / "test.prompt.md").exists()
        assert (result / "commands" / "sdd" / "test.prompt.md").read_text() == "content"
        assert (result / "instructions" / "bash.md").exists()

    def test_creates_backup_root_if_missing(self, tmp_path):
        """Creates backup root directory if it doesn't exist."""
        from teambot.scaffolds import backup_directory

        source = tmp_path / ".agent"
        source.mkdir()
        (source / "test.txt").write_text("content")
        backup_root = tmp_path / "deeply" / "nested" / "backups"

        result = backup_directory(source, backup_root)

        assert backup_root.exists()
        assert result.exists()

    def test_backup_directory_named_after_source(self, tmp_path):
        """Backup directory retains source directory name."""
        from teambot.scaffolds import backup_directory

        source = tmp_path / ".agent"
        source.mkdir()
        (source / "test.txt").write_text("content")
        backup_root = tmp_path / "backups"

        result = backup_directory(source, backup_root)

        assert result.name == ".agent"

    def test_multiple_backups_create_separate_directories(self, tmp_path):
        """Rapid successive backups each produce a distinct timestamped directory."""
        from teambot.scaffolds import backup_directory

        backup_root = tmp_path / "backups"
        backup_paths = []

        for i in range(3):
            source = tmp_path / f"source_{i}"
            source.mkdir()
            (source / "file.txt").write_text(f"content {i}")
            result = backup_directory(source, backup_root)
            backup_paths.append(result.parent)

        # All timestamp directories must be unique
        unique_parents = set(str(p) for p in backup_paths)
        assert len(unique_parents) == 3, (
            f"Expected 3 distinct backup directories, got: {backup_paths}"
        )
