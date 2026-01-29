"""Tests for TeamBotApp main application."""

from unittest.mock import MagicMock

import pytest


class TestTeamBotApp:
    """Tests for TeamBotApp main application."""

    @pytest.mark.asyncio
    async def test_app_displays_both_panes(self):
        """App shows input and output panes."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test():
            assert app.query_one("#input-pane") is not None
            assert app.query_one("#output") is not None
            assert app.query_one("#prompt") is not None

    @pytest.mark.asyncio
    async def test_input_echoed_to_output(self):
        """Submitted input appears in output pane."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            await pilot.click("#prompt")
            await pilot.press("@", "p", "m", " ", "t", "e", "s", "t")
            await pilot.press("enter")
            await pilot.pause()

            output = app.query_one("#output")
            # Check output contains the command (at least one line)
            assert len(output.lines) > 0

    @pytest.mark.asyncio
    async def test_input_cleared_after_submit(self):
        """Input field cleared after submission."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            await pilot.click("#prompt")
            await pilot.press("@", "p", "m", " ", "t", "e", "s", "t")
            await pilot.press("enter")
            await pilot.pause()

            input_pane = app.query_one("#prompt")
            assert input_pane.value == ""

    @pytest.mark.asyncio
    async def test_raw_input_shows_tip(self):
        """Raw input (not @agent or /command) shows tip message."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            await pilot.click("#prompt")
            await pilot.press("h", "e", "l", "l", "o")
            await pilot.press("enter")
            await pilot.pause()

            output = app.query_one("#output")
            # Should have output lines
            assert len(output.lines) >= 1

    @pytest.mark.asyncio
    async def test_app_with_executor(self):
        """App accepts executor parameter."""
        from teambot.ui.app import TeamBotApp

        mock_executor = MagicMock()

        app = TeamBotApp(executor=mock_executor)
        async with app.run_test():
            # App should have executor
            assert app._executor is mock_executor

    @pytest.mark.asyncio
    async def test_header_displays_teambot(self):
        """Header shows TeamBot branding."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test():
            header = app.query_one("#header")
            assert header is not None


class TestStatusPanelIntegration:
    """Integration tests for StatusPanel in TeamBotApp."""

    @pytest.mark.asyncio
    async def test_status_panel_present_in_app(self):
        """App includes status panel widget."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test():
            panel = app.query_one("#status-panel")
            assert panel is not None

    @pytest.mark.asyncio
    async def test_status_panel_between_header_and_prompt(self):
        """Status panel is positioned between header and input."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test():
            input_pane = app.query_one("#input-pane")
            children = list(input_pane.children)

            # Should have header, status-panel, prompt
            ids = [c.id for c in children if c.id]
            assert "header" in ids
            assert "status-panel" in ids
            assert "prompt" in ids

    @pytest.mark.asyncio
    async def test_app_has_agent_status_manager(self):
        """App has AgentStatusManager instance."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test():
            assert hasattr(app, "_agent_status")
            assert app._agent_status is not None

    @pytest.mark.asyncio
    async def test_status_panel_shows_all_agents(self):
        """Status panel displays all 6 agents."""
        from teambot.ui.app import TeamBotApp
        from teambot.ui.widgets.status_panel import StatusPanel

        app = TeamBotApp()
        async with app.run_test():
            panel = app.query_one("#status-panel", StatusPanel)
            content = panel._format_status()

            for agent in ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]:
                assert agent in content
