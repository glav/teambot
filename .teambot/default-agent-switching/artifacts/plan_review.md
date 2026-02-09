<!-- markdownlint-disable-file -->
# Implementation Plan Review: Runtime Default Agent Switching

**Review Date**: 2026-02-09
**Plan File**: `.agent-tracking/plans/20260209-default-agent-switching-plan.instructions.md`
**Details File**: `.agent-tracking/details/20260209-default-agent-switching-details.md`
**Research File**: `.agent-tracking/research/20260209-default-agent-switching-research.md`
**Test Strategy File**: `.agent-tracking/test-strategies/20260209-default-agent-switching-test-strategy.md`
**Reviewer**: Implementation Plan Review Agent
**Status**: APPROVED (Conditional)

## Overall Assessment

This is a well-constructed, comprehensive implementation plan that correctly extends existing patterns (handle_model, set_executor, AgentStatusManager.set_model) to deliver the runtime default agent switching feature. The plan correctly implements a Hybrid TDD/Code-First approach with 25 tasks across 8 phases, covering all 11 success criteria from the objective. All source code line references are verified accurate against the current codebase. The only critical issue is that the Plan → Details file cross-references use incorrect line numbers, which must be corrected before handoff to the builder.

**Completeness Score**: 9/10
**Actionability Score**: 9/10
**Test Integration Score**: 10/10
**Implementation Readiness**: 8/10

## ✅ Strengths

* **Excellent pattern adherence**: Every new component follows an existing codebase pattern (handle_model for commands, set_executor for wiring, set_model for status manager). Minimizes architectural risk.
* **Precise source code references**: All references to actual source files (router.py:52, commands.py:218-277, agent_state.py:194-209, etc.) are verified accurate against the current codebase.
* **Test strategy integration**: TDD for core routing and command logic (highest-risk), Code-First for UI and wiring (lower-risk) — exactly matching the test strategy document's recommendations.
* **Comprehensive dependency graph**: Mermaid diagram with critical path, parallel opportunities, and phase gates with explicit "Cannot Proceed If" conditions.
* **Full objective coverage**: All 11 success criteria from the objective are addressed by specific tasks.
* **Effort estimation**: All 25 tasks estimated with complexity and risk ratings.
* **Both modes covered**: Plan explicitly addresses REPL (loop.py) and split-pane UI (app.py) paths throughout.

## ⚠️ Issues Found

### Critical (Must Fix Before Implementation)

#### [CRITICAL] Plan → Details Line References Are All Incorrect

* **Location**: Every `Details: Lines X-Y` reference in the plan file
* **Problem**: All line references in the plan pointing to the details file use incorrect line numbers. The offset grows progressively — Phase 1 is off by ~10-30 lines, Phase 7 is off by ~200+ lines. The details file contains extensive code blocks that weren't accounted for in the line numbering.
* **Impact**: A builder following the plan's line references would land on the wrong section of the details file, causing confusion and potential implementation errors.
* **Required Fix**: Update all line references. Corrected values provided below.

**Corrected Line Reference Table:**

| Plan Reference | Claimed Lines | Actual Lines | Content |
|----------------|--------------|--------------|---------|
| Phase 1 | 1-77 | 11-116 | Core Router Mutation |
| Task 1.1 | 10-39 | 13-69 | Router mutation tests |
| Task 1.2 | 41-77 | 71-114 | Implement set_default_agent |
| Phase 2 | 79-162 | 118-283 | Command Handlers |
| Task 2.1 | 85-115 | 120-166 | use-agent tests |
| Task 2.2 | 117-138 | 168-213 | Implement handle_use_agent |
| Task 2.3 | 140-155 | 215-246 | reset-agent tests |
| Task 2.4 | 157-162 | 248-281 | Implement handle_reset_agent |
| Phase 3 | 164-217 | 285-367 | SystemCommands Integration |
| Task 3.1 | 170-188 | 287-319 | Add router to SystemCommands |
| Task 3.2 | 190-210 | 321-342 | Add dispatch entries |
| Task 3.3 | 212-217 | 344-365 | Dispatch integration tests |
| Phase 4 | 219-276 | 369-449 | Help and Status Updates |
| Task 4.1 | 225-238 | 371-382 | Update help text |
| Task 4.2 | 240-260 | 384-408 | Update handle_status |
| Task 4.3 | 262-270 | 410-423 | Wire status to router |
| Task 4.4 | 272-276 | 425-447 | Help/status tests |
| Phase 5 | 278-318 | 451-518 | AgentStatusManager |
| Task 5.1 | 284-306 | 453-485 | Add default_agent tracking |
| Task 5.2 | 308-318 | 487-516 | StatusManager tests |
| Phase 6 | 320-360 | 520-583 | Status Panel Indicator |
| Task 6.1 | 326-350 | 522-557 | Add default indicator |
| Task 6.2 | 352-360 | 559-581 | Panel indicator tests |
| Phase 7 | 362-440 | 585-696 | Wiring — REPL and UI |
| Task 7.1 | 368-380 | 587-607 | Wire router in loop.py |
| Task 7.2 | 382-398 | 609-629 | Wire router in app.py |
| Task 7.3 | 400-418 | 631-642 | UI post-dispatch update |
| Task 7.4 | 420-432 | 644-665 | UI _get_status update |
| Task 7.5 | 434-440 | 667-693 | Wiring integration tests |

### Important (Should Address)

#### [IMPORTANT] Task 6.1 Provides Two Approaches Without Clear Decision

* **Location**: Details file, Task 6.1 (Lines 522-557)
* **Problem**: The details provide two approaches for the status panel indicator (indicator on all states vs. indicator only on idle) and says "Recommendation: Use the first approach" — but the plan file (Task 6.1 description) says "Add ⬤ default label" which suggests the second approach. The builder may be confused about which character to use (★ vs ⬤) and which placement approach to follow.
* **Recommendation**: Make the decision explicit in the plan: use the first approach (indicator on all states) with the ★ character for terminal compatibility. Update the plan description to match.

#### [IMPORTANT] Missing `/help agent` Subtopic Update

* **Location**: Plan Phase 4 / Details Task 4.1
* **Problem**: The `/help agent` subtopic (commands.py lines 41-56) lists available agents but doesn't mention the default agent or `/use-agent` command. Task 4.1 only updates the main `/help` output (lines 85-98). Users who type `/help agent` won't learn about the new feature.
* **Recommendation**: Add a brief note to `/help agent` output mentioning that the default agent can be changed with `/use-agent`. This can be folded into Task 4.1 as a minor addition.

### Minor (Nice to Have)

* The details file research reference at line 69 says "research Lines 344-357" but the cited section actually begins at line 344 with Pattern A heading, not directly with the test example. More precisely it should reference Lines 346-357 for the test pattern itself. Low impact.
* Task 6.2 test code in details (lines 559-581) uses comments as pseudo-assertions ("# Find pm line and verify indicator"). The builder should write proper assertions. The test pattern from test strategy provides clearer guidance.

## Test Strategy Integration

### Test Phase Validation
* **Test Strategy Document**: ✅ FOUND (`.agent-tracking/test-strategies/20260209-default-agent-switching-test-strategy.md`)
* **Test Phases in Plan**: ✅ PRESENT — Tests integrated throughout all 8 phases
* **Test Approach Alignment**: ✅ ALIGNED — TDD for Phases 1-2, Code-First for Phases 3-7
* **Coverage Requirements**: ✅ SPECIFIED — 95% for new code (Phase 8 gate), 100% for TDD components

### Test Implementation Details

| Component | Test Approach | Phase | Coverage Target | Status |
|-----------|---------------|-------|-----------------|--------|
| `AgentRouter` mutation | TDD | Phase 1 (T1.1) | 100% | ✅ OK |
| `handle_use_agent()` | TDD | Phase 2 (T2.1) | 100% | ✅ OK |
| `handle_reset_agent()` | TDD | Phase 2 (T2.3) | 100% | ✅ OK |
| `SystemCommands` dispatch | Code-First | Phase 3 (T3.3) | 90% | ✅ OK |
| `/help` text | Code-First | Phase 4 (T4.4) | 100% | ✅ OK |
| `/status` enhancement | Code-First | Phase 4 (T4.4) | 90% | ✅ OK |
| `AgentStatusManager` default | Code-First | Phase 5 (T5.2) | 100% | ✅ OK |
| `StatusPanel` indicator | Code-First | Phase 6 (T6.2) | 90% | ✅ OK |
| Wiring (loop.py, app.py) | Code-First | Phase 7 (T7.5) | 80% | ✅ OK |

### Test Timing Validation
* ✅ TDD tasks (T1.1, T2.1, T2.3) appear BEFORE their corresponding implementation tasks
* ✅ Code-First tests (T3.3, T4.4, T5.2, T6.2, T7.5) appear AFTER implementation
* ✅ Final validation (T8.1) runs full suite with coverage check

### Test-Related Issues
* None — test strategy is properly integrated throughout the plan.

## Phase Analysis

### Phase 1: Core Router Mutation (TDD)
* **Status**: ✅ Ready
* **Task Count**: 2 tasks
* **Issues**: None — clean extension of existing AgentRouter
* **Dependencies**: Satisfied (AgentRouter exists at router.py:30)

### Phase 2: Command Handlers (TDD)
* **Status**: ✅ Ready
* **Task Count**: 4 tasks
* **Issues**: None — follows handle_model pattern exactly
* **Dependencies**: Depends on Phase 1 (router mutation)

### Phase 3: SystemCommands Integration
* **Status**: ✅ Ready
* **Task Count**: 3 tasks
* **Issues**: None — follows set_executor/set_overlay pattern
* **Dependencies**: Depends on Phase 2 (handler functions)

### Phase 4: Help and Status Updates
* **Status**: ⚠️ Minor gap (missing `/help agent` update)
* **Task Count**: 4 tasks
* **Issues**: `/help agent` subtopic not updated (see [IMPORTANT] above)
* **Dependencies**: Depends on Phase 1 (router methods) and Phase 3 (dispatch wiring)

### Phase 5: AgentStatusManager
* **Status**: ✅ Ready
* **Task Count**: 2 tasks
* **Issues**: None — follows set_model pattern exactly
* **Dependencies**: Depends on Phase 1 (router interface)

### Phase 6: Status Panel Indicator
* **Status**: ⚠️ Ambiguous approach (see [IMPORTANT] above)
* **Task Count**: 2 tasks
* **Issues**: Two approaches provided, needs clear decision
* **Dependencies**: Depends on Phase 5 (AgentStatusManager)

### Phase 7: Wiring — REPL and UI
* **Status**: ✅ Ready
* **Task Count**: 5 tasks
* **Issues**: None — straightforward constructor/setter changes
* **Dependencies**: Depends on Phases 3, 5, 6

### Phase 8: Final Validation
* **Status**: ✅ Ready
* **Task Count**: 3 tasks
* **Issues**: None

## Line Number Validation

### Plan → Details References
* **Status**: ❌ ALL INVALID — See corrected table in Critical Issues section above
* **Total References**: 28 (8 phase-level + 20 task-level)
* **Valid**: 0
* **Invalid**: 28
* **Root Cause**: Line references appear to have been estimated without accounting for multi-line code blocks in the details file

### Details → Research References
* **Status**: ✅ Valid (minor precision issue at line 69)
* Details line 69 references "research Lines 344-357" — content is present and relevant

### Source Code References (in both plan and details)
* **Status**: ✅ ALL VALID — All source code line references verified against current files:
  * router.py: `__init__` at 39, `_default_agent` at 52, `get_default_agent` at 85-91, `_route_raw` at 159-188, `VALID_AGENTS` at 20 ✅
  * commands.py: `handle_help` at 32-112, `handle_status` at 115-132, `handle_model` at 218-277, `SystemCommands` at 515-646 ✅
  * agent_state.py: `AgentStatusManager` at 77, `set_model` at 194-209, `_notify` at 211-217 ✅
  * status_panel.py: `_format_status` at 101-142 ✅
  * loop.py: `SystemCommands()` at 58 ✅
  * app.py: `SystemCommands(executor=executor)` at 55, `_handle_system_command` at 286-315, `_get_status` at 405-430 ✅

## Dependencies and Prerequisites

### External Dependencies
* Python 3.12+: ✅ Available (3.12.12)
* uv: ✅ Available (0.9.27)
* pytest + plugins: ✅ Available
* ruff: ✅ Available

### Internal Dependencies
* `AgentRouter` class: ✅ Exists at router.py:30
* `SystemCommands` class: ✅ Exists at commands.py:515
* `AgentStatusManager` class: ✅ Exists at agent_state.py:77
* `StatusPanel` class: ✅ Exists at status_panel.py:17
* `VALID_AGENTS` constant: ✅ Exists at router.py:20 (already imported in commands.py)

### Circular Dependencies
* None found — dependency graph is a directed acyclic graph (verified from mermaid diagram)

## Research Alignment

### Alignment Score: 10/10

#### Well-Aligned Areas
* **Router extension**: Plan adds `set_default_agent()`/`get_config_default_agent()` exactly as research recommends (research Lines 182-209)
* **Command pattern**: `handle_use_agent()`/`handle_reset_agent()` follow `handle_model()` pattern identified in research (research Lines 256-277)
* **SystemCommands wiring**: Router passed via constructor + setter, matching existing `set_executor`/`set_overlay` (research Lines 236-252)
* **UI state management**: Default agent tracked via `AgentStatusManager` rather than coupling `StatusPanel` to router (research Lines 289-293)
* **Post-dispatch update**: Follows `/model` post-dispatch pattern for UI refresh (research Lines 311-325)

#### Misalignments Found
* None — plan follows research recommendations precisely

## Actionability Assessment

### Clear and Actionable Tasks
* 25/25 tasks have specific action verbs and target files
* 25/25 tasks have measurable success criteria (via phase gates)
* 22/25 tasks include exact code changes with line numbers

### Needs Clarification
* **Task 6.1**: Two approaches presented — needs single clear decision (see Important issue)

### Success Criteria Validation
* **Clear Criteria**: 25 tasks
* **Vague Criteria**: 0 tasks
* **Missing Criteria**: 0 tasks

## Risk Assessment

### Risk 1: Test Breakage from Constructor Changes
* **Category**: Integration
* **Impact**: MEDIUM
* **Probability**: LOW
* **Affected Tasks**: T3.1, T7.1, T7.2
* **Mitigation**: All new parameters are optional (default=None), preserving backward compatibility. ✅ Well mitigated.

### Risk 2: UI Status Panel Rendering Issues
* **Category**: Technical
* **Impact**: LOW
* **Probability**: MEDIUM
* **Affected Tasks**: T6.1
* **Mitigation**: Plan recommends ★ character for terminal compatibility; test coverage will validate rendering. ✅ Acceptable.

### Risk 3: Dual-Path Consistency (REPL vs UI)
* **Category**: Quality
* **Impact**: HIGH
* **Probability**: LOW
* **Affected Tasks**: T4.2, T7.2, T7.3, T7.4
* **Mitigation**: Both paths covered in separate tasks with dedicated tests (T4.4, T7.5). Research explicitly documents both code paths. ✅ Well mitigated.

## Implementation Quality Checks

- [x] Linting mentioned in success criteria (T8.2: `ruff check . && ruff format --check .`)
- [x] Full test suite validation (T8.1: `pytest --cov`)
- [x] Phase gate checkpoints at every phase boundary
- [x] Error scenarios identified (invalid agent, no-router, idempotent operations)
- [x] Validation steps included in phase gates

## Missing Elements

### Critical Missing Items
* None — the plan is comprehensive

### Recommended Additions
* Add `/help agent` subtopic update to Task 4.1 (minor scope increase)
* Make Task 6.1 indicator approach decision explicit (remove ambiguity)

## Validation Checklist

- [x] All required sections present in plan file
- [x] Every plan task has corresponding details entry
- [x] Test strategy is integrated appropriately
- [ ] All line number references are accurate ← **FAILED: Plan→Details refs need correction**
- [x] Dependencies are identified and satisfiable
- [x] Success criteria are measurable
- [x] Phases follow logical progression
- [x] No circular dependencies exist
- [x] Research findings are incorporated
- [x] File paths are specific and correct
- [x] Tasks are atomic and independently completable

## Recommendation

**Overall Status**: APPROVED (Conditional)

### Approval Conditions

The plan is approved for implementation with the following conditions:

1. **REQUIRED**: The Plan → Details line references must be corrected using the table provided in the Critical Issues section above. This is a mechanical fix (no content changes).
2. **RECOMMENDED**: Task 6.1 should commit to the first approach (indicator on all agent states, using ★ character). Remove the alternative approach text to avoid builder confusion.
3. **RECOMMENDED**: Task 4.1 should include a one-line addition to the `/help agent` subtopic mentioning `/use-agent`.

### Why Conditional Approval (not Revision)

The line reference issue is the only blocker, and it is purely mechanical — the corrected values are provided in this review. The plan content, task structure, test integration, source code references, and overall architecture are all sound. Sending back for full revision would waste effort when the fix is a simple find-and-replace of line numbers.

### Next Steps

1. Update plan file line references using the corrected table in this review
2. Clarify Task 6.1 indicator approach (pick one)
3. Proceed to **Step 7** (`sdd.7-task-implementer-for-feature.prompt.md`) for implementation

## Approval Sign-off

- [x] Plan structure is complete and well-organized
- [x] Test strategy is properly integrated
- [x] All tasks are actionable with clear success criteria
- [x] Dependencies are identified and satisfiable
- [ ] Line references are accurate ← **Corrected values provided above**
- [x] No critical blockers exist (line refs are a mechanical fix)
- [x] Implementation risks are acceptable

**Ready for Implementation Phase**: CONDITIONAL

**Conditional Notes**: Builder should use the corrected line reference table from this review (or navigate by section headings in the details file). Line reference corrections should be applied to the plan file before or during implementation.

---

**Review Status**: COMPLETE
**Approved By**: PENDING USER CONFIRMATION
**Implementation Can Proceed**: AFTER LINE REFERENCE CORRECTIONS
