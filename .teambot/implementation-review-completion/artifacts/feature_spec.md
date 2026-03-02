<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Implementation Review Completion Check - Feature Specification

Version 1.0 | Status: Draft | Owner: BA Agent | Team: TeamBot | Target: Next Release | Lifecycle: Development

## Progress Tracker

| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-03-02 |
| Problem & Users | ✅ | None | 2026-03-02 |
| Scope | ✅ | None | 2026-03-02 |
| Requirements | ✅ | None | 2026-03-02 |
| Metrics & Risks | ✅ | None | 2026-03-02 |
| Operationalization | ✅ | None | 2026-03-02 |
| Finalization | ✅ | None | 2026-03-02 |

Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context

The TeamBot SDD workflow includes an IMPLEMENTATION_REVIEW stage with `is_review_stage: true`, enabling up to 4 iterations via ReviewIterator. However, this stage currently has `prompt_template: null`, meaning there are no explicit instructions for reviewers to verify task completion before reviewing code quality.

### Core Opportunity

By adding a dedicated prompt template for IMPLEMENTATION_REVIEW that enforces task completion verification as a blocking pre-check, we can detect incomplete implementations early and loop builders back to finish work—leveraging the existing 4-iteration capability.

### Goals

| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | IMPLEMENTATION_REVIEW verifies all plan tasks are complete before code review | Quality | No verification | 100% task verification | Immediate | P0 |
| G-002 | Incomplete implementations are rejected with actionable feedback | Quality | No rejection mechanism | Clear rejection format | Immediate | P0 |
| G-003 | Feedback format enables builders to understand exactly what's missing | UX | Generic feedback | Specific task list | Immediate | P1 |

---

## 2. Problem Definition

### Current Situation

- `IMPLEMENTATION_REVIEW` stage has `prompt_template: null` (stages.yaml line 326)
- Reviewers have no explicit instructions to check task completion
- Task completion verification only happens at POST_REVIEW stage (stage 13 of 14)
- Incomplete implementations may pass IMPLEMENTATION_REVIEW without detection

### Problem Statement

When builder agents fail to complete all planned tasks during the IMPLEMENTATION stage, the workflow has no mechanism to detect incomplete work and loop back. Incomplete implementations proceed through TEST, ACCEPTANCE_TEST stages, wasting resources and compromising workflow integrity.

### Root Causes

- IMPLEMENTATION_REVIEW stage was designed to support iteration (`is_review_stage: true`) but was never given a prompt template
- No explicit verification instructions exist for the reviewer agent at this stage
- Task completion verification logic was deferred to POST_REVIEW (too late in workflow)

### Impact of Inaction

- Incomplete code proceeds through multiple downstream stages before detection
- Wasted compute cycles on testing incomplete features
- Builders receive feedback too late, increasing context-switching cost
- Workflow quality guarantees are undermined

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Builder Agent | Complete implementation tasks efficiently | Unclear feedback on what's incomplete | Primary - receives actionable rejection feedback |
| Reviewer Agent | Verify implementation quality | No instructions for task completion verification | Primary - gains explicit verification protocol |
| Project Manager | Ensure workflow proceeds only when ready | Incomplete work slips through to later stages | Secondary - improved workflow integrity |
| End User | Receive fully implemented features | Incomplete features may reach testing | Secondary - better quality assurance |

---

## 4. Scope

### In Scope

- Create new prompt file `sdd.7b-implementation-review.prompt.md`
- Define pre-code-review checklist (blocking)
- Define rejection format with incomplete task list
- Define approval flow proceeding to code review
- Update `stages.yaml` line 326 to reference new prompt

### Out of Scope (justify if empty)

- Changes to IMPLEMENTATION stage workflow (would cause deadlock with prerequisite checks)
- Changes to ReviewIterator logic (existing 4-iteration behavior is sufficient)
- Changes to POST_REVIEW stage (serves different purpose: final validation)
- New completion signal artifacts (use existing plan markdown checkboxes)

### Assumptions

- Plan files use markdown checkbox format: `- [x]` for complete, `- [ ]` for incomplete
- Changes log exists and documents completed work
- ReviewIterator correctly supports up to 4 iterations
- Reviewer agent can parse markdown checkboxes from plan files

### Constraints

- Solution must be prompt-only (no code changes to orchestrator)
- Must integrate with existing ReviewIterator behavior
- Must not introduce new artifact types

---

## 5. Product Overview

### Value Proposition

A prompt template for IMPLEMENTATION_REVIEW that enforces task completion verification as a blocking pre-check before code quality review, with actionable rejection feedback listing exact incomplete tasks.

### Differentiators

- Early detection: Catches incomplete work at stage 10 instead of stage 13
- Actionable feedback: Lists exact `[ ]` items, not generic rejection
- Zero code changes: Pure prompt-based solution leveraging existing infrastructure

### Technical Stack

- **Language**: Prompt/Markdown (no code changes)
- **Integration**: stages.yaml configuration reference
- **Testing Approach**: Manual validation via workflow run

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|-------------|-------|----------|----------|------------|-------|
| FR-001 | Phase Completion Verification | Reviewer verifies all plan phases are marked `[x]` | G-001 | Reviewer | P0 | Plan file parsed, all phase checkboxes verified | Load from `.agent-tracking/plans/` |
| FR-002 | Task Completion Verification | Reviewer verifies all plan tasks are marked `[x]` | G-001 | Reviewer | P0 | All `[ ]` items detected and flagged | Must parse nested task lists |
| FR-003 | Changes Log Cross-Reference | Reviewer verifies changes log has entries for completed tasks | G-001 | Reviewer | P0 | Cross-reference plan tasks with changes log | Load from `.agent-tracking/changes/` |
| FR-004 | Incomplete Implementation Rejection | Incomplete implementation triggers REJECT with exact task list | G-002, G-003 | Builder, Reviewer | P0 | Rejection output includes phase/task/description | Format specified in prompt |
| FR-005 | Complete Implementation Approval | Complete implementation proceeds to code quality review | G-001 | Reviewer | P0 | Pre-check passes, code review begins | Only after all `[x]` verified |

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Process | Pre-check is blocking | No code review until tasks complete | P0 | Manual workflow test | Prompt instructions enforce order |
| NFR-002 | Usability | Rejection format is actionable | Includes exact `[ ]` items with descriptions | P0 | Review rejection output | Builders can act on feedback |
| NFR-003 | Compatibility | Integrates with ReviewIterator | Uses existing 4-iteration mechanism | P0 | Workflow test | No ReviewIterator changes needed |
| NFR-004 | Maintainability | Prompt follows SDD prompt conventions | Matches sdd.7 and sdd.8 format | P1 | Code review | Consistent with other prompts |

---

## 8. Acceptance Test Scenarios

### AT-001: Incomplete Implementation Rejected

**Description**: Reviewer detects incomplete tasks and rejects implementation with specific feedback

**Preconditions**:
- IMPLEMENTATION stage has completed
- Plan file exists in `.agent-tracking/plans/` with at least one `[ ]` item
- Workflow transitions to IMPLEMENTATION_REVIEW stage

**Steps**:
1. Orchestrator triggers IMPLEMENTATION_REVIEW stage
2. Reviewer agent loads plan file from `.agent-tracking/plans/`
3. Reviewer parses markdown checkboxes and finds `[ ]` items
4. Reviewer outputs REJECT with incomplete task list

**Expected Result**:
```
## IMPLEMENTATION_REVIEW: REJECTED
### Status: INCOMPLETE IMPLEMENTATION
### Incomplete Tasks
- [ ] Phase 2, Task 3: Add unit tests for validation logic
- [ ] Phase 2, Task 4: Update error handling
### Action Required
Complete the tasks listed above before code review can proceed.
### Iteration Status: 1/4
```

**Verification**: Builder agent receives specific task list and can resume work on exactly those items

---

### AT-002: Complete Implementation Approved for Code Review

**Description**: Reviewer verifies all tasks complete and proceeds to code quality review

**Preconditions**:
- IMPLEMENTATION stage has completed
- Plan file exists with all items marked `[x]`
- Changes log documents completed work

**Steps**:
1. Orchestrator triggers IMPLEMENTATION_REVIEW stage
2. Reviewer agent loads plan file and changes log
3. Reviewer verifies all checkboxes are `[x]`
4. Reviewer outputs TASK COMPLETION VERIFIED and proceeds to code review

**Expected Result**:
```
## IMPLEMENTATION_REVIEW: TASK COMPLETION VERIFIED ✅
### Pre-Review Checklist
- [x] All phases complete
- [x] All tasks complete
- [x] Changes log documents work
### Proceeding to Code Review
[Code quality review content follows...]
```

**Verification**: Workflow proceeds to code quality review phase within same stage

---

### AT-003: Iteration Loop After Rejection

**Description**: After rejection, builder fixes issues, and reviewer re-validates

**Preconditions**:
- First iteration rejected with incomplete tasks
- Builder has addressed the incomplete items
- Plan file now shows all `[x]`

**Steps**:
1. Builder marks previously incomplete tasks as `[x]`
2. ReviewIterator triggers second iteration
3. Reviewer re-parses plan file
4. Reviewer finds all tasks complete
5. Reviewer proceeds to code quality review

**Expected Result**: Second iteration approves task completion and proceeds to code review

**Verification**: Iteration count increments (2/4) and workflow progresses

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| ReviewIterator | Internal | High | Orchestrator | Low - existing functionality | Already proven with other review stages |
| Plan file format | Internal | High | PLAN stage | Low - established convention | Document expected format in prompt |
| Changes log format | Internal | Medium | IMPLEMENTATION stage | Low - established convention | Document expected format in prompt |
| stages.yaml | Internal | High | Config | Low - simple path update | Single line change |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Reviewer misparses plan checkbox format | Medium | Low | Document exact format in prompt with examples | Builder | Open |
| R-002 | False rejection on valid completion | Medium | Low | Include verification section in approval output | Reviewer | Open |
| R-003 | Prompt instructions unclear | Low | Medium | Follow existing sdd.7/sdd.8 format conventions | BA | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification

- Internal only - no external data exposure
- Plan files and changes logs contain task descriptions only

### PII Handling

- N/A - no personal information involved

### Threat Considerations

- N/A - prompt-only change with no security surface

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Copy prompt file to `.agent/commands/sdd/` | No restart required |
| Rollback | Delete prompt file, revert stages.yaml line 326 | Simple revert |
| Monitoring | N/A | Prompt-based, no instrumentation |
| Alerting | N/A | No runtime component |
| Support | Document new rejection format for users | Update workflow guide |
| Capacity Planning | N/A | No performance impact |

---

## 13. Rollout & Launch Plan

### Phases / Milestones

| Phase | Date | Gate Criteria | Owner |
|-------|------|---------------|-------|
| Phase 1: Create Prompt | Day 1 | Prompt file created with all sections | Builder |
| Phase 2: Update stages.yaml | Day 1 | Line 326 references new prompt | Builder |
| Phase 3: Validation | Day 1 | Tests pass, lint passes | Builder |

---

## 14. Implementation Tasks

### Phase 1: Create IMPLEMENTATION_REVIEW Prompt

- [ ] Create `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md`
- [ ] Include YAML frontmatter with description and tools
- [ ] Add Quick Reference table
- [ ] Add Pre-Code-Review Checklist section (BLOCKING)
- [ ] Add artifact loading instructions (plan + changes log)
- [ ] Add task completion verification logic
- [ ] Define decision logic (incomplete → REJECT, complete → proceed)
- [ ] Add rejection format template with incomplete task list
- [ ] Add approval format template
- [ ] Add code quality review section (after pre-check passes)

### Phase 2: Update stages.yaml

- [ ] Update line 326: `prompt_template: .agent/commands/sdd/sdd.7b-implementation-review.prompt.md`

### Phase 3: Validation

- [ ] Run existing tests (`uv run pytest`)
- [ ] Verify YAML validity
- [ ] Run linting (`uv run ruff check .` and `uv run ruff format --check .`)

---

## 15. Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md` | CREATE | New implementation review prompt |
| `stages.yaml` | MODIFY | Update line 326 with prompt path |

---

## 16. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| - | None | - | - | - |

---

## 17. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-03-02 | BA Agent | Initial specification with acceptance tests | Initial |

---

## 18. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Config | stages.yaml:313-327 | IMPLEMENTATION_REVIEW stage configuration | Source of truth |
| REF-002 | Prompt | sdd.7-task-implementer-for-feature.prompt.md | Implementation stage prompt (produces plan artifacts) | Reference for format |
| REF-003 | Prompt | sdd.8-post-implementation-review.prompt.md | Post-review stage prompt (late verification) | Reference for format |
| REF-004 | Spec | docs/feature-specs/implementation-review-completion-check.md | Original feature specification | Expanded in this document |

<!-- markdown-table-prettify-ignore-end -->
