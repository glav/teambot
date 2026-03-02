<!-- markdownlint-disable-file -->
# Task Research Documents: Implementation Review Completion Check

This research document provides comprehensive analysis for implementing the IMPLEMENTATION_REVIEW prompt template (`sdd.7b-implementation-review.prompt.md`) that verifies task completion before code review. The feature addresses a gap where incomplete implementations can pass IMPLEMENTATION_REVIEW without detection because the stage has `prompt_template: null`.

## Task Implementation Requests

* **Task 1**: Create `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md` - New implementation review prompt with YAML frontmatter, pre-code-review checklist (blocking), task completion verification, and rejection/approval formats
* **Task 2**: Update `stages.yaml` line 326 to reference the new prompt: `prompt_template: .agent/commands/sdd/sdd.7b-implementation-review.prompt.md`
* **Task 3**: Run existing tests (`uv run pytest`) to verify no regressions
* **Task 4**: Run linting (`uv run ruff check .` and `uv run ruff format --check .`)

## Scope and Success Criteria

* **Scope**: Create a new prompt file for IMPLEMENTATION_REVIEW stage that enforces task completion verification before code review; update stages.yaml to reference it
* **Out of Scope**: Changes to IMPLEMENTATION stage workflow, ReviewIterator logic, POST_REVIEW stage, or new completion signal artifacts
* **Assumptions**:
  1. Existing ReviewIterator handles iteration logic (up to 4 iterations) - no changes needed
  2. Plan files follow the established `.agent-tracking/plans/` format with `[ ]` and `[x]` task markers
  3. Changes logs exist in `.agent-tracking/changes/` with structured sections
  4. The prompt file is the only mechanism for guiding reviewer behavior
* **Success Criteria**:
  * Prompt file `sdd.7b-implementation-review.prompt.md` exists in `.agent/commands/sdd/`
  * Prompt includes YAML frontmatter with description, agent, and tools
  * Prompt includes blocking pre-code-review checklist
  * Prompt includes rejection format with incomplete task list
  * Prompt includes approval format proceeding to code review
  * `stages.yaml` line 326 references new prompt path
  * All existing tests pass (1800+ tests)
  * Linting passes

## Outline

1. Entry Point Analysis - How IMPLEMENTATION_REVIEW is triggered and executed
2. Testing Infrastructure Research - Test framework, patterns, coverage
3. Research Executed - File analysis, code patterns, external research
4. Key Discoveries - Project structure, implementation patterns, examples
5. Technical Scenarios - Prompt structure and content requirements
6. Potential Next Research - Any remaining questions

### Potential Next Research

* **None identified** - Research is complete for the defined scope
  * **Reasoning**: The feature is a documentation/prompt file change with a single config update; no complex code paths to analyze
  * **Reference**: Feature spec defines the scope as prompt file creation + config update only

## Research Executed

### Testing Infrastructure Research

* **Framework**: pytest 7.4.0+ with pytest-asyncio
  * Location: `tests/` directory with subdirectories mirroring `src/teambot/`
  * Naming: `test_*.py` pattern, `Test*` classes, `test_*` functions
  * Runner: `uv run pytest` (default excludes acceptance tests with `-m 'not acceptance'`)
  * Coverage: pytest-cov with 80-85% target, `--cov=src/teambot --cov-report=term-missing`

### Test Patterns Found

* **File**: `tests/test_orchestration/test_review_iterator.py` (Lines 1-366)
  * Uses `pytest.fixture` for creating mock SDK clients and iterators
  * Mock SDK responses with `side_effect` for multi-iteration scenarios
  * Tests approval/rejection patterns: `VERIFIED_APPROVED:`, `REJECTED:`
  * Tests iteration counts, feedback incorporation, cancellation handling
  * Tests failure report generation to `.teambot/failures/`

* **File**: `tests/test_workflow/test_stages.py` (Lines 1-209)
  * Tests stage enum completeness and ordering
  * Tests metadata registry and stage transitions
  * Tests persona allowances and skippability
  * Tests parallel stage groups and convergence

* **File**: `tests/conftest.py` (Lines 1-185)
  * Shared fixtures: `temp_teambot_dir`, `sample_agent_config`, `sample_objective`
  * Mock SDK fixtures: `MockSDKResponse`, `mock_sdk_session`, `mock_sdk_client`
  * Streaming fixtures: `MockStreamingSession`, `MockEventTypes`, `MockEventData`

### Coverage Standards

* **Unit Tests**: 80-85% minimum (per pyproject.toml)
* **Integration Tests**: Covered by test files like `test_orchestration/*.py`
* **Critical Paths**: Review iteration logic tested comprehensively (test_review_iterator.py)
* **Note**: For prompt file changes, testing is validation-focused (YAML validity, existing tests pass)

### Testing Approach Recommendation

* **Prompt File (sdd.7b)**: Code-First - This is a markdown file, not code. Validation is YAML syntax checking.
* **stages.yaml Update**: Code-First - Single line change, validated by existing tests that parse stages.yaml.

**Rationale**: The implementation consists of creating a prompt file (documentation) and a config update (single line YAML change). TDD is not appropriate for documentation files. Validation comes from existing test infrastructure that parses stages.yaml.

### File Analysis

* **`stages.yaml` (Lines 313-327)** - IMPLEMENTATION_REVIEW stage configuration:
  ```yaml
  IMPLEMENTATION_REVIEW:
    name: Implementation Review
    description: Review implemented changes for quality, correctness, and adherence to spec
    work_agent: builder-1
    review_agent: reviewer
    allowed_personas:
      - reviewer
    artifacts:
      - impl_review.md
    exit_criteria:
      - Implementation approved or revision feedback provided
    optional: false
    is_review_stage: true
    prompt_template: null  # ← Line 326 - CURRENTLY NULL, needs to be updated
    include_objective: true
  ```

* **`.agent/commands/sdd/sdd.7-task-implementer-for-feature.prompt.md` (Lines 1-305)** - Implementation stage prompt pattern:
  * YAML frontmatter with description, agent, tools
  * Quick Reference table
  * Required Artifacts section
  * Implementation protocol with phases
  * Output Validation Checklist with explicit validation commands
  * Handoff message template

* **`.agent/commands/sdd/sdd.6-review-plan.prompt.md` (Lines 1-594)** - Plan review prompt pattern:
  * Strict review requirements with checklists
  * Validation sections (structural, content, alignment)
  * Issue categorization (Critical/Important/Minor)
  * Explicit approval protocol with user sign-off
  * Output Validation Checklist with validation commands

* **`.agent/commands/sdd/sdd.8-post-implementation-review.prompt.md` (Lines 1-410)** - Post-review prompt pattern:
  * Acceptance test execution (CRITICAL section)
  * Validation checklists with test/coverage/lint checks
  * Approval criteria based on test results
  * Final review report template

* **Plan file format** (`20260225-critical-failure-handling-plan.instructions.md`):
  * YAML frontmatter with `applyTo` for changes file
  * `<!-- markdownlint-disable-file -->` header
  * Overview, Objectives, Research Summary sections
  * Implementation Checklist with `### [x] Phase N:` and `* [x] Task N.M:` format
  * Phase Gates with explicit completion criteria

* **Changes file format** (`20260225-critical-failure-handling-changes.md`):
  * `<!-- markdownlint-disable-file -->` header
  * Related Plan reference
  * Summary section
  * Added/Modified/Removed sections
  * Release Summary with file counts

### Code Search Results

* `ReviewIterator` class location: `src/teambot/orchestration/review_iterator.py:48`
* Approval markers parsed: `VERIFIED_APPROVED:` and `REJECTED:` (Lines 326-343)
* Review stages use `is_review_stage: true` flag triggering ReviewIterator (stages.yaml:325)
* 4 maximum iterations enforced by `MAX_ITERATIONS = 4` (review_iterator.py:51)

### External Research (Evidence Log)

* **No external research required** - All patterns discovered within existing codebase
  * Plan and changes file formats documented in SDD prompts
  * Prompt structure patterns established by existing `.agent/commands/sdd/*.prompt.md` files
  * ReviewIterator behavior documented in test files and implementation

### Project Conventions

* **Standards referenced**:
  * AGENTS.md - Clean commit requirements (`uv run ruff format -- . && uv run ruff check . --fix`)
  * All `.agent-tracking/**` files use `<!-- markdownlint-disable-file -->` header
  * Prompt files follow strict YAML frontmatter format
* **Instructions followed**:
  * SDD prompt template patterns from existing files
  * Review stage patterns from sdd.6-review-plan.prompt.md

## Key Discoveries

### Project Structure

* **SDD Prompts Location**: `.agent/commands/sdd/`
* **Naming Convention**: `sdd.{N}-{step-name}.prompt.md` where N is step number
* **The feature requires**: `sdd.7b-implementation-review.prompt.md` (between step 7 and 8)
* **Stage Configuration**: `stages.yaml` in repository root
* **Artifact Locations**:
  * Plans: `.agent-tracking/plans/YYYYMMDD-{name}-plan.instructions.md`
  * Changes: `.agent-tracking/changes/YYYYMMDD-{name}-changes.md`
  * Reviews: `.agent-tracking/implementation-reviews/` (for output)

### Implementation Patterns

* **Review Stage Prompts** include:
  1. YAML frontmatter with description, agent (always `agent`), and tools list
  2. Quick Reference table with Purpose, Input, Output, Decision outcomes
  3. Core Mission / Core Principles section
  4. Detailed validation process with checklists
  5. Issue categorization (Critical/Important/Minor)
  6. Explicit approval/rejection format templates
  7. Output Validation Checklist (MANDATORY section)
  8. User Interaction Protocol

* **Approval Detection**:
  * ReviewIterator parses `VERIFIED_APPROVED:` for approval
  * Rejection is anything else or `REJECTED:`
  * Evidence verification is required for approval

* **Task Completion Markers**:
  * Unchecked: `[ ]` or `- [ ]`
  * Checked: `[x]` or `- [x]`
  * Case-insensitive matching recommended

### Complete Examples

#### YAML Frontmatter Pattern (from sdd.6-review-plan.prompt.md)
```yaml
---
description: "Implementation plan review and validation before execution phase"
agent: agent
tools: ['edit/createFile', 'edit/createDirectory', 'edit/editFiles', 'search', 'read/readFile']
---
```

#### Quick Reference Table Pattern
```markdown
## Quick Reference

| Item | Value |
|------|-------|
| **Purpose** | Validate plan quality and implementation readiness |
| **Input** | Plan + Details + Research + Test Strategy files |
| **Output** | `.agent-tracking/plan-reviews/YYYYMMDD-{{name}}-plan-review.md` |
| **Decision** | APPROVED / NEEDS_REVISION / BLOCKED |
| **If Approved** | `sdd.7-task-implementer-for-feature.prompt.md` |
| **If Revision Needed** | Return to `sdd.5-task-planner-for-feature.prompt.md` |
```

#### Rejection Format Pattern (adapted from spec)
```markdown
## IMPLEMENTATION_REVIEW: REJECTED
### Status: INCOMPLETE IMPLEMENTATION
### Incomplete Tasks
- [ ] Phase N, Task X: Description
- [ ] Phase M, Task Y: Description
### Missing Artifacts (if any)
- Changes log not found
### Action Required
Please complete the listed tasks and update the changes log before requesting review.
### Iteration Status: X/4
```

#### Approval Format Pattern (adapted from spec)
```markdown
## IMPLEMENTATION_REVIEW: TASK COMPLETION VERIFIED ✅
### Pre-Review Checklist (all checked)
- [x] All phases marked complete in plan
- [x] All tasks marked complete in plan
- [x] Changes log has entries for completed tasks
### Proceeding to Code Review
[Code review section follows]
```

### API and Schema Documentation

* **ReviewIterator.execute()** (review_iterator.py:137-208):
  * Takes: stage, work_agent, review_agent, context, on_progress callback
  * Returns: ReviewResult with status, iterations_used, final_output, summary
  * Parses `VERIFIED_APPROVED:` for approval, anything else is rejection

* **stages.yaml schema fields** (stages.yaml:13-31):
  * `prompt_template` - Path to SDD prompt file (relative to repo root)
  * `is_review_stage` - Triggers ReviewIterator (4 iterations max)
  * `work_agent` - Agent that addresses feedback
  * `review_agent` - Agent that approves/rejects

### Configuration Examples

#### stages.yaml update (Line 326)
```yaml
# Before
prompt_template: null  # Uses general review approach

# After
prompt_template: .agent/commands/sdd/sdd.7b-implementation-review.prompt.md
```

## Technical Scenarios

### 1. Implementation Review Prompt Structure

Create a new prompt file that enforces task completion verification before allowing code quality review.

**Requirements:**
* YAML frontmatter with standard SDD prompt format
* Pre-code-review checklist that is BLOCKING
* Task completion verification logic
* Clear rejection format with incomplete task list
* Clear approval format proceeding to code review
* Code quality review section (after pre-check passes)
* Output validation checklist

**Preferred Approach:**
Create `sdd.7b-implementation-review.prompt.md` following the established pattern from `sdd.6-review-plan.prompt.md` and `sdd.8-post-implementation-review.prompt.md`, with specialized logic for:
1. Loading and parsing plan files to detect `[ ]` unchecked items
2. Loading and validating changes log entries
3. Blocking code review if ANY task is incomplete
4. Providing actionable rejection feedback with exact incomplete task list

```text
.agent/commands/sdd/
├── sdd.7-task-implementer-for-feature.prompt.md  # IMPLEMENTATION stage
├── sdd.7b-implementation-review.prompt.md         # NEW - IMPLEMENTATION_REVIEW stage
└── sdd.8-post-implementation-review.prompt.md    # POST_REVIEW stage
```

```mermaid
graph TD
    subgraph IMPLEMENTATION_REVIEW["IMPLEMENTATION_REVIEW Stage (4 iterations max)"]
        A[Load Plan File] --> B{Parse Tasks}
        B --> C{Any [ ] Tasks?}
        C -->|Yes| D[REJECT: Incomplete Tasks]
        C -->|No| E[Verify Changes Log]
        E --> F{Entries Match Tasks?}
        F -->|No| G[REJECT: Missing Changes]
        F -->|Yes| H[Pre-Check PASSED]
        H --> I[Proceed to Code Review]
        I --> J{Code Quality OK?}
        J -->|Yes| K[VERIFIED_APPROVED]
        J -->|No| L[REJECTED: Code Issues]
    end
    
    D --> M[Builder Addresses Feedback]
    G --> M
    L --> M
    M --> A
```

**Implementation Details:**

1. **YAML Frontmatter** (required format):
```yaml
---
description: "Implementation review - verifies task completion before code review"
agent: agent
tools: ['read/readFile', 'search', 'edit/editFiles']
---
```

2. **Pre-Code-Review Checklist Section**:
   * Load plan file from `.agent-tracking/plans/`
   * Load changes log from `.agent-tracking/changes/`
   * Verify all phases marked `[x]`
   * Verify all tasks marked `[x]`
   * Verify changes log has entries for tasks
   * Decision: If ANY `[ ]` → REJECT; If ALL `[x]` → proceed

3. **Rejection Format Template**:
```markdown
## IMPLEMENTATION_REVIEW: REJECTED
### Status: INCOMPLETE IMPLEMENTATION
### Incomplete Tasks
- [ ] Phase N, Task X: {{task_description}}
### Missing Artifacts (if any)
- {{missing_item}}
### Action Required
Complete the listed tasks before requesting review.
### Iteration Status: X/4
```

4. **Approval Format Template**:
```markdown
## IMPLEMENTATION_REVIEW: TASK COMPLETION VERIFIED ✅
### Pre-Review Checklist
- [x] All phases complete
- [x] All tasks complete
- [x] Changes log updated
### Proceeding to Code Review
[Full code review follows]
```

5. **Code Quality Review Section** (after pre-check passes):
   * Implementation correctness
   * Test coverage verification
   * Code quality and style
   * Final approval decision using `VERIFIED_APPROVED:`

#### Considered Alternatives (Removed After Selection)

**Alternative: Separate pre-check prompt + code review prompt** - Rejected because:
* Would require two prompt files and workflow changes
* Existing ReviewIterator handles iteration with single prompt
* More complex than necessary for the requirement

**Alternative: Modify POST_REVIEW to handle completion check** - Rejected because:
* POST_REVIEW is too late in the workflow
* Incomplete implementations would already have passed IMPLEMENTATION_REVIEW
* Feature spec explicitly targets IMPLEMENTATION_REVIEW stage

## Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `teambot run objectives/x.md` | cli.py → orchestrator.py → ExecutionLoop → ReviewIterator | YES | YES - prompt loaded from stages.yaml |
| IMPLEMENTATION stage completes | ExecutionLoop._execute_work_stage → transition to IMPLEMENTATION_REVIEW | YES | YES - new prompt loaded |
| ReviewIterator iteration | review_iterator.py:execute() → prompt context passed to agent | YES | YES - prompt content defines behavior |

### Code Path Trace

#### Entry Point 1: Workflow reaches IMPLEMENTATION_REVIEW
1. Builder completes IMPLEMENTATION stage
2. ExecutionLoop.execute() advances to IMPLEMENTATION_REVIEW
3. `_execute_review_stage()` called (is_review_stage: true)
4. ReviewIterator.execute() invoked with context from prompt_template
5. Prompt content loaded from `stages.yaml:prompt_template` path ← **CURRENTLY NULL**
6. If null, no specific prompt provided; ReviewIterator uses generic context

#### Entry Point 2: With new prompt_template
1. Same as above, but prompt_template = `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md`
2. Prompt file content loaded and provided as context to reviewer agent
3. Reviewer follows prompt instructions for task completion verification
4. Returns `VERIFIED_APPROVED:` or `REJECTED:` based on prompt guidance

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| `prompt_template: null` on line 326 | No task completion check before code review | Set to new prompt path |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

**Note**: No code changes required beyond creating the prompt file and updating stages.yaml. The existing ReviewIterator infrastructure handles all execution logic.
