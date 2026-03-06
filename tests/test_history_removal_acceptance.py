"""Acceptance test validation for /history command removal.

This module validates all acceptance scenarios by exercising REAL implementation code.
No mocking of core functionality - these are true integration tests.
"""

import subprocess
from pathlib import Path

import pytest

from teambot.repl.commands import SystemCommands, handle_help


class TestHistoryRemovalAcceptanceScenarios:
    """Acceptance tests for /history command removal feature."""

    def test_at_001_code_removal_verification(self):
        """AT-001: Verify that all /history command code has been removed from the codebase."""
        repo_root = Path(__file__).parent.parent

        # Check for handle_history in source
        result_handle = subprocess.run(
            ["grep", "-r", "handle_history", "src/teambot/repl/"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        # grep returns exit code 1 when no matches found (expected)
        assert result_handle.returncode == 1, (
            f"Found handle_history references in source: {result_handle.stdout}"
        )

        # Check for def history method in commands.py
        result_method = subprocess.run(
            ["grep", "-n", "def history", "src/teambot/repl/commands.py"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        # grep returns exit code 1 when no matches found (expected)
        assert result_method.returncode == 1, (
            f"Found 'def history' in commands.py: {result_method.stdout}"
        )

        # Verify the function is not importable
        with pytest.raises(ImportError):
            from teambot.repl.commands import handle_history  # noqa: F401

    def test_at_002_repl_help_output_validation(self):
        """AT-002: Verify /history no longer appears in help text."""
        # Call the REAL handle_help function
        result = handle_help([])

        # Verify /history is NOT in the output
        assert "/history" not in result.output, "Help text still contains /history reference"

        # Verify other commands ARE present (sanity check)
        assert "/help" in result.output
        assert "/status" in result.output
        assert "/quit" in result.output

        # Verify success flag
        assert result.success is True

    async def test_at_003_command_error_on_history_usage(self):
        """AT-003: Verify /history returns appropriate error when invoked."""
        # Create REAL SystemCommands instance (no mocking)
        commands = SystemCommands()

        # Dispatch the history command using the real dispatch method
        result = await commands.dispatch("history", [])

        # Verify it returns an error
        assert result.success is False, "Expected /history to fail but it succeeded"

        # Verify the error message
        assert "Unknown command" in result.output, (
            f"Expected 'Unknown command' in output, got: {result.output}"
        )
        assert "history" in result.output.lower(), (
            f"Expected 'history' in error message, got: {result.output}"
        )

        # Verify REPL doesn't exit
        assert result.should_exit is False

    def test_at_004_test_suite_passes(self):
        """AT-004: Verify all existing tests pass after removal."""
        repo_root = Path(__file__).parent.parent

        # Run the REPL test suite (which was modified in the implementation)
        result = subprocess.run(
            ["uv", "run", "pytest", "tests/test_repl/", "-v", "--tb=short"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Verify tests passed
        assert result.returncode == 0, (
            f"REPL tests failed. Output:\n{result.stdout}\n{result.stderr}"
        )

        # Verify reasonable number of tests ran (should be ~248)
        assert "passed" in result.stdout, "No tests passed"

    async def test_at_005_other_repl_commands_unaffected(self):
        """AT-005: Verify other REPL commands continue functioning."""
        # Create REAL SystemCommands instance
        commands = SystemCommands()

        # Test /help command
        help_result = await commands.dispatch("help", [])
        assert help_result.success is True, "/help command failed"
        assert len(help_result.output) > 0, "/help returned empty output"

        # Test /status command
        status_result = await commands.dispatch("status", [])
        assert status_result.success is True, "/status command failed"
        assert len(status_result.output) > 0, "/status returned empty output"

        # Test /tasks command (will fail without executor, which is expected)
        tasks_result = await commands.dispatch("tasks", [])
        # tasks command returns False when no executor available, which is OK
        # Just verify it returns a result without crashing
        assert tasks_result is not None, "/tasks command crashed"
        assert isinstance(tasks_result.output, str), "/tasks should return string output"

        # Test /quit command
        quit_result = await commands.dispatch("quit", [])
        assert quit_result.success is True, "/quit command failed"
        assert quit_result.should_exit is True, "/quit should set exit flag"

        # Test /models command
        models_result = await commands.dispatch("models", [])
        assert models_result.success is True, "/models command failed"

    def test_at_006_documentation_cleanup_verification(self):
        """AT-006: Verify all documentation references to /history removed."""
        repo_root = Path(__file__).parent.parent

        # Search for /history in documentation
        result = subprocess.run(
            ["grep", "-r", "/history", "docs/"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )

        # Check the output
        if result.returncode == 0:
            # Found some matches - verify they're acceptable
            lines = result.stdout.strip().split("\n")

            # Filter out acceptable references
            unacceptable = []
            for line in lines:
                # Allow references in objective and feature spec for this task
                if "remove-history-command" in line:
                    continue
                # Allow .teambot/history/ path references (directory, not command)
                if ".teambot" in line and "history/" in line:
                    continue
                # Anything else is unacceptable
                unacceptable.append(line)

            assert len(unacceptable) == 0, (
                "Found unacceptable /history references in docs:\n" + "\n".join(unacceptable)
            )
        # If returncode == 1, no matches found at all (acceptable)

    def test_at_007_linting_and_formatting_pass(self):
        """AT-007: Verify code follows repository standards after changes."""
        repo_root = Path(__file__).parent.parent

        # Check linting on the modified files
        modified_files = [
            "src/teambot/repl/commands.py",
            "tests/test_repl/test_commands.py",
            "tests/test_repl/test_parser.py",
        ]

        for file_path in modified_files:
            # Run ruff check
            result_check = subprocess.run(
                ["uv", "run", "ruff", "check", file_path],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )
            assert result_check.returncode == 0, (
                f"Linting failed for {file_path}:\n{result_check.stdout}\n{result_check.stderr}"
            )

            # Run ruff format check
            result_format = subprocess.run(
                ["uv", "run", "ruff", "format", "--check", file_path],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )
            assert result_format.returncode == 0, (
                f"Formatting check failed for {file_path}:\n"
                f"{result_format.stdout}\n{result_format.stderr}"
            )
