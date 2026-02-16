# Problem Statement: Dynamic Model Discovery

## Business Problem

TeamBot currently maintains **hardcoded model lists** (`_FALLBACK_MODELS` and `_FALLBACK_MODEL_INFO`) that serve as a fallback when SDK queries fail or cache is unavailable. This approach creates several critical issues:

### 1. **Stale Model Information**
- The hardcoded list (last verified 2026-02-04) becomes outdated as GitHub Copilot adds new models
- Premium models like `claude-opus-4.6` may be available in the SDK but absent from the static list
- Users cannot access new models until TeamBot's code is updated

### 2. **Silent Degradation**
- When SDK queries fail, the system silently falls back to outdated model data
- Users may not realize they're working with stale information
- This masks SDK connectivity issues that should be surfaced

### 3. **Inconsistent Tier Classification**
- The `_adapt_model_info()` function may not correctly extract tier information from all SDK response formats
- Hardcoded tier mappings in `_FALLBACK_MODEL_INFO` may not match actual SDK classifications
- Users may see incorrect model tier indicators (fast/standard/premium)

### 4. **Maintenance Burden**
- Developers must manually update the fallback list as models change
- Risk of human error in maintaining tier classifications
- Duplicate source of truth (SDK vs. hardcoded data)

---

## Business Goals

| Goal | Description |
|------|-------------|
| **Single Source of Truth** | All model data (names, IDs, tier classifications) comes exclusively from the GitHub Copilot SDK |
| **Transparency** | When SDK queries fail, users receive clear error messages explaining the failure |
| **Accuracy** | Model tier classifications always reflect the SDK's authoritative data |
| **Currency** | Users always see the complete, up-to-date list of models available to their account |

---

## Success Criteria

| # | Criterion | Verification Method |
|---|-----------|---------------------|
| 1 | Model list comes exclusively from SDK query - no static fallback list used | Code review: `_FALLBACK_MODELS` and `_FALLBACK_MODEL_INFO` removed from schema.py |
| 2 | All tier classifications (fast, standard, premium) are retrieved from SDK and displayed with appropriate indicators | Test: Verify tier displays match SDK response data |
| 3 | Premium models (e.g., `claude-opus-4.6`) appear when available in SDK response | Test: Query SDK with premium-enabled account, verify premium models displayed |
| 4 | If SDK query fails, an error is reported and operation stops (no silent fallback) | Test: Simulate SDK failure, verify error message shown and no fallback used |
| 5 | SDK queries use appropriate timeout consistent with other timeouts in codebase | Code review: Timeout value matches existing SDK timeout patterns |
| 6 | `/models --refresh` accurately reflects all models available to the user's account | Manual test: Run refresh, compare output to SDK capabilities |

---

## Stakeholders

| Role | Interest |
|------|----------|
| **End Users** | Access to all available models with accurate tier information |
| **Developers** | Reduced maintenance burden, cleaner architecture |
| **DevOps** | Clear error messages for troubleshooting SDK connectivity |

---

## Scope

### In Scope
- Remove static fallback model lists from `schema.py`
- Fix tier extraction logic in `sdk_client.py`
- Update cache logic in `model_cache.py` to store SDK tier data properly
- Update `/models` display logic to handle SDK-only data source
- Implement clear error handling when SDK is unavailable

### Out of Scope
- Changes to the GitHub Copilot SDK itself
- Adding new model capabilities beyond discovery
- Changes to model selection or preference logic

---

## Constraints

| Constraint | Rationale |
|------------|-----------|
| **SDK-only model source** | Only models supported by GitHub Copilot CLI SDK are valid; no external model sources |
| **Graceful error handling** | SDK unavailability must surface a clear, actionable error message |
| **Timeout consistency** | SDK query timeouts must match existing timeout patterns in the codebase |
| **No silent fallback** | System must not silently use stale/hardcoded data when SDK fails |

---

## Assumptions

1. The GitHub Copilot SDK provides a reliable `capabilities.tier` field (or equivalent) for all models
2. Users have network connectivity to reach the GitHub Copilot SDK endpoint
3. The existing cache mechanism (TTL-based, 24-hour default) remains appropriate for SDK data
4. The SDK response format for model data is stable

---

## Dependencies

| Dependency | Type | Risk |
|------------|------|------|
| GitHub Copilot SDK availability | External | High - no fallback if unavailable |
| SDK response format stability | External | Medium - may require adaptation if format changes |
| Existing cache infrastructure | Internal | Low - reuse existing model_cache.py patterns |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SDK unavailable at startup | Medium | High | Clear error message with troubleshooting guidance |
| SDK tier field missing/malformed | Low | Medium | Validate SDK response, error on unexpected format |
| Cache invalidation issues | Low | Low | Existing TTL mechanism, `/models --refresh` for manual override |

---

## Measurable Outcomes

1. **Zero hardcoded models**: Code contains no static model lists
2. **100% tier accuracy**: All displayed tiers match SDK response data
3. **Clear failure mode**: SDK failures produce user-visible error within 5 seconds (timeout)
4. **Complete model visibility**: All SDK-available models shown in `/models` output
