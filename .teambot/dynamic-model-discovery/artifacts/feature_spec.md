<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->

# Feature Specification: Dynamic Model Discovery

| Field | Value |
|-------|-------|
| **Spec ID** | SPEC-DMD-001 |
| **Version** | 1.0 |
| **Status** | Draft |
| **Author** | Business Analyst Agent |
| **Created** | 2026-02-16 |

---

## Executive Summary

### Context
TeamBot provides AI model selection functionality through the `/models` command and agent `--model` flag. Currently, model availability is determined through a hybrid approach: SDK query with cached results, falling back to hardcoded static lists when SDK or cache is unavailable.

### Opportunity
Eliminating static fallback lists ensures users always see accurate, current model information directly from the GitHub Copilot SDK. This removes maintenance burden, prevents stale data, and surfaces connectivity issues transparently.

### Goals
| ID | Goal | Success Metric |
|----|------|----------------|
| G-001 | Single source of truth for model data | Zero static model definitions in codebase |
| G-002 | Transparent failure handling | 100% of SDK failures produce visible error messages |
| G-003 | Accurate tier classification | All displayed tiers match SDK `capabilities.tier` values |
| G-004 | Current model visibility | All SDK-available models appear in `/models` output |

---

## Problem Definition

### Current Situation
TeamBot maintains two data sources for model information:

1. **Primary**: SDK query via `SDKClientWrapper.fetch_models()` → cached in `.teambot/model_cache.json`
2. **Fallback**: Static lists `_FALLBACK_MODELS` and `_FALLBACK_MODEL_INFO` in `schema.py`

The fallback mechanism creates these issues:

| Issue | Impact | Evidence |
|-------|--------|----------|
| Stale model data | Users cannot access new models | `_FALLBACK_MODELS` last verified 2026-02-04 |
| Silent degradation | SDK failures go unnoticed | Code falls back silently with only debug log |
| Tier inaccuracy | Wrong model classification displayed | Static tier mappings may diverge from SDK |
| Maintenance burden | Manual updates required | 14 models × 3 fields to maintain |

### Problem Statement
**When the SDK query fails or cache is unavailable, TeamBot silently uses outdated hardcoded model lists, causing users to see incomplete or inaccurate model information without any indication that the data is stale.**

### Impact Assessment
| Stakeholder | Impact | Severity |
|-------------|--------|----------|
| End Users | May miss premium models; incorrect tier indicators | Medium |
| Developers | Must maintain duplicate data sources | Low |
| DevOps | SDK issues masked by silent fallback | Medium |

---

## Personas

### P-001: Developer User
- **Description**: Software developer using TeamBot for AI-assisted development
- **Needs**: Access to all available models, accurate tier information for cost decisions
- **Pain Points**: Doesn't know when using stale data; may miss new premium models

### P-002: TeamBot Maintainer
- **Description**: Developer maintaining the TeamBot codebase
- **Needs**: Minimal maintenance overhead; single source of truth
- **Pain Points**: Must manually update fallback lists when models change

---

## Functional Requirements

### FR-001: Remove Static Fallback Model Lists
**Priority**: P0 - Critical
**Linked Goal**: G-001
**Description**: Remove all hardcoded model definitions from the codebase.

**Acceptance Criteria**:
- [ ] `_FALLBACK_MODELS` removed from `src/teambot/config/schema.py`
- [ ] `_FALLBACK_MODEL_INFO` removed from `src/teambot/config/schema.py`
- [ ] `VALID_MODELS` and `MODEL_INFO` aliases removed or updated
- [ ] No other static model sets exist in codebase
- [ ] Code that referenced fallback lists uses SDK/cache data exclusively

---

### FR-002: SDK-Only Model Discovery
**Priority**: P0 - Critical
**Linked Goal**: G-001
**Description**: All model data must come from SDK query or valid cache populated by SDK.

**Acceptance Criteria**:
- [ ] `get_available_models()` returns SDK-sourced data only
- [ ] `get_model_info()` returns SDK-sourced tier/display data only
- [ ] `validate_model()` validates against SDK-sourced model list only
- [ ] If no cache exists and SDK query fails, functions return empty/error (not fallback data)

---

### FR-003: Mandatory SDK Query on Empty Cache
**Priority**: P0 - Critical
**Linked Goal**: G-002, G-004
**Description**: When cache is missing or expired, SDK query is mandatory. If SDK query fails, operation fails with error.

**Acceptance Criteria**:
- [ ] First access with no cache triggers synchronous SDK query
- [ ] `/models` command shows error if SDK unavailable and cache empty
- [ ] `/models --refresh` fails with clear error if SDK unavailable
- [ ] No silent fallback to hardcoded data

---

### FR-004: Error Handling for SDK Failures
**Priority**: P0 - Critical
**Linked Goal**: G-002
**Description**: SDK query failures must produce user-visible error messages.

**Acceptance Criteria**:
- [ ] SDK timeout produces: `[red]✗ Failed to fetch models: SDK timeout[/red]`
- [ ] SDK connection error produces: `[red]✗ Failed to fetch models: Connection error[/red]`
- [ ] Error message includes actionable guidance (e.g., "Check network connectivity")
- [ ] Error is shown to user, not just logged
- [ ] Use existing `SDKClientError` exception class

**Error Message Format** (follow existing REPL patterns):
```
[red]✗ Failed to fetch models: {error_type}[/red]
[dim]Run 'copilot --version' to verify SDK installation.[/dim]
```

---

### FR-005: Fix Tier Extraction in `_adapt_model_info()`
**Priority**: P1 - High
**Linked Goal**: G-003
**Description**: Ensure tier/category is correctly extracted from all SDK response formats.

**Acceptance Criteria**:
- [ ] Tier extracted from `capabilities.tier` when present
- [ ] Tier extracted from `capabilities["tier"]` when dict format
- [ ] If tier field is `None`, empty string, or missing: **error, not default**
- [ ] Valid tiers: `fast`, `standard`, `premium`
- [ ] Invalid tier values produce warning log, use `standard` as fallback for display only

**Implementation Note**: Current code defaults missing tier to `"standard"`. This masks SDK issues. The new behavior should:
1. Log a warning when tier is missing/invalid
2. Still display the model (don't fail entirely)
3. Use `"standard"` only for display, not as authoritative data

---

### FR-006: Update `/models` Display Logic
**Priority**: P1 - High
**Linked Goal**: G-004
**Description**: Update `/models` command to handle SDK-only data source.

**Acceptance Criteria**:
- [ ] Remove "Using fallback list" message (line 263 in commands.py)
- [ ] When cache valid: Show "(Cached: X minutes/hours ago)"
- [ ] When cache empty/expired: Attempt SDK refresh before display
- [ ] On SDK failure: Show error message instead of model list
- [ ] `/models --refresh` shows success count or specific error

---

### FR-007: SDK Query Timeout Configuration
**Priority**: P2 - Medium
**Linked Goal**: Consistency
**Description**: SDK model queries must use timeout consistent with existing SDK patterns.

**Acceptance Criteria**:
- [ ] Model fetch uses same timeout as `SDKClientWrapper.execute()`: `120.0` seconds
- [ ] Timeout is configurable via same mechanism as other SDK timeouts
- [ ] Timeout errors produce specific message: "SDK query timed out after {X} seconds"

---

### FR-008: Cache Validation on Load
**Priority**: P2 - Medium
**Linked Goal**: G-003
**Description**: Validate cached data contains required fields with valid values.

**Acceptance Criteria**:
- [ ] Cache load validates each model has: `id` (non-empty string), `name` (string), `category` (valid tier)
- [ ] Invalid cache entries are logged and skipped
- [ ] Corrupted cache file triggers SDK refresh

---

## Non-Functional Requirements

### NFR-001: Response Time
**Priority**: P1
**Description**: Model list display should not significantly delay user interaction.
**Metric**: `/models` command completes within 200ms when using valid cache
**Verification**: Timing test with valid cache file

### NFR-002: SDK Timeout Bound
**Priority**: P1
**Description**: SDK queries must not block indefinitely.
**Metric**: SDK model fetch times out after 120 seconds maximum
**Verification**: Integration test with mocked slow SDK

### NFR-003: Error Message Clarity
**Priority**: P1
**Description**: Error messages must be actionable.
**Metric**: All error messages include both error type and suggested action
**Verification**: Code review of error message strings

### NFR-004: Backward Compatibility
**Priority**: P2
**Description**: Existing cache files remain compatible.
**Metric**: Cache files from previous versions load successfully
**Verification**: Load test with existing cache file format

---

## Acceptance Test Scenarios

### AT-001: Fresh Install Model Discovery
**Description**: User runs `/models` for first time with no cache
**Preconditions**: No `.teambot/model_cache.json` exists, SDK is available
**Steps**:
1. User starts TeamBot REPL
2. User enters `/models`
**Expected Result**: Models are fetched from SDK, displayed with correct tiers, cache file created
**Verification**: 
- Model list includes models from SDK (check for multiple tiers present)
- `.teambot/model_cache.json` exists with timestamp
- Output shows "(Cached: 0 minutes ago)"

### AT-002: Cached Model Display
**Description**: User runs `/models` with valid cache
**Preconditions**: Valid `.teambot/model_cache.json` exists (< 24 hours old)
**Steps**:
1. User starts TeamBot REPL
2. User enters `/models`
**Expected Result**: Models displayed from cache without SDK call
**Verification**: 
- Model list matches cache file contents
- Output shows "(Cached: X minutes/hours ago)"
- No SDK network call made (verify via logs or mock)

### AT-003: SDK Failure - No Cache
**Description**: User runs `/models` when SDK unavailable and no cache exists
**Preconditions**: No cache file, SDK returns error (mock network failure)
**Steps**:
1. User starts TeamBot REPL
2. User enters `/models`
**Expected Result**: Error message displayed, no model list shown
**Verification**: 
- Output contains `[red]` error formatting
- Output contains "Failed to fetch models"
- Output contains actionable guidance
- No fallback list displayed

### AT-004: SDK Failure - Valid Cache Exists
**Description**: User runs `/models --refresh` when SDK unavailable but cache exists
**Preconditions**: Valid cache exists, SDK returns error
**Steps**:
1. User enters `/models --refresh`
**Expected Result**: Error message about refresh failure, cache remains usable
**Verification**: 
- Error message indicates refresh failed
- Subsequent `/models` (without --refresh) still shows cached data
- Cache file not corrupted

### AT-005: Premium Model Visibility
**Description**: Premium models from SDK appear in output
**Preconditions**: SDK response includes premium tier models (e.g., `claude-opus-4.6`)
**Steps**:
1. User enters `/models --refresh`
2. User enters `/models`
**Expected Result**: Premium models displayed under "PREMIUM:" category
**Verification**: 
- Output contains "PREMIUM:" section
- Premium model ID and display name shown
- Tier indicator correct

### AT-006: Tier Classification Accuracy
**Description**: All tier classifications match SDK data
**Preconditions**: SDK returns models with various tiers
**Steps**:
1. User enters `/models --refresh`
2. User enters `/models`
**Expected Result**: Each model appears in correct tier category
**Verification**: 
- Compare displayed tiers against SDK response data
- No model appears in wrong category
- Models with `fast` tier under "FAST:", `premium` under "PREMIUM:", etc.

---

## Technical Context

### Target Files
| File | Changes Required |
|------|------------------|
| `src/teambot/config/schema.py` | Remove `_FALLBACK_MODELS`, `_FALLBACK_MODEL_INFO`, update `get_available_models()`, `get_model_info()`, `validate_model()` |
| `src/teambot/copilot/sdk_client.py` | Fix tier extraction in `_adapt_model_info()`, add logging for missing tier |
| `src/teambot/config/model_cache.py` | Add cache validation, ensure tier data preserved correctly |
| `src/teambot/repl/commands.py` | Update `handle_models()` to handle no-fallback scenario, improve error messages |

### Existing Patterns to Follow
| Pattern | Reference | Usage |
|---------|-----------|-------|
| SDK timeout | `sdk_client.py:314` - `120.0` seconds | Use same timeout for model fetch |
| Error formatting | `loop.py:96-104` - `[red]SDK Error: {e}[/red]` | Use same Rich markup pattern |
| Exception class | `sdk_client.py:89` - `SDKClientError` | Raise for SDK failures |
| Cache TTL | `model_cache.py:18` - `24 * 60 * 60` | Maintain existing TTL |

### Testing Approach
**Framework**: pytest (existing)
**Pattern**: Follow existing test structure in `tests/`
**Coverage**: Must maintain or improve existing coverage

---

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| GitHub Copilot SDK | External | Source of model data |
| `SDKClientWrapper.fetch_models()` | Internal | Existing SDK query method |
| `model_cache.py` | Internal | Existing cache infrastructure |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SDK unavailable at first use | Medium | High | Clear error message with troubleshooting steps |
| Cache corruption | Low | Medium | Validate on load, refresh on corruption |
| SDK response format change | Low | Medium | Log warnings for unexpected format, graceful handling |

---

## Out of Scope

- Changes to the GitHub Copilot SDK itself
- Adding new model capabilities beyond discovery
- Changes to model selection logic or `--model` flag behavior
- Model preference or default model settings
- Model usage analytics or tracking

---

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| 1 | Should expired cache still be usable when SDK is down? | **Decision Needed** | Recommend: Yes, show warning but allow usage |
| 2 | What happens to `validate_model()` when no models available? | **Decision Needed** | Recommend: Return False for all, log error |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-16 | BA Agent | Initial specification |

<!-- markdown-table-prettify-ignore-end -->
