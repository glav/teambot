## Objective

Configurable logging output to prevent log messages from interfering with the interactive terminal UI display.

**Goal**:
- Logging output (e.g., `INFO: <msg>`, `DEBUG: ...`) currently outputs to console which interferes with the Rich/Textual interactive terminal display
- Log messages appear, then get partially cleared on UI refresh, causing a messy visual experience
- Implement configuration-based control of logging output per execution mode

**Problem Statement**:
- When the interactive UI is active, Python logging messages write directly to stdout/stderr
- These messages interleave with Rich console output and Textual UI rendering
- The display appears corrupted until the next UI refresh cycle
- Heavy logging activity makes the experience especially disruptive
- Currently no way to suppress console logging while preserving log capture

**Success Criteria**:
- [ ] Logging output configuration added to `teambot.json` schema
- [ ] Interactive UI mode defaults to file-only logging (no console output)
- [ ] File-based orchestration mode defaults to console logging
- [ ] Both modes support file logging (always available for debugging)
- [ ] Configuration is overridable per mode
- [ ] No breaking changes to existing configurations (backwards compatible)
- [ ] Clean interactive UI experience with no log message interference
- [ ] CLI override flag `--log-to-console` available for debugging interactive mode

---

## Technical Context

**Target Codebase**: Existing teambot

**Primary Language/Framework**: Python (logging, Rich, Textual)

**Testing Preference**: Hybrid (unit tests for config loading, manual verification for UI)

**Key Constraints**:
- Minimal code changes - primarily configuration-driven
- Preserve all existing log capture capability (no log loss)
- Backwards compatible with existing `teambot.json` files
- Log file location should be configurable (default: `.teambot/logs/`)

---

## Proposed Configuration Schema

Add a new `logging` section to `teambot.json`:

```json
{
  "logging": {
    "level": "INFO",
    "file": {
      "enabled": true,
      "path": ".teambot/logs/teambot.log",
      "level": "DEBUG",
      "rotation": 10485760
    },
    "console": {
      "level": "WARNING",
      "interactive_ui": false,
      "file_based_orchestration": true
    },
    "format": "simple"
  }
}
```

| Field | Description | Default |
|-------|-------------|---------|
| `logging.level` | Global log level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `logging.file.enabled` | Enable file logging | `true` |
| `logging.file.path` | Log file path | `.teambot/logs/teambot.log` |
| `logging.file.level` | File-specific log level (overrides global) | *uses global* |
| `logging.file.rotation` | Max file size in bytes before rotation (optional) | `10485760` (10MB) |
| `logging.console.level` | Console-specific log level (overrides global) | *uses global* |
| `logging.console.interactive_ui` | Console output in interactive UI mode | `false` |
| `logging.console.file_based_orchestration` | Console output in file-based orchestration mode | `true` |
| `logging.format` | Log format: `"simple"` or `"detailed"` | `"simple"` |

---

## Implementation Approach

1. **Config schema extension**: Add `logging` section to JSON schema validation
2. **Logging setup modification**: Update `setup_logging()` in `cli.py` to read config and configure handlers based on execution mode
3. **Mode detection**: Pass execution mode (interactive vs file-based orchestration) to logging setup. Mode is determined by:
   - **Interactive UI mode**: When using `teambot repl` or any command that launches the Textual/Rich interactive interface
   - **File-based orchestration mode**: When using `teambot run` with objective files or non-interactive CLI commands
4. **File handler**: Add `logging.FileHandler` with optional rotation (`RotatingFileHandler`). Rotation size specified in bytes (e.g., `10485760` for 10MB)
5. **Console handler**: Conditionally add `StreamHandler` based on mode and config
6. **Per-handler levels**: Support independent log levels for file and console handlers
7. **Format support**: Implement `"simple"` (timestamp + level + message) and `"detailed"` (adds module, line number) formats

---

## Additional Context

- The `--verbose` CLI flag should continue to work, increasing log level to DEBUG
- CLI flag `--log-to-console` overrides config to force console output (useful for debugging interactive mode)
- Log file directory should be created automatically if it doesn't exist
- Existing config files without `logging` section should use sensible defaults

---

## Reviewer Feedback (Incorporated)

The following suggestions from the spec review have been incorporated:

1. ✅ **Per-handler log levels** - Added `file.level` and `console.level` to allow verbose file logging while keeping console quiet
2. ✅ **Clarified mode terminology** - Changed "orchestration mode" to "file-based orchestration mode" throughout; added mode detection explanation
3. ✅ **Added CLI override to success criteria** - `--log-to-console` flag now in scope
4. ✅ **Added log format option** - `format: "simple" | "detailed"` added to schema
5. ✅ **Rotation unit clarified** - Now specified in bytes (e.g., `10485760`) for direct compatibility with Python's `RotatingFileHandler`

---
