
<!-- <plan-template> -->
<!-- markdownlint-disable-file -->
# Task Checklist: {{task_name}}

## Overview

{{task_overview_sentence}}

Follow all instructions from #file:{{relative_path}}/.github/instructions/task-implementation.instructions.md

## Objectives

* {{specific_goal_1}}
* {{specific_goal_2}}

## Research Summary

### Project Files
* {{file_path}} - {{file_relevance_description}}

### External References
* .agent-tracking/research/{{research_file_name}} - {{research_description}}
* "{{org_repo}} {{search_terms}}" - {{implementation_patterns_description}}
* {{documentation_url}} - {{documentation_description}}

### Standards References
* #file:{{relative_path}}/.github/instructions/{{language}}.instructions.md - {{language_conventions_description}}
* #file:{{relative_path}}/.github/instructions/{{instruction_file}}.instructions.md - {{instruction_description}}

## Implementation Checklist

### [ ] Phase 1: {{phase_1_name}}

**Phase Objective**: {{measurable_outcome_for_this_phase}}

#### Sub-phase 1.A: {{sub_phase_name}} (optional grouping for complex phases)

* [ ] Task 1.A.1: {{specific_atomic_action}}
  * Details: .agent-tracking/details/{{date}}-{{task_description}}-details.md (Lines {{line_start}}-{{line_end}})
  * Dependencies: {{prerequisites_or_none}}
  * Priority: {{CRITICAL | HIGH | MEDIUM}}

* [ ] Task 1.A.2: {{specific_atomic_action}}
  * Details: .agent-tracking/details/{{date}}-{{task_description}}-details.md (Lines {{line_start}}-{{line_end}})
  * Dependencies: Task 1.A.1

### [ ] Phase 2: {{phase_2_name}}

**Phase Objective**: {{measurable_outcome_for_this_phase}}

* [ ] Task 2.1: {{specific_action_2_1}}
  * Details: .agent-tracking/details/{{date}}-{{task_description}}-details.md (Lines {{line_start}}-{{line_end}})
  * Dependencies: Phase 1 completion

### [ ] Phase X: Test Implementation (REQUIRED for code features - adjust timing per test strategy)

**Test Strategy**: {{TDD | Code-First | Hybrid}} - See .agent-tracking/test-strategies/{{date}}-{{task_description}}-test-strategy.md

#### For TDD: This phase comes BEFORE implementation phases
#### For Code-First: This phase comes AFTER implementation phases

* [ ] Task X.1: Create/Update tests for {{component_name}}
  * Details: .agent-tracking/details/{{date}}-{{task_description}}-details.md (Lines {{line_start}}-{{line_end}})
  * Test Approach: {{TDD | Code-First}} (per test strategy)
  * Coverage Target: {{X}}% (per test strategy)
  * Test Framework: {{framework_from_research}}
  * Dependencies: {{test_infrastructure_or_implementation}}

* [ ] Task X.2: Validate test coverage and quality
  * Details: .agent-tracking/details/{{date}}-{{task_description}}-details.md (Lines {{line_start}}-{{line_end}})
  * Success: Coverage meets {{X}}% target, all tests pass
  * Dependencies: Task X.1

## Dependencies

* {{required_tool_framework_1}}
* {{required_tool_framework_2}}

## Success Criteria

* {{overall_completion_indicator_1}}
* {{overall_completion_indicator_2}}
```
<!-- </plan-template> -->

### Details Template

<!-- <details-template> -->
```markdown
<!-- markdownlint-disable-file -->
# Task Details: {{task_name}}

## Research Reference

**Source Research**: .agent-tracking/research/{{date}}-{{task_description}}-research.md

## Phase 1: {{phase_1_name}}

### Task 1.1: {{specific_action_1_1}}

{{specific_action_description}}

* **Files**:
  * {{file_1_path}} - {{file_1_description}}
  * {{file_2_path}} - {{file_2_description}}
* **Success**:
  * {{completion_criteria_1}}
  * {{completion_criteria_2}}
* **Research References**:
  * .agent-tracking/research/{{date}}-{{task_description}}-research.md (Lines {{research_line_start}}-{{research_line_end}}) - {{research_section_description}}
  * #githubRepo:"{{org_repo}} {{search_terms}}" - {{implementation_patterns_description}}
* **Dependencies**:
  * {{previous_task_requirement}}
  * {{external_dependency}}

### Task 1.2: {{specific_action_1_2}}

{{specific_action_description}}

* **Files**:
  * {{file_path}} - {{file_description}}
* **Success**:
  * {{completion_criteria}}
* **Research References**:
  * .agent-tracking/research/{{date}}-{{task_description}}-research.md (Lines {{research_line_start}}-{{research_line_end}}) - {{research_section_description}}
* **Dependencies**:
  * Task 1.1 completion

## Phase 2: {{phase_2_name}}

### Task 2.1: {{specific_action_2_1}}

{{specific_action_description}}

* **Files**:
  * {{file_path}} - {{file_description}}
* **Success**:
  * {{completion_criteria}}
* **Research References**:
  * .agent-tracking/research/{{date}}-{{task_description}}-research.md (Lines {{research_line_start}}-{{research_line_end}}) - {{research_section_description}}
  * #githubRepo:"{{org_repo}} {{search_terms}}" - {{patterns_description}}
* **Dependencies**:
  * Phase 1 completion

## Dependencies

* {{required_tool_framework_1}}

## Success Criteria

* {{overall_completion_indicator_1}}
```
<!-- </details-template> -->

### Implementation Prompt Template

<!-- <implementation-prompt-template> -->
````markdown
<!-- markdownlint-disable-file -->
# Implementation Prompt: {{task_name}}

## Implementation Instructions

### Step 1: Create Changes Tracking File

You WILL create `{{date}}-{{task_description}}-changes.md` in `.agent-tracking/changes/` if it does not exist.

### Step 2: Execute Implementation

You WILL follow #file:{{relative_path}}/.github/instructions/task-implementation.instructions.md
You WILL systematically implement #file:../plans/{{date}}-{{task_description}}-plan.instructions.md task-by-task
You WILL follow ALL project standards and conventions

**CRITICAL**: If ${input:phaseStop:true} is true, you WILL stop after each Phase for user review.
**CRITICAL**: If ${input:taskStop:false} is true, you WILL stop after each Task for user review.

### Step 3: Cleanup

When ALL Phases are checked off (`[x]`) and completed you WILL do the following:
  1. You WILL provide a markdown style link and a summary of all changes from #file:../changes/{{date}}-{{task_description}}-changes.md to the user:
    * You WILL keep the overall summary brief
    * You WILL add spacing around any lists
    * You MUST wrap any reference to a file in a markdown style link
  2. You WILL provide markdown style links to .agent-tracking/plans/{{date}}-{{task_description}}-plan.instructions.md, .agent-tracking/details/{{date}}-{{task_description}}-details.md, and .agent-tracking/research/{{date}}-{{task_description}}-research.md documents. You WILL recommend cleaning these files up as well.
  3. **MANDATORY**: You WILL attempt to delete .agent-tracking/prompts/{{implement_task_description}}.prompt.md

## Success Criteria

* [ ] Changes tracking file created
* [ ] All plan items implemented with working code
* [ ] All detailed specifications satisfied
* [ ] Project conventions followed
* [ ] Changes file updated continuously
<!-- </implementation-prompt-template> -->
