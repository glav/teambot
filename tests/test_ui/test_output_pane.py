"""Tests for OutputPane widget."""

from unittest.mock import MagicMock, patch
from datetime import datetime


class TestOutputPane:
    """Tests for OutputPane widget."""

    def test_write_command_format(self):
        """write_command outputs correct format."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_command("@pm test")

                mock_write.assert_called_once()
                call_arg = mock_write.call_args[0][0]
                assert "@pm test" in call_arg
                assert ">" in call_arg

    def test_write_task_complete_format(self):
        """write_task_complete has correct format with checkmark."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_complete("pm", "Plan created")

                mock_write.assert_called_once()
                call_arg = mock_write.call_args[0][0]
                assert "✓" in call_arg
                assert "@pm" in call_arg
                assert "Plan created" in call_arg

    def test_write_task_error_format(self):
        """write_task_error has correct format with X."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_error("pm", "Failed to connect")

                mock_write.assert_called_once()
                call_arg = mock_write.call_args[0][0]
                assert "✗" in call_arg
                assert "@pm" in call_arg
                assert "Failed to connect" in call_arg

    def test_write_info_format(self):
        """write_info has correct format with info icon."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_info("Tip: Use @agent")

                mock_write.assert_called_once()
                call_arg = mock_write.call_args[0][0]
                assert "ℹ" in call_arg
                assert "Tip: Use @agent" in call_arg

    def test_write_system_format(self):
        """write_system outputs with timestamp and newline."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_system("Status: OK")

                mock_write.assert_called_once()
                call_arg = mock_write.call_args[0][0]
                assert "Status: OK" in call_arg

    def test_all_methods_call_scroll_end(self):
        """All write methods scroll to end."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        methods_and_args = [
            ("write_command", ("test",)),
            ("write_task_complete", ("pm", "done")),
            ("write_task_error", ("pm", "error")),
            ("write_info", ("info",)),
            ("write_system", ("output",)),
        ]

        for method_name, args in methods_and_args:
            with patch.object(pane, "write"):
                with patch.object(pane, "scroll_end") as mock_scroll:
                    method = getattr(pane, method_name)
                    method(*args)
                    mock_scroll.assert_called_once()

    def test_timestamp_present_in_all_outputs(self):
        """All write methods include timestamp."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        # Check that timestamp pattern appears (HH:MM:SS)
        import re

        timestamp_pattern = r"\d{2}:\d{2}:\d{2}"

        methods_and_args = [
            ("write_command", ("test",)),
            ("write_task_complete", ("pm", "done")),
            ("write_task_error", ("pm", "error")),
            ("write_info", ("info",)),
            ("write_system", ("output",)),
        ]

        for method_name, args in methods_and_args:
            with patch.object(pane, "write") as mock_write:
                with patch.object(pane, "scroll_end"):
                    method = getattr(pane, method_name)
                    method(*args)

                    call_arg = mock_write.call_args[0][0]
                    assert re.search(
                        timestamp_pattern, call_arg
                    ), f"{method_name} should include timestamp"
