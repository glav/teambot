"""Acceptance tests for enhanced .env file loading feature.

Core logic is tested directly; selective mocking is used for external dependencies.

These tests validate the acceptance scenarios from the feature specification:
- AT-001 through AT-008
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.acceptance
class TestEnvLoadingAcceptance:
    """Acceptance test scenarios from feature specification."""

    def test_at_001_default_cwd_loading(self, tmp_path, monkeypatch):
        """AT-001: .env loads from current working directory by default.

        Validates:
        - Default behavior loads .env from cwd
        - Environment variables are set correctly
        """
        # Setup
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("TEST_VAR=hello")
        monkeypatch.delenv("TEST_VAR", raising=False)

        # Execute
        from teambot.env_loader import load_environment

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            loaded = load_environment()

        # Verify
        assert os.environ.get("TEST_VAR") == "hello"
        assert tmp_path / ".env" in loaded

    def test_at_002_parent_directory_merge(self, tmp_path, monkeypatch):
        """AT-002: Parent .env provides defaults, child overrides conflicts.

        Validates:
        - Parent directory .env files are discovered
        - Variables from both parent and child are available
        - Child values take precedence for conflicts
        """
        # Setup
        child = tmp_path / "child"
        child.mkdir()
        monkeypatch.chdir(child)

        (tmp_path / ".env").write_text("PARENT_VAR=parent\nSHARED_VAR=parent")
        (child / ".env").write_text("CHILD_VAR=child\nSHARED_VAR=child")

        for var in ["PARENT_VAR", "CHILD_VAR", "SHARED_VAR"]:
            monkeypatch.delenv(var, raising=False)

        # Execute
        from teambot.env_loader import load_environment

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            load_environment()

        # Verify
        assert os.environ.get("PARENT_VAR") == "parent"
        assert os.environ.get("CHILD_VAR") == "child"
        assert os.environ.get("SHARED_VAR") == "child"  # child wins

    def test_at_003_explicit_env_file_path(self, tmp_path, monkeypatch):
        """AT-003: --env-file loads only the specified file.

        Validates:
        - Explicit env_file parameter loads only that file
        - CWD .env is not loaded when explicit path is provided
        """
        # Setup
        monkeypatch.chdir(tmp_path)
        custom = tmp_path / "custom.env"
        custom.write_text("CUSTOM_VAR=custom")
        (tmp_path / ".env").write_text("CWD_VAR=cwd")

        monkeypatch.delenv("CUSTOM_VAR", raising=False)
        monkeypatch.delenv("CWD_VAR", raising=False)

        # Execute
        from teambot.env_loader import load_environment

        load_environment(env_file=custom)

        # Verify
        assert os.environ.get("CUSTOM_VAR") == "custom"
        assert os.environ.get("CWD_VAR") is None

    def test_at_004_env_file_missing_error(self, tmp_path):
        """AT-004: --env-file with missing path raises clear error.

        Validates:
        - FileNotFoundError is raised for missing file
        - Error message includes the missing file path
        """
        missing = tmp_path / "nonexistent.env"

        from teambot.env_loader import load_environment

        with pytest.raises(FileNotFoundError) as exc_info:
            load_environment(env_file=missing)

        assert "nonexistent.env" in str(exc_info.value)

    def test_at_005_no_env_disables_loading(self, tmp_path, monkeypatch):
        """AT-005: --no-env prevents all .env loading.

        Validates:
        - no_env=True prevents loading even when .env exists
        - Returns empty list
        - Environment variable is not set
        """
        # Setup
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("SHOULD_NOT_LOAD=yes")
        monkeypatch.delenv("SHOULD_NOT_LOAD", raising=False)

        # Execute
        from teambot.env_loader import load_environment

        loaded = load_environment(no_env=True)

        # Verify
        assert os.environ.get("SHOULD_NOT_LOAD") is None
        assert loaded == []

    def test_at_006_mutual_exclusivity(self):
        """AT-006: --env-file and --no-env are mutually exclusive in parser.

        Validates:
        - argparse enforces mutual exclusivity
        - SystemExit with code 2 (argparse error)
        """
        from teambot.cli import create_parser

        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--env-file", ".env", "--no-env", "status"])

        assert exc_info.value.code == 2  # argparse error code

    def test_at_007_all_commands_support_flags_init(self):
        """AT-007a: --no-env works with init command.

        Validates:
        - --no-env flag is accepted by init command
        """
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--no-env", "init"])
        assert args.no_env is True
        assert args.command == "init"

    def test_at_007_all_commands_support_flags_status(self):
        """AT-007b: --env-file works with status command.

        Validates:
        - --env-file flag is accepted by status command
        """
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--env-file", ".env", "status"])
        assert args.env_file == Path(".env")
        assert args.command == "status"

    def test_at_007_all_commands_support_flags_run(self):
        """AT-007c: --no-env works with run command.

        Validates:
        - --no-env flag is accepted by run command
        """
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--no-env", "run", "objectives/task.md"])
        assert args.no_env is True
        assert args.command == "run"
        assert args.objective == "objectives/task.md"


# AT-008 (uvx invocation) requires manual verification and is documented in Phase 6


@pytest.mark.acceptance
class TestEnvLoadingEdgeCases:
    """Additional edge case tests for comprehensive coverage."""

    def test_deeply_nested_directory_finds_parent_env(self, tmp_path, monkeypatch):
        """Deeply nested directories still find parent .env files."""
        # Create deep structure
        deep_path = tmp_path / "a" / "b" / "c" / "d"
        deep_path.mkdir(parents=True)
        monkeypatch.chdir(deep_path)

        # Put .env at root
        (tmp_path / ".env").write_text("DEEP_NESTED_TEST=found")
        monkeypatch.delenv("DEEP_NESTED_TEST", raising=False)

        # Execute
        from teambot.env_loader import load_environment

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            load_environment()

        # Verify
        assert os.environ.get("DEEP_NESTED_TEST") == "found"

    def test_no_env_files_anywhere(self, tmp_path, monkeypatch):
        """No .env files returns empty list without error."""
        monkeypatch.chdir(tmp_path)

        from teambot.env_loader import load_environment

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            loaded = load_environment()

        assert loaded == []

    def test_env_file_with_special_characters(self, tmp_path, monkeypatch):
        """Environment variables with special characters are handled."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("SPECIAL_VAR=\"hello world\"\nQUOTED_VAR='test'")
        monkeypatch.delenv("SPECIAL_VAR", raising=False)
        monkeypatch.delenv("QUOTED_VAR", raising=False)

        from teambot.env_loader import load_environment

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            load_environment()

        # python-dotenv handles quotes
        assert os.environ.get("SPECIAL_VAR") == "hello world"
        assert os.environ.get("QUOTED_VAR") == "test"

    def test_multiple_parent_levels_merge(self, tmp_path, monkeypatch):
        """Multiple parent levels all contribute variables."""
        # Create 3-level structure
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)
        monkeypatch.chdir(level2)

        (tmp_path / ".env").write_text("ROOT_VAR=root")
        (level1 / ".env").write_text("L1_VAR=level1")
        (level2 / ".env").write_text("L2_VAR=level2")

        for var in ["ROOT_VAR", "L1_VAR", "L2_VAR"]:
            monkeypatch.delenv(var, raising=False)

        from teambot.env_loader import load_environment

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            loaded = load_environment()

        assert os.environ.get("ROOT_VAR") == "root"
        assert os.environ.get("L1_VAR") == "level1"
        assert os.environ.get("L2_VAR") == "level2"
        assert len(loaded) == 3

    def test_extract_env_args_removes_args_from_argv(self):
        """extract_env_args properly removes env args from argv."""
        from teambot.env_loader import extract_env_args

        argv = ["teambot", "--env-file", "custom.env", "--verbose", "run", "obj.md"]
        env_args, cleaned = extract_env_args(argv)

        assert env_args.env_file == Path("custom.env")
        assert "--env-file" not in cleaned
        assert "custom.env" not in cleaned
        assert cleaned == ["teambot", "--verbose", "run", "obj.md"]
