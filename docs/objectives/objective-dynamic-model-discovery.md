## Objective

**Goal**: Replace static model lists with fully dynamic SDK-based model discovery, ensuring all models and their tier classifications come exclusively from the GitHub Copilot SDK.

**Problem Statement**: 
- The current `/models` command uses a hardcoded static fallback list that becomes outdated (e.g., missing `claude-opus-4.6`)
- Tier classifications (fast/standard/premium) are hardcoded rather than queried from the SDK
- The SDK query returns all tiers as "standard" because tier data is not being properly extracted
- Users cannot see or select premium models that are available to them in the Copilot CLI

**Success Criteria**:
- [ ] Model list comes exclusively from SDK query - no static fallback list used
- [ ] All tier classifications (fast, standard, premium) are retrieved from SDK and displayed with appropriate indicators
- [ ] Premium models (e.g., `claude-opus-4.6`) appear when available in SDK response
- [ ] If SDK query fails, an error is reported and operation stops (no silent fallback)
- [ ] SDK queries use appropriate timeout consistent with other timeouts in codebase
- [ ] `/models --refresh` accurately reflects all models available to the user's account

---

## Technical Context

**Target Codebase**: 
- `src/teambot/config/schema.py` (remove `_FALLBACK_MODELS`, `_FALLBACK_MODEL_INFO`)
- `src/teambot/copilot/sdk_client.py` (fix tier extraction in `_adapt_model_info`)
- `src/teambot/config/model_cache.py` (update caching to store SDK tier data)
- `src/teambot/repl/commands.py` (update `/models` display logic)

**Primary Language/Framework**: Python

**Testing Preference**: Follow current pattern (pytest)

**Key Constraints**:
- Only models supported by GitHub Copilot CLI SDK are valid
- Must handle SDK unavailability gracefully with clear error message
- Timeout should be consistent with other SDK timeouts in codebase
- No static/hardcoded model lists or tier mappings

---

## Additional Context

- The static fallback list in `schema.py` was last verified 2026-02-04 and is already outdated
- Current cache at `.teambot/model_cache.json` shows all models with `"category": "standard"` indicating tier data is lost
- The SDK's `capabilities.tier` attribute should provide tier classification but may need different extraction logic
- This change supports the existing model selection feature by ensuring users can see and select all available models including premium tier

---
