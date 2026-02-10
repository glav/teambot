# Problem Statement: Runtime Validator Error-Scenario Detection & Agent Validation Gaps

## 1. Business Problem

TeamBot's quality assurance workflow includes a runtime acceptance test executor that validates features end-to-end by executing commands and comparing actual behavior against expected results defined in feature specifications. This executor is currently **misclassifying expected-error scenarios as test failures**, undermining confidence in the acceptance test pipeline and blocking feature completion.

Specifically, the `unknown-agent-validation` feature — which ensures that commands targeting non-existent agents are cleanly rejected — produced **correct error output** for 3 of its 7 acceptance test scenarios (AT-001, AT-002, AT-007), but the runtime validator marked them as `RUNTIME VALIDATION FAILED` because it failed to recognize that an error was the **expected** outcome.

Additionally, there are **remaining validation gaps** where unknown agent IDs can bypass the primary router guard through alternative execution paths (TaskExecutor, App dispatch, AgentStatusManager), which need to be closed with targeted guard clauses.

## 2. Affected Components

| Component | File | Issue |
|-----------|------|-------|
| Runtime Validator | `src/teambot/orchestration/acceptance_test_executor.py` | `_is_expected_error_scenario()` does not match backtick-formatted `expected_result` text |
| Field Extractor | `src/teambot/orchestration/acceptance_test_executor.py` | `_extract_field()` passes through markdown backticks that may interfere with keyword matching |
| TaskExecutor | `src/teambot/tasks/executor.py` | Agent ID validation guard needs verification/completion |
| App Dispatch | `src/teambot/ui/app.py` | Agent ID validation guard needs verification/completion |
| Agent Status | `src/teambot/ui/agent_state.py` | AgentStatusManager should not auto-create entries for invalid agent IDs |

## 3. Root Cause Analysis

### 3.1 Runtime Validator False Failures (Primary Issue)

The `_is_expected_error_scenario()` method checks whether a scenario's `expected_result` text contains keywords like `"error message"`, `"rejected"`, `"unknown agent"`, etc. The `expected_result` field is extracted from the feature spec's markdown by `_extract_field()`.

**The problem**: Feature spec scenario definitions use markdown backtick formatting in their `Expected Result` fields. For example:

```
**Expected Result**: Error message: `Unknown agent: 'unknown-agent'. Valid agents: ...`
```

When `_extract_field()` parses this, the extracted text retains the backtick characters. The keyword matching in `_is_expected_error_scenario()` may be disrupted by the backtick characters depending on how the text is processed, or there may be a code path where `_is_expected_error_scenario()` is not consulted before marking a command failure as a test failure.

**Evidence**: The acceptance test results file (`.teambot/unknown-agent-validation/artifacts/acceptance_test_results.md`) shows:
- AT-001: Command produced `Unknown agent: 'unknown-agent'. Valid agents: ...` → marked FAILED
- AT-002: Command produced `Unknown agent: 'unknown-agent'. Valid agents: ...` → marked FAILED
- AT-007: Command produced `Unknown agent: 'buidler-1'. Valid agents: ...` → marked FAILED

All three produced the **exact error output** that the scenarios defined as the expected result.

### 3.2 Agent Validation Bypass Paths (Secondary Issue)

The primary validation happens in the REPL router (`src/teambot/repl/router.py`), which checks agent IDs against `VALID_AGENTS`. However, commands can reach agents through alternative paths:

- **TaskExecutor.execute()**: Background/async task dispatch — needs guard before agent dispatch
- **TeamBotApp._handle_agent_command()**: UI-level command handling — needs guard before processing
- **AgentStatusManager**: Should not create status entries for unknown agents, which would imply they exist

These guards must all reference the canonical `VALID_AGENTS` set in `router.py` as the single source of truth.

## 4. Impact Assessment

| Impact Area | Severity | Description |
|-------------|----------|-------------|
| Feature Completion | **High** | The `unknown-agent-validation` feature cannot pass its acceptance test stage (2/7 scenarios pass) despite the underlying validation logic working correctly |
| Developer Trust | **Medium** | False runtime validation failures erode trust in the acceptance test pipeline — developers may ignore valid failures |
| Quality Gates | **Medium** | The POST_REVIEW stage requires acceptance tests to pass (`requires_acceptance_tests_passed: true` in stages.yaml), so this blocks workflow progression |
| Security Surface | **Low** | Unknown agent IDs reaching execution paths could cause unexpected behavior, though current impact is limited to error messages rather than code execution |

## 5. Goals

### G1: Fix Runtime Validator Error-Scenario Detection
`_is_expected_error_scenario()` must correctly return `True` for AT-001, AT-002, and AT-007 `expected_result` text, regardless of whether the text contains markdown backtick formatting.

### G2: Complete Agent Validation Guards
Close all bypass paths where unknown agent IDs could reach execution without validation:
- TaskExecutor.execute() validates against VALID_AGENTS before dispatch
- AgentStatusManager rejects unknown agent IDs
- Multi-agent and pipeline commands validate all agent IDs before execution

### G3: Comprehensive Test Coverage
Unit tests must cover:
- `_is_expected_error_scenario()` with backtick-formatted input, plain text input, and edge cases
- Each agent validation guard (TaskExecutor, App, AgentStatusManager) with unknown agent rejection
- Regression tests for valid agents and aliases continuing to work

## 6. Success Criteria

| ID | Criterion | Measurable Target |
|----|-----------|-------------------|
| SC-1 | `_is_expected_error_scenario()` recognizes formatted error scenarios | Returns `True` for AT-001, AT-002, AT-007 expected_result text with backticks |
| SC-2 | Runtime acceptance tests pass | 7/7 pass, or failures documented with rationale if runtime validation is skipped |
| SC-3 | Unit test coverage for error-scenario detection | Tests cover backtick input, plain text input, empty input, edge cases |
| SC-4 | TaskExecutor validates agent IDs | `execute()` checks all agent IDs against VALID_AGENTS before dispatch |
| SC-5 | AgentStatusManager guards against invalid agents | Does not auto-create entries for unknown agent IDs |
| SC-6 | Multi-agent/pipeline validation | All agent IDs validated before execution |
| SC-7 | Existing tests unbroken | Full test suite passes (`uv run pytest`) |
| SC-8 | Code quality | `ruff check .` and `ruff format .` pass cleanly |

## 7. Constraints

- **Single Source of Truth**: `VALID_AGENTS` in `router.py` is the canonical agent ID set — do not duplicate
- **Minimal Changes**: Targeted fixes only — no refactoring of unrelated code
- **Import Pattern**: Use local imports in `executor.py` (consistent with existing pattern at line 199)
- **Backward Compatibility**: Must not break the existing simple-path router validation
- **Runtime Validation**: Can be skipped for specific scenarios with documented rationale if the fix is too complex, but should be attempted first

## 8. Stakeholders

| Role | Interest |
|------|----------|
| Builder Agents | Implement the fixes in the identified files |
| Reviewer Agent | Verify correctness, minimal change footprint, test coverage |
| PM Agent | Track progress against success criteria |
| QA/Acceptance | Validate that runtime acceptance tests pass end-to-end |

## 9. Dependencies

- Existing `VALID_AGENTS` set and `AGENT_ALIASES` dict in `src/teambot/repl/router.py`
- Existing acceptance test scenarios in `.teambot/unknown-agent-validation/artifacts/feature_spec.md`
- Existing unit tests in `tests/test_orchestration/test_acceptance_test_executor.py`
- Existing acceptance validation tests in `tests/test_acceptance_validation.py` and `tests/test_acceptance_unknown_agent.py`

## 10. Assumptions

1. The `_extract_field()` regex correctly captures multi-line field content but retains backtick characters
2. The keyword indicators in `_is_expected_error_scenario()` are a valid heuristic — the fix should make them robust to formatting, not replace the approach
3. The TaskExecutor, App, and AgentStatusManager validation guards are partially implemented and need completion/verification, not ground-up implementation
4. The `DEFAULT_AGENTS` list in `agent_state.py` and `VALID_AGENTS` set in `router.py` contain the same 6 agents
