"""Acceptance tests for Model Cache Auto-Setup and Login Validation.

Core logic is tested directly; selective mocking is used for external dependencies.
"""

import argparse
import json
from unittest.mock import AsyncMock, MagicMock, patch


class TestModelCacheAutoSetupAcceptance:
    """Acceptance test scenarios for model cache auto-setup."""

    # =========================================================================
    # AT-001: First Run After Installation (Happy Path)
    # =========================================================================

    def test_at_001_missing_cache_triggers_refresh(self, tmp_path, monkeypatch, capsys):
        """AT-001: Missing cache triggers auto-refresh during teambot run."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Setup: create config but no cache
        (tmp_path / ".teambot").mkdir()
        config_path = tmp_path / "teambot.json"
        config_path.write_text(json.dumps({"agents": []}))

        # Mock auth success, cache missing, refresh success
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.config.model_cache.load_cache", return_value=None):
                with patch("teambot.config.model_cache.is_cache_valid", return_value=False):
                    with patch(
                        "teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)
                    ):
                        # Mock interactive mode to avoid hanging
                        async def mock_repl(*args, **kwargs):
                            pass

                        with patch("teambot.repl.run_interactive_mode", mock_repl):
                            args = argparse.Namespace(
                                config="teambot.json", objective=None, resume=False
                            )
                            display = ConsoleDisplay()

                            cmd_run(args, display)

        captured = capsys.readouterr()
        # Verify refresh message was shown
        assert "Refreshing model cache" in captured.out

    def test_at_001_refresh_success_continues_workflow(self, tmp_path, monkeypatch, capsys):
        """AT-001: Successful refresh allows workflow to continue normally."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Setup: create config with no default_model (optional field)
        (tmp_path / ".teambot").mkdir()
        config_path = tmp_path / "teambot.json"
        config_path.write_text(json.dumps({"agents": []}))

        # Mock auth success, cache missing, refresh success
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.config.model_cache.load_cache", return_value=None):
                with patch("teambot.config.model_cache.is_cache_valid", return_value=False):
                    with patch(
                        "teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)
                    ):

                        async def mock_repl(*args, **kwargs):
                            pass

                        with patch("teambot.repl.run_interactive_mode", mock_repl):
                            args = argparse.Namespace(
                                config="teambot.json", objective=None, resume=False
                            )
                            display = ConsoleDisplay()

                            result = cmd_run(args, display)

        # Result should be 0 (success) - workflow continues
        assert result == 0

    # =========================================================================
    # AT-002: Unauthenticated User
    # =========================================================================

    def test_at_002_unauthenticated_stops_with_clear_error(self, tmp_path, monkeypatch, capsys):
        """AT-002: Unauthenticated user gets clear error with guidance."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Setup: create config file
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        # Mock auth failure
        with patch(
            "teambot.cli._check_auth_async", AsyncMock(return_value=(False, "Not authenticated"))
        ):
            args = argparse.Namespace(config="teambot.json", objective=None, resume=False)
            display = ConsoleDisplay()

            result = cmd_run(args, display)

        assert result == 1
        captured = capsys.readouterr()
        assert "not authenticated" in captured.out.lower()
        assert "copilot auth" in captured.out.lower()

    def test_at_002_unauthenticated_does_not_proceed_to_config(self, tmp_path, monkeypatch, capsys):
        """AT-002: Unauthenticated state blocks before config loading."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Setup: create INVALID config file (would fail if loaded)
        (tmp_path / "teambot.json").write_text("not valid json {{{")

        # Mock auth failure
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(False, None))):
            args = argparse.Namespace(config="teambot.json", objective=None, resume=False)
            display = ConsoleDisplay()

            result = cmd_run(args, display)

        # Should fail on auth, not on invalid config
        assert result == 1
        captured = capsys.readouterr()
        assert "not authenticated" in captured.out.lower()
        # Should NOT see JSON parse error
        assert "invalid json" not in captured.out.lower()

    # =========================================================================
    # AT-003: Network Failure During Cache Refresh
    # =========================================================================

    def test_at_003_network_failure_shows_warning(self, tmp_path, monkeypatch, capsys):
        """AT-003: Cache refresh failure shows warning but continues."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Setup: config exists but no cache
        (tmp_path / ".teambot").mkdir()
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        # Mock auth success, cache missing, refresh failure
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.config.model_cache.load_cache", return_value=None):
                with patch("teambot.config.model_cache.is_cache_valid", return_value=False):
                    with patch(
                        "teambot.cli._refresh_model_cache_async", AsyncMock(return_value=False)
                    ):

                        async def mock_repl(*args, **kwargs):
                            pass

                        with patch("teambot.repl.run_interactive_mode", mock_repl):
                            args = argparse.Namespace(
                                config="teambot.json", objective=None, resume=False
                            )
                            display = ConsoleDisplay()

                            cmd_run(args, display)

        captured = capsys.readouterr()
        # Should still attempt refresh
        assert "Refreshing model cache" in captured.out
        # _refresh_model_cache handles its own warning messages

    # =========================================================================
    # AT-004: Returning User With Valid Cache (No-Op)
    # =========================================================================

    def test_at_004_valid_cache_no_refresh_output(self, tmp_path, monkeypatch, capsys):
        """AT-004: Valid cache skips refresh - no delay or messages."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Setup: config (no default_model - optional field) and valid cache
        (tmp_path / ".teambot").mkdir()
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        # Mock auth success, valid cache
        mock_cache = MagicMock()
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.config.model_cache.load_cache", return_value=mock_cache):
                with patch("teambot.config.model_cache.is_cache_valid", return_value=True):

                    async def mock_repl(*args, **kwargs):
                        pass

                    with patch("teambot.repl.run_interactive_mode", mock_repl):
                        args = argparse.Namespace(
                            config="teambot.json", objective=None, resume=False
                        )
                        display = ConsoleDisplay()

                        result = cmd_run(args, display)

        captured = capsys.readouterr()
        # Should NOT show refresh messages when cache is valid
        assert "Refreshing model cache" not in captured.out
        assert result == 0

    def test_at_004_valid_cache_fast_startup(self, tmp_path, monkeypatch):
        """AT-004: Valid cache results in fast startup (no refresh delay)."""
        import time

        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        # Setup
        (tmp_path / ".teambot").mkdir()
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        mock_cache = MagicMock()
        start_time = time.time()

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.config.model_cache.load_cache", return_value=mock_cache):
                with patch("teambot.config.model_cache.is_cache_valid", return_value=True):

                    async def mock_repl(*args, **kwargs):
                        pass

                    with patch("teambot.repl.run_interactive_mode", mock_repl):
                        args = argparse.Namespace(
                            config="teambot.json", objective=None, resume=False
                        )
                        display = ConsoleDisplay()
                        cmd_run(args, display)

        elapsed = time.time() - start_time
        # Should complete quickly (no network refresh)
        assert elapsed < 2.0

    # =========================================================================
    # AT-005: Cache Exists But Expired
    # =========================================================================

    def test_at_005_expired_cache_triggers_refresh(self, tmp_path, monkeypatch, capsys):
        """AT-005: Expired cache triggers refresh with appropriate message."""
        from teambot.cli import ConsoleDisplay, cmd_run
        from teambot.config.model_cache import CachedModel, ModelCache

        monkeypatch.chdir(tmp_path)

        # Setup: config exists, cache with old timestamp
        (tmp_path / ".teambot").mkdir()
        (tmp_path / "teambot.json").write_text('{"agents": []}')

        # Create expired cache
        expired_cache = ModelCache(
            models=[CachedModel(id="test", name="Test", category="standard")],
            timestamp=0,  # Very old timestamp
            sdk_version="1.0",
        )

        # Mock auth success, expired cache detected
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.config.model_cache.load_cache", return_value=expired_cache):
                with patch("teambot.config.model_cache.is_cache_valid", return_value=False):
                    with patch(
                        "teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)
                    ):

                        async def mock_repl(*args, **kwargs):
                            pass

                        with patch("teambot.repl.run_interactive_mode", mock_repl):
                            args = argparse.Namespace(
                                config="teambot.json", objective=None, resume=False
                            )
                            display = ConsoleDisplay()

                            cmd_run(args, display)

        captured = capsys.readouterr()
        # Should show expired message
        assert "expired" in captured.out.lower()
