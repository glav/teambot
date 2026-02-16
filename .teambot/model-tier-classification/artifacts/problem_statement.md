# Problem Statement: Model Tier Classification Fix

## Problem Definition

The current model tier classification logic in TeamBot relies on a **non-existent SDK attribute** (`capabilities.tier`), causing:

1. **Persistent warning spam** - Every model refresh logs "missing tier in capabilities" warnings
2. **Incorrect tier assignments** - All models default to "standard" regardless of actual pricing/capability tier
3. **Misleading `/models` output** - Users cannot distinguish between fast, standard, and premium models

### Current Behavior (Broken)

```
sdk_model.capabilities.tier  →  Does not exist in SDK
                            →  Falls back to "standard" with warning
```

**Impact**: Users see incorrect tier labels and are flooded with warnings during model refresh operations.

---

## Root Cause Analysis

| Aspect | Current State | Expected State |
|--------|---------------|----------------|
| **SDK Attribute** | `capabilities.tier` (does not exist) | `billing.multiplier` (available in SDK) |
| **Fallback Behavior** | Logs warning, uses "standard" | Silent fallback to "standard" |
| **Tier Mapping** | N/A (attribute missing) | Derived from multiplier ranges |

---

## Business Goals

| # | Goal | Measurable Outcome |
|---|------|-------------------|
| G1 | **Accurate tier classification** | Models display correct tier (e.g., `claude-opus-4.5` → premium) |
| G2 | **Eliminate warning noise** | Zero "missing tier" warnings during normal operation |
| G3 | **Transparency for users** | `/models` command shows billing multiplier alongside tier |
| G4 | **Graceful degradation** | Missing `billing.multiplier` silently defaults to "standard" |

---

## Success Criteria

| Criterion | Validation Method |
|-----------|-------------------|
| Model tier derived from `billing.multiplier` | Unit test: verify multiplier extraction |
| Tier mapping: `0.0-0.5` → fast, `0.51-1.5` → standard, `>1.5` → premium | Unit test: boundary values |
| No warnings logged for missing `billing.multiplier` | Integration test: verify log output |
| `claude-opus-4.5` displays as "premium" | Acceptance test: model info verification |
| Graceful fallback to "standard" when unavailable | Unit test: missing attribute handling |
| Existing tests updated for new logic | Test suite passes |
| Cache stores tier derived from billing multiplier | Unit test: cache round-trip |
| `/models` command lists multiplier per model | Manual/integration test: command output |

---

## Scope

### In Scope

- Modify `_adapt_model_info()` in `sdk_client.py` (lines 551-582)
- Update `TeamBotModelInfo` dataclass to include `multiplier` field (optional)
- Update `/models` command output to display multiplier
- Update existing unit and acceptance tests
- Ensure cache compatibility

### Out of Scope

- Changes to model pricing or billing logic
- SDK modifications
- UI changes beyond `/models` command output
- Breaking changes to `TeamBotModelInfo` interface

---

## Stakeholders

| Role | Interest |
|------|----------|
| **End Users** | Accurate model tier display, no warning noise |
| **Developers** | Clean logs, accurate model metadata |
| **Operations** | Reduced log volume, correct tier-based decisions |

---

## Assumptions

1. The Copilot SDK provides `billing.multiplier` as a numeric attribute on model objects
2. Multiplier ranges are stable: fast (≤0.5), standard (0.51-1.5), premium (>1.5)
3. Some models may not have `billing` attribute (edge case)
4. Existing tier values ("fast", "standard", "premium") must remain unchanged for UI compatibility

---

## Dependencies

| Dependency | Type | Risk |
|------------|------|------|
| Copilot SDK `billing.multiplier` attribute | External | Low - SDK documented |
| `TeamBotModelInfo` dataclass consumers | Internal | Low - additive change only |
| Model cache serialization format | Internal | Low - backward compatible |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SDK changes multiplier semantics | Low | Medium | Document current SDK version; add defensive bounds |
| Multiplier boundaries shift | Low | Low | Make thresholds configurable in future |
| Breaking existing cache entries | Low | Low | New field is optional; old cache still valid |

---

## Acceptance Criteria (User Story Format)

### US-1: Accurate Tier Classification
**As a** TeamBot user  
**I want** models to display their correct tier (fast/standard/premium)  
**So that** I can make informed decisions about model selection based on cost/capability

**Acceptance Criteria:**
- [ ] `claude-haiku-4.5` (multiplier ~0.25) → "fast"
- [ ] `claude-sonnet-4` (multiplier ~1.0) → "standard"  
- [ ] `claude-opus-4.5` (multiplier ~5.0) → "premium"

### US-2: Silent Fallback
**As a** developer  
**I want** missing billing data to silently default to "standard"  
**So that** logs remain clean and actionable

**Acceptance Criteria:**
- [ ] No warning logged when `billing.multiplier` is unavailable
- [ ] Model correctly defaults to "standard" tier

### US-3: Multiplier Visibility
**As a** user running `/models`  
**I want** to see the billing multiplier for each model  
**So that** I understand the relative cost of each model

**Acceptance Criteria:**
- [ ] `/models` output includes multiplier (e.g., `claude-opus-4.5 (5.0x) - premium`)

---

## Next Steps

1. **SPEC Stage**: Create detailed feature specification with implementation guidance
2. **TEST_STRATEGY Stage**: Define test cases for tier mapping logic
3. **IMPLEMENTATION Stage**: Builder agent implements changes to `sdk_client.py` and tests
