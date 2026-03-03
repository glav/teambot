<!-- markdownlint-disable-file -->
# Task Research Document: Configurable Logging for TeamBot

This research investigates the implementation requirements for configurable logging in TeamBot to prevent log messages from interfering with the Rich/Textual interactive UI. The feature enables mode-aware logging: file-only in interactive mode (clean UI) and console+file in orchestration mode (debugging visibility).

## 🎉 Critical Finding: Feature Already Implemented

**All code changes for configurable logging are 100% complete.** The only remaining work is **documentation updates**.

## Task Implementation Requests

* ✅ ~~Add `logging` configuration section to `teambot.json` schema~~ **DONE**
* ✅ ~~Create logging configuration module~~ **DONE** (`src/teambot/config/logging_config.py`)
* ✅ ~~Update `setup_logging()` with mode detection~~ **DONE**
* ✅ ~~Add `--log-to-console` CLI override flag~~ **DONE** (`cli.py` line 565)
* ✅ ~~Add default log file location~~ **DONE** (`.teambot/logs/teambot.log`)
* ✅ ~~Update `ConfigLoader` validation~~ **DONE** (`loader.py` lines 269-339)
* ✅ ~~Write unit tests~~ **DONE** (18 tests in `test_logging_config.py`)
* 📄 **Documentation task**: Add "Logging and Debugging" section to `docs/guides/configuration.md`
* 📄 **Documentation task**: Update `docs/guides/cli-reference.md` with `--log-to-console` flag
* 📄 **Documentation task**: Document all logging configuration options with examples

## Scope and Success Criteria

* **Scope**: Verify existing implementation meets all requirements, identify documentation gaps
* **Exclusions**: Log aggregation, remote logging, structured logging formats (JSON)
* **Assumptions**:
  1. Existing `teambot.json` files without `logging` section work (backwards compatible) ✅
  2. Interactive mode = Textual/Rich split-pane UI (`TeamBotApp`)
  3. File-based mode = orchestration via `teambot run objectives/file.md`

* **Success Criteria**:
  * ✅ Logging output configuration added to `teambot.json` schema
  * ✅ Interactive UI mode defaults to file-only logging (no console output)
  * ✅ File-based orchestration mode defaults to console logging
  * ✅ Both modes support file logging (always available for debugging)
  * ✅ Configuration is overridable per mode
  * ✅ No breaking changes to existing configurations (backwards compatible)
  * ✅ Clean interactive UI experience with no log message interference
  * ✅ CLI override flag `--log-to-console` available for debugging interactive mode
  * ⚠️ **Documentation**: Add "Logging and Debugging" section to `docs/guides/configuration.md` - **NOT DONE**
  * ⚠️ **Documentation**: Update `docs/guides/cli-reference.md` with `--log-to-console` flag - **NOT DONE**
  * ⚠️ **Documentation**: Document all logging configuration options with examples - **NOT DONE**

## Outline

1. Entry Point Analysis - How logging configuration flows through the system
2. Implementation Verification - Confirming existing code meets requirements
3. Configuration Schema - JSON schema and validation (verified complete)
4. Test Coverage - Existing test suite (18 tests)
5. Documentation Gap Analysis - What documentation is missing

### Potential Next Research

* None - all code implementation research is complete
* Only documentation tasks remain

## Research Executed

### Entry Point Analysis

| Entry Point | Code Path | Feature Implemented? | Notes |
|-------------|-----------|---------------------|-------|
| `teambot run` (no objective) | `cli.py:main()` → `cmd_run()` → `is_interactive_mode()` → `setup_mode_logging()` | ✅ YES | Interactive mode, console disabled by default |
| `teambot run objectives/task.md` | `cli.py:main()` → `cmd_run()` → `is_interactive_mode()` → `setup_mode_logging()` | ✅ YES | Orchestration mode, console enabled by default |
| `teambot run --log-to-console` | `cli.py:main()` → `cmd_run()` → `setup_mode_logging(force_console=True)` | ✅ YES | Force console in any mode |
| `teambot run -v` / `--verbose` | `cli.py:main()` → `setup_logging(verbose=True)` + `setup_mode_logging(verbose=True)` | ✅ YES | Sets DEBUG level |
| `teambot.json` logging config | `ConfigLoader.load()` → `_validate_logging()` → `_apply_defaults()` | ✅ YES | All config options validated |

#### Code Path Trace

**Entry Point 1: Interactive Mode (`teambot run`)**
1. User runs: `teambot run`
2. Handled by: `cli.py:main()` (line 1300)
3. Routes to: `cli.py:cmd_run()` (line 1332)
4. Loads config: `ConfigLoader().load(config_path)` (line 910)
5. Validates logging: `_validate_logging()` (line 165-166)
6. Applies defaults: `_apply_defaults()` (lines 329-339)
7. Checks mode: `is_interactive_mode(has_objective=False)` → returns `True` (line 919)
8. Configures logging: `setup_mode_logging(is_interactive=True)` (lines 920-925)
9. Result: Console handler NOT added, file handler added ✅

**Entry Point 2: Orchestration Mode (`teambot run objectives/task.md`)**
1. User runs: `teambot run objectives/task.md`
2. Handled by: `cli.py:main()` (line 1300)
3. Routes to: `cli.py:cmd_run()` (line 1332)
4. Checks mode: `is_interactive_mode(has_objective=True)` → returns `False` (line 919)
5. Configures logging: `setup_mode_logging(is_interactive=False)` (lines 920-925)
6. Result: Console handler added, file handler added ✅

**Entry Point 3: Debug Override (`--log-to-console`)**
1. User runs: `teambot run --log-to-console`
2. Parser captures: `args.log_to_console = True` (line 565)
3. Configures logging: `setup_mode_logging(force_console=True)` (line 923)
4. Result: Console handler added regardless of mode ✅

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| None | N/A | All code paths implemented |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] No coverage gaps found
- [x] **Result: Feature is fully implemented**

### Testing Infrastructure Research

* **Framework**: pytest 7.4.0 with pytest-cov, pytest-mock, pytest-asyncio
  * Location: `tests/` directory (mirrors `src/` structure)
  * Naming: `test_*.py` pattern, class `Test*`, function `test_*`
  * Runner: `uv run pytest` (from `pyproject.toml`)
  * Coverage: `--cov=src/teambot --cov-report=term-missing`

### Test Patterns Found

* **File**: `tests/test_config/test_logging_config.py` (Lines 1-377)
  * **18 comprehensive tests** covering all logging scenarios
  * `TestIsInteractiveMode`: 4 tests for mode detection
  * `TestSetupLogging`: 14 tests for handler configuration
  * Uses `monkeypatch` for environment variable mocking
  * Uses `tmp_path` fixture for temporary log file creation
  * Tests both positive and negative cases (permission errors, OS errors)
  * Clear arrange-act-assert structure with descriptive docstrings

* **File**: `tests/test_config/test_loader.py` (Lines 672-780)
  * Logging validation tests for ConfigLoader
  * Tests schema validation for all logging fields
  * Tests default application for missing fields

### Coverage Standards

* **Unit Tests**: Comprehensive coverage of logging_config.py
* **Integration Tests**: CLI integration covered via test_loader.py
* **Critical Paths**: All error paths tested (permission denied, OS errors)

### Testing Approach Recommendation

* **Documentation changes**: No automated testing required
* **If future code changes needed**: Code-First (existing patterns are well-established)

**Rationale**: The logging feature is already fully implemented with comprehensive test coverage. Only documentation updates are needed.

---

## Key Discoveries

### 🎉 Critical Finding: Feature is Complete

The configurable logging feature is **100% implemented** in the codebase:

| Component | Location | Status |
|-----------|----------|--------|
| Logging Config Module | `src/teambot/config/logging_config.py` (111 lines) | ✅ Complete |
| Config Validation | `src/teambot/config/loader.py` (lines 269-339) | ✅ Complete |
| CLI Integration | `src/teambot/cli.py` (lines 565-568, 915-925) | ✅ Complete |
| Unit Tests | `tests/test_config/test_logging_config.py` (377 lines, 18 tests) | ✅ Complete |

### Project Structure

```
src/teambot/
├── config/
│   ├── loader.py           # Config validation (_validate_logging, _apply_defaults)
│   └── logging_config.py   # Mode-aware logging setup (is_interactive_mode, setup_logging)
├── cli.py                  # --log-to-console flag (L565), setup integration (L915-925)
└── ...

tests/test_config/
├── test_loader.py          # Logging validation tests (lines 672-780)
└── test_logging_config.py  # Comprehensive logging tests (18 tests)
```

### Implementation Patterns (Verified in Codebase)

**Mode Detection** (`logging_config.py` Lines 16-37):
```python
def is_interactive_mode(has_objective: bool) -> bool:
    """Determine if running in interactive UI mode."""
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
```

**Console Handler Logic** (`logging_config.py` Lines 96-110):
```python
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
```

### Configuration Schema (Verified in Codebase)

**JSON Schema** (from `loader.py` lines 269-299):
```json
{
  "logging": {
    "console_output": true | false | null,  // null = mode-dependent
    "file_output": true | false,            // default: true
    "log_file": "string",                   // default: ".teambot/logs/teambot.log"
    "level": "DEBUG" | "INFO" | "WARNING" | "ERROR"  // default: "INFO"
  }
}
```

**Default Application** (from `loader.py` lines 329-339):
```python
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

### API and Schema Documentation

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `console_output` | `boolean \| null` | `null` | `null` = auto (off for interactive, on for orchestration). `true` = always on. `false` = always off. |
| `file_output` | `boolean` | `true` | Enable/disable file logging |
| `log_file` | `string` | `.teambot/logs/teambot.log` | Path to log file |
| `level` | `string` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |

### CLI Flags (Verified in Codebase)

| Flag | Location | Description |
|------|----------|-------------|
| `--log-to-console` | `cli.py` line 565-568 | Force console output in any mode |
| `-v, --verbose` | `cli.py` line 527 | Sets log level to DEBUG |

---

## Technical Scenarios

### 1. Documentation Updates Required (Only Remaining Task)

The code is complete. Only documentation needs to be added.

**Requirements:**
* Add "Logging and Debugging" section to `docs/guides/configuration.md`
* Update `docs/guides/cli-reference.md` with `--log-to-console` flag
* Document all logging configuration options with examples

**Preferred Approach:**
* Add comprehensive documentation following existing guide patterns

```text
docs/guides/
├── configuration.md     # Add "Logging and Debugging" section after line 266 (after Notifications)
└── cli-reference.md     # Add --log-to-console to run command options table (around line 30)
```

**Implementation Details:**

#### Documentation for `configuration.md`

Add after the Notifications section (line 266):

```markdown
## Logging and Debugging

TeamBot provides configurable logging that adapts to your execution mode.

### Default Behavior

| Mode | Console Output | File Output |
|------|---------------|-------------|
| Interactive (`teambot run`) | ❌ Disabled | ✅ Enabled |
| Orchestration (`teambot run objective.md`) | ✅ Enabled | ✅ Enabled |

This ensures a clean interactive UI experience while preserving full logs for debugging.

### Configuration Options

\`\`\`json
{
  "logging": {
    "console_output": null,
    "file_output": true,
    "log_file": ".teambot/logs/teambot.log",
    "level": "INFO"
  }
}
\`\`\`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `console_output` | `boolean \| null` | `null` | `null` = auto (mode-dependent), `true` = always on, `false` = always off |
| `file_output` | `boolean` | `true` | Enable file logging |
| `log_file` | `string` | `.teambot/logs/teambot.log` | Log file path |
| `level` | `string` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |

### CLI Override

Force console output in interactive mode for debugging:

\`\`\`bash
teambot run --log-to-console
\`\`\`

Enable verbose (DEBUG level) logging:

\`\`\`bash
teambot run -v
# or
teambot run --verbose
\`\`\`

### Examples

**Disable all file logging:**
\`\`\`json
{
  "logging": {
    "file_output": false
  }
}
\`\`\`

**Always show console output (even in interactive mode):**
\`\`\`json
{
  "logging": {
    "console_output": true
  }
}
\`\`\`

**Custom log file location:**
\`\`\`json
{
  "logging": {
    "log_file": "logs/teambot-debug.log",
    "level": "DEBUG"
  }
}
\`\`\`
```

#### Documentation for `cli-reference.md`

Update the `teambot run` options table (around line 30) to include:

```markdown
| `--log-to-console` | Enable console logging output (useful for debugging interactive mode) |
```

#### Considered Alternatives (Removed After Selection)

None - documentation approach follows existing patterns.

---

## Validation Summary

```
RESEARCH_VALIDATION: PASS
- Document: CREATED ✅
- Placeholders: 0 remaining ✅
- Technical Approach: DOCUMENTED (feature already implemented) ✅
- Entry Points: 5 traced, 5 covered ✅
- Test Infrastructure: RESEARCHED (18 tests, comprehensive coverage) ✅
- Implementation Ready: YES (documentation only) ✅
```
