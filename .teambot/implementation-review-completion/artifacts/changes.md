<!-- markdownlint-disable-file -->
# Release Changes: Implementation Review Completion Check

**Related Plan**: Feature Spec Section 5 (docs/feature-specs/implementation-review-completion-check.md)
**Implementation Date**: 2026-03-02

## Summary

Created IMPLEMENTATION_REVIEW prompt template that enforces task completion verification before code quality review. The prompt implements a two-phase review process: (1) blocking pre-check that verifies all plan tasks are marked `[x]` complete, and (2) code quality review that only proceeds after pre-check passes.

## Changes

### Added

* `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md` - New implementation review prompt with:
  - YAML frontmatter (description, agent, tools)
  - Quick Reference table
  - Pre-Code-Review Checklist section (BLOCKING)
  - Task completion verification logic for `[ ]` and `[x]` markers
  - Rejection format template with incomplete task list
  - Approval format template transitioning to code review
  - Code quality review section (Phase 2 after pre-check)
  - Output validation checklist

### Modified

* `stages.yaml` - Updated IMPLEMENTATION_REVIEW stage (line 326):
  - Changed `prompt_template: null` to `prompt_template: .agent/commands/sdd/sdd.7b-implementation-review.prompt.md`

### Removed

None

## Release Summary

**Total Files Affected**: 2

### Files Created (1)

* `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md` - Implementation review prompt with task completion verification

### Files Modified (1)

* `stages.yaml` - Added prompt_template reference for IMPLEMENTATION_REVIEW stage

### Files Removed (0)

None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: IMPLEMENTATION_REVIEW stage now has explicit prompt template

### Deployment Notes

No special deployment considerations. The change is backward-compatible:
- Existing ReviewIterator handles the review iteration logic
- The new prompt provides explicit instructions for task completion verification
- All existing tests continue to pass
