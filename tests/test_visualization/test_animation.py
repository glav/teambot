"""Tests for startup animation module — Code-First approach."""

import os
from unittest.mock import MagicMock, patch


class TestShouldAnimate:
    """Tests for animation eligibility decision logic."""

    def test_returns_true_when_tty_and_enabled(self):
        """Animation plays when TTY, config enabled, no flags."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        with (
            patch("teambot.visualization.animation.sys") as mock_sys,
            patch("teambot.visualization.animation.shutil") as mock_shutil,
            patch("teambot.visualization.animation.os") as mock_os,
        ):
            mock_sys.stdout.isatty.return_value = True
            mock_shutil.get_terminal_size.return_value = os.terminal_size((80, 24))
            mock_os.environ.get.return_value = ""

            result = anim.should_animate(config={"show_startup_animation": True})

        assert result is True

    def test_returns_false_when_no_animation_flag(self):
        """--no-animation flag disables animation."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        result = anim.should_animate(no_animation_flag=True)

        assert result is False

    def test_returns_false_when_config_disabled(self):
        """show_startup_animation=false disables animation."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        result = anim.should_animate(config={"show_startup_animation": False})

        assert result is False

    def test_returns_false_when_not_tty(self):
        """Non-TTY environment disables animation."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        with (
            patch("teambot.visualization.animation.sys") as mock_sys,
            patch("teambot.visualization.animation.os") as mock_os,
        ):
            mock_sys.stdout.isatty.return_value = False
            mock_os.environ.get.return_value = ""

            result = anim.should_animate()

        assert result is False

    def test_returns_false_when_term_is_dumb(self):
        """TERM=dumb disables animation."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        with (
            patch("teambot.visualization.animation.sys") as mock_sys,
            patch("teambot.visualization.animation.os") as mock_os,
        ):
            mock_sys.stdout.isatty.return_value = True
            mock_os.environ.get.side_effect = lambda key, default="": (
                "dumb" if key == "TERM" else default
            )

            result = anim.should_animate()

        assert result is False

    def test_returns_false_when_terminal_too_small(self):
        """Small terminal disables animation."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        with (
            patch("teambot.visualization.animation.sys") as mock_sys,
            patch("teambot.visualization.animation.shutil") as mock_shutil,
            patch("teambot.visualization.animation.os") as mock_os,
        ):
            mock_sys.stdout.isatty.return_value = True
            mock_shutil.get_terminal_size.return_value = os.terminal_size((40, 5))
            mock_os.environ.get.return_value = ""

            result = anim.should_animate()

        assert result is False

    def test_returns_true_when_config_is_none(self):
        """Animation plays when config is None (default enabled)."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        with (
            patch("teambot.visualization.animation.sys") as mock_sys,
            patch("teambot.visualization.animation.shutil") as mock_shutil,
            patch("teambot.visualization.animation.os") as mock_os,
        ):
            mock_sys.stdout.isatty.return_value = True
            mock_shutil.get_terminal_size.return_value = os.terminal_size((80, 24))
            mock_os.environ.get.return_value = ""

            result = anim.should_animate(config=None)

        assert result is True

    def test_returns_false_when_env_var_set(self):
        """TEAMBOT_NO_ANIMATION env var disables animation."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        with patch("teambot.visualization.animation.os") as mock_os:
            mock_os.environ.get.side_effect = lambda key, default="": (
                "1" if key == "TEAMBOT_NO_ANIMATION" else default
            )

            result = anim.should_animate()

        assert result is False


class TestStartupAnimation:
    """Tests for animation rendering."""

    def test_play_calls_animated_when_eligible(self):
        """play() dispatches to animated path when all conditions met."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        with (
            patch.object(anim, "_is_explicitly_disabled", return_value=False),
            patch.object(anim, "_supports_animation", return_value=True),
            patch.object(anim, "_play_animated") as mock_animated,
        ):
            anim.play()
            mock_animated.assert_called_once()

    def test_play_calls_static_when_environment_limited(self):
        """play() shows static banner when environment doesn't support animation."""
        from teambot.visualization.animation import StartupAnimation

        anim = StartupAnimation(console=MagicMock())
        with (
            patch.object(anim, "_is_explicitly_disabled", return_value=False),
            patch.object(anim, "_supports_animation", return_value=False),
            patch.object(anim, "_show_static_banner") as mock_static,
        ):
            anim.play()
            mock_static.assert_called_once()

    def test_play_shows_static_banner_when_explicitly_disabled(self):
        """play() shows static banner when explicitly disabled."""
        from teambot.visualization.animation import StartupAnimation

        mock_console = MagicMock()
        anim = StartupAnimation(console=mock_console)
        with (
            patch.object(anim, "_is_explicitly_disabled", return_value=True),
            patch.object(anim, "_show_static_banner") as mock_static,
            patch.object(anim, "_play_animated") as mock_animated,
        ):
            anim.play()
            mock_static.assert_called_once()
            mock_animated.assert_not_called()

    def test_static_banner_contains_version(self):
        """Static banner includes version string."""
        from io import StringIO

        from rich.console import Console

        from teambot.visualization.animation import StartupAnimation

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        anim = StartupAnimation(console=console, version="1.2.3")
        banner = anim._final_banner()

        # Render to string and check content
        console.print(banner)
        rendered = output.getvalue()
        assert "1.2.3" in rendered

    def test_static_banner_contains_teambot_text(self):
        """Static banner includes TeamBot branding."""
        from io import StringIO

        from rich.console import Console

        from teambot.visualization.animation import StartupAnimation

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)
        anim = StartupAnimation(console=console)
        banner = anim._final_banner()

        console.print(banner)
        rendered = output.getvalue()
        assert "TeamBot" in rendered or "TEAMBOT" in rendered or "██" in rendered

    def test_frame_generation_returns_nonempty_list(self):
        """Frame generation produces renderable frames."""
        from rich.console import Console

        from teambot.visualization.animation import StartupAnimation

        console = Console(force_terminal=True, width=80)
        anim = StartupAnimation(console=console)

        convergence = anim._generate_convergence_frames()
        logo = anim._generate_logo_frames()

        assert len(convergence) > 0
        assert len(logo) > 0
        # Each frame is a (renderable, delay) tuple
        assert isinstance(convergence[0], tuple)
        assert len(convergence[0]) == 2

    def test_ascii_fallback_uses_no_unicode_box_drawing(self):
        """ASCII fallback logo contains no Unicode box-drawing characters."""
        from teambot.visualization.animation import TEAMBOT_LOGO_ASCII

        box_chars = set("╗╔╝╚║═█▀▄╚═╝╗╔║▐▌░▒▓━┌┐└┘├┤┬┴┼│─")
        for line in TEAMBOT_LOGO_ASCII:
            for char in line:
                assert char not in box_chars, f"Unicode box char '{char}' found in ASCII logo"


class TestAnimationConstants:
    """Tests for animation module constants."""

    def test_agent_order_has_six_agents(self):
        """AGENT_ORDER contains all 6 agents."""
        from teambot.visualization.animation import AGENT_ORDER

        assert len(AGENT_ORDER) == 6
        assert "pm" in AGENT_ORDER
        assert "reviewer" in AGENT_ORDER

    def test_logo_color_map_covers_full_width(self):
        """Logo color map spans the full logo width."""
        from teambot.visualization.animation import LOGO_COLOR_MAP, TEAMBOT_LOGO

        max_width = max(len(line) for line in TEAMBOT_LOGO)
        # Last entry's end should reach or exceed the logo width
        last_end = max(end for _, end, _ in LOGO_COLOR_MAP)
        assert last_end >= max_width - 1


class TestPlayStartupAnimation:
    """Tests for module-level convenience function."""

    def test_convenience_function_creates_and_plays(self):
        """play_startup_animation creates StartupAnimation and calls play."""
        from teambot.visualization.animation import play_startup_animation

        mock_console = MagicMock()
        with patch("teambot.visualization.animation.StartupAnimation") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            play_startup_animation(
                console=mock_console,
                config={"show_startup_animation": True},
                no_animation_flag=False,
                version="0.1.0",
            )

            mock_cls.assert_called_once_with(mock_console, "0.1.0")
            mock_instance.play.assert_called_once_with({"show_startup_animation": True}, False)
