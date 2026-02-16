## Objective

**Goal**: Fix model tier classification to use `billing.multiplier` from the SDK instead of the non-existent `capabilities.tier` attribute.

**Problem Statement**:
- The current `_adapt_model_info` method in `sdk_client.py` looks for `capabilities.tier` which does not exist in the SDK's `ModelInfo` response
- This causes a WARNING log for every model during refresh: `"Model 'x' missing tier in capabilities, using 'standard'"`
- The warning briefly overlays user input before the display refresh, creating a poor UX
- All models incorrectly default to "standard" tier regardless of their actual classification

**Success Criteria**:
- [ ] Model tier is derived from `billing.multiplier` attribute
- [ ] Tier mapping uses: `0.0-0.5` → fast, `0.51-1.5` → standard, `>1.5` → premium
- [ ] No "missing tier" warnings logged during model refresh
- [ ] Models display correct tier classification (e.g., `claude-opus-4.5` shows as premium)
- [ ] Graceful fallback to "standard" if `billing.multiplier` is unavailable (no warning spam)
- [ ] Existing tests updated to reflect new tier extraction logic
- [ ] Cache correctly stores and retrieves tier derived from billing multiplier
- [ ] `/models` command also lists the associated multiplier against each model

---

## Technical Context

**Target Codebase**:
- `src/teambot/copilot/sdk_client.py` (`_adapt_model_info` method, lines 551-582)

**Primary Language/Framework**: Python

**Testing Preference**: Follow current pattern (pytest)

**Key Constraints**:
- Maintain backward compatibility with existing `TeamBotModelInfo` dataclass
- Tier values must remain "fast", "standard", or "premium" for UI consistency
- Must handle edge cases where `billing` or `multiplier` attributes are missing

---

## Additional Context

### SDK Response Structure (verified by @builder-1)

Each `ModelInfo` from `list_models()` contains:
- `billing.multiplier`:
  - `0.0` or `0.33` → fast/cheap models (e.g., `gpt-5-mini`, `claude-haiku-4.5`)
  - `1.0` → standard models (most models)
  - `3.0` → premium models (e.g., `claude-opus-4.5`)

### References to Remove
- All references to `capabilities.tier` should be removed
- The warning log at line 575-576 should be removed or converted to DEBUG level for the fallback case

---
