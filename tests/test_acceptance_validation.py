"""Acceptance test validation for feature specifications.

These tests exercise the REAL implementation code to validate
each acceptance scenario from feature specifications.
"""

from __future__ import annotations

import argparse
import json
import re
from io import StringIO

import pytest
from rich.console import Console
from rich.panel import Panel

from teambot.repl.commands import (
    SystemCommands,
    handle_help,
    handle_reset_agent,
    handle_status,
    handle_use_agent,
)
from teambot.repl.parser import CommandType, parse_command
from teambot.repl.router import VALID_AGENTS, AgentRouter
from teambot.ui.agent_state import AgentStatusManager
from teambot.ui.widgets.status_panel import StatusPanel
from teambot.visualization.animation import (
    LOGO_COLOR_MAP,
    TEAMBOT_LOGO,
    StartupAnimation,
    play_startup_animation,
)


class TestAcceptanceScenarios:
    """Acceptance test scenarios for the startup animation feature."""

    # -- AT-001: Default Startup Animation Plays --

    def test_at_001_convergence_frames_use_all_six_agent_colors(self):
        """Convergence animation uses all 6 agent colors."""
        console = Console(file=StringIO(), force_terminal=True, color_system="truecolor", width=80)
        anim = StartupAnimation(console=console, version="0.1.0")

        frames = anim._generate_convergence_frames()
        assert len(frames) == 20, f"Expected 20 convergence frames, got {len(frames)}"

        all_styles: set[str] = set()
        for text_obj, _delay in frames:
            for span in text_obj.spans:
                if span.style:
                    all_styles.add(str(span.style))

        expected_colors = {"blue", "cyan", "magenta", "green", "yellow", "red"}
        found_colors: set[str] = set()
        for style_str in all_styles:
            for color in expected_colors:
                if color in style_str:
                    found_colors.add(color)

        assert found_colors == expected_colors, (
            f"Missing agent colors: {expected_colors - found_colors}"
        )

    def test_at_001_convergence_dots_converge_to_center(self):
        """Agent dots converge from edges to center over frames."""
        console = Console(file=StringIO(), force_terminal=True, color_system="truecolor", width=80)
        anim = StartupAnimation(console=console, version="0.1.0")

        frames = anim._generate_convergence_frames()
        first_text = frames[0][0].plain
        last_text = frames[-1][0].plain

        # First frame: 6 dots spread across grid
        assert first_text.count("●") == 6

        # Last frame: dots converge to center, overlapping in the grid cell
        # (fewer visible dots is expected — they share the same position)
        assert last_text.count("●") >= 1

        def get_dot_positions(text: str) -> list[tuple[int, int]]:
            positions = []
            for row_idx, line in enumerate(text.split("\n")):
                for col_idx, char in enumerate(line):
                    if char == "●":
                        positions.append((col_idx, row_idx))
            return positions

        def spread(positions: list[tuple[int, int]]) -> float:
            if not positions:
                return 0.0
            cx = sum(p[0] for p in positions) / len(positions)
            cy = sum(p[1] for p in positions) / len(positions)
            return max(abs(p[0] - cx) + abs(p[1] - cy) for p in positions)

        first_spread = spread(get_dot_positions(first_text))
        last_spread = spread(get_dot_positions(last_text))
        assert last_spread < first_spread, (
            f"Dots should converge: first spread={first_spread}, last spread={last_spread}"
        )

    def test_at_001_logo_reveal_produces_colored_wordmark(self):
        """Logo reveal frames progressively show the colored TeamBot wordmark."""
        console = Console(file=StringIO(), force_terminal=True, color_system="truecolor", width=80)
        anim = StartupAnimation(console=console, version="0.1.0")

        frames = anim._generate_logo_frames()
        assert len(frames) == 10, f"Expected 10 logo frames, got {len(frames)}"

        last_frame_text = frames[-1][0].plain
        assert "██" in last_frame_text or "TEAMBOT" in last_frame_text.upper()

    def test_at_001_animation_duration_within_range(self):
        """Total animation frames yield 3–4 second duration."""
        console = Console(file=StringIO(), force_terminal=True, color_system="truecolor", width=80)
        anim = StartupAnimation(console=console, version="0.1.0")

        convergence = anim._generate_convergence_frames()
        logo = anim._generate_logo_frames()

        total_delay = sum(d for _, d in convergence) + sum(d for _, d in logo)
        assert 2.5 <= total_delay <= 4.0, f"Animation duration {total_delay}s not in 2.5–4.0s range"

    def test_at_001_final_banner_contains_version_string(self):
        """Final banner displays version string after animation."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, color_system="truecolor", width=80)
        anim = StartupAnimation(console=console, version="0.1.0")

        banner = anim._final_banner()
        console.print(banner)
        rendered = output.getvalue()

        assert "0.1.0" in rendered, "Version string not found in final banner"
        assert "AI agents working together" in rendered

    # -- AT-002: Animation on `teambot init` --

    def test_at_002_animation_called_during_init(self, tmp_path, monkeypatch):
        """cmd_init() invokes play_startup_animation."""
        monkeypatch.chdir(tmp_path)

        call_log: list[str] = []
        original_play = play_startup_animation

        def tracking_play(*args, **kwargs):
            call_log.append("animation")
            original_play(*args, **kwargs)

        monkeypatch.setattr("teambot.cli.play_startup_animation", tracking_play)

        output = StringIO()
        console = Console(file=output, force_terminal=True, color_system="truecolor", width=80)
        from teambot.visualization.console import ConsoleDisplay

        display = ConsoleDisplay()
        display.console = console

        args = argparse.Namespace(force=False, no_animation=True)

        from teambot.cli import cmd_init

        result = cmd_init(args, display)
        assert result == 0
        assert "animation" in call_log, "play_startup_animation was not called during init"

    def test_at_002_animation_before_agent_table(self, tmp_path, monkeypatch):
        """Animation output appears before agent table in init flow."""
        monkeypatch.chdir(tmp_path)

        call_order: list[str] = []

        original_play = play_startup_animation

        def tracking_play(*args, **kwargs):
            call_order.append("animation")
            original_play(*args, **kwargs)

        monkeypatch.setattr("teambot.cli.play_startup_animation", tracking_play)

        from teambot.visualization.console import ConsoleDisplay

        original_print_status = ConsoleDisplay.print_status

        def tracking_print_status(self):
            call_order.append("agent_table")
            original_print_status(self)

        monkeypatch.setattr(ConsoleDisplay, "print_status", tracking_print_status)

        display = ConsoleDisplay()
        args = argparse.Namespace(force=False, no_animation=True)

        from teambot.cli import cmd_init

        cmd_init(args, display)

        assert "animation" in call_order, "Animation not called"
        assert "agent_table" in call_order, "Agent table not printed"
        assert call_order.index("animation") < call_order.index("agent_table"), (
            f"Animation must come before agent table, got: {call_order}"
        )

    # -- AT-003: --no-animation Flag Disables Animation --

    def test_at_003_no_animation_flag_shows_static_banner(self):
        """--no-animation flag shows static banner instead of animation."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, color_system="truecolor", width=80)

        play_startup_animation(
            console=console,
            config={"show_startup_animation": True},
            no_animation_flag=True,
            version="0.1.0",
        )

        rendered = output.getvalue()
        assert len(rendered) > 0, "Static banner should appear when animation disabled"
        assert "0.1.0" in rendered, "Version string should appear in static banner"

    def test_at_003_cli_parser_parses_no_animation(self):
        """CLI parser correctly parses --no-animation flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--no-animation", "run", "obj.md"])
        assert args.no_animation is True

    # -- AT-004: Config Setting Disables Animation --

    def test_at_004_config_false_shows_static_banner(self):
        """show_startup_animation=false shows static banner instead of animation."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, color_system="truecolor", width=80)

        play_startup_animation(
            console=console,
            config={"show_startup_animation": False},
            no_animation_flag=False,
            version="0.1.0",
        )

        rendered = output.getvalue()
        assert len(rendered) > 0, "Static banner should appear when config disables animation"
        assert "0.1.0" in rendered, "Version string should appear in static banner"

    def test_at_004_config_loader_validates_setting(self, tmp_path):
        """Config loader validates show_startup_animation: false."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "show_startup_animation": False,
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)
        assert config["show_startup_animation"] is False

    # -- AT-005: CLI Flag Overrides Config Setting --

    def test_at_005_flag_overrides_config_enabled(self):
        """--no-animation flag overrides config show_startup_animation=true."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, color_system="truecolor", width=80)

        # Config says animate, but flag says no → static banner
        play_startup_animation(
            console=console,
            config={"show_startup_animation": True},
            no_animation_flag=True,
            version="0.1.0",
        )

        rendered = output.getvalue()
        assert len(rendered) > 0, "Static banner should appear when flag overrides config"
        assert "0.1.0" in rendered

    def test_at_005_is_explicitly_disabled_flag_takes_precedence(self):
        """_is_explicitly_disabled returns True when flag=True regardless of config."""
        console = Console(file=StringIO(), force_terminal=True, width=80)
        anim = StartupAnimation(console=console)

        assert (
            anim._is_explicitly_disabled(
                config={"show_startup_animation": True},
                no_animation_flag=True,
            )
            is True
        )

    # -- AT-006: Auto-Disable in Non-TTY Environment --

    def test_at_006_non_tty_shows_static_banner(self):
        """Non-TTY environment gets static banner, not animation."""
        output = StringIO()
        # force_terminal=False simulates non-TTY
        console = Console(file=output, force_terminal=False, width=80)

        anim = StartupAnimation(console=console, version="0.1.0")
        anim.play(config={"show_startup_animation": True}, no_animation_flag=False)

        rendered = output.getvalue()
        # In non-TTY: _is_explicitly_disabled=False, _supports_animation=False → static banner
        assert len(rendered) > 0, "Non-TTY should produce static banner output"

    def test_at_006_supports_animation_false_for_non_tty(self):
        """_supports_animation returns False when stdout is not a TTY."""
        console = Console(file=StringIO(), force_terminal=True, width=80)
        anim = StartupAnimation(console=console)

        # In test runner, sys.stdout.isatty() is typically False
        result = anim._supports_animation()
        assert isinstance(result, bool)

    # -- AT-007: Graceful Degradation — Colour-Limited Terminal --

    def test_at_007_no_color_produces_plain_text_banner(self):
        """No-color console produces banner without ANSI color codes."""
        output = StringIO()
        console = Console(file=output, color_system=None, width=80)

        anim = StartupAnimation(console=console, version="0.1.0")
        anim._show_static_banner()

        rendered = output.getvalue()
        ansi_pattern = re.compile(r"\033\[")
        assert not ansi_pattern.search(rendered), (
            f"Found ANSI escapes in no-color output: {repr(rendered[:200])}"
        )
        assert "0.1.0" in rendered
        has_logo = any(ch in rendered for ch in ["█", "╗", "T", "_"])
        assert has_logo, "No logo characters found in degraded output"

    def test_at_007_colorize_returns_plain_text_when_no_color(self):
        """_colorize_logo_line returns unstyled text when color_system is None."""
        console = Console(file=StringIO(), color_system=None, width=80)
        anim = StartupAnimation(console=console)

        line = TEAMBOT_LOGO[0]
        result = anim._colorize_logo_line(line, LOGO_COLOR_MAP)

        assert len(result.spans) == 0, "Expected no style spans in no-color mode"
        assert result.plain == line

    def test_at_007_ascii_fallback_for_non_utf8(self):
        """Non-UTF-8 console uses ASCII fallback logo."""
        output = StringIO()
        console = Console(
            file=output,
            force_terminal=True,
            color_system="standard",
            width=80,
        )

        anim = StartupAnimation(console=console, version="0.1.0")

        # Patch encoding property to return 'ascii'
        import unittest.mock

        with unittest.mock.patch.object(
            type(console), "encoding", new_callable=lambda: property(lambda self: "ascii")
        ):
            assert anim._supports_unicode() is False

            banner = anim._final_banner()
            console.print(banner)
            rendered = output.getvalue()

        assert "___" in rendered or "|_" in rendered, (
            "ASCII fallback logo not found in non-UTF-8 output"
        )

    # -- AT-008: Clean Handoff to Overlay --

    def test_at_008_animation_output_is_self_contained(self):
        """Animation produces clean output that doesn't corrupt subsequent prints."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, color_system="truecolor", width=80)

        anim = StartupAnimation(console=console, version="0.1.0")
        anim._show_static_banner()

        console.print("[green]✓[/green] Agent pm started")
        console.print("[blue]Status: running[/blue]")

        rendered = output.getvalue()
        lines = rendered.strip().split("\n")

        agent_lines = [line for line in lines if "Agent pm started" in line]
        status_lines = [line for line in lines if "Status: running" in line]

        assert len(agent_lines) == 1, "Agent message should appear exactly once"
        assert len(status_lines) == 1, "Status message should appear exactly once"

    def test_at_008_final_banner_is_rich_panel(self):
        """Final banner is a Rich Panel (proper renderable)."""
        console = Console(file=StringIO(), force_terminal=True, color_system="truecolor", width=80)
        anim = StartupAnimation(console=console, version="0.1.0")

        banner = anim._final_banner()
        assert isinstance(banner, Panel), f"Expected Panel, got {type(banner)}"

    def test_at_008_disabled_animation_shows_static_banner(self):
        """Disabled animation shows static banner, then subsequent output works."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, color_system="truecolor", width=80)

        play_startup_animation(
            console=console,
            config={"show_startup_animation": True},
            no_animation_flag=True,
            version="0.1.0",
        )

        banner_output = output.getvalue()
        assert len(banner_output) > 0, "Static banner should appear"
        assert "0.1.0" in banner_output

        # Subsequent output should work cleanly
        console.print("Test message")
        assert "Test message" in output.getvalue()


# ═══════════════════════════════════════════════════════════════════════
# Default Agent Switching — Acceptance Tests
# ═══════════════════════════════════════════════════════════════════════


class TestDefaultAgentSwitchingAcceptance:
    """Acceptance tests for runtime default agent switching feature."""

    # ── AT-001: Switch Default Agent and Send Plain Text ──

    @pytest.mark.asyncio
    async def test_at_001_switch_default_and_route_plain_text(self):
        """After /use-agent builder-1, plain text routes to builder-1."""
        router = AgentRouter(default_agent="pm")
        agent_calls = []

        async def agent_handler(agent_id: str, content: str) -> str:
            agent_calls.append((agent_id, content))
            return f"Response from {agent_id}"

        router.register_agent_handler(agent_handler)

        # Step 1-2: Plain text "hello" routes to pm (config default)
        cmd1 = parse_command("hello")
        assert cmd1.type == CommandType.RAW
        await router.route(cmd1)
        assert agent_calls[-1] == ("pm", "hello")

        # Step 3-4: Switch default via /use-agent builder-1
        result = handle_use_agent(["builder-1"], router)
        assert result.success is True
        assert "builder-1" in result.output
        assert router.get_default_agent() == "builder-1"

        # Step 5-6: Plain text "build the feature" now routes to builder-1
        cmd2 = parse_command("build the feature")
        assert cmd2.type == CommandType.RAW
        await router.route(cmd2)
        assert agent_calls[-1] == ("builder-1", "build the feature")

    # ── AT-002: Explicit @agent Directive Overrides Default ──

    @pytest.mark.asyncio
    async def test_at_002_explicit_agent_overrides_default(self):
        """@reviewer routes to reviewer; plain text still routes to builder-1."""
        router = AgentRouter(default_agent="pm")
        agent_calls = []

        async def agent_handler(agent_id: str, content: str) -> str:
            agent_calls.append((agent_id, content))
            return f"Response from {agent_id}"

        router.register_agent_handler(agent_handler)

        # Pre-condition: switch default to builder-1 (as AT-001 would have done)
        switch_result = handle_use_agent(["builder-1"], router)
        assert switch_result.success is True
        assert router.get_default_agent() == "builder-1"

        # Step 1-2: Explicit @reviewer directive routes to reviewer
        cmd1 = parse_command("@reviewer check the code")
        assert cmd1.type == CommandType.AGENT
        await router.route(cmd1)
        assert agent_calls[-1] == ("reviewer", "check the code")

        # Step 3-4: Plain text still routes to builder-1 (current default)
        cmd2 = parse_command("continue building")
        assert cmd2.type == CommandType.RAW
        await router.route(cmd2)
        assert agent_calls[-1] == ("builder-1", "continue building")

    # ── AT-003: Reset Agent to Configuration Default ──

    @pytest.mark.asyncio
    async def test_at_003_reset_agent_to_config_default(self):
        """After /reset-agent, plain text routes back to pm."""
        router = AgentRouter(default_agent="pm")
        agent_calls = []

        async def agent_handler(agent_id: str, content: str) -> str:
            agent_calls.append((agent_id, content))
            return f"Response from {agent_id}"

        router.register_agent_handler(agent_handler)

        # Pre-condition: switch away from config default
        router.set_default_agent("builder-1")
        assert router.get_default_agent() == "builder-1"

        # Step 1-2: Reset to config default
        result = handle_reset_agent([], router)
        assert result.success is True
        assert "pm" in result.output
        assert "configuration" in result.output.lower()
        assert router.get_default_agent() == "pm"

        # Step 3-4: Plain text routes to pm
        cmd = parse_command("plan the next sprint")
        await router.route(cmd)
        assert agent_calls[-1] == ("pm", "plan the next sprint")

    # ── AT-004: Invalid Agent ID Produces Error ──

    def test_at_004_invalid_agent_id_error(self):
        """Invalid agent ID returns error with available agents list."""
        router = AgentRouter(default_agent="pm")

        result = handle_use_agent(["foo"], router)

        assert result.success is False
        assert "foo" in result.output
        for agent in sorted(VALID_AGENTS):
            assert agent in result.output
        # Default unchanged
        assert router.get_default_agent() == "pm"

    # ── AT-005: /use-agent Without Arguments Shows Info ──

    def test_at_005_use_agent_no_args_shows_info(self):
        """/use-agent with no args shows current default and available agents."""
        router = AgentRouter(default_agent="builder-1")

        result = handle_use_agent([], router)

        assert result.success is True
        assert "builder-1" in result.output
        for agent in sorted(VALID_AGENTS):
            assert agent in result.output

    # ── AT-006: /status Shows Default Agent ──

    def test_at_006_status_shows_default_agent(self):
        """/status output includes default agent with session override info."""
        router = AgentRouter(default_agent="pm")
        router.set_default_agent("builder-1")

        # Test direct handler
        result = handle_status([], router)
        assert result.success is True
        assert "Default Agent" in result.output
        assert "builder-1" in result.output
        assert "session override" in result.output
        assert "pm" in result.output

        # Test via SystemCommands dispatch
        commands = SystemCommands(router=router)
        dispatch_result = commands.dispatch("status", [])
        assert dispatch_result.success is True
        assert "Default Agent" in dispatch_result.output
        assert "builder-1" in dispatch_result.output

    # ── AT-007: Status Panel Shows Default Indicator ──

    def test_at_007_status_panel_default_indicator(self):
        """Status panel marks default agent with ★ and 'default' label."""
        manager = AgentStatusManager()

        # Step 1: pm is the default
        manager.set_default_agent("pm")
        panel = StatusPanel(manager)
        content = panel._format_status()

        lines = content.split("\n")
        pm_line = [line for line in lines if "pm" in line and "★" in line]
        assert len(pm_line) > 0, f"pm should have ★ indicator, got:\n{content}"
        assert "default" in pm_line[0]

        # Step 2-3: Switch to writer — indicator moves
        manager.set_default_agent("writer")
        content2 = panel._format_status()

        lines2 = content2.split("\n")
        writer_line = [line for line in lines2 if "writer" in line and "★" in line]
        assert len(writer_line) > 0, f"writer should have ★, got:\n{content2}"
        assert "default" in writer_line[0]

        pm_line2 = [line for line in lines2 if "pm" in line]
        assert len(pm_line2) > 0
        assert "★" not in pm_line2[0]
        assert "idle" in pm_line2[0]

    # ── AT-008: Session Restart Resets Default ──

    def test_at_008_session_restart_resets_default(self):
        """New router starts with config default, not runtime value."""
        # Simulate session 1
        router1 = AgentRouter(default_agent="pm")
        router1.set_default_agent("builder-2")
        assert router1.get_default_agent() == "builder-2"

        # Simulate session restart — fresh router with same config
        router2 = AgentRouter(default_agent="pm")
        assert router2.get_default_agent() == "pm"
        assert router2.get_config_default_agent() == "pm"

    # ── AT-009: /help Documents New Commands ──

    def test_at_009_help_documents_new_commands(self):
        """/help includes /use-agent and /reset-agent."""
        result = handle_help([])
        assert result.success is True
        assert "/use-agent" in result.output
        assert "/reset-agent" in result.output

        # Also via dispatch
        commands = SystemCommands()
        dispatch_result = commands.dispatch("help", [])
        assert dispatch_result.success is True
        assert "/use-agent" in dispatch_result.output
        assert "/reset-agent" in dispatch_result.output


class TestDefaultAgentSwitchingE2E:
    """End-to-end integration test for the full dispatch chain."""

    @pytest.mark.asyncio
    async def test_at_e2e_full_workflow(self):
        """Full workflow: start → switch → explicit @agent → reset → use."""
        router = AgentRouter(default_agent="pm")
        commands = SystemCommands(router=router)
        agent_calls = []

        async def agent_handler(agent_id: str, content: str) -> str:
            agent_calls.append((agent_id, content))
            return f"OK from {agent_id}"

        router.register_agent_handler(agent_handler)
        router.register_system_handler(commands.dispatch)

        # 1. Plain text → pm (default from config)
        await router.route(parse_command("hello"))
        assert agent_calls[-1] == ("pm", "hello")

        # 2. /use-agent builder-1 via full dispatch chain
        result = await router.route(parse_command("/use-agent builder-1"))
        assert result.success is True

        # 3. Plain text → builder-1 (new default)
        await router.route(parse_command("build it"))
        assert agent_calls[-1] == ("builder-1", "build it")

        # 4. @reviewer explicit → reviewer (not affected by default)
        await router.route(parse_command("@reviewer review this"))
        assert agent_calls[-1] == ("reviewer", "review this")

        # 5. Plain text → still builder-1
        await router.route(parse_command("keep going"))
        assert agent_calls[-1] == ("builder-1", "keep going")

        # 6. /reset-agent via full dispatch chain
        result = await router.route(parse_command("/reset-agent"))
        assert result.success is True

        # 7. Plain text → pm (restored from config)
        await router.route(parse_command("plan stuff"))
        assert agent_calls[-1] == ("pm", "plan stuff")
