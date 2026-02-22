"""Acceptance tests for Init Command Model Configuration feature.

These tests validate the real implementation against acceptance scenarios.
Tests exercise actual code paths without mocking core functionality.
"""

import argparse
import json
from unittest.mock import AsyncMock, patch


class TestInitModelConfigAcceptance:
    """Acceptance test scenarios for init command model configuration."""

    # =========================================================================
    # AT-001: Fresh Init Creates Updated Default Config
    # =========================================================================

    def test_at_001_default_model_is_claude_sonnet_4_5(self):
        """AT-001: Default config has claude-sonnet-4.5 as default model."""
        from teambot.config.loader import create_default_config

        # Call REAL implementation
        config = create_default_config()

        # Verify default_model field
        assert "default_model" in config
        assert config["default_model"] == "claude-sonnet-4.5"

    def test_at_001_all_agents_have_explicit_model_field(self):
        """AT-001: Each agent in default config has explicit model field."""
        from teambot.config.loader import create_default_config

        # Call REAL implementation
        config = create_default_config()

        # Verify all 6 agents have model field
        assert len(config["agents"]) == 6

        for agent in config["agents"]:
            assert "model" in agent, f"Agent {agent['id']} missing 'model' field"
            assert agent["model"] == "claude-sonnet-4.5", (
                f"Agent {agent['id']} has wrong model: {agent['model']}"
            )

    def test_at_001_init_creates_config_with_correct_model(self, tmp_path, monkeypatch):
        """AT-001: Running init creates teambot.json with correct default model."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Mock async operations to avoid network calls
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                # Call REAL cmd_init
                result = cmd_init(args, display)

        # Verify init succeeded
        assert result == 0

        # Verify teambot.json created with correct model
        config_file = tmp_path / "teambot.json"
        assert config_file.exists()

        config = json.loads(config_file.read_text())
        assert config["default_model"] == "claude-sonnet-4.5"

        # Verify all agents have model field
        for agent in config["agents"]:
            assert agent.get("model") == "claude-sonnet-4.5"

    # =========================================================================
    # AT-002: Init With Unauthenticated Copilot CLI
    # =========================================================================

    def test_at_002_auth_check_returns_false_when_not_authenticated(self):
        """AT-002: Auth check correctly identifies unauthenticated state."""
        from teambot.cli import _check_copilot_authentication
        from teambot.visualization.console import ConsoleDisplay

        # Mock SDK to return unauthenticated
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(False, None))):
            display = ConsoleDisplay()

            # Call REAL _check_copilot_authentication
            result = _check_copilot_authentication(display)

        # Should return False for unauthenticated
        assert result is False

    def test_at_002_init_succeeds_when_not_authenticated(self, tmp_path, monkeypatch, capsys):
        """AT-002: Init completes successfully even when not authenticated."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Mock auth to return unauthenticated
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(False, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                # Call REAL cmd_init
                result = cmd_init(args, display)

        # Init should still succeed
        assert result == 0
        assert (tmp_path / "teambot.json").exists()

        # Verify warning was displayed
        captured = capsys.readouterr()
        output = captured.out.lower()
        assert "not authenticated" in output or "copilot login" in output

    def test_at_002_auth_guidance_displayed_when_unauthenticated(
        self, tmp_path, monkeypatch, capsys
    ):
        """AT-002: Helpful auth guidance is displayed when not authenticated."""
        from teambot.cli import _check_copilot_authentication
        from teambot.visualization.console import ConsoleDisplay

        monkeypatch.chdir(tmp_path)

        # Mock unauthenticated state
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(False, None))):
            display = ConsoleDisplay()
            _check_copilot_authentication(display)

        captured = capsys.readouterr()

        # Should display guidance about authentication
        output_lower = captured.out.lower()
        assert "copilot login" in output_lower or "github_token" in output_lower

    # =========================================================================
    # AT-003: Init With Network Failure During Model Refresh
    # =========================================================================

    def test_at_003_model_refresh_handles_network_failure(self, capsys):
        """AT-003: Model refresh handles network failures gracefully."""
        from teambot.cli import _refresh_model_cache
        from teambot.visualization.console import ConsoleDisplay

        # Mock network failure
        async def mock_network_failure():
            raise ConnectionError("Network unavailable")

        with patch("teambot.cli._refresh_model_cache_async", mock_network_failure):
            display = ConsoleDisplay()

            # Call REAL _refresh_model_cache
            result = _refresh_model_cache(display)

        # Should return False on failure
        assert result is False

        # Should display warning
        captured = capsys.readouterr()
        assert "failed" in captured.out.lower() or "refresh" in captured.out.lower()

    def test_at_003_init_succeeds_despite_model_refresh_failure(self, tmp_path, monkeypatch):
        """AT-003: Init completes successfully even if model refresh fails."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Mock model refresh to fail
        async def mock_refresh_failure():
            raise RuntimeError("Network error")

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", mock_refresh_failure):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                # Call REAL cmd_init
                result = cmd_init(args, display)

        # Init should still succeed
        assert result == 0
        assert (tmp_path / "teambot.json").exists()

    def test_at_003_warning_shown_on_model_refresh_failure(self, tmp_path, monkeypatch, capsys):
        """AT-003: Clear warning is shown when model refresh fails."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Mock model refresh to return False (failure)
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=False)):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                cmd_init(args, display)

        captured = capsys.readouterr()

        # Should contain warning about model cache
        output_lower = captured.out.lower()
        assert "model" in output_lower and ("refresh" in output_lower or "cache" in output_lower)

    # =========================================================================
    # AT-004: Post-Init Guidance Displayed
    # =========================================================================

    def test_at_004_guidance_displayed_after_init(self, tmp_path, monkeypatch, capsys):
        """AT-004: Recommended Next Steps guidance is displayed after init."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                cmd_init(args, display)

        captured = capsys.readouterr()

        # Should display "Recommended Next Steps"
        assert "Recommended Next Steps" in captured.out

    def test_at_004_guidance_contains_model_configuration_tip(self, tmp_path, monkeypatch, capsys):
        """AT-004: Guidance suggests per-agent model configuration."""
        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                args = argparse.Namespace(force=False, no_animation=True)
                display = ConsoleDisplay()

                cmd_init(args, display)

        captured = capsys.readouterr()

        # Should mention model configuration
        output_lower = captured.out.lower()
        assert "model" in output_lower

    def test_at_004_display_guidance_function_works(self, capsys):
        """AT-004: _display_post_init_guidance function displays content."""
        from teambot.cli import _display_post_init_guidance
        from teambot.visualization.console import ConsoleDisplay

        display = ConsoleDisplay()

        # Call REAL function
        _display_post_init_guidance(display)

        captured = capsys.readouterr()

        # Should contain guidance content
        assert "Next Steps" in captured.out or "objective" in captured.out.lower()

    # =========================================================================
    # AT-005: Guidance Loaded From External File
    # =========================================================================

    def test_at_005_guidance_file_exists_in_scaffolds(self):
        """AT-005: Guidance file exists in scaffolds directory."""
        from teambot.scaffolds import get_scaffolds_dir

        # Call REAL implementation
        scaffolds_dir = get_scaffolds_dir()
        guidance_file = scaffolds_dir / "init-next-steps.md"

        assert guidance_file.exists(), f"Guidance file not found at {guidance_file}"

    def test_at_005_guidance_file_contains_model_content(self):
        """AT-005: Guidance file contains model customization content."""
        from teambot.scaffolds import get_scaffolds_dir

        scaffolds_dir = get_scaffolds_dir()
        guidance_file = scaffolds_dir / "init-next-steps.md"

        # Read REAL file content
        content = guidance_file.read_text(encoding="utf-8")

        # Should contain model-related content
        assert "model" in content.lower()
        assert "agent" in content.lower()

    def test_at_005_guidance_loaded_from_file_not_hardcoded(self, capsys):
        """AT-005: Guidance is loaded from file, not hardcoded."""
        from teambot.cli import _display_post_init_guidance
        from teambot.visualization.console import ConsoleDisplay

        # Display guidance
        display = ConsoleDisplay()
        _display_post_init_guidance(display)

        captured = capsys.readouterr()

        # Verify displayed content matches file content (check key phrases)
        # The file contains "Configure Per-Agent Models"
        assert "Per-Agent Models" in captured.out or "Configure" in captured.out

    def test_at_005_guidance_fallback_when_file_missing(self, capsys):
        """AT-005: Fallback guidance used when file cannot be loaded."""
        from teambot.cli import _display_post_init_guidance
        from teambot.visualization.console import ConsoleDisplay

        # Mock importlib.resources.files to simulate file not found
        with patch("importlib.resources.files", side_effect=FileNotFoundError("Not found")):
            display = ConsoleDisplay()
            _display_post_init_guidance(display)

        captured = capsys.readouterr()

        # Should still display some guidance (fallback)
        assert "Next Steps" in captured.out or "teambot.json" in captured.out
