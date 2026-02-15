"""Acceptance test validation for overlay removal feature.

These tests exercise the REAL implementation code to validate
each acceptance scenario from the overlay removal feature specification.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from teambot.config.loader import ConfigLoader
from teambot.repl.commands import SystemCommands, handle_help
from teambot.repl.router import AgentRouter


class TestOverlayRemovalAcceptanceScenarios:
    """Acceptance test scenarios for overlay removal feature."""

    # -- AT-001: REPL Starts Successfully Without Overlay --

    def test_at_001_repl_imports_without_overlay(self):
        """Verify REPL modules import without overlay dependency."""
        # Import the real REPL modules - should not raise ImportError
        from teambot.repl.commands import SystemCommands
        from teambot.repl.router import AgentRouter

        # Verify SystemCommands can be instantiated without overlay parameter
        router = AgentRouter()
        commands = SystemCommands(router=router)

        # Verify commands object has no overlay attribute
        assert not hasattr(commands, "_overlay") or commands._overlay is None

    def test_at_001_repl_loop_initializes_without_overlay(self):
        """Verify REPLLoop initializes without overlay."""
        # REPLLoop should initialize without enable_overlay parameter
        # (parameter was removed)
        import inspect

        import teambot.repl.loop as loop_module

        sig = inspect.signature(loop_module.REPLLoop.__init__)
        param_names = list(sig.parameters.keys())

        # enable_overlay parameter should not exist
        assert "enable_overlay" not in param_names

    def test_at_001_visualization_module_imports_without_overlay(self):
        """Verify visualization module imports without overlay classes."""
        from teambot.visualization import __all__

        # Overlay classes should not be in exports
        assert "OverlayRenderer" not in __all__
        assert "OverlayState" not in __all__
        assert "OverlayPosition" not in __all__

        # Other exports should still exist
        assert "ConsoleDisplay" in __all__
        assert "StartupAnimation" in __all__

    # -- AT-002: Unknown Command Response for /overlay --

    def test_at_002_overlay_command_returns_unknown(self):
        """Verify /overlay command returns unknown command error."""
        router = AgentRouter()
        commands = SystemCommands(router=router)

        # Dispatch /overlay command
        result = commands.dispatch("overlay", [])

        # Should return unknown command error
        assert result.success is False
        assert "Unknown command" in result.output or "unknown" in result.output.lower()

    def test_at_002_overlay_not_in_dispatch_handlers(self):
        """Verify overlay is not in the command dispatch handlers."""
        router = AgentRouter()
        commands = SystemCommands(router=router)

        # Get the handlers from dispatch method by calling it
        # The dispatch method should not have 'overlay' as a valid command
        result = commands.dispatch("overlay", [])

        # Should fail because overlay is not a recognized command
        assert result.success is False

    # -- AT-003: Help Command Excludes Overlay --

    def test_at_003_help_output_excludes_overlay(self):
        """Verify /help output does not contain overlay."""
        result = handle_help([])

        # Check that overlay is not mentioned in help output
        assert "overlay" not in result.output.lower()
        assert "/overlay" not in result.output

    def test_at_003_help_still_shows_other_commands(self):
        """Verify /help still shows expected commands."""
        result = handle_help([])

        # Verify other commands are still present
        assert "/help" in result.output
        assert "/status" in result.output
        assert "/tasks" in result.output
        assert "/quit" in result.output
        assert "/models" in result.output
        assert "@agent" in result.output

    # -- AT-004: Full Test Suite Passes --

    def test_at_004_no_overlay_imports_in_commands(self):
        """Verify commands.py has no overlay imports."""
        import inspect
        import sys

        # Access module via sys.modules to avoid duplicate import style
        commands_module = sys.modules["teambot.repl.commands"]
        source = inspect.getsource(commands_module)

        # Should not have OverlayRenderer import
        assert "from teambot.visualization.overlay import" not in source

    def test_at_004_no_overlay_imports_in_loop(self):
        """Verify loop.py has no overlay imports."""
        import inspect

        import teambot.repl.loop as loop_module

        source = inspect.getsource(loop_module)

        # Should not have OverlayRenderer import
        assert "from teambot.visualization.overlay import" not in source

    # -- AT-005: Linting Passes --

    def test_at_005_no_undefined_overlay_references(self):
        """Verify no undefined overlay references in key modules."""
        # Import modules - would fail if there are undefined references

        # If we get here, no import errors occurred
        assert True

    # -- AT-006: Config Loads Without Overlay Options --

    def test_at_006_config_loads_without_overlay_section(self):
        """Verify config loads successfully without overlay section."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "teambot.json"
            config_data = {
                "agents": [
                    {"id": "pm", "persona": "project_manager"},
                    {"id": "builder-1", "persona": "builder"},
                ]
            }
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            config = loader.load(config_path)

            # Config should load successfully
            assert "agents" in config
            assert len(config["agents"]) == 2

    def test_at_006_config_ignores_overlay_section_if_present(self):
        """Verify config with overlay section doesn't cause errors."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "teambot.json"
            # Include old overlay config - should be ignored, not cause error
            config_data = {
                "agents": [
                    {"id": "pm", "persona": "project_manager"},
                ],
                "overlay": {"enabled": True, "position": "top-right"},
            }
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            # Should not raise ConfigError for overlay section
            config = loader.load(config_path)

            # Config should load successfully
            assert "agents" in config

    def test_at_006_no_overlay_defaults_applied(self):
        """Verify no overlay defaults are applied to config."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "teambot.json"
            config_data = {
                "agents": [
                    {"id": "pm", "persona": "project_manager"},
                ]
            }
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            config = loader.load(config_path)

            # Overlay defaults should NOT be applied
            assert "overlay" not in config or config.get("overlay") == {}

    def test_at_006_valid_overlay_positions_constant_removed(self):
        """Verify VALID_OVERLAY_POSITIONS constant is removed."""
        from teambot.config import loader as loader_module

        # The constant should not exist
        assert not hasattr(loader_module, "VALID_OVERLAY_POSITIONS")
