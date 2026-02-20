<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Configurable Logging Output - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot Core | Target v0.2.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-20 |
| Problem & Users | ✅ | None | 2026-02-20 |
| Scope | ✅ | None | 2026-02-20 |
| Requirements | ✅ | None | 2026-02-20 |
| Metrics & Risks | ✅ | None | 2026-02-20 |
| Operationalization | ✅ | None | 2026-02-20 |
| Finalization | ⏳ | Pending review | 2026-02-20 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot is a CLI tool that orchestrates multi-agent AI workflows using Rich and Textual for interactive terminal displays. The current logging implementation outputs all log messages to the console (stderr), which interferes with the interactive UI rendering. Log messages appear briefly then get partially cleared during UI refreshes, creating visual artifacts and a poor user experience.

### Core Opportunity
Implement configuration-driven logging output control that separates console output by execution mode, enabling a clean interactive UI while preserving full debugging capability through file-based logging.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Eliminate log interference with interactive UI | UX Quality | 100% interference | 0% interference | v0.2.0 | P0 |
| G-002 | Preserve debugging capability | Maintainability | Console-only | Console + File | v0.2.0 | P0 |
| G-003 | Enable configuration flexibility | Usability | No config | Per-mode config | v0.2.0 | P1 |
| G-004 | Maintain backwards compatibility | Stability | N/A | 100% compatible | v0.2.0 | P0 |

### Objectives (Optional)
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Clean UI Experience | Zero log messages visible in interactive mode by default | P0 | Builder |
| Debugging Support | All log messages persisted to file for troubleshooting | P0 | Builder |
| Developer Override | CLI flag available for console logging when debugging | P1 | Builder |

## 2. Problem Definition

### Current Situation
- Logging configured via `setup_logging()` in `cli.py` using Python's `logging.basicConfig()`
- All log output goes to console (stderr) by default
- No file-based logging handlers exist
- Textual UI uses `RichLog` widget for output display (separate from logging system)
- No `logging` section exists in `teambot.json` schema
- Only control available is `-v/--verbose` flag for log level (INFO vs DEBUG)

### Problem Statement
When running TeamBot in interactive UI mode, log messages (e.g., `INFO: Starting agent...`, `DEBUG: Processing message...`) print to the console and are then partially overwritten or cleared when the Rich/Textual UI refreshes. This creates:
1. **Visual noise**: Fragmented log text mixed with UI elements
2. **Unreadable logs**: Messages truncated mid-display
3. **Poor UX**: Users cannot focus on agent interactions
4. **No alternative**: Users must choose between debugging info OR clean UI

### Root Causes
* Python logging outputs to stderr by default, which is the same output stream the terminal UI renders to
* No execution-mode-aware logging configuration exists
* No file-based logging alternative is implemented
* `logging.basicConfig()` provides no console/file routing options

### Impact of Inaction
Continued poor user experience with cluttered, unreadable interactive displays. Users will lose trust in the tool's polish and professionalism. Debugging will remain difficult as log messages are ephemeral and unreadable.

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| End User | Clean, focused interaction with AI agents | Log messages disrupt UI, hard to read agent responses | High - Primary user of interactive mode |
| Developer | Debug issues, understand agent behavior | Logs disappear when UI refreshes, no persistence | High - Cannot troubleshoot effectively |
| DevOps/Admin | Review logs post-session, diagnose failures | No log files exist for analysis | Medium - Cannot perform post-mortem |

### Journeys (Optional)
**End User Interactive Session**:
1. Runs `teambot run --ui` to start interactive session
2. Expects clean terminal UI with agent panels
3. Currently sees: Log messages flash, get overwritten, visual chaos
4. Expected: Clean UI, logs silently written to file

**Developer Debugging Session**:
1. Runs `teambot run --ui` and encounters unexpected behavior
2. Needs to see detailed log output for debugging
3. Currently: Must run without UI or accept visual chaos
4. Expected: Can add `--log-to-console` flag or check `.teambot/logs/`

## 4. Scope

### In Scope
* Add `logging` configuration section to `teambot.json` schema
* Implement mode-aware logging output routing (console vs file)
* Add file handler support with configurable log file path
* Add `--log-to-console` CLI flag for interactive mode debugging
* Default interactive UI mode to file-only logging
* Default file-based orchestration mode to console logging
* Ensure backwards compatibility with existing configurations

### Out of Scope (justify if empty)
* Log rotation and retention policies (complexity; can be added later)
* Log aggregation or external log shipping (out of MVP scope)
* Structured logging / JSON format (future enhancement)
* Per-agent log configuration (excessive complexity for initial release)
* Log level configuration per mode (can use existing `-v` flag)

### Assumptions
* Users accept that interactive mode will not show logs on console by default
* A CLI override (`--log-to-console`) is sufficient for debugging interactive mode
* File logging introduces acceptable disk I/O overhead
* Log rotation is acceptable to defer to a future release
* Default log directory `.teambot/logs/` is acceptable

### Constraints
* **Minimal code changes**: Solution should be primarily configuration-driven
* **No log loss**: All log data must be capturable (via file if not console)
* **Backwards compatible**: Existing `teambot.json` files must work without changes
* **Python stdlib**: Use standard library `logging` module (no new dependencies)

## 5. Product Overview

### Value Proposition
TeamBot users get a clean, professional interactive UI experience without sacrificing debugging capability. Logs are always available in files for troubleshooting, and developers can optionally enable console logging when needed.

### Differentiators (Optional)
* Mode-aware defaults reduce configuration burden
* Single CLI flag enables debugging without config changes
* Backwards compatible design protects existing users

### UX / UI (Conditional)
No UI changes required. The feature removes visual noise from the existing UI. | UX Status: Improved by absence of interference

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Schema Extension | Add `logging` section to `teambot.json` schema with fields: `log_dir`, `interactive_mode`, `file_mode` | G-003 | Developer, Admin | P0 | Config file with `logging` section is parsed correctly | See schema below |
| FR-002 | File Handler Support | Implement file-based logging handler writing to configurable directory | G-002 | Developer, Admin | P0 | Logs written to `.teambot/logs/teambot.log` | Auto-create directory |
| FR-003 | Interactive Mode Default | Interactive UI mode defaults to file-only logging (no console) | G-001 | End User | P0 | No log messages on console during `--ui` mode | Console handler disabled |
| FR-004 | File Mode Default | File-based orchestration mode defaults to console + file logging | G-002 | Developer | P1 | Logs appear on console and in file | Both handlers active |
| FR-005 | CLI Override Flag | Add `--log-to-console` CLI flag to enable console logging in interactive mode | G-002, G-003 | Developer | P1 | Flag enables console output in UI mode | Override config |
| FR-006 | Backwards Compatibility | Existing `teambot.json` files without `logging` section use sensible defaults | G-004 | All | P0 | Old configs work unchanged | Default values applied |
| FR-007 | Log Directory Creation | Automatically create log directory if it doesn't exist | G-002 | All | P0 | Directory created on first log write | Handle permission errors gracefully |
| FR-008 | Per-Mode Config Override | Allow `interactive_mode` and `file_mode` to specify `console` and `file` booleans | G-003 | Developer | P2 | Custom mode configs applied | Optional override |

### Configuration Schema

```json
{
  "logging": {
    "log_dir": ".teambot/logs",
    "interactive_mode": {
      "console": false,
      "file": true
    },
    "file_mode": {
      "console": true,
      "file": true
    }
  }
}
```

**Default Values** (when `logging` section is absent):
- `log_dir`: `.teambot/logs`
- `interactive_mode.console`: `false`
- `interactive_mode.file`: `true`
- `file_mode.console`: `true`
- `file_mode.file`: `true`

### Feature Hierarchy (Optional)
```plain
Configurable Logging
├── Configuration (FR-001, FR-006, FR-008)
│   ├── Schema extension
│   ├── Default values
│   └── Per-mode overrides
├── File Logging (FR-002, FR-007)
│   ├── File handler implementation
│   └── Directory auto-creation
├── Mode Routing (FR-003, FR-004)
│   ├── Interactive mode (file-only default)
│   └── File mode (console+file default)
└── CLI Override (FR-005)
    └── --log-to-console flag
```

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Performance | File logging should not noticeably impact CLI responsiveness | <50ms overhead per session | P1 | Benchmark before/after | Buffered writes |
| NFR-002 | Reliability | Logging failures should not crash the application | 0 crashes from logging | P0 | Exception handling | Graceful degradation |
| NFR-003 | Maintainability | Logging configuration should be self-documenting | Config matches docs | P2 | Review | Clear field names |
| NFR-004 | Observability | All log messages must be capturable via file output | 100% log capture | P0 | Test verification | No silent drops |
| NFR-005 | Security | Log files should not contain secrets (tokens, passwords) | 0 secrets in logs | P0 | Code review | Filter sensitive data |
| NFR-006 | Usability | Default behavior should require zero configuration | Works out-of-box | P0 | Fresh install test | Sensible defaults |

Categories: Performance, Reliability, Scalability, Security, Privacy, Accessibility, Observability, Maintainability, Localization (if), Compliance (if).

## 8. Data & Analytics (Conditional)

### Inputs
- `teambot.json` configuration file (optional `logging` section)
- CLI arguments (`--log-to-console`, `-v/--verbose`)
- Execution mode detection (interactive vs file-based)

### Outputs / Events
- Log file at `{log_dir}/teambot.log`
- Console output (when enabled)

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|--------|---------|-------|
| logging_configured | App startup | mode, handlers_active | Track logging mode usage | Builder |
| log_file_created | First log write | file_path | Confirm file logging works | Builder |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| UI visual artifacts | Quality | Present | Absent | Per session | Manual test |
| Log file creation rate | Reliability | 0% | 100% | Per session | File existence |
| Config parse errors | Quality | 0 | 0 | Per release | Error logs |

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| `teambot.json` schema | Internal | High | Builder | Schema changes break loaders | Add to existing loader |
| `setup_logging()` in cli.py | Internal | High | Builder | Function signature change | Add optional params |
| CLI argument parser | Internal | Medium | Builder | New flag conflicts | Check existing flags |
| Python `logging` module | External | Low | Python stdlib | Stable API | Use standard patterns |
| `.teambot/` directory | Internal | Low | Builder | May not exist | Create if missing |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Breaking existing configs | High | Low | Schema extension with defaults; no required fields | Builder | Mitigated |
| R-002 | Log file permission denied | Medium | Medium | Graceful error handling; fallback to console | Builder | Open |
| R-003 | Disk space exhaustion | Low | Low | Document in user guide; out of scope for v1 | Writer | Accepted |
| R-004 | Log file locking on Windows | Medium | Low | Use standard logging handlers with thread safety | Builder | Mitigated |
| R-005 | Mode detection incorrect | Medium | Low | Explicit mode detection logic; test coverage | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
Log files may contain:
- Session metadata (timestamps, command names)
- Agent interactions (prompts, responses)
- Error messages and stack traces

Classification: **Internal** - No PII or secrets by design

### PII Handling
- No PII should be logged by design
- Agent prompts may contain user-provided content; users control what they input
- Log files stored locally; no transmission

### Threat Considerations
- Log files readable by local user only (default file permissions)
- No secrets should be logged (ensure environment variables not logged)
- Log injection attacks: Low risk (logs not parsed or executed)

### Regulatory / Compliance (Conditional)
| Regulation | Applicability | Action | Owner | Status |
|-----------|--------------|--------|-------|--------|
| N/A | Local CLI tool | None required | - | N/A |

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Standard pip/uv install | No additional steps |
| Rollback | Remove `logging` config section | Defaults apply |
| Monitoring | Check log file existence/growth | Manual verification |
| Alerting | N/A (local CLI tool) | - |
| Support | Document in user guide | Troubleshooting section |
| Capacity Planning | N/A (local files) | User manages disk space |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|--------------|-------|
| Implementation | TBD | All FRs complete, tests pass | Builder |
| Testing | TBD | Unit + integration tests pass | Builder |
| Documentation | TBD | User guide updated | Writer |
| Release | TBD | All gates pass, PR merged | PM |

### Feature Flags (Conditional)
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|--------|----------------|
| N/A | Feature always enabled once released | - | - |

### Communication Plan (Optional)
- Update CHANGELOG.md with new feature
- Update README.md with logging configuration section
- Add troubleshooting section to user guide

## 14. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| None | All questions resolved | - | - | ✅ |

## 15. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-02-20 | BA Agent | Initial specification | Creation |

## 16. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Problem Statement | `.teambot/configurable-logging/artifacts/problem_statement.md` | Business problem, goals, success criteria | Primary source |
| REF-002 | Current Config | `teambot.json` | Existing schema structure | Extend, don't modify |
| REF-003 | Current Logging | `src/teambot/cli.py:setup_logging()` | Current logging implementation | Modify in place |

### Citation Usage
Problem statement cited for goals and success criteria. Current codebase analyzed for technical context.

## 17. Acceptance Test Scenarios

### AT-001: Interactive Mode Default Behavior
**Description**: Verify interactive UI mode does not show log messages on console by default
**Preconditions**: Fresh install, no `logging` section in `teambot.json`
**Steps**:
1. Run `teambot run objectives/test.md --ui`
2. Observe terminal output during agent execution
3. Check `.teambot/logs/teambot.log` for log content
**Expected Result**: No `INFO:`, `DEBUG:`, or logging output visible on terminal; clean UI renders without interference
**Verification**: Terminal shows only Textual UI elements; log file contains expected log messages

### AT-002: File Mode Default Behavior
**Description**: Verify file-based orchestration mode shows logs on console and writes to file
**Preconditions**: Fresh install, no `logging` section in `teambot.json`
**Steps**:
1. Run `teambot run objectives/test.md` (no `--ui` flag)
2. Observe console output
3. Check `.teambot/logs/teambot.log`
**Expected Result**: Log messages appear on console AND are written to log file
**Verification**: Console shows log output; file contains same messages

### AT-003: CLI Override in Interactive Mode
**Description**: Verify `--log-to-console` flag enables console logging in interactive mode
**Preconditions**: Standard install
**Steps**:
1. Run `teambot run objectives/test.md --ui --log-to-console`
2. Observe terminal output
**Expected Result**: Log messages appear on console (may interfere with UI, expected for debugging)
**Verification**: Console shows `INFO:` and `DEBUG:` messages; useful for debugging

### AT-004: Custom Configuration Applied
**Description**: Verify custom `logging` configuration is respected
**Preconditions**: `teambot.json` contains:
```json
{
  "logging": {
    "log_dir": ".custom-logs",
    "interactive_mode": {
      "console": true,
      "file": false
    }
  }
}
```
**Steps**:
1. Run `teambot run objectives/test.md --ui`
2. Observe console output
3. Check if `.custom-logs/teambot.log` exists
**Expected Result**: Console logging enabled; file logging disabled; custom directory used
**Verification**: Console shows logs; no file created in custom directory

### AT-005: Backwards Compatibility
**Description**: Verify existing `teambot.json` without `logging` section works unchanged
**Preconditions**: Existing `teambot.json` with agents, workflow, notifications (no `logging` key)
**Steps**:
1. Run `teambot run objectives/test.md --ui`
2. Verify application starts successfully
3. Verify default logging behavior applies
**Expected Result**: Application runs normally; defaults applied; no errors or warnings about missing config
**Verification**: No config parsing errors; interactive mode uses file-only logging by default

### AT-006: Log Directory Auto-Creation
**Description**: Verify log directory is created automatically if missing
**Preconditions**: `.teambot/logs/` directory does not exist
**Steps**:
1. Delete `.teambot/logs/` if it exists
2. Run `teambot run objectives/test.md`
3. Check if `.teambot/logs/` was created
**Expected Result**: Directory created automatically; log file written successfully
**Verification**: Directory exists; `teambot.log` file present with content

## 18. Appendices (Optional)

### Glossary
| Term | Definition |
|------|-----------|
| Interactive Mode | Running TeamBot with `--ui` flag using Textual TUI |
| File Mode | Running TeamBot without `--ui` flag (standard CLI output) |
| Log Handler | Python logging component that routes log messages to destinations |

### Additional Notes
- Log format remains: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Log level controlled by existing `-v/--verbose` flag (INFO default, DEBUG with flag)
- File handler uses `logging.FileHandler` with UTF-8 encoding

### Implementation Guidance

**Technical Stack**:
- Language: Python 3.x
- Framework: Python standard library `logging` module
- UI: Rich/Textual (no changes needed)

**Testing Approach**: Hybrid
- Unit tests for configuration loading and parsing
- Unit tests for logging handler setup logic
- Integration tests for mode detection
- Manual verification for UI visual experience

**Key Files to Modify**:
1. `src/teambot/cli.py` - `setup_logging()` function
2. `src/teambot/config/loader.py` - Add logging config parsing
3. `src/teambot/config/schema.py` - Add logging schema (if exists)
4. `tests/test_cli.py` - Add logging configuration tests
5. `tests/test_config/` - Add logging config loading tests

Generated 2026-02-20T04:28:40Z by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
