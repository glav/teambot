<!-- markdownlint-disable-file -->
# Implementation Plan: Fix Runtime Validator & Complete Unknown Agent Validation

**Status**: Ready for implementation
**Prior Work**: Core validation (TaskExecutor, App, AgentStatusManager) — COMPLETE
**Focus**: Fix runtime acceptance test executor to correctly recognise expected-error scenarios

---

## Problem Statement

The core unknown-agent validation is implemented and unit-tested. However, the `AcceptanceTestExecutor`'s runtime validation incorrectly fails 5/7 scenarios:

| Scenario | Issue | Category |
|----------|-------|----------|
| AT-001 | Expected error not recognised | `_is_expected_error_scenario()` bug |
| AT-002 | Expected error not recognised | Same |
| AT-007 | Expected error not recognised | Same |
| AT-004 | Wrong error (pipeline parser) | Pipeline validation order |
| AT-006 | Output mismatch (positive test) | `_verify_expected_output()` too strict |

**Key finding**: Unit tests for `_is_expected_error_scenario()` PASS with backtick-formatted text. The bug is in how scenarios are parsed from the feature spec at runtime OR in the runtime execution flow.

---

## Plan Summary

| Phase | Tasks | Focus |
|-------|-------|-------|
| Phase 1 | T1.1, T1.2, T1.3 | Root cause investigation |
| Phase 2 | T2.1, T2.2 | Fix expected-error recognition (AT-001/002/007) |
| Phase 3 | T3.1, T3.2 | Fix remaining failures (AT-004, AT-006) |
| Phase 4 | T4.1 | Full verification |

**Estimated effort**: ~110 min
**Approach**: Code-First (per test strategy)

---

## Detailed Plan

### Phase 1: Root Cause Investigation

**T1.1 — Diagnose AT-001/AT-002/AT-007** (20 min, MEDIUM complexity)
- File: `src/teambot/orchestration/acceptance_test_executor.py`
- Write diagnostic test: parse actual feature spec → extract `expected_result` for AT-001/002/007 → pass to `_is_expected_error_scenario()` → assert True
- Run with `-s` to see exact extracted text
- Determine: is the bug in `_extract_field()` regex, runtime flow control, or scenario loading?

**T1.2 — Diagnose AT-004** (10 min, LOW complexity)
- Test `parse_command("@fake -> @pm create a plan")` directly
- Pipeline parser may reject "no task content" before agent validation runs
- Determine fix: parser priority, expected_result update, or new error keyword

**T1.3 — Diagnose AT-006** (10 min, LOW complexity)
- `_verify_expected_output()` extracts key terms from "All 6 commands are accepted and dispatched" and checks ≥30% appear in output
- Headless runtime output is empty → 0% match → FAIL
- Determine: fix output matching or runtime-skip with rationale

### Phase 2: Fix Expected Error Recognition

**T2.1 — Apply fix** (15 min, MEDIUM complexity)
- File: `src/teambot/orchestration/acceptance_test_executor.py`
- Likely fix: strip backticks in `_is_expected_error_scenario()` OR fix `_extract_field()` regex OR fix runtime flow
- Minimal change — no refactoring, no new dependencies

**T2.2 — Add regression tests** (20 min, LOW complexity)
- File: `tests/test_orchestration/test_acceptance_test_executor.py`
- 5 new tests: backtick-wrapped AT-001 text, plain AT-002 text, AT-007 text, `_extract_field()` backtick preservation, runtime integration

### Phase 3: Fix Remaining Runtime Failures

**T3.1 — Fix AT-004 pipeline** (15 min, MEDIUM complexity)
- Option A: Fix parser to validate agents before task content
- Option B: Update feature spec expected_result
- Option C: Add keyword to `_is_expected_error_scenario()`

**T3.2 — Fix AT-006 output matching** (10 min, LOW complexity)
- Option A: Don't require output matching when all commands succeed
- Option B: Runtime-skip with documented rationale

### Phase 4: Verification

**T4.1 — Full validation** (10 min, LOW complexity)
- `uv run ruff format .` + `uv run ruff check . --fix`
- `uv run pytest` — all tests pass
- Acceptance tests: ≥5/7 runtime pass (AT-004/006 may be skipped with rationale)

---

## Key Source Files

| File | Role | Key Lines |
|------|------|-----------|
| `src/teambot/orchestration/acceptance_test_executor.py` | Runtime validator | `_is_expected_error_scenario()`: 517-542, `_extract_field()`: 133-139, runtime loop: 365-435 |
| `src/teambot/repl/parser.py` | Command parser | `parse_command()`: 95+, `_parse_pipeline()`: 254+ |
| `tests/test_orchestration/test_acceptance_test_executor.py` | Executor tests | Existing error scenario tests: 458-506 |
| `.teambot/unknown-agent-validation/artifacts/feature_spec.md` | AT definitions | AT-001: line 250, AT-002: 259, AT-007: 308 |

---

## Detailed SDD Artifacts

- **Plan**: `.agent-tracking/plans/20260210-runtime-validator-fix-plan.instructions.md`
- **Details**: `.agent-tracking/details/20260210-runtime-validator-fix-details.md`

---

## Success Criteria

1. `_is_expected_error_scenario()` returns True for AT-001, AT-002, AT-007 expected_result text
2. Runtime acceptance tests pass ≥5/7
3. Unit tests cover the fix with exact feature spec text formats
4. All existing tests pass
5. Code passes `ruff check` and `ruff format`

---

## Next Step

Run **Step 6** (`sdd.6-review-plan.prompt.md`) to validate this plan, then delegate implementation to `@builder-1` or `@builder-2`.
