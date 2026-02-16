<!-- markdownlint-disable-file -->
# Implementation Details: Model Tier Classification Fix

**Research Reference**: `.teambot/model-tier-classification/artifacts/research.md`
**Test Strategy**: `.teambot/model-tier-classification/artifacts/test_strategy.md`
**Plan File**: `.agent-tracking/plans/20260216-model-tier-classification-plan.instructions.md`

---

## Phase 1: TDD Test Setup

### Task 1.1: Write Boundary Value Tests (Lines 28-70)

**File**: `tests/test_copilot/test_sdk_client.py`
**Location**: After line 1178 (end of current adapt tests)

Add parametrized test for all tier boundaries:

```python
@pytest.mark.parametrize("multiplier,expected_tier", [
    (0.0, "fast"),
    (0.25, "fast"),
    (0.5, "fast"),       # Upper boundary of fast
    (0.51, "standard"),  # Lower boundary of standard
    (1.0, "standard"),
    (1.5, "standard"),   # Upper boundary of standard
    (1.51, "premium"),   # Lower boundary of premium
    (5.0, "premium"),
    (100.0, "premium"),
    (-1.0, "standard"),  # Negative - defensive fallback
])
def test_adapt_model_info_tier_boundaries(self, multiplier, expected_tier):
    """Test tier mapping boundary values from billing.multiplier."""
    from teambot.copilot.sdk_client import CopilotSDKClient

    class MockBilling:
        pass

    class MockModel:
        id = "test-model"
        name = "Test Model"
        billing = MockBilling()

    MockModel.billing.multiplier = multiplier

    result = CopilotSDKClient._adapt_model_info(MockModel())
    assert result.category == expected_tier
    assert result.multiplier == multiplier
```

Add test for dict-style billing:

```python
def test_adapt_model_info_with_dict_billing(self):
    """Test _adapt_model_info handles dict billing."""
    from teambot.copilot.sdk_client import CopilotSDKClient

    class MockModel:
        id = "test-model"
        name = "Test Model"
        billing = {"multiplier": 5.0}

    result = CopilotSDKClient._adapt_model_info(MockModel())
    assert result.id == "test-model"
    assert result.name == "Test Model"
    assert result.category == "premium"
    assert result.multiplier == 5.0
```

### Task 1.2: Write Silent Fallback Test (Lines 72-95)

**File**: `tests/test_copilot/test_sdk_client.py`

Add test for silent fallback (no warning):

```python
def test_adapt_model_info_silent_fallback_no_warning(self, caplog):
    """Test that missing billing data defaults silently without warning."""
    import logging

    from teambot.copilot.sdk_client import CopilotSDKClient

    class MockModel:
        id = "test-model"
        name = "Test Model"
        # No billing attribute

    with caplog.at_level(logging.WARNING):
        result = CopilotSDKClient._adapt_model_info(MockModel())

    assert result.category == "standard"
    assert result.multiplier is None
    # Verify NO warning was logged
    assert "warning" not in caplog.text.lower()
    assert "missing" not in caplog.text.lower()
    assert "tier" not in caplog.text.lower()
```

### Task 1.3: Delete Obsolete Tests (Lines 97-112)

**File**: `tests/test_copilot/test_sdk_client.py`

Delete these test methods:
- `test_adapt_model_info_logs_warning_for_missing_tier` (lines 1145-1161)
- `test_adapt_model_info_logs_warning_for_invalid_tier` (lines 1163-1179)

Update `test_adapt_model_info_with_dict_capabilities` to use billing (lines 1104-1116):

```python
def test_adapt_model_info_with_dict_billing(self):
    """Test _adapt_model_info handles dict billing."""
    from teambot.copilot.sdk_client import CopilotSDKClient

    class MockModel:
        id = "test-model"
        name = "Test Model"
        billing = {"multiplier": 5.0}  # Premium tier

    result = CopilotSDKClient._adapt_model_info(MockModel())
    assert result.id == "test-model"
    assert result.name == "Test Model"
    assert result.category == "premium"
    assert result.multiplier == 5.0
```

Update `test_adapt_model_info_with_object_capabilities` to use billing (lines 1118-1131):

```python
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
```

---

## Phase 2: Core Implementation

### Task 2.1: Add Multiplier Field to TeamBotModelInfo (Lines 114-133)

**File**: `src/teambot/copilot/sdk_client.py`
**Location**: Lines 13-26

Replace dataclass:

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
    multiplier: float | None = None
```

**Backward Compatibility**: Field has default value, so existing code creating `TeamBotModelInfo(id=..., name=..., category=...)` continues to work.

### Task 2.2: Add Helper Functions (Lines 135-175)

**File**: `src/teambot/copilot/sdk_client.py`
**Location**: Add before `_adapt_model_info` method (around line 545)

Add these module-level helper functions:

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

### Task 2.3: Rewrite _adapt_model_info Method (Lines 177-195)

**File**: `src/teambot/copilot/sdk_client.py`
**Location**: Lines 551-581

Replace method:

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
        multiplier=multiplier,
    )
```

**Key Changes**:
- Removed `capabilities.tier` extraction (bug)
- Removed warning logs (spam)
- Added billing.multiplier extraction
- Returns multiplier in result

---

## Phase 3: Cache Updates

### Task 3.1: Update CachedModel Dataclass (Lines 197-215)

**File**: `src/teambot/config/model_cache.py`
**Location**: Lines 25-37

Replace dataclass:

```python
@dataclass
class CachedModel:
    """Cached model information.

    Attributes:
        id: Model identifier.
        name: Display name.
        category: Model tier (standard/fast/premium).
        multiplier: Billing multiplier (None if unavailable).
    """

    id: str
    name: str
    category: str
    multiplier: float | None = None
```

### Task 3.2: Update load_cache Function (Lines 217-235)

**File**: `src/teambot/config/model_cache.py`
**Location**: Lines 115-121

Replace models list comprehension:

```python
models = [
    CachedModel(
        id=m["id"],
        name=m["name"],
        category=m["category"],
        multiplier=m.get("multiplier"),  # NEW: optional load
    )
    for m in data.get("models", [])
]
```

### Task 3.3: Update save_cache Function (Lines 237-260)

**File**: `src/teambot/config/model_cache.py`
**Location**: Lines 156-171

Update object branch (lines 157-162):

```python
if hasattr(m, "id"):
    model_dicts.append(
        {
            "id": m.id,
            "name": getattr(m, "name", m.id),
            "category": getattr(m, "category", "standard"),
            "multiplier": getattr(m, "multiplier", None),  # NEW
        }
    )
```

Update dict branch (lines 164-171):

```python
elif isinstance(m, dict):
    model_dicts.append(
        {
            "id": m.get("id", ""),
            "name": m.get("name", m.get("id", "")),
            "category": m.get("category", "standard"),
            "multiplier": m.get("multiplier"),  # NEW
        }
    )
```

### Task 3.4: Update schema.py (Lines 262-280)

**File**: `src/teambot/config/schema.py`
**Location**: Lines 42 and 49

Update valid cache branch (line 42):

```python
_cached_models = {
    m.id: {
        "display": m.name,
        "category": m.category,
        "multiplier": getattr(m, "multiplier", None),  # NEW
    }
    for m in cache.models
}
```

Update expired cache branch (line 49):

```python
_cached_models = {
    m.id: {
        "display": m.name,
        "category": m.category,
        "multiplier": getattr(m, "multiplier", None),  # NEW
    }
    for m in cache.models
}
```

---

## Phase 4: Display Updates

### Task 4.1: Update handle_models Function (Lines 282-310)

**File**: `src/teambot/repl/commands.py`
**Location**: Lines 244-259

Update model info extraction (lines 244-252):

```python
for model_id in models:
    info = get_model_info(model_id)
    if info:
        display_name = info.get("display", model_id)
        category = info.get("category", "standard")
        multiplier = info.get("multiplier")  # NEW
    else:
        display_name = model_id
        category = "standard"
        multiplier = None  # NEW
    categories.setdefault(category, []).append((model_id, display_name, multiplier))
```

Update display loop (lines 254-259):

```python
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

### Task 4.2: Add Display Integration Test (Lines 312-330)

**File**: `tests/test_repl/test_commands.py` or `tests/test_dynamic_model_discovery_acceptance.py`

Add test for multiplier display:

```python
@pytest.mark.asyncio
async def test_handle_models_shows_multiplier(self, temp_teambot_dir, reset_schema_state):
    """Verify /models command displays multiplier for each model."""
    from unittest.mock import patch

    from teambot.config.model_cache import save_cache
    from teambot.config.schema import reset_model_cache
    from teambot.copilot.sdk_client import TeamBotModelInfo
    from teambot.repl.commands import handle_models

    mock_models = [
        TeamBotModelInfo(id="gpt-5", name="GPT-5", category="standard", multiplier=1.0),
        TeamBotModelInfo(id="gpt-5-mini", name="GPT-5 Mini", category="fast", multiplier=0.25),
        TeamBotModelInfo(id="claude-opus", name="Claude Opus", category="premium", multiplier=5.0),
    ]

    with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
        save_cache(mock_models, "1.0.0")

    reset_model_cache()

    with patch("teambot.config.model_cache.Path.cwd", return_value=temp_teambot_dir):
        result = await handle_models([])

    # Verify multiplier display
    assert "[1.0x]" in result.output or "[1x]" in result.output
    assert "[5.0x]" in result.output or "[5x]" in result.output
    assert "[0.25x]" in result.output
```

---

## Phase 5: Validation

### Task 5.1: Run Full Test Suite (Lines 332-345)

**Commands**:

```bash
# Run all tests
uv run pytest

# Run specific adapter tests
uv run pytest tests/test_copilot/test_sdk_client.py::TestCopilotSDKClient -v

# Run cache tests
uv run pytest tests/test_config/ -v -k cache

# Run command tests
uv run pytest tests/test_repl/ -v -k models
```

**Expected**: All tests pass

### Task 5.2: Verify Coverage (Lines 347-358)

**Command**:

```bash
uv run pytest --cov=src/teambot --cov-report=term-missing
```

**Expected**:
- `_extract_multiplier`: 100%
- `_get_tier_from_multiplier`: 100%
- `_adapt_model_info`: 100%
- Overall: 80%+

### Task 5.3: Run Linter (Lines 360-370)

**Commands**:

```bash
# Check for lint errors
uv run ruff check .

# Check formatting
uv run ruff format --check .

# Auto-fix if needed
uv run ruff format .
uv run ruff check . --fix
```

**Expected**: No errors

---

## Files Modified Summary

| File | Changes |
|------|---------|
| `src/teambot/copilot/sdk_client.py` | Add multiplier field, helper functions, rewrite adapter |
| `src/teambot/config/model_cache.py` | Add multiplier to CachedModel, update load/save |
| `src/teambot/config/schema.py` | Add multiplier to cached model dict |
| `src/teambot/repl/commands.py` | Display multiplier in /models output |
| `tests/test_copilot/test_sdk_client.py` | Delete 2 tests, add 4 new tests, update 3 tests |

---

## Success Criteria Verification

| Criterion | Verification Method |
|-----------|---------------------|
| No "missing tier" warnings | `caplog` test + manual log check |
| Correct tier classification | Boundary value tests |
| `/models` shows multiplier | Integration test + manual check |
| Tests pass | `uv run pytest` |
| Coverage maintained | `uv run pytest --cov=src/teambot` |
