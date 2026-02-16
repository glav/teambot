<!-- markdownlint-disable-file -->
# Model Tier Classification Fix - Research Document

**Date**: 2026-02-16  
**Feature**: Model Tier Classification Fix  
**Status**: ✅ Research Complete  
**Specification**: `.teambot/model-tier-classification/artifacts/feature_spec.md`

---

## 📋 Research Summary

| Item | Finding |
|------|---------|
| **Root Cause** | Code reads `capabilities.tier` but SDK `ModelCapabilities` only has `supports` and `limits` |
| **Solution** | Use `billing.multiplier` attribute from SDK `ModelInfo` |
| **SDK Verification** | ✅ Confirmed in `copilot/types.py` lines 844-918 |
| **Impact Scope** | 4 files (sdk_client.py, commands.py, model_cache.py, test files) |
| **Testing** | pytest framework, ~1050 tests, 80% coverage |

---

## 1. SDK Structure Analysis

### 1.1 ModelInfo Class (SDK Source)

**Source File**: `.venv/lib/python3.12/site-packages/copilot/types.py` (Lines 863-918)

```python
@dataclass
class ModelInfo:
    """Information about an available model"""
    
    id: str                              # Model identifier (e.g., "claude-sonnet-4.5")
    name: str                            # Display name
    capabilities: ModelCapabilities      # Model capabilities and limits
    policy: ModelPolicy | None = None    # Policy state
    billing: ModelBilling | None = None  # ✅ BILLING INFORMATION (OPTIONAL)
    supported_reasoning_efforts: list[str] | None = None
    default_reasoning_effort: str | None = None
```

**Key Finding**: `billing` is an **optional field** (`ModelBilling | None`).

### 1.2 ModelBilling Class (SDK Source)

**Source File**: `.venv/lib/python3.12/site-packages/copilot/types.py` (Lines 844-860)

```python
@dataclass
class ModelBilling:
    """Model billing information"""
    
    multiplier: float  # ✅ THE FIELD WE NEED
    
    @staticmethod
    def from_dict(obj: Any) -> ModelBilling:
        multiplier = obj.get("multiplier")
        if multiplier is None:
            raise ValueError("Missing required field 'multiplier' in ModelBilling")
        return ModelBilling(multiplier=float(multiplier))
```

**Key Finding**: `multiplier` is a **required field** within `ModelBilling` (float type).

### 1.3 ModelCapabilities Class (SDK Source)

**Source File**: `.venv/lib/python3.12/site-packages/copilot/types.py` (Lines 791-815)

```python
class ModelCapabilities:
    """Model capabilities and limits"""
    
    supports: ModelSupports  # What the model supports
    limits: ModelLimits      # Model limits
```

**❌ CONFIRMS BUG**: `ModelCapabilities` does **NOT** have a `tier` attribute. The current code's attempt to read `capabilities.tier` will always fail.

---

## 2. Entry Point Analysis

### 2.1 User Input Entry Points

| Entry Point | Code Path | Reaches `_adapt_model_info`? | Implementation Required? |
|-------------|-----------|------------------------------|-------------------------|
| `/models --refresh` | `commands.py:_handle_models_refresh()` → `schema.py:refresh_models()` → `sdk_client.py:list_models()` → `_adapt_model_info()` | ✅ YES | ✅ YES |
| `/models` (cache miss) | `commands.py:handle_models()` → `schema.py:get_available_models()` → cache load | ❌ NO (cache only) | ✅ Cache format update |
| SDK startup | `sdk_client.py:list_models()` → `_adapt_model_info()` | ✅ YES | ✅ YES |

### 2.2 Code Path Trace

#### Entry Point 1: `/models --refresh` Command

```
1. User enters: `/models --refresh`
2. Handled by: `commands.py:_handle_models_refresh()` (lines 284-307)
3. Routes to: `schema.py:refresh_models()` (lines 128-175)
4. Calls: `sdk_client.py:client.list_models()` (line 150)
5. Adapts: `sdk_client.py:_adapt_model_info()` (line 546)  ✅ REACHES FEATURE
6. Saves: `model_cache.py:save_cache()` (line 164)
7. Returns: `TeamBotModelInfo` with category field
```

#### Entry Point 2: `/models` Command (Cached)

```
1. User enters: `/models`
2. Handled by: `commands.py:handle_models()` (lines 209-281)
3. Loads from: `schema.py:get_available_models()` (lines 88-100)
4. Reads: `model_cache.py:load_cache()` → `CachedModel` objects
5. Displays: category from cache  ✅ REQUIRES CACHE UPDATE FOR MULTIPLIER
```

### 2.3 Coverage Verification

| Component | Entry Point Coverage | Notes |
|-----------|---------------------|-------|
| `_adapt_model_info()` | ✅ Fully covered | Called via `list_models()` |
| `TeamBotModelInfo` | ✅ Fully covered | Created by adapter |
| Model cache | ⚠️ Needs update | Must store/retrieve `multiplier` |
| `/models` display | ⚠️ Needs update | Must show `[{multiplier}x]` |

### 2.4 Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| Cache schema lacks `multiplier` | `/models` cannot display multiplier | Add `multiplier` field to `CachedModel` and cache format |
| `/models` output format | Users cannot see billing info | Update display loop in `handle_models()` |

---

## 3. Current Implementation Analysis

### 3.1 TeamBotModelInfo Dataclass (Current)

**File**: `src/teambot/copilot/sdk_client.py` (Lines 13-25)

```python
@dataclass
class TeamBotModelInfo:
    """Model information adapted from SDK for TeamBot use."""
    
    id: str
    name: str
    category: str  # "standard", "fast", or "premium"
    # ❌ MISSING: multiplier field
```

### 3.2 _adapt_model_info Method (Current - Broken)

**File**: `src/teambot/copilot/sdk_client.py` (Lines 551-581)

```python
@staticmethod
def _adapt_model_info(sdk_model: Any) -> TeamBotModelInfo:
    model_id = getattr(sdk_model, "id", str(sdk_model))
    name = getattr(sdk_model, "name", model_id)

    # ❌ BUG: capabilities.tier DOES NOT EXIST
    capabilities = getattr(sdk_model, "capabilities", None)
    category = None

    if isinstance(capabilities, dict):
        category = capabilities.get("tier")  # ❌ Never succeeds
    elif capabilities is not None:
        category = getattr(capabilities, "tier", None)  # ❌ Never succeeds

    # ❌ Always logs warning and defaults to "standard"
    if not category:
        logger.warning(f"Model '{model_id}' missing tier in capabilities, using 'standard'")
        category = "standard"
    
    return TeamBotModelInfo(id=model_id, name=name, category=category)
```

### 3.3 CachedModel Dataclass (Current)

**File**: `src/teambot/config/model_cache.py` (Lines 25-37)

```python
@dataclass
class CachedModel:
    """Cached model information."""
    
    id: str
    name: str
    category: str
    # ❌ MISSING: multiplier field
```

---

## 4. Recommended Implementation

### 4.1 Helper Functions (NEW)

Add to `src/teambot/copilot/sdk_client.py` before `_adapt_model_info`:

```python
def _extract_multiplier(sdk_model: Any) -> float | None:
    """Extract billing multiplier from SDK model.
    
    Args:
        sdk_model: SDK ModelInfo object.
    
    Returns:
        Multiplier value if available, None otherwise.
    """
    billing = getattr(sdk_model, "billing", None)
    if billing is None:
        return None
    if isinstance(billing, dict):
        return billing.get("multiplier")
    return getattr(billing, "multiplier", None)


def _get_tier_from_multiplier(multiplier: float | None) -> str:
    """Convert billing multiplier to tier category.
    
    Args:
        multiplier: Billing multiplier value (may be None).
    
    Returns:
        Tier string: "fast", "standard", or "premium".
    """
    if multiplier is None or multiplier < 0:
        return "standard"  # Default for missing/invalid data
    if multiplier <= 0.5:
        return "fast"
    if multiplier <= 1.5:
        return "standard"
    return "premium"
```

### 4.2 TeamBotModelInfo Update

**File**: `src/teambot/copilot/sdk_client.py` (Lines 13-25)

```python
@dataclass
class TeamBotModelInfo:
    """Model information adapted from SDK for TeamBot use.

    Attributes:
        id: Model identifier (e.g., "claude-opus-4.6").
        name: Human-readable display name.
        category: Model tier - "standard", "fast", or "premium".
        multiplier: Billing multiplier (None if unavailable).
    """

    id: str
    name: str
    category: str
    multiplier: float | None = None  # ✅ NEW: optional, backward compatible
```

### 4.3 _adapt_model_info Rewrite

**File**: `src/teambot/copilot/sdk_client.py` (Lines 551-581)

```python
@staticmethod
def _adapt_model_info(sdk_model: Any) -> TeamBotModelInfo:
    """Adapt SDK ModelInfo to TeamBot format.

    Args:
        sdk_model: SDK ModelInfo object.

    Returns:
        TeamBotModelInfo with adapted fields.
    """
    model_id = getattr(sdk_model, "id", str(sdk_model))
    name = getattr(sdk_model, "name", model_id)
    
    # Extract billing multiplier (None if unavailable)
    multiplier = _extract_multiplier(sdk_model)
    
    # Derive tier from multiplier (silent fallback to "standard")
    category = _get_tier_from_multiplier(multiplier)

    return TeamBotModelInfo(
        id=model_id, 
        name=name, 
        category=category, 
        multiplier=multiplier
    )
```

### 4.4 CachedModel Update

**File**: `src/teambot/config/model_cache.py` (Lines 25-37)

```python
@dataclass
class CachedModel:
    """Cached model information."""

    id: str
    name: str
    category: str
    multiplier: float | None = None  # ✅ NEW: optional for backward compat
```

### 4.5 Cache Load/Save Updates

**File**: `src/teambot/config/model_cache.py`

Update `load_cache()` (around line 115-121):
```python
models = [
    CachedModel(
        id=m["id"],
        name=m["name"],
        category=m["category"],
        multiplier=m.get("multiplier"),  # ✅ NEW: optional load
    )
    for m in data.get("models", [])
]
```

Update `save_cache()` (around line 154-162):
```python
if hasattr(m, "id"):
    model_dicts.append(
        {
            "id": m.id,
            "name": getattr(m, "name", m.id),
            "category": getattr(m, "category", "standard"),
            "multiplier": getattr(m, "multiplier", None),  # ✅ NEW
        }
    )
elif isinstance(m, dict):
    model_dicts.append(
        {
            "id": m.get("id", ""),
            "name": m.get("name", m.get("id", "")),
            "category": m.get("category", "standard"),
            "multiplier": m.get("multiplier"),  # ✅ NEW
        }
    )
```

### 4.6 Schema.py Updates

**File**: `src/teambot/config/schema.py`

Update `_ensure_models_loaded()` (around lines 42, 49, 166):
```python
_cached_models = {
    m.id: {
        "display": m.name, 
        "category": m.category,
        "multiplier": getattr(m, "multiplier", None),  # ✅ NEW
    } 
    for m in cache.models
}
```

### 4.7 /models Command Display Update

**File**: `src/teambot/repl/commands.py` (Lines 244-259)

```python
for model_id in models:
    info = get_model_info(model_id)
    if info:
        display_name = info.get("display", model_id)
        category = info.get("category", "standard")
        multiplier = info.get("multiplier")  # ✅ NEW
    else:
        display_name = model_id
        category = "standard"
        multiplier = None  # ✅ NEW
    categories.setdefault(category, []).append((model_id, display_name, multiplier))

# Update display loop:
for category in ["standard", "fast", "premium"]:
    if categories.get(category):
        lines.append(f"  {category.upper()}:")
        for model_id, display_name, multiplier in categories[category]:
            if multiplier is not None:
                lines.append(f"    {model_id:25} ({display_name}) [{multiplier}x]")
            else:
                lines.append(f"    {model_id:25} ({display_name})")
        lines.append("")
```

---

## 5. Testing Strategy Research

### 5.1 Existing Test Infrastructure

| Item | Value |
|------|-------|
| **Framework** | pytest 7.4+ with pytest-asyncio |
| **Test Location** | `tests/` directory (mirrors `src/` structure) |
| **Test Naming** | `test_*.py` pattern |
| **Runner** | `uv run pytest` |
| **Coverage Tool** | coverage.py |
| **Coverage Target** | 80% (current: ~80%, ~1050 tests) |

### 5.2 Relevant Test Files

| File | Purpose | Lines to Update |
|------|---------|-----------------|
| `tests/test_copilot/test_sdk_client.py` | Unit tests for `_adapt_model_info()` | Lines 1104-1178 |
| `tests/test_dynamic_model_discovery_acceptance.py` | Acceptance tests for `/models` | Lines 32-47 (fixtures), throughout |

### 5.3 Test Patterns Found

**File**: `tests/test_copilot/test_sdk_client.py` (Lines 1104-1178)

- Uses inner `MockModel` classes with attributes
- Uses `MockCapabilities` class with `tier` attribute (needs update to `MockBilling`)
- Tests fallback behavior for minimal models
- Tests warning logging via `caplog` fixture

**Example Pattern** (current test):
```python
def test_adapt_model_info_with_dict_capabilities(self):
    from teambot.copilot.sdk_client import CopilotSDKClient

    class MockModel:
        id = "test-model"
        name = "Test Model"
        capabilities = {"tier": "premium", "other": "value"}  # ❌ WRONG

    result = CopilotSDKClient._adapt_model_info(MockModel())
    assert result.category == "premium"
```

### 5.4 Test Updates Required

#### DELETE These Tests (No Longer Valid):
- `test_adapt_model_info_logs_warning_for_missing_tier` (line 1145)
- `test_adapt_model_info_logs_warning_for_invalid_tier` (line 1163)

#### UPDATE These Tests:
```python
def test_adapt_model_info_with_dict_billing(self):
    """Test _adapt_model_info handles dict billing."""
    from teambot.copilot.sdk_client import CopilotSDKClient

    class MockModel:
        id = "test-model"
        name = "Test Model"
        billing = {"multiplier": 5.0}  # ✅ Premium tier

    result = CopilotSDKClient._adapt_model_info(MockModel())
    assert result.id == "test-model"
    assert result.name == "Test Model"
    assert result.category == "premium"
    assert result.multiplier == 5.0


def test_adapt_model_info_with_object_billing(self):
    """Test _adapt_model_info handles object billing."""
    from teambot.copilot.sdk_client import CopilotSDKClient

    class MockBilling:
        multiplier = 0.25  # Fast tier

    class MockModel:
        id = "test-model"
        name = "Test Model"
        billing = MockBilling()

    result = CopilotSDKClient._adapt_model_info(MockModel())
    assert result.category == "fast"
    assert result.multiplier == 0.25


def test_adapt_model_info_minimal_no_warning(self, caplog):
    """Test _adapt_model_info silently defaults to standard."""
    import logging
    from teambot.copilot.sdk_client import CopilotSDKClient

    class MockModel:
        id = "test-model"

    with caplog.at_level(logging.WARNING):
        result = CopilotSDKClient._adapt_model_info(MockModel())

    assert result.category == "standard"
    assert result.multiplier is None
    assert "warning" not in caplog.text.lower()  # ✅ NO WARNING
    assert "missing" not in caplog.text.lower()
```

#### ADD New Boundary Tests:
```python
@pytest.mark.parametrize("multiplier,expected_tier", [
    (0.0, "fast"),
    (0.5, "fast"),      # boundary
    (0.51, "standard"), # boundary
    (1.0, "standard"),
    (1.5, "standard"),  # boundary
    (1.51, "premium"),  # boundary
    (5.0, "premium"),
    (None, "standard"),
    (-1.0, "standard"), # defensive
])
def test_adapt_model_info_tier_boundaries(self, multiplier, expected_tier):
    """Test tier mapping boundary values."""
    from teambot.copilot.sdk_client import CopilotSDKClient

    class MockBilling:
        pass
    
    class MockModel:
        id = "test-model"
        name = "Test"
        billing = None if multiplier is None else MockBilling()
    
    if multiplier is not None:
        MockModel.billing = MockBilling()
        MockModel.billing.multiplier = multiplier

    result = CopilotSDKClient._adapt_model_info(MockModel())
    assert result.category == expected_tier
```

### 5.5 Acceptance Test Updates

**File**: `tests/test_dynamic_model_discovery_acceptance.py`

Update `mock_sdk_models` fixture (lines 32-47):
```python
@pytest.fixture
def mock_sdk_models(self):
    """Create mock SDK model responses with all tiers."""
    from teambot.copilot.sdk_client import TeamBotModelInfo

    return [
        TeamBotModelInfo(id="gpt-5", name="GPT-5", category="standard", multiplier=1.0),
        TeamBotModelInfo(id="gpt-5-mini", name="GPT-5 Mini", category="fast", multiplier=0.25),
        TeamBotModelInfo(id="claude-opus-4.6", name="Claude Opus 4.6", category="premium", multiplier=5.0),
        TeamBotModelInfo(id="claude-sonnet-4.5", name="Claude Sonnet 4.5", category="standard", multiplier=1.0),
        TeamBotModelInfo(id="claude-haiku-4.5", name="Claude Haiku 4.5", category="fast", multiplier=0.3),
    ]
```

Add multiplier display test:
```python
@pytest.mark.asyncio
async def test_models_command_shows_multiplier(self, temp_teambot_dir, reset_schema_state, mock_sdk_models):
    """Verify /models command displays multiplier for each model."""
    from teambot.config.model_cache import save_cache
    from teambot.config.schema import reset_model_cache
    from teambot.repl.commands import handle_models

    with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
        save_cache(mock_sdk_models, "1.0.0")

    reset_model_cache()

    with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
        result = await handle_models([])

    # Verify multiplier display
    assert "[1.0x]" in result.output or "[1x]" in result.output
    assert "[5.0x]" in result.output or "[5x]" in result.output
    assert "[0.25x]" in result.output
```

### 5.6 Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `_extract_multiplier()` | Code-First | Simple extraction, low complexity |
| `_get_tier_from_multiplier()` | TDD | Boundary values critical, well-defined spec |
| `_adapt_model_info()` | Code-First then add tests | Rewrite of existing, test boundaries after |
| Cache updates | Code-First | Additive, backward compatible |
| `/models` display | Code-First | UI change, verify manually |

---

## 6. Implementation Checklist

### 6.1 Core Implementation (P0)

- [ ] Add `_extract_multiplier()` helper to `sdk_client.py`
- [ ] Add `_get_tier_from_multiplier()` helper to `sdk_client.py`
- [ ] Update `TeamBotModelInfo` dataclass with `multiplier` field
- [ ] Rewrite `_adapt_model_info()` to use billing.multiplier
- [ ] Remove warning logs for missing tier data

### 6.2 Cache Updates (P1)

- [ ] Update `CachedModel` dataclass with `multiplier` field
- [ ] Update `load_cache()` to read `multiplier`
- [ ] Update `save_cache()` to write `multiplier`
- [ ] Update `schema.py` to propagate `multiplier` to in-memory cache

### 6.3 Display Updates (P1)

- [ ] Update `handle_models()` to include multiplier in output
- [ ] Format: `{model_id:25} ({display_name}) [{multiplier}x]`
- [ ] Handle None multiplier gracefully (omit or show `[–]`)

### 6.4 Test Updates (P0)

- [ ] Delete warning tests (2 tests)
- [ ] Update `test_adapt_model_info_with_dict_capabilities` → billing
- [ ] Update `test_adapt_model_info_with_object_capabilities` → billing
- [ ] Update `test_adapt_model_info_minimal` → verify no warning
- [ ] Add parametrized boundary test
- [ ] Add multiplier extraction test
- [ ] Update acceptance test fixtures
- [ ] Add multiplier display acceptance test

### 6.5 Validation

- [ ] Run `uv run pytest` - all tests pass
- [ ] Run `uv run pytest --cov=src/teambot` - coverage maintained
- [ ] Run `uv run ruff check .` - no lint errors
- [ ] Manual test with real SDK (if available)

---

## 7. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SDK `billing` field changes | Low | Medium | Use defensive `getattr()` with None fallback |
| Old cache files break | Low | Low | `multiplier` field optional with default None |
| Multiplier boundaries shift | Low | Low | Consider config-based thresholds in future |
| Negative/extreme multipliers | Low | Low | Defensive handling returns "standard" |

---

## 8. Task Implementation Requests

### Task 1: Update TeamBotModelInfo and _adapt_model_info
**Priority**: P0  
**Files**: `src/teambot/copilot/sdk_client.py`  
**Scope**: Add `multiplier` field, add helper functions, rewrite adapter

### Task 2: Update Model Cache
**Priority**: P1  
**Files**: `src/teambot/config/model_cache.py`, `src/teambot/config/schema.py`  
**Scope**: Add multiplier to cache schema, update load/save

### Task 3: Update /models Command Display  
**Priority**: P1  
**Files**: `src/teambot/repl/commands.py`  
**Scope**: Show `[{multiplier}x]` suffix for each model

### Task 4: Update Tests
**Priority**: P0  
**Files**: `tests/test_copilot/test_sdk_client.py`, `tests/test_dynamic_model_discovery_acceptance.py`  
**Scope**: Delete obsolete tests, add new tests, update fixtures

---

## 9. Potential Next Research

*None - research is complete for this feature.*

---

## VALIDATION_STATUS: PASS

- Document: CREATED ✅
- Placeholders: 0 remaining ✅
- Technical Approach: DOCUMENTED ✅
- Entry Points: 3 traced, 3 covered ✅
- Test Infrastructure: RESEARCHED ✅
- Implementation Ready: YES ✅
