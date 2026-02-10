<!-- markdownlint-disable-file -->
# Specification Review: Fix Runtime Validator Error-Scenario Detection & Complete Agent Validation Guards

**Review Date**: 2026-02-10
**Specification**: `.teambot/runtime-validator-agent/artifacts/feature_spec.md`
**Problem Statement**: `.teambot/runtime-validator-agent/artifacts/problem_statement.md`
**Reviewer**: Specification Review Agent
**Status**: APPROVED

## Overall Assessment

This is a well-structured, thorough specification for a targeted bug-fix and feature-completion objective. All 17 template sections are populated with substantive content, code references are accurate (verified against current HEAD), and the 9 functional requirements are testable with clear acceptance criteria. The specification correctly scopes the work to 3 distinct but related concerns — runtime validator backtick handling, agent validation guard completeness, and test coverage — and explicitly documents what is out of scope (AT-004 and AT-006 failures). One important gap was identified in the App pipeline validation coverage (see §Issues below), but it is mitigated by the TaskExecutor's own pipeline validation.

**Completeness Score**: 9/10
**Clarity Score**: 9/10
**Testability Score**: 9/10
**Technical Readiness**: 9/10

## ✅ Strengths

* **Accurate code references**: All 12 source code references (REF-002 through REF-012) were verified against the live codebase — line numbers, method signatures, and code content match exactly
* **Well-defined scope boundary**: Clear separation between the 3 in-scope error-scenario misclassifications (AT-001, AT-002, AT-007) and the 2 out-of-scope failures (AT-004 pipeline content, AT-006 output matching), with rationale for each exclusion
* **Concrete acceptance test scenarios**: 7 scenarios with specific commands, expected outputs, and verification criteria — directly executable by builders
* **Strong traceability**: Every FR links to a Goal, every Goal has a measurable baseline→target, and the Appendix codebase summary provides a clear map of all touch points
* **Pragmatic constraints**: The "runtime validation flexibility" constraint (skip with documented rationale if too complex) prevents scope creep while preserving the quality aspiration
* **Defence-in-depth approach**: Stripping backticks before matching (rather than adding more keywords) makes the fix robust against future markdown formatting variations
* **Existing guard implementations verified**: The spec correctly identifies that TaskExecutor (line 178-196), App (line 149-160), and AgentStatusManager (lines 159-161, 187-188, 207-208) guards already exist and need verification, not greenfield implementation

## ⚠️ Issues Found

### Important (Should Address)

* **[IMPORTANT-1]** App pipeline validation gap in FR-004
  * **Location**: Section 6, FR-004; also `src/teambot/ui/app.py` lines 149-160
  * **Detail**: FR-004 states "validates all agent IDs against `VALID_AGENTS` before processing," but the App's current validation loop iterates over `command.agent_ids` only — it does **not** validate agent IDs embedded in pipeline stages (`command.pipeline[*].agent_ids`). If a pipeline command like `@fake -> @pm create a plan` is processed, the App would not catch `fake` in its own validation.
  * **Mitigating factor**: `TaskExecutor.execute()` (FR-003, lines 181-183) **does** iterate over pipeline stages and validates all embedded agent IDs before dispatch. So the gap is a defence-in-depth omission, not a functional bypass.
  * **Recommendation**: Either (a) update FR-004's acceptance criteria to clarify that App validation covers `command.agent_ids` only and pipeline stages are validated by the TaskExecutor, or (b) extend the App validation to include pipeline stage agent IDs for consistency. Option (a) is recommended to honour the "minimal changes" constraint.

* **[IMPORTANT-2]** Root cause hypothesis is hedged rather than confirmed
  * **Location**: Section 2, Root Causes (RC-1)
  * **Detail**: RC-1 states "there **may be** an edge case where the extracted text format...prevents `_is_expected_error_scenario()` from being consulted." The spec acknowledges that backticks alone shouldn't prevent keyword matching (since `"error message"` is still present in the lowered text). This suggests the root cause might be subtler — perhaps an exception in the command execution path, a parse failure before `_is_expected_error_scenario()` is reached, or `_extract_field()` returning unexpected content for these specific scenarios.
  * **Impact**: A builder implementing FR-001 (backtick stripping) alone may find it doesn't resolve the issue if the real root cause is upstream.
  * **Recommendation**: The builder should add a diagnostic step during implementation: extract the actual `expected_result` value for AT-001/002/007 at runtime and log it, confirming whether backtick stripping alone resolves the issue before proceeding. The spec's "Code-First" testing approach accommodates this naturally — implement the fix, run the test, iterate if needed.

### Minor (Nice to Have)

* **[MINOR-1]** NFR-001 metric ("< 10 lines changed in acceptance_test_executor.py") is reasonable but may need adjustment if the root cause turns out to be in the execution loop rather than `_is_expected_error_scenario()` alone. Consider softening to "minimal change footprint" with code review as the validation method.

* **[MINOR-2]** Goals table is missing the "Timeframe" column that appears in the template. Not critical for a sprint-scoped bug fix, but noted for template compliance.

* **[MINOR-3]** The Metrics table in §8 shows "4/7" as baseline for "AT scenarios correctly classified" but the acceptance test results show 2/7 passed. The discrepancy is because 3 are misclassified (the target of this fix) and 2 are separate failures (out of scope). Consider adding a note clarifying this distinction.

## Testing Readiness

### Test Strategy Status
* **Testing Approach**: ✅ DEFINED — Code-First (documented in §17 Appendices and objective context)
* **Coverage Requirements**: ✅ SPECIFIED — FR-008 and FR-009 enumerate specific test cases for error-scenario detection and agent validation guards
* **Test Data Needs**: ✅ DOCUMENTED — Specific input strings defined in FR-001 acceptance criteria (backtick-formatted expected_result text)

### Testability Issues
* All 9 functional requirements have measurable acceptance criteria ✅
* FR-001 includes a specific test assertion: `_is_expected_error_scenario()` returns `True` for `"Error message: \`Unknown agent: 'unknown-agent'\`"` ✅
* FR-008 enumerates 5 test categories (backtick, plain text, empty, no indicators, mixed) ✅
* FR-009 enumerates test paths (TaskExecutor, App, AgentStatusManager × simple, multi-agent, pipeline) ✅

### Acceptance Test Scenarios
* 7 scenarios defined (AT-001 through AT-007) ✅
* Each has Description, Preconditions, Steps, Expected Result, and Verification ✅
* Scenarios cover: simple path, background, multi-agent, pipeline, alias, regression, typo ✅
* Scenarios are concrete with specific commands and expected error messages ✅

## Technical Stack Clarity

* **Primary Language**: ✅ SPECIFIED — Python
* **Test Framework**: ✅ SPECIFIED — pytest with pytest-cov and pytest-mock
* **Linting**: ✅ SPECIFIED — Ruff (`ruff check .` and `ruff format .`)
* **Package Manager**: ✅ SPECIFIED — uv (`uv run pytest`)
* **Technical Constraints**: ✅ CLEAR — Single source of truth, local imports, minimal changes, backward compatibility

## Missing Information

### Required Before Research
* None — all critical information is present

### Recommended Additions
* A diagnostic step in the implementation plan to confirm the exact `expected_result` value extracted at runtime for AT-001/002/007 (per IMPORTANT-2)
* Clarification on whether FR-004 App validation should cover pipeline stages or defer to TaskExecutor (per IMPORTANT-1)

## Validation Checklist

* [x] All required sections present and substantive
* [x] Technical stack explicitly defined
* [x] Testing approach documented
* [x] All requirements are testable
* [x] Success metrics are measurable
* [x] Dependencies are identified
* [x] Risks have mitigation strategies
* [x] No unresolved critical questions
* [x] Acceptance test scenarios defined (7 scenarios)
* [x] Code references verified against current HEAD

## Recommendation

**APPROVE FOR RESEARCH** — The specification is comprehensive, accurate, and ready for implementation. The two Important issues identified are refinements, not blockers:

1. **IMPORTANT-1** (App pipeline gap): Can be resolved during implementation by adding a clarifying note to FR-004. The TaskExecutor already covers pipeline validation, so this is not a functional gap.
2. **IMPORTANT-2** (Root cause confirmation): The Code-First approach naturally accommodates diagnostic iteration. The builder should verify the fix resolves the issue and iterate if backtick stripping alone is insufficient.

### Next Steps
1. Address IMPORTANT-1 by clarifying FR-004 scope (App validates `command.agent_ids`; pipeline stages validated by TaskExecutor)
2. Proceed to implementation with diagnostic logging for RC-1 confirmation
3. Run `uv run pytest` baseline before any changes
4. Implement FR-001 (backtick stripping) first, verify against AT-001/002/007, then proceed to FR-003–FR-009

## Approval Sign-off

* [x] Specification meets quality standards for research phase
* [x] All critical issues are addressed or documented
* [x] Technical approach is sufficiently defined
* [x] Testing strategy is ready for detailed planning

**Ready for Research Phase**: YES
