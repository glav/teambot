"""Tests for CLI - end-to-end tests."""

import json

import pytest


class TestCLIParser:
    """Tests for CLI argument parsing."""

    def test_parser_init_command(self):
        """Parser recognizes init command."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["init"])

        assert args.command == "init"

    def test_parser_run_command(self):
        """Parser recognizes run command with objective."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "objective.md"])

        assert args.command == "run"
        assert args.objective == "objective.md"

    def test_parser_run_with_config(self):
        """Parser accepts custom config path."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "-c", "custom.json", "obj.md"])

        assert args.config == "custom.json"

    def test_parser_status_command(self):
        """Parser recognizes status command."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["status"])

        assert args.command == "status"

    def test_parser_verbose_flag(self):
        """Parser recognizes verbose flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["-v", "init"])

        assert args.verbose is True

    def test_parser_accepts_no_animation_flag(self):
        """Parser recognizes --no-animation flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--no-animation", "run", "obj.md"])

        assert args.no_animation is True

    def test_no_animation_flag_defaults_false(self):
        """--no-animation defaults to False when not provided."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["run", "obj.md"])

        assert args.no_animation is False


class TestCLIInit:
    """Tests for init command."""

    def test_init_creates_config(self, tmp_path, monkeypatch):
        """Init creates configuration file."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0
        assert (tmp_path / "teambot.json").exists()
        assert (tmp_path / ".teambot").exists()

    def test_init_fails_if_exists(self, tmp_path, monkeypatch):
        """Init fails if config exists without --force."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create existing config
        (tmp_path / "teambot.json").write_text("{}", encoding="utf-8")

        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 1

    def test_init_force_overwrites(self, tmp_path, monkeypatch):
        """Init with --force overwrites existing config."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init

        monkeypatch.chdir(tmp_path)

        # Create existing config
        (tmp_path / "teambot.json").write_text("{}", encoding="utf-8")

        args = argparse.Namespace(force=True)
        display = ConsoleDisplay()

        result = cmd_init(args, display)

        assert result == 0
        # Should have real config now
        config = json.loads((tmp_path / "teambot.json").read_text(encoding="utf-8"))
        assert "agents" in config


class TestCLIRun:
    """Tests for run command."""

    def test_run_fails_without_config(self, tmp_path, monkeypatch):
        """Run fails if no configuration exists."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace(config="teambot.json", objective=None)
        display = ConsoleDisplay()

        result = cmd_run(args, display)

        assert result == 1

    def test_run_with_valid_config(self, tmp_path, monkeypatch):
        """Run succeeds with valid configuration."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init, cmd_run

        monkeypatch.chdir(tmp_path)

        # Initialize first
        init_args = argparse.Namespace(force=False)
        cmd_init(init_args, ConsoleDisplay())

        args = argparse.Namespace(config="teambot.json", objective=None)
        display = ConsoleDisplay()

        # Mock the REPL to avoid hanging on input

        async def mock_repl(*args, **kwargs):
            pass

        monkeypatch.setattr("teambot.repl.run_interactive_mode", mock_repl)

        result = cmd_run(args, display)

        assert result == 0


class TestCLIStatus:
    """Tests for status command."""

    def test_status_fails_without_init(self, tmp_path, monkeypatch):
        """Status fails if TeamBot not initialized."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_status

        monkeypatch.chdir(tmp_path)

        args = argparse.Namespace()
        display = ConsoleDisplay()

        result = cmd_status(args, display)

        assert result == 1

    def test_status_succeeds_after_init(self, tmp_path, monkeypatch):
        """Status succeeds after initialization."""
        import argparse

        from teambot.cli import ConsoleDisplay, cmd_init, cmd_status

        monkeypatch.chdir(tmp_path)

        # Initialize first
        init_args = argparse.Namespace(force=False)
        cmd_init(init_args, ConsoleDisplay())

        args = argparse.Namespace()
        display = ConsoleDisplay()

        result = cmd_status(args, display)

        assert result == 0


class TestCLIMain:
    """Tests for main entry point."""

    def test_main_no_command_shows_help(self, capsys):
        """Main with no command shows help."""
        import sys

        from teambot.cli import main

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(sys, "argv", ["teambot"])
            result = main()

        assert result == 0

    def test_main_returns_int(self, tmp_path, monkeypatch):
        """Main returns integer exit code."""
        import sys

        from teambot.cli import main

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["teambot", "status"])

        result = main()

        assert isinstance(result, int)


class TestInitNotificationMode:
    """Tests for notification mode selection in init wizard."""

    def test_setup_telegram_includes_notification_mode(self, tmp_path, monkeypatch):
        """_setup_telegram_notifications adds notification_mode to config."""
        from teambot.cli import ConsoleDisplay, _setup_telegram_notifications

        # Mock stdin for interactive input
        # Simulate: Y (proceed), Enter (default token), Enter (default chat_id), 2 (agent_status)
        inputs = iter(["y", "", "", "2"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        config = {}
        display = ConsoleDisplay()

        result = _setup_telegram_notifications(config, display)

        assert result is True
        assert "notifications" in config
        channel = config["notifications"]["channels"][0]
        assert "notification_mode" in channel
        assert channel["notification_mode"] == "agent_status"

    def test_setup_telegram_default_mode_is_stages_only(self, tmp_path, monkeypatch):
        """Default notification mode is stages_only when user presses Enter."""
        from teambot.cli import ConsoleDisplay, _setup_telegram_notifications

        # Simulate: Y (proceed), Enter x3 (all defaults including mode)
        inputs = iter(["y", "", "", ""])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        config = {}
        display = ConsoleDisplay()

        result = _setup_telegram_notifications(config, display)

        assert result is True
        channel = config["notifications"]["channels"][0]
        assert channel["notification_mode"] == "stages_only"

    def test_setup_telegram_all_mode(self, tmp_path, monkeypatch):
        """Mode '3' selects 'all' notification mode."""
        from teambot.cli import ConsoleDisplay, _setup_telegram_notifications

        inputs = iter(["y", "", "", "3"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        config = {}
        display = ConsoleDisplay()

        result = _setup_telegram_notifications(config, display)

        assert result is True
        channel = config["notifications"]["channels"][0]
        assert channel["notification_mode"] == "all"
