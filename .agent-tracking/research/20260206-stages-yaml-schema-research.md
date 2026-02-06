<!-- markdownlint-disable-file -->
# Research: stages.yaml Schema Improvement

**Date**: 2026-02-06
**Researcher**: Builder-1
**Objective**: Make the `stages.yaml` schema more intuitive by consolidating redundant fields, clarifying semantics, and documenting implicit behaviors

## ✅ RESEARCH STATUS: COMPLETE

All success criteria have been met. The `stages.yaml` schema has been enhanced with comprehensive documentation following **Option A (Documentation-Only)** approach, which was recommended because:

1. ✅ No breaking changes to existing workflows
2. ✅ All 920 tests continue to pass
3. ✅ Clarifies semantics without code changes
4. ✅ Lower risk than schema refactoring

**Key Documentation Added to `stages.yaml`**:
- **SCHEMA REFERENCE** (lines 12-30): Complete field reference
- **AGENT FIELD SEMANTICS** (lines 32-54): Explains dual meaning of work_agent/review_agent
- **ARTIFACT STORAGE** (lines 56-72): Explicit path template with example
- **REVIEW STAGE MAPPING** (lines 74-90): Clarifies is_review_stage vs work_to_review_mapping

---

## 📋 Research Scope

### Primary Questions to Answer

1. What are the exact semantics of `work_agent` and `review_agent` in different contexts?
2. Where are artifacts stored and how should this be documented?
3. What is the relationship between `is_review_stage` and `work_to_review_mapping`?
4. Which fields are redundant and can be consolidated?
5. What implicit behaviors need to be made explicit?

### Success Criteria

- [x] `stages.yaml` includes header documentation explaining the schema ✅ **IMPLEMENTED**
- [x] `work_agent`/`review_agent` semantics are documented clearly ✅ **IMPLEMENTED**
- [x] Artifact storage path is explicitly documented with template syntax ✅ **IMPLEMENTED**
- [x] `is_review_stage` relationship to `work_to_review_mapping` is clarified ✅ **IMPLEMENTED**
- [x] All implicit behaviors are made explicit or documented ✅ **IMPLEMENTED**
- [x] Existing tests continue to pass (no breaking changes) ✅ **920 tests pass**
- [x] Migration guide or backward compatibility notes if schema changes ✅ **N/A - documentation only**

---

## 🔍 Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Configuration Consumed | Notes |
|-------------|-----------|------------------------|-------|
| `teambot run <objective>` | `cli.py` → `ExecutionLoop` → `stage_config.py` | ✅ Full | Primary entry point |
| `ExecutionLoop.__init__()` | `execution_loop.py:110-116` | ✅ Full | Loads `stages_config` |
| Review stage execution | `execution_loop.py:175-193` | `is_review_stage`, `work_agent`, `review_agent` | Triggers `ReviewIterator` |
| Work stage execution | `execution_loop.py:194-195` | `work_agent` | Standard execution |
| Acceptance test execution | `execution_loop.py:169-174` | `is_acceptance_test_stage` | Special handling |

### Code Path Trace

#### Entry Point 1: Stage Configuration Loading
1. `ExecutionLoop.__init__()` calls `load_stages_config()` (line 113-115)
2. `load_stages_config()` parses YAML into `StagesConfiguration` (stage_config.py:71-105)
3. `_parse_configuration()` creates `StageConfig` objects (stage_config.py:108-180)
4. Configuration stored in `self.stages_config` for workflow execution

#### Entry Point 2: Review Stage Execution
1. `run()` checks `stage in self.stages_config.review_stages` (line 175)
2. If true, calls `_execute_review_stage()` (line 190)
3. `ReviewIterator.execute()` uses `work_agent` and `review_agent` (review_iterator.py:137-156)
4. `work_agent` = agent that does work/makes revisions
5. `review_agent` = agent that reviews and approves

#### Entry Point 3: Artifact Storage
1. `ExecutionLoop.__init__()` creates feature directory (lines 102-107):
   ```python
   self.feature_name = self.objective.feature_name
   self.teambot_dir = teambot_dir / self.feature_name
   (self.teambot_dir / "artifacts").mkdir(exist_ok=True)
   ```
2. Artifacts saved to: `.teambot/{feature-name}/artifacts/{artifact-file}`
3. **This path is NOT documented in stages.yaml**

### Coverage Verification

| Configuration Field | Entry Points Covered | Implementation Status |
|---------------------|---------------------|----------------------|
| `work_agent` | Work stages, Review stages | ✅ Used correctly |
| `review_agent` | Review stages only | ✅ Used correctly |
| `is_review_stage` | Stage type determination | ✅ Used correctly |
| `artifacts` | Listed with path documented | ✅ Path now documented in header |
| `work_to_review_mapping` | `ReviewIterator` iteration | ✅ Used correctly |
| `allowed_personas` | Loaded, marked as informational | ✅ Usage documented (not enforced) |

---

## 📊 Current Schema Analysis

### StageConfig Dataclass (stage_config.py:17-34)

```python
@dataclass
class StageConfig:
    name: str
    description: str
    work_agent: str | None
    review_agent: str | None
    allowed_personas: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    exit_criteria: list[str] = field(default_factory=list)
    optional: bool = False
    is_review_stage: bool = False
    is_acceptance_test_stage: bool = False
    requires_acceptance_tests_passed: bool = False
    parallel_agents: list[str] | None = None
    prompt_template: str | None = None
    include_objective: bool = True
```

### Field Categories

#### 🎭 Agent Assignment Fields
| Field | Purpose | Context |
|-------|---------|---------|
| `work_agent` | Agent executing primary work | Non-review: executes stage work. Review: addresses feedback |
| `review_agent` | Agent performing review | Only used in review stages (`is_review_stage: true`) |
| `parallel_agents` | Additional agents for parallel work | Only used by IMPLEMENTATION stage currently |
| `allowed_personas` | Personas permitted at this stage | **Purpose unclear** - see analysis below |

#### 📁 Artifact Fields
| Field | Purpose | Issue |
|-------|---------|-------|
| `artifacts` | List of artifact filenames | Path is implicit: `.teambot/{feature}/artifacts/{filename}` |

#### 🔀 Stage Type Fields
| Field | Purpose | Relationship |
|-------|---------|--------------|
| `is_review_stage` | Triggers review iteration loop | Per-stage boolean flag |
| `is_acceptance_test_stage` | Triggers acceptance test handling | Specialized behavior |
| `requires_acceptance_tests_passed` | Blocks stage if tests failed | Only on POST_REVIEW |

#### 🔧 Execution Control Fields
| Field | Purpose |
|-------|---------|
| `optional` | Can be skipped |
| `exit_criteria` | Completion conditions (informational) |
| `prompt_template` | Path to SDD prompt file |
| `include_objective` | Whether to include objective in agent context |

---

## 🔎 Detailed Findings

### Finding 1: `work_agent` / `review_agent` Semantic Confusion

**Problem**: The meaning of `work_agent` changes based on `is_review_stage`:

| Context | `work_agent` Meaning | `review_agent` Meaning |
|---------|---------------------|----------------------|
| `is_review_stage: false` | Executes stage work | Unused (should be null) |
| `is_review_stage: true` | Addresses feedback/makes revisions | Performs review and approval |

**Evidence** (execution_loop.py:175-195):
```python
elif stage in self.stages_config.review_stages:
    result = await self._execute_review_stage(stage, on_progress)
else:
    await self._execute_work_stage(stage, on_progress)
```

**Evidence** (review_iterator.py:137-156):
```python
async def execute(
    self,
    stage: WorkflowStage,
    work_agent: str,      # Agent that does work/revisions
    review_agent: str,    # Agent that reviews
    context: str,
    on_progress: ...,
) -> ReviewResult:
```

**Example of Confusion** (SPEC_REVIEW in stages.yaml):
```yaml
SPEC_REVIEW:
  work_agent: ba          # BA does revisions in review stage
  review_agent: reviewer  # Reviewer approves
  allowed_personas:       # Doesn't include 'ba' - inconsistent
    - reviewer
    - project_manager
    - pm
  is_review_stage: true
```

**Recommendation**: Add documentation explaining the dual semantics, OR rename fields for review stages.

---

### Finding 2: Artifact Storage Path is Implicit

**Problem**: `artifacts` field only lists filenames, not paths. Actual path is computed in code.

**Evidence** (execution_loop.py:100-107):
```python
self.feature_name = self.objective.feature_name
self.teambot_dir = teambot_dir / self.feature_name
self.teambot_dir.mkdir(parents=True, exist_ok=True)
(self.teambot_dir / "artifacts").mkdir(exist_ok=True)
```

**Actual Path Formula**:
```
{teambot_dir}/{feature_name}/artifacts/{artifact_filename}
```

Where:
- `teambot_dir` = from `teambot.json` → `teambot_dir` field (default: `.teambot`)
- `feature_name` = from objective file's `## Feature Name` or derived from filename

**Example**:
- Objective: `objectives/add-login.md`
- Feature name: `add-login`
- Artifact: `feature_spec.md`
- **Full path**: `.teambot/add-login/artifacts/feature_spec.md`

**Recommendation**: Add explicit path documentation in stages.yaml header.

---

### Finding 3: `is_review_stage` vs `work_to_review_mapping` Relationship

**Problem**: Both exist and seem to serve related purposes. Relationship unclear.

**Analysis**:

| Construct | Purpose | Location |
|-----------|---------|----------|
| `is_review_stage` | Marks stage as requiring review iteration loop | Per-stage field |
| `work_to_review_mapping` | Maps work stage → its review stage | Global mapping |

**Observation**: They are NOT redundant - they serve different purposes:

1. `is_review_stage: true` → **Execution behavior** (triggers `ReviewIterator`)
2. `work_to_review_mapping` → **Navigation** (which review follows which work stage)

**Current Inconsistency**:
- `work_to_review_mapping` maps `ACCEPTANCE_TEST → POST_REVIEW`
- But `ACCEPTANCE_TEST` has `is_acceptance_test_stage: true`, not `is_review_stage: true`

**Evidence** (stages.yaml:285-290):
```yaml
work_to_review_mapping:
  SPEC: SPEC_REVIEW
  PLAN: PLAN_REVIEW
  IMPLEMENTATION: IMPLEMENTATION_REVIEW
  ACCEPTANCE_TEST: POST_REVIEW  # Acceptance test maps to post-review
```

**Recommendation**: Document the distinct purposes and add validation.

---

### Finding 4: `allowed_personas` Field Usage

**Problem**: Field exists but usage/enforcement is unclear.

**Evidence** (stage_config.py:55-58):
```python
def get_allowed_personas(self, stage: WorkflowStage) -> list[str]:
    """Get allowed personas for a stage."""
    config = self.stages.get(stage)
    return config.allowed_personas if config else []
```

**Observations**:
1. Method exists to retrieve allowed personas
2. No enforcement found in `execution_loop.py`
3. `STAGE_METADATA` in `stages.py` also has `allowed_personas`
4. Some inconsistencies between `allowed_personas` and agent assignments

**Example Inconsistency** (SPEC_REVIEW):
```yaml
work_agent: ba          # BA is assigned
allowed_personas:       # BA not listed!
  - reviewer
  - project_manager
  - pm
```

**Recommendation**:
- Option A: Document that `allowed_personas` is informational only
- Option B: Remove if not enforced
- Option C: Implement enforcement

---

### Finding 5: Legacy Constants in execution_loop.py

**Problem**: `execution_loop.py` has both YAML config AND hardcoded constants.

**Evidence** (execution_loop.py:36-65):
```python
# Legacy constants for backward compatibility - prefer using StagesConfiguration
REVIEW_STAGES = {
    WorkflowStage.SPEC_REVIEW,
    WorkflowStage.PLAN_REVIEW,
    ...
}

WORK_TO_REVIEW_MAPPING = { ... }
STAGE_AGENTS = { ... }
STAGE_ORDER = [ ... ]
```

**Recommendation**: Keep for backward compatibility, but document they are deprecated.

---

### Finding 6: Field Consistency Issues

| Stage | `work_agent` | In `allowed_personas`? | Issue |
|-------|--------------|----------------------|-------|
| SPEC_REVIEW | `ba` | ❌ No | Inconsistent |
| PLAN_REVIEW | `pm` | ✅ Yes | OK |
| IMPLEMENTATION | `builder-1` | Uses `builder`/`developer` | Aliasing issue |
| IMPLEMENTATION_REVIEW | `builder-1` | Uses `reviewer` only | Inconsistent |

**Recommendation**: Document agent ID vs persona aliasing.

---

## 📝 Recommended Approach: Documentation Enhancement (Option A)

Based on analysis, **Option A (Documentation-Only)** is recommended because:

1. ✅ No breaking changes to existing workflows
2. ✅ All 192 tests continue to pass
3. ✅ Clarifies semantics without code changes
4. ✅ Lower risk than schema refactoring

### Proposed Documentation Structure

Add a comprehensive header to `stages.yaml`:

```yaml
# =============================================================================
# TeamBot Stage Configuration
# =============================================================================
#
# This file defines the workflow stages for TeamBot orchestration.
#
# SCHEMA REFERENCE
# ================
#
# Stage Fields:
#   name              - Display name for the stage
#   description       - What this stage does
#   work_agent        - Agent that executes work (see semantics below)
#   review_agent      - Agent that performs review (review stages only)
#   allowed_personas  - Personas allowed at this stage (informational)
#   artifacts         - Files produced (stored in artifact directory - see below)
#   exit_criteria     - Completion conditions (informational)
#   optional          - Whether stage can be skipped (default: false)
#   is_review_stage   - Triggers review iteration loop (default: false)
#   parallel_agents   - Agents that can run in parallel
#   prompt_template   - Path to SDD prompt file
#   include_objective - Include objective in agent context (default: true)
#
# AGENT FIELD SEMANTICS
# =====================
#
# For WORK stages (is_review_stage: false):
#   work_agent   = Agent that executes the stage work
#   review_agent = Not used (should be null)
#
# For REVIEW stages (is_review_stage: true):
#   work_agent   = Agent that addresses feedback and makes revisions
#   review_agent = Agent that reviews work and approves/rejects
#
# The review process iterates up to 4 times:
#   1. work_agent executes/revises
#   2. review_agent reviews and provides feedback
#   3. If not approved, work_agent addresses feedback
#   4. Repeat until approved or max iterations reached
#
# ARTIFACT STORAGE
# ================
#
# Artifacts are stored at:
#   {teambot_dir}/{feature_name}/artifacts/{artifact_filename}
#
# Where:
#   teambot_dir  = .teambot (or custom from teambot.json)
#   feature_name = From objective file (## Feature Name or filename)
#
# Example:
#   Objective: objectives/add-login.md
#   Artifact: feature_spec.md
#   Path: .teambot/add-login/artifacts/feature_spec.md
#
# REVIEW STAGE MAPPING
# ====================
#
# work_to_review_mapping defines which review stage follows each work stage.
# is_review_stage marks stages that use the review iteration loop.
#
# These serve different purposes:
#   - work_to_review_mapping = Navigation (next stage after work)
#   - is_review_stage        = Execution behavior (review loop enabled)
#
# =============================================================================
```

---

## 🧪 Testing Strategy Research

### Existing Test Infrastructure

| Item | Value |
|------|-------|
| **Framework** | pytest 7.4+ |
| **Location** | `tests/test_orchestration/` |
| **Coverage** | 88% (192 tests total) |
| **Runner** | `uv run pytest` |

### Relevant Test Files

| File | Purpose | Lines |
|------|---------|-------|
| `test_stage_config.py` | Stage config loading and parsing | 332 lines |
| `test_execution_loop.py` | Execution behavior tests | ~500 lines |
| `test_review_iterator.py` | Review iteration tests | ~300 lines |

### Test Patterns Found

**From `test_stage_config.py`** (Lines 22-60):
- Uses `tmp_path` fixture for temp YAML files
- Tests YAML parsing and validation
- Tests default configuration fallback
- Uses `pytest.raises` for error cases

**Example Test Pattern**:
```python
def test_load_from_yaml_file(self, tmp_path: Path) -> None:
    yaml_content = """
stages:
  SETUP:
    name: Setup
    ...
"""
    config_file = tmp_path / "stages.yaml"
    config_file.write_text(yaml_content)
    config = load_stages_config(config_file)
    assert WorkflowStage.SETUP in config.stages
```

### Testing Approach for This Task

Since this is a **documentation-only** change:

| Component | Testing Approach | Rationale |
|-----------|-----------------|-----------|
| Header documentation | Manual review | No code changes |
| Existing tests | Re-run to confirm no regressions | Validation |
| YAML parsing | Existing tests cover | No schema changes |

**Verification Command**:
```bash
uv run pytest tests/test_orchestration/test_stage_config.py -v
```

---

## ✅ Implementation Guidance

### Task 1: Add Schema Documentation Header

**Location**: `stages.yaml` (lines 1-8)

**Current**:
```yaml
# TeamBot Stage Configuration
#
# This file defines the 14-stage prescriptive workflow...
```

**Proposed**: Replace with comprehensive header (see Recommended Approach section)

### Task 2: Document Agent Semantics

**Add after each review stage definition**:
```yaml
  SPEC_REVIEW:
    name: Spec Review
    description: Review and approve the feature specification
    # In review stages:
    #   work_agent = addresses feedback (BA revises spec)
    #   review_agent = reviews and approves
    work_agent: ba
    review_agent: reviewer
```

### Task 3: Add Artifact Path Documentation

**Add as inline comment**:
```yaml
    artifacts:
      - feature_spec.md  # Stored at: .teambot/{feature}/artifacts/feature_spec.md
```

### Task 4: Clarify is_review_stage vs work_to_review_mapping

**Add section comment before work_to_review_mapping**:
```yaml
# Review Stage Navigation Mapping
# ================================
# Maps work stages to their corresponding review stages.
# Note: is_review_stage (per-stage) enables review loop behavior.
#       work_to_review_mapping (global) defines stage sequencing.
work_to_review_mapping:
  SPEC: SPEC_REVIEW
  ...
```

### Task 5: Verify Tests Pass

```bash
uv run pytest tests/test_orchestration/ -v
```

---

## 🚫 Out of Scope (Option B - Schema Refactoring)

The following changes were analyzed but NOT recommended:

1. **Renaming fields** (`work_agent` → `executor`/`reviser`)
   - Would break backward compatibility
   - Requires migration tooling
   - High risk for low benefit

2. **Adding artifact path templates**
   - Would require code changes to respect new format
   - Existing path logic is clear once documented

3. **Removing redundant fields**
   - `allowed_personas` may be used by custom extensions
   - Safe to keep as informational

4. **Deriving is_review_stage from work_to_review_mapping**
   - Conceptually different purposes
   - Current explicit approach is clearer

---

## 📋 Task Implementation Requests

### Documentation Tasks (Priority) - ✅ ALL COMPLETE

- [x] **Task 1**: Add comprehensive schema documentation header to `stages.yaml` ✅
  - **Location**: `stages.yaml` lines 1-90
  - **Status**: Implemented with SCHEMA REFERENCE, AGENT SEMANTICS, ARTIFACT STORAGE, and REVIEW STAGE MAPPING sections
  
- [x] **Task 2**: Add inline comments explaining `work_agent`/`review_agent` in review stages ✅
  - **Location**: `stages.yaml` lines 32-54
  - **Status**: AGENT FIELD SEMANTICS section documents dual meaning
  
- [x] **Task 3**: Add artifact path documentation with explicit template syntax ✅
  - **Location**: `stages.yaml` lines 55-72
  - **Status**: ARTIFACT STORAGE section with template `{teambot_dir}/{feature_name}/artifacts/{artifact_filename}`
  
- [x] **Task 4**: Add section comments clarifying `is_review_stage` vs `work_to_review_mapping` ✅
  - **Location**: `stages.yaml` lines 73-90
  - **Status**: REVIEW STAGE MAPPING section clarifies distinction
  
- [x] **Task 5**: Verify all existing tests pass after documentation changes ✅
  - **Status**: 920 tests pass (increased from original 192)

### Optional Enhancement Tasks

- [x] **Task 6**: Add `allowed_personas` usage note (informational only) ✅
  - **Location**: `stages.yaml` line 20
  - **Status**: Marked as "(informational, not enforced)"
  
- [x] **Task 7**: Update `docs/guides/configuration.md` with expanded schema reference ✅
  - **Status**: Already includes Stage Configuration Fields table and prompt template documentation
  
- [ ] **Task 8**: Add deprecation note for legacy constants in `execution_loop.py`
  - **Status**: Low priority - already has comment "Legacy constants for backward compatibility"

---

## 🔮 Potential Next Research

| Topic | Priority | Rationale |
|-------|----------|-----------|
| Persona enforcement | Low | `allowed_personas` not currently enforced |
| Custom stage support | Medium | Adding user-defined stages |
| Artifact validation | Low | Verifying artifacts exist after stage |

---

## 📚 References

### Files Analyzed

| File | Lines | Purpose |
|------|-------|---------|
| `stages.yaml` | 1-291 | Primary configuration file |
| `stage_config.py` | 1-283 | Configuration loader |
| `execution_loop.py` | 1-550+ | Stage execution logic |
| `review_iterator.py` | 1-480 | Review iteration system |
| `stages.py` | 1-212 | Workflow stage definitions |
| `test_stage_config.py` | 1-332 | Unit tests for config |
| `docs/guides/configuration.md` | 1-220 | User documentation |
| `docs/feature-specs/file-orchestration-stages-cleanup.md` | 1-223 | Feature specification |

### Key Code Locations

| Behavior | File | Lines |
|----------|------|-------|
| Artifact directory creation | execution_loop.py | 100-107 |
| Review stage detection | execution_loop.py | 175 |
| Review iteration loop | review_iterator.py | 160-208 |
| Config parsing | stage_config.py | 108-180 |
| Default config | stage_config.py | 183-282 |
