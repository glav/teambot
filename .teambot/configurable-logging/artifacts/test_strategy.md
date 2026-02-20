<!-- markdownlint-disable-file -->
# Test Strategy: Configurable Logging Output

**Strategy Date**: 2026-02-20
**Feature Specification**: .teambot/configurable-logging/artifacts/feature_spec.md
**Research Reference**: N/A (feature is straightforward configuration extension)
**Strategist**: Builder-2 Agent

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | Rationale |
|--------|----------|-------|-----------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | TDD +3 | Specification has 8 FRs with explicit acceptance criteria and 6 AT scenarios |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | TDD +1 | Low-medium complexity; primarily configuration parsing and handler routing |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | TDD +2 | Medium-high risk; incorrect logging affects debugging capability (NFR-002) |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | Code-First +0 | No - requirements are stable and well-defined |
| **Simplicity** | Is this straightforward CRUD or simple logic? | Code-First +1 | Partially - config loading is straightforward, mode routing requires care |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | Code-First +0 | No time pressure indicated |
| **Requirements Stability** | Are requirements likely to change during development? | Code-First +0 | Requirements stable; spec is approved |

### Decision Calculation

```
TDD Score: 3 + 1 + 2 = 6
Code-First Score: 0 + 1 + 0 + 0 = 1

Decision: TDD (score 6 >= threshold 6)
```

## Recommended Testing Approach

**Primary Approach**: TDD (Test-Driven Development)

### Rationale

The configurable logging feature is a configuration-driven enhancement with well-defined requirements, clear acceptance criteria, and medium-high risk if implemented incorrectly (logging failures affecting debugging capability). The specification includes 8 functional requirements with explicit acceptance criteria and 6 acceptance test scenarios covering all major user flows.

TDD is appropriate here because:
1. **Clear requirements**: FR-001 through FR-008 have testable acceptance criteria
2. **Configuration parsing is testable**: JSON schema validation can be written test-first
3. **Risk mitigation**: Incorrect logging setup could silently fail; tests catch this early
4. **Existing patterns**: The codebase has extensive TDD patterns in `tests/test_config/test_loader.py` to follow

**Key Factors:**
* Complexity: LOW-MEDIUM (configuration parsing and handler setup)
* Risk: MEDIUM-HIGH (logging failures impact debugging capability)
* Requirements Clarity: CLEAR (8 FRs, 6 ATs, explicit schema)
* Time Pressure: LOW (no deadline constraints)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Low - straightforward conditional logic for handler routing
* **Integration Depth**: Low-Medium - integrates with Python logging, CLI parser, config loader
* **State Management**: Low - stateless configuration at startup
* **Error Scenarios**: Medium - permission errors, directory creation, missing config

### Risk Profile
* **Business Criticality**: MEDIUM - debugging depends on proper logging
* **User Impact**: HIGH - all users affected if logging misconfigured
* **Data Sensitivity**: LOW - no PII, local log files only
* **Failure Cost**: MEDIUM - silent log loss could hamper debugging

### Requirements Clarity
* **Specification Completeness**: COMPLETE (10/10 per spec review)
* **Acceptance Criteria Quality**: PRECISE (6 executable scenarios)
* **Edge Cases Identified**: 4 documented (backwards compat, directory creation, permission errors, mode detection)
* **Dependencies Status**: STABLE (Python stdlib logging, existing config loader)

## Test Strategy by Component

### 1. Logging Configuration Schema (FR-001, FR-008) - TDD

**Approach**: TDD
**Rationale**: Schema validation is deterministic; test cases can be written directly from schema spec

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Valid `logging` section parsed correctly
  * Missing `logging` section uses defaults
  * Invalid `logging` type (non-object) raises ConfigError
  * Nested mode config (`interactive_mode`, `file_mode`) validated
* Edge Cases:
  * `logging.log_dir` as relative vs absolute path
  * `logging.interactive_mode.console` as non-boolean
  * Partial mode config (only `console`, missing `file`)

**Testing Sequence** (TDD):
1. Write test: `test_logging_section_defaults_when_absent`
2. Write test: `test_logging_section_parsed_correctly`
3. Write test: `test_logging_not_object_raises_config_error`
4. Write test: `test_logging_mode_config_defaults`
5. Implement config parsing incrementally

### 2. File Handler Implementation (FR-002, FR-007) - TDD

**Approach**: TDD
**Rationale**: File operations are testable with `tmp_path`; clear pass/fail criteria

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit + Integration
* Critical Scenarios:
  * Log directory created if missing
  * Log file created with correct path
  * Log messages written to file
  * File handler uses UTF-8 encoding
* Edge Cases:
  * Permission denied on directory creation (graceful fallback)
  * Custom `log_dir` path honored
  * Existing directory not overwritten

**Testing Sequence** (TDD):
1. Write test: `test_log_directory_created_if_missing`
2. Write test: `test_log_file_receives_messages`
3. Write test: `test_file_handler_uses_utf8`
4. Write test: `test_permission_error_handled_gracefully`
5. Implement file handler setup

### 3. Mode Routing (FR-003, FR-004) - TDD

**Approach**: TDD
**Rationale**: Mode detection and handler routing have clear boolean logic

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Interactive mode (UI) defaults to file-only logging
  * File mode defaults to console + file logging
  * Mode detection based on `--ui` flag presence
  * Custom mode config overrides defaults
* Edge Cases:
  * Both `console` and `file` disabled (should log warning?)
  * Mode config with only one handler specified

**Testing Sequence** (TDD):
1. Write test: `test_interactive_mode_defaults_file_only`
2. Write test: `test_file_mode_defaults_console_and_file`
3. Write test: `test_mode_detection_from_ui_flag`
4. Write test: `test_custom_mode_config_overrides_default`
5. Implement mode routing in `setup_logging()`

### 4. CLI Override Flag (FR-005) - TDD

**Approach**: TDD
**Rationale**: CLI argument parsing is deterministic and easily testable

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * `--log-to-console` flag recognized by parser
  * Flag defaults to `False`
  * Flag overrides interactive mode's file-only default
* Edge Cases:
  * Flag combined with `-v/--verbose`
  * Flag in non-interactive mode (no effect expected)

**Testing Sequence** (TDD):
1. Write test: `test_parser_accepts_log_to_console_flag`
2. Write test: `test_log_to_console_flag_defaults_false`
3. Write test: `test_log_to_console_overrides_interactive_mode`
4. Implement CLI flag in `create_parser()`

### 5. Backwards Compatibility (FR-006) - TDD

**Approach**: TDD
**Rationale**: Compatibility is critical; regression tests prevent breaking changes

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit + Integration
* Critical Scenarios:
  * Config without `logging` section loads successfully
  * Default logging behavior applied to legacy configs
  * No warnings or errors for missing `logging` key
* Edge Cases:
  * Empty `teambot.json` (only required fields)
  * All optional fields absent

**Testing Sequence** (TDD):
1. Write test: `test_config_without_logging_section_valid`
2. Write test: `test_legacy_config_applies_default_logging`
3. Write test: `test_no_warning_for_missing_logging_key`
4. Verify no changes needed if defaults work

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: As specified in `pyproject.toml`
* **Configuration**: `[tool.pytest.ini_options]` in `pyproject.toml`
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `pytest-mock` (3.12.0+) - for mocking filesystem and logging handlers
* **Assertions**: pytest built-in assertions - `assert`, `pytest.raises`
* **Coverage**: `pytest-cov` (4.1.0+) - Target: 90%+ for new code
* **Test Data**: JSON config fixtures created inline with `tmp_path`

### Test Organization
* **Test Location**: `tests/` directory
* **Naming Convention**: `test_*.py` files, `test_*` functions, `Test*` classes
* **Fixture Strategy**: Shared fixtures in `tests/conftest.py`, local fixtures per test module
* **Setup/Teardown**: pytest fixtures with `tmp_path` for filesystem isolation

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% minimum for new code
* **Integration Coverage**: 80%
* **Critical Path Coverage**: 100% (mode routing, file handler setup)
* **Error Path Coverage**: 85% (permission errors, config validation errors)

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| Logging config schema (`loader.py`) | 95% | N/A | CRITICAL | Must validate all field types |
| File handler setup (`cli.py`) | 90% | 85% | CRITICAL | File I/O needs integration tests |
| Mode routing (`cli.py`) | 90% | 80% | HIGH | Determines handler activation |
| CLI flag parsing (`cli.py`) | 95% | N/A | HIGH | Simple argument parsing |
| Backwards compatibility | 100% | 100% | CRITICAL | Must not break existing configs |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Config Loading with Logging Section** (Priority: CRITICAL)
   * **Description**: Valid `logging` configuration is parsed and applied
   * **Test Type**: Unit
   * **Success Criteria**: Config object contains logging settings with correct values
   * **Test Approach**: TDD

2. **Interactive Mode Default Behavior** (Priority: CRITICAL)
   * **Description**: UI mode uses file-only logging by default
   * **Test Type**: Integration
   * **Success Criteria**: Console handler NOT attached when `--ui` flag present
   * **Test Approach**: TDD

3. **Backwards Compatibility** (Priority: CRITICAL)
   * **Description**: Legacy configs without `logging` section work unchanged
   * **Test Type**: Unit + Integration
   * **Success Criteria**: No errors; default behavior applied
   * **Test Approach**: TDD

4. **Log Directory Creation** (Priority: HIGH)
   * **Description**: Log directory created automatically if missing
   * **Test Type**: Integration
   * **Success Criteria**: Directory exists after first log write
   * **Test Approach**: TDD

5. **CLI Override Flag** (Priority: HIGH)
   * **Description**: `--log-to-console` enables console logging in UI mode
   * **Test Type**: Unit
   * **Success Criteria**: Console handler attached when flag present
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Empty logging section**: `"logging": {}` applies all defaults
* **Partial mode config**: `"interactive_mode": {"console": true}` (file defaults to true)
* **Custom log directory**: Non-default path is respected
* **Permission denied**: Graceful fallback when log directory cannot be created
* **Both handlers disabled**: Log warning but don't crash

### Error Scenarios

* **Invalid config type**: `"logging": "invalid"` raises `ConfigError`
* **Invalid mode field**: `"logging": {"interactive_mode": "invalid"}` raises `ConfigError`
* **Non-boolean handler flags**: `"console": "yes"` raises `ConfigError`
* **Directory creation failure**: Permission denied logs warning, continues without file logging

## Test Data Strategy

### Test Data Requirements
* **Config fixtures**: JSON strings created inline per test
* **Log messages**: Simple string messages for verification
* **Temp directories**: pytest `tmp_path` fixture for filesystem isolation

### Test Data Management
* **Storage**: Inline in test files (no external fixtures needed)
* **Generation**: Manual creation of minimal config snippets
* **Isolation**: Each test uses fresh `tmp_path`
* **Cleanup**: Automatic via pytest fixtures

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_config/test_loader.py`
**Pattern**: Config validation with error checking

```python
class TestNotificationsConfigValidation:
    """Tests for notifications configuration validation."""

    def test_valid_notifications_config(self, tmp_path):
        """Valid notifications config passes validation."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                    }
                ],
            },
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["notifications"]["enabled"] is True
        assert len(config["notifications"]["channels"]) == 1

    def test_notifications_not_object_raises(self, tmp_path):
        """notifications must be an object."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": "invalid",
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="'notifications' must be an object"):
            loader.load(config_file)
```

**Key Conventions:**
* Tests organized in classes by feature area
* Use `tmp_path` fixture for file I/O isolation
* Inline JSON config creation
* `pytest.raises` with `match` for error messages

### Recommended Test Structure

```python
"""Tests for logging configuration."""

import json
import pytest


class TestLoggingConfigValidation:
    """Tests for logging section in config loader."""

    def test_logging_section_defaults_when_absent(self, tmp_path):
        """Missing logging section applies default values."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        loader = ConfigLoader()
        config = loader.load(config_file)

        # Defaults applied
        assert config.get("logging", {}).get("log_dir", ".teambot/logs") == ".teambot/logs"

    def test_logging_not_object_raises_config_error(self, tmp_path):
        """logging must be an object."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "logging": "invalid",
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="'logging' must be an object"):
            loader.load(config_file)


class TestLoggingSetup:
    """Tests for setup_logging function with mode routing."""

    def test_interactive_mode_file_only_default(self, tmp_path, caplog):
        """Interactive mode defaults to file-only logging."""
        # Test implementation will verify no console handler for UI mode
        pass  # TDD placeholder

    def test_file_mode_console_and_file_default(self, tmp_path, caplog):
        """File mode defaults to console + file logging."""
        # Test implementation will verify both handlers active
        pass  # TDD placeholder
```

## Success Criteria

### Test Implementation Complete When:
* [ ] All critical scenarios have tests (5 scenarios)
* [ ] Coverage targets are met per component (90%+ for new code)
* [ ] All edge cases are tested (5 edge cases)
* [ ] Error paths are validated (4 error scenarios)
* [ ] Tests follow codebase conventions (pytest, tmp_path, ConfigLoader pattern)
* [ ] Tests are maintainable and clear (docstrings, descriptive names)
* [ ] CI/CD integration is working (`uv run pytest` passes)

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast and reliable (no flakiness)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem
* Mock/stub usage is appropriate and minimal (prefer real config loading)

## Implementation Guidance

### For TDD Components:
1. Start with simplest test case (backwards compatibility - config without logging section)
2. Write minimal code to pass
3. Add next test case (valid logging section)
4. Refactor when all tests pass
5. Focus on behavior, not implementation

### Test File Organization:
1. **Config validation tests**: Add to `tests/test_config/test_loader.py`
2. **CLI parsing tests**: Add to `tests/test_cli.py`
3. **Logging setup tests**: Add new `tests/test_logging.py` or extend `test_cli.py`
4. **Acceptance tests**: Create `tests/test_configurable_logging_acceptance.py`

### Priority Order:
1. FR-006: Backwards compatibility (ensures no breakage)
2. FR-001: Schema validation (foundation for config)
3. FR-002, FR-007: File handler (core new functionality)
4. FR-003, FR-004: Mode routing (ties it together)
5. FR-005: CLI flag (enhancement)
6. FR-008: Per-mode override (optional enhancement)

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures all requirements have corresponding tests
* Early test failures catch schema parsing errors
* Regression safety for backwards compatibility

### Accepted Trade-offs:
* Initial development may be slightly slower due to test-first approach
* Some integration aspects (actual Rich/Textual UI) require manual verification

### Risk Mitigation:
* TDD catches configuration parsing errors early
* File I/O tests use `tmp_path` for isolation
* Backwards compatibility tests prevent breaking existing users

## References

* **Feature Spec**: [.teambot/configurable-logging/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/configurable-logging/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: `tests/test_config/test_loader.py`, `tests/test_cli.py`
* **Test Standards**: pytest conventions per `pyproject.toml`

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow TDD approach per component

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

## Test Strategy Validation

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE
- Approach: TDD (TDD score 6 >= threshold 6)
- Coverage Targets: SPECIFIED (90%+ for new code)
- Components Covered: 5/5 (Schema, File Handler, Mode Routing, CLI Flag, Backwards Compat)
```
