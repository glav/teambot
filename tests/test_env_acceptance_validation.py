"""Acceptance test validation for Enhanced .env File Loading - STRICT MODE.

These tests validate acceptance scenarios by exercising the REAL implementation.
Core logic is tested directly; selective mocking only for external dependencies.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

# Import REAL implementation
from teambot.cli import create_parser
from teambot.env_loader import (
    extract_env_args,
    find_env_files,
    load_environment,
)


class TestEnvLoadingAcceptanceValidation:
    """Strict acceptance test validation for AT-001 through AT-008."""

    # =========================================================================
    # AT-001: Default CWD Loading
    # =========================================================================
    def test_at_001_default_cwd_loading(self, tmp_path, monkeypatch):
        """AT-001: Verify .env loads from current working directory by default.

        Steps:
        1. Create .env in test directory with TEST_VAR=hello
        2. Call load_environment() (same as teambot status does)
        3. Check os.environ.get('TEST_VAR')

        Expected: TEST_VAR equals hello
        """
        # Setup
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("TEST_VAR_AT001=hello")
        monkeypatch.delenv("TEST_VAR_AT001", raising=False)

        # Execute REAL implementation
        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            loaded = load_environment()

        # Verify
        assert os.environ.get("TEST_VAR_AT001") == "hello"
        assert tmp_path / ".env" in loaded

    # =========================================================================
    # AT-002: Parent Directory Merge
    # =========================================================================
    def test_at_002_parent_directory_merge(self, tmp_path, monkeypatch):
        """AT-002: Verify parent .env provides defaults, child overrides.

        Steps:
        1. Create parent .env with PARENT_VAR=parent, SHARED_VAR=parent
        2. Create child .env with CHILD_VAR=child, SHARED_VAR=child
        3. Call load_environment() from child directory

        Expected: PARENT_VAR=parent, CHILD_VAR=child, SHARED_VAR=child
        """
        # Setup parent and child directories
        child = tmp_path / "child"
        child.mkdir()
        monkeypatch.chdir(child)

        (tmp_path / ".env").write_text("PARENT_VAR_AT002=parent\nSHARED_VAR_AT002=parent")
        (child / ".env").write_text("CHILD_VAR_AT002=child\nSHARED_VAR_AT002=child")

        for var in ["PARENT_VAR_AT002", "CHILD_VAR_AT002", "SHARED_VAR_AT002"]:
            monkeypatch.delenv(var, raising=False)

        # Execute REAL implementation
        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            load_environment()

        # Verify all three variables with correct precedence
        assert os.environ.get("PARENT_VAR_AT002") == "parent"
        assert os.environ.get("CHILD_VAR_AT002") == "child"
        assert os.environ.get("SHARED_VAR_AT002") == "child"  # child wins

    # =========================================================================
    # AT-003: Explicit --env-file Path
    # =========================================================================
    def test_at_003_explicit_env_file_path(self, tmp_path, monkeypatch):
        """AT-003: Verify --env-file loads only the specified file.

        Steps:
        1. Create custom.env with CUSTOM_VAR=custom
        2. Create cwd .env with CWD_VAR=cwd
        3. Call load_environment(env_file=custom.env)

        Expected: CUSTOM_VAR=custom is set; CWD_VAR is NOT set
        """
        # Setup
        monkeypatch.chdir(tmp_path)
        custom = tmp_path / "custom.env"
        custom.write_text("CUSTOM_VAR_AT003=custom")
        (tmp_path / ".env").write_text("CWD_VAR_AT003=cwd")

        monkeypatch.delenv("CUSTOM_VAR_AT003", raising=False)
        monkeypatch.delenv("CWD_VAR_AT003", raising=False)

        # Execute REAL implementation with explicit env_file
        loaded = load_environment(env_file=custom)

        # Verify only custom file loaded
        assert os.environ.get("CUSTOM_VAR_AT003") == "custom"
        assert os.environ.get("CWD_VAR_AT003") is None
        assert loaded == [custom]

    # =========================================================================
    # AT-004: --env-file Missing File Error
    # =========================================================================
    def test_at_004_env_file_missing_error(self, tmp_path):
        """AT-004: Verify clear error when --env-file path doesn't exist.

        Steps:
        1. Call load_environment(env_file=/nonexistent/.env)

        Expected: FileNotFoundError with path in message
        """
        missing = tmp_path / "nonexistent" / "missing.env"

        # Execute REAL implementation
        with pytest.raises(FileNotFoundError) as exc_info:
            load_environment(env_file=missing)

        # Verify error message contains the path
        assert "missing.env" in str(exc_info.value)
        assert "Environment file not found" in str(exc_info.value)

    # =========================================================================
    # AT-005: --no-env Disables Loading
    # =========================================================================
    def test_at_005_no_env_disables_loading(self, tmp_path, monkeypatch):
        """AT-005: Verify --no-env prevents all .env loading.

        Steps:
        1. Create .env in cwd with TEST_VAR=hello
        2. Unset TEST_VAR
        3. Call load_environment(no_env=True)

        Expected: TEST_VAR is NOT in environment
        """
        # Setup
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("NOENV_VAR_AT005=should_not_load")
        monkeypatch.delenv("NOENV_VAR_AT005", raising=False)

        # Execute REAL implementation with no_env=True
        loaded = load_environment(no_env=True)

        # Verify no files loaded
        assert os.environ.get("NOENV_VAR_AT005") is None
        assert loaded == []

    # =========================================================================
    # AT-006: Mutual Exclusivity Error
    # =========================================================================
    def test_at_006_mutual_exclusivity_error(self):
        """AT-006: Verify --env-file and --no-env cannot be used together.

        Steps:
        1. Parse args with both --env-file and --no-env

        Expected: SystemExit with code 2 (argparse error)
        """
        # Execute REAL parser
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--env-file", ".env", "--no-env", "status"])

        # Verify argparse error code
        assert exc_info.value.code == 2

    # =========================================================================
    # AT-007: All Commands Support Flags
    # =========================================================================
    def test_at_007a_init_command_supports_no_env(self):
        """AT-007a: Verify --no-env works with init command."""
        parser = create_parser()
        args = parser.parse_args(["--no-env", "init"])

        assert args.no_env is True
        assert args.command == "init"

    def test_at_007b_status_command_supports_env_file(self):
        """AT-007b: Verify --env-file works with status command."""
        parser = create_parser()
        args = parser.parse_args(["--env-file", ".env", "status"])

        assert args.env_file == Path(".env")
        assert args.command == "status"

    def test_at_007c_run_command_supports_no_env(self):
        """AT-007c: Verify --no-env works with run command."""
        parser = create_parser()
        args = parser.parse_args(["--no-env", "run", "objectives/task.md"])

        assert args.no_env is True
        assert args.command == "run"
        assert args.objective == "objectives/task.md"

    # =========================================================================
    # AT-008: uvx Invocation Loads CWD .env
    # =========================================================================
    def test_at_008_uvx_invocation_cwd_loading(self, tmp_path, monkeypatch):
        """AT-008: Verify uvx-style invocation loads .env from current directory.

        This test validates the core fix: using Path.cwd() explicitly instead
        of relying on find_dotenv() which searches from module location.

        Steps:
        1. Create .env with UVX_TEST=success
        2. Simulate uvx invocation (call load_environment from different cwd)
        3. Verify variable is loaded

        Expected: UVX_TEST=success is available

        Note: Actual uvx invocation requires external package installation.
        This test validates the underlying mechanism that makes uvx work.
        """
        # Setup - simulate being in a different cwd than module location
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("UVX_TEST_AT008=success")
        monkeypatch.delenv("UVX_TEST_AT008", raising=False)

        # The key fix: load_environment uses Path.cwd() explicitly
        # This is what makes uvx work (vs find_dotenv which uses module path)
        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            loaded = load_environment()

        # Verify - cwd .env loaded regardless of module location
        assert os.environ.get("UVX_TEST_AT008") == "success"
        assert tmp_path / ".env" in loaded


class TestExtractEnvArgsValidation:
    """Validate extract_env_args function works correctly for CLI integration."""

    def test_at_extract_removes_env_args_from_argv(self):
        """Validate that env args are extracted and removed from argv."""
        argv = ["teambot", "--env-file", "custom.env", "--verbose", "run", "obj.md"]

        env_args, cleaned = extract_env_args(argv)

        assert env_args.env_file == Path("custom.env")
        assert env_args.no_env is False
        assert "--env-file" not in cleaned
        assert "custom.env" not in cleaned
        assert cleaned == ["teambot", "--verbose", "run", "obj.md"]

    def test_at_extract_handles_no_env_flag(self):
        """Validate --no-env is extracted correctly."""
        argv = ["teambot", "--no-env", "status"]

        env_args, cleaned = extract_env_args(argv)

        assert env_args.no_env is True
        assert env_args.env_file is None
        assert "--no-env" not in cleaned
        assert cleaned == ["teambot", "status"]


class TestFindEnvFilesValidation:
    """Validate find_env_files discovers files correctly."""

    def test_at_finds_cwd_and_parent_files(self, tmp_path, monkeypatch):
        """Validate hierarchical discovery works."""
        # Create structure: parent/.env -> child/.env
        child = tmp_path / "child"
        child.mkdir()
        monkeypatch.chdir(child)

        parent_env = tmp_path / ".env"
        parent_env.write_text("PARENT=value")
        child_env = child / ".env"
        child_env.write_text("CHILD=value")

        with patch("teambot.env_loader.find_git_root", return_value=tmp_path):
            result = find_env_files(child)

        # Should find both, cwd first
        assert len(result) == 2
        assert result[0] == child_env
        assert result[1] == parent_env
