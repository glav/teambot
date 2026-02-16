<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Model Tier Classification Fix - Feature Specification Document
Version 1.0 | Status Draft | Owner TBD | Team TeamBot | Target TBD | Lifecycle Implementation

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-02-16 |
| Problem & Users | 100% | None | 2026-02-16 |
| Scope | 100% | None | 2026-02-16 |
| Requirements | 100% | None | 2026-02-16 |
| Metrics & Risks | 100% | None | 2026-02-16 |
| Acceptance Tests | 100% | None | 2026-02-16 |
| Finalization | 0% | Pending implementation | - |
Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context
TeamBot's model tier classification currently attempts to read `capabilities.tier` from SDK model objects, but this attribute does not exist. The SDK actually provides pricing/capability information via `billing.multiplier`. This causes every model refresh to log warnings and incorrectly classify all models as "standard".

### Core Opportunity
Replace the broken `capabilities.tier` extraction with `billing.multiplier`-based tier derivation. This provides accurate tier classification without SDK changes, eliminates warning spam, and gives users visibility into model pricing via the `/models` command.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Accurate model tier classification | Correctness | All models show "standard" | Correct tier per multiplier | MVP | P0 |
| G-002 | Eliminate warning log spam | UX | Warning per model per refresh | Zero warnings | MVP | P0 |
| G-003 | Display billing multiplier in `/models` | Transparency | Tier only | Tier + multiplier | MVP | P1 |
| G-004 | Graceful fallback for missing data | Resilience | Warn + default | Silent default | MVP | P0 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Fix tier extraction logic | `_adapt_model_info()` derives tier from `billing.multiplier` | P0 | Builder |
| Update dataclass | `TeamBotModelInfo` includes optional `multiplier` field | P1 | Builder |
| Update `/models` display | Command shows multiplier alongside tier | P1 | Builder |
| Update test suite | All tier-related tests use new extraction logic | P0 | Builder |

---

## 2. Problem Definition

### Current Situation
- **Wrong attribute**: Code reads `capabilities.tier` which does not exist in SDK
- **Warning flood**: Every model logs "missing tier in capabilities" on refresh
- **Wrong classification**: All models default to "standard" regardless of actual tier
- **No pricing visibility**: Users cannot see billing multiplier in `/models` output

### Problem Statement
The model tier classification logic relies on a non-existent SDK attribute (`capabilities.tier`), causing incorrect tier assignments and excessive warning logs. The SDK provides tier information via `billing.multiplier`, which is not being used.

### Root Causes
1. Original implementation assumed `capabilities.tier` would exist in SDK model objects
2. SDK actually exposes pricing/tier info via `billing.multiplier` attribute
3. No validation that the assumed SDK structure matched reality

### Impact of Inaction
- Users see incorrect tier labels (all "standard")
- Log files fill with repetitive warnings
- Users cannot make informed model selection decisions based on pricing
- Trust in tool accuracy diminishes

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Developer | Select appropriate model for task | Cannot distinguish fast vs premium models | Medium - suboptimal model choices |
| Operations | Clean, actionable logs | Warning spam obscures real issues | High - monitoring effectiveness |
| Cost-conscious User | Understand model pricing | No visibility into billing multipliers | Medium - cost surprises |

---

## 4. Scope

### In Scope
| Item | Description | Priority |
|------|-------------|----------|
| `_adapt_model_info()` method | Modify to extract tier from `billing.multiplier` | P0 |
| `TeamBotModelInfo` dataclass | Add optional `multiplier: float | None` field | P1 |
| Tier mapping logic | Implement multiplier → tier conversion | P0 |
| Silent fallback | Default to "standard" without warning when data missing | P0 |
| `/models` command output | Display multiplier alongside tier | P1 |
| Unit tests | Update existing tests for new logic | P0 |
| Acceptance tests | Verify end-to-end behavior | P0 |

### Out of Scope
| Item | Reason |
|------|--------|
| SDK modifications | External dependency, not controlled |
| UI changes beyond `/models` | Separate feature scope |
| Billing calculations | Display only, no cost computation |
| Breaking `TeamBotModelInfo` API | Backward compatibility required |

### Dependencies
| Dependency | Type | Risk | Mitigation |
|------------|------|------|------------|
| Copilot SDK `billing.multiplier` | External | Low | Attribute documented in SDK |
| Model cache format | Internal | Low | Additive change only |

---

## 5. Functional Requirements

### FR-001: Extract Tier from Billing Multiplier
**Description**: The `_adapt_model_info()` method must derive the model tier from `billing.multiplier` instead of `capabilities.tier`.

**Acceptance Criteria**:
- [ ] Read `billing.multiplier` from SDK model object (supports both dict and object access)
- [ ] Convert multiplier to tier using defined thresholds
- [ ] Return tier as part of `TeamBotModelInfo`

**Links**: G-001 (Accurate classification)

---

### FR-002: Tier Mapping Thresholds
**Description**: Map billing multiplier values to tier categories using defined boundaries.

**Tier Mapping Rules**:
| Multiplier Range | Tier | Examples |
|------------------|------|----------|
| 0.0 – 0.5 (inclusive) | fast | claude-haiku-4.5 (~0.25) |
| 0.51 – 1.5 (inclusive) | standard | claude-sonnet-4 (~1.0) |
| > 1.5 | premium | claude-opus-4.5 (~5.0) |

**Acceptance Criteria**:
- [ ] Multiplier 0.0 → "fast"
- [ ] Multiplier 0.5 → "fast" (boundary)
- [ ] Multiplier 0.51 → "standard" (boundary)
- [ ] Multiplier 1.0 → "standard"
- [ ] Multiplier 1.5 → "standard" (boundary)
- [ ] Multiplier 1.51 → "premium" (boundary)
- [ ] Multiplier 5.0 → "premium"

**Links**: G-001 (Accurate classification)

---

### FR-003: Graceful Fallback for Missing Billing Data
**Description**: When `billing` or `multiplier` is unavailable, silently default to "standard" tier without logging warnings.

**Acceptance Criteria**:
- [ ] Missing `billing` attribute → "standard" tier, no warning
- [ ] Missing `multiplier` attribute → "standard" tier, no warning
- [ ] `None` multiplier value → "standard" tier, no warning
- [ ] Negative multiplier value → "standard" tier (defensive)

**Links**: G-002 (No warnings), G-004 (Graceful fallback)

---

### FR-004: Store Multiplier in TeamBotModelInfo
**Description**: Extend `TeamBotModelInfo` dataclass to include the billing multiplier value.

**Acceptance Criteria**:
- [ ] Add `multiplier: float | None` field with default `None`
- [ ] Populate multiplier from SDK `billing.multiplier` when available
- [ ] Existing code using `TeamBotModelInfo` continues to work (backward compatible)

**Links**: G-003 (Display multiplier)

---

### FR-005: Display Multiplier in /models Command
**Description**: The `/models` command output must show the billing multiplier alongside each model.

**Output Format**:
```
Available Models:

  FAST:
    claude-haiku-4.5          (Claude Haiku 4.5) [0.25x]
    gpt-5-mini                (GPT-5 Mini) [0.3x]

  STANDARD:
    claude-sonnet-4           (Claude Sonnet 4) [1.0x]
    gpt-5                     (GPT-5) [1.0x]

  PREMIUM:
    claude-opus-4.5           (Claude Opus 4.5) [5.0x]
```

**Acceptance Criteria**:
- [ ] Each model line includes `[{multiplier}x]` suffix
- [ ] Missing multiplier displays as `[–]` or omitted
- [ ] Format: `{model_id:25} ({display_name}) [{multiplier}x]`

**Links**: G-003 (Display multiplier)

---

## 6. Non-Functional Requirements

### NFR-001: No Warning Log Spam
**Description**: Normal model refresh operations must not produce warning logs for missing tier data.

**Acceptance Criteria**:
- [ ] Zero warnings logged when `billing.multiplier` is present
- [ ] Zero warnings logged when `billing.multiplier` is absent
- [ ] Debug-level logging acceptable for troubleshooting

**Links**: G-002 (Eliminate warnings)

---

### NFR-002: Backward Compatibility
**Description**: Changes must not break existing consumers of `TeamBotModelInfo`.

**Acceptance Criteria**:
- [ ] Existing code accessing `.id`, `.name`, `.category` continues to work
- [ ] New `.multiplier` field is optional (defaults to `None`)
- [ ] Model cache can read old entries without errors

**Links**: G-004 (Graceful fallback)

---

### NFR-003: Cache Compatibility
**Description**: Tier derived from billing multiplier must be correctly stored and retrieved from cache.

**Acceptance Criteria**:
- [ ] Cached models retain correct tier classification
- [ ] Cached models retain multiplier value
- [ ] Old cache entries without multiplier still load correctly

**Links**: G-001 (Accurate classification)

---

## 7. Technical Guidance

### Target Files
| File | Change Type | Description |
|------|-------------|-------------|
| `src/teambot/copilot/sdk_client.py` | Modify | Update `_adapt_model_info()` (lines 551-582), update `TeamBotModelInfo` dataclass |
| `src/teambot/repl/commands.py` | Modify | Update `/models` display format (around line 258) |
| `tests/test_copilot/test_sdk_client.py` | Modify | Update tier extraction tests |
| `tests/test_dynamic_model_discovery_acceptance.py` | Modify | Update acceptance tests |

### Implementation Notes

#### Tier Extraction Logic (Pseudocode)
```
def _get_tier_from_multiplier(multiplier: float | None) -> str:
    if multiplier is None:
        return "standard"
    if multiplier <= 0.5:
        return "fast"
    if multiplier <= 1.5:
        return "standard"
    return "premium"

def _extract_multiplier(sdk_model) -> float | None:
    billing = getattr(sdk_model, "billing", None)
    if billing is None:
        return None
    if isinstance(billing, dict):
        return billing.get("multiplier")
    return getattr(billing, "multiplier", None)
```

#### TeamBotModelInfo Update
```python
@dataclass
class TeamBotModelInfo:
    id: str
    name: str
    category: str
    multiplier: float | None = None  # NEW: billing multiplier
```

---

## 8. Acceptance Test Scenarios

### AT-001: Standard Model Tier Classification
**Description**: Verify models with multiplier ~1.0 are classified as "standard"
**Preconditions**: SDK returns model with `billing.multiplier = 1.0`
**Steps**:
1. Call `list_models()` or refresh model cache
2. Retrieve model info for a model with multiplier 1.0
3. Check tier classification
**Expected Result**: Model tier is "standard"
**Verification**: `model.category == "standard"`

---

### AT-002: Fast Model Tier Classification
**Description**: Verify models with multiplier ≤0.5 are classified as "fast"
**Preconditions**: SDK returns model with `billing.multiplier = 0.25`
**Steps**:
1. Call `list_models()` or refresh model cache
2. Retrieve model info for a model with multiplier 0.25
3. Check tier classification
**Expected Result**: Model tier is "fast"
**Verification**: `model.category == "fast"`

---

### AT-003: Premium Model Tier Classification
**Description**: Verify models with multiplier >1.5 are classified as "premium"
**Preconditions**: SDK returns model with `billing.multiplier = 5.0`
**Steps**:
1. Call `list_models()` or refresh model cache
2. Retrieve model info for a model with multiplier 5.0
3. Check tier classification
**Expected Result**: Model tier is "premium"
**Verification**: `model.category == "premium"`

---

### AT-004: Missing Billing Data Silent Fallback
**Description**: Verify models without billing data default to "standard" silently
**Preconditions**: SDK returns model without `billing` attribute
**Steps**:
1. Call `list_models()` with a model missing billing data
2. Check tier classification
3. Check log output
**Expected Result**: Model tier is "standard", no warning logged
**Verification**: `model.category == "standard"` and no "missing" or "warning" in logs

---

### AT-005: /models Command Shows Multiplier
**Description**: Verify `/models` command displays billing multiplier for each model
**Preconditions**: Models are cached with multiplier data
**Steps**:
1. Run `/models` command
2. Examine output format
**Expected Result**: Each model shows `[{multiplier}x]` suffix
**Verification**: Output contains strings like `[1.0x]`, `[0.25x]`, `[5.0x]`

---

### AT-006: Tier Boundary Values
**Description**: Verify boundary values classify correctly
**Preconditions**: SDK returns models with boundary multipliers
**Test Cases**:
| Multiplier | Expected Tier |
|------------|---------------|
| 0.5 | fast |
| 0.51 | standard |
| 1.5 | standard |
| 1.51 | premium |
**Expected Result**: Each boundary value maps to correct tier
**Verification**: Assert each boundary case

---

## 9. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SDK changes multiplier semantics | Low | Medium | Document SDK version; add defensive bounds |
| Multiplier boundaries shift | Low | Low | Consider making thresholds configurable |
| Old cache entries incompatible | Low | Low | New field optional; graceful degradation |
| Edge case multipliers (negative, very large) | Low | Low | Defensive handling, default to standard |

---

## 10. Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Warning log count | N per model per refresh | 0 | Log analysis |
| Tier accuracy | 0% (all "standard") | 100% | Manual verification against SDK data |
| Test coverage | Existing | Maintained or improved | pytest --cov |

---

## 11. Test Strategy

### Unit Tests (Update Existing)
- `test_adapt_model_info_with_dict_capabilities` → Change to test `billing.multiplier` dict
- `test_adapt_model_info_with_object_capabilities` → Change to test `billing.multiplier` object
- `test_adapt_model_info_minimal` → Verify silent fallback (no warning)
- `test_adapt_model_info_logs_warning_for_missing_tier` → **DELETE** (no longer warns)
- `test_adapt_model_info_logs_warning_for_invalid_tier` → **DELETE** (no longer warns)
- **NEW**: `test_adapt_model_info_tier_boundaries` → Test all boundary values
- **NEW**: `test_adapt_model_info_multiplier_extraction` → Test multiplier stored in result

### Acceptance Tests (Update Existing)
- Update mock models in `test_dynamic_model_discovery_acceptance.py` to use `billing.multiplier`
- Add tests for `/models` output format including multiplier display

---

## 12. Implementation Checklist

- [ ] Update `TeamBotModelInfo` dataclass with `multiplier` field
- [ ] Rewrite `_adapt_model_info()` to extract `billing.multiplier`
- [ ] Implement tier mapping with defined thresholds
- [ ] Remove warning logs for missing tier data
- [ ] Update `/models` command output format
- [ ] Update unit tests in `test_sdk_client.py`
- [ ] Update acceptance tests in `test_dynamic_model_discovery_acceptance.py`
- [ ] Run full test suite to verify no regressions
- [ ] Manual verification with real SDK models

---

## VALIDATION_STATUS: PASS
- Placeholders: 0 remaining
- Sections Complete: 12/12
- Technical Stack: DEFINED (Python, pytest)
- Testing Approach: DEFINED (update existing tests)
- Acceptance Tests: 6 scenarios defined

---

<!-- markdown-table-prettify-ignore-end -->
