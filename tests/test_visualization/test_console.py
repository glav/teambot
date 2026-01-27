"""Tests for console visualization - Code-First approach."""


class TestConsoleDisplay:
    """Tests for ConsoleDisplay class."""

    def test_create_display(self):
        """Display initializes with empty agents."""
        from teambot.visualization.console import ConsoleDisplay

        display = ConsoleDisplay()

        assert display.agents == {}
        assert display.console is not None

    def test_add_agent(self):
        """Add agent registers it for display."""
        from teambot.visualization.console import AgentStatus, ConsoleDisplay

        display = ConsoleDisplay()

        display.add_agent("builder-1", "builder", "Builder (Primary)")

        assert "builder-1" in display.agents
        assert display.agents["builder-1"]["persona"] == "builder"
        assert display.agents["builder-1"]["display_name"] == "Builder (Primary)"
        assert display.agents["builder-1"]["status"] == AgentStatus.IDLE

    def test_add_agent_default_display_name(self):
        """Agent uses ID as display name if not provided."""
        from teambot.visualization.console import ConsoleDisplay

        display = ConsoleDisplay()

        display.add_agent("pm", "project_manager")

        assert display.agents["pm"]["display_name"] == "pm"

    def test_update_status(self):
        """Update agent status."""
        from teambot.visualization.console import AgentStatus, ConsoleDisplay

        display = ConsoleDisplay()
        display.add_agent("builder-1", "builder")

        display.update_status(
            "builder-1",
            AgentStatus.WORKING,
            task="Implementing feature",
            progress=50,
        )

        agent = display.agents["builder-1"]
        assert agent["status"] == AgentStatus.WORKING
        assert agent["current_task"] == "Implementing feature"
        assert agent["progress"] == 50

    def test_update_status_unknown_agent(self):
        """Update status for unknown agent does nothing."""
        from teambot.visualization.console import AgentStatus, ConsoleDisplay

        display = ConsoleDisplay()

        # Should not raise
        display.update_status("unknown", AgentStatus.WORKING)

    def test_get_status(self):
        """Get agent status."""
        from teambot.visualization.console import AgentStatus, ConsoleDisplay

        display = ConsoleDisplay()
        display.add_agent("builder-1", "builder")

        status = display.get_status("builder-1")

        assert status == AgentStatus.IDLE

    def test_get_status_unknown_agent(self):
        """Get status for unknown agent returns None."""
        from teambot.visualization.console import ConsoleDisplay

        display = ConsoleDisplay()

        status = display.get_status("unknown")

        assert status is None

    def test_progress_clamped(self):
        """Progress is clamped to 0-100."""
        from teambot.visualization.console import AgentStatus, ConsoleDisplay

        display = ConsoleDisplay()
        display.add_agent("builder-1", "builder")

        display.update_status("builder-1", AgentStatus.WORKING, progress=150)
        assert display.agents["builder-1"]["progress"] == 100

        display.update_status("builder-1", AgentStatus.WORKING, progress=-10)
        assert display.agents["builder-1"]["progress"] == 0

    def test_render_table(self):
        """Render agents as Rich table."""
        from rich.table import Table

        from teambot.visualization.console import ConsoleDisplay

        display = ConsoleDisplay()
        display.add_agent("pm", "project_manager", "Project Manager")
        display.add_agent("builder-1", "builder", "Builder")

        table = display.render_table()

        assert isinstance(table, Table)

    def test_make_progress_bar(self):
        """Progress bar renders correctly."""
        from teambot.visualization.console import ConsoleDisplay

        display = ConsoleDisplay()

        bar_0 = display._make_progress_bar(0)
        assert "0%" in bar_0

        bar_50 = display._make_progress_bar(50)
        assert "50%" in bar_50

        bar_100 = display._make_progress_bar(100)
        assert "100%" in bar_100


class TestAgentStatus:
    """Tests for AgentStatus enum."""

    def test_status_values(self):
        """All expected status values exist."""
        from teambot.visualization.console import AgentStatus

        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.WORKING.value == "working"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.WAITING.value == "waiting"


class TestPersonaColors:
    """Tests for persona color mapping."""

    def test_all_personas_have_colors(self):
        """All MVP personas have assigned colors."""
        from teambot.visualization.console import PERSONA_COLORS

        expected_personas = [
            "project_manager",
            "business_analyst",
            "technical_writer",
            "builder",
            "reviewer",
        ]

        for persona in expected_personas:
            assert persona in PERSONA_COLORS
            assert PERSONA_COLORS[persona] is not None
