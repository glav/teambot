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
            "builder_primary",
            "builder_secondary",
            "reviewer",
        ]

        for persona in expected_personas:
            assert persona in PERSONA_COLORS
            assert PERSONA_COLORS[persona] is not None


class TestAgentStyling:
    """Tests for agent styling constants and helper."""

    def test_all_agents_have_personas(self):
        """All 6 agent IDs have persona mappings."""
        from teambot.visualization.console import AGENT_PERSONAS

        expected_agents = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]
        for agent_id in expected_agents:
            assert agent_id in AGENT_PERSONAS

    def test_all_agents_have_icons(self):
        """All 6 agent IDs have icon mappings."""
        from teambot.visualization.console import AGENT_ICONS

        expected_agents = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]
        for agent_id in expected_agents:
            assert agent_id in AGENT_ICONS

    def test_get_agent_style_pm_returns_blue_and_clipboard(self):
        """get_agent_style returns blue color and clipboard icon for PM."""
        from teambot.visualization.console import get_agent_style

        color, icon = get_agent_style("pm")
        assert color == "blue"
        assert icon == "📋"

    def test_get_agent_style_all_agents(self):
        """All agents return correct color and icon."""
        from teambot.visualization.console import get_agent_style

        expected = {
            "pm": ("blue", "📋"),
            "ba": ("cyan", "📊"),
            "writer": ("magenta", "📝"),
            "builder-1": ("green", "🔨"),
            "builder-2": ("yellow", "🔨"),
            "reviewer": ("red", "🔍"),
        }
        for agent_id, (expected_color, expected_icon) in expected.items():
            color, icon = get_agent_style(agent_id)
            assert color == expected_color, f"{agent_id} color mismatch"
            assert icon == expected_icon, f"{agent_id} icon mismatch"

    def test_get_agent_style_unknown_agent_returns_default(self):
        """Unknown agent returns default styling."""
        from teambot.visualization.console import get_agent_style

        color, icon = get_agent_style("unknown-agent")
        assert color == "white"
        assert icon == "●"
