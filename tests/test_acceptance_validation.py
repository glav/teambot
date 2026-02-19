"""Acceptance Validation Tests - Integration tests exercising REAL implementation.

These tests call the real implementation code with minimal mocking.
Only external dependencies (Copilot CLI, network) are mocked.
"""

import argparse
import json
from unittest.mock import AsyncMock, patch


class TestAcceptanceScenarios:
    """Integration tests for acceptance scenarios AT-001 through AT-005."""

    # =========================================================================
    # AT-001: First Run After Installation (Happy Path)
    # =========================================================================

    def test_at_001_first_run_missing_cache_triggers_refresh(self, tmp_path, monkeypatch, capsys):
        """AT-001: Missing cache triggers auto-refresh with user feedback.

        Tests the REAL implementation:
        - _check_copilot_authentication_blocking() is called
        - _ensure_model_cache() detects missing cache
        - User sees "Refreshing model cache..." message
        - Workflow can proceed after refresh
        """
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Setup: Create minimal valid config and .teambot directory
        (tmp_path / ".teambot").mkdir()
        config = {"agents": []}
        (tmp_path / "teambot.json").write_text(json.dumps(config))

        # Mock ONLY external dependencies:
        # 1. Copilot CLI auth check (external process)
        # 2. Model cache file (filesystem state)
        # 3. Network refresh call (external API)
        # 4. Interactive REPL (would block)

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            # Simulate missing cache file - load_cache returns None
            with patch("teambot.config.model_cache.load_cache", return_value=None):
                # Cache is invalid when None
                with patch("teambot.config.model_cache.is_cache_valid", return_value=False):
                    # Mock the async refresh to succeed
                    with patch(
                        "teambot.cli._refresh_model_cache_async",
                        AsyncMock(return_value=True),
                    ):
                        # Mock REPL to avoid blocking
                        async def mock_repl(*args, **kwargs):
                            pass

                        with patch("teambot.repl.run_interactive_mode", mock_repl):
                            args = argparse.Namespace(
                                config="teambot.json", objective=None, resume=False
                            )
                            display = ConsoleDisplay()

                            # Call REAL cmd_run implementation
                            result = cmd_run(args, display)

        captured = capsys.readouterr()

        # Verify the REAL implementation behavior:
        # 1. Shows refresh message (from _ensure_model_cache)
        assert "Refreshing model cache" in captured.out, (
            f"Expected refresh message in output: {captured.out}"
        )

        # 2. Workflow proceeds (exit code 0)
        assert result == 0, f"Expected exit code 0, got {result}"

    def test_at_001_refresh_success_continues_to_workflow(self, tmp_path, monkeypatch, capsys):
        """AT-001: After successful refresh, workflow execution begins normally."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Setup config with agents (more realistic)
        (tmp_path / ".teambot").mkdir()
        config = {"agents": [{"id": "pm", "persona": "project_manager", "display_name": "PM"}]}
        (tmp_path / "teambot.json").write_text(json.dumps(config))

        workflow_started = False

        async def mock_repl(*args, **kwargs):
            nonlocal workflow_started
            workflow_started = True

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.config.model_cache.load_cache", return_value=None):
                with patch("teambot.config.model_cache.is_cache_valid", return_value=False):
                    with patch(
                        "teambot.cli._refresh_model_cache_async",
                        AsyncMock(return_value=True),
                    ):
                        with patch("teambot.repl.run_interactive_mode", mock_repl):
                            args = argparse.Namespace(
                                config="teambot.json", objective=None, resume=False
                            )
                            display = ConsoleDisplay()

                            result = cmd_run(args, display)

        # Verify workflow reached interactive mode (would be SETUP stage)
        assert workflow_started, "Workflow should have started after cache refresh"
        assert result == 0

    # =========================================================================
    # AT-002: Unauthenticated User
    # =========================================================================

    def test_at_002_unauthenticated_blocks_with_guidance(self, tmp_path, monkeypatch, capsys):
        """AT-002: Unauthenticated user sees clear error with 'copilot auth' guidance.

        Tests the REAL implementation:
        - _check_copilot_authentication_blocking() returns False
        - cmd_run exits with code 1
        - User sees actionable error message
        """
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Config exists but auth will fail first
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        # Mock Copilot CLI returning not authenticated
        with patch(
            "teambot.cli._check_auth_async",
            AsyncMock(return_value=(False, "Not authenticated")),
        ):
            args = argparse.Namespace(config="teambot.json", objective=None, resume=False)
            display = ConsoleDisplay()

            # Call REAL cmd_run
            result = cmd_run(args, display)

        captured = capsys.readouterr()

        # Verify REAL implementation behavior:
        # 1. Exit code 1
        assert result == 1, f"Expected exit code 1, got {result}"

        # 2. Error message mentions authentication
        assert "not authenticated" in captured.out.lower(), (
            f"Expected auth error in: {captured.out}"
        )

        # 3. Guidance to run copilot auth
        assert "copilot auth" in captured.out.lower(), (
            f"Expected 'copilot auth' guidance in: {captured.out}"
        )

    def test_at_002_auth_failure_prevents_config_loading(self, tmp_path, monkeypatch, capsys):
        """AT-002: Auth failure blocks BEFORE config loading (no model validation)."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Create INVALID config - if loaded, would cause JSON error
        (tmp_path / "teambot.json").write_text("{ invalid json <<<")

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(False, None))):
            args = argparse.Namespace(config="teambot.json", objective=None, resume=False)
            display = ConsoleDisplay()

            result = cmd_run(args, display)

        captured = capsys.readouterr()

        # Auth failure should happen BEFORE config loading
        assert result == 1
        assert "not authenticated" in captured.out.lower()
        # Should NOT see JSON parse error
        assert "json" not in captured.out.lower(), "Config should not be loaded"

    # =========================================================================
    # AT-003: Network Failure During Cache Refresh
    # =========================================================================

    def test_at_003_network_failure_continues_gracefully(self, tmp_path, monkeypatch, capsys):
        """AT-003: Network failure during refresh continues (graceful degradation).

        Tests the REAL implementation:
        - _ensure_model_cache() attempts refresh
        - Refresh fails (network error)
        - Function continues (non-blocking design)
        - ConfigLoader will report specific model errors if needed
        """
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        (tmp_path / ".teambot").mkdir()
        # Config with no model references - will pass validation even without cache
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        async def mock_repl(*args, **kwargs):
            pass

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.config.model_cache.load_cache", return_value=None):
                with patch("teambot.config.model_cache.is_cache_valid", return_value=False):
                    # Refresh fails (simulating network error)
                    with patch(
                        "teambot.cli._refresh_model_cache_async",
                        AsyncMock(return_value=False),
                    ):
                        with patch("teambot.repl.run_interactive_mode", mock_repl):
                            args = argparse.Namespace(
                                config="teambot.json", objective=None, resume=False
                            )
                            display = ConsoleDisplay()

                            result = cmd_run(args, display)

        captured = capsys.readouterr()

        # REAL implementation is non-blocking:
        # 1. Should still attempt refresh (shows message)
        assert "Refreshing model cache" in captured.out

        # 2. Should continue despite failure (graceful degradation)
        # With agents: [] config, no model validation needed
        assert result == 0, "Should continue despite refresh failure"

    # =========================================================================
    # AT-004: Returning User With Valid Cache (No-Op)
    # =========================================================================

    def test_at_004_valid_cache_skips_refresh(self, tmp_path, monkeypatch, capsys):
        """AT-004: Valid cache means no refresh - fast startup path.

        Tests the REAL implementation:
        - _ensure_model_cache() detects valid cache
        - No refresh message displayed
        - No network calls made
        - Workflow starts immediately
        """
        from unittest.mock import MagicMock

        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        (tmp_path / ".teambot").mkdir()
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        mock_cache = MagicMock()
        mock_cache.models = ["model-1", "model-2"]  # Non-empty cache

        async def mock_repl(*args, **kwargs):
            pass

        refresh_called = False

        def track_refresh(*args, **kwargs):
            nonlocal refresh_called
            refresh_called = True

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            # Valid cache exists
            with patch("teambot.config.model_cache.load_cache", return_value=mock_cache):
                with patch("teambot.config.model_cache.is_cache_valid", return_value=True):
                    with patch("teambot.cli._refresh_model_cache", track_refresh):
                        with patch("teambot.repl.run_interactive_mode", mock_repl):
                            args = argparse.Namespace(
                                config="teambot.json", objective=None, resume=False
                            )
                            display = ConsoleDisplay()

                            result = cmd_run(args, display)

        captured = capsys.readouterr()

        # REAL implementation with valid cache:
        # 1. No refresh message
        assert "Refreshing model cache" not in captured.out, f"Should not refresh: {captured.out}"

        # 2. Refresh function not called
        assert not refresh_called, "Refresh should not be called for valid cache"

        # 3. Workflow proceeds
        assert result == 0

    def test_at_004_valid_cache_no_delay(self, tmp_path, monkeypatch, capsys):
        """AT-004: Valid cache path has minimal overhead."""
        import time
        from unittest.mock import MagicMock

        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        (tmp_path / ".teambot").mkdir()
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        mock_cache = MagicMock()

        async def mock_repl(*args, **kwargs):
            pass

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.config.model_cache.load_cache", return_value=mock_cache):
                with patch("teambot.config.model_cache.is_cache_valid", return_value=True):
                    with patch("teambot.repl.run_interactive_mode", mock_repl):
                        args = argparse.Namespace(
                            config="teambot.json", objective=None, resume=False
                        )
                        display = ConsoleDisplay()

                        start = time.time()
                        result = cmd_run(args, display)
                        elapsed = time.time() - start

        # Should be fast (< 1 second for the check path)
        assert elapsed < 1.0, f"Valid cache path took too long: {elapsed}s"
        assert result == 0

    # =========================================================================
    # AT-005: Cache Exists But Empty
    # =========================================================================

    def test_at_005_empty_cache_triggers_refresh(self, tmp_path, monkeypatch, capsys):
        """AT-005: Empty cache is treated same as missing - triggers refresh.

        Tests the REAL implementation:
        - is_cache_valid() returns False for empty cache
        - _ensure_model_cache() triggers refresh
        - Same flow as AT-001
        """
        from unittest.mock import MagicMock

        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        (tmp_path / ".teambot").mkdir()
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        # Empty cache - exists but no models
        empty_cache = MagicMock()
        empty_cache.models = []

        async def mock_repl(*args, **kwargs):
            pass

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            # Cache exists but is invalid (empty)
            with patch("teambot.config.model_cache.load_cache", return_value=empty_cache):
                with patch("teambot.config.model_cache.is_cache_valid", return_value=False):
                    with patch(
                        "teambot.cli._refresh_model_cache_async",
                        AsyncMock(return_value=True),
                    ):
                        with patch("teambot.repl.run_interactive_mode", mock_repl):
                            args = argparse.Namespace(
                                config="teambot.json", objective=None, resume=False
                            )
                            display = ConsoleDisplay()

                            result = cmd_run(args, display)

        captured = capsys.readouterr()

        # Empty cache triggers refresh like missing cache
        assert "Model cache is empty, refreshing" in captured.out
        assert result == 0


class TestRealFunctionBehavior:
    """Direct tests of the real helper functions."""

    def test_at_001_helper_check_auth_blocking_authenticated(self, capsys):
        """Test _check_copilot_authentication_blocking with authenticated user."""
        from teambot.cli import _check_copilot_authentication_blocking
        from teambot.visualization.console import ConsoleDisplay

        # Only mock the external async call
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            display = ConsoleDisplay()
            result = _check_copilot_authentication_blocking(display)

        assert result is True
        captured = capsys.readouterr()
        assert "not authenticated" not in captured.out.lower()

    def test_at_002_helper_check_auth_blocking_not_authenticated(self, capsys):
        """Test _check_copilot_authentication_blocking with unauthenticated user."""
        from teambot.cli import _check_copilot_authentication_blocking
        from teambot.visualization.console import ConsoleDisplay

        with patch(
            "teambot.cli._check_auth_async",
            AsyncMock(return_value=(False, "Token expired")),
        ):
            display = ConsoleDisplay()
            result = _check_copilot_authentication_blocking(display)

        assert result is False
        captured = capsys.readouterr()
        assert "not authenticated" in captured.out.lower()
        assert "copilot auth" in captured.out.lower()

    def test_at_004_helper_ensure_model_cache_valid(self, capsys):
        """Test _ensure_model_cache with valid cache - no refresh."""
        from unittest.mock import MagicMock

        from teambot.cli import _ensure_model_cache
        from teambot.visualization.console import ConsoleDisplay

        mock_cache = MagicMock()

        with patch("teambot.config.model_cache.load_cache", return_value=mock_cache):
            with patch("teambot.config.model_cache.is_cache_valid", return_value=True):
                with patch("teambot.cli._refresh_model_cache") as mock_refresh:
                    display = ConsoleDisplay()
                    _ensure_model_cache(display)

        mock_refresh.assert_not_called()
        captured = capsys.readouterr()
        assert "Refreshing" not in captured.out

    def test_at_005_helper_ensure_model_cache_missing(self, capsys):
        """Test _ensure_model_cache with missing cache - triggers refresh."""
        from teambot.cli import _ensure_model_cache
        from teambot.visualization.console import ConsoleDisplay

        with patch("teambot.config.model_cache.load_cache", return_value=None):
            with patch("teambot.config.model_cache.is_cache_valid", return_value=False):
                with patch("teambot.cli._refresh_model_cache") as mock_refresh:
                    display = ConsoleDisplay()
                    _ensure_model_cache(display)

        mock_refresh.assert_called_once()
        captured = capsys.readouterr()
        assert "Refreshing model cache" in captured.out
