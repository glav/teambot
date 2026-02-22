"""Logging configuration module for TeamBot.

This module provides mode-aware logging configuration that:
- Defaults to file-only logging in interactive UI mode
- Defaults to console + file logging in file orchestration mode
- Supports CLI override via force_console flag
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any


def is_interactive_mode(has_objective: bool) -> bool:
    """Determine if running in interactive UI mode.

    Args:
        has_objective: True if an objective file was provided.

    Returns:
        True if interactive mode (Textual/Rich UI), False if file orchestration.
    """
    # File orchestration mode if objective provided
    if has_objective:
        return False

    # Legacy mode flag forces non-interactive
    if os.environ.get("TEAMBOT_LEGACY_MODE", "").lower() == "true":
        return False

    # Check if stdout is a TTY (required for interactive)
    if not sys.stdout.isatty():
        return False

    return True


def setup_logging(
    config: dict[str, Any],
    is_interactive: bool,
    force_console: bool = False,
    verbose: bool = False,
) -> None:
    """Configure logging based on execution mode and config.

    Args:
        config: TeamBot configuration dict (must have "logging" key with defaults).
        is_interactive: True if running in interactive UI mode.
        force_console: Override to enable console output (--log-to-console).
        verbose: Enable DEBUG level logging (from -v flag).
    """
    logging_config = config.get("logging", {})

    # Determine log level
    level_str = logging_config.get("level", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)
    if verbose:
        level = logging.DEBUG

    # Clear any existing handlers on root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    # Formatter for all handlers
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    # File handler (always enabled unless explicitly disabled)
    file_handler_added = False
    if logging_config.get("file_output", True):
        log_file = logging_config.get("log_file", ".teambot/logs/teambot.log")
        log_path = Path(log_file)

        try:
            # Create directory if missing
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            file_handler_added = True
        except OSError:
            # Fall back to console-only logging; warn via stderr to avoid recursion
            print(  # noqa: T201
                f"WARNING: Could not set up log file '{log_path}'."
                " Falling back to console-only logging.",
                file=sys.stderr,
            )

    # Console handler (mode-dependent)
    console_enabled = logging_config.get("console_output")
    if console_enabled is None:
        # Default: console for file-orchestration, no console for interactive
        console_enabled = not is_interactive

    # Always enable console if file handler setup failed (graceful degradation)
    if not file_handler_added and logging_config.get("file_output", True):
        console_enabled = True

    if force_console or console_enabled:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
