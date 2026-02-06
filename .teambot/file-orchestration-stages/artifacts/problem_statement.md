# Problem Statement: Stages.yaml Schema Clarity

## Business Problem

The `stages.yaml` configuration file drives TeamBot's 14-stage workflow orchestration, but its schema suffers from **unclear semantics**, **undocumented implicit behaviors**, and **redundant concepts** that create confusion for users who need to customize workflows.

### Core Issues

| Issue | Description | Impact |
|-------|-------------|--------|
| **Ambiguous Agent Semantics** | `work_agent` and `review_agent` naming is unclear—users don't understand when each agent executes or how they interact | Users misconfigure agent assignments, causing workflow failures |
| **Undocumented Artifact Storage** | Artifacts are stored in `.teambot/{feature}/artifacts/{artifact_name}` but this path template is nowhere documented | Users create artifacts in wrong locations; orchestrator can't find them |
| **Implicit `is_review_stage` Behavior** | The relationship between `is_review_stage: true` and `work_to_review_mapping` is not explained | Users don't understand when to set each flag or why both exist |
| **Missing Schema Documentation** | No header explaining what each field means, which are required, and valid values | Users must reverse-engineer behavior from code |
| **Redundant Fields** | `allowed_personas` overlaps conceptually with `work_agent`/`review_agent`, creating confusion | Users unsure which field controls agent access |

---

## Goals

1. **Improve Developer Experience**: Make `stages.yaml` self-documenting so users can customize workflows without reading source code
2. **Eliminate Ambiguity**: Clarify or rename fields where current naming causes confusion
3. **Make Implicit Behaviors Explicit**: Document artifact storage paths, agent execution order, and review stage mechanics
4. **Maintain Backward Compatibility**: Existing `stages.yaml` files must continue to work (or have clear migration path)

---

## Success Criteria

| Criterion | Verification Method |
|-----------|---------------------|
| `stages.yaml` includes header documentation explaining the schema | Visual inspection of file |
| `work_agent`/`review_agent` semantics are either renamed or documented clearly | Review documentation or field names |
| Artifact storage path is explicitly documented with template syntax | Verify `{teambot_dir}/artifacts/{artifact}` pattern documented |
| `is_review_stage` relationship to `work_to_review_mapping` is clarified | Review inline comments or documentation |
| All implicit behaviors are made explicit or documented | Code review + documentation review |
| Existing tests continue to pass (no breaking changes) | `uv run pytest` passes (192 tests) |
| Migration guide or backward compatibility notes if schema changes | Document exists if changes are breaking |

---

## Stakeholders

| Role | Interest |
|------|----------|
| **TeamBot Users** | Need to understand and customize workflow stages without source code |
| **TeamBot Maintainers** | Need clear schema for future extensions |
| **Integration Developers** | Need predictable artifact locations for tooling |

---

## Scope

### In Scope
- `stages.yaml` schema documentation and clarity improvements
- `src/teambot/orchestration/stage_config.py` loader comments/documentation
- Any necessary inline schema documentation

### Out of Scope
- Changing workflow execution logic
- Adding new stages or workflow features
- Modifying the 14-stage workflow structure
- Changes to agent persona definitions

---

## Constraints

1. **Backward Compatibility**: Existing valid `stages.yaml` files must continue to load and execute correctly
2. **Test Suite**: All 192 existing tests must continue to pass
3. **No Logic Changes**: This is a documentation/naming improvement, not a functional change

---

## Analysis: Current State vs Desired State

### Current State (stages.yaml)

```yaml
SPEC:
  name: Specification
  description: Create detailed feature specification
  work_agent: ba              # ← What does "work" mean?
  review_agent: reviewer      # ← When does this execute?
  allowed_personas:           # ← How does this relate to work_agent?
    - business_analyst
    - ba
  artifacts:                  # ← Where are these stored?
    - feature_spec.md
  is_review_stage: false      # ← Implicit; what triggers review stages?
```

### Desired State (stages.yaml)

```yaml
# =========================================================================
# STAGE CONFIGURATION SCHEMA
# =========================================================================
# 
# Each stage defines:
#   - primary_agent: Agent ID who performs the main work for this stage
#   - review_agent: Agent ID who reviews work (only used in review stages)
#   - artifacts: Files created, stored in: .teambot/{objective}/artifacts/
#   - is_review_stage: If true, this stage reviews the linked work stage
#                      (see work_to_review_mapping for linkage)
# =========================================================================

SPEC:
  name: Specification
  description: Create detailed feature specification
  primary_agent: ba           # Agent who creates the spec
  review_agent: reviewer      # Agent who will review in SPEC_REVIEW stage
  artifacts:
    - feature_spec.md         # → .teambot/{objective}/artifacts/feature_spec.md
  is_review_stage: false
```

---

## Recommended Approach

### Option A: Documentation-Only (Zero Breaking Changes)
- Add comprehensive YAML header comments explaining all fields
- Add inline comments for each field explaining purpose
- Document artifact path template: `.teambot/{objective-name}/artifacts/{artifact-name}`
- Document `is_review_stage` + `work_to_review_mapping` relationship

### Option B: Rename with Aliases (Low Breaking Risk)
- Rename `work_agent` → `primary_agent` (clearer intent)
- Keep `work_agent` as deprecated alias in loader
- Add deprecation warning to logs when old name used

**Recommendation**: Start with **Option A** to deliver immediate value with zero risk. Consider Option B for future release.

---

## Measurable Business Value

| Metric | Before | After |
|--------|--------|-------|
| Time to understand schema | Read source code (~30 min) | Read header (~5 min) |
| Configuration errors | Common (undocumented paths) | Rare (paths documented) |
| Support questions | High ("where are artifacts?") | Low (self-documented) |

---

## Current State Assessment (Updated 2026-02-06)

Upon reviewing the current `stages.yaml`, **the objective success criteria appear to be fully met**:

### Success Criteria Status

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Header documentation explaining schema | ✅ DONE | Lines 1-91: "SCHEMA REFERENCE" section |
| 2 | `work_agent`/`review_agent` semantics documented | ✅ DONE | Lines 31-54: "AGENT FIELD SEMANTICS" section |
| 3 | Artifact storage path template documented | ✅ DONE | Lines 56-72: "ARTIFACT STORAGE" section with template |
| 4 | `is_review_stage` vs `work_to_review_mapping` clarified | ✅ DONE | Lines 74-90: "REVIEW STAGE MAPPING" section |
| 5 | Implicit behaviors made explicit | ✅ DONE | Schema reference lists defaults for all fields |
| 6 | Existing tests pass | 🔲 VERIFY | Run `uv run pytest` to confirm |
| 7 | Migration guide (if needed) | ✅ N/A | No breaking changes introduced |

### Detailed Evidence

**Header Documentation (Lines 1-11)**
```yaml
# =============================================================================
# TeamBot Stage Configuration
# =============================================================================
# This file defines the workflow stages for TeamBot orchestration.
# Each stage specifies which agents run, what artifacts are produced...
```

**Schema Reference (Lines 12-30)**
```yaml
# Stage Fields:
#   name              - Display name for the stage
#   work_agent        - Agent that executes work (see AGENT SEMANTICS below)
#   review_agent      - Agent that performs review (review stages only)
#   ...
```

**Agent Semantics (Lines 31-54)**
```yaml
# WORK STAGES (is_review_stage: false):
#   work_agent   = Agent that executes the stage work
#   review_agent = Not used (should be null)
#
# REVIEW STAGES (is_review_stage: true):
#   work_agent   = Agent that addresses feedback and makes revisions
#   review_agent = Agent that reviews work and approves/rejects
```

**Artifact Storage (Lines 56-72)**
```yaml
# Artifacts listed in the 'artifacts' field are stored at:
#   {teambot_dir}/{feature_name}/artifacts/{artifact_filename}
```

**Review Stage Mapping (Lines 74-90)**
```yaml
# Two related but distinct concepts control review behavior:
# 1. is_review_stage (per-stage field): Enables the review iteration loop
# 2. work_to_review_mapping (global mapping): Defines navigation/sequencing
# These are NOT redundant...
```

### Minor Opportunities for Improvement

While all success criteria are met, these **optional enhancements** could add value:

1. **Inline artifact path comments** - Only `BUSINESS_PROBLEM` stage has example path; could add to others
2. **`allowed_personas` clarification** - Header states "(informational, not enforced)" but relationship to agents could be clearer
3. **Validation error messages** - `stage_config.py` could provide better error messages for invalid configs

### Revised Recommendation

**This objective may be complete.** The recommended action is:

1. **Run test suite** to validate all 192 tests pass (criterion #6)
2. **Stakeholder review** to confirm documentation meets user needs
3. **Close objective** if tests pass and stakeholders approve

---

## Next Steps

1. **SPEC Stage**: Document acceptance criteria for test validation
2. **TEST Stage**: Execute `uv run pytest` to confirm no regressions
3. **POST_REVIEW**: Final sign-off on success criteria

---

*Document Version: 1.1*  
*Stage: BUSINESS_PROBLEM*  
*Author: Business Analyst Agent*  
*Last Updated: 2026-02-06*
