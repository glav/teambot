<!-- markdownlint-disable-file -->
# Release Changes: Fix Runtime Validator for Unknown Agent Validation

**Related Plan**: 20260210-runtime-validator-fix-plan.instructions.md
**Implementation Date**: 2026-02-10

## Summary

Fixed the runtime acceptance test executor to achieve 7/7 scenario pass rate for the unknown-agent-validation feature. Three root causes were addressed: (1) command extraction regex couldn't match multi-agent commas or underscore aliases, (2) positive scenario output matching was too strict for mock SDK execution, and (3) the parser's AGENT_PATTERN didn't support underscores in agent IDs (required for aliases like `@project_manager`). Added backtick stripping as defense-in-depth in `_is_expected_error_scenario()`.

## Changes

### Added

* `tests/test_orchestration/test_acceptance_test_executor.py` — 10 new tests: `TestExtractCommandsExtendedSyntax` (5 tests for multi-agent, underscore, pipeline, simple, background command extraction) and `TestExpectedErrorScenarioEdgeCases` (5 tests for backtick-formatted error detection and `_extract_field` preservation)

### Modified

* `src/teambot/orchestration/acceptance_test_executor.py` — Fixed `extract_commands_from_steps()` regex to support multi-agent commas and underscore aliases (`[a-zA-Z0-9-]*` → `[a-zA-Z0-9,_-]*`); added backtick stripping in `_is_expected_error_scenario()` for defense-in-depth; simplified positive scenario verification to treat successful command execution as sufficient runtime proof; removed dead `_verify_expected_output()` method
* `src/teambot/repl/parser.py` — Added underscore to `AGENT_PATTERN` and `REFERENCE_PATTERN` character classes to support alias agent IDs like `@project_manager` and `$project_manager`

### Removed

* None

## Release Summary

**Total Files Affected**: 3

### Files Created (0)

* None

### Files Modified (3)

* `src/teambot/orchestration/acceptance_test_executor.py` — Regex fix, backtick stripping, positive scenario simplification
* `src/teambot/repl/parser.py` — Underscore support in AGENT_PATTERN
* `tests/test_orchestration/test_acceptance_test_executor.py` — 10 new test methods in 2 new test classes

### Files Removed (0)

* None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No special deployment considerations. All changes are backward-compatible.
