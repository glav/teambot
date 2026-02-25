"""Unit tests for env_loader module.

Tests for environment file loading utilities following TDD approach.
Tests are written first, then implementation makes them pass.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Task 1.1: Tests for extract_env_args()
# =============================================================================


class TestExtractEnvArgs:
    """Tests for extract_env_args function."""

    def test_no_env_args_returns_defaults(self):
        """No env args returns (EnvArgs(None, False), original argv)."""
        from teambot.env_loader import EnvArgs, extract_env_args

        argv = ["teambot", "run", "obj.md"]
        env_args, cleaned = extract_env_args(argv)

        assert env_args == EnvArgs(None, False)
        assert cleaned == ["teambot", "run", "obj.md"]

    def test_extract_env_file_with_space(self):
        """--env-file /path extracts correctly."""
        from teambot.env_loader import extract_env_args

        argv = ["teambot", "--env-file", "/path/.env", "run", "obj.md"]
        env_args, cleaned = extract_env_args(argv)

        assert env_args.env_file == Path("/path/.env")
        assert env_args.no_env is False
        assert cleaned == ["teambot", "run", "obj.md"]

    def test_extract_env_file_with_equals(self):
        """--env-file=/path extracts correctly."""
        from teambot.env_loader import extract_env_args

        argv = ["teambot", "--env-file=/path/.env", "run", "obj.md"]
        env_args, cleaned = extract_env_args(argv)

        assert env_args.env_file == Path("/path/.env")
        assert env_args.no_env is False
        assert cleaned == ["teambot", "run", "obj.md"]

    def test_extract_no_env_flag(self):
        """--no-env sets no_env=True."""
        from teambot.env_loader import extract_env_args

        argv = ["teambot", "--no-env", "run", "obj.md"]
        env_args, cleaned = extract_env_args(argv)

        assert env_args.env_file is None
        assert env_args.no_env is True
        assert cleaned == ["teambot", "run", "obj.md"]

    def test_both_args_extracted(self):
        """Both args extracted (validation happens elsewhere)."""
        from teambot.env_loader import extract_env_args

        argv = ["teambot", "--no-env", "--env-file", ".env", "status"]
        env_args, cleaned = extract_env_args(argv)

        assert env_args.env_file == Path(".env")
        assert env_args.no_env is True
        assert cleaned == ["teambot", "status"]

    def test_preserves_other_args(self):
        """Other args remain in cleaned argv."""
        from teambot.env_loader import extract_env_args

        argv = [
            "teambot",
            "-v",
            "--no-animation",
            "--env-file",
            ".env",
            "run",
            "-c",
            "config.json",
            "obj.md",
        ]
        env_args, cleaned = extract_env_args(argv)

        assert env_args.env_file == Path(".env")
        assert cleaned == ["teambot", "-v", "--no-animation", "run", "-c", "config.json", "obj.md"]

    def test_env_file_before_command(self):
        """teambot --env-file .env run works."""
        from teambot.env_loader import extract_env_args

        argv = ["teambot", "--env-file", ".env", "run", "objectives/task.md"]
        env_args, cleaned = extract_env_args(argv)

        assert env_args.env_file == Path(".env")
        assert cleaned == ["teambot", "run", "objectives/task.md"]

    def test_env_file_missing_value_preserved(self):
        """--env-file at end without value is preserved for argparse to error."""
        from teambot.env_loader import extract_env_args

        argv = ["teambot", "run", "--env-file"]
        env_args, cleaned = extract_env_args(argv)

        # Missing value - arg should be preserved so argparse can report proper error
        assert env_args.env_file is None
        assert "--env-file" in cleaned

    def test_defaults_to_sys_argv(self):
        """When argv is None, defaults to sys.argv."""
        from teambot.env_loader import extract_env_args

        # Just verify it doesn't crash - actual sys.argv varies
        env_args, cleaned = extract_env_args(None)
        assert isinstance(env_args.no_env, bool)


# =============================================================================
# Task 1.2: Tests for find_env_files()
# =============================================================================


class TestFindEnvFiles:
    """Tests for find_env_files function."""

    def test_no_env_files_returns_empty(self, tmp_path, monkeypatch):
        """Returns empty list when no .env files exist."""
        from teambot.env_loader import find_env_files

        monkeypatch.chdir(tmp_path)
        # Mock git root to avoid interference from actual repo
        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            result = find_env_files(tmp_path)

        assert result == []

    def test_finds_cwd_env_file(self, tmp_path, monkeypatch):
        """Finds .env in current directory."""
        from teambot.env_loader import find_env_files

        env_file = tmp_path / ".env"
        env_file.write_text("TEST=value")
        monkeypatch.chdir(tmp_path)

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            result = find_env_files(tmp_path)

        assert len(result) == 1
        assert result[0] == env_file

    def test_finds_parent_env_file(self, tmp_path, monkeypatch):
        """Finds .env in parent when cwd has none."""
        from teambot.env_loader import find_env_files

        # Create parent .env
        parent_env = tmp_path / ".env"
        parent_env.write_text("PARENT=value")

        # Create child without .env
        child = tmp_path / "child"
        child.mkdir()
        monkeypatch.chdir(child)

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            result = find_env_files(child)

        assert len(result) == 1
        assert result[0] == parent_env

    def test_finds_both_parent_and_cwd(self, tmp_path, monkeypatch):
        """Returns [cwd, parent] when both have .env files."""
        from teambot.env_loader import find_env_files

        # Create parent .env
        parent_env = tmp_path / ".env"
        parent_env.write_text("PARENT=value")

        # Create child with .env
        child = tmp_path / "child"
        child.mkdir()
        child_env = child / ".env"
        child_env.write_text("CHILD=value")
        monkeypatch.chdir(child)

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            result = find_env_files(child)

        assert len(result) == 2
        assert result[0] == child_env  # cwd first
        assert result[1] == parent_env  # parent second

    def test_stops_at_git_root(self, tmp_path, monkeypatch):
        """Stops traversal at git root directory."""
        from teambot.env_loader import find_env_files

        # Create structure: grandparent/.env -> parent (git root) -> child
        grandparent = tmp_path / "grandparent"
        grandparent.mkdir()
        grandparent_env = grandparent / ".env"
        grandparent_env.write_text("GRANDPARENT=value")

        parent = grandparent / "parent"
        parent.mkdir()
        parent_env = parent / ".env"
        parent_env.write_text("PARENT=value")

        child = parent / "child"
        child.mkdir()
        monkeypatch.chdir(child)

        # Parent is the git root - should not find grandparent
        with patch("teambot.env_loader.find_git_root", return_value=parent):
            result = find_env_files(child)

        assert len(result) == 1
        assert result[0] == parent_env
        assert grandparent_env not in result

    def test_respects_max_depth(self, tmp_path, monkeypatch):
        """Stops after max_depth directories."""
        from teambot.env_loader import find_env_files

        # Create deeply nested structure
        current = tmp_path
        for i in range(15):
            current = current / f"level{i}"
            current.mkdir()

        # Put .env at level 12 (deeper than default max_depth of 10)
        deep_env = tmp_path / "level0" / "level1" / "level2" / "level3" / ".env"
        deep_env.parent.mkdir(parents=True, exist_ok=True)
        deep_env.write_text("DEEP=value")

        deepest = current  # level14
        monkeypatch.chdir(deepest)

        # No git root - should stop at max_depth
        with patch("teambot.env_loader.find_git_root", return_value=None):
            result = find_env_files(deepest, max_depth=5)

        # Should find nothing because .env is deeper than 5 levels from deepest
        # Actually let's test this properly - put .env at different depths
        assert len(result) == 0  # max_depth is 5, .env is much further up

    def test_order_is_cwd_to_parent(self, tmp_path, monkeypatch):
        """Returns files ordered from cwd (first) to farthest parent (last)."""
        from teambot.env_loader import find_env_files

        # Create 3-level structure with .env at each level
        level0 = tmp_path
        level0_env = level0 / ".env"
        level0_env.write_text("LEVEL0=value")

        level1 = level0 / "level1"
        level1.mkdir()
        level1_env = level1 / ".env"
        level1_env.write_text("LEVEL1=value")

        level2 = level1 / "level2"
        level2.mkdir()
        level2_env = level2 / ".env"
        level2_env.write_text("LEVEL2=value")

        monkeypatch.chdir(level2)

        with patch("teambot.env_loader.find_git_root", return_value=level0):
            result = find_env_files(level2)

        assert len(result) == 3
        assert result[0] == level2_env  # cwd first
        assert result[1] == level1_env  # parent
        assert result[2] == level0_env  # grandparent (git root)


class TestFindGitRoot:
    """Tests for find_git_root function."""

    def test_returns_none_when_not_in_repo(self, tmp_path, monkeypatch):
        """Returns None when not in a git repository."""
        from teambot.env_loader import find_git_root

        monkeypatch.chdir(tmp_path)

        # Mock subprocess to simulate not being in a git repo
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            result = find_git_root()

        assert result is None

    def test_returns_path_when_in_repo(self, tmp_path, monkeypatch):
        """Returns git root path when in a repository."""
        from teambot.env_loader import find_git_root

        monkeypatch.chdir(tmp_path)

        # Mock subprocess to return a valid path
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = str(tmp_path) + "\n"

        with patch("subprocess.run", return_value=mock_result):
            result = find_git_root()

        assert result == tmp_path

    def test_handles_timeout(self, tmp_path, monkeypatch):
        """Returns None when git command times out."""
        from teambot.env_loader import find_git_root

        monkeypatch.chdir(tmp_path)

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 5)):
            result = find_git_root()

        assert result is None

    def test_handles_git_not_found(self, tmp_path, monkeypatch):
        """Returns None when git is not installed."""
        from teambot.env_loader import find_git_root

        monkeypatch.chdir(tmp_path)

        with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            result = find_git_root()

        assert result is None


# =============================================================================
# Task 1.3: Tests for load_environment()
# =============================================================================


class TestLoadEnvironment:
    """Tests for load_environment function."""

    def test_no_env_skips_loading(self, monkeypatch):
        """no_env=True prevents all .env loading."""
        from teambot.env_loader import load_environment

        # Clear any existing test var
        monkeypatch.delenv("SKIP_TEST_VAR", raising=False)

        with patch("teambot.env_loader.load_dotenv") as mock_load:
            result = load_environment(no_env=True)

        # load_dotenv should never be called
        mock_load.assert_not_called()
        assert result == []

    def test_explicit_env_file_loads_only_that_file(self, tmp_path, monkeypatch):
        """env_file parameter loads only specified file."""
        from teambot.env_loader import load_environment

        env_file = tmp_path / "custom.env"
        env_file.write_text("CUSTOM_VAR=custom")
        monkeypatch.chdir(tmp_path)

        with patch("teambot.env_loader.load_dotenv") as mock_load:
            result = load_environment(env_file=env_file)

        mock_load.assert_called_once_with(env_file, override=True)
        assert result == [env_file]

    def test_explicit_env_file_not_found_raises(self, tmp_path):
        """env_file pointing to missing file raises FileNotFoundError."""
        from teambot.env_loader import load_environment

        missing = tmp_path / "nonexistent.env"

        with pytest.raises(FileNotFoundError):
            load_environment(env_file=missing)

    def test_error_message_contains_path(self, tmp_path):
        """FileNotFoundError message includes the missing path."""
        from teambot.env_loader import load_environment

        missing = tmp_path / "my-missing-file.env"

        with pytest.raises(FileNotFoundError) as exc_info:
            load_environment(env_file=missing)

        assert "my-missing-file.env" in str(exc_info.value)

    def test_default_loads_from_cwd(self, tmp_path, monkeypatch):
        """Default behavior loads .env from cwd."""
        from teambot.env_loader import load_environment

        env_file = tmp_path / ".env"
        env_file.write_text("CWD_VAR=cwd")
        monkeypatch.chdir(tmp_path)

        # Mock git root to stop at tmp_path
        with (
            patch("teambot.env_loader.find_git_root", return_value=tmp_path),
            patch("teambot.env_loader.load_dotenv") as mock_load,
        ):
            result = load_environment()

        mock_load.assert_called_once()
        assert env_file in result

    def test_default_merges_parent_files(self, tmp_path, monkeypatch):
        """Default behavior merges parent .env files."""
        from teambot.env_loader import load_environment

        # Create parent and child .env files
        parent_env = tmp_path / ".env"
        parent_env.write_text("PARENT_VAR=parent")

        child = tmp_path / "child"
        child.mkdir()
        child_env = child / ".env"
        child_env.write_text("CHILD_VAR=child")
        monkeypatch.chdir(child)

        load_calls = []

        def track_load(path, override=False):
            load_calls.append((path, override))

        with (
            patch("teambot.env_loader.find_git_root", return_value=tmp_path),
            patch("teambot.env_loader.load_dotenv", side_effect=track_load),
        ):
            load_environment()

        # Should load both files
        assert len(load_calls) == 2
        # Parent should be loaded first (it's farthest)
        assert load_calls[0][0] == parent_env
        # Child should be loaded second (override parent values)
        assert load_calls[1][0] == child_env

    def test_cwd_overrides_parent_conflicts(self, tmp_path, monkeypatch):
        """CWD .env values override parent .env for same key."""
        from teambot.env_loader import load_environment

        # Create parent and child with same key
        parent_env = tmp_path / ".env"
        parent_env.write_text("SHARED_VAR=parent")

        child = tmp_path / "child"
        child.mkdir()
        child_env = child / ".env"
        child_env.write_text("SHARED_VAR=child")
        monkeypatch.chdir(child)

        load_calls = []

        def track_load(path, override=False):
            load_calls.append((path, override))

        with (
            patch("teambot.env_loader.find_git_root", return_value=tmp_path),
            patch("teambot.env_loader.load_dotenv", side_effect=track_load),
        ):
            load_environment()

        # Child (cwd) should be loaded last with override=True to win conflicts
        assert load_calls[-1][0] == child_env
        assert load_calls[-1][1] is True  # override=True

    def test_returns_list_of_loaded_files(self, tmp_path, monkeypatch):
        """Returns list of Path objects for loaded files."""
        from teambot.env_loader import load_environment

        env_file = tmp_path / ".env"
        env_file.write_text("TEST=value")
        monkeypatch.chdir(tmp_path)

        with (
            patch("teambot.env_loader.find_git_root", return_value=tmp_path),
            patch("teambot.env_loader.load_dotenv"),
        ):
            result = load_environment()

        assert isinstance(result, list)
        assert all(isinstance(p, Path) for p in result)
        assert env_file in result

    def test_returns_empty_when_no_env_files(self, tmp_path, monkeypatch):
        """Returns empty list when no .env files are found."""
        from teambot.env_loader import load_environment

        monkeypatch.chdir(tmp_path)

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            result = load_environment()

        assert result == []
