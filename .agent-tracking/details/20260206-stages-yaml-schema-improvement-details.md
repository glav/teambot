<!-- markdownlint-disable-file -->
# Implementation Details: stages.yaml Schema Improvement

**Research Reference**: `.teambot/file-orchestration-stages/artifacts/research.md`
**Test Strategy Reference**: `.teambot/file-orchestration-stages/artifacts/test_strategy.md`
**Plan Reference**: `.agent-tracking/plans/20260206-stages-yaml-schema-improvement-plan.instructions.md`

---

## Task Details

### Phase 1: Baseline Validation

#### Task 1.1: Run Baseline Tests (Lines 15-40)

**Purpose**: Establish baseline test state before making changes

**Command**:
```bash
uv run pytest tests/test_orchestration/test_stage_config.py -v
```

**Expected Output**:
- 21 tests pass
- Exit code 0
- No warnings related to YAML parsing

**Success Criteria**:
- All tests green
- Test count: 21 (record actual count)

**Dependencies**:
- Python environment with uv
- Test dependencies installed

---

### Phase 2: Header Documentation

#### Task 2.1: Add Comprehensive Schema Header (Lines 42-180)

**Purpose**: Replace minimal header with complete schema documentation

**File**: `stages.yaml`
**Location**: Lines 1-8 (replace existing header)

**Current Content** (Lines 1-8):
```yaml
# TeamBot Stage Configuration
#
# This file defines the 14-stage prescriptive workflow for TeamBot orchestration.
# Each stage specifies which agents run, what artifacts are produced, and exit criteria.
#
# To customize the workflow, copy this file and point to it in teambot.json:
#   "stages_config": "path/to/custom-stages.yaml"
```

**New Content**:
```yaml
# =============================================================================
# TeamBot Stage Configuration
# =============================================================================
#
# This file defines the workflow stages for TeamBot orchestration.
# Each stage specifies which agents run, what artifacts are produced, and exit criteria.
#
# To customize the workflow, copy this file and point to it in teambot.json:
#   "stages_config": "path/to/custom-stages.yaml"
#
# =============================================================================
# SCHEMA REFERENCE
# =============================================================================
#
# Stage Fields:
#   name              - Display name for the stage
#   description       - What this stage does
#   work_agent        - Agent that executes work (see AGENT SEMANTICS below)
#   review_agent      - Agent that performs review (review stages only)
#   allowed_personas  - Personas allowed at this stage (informational, not enforced)
#   artifacts         - Files produced (see ARTIFACT STORAGE below)
#   exit_criteria     - Completion conditions (informational)
#   optional          - Whether stage can be skipped (default: false)
#   is_review_stage   - Triggers review iteration loop (default: false)
#   is_acceptance_test_stage - Triggers acceptance test handling (default: false)
#   requires_acceptance_tests_passed - Blocks if acceptance tests failed (default: false)
#   parallel_agents   - Agents that can run in parallel (e.g., builder-1, builder-2)
#   prompt_template   - Path to SDD prompt file (relative to repo root)
#   include_objective - Include objective content in agent context (default: true)
#
# =============================================================================
# AGENT FIELD SEMANTICS
# =============================================================================
#
# The meaning of work_agent and review_agent depends on stage type:
#
# WORK STAGES (is_review_stage: false):
#   work_agent   = Agent that executes the stage work
#   review_agent = Not used (should be null)
#
# REVIEW STAGES (is_review_stage: true):
#   work_agent   = Agent that addresses feedback and makes revisions
#   review_agent = Agent that reviews work and approves/rejects
#
# Review stages iterate up to 4 times:
#   1. work_agent executes or revises based on feedback
#   2. review_agent reviews and provides feedback
#   3. If not approved, work_agent addresses feedback
#   4. Repeat until approved or max iterations reached
#
# Example: In SPEC_REVIEW stage:
#   work_agent: ba        → Business Analyst revises the spec
#   review_agent: reviewer → Reviewer approves or requests changes
#
# =============================================================================
# ARTIFACT STORAGE
# =============================================================================
#
# Artifacts listed in the 'artifacts' field are stored at:
#
#   {teambot_dir}/{feature_name}/artifacts/{artifact_filename}
#
# Where:
#   teambot_dir  = .teambot (or custom path from teambot.json "teambot_dir")
#   feature_name = Derived from objective file (## Feature Name or filename)
#
# Example:
#   Objective: objectives/add-user-login.md
#   Feature name: add-user-login
#   Artifact: feature_spec.md
#   Full path: .teambot/add-user-login/artifacts/feature_spec.md
#
# =============================================================================
# REVIEW STAGE MAPPING
# =============================================================================
#
# Two related but distinct concepts control review behavior:
#
# 1. is_review_stage (per-stage field):
#    - Enables the review iteration loop for that stage
#    - When true, ReviewIterator handles the stage execution
#
# 2. work_to_review_mapping (global mapping):
#    - Defines which review stage follows each work stage
#    - Used for navigation and workflow sequencing
#
# These are NOT redundant - a stage can be in work_to_review_mapping
# without being a review stage itself (e.g., ACCEPTANCE_TEST → POST_REVIEW).
#
# =============================================================================

```

**Research References**:
- Agent semantics: research.md (Lines 139-180)
- Artifact storage: research.md (Lines 184-211)
- Review mapping: research.md (Lines 215-244)

**Success Criteria**:
- Header comments preserve original customization instructions
- All field definitions accurate per StageConfig dataclass
- YAML remains valid (no syntax errors)
- Tests pass after change

---

### Phase 3: Inline Documentation

#### Task 3.1: Add Artifact Path Comment (Lines 184-195)

**Purpose**: Provide inline example of artifact storage path

**File**: `stages.yaml`
**Location**: BUSINESS_PROBLEM stage artifacts section (approximately line 37)

**Current Content**:
```yaml
    artifacts:
      - problem_statement.md
```

**New Content**:
```yaml
    artifacts:
      - problem_statement.md  # → .teambot/{feature}/artifacts/problem_statement.md
```

**Success Criteria**:
- Comment added on same line as artifact
- YAML parsing unaffected
- Provides clear example of path template

---

#### Task 3.2: Add work_to_review_mapping Section Documentation (Lines 197-215)

**Purpose**: Clarify purpose of work_to_review_mapping vs is_review_stage

**File**: `stages.yaml`
**Location**: Before `work_to_review_mapping:` (approximately line 285)

**Current Content**:
```yaml
# Mapping of work stages to their review stages
work_to_review_mapping:
```

**New Content**:
```yaml
# =============================================================================
# Work Stage → Review Stage Mapping
# =============================================================================
# Maps work stages to their corresponding review stages for workflow navigation.
# Note: This controls SEQUENCING. The is_review_stage field (per-stage) controls
# whether the ReviewIterator loop is used for execution.
#
# A stage listed here as a value (right side) should have is_review_stage: true.
# A stage listed here as a key (left side) is the work stage that precedes review.
# =============================================================================
work_to_review_mapping:
```

**Research Reference**: research.md (Lines 215-244)

**Success Criteria**:
- Explanation distinguishes purpose from is_review_stage
- Relationship clearly documented
- YAML valid

---

### Phase 4: Final Validation

#### Task 4.1: Run Orchestration Tests (Lines 219-230)

**Purpose**: Validate all orchestration-related tests pass

**Command**:
```bash
uv run pytest tests/test_orchestration/ -v
```

**Expected Output**:
- All orchestration tests pass
- No new warnings or errors

**Success Criteria**:
- Exit code 0
- Test count same or greater than baseline

---

#### Task 4.2: Run Full Test Suite (Lines 232-242)

**Purpose**: Confirm no regressions across entire codebase

**Command**:
```bash
uv run pytest
```

**Expected Output**:
- 192 tests pass (or current total)
- No failures

**Success Criteria**:
- Exit code 0
- All tests green
- Coverage maintained at 88%+

---

#### Task 4.3: Manual Documentation Review (Lines 244-255)

**Purpose**: Verify documentation accuracy and quality

**Checklist**:
- [ ] Agent semantics match code behavior (execution_loop.py, review_iterator.py)
- [ ] Artifact path formula matches code (execution_loop.py:100-107)
- [ ] Field descriptions match StageConfig dataclass (stage_config.py:17-34)
- [ ] No typos or grammatical errors
- [ ] Template syntax is consistent (uses curly braces `{}`)
- [ ] Line references in plan still valid

**Success Criteria**:
- All checklist items verified
- No inaccuracies found

---

### Phase 5: Copy Artifact

#### Task 5.1: Copy Plan to Artifacts Directory (Lines 259-265)

**Purpose**: Place implementation plan in expected artifacts location

**Source**: `.agent-tracking/plans/20260206-stages-yaml-schema-improvement-plan.instructions.md`
**Destination**: `.teambot/file-orchestration-stages/artifacts/implementation_plan.md`

**Command**:
```bash
cp .agent-tracking/plans/20260206-stages-yaml-schema-improvement-plan.instructions.md \
   .teambot/file-orchestration-stages/artifacts/implementation_plan.md
```

**Success Criteria**:
- File exists at destination
- Content matches source

---

## File Operations Summary

| Operation | File | Lines Affected |
|-----------|------|----------------|
| REPLACE | `stages.yaml` | 1-8 → 1-85 (header) |
| MODIFY | `stages.yaml` | ~37 (artifact comment) |
| REPLACE | `stages.yaml` | ~285-286 (mapping section) |
| CREATE | `.teambot/.../implementation_plan.md` | New file |

---

## Error Recovery

### If YAML Parse Error After Changes

1. Run: `python -c "import yaml; yaml.safe_load(open('stages.yaml'))"`
2. Error message will indicate line number
3. Check for:
   - Unclosed quotes
   - Invalid indentation
   - Special characters in comments
4. Fix syntax and re-run tests

### If Tests Fail

1. Compare test output to baseline (Task 1.1)
2. If new failure, check if change affected that test
3. Revert specific change and re-test
4. Common issues:
   - Comment breaking multi-line YAML
   - Indentation changes

---

## Research References Index

| Topic | Research File Location |
|-------|----------------------|
| Agent semantics analysis | research.md Lines 139-180 |
| Artifact storage finding | research.md Lines 184-211 |
| Review mapping relationship | research.md Lines 215-244 |
| allowed_personas usage | research.md Lines 248-279 |
| Recommended approach | research.md Lines 317-397 |
| Test infrastructure | research.md Lines 400-458 |
| Implementation guidance | research.md Lines 462-509 |

---

## Test Strategy References Index

| Topic | Test Strategy Location |
|-------|----------------------|
| Testing approach decision | test_strategy.md Lines 10-67 |
| Component testing breakdown | test_strategy.md Lines 104-138 |
| Coverage requirements | test_strategy.md Lines 175-215 |
| Example test patterns | test_strategy.md Lines 219-267 |
| Verification commands | test_strategy.md Lines 258-267 |
