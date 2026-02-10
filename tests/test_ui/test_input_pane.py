"""Tests for InputPane widget."""

import pytest


class TestInputPane:
    """Tests for InputPane widget."""

    @pytest.mark.asyncio
    async def test_history_navigation_up(self):
        """Up arrow shows previous command."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")

            # Submit some commands to build history
            await pilot.click("#prompt")
            await pilot.press("f", "i", "r", "s", "t")
            await pilot.press("enter")
            await pilot.pause()

            await pilot.click("#prompt")
            await pilot.press("s", "e", "c", "o", "n", "d")
            await pilot.press("enter")
            await pilot.pause()

            # Press up arrow to get previous command
            await pilot.click("#prompt")
            await pilot.press("up")
            await pilot.pause()

            assert input_pane.text == "second"

    @pytest.mark.asyncio
    async def test_history_navigation_down(self):
        """Down arrow shows next command after up."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")

            # Submit commands
            await pilot.click("#prompt")
            await pilot.press("f", "i", "r", "s", "t")
            await pilot.press("enter")
            await pilot.pause()

            await pilot.click("#prompt")
            await pilot.press("s", "e", "c", "o", "n", "d")
            await pilot.press("enter")
            await pilot.pause()

            # Navigate up twice then down once
            await pilot.click("#prompt")
            await pilot.press("up", "up", "down")
            await pilot.pause()

            assert input_pane.text == "second"

    @pytest.mark.asyncio
    async def test_empty_history_no_crash(self):
        """Up arrow with empty history doesn't crash."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")

            # Press up with empty history
            await pilot.click("#prompt")
            await pilot.press("up")
            await pilot.pause()

            # Should not crash, value should be empty
            assert input_pane.text == ""

    @pytest.mark.asyncio
    async def test_history_preserves_current_input(self):
        """Navigating history preserves current unsaved input."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")

            # Submit a command
            await pilot.click("#prompt")
            await pilot.press("h", "i", "s", "t", "o", "r", "y")
            await pilot.press("enter")
            await pilot.pause()

            # Type something new
            await pilot.click("#prompt")
            await pilot.press("n", "e", "w")
            await pilot.pause()

            # Navigate up then down to return to current
            await pilot.press("up", "down")
            await pilot.pause()

            # Should have preserved "new"
            assert input_pane.text == "new"


class TestMultiLineInput:
    """Tests for multi-line input behavior."""

    @pytest.mark.asyncio
    async def test_submitted_message_has_value(self):
        """Submitted message has .value attribute with text content."""
        from teambot.ui.widgets.input_pane import InputPane

        msg = InputPane.Submitted(input=None, value="hello")
        assert msg.value == "hello"

    @pytest.mark.asyncio
    async def test_submitted_message_has_input_ref(self):
        """Submitted message has .input attribute referencing widget."""
        from teambot.ui.widgets.input_pane import InputPane

        sentinel = object()
        msg = InputPane.Submitted(input=sentinel, value="x")
        assert msg.input is sentinel

    @pytest.mark.asyncio
    async def test_enter_submits_text(self):
        """Enter key submits text and echoes to output."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            output = app.query_one("#output")
            await pilot.click("#prompt")
            await pilot.press("h", "e", "l", "l", "o")
            await pilot.press("enter")
            await pilot.pause()

            # Command should appear in output (echoed by handle_input)
            assert len(output.lines) > 0

    @pytest.mark.asyncio
    async def test_enter_clears_input(self):
        """Input is cleared after Enter submission."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")
            await pilot.click("#prompt")
            await pilot.press("h", "i")
            await pilot.press("enter")
            await pilot.pause()
            assert input_pane.text == ""

    @pytest.mark.asyncio
    async def test_enter_on_empty_does_not_submit(self):
        """Enter on empty input does not produce output."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            output = app.query_one("#output")
            initial_lines = len(output.lines)
            await pilot.click("#prompt")
            await pilot.press("enter")
            await pilot.pause()
            assert len(output.lines) == initial_lines

    @pytest.mark.asyncio
    async def test_ctrl_enter_inserts_newline(self):
        """Ctrl+Enter inserts newline without submitting."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")
            output = app.query_one("#output")
            initial_lines = len(output.lines)

            await pilot.click("#prompt")
            await pilot.press("l", "i", "n", "e", "1")
            await pilot.press("ctrl+enter")
            await pilot.press("l", "i", "n", "e", "2")
            await pilot.pause()

            # Should have newline in text, not submitted
            assert "\n" in input_pane.text
            assert "line1" in input_pane.text
            assert "line2" in input_pane.text
            assert len(output.lines) == initial_lines

    @pytest.mark.asyncio
    async def test_alt_enter_inserts_newline(self):
        """Alt+Enter inserts newline without submitting."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")
            output = app.query_one("#output")
            initial_lines = len(output.lines)

            await pilot.click("#prompt")
            await pilot.press("a", "b", "c")
            await pilot.press("alt+enter")
            await pilot.press("d", "e", "f")
            await pilot.pause()

            assert "\n" in input_pane.text
            assert len(output.lines) == initial_lines

    @pytest.mark.asyncio
    async def test_shift_enter_inserts_newline(self):
        """Shift+Enter inserts newline without submitting."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")
            output = app.query_one("#output")
            initial_lines = len(output.lines)

            await pilot.click("#prompt")
            await pilot.press("x", "y")
            await pilot.press("shift+enter")
            await pilot.press("z")
            await pilot.pause()

            assert "\n" in input_pane.text
            assert len(output.lines) == initial_lines

    @pytest.mark.asyncio
    async def test_history_up_only_on_first_line(self):
        """Up arrow triggers history only when cursor is on first line."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")

            # Submit a command to build history
            await pilot.click("#prompt")
            await pilot.press("p", "r", "e", "v")
            await pilot.press("enter")
            await pilot.pause()

            # Type multi-line content: "line1\nline2"
            await pilot.click("#prompt")
            await pilot.press("l", "i", "n", "e", "1")
            await pilot.press("ctrl+enter")
            await pilot.press("l", "i", "n", "e", "2")
            await pilot.pause()

            # Cursor is on line 2 (last line). Up should move cursor, NOT history.
            await pilot.press("up")
            await pilot.pause()

            # Content should still be the multi-line text (not replaced by history)
            assert "line1" in input_pane.text
            assert "line2" in input_pane.text

    @pytest.mark.asyncio
    async def test_single_line_up_down_is_history(self):
        """Single-line content: Up/Down behaves like old Input (history)."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")

            # Submit two commands
            await pilot.click("#prompt")
            await pilot.press("f", "i", "r", "s", "t")
            await pilot.press("enter")
            await pilot.pause()

            await pilot.click("#prompt")
            await pilot.press("s", "e", "c", "o", "n", "d")
            await pilot.press("enter")
            await pilot.pause()

            # On single-line (empty), up should get history
            await pilot.click("#prompt")
            await pilot.press("up")
            await pilot.pause()
            assert input_pane.text == "second"

    @pytest.mark.asyncio
    async def test_multiline_content_submitted_intact(self):
        """Multi-line content is submitted with newlines preserved."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            output = app.query_one("#output")
            input_pane = app.query_one("#prompt")

            await pilot.click("#prompt")
            await pilot.press("l", "i", "n", "e", "1")
            await pilot.press("ctrl+enter")
            await pilot.press("l", "i", "n", "e", "2")
            await pilot.press("enter")
            await pilot.pause()

            # Input should be cleared after submit
            assert input_pane.text == ""
            # Output should have content (echoed)
            assert len(output.lines) > 0

    @pytest.mark.asyncio
    async def test_multiline_history_recall(self):
        """Multi-line content is stored and recalled from history."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")

            # Submit multi-line content
            await pilot.click("#prompt")
            await pilot.press("l", "i", "n", "e", "1")
            await pilot.press("ctrl+enter")
            await pilot.press("l", "i", "n", "e", "2")
            await pilot.press("enter")
            await pilot.pause()

            # Navigate history to recall it
            await pilot.click("#prompt")
            await pilot.press("up")
            await pilot.pause()

            # Should recall full multi-line text
            assert "line1" in input_pane.text
            assert "line2" in input_pane.text
            assert "\n" in input_pane.text
