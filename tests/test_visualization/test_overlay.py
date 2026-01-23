"""Tests for persistent status overlay."""

import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from teambot.visualization.overlay import (
    OVERLAY_HEIGHT,
    OVERLAY_WIDTH,
    SPINNER_FRAMES,
    OverlayPosition,
    OverlayRenderer,
    OverlayState,
)


class TestOverlayState:
    """Tests for OverlayState dataclass."""

    def test_default_state(self):
        """Test default state values."""
        state = OverlayState()
        assert state.enabled is True
        assert state.position == OverlayPosition.TOP_RIGHT
        assert state.active_agents == []
        assert state.running_count == 0
        assert state.pending_count == 0
        assert state.completed_count == 0
        assert state.failed_count == 0
        assert state.spinner_frame == 0

    def test_is_idle_when_no_tasks(self):
        """Test is_idle returns True when no running tasks."""
        state = OverlayState()
        assert state.is_idle() is True

    def test_is_idle_false_when_running(self):
        """Test is_idle returns False when tasks running."""
        state = OverlayState(running_count=1)
        assert state.is_idle() is False

    def test_is_idle_false_when_active_agents(self):
        """Test is_idle returns False when agents active."""
        state = OverlayState(active_agents=["pm"])
        assert state.is_idle() is False

    def test_total_tasks(self):
        """Test total_tasks calculation."""
        state = OverlayState(
            running_count=2,
            pending_count=3,
            completed_count=5,
            failed_count=1,
        )
        assert state.total_tasks() == 11


class TestOverlayPosition:
    """Tests for OverlayPosition enum."""

    def test_all_positions(self):
        """Test all position values exist."""
        assert OverlayPosition.TOP_RIGHT.value == "top-right"
        assert OverlayPosition.TOP_LEFT.value == "top-left"
        assert OverlayPosition.BOTTOM_RIGHT.value == "bottom-right"
        assert OverlayPosition.BOTTOM_LEFT.value == "bottom-left"


class TestOverlayRendererInit:
    """Tests for OverlayRenderer initialization."""

    def test_default_init(self):
        """Test default initialization."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer()
            assert renderer.is_enabled is True
            assert renderer.state.position == OverlayPosition.TOP_RIGHT

    def test_init_with_position(self):
        """Test initialization with custom position."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer(position=OverlayPosition.BOTTOM_LEFT)
            assert renderer.state.position == OverlayPosition.BOTTOM_LEFT

    def test_init_disabled(self):
        """Test initialization with disabled state."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer(enabled=False)
            assert renderer.state.enabled is False


class TestTerminalSupport:
    """Tests for terminal capability detection."""

    def test_not_tty(self):
        """Test non-TTY terminal is not supported."""
        with patch("sys.stdout.isatty", return_value=False):
            renderer = OverlayRenderer()
            assert renderer.is_supported is False

    def test_small_terminal(self):
        """Test small terminal is not supported."""
        with patch("sys.stdout.isatty", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(20, 5)):
                renderer = OverlayRenderer()
                assert renderer.is_supported is False

    def test_dumb_terminal(self):
        """Test dumb terminal is not supported."""
        with patch("sys.stdout.isatty", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch.dict(os.environ, {"TERM": "dumb"}):
                    renderer = OverlayRenderer()
                    assert renderer.is_supported is False

    def test_supported_terminal(self):
        """Test normal terminal is supported."""
        with patch("sys.stdout.isatty", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch.dict(os.environ, {"TERM": "xterm-256color"}):
                    renderer = OverlayRenderer()
                    assert renderer.is_supported is True


class TestPositionCalculation:
    """Tests for overlay position calculation."""

    @patch("shutil.get_terminal_size", return_value=(80, 24))
    def test_top_right_position(self, mock_size):
        """Test top-right position calculation."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer(position=OverlayPosition.TOP_RIGHT)
            row, col = renderer._calculate_position()
            assert row == 1
            assert col == 80 - OVERLAY_WIDTH

    @patch("shutil.get_terminal_size", return_value=(80, 24))
    def test_top_left_position(self, mock_size):
        """Test top-left position calculation."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer(position=OverlayPosition.TOP_LEFT)
            row, col = renderer._calculate_position()
            assert row == 1
            assert col == 1

    @patch("shutil.get_terminal_size", return_value=(80, 24))
    def test_bottom_right_position(self, mock_size):
        """Test bottom-right position calculation."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer(position=OverlayPosition.BOTTOM_RIGHT)
            row, col = renderer._calculate_position()
            assert row == 24 - OVERLAY_HEIGHT - 1
            assert col == 80 - OVERLAY_WIDTH

    @patch("shutil.get_terminal_size", return_value=(80, 24))
    def test_bottom_left_position(self, mock_size):
        """Test bottom-left position calculation."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer(position=OverlayPosition.BOTTOM_LEFT)
            row, col = renderer._calculate_position()
            assert row == 24 - OVERLAY_HEIGHT - 1
            assert col == 1


class TestContentBuilding:
    """Tests for overlay content building."""

    def test_idle_content(self):
        """Test content when idle."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer()
            lines = renderer._build_content()
            assert "✓ Idle" in lines[0]
            assert "Tasks:" in lines[1]

    def test_active_content(self):
        """Test content when agents active."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer()
            renderer._state.active_agents = ["pm", "ba"]
            renderer._state.running_count = 2
            lines = renderer._build_content()
            assert "@pm" in lines[0]
            assert "@ba" in lines[0]
            # Should have spinner character
            assert any(c in lines[0] for c in SPINNER_FRAMES)

    def test_task_counts_content(self):
        """Test task counts in content."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer()
            renderer._state.running_count = 2
            renderer._state.pending_count = 1
            renderer._state.completed_count = 5
            lines = renderer._build_content()
            assert "2⏳" in lines[1]
            assert "1⏸" in lines[1]
            assert "5✓" in lines[1]

    def test_failed_count_shown(self):
        """Test failed count appears when non-zero."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer()
            renderer._state.failed_count = 2
            lines = renderer._build_content()
            assert "2✗" in lines[1]

    def test_many_agents_truncated(self):
        """Test many agents are truncated."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer()
            renderer._state.active_agents = ["pm", "ba", "writer", "builder-1", "builder-2"]
            renderer._state.running_count = 5
            lines = renderer._build_content()
            # Shows overflow indicator
            assert "+2" in lines[0] or "+" in lines[0]


class TestRenderAndClear:
    """Tests for render and clear operations."""

    def test_render_writes_to_stdout(self):
        """Test render writes ANSI sequences to stdout."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write") as mock_write:
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer()
                        renderer.render()
                        mock_write.assert_called()
                        output = mock_write.call_args[0][0]
                        # Should contain box characters
                        assert "┌" in output
                        assert "└" in output

    def test_render_disabled_does_nothing(self):
        """Test render does nothing when disabled."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("sys.stdout.write") as mock_write:
                renderer = OverlayRenderer(enabled=False)
                renderer.render()
                mock_write.assert_not_called()

    def test_clear_writes_spaces(self):
        """Test clear writes spaces to overlay area."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write") as mock_write:
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer()
                        renderer.clear()
                        mock_write.assert_called()


class TestEnableDisable:
    """Tests for enable/disable functionality."""

    def test_enable(self):
        """Test enabling overlay."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer(enabled=False)
                        renderer.enable()
                        assert renderer.state.enabled is True

    def test_disable(self):
        """Test disabling overlay."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer(enabled=True)
                        renderer.disable()
                        assert renderer.state.enabled is False


class TestSetPosition:
    """Tests for position setting."""

    def test_set_position(self):
        """Test setting overlay position."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer()
                        renderer.set_position(OverlayPosition.BOTTOM_LEFT)
                        assert renderer.state.position == OverlayPosition.BOTTOM_LEFT


class TestUpdateState:
    """Tests for state updates."""

    def test_update_active_agents(self):
        """Test updating active agents."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer()
                        renderer.update_state(active_agents=["pm", "ba"])
                        assert renderer.state.active_agents == ["pm", "ba"]

    def test_update_counts(self):
        """Test updating task counts."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer()
                        renderer.update_state(
                            running_count=2,
                            pending_count=3,
                            completed_count=5,
                        )
                        assert renderer.state.running_count == 2
                        assert renderer.state.pending_count == 3
                        assert renderer.state.completed_count == 5


class TestSpinner:
    """Tests for spinner animation."""

    def test_advance_spinner(self):
        """Test spinner frame advances."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer()
                        renderer._state.active_agents = ["pm"]
                        renderer._state.running_count = 1
                        initial_frame = renderer.state.spinner_frame
                        renderer.advance_spinner()
                        assert renderer.state.spinner_frame == initial_frame + 1

    def test_spinner_wraps(self):
        """Test spinner frame wraps around."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer()
            renderer._state.spinner_frame = len(SPINNER_FRAMES) - 1
            renderer._state.active_agents = ["pm"]
            renderer._state.running_count = 1
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        renderer.advance_spinner()
            assert renderer.state.spinner_frame == 0

    @pytest.mark.asyncio
    async def test_start_spinner(self):
        """Test starting spinner timer."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer()
            renderer._state.active_agents = ["pm"]
            renderer._state.running_count = 1

            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        await renderer.start_spinner()
                        assert renderer._spinner_task is not None

                        # Let it run briefly
                        await asyncio.sleep(0.15)
                        assert renderer.state.spinner_frame > 0

                        await renderer.stop_spinner()
                        assert renderer._spinner_task is None

    @pytest.mark.asyncio
    async def test_stop_spinner_cleanup(self):
        """Test spinner cleanup on stop."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer()
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        await renderer.start_spinner()
                        await renderer.stop_spinner()
                        assert renderer._spinner_task is None


class TestEventHandlers:
    """Tests for task event handlers."""

    def test_on_task_started(self):
        """Test handling task started event."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer()
                        renderer._state.pending_count = 1

                        task = MagicMock()
                        task.agent_id = "pm"

                        renderer.on_task_started(task)

                        assert "pm" in renderer.state.active_agents
                        assert renderer.state.running_count == 1
                        assert renderer.state.pending_count == 0

    def test_on_task_completed_success(self):
        """Test handling task completed successfully."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer()
                        renderer._state.active_agents = ["pm"]
                        renderer._state.running_count = 1

                        task = MagicMock()
                        task.agent_id = "pm"
                        result = MagicMock()
                        result.success = True

                        renderer.on_task_completed(task, result)

                        assert "pm" not in renderer.state.active_agents
                        assert renderer.state.running_count == 0
                        assert renderer.state.completed_count == 1

    def test_on_task_completed_failure(self):
        """Test handling task failed."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer()
                        renderer._state.active_agents = ["pm"]
                        renderer._state.running_count = 1

                        task = MagicMock()
                        task.agent_id = "pm"
                        result = MagicMock()
                        result.success = False

                        renderer.on_task_completed(task, result)

                        assert renderer.state.failed_count == 1
                        assert renderer.state.completed_count == 0

    def test_on_task_pending(self):
        """Test handling task added to queue."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                with patch("sys.stdout.write"):
                    with patch("sys.stdout.flush"):
                        renderer = OverlayRenderer()

                        task = MagicMock()
                        task.agent_id = "pm"

                        renderer.on_task_pending(task)

                        assert renderer.state.pending_count == 1


class TestPrintWithOverlay:
    """Tests for print_with_overlay."""

    def test_print_clears_and_redraws(self):
        """Test print clears then redraws overlay."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            with patch("shutil.get_terminal_size", return_value=(80, 24)):
                console = MagicMock()
                renderer = OverlayRenderer(console=console)

                with patch.object(renderer, "clear") as mock_clear:
                    with patch.object(renderer, "render") as mock_render:
                        renderer.print_with_overlay("Hello")

                        mock_clear.assert_called_once()
                        console.print.assert_called_once_with("Hello")
                        mock_render.assert_called_once()
