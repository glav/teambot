<!-- markdownlint-disable-file -->
# Specification Review: Unknown Agent ID Validation

**Review Date**: 2026-02-09
**Specification**: .teambot/unknown-agent-validation/artifacts/feature_spec.md
**Reviewer**: Specification Review Agent
**Status**: APPROVED

## Overall Assessment

This is a high-quality, implementation-ready specification for a targeted bug fix. The problem is precisely defined with root-cause analysis grounded in specific code locations. All 17 template sections are populated with substantive content, 7 functional requirements are individually testable with clear acceptance criteria, and 7 acceptance test scenarios cover every command shape (simple, background, multi-agent, pipeline, alias, regression, typo). The specification is well-scoped for a minimal fix and explicitly avoids scope creep.

**Completeness Score**: 10/10
**Clarity Score**: 9/10
**Testability Score**: 10/10
**Technical Readiness**: 10/10

## ✅ Strengths

* **Precise root-cause analysis**: Three root causes identified with exact file paths and line numbers (loop.py:323-336, agent_state.py:153-210, agent_runner.py:55-59). This gives implementers an unambiguous starting point.
* **All command shapes covered**: FRs explicitly address simple, multi-agent, pipeline, background, and $ref paths — no command shape is left unvalidated.
* **Single source of truth enforced**: Both the spec and NFR-002 mandate that `VALID_AGENTS` in `router.py` is the sole authority, with no duplication.
* **Defence-in-depth design**: FR-005 (AgentStatusManager guard) provides a safety net even if upstream validation is somehow bypassed, while FR-001 handles the primary validation.
* **Comprehensive acceptance tests**: 7 scenarios (AT-001 through AT-007) covering the exact bug paths, regression safety, alias support, and typo detection.
* **Well-defined scope boundaries**: Out-of-scope items have clear rationale; constraints prevent scope creep.
* **Existing import pattern acknowledged**: Risk R-001 explicitly notes the circular import concern and references the existing local-import pattern at executor.py:199 as the proven mitigation.
* **User journeys illustrate the bug**: The "Current (broken) journey" vs "Desired journey" comparison in Section 3 makes the problem viscerally clear.

## ⚠️ Issues Found

### Critical (Must Fix Before Research)

None.

### Important (Should Address)

* **[IMPORTANT]** Minor inconsistency in error message format between sections
  * **Location**: Section 5 (UX/UI, line 123) vs FR-007 (line 136) and AT-001 (line 250)
  * **Detail**: Section 5 lists agents in definition order (`pm, ba, writer, builder-1, builder-2, reviewer`), while FR-007 and AT-001 use alphabetically sorted order (`ba, builder-1, builder-2, pm, reviewer, writer`). FR-007 explicitly states "sorted for consistency".
  * **Recommendation**: Update Section 5 UX/UI to use the sorted order to match FR-007, which is the authoritative requirement. This is cosmetic — FR-007 is correct and should be the implementation target.

### Minor (Nice to Have)

* AT scenarios do not include a dedicated `$ref` command test (e.g., `@pm $unknown-agent query`). The spec notes `$ref` validation already exists at executor.py:199, so this is an existing-behaviour test rather than a new-behaviour test. Consider adding an AT-008 for completeness if the reviewer team deems it valuable, but not blocking.
* Section 13 (Rollout) milestone table is missing the "Date" column that the template includes. Acceptable for a bug fix with no calendar-bound release, but noted for template compliance.

## Testing Readiness

### Test Strategy Status
* **Testing Approach**: DEFINED — pytest, test-after pattern (Section 17 Appendix: Technical Stack)
* **Coverage Requirements**: SPECIFIED — NFR-005 mandates 100% path coverage for new code
* **Test Data Needs**: DOCUMENTED — inputs are `command.agent_ids`, `VALID_AGENTS`, `AGENT_ALIASES` (Section 8)

### Testability Issues
* None. All 7 FRs have measurable acceptance criteria. Each acceptance test scenario has concrete steps and expected results.

## Technical Stack Clarity

* **Primary Language**: SPECIFIED — Python
* **Frameworks**: SPECIFIED — pytest for testing
* **Technical Constraints**: CLEAR — no circular imports (local-import pattern), single source of truth, minimal changes

## Missing Information

### Required Before Research
* None. All information needed for implementation is present.

### Recommended Additions
* Optional: AT-008 for `$ref` validation of unknown agent IDs (existing behaviour, low priority)
* Optional: "Date" column in Section 13 milestones (template compliance, non-blocking)

## Validation Checklist

* [x] All required sections present and substantive
* [x] Technical stack explicitly defined
* [x] Testing approach documented
* [x] All requirements are testable
* [x] Success metrics are measurable
* [x] Dependencies are identified
* [x] Risks have mitigation strategies
* [x] No unresolved critical questions
* [x] Acceptance test scenarios defined (7 scenarios — exceeds minimum of 2-3)

## Recommendation

**APPROVE FOR RESEARCH**

This specification is implementation-ready. The one "Important" issue (error message format inconsistency between Section 5 and FR-007) is cosmetic and does not block research or implementation — FR-007 is unambiguous as the authoritative requirement.

### Next Steps
1. Optionally address the Section 5 UX/UI sort-order inconsistency (non-blocking)
2. Proceed to Research phase (`sdd.3-research-feature.prompt.md`)
3. Implementation should follow the feature hierarchy: TaskExecutor validation first (FR-001), then multi-agent/pipeline/background (FR-002–004), then AgentStatusManager guard (FR-005)

## Approval Sign-off

* [x] Specification meets quality standards for research phase
* [x] All critical issues are addressed or documented
* [x] Technical approach is sufficiently defined
* [x] Testing strategy is ready for detailed planning

**Ready for Research Phase**: YES
