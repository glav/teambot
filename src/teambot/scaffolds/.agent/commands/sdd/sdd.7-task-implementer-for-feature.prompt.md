---
description: 'Required instructions for implementing task plans located in .agent-tracking/plans and .agent-tracking/details folders, with progressive tracking and change records - Brought to you by microsoft/edge-ai'
agent: agent
tools: ['search/usages', 'read/problems', 'web/fetch', 'web/githubRepo', 'execute/getTerminalOutput', 'execute/runInTerminal', 'read/terminalLastCommand', 'read/terminalSelection', 'edit/createFile', 'edit/createDirectory', 'edit/editFiles', 'search','microsoft-learn/*']
---
# Task Plan Implementation Instructions

## Quick Reference

| Item | Value |
|------|-------|
| **Purpose** | Execute implementation plan systematically with test implementation |
| **Input** | Approved plan + details + test strategy |
| **Output** | Working code + tests + `.agent-tracking/changes/{{date}}-{{name}}-changes.md` |
| **Key Actions** | Implement tasks, run tests, update tracking, mark complete |
| **Next Step** | `sdd.8-post-implementation-review.prompt.md` (when all phases complete) |

---

* Fulfill task plans instructions located in `.agent-tracking/plans/**` by applying the paired task plan details and research references.
* Progress is tracked in matching change logs located in `.agent-tracking/changes/**`.

### runSubagent Tool

Use the runSubagent tool:
* When needing to read the details or the research document for details on implementing a task or phase in the plan.
* When reading and reviewing the codebase for details to complete the task or phase.
* When needing to gather additional research from tools to complete the task with high quality.
* When additional tasks or Phases are identified or needed through runSubagent tool calls then update the task plan and details with additional phases and/or tasks.

Each runSubagent tool call should do the following:
* runSubagent tool calls should have a single responsibility.
* runSubagent tool calls must have a clear understanding of its purpose and response.
* runSubagent tool calls should always follow the conventions and standards of the codebase.
  * runSubagent tool calls could require indicating which instructions files to read and follow.
  * runSubagent tool calls could require indicating which files to use as examples or templates.
* When using runSubagent tool calls to gather details, make sure only the required details are returned to fulfill its purpose.
  * Make sure the runSubagent tool avoids summarizing details that must be known exactly.

## Scope and Purpose

* Guides the end-to-end process for turning plan checklists into committed code changes.
* Ensures change logs remain synchronized with plan progress and user-provided stop controls.

## Required Artifacts

* **Task Plan Instructions**: `.agent-tracking/plans/<date>-<description>-plan.instructions.md`
* **Task Plan Details**: `.agent-tracking/details/<date>-<description>-details.md`
* **Research References**: `.agent-tracking/research/<date>-<description>-research.md`
* **Test Strategy**: `.agent-tracking/test-strategies/<date>-<description>-test-strategy.md`
* **Changes Log**: `.agent-tracking/changes/<date>-<description>-changes.md`
* **Workspace Standards**: Reference the relevant guidance in `.agent/instructions/**` before editing code.

## Preparation Rules

* Note any `${input:taskStop:false}` or `${input:phaseStop:true}` values supplied with the plan.
* Review the plan header, overview, and checklist structure to understand task plan phases, tasks, and dependencies.
* Inspect the existing changes log to confirm current status before making edits.
* Do **not** read entire details or research files upfront. Use the line ranges provided in each task plan entry to load only the required segments with `read_file(offset=<start>, limit=<end-start+1>)`.

## Required Protocol

Follow these steps in order until all task plan phases and tasks are complete.

1. **Select the next task**
   * Locate the first unchecked `[ ] Phase` in the task plan instructions.
   * Within that phase, choose the earliest unchecked `[ ] Task`.
   * If every task is complete, move to the completion checks section below.

2. **Load task plan details by line range**
   * Use the `(Lines X-Y)` hint from the plan to read the matching slice from the task plan details file.
   * If the slice lacks necessary context, load additional targeted ranges rather than the entire file.

3. **Verify task plan dependencies**
   * Review the `Dependencies` list for the current task details.
   * If a dependency task was previously marked complete but its outputs are missing, uncheck that dependency in the task plan instructions, append required notes to its details section, and restart the protocol using the re-opened task.

4. **Review task plan research references and test strategy**
   * Use each `(Lines X-Y)` pointer in the task details’s `Research References` section to read only the specified segments from the research markdown file.
   * Expand the range only when the cited excerpt is insufficient to proceed.
   * Load test strategy document if task involves test implementation.
   * Verify testing approach (TDD vs Code-First) for current task.
   * Confirm coverage targets and test patterns to follow.

5. **Gather project context and implement the task**
   * Refer to the task detail’s `Files` section for expected touchpoints and update any additional files required to meet the task detail’s `Success` criteria.
   * Read additional workspace sources as needed to confirm conventions, variable definitions, or prior implementations.
   * Apply code or content changes that satisfy the task detail’s `Success` subsection.
   * Follow repository style guides, validation workflows, and dependency management practices.
   * **For test tasks**: Follow test strategy approach (TDD/Code-First), use researched test patterns, meet coverage targets.
   * Perform required tooling runs (lint, validate) and execute tests before marking tasks complete.

6. **Update tracking artifacts**
   * Append entries to the changes log under **Added**, **Modified**, or **Removed**, noting relative paths and concise summaries.
   * Record any deviations from the task plan details in the relevant section of the changes log and update the task plan details file with clarifying guidance when future work is required.
   * Mark the task as `[x]` in the task plan instructions once validation passes.

7. **Respect stop controls**
   * If `${input:taskStop}` is true, pause after marking the current task plan instructions complete and await user confirmation before selecting the next task.
   * When a phase’s tasks are all `[x]`, mark the phase as complete. If `${input:phaseStop}` is true or unspecified, pause before beginning the next phase; continue immediately only when `phaseStop=false`.

8. **When stopping due to stop controls**
   * Review all changes since previously stopping due to stop controls.
   * Provide the user in the conversation a commit message between a markdown codeblock by following the instructions from #file:./commit-message.instructions.md based on all changes since previously stopping.
   * Include any additional changes that were added from the user.
   * Do not include any changes or updates to files in `.agent-tracking` for the commit message.

9. **Repeat for remaining tasks**
   * Resume at Step 1 with the next unchecked task or phase from the task plan instructions.

## Implementation Standards

* Every implementation must produce self-sufficient, working code aligned with task details.
* Success validations must include verifiable outcomes, commands, or validation steps aligned with repository tooling from `package.json` for `npm run` when available.
* Implementation must follow exact file paths, schemas, and instruction documents cited in the task details and research references.
* Changes log must stay synchronized with task progress; update the changes file after every task completion.
* **Test implementation is REQUIRED**: Create tests as specified in task details following test strategy approach.
* Tests must be executed and passing before marking implementation tasks complete.
* Follow test patterns from research and meet coverage targets from test strategy.

### Code Quality

* Mirror existing patterns for architecture, data flow, and naming found in the current repository.
* Keep code self-contained, avoiding partial implementations that leave completed tasks in an indeterminate state.
* Run required validation commands (linters, validation, only run tests if specified or implementing tests) relevant to the artifacts you touched.
* Document complex logic with concise comments only when necessary for maintainers.

### Test Implementation Requirements (UPDATED)

**CRITICAL CHANGE**: Test implementation is now REQUIRED for code-related tasks following test strategy.

You MUST:
* Implement tests when specified in task details (which should include tests based on test strategy)
* Follow test strategy approach per component (TDD vs Code-First from test strategy document)
* Use existing test frameworks identified in research
* Follow test patterns documented in research
* Meet coverage targets specified in test strategy
* Execute tests and validate they pass before marking tasks complete

**Test Task Identification**:
* Task details will explicitly include test implementation tasks
* Test strategy document path will be referenced in plan
* Testing approach (TDD/Code-First) will be specified per task
* Coverage targets will be provided

**When Test Infrastructure is Missing**:
* If test framework setup is needed, it should be in task details as a dedicated task
* If test infrastructure is missing and not in plan, escalate to user
* Do NOT skip tests because infrastructure is missing

### Explicit Implementation Constraints

Avoid implementing the following unless explicitly specified in the task details:
* Never create one-off or non-standard scripts for functionality around validation, examples, non-standard building, or deployments.
* Never create scripts or tests into non-standard locations in the codebase (follow patterns from research).
* Never create one-off or non-standard markdown documents.
* Never implement backwards compatibility or workarounds for potentially breaking changes. Breaking changes are always allowed.
* Never add one-off or non-standard documentation or comments into code files.
* Never update auto-generated README.md files in framework directories (e.g., `{component}/{framework}/README.md`). Use `npm run` instead.

## Completion Checks

Implementation work is entirely complete when:

* Every task plan phase and task is marked `[x]` in the task plan instructions with aligned change log updates.
* All referenced files compile, lint, and if specified or implementing tests then test successfully.
* The changes log includes a Release Summary only after the final phase is complete.
* Outstanding follow-ups are noted in the task details file for future task plans.

## Changes Log Expectations

* Keep the changes file chronological. Add new summaries just beneath the relevant **Added**, **Modified**, or **Removed** heading after each task plan task.
* Capture links to supporting research excerpts when they inform implementation decisions.

## Changes File Template

Use this template when creating or refreshing a change log. Replace `{{ }}` placeholders accordingly and save under `.agent-tracking/changes/` using the naming pattern `YYYYMMDD-task-description-changes.md`.

**IMPORTANT**: Update the log after every task plan task completion by appending to the **Added**, **Modified**, or **Removed** sections.
**MANDATORY**: Begin every changes file with `<!-- markdownlint-disable-file -->`.

<!-- <changes-template> -->
```markdown
<!-- markdownlint-disable-file -->
# Release Changes: {{task name}}

**Related Plan**: {{plan-file-name}}
**Implementation Date**: {{YYYY-MM-DD}}

## Summary

{{Brief description of the overall changes made for this release}}

## Changes

### Added

* {{relative-file-path}} - {{one sentence summary of what was implemented}}

### Modified

* {{relative-file-path}} - {{one sentence summary of what was changed}}

### Removed

* {{relative-file-path}} - {{one sentence summary of what was removed}}

## Release Summary

**Total Files Affected**: {{number}}

### Files Created ({{count}})

* {{file-path}} - {{purpose}}

### Files Modified ({{count}})

* {{file-path}} - {{changes-made}}

### Files Removed ({{count}})

* {{file-path}} - {{reason}}

### Dependencies & Infrastructure

* **New Dependencies**: {{list-of-new-dependencies}}
* **Updated Dependencies**: {{list-of-updated-dependencies}}
* **Infrastructure Changes**: {{infrastructure-updates}}
* **Configuration Updates**: {{configuration-changes}}

### Deployment Notes

{{Any specific deployment considerations or steps}}
```
<!-- </changes-template> -->

## Output Validation Checklist (MANDATORY)

After completing each task:

- [ ] **Code Implemented**: All code changes match task details specifications
- [ ] **Tests Written**: Test tasks completed per test strategy (TDD/Code-First)
- [ ] **Tests Passing**: All tests execute successfully
- [ ] **Coverage Met**: Coverage targets from test strategy achieved
- [ ] **Changes Log Updated**: `.agent-tracking/changes/{{date}}-{{name}}-changes.md` reflects task
- [ ] **Plan Updated**: Task marked `[x]` in plan file
- [ ] **Linting Passed**: Code passes project linters

After completing ALL phases:

- [ ] **All Tasks Complete**: Every task in plan marked `[x]`
- [ ] **All Tests Pass**: Full test suite passes
- [ ] **Coverage Validated**: Overall coverage meets targets
- [ ] **Release Summary Added**: Changes log has Release Summary section
- [ ] **No Orphan Changes**: All file changes documented in changes log

**Validation Command**: After each task, explicitly state:
```
TASK_VALIDATION: PASS | FAIL
- Task: {{task_id}}
- Code: IMPLEMENTED | INCOMPLETE
- Tests: WRITTEN | N/A | MISSING
- Tests Pass: YES | NO | N/A
- Changes Log: UPDATED | NOT_UPDATED
- Plan Marked: YES | NO
```

**Phase Completion Command**: After each phase:
```
PHASE_VALIDATION: PASS | FAIL
- Phase: {{phase_number}}
- Tasks Complete: X/Y
- Tests Passing: X/Y
- Coverage: X% (target: Y%)
- Ready for Next Phase: YES | NO
```

## Implementation Completion Handoff

When ALL phases complete:

```markdown
## ✅ Implementation Complete: {{feature_name}}

All implementation tasks have been completed.

**📄 Artifacts:**
* Changes Log: `.agent-tracking/changes/{{date}}-{{name}}-changes.md`
* Plan (completed): `.agent-tracking/plans/{{date}}-{{name}}-plan.instructions.md`

**📊 Summary:**
* Total Tasks: {{X}} completed
* Files Created: {{Y}}
* Files Modified: {{Z}}
* Tests Written: {{N}}
* Test Coverage: {{X}}%

**✅ Quality Checks:**
* All tests passing: ✅
* Coverage targets met: ✅
* Linting passed: ✅

**➡️ Recommended Next Step:**
Run **Step 8** (`sdd.8-post-implementation-review.prompt.md`) for final validation and cleanup.
```