"""Tests for StatusPanel widget."""

import subprocess
from unittest.mock import MagicMock, patch

from teambot.ui.agent_state import AgentStatusManager


class TestStatusPanel:
    """Tests for StatusPanel widget."""

    def test_renders_all_agents(self):
        """Panel renders all 7 default agents including notify."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        content = panel._format_status()

        for agent in ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer", "notify"]:
            assert agent in content

    def test_shows_idle_indicator_for_idle_agents(self):
        """Idle agents show dim indicator."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "[dim]●[/dim]" in content

    def test_shows_running_indicator(self):
        """Running agents show yellow indicator."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_running("pm", "test task")
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "[yellow]●[/yellow]" in content

    def test_shows_streaming_indicator(self):
        """Streaming agents show cyan indicator."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_running("pm", "task")
        manager.set_streaming("pm")
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "[cyan]◉[/cyan]" in content

    def test_shows_completed_indicator(self):
        """Completed agents show green checkmark."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_completed("pm")
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "[green]✓[/green]" in content

    def test_shows_failed_indicator(self):
        """Failed agents show red X."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_failed("pm")
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "[red]✗[/red]" in content

    def test_shows_task_for_running_agents(self):
        """Running agents display their task indented."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_running("pm", "implement auth")
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "implement auth" in content
        assert "→" in content  # Task indicator

    def test_shows_task_for_streaming_agents(self):
        """Streaming agents display their task indented."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_running("pm", "implement auth")
        manager.set_streaming("pm")
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "implement auth" in content

    def test_truncates_long_task(self):
        """Long tasks are truncated with ellipsis."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        # Task is truncated to 40 chars by manager, then to 20 by panel
        manager.set_running("pm", "this is a very long task description")
        panel = StatusPanel(manager)

        content = panel._format_status()
        # Should be truncated
        assert "..." in content

    def test_listener_registered_on_mount(self):
        """Panel registers listener with manager on mount."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        # Simulate mount
        with patch.object(panel, "set_interval", return_value=MagicMock()):
            with patch.object(panel, "update"):
                panel.on_mount()

        # Listener should be registered
        assert panel._on_status_change in manager._listeners

    def test_listener_removed_on_unmount(self):
        """Panel removes listener on unmount."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        # Simulate mount then unmount
        with patch.object(panel, "set_interval", return_value=MagicMock()):
            with patch.object(panel, "update"):
                panel.on_mount()
                panel.on_unmount()

        # Listener should be removed
        assert panel._on_status_change not in manager._listeners

    def test_update_called_on_status_change(self):
        """Panel updates when status changes."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        # Manually register listener (simulating mount)
        manager.add_listener(panel._on_status_change)

        with patch.object(panel, "update") as mock_update:
            manager.set_running("pm", "task")
            mock_update.assert_called()


class TestStatusPanelGitBranch:
    """Tests for Git branch display."""

    def test_get_git_branch_success(self):
        """Returns branch name when in git repo."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="main\n")
            branch = panel._get_git_branch()
            assert branch == "main"

    def test_get_git_branch_not_in_repo(self):
        """Returns empty string when not in git repo."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=128, stdout="")
            branch = panel._get_git_branch()
            assert branch == ""

    def test_get_git_branch_timeout(self):
        """Returns empty string on timeout."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 2)
            branch = panel._get_git_branch()
            assert branch == ""

    def test_get_git_branch_git_not_installed(self):
        """Returns empty string when git is not installed."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            branch = panel._get_git_branch()
            assert branch == ""

    def test_git_branch_displayed_in_status(self):
        """Git branch is displayed at top of status panel."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)
        panel._git_branch = "feature/test"

        content = panel._format_status()
        assert "feature/test" in content

    def test_git_branch_truncated_if_long(self):
        """Long git branch names are truncated."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)
        panel._git_branch = "feature/very-long-branch-name-here"

        content = panel._format_status()
        # Should be truncated to ~15 chars
        assert "..." in content
        assert "feature/very-long-branch-name-here" not in content

    def test_no_git_branch_when_empty(self):
        """No branch line when not in git repo."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)
        panel._git_branch = ""

        content = panel._format_status()
        # Should start with agent status, not empty branch
        lines = content.split("\n")
        assert lines[0] != ""
        assert "(" not in lines[0]  # No branch parentheses


class TestStatusPanelDefaultIndicator:
    """Tests for default agent indicator in status panel."""

    def test_default_agent_shows_indicator(self):
        """Default agent shows ★ indicator."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_default_agent("pm")
        panel = StatusPanel(manager)

        content = panel._format_status()
        # pm line should have star indicator
        assert "★" in content

    def test_default_agent_shows_default_label(self):
        """Idle default agent shows 'default' label instead of 'idle'."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_default_agent("pm")
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "default" in content

    def test_non_default_agent_shows_idle(self):
        """Non-default idle agents show 'idle' label."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_default_agent("pm")
        panel = StatusPanel(manager)

        content = panel._format_status()
        # Other agents should still show idle
        assert "[dim]idle[/dim]" in content

    def test_indicator_moves_when_default_changes(self):
        """Indicator moves to new default agent."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_default_agent("pm")
        panel = StatusPanel(manager)

        # Change default to builder-1
        manager.set_default_agent("builder-1")
        content = panel._format_status()

        # Find line with builder-1 — should have star
        lines = content.split("\n")
        builder_line = [line for line in lines if "builder-1" in line][0]
        assert "★" in builder_line


class TestStatusPanelNotifyAgent:
    """Tests for @notify pseudo-agent in status panel."""

    def test_notify_agent_included_in_status(self):
        """Panel renders notify pseudo-agent."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "notify" in content

    def test_notify_agent_shows_na_model(self):
        """Notify agent displays (n/a) instead of model name."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        content = panel._format_status()
        # Find the notify line
        lines = content.split("\n")
        notify_lines = [line for line in lines if "notify" in line]
        assert len(notify_lines) >= 1
        notify_line = notify_lines[0]
        assert "(n/a)" in notify_line

    def test_all_seven_agents_rendered(self):
        """Panel renders all 7 agents including notify."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        content = panel._format_status()
        expected_agents = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer", "notify"]
        for agent in expected_agents:
            assert agent in content
