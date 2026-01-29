"""Tests for OutputPane widget."""

from unittest.mock import patch


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
                    assert re.search(timestamp_pattern, call_arg), (
                        f"{method_name} should include timestamp"
                    )


class TestOutputPaneStreaming:
    """Tests for OutputPane streaming functionality."""

    def test_write_streaming_start_initializes_buffer(self):
        """write_streaming_start creates buffer for agent."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write"):
            pane.write_streaming_start("pm")

            assert "pm" in pane._streaming_buffers
            assert pane._streaming_buffers["pm"] == []
            assert "pm" in pane._streaming_starts

    def test_write_streaming_chunk_accumulates(self):
        """write_streaming_chunk accumulates chunks in buffer."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write"):
            with patch.object(pane, "scroll_end"):
                pane.write_streaming_start("pm")
                pane.write_streaming_chunk("pm", "Hello ")
                pane.write_streaming_chunk("pm", "World!")

                assert pane._streaming_buffers["pm"] == ["Hello ", "World!"]

    def test_write_streaming_chunk_auto_starts(self):
        """write_streaming_chunk auto-starts streaming if not started."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write"):
            with patch.object(pane, "scroll_end"):
                # No explicit start, just chunk
                pane.write_streaming_chunk("pm", "Content")

                assert "pm" in pane._streaming_buffers
                assert pane._streaming_buffers["pm"] == ["Content"]

    def test_finish_streaming_writes_accumulated_content(self):
        """finish_streaming writes complete accumulated content."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_streaming_start("pm")
                pane.write_streaming_chunk("pm", "Hello ")
                pane.write_streaming_chunk("pm", "World!")
                pane.finish_streaming("pm")

                # Last call should have the complete content
                last_call = mock_write.call_args_list[-1][0][0]
                assert "Hello World!" in last_call
                assert "✓" in last_call  # Success indicator
                assert "@pm" in last_call

    def test_finish_streaming_cleans_up_state(self):
        """finish_streaming cleans up streaming state."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write"):
            with patch.object(pane, "scroll_end"):
                pane.write_streaming_start("pm")
                pane.write_streaming_chunk("pm", "Content")
                pane.finish_streaming("pm")

                assert "pm" not in pane._streaming_buffers
                assert "pm" not in pane._streaming_starts

    def test_finish_streaming_with_error_shows_error_indicator(self):
        """finish_streaming with success=False shows error indicator."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_streaming_start("pm")
                pane.write_streaming_chunk("pm", "Partial content")
                pane.finish_streaming("pm", success=False)

                last_call = mock_write.call_args_list[-1][0][0]
                assert "✗" in last_call  # Error indicator

    def test_is_streaming_returns_true_when_active(self):
        """is_streaming returns True when agent is streaming."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write"):
            assert pane.is_streaming("pm") is False

            pane.write_streaming_start("pm")
            assert pane.is_streaming("pm") is True
            assert pane.is_streaming() is True  # Any agent

    def test_is_streaming_returns_false_after_finish(self):
        """is_streaming returns False after finish_streaming."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write"):
            with patch.object(pane, "scroll_end"):
                pane.write_streaming_start("pm")
                pane.finish_streaming("pm")

                assert pane.is_streaming("pm") is False
                assert pane.is_streaming() is False

    def test_get_streaming_agents(self):
        """get_streaming_agents returns list of active agents."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write"):
            assert pane.get_streaming_agents() == []

            pane.write_streaming_start("pm")
            pane.write_streaming_start("builder-1")

            agents = pane.get_streaming_agents()
            assert "pm" in agents
            assert "builder-1" in agents

    def test_multiple_agents_stream_independently(self):
        """Multiple agents can stream without interfering."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_streaming_start("pm")
                pane.write_streaming_start("builder-1")

                pane.write_streaming_chunk("pm", "PM says hi")
                pane.write_streaming_chunk("builder-1", "Builder says hello")

                pane.finish_streaming("pm")
                pane.finish_streaming("builder-1")

                # Check both agents got their content
                calls = [c[0][0] for c in mock_write.call_args_list]
                pm_call = [c for c in calls if "@pm" in c and "PM says hi" in c]
                builder_call = [c for c in calls if "@builder-1" in c and "Builder says hello" in c]

                assert len(pm_call) >= 1
                assert len(builder_call) >= 1
