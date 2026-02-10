<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Fix Runtime Validator Error-Scenario Detection & Complete Agent Validation Guards - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target Current Sprint | Lifecycle Active Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-10 |
| Problem & Users | ✅ | None | 2026-02-10 |
| Scope | ✅ | None | 2026-02-10 |
| Requirements | ✅ | None | 2026-02-10 |
| Metrics & Risks | ✅ | None | 2026-02-10 |
| Operationalization | ✅ | None | 2026-02-10 |
| Finalization | ✅ | None | 2026-02-10 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot's quality assurance pipeline includes a runtime acceptance test executor (`AcceptanceTestExecutor`) that validates features end-to-end by parsing scenario definitions from feature spec markdown, executing the commands they describe, and comparing actual behaviour against expected results. The `unknown-agent-validation` feature — which ensures commands targeting non-existent agent IDs are cleanly rejected — was recently implemented across the router, TaskExecutor, App, and AgentStatusManager layers. All 21 unit-level acceptance tests pass (in `tests/test_acceptance_validation.py`), confirming the validation logic is correct in isolation.

However, when the runtime acceptance test executor runs the same scenarios end-to-end, **3 of 7 scenarios (AT-001, AT-002, AT-007) are marked `RUNTIME VALIDATION FAILED`** despite producing the correct error output. The runtime validator's `_is_expected_error_scenario()` method fails to recognise these scenarios as "expected-error" scenarios, causing it to treat the (correct) command failures as test failures.

### Core Opportunity
Fix the runtime validator so that expected-error scenarios are correctly classified, restoring confidence in the acceptance test pipeline. Additionally, verify and complete the agent validation guard clauses across all command dispatch paths.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Priority |
|---------|-----------|------|----------|--------|----------|
| G-001 | `_is_expected_error_scenario()` correctly classifies all expected-error acceptance test scenarios regardless of markdown formatting in `expected_result` text | Bug Fix | 4/7 scenarios misclassified | 0/7 misclassified | P0 |
| G-002 | Runtime acceptance tests for `unknown-agent-validation` pass 7/7 (or runtime validation explicitly skipped with documented rationale) | Quality Gate | 2/7 pass | 7/7 pass | P0 |
| G-003 | All command dispatch paths validate agent IDs against `VALID_AGENTS` before execution | Feature Completion | Router-only validation | Router + TaskExecutor + App + AgentStatusManager | P1 |
| G-004 | Comprehensive test coverage for both the runtime validator fix and agent validation guards | Test Coverage | Partial | Complete (backtick input, plain text, edge cases, all guard paths) | P1 |

## 2. Problem Definition

### Current Situation
The `unknown-agent-validation` feature implementation is functionally correct — all 21 code-level acceptance tests pass. However, the feature cannot progress past the ACCEPTANCE_TEST workflow stage because the runtime validator incorrectly marks 5 of 7 scenarios as failed (3 due to error-scenario misclassification, 2 due to separate issues).

The acceptance test results show:
- **AT-001** (Simple unknown agent): ❌ `RUNTIME VALIDATION FAILED` — Command produced correct error `Unknown agent: 'unknown-agent'...` but validator treated it as failure
- **AT-002** (Background unknown agent): ❌ `RUNTIME VALIDATION FAILED` — Same issue as AT-001
- **AT-003** (Multi-agent invalid ID): ✅ Passed
- **AT-004** (Pipeline unknown agent): ❌ Failed — Pipeline content error (separate issue)
- **AT-005** (Valid alias): ✅ Passed
- **AT-006** (All six valid agents): ❌ Failed — Output matching issue (separate issue)
- **AT-007** (Typo near valid ID): ❌ `RUNTIME VALIDATION FAILED` — Same issue as AT-001

### Problem Statement
The runtime acceptance test executor's `_is_expected_error_scenario()` method does not recognise AT-001, AT-002, and AT-007 as expected-error scenarios. These scenarios define their expected results with markdown backtick formatting (e.g., `` Error message: `Unknown agent: 'unknown-agent'...` ``), but the method's keyword matching does not account for or strip this formatting before comparison. When the command correctly fails with the expected error, the validator falls through to the "command failed" error path instead of the "expected error produced" success path.

### Root Causes
* **RC-1: Backtick interference in `_is_expected_error_scenario()`** — The `_extract_field()` function correctly extracts the `Expected Result` text from markdown but preserves backtick characters. The `_is_expected_error_scenario()` method performs keyword matching (e.g., `"error message" in lower`) on this text. While the keywords should still match with backticks present (since backticks don't replace the keyword text), there may be an edge case where the extracted text format or a code path in the execution loop prevents `_is_expected_error_scenario()` from being consulted, or where the extracted text is truncated/malformed. The exact interaction needs to be confirmed during implementation, but the fix should ensure backtick-formatted text is handled robustly.
* **RC-2: No backtick stripping in the extraction pipeline** — The `_extract_field()` regex captures markdown-formatted text verbatim. A defence-in-depth approach would strip backticks before keyword matching, ensuring robustness regardless of how scenario authors format their expected results.
* **RC-3: Incomplete validation across dispatch paths** — While TaskExecutor, App, and AgentStatusManager guards appear to be implemented (per code inspection), their completeness and test coverage need verification as part of this feature closure.

### Impact of Inaction
* The `unknown-agent-validation` feature cannot pass its acceptance test stage, blocking workflow progression to POST_REVIEW and COMPLETE
* False runtime validation failures erode developer trust in the acceptance test pipeline
* Other future features with expected-error scenarios will hit the same classification bug
* The POST_REVIEW stage gate (`requires_acceptance_tests_passed: true`) permanently blocks completion

## 3. Users & Personas
| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| Builder Agent | Implement features and have them pass acceptance tests | Runtime validator marks correct error output as failure; feature appears broken when it works | Direct — blocks feature completion |
| Reviewer Agent | Verify feature correctness via acceptance tests | False failures in acceptance results obscure real issues | Direct — cannot distinguish real failures from false ones |
| PM Agent | Track feature progress through workflow stages | Feature stuck at ACCEPTANCE_TEST stage despite unit tests passing | Direct — inaccurate progress reporting |
| End User (Developer) | Send commands to valid agents, get clear errors for invalid ones | N/A (underlying validation works correctly) | Indirect — feature delivery delayed |

## 4. Scope

### In Scope
* Fix `_is_expected_error_scenario()` to handle markdown backtick formatting in `expected_result` text (strip backticks before keyword matching)
* Add unit tests for `_is_expected_error_scenario()` with backtick-formatted input, plain text, and edge cases
* Verify TaskExecutor.execute() agent ID validation guard is complete and correct
* Verify AgentStatusManager guard clauses reject unknown agent IDs
* Verify App._handle_agent_command() agent ID validation is complete
* Add/update tests for all agent validation guards
* Ensure all existing tests continue to pass
* Ensure code passes `ruff check` and `ruff format`

### Out of Scope (justify if empty)
* Fixing AT-004 (pipeline content error) — separate root cause related to pipeline parsing, not error-scenario detection
* Fixing AT-006 (output matching for valid agents) — separate root cause related to output verification, not error-scenario detection
* Refactoring the acceptance test executor architecture
* Changing the `VALID_AGENTS` source of truth or adding new agents
* Modifying the REPL router's existing simple-path validation

### Assumptions
* The `VALID_AGENTS` set in `router.py` (`{"pm", "ba", "writer", "builder-1", "builder-2", "reviewer"}`) is stable and will not change during this fix
* The `DEFAULT_AGENTS` list in `agent_state.py` contains the same 6 agents as `VALID_AGENTS`
* The `_extract_field()` regex correctly captures multi-line field content (the issue is downstream in keyword matching, not upstream in extraction)
* The local-import pattern used in `executor.py` (line 178) is the approved pattern for avoiding circular imports

### Constraints
* **Single source of truth**: All agent ID validation must reference `VALID_AGENTS` from `router.py` — no duplication
* **Local imports**: Use lazy/local imports in `executor.py` and `app.py` to avoid circular dependency issues (matches existing pattern)
* **Minimal changes**: Targeted fixes only — no refactoring of unrelated code paths
* **Backward compatibility**: Must not break the router's existing simple-path validation
* **Runtime validation flexibility**: Runtime validation can be skipped for specific scenarios with documented rationale if the fix proves too complex, but the goal is 7/7 pass

## 5. Product Overview

### Value Proposition
Restoring runtime acceptance test accuracy ensures the quality gate pipeline produces trustworthy results, enabling features to progress through workflow stages when they are genuinely complete and catching real failures when they occur.

### Differentiators (Optional)
* Defence-in-depth: Stripping backticks before keyword matching makes the error-scenario detector robust against any markdown formatting, not just the specific patterns in the current feature spec

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Priority | Acceptance Criteria |
|-------|-------|------------|-------|----------|-----------|
| FR-001 | Strip backticks in error-scenario detection | `_is_expected_error_scenario()` must strip markdown backtick characters from `expected_result` text before performing keyword matching | G-001 | P0 | Method returns `True` for `"Error message: \`Unknown agent: 'unknown-agent'\`"` |
| FR-002 | Detect error indicators robustly | `_is_expected_error_scenario()` must match all existing error indicators (`error message`, `error identifying`, `error listing`, `rejected`, `rejects`, `unknown agent`) in both plain text and backtick-formatted text | G-001 | P0 | Unit tests pass for all indicator keywords with and without backticks |
| FR-003 | TaskExecutor agent ID validation | `TaskExecutor.execute()` validates all agent IDs (simple, multi-agent, pipeline) against `VALID_AGENTS` before dispatching to any execution path | G-003 | P1 | Unknown agent returns `ExecutionResult(success=False, error="Unknown agent: ...")` |
| FR-004 | App agent ID validation | `TeamBotApp._handle_agent_command()` validates all agent IDs against `VALID_AGENTS` before processing | G-003 | P1 | Unknown agent triggers `write_task_error()` and returns without execution |
| FR-005 | AgentStatusManager guard | `AgentStatusManager.set_idle()`, `_update()`, and `set_model()` silently reject agent IDs not in `DEFAULT_AGENTS` | G-003 | P1 | Unknown agent ID does not create a status entry |
| FR-006 | Alias resolution before validation | All validation paths resolve aliases via `AGENT_ALIASES` before checking against `VALID_AGENTS` | G-003 | P1 | `@project_manager` resolves to `pm` and passes validation |
| FR-007 | Consistent error format | All validation paths produce errors in the format: `Unknown agent: '{id}'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer` | G-003 | P2 | Error messages are identical across router, TaskExecutor, and App |
| FR-008 | Unit test coverage — error-scenario detection | New unit tests cover `_is_expected_error_scenario()` with: backtick-formatted input, plain text input, empty input, text with no error indicators, mixed formatting | G-004 | P1 | All test cases pass |
| FR-009 | Unit test coverage — agent validation guards | Tests cover unknown agent rejection in TaskExecutor, App, and AgentStatusManager for simple, multi-agent, and pipeline commands | G-004 | P1 | All test cases pass |

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation |
|--------|----------|------------|--------------|----------|-----------|
| NFR-001 | Maintainability | Fix must be minimal — fewest lines changed | < 10 lines changed in `acceptance_test_executor.py` | P1 | Code review |
| NFR-002 | Reliability | All existing tests must continue to pass | 0 regressions in full test suite | P0 | `uv run pytest` — all tests pass |
| NFR-003 | Code Quality | Code passes linting and formatting checks | `ruff check .` and `ruff format .` produce no errors | P0 | CI/lint pass |
| NFR-004 | Compatibility | Fix must not alter the behaviour of non-error acceptance test scenarios | AT-003, AT-005 continue to pass | P0 | Runtime acceptance rerun |
| NFR-005 | Robustness | Error-scenario detection handles future markdown formatting variations | Backtick stripping is applied generically, not pattern-specific | P1 | Edge case tests |

## 8. Data & Analytics (Conditional)

### Inputs
* Feature spec markdown files (`.teambot/{feature}/artifacts/feature_spec.md`) containing acceptance test scenario definitions with `**Expected Result**` fields
* `VALID_AGENTS` set from `src/teambot/repl/router.py`

### Outputs / Events
* Corrected acceptance test results (7/7 pass for `unknown-agent-validation`)
* Accurate `AcceptanceTestStatus` values for each scenario

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Source |
|--------|------|----------|--------|--------|
| AT scenarios correctly classified | Accuracy | 4/7 | 7/7 | Runtime acceptance test results |
| Unit test pass rate | Quality | All pass | All pass (+ new tests) | `uv run pytest` |
| Ruff lint errors | Quality | 0 | 0 | `ruff check .` |

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| `VALID_AGENTS` set in `router.py` | Code — single source of truth | Critical | Existing code | Low — stable set | No changes needed |
| `AGENT_ALIASES` dict in `router.py` | Code — alias resolution | Critical | Existing code | Low — stable dict | No changes needed |
| `DEFAULT_AGENTS` list in `agent_state.py` | Code — status manager guard | Medium | Existing code | Low — mirrors `VALID_AGENTS` | Verify alignment |
| Existing test suite (1050+ tests) | Test — regression safety net | High | Existing tests | Low | Run full suite before/after |
| `_extract_field()` regex | Code — upstream text extraction | Medium | Existing code | Low — not being changed | Verify extraction output |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Status |
|---------|-------------|---------|-----------|-----------|--------|
| R-001 | Backtick stripping changes keyword matching for non-error scenarios | Medium | Low | Test with AT-005 (valid alias) and AT-006 (all agents) to ensure non-error scenarios unaffected | Open |
| R-002 | Local imports in executor.py cause circular import issues | Medium | Low | Pattern already established at line 178; follow same approach | Open |
| R-003 | Fix for AT-001/002/007 does not resolve AT-004/AT-006 | Low | High | AT-004 and AT-006 have separate root causes (documented as out-of-scope); focus on the 3 error-scenario misclassifications | Accepted |
| R-004 | State file in `.agent-tracking/` may be stale | Low | Medium | Verify against actual code state before relying on cached state | Open |

## 11. Privacy, Security & Compliance

### Data Classification
Internal/Development — no user data, PII, or secrets involved. All data is test scenario definitions and agent identifiers.

### PII Handling
N/A — no personal data processed.

### Threat Considerations
* Unknown agent IDs reaching execution paths could theoretically cause unexpected behaviour, but current impact is limited to error messages (no code execution risk)
* Agent ID validation is a defence-in-depth measure, not a security boundary

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Standard merge to main | No feature flags needed |
| Rollback | Revert commit | Changes are isolated to keyword matching and guard clauses |
| Monitoring | Acceptance test results | Re-run runtime acceptance tests post-merge |
| Testing | `uv run pytest` + `ruff check .` + `ruff format .` | Standard CI pipeline |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Gate Criteria | Owner |
|-------|--------------|-------|
| Implementation | Fix `_is_expected_error_scenario()`, add unit tests | Builder Agent |
| Verification | All existing + new tests pass; ruff clean | Builder Agent |
| Acceptance | Runtime acceptance tests 7/7 (or documented skip rationale) | Reviewer Agent |
| Merge | Code review approved, all gates pass | PM Agent |

## Acceptance Test Scenarios

### AT-001: Simple Unknown Agent Command (Simple Path)
**Description**: User sends a command to an unknown agent via the simple (single-agent, synchronous) path
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@unknown-agent do something`
2. Observe REPL output
**Expected Result**: Error message: `Unknown agent: 'unknown-agent'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`
**Verification**: No task dispatched; no status entry created for "unknown-agent"

### AT-002: Unknown Agent in Background Command (Advanced Path)
**Description**: User sends a background command to an unknown agent, which previously bypassed validation
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@unknown-agent do something &`
2. Observe REPL output
**Expected Result**: Error message listing valid agents; no background task spawned
**Verification**: Status window does not show "unknown-agent"; no task result produced

### AT-003: Multi-Agent Command with One Invalid ID
**Description**: User sends a multi-agent command where one of the agent IDs is invalid
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@builder-1,fake-agent implement the feature`
2. Observe REPL output
**Expected Result**: Error message identifying "fake-agent" as unknown; entire command rejected (builder-1 does not execute)
**Verification**: No task dispatched for either agent; no status entries created

### AT-004: Pipeline Command with Unknown Agent
**Description**: User creates a pipeline where one stage targets an unknown agent
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@fake -> @pm create a plan`
2. Observe REPL output
**Expected Result**: Error message identifying "fake" as unknown; no pipeline stages execute
**Verification**: No tasks dispatched; PM does not receive any input

### AT-005: Valid Alias Continues to Work
**Description**: User uses a valid agent alias that should resolve to a canonical agent ID
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@project_manager create a project plan`
2. Observe REPL output
**Expected Result**: Command is accepted and routed to the `pm` agent; plan is produced
**Verification**: PM agent executes successfully; status shows "pm" as active

### AT-006: All Six Valid Agents Work (Regression)
**Description**: Verify that all 6 valid agents continue to accept commands
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@pm plan this`
2. User enters: `@ba analyze this`
3. User enters: `@writer document this`
4. User enters: `@builder-1 build this`
5. User enters: `@builder-2 build that`
6. User enters: `@reviewer review this`
**Expected Result**: All 6 commands are accepted and dispatched to the correct agent
**Verification**: Each agent produces output; no validation errors

### AT-007: Typo Near Valid Agent ID
**Description**: User makes a common typo that is close to but not exactly a valid agent ID
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@buidler-1 implement login`
2. Observe REPL output
**Expected Result**: Error message: `Unknown agent: 'buidler-1'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`
**Verification**: No task dispatched; user can correct the typo and re-submit

## 14. Open Questions

| Q ID | Question | Owner | Status |
|------|----------|-------|--------|
| — | No open questions | — | — |

## 15. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-02-10 | BA Agent | Initial specification for runtime validator fix and agent validation completion | Creation |

## 16. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Problem Statement | `.teambot/runtime-validator-agent/artifacts/problem_statement.md` | Root cause analysis, impact assessment, success criteria | N/A |
| REF-002 | Source Code | `src/teambot/orchestration/acceptance_test_executor.py:518-542` | `_is_expected_error_scenario()` — keyword matching method | N/A |
| REF-003 | Source Code | `src/teambot/orchestration/acceptance_test_executor.py:133-139` | `_extract_field()` — markdown field extraction preserving backticks | N/A |
| REF-004 | Source Code | `src/teambot/orchestration/acceptance_test_executor.py:359-430` | Command execution loop — error path and expected-error check | N/A |
| REF-005 | Source Code | `src/teambot/tasks/executor.py:162-202` | `TaskExecutor.execute()` — agent ID validation guard | N/A |
| REF-006 | Source Code | `src/teambot/ui/app.py:143-160` | `TeamBotApp._handle_agent_command()` — agent ID validation | N/A |
| REF-007 | Source Code | `src/teambot/ui/agent_state.py:153-216` | `AgentStatusManager` guard clauses in `set_idle()`, `_update()`, `set_model()` | N/A |
| REF-008 | Source Code | `src/teambot/repl/router.py:20` | `VALID_AGENTS` — canonical set of valid agent IDs | N/A |
| REF-009 | Test Results | `.teambot/unknown-agent-validation/artifacts/acceptance_test_results.md` | Runtime acceptance results: 2/7 pass, AT-001/002/007 false failures | N/A |
| REF-010 | Existing Spec | `.teambot/unknown-agent-validation/artifacts/feature_spec.md:242-309` | Original acceptance test scenario definitions with backtick-formatted expected results | N/A |
| REF-011 | Test Code | `tests/test_orchestration/test_acceptance_test_executor.py:458-480` | Existing `_is_expected_error_scenario()` tests | N/A |
| REF-012 | Test Code | `tests/test_acceptance_validation.py` | 21 unit-level acceptance tests — all passing | N/A |

### Citation Usage
All source code references verified via direct file inspection on 2026-02-10. Line numbers correspond to current HEAD.

## 17. Appendices (Optional)

### Glossary
| Term | Definition |
|------|-----------|
| Runtime Validator | The `AcceptanceTestExecutor` component that executes acceptance test scenarios at runtime and compares actual vs expected behaviour |
| Expected-Error Scenario | An acceptance test scenario where the expected result is an error message (e.g., unknown agent rejection) — command failure is correct behaviour |
| `VALID_AGENTS` | The canonical set of 6 valid agent IDs: `{pm, ba, writer, builder-1, builder-2, reviewer}` defined in `router.py` |
| Guard Clause | An early-return validation check that rejects invalid input before the main execution path |

### Target Codebase Summary
```
src/teambot/orchestration/acceptance_test_executor.py  — Runtime validator (primary fix target)
  ├─ _extract_field()            line 133   — Markdown field extraction (preserves backticks)
  ├─ extract_commands_from_steps() line 142 — Command extraction from test steps
  ├─ _is_expected_error_scenario() line 518 — Error-scenario keyword matching (FIX TARGET)
  └─ execute loop                line 359   — Command execution with error path handling

src/teambot/tasks/executor.py    — TaskExecutor (verify guard)
  └─ execute()                   line 162   — Agent ID validation before dispatch

src/teambot/ui/app.py            — TeamBotApp (verify guard)
  └─ _handle_agent_command()     line 143   — Agent ID validation before processing

src/teambot/ui/agent_state.py    — AgentStatusManager (verify guard)
  ├─ set_idle()                  line 153   — Guard: reject unknown agents
  ├─ _update()                   line 178   — Guard: reject unknown agents
  └─ set_model()                 line 199   — Guard: reject unknown agents

src/teambot/repl/router.py       — Single source of truth
  └─ VALID_AGENTS                line 20    — {"pm", "ba", "writer", "builder-1", "builder-2", "reviewer"}
```

### Testing Preference
**Code-First** — Logic is straightforward guard clauses and keyword matching. Write implementation first, then add targeted unit tests.

### Technical Stack
* **Language**: Python
* **Test Framework**: pytest with pytest-cov and pytest-mock
* **Linting**: Ruff (`ruff check .` and `ruff format .`)
* **Package Manager**: uv (`uv run pytest`)

Generated 2026-02-10 by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
