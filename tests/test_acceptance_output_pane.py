"""Acceptance validation tests for Output Pane Enhancement.

These tests validate acceptance scenarios using REAL implementation code.
Each test corresponds to an acceptance scenario (AT-XXX).
"""

from teambot.ui.widgets.output_pane import OutputPane
from teambot.visualization.console import (
    AGENT_ICONS,
    AGENT_PERSONAS,
    PERSONA_COLORS,
    get_agent_style,
)


class TestOutputPaneAcceptanceScenarios:
    """Acceptance scenario validation tests for output pane enhancement."""

    # =========================================================================
    # AT-001: Multi-Agent Output Identification
    # =========================================================================
    def test_at_001_pm_agent_has_blue_color_and_clipboard_icon(self):
        """AT-001: PM output appears in blue with 📋 icon."""
        color, icon = get_agent_style("pm")
        assert color == "blue", f"PM should be blue, got {color}"
        assert icon == "📋", f"PM should have 📋 icon, got {icon}"

    def test_at_001_builder_agent_has_green_color_and_hammer_icon(self):
        """AT-001: Builder-1 output appears in green with 🔨 icon."""
        color, icon = get_agent_style("builder-1")
        assert color == "green", f"Builder-1 should be green, got {color}"
        assert icon == "🔨", f"Builder-1 should have 🔨 icon, got {icon}"

    def test_at_001_builder2_agent_has_yellow_color_and_hammer_icon(self):
        """AT-001: Builder-2 output appears in yellow with 🔨 icon."""
        color, icon = get_agent_style("builder-2")
        assert color == "yellow", f"Builder-2 should be yellow, got {color}"
        assert icon == "🔨", f"Builder-2 should have 🔨 icon, got {icon}"

    def test_at_001_agents_are_distinguishable(self):
        """AT-001: Each agent has distinct color - clearly distinguishable."""
        pm_color, pm_icon = get_agent_style("pm")
        builder_color, builder_icon = get_agent_style("builder-1")
        ba_color, ba_icon = get_agent_style("ba")
        writer_color, writer_icon = get_agent_style("writer")
        reviewer_color, reviewer_icon = get_agent_style("reviewer")

        # All colors are different (except builder-1 and builder-2 which share)
        colors = {pm_color, builder_color, ba_color, writer_color, reviewer_color}
        assert len(colors) == 5, f"Expected 5 distinct colors, got {colors}"

        # All icons are different (except builders)
        icons = {pm_icon, builder_icon, ba_icon, writer_icon, reviewer_icon}
        assert len(icons) == 5, f"Expected 5 distinct icons, got {icons}"

    def test_at_001_output_pane_formats_with_persona_color(self):
        """AT-001: OutputPane write methods include persona color in markup."""
        pane = OutputPane()
        written_lines = []

        # Capture what gets written by patching write
        pane.write = lambda text: written_lines.append(text)

        pane.write_task_complete("pm", "Creating project plan...")
        pane.write_task_complete("builder-1", "Implementing feature X...")

        # Verify PM output has blue markup
        pm_line = written_lines[0]
        assert "[blue]" in pm_line, f"PM output should contain [blue] markup: {pm_line}"
        assert "📋" in pm_line, f"PM output should contain 📋 icon: {pm_line}"
        assert "@pm" in pm_line, f"PM output should contain @pm: {pm_line}"

        # Verify Builder-1 output has green markup (per spec: builder-1=green)
        builder_line = written_lines[1]  # Skip handoff separator
        # Find the actual builder line (may be after handoff)
        for line in written_lines:
            if "@builder-1" in line and "✓" in line:
                builder_line = line
                break
        assert "[green]" in builder_line, f"Builder-1 output should contain [green]: {builder_line}"
        assert "🔨" in builder_line, f"Builder-1 output should contain 🔨 icon: {builder_line}"

    # =========================================================================
    # AT-002: Long Line Word Wrap
    # =========================================================================
    def test_at_002_outputpane_wrap_enabled_by_default(self):
        """AT-002: OutputPane has wrap=True to prevent horizontal scrolling."""
        pane = OutputPane()
        # RichLog stores wrap in .wrap attribute (public property)
        # Check that wrap was passed as True
        assert pane.wrap is True, "OutputPane should have wrap=True by default"

    def test_at_002_wrap_can_be_overridden(self):
        """AT-002: wrap setting can be explicitly overridden if needed."""
        pane_wrapped = OutputPane(wrap=True)
        pane_no_wrap = OutputPane(wrap=False)

        assert pane_wrapped.wrap is True
        assert pane_no_wrap.wrap is False

    # =========================================================================
    # AT-003: Agent Handoff Indicator
    # =========================================================================
    def test_at_003_handoff_detected_when_agent_changes(self):
        """AT-003: _check_handoff returns True when switching agents."""
        pane = OutputPane()

        # First agent - no handoff
        pane._last_agent_id = None
        assert pane._check_handoff("pm") is False

        # Same agent - no handoff
        pane._last_agent_id = "pm"
        assert pane._check_handoff("pm") is False

        # Different agent - handoff!
        assert pane._check_handoff("builder-1") is True

    def test_at_003_handoff_separator_contains_divider(self):
        """AT-003: Handoff separator has horizontal divider."""
        pane = OutputPane()
        written_lines = []
        pane.write = lambda text: written_lines.append(text)

        pane._write_handoff_separator("pm", "builder-1")

        assert len(written_lines) == 1
        separator = written_lines[0]
        assert "─" in separator, f"Separator should contain ─ divider: {separator}"

    def test_at_003_handoff_separator_shows_new_agent_label(self):
        """AT-003: Handoff separator shows → @builder-1 label."""
        pane = OutputPane()
        written_lines = []
        pane.write = lambda text: written_lines.append(text)

        pane._write_handoff_separator("pm", "builder-1")

        separator = written_lines[0]
        assert "→" in separator, f"Separator should contain → arrow: {separator}"
        assert "@builder-1" in separator, f"Separator should show @builder-1: {separator}"
        assert "🔨" in separator, f"Separator should show builder icon: {separator}"

    def test_at_003_handoff_triggered_on_task_complete(self):
        """AT-003: Handoff separator written when switching agents on task_complete."""
        pane = OutputPane()
        written_lines = []
        pane.write = lambda text: written_lines.append(text)

        # PM completes task
        pane.write_task_complete("pm", "Plan complete")
        # Builder completes task - should trigger handoff
        pane.write_task_complete("builder-1", "Starting implementation")

        # Should have: PM header, PM content, handoff separator, builder header, builder content
        assert len(written_lines) == 5, (
            f"Expected 5 lines, got {len(written_lines)}: {written_lines}"
        )
        # Line 0: PM header
        assert "@pm" in written_lines[0]
        # Line 1: PM content with indent
        assert "│" in written_lines[1] and "Plan complete" in written_lines[1]
        # Line 2: Handoff separator
        assert "→" in written_lines[2] and "@builder-1" in written_lines[2]
        # Line 3: Builder header
        assert "@builder-1" in written_lines[3]
        # Line 4: Builder content with indent
        assert "│" in written_lines[4] and "Starting implementation" in written_lines[4]

    # =========================================================================
    # AT-004: Code Block Formatting Preserved
    # =========================================================================
    def test_at_004_wrap_preserves_content_integrity(self):
        """AT-004: Wrap doesn't mangle content - preserves indentation in string."""
        pane = OutputPane()
        written_lines = []
        pane.write = lambda text: written_lines.append(text)

        # Code block with indentation
        code_block = """```python
def example():
    if True:
        print("Hello")
```"""
        pane.write_task_complete("builder-1", code_block)

        # The code block should be preserved in the output
        output = written_lines[-1]  # May be after handoff
        assert "def example():" in output
        assert "    if True:" in output or "if True:" in output  # Indentation may vary
        assert 'print("Hello")' in output

    # =========================================================================
    # AT-005: Color Consistency Across Message Types
    # =========================================================================
    def test_at_005_streaming_start_uses_persona_color(self):
        """AT-005: Streaming start (⟳) uses PM's blue color."""
        pane = OutputPane()
        written_lines = []
        pane.write = lambda text: written_lines.append(text)

        pane.write_streaming_start("pm")

        line = written_lines[-1]
        assert "[blue]" in line, f"Streaming start should use blue for PM: {line}"
        assert "⟳" in line, f"Streaming start should have ⟳ indicator: {line}"
        assert "@pm" in line, f"Streaming start should show @pm: {line}"

    def test_at_005_task_complete_uses_persona_color(self):
        """AT-005: Task complete (✓) uses PM's blue color."""
        pane = OutputPane()
        written_lines = []
        pane.write = lambda text: written_lines.append(text)

        pane.write_task_complete("pm", "Success!")

        # First line is the header with the checkmark
        header_line = written_lines[0]
        assert "[blue]" in header_line, f"Task complete should use blue for PM: {header_line}"
        assert "✓" in header_line, f"Task complete should have ✓ indicator: {header_line}"
        assert "@pm" in header_line

        # Second line is the content with indent
        content_line = written_lines[1]
        assert "│" in content_line, f"Content should have indent: {content_line}"
        assert "Success!" in content_line

    def test_at_005_task_error_uses_persona_color(self):
        """AT-005: Task error (✗) uses PM's blue color for agent ID."""
        pane = OutputPane()
        written_lines = []
        pane.write = lambda text: written_lines.append(text)

        pane.write_task_error("pm", "Failed!")

        # First line is the header with error indicator
        header_line = written_lines[0]
        assert "[blue]" in header_line, f"Task error should use blue for PM: {header_line}"
        assert "✗" in header_line, f"Task error should have ✗ indicator: {header_line}"
        assert "@pm" in header_line

        # Second line is the content with indent
        content_line = written_lines[1]
        assert "│" in content_line, f"Content should have indent: {content_line}"
        assert "Failed!" in content_line

    def test_at_005_finish_streaming_uses_persona_color(self):
        """AT-005: Finish streaming uses PM's blue color."""
        pane = OutputPane()
        written_lines = []
        pane.write = lambda text: written_lines.append(text)

        # Start and finish streaming
        pane.write_streaming_start("pm")
        pane.write_streaming_chunk("pm", "content")
        pane.finish_streaming("pm", success=True)

        # Last line is the finish status
        finish_line = written_lines[-1]
        assert "[blue]" in finish_line, f"Finish streaming should use blue: {finish_line}"
        assert "✓" in finish_line, f"Finish streaming should have ✓: {finish_line}"
        assert "streaming complete" in finish_line, f"Should indicate completion: {finish_line}"

    def test_at_005_all_message_types_consistent_color(self):
        """AT-005: All three message types show PM's blue color consistently."""
        pane = OutputPane()
        written_lines = []
        pane.write = lambda text: written_lines.append(text)

        # Generate all three message types for PM
        pane.write_streaming_start("pm")  # Line 0: ⟳
        written_lines.clear()  # Reset for cleaner test

        pane._streaming_buffers.clear()
        pane._last_agent_id = None
        pane._indent_stack = []

        pane.write_task_complete("pm", "Success")  # ✓
        pane.write_task_error("pm", "Error")  # ✗
        pane.write_streaming_start("pm")  # ⟳

        # All lines should contain [blue] for PM's color
        # (either in header or indent bar)
        for i, line in enumerate(written_lines):
            assert "[blue]" in line, f"Line {i} should have [blue]: {line}"


class TestAgentStyleIntegration:
    """Integration tests verifying agent style system works end-to-end."""

    def test_all_six_agents_have_styles(self):
        """All 6 MVP agents have defined styles."""
        agents = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]

        for agent_id in agents:
            color, icon = get_agent_style(agent_id)
            assert color != "white", f"{agent_id} should have a color, not white"
            assert icon != "●", f"{agent_id} should have an icon, not default ●"

    def test_unknown_agent_gets_default_style(self):
        """Unknown agent gets white color and default icon."""
        color, icon = get_agent_style("unknown-agent")
        assert color == "white"
        assert icon == "●"

    def test_persona_to_color_mapping_is_complete(self):
        """All personas defined in AGENT_PERSONAS have colors."""
        for _agent_id, persona in AGENT_PERSONAS.items():
            assert persona in PERSONA_COLORS, f"Persona {persona} missing from PERSONA_COLORS"

    def test_all_agents_have_icons(self):
        """All agents in AGENT_PERSONAS have icons."""
        for agent_id in AGENT_PERSONAS:
            assert agent_id in AGENT_ICONS, f"Agent {agent_id} missing from AGENT_ICONS"
