"""Tests for logging configuration module."""

import logging


class TestIsInteractiveMode:
    """Tests for is_interactive_mode() function."""

    def test_file_orchestration_mode_not_interactive(self):
        """When objective provided, not interactive mode."""
        from teambot.config.logging_config import is_interactive_mode

        result = is_interactive_mode(has_objective=True)
        assert result is False

    def test_no_objective_is_interactive(self, monkeypatch):
        """When no objective and TTY, is interactive mode."""
        import sys

        from teambot.config.logging_config import is_interactive_mode

        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        monkeypatch.delenv("TEAMBOT_LEGACY_MODE", raising=False)
        result = is_interactive_mode(has_objective=False)
        assert result is True

    def test_legacy_mode_not_interactive(self, monkeypatch):
        """TEAMBOT_LEGACY_MODE=true forces non-interactive."""
        from teambot.config.logging_config import is_interactive_mode

        monkeypatch.setenv("TEAMBOT_LEGACY_MODE", "true")
        result = is_interactive_mode(has_objective=False)
        assert result is False

    def test_no_tty_not_interactive(self, monkeypatch):
        """When stdout not a TTY, not interactive."""
        import sys

        from teambot.config.logging_config import is_interactive_mode

        monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
        monkeypatch.delenv("TEAMBOT_LEGACY_MODE", raising=False)
        result = is_interactive_mode(has_objective=False)
        assert result is False


class TestSetupLogging:
    """Tests for setup_logging() function."""

    def setup_method(self):
        """Clear handlers before each test."""
        root = logging.getLogger()
        root.handlers.clear()

    def teardown_method(self):
        """Clear handlers after each test."""
        root = logging.getLogger()
        root.handlers.clear()

    def test_interactive_mode_no_console_handler(self, tmp_path):
        """Interactive mode should not have console handler by default."""
        from teambot.config.logging_config import setup_logging

        config = {
            "logging": {
                "file_output": True,
                "log_file": str(tmp_path / "test.log"),
                "level": "INFO",
            }
        }

        setup_logging(config, is_interactive=True, force_console=False)

        root = logging.getLogger()
        console_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 0

    def test_file_mode_has_console_handler(self, tmp_path):
        """File mode should have console handler by default."""
        from teambot.config.logging_config import setup_logging

        config = {
            "logging": {
                "file_output": True,
                "log_file": str(tmp_path / "test.log"),
                "level": "INFO",
            }
        }

        setup_logging(config, is_interactive=False, force_console=False)

        root = logging.getLogger()
        console_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 1

    def test_force_console_overrides_interactive(self, tmp_path):
        """force_console=True adds console handler in interactive mode."""
        from teambot.config.logging_config import setup_logging

        config = {
            "logging": {
                "file_output": True,
                "log_file": str(tmp_path / "test.log"),
                "level": "INFO",
            }
        }

        setup_logging(config, is_interactive=True, force_console=True)

        root = logging.getLogger()
        console_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 1

    def test_file_handler_created(self, tmp_path):
        """File handler created when file_output=True."""
        from teambot.config.logging_config import setup_logging

        log_file = tmp_path / "test.log"
        config = {
            "logging": {
                "file_output": True,
                "log_file": str(log_file),
                "level": "INFO",
            }
        }

        setup_logging(config, is_interactive=True, force_console=False)

        root = logging.getLogger()
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1

    def test_log_directory_created(self, tmp_path):
        """Log directory created if missing."""
        from teambot.config.logging_config import setup_logging

        log_file = tmp_path / "logs" / "subdir" / "test.log"
        config = {
            "logging": {
                "file_output": True,
                "log_file": str(log_file),
                "level": "INFO",
            }
        }

        setup_logging(config, is_interactive=True, force_console=False)

        assert log_file.parent.exists()

    def test_no_file_handler_when_disabled(self, tmp_path):
        """No file handler when file_output=False."""
        from teambot.config.logging_config import setup_logging

        config = {
            "logging": {
                "file_output": False,
                "log_file": str(tmp_path / "test.log"),
                "level": "INFO",
            }
        }

        setup_logging(config, is_interactive=False, force_console=False)

        root = logging.getLogger()
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 0

    def test_verbose_overrides_config_level(self, tmp_path):
        """verbose=True sets DEBUG level regardless of config."""
        from teambot.config.logging_config import setup_logging

        config = {
            "logging": {
                "file_output": True,
                "log_file": str(tmp_path / "test.log"),
                "level": "WARNING",  # Higher than DEBUG
            }
        }

        setup_logging(config, is_interactive=True, force_console=False, verbose=True)

        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_config_level_applied(self, tmp_path):
        """Config level is applied when verbose=False."""
        from teambot.config.logging_config import setup_logging

        config = {
            "logging": {
                "file_output": True,
                "log_file": str(tmp_path / "test.log"),
                "level": "WARNING",
            }
        }

        setup_logging(config, is_interactive=True, force_console=False, verbose=False)

        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_console_output_true_overrides_interactive(self, tmp_path):
        """console_output=True forces console even in interactive mode."""
        from teambot.config.logging_config import setup_logging

        config = {
            "logging": {
                "console_output": True,
                "file_output": True,
                "log_file": str(tmp_path / "test.log"),
                "level": "INFO",
            }
        }

        setup_logging(config, is_interactive=True, force_console=False)

        root = logging.getLogger()
        console_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 1

    def test_console_output_false_suppresses_in_file_mode(self, tmp_path):
        """console_output=False suppresses console even in file orchestration mode."""
        from teambot.config.logging_config import setup_logging

        config = {
            "logging": {
                "console_output": False,
                "file_output": True,
                "log_file": str(tmp_path / "test.log"),
                "level": "INFO",
            }
        }

        setup_logging(config, is_interactive=False, force_console=False)

        root = logging.getLogger()
        console_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 0

    def test_clears_existing_handlers(self, tmp_path):
        """setup_logging closes and removes existing handlers."""
        from unittest.mock import MagicMock

        from teambot.config.logging_config import setup_logging

        # Add an existing handler with a mock close method
        root = logging.getLogger()
        existing_handler = logging.StreamHandler()
        existing_handler.set_name("test_existing_handler")
        existing_handler.close = MagicMock()
        root.addHandler(existing_handler)
        assert existing_handler in root.handlers

        config = {
            "logging": {
                "file_output": True,
                "log_file": str(tmp_path / "test.log"),
                "level": "INFO",
            }
        }

        setup_logging(config, is_interactive=True, force_console=False)

        # Old handler should be closed and removed
        existing_handler.close.assert_called_once()
        assert existing_handler not in root.handlers
