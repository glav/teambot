<!-- markdownlint-disable-file -->
# Task Details: Configurable Logging Output

## Research Reference

**Source Research**: .agent-tracking/research/20260220-configurable-logging-research.md

## Test Strategy Reference

**Test Strategy**: .teambot/configurable-logging/artifacts/test_strategy.md
**Approach**: TDD (Test-Driven Development)
**Coverage Target**: 90%+ for new code

---

## Phase 1: TDD Tests - Config Schema Validation

### Task 1.1: Write tests for logging schema validation

Write failing tests for logging configuration validation in `tests/test_config/test_loader.py`.

* **Files**:
  * `tests/test_config/test_loader.py` - Add new test class `TestLoggingConfigValidation`

* **Test Cases to Implement**:
  ```python
  class TestLoggingConfigValidation:
      """Tests for logging configuration validation."""

      def test_logging_section_parsed_correctly(self, tmp_path):
          """Valid logging config is parsed without errors."""
          # Config with full logging section
          # Assert config["logging"] has expected values

      def test_logging_not_object_raises_config_error(self, tmp_path):
          """logging must be an object, not string/number/array."""
          # Config with "logging": "invalid"
          # Assert raises ConfigError with match "'logging' must be an object"

      def test_logging_console_output_boolean_or_null(self, tmp_path):
          """console_output must be boolean or null."""
          # Config with "logging": {"console_output": "invalid"}
          # Assert raises ConfigError

      def test_logging_file_output_must_be_boolean(self, tmp_path):
          """file_output must be boolean."""
          # Config with "logging": {"file_output": "yes"}
          # Assert raises ConfigError

      def test_logging_log_file_must_be_string(self, tmp_path):
          """log_file must be a string path."""
          # Config with "logging": {"log_file": 123}
          # Assert raises ConfigError

      def test_logging_level_must_be_valid(self, tmp_path):
          """level must be DEBUG, INFO, WARNING, or ERROR."""
          # Config with "logging": {"level": "INVALID"}
          # Assert raises ConfigError
  ```

* **Success**:
  * Tests are syntactically correct and import properly
  * Tests fail because `_validate_logging()` doesn't exist yet
  * Tests follow existing patterns in `TestNotificationsConfigValidation`

* **Research References**:
  * .agent-tracking/research/20260220-configurable-logging-research.md (Lines 393-421) - Validation implementation
  * .teambot/configurable-logging/artifacts/test_strategy.md (Lines 296-350) - Test patterns from codebase

* **Dependencies**:
  * None (first task)

---

### Task 1.2: Write tests for logging defaults application

Write failing tests for default logging configuration in `tests/test_config/test_loader.py`.

* **Files**:
  * `tests/test_config/test_loader.py` - Add tests to `TestLoggingConfigValidation`

* **Test Cases to Implement**:
  ```python
  def test_logging_section_defaults_when_absent(self, tmp_path):
      """Missing logging section applies default values."""
      # Config without logging key
      # Assert config["logging"]["file_output"] == True
      # Assert config["logging"]["log_file"] == ".teambot/logs/teambot.log"
      # Assert config["logging"]["level"] == "INFO"

  def test_logging_partial_config_fills_defaults(self, tmp_path):
      """Partial logging config fills in missing defaults."""
      # Config with "logging": {"level": "DEBUG"}
      # Assert other defaults are applied

  def test_backwards_compatibility_no_logging_key(self, tmp_path):
      """Existing config without logging key works unchanged."""
      # Config with agents, workflow, notifications but no logging
      # Assert no errors raised
      # Assert defaults applied
  ```

* **Success**:
  * Tests fail because defaults not yet implemented
  * Tests verify backwards compatibility requirement

* **Research References**:
  * .agent-tracking/research/20260220-configurable-logging-research.md (Lines 423-436) - Defaults application
  * .teambot/configurable-logging/artifacts/feature_spec.md (Lines 163-169) - Default values

* **Dependencies**:
  * Task 1.1 completion

---

## Phase 2: Config Schema Implementation

### Task 2.1: Add `_validate_logging()` method to ConfigLoader

Implement logging validation in `src/teambot/config/loader.py`.

* **Files**:
  * `src/teambot/config/loader.py` - Add `_validate_logging()` method

* **Implementation**:
  ```python
  VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}

  def _validate_logging(self, logging: dict[str, Any]) -> None:
      """Validate logging configuration.
      
      Args:
          logging: The logging configuration dict.
          
      Raises:
          ConfigError: If validation fails.
      """
      if not isinstance(logging, dict):
          raise ConfigError("'logging' must be an object")
      
      if "console_output" in logging:
          val = logging["console_output"]
          if val is not None and not isinstance(val, bool):
              raise ConfigError("'logging.console_output' must be a boolean or null")
      
      if "file_output" in logging:
          if not isinstance(logging["file_output"], bool):
              raise ConfigError("'logging.file_output' must be a boolean")
      
      if "log_file" in logging:
          if not isinstance(logging["log_file"], str):
              raise ConfigError("'logging.log_file' must be a string")
      
      if "level" in logging:
          level = logging["level"]
          if not isinstance(level, str) or level.upper() not in VALID_LOG_LEVELS:
              raise ConfigError(
                  f"'logging.level' must be one of: {', '.join(sorted(VALID_LOG_LEVELS))}"
              )
  ```

* **Integration Point**:
  * Call `_validate_logging()` from `_validate()` method when `logging` key exists

* **Success**:
  * Task 1.1 validation tests pass
  * ConfigError raised for invalid configs

* **Research References**:
  * .agent-tracking/research/20260220-configurable-logging-research.md (Lines 393-421) - Implementation code
  * src/teambot/config/loader.py - Existing `_validate_notifications()` pattern

* **Dependencies**:
  * Phase 1 completion (tests exist)

---

### Task 2.2: Update `_apply_defaults()` with logging defaults

Add logging defaults to the `_apply_defaults()` method in `src/teambot/config/loader.py`.

* **Files**:
  * `src/teambot/config/loader.py` - Update `_apply_defaults()` method

* **Implementation**:
  ```python
  # Add to _apply_defaults() method:
  
  # Apply logging defaults
  if "logging" not in config:
      config["logging"] = {}
  logging_cfg = config["logging"]
  if "file_output" not in logging_cfg:
      logging_cfg["file_output"] = True
  if "log_file" not in logging_cfg:
      logging_cfg["log_file"] = ".teambot/logs/teambot.log"
  if "level" not in logging_cfg:
      logging_cfg["level"] = "INFO"
  # Note: console_output defaults to None (mode-dependent)
  ```

* **Success**:
  * Task 1.2 defaults tests pass
  * Backwards compatibility maintained
  * Existing configs load without changes

* **Research References**:
  * .agent-tracking/research/20260220-configurable-logging-research.md (Lines 423-436) - Defaults code
  * .teambot/configurable-logging/artifacts/feature_spec.md (Lines 163-169) - Default values

* **Dependencies**:
  * Task 2.1 completion

---

## Phase 3: TDD Tests - Logging Module

### Task 3.1: Write tests for `is_interactive_mode()` function

Create test file for logging module with mode detection tests.

* **Files**:
  * `tests/test_config/test_logging_config.py` - **CREATE** new test file

* **Test Cases to Implement**:
  ```python
  """Tests for logging configuration module."""

  import pytest


  class TestIsInteractiveMode:
      """Tests for is_interactive_mode() function."""

      def test_file_orchestration_mode_not_interactive(self):
          """When objective provided, not interactive mode."""
          from teambot.config.logging_config import is_interactive_mode
          
          result = is_interactive_mode(has_objective=True)
          assert result is False

      def test_no_objective_is_interactive(self, monkeypatch):
          """When no objective and TTY, is interactive mode."""
          from teambot.config.logging_config import is_interactive_mode
          import sys
          
          monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
          result = is_interactive_mode(has_objective=False)
          assert result is True

      def test_legacy_mode_not_interactive(self, monkeypatch):
          """TEAMBOT_LEGACY_MODE=true forces non-interactive."""
          from teambot.config.logging_config import is_interactive_mode
          import os
          
          monkeypatch.setenv("TEAMBOT_LEGACY_MODE", "true")
          result = is_interactive_mode(has_objective=False)
          assert result is False

      def test_no_tty_not_interactive(self, monkeypatch):
          """When stdout not a TTY, not interactive."""
          from teambot.config.logging_config import is_interactive_mode
          import sys
          
          monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
          result = is_interactive_mode(has_objective=False)
          assert result is False
  ```

* **Success**:
  * Tests fail because module doesn't exist
  * Tests cover all mode detection scenarios

* **Research References**:
  * .agent-tracking/research/20260220-configurable-logging-research.md (Lines 495-518) - is_interactive_mode() code

* **Dependencies**:
  * Phase 2 completion

---

### Task 3.2: Write tests for `setup_logging()` with mode routing

Add tests for logging handler setup to `tests/test_config/test_logging_config.py`.

* **Files**:
  * `tests/test_config/test_logging_config.py` - Add new test class

* **Test Cases to Implement**:
  ```python
  import logging
  from pathlib import Path


  class TestSetupLogging:
      """Tests for setup_logging() function."""

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
          console_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
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
          console_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
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
          console_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
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
  ```

* **Success**:
  * Tests fail because `setup_logging()` doesn't exist
  * Tests cover handler routing and directory creation

* **Research References**:
  * .agent-tracking/research/20260220-configurable-logging-research.md (Lines 239-298) - setup_logging() implementation

* **Dependencies**:
  * Task 3.1 completion

---

## Phase 4: Logging Module Implementation

### Task 4.1: Create `src/teambot/config/logging_config.py`

Implement the logging configuration module.

* **Files**:
  * `src/teambot/config/logging_config.py` - **CREATE** new module

* **Implementation**:
  ```python
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
      formatter = logging.Formatter(
          "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
      )
      console_formatter = logging.Formatter(
          "%(name)s - %(levelname)s - %(message)s"
      )
      
      # File handler (always enabled unless explicitly disabled)
      if logging_config.get("file_output", True):
          log_file = logging_config.get("log_file", ".teambot/logs/teambot.log")
          log_path = Path(log_file)
          
          # Create directory if missing
          log_path.parent.mkdir(parents=True, exist_ok=True)
          
          file_handler = logging.FileHandler(log_path, encoding="utf-8")
          file_handler.setLevel(level)
          file_handler.setFormatter(formatter)
          root_logger.addHandler(file_handler)
      
      # Console handler (mode-dependent)
      console_enabled = logging_config.get("console_output")
      if console_enabled is None:
          # Default: console for file-orchestration, no console for interactive
          console_enabled = not is_interactive
      
      if force_console or console_enabled:
          console_handler = logging.StreamHandler()
          console_handler.setLevel(level)
          console_handler.setFormatter(console_formatter)
          root_logger.addHandler(console_handler)
  ```

* **Success**:
  * All Phase 3 tests pass
  * Module is importable with no errors
  * Handlers configured correctly based on mode

* **Research References**:
  * .agent-tracking/research/20260220-configurable-logging-research.md (Lines 239-298) - Full implementation
  * .agent-tracking/research/20260220-configurable-logging-research.md (Lines 495-518) - Mode detection

* **Dependencies**:
  * Phase 3 completion (tests exist)

---

## Phase 5: CLI Integration

### Task 5.1: Add `--log-to-console` flag to argument parser

Add CLI flag for debugging interactive mode.

* **Files**:
  * `src/teambot/cli.py` - Update `create_parser()` function

* **Implementation**:
  Locate the `run_parser` subparser in `create_parser()` and add:
  ```python
  run_parser.add_argument(
      "--log-to-console",
      action="store_true",
      help="Enable console logging output (useful for debugging interactive mode)",
  )
  ```

* **Success**:
  * `uv run teambot run --help` shows `--log-to-console` flag
  * Flag defaults to False
  * No breaking changes to existing arguments

* **Research References**:
  * .agent-tracking/research/20260220-configurable-logging-research.md (Lines 579-585) - CLI argument code

* **Dependencies**:
  * Phase 4 completion

---

### Task 5.2: Update `cmd_run()` to use new logging setup

Integrate mode-aware logging into the run command.

* **Files**:
  * `src/teambot/cli.py` - Update `cmd_run()` function

* **Implementation**:
  1. Add import at top of file:
     ```python
     from teambot.config.logging_config import is_interactive_mode, setup_logging as setup_mode_logging
     ```

  2. In `cmd_run()`, after config is loaded but before running:
     ```python
     # Determine execution mode
     interactive = is_interactive_mode(has_objective=bool(args.objective))
     
     # Configure logging with mode awareness
     setup_mode_logging(
         config=config,
         is_interactive=interactive,
         force_console=getattr(args, "log_to_console", False),
         verbose=getattr(args, "verbose", False),
     )
     ```

  3. Ensure the old `setup_logging()` call in `main()` is kept for early startup logging (before config loaded), but the mode-aware setup overrides it in `cmd_run()`.

* **Success**:
  * Interactive mode (`teambot run`) has file-only logging
  * File mode (`teambot run objective.md`) has console + file logging
  * `--log-to-console` flag enables console in interactive mode

* **Research References**:
  * .agent-tracking/research/20260220-configurable-logging-research.md (Lines 534-548) - CLI integration code
  * .agent-tracking/research/20260220-configurable-logging-research.md (Lines 68-84) - Code path trace

* **Dependencies**:
  * Task 5.1 completion
  * Phase 4 completion (logging module exists)

---

## Phase 6: Validation and Cleanup

### Task 6.1: Run full test suite

Verify all tests pass with adequate coverage.

* **Commands**:
  ```bash
  # Run all tests with coverage
  uv run pytest --cov=src/teambot --cov-report=term-missing
  
  # Run specific logging tests
  uv run pytest tests/test_config/test_loader.py -k logging -v
  uv run pytest tests/test_config/test_logging_config.py -v
  ```

* **Success**:
  * All tests pass (no failures)
  * Coverage for new files ≥ 90%
  * No regressions in existing tests

* **Dependencies**:
  * Phase 5 completion

---

### Task 6.2: Format and lint code

Ensure code meets project standards.

* **Commands**:
  ```bash
  # Format code
  uv run ruff format .
  
  # Check linting
  uv run ruff check . --fix
  
  # Verify formatting passes CI check
  uv run ruff format --check .
  ```

* **Success**:
  * No formatting changes needed
  * No lint errors
  * Code ready for commit

* **Dependencies**:
  * Task 6.1 completion

---

## Dependencies

* Python `logging` standard library module
* pytest 7.4.0+, pytest-cov 4.1.0+, pytest-mock 3.12.0+
* ruff 0.8.0+
* Existing `ConfigLoader` class in `src/teambot/config/loader.py`

## Success Criteria

* All Phase 1-3 TDD tests pass after corresponding implementation
* 90%+ test coverage for new code (`logging_config.py`, new `loader.py` code)
* Interactive mode has no console log pollution by default
* File orchestration mode shows logs on console
* `--log-to-console` flag works as documented
* Backwards compatibility verified (existing configs work unchanged)
* All lint and format checks pass
