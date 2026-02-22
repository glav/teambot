"""Acceptance Tests for Auth Message Fix - Integration tests exercising REAL implementation.

These tests validate the 'copilot auth' -> 'copilot login' message update.
Tests call the real implementation code with minimal mocking for external dependencies only.
"""

import argparse
from unittest.mock import AsyncMock, patch

import pytest


class TestAuthMessageAcceptance:
    """Integration tests for auth message fix acceptance scenarios AT-001 through AT-004."""

    # =========================================================================
    # AT-001: Unauthenticated User Runs TeamBot
    # =========================================================================

    def test_at_001_unauthenticated_run_shows_copilot_login(self, tmp_path, monkeypatch, capsys):
        """AT-001: Verify 'teambot run' shows 'copilot login' when not authenticated.

        Tests REAL implementation:
        - _check_copilot_authentication_blocking() is called
        - Error message contains 'copilot login'
        - Error message does NOT contain 'copilot auth'
        """
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Create minimal config
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        # Mock ONLY the external Copilot CLI call - everything else is REAL
        with patch(
            "teambot.cli._check_auth_async",
            AsyncMock(return_value=(False, "Not authenticated")),
        ):
            args = argparse.Namespace(config="teambot.json", objective=None, resume=False)
            display = ConsoleDisplay()

            # Call REAL cmd_run implementation
            result = cmd_run(args, display)

        captured = capsys.readouterr()
        output_lower = captured.out.lower()

        # Verify REAL implementation behavior
        assert result == 1, f"Expected exit code 1, got {result}"
        assert "copilot login" in output_lower, (
            f"Expected 'copilot login' in output, got: {captured.out}"
        )
        assert "copilot auth" not in output_lower, (
            f"Should NOT contain 'copilot auth', got: {captured.out}"
        )

    def test_at_001_blocking_auth_exception_shows_copilot_login(self, capsys):
        """AT-001: Verify exception handling also shows 'copilot login'.

        Tests REAL _check_copilot_authentication_blocking function directly.
        """
        from teambot.cli import _check_copilot_authentication_blocking
        from teambot.visualization.console import ConsoleDisplay

        async def raise_error():
            raise RuntimeError("Connection failed")

        with patch("teambot.cli._check_auth_async", raise_error):
            display = ConsoleDisplay()
            result = _check_copilot_authentication_blocking(display)

        captured = capsys.readouterr()
        output_lower = captured.out.lower()

        assert result is False
        assert "copilot login" in output_lower
        assert "copilot auth" not in output_lower

    # =========================================================================
    # AT-002: Unauthenticated User Runs Init
    # =========================================================================

    def test_at_002_unauthenticated_init_shows_copilot_login(self, capsys):
        """AT-002: Verify 'teambot init' auth check shows 'copilot login'.

        Tests REAL _check_copilot_authentication function directly.
        """
        from teambot.cli import _check_copilot_authentication
        from teambot.visualization.console import ConsoleDisplay

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(False, None))):
            display = ConsoleDisplay()
            result = _check_copilot_authentication(display)

        captured = capsys.readouterr()
        output_lower = captured.out.lower()

        assert result is False
        assert "copilot login" in output_lower
        assert "copilot auth" not in output_lower

    def test_at_002_init_auth_exception_shows_copilot_login(self, capsys):
        """AT-002: Verify init exception handling shows 'copilot login'.

        Tests REAL _check_copilot_authentication with exception scenario.
        """
        from teambot.cli import _check_copilot_authentication
        from teambot.visualization.console import ConsoleDisplay

        async def raise_error():
            raise RuntimeError("Auth check failed")

        with patch("teambot.cli._check_auth_async", raise_error):
            display = ConsoleDisplay()
            result = _check_copilot_authentication(display)

        captured = capsys.readouterr()
        output_lower = captured.out.lower()

        assert result is False
        assert "copilot login" in output_lower
        assert "copilot auth" not in output_lower

    # =========================================================================
    # AT-003: Test Suite Passes with Updated Assertions
    # =========================================================================

    def test_at_003_no_copilot_auth_in_cli_source(self):
        """AT-003: Verify source code has no 'copilot auth' strings.

        This test reads the REAL source file and validates no 'copilot auth' remains.
        """
        import pathlib

        cli_path = pathlib.Path("src/teambot/cli.py")
        assert cli_path.exists(), "cli.py not found"

        content = cli_path.read_text()

        # Should have copilot login
        assert "copilot login" in content, "cli.py should contain 'copilot login'"

        # Should NOT have copilot auth
        assert "copilot auth" not in content, "cli.py should NOT contain 'copilot auth'"

    def test_at_003_no_copilot_auth_in_test_assertions(self):
        """AT-003: Verify test files have no 'copilot auth' in assertions.

        This test reads REAL test files and validates assertions are updated.
        """
        import pathlib

        test_files = [
            "tests/test_cli.py",
            "tests/test_acceptance_validation.py",
            "tests/test_init_model_config_acceptance.py",
            "tests/test_model_cache_auto_acceptance.py",
        ]

        for test_file in test_files:
            path = pathlib.Path(test_file)
            assert path.exists(), f"{test_file} not found"

            content = path.read_text()

            # Check for copilot auth in assertions (not in comments/docstrings about the change)
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if "assert" in line and "copilot auth" in line.lower():
                    pytest.fail(
                        f"{test_file}:{i} contains 'copilot auth' in assertion: {line.strip()}"
                    )

    # =========================================================================
    # AT-004: Documentation Shows Correct Command
    # =========================================================================

    def test_at_004_readme_shows_copilot_login(self):
        """AT-004: Verify README.md shows 'copilot login'.

        This test reads the REAL README file.
        """
        import pathlib

        readme_path = pathlib.Path("README.md")
        assert readme_path.exists(), "README.md not found"

        content = readme_path.read_text()

        # Should have copilot login
        assert "copilot login" in content, "README.md should contain 'copilot login'"

        # Should NOT have copilot auth (in user-facing instructions)
        # Note: We check for the specific pattern used in instructions
        assert "authenticate with `copilot auth`" not in content, (
            "README.md should NOT contain 'authenticate with `copilot auth`'"
        )

    def test_at_004_installation_guide_shows_copilot_login(self):
        """AT-004: Verify installation.md shows 'copilot login'.

        This test reads the REAL installation guide file.
        """
        import pathlib

        install_path = pathlib.Path("docs/guides/installation.md")
        assert install_path.exists(), "installation.md not found"

        content = install_path.read_text()

        # Should have copilot login (at least twice - lines 17 and 227)
        assert content.count("copilot login") >= 2, (
            "installation.md should contain 'copilot login' at least twice"
        )

        # Count copilot auth - should be 0 in code blocks
        # (Historical context in prose may remain)
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            # Check code lines (start with copilot or in code block)
            if line.strip().startswith("copilot auth"):
                pytest.fail(f"installation.md:{i} contains 'copilot auth' command: {line.strip()}")
