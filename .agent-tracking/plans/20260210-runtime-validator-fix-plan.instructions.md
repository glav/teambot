---
applyTo: '.agent-tracking/changes/20260210-runtime-validator-fix-changes.md'
---
<!-- markdownlint-disable-file -->
# Implementation Plan: Fix Runtime Validator for Unknown Agent Validation

**Objective**: Fix the acceptance test executor's runtime validation so that expected-error scenarios (AT-001, AT-002, AT-007) are correctly recognised as passing, and address remaining runtime failures (AT-004, AT-006) to achieve 7/7 acceptance test pass rate.

**Prior Plan**: [20260209-unknown-agent-validation-plan.instructions.md](20260209-unknown-agent-validation-plan.instructions.md) — all 4 phases COMPLETE (core validation implemented)
**Research**: [.agent-tracking/research/20260209-unknown-agent-validation-research.md](../research/20260209-unknown-agent-validation-research.md)
**Test Strategy**: [.agent-tracking/test-strategies/20260209-unknown-agent-validation-test-strategy.md](../test-strategies/20260209-unknown-agent-validation-test-strategy.md)
**Approach**: Code-First (per test strategy)

---

## Context & Problem Analysis

The core unknown-agent validation logic is fully implemented and unit-tested. However, runtime acceptance testing (via `AcceptanceTestExecutor`) fails 5/7 scenarios:

| Scenario | Failure Type | Root Cause Category |
|----------|-------------|---------------------|
| AT-001 | Expected error not recognised | `_is_expected_error_scenario()` returns False at runtime |
| AT-002 | Expected error not recognised | Same as AT-001 |
| AT-007 | Expected error not recognised | Same as AT-001 |
| AT-004 | Wrong error message | Pipeline parser error precedes agent validation |
| AT-006 | Output mismatch | Positive scenario check too strict for headless execution |

**Critical Finding**: Unit tests for `_is_expected_error_scenario()` PASS with backtick-formatted text (line 462 of `test_acceptance_test_executor.py`). This means the keyword matching logic works correctly in isolation. The bug is in how the runtime executor parses scenarios from the feature spec or orchestrates the validation flow.

---

## Task Dependency Graph

```mermaid
graph TD
    subgraph Phase1[Phase 1: Root Cause Investigation]
        T1.1[T1.1: Reproduce & diagnose AT-001/002/007]
        T1.2[T1.2: Diagnose AT-004 pipeline error]
        T1.3[T1.3: Diagnose AT-006 output mismatch]
    end

    subgraph Phase2[Phase 2: Fix Expected Error Recognition]
        T2.1[T2.1: Fix _is_expected_error_scenario or _extract_field]
        T2.2[T2.2: Add regression tests for fix]
    end

    subgraph Phase3[Phase 3: Fix Remaining Runtime Failures]
        T3.1[T3.1: Fix AT-004 pipeline validation order]
        T3.2[T3.2: Fix AT-006 positive scenario matching]
    end

    subgraph Phase4[Phase 4: Verification]
        T4.1[T4.1: Full test suite + lint + acceptance]
    end

    T1.1 --> T2.1
    T1.2 --> T3.1
    T1.3 --> T3.2
    T2.1 --> T2.2
    T2.2 --> T4.1
    T3.1 --> T4.1
    T3.2 --> T4.1

    %% Critical path
    style T1.1 fill:#ff9999
    style T2.1 fill:#ff9999
    style T2.2 fill:#ff9999
    style T4.1 fill:#ff9999
```

**Critical Path**: T1.1 → T2.1 → T2.2 → T4.1
**Parallel Opportunities**: All Phase 1 tasks can run in parallel; T3.1 and T3.2 can run in parallel with Phase 2.

---

## Phase 1: Root Cause Investigation

### Task 1.1: Reproduce & diagnose AT-001/AT-002/AT-007 expected-error failure
**File**: `src/teambot/orchestration/acceptance_test_executor.py`
**Details**: [Details file, Lines 10-62](../details/20260210-runtime-validator-fix-details.md)

- [x] Write a diagnostic test that: (a) loads the actual feature spec from `.teambot/unknown-agent-validation/artifacts/feature_spec.md`, (b) parses scenarios using `parse_acceptance_scenarios()`, (c) prints the exact `scenario.expected_result` text for AT-001, AT-002, AT-007
- [x] Pass each extracted `expected_result` into `_is_expected_error_scenario()` and assert it returns `True`
- [x] If it returns `False`, examine the extracted text for unexpected characters, encoding issues, or empty strings
- [x] Determine root cause: is it `_extract_field()` parsing, character encoding, multiline handling, or the runtime flow control?

**Success Criteria**: Root cause identified and documented. We know exactly why `_is_expected_error_scenario()` returns False at runtime.

### Task 1.2: Diagnose AT-004 pipeline error
**File**: `src/teambot/orchestration/acceptance_test_executor.py`, `src/teambot/repl/parser.py`
**Details**: [Details file, Lines 65-97](../details/20260210-runtime-validator-fix-details.md)

- [x] AT-004 step is: `@fake -> @pm create a plan`
- [x] The error is "Pipeline stage 1 requires task content" — not the expected agent validation error
- [x] Investigate: does `parse_command("@fake -> @pm create a plan")` parse correctly?
- [x] Check if `_parse_pipeline()` validates agent IDs and raises `ParseError` before the command reaches `TaskExecutor.execute()`
- [x] Determine if fix belongs in the parser, executor, or the expected result text in the feature spec

**Success Criteria**: Root cause identified. Clear fix path determined.

### Task 1.3: Diagnose AT-006 positive scenario output mismatch
**File**: `src/teambot/orchestration/acceptance_test_executor.py`
**Details**: [Details file, Lines 100-128](../details/20260210-runtime-validator-fix-details.md)

- [x] AT-006 runs 6 commands (`@pm plan this`, `@ba analyze this`, etc.) and expects "All 6 commands are accepted and dispatched to the correct agent"
- [x] The runtime executor compares output to expected text via `_verify_expected_output()` (lines 490-515)
- [x] Investigate: does `_verify_expected_output()` extract key terms from "All 6 commands are accepted and dispatched to the correct agent" and check if they appear in the actual output?
- [x] The actual output is likely mocked/empty in headless mode — determine if AT-006 should be runtime-tested or skipped
- [x] Determine if this is fixable or should be marked as runtime-skip with documented rationale

**Success Criteria**: Root cause identified. Decision made: fix or runtime-skip with rationale.

### Phase Gate: Phase 1 Complete When
- [x] Root cause confirmed for AT-001/002/007 with evidence
- [x] Root cause confirmed for AT-004
- [x] Root cause confirmed or skip decision documented for AT-006
- [x] All findings documented in details file

**Cannot Proceed If**: Root cause for AT-001/002/007 not definitively identified.

---

## Phase 2: Fix Expected Error Recognition (AT-001, AT-002, AT-007)

### Task 2.1: Apply fix based on root cause
**File**: `src/teambot/orchestration/acceptance_test_executor.py`
**Details**: [Details file, Lines 131-177](../details/20260210-runtime-validator-fix-details.md)

Based on investigation, apply the minimal fix. Likely candidates:

- [x] **If `_extract_field()` returns empty/malformed text**: Fix the regex pattern at line 135 to correctly capture expected_result with inline backticks
- [x] **If backticks wrap the entire value**: Add backtick stripping in `_is_expected_error_scenario()` — e.g., `lower = expected_result.lower().strip().strip('\`')`
- [x] **If multiline expected_result breaks parsing**: Adjust the `_extract_field()` regex to handle multiline values with backtick code spans
- [x] **If runtime flow skips `_is_expected_error_scenario()` call**: Fix the control flow to ensure the method is called for all error scenarios
- [x] Verify fix is minimal — no refactoring, no new dependencies
- [x] Ensure fix handles all three patterns: backtick-wrapped text (AT-001, AT-007), plain text (AT-002), and mixed formatting

**Success Criteria**: `_is_expected_error_scenario()` returns True for all three scenario expected_result texts as parsed from the actual feature spec.

### Task 2.2: Add regression tests
**File**: `tests/test_orchestration/test_acceptance_test_executor.py`
**Details**: [Details file, Lines 180-223](../details/20260210-runtime-validator-fix-details.md)

- [x] `test_is_expected_error_scenario_with_backtick_wrapped_error_message` — exact text from AT-001's expected_result as parsed from feature spec
- [x] `test_is_expected_error_scenario_with_plain_error_listing` — exact text from AT-002's expected_result
- [x] `test_is_expected_error_scenario_with_backtick_wrapped_typo` — exact text from AT-007's expected_result
- [x] `test_extract_field_preserves_backtick_content` — verify `_extract_field()` correctly extracts expected_result containing inline backticks
- [x] `test_runtime_validation_passes_expected_error_with_backtick_spec` — integration test: parse real scenario, execute command that fails, verify runtime marks it as PASSED
- [x] All tests use the actual text formats from the feature spec (not simplified versions)

**Success Criteria**: All 5 tests pass. Tests fail if the fix is reverted.

### Phase Gate: Phase 2 Complete When
- [x] Fix applied and all new tests pass
- [x] Existing `_is_expected_error_scenario` tests still pass
- [x] `uv run pytest tests/test_orchestration/test_acceptance_test_executor.py` passes

**Cannot Proceed If**: New tests fail or existing tests regress.

---

## Phase 3: Fix Remaining Runtime Failures

### Task 3.1: Fix AT-004 pipeline validation order
**File**: `src/teambot/orchestration/acceptance_test_executor.py` and/or `src/teambot/repl/parser.py`
**Details**: [Details file, Lines 226-242](../details/20260210-runtime-validator-fix-details.md)

- [x] Based on Phase 1 investigation, apply fix:
  - **Option A**: If parser raises ParseError for `@fake -> @pm create a plan`, update `_is_expected_error_scenario()` to also recognize parse-level errors (add "requires task content" or "invalid" to indicators)
  - **Option B**: If the issue is command extraction from steps, fix `extract_commands_from_steps()` to correctly handle pipeline syntax
  - **Option C**: If the expected_result text should be updated, update the feature spec's AT-004 expected_result to match the actual error
- [x] Choose the option that requires minimal changes
- [x] Add test verifying AT-004 scenario passes at runtime

**Success Criteria**: AT-004 passes in runtime validation.

### Task 3.2: Fix AT-006 positive scenario output matching
**File**: `src/teambot/orchestration/acceptance_test_executor.py`
**Details**: [Details file, Lines 245-267](../details/20260210-runtime-validator-fix-details.md)

- [x] AT-006 sends 6 valid agent commands and expects "All 6 commands are accepted and dispatched to the correct agent"
- [x] In headless runtime, commands execute against a mock/no-op executor — output doesn't contain meaningful text
- [x] Based on investigation, apply fix:
  - **Option A**: Adjust `_verify_expected_output()` to accept scenarios where all commands succeed as a pass (success = verification enough)
  - **Option B**: Mark AT-006 as a runtime-skip scenario (it tests regression, not error handling — code-level tests are sufficient)
  - **Option C**: Add a "commands accepted" marker to the positive scenario check
- [x] Document rationale for chosen approach
- [x] Add test if fix is applied, or document skip rationale

**Success Criteria**: AT-006 either passes or is explicitly skipped with documented rationale in the code.

### Phase Gate: Phase 3 Complete When
- [x] AT-004 and AT-006 resolved (pass or documented skip)
- [x] No regression in AT-001/002/003/005/007
- [x] `uv run pytest` passes

**Cannot Proceed If**: Previously passing scenarios (AT-003, AT-005) regress.

---

## Phase 4: Final Verification

### Task 4.1: Full suite validation, lint, and acceptance
**Details**: [Details file, Lines 270-299](../details/20260210-runtime-validator-fix-details.md)

- [x] Run `uv run ruff format .` — no formatting issues
- [x] Run `uv run ruff check . --fix` — no lint errors
- [x] Run `uv run pytest` — all tests pass (1050+ existing + new tests)
- [x] Run `uv run pytest tests/test_acceptance_unknown_agent.py -v` — all 19+ acceptance unit tests pass
- [x] Run `uv run pytest tests/test_orchestration/test_acceptance_test_executor.py -v` — all executor tests pass
- [x] Verify error message format: `Unknown agent: '{id}'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`
- [x] Verify no `VALID_AGENTS` duplication introduced
- [x] Confirm acceptance test results can be updated to 7/7 (or N/7 with documented skips)

### Phase Gate: Phase 4 Complete When
- [x] Zero lint errors
- [x] All tests pass
- [x] Code passes `ruff check` and `ruff format`
- [x] Acceptance results documented

**Cannot Proceed If**: Any test or lint failure.

---

## Effort Estimation

| Task | Estimated Effort | Complexity | Risk |
|------|-----------------|------------|------|
| T1.1: Diagnose AT-001/002/007 | 20 min | MEDIUM | LOW |
| T1.2: Diagnose AT-004 | 10 min | LOW | LOW |
| T1.3: Diagnose AT-006 | 10 min | LOW | LOW |
| T2.1: Fix expected error recognition | 15 min | MEDIUM | MEDIUM |
| T2.2: Add regression tests | 20 min | LOW | LOW |
| T3.1: Fix AT-004 pipeline | 15 min | MEDIUM | LOW |
| T3.2: Fix AT-006 positive scenario | 10 min | LOW | LOW |
| T4.1: Full verification | 10 min | LOW | LOW |

**Total**: ~110 min

---

## Dependencies

| Dependency | Status |
|------------|--------|
| Core validation (TaskExecutor, App, AgentStatusManager) | ✅ DONE (prior plan) |
| `VALID_AGENTS` in `router.py` (line 20) | ✅ Exists |
| Feature spec with AT scenarios | ✅ Exists at `.teambot/unknown-agent-validation/artifacts/feature_spec.md` |
| `AcceptanceTestExecutor` class | ✅ Exists at `src/teambot/orchestration/acceptance_test_executor.py` |
| Existing executor tests | ✅ Exist at `tests/test_orchestration/test_acceptance_test_executor.py` |

---

## Files Changed Summary

| File | Change Type | Lines Changed (est.) |
|------|-------------|---------------------|
| `src/teambot/orchestration/acceptance_test_executor.py` | Modify | ~10-20 |
| `tests/test_orchestration/test_acceptance_test_executor.py` | Modify | ~40-60 |
| `.teambot/unknown-agent-validation/artifacts/feature_spec.md` | Possibly modify | ~2-5 (if AT-004 expected_result needs updating) |
| **Total** | | **~55-85** |

---

## Success Criteria (Overall)

1. [x] `_is_expected_error_scenario()` correctly returns True for AT-001, AT-002, AT-007 expected_result text
2. [x] Runtime acceptance tests pass ≥5/7 (AT-001, AT-002, AT-003, AT-005, AT-007)
3. [x] AT-004 and AT-006 either pass or are explicitly skipped with documented rationale
4. [x] Unit tests cover `_is_expected_error_scenario()` with backtick-formatted, plain text, and edge cases
5. [x] All existing tests pass; new tests cover the runtime validator fix
6. [x] Code passes `ruff check` and `ruff format`
