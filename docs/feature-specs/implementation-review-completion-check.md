# Implementation Review Completion Check - Feature Specification

Version 1.0 | Status: Draft | Priority: P1 | Parent: stages.yaml

---

## 1. Executive Summary

### Context

The TeamBot SDD workflow includes an IMPLEMENTATION_REVIEW stage with `is_review_stage: true`, enabling up to 4 iterations via ReviewIterator. However, this stage currently has `prompt_template: null`, meaning there are no explicit instructions for reviewers to verify task completion before reviewing code quality.

### Problem Statement

When builder agents don't complete all implementation tasks, the workflow has no mechanism to detect incomplete work and loop back. The IMPLEMENTATION stage has no iteration capability, and adding one would cause deadlock with prerequisite checks. The existing IMPLEMENTATION_REVIEW stage should serve as the driver for ensuring completion, but lacks explicit instructions.

### Goals

| Goal ID | Statement | Priority |
|---------|-----------|----------|
| G-001 | IMPLEMENTATION_REVIEW verifies all plan tasks are complete before code review | P0 |
| G-002 | Incomplete implementations are rejected with actionable feedback | P0 |
| G-003 | Feedback format enables builders to understand exactly what's missing | P1 |

---

## 2. Problem Definition

### Current Behavior

- `IMPLEMENTATION_REVIEW` stage has `prompt_template: null` (stages.yaml:326)
- Reviewers have no explicit instructions to check task completion
- Task completion verification only happens at POST_REVIEW stage (sdd.8)
- Incomplete implementations may pass IMPLEMENTATION_REVIEW without detection

### Root Cause

The IMPLEMENTATION_REVIEW stage was designed to support iteration (`is_review_stage: true` with 4 iterations) but was never given a prompt template with explicit verification instructions.

### Impact

- Incomplete implementations proceed to later stages
- Wasted iterations on code review when tasks aren't even complete
- Builders don't receive clear feedback on what's missing
- Workflow integrity compromised

---

## 3. Requirements

### Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-001 | Reviewer verifies all plan phases marked `[x]` | P0 | Plan file parsed, unchecked items detected |
| FR-002 | Reviewer verifies all plan tasks marked `[x]` | P0 | All `[ ]` items flagged as incomplete |
| FR-003 | Reviewer verifies changes log has entries for completed tasks | P0 | Cross-reference plan tasks with changes log |
| FR-004 | Incomplete implementation triggers REJECT with task list | P0 | Rejection includes exact list of `[ ]` items |
| FR-005 | Complete implementation proceeds to code quality review | P0 | Only after pre-check passes |

### Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-001 | Pre-check is blocking - no code review until tasks complete | P0 |
| NFR-002 | Rejection format is actionable and specific | P0 |
| NFR-003 | Integrates with existing ReviewIterator (4 iterations) | P0 |

---

## 4. Scope

### In Scope

- Create new prompt file `sdd.7b-implementation-review.prompt.md`
- Define pre-code-review checklist (blocking)
- Define rejection format with incomplete task list
- Define approval flow proceeding to code review
- Update `stages.yaml` to reference new prompt

### Out of Scope

- Changes to IMPLEMENTATION stage workflow
- Changes to ReviewIterator logic
- Changes to POST_REVIEW stage
- New completion signal artifacts

---

## 5. Implementation Tasks

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

## 6. Prompt Content Specification

### Required Sections

1. **YAML Frontmatter**
   - description: "Implementation review - verifies task completion before code review"
   - agent: agent
   - tools: ['read/readFile', 'search', 'edit/editFiles']

2. **Quick Reference Table**
   - Purpose: Verify implementation completeness before code review
   - Input: Plan + Changes Log from IMPLEMENTATION stage
   - Output: APPROVED or REJECTED
   - Key Check: All plan tasks marked `[x]`

3. **Pre-Code-Review Checklist (BLOCKING)**
   - Load plan file from `.agent-tracking/plans/`
   - Load changes log from `.agent-tracking/changes/`
   - Verify all phases marked `[x]`
   - Verify all tasks marked `[x]`
   - Verify changes log has entries for tasks
   - Decision: If ANY `[ ]` → REJECT; If ALL `[x]` → proceed

4. **Rejection Format**
   ```
   ## IMPLEMENTATION_REVIEW: REJECTED
   ### Status: INCOMPLETE IMPLEMENTATION
   ### Incomplete Tasks
   - [ ] Phase N, Task X: Description
   ### Missing Artifacts (if any)
   ### Action Required
   ### Iteration Status: X/4
   ```

5. **Approval Format**
   ```
   ## IMPLEMENTATION_REVIEW: TASK COMPLETION VERIFIED ✅
   ### Pre-Review Checklist (all checked)
   ### Proceeding to Code Review
   ```

6. **Code Quality Review**
   - Implementation correctness
   - Test coverage
   - Code quality
   - Final decision

---

## 7. Acceptance Criteria

- [ ] Prompt file `sdd.7b-implementation-review.prompt.md` exists in `.agent/commands/sdd/`
- [ ] Prompt includes YAML frontmatter
- [ ] Prompt includes blocking pre-code-review checklist
- [ ] Prompt includes rejection format with incomplete task list
- [ ] Prompt includes approval format proceeding to code review
- [ ] `stages.yaml` line 326 references new prompt path
- [ ] All existing tests pass
- [ ] Linting passes

---

## 8. Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md` | CREATE | New implementation review prompt |
| `stages.yaml` | MODIFY | Update line 326 with prompt path |

---

## 9. Changelog

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0 | 2026-03-02 | PM Agent | Initial specification based on reviewer feedback |

---

## 10. References

- Reviewer analysis of implementation non-completion issue
- `stages.yaml` IMPLEMENTATION_REVIEW configuration (lines 320-327)
- `sdd.7-task-implementer-for-feature.prompt.md` (implementation stage prompt)
- `sdd.8-post-implementation-review.prompt.md` (post-review verification)
