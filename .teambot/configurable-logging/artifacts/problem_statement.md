# Problem Statement: Configurable Logging Output

## Business Problem

TeamBot's logging output interferes with the interactive terminal UI, creating a poor user experience. Log messages (e.g., `INFO:`, `DEBUG:`) print to the console and are then partially cleared during Rich/Textual UI refreshes, resulting in visual artifacts and a cluttered display.

Users cannot currently control where log output is directed, forcing a trade-off between debugging visibility and a clean UI experience.

## Current State

| Aspect | Current Behavior |
|--------|------------------|
| Log destination | Console only (stderr) |
| File logging | Not implemented |
| Mode-specific config | None |
| User override | None (only `--verbose` flag for level) |
| UI impact | Log messages interfere with Rich/Textual display |

### Technical Context
- Logging configured via `setup_logging()` in `cli.py` using `logging.basicConfig()`
- Default level: `INFO`, verbose mode: `DEBUG`
- No log file handlers exist
- Textual UI uses `RichLog` widget for output display (separate from logging system)
- No logging section in `teambot.json` schema

## Desired State

| Aspect | Desired Behavior |
|--------|------------------|
| Log destination | Configurable per execution mode |
| File logging | Always available for debugging |
| Interactive UI mode | Defaults to file-only (no console interference) |
| File-based orchestration | Defaults to console logging |
| User override | CLI flag `--log-to-console` for debugging |
| Configuration | Via `teambot.json` with sensible defaults |

## Stakeholders

| Stakeholder | Interest |
|-------------|----------|
| End Users | Clean, readable interactive UI without visual artifacts |
| Developers | Access to debug logs when troubleshooting |
| Operations | Persistent log files for post-mortem analysis |

## Goals

1. **Clean Interactive Experience**: Eliminate log message interference with Rich/Textual terminal display
2. **Debugging Capability**: Preserve full logging capability via file output
3. **Configuration Flexibility**: Allow users to customize logging behavior per mode
4. **Backwards Compatibility**: Existing configurations continue to work without modification

## Success Criteria

| ID | Criterion | Measurable Outcome |
|----|-----------|-------------------|
| SC-1 | Schema extension | `logging` section added to `teambot.json` schema |
| SC-2 | Interactive mode default | File-only logging when running interactive UI |
| SC-3 | File mode default | Console logging when running file-based orchestration |
| SC-4 | File logging available | Both modes can log to file (default: `.teambot/logs/`) |
| SC-5 | Configuration override | Per-mode settings can be customized in config |
| SC-6 | Backwards compatible | Existing `teambot.json` files work without changes |
| SC-7 | Clean UI | No log messages appear in interactive terminal |
| SC-8 | CLI override | `--log-to-console` flag enables console logging for debugging |

## Constraints

- **Minimal code changes**: Solution should be primarily configuration-driven
- **No log loss**: All log data must be capturable (via file if not console)
- **Backwards compatible**: Existing configurations must continue to work
- **Configurable log path**: Default to `.teambot/logs/`, allow override

## Assumptions

1. Users accept that interactive mode will not show logs on console by default
2. A CLI override (`--log-to-console`) is sufficient for debugging interactive mode
3. File logging introduces acceptable disk I/O overhead
4. Log rotation is out of scope for initial implementation

## Dependencies

| Dependency | Description |
|------------|-------------|
| `teambot.json` schema | Must be extended to include logging configuration |
| `setup_logging()` | Must be modified to support file handlers |
| CLI argument parsing | Must add `--log-to-console` flag |

## Out of Scope

- Log rotation and retention policies
- Log aggregation or external log shipping
- Structured logging (JSON format)
- Per-agent log configuration

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing configs | Low | High | Schema extension with defaults |
| Log file permission issues | Medium | Medium | Document requirements, fail gracefully |
| Disk space from logging | Low | Low | Out of scope; document in user guide |

## Acceptance Criteria

The solution is accepted when:

1. Running `teambot run --ui` shows no log messages on console
2. Log messages are written to `.teambot/logs/teambot.log`
3. Running `teambot run` (file mode) shows log messages on console
4. Running `teambot run --ui --log-to-console` shows logs on console
5. A `teambot.json` without `logging` section uses sensible defaults
6. A `teambot.json` with `logging` section applies custom settings

---

**Document Version**: 1.0  
**Stage**: BUSINESS_PROBLEM  
**Status**: Draft  
**Last Updated**: 2026-02-20
