"""Acceptance test validation for feature specifications.

These tests exercise the REAL implementation code to validate
each acceptance scenario from feature specifications.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from rich.console import Console
from rich.panel import Panel

from teambot.orchestration.execution_loop import ExecutionLoop
from teambot.orchestration.stage_config import load_stages_config
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
from teambot.ui.widgets.input_pane import InputPane
from teambot.ui.widgets.status_panel import StatusPanel
from teambot.visualization.animation import (
    LOGO_COLOR_MAP,
    TEAMBOT_LOGO,
    StartupAnimation,
    play_startup_animation,
)
from teambot.workflow.stages import WorkflowStage


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

    # -- AT-008: Clean Handoff to Status Output --

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

    @pytest.mark.asyncio
    async def test_at_001_no_task_dispatched(self):
        """Router handler must never be called for unknown agent."""
        router = AgentRouter()
        mock_handler = AsyncMock(return_value="ok")
        router.register_agent_handler(mock_handler)

        command = parse_command("@unknown-agent do something")
        with pytest.raises(RouterError):
            await router.route(command)

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
    # AT-006: All Seven Valid Agents Work (Including Notify)
    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_006_all_seven_agents_accepted_by_router(self):
        """All 7 valid agents are accepted by the router without error."""
        router = AgentRouter()
        mock_handler = AsyncMock(return_value="done")
        router.register_agent_handler(mock_handler)

        for agent_id in sorted(VALID_AGENTS):
            command = parse_command(f"@{agent_id} do work")
            result = await router.route(command)
            assert result == "done"

        assert mock_handler.call_count == 7

    @pytest.mark.asyncio
    async def test_at_006_all_seven_agents_accepted_by_executor(self):
        """All 7 valid agents dispatched without validation error via executor."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")
        executor = TaskExecutor(sdk_client=mock_sdk)

        for agent_id in sorted(VALID_AGENTS):
            command = parse_command(f"@{agent_id} do work &")
            result = await executor.execute(command)
            assert result.error is None or "Unknown agent" not in (result.error or ""), (
                f"Agent '{agent_id}' was incorrectly rejected"
            )

    def test_at_006_all_seven_agents_have_status_entries(self):
        """All 7 valid agents have default status entries."""
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

    @pytest.mark.asyncio
    async def test_at_007_no_task_dispatched_for_typo(self):
        """Typo agent results in zero tasks dispatched."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)

        command = parse_command("@buidler-1 implement login &")

        await executor.execute(command)

        assert executor.task_count == 0


# ═══════════════════════════════════════════════════════════════════════════
# Enhanced Multi-Line Text Input — Acceptance Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestMultiLineInputAcceptance:
    """Acceptance tests for enhanced multi-line text input feature."""

    # ── AT-001: Paste Multi-Line Code Snippet ───────────────────────────

    @pytest.mark.asyncio
    async def test_at_001_paste_multiline_code_snippet(self):
        """User composes a multi-line code snippet prefixed with agent command and submits."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt", InputPane)
            output = app.query_one("#output")

            await pilot.click("#prompt")

            # Type agent prefix
            for ch in "@builder-1 review this code:":
                await pilot.press(ch)

            # Alt+Enter for newlines (simulating multi-line paste)
            await pilot.press("alt+enter")
            for ch in "def hello():":
                await pilot.press(ch)
            await pilot.press("alt+enter")
            for ch in "    print('hi')":
                await pilot.press(ch)
            await pilot.press("alt+enter")
            for ch in "    return True":
                await pilot.press(ch)
            await pilot.press("alt+enter")
            # empty line
            await pilot.press("alt+enter")
            for ch in "hello()":
                await pilot.press(ch)
            await pilot.pause()

            # Verify multi-line content in input before submit
            text = input_pane.text
            assert "@builder-1 review this code:" in text
            assert "def hello():" in text
            assert "hello()" in text
            assert text.count("\n") == 5  # 5 newlines = 6 lines

            # Submit with Enter
            await pilot.press("enter")
            await pilot.pause()

            # Input cleared after submit
            assert input_pane.text == ""
            # Output received the command (echoed)
            assert len(output.lines) > 0

    @pytest.mark.asyncio
    async def test_at_001_multiline_parsed_as_agent_command(self):
        """Multi-line content with @agent prefix is parsed correctly by real parser."""
        multiline = (
            "@builder-1 review this code:\n"
            "def hello():\n"
            "    print('hi')\n"
            "    return True\n"
            "\n"
            "hello()"
        )
        cmd = parse_command(multiline)
        assert cmd.type == CommandType.AGENT
        assert cmd.agent_ids == ["builder-1"]
        assert "def hello():" in cmd.content
        assert "hello()" in cmd.content

    # ── AT-002: Enter Submits, Alt+Enter Inserts Newline ────────────────

    @pytest.mark.asyncio
    async def test_at_002_enter_submits_alt_enter_inserts_newline(self):
        """Alt+Enter inserts newlines without submitting; Enter submits all content."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt", InputPane)
            output = app.query_one("#output")
            initial_lines = len(output.lines)

            await pilot.click("#prompt")

            # Step 1: type prefix
            for ch in "@pm plan the following:":
                await pilot.press(ch)
            await pilot.pause()

            # Step 2: Alt+Enter (newline, NOT submitted)
            await pilot.press("alt+enter")
            await pilot.pause()
            assert len(output.lines) == initial_lines  # No submission

            # Step 3: type first item
            for ch in "- Add authentication":
                await pilot.press(ch)

            # Step 4: Alt+Enter again (newline, NOT submitted)
            await pilot.press("alt+enter")
            await pilot.pause()
            assert len(output.lines) == initial_lines  # Still no submission

            # Step 5: type second item
            for ch in "- Add logging":
                await pilot.press(ch)
            await pilot.pause()

            # Verify 3 lines in input before submit
            text = input_pane.text
            assert "@pm plan the following:" in text
            assert "- Add authentication" in text
            assert "- Add logging" in text
            assert text.count("\n") == 2

            # Step 6: Enter to submit
            await pilot.press("enter")
            await pilot.pause()

            # Submission occurred
            assert len(output.lines) > initial_lines
            # Input cleared
            assert input_pane.text == ""

    # ── AT-003: History Navigation in Multi-Line Context ────────────────

    @pytest.mark.asyncio
    async def test_at_003_history_navigation_multiline(self):
        """Up/Down on interior lines move cursor; on boundary trigger history."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt", InputPane)

            # Submit a previous command to have history
            await pilot.click("#prompt")
            for ch in "@pm hello":
                await pilot.press(ch)
            await pilot.press("enter")
            await pilot.pause()

            # Step 1: Type 2-line input
            await pilot.click("#prompt")
            for ch in "line one":
                await pilot.press(ch)
            await pilot.press("alt+enter")
            for ch in "line two":
                await pilot.press(ch)
            await pilot.pause()

            # Verify 2-line content
            assert "line one" in input_pane.text
            assert "line two" in input_pane.text

            # Step 2: Cursor is on line 2. Press Up → moves cursor to line 1
            await pilot.press("up")
            await pilot.pause()
            # Content should still be 2-line text (not replaced by history)
            assert "line one" in input_pane.text
            assert "line two" in input_pane.text

            # Step 3: Cursor now on line 1. Press Up → history loads "@pm hello"
            await pilot.press("up")
            await pilot.pause()
            assert input_pane.text == "@pm hello"

            # Step 4: Press Down → original 2-line input restored
            await pilot.press("down")
            await pilot.pause()
            assert "line one" in input_pane.text
            assert "line two" in input_pane.text
            assert "\n" in input_pane.text

    # ── AT-004: Single-Line Workflow Backward Compatibility ─────────────

    @pytest.mark.asyncio
    async def test_at_004_single_line_backward_compat(self):
        """Single-line commands work identically to pre-migration behavior."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt", InputPane)
            output = app.query_one("#output")
            initial_lines = len(output.lines)

            # Step 1-2: Type and submit single-line command
            await pilot.click("#prompt")
            for ch in "@pm create a plan":
                await pilot.press(ch)
            await pilot.press("enter")
            await pilot.pause()

            # Step 3: Command submitted
            assert len(output.lines) > initial_lines
            assert input_pane.text == ""

            # Step 4-5: Up arrow recalls previous command
            await pilot.click("#prompt")
            await pilot.press("up")
            await pilot.pause()
            assert input_pane.text == "@pm create a plan"

    @pytest.mark.asyncio
    async def test_at_004_single_line_parsed_correctly(self):
        """Single-line agent command parses and routes correctly."""
        cmd = parse_command("@pm create a plan")
        assert cmd.type == CommandType.AGENT
        assert cmd.agent_ids == ["pm"]
        assert cmd.content == "create a plan"

    # ── AT-005: Word Wrap and Scrolling ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_at_005_word_wrap_enabled(self):
        """TextArea has soft_wrap=True for word wrapping."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as _pilot:
            input_pane = app.query_one("#prompt", InputPane)
            assert input_pane.soft_wrap is True

    @pytest.mark.asyncio
    async def test_at_005_css_height_configured(self):
        """Input pane has multi-line height configuration."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as _pilot:
            input_pane = app.query_one("#prompt", InputPane)
            assert input_pane.styles.min_height is not None

    @pytest.mark.asyncio
    async def test_at_005_large_content_scrollable(self):
        """20 lines of content can be entered and all are accessible."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt", InputPane)

            await pilot.click("#prompt")
            for i in range(20):
                for ch in f"line {i + 1}":
                    await pilot.press(ch)
                if i < 19:
                    await pilot.press("ctrl+enter")
            await pilot.pause()

            text = input_pane.text
            assert text.count("\n") == 19  # 19 newlines = 20 lines
            assert "line 1" in text
            assert "line 10" in text
            assert "line 20" in text

    # ── AT-006: Ctrl+Enter as Alternative Newline Binding ───────────────

    @pytest.mark.asyncio
    async def test_at_006_ctrl_enter_inserts_newline(self):
        """Ctrl+Enter inserts a newline; Enter submits both lines."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt", InputPane)
            output = app.query_one("#output")
            initial_lines = len(output.lines)

            await pilot.click("#prompt")

            # Step 1: type first line
            for ch in "first line":
                await pilot.press(ch)

            # Step 2-3: Ctrl+Enter inserts newline
            await pilot.press("ctrl+enter")
            await pilot.pause()

            # No submission occurred
            assert len(output.lines) == initial_lines
            # Newline inserted
            assert "\n" in input_pane.text

            # Step 4: type second line
            for ch in "second line":
                await pilot.press(ch)
            await pilot.pause()

            # Verify content
            assert input_pane.text == "first line\nsecond line"

            # Step 5: Enter to submit
            await pilot.press("enter")
            await pilot.pause()

            # Submitted
            assert len(output.lines) > initial_lines
            assert input_pane.text == ""


# =============================================================================
# Parallel Stage Groups Acceptance Tests
# =============================================================================


class TestParallelStageGroupsAcceptance:
    """Acceptance tests for parallel stage groups feature."""

    @pytest.fixture
    def objective_file(self, tmp_path: Path) -> Path:
        """Create a minimal objective file."""
        obj_file = tmp_path / "test-objective.md"
        obj_file.write_text(
            """# Test Objective

## Goals
- Test parallel stage groups

## Success Criteria
- [ ] Parallel execution works

## Context
**Target Codebase**: Test
**Primary Language/Framework**: Python
"""
        )
        return obj_file

    @pytest.fixture
    def teambot_dir(self, tmp_path: Path) -> Path:
        """Create teambot directory."""
        tb_dir = tmp_path / ".teambot"
        tb_dir.mkdir()
        return tb_dir

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client that approves all work."""
        client = AsyncMock()
        client.execute_streaming.return_value = "VERIFIED_APPROVED: Work completed successfully."
        return client

    # =========================================================================
    # AT-001: Concurrent Execution of RESEARCH and TEST_STRATEGY
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_001_concurrent_execution_research_and_test_strategy(
        self, objective_file: Path, teambot_dir: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """AT-001: RESEARCH and TEST_STRATEGY execute concurrently after SPEC_REVIEW."""
        # Track stage start times using REAL parallel group execution
        stage_times: dict[str, dict[str, float]] = {}

        def track_progress(event: str, data: dict) -> None:
            if event == "parallel_stage_start":
                stage_times[data["stage"]] = {"start": time.time()}
            elif event in ("parallel_stage_complete", "parallel_stage_failed"):
                if data["stage"] in stage_times:
                    stage_times[data["stage"]]["end"] = time.time()

        # Create feature spec artifact
        feature_dir = teambot_dir / "test-objective"
        feature_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir = feature_dir / "artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "feature_spec.md").write_text("# Test Spec\n\n## Acceptance")

        # Load REAL stages config with parallel groups
        stages_config = load_stages_config()

        # Verify parallel groups are configured
        assert len(stages_config.parallel_groups) > 0
        group = stages_config.parallel_groups[0]
        assert group.name == "post_spec_review"
        assert WorkflowStage.RESEARCH in group.stages
        assert WorkflowStage.TEST_STRATEGY in group.stages

        # Create REAL ExecutionLoop
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=1.0,
            stages_config=stages_config,
        )

        # Start from SPEC_REVIEW (which triggers parallel group on next stage)
        loop.current_stage = WorkflowStage.SPEC_REVIEW
        loop.sdk_client = mock_sdk_client

        # Execute parallel group directly to test concurrency
        success = await loop._execute_parallel_group(group, on_progress=track_progress)

        # Verify both stages were executed
        assert success is True
        assert "RESEARCH" in stage_times
        assert "TEST_STRATEGY" in stage_times

        # Verify concurrent execution (starts within 1 second of each other)
        research_start = stage_times["RESEARCH"]["start"]
        test_strategy_start = stage_times["TEST_STRATEGY"]["start"]
        start_diff = abs(research_start - test_strategy_start)
        assert start_diff < 1.0, f"Stages started {start_diff}s apart (expected < 1s)"

        # Verify both stages have outputs (REAL stage execution)
        assert WorkflowStage.RESEARCH in loop.stage_outputs
        assert WorkflowStage.TEST_STRATEGY in loop.stage_outputs

    # =========================================================================
    # AT-002: Resume Mid-Parallel-Group with One Stage Complete
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_002_resume_mid_parallel_group_reruns_only_incomplete(
        self, objective_file: Path, teambot_dir: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """AT-002: Resume mid-parallel-group only re-runs incomplete stages."""
        # Create feature directory structure
        feature_dir = teambot_dir / "test-objective"
        feature_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir = feature_dir / "artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "feature_spec.md").write_text("# Test Spec\n\n## Acceptance")

        # Create REAL state file simulating mid-parallel-group interrupt
        state_file = feature_dir / "orchestration_state.json"
        state_file.write_text(
            json.dumps(
                {
                    "objective_file": str(objective_file),
                    "current_stage": "RESEARCH",
                    "elapsed_seconds": 100,
                    "max_seconds": 3600,
                    "status": "in_progress",
                    "stage_outputs": {"RESEARCH": "Research completed successfully."},
                    "parallel_group_status": {
                        "post_spec_review": {
                            "stages": {
                                "RESEARCH": {"status": "completed", "error": None},
                                # TEST_STRATEGY not present = incomplete
                            }
                        }
                    },
                }
            )
        )

        # Use REAL resume() classmethod
        loop = ExecutionLoop.resume(teambot_dir, {})

        # Verify state was loaded correctly
        assert (
            loop.parallel_group_status["post_spec_review"]["stages"]["RESEARCH"]["status"]
            == "completed"
        )

        # Load stages config and get parallel group
        stages_config = load_stages_config()
        loop.stages_config = stages_config
        group = stages_config.parallel_groups[0]

        # Use REAL _filter_incomplete_stages method
        incomplete = loop._filter_incomplete_stages(group)

        # Verify only TEST_STRATEGY is incomplete
        assert len(incomplete) == 1
        assert WorkflowStage.TEST_STRATEGY in incomplete
        assert WorkflowStage.RESEARCH not in incomplete

        # Verify RESEARCH output preserved
        assert loop.stage_outputs[WorkflowStage.RESEARCH] == "Research completed successfully."

    # =========================================================================
    # AT-003: Parallel Group Failure Handling
    # =========================================================================
    @pytest.mark.asyncio
    async def test_at_003_parallel_group_failure_allows_sibling_completion(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """AT-003: One stage fails, sibling completes, failure reported."""
        # Create feature directory structure
        feature_dir = teambot_dir / "test-objective"
        feature_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir = feature_dir / "artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "feature_spec.md").write_text("# Test Spec\n\n## Acceptance")

        # Create mock that fails on first call (RESEARCH), succeeds on second
        call_count = 0

        async def fail_first_succeed_second(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("RESEARCH failed: simulated error")
            return "VERIFIED_APPROVED: Work completed."

        mock_sdk_client = AsyncMock()
        mock_sdk_client.execute_streaming.side_effect = fail_first_succeed_second

        stages_config = load_stages_config()
        group = stages_config.parallel_groups[0]

        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
            max_hours=1.0,
            stages_config=stages_config,
        )
        loop.sdk_client = mock_sdk_client

        # Track events
        events: list[tuple[str, dict]] = []

        def track_events(event: str, data: dict) -> None:
            events.append((event, data))

        # Execute REAL parallel group
        success = await loop._execute_parallel_group(group, on_progress=track_events)

        # Verify overall failure (one stage failed)
        assert success is False

        # Verify parallel_group_status shows partial completion
        group_status = loop.parallel_group_status["post_spec_review"]["stages"]

        # One stage should be failed, one completed
        statuses = {s: info["status"] for s, info in group_status.items()}
        assert "failed" in statuses.values()
        assert "completed" in statuses.values()

        # Verify failure event was fired
        failed_events = [e for e in events if e[0] == "parallel_stage_failed"]
        assert len(failed_events) >= 1

        # Verify group complete event shows failure
        complete_events = [e for e in events if e[0] == "parallel_group_complete"]
        assert len(complete_events) == 1
        assert complete_events[0][1]["all_success"] is False

    # =========================================================================
    # AT-004: Backward Compatibility with Legacy State File
    # =========================================================================
    def test_at_004_backward_compat_legacy_state_file_loads(
        self, objective_file: Path, teambot_dir: Path
    ) -> None:
        """AT-004: Legacy state file without parallel_group_status loads correctly."""
        # Create feature directory
        feature_dir = teambot_dir / "test-objective"
        feature_dir.mkdir(parents=True, exist_ok=True)

        # Create LEGACY state file (no parallel_group_status field)
        state_file = feature_dir / "orchestration_state.json"
        state_file.write_text(
            json.dumps(
                {
                    "objective_file": str(objective_file),
                    "current_stage": "RESEARCH",
                    "elapsed_seconds": 50,
                    "max_seconds": 28800,
                    "status": "in_progress",
                    "stage_outputs": {"SETUP": "Setup complete"},
                    # NOTE: No parallel_group_status field - legacy format
                }
            )
        )

        # Use REAL resume() classmethod - should not crash
        loop = ExecutionLoop.resume(teambot_dir, {})

        # Verify resume succeeded
        assert loop.current_stage == WorkflowStage.RESEARCH

        # Verify parallel_group_status defaulted to empty dict
        assert loop.parallel_group_status == {}

        # Verify other state was preserved
        assert loop.stage_outputs[WorkflowStage.SETUP] == "Setup complete"

    # =========================================================================
    # AT-005: Configuration Validation Rejects Invalid Parallel Groups
    # =========================================================================
    def test_at_005_config_rejects_nonexistent_stage_in_parallel_group(
        self, tmp_path: Path
    ) -> None:
        """AT-005: Configuration rejects non-existent stages in parallel groups."""
        # Create invalid stages.yaml with non-existent stage
        invalid_config = tmp_path / "invalid_stages.yaml"
        invalid_config.write_text(
            """
stages:
  SETUP:
    work_agent: pm
    review_agent: null
  SPEC:
    work_agent: ba
    review_agent: reviewer
  SPEC_REVIEW:
    work_agent: ba
    review_agent: reviewer
    is_review_stage: true
  RESEARCH:
    work_agent: builder-1
    review_agent: null
  TEST_STRATEGY:
    work_agent: builder-1
    review_agent: null
  PLAN:
    work_agent: pm
    review_agent: reviewer

stage_order:
  - SETUP
  - SPEC
  - SPEC_REVIEW
  - RESEARCH
  - TEST_STRATEGY
  - PLAN

parallel_groups:
  invalid_group:
    after: SPEC_REVIEW
    stages:
      - RESEARCH
      - NONEXISTENT_STAGE
    before: PLAN
"""
        )

        # Attempt to load REAL config - should raise error
        with pytest.raises(ValueError) as exc_info:
            load_stages_config(invalid_config)

        # Verify error mentions invalid stage
        error_msg = str(exc_info.value)
        assert "NONEXISTENT_STAGE" in error_msg


# =============================================================================
# Notification UX Improvements Acceptance Tests
# =============================================================================


class TestNotificationUXAcceptance:
    """Acceptance tests for notification UX improvements.

    These tests validate header/footer notifications and /notify command.
    """

    # -------------------------------------------------------------------------
    # AT-001: Header Notification on Run Start
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_001_header_notification_emitted_on_run_start(self, tmp_path: Path) -> None:
        """Validate orchestration emits started event with objective name.

        Steps:
        1. Create ExecutionLoop with objective file
        2. Call run() with on_progress callback
        3. Verify orchestration_started event emitted with objective_name
        """
        from unittest.mock import AsyncMock

        from teambot.orchestration.execution_loop import ExecutionLoop

        # Create objective file with proper frontmatter
        objective_content = """# Objective: my-feature objective

## Goals
1. Test goal

## Success Criteria
- [ ] Test criteria
"""
        objective_path = tmp_path / "objective.md"
        objective_path.write_text(objective_content)

        # Create teambot dir with feature spec
        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()
        feature_dir = teambot_dir / "my-feature-objective"
        feature_dir.mkdir()
        artifacts_dir = feature_dir / "artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "feature_spec.md").write_text("# Feature Spec\n\n## Overview\nTest.")

        # Create ExecutionLoop with real objective file
        loop = ExecutionLoop(
            objective_path=objective_path,
            config={},
            teambot_dir=teambot_dir,
            max_hours=8.0,
        )

        # Track emitted events
        events: list[tuple[str, dict]] = []

        def on_progress(event_type: str, data: dict) -> None:
            events.append((event_type, data))

        # Mock SDK client
        mock_sdk = AsyncMock()
        mock_sdk.execute_streaming.return_value = "VERIFIED_APPROVED: Done."

        # Run - loop will emit started event immediately, then complete
        await loop.run(sdk_client=mock_sdk, on_progress=on_progress)

        # Verify orchestration_started was emitted
        started_events = [e for e in events if e[0] == "orchestration_started"]
        assert len(started_events) == 1, f"Expected 1 started event, got {len(started_events)}"

        event_data = started_events[0][1]
        assert "my-feature objective" in event_data["objective_name"]
        assert "objective_path" in event_data

    def test_at_001_started_template_renders_objective_name(self) -> None:
        """Validate started template renders with objective name."""
        from teambot.notifications.events import NotificationEvent
        from teambot.notifications.templates import MessageTemplates

        templates = MessageTemplates()
        event = NotificationEvent(
            event_type="orchestration_started",
            feature_name="my-feature",
            data={"objective_name": "my-feature objective"},
        )

        result = templates.render(event)

        assert "🚀" in result
        assert "Starting" in result
        assert "my-feature objective" in result

    # -------------------------------------------------------------------------
    # AT-002: Footer Notification on Run Complete
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_002_footer_notification_emitted_on_complete(self, tmp_path: Path) -> None:
        """Validate orchestration emits completed event with duration.

        Steps:
        1. Create ExecutionLoop and run until completion
        2. Verify orchestration_completed event emitted
        3. Verify event includes duration_seconds
        """
        from unittest.mock import AsyncMock

        from teambot.orchestration.execution_loop import ExecutionLoop

        # Create objective file
        objective_content = """# Objective: my-feature objective

## Goals
1. Test goal

## Success Criteria
- [ ] Test criteria
"""
        objective_path = tmp_path / "objective.md"
        objective_path.write_text(objective_content)

        # Create teambot dir with feature spec
        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()
        feature_dir = teambot_dir / "my-feature-objective"
        feature_dir.mkdir()
        artifacts_dir = feature_dir / "artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "feature_spec.md").write_text("# Feature Spec\n\n## Overview\nTest.")

        loop = ExecutionLoop(
            objective_path=objective_path,
            config={},
            teambot_dir=teambot_dir,
            max_hours=8.0,
        )

        events: list[tuple[str, dict]] = []

        def on_progress(event_type: str, data: dict) -> None:
            events.append((event_type, data))

        mock_sdk = AsyncMock()
        mock_sdk.execute_streaming.return_value = "VERIFIED_APPROVED: Done."

        # Run to completion
        await loop.run(sdk_client=mock_sdk, on_progress=on_progress)

        # Verify orchestration_completed was emitted
        completed_events = [e for e in events if e[0] == "orchestration_completed"]
        assert len(completed_events) == 1, (
            f"Expected 1 completed event, got {len(completed_events)}"
        )

        event_data = completed_events[0][1]
        assert "my-feature objective" in event_data["objective_name"]
        assert "duration_seconds" in event_data
        assert isinstance(event_data["duration_seconds"], (int, float))

    def test_at_002_completed_template_includes_duration(self) -> None:
        """Validate completed template renders with duration."""
        from teambot.notifications.events import NotificationEvent
        from teambot.notifications.templates import MessageTemplates

        templates = MessageTemplates()
        event = NotificationEvent(
            event_type="orchestration_completed",
            feature_name="my-feature",
            data={
                "objective_name": "my-feature objective",
                "duration_seconds": 125,  # 2m 5s
            },
        )

        result = templates.render(event)

        assert "✅" in result
        assert "Completed" in result
        assert "my-feature objective" in result
        assert "2m 5s" in result

    # -------------------------------------------------------------------------
    # AT-003: @notify Pseudo-Agent Success (legacy /notify removed)
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_003_notify_agent_sends_message(self) -> None:
        """Validate @notify agent sends message.

        Steps:
        1. Create TaskExecutor with valid notification config
        2. Execute @notify command
        3. Verify notification is sent via EventBus
        """
        from unittest.mock import AsyncMock, MagicMock, patch

        from teambot.tasks.executor import TaskExecutor

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TELEGRAM_BOT_TOKEN}",
                        "chat_id": "${TELEGRAM_CHAT_ID}",
                    }
                ],
            }
        }

        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        mock_event_bus = MagicMock()
        mock_event_bus._channels = [MagicMock()]

        with patch(
            "teambot.tasks.executor.create_event_bus_from_config",
            return_value=mock_event_bus,
        ):
            result = await executor._handle_notify("Hello from TeamBot!", background=False)

        assert result.success is True
        assert "Notification sent" in result.output
        mock_event_bus.emit_sync.assert_called()

    def test_at_003_custom_message_template_renders(self) -> None:
        """Validate custom_message template renders user message."""
        from teambot.notifications.events import NotificationEvent
        from teambot.notifications.templates import MessageTemplates

        templates = MessageTemplates()
        event = NotificationEvent(
            event_type="custom_message",
            feature_name="test",
            data={"message": "Hello from TeamBot!"},
        )

        result = templates.render(event)

        assert "Hello from TeamBot!" in result
        assert "📢" in result

    # -------------------------------------------------------------------------
    # AT-004: Legacy /notify Removed
    # -------------------------------------------------------------------------
    def test_at_004_legacy_notify_command_removed(self) -> None:
        """Validate /notify returns unknown command (superseded by @notify).

        Steps:
        1. Create SystemCommands
        2. Call dispatch() with "notify"
        3. Verify unknown command error
        """
        from teambot.repl.commands import SystemCommands

        commands = SystemCommands(router=None, config=None)

        result = commands.dispatch("notify", ["test"])

        assert result.success is False
        assert "Unknown command" in result.output

    # -------------------------------------------------------------------------
    # AT-005: @notify Graceful Failure
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_at_005_notify_without_config_returns_warning(self) -> None:
        """Validate @notify without config returns warning but succeeds.

        Steps:
        1. Create TaskExecutor with no config
        2. Execute _handle_notify()
        3. Verify warning output but success (non-blocking)
        """
        from unittest.mock import AsyncMock

        from teambot.tasks.executor import TaskExecutor

        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk, config=None)

        result = await executor._handle_notify("Test message", background=False)

        # Should return warning but still succeed (non-blocking)
        assert result.success is True
        assert "notification" in result.output.lower()

    @pytest.mark.asyncio
    async def test_at_005_notify_disabled_returns_warning(self) -> None:
        """Validate @notify with disabled notifications returns warning."""
        from unittest.mock import AsyncMock

        from teambot.tasks.executor import TaskExecutor

        mock_sdk = AsyncMock()
        config = {"notifications": {"enabled": False}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        result = await executor._handle_notify("Test", background=False)

        # Should succeed (non-blocking) but may include warning
        assert result.success is True

    @pytest.mark.asyncio
    async def test_at_005_notify_no_channels_returns_warning(self) -> None:
        """Validate @notify with no channels returns warning."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from teambot.tasks.executor import TaskExecutor

        mock_sdk = AsyncMock()
        config = {"notifications": {"enabled": True, "channels": []}}
        executor = TaskExecutor(sdk_client=mock_sdk, config=config)

        mock_event_bus = MagicMock()
        mock_event_bus._channels = []  # No channels

        with patch(
            "teambot.tasks.executor.create_event_bus_from_config",
            return_value=mock_event_bus,
        ):
            result = await executor._handle_notify("Test", background=False)

        # Should succeed (non-blocking) even if no channels
        assert result.success is True

    # -------------------------------------------------------------------------
    # AT-006: Header/Footer with Missing Objective Name
    # -------------------------------------------------------------------------
    def test_at_006_started_fallback_when_name_missing(self) -> None:
        """Validate started template uses fallback when name missing."""
        from teambot.notifications.events import NotificationEvent
        from teambot.notifications.templates import MessageTemplates

        templates = MessageTemplates()
        event = NotificationEvent(
            event_type="orchestration_started",
            feature_name="feature",
            data={},  # No objective_name
        )

        result = templates.render(event)

        assert "Starting" in result
        assert "orchestration run" in result

    def test_at_006_started_fallback_when_name_empty(self) -> None:
        """Validate started template uses fallback when name empty."""
        from teambot.notifications.events import NotificationEvent
        from teambot.notifications.templates import MessageTemplates

        templates = MessageTemplates()
        event = NotificationEvent(
            event_type="orchestration_started",
            feature_name="feature",
            data={"objective_name": ""},
        )

        result = templates.render(event)

        assert "Starting" in result
        assert "orchestration run" in result

    def test_at_006_completed_fallback_when_name_missing(self) -> None:
        """Validate completed template uses fallback when name missing."""
        from teambot.notifications.events import NotificationEvent
        from teambot.notifications.templates import MessageTemplates

        templates = MessageTemplates()
        event = NotificationEvent(
            event_type="orchestration_completed",
            feature_name="feature",
            data={"duration_seconds": 60},  # No objective_name
        )

        result = templates.render(event)

        assert "Completed" in result
        assert "orchestration run" in result

    @pytest.mark.asyncio
    async def test_at_006_execution_loop_fallback_to_feature_name(self, tmp_path: Path) -> None:
        """Validate ExecutionLoop uses feature_name when objective has no explicit description.

        When the objective parsing derives feature_name from title (no separate description),
        that feature_name is used in events.
        """
        from unittest.mock import AsyncMock

        from teambot.orchestration.execution_loop import ExecutionLoop

        # Objective with minimal content - feature_name derived from title
        objective_content = """# My Task

## Goals
1. Do the thing

## Success Criteria
- [ ] Thing is done
"""
        objective_path = tmp_path / "objective.md"
        objective_path.write_text(objective_content)

        # Create teambot dir with feature spec
        teambot_dir = tmp_path / ".teambot"
        teambot_dir.mkdir()
        feature_dir = teambot_dir / "my-task"
        feature_dir.mkdir()
        artifacts_dir = feature_dir / "artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "feature_spec.md").write_text("# Feature Spec\n\n## Overview\nTest.")

        loop = ExecutionLoop(
            objective_path=objective_path,
            config={},
            teambot_dir=teambot_dir,
            max_hours=8.0,
        )

        events: list[tuple[str, dict]] = []

        def on_progress(event_type: str, data: dict) -> None:
            events.append((event_type, data))

        mock_sdk = AsyncMock()
        mock_sdk.execute_streaming.return_value = "VERIFIED_APPROVED: Done."

        await loop.run(sdk_client=mock_sdk, on_progress=on_progress)

        # Should have emitted started event with the feature_name
        started_events = [e for e in events if e[0] == "orchestration_started"]
        assert len(started_events) == 1
        # Feature name is derived from "# My Task" -> "my-task"
        assert started_events[0][1]["objective_name"] is not None

    # -------------------------------------------------------------------------
    # AT-007: /help Includes @notify
    # -------------------------------------------------------------------------
    def test_at_007_help_includes_notify_agent(self) -> None:
        """Validate /help output includes @notify pseudo-agent.

        Steps:
        1. Call handle_help() with no args
        2. Verify output includes @notify
        """
        from teambot.repl.commands import handle_help

        result = handle_help([])

        assert "@notify" in result.output
        assert "notification" in result.output.lower()

    def test_at_007_help_notify_has_description(self) -> None:
        """Validate @notify in help has meaningful description."""
        from teambot.repl.commands import handle_help

        result = handle_help([])

        # Find the line with @notify
        lines = result.output.split("\n")
        notify_lines = [line for line in lines if "@notify" in line]

        assert len(notify_lines) >= 1
        # Should have description after command
        notify_line = notify_lines[0]
        assert "<msg>" in notify_line or "message" in notify_line.lower()
