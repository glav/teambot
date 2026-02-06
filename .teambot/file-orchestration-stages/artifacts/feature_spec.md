<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Stages.yaml Schema Clarity - Feature Specification Document
Version 1.1 | Status Ready for Review | Owner TeamBot Maintainers | Team Platform | Target v0.2.0 | Lifecycle Active Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-06 |
| Problem & Users | ✅ | None | 2026-02-06 |
| Scope | ✅ | None | 2026-02-06 |
| Requirements | ✅ | None | 2026-02-06 |
| Metrics & Risks | ✅ | None | 2026-02-06 |
| Operationalization | ✅ | None | 2026-02-06 |
| Finalization | ✅ | None | 2026-02-06 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot's `stages.yaml` already has **91 lines of header documentation** (a significant improvement from earlier versions). However, an analysis reveals **four remaining documentation gaps** that need to be addressed to achieve full schema clarity.

### Core Opportunity
Complete the documentation effort by fixing one **critical accuracy issue** (`allowed_personas` incorrectly documented as "informational") and three **consistency gaps** (inline comments, defaults, validation rules).

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Complete remaining documentation gaps | UX | 80% documented | 100% documented | 1 sprint | P0 |
| G-002 | Fix incorrect `allowed_personas` documentation | Accuracy | Incorrect | Accurate | Immediate | P0 (Critical) |
| G-003 | Ensure consistent inline artifact comments | UX | 1/10 stages | 10/10 stages | 1 sprint | P1 |
| G-004 | Maintain backward compatibility | Stability | 192 passing tests | 192 passing tests | Always | P0 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Documentation header added | Users can understand schema in <5 minutes | P0 | Builder |
| Field semantics clarified | Zero user questions about field meanings | P1 | Builder |
| Implicit behaviors documented | All runtime behaviors have documentation | P1 | Builder |

## 2. Problem Definition

### Current Situation

**UPDATE (2026-02-06)**: The `stages.yaml` file now has **91 lines of header documentation** covering:
- ✅ Schema reference with all field descriptions
- ✅ Agent field semantics (work vs review stages)
- ✅ Artifact storage path template documented
- ✅ Review stage mapping distinction explained

However, **four documentation gaps remain**:

| Gap | Description | Impact |
|-----|-------------|--------|
| Incorrect `allowed_personas` docs | Header says "informational, not enforced" but `state_machine.py:302` enforces it | Users misconfigure persona lists |
| Inconsistent inline comments | Only `BUSINESS_PROBLEM` has artifact path inline comment | Users can't see paths at-a-glance |
| Missing defaults in schema | 4 fields lack default value documentation | Users don't know what's implied |
| No validation rules | Valid field combinations undocumented | Users create invalid configurations |

### Problem Statement

The documentation is **80% complete** but has a critical accuracy issue: `allowed_personas` is documented as "informational, not enforced" when the code **actually enforces it** via `is_persona_allowed()` in `state_machine.py:302`.

### Root Causes
* **Code-documentation drift**: The `allowed_personas` behavior changed but header wasn't updated
* **Inconsistent inline patterns**: Artifact path comments added to one stage but not propagated
* **Incremental documentation**: Schema reference added over time without completeness review

### Impact of Inaction
* Users configure `allowed_personas` incorrectly, expecting it to be ignored
* Inconsistent inline comments create confusion about documentation standards
* Missing defaults require users to read source code for implicit values

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| TeamBot User | Customize workflow stages for project needs | Cannot understand schema without code | High - blocked from customization |
| TeamBot Maintainer | Extend workflow with new stages | Must explain schema repeatedly | Medium - support burden |
| Integration Developer | Build tooling around TeamBot artifacts | Cannot predict artifact locations | High - blocked from integration |
| New Contributor | Contribute to TeamBot codebase | Must reverse-engineer schema | Medium - slow onboarding |

## 4. Scope

### In Scope
* Adding comprehensive YAML header documentation to `stages.yaml`
* Documenting each field's purpose, type, and valid values
* Documenting artifact storage path template
* Clarifying `is_review_stage` and `work_to_review_mapping` relationship
* Adding inline comments to key stage definitions
* Documenting the `allowed_personas` vs agent relationship

### Out of Scope
* Renaming fields (e.g., `work_agent` → `primary_agent`) - deferred to future release
* Adding field aliases or deprecation warnings in loader
* Changing workflow execution logic
* Adding new stages or workflow features
* Modifying `stage_config.py` or `execution_loop.py` code logic

### Assumptions
* Users read YAML comments when trying to understand configuration
* Inline documentation is sufficient (no separate documentation file needed)
* Existing field names remain acceptable with proper documentation

### Constraints
* **Backward Compatibility**: All existing `stages.yaml` files must continue working
* **Test Suite**: All 192 tests must pass without modification
* **No Code Changes**: Only YAML comments change; no Python code modifications

## 5. Product Overview

### Value Proposition
A self-documenting `stages.yaml` that enables users to understand and customize TeamBot workflows without reading source code, reducing time-to-understanding from ~30 minutes to ~5 minutes.

### Differentiators
* Comprehensive schema header with field reference table
* Artifact path template clearly documented
* Inline examples for complex configurations
* Relationship documentation between related fields

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Priority | Acceptance Criteria | Notes |
|-------|-------|-------------|-------|----------|---------------------|-------|
| FR-001 | Fix `allowed_personas` Documentation | Update header line ~21 to say "enforced by is_persona_allowed()" instead of "informational, not enforced" | G-002 | P0 (Critical) | Documentation matches code behavior | Currently incorrect |
| FR-002 | Add Inline Artifact Path Comments | Add `# → .teambot/{feature}/artifacts/{filename}` to all 10 stages with artifacts | G-001, G-003 | P1 | All stages have consistent inline comments | Only BUSINESS_PROBLEM has this |
| FR-003 | Complete Default Values | Add missing defaults to schema reference: `parallel_agents: null`, `prompt_template: null`, `is_acceptance_test_stage: false`, `requires_acceptance_tests_passed: false` | G-001 | P1 | All 13 fields have documented defaults | 4 currently missing |
| FR-004 | Add Validation Rules Section | Add new header section documenting valid field combinations (e.g., review_agent should be null for non-review stages) | G-002 | P2 | New section with 3+ validation rules | Does not exist |

### Detailed Requirements

#### FR-001: Fix `allowed_personas` Documentation (CRITICAL)

**Current (Line ~21, INCORRECT)**:
```yaml
#   allowed_personas  - Personas allowed at this stage (informational, not enforced)
```

**Required (CORRECT)**:
```yaml
#   allowed_personas  - Personas allowed at this stage (enforced by is_persona_allowed())
#                       The WorkflowStateMachine validates persona assignments against this list.
#                       See: src/teambot/workflow/state_machine.py:302
```

**Verification**: Read `state_machine.py:302`:
```python
return persona.lower() in [p.lower() for p in metadata.allowed_personas]
```
This confirms the field IS enforced, not informational.

#### FR-002: Add Inline Artifact Path Comments

**Pattern to apply**:
```yaml
    artifacts:
      - feature_spec.md  # → .teambot/{feature}/artifacts/feature_spec.md
```

**Stages requiring update** (10 total):
| Stage | Artifact | Status |
|-------|----------|--------|
| BUSINESS_PROBLEM | problem_statement.md | ✅ Already has inline comment |
| SPEC | feature_spec.md | ❌ Needs inline comment |
| SPEC_REVIEW | spec_review.md | ❌ Needs inline comment |
| RESEARCH | research.md | ❌ Needs inline comment |
| TEST_STRATEGY | test_strategy.md | ❌ Needs inline comment |
| PLAN | implementation_plan.md | ❌ Needs inline comment |
| PLAN_REVIEW | plan_review.md | ❌ Needs inline comment |
| IMPLEMENTATION_REVIEW | impl_review.md | ❌ Needs inline comment |
| TEST | test_results.md | ❌ Needs inline comment |
| ACCEPTANCE_TEST | acceptance_test_results.md | ❌ Needs inline comment |
| POST_REVIEW | post_review.md | ❌ Needs inline comment |

**Stages with empty artifacts (no change needed)**: SETUP, IMPLEMENTATION, COMPLETE

#### FR-003: Complete Default Values in Schema Reference

**Current schema reference (lines 12-30)** is missing defaults for:
- `parallel_agents` - default: null
- `prompt_template` - default: null  
- `is_acceptance_test_stage` - default: false
- `requires_acceptance_tests_passed` - default: false

**Updated text**:
```yaml
#   parallel_agents   - Agents that can run in parallel (e.g., builder-1, builder-2) (default: null)
#   prompt_template   - Path to SDD prompt file (relative to repo root) (default: null)
#   is_acceptance_test_stage - Triggers acceptance test handling (default: false)
#   requires_acceptance_tests_passed - Blocks if acceptance tests failed (default: false)
```

#### FR-004: Add Validation Rules Section

**New section to add after "REVIEW STAGE MAPPING" (~line 90)**:
```yaml
# =============================================================================
# VALIDATION RULES
# =============================================================================
#
# Valid field combinations by stage type:
#
# WORK STAGES (is_review_stage: false):
#   ✓ work_agent: Required (agent ID who performs work)
#   ✓ review_agent: Should be null (ignored if set on work stages)
#   ✓ parallel_agents: Optional (enables parallel execution)
#
# REVIEW STAGES (is_review_stage: true):
#   ✓ work_agent: Required (agent who makes revisions based on feedback)
#   ✓ review_agent: Required (agent who approves/rejects)
#   ✗ parallel_agents: Not applicable (reviews are sequential)
#
# TERMINAL STAGE (COMPLETE):
#   ✓ work_agent: null (no agent executes)
#   ✓ review_agent: null
#   ✓ artifacts: [] (empty)
#
# =============================================================================
```

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Maintainability | Documentation must be in YAML comments (not separate file) | 100% in-file | P0 | Visual inspection | Co-located docs |
| NFR-002 | Compatibility | Existing stages.yaml files must load without error | 192 tests pass | P0 | `uv run pytest` | No breaking changes |
| NFR-003 | Readability | Documentation follows YAML comment best practices | Consistent # style | P1 | Style review | Clean formatting |
| NFR-004 | Completeness | All 12 stage fields must be documented | 12/12 fields | P0 | Field count check | See field list |

### Stage Field Inventory (12 fields to document)

| Field | Type | Required | Current Documentation |
|-------|------|----------|----------------------|
| `name` | string | Yes | None |
| `description` | string | Yes | None |
| `work_agent` | string\|null | Yes | None |
| `review_agent` | string\|null | Yes | None |
| `allowed_personas` | list[string] | No | None |
| `artifacts` | list[string] | No | None |
| `exit_criteria` | list[string] | No | None |
| `optional` | boolean | No | None |
| `is_review_stage` | boolean | No | None |
| `is_acceptance_test_stage` | boolean | No | None |
| `requires_acceptance_tests_passed` | boolean | No | None |
| `parallel_agents` | list[string]\|null | No | None |
| `prompt_template` | string\|null | No | None |
| `include_objective` | boolean | No | None |

## 8. Data & Analytics

### Inputs
* Current `stages.yaml` file (291 lines)
* `stage_config.py` for field definitions (283 lines)
* `execution_loop.py` for behavior documentation

### Outputs / Events
* Updated `stages.yaml` with documentation header (estimated +50-80 lines)

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Schema understanding time | UX | ~30 min | <5 min | Per user | User feedback |
| Configuration errors | Quality | Unknown | Reduced | Ongoing | Issue tracker |
| Test pass rate | Stability | 192/192 | 192/192 | Immediate | pytest |

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| Current stages.yaml | Input | Critical | TeamBot | None | File exists |
| stage_config.py | Reference | High | TeamBot | None | For field definitions |
| execution_loop.py | Reference | Medium | TeamBot | None | For behavior details |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Documentation becomes stale as code evolves | Medium | Medium | Add "last updated" comment, review in PRs | Maintainers | Open |
| R-002 | YAML parser rejects certain comment formats | Low | Low | Test with Python yaml.safe_load | Builder | Open |
| R-003 | Header becomes too long and hard to navigate | Low | Low | Use section headers, keep concise | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
Not applicable - this change only adds documentation comments to a configuration file.

### PII Handling
Not applicable - no PII involved.

### Threat Considerations
Not applicable - documentation-only change.

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Replace stages.yaml | Single file update |
| Rollback | Restore previous stages.yaml | Git revert |
| Monitoring | N/A | Documentation change |
| Alerting | N/A | Documentation change |
| Support | Reduced questions expected | Self-service docs |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|--------------|-------|
| Implementation | v0.2.0 | Documentation added, tests pass | Builder |
| Review | v0.2.0 | Technical review complete | Reviewer |
| Release | v0.2.0 | Merged to main | Maintainers |

## 14. Acceptance Test Scenarios

### AT-001: `allowed_personas` Documentation Accuracy (CRITICAL)
**Description**: Verify `allowed_personas` documentation matches enforcement behavior in code
**Preconditions**: Updated `stages.yaml` file
**Steps**:
1. Open `stages.yaml` header section
2. Locate `allowed_personas` field description (~line 21)
3. Verify description says "enforced" not "informational"
4. Cross-reference with `src/teambot/workflow/state_machine.py:302`
**Expected Result**: Documentation states field is enforced via `is_persona_allowed()`
**Verification**: Text includes "enforced" AND references `is_persona_allowed()` or `state_machine.py`

### AT-002: Inline Artifact Path Comments
**Description**: Verify all stages with artifacts have consistent path comments
**Preconditions**: Updated `stages.yaml` file
**Steps**:
1. For each stage with non-empty `artifacts` list (10 stages)
2. Check artifact line has inline comment showing full path
3. Verify path format is `# → .teambot/{feature}/artifacts/{filename}`
**Expected Result**: All 10 stages have inline artifact path comments
**Verification**: `grep "# →" stages.yaml | wc -l` returns 10+

### AT-003: Default Values Complete
**Description**: Verify all 13 stage fields have documented defaults
**Preconditions**: Updated `stages.yaml` header
**Steps**:
1. Open schema reference section in header
2. For each field, check if "(default: ...)" is present
3. Count fields with defaults
**Expected Result**: All 13 fields have explicit default values documented
**Verification**: Manual count of "(default:" occurrences matches field count

### AT-004: Validation Rules Section Exists
**Description**: Verify new validation rules section is present
**Preconditions**: Updated `stages.yaml` header
**Steps**:
1. Search for "VALIDATION RULES" in header
2. Verify section documents work stage, review stage, and terminal stage rules
**Expected Result**: Validation rules section exists with 3+ rule categories
**Verification**: Section header found AND contains "WORK STAGES", "REVIEW STAGES", "TERMINAL STAGE"

### AT-005: Backward Compatibility
**Description**: Verify all existing tests pass with updated stages.yaml
**Preconditions**: Updated `stages.yaml` in repository
**Steps**:
1. Run `uv run pytest`
2. Observe test results
**Expected Result**: All 192 tests pass
**Verification**: Exit code 0, "192 passed" in output

## 15. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| None | All questions resolved | - | - | Complete |

## 16. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-02-06 | BA Agent | Initial specification | Creation |
| 1.1 | 2026-02-06 | BA Agent | Verified gaps still exist; ready for review | Update |

## 17. Appendices

### Glossary
| Term | Definition |
|------|-----------|
| Stage | A discrete step in the 14-stage TeamBot workflow |
| Work Agent | The agent ID that performs the main work for a stage |
| Review Agent | The agent ID that reviews work in linked review stages |
| Artifact | A file produced by a stage, stored in `.teambot/{objective}/artifacts/` |
| Review Stage | A stage that reviews work from a linked work stage |
| `is_persona_allowed()` | Method in `state_machine.py:302` that validates personas against `allowed_personas` |

### Implementation Checklist (for Builder Agent)

**FR-001: Fix `allowed_personas` Documentation** (Line ~21)
- [ ] Change `(informational, not enforced)` to `(enforced by is_persona_allowed())`
- [ ] Add reference to `state_machine.py:302`

**FR-002: Add Inline Artifact Path Comments** (10 stages)
- [ ] SPEC: `feature_spec.md` → add `# → .teambot/{feature}/artifacts/feature_spec.md`
- [ ] SPEC_REVIEW: `spec_review.md` → add inline comment
- [ ] RESEARCH: `research.md` → add inline comment
- [ ] TEST_STRATEGY: `test_strategy.md` → add inline comment
- [ ] PLAN: `implementation_plan.md` → add inline comment
- [ ] PLAN_REVIEW: `plan_review.md` → add inline comment
- [ ] IMPLEMENTATION_REVIEW: `impl_review.md` → add inline comment
- [ ] TEST: `test_results.md` → add inline comment
- [ ] ACCEPTANCE_TEST: `acceptance_test_results.md` → add inline comment
- [ ] POST_REVIEW: `post_review.md` → add inline comment

**FR-003: Complete Default Values** (Schema reference section)
- [ ] Add `(default: null)` to `parallel_agents`
- [ ] Add `(default: null)` to `prompt_template`
- [ ] Add `(default: false)` to `is_acceptance_test_stage`
- [ ] Add `(default: false)` to `requires_acceptance_tests_passed`

**FR-004: Add Validation Rules Section** (After line ~90)
- [ ] Add new `VALIDATION RULES` section header
- [ ] Document WORK STAGES valid combinations
- [ ] Document REVIEW STAGES valid combinations
- [ ] Document TERMINAL STAGE (COMPLETE) valid combinations

**Final Verification**
- [ ] Run `uv run pytest` - all 192 tests pass
- [ ] Verify YAML parses: `python -c "import yaml; yaml.safe_load(open('stages.yaml'))"`

### Technical Stack

| Aspect | Value |
|--------|-------|
| Primary Language | YAML (configuration) |
| Validation Language | Python |
| Testing Approach | Existing test suite (`uv run pytest`) |
| Framework | N/A (documentation-only change) |

---

**VALIDATION_STATUS: PASS**
- Placeholders: 0 remaining
- Sections Complete: 17/17
- Technical Stack: DEFINED (YAML + Python)
- Testing Approach: DEFINED (existing test suite, 192 tests)
- Acceptance Tests: 5 scenarios defined

<!-- markdown-table-prettify-ignore-end -->
