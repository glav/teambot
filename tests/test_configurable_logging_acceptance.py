"""Acceptance tests for configurable logging feature.

These tests validate the REAL implementation code for the configurable logging
feature. Each test corresponds to an acceptance scenario (AT-XXX).

Core logic is tested directly; selective mocking is used only for external
dependencies like TTY detection.
"""

import logging

import pytest


@pytest.mark.acceptance
class TestAcceptanceScenarios:
    """Acceptance test scenarios for configurable logging."""

    def setup_method(self):
        """Clear logging handlers before each test."""
        root = logging.getLogger()
        root.handlers.clear()

    def teardown_method(self):
        """Clear logging handlers after each test."""
        root = logging.getLogger()
        root.handlers.clear()

    def test_at_001_interactive_mode_default_no_console_handler(self, tmp_path, monkeypatch):
        """AT-001: Interactive mode defaults to file-only logging (no console output).

        Validates that when running in interactive mode (no objective provided,
        TTY available), console logging is disabled by default.
        """
        import sys

        from teambot.config.loader import ConfigLoader
        from teambot.config.logging_config import is_interactive_mode, setup_logging

        # Create minimal config file
        config_file = tmp_path / "teambot.json"
        config_file.write_text('{"agents": [{"id": "pm", "persona": "project_manager"}]}')

        # Simulate interactive mode environment
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.delenv("TEAMBOT_LEGACY_MODE", raising=False)

        # Load config using REAL ConfigLoader
        loader = ConfigLoader()
        config = loader.load(config_file)

        # Override log file to temp directory
        config["logging"]["log_file"] = str(tmp_path / "teambot.log")

        # Determine mode using REAL is_interactive_mode
        interactive = is_interactive_mode(has_objective=False)
        assert interactive is True, "Should detect interactive mode"

        # Setup logging using REAL setup_logging
        setup_logging(config, is_interactive=interactive, force_console=False)

        # Verify: NO console handlers in interactive mode
        root = logging.getLogger()
        console_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 0, "Interactive mode should have NO console handler"

        # Verify: File handler IS present
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1, "File handler should be present"

        # Verify: Log file is created and writable
        test_logger = logging.getLogger("test")
        test_logger.info("Test message for AT-001")

        log_file = tmp_path / "teambot.log"
        assert log_file.exists(), "Log file should be created"
        content = log_file.read_text()
        assert "Test message for AT-001" in content, "Message should be in log file"

    def test_at_002_file_mode_has_console_and_file_handler(self, tmp_path, monkeypatch):
        """AT-002: File-based orchestration mode shows logs on console AND writes to file.

        Validates that when running with an objective file (file-based mode),
        both console and file logging are enabled by default.
        """
        from teambot.config.loader import ConfigLoader
        from teambot.config.logging_config import is_interactive_mode, setup_logging

        # Create minimal config file
        config_file = tmp_path / "teambot.json"
        config_file.write_text('{"agents": [{"id": "pm", "persona": "project_manager"}]}')

        # Load config using REAL ConfigLoader
        loader = ConfigLoader()
        config = loader.load(config_file)

        # Override log file to temp directory
        config["logging"]["log_file"] = str(tmp_path / "teambot.log")

        # Determine mode using REAL is_interactive_mode with objective
        interactive = is_interactive_mode(has_objective=True)
        assert interactive is False, "Should detect file-based mode when objective provided"

        # Setup logging using REAL setup_logging
        setup_logging(config, is_interactive=interactive, force_console=False)

        # Verify: Console handler IS present in file mode
        root = logging.getLogger()
        console_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 1, "File mode should have console handler"

        # Verify: File handler IS also present
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1, "File handler should be present"

        # Verify: Log message goes to both
        test_logger = logging.getLogger("test")
        test_logger.info("Test message for AT-002")

        log_file = tmp_path / "teambot.log"
        assert log_file.exists(), "Log file should be created"
        content = log_file.read_text()
        assert "Test message for AT-002" in content, "Message should be in log file"

    def test_at_003_force_console_enables_console_in_interactive_mode(self, tmp_path, monkeypatch):
        """AT-003: --log-to-console flag enables console logging in interactive mode.

        Validates that the force_console parameter (from --log-to-console CLI flag)
        overrides the default file-only behavior in interactive mode.
        """
        import sys

        from teambot.config.loader import ConfigLoader
        from teambot.config.logging_config import is_interactive_mode, setup_logging

        # Create minimal config file
        config_file = tmp_path / "teambot.json"
        config_file.write_text('{"agents": [{"id": "pm", "persona": "project_manager"}]}')

        # Simulate interactive mode environment
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.delenv("TEAMBOT_LEGACY_MODE", raising=False)

        # Load config using REAL ConfigLoader
        loader = ConfigLoader()
        config = loader.load(config_file)

        # Override log file to temp directory
        config["logging"]["log_file"] = str(tmp_path / "teambot.log")

        # Determine mode - should be interactive
        interactive = is_interactive_mode(has_objective=False)
        assert interactive is True, "Should detect interactive mode"

        # Setup logging with force_console=True (simulates --log-to-console)
        setup_logging(config, is_interactive=interactive, force_console=True)

        # Verify: Console handler IS now present due to force_console
        root = logging.getLogger()
        console_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 1, "force_console should enable console handler"

        # Verify: File handler still present
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1, "File handler should still be present"

    def test_at_004_custom_configuration_applied(self, tmp_path, monkeypatch):
        """AT-004: Custom logging configuration is respected.

        Validates that custom logging settings in teambot.json are applied:
        - console_output can be explicitly enabled/disabled
        - log_file path is customizable
        - level setting is respected
        """
        import json
        import sys

        from teambot.config.loader import ConfigLoader
        from teambot.config.logging_config import setup_logging

        # Create config with custom logging settings
        custom_log_dir = tmp_path / "custom-logs"
        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "logging": {
                "console_output": True,  # Explicitly enable console
                "file_output": False,  # Disable file logging
                "log_file": str(custom_log_dir / "custom.log"),
                "level": "DEBUG",
            },
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        # Simulate interactive mode
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.delenv("TEAMBOT_LEGACY_MODE", raising=False)

        # Load config using REAL ConfigLoader
        loader = ConfigLoader()
        config = loader.load(config_file)

        # Setup logging using REAL setup_logging
        setup_logging(config, is_interactive=True, force_console=False)

        root = logging.getLogger()

        # Verify: Console handler enabled (overrides interactive default)
        console_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 1, "console_output=True should enable console"

        # Verify: File handler disabled
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 0, "file_output=False should disable file handler"

        # Verify: Custom directory NOT created (since file_output=False)
        assert not custom_log_dir.exists(), "Custom log dir should not be created when disabled"

        # Verify: DEBUG level applied
        assert root.level == logging.DEBUG, "Custom level should be applied"

    def test_at_005_backwards_compatibility_no_logging_section(self, tmp_path, monkeypatch):
        """AT-005: Existing config without 'logging' section works unchanged.

        Validates that a teambot.json file without any logging configuration
        (backwards compatibility scenario) loads successfully with defaults applied.
        """
        import json
        import sys

        from teambot.config.loader import ConfigLoader
        from teambot.config.logging_config import is_interactive_mode, setup_logging

        # Create config WITHOUT logging section (legacy config)
        config_data = {
            "agents": [
                {"id": "pm", "persona": "project_manager"},
                {"id": "ba", "persona": "business_analyst"},
            ],
            "workflow": {"stages": ["setup", "implementation"]},
            "notifications": {"enabled": False},
            # NO "logging" key - testing backwards compatibility
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        # Simulate interactive mode
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.delenv("TEAMBOT_LEGACY_MODE", raising=False)

        # Load config using REAL ConfigLoader - should NOT raise any errors
        loader = ConfigLoader()
        config = loader.load(config_file)

        # Verify: Logging section added with defaults
        assert "logging" in config, "Logging section should be auto-added"
        assert config["logging"]["file_output"] is True, "Default file_output=True"
        assert config["logging"]["log_file"] == ".teambot/logs/teambot.log", "Default log path"
        assert config["logging"]["level"] == "INFO", "Default level=INFO"

        # Override log file for test isolation
        config["logging"]["log_file"] = str(tmp_path / "teambot.log")

        # Verify: Logging setup works with defaults
        interactive = is_interactive_mode(has_objective=False)
        setup_logging(config, is_interactive=interactive, force_console=False)

        # Verify: Default behavior in interactive mode (no console)
        root = logging.getLogger()
        console_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 0, "Default interactive should have no console"

        # Verify: File handler present
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1, "Default should have file handler"

    def test_at_006_log_directory_auto_creation(self, tmp_path):
        """AT-006: Log directory is created automatically if missing.

        Validates that when the log file path specifies a directory that doesn't
        exist, the directory structure is created automatically.
        """
        import json

        from teambot.config.loader import ConfigLoader
        from teambot.config.logging_config import setup_logging

        # Create nested directory path that doesn't exist
        nested_log_dir = tmp_path / "deeply" / "nested" / "logs"
        log_file_path = nested_log_dir / "teambot.log"

        # Verify directory doesn't exist before test
        assert not nested_log_dir.exists(), "Directory should not exist before test"

        # Create config with nested log path
        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "logging": {
                "file_output": True,
                "log_file": str(log_file_path),
                "level": "INFO",
            },
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        # Load config using REAL ConfigLoader
        loader = ConfigLoader()
        config = loader.load(config_file)

        # Setup logging - should auto-create directory
        setup_logging(config, is_interactive=False, force_console=False)

        # Verify: Directory was created
        assert nested_log_dir.exists(), "Log directory should be auto-created"

        # Verify: Log file is writable
        test_logger = logging.getLogger("test")
        test_logger.info("Test message for AT-006")

        # Verify: Log file exists and has content
        assert log_file_path.exists(), "Log file should be created"
        content = log_file_path.read_text()
        assert "Test message for AT-006" in content, "Message should be in log file"
