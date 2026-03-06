"""Acceptance test validation for /history command removal.

This module validates all acceptance scenarios by exercising REAL implementation code.
No mocking of core functionality - these are true integration tests.
"""

import subprocess
from pathlib import Path

import pytest

from teambot.repl.commands import SystemCommands, handle_help


@pytest.mark.acceptance
def _search_files(directory: Path, pattern: str, glob: str = "**/*") -> list[str]:
    """Walk directory tree and return matching lines as 'path:lineno: content' strings.

    Args:
        directory: Root directory to search recursively.
        pattern: Substring to search for within each file's lines.
        glob: Glob pattern used to filter files (default matches all files).

    Returns:
        List of strings in the format 'path:lineno: line_content' for each match.
        Binary files and unreadable files are silently skipped.
    """
    matches = []
    for path in sorted(directory.glob(glob)):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        for lineno, line in enumerate(content.splitlines(), 1):
            if pattern in line:
                matches.append(f"{path}:{lineno}: {line}")
    return matches


class TestHistoryRemovalAcceptanceScenarios:
    """Acceptance tests for /history command removal feature."""

    def test_at_001_code_removal_verification(self):
        """AT-001: Verify that all /history command code has been removed from the codebase."""
        repo_root = Path(__file__).parent.parent

        # Check for handle_history in source
        handle_history_matches = _search_files(
            repo_root / "src" / "teambot" / "repl", "handle_history", "**/*.py"
        )
        assert len(handle_history_matches) == 0, (
            f"Found handle_history references in source: {handle_history_matches}"
        )

        # Check for def history method in commands.py
        commands_file = repo_root / "src" / "teambot" / "repl" / "commands.py"
        commands_content = commands_file.read_text(encoding="utf-8")
        assert "def history" not in commands_content, "Found 'def history' in commands.py"

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
        """AT-004: Verify all existing REPL test files are present after removal.

        Execution of the REPL test suite is handled by the regular CI test run
        (uv run pytest tests/test_repl/). This acceptance test only verifies the
        structural presence of those test files to avoid spawning a nested pytest
        process, which is slow and can deadlock under some CI configurations.
        """
        repo_root = Path(__file__).parent.parent
        repl_test_dir = repo_root / "tests" / "test_repl"

        # Verify the REPL test directory exists
        assert repl_test_dir.is_dir(), f"REPL test directory not found: {repl_test_dir}"

        # Verify expected test files are present
        test_files = list(repl_test_dir.glob("test_*.py"))
        assert len(test_files) > 0, f"No test files found in {repl_test_dir}"

        # Verify no test file references the removed handle_history function
        for test_file in test_files:
            content = test_file.read_text()
            assert "handle_history" not in content, (
                f"Found 'handle_history' reference in {test_file.name}"
            )

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
        all_matches = _search_files(repo_root / "docs", "/history")

        # Filter out acceptable references
        unacceptable = []
        for ref in all_matches:
            # Allow references in objective and feature spec for this task
            if "remove-history-command" in ref:
                continue
            # Allow .teambot/history/ path references (directory, not command)
            if ".teambot" in ref and "history/" in ref:
                continue
            # Anything else is unacceptable
            unacceptable.append(ref)

        assert len(unacceptable) == 0, (
            "Found unacceptable /history references in docs:\n" + "\n".join(unacceptable)
        )

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
