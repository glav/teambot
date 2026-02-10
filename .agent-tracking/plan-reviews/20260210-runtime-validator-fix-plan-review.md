<!-- markdownlint-disable-file -->
# Implementation Plan Review: Runtime Validator Fix for Unknown Agent Validation

**Review Date**: 2026-02-10
**Plan File**: .agent-tracking/plans/20260210-runtime-validator-fix-plan.instructions.md
**Details File**: .agent-tracking/details/20260210-runtime-validator-fix-details.md
**Reviewer**: Implementation Plan Review Agent
**Status**: APPROVED (after revision — line references and details corrected)

## Overall Assessment

The plan is well-structured with a sound investigation-first approach that correctly identifies the discrepancy between unit test behaviour and runtime behaviour. The 4-phase progression (investigate → fix → remaining issues → verify) is appropriate and the dependency graph is clean. However, **all 8 plan-to-details line references are incorrect** (off by 3–30 lines), one details section contains inaccurate code snippets, and the test plan has a minor scope gap. These are straightforward fixes that should not require re-planning.

**Completeness Score**: 8/10
**Actionability Score**: 7/10
**Test Integration Score**: 8/10
**Implementation Readiness**: 7/10

## ✅ Strengths

* **Investigation-first approach**: Phase 1 correctly prioritises root cause confirmation before applying fixes — avoids building on unverified assumptions
* **Multiple fix options per task**: T2.1 provides 4 conditional fix paths, T3.1 provides 3 options, T3.2 provides 3 options — the builder can choose based on investigation findings without returning to the planner
* **Accurate problem analysis**: Correctly identifies that `_is_expected_error_scenario()` unit tests pass (line 462 of test file confirms backtick text works) but runtime fails — points investigation at the parsing/flow layer
* **Core validation confirmed done**: Correctly identifies that all prior plan phases (TaskExecutor, App, AgentStatusManager) are fully implemented and tested
* **Clean dependency graph**: No circular dependencies; critical path (T1.1 → T2.1 → T2.2 → T4.1) is well-identified; parallel opportunities noted

## ⚠️ Issues Found

### Critical (Must Fix Before Implementation)

#### [CRITICAL-1] All Plan → Details Line References Are Incorrect

* **Location**: Plan lines 80, 91, 103, 127, 142, 166, 179, 204
* **Problem**: Every task's line reference to the details file is offset by 3–30 lines. This will cause the builder to look at wrong sections.
* **Impact**: Builder may implement against wrong task details, leading to wasted time or incorrect fixes.
* **Required Fix**: Update all 8 line references in the plan file:

| Task | Plan Says | Should Be |
|------|-----------|-----------|
| T1.1 | Lines 11-60 | Lines 10-62 |
| T1.2 | Lines 62-85 | Lines 65-97 |
| T1.3 | Lines 87-108 | Lines 100-128 |
| T2.1 | Lines 110-155 | Lines 131-177 |
| T2.2 | Lines 157-195 | Lines 180-223 |
| T3.1 | Lines 197-228 | Lines 226-242 |
| T3.2 | Lines 230-260 | Lines 245-267 |
| T4.1 | Lines 262-285 | Lines 270-299 |

### Important (Should Address)

#### [IMPORTANT-1] Details File T1.3 Contains Inaccurate `_verify_expected_output()` Code

* **Location**: Details file, lines 108-115 (Task 1.3 investigation)
* **Problem**: The pseudo-code shows `expected.split()` and `len(t) > 3 and t.isalpha()`, but the actual code at acceptance_test_executor.py line 504-505 uses `re.findall(r"\b\w{4,}\b", expected)` with a `common_words` exclusion set (lines 489-503). The `common_words` set notably excludes "agent" — which appears in AT-006's expected text.
* **Impact**: Builder following the details file would have an incorrect mental model of the matching logic, potentially leading to a wrong fix for AT-006.
* **Recommendation**: Update the code snippet in details T1.3 to match the actual implementation, and note that the `common_words` exclusion of "agent" removes a key term from AT-006's expected text.

#### [IMPORTANT-2] Integration Test (T2.2) Has Placeholder Body

* **Location**: Details file, line 212-216 (task 2.2 regression tests)
* **Problem**: The `test_runtime_expected_error_integration` test body contains only `...` (ellipsis placeholder). This is the most critical test — it validates the full runtime flow end-to-end.
* **Recommendation**: Flesh out the integration test template. The existing test at test_acceptance_test_executor.py lines 483-506 provides a pattern — but note it uses simplified text "Error message: Unknown agent" without backticks. The new test should use exact feature spec formatting.

#### [IMPORTANT-3] Task Count Mismatch in T2.2

* **Location**: Plan line 151 says "All 5 tests pass" but plan lines 144-148 list 5 named tests plus "All tests use actual text formats" (which is a constraint, not a test)
* **Problem**: Minor confusion — the 5 test count is correct (5 bullet points, 5 tests), but the details file lists 5 tests including the integration placeholder. If the integration test is properly implemented, there are exactly 5 tests. This is a non-issue upon closer inspection.
* **Recommendation**: No change needed, but the integration test placeholder must be resolved per IMPORTANT-2.

### Minor (Nice to Have)

* **Plan line 106**: References `_verify_expected_output()` at "lines 490-515" but actual method starts at line 476 (docstring) / 480 (body). Could confuse builder. Suggest updating to "lines 476-515".
* **Details T3.2 line 258**: Suggests adding `_is_positive_success_scenario()` as a new method — this adds scope. The simpler fix of just skipping output matching when all commands succeed may be preferable. Clarify this is the fallback option, not the first choice.
* **Effort estimate**: T1.1 is estimated at 20 min (MEDIUM complexity) but involves writing a diagnostic test, running it, interpreting results, and documenting findings — may be closer to 30 min.

## Test Strategy Integration

### Test Phase Validation
* **Test Strategy Document**: ✅ FOUND (20260209-unknown-agent-validation-test-strategy.md)
* **Test Phases in Plan**: ✅ PRESENT (T2.2 in Phase 2)
* **Test Approach Alignment**: ✅ ALIGNED (Code-First — fix first, test after)
* **Coverage Requirements**: ✅ SPECIFIED (5 regression tests targeting the fix)

### Test Implementation Details

| Component | Test Approach | Phase | Coverage Target | Status |
|-----------|---------------|-------|-----------------|--------|
| `_is_expected_error_scenario()` fix | Code-First | Phase 2 (T2.2) | 100% of fix | ✅ OK |
| `_extract_field()` fix | Code-First | Phase 2 (T2.2) | backtick content | ✅ OK |
| AT-004 pipeline fix | Code-First | Phase 3 (T3.1) | 1 test | ⚠️ Mentioned but not detailed |
| AT-006 output match fix | Code-First | Phase 3 (T3.2) | conditional | ⚠️ May be runtime-skip |

### Test-Related Issues
* The existing integration test (line 483-506 of test file) uses **simplified** expected_result text — it does NOT reproduce the real feature spec format. The new integration test in T2.2 must use exact feature spec text to be a valid regression test.
* Phase 3 tasks (T3.1, T3.2) mention "Add test" but don't spec the test cases. This is acceptable since the fix approach is TBD (depends on investigation), but the builder should be reminded.

## Phase Analysis

### Phase 1: Root Cause Investigation
* **Status**: ✅ Ready
* **Task Count**: 3 tasks (T1.1, T1.2, T1.3)
* **Issues**: None — investigation tasks are well-scoped with clear success criteria
* **Dependencies**: All satisfied (source files, feature spec, test infrastructure exist)
* **Note**: All 3 tasks can run in parallel ✅

### Phase 2: Fix Expected Error Recognition
* **Status**: ⚠️ Needs Work (line references + integration test placeholder)
* **Task Count**: 2 tasks (T2.1, T2.2)
* **Issues**: Line references incorrect; integration test body is placeholder
* **Dependencies**: Depends on Phase 1 findings — properly gated

### Phase 3: Fix Remaining Runtime Failures
* **Status**: ✅ Ready (conditional on Phase 1 findings)
* **Task Count**: 2 tasks (T3.1, T3.2)
* **Issues**: None — multiple fix options provided for each, builder chooses based on investigation
* **Dependencies**: Properly gated on Phase 1 investigation

### Phase 4: Final Verification
* **Status**: ✅ Ready
* **Task Count**: 1 task (T4.1)
* **Issues**: None — comprehensive checklist
* **Dependencies**: Properly gated on all prior phases

## Line Number Validation

### Invalid References Found

#### Plan → Details References (ALL 8 INVALID)

| Task | Plan Ref | Actual Lines | Offset |
|------|----------|-------------|--------|
| T1.1 | Lines 11-60 | Lines 10-62 | -1/+2 |
| T1.2 | Lines 62-85 | Lines 65-97 | +3/+12 |
| T1.3 | Lines 87-108 | Lines 100-128 | +13/+20 |
| T2.1 | Lines 110-155 | Lines 131-177 | +21/+22 |
| T2.2 | Lines 157-195 | Lines 180-223 | +23/+28 |
| T3.1 | Lines 197-228 | Lines 226-242 | +29/+14 |
| T3.2 | Lines 230-260 | Lines 245-267 | +15/+7 |
| T4.1 | Lines 262-285 | Lines 270-299 | +8/+14 |

#### Source Code References in Plan (MOSTLY VALID)

| Reference | Plan Says | Actual | Status |
|-----------|-----------|--------|--------|
| `_is_expected_error_scenario()` | lines 517-542 | lines 517-542 | ✅ Valid |
| `_extract_field()` | line 135 | lines 133-139 | ✅ Close enough |
| Runtime loop | lines 365-402 | lines 365-402 | ✅ Valid |
| `_verify_expected_output()` | lines 490-515 | lines 476-515 | ⚠️ Starts earlier (line 476 with docstring) |
| Output matching | lines 411-423 | lines 411-423 | ✅ Valid |

### Valid References
* Source code references are accurate ✅ (with minor offset on `_verify_expected_output`)

## Dependencies and Prerequisites

### External Dependencies
* None — all work is internal to the codebase

### Internal Dependencies
* Core validation (TaskExecutor, App, AgentStatusManager): ✅ DONE and verified in source code
* `VALID_AGENTS` / `AGENT_ALIASES` in router.py: ✅ Present (lines 19-27)
* Feature spec with AT scenarios: ✅ Present at `.teambot/unknown-agent-validation/artifacts/feature_spec.md`
* Existing executor tests: ✅ Present (includes `_is_expected_error_scenario` tests at lines 458-506)

### Missing Dependencies Identified
* None

### Circular Dependencies
* None found ✅

## Research Alignment

### Alignment Score: 9/10

#### Well-Aligned Areas
* Plan correctly builds on completed research (all 3 code changes implemented per research recommendations)
* Error message format matches research specification exactly
* Local-import pattern preserved per research guidance

#### Misalignments Found
* **Minor**: Research focused on the 3 production code changes (executor, app, agent_state); it does not cover the runtime validator bug. This is expected — the runtime validator issue was discovered after the initial research/implementation cycle. The plan correctly treats it as a new investigation.

#### Missing Research Coverage
* `AcceptanceTestExecutor` parsing and runtime flow are not covered by the original research. The plan correctly addresses this via Phase 1 investigation rather than assuming.

## Actionability Assessment

### Clear and Actionable Tasks
* 6/8 tasks have specific file paths, line numbers, and action verbs ✅
* All tasks have measurable success criteria ✅

### Needs Clarification
* **T2.2 integration test**: The test body is a placeholder (`...`) — builder needs concrete guidance
* **T3.1/T3.2 tests**: Plan mentions "Add test" but doesn't specify test file location or pattern

### Success Criteria Validation
* **Clear Criteria**: 8 tasks (all have explicit pass/fail criteria)
* **Vague Criteria**: 0 tasks
* **Missing Criteria**: 0 tasks

## Risk Assessment

### High Risks Identified
* None

### Medium Risks

#### Risk: Root cause may not match any hypothesised scenario
* **Category**: Technical
* **Impact**: MEDIUM
* **Probability**: LOW (4 likely causes ranked in details)
* **Affected Tasks**: T1.1 → T2.1
* **Mitigation**: T1.1 is an investigation task with diagnostic test — will reveal actual cause regardless. Plan provides 4 fix paths for T2.1.

### Low Risks

#### Risk: AT-006 fix may require new method
* **Category**: Technical
* **Impact**: LOW
* **Probability**: MEDIUM
* **Affected Tasks**: T3.2
* **Mitigation**: Plan offers 3 options including simple runtime-skip. Objective explicitly allows skipping runtime validation with rationale.

## Implementation Quality Checks

### Code Quality Provisions
- [x] Linting mentioned in success criteria (T4.1)
- [x] Format check mentioned (T4.1 — `ruff format .`)
- [x] Minimal-change constraint stated (T2.1)

### Error Handling
- [x] Error scenarios identified (all 5 failing ATs analysed)
- [x] Validation steps included (phase gates)
- [x] Regression check (AT-003, AT-005 must continue passing)

### Documentation Requirements
- [x] Fix rationale documented per task
- [x] Skip rationale required if AT-006 runtime-skipped

## Missing Elements

### Critical Missing Items
1. **Correct line references** — All 8 plan → details references must be updated (see CRITICAL-1)

### Recommended Additions
* Flesh out T2.2 integration test body (see IMPORTANT-2)
* Update T1.3 code snippet to match actual `_verify_expected_output()` implementation (see IMPORTANT-1)

## Validation Checklist

- [x] All required sections present in plan file
- [x] Every plan task has corresponding details entry
- [x] Test strategy is integrated appropriately (Code-First, Phase 2)
- [ ] **All line number references are accurate** ← FAILS (8/8 plan→details refs incorrect)
- [x] Dependencies are identified and satisfiable
- [x] Success criteria are measurable
- [x] Phases follow logical progression
- [x] No circular dependencies exist
- [x] Research findings are incorporated
- [x] File paths are specific and correct
- [x] Tasks are atomic and independently completable

## Recommendation

**Overall Status**: APPROVED_FOR_IMPLEMENTATION

### Revision Applied

The 3 issues identified during review have been corrected in-place:

1. ✅ **[CRITICAL-1]** All 8 plan → details line references updated to correct values
2. ✅ **[IMPORTANT-1]** T1.3 `_verify_expected_output()` code snippet updated with actual implementation (including `common_words` exclusion set)
3. ✅ **[IMPORTANT-2]** Integration test placeholder replaced with concrete test template using backtick-formatted feature spec text

### After Revision

Once the 3 items above are addressed, this plan is **APPROVED FOR IMPLEMENTATION**. The builder should be `@builder-1` or `@builder-2`, starting with Phase 1 (all 3 investigation tasks can run in parallel).

### Next Steps

1. Proceed to **Step 7** (`sdd.7-task-implementer-for-feature.prompt.md`)
2. Assign implementation to `@builder-1` or `@builder-2`
3. Builder starts with Phase 1 (all 3 investigation tasks can run in parallel)

## Approval Sign-off

- [x] Plan structure is complete and well-organized
- [x] Test strategy is properly integrated
- [x] All tasks are actionable with clear success criteria
- [x] Dependencies are identified and satisfiable
- [x] **Line references are accurate** ← FIXED (all 8 corrected)
- [x] No critical blockers exist
- [x] Implementation risks are acceptable

**Ready for Implementation Phase**: YES

**Conditional Notes**: All revision items resolved. Plan approved for immediate implementation.

---

**Review Status**: COMPLETE
**Approved By**: Plan Review Agent (post-revision)
**Implementation Can Proceed**: YES
