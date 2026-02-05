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

                # Header and content are now separate writes
                assert mock_write.call_count == 2
                all_calls = "".join(c[0][0] for c in mock_write.call_args_list)
                assert "✓" in all_calls
                assert "@pm" in all_calls
                assert "Plan created" in all_calls

    def test_write_task_error_format(self):
        """write_task_error has correct format with X."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_error("pm", "Failed to connect")

                # Header and content are now separate writes
                assert mock_write.call_count == 2
                all_calls = "".join(c[0][0] for c in mock_write.call_args_list)
                assert "✗" in all_calls
                assert "@pm" in all_calls
                assert "Failed to connect" in all_calls

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

                    # Check first call for timestamp (header call)
                    first_call = mock_write.call_args_list[0][0][0]
                    assert re.search(timestamp_pattern, first_call), (
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
                pane.write_streaming_chunk("pm", "World!\n")
                pane.finish_streaming("pm")

                # Content is written via streaming chunks, completion shows status
                all_calls = "".join(c[0][0] for c in mock_write.call_args_list)
                assert "Hello" in all_calls
                assert "World!" in all_calls
                assert "✓" in all_calls  # Success indicator
                assert "@pm" in all_calls

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

                pane.write_streaming_chunk("pm", "PM says hi\n")
                pane.write_streaming_chunk("builder-1", "Builder says hello\n")

                pane.finish_streaming("pm")
                pane.finish_streaming("builder-1")

                # Check both agents got their content
                all_calls = "".join(c[0][0] for c in mock_write.call_args_list)
                assert "PM says hi" in all_calls
                assert "Builder says hello" in all_calls
                assert "@pm" in all_calls
                assert "@builder-1" in all_calls


class TestOutputPaneWrap:
    """Tests for word wrap configuration."""

    def test_outputpane_wrap_enabled_by_default(self):
        """OutputPane has wrap enabled by default."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()
        # RichLog stores wrap setting internally
        assert pane.wrap is True


class TestHandoffDetection:
    """Tests for agent handoff separator functionality."""

    def test_check_handoff_returns_false_for_first_message(self):
        """First message has no previous agent, so no handoff."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()
        pane._last_agent_id = None

        result = pane._check_handoff("pm")

        assert result is False

    def test_check_handoff_returns_false_for_same_agent(self):
        """Same agent continuing does not trigger handoff."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()
        pane._last_agent_id = "pm"

        result = pane._check_handoff("pm")

        assert result is False

    def test_check_handoff_returns_true_for_different_agent(self):
        """Different agent triggers handoff."""
        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()
        pane._last_agent_id = "pm"

        result = pane._check_handoff("builder-1")

        assert result is True

    def test_handoff_separator_contains_divider_line(self):
        """Handoff separator contains horizontal divider."""
        from unittest.mock import patch

        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            pane._write_handoff_separator("pm", "builder-1")

            call_arg = mock_write.call_args[0][0]
            assert "─" in call_arg

    def test_handoff_separator_shows_new_agent(self):
        """Handoff separator shows new agent icon and ID."""
        from unittest.mock import patch

        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            pane._write_handoff_separator("pm", "builder-1")

            call_arg = mock_write.call_args[0][0]
            assert "@builder-1" in call_arg
            assert "🔨" in call_arg


class TestAgentStyledOutput:
    """Tests for persona-styled output methods."""

    def test_write_task_complete_uses_persona_color(self):
        """write_task_complete applies persona color to agent ID."""
        from unittest.mock import patch

        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_complete("pm", "Plan created")

                # Header call contains agent ID and icon
                calls = [c[0][0] for c in mock_write.call_args_list]
                header_call = [c for c in calls if "@pm" in c][0]
                assert "[blue]" in header_call
                assert "📋" in header_call
                # Content call has colored indent
                content_call = [c for c in calls if "Plan created" in c][0]
                assert "[blue]│" in content_call or "[blue]|" in content_call

    def test_write_task_complete_includes_icon(self):
        """write_task_complete includes agent icon."""
        from unittest.mock import patch

        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_complete("builder-1", "Code complete")

                calls = [c[0][0] for c in mock_write.call_args_list]
                header_call = [c for c in calls if "@builder-1" in c][0]
                assert "🔨" in header_call

    def test_write_task_complete_triggers_handoff_separator(self):
        """write_task_complete shows separator on agent change."""
        from unittest.mock import patch

        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()
        pane._last_agent_id = "pm"

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_complete("builder-1", "Code complete")

                # Should have 3 write calls: separator + header + content
                assert mock_write.call_count == 3
                separator_call = mock_write.call_args_list[0][0][0]
                assert "─" in separator_call

    def test_write_task_error_uses_persona_color(self):
        """write_task_error applies persona color to agent ID."""
        from unittest.mock import patch

        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_task_error("reviewer", "Review failed")

                calls = [c[0][0] for c in mock_write.call_args_list]
                header_call = [c for c in calls if "@reviewer" in c][0]
                # Reviewer has red color
                assert "[red]" in header_call
                assert "🔍" in header_call

    def test_streaming_start_uses_persona_color(self):
        """write_streaming_start applies persona color."""
        from unittest.mock import patch

        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.write_streaming_start("ba")

                calls = [c[0][0] for c in mock_write.call_args_list]
                main_call = [c for c in calls if "streaming" in c][0]
                assert "[cyan]" in main_call
                assert "📊" in main_call

    def test_finish_streaming_uses_persona_color(self):
        """finish_streaming applies persona color."""
        from unittest.mock import patch

        from teambot.ui.widgets.output_pane import OutputPane

        pane = OutputPane()
        pane._streaming_buffers["writer"] = ["Documentation complete"]
        pane._streaming_starts["writer"] = "12:00:00"

        with patch.object(pane, "write") as mock_write:
            with patch.object(pane, "scroll_end"):
                pane.finish_streaming("writer", success=True)

                calls = [c[0][0] for c in mock_write.call_args_list]
                # Look for the completion status line which has the agent styling
                main_call = [c for c in calls if "@writer" in c][0]
                assert "[magenta]" in main_call  # Writer color
                assert "📝" in main_call

    def test_all_six_agents_get_correct_icon_and_color(self):
        """All 6 MVP agents get their correct icon and color in output."""
        from unittest.mock import patch

        from teambot.ui.widgets.output_pane import OutputPane

        # Expected styling for each agent
        expected_styles = {
            "pm": {"color": "blue", "icon": "📋"},
            "ba": {"color": "cyan", "icon": "📊"},
            "writer": {"color": "magenta", "icon": "📝"},
            "builder-1": {"color": "green", "icon": "🔨"},
            "builder-2": {"color": "yellow", "icon": "🔨"},
            "reviewer": {"color": "red", "icon": "🔍"},
        }

        for agent_id, expected in expected_styles.items():
            pane = OutputPane()

            with patch.object(pane, "write") as mock_write:
                with patch.object(pane, "scroll_end"):
                    pane.write_task_complete(agent_id, f"Task by {agent_id}")

                    calls = [c[0][0] for c in mock_write.call_args_list]
                    # Header call contains agent ID and icon
                    header_call = [c for c in calls if f"@{agent_id}" in c][0]

                    assert f"[{expected['color']}]" in header_call, (
                        f"{agent_id} should have [{expected['color']}], got: {header_call}"
                    )
                    assert expected["icon"] in header_call, (
                        f"{agent_id} should have {expected['icon']}, got: {header_call}"
                    )
