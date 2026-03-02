# Problem Statement: Implementation Review Completion Check

## Business Problem

### Context

TeamBot orchestrates a 14-stage SDD (Spec-Driven Development) workflow where builder agents implement features according to an approved plan. The IMPLEMENTATION_REVIEW stage exists to review completed work before proceeding to testing, with up to 4 feedback iterations via ReviewIterator.

### Problem

**Incomplete implementations proceed through the workflow undetected.**

When builder agents fail to complete all planned tasks during the IMPLEMENTATION stage, the workflow currently has no mechanism to:
1. Detect that tasks remain incomplete
2. Reject the implementation with actionable feedback
3. Loop the builder back to finish the work

The IMPLEMENTATION_REVIEW stage has `is_review_stage: true` enabling iterations, but `prompt_template: null` means reviewers have no explicit instructions to verify task completion. Task completion verification only happens at POST_REVIEW (stage 13 of 14)—far too late in the workflow.

### Impact

| Impact Area | Description | Severity |
|-------------|-------------|----------|
| Workflow Integrity | Incomplete code progresses through TEST, ACCEPTANCE_TEST stages | High |
| Wasted Resources | Iterations spent on code quality review when tasks aren't complete | Medium |
| Builder Experience | No clear feedback on what's missing, leading to confusion | Medium |
| Quality Assurance | Defects from incomplete work discovered late in workflow | High |

---

## Goals

| Goal ID | Statement | Measurable Outcome |
|---------|-----------|-------------------|
| G-001 | IMPLEMENTATION_REVIEW verifies all plan tasks are complete before code review | Plan file parsed, all `[x]` items verified |
| G-002 | Incomplete implementations are rejected with actionable feedback | REJECT output lists exact `[ ]` items |
| G-003 | Feedback format enables builders to understand exactly what's missing | Rejection includes phase, task number, and description |

---

## Success Criteria

### Required Outcomes

- [ ] **SC-01**: IMPLEMENTATION_REVIEW stage has a prompt template that enforces task completion verification
- [ ] **SC-02**: Reviewer verifies all plan phases marked `[x]` before proceeding to code review
- [ ] **SC-03**: Reviewer verifies all plan tasks marked `[x]` before proceeding to code review
- [ ] **SC-04**: Incomplete implementations trigger REJECT with explicit list of uncompleted tasks
- [ ] **SC-05**: Complete implementations proceed to code quality review within the same stage
- [ ] **SC-06**: Integration with existing ReviewIterator (4 iteration maximum) is preserved

### Validation

- Existing test suite passes (`uv run pytest`)
- YAML syntax remains valid in stages.yaml
- Linting passes (`uv run ruff check .` and `uv run ruff format --check .`)

---

## Constraints

| Constraint | Rationale |
|------------|-----------|
| No changes to IMPLEMENTATION stage | Adding iteration to IMPLEMENTATION causes deadlock with prerequisite checks |
| No changes to ReviewIterator logic | Existing 4-iteration behavior is sufficient |
| No changes to POST_REVIEW stage | POST_REVIEW serves a different purpose (final validation) |
| Prompt-only solution | Solution is a new prompt template + stages.yaml reference |

---

## Stakeholders

| Role | Interest |
|------|----------|
| Builder Agents | Receive clear feedback on incomplete work |
| Reviewer Agent | Has explicit instructions for completion verification |
| Project Manager | Workflow proceeds only when implementation is truly complete |
| Users | Features are fully implemented before testing begins |

---

## References

- `stages.yaml` lines 313-327: IMPLEMENTATION_REVIEW configuration
- `docs/feature-specs/implementation-review-completion-check.md`: Detailed feature specification
- `sdd.7-task-implementer-for-feature.prompt.md`: IMPLEMENTATION stage prompt (artifacts produced)
- `sdd.8-post-implementation-review.prompt.md`: POST_REVIEW stage prompt (late verification)
