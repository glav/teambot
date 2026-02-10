## Objective

- Fix the runtime validator's error-expectation logic so that acceptance test scenarios which *expect* error output (e.g., unknown agent rejection) are correctly recognised as passing, and complete the remaining unknown agent validation implementation.

**Goal**:

- The acceptance test executor's `_is_expected_error_scenario()` method in `acceptance_test_executor.py` fails to recognise scenarios AT-001, AT-002, and AT-007 as expected-error scenarios. These scenarios produce the correct error output (`Unknown agent: '...'`), but the runtime validator treats any command failure as a test failure — marking them `RUNTIME VALIDATION FAILED`.
- The root cause is likely markdown backtick formatting in the `expected_result` field (parsed via `_extract_field()`) interfering with the keyword matching in `_is_expected_error_scenario()`.
- Additionally, complete the core unknown agent validation (TaskExecutor, App, AgentStatusManager guard) and associated tests from the existing implementation plan.

**Problem Statement**:

- The runtime validator in `src/teambot/orchestration/acceptance_test_executor.py` has a method `_is_expected_error_scenario()` (line 518) that checks whether a scenario's `expected_result` text contains error indicators like `"error message"`, `"rejected"`, `"unknown agent"`.
- For AT-001, AT-002, and AT-007, the `expected_result` parsed from the feature spec contains backtick-wrapped text (e.g., `` Error message: `Unknown agent: 'unknown-agent'...` ``). The `_extract_field()` function may be stripping or truncating content at backtick boundaries, causing the keyword match to fail.
- When `_is_expected_error_scenario()` returns `False` for an expected-error scenario, the runtime validator falls into the failure branch (line 388-391), marking the scenario as failed even though the feature is working correctly.
- Separately, the core validation (TaskExecutor entry-point validation, App validation, AgentStatusManager guard) and its tests still need to be completed per the existing implementation plan.

**Success Criteria**:
- [ ] `_is_expected_error_scenario()` correctly returns `True` for AT-001, AT-002, and AT-007 expected_result text (with backtick formatting).
- [ ] Runtime acceptance tests for `unknown-agent-validation` pass 7/7 (or runtime validation is explicitly skipped with documented rationale if the fix is deemed too complex for this feature).
- [ ] Unit tests cover `_is_expected_error_scenario()` with backtick-formatted input, plain text input, and edge cases.
- [ ] TaskExecutor.execute() validates all agent IDs against VALID_AGENTS before dispatching (closes the bypass around the router).
- [ ] AgentStatusManager does not auto-create entries for invalid agent IDs.
- [ ] Multi-agent and pipeline commands validate all agent IDs before execution.
- [ ] All existing tests pass; new tests cover both the runtime validator fix and the unknown agent rejection paths.
- [ ] Code passes `ruff check` and `ruff format`.

---

## Technical Context

**Target Codebase**:

- `src/teambot/orchestration/acceptance_test_executor.py` — runtime validator (`_is_expected_error_scenario()`, `_extract_field()`, command execution loop)
- `src/teambot/tasks/executor.py` — TaskExecutor agent ID validation
- `src/teambot/ui/app.py` — TeamBotApp agent ID validation
- `src/teambot/ui/agent_state.py` — AgentStatusManager guard

**Primary Language/Framework**:

- Python

**Testing Preference**:

- Code-First (per existing test strategy decision — logic is straightforward guard clauses and keyword matching)

**Key Constraints**:
- Runtime validation can be skipped for this particular feature if the fix is deemed too complex, but it should typically happen wherever it can be done to ensure features work end-to-end.
- The `VALID_AGENTS` set in `router.py` is the single source of truth — do not duplicate.
- Use the existing local-import pattern in executor.py (matches line 199).
- Minimal changes — targeted fixes, not refactors.
- Must not break the existing simple-path router validation.

---

## Additional Context

- **Existing artifacts**: The full feature spec, implementation plan, test strategy, and acceptance test results are in `.teambot/unknown-agent-validation/artifacts/`.
- **Code-level tests already pass**: 21/21 pytest acceptance tests in `tests/test_acceptance_validation.py` pass. The failures are only in the runtime validation layer.
- **AT-004 (pipeline)**: Fails with `Pipeline stage 1 requires task content` — this is a different issue from the error-expectation logic; the pipeline parser requires content per stage.
- **AT-006 (all valid agents work)**: Runtime validator expects output matching but can't execute real SDK calls in test mode; may need mock or explicit skip.
- **Phase 4 can run in parallel**: The runtime validator fix (`acceptance_test_executor.py`) is an independent subsystem from the core validation work (`executor.py`, `app.py`, `agent_state.py`). A second builder can work on it in parallel.
- **Recommended assignment**: `@builder-1` for Phases 1-3 (core validation + tests), `@builder-2` for Phase 4 (runtime validator fix).

---
