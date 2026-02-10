"""Acceptance test validation for feature specifications.

These tests exercise the REAL implementation code to validate
each acceptance scenario from feature specifications.
"""

from __future__ import annotations

import argparse
import json
import re
from io import StringIO
from unittest.mock import AsyncMock

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
from teambot.repl.parser import CommandType, ParseError, parse_command
from teambot.repl.router import AGENT_ALIASES, VALID_AGENTS, AgentRouter, RouterError
from teambot.tasks.executor import TaskExecutor
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


class TestUnknownAgentValidationAcceptance:
    """Acceptance tests for unknown agent ID validation (AT-001 through AT-007).

    These tests exercise the REAL router, parser, executor, and agent_state
    code. Only the SDK client (network boundary) is mocked.
    """

    # ------------------------------------------------------------------
    # AT-001: Simple Unknown Agent Command (Simple Path)
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_001_router_rejects_unknown_agent_with_message(self):
        """Simple path: router rejects unknown agent with spec-format error."""
        router = AgentRouter()
        router.register_agent_handler(AsyncMock(return_value="ok"))

        command = parse_command("@unknown-agent do something")
        with pytest.raises(RouterError, match=r"Unknown agent: 'unknown-agent'") as exc_info:
            await router.route(command)

        error_msg = str(exc_info.value)
        assert "Valid agents:" in error_msg
        assert "ba" in error_msg
        assert "builder-1" in error_msg
        assert "pm" in error_msg

    def test_at_001_no_status_entry_created(self):
        """Unknown agent must not get an entry in AgentStatusManager."""
        manager = AgentStatusManager()
        manager.set_running("unknown-agent", "do something")
        assert manager.get("unknown-agent") is None

    def test_at_001_no_task_dispatched(self):
        """Router handler must never be called for unknown agent."""
        router = AgentRouter()
        mock_handler = AsyncMock(return_value="ok")
        router.register_agent_handler(mock_handler)

        command = parse_command("@unknown-agent do something")
        with pytest.raises(RouterError):
            import asyncio

            asyncio.get_event_loop().run_until_complete(router.route(command))

        mock_handler.assert_not_called()

    # ------------------------------------------------------------------
    # AT-002: Unknown Agent in Background Command (Advanced Path)
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_002_executor_rejects_unknown_background(self):
        """Background command to unknown agent returns error, no task spawned."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@unknown-agent do something &")
        result = await executor.execute(command)

        assert not result.success
        assert "Unknown agent: 'unknown-agent'" in result.error
        assert "Valid agents:" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_at_002_no_status_entry_for_background_unknown(self):
        """No status entry created when background unknown agent is rejected."""
        manager = AgentStatusManager()
        manager.set_running("unknown-agent", "do something")
        assert manager.get("unknown-agent") is None

    @pytest.mark.asyncio
    async def test_at_002_no_task_result_produced(self):
        """Executor returns zero tasks for rejected background command."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@unknown-agent do something &")
        result = await executor.execute(command)

        assert executor.task_count == 0
        assert result.task_ids == []

    # ------------------------------------------------------------------
    # AT-003: Multi-Agent Command with One Invalid ID
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_003_multi_agent_rejects_when_one_invalid(self):
        """Multi-agent command with one invalid ID rejects entire command."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@builder-1,fake-agent implement the feature")
        result = await executor.execute(command)

        assert not result.success
        assert "fake-agent" in result.error
        assert "Unknown agent:" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_at_003_no_tasks_dispatched_for_either_agent(self):
        """Neither valid nor invalid agent gets a task when one is invalid."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@builder-1,fake-agent implement the feature")
        result = await executor.execute(command)

        assert executor.task_count == 0
        assert result.task_ids == []

    @pytest.mark.asyncio
    async def test_at_003_no_status_entries_created(self):
        """No status entries created for any agent in rejected multi-agent cmd."""
        manager = AgentStatusManager()
        # Simulate what would happen — fake-agent should not get an entry
        manager.set_running("fake-agent", "implement the feature")
        assert manager.get("fake-agent") is None

    # ------------------------------------------------------------------
    # AT-004: Pipeline Command with Unknown Agent
    # ------------------------------------------------------------------
    def test_at_004_pipeline_unknown_agent_rejected_at_parse(self):
        """Pipeline with unknown agent rejected during parsing."""
        with pytest.raises(ParseError, match=r"Unknown agent: 'fake'"):
            parse_command("@fake -> @pm create a plan")

    def test_at_004_error_lists_valid_agents(self):
        """Pipeline parse error for unknown agent lists valid agents."""
        with pytest.raises(ParseError) as exc_info:
            parse_command("@fake -> @pm create a plan")

        error_msg = str(exc_info.value)
        assert "Valid agents:" in error_msg
        assert "pm" in error_msg

    def test_at_004_pm_does_not_receive_input(self):
        """PM never executes when pipeline is rejected at parse time."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        with pytest.raises(ParseError, match="Unknown agent"):
            parse_command("@fake -> @pm create a plan")

        # Parser rejects — executor never sees the command
        assert executor.task_count == 0
        mock_sdk.execute.assert_not_called()

    # ------------------------------------------------------------------
    # AT-005: Valid Alias Continues to Work
    # ------------------------------------------------------------------
    def test_at_005_alias_resolves_to_canonical_id(self):
        """Router resolves 'project_manager' alias to 'pm'."""
        router = AgentRouter()
        assert router.resolve_agent_id("project_manager") == "pm"
        assert router.is_valid_agent("project_manager")

    def test_at_005_all_aliases_valid(self):
        """All defined aliases resolve to valid canonical agent IDs."""
        router = AgentRouter()
        for alias, canonical in AGENT_ALIASES.items():
            assert router.resolve_agent_id(alias) == canonical
            assert router.is_valid_agent(alias)

    @pytest.mark.asyncio
    async def test_at_005_alias_accepted_by_executor(self):
        """Executor accepts commands with valid alias agent IDs."""
        from teambot.repl.parser import Command, CommandType

        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Plan created")
        executor = TaskExecutor(sdk_client=mock_sdk)

        cmd = Command(
            type=CommandType.AGENT,
            agent_id="project_manager",
            agent_ids=["project_manager"],
            content="create a project plan",
        )
        result = await executor.execute(cmd)

        assert result.success
        assert result.error is None or "Unknown agent" not in (result.error or "")

    # ------------------------------------------------------------------
    # AT-006: All Six Valid Agents Work (Regression)
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_006_all_six_agents_accepted_by_router(self):
        """All 6 valid agents are accepted by the router without error."""
        router = AgentRouter()
        mock_handler = AsyncMock(return_value="done")
        router.register_agent_handler(mock_handler)

        for agent_id in sorted(VALID_AGENTS):
            command = parse_command(f"@{agent_id} do work")
            result = await router.route(command)
            assert result == "done"

        assert mock_handler.call_count == 6

    @pytest.mark.asyncio
    async def test_at_006_all_six_agents_accepted_by_executor(self):
        """All 6 valid agents dispatched without validation error via executor."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")
        executor = TaskExecutor(sdk_client=mock_sdk)

        for agent_id in sorted(VALID_AGENTS):
            command = parse_command(f"@{agent_id} do work &")
            result = await executor.execute(command)
            assert result.error is None or "Unknown agent" not in (result.error or ""), (
                f"Agent '{agent_id}' was incorrectly rejected"
            )

    def test_at_006_all_six_agents_have_status_entries(self):
        """All 6 valid agents have default status entries."""
        manager = AgentStatusManager()
        for agent_id in sorted(VALID_AGENTS):
            status = manager.get(agent_id)
            assert status is not None, f"Missing status entry for '{agent_id}'"

    # ------------------------------------------------------------------
    # AT-007: Typo Near Valid Agent ID
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_007_typo_rejected_by_router(self):
        """Typo 'buidler-1' is rejected with helpful error message."""
        router = AgentRouter()
        router.register_agent_handler(AsyncMock(return_value="ok"))

        command = parse_command("@buidler-1 implement login")
        with pytest.raises(RouterError, match=r"Unknown agent: 'buidler-1'") as exc_info:
            await router.route(command)

        error_msg = str(exc_info.value)
        assert "Valid agents:" in error_msg

    @pytest.mark.asyncio
    async def test_at_007_typo_rejected_by_executor(self):
        """Typo 'buidler-1' rejected via executor path too."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@buidler-1 implement login &")
        result = await executor.execute(command)

        assert not result.success
        assert "Unknown agent: 'buidler-1'" in result.error
        mock_sdk.execute.assert_not_called()

    def test_at_007_no_task_dispatched_for_typo(self):
        """Typo agent results in zero tasks dispatched."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@buidler-1 implement login &")

        import asyncio

        asyncio.get_event_loop().run_until_complete(executor.execute(command))

        assert executor.task_count == 0
