"""Tests for window manager - Code-First approach."""

from unittest.mock import MagicMock, patch

import pytest


class TestWindowManager:
    """Tests for WindowManager class."""

    def test_create_manager(self):
        """Manager initializes with system detection."""
        from teambot.window_manager import WindowManager

        manager = WindowManager()

        assert manager.system in ["Windows", "Darwin", "Linux"]
        assert manager._processes == {}

    def test_detect_linux_terminal_caches(self):
        """Linux terminal detection result is cached."""
        from teambot.window_manager import WindowManager

        manager = WindowManager()
        manager._linux_terminal = ("xterm", "-e")

        # Should return cached value
        result = manager._detect_linux_terminal()

        assert result == ("xterm", "-e")

    @patch("shutil.which")
    def test_detect_linux_terminal_finds_gnome(self, mock_which):
        """Detects gnome-terminal when available."""
        from teambot.window_manager import WindowManager

        def which_gnome(x):
            return "/usr/bin/gnome-terminal" if x == "gnome-terminal" else None

        mock_which.side_effect = which_gnome

        manager = WindowManager()
        manager._linux_terminal = None  # Reset cache

        result = manager._detect_linux_terminal()

        assert result == ("gnome-terminal", "--")

    @patch("shutil.which")
    def test_detect_linux_terminal_fallback(self, mock_which):
        """Falls back to xterm when preferred terminals unavailable."""
        from teambot.window_manager import WindowManager

        def which_side_effect(name):
            return "/usr/bin/xterm" if name == "xterm" else None

        mock_which.side_effect = which_side_effect

        manager = WindowManager()
        manager._linux_terminal = None  # Reset cache

        result = manager._detect_linux_terminal()

        assert result == ("xterm", "-e")

    def test_get_process_unknown_agent(self):
        """Getting process for unknown agent returns None."""
        from teambot.window_manager import WindowManager

        manager = WindowManager()

        process = manager.get_process("unknown-agent")

        assert process is None

    def test_is_running_unknown_agent(self):
        """Checking if unknown agent is running returns False."""
        from teambot.window_manager import WindowManager

        manager = WindowManager()

        assert not manager.is_running("unknown-agent")

    def test_is_running_with_active_process(self):
        """Returns True when process is active."""
        from teambot.window_manager import WindowManager

        manager = WindowManager()
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Still running
        manager._processes["agent-1"] = mock_process

        assert manager.is_running("agent-1")

    def test_is_running_with_finished_process(self):
        """Returns False when process has finished."""
        from teambot.window_manager import WindowManager

        manager = WindowManager()
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Finished with exit code 0
        manager._processes["agent-1"] = mock_process

        assert not manager.is_running("agent-1")

    def test_terminate_removes_process(self):
        """Terminate removes process from tracking."""
        from teambot.window_manager import WindowManager

        manager = WindowManager()
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        manager._processes["agent-1"] = mock_process

        manager.terminate("agent-1")

        assert "agent-1" not in manager._processes
        mock_process.terminate.assert_called_once()

    def test_terminate_all_clears_all(self):
        """Terminate all clears all processes."""
        from teambot.window_manager import WindowManager

        manager = WindowManager()
        for i in range(3):
            mock_process = MagicMock()
            mock_process.poll.return_value = None
            manager._processes[f"agent-{i}"] = mock_process

        manager.terminate_all()

        assert len(manager._processes) == 0

    def test_get_active_agents(self):
        """Get list of agents with active processes."""
        from teambot.window_manager import WindowManager

        manager = WindowManager()

        # Add active process
        active_process = MagicMock()
        active_process.poll.return_value = None
        manager._processes["active"] = active_process

        # Add finished process
        finished_process = MagicMock()
        finished_process.poll.return_value = 0
        manager._processes["finished"] = finished_process

        active = manager.get_active_agents()

        assert "active" in active
        assert "finished" not in active


class TestWindowSpawning:
    """Tests for actual window spawning (mocked)."""

    @patch("teambot.window_manager.subprocess.Popen")
    def test_spawn_window_windows(self, mock_popen):
        """Spawn window on Windows uses CREATE_NEW_CONSOLE."""
        import teambot.window_manager as wm
        from teambot.window_manager import WindowManager

        # Mock CREATE_NEW_CONSOLE for non-Windows platforms
        if not hasattr(wm.subprocess, "CREATE_NEW_CONSOLE"):
            wm.subprocess.CREATE_NEW_CONSOLE = 0x00000010

        manager = WindowManager()
        manager.system = "Windows"

        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        result = manager.spawn_window("agent-1", "script.py", args=["--arg1"], title="Test")

        assert result == mock_process
        assert "agent-1" in manager._processes

    @patch("subprocess.Popen")
    def test_spawn_window_macos(self, mock_popen):
        """Spawn window on macOS uses osascript."""
        from teambot.window_manager import WindowManager

        manager = WindowManager()
        manager.system = "Darwin"

        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        result = manager.spawn_window("agent-1", "script.py")

        assert result == mock_process
        # Verify osascript was used
        call_args = mock_popen.call_args[0][0]
        assert call_args[0] == "osascript"

    @patch("subprocess.Popen")
    @patch("shutil.which")
    def test_spawn_window_linux_gnome(self, mock_which, mock_popen):
        """Spawn window on Linux uses detected terminal."""
        from teambot.window_manager import WindowManager

        mock_which.return_value = "/usr/bin/gnome-terminal"

        manager = WindowManager()
        manager.system = "Linux"
        manager._linux_terminal = None

        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        result = manager.spawn_window("agent-1", "script.py")

        assert result == mock_process
        call_args = mock_popen.call_args[0][0]
        assert "gnome-terminal" in call_args

    @patch("shutil.which")
    def test_spawn_window_linux_no_terminal_raises(self, mock_which):
        """Spawn on Linux without terminal raises error."""
        from teambot.window_manager import WindowManager, WindowSpawnError

        mock_which.return_value = None

        manager = WindowManager()
        manager.system = "Linux"
        manager._linux_terminal = None

        with pytest.raises(WindowSpawnError):
            manager.spawn_window("agent-1", "script.py")
