"""Tests for /overlay command."""

from unittest.mock import MagicMock

from teambot.repl.commands import SystemCommands, handle_overlay
from teambot.visualization.overlay import OverlayPosition


class TestHandleOverlay:
    """Tests for /overlay command handler."""

    def test_no_overlay(self):
        """Test error when no overlay."""
        result = handle_overlay([], None)
        assert not result.success
        assert "not available" in result.output

    def test_unsupported_terminal(self):
        """Test error when terminal unsupported."""
        overlay = MagicMock()
        overlay.is_supported = False

        result = handle_overlay([], overlay)
        assert not result.success
        assert "not supported" in result.output

    def test_status_no_args(self):
        """Test showing overlay status."""
        overlay = MagicMock()
        overlay.is_supported = True
        overlay.is_enabled = True
        overlay.state.position = OverlayPosition.TOP_RIGHT

        result = handle_overlay([], overlay)
        assert result.success
        assert "enabled" in result.output
        assert "top-right" in result.output

    def test_overlay_on(self):
        """Test enabling overlay."""
        overlay = MagicMock()
        overlay.is_supported = True

        result = handle_overlay(["on"], overlay)
        assert result.success
        assert "enabled" in result.output
        overlay.enable.assert_called_once()

    def test_overlay_off(self):
        """Test disabling overlay."""
        overlay = MagicMock()
        overlay.is_supported = True

        result = handle_overlay(["off"], overlay)
        assert result.success
        assert "disabled" in result.output
        overlay.disable.assert_called_once()

    def test_overlay_position_no_arg(self):
        """Test position command without argument."""
        overlay = MagicMock()
        overlay.is_supported = True

        result = handle_overlay(["position"], overlay)
        assert not result.success
        assert "Usage" in result.output

    def test_overlay_position_valid(self):
        """Test setting valid position."""
        overlay = MagicMock()
        overlay.is_supported = True

        result = handle_overlay(["position", "bottom-left"], overlay)
        assert result.success
        assert "bottom-left" in result.output
        overlay.set_position.assert_called_once_with(OverlayPosition.BOTTOM_LEFT)

    def test_overlay_position_invalid(self):
        """Test setting invalid position."""
        overlay = MagicMock()
        overlay.is_supported = True

        result = handle_overlay(["position", "middle"], overlay)
        assert not result.success
        assert "Invalid position" in result.output

    def test_unknown_subcommand(self):
        """Test unknown subcommand."""
        overlay = MagicMock()
        overlay.is_supported = True

        result = handle_overlay(["foobar"], overlay)
        assert not result.success
        assert "Unknown" in result.output


class TestSystemCommandsOverlay:
    """Tests for SystemCommands overlay integration."""

    def test_set_overlay(self):
        """Test setting overlay renderer."""
        cmds = SystemCommands()
        overlay = MagicMock()

        cmds.set_overlay(overlay)
        assert cmds._overlay == overlay

    def test_dispatch_overlay(self):
        """Test dispatching /overlay command."""
        overlay = MagicMock()
        overlay.is_supported = True
        overlay.is_enabled = True
        overlay.state.position = OverlayPosition.TOP_RIGHT

        cmds = SystemCommands(overlay=overlay)
        result = cmds.dispatch("overlay", [])

        assert result.success
        assert "enabled" in result.output

    def test_dispatch_overlay_on(self):
        """Test dispatching /overlay on."""
        overlay = MagicMock()
        overlay.is_supported = True

        cmds = SystemCommands(overlay=overlay)
        result = cmds.dispatch("overlay", ["on"])

        assert result.success
        overlay.enable.assert_called_once()

    def test_dispatch_overlay_position(self):
        """Test dispatching /overlay position."""
        overlay = MagicMock()
        overlay.is_supported = True

        cmds = SystemCommands(overlay=overlay)
        result = cmds.dispatch("overlay", ["position", "top-left"])

        assert result.success
        overlay.set_position.assert_called_once_with(OverlayPosition.TOP_LEFT)
