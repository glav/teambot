<!-- markdownlint-disable-file -->

# Research Document: Dynamic Model Discovery

| Field | Value |
|-------|-------|
| **Research ID** | RES-DMD-001 |
| **Feature Spec** | `.teambot/dynamic-model-discovery/artifacts/feature_spec.md` |
| **Date** | 2026-02-16 |
| **Status** | Complete |

---

## 📋 Research Scope

### Objective
Deep technical research on replacing static model lists with SDK-exclusive dynamic model discovery in TeamBot.

### Research Questions
1. What are all entry points where model data is accessed?
2. How does the current fallback mechanism work?
3. What error handling patterns should be followed?
4. What SDK timeout patterns exist in the codebase?
5. What test patterns should be used?

### Success Criteria
- All entry points for model discovery identified and traced
- Technical approach for SDK-only discovery documented
- Error handling patterns documented with code examples
- Test strategy with existing patterns documented

---

## 🔍 Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Current Behavior | Change Required |
|-------------|-----------|------------------|-----------------|
| `/models` command | `commands.py:handle_models()` → `schema.py:get_available_models()` | Falls back to `_FALLBACK_MODELS` | YES - Remove fallback |
| `/models --refresh` | `commands.py:_handle_models_refresh()` → `schema.py:refresh_models()` | SDK query, falls back on failure | YES - Error on failure |
| `/model <agent> <model>` | `commands.py:handle_model()` → `schema.py:validate_model()` | Falls back to `_FALLBACK_MODELS` | YES - Remove fallback |
| `@agent --model <model>` | `parser.py` → `executor.py` → `schema.py:validate_model()` | Falls back to `_FALLBACK_MODELS` | YES - Remove fallback |
| Config load (`teambot.json`) | `loader.py:_validate_agent_model()` → `schema.py:validate_model()` | Falls back to `_FALLBACK_MODELS` | YES - Remove fallback |
| Config load (default_model) | `loader.py:_validate_default_model()` → `schema.py:validate_model()` | Falls back to `_FALLBACK_MODELS` | YES - Remove fallback |

### Code Path Trace

#### Entry Point 1: `/models` Command
1. User enters: `/models`
2. Handled by: `commands.py:handle_models()` (lines 209-270)
3. Calls: `schema.py:get_available_models()` (line 231)
4. `get_available_models()` → `_ensure_models_loaded()` → checks cache
5. If cache invalid: Falls back to `_FALLBACK_MODELS` ❌ **This is the problem**

#### Entry Point 2: `/models --refresh`
1. User enters: `/models --refresh`
2. Handled by: `commands.py:_handle_models_refresh()` (lines 273-296)
3. Calls: `schema.py:refresh_models()` (line 281)
4. `refresh_models()` → `CopilotSDKClient.list_models()` → `save_cache()`
5. On failure: Returns `False`, shows "Using cached/fallback list" ❌ **Should error**

#### Entry Point 3: `/model <agent> <model>`
1. User enters: `/model pm gpt-5`
2. Handled by: `commands.py:handle_model()` (lines 299-358)
3. Calls: `schema.py:validate_model()` (line 351)
4. `validate_model()` → `_ensure_models_loaded()` → checks cache
5. If cache empty: Falls back to `_FALLBACK_MODELS` ❌

#### Entry Point 4: Inline model (`@pm --model gpt-5`)
1. User enters: `@pm --model gpt-5 Create plan`
2. Parsed by: `parser.py:parse_input()` extracts model flag (lines 180-190)
3. Validated in: `executor.py` uses `schema.py:validate_model()`
4. Falls back to `_FALLBACK_MODELS` if cache empty ❌

#### Entry Point 5: Config validation
1. Config loaded: `loader.py:load_config()`
2. Agent model validated: `loader.py:_validate_agent_model()` (line 175)
3. Global default validated: `loader.py:_validate_default_model()` (line 196)
4. Both call: `schema.py:validate_model()`
5. Falls back to `_FALLBACK_MODELS` ❌

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| All entry points fall back to static list | Stale model data shown | Remove `_FALLBACK_MODELS` usage |
| Config validation during startup | May fail without cache | Need initial SDK query or graceful handling |
| Error handling returns `False` not error | Silent failures | Raise `SDKClientError` or return error result |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced (5 entry points)
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## 🏗️ Technical Approach

### Selected Approach: SDK-Only with Graceful Cache Fallback

**Rationale**: Following the feature spec, remove static fallback but allow expired cache usage with warning when SDK is unavailable.

### Architecture Changes

```
┌─────────────────────────────────────────────────────────────┐
│                      Entry Points                           │
│  /models  │  /model  │  @agent --model  │  config load     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    schema.py Functions                      │
│  get_available_models() │ validate_model() │ get_model_info()│
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  _ensure_models_loaded()                    │
│  1. Check in-memory cache                                   │
│  2. Load from disk cache (model_cache.py)                   │
│  3. If cache invalid → trigger SDK refresh                  │
│  4. If SDK fails → use expired cache with warning OR error  │
│  5. NO FALLBACK TO STATIC LIST                              │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│   model_cache.py    │       │   sdk_client.py     │
│  - load_cache()     │       │  - list_models()    │
│  - save_cache()     │       │  - _adapt_model_info│
│  - is_cache_valid() │       └─────────────────────┘
└─────────────────────┘
```

### File Changes Required

| File | Changes |
|------|---------|
| `src/teambot/config/schema.py` | Remove `_FALLBACK_MODELS`, `_FALLBACK_MODEL_INFO`; update `_ensure_models_loaded()`, `validate_model()`, `get_available_models()`, `get_model_info()` |
| `src/teambot/copilot/sdk_client.py` | Fix `_adapt_model_info()` tier extraction; add warning logging for missing tier |
| `src/teambot/config/model_cache.py` | Add cache validation on load; handle expired cache gracefully |
| `src/teambot/repl/commands.py` | Update `handle_models()` to show errors; remove "Using fallback list" message |

---

## 📂 Existing Code Patterns

### Error Handling Pattern (Rich Markup)
**Location**: `src/teambot/repl/loop.py` (lines 96-104)

```python
# Standard error pattern with actionable guidance
except SDKClientError as e:
    error_msg = str(e)
    if "timeout" in error_msg.lower():
        return (
            "[red]Request timed out.[/red]\n"
            "[yellow]This usually means Copilot is not authenticated.[/yellow]\n"
            "[dim]Run 'copilot' then '/login' to authenticate, or set GITHUB_TOKEN.[/dim]"
        )
    return f"[red]SDK Error: {e}[/red]"
```

### SDK Timeout Pattern
**Location**: `src/teambot/copilot/sdk_client.py` (line 314)

```python
async def execute(self, agent_id: str, prompt: str, timeout: float = 120.0) -> str:
    """Execute a prompt for a specific agent.
    
    The timeout parameter is kept for API compatibility but is not
    enforced when streaming is enabled.
    """
```

**Other timeout values in codebase**:
- `sdk_client.py:314` - `120.0` seconds (execute method)
- `sdk_client.py:479` - `1800.0` seconds (30 min streaming max)
- `client.py:33` - `300` seconds (5 min CLI timeout)
- `tasks/models.py:75` - `120.0` seconds (task default)
- `notifications/channels/telegram.py:68` - `30.0` seconds (HTTP client)

**Recommendation**: Use `120.0` seconds for model fetch (consistent with execute timeout).

### SDKClientError Usage
**Location**: `src/teambot/copilot/sdk_client.py` (lines 89-92)

```python
class SDKClientError(Exception):
    """Error raised by SDK client operations."""
    pass
```

**Raise patterns**:
```python
# Not available
raise SDKClientError("Copilot SDK not available - install github-copilot-sdk")

# Not started
raise SDKClientError("Client not started - call start() first")

# Timeout
raise SDKClientError(f"Request timed out after {timeout}s")

# Generic SDK error
raise SDKClientError(f"SDK error: {e}")
```

### Model Info Adaptation
**Location**: `src/teambot/copilot/sdk_client.py` (lines 551-573)

```python
@staticmethod
def _adapt_model_info(sdk_model: Any) -> TeamBotModelInfo:
    """Adapt SDK ModelInfo to TeamBot format."""
    model_id = getattr(sdk_model, "id", str(sdk_model))
    name = getattr(sdk_model, "name", model_id)

    # Extract category from capabilities.tier, defaulting to "standard"
    capabilities = getattr(sdk_model, "capabilities", None)
    if isinstance(capabilities, dict):
        category = capabilities.get("tier") or "standard"
    elif capabilities is not None:
        category = getattr(capabilities, "tier", None) or "standard"
    else:
        category = "standard"

    return TeamBotModelInfo(id=model_id, name=name, category=category)
```

**Issue**: Silently defaults to "standard" when tier is missing. Should log warning per spec.

### Cache Loading Pattern
**Location**: `src/teambot/config/model_cache.py` (lines 99-134)

```python
def load_cache() -> ModelCache | None:
    """Load model cache from disk."""
    cache_path = _get_cache_path()

    if not cache_path.exists():
        logger.debug(f"Cache file not found: {cache_path}")
        return None

    try:
        with cache_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # ... parse models
        return ModelCache(models=models, timestamp=timestamp, sdk_version=version)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Corrupted cache file, ignoring: {type(e).__name__}")
        return None
```

---

## 🧪 Testing Strategy Research

### Existing Test Infrastructure

| Item | Value |
|------|-------|
| **Framework** | pytest 7.x with pytest-asyncio |
| **Location** | `tests/` directory (mirrors `src/` structure) |
| **Naming** | `test_*.py` pattern |
| **Runner** | `uv run pytest` |
| **Coverage** | pytest-cov with 80% target |
| **Async Mode** | `asyncio_mode = "auto"` in pyproject.toml |

### Relevant Test Files

| File | Contents | Line Count |
|------|----------|------------|
| `tests/test_config/test_model_cache.py` | Cache save/load/TTL tests | 250 lines |
| `tests/test_copilot/test_sdk_client.py` | SDK client tests including `list_models()` | 1143 lines |
| `tests/test_repl/test_commands.py` | REPL command tests (if exists) | - |

### Test Patterns Found

**Pattern 1: Mock SDK Client** (`tests/test_copilot/test_sdk_client.py:1004-1042`)
```python
@pytest.mark.asyncio
async def test_list_models_returns_adapted_models(self):
    """Test list_models adapts SDK models to TeamBot format."""
    class MockSDKModel:
        def __init__(self, id, name, capabilities):
            self.id = id
            self.name = name
            self.capabilities = capabilities

    mock_sdk_models = [
        MockSDKModel("gpt-5", "GPT-5", {"tier": "standard"}),
        MockSDKModel("claude-opus-4.6", "Claude Opus 4.6", {"tier": "premium"}),
    ]

    with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
        mock_client = MagicMock()
        mock_client.list_models = AsyncMock(return_value=mock_sdk_models)
        # ... test assertions
```

**Pattern 2: Cache TTL Testing** (`tests/test_config/test_model_cache.py:74-90`)
```python
def test_cache_ttl_expiration(self, mock_cwd, temp_cache_dir):
    """Test cache expires after TTL."""
    from teambot.config.model_cache import is_cache_valid, CachedModel, ModelCache

    # Create cache that expired 1 hour ago
    old_timestamp = time.time() - (25 * 60 * 60)  # 25 hours ago
    cache = ModelCache(
        models=[CachedModel("gpt-5", "GPT-5", "standard")],
        timestamp=old_timestamp,
        sdk_version="1.0.0",
    )
    assert is_cache_valid(cache) is False
```

**Pattern 3: Monkeypatch Environment** (`tests/test_config/test_model_cache.py:110-137`)
```python
def test_cache_ttl_from_env_var(self, mock_cwd, temp_cache_dir, monkeypatch):
    """Test TTL can be configured via environment variable."""
    monkeypatch.setenv("TEAMBOT_MODEL_CACHE_TTL", "3600")
    # ... test with custom TTL
```

### Test Coverage Requirements

| Component | Existing Coverage | Required New Tests |
|-----------|-------------------|-------------------|
| `_adapt_model_info()` | 3 tests (dict, object, minimal) | +1 test for missing tier warning |
| `list_models()` | 4 tests | +1 test for timeout handling |
| `get_available_models()` | 0 direct tests | +3 tests (cache hit, SDK refresh, no data error) |
| `validate_model()` | Via config tests | +2 tests (valid from cache, invalid without data) |
| `handle_models()` | Minimal | +4 tests (normal, refresh success, refresh fail, no cache error) |

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `_adapt_model_info()` tier warning | Code-First | Simple addition, existing tests cover main logic |
| `get_available_models()` changes | TDD | Critical path, need to verify no fallback behavior |
| Error handling in `/models` | TDD | User-facing, need to verify error message format |
| `validate_model()` without fallback | Code-First | Behavior change is straightforward |
| Cache validation | Code-First | Extension of existing patterns |

---

## 📝 Implementation Guidance

### Step 1: Fix `_adapt_model_info()` Tier Extraction

**File**: `src/teambot/copilot/sdk_client.py` (lines 551-573)

**Changes**:
```python
@staticmethod
def _adapt_model_info(sdk_model: Any) -> TeamBotModelInfo:
    """Adapt SDK ModelInfo to TeamBot format."""
    model_id = getattr(sdk_model, "id", str(sdk_model))
    name = getattr(sdk_model, "name", model_id)

    # Extract category from capabilities.tier
    capabilities = getattr(sdk_model, "capabilities", None)
    category = None
    
    if isinstance(capabilities, dict):
        category = capabilities.get("tier")
    elif capabilities is not None:
        category = getattr(capabilities, "tier", None)
    
    # Log warning if tier missing, use "standard" for display only
    if not category:
        logger.warning(f"Model '{model_id}' missing tier in capabilities, using 'standard'")
        category = "standard"
    elif category not in ("fast", "standard", "premium"):
        logger.warning(f"Model '{model_id}' has invalid tier '{category}', using 'standard'")
        category = "standard"

    return TeamBotModelInfo(id=model_id, name=name, category=category)
```

### Step 2: Remove Static Fallbacks from `schema.py`

**File**: `src/teambot/config/schema.py`

**Remove** (lines 17-60):
```python
# Delete these entirely:
_FALLBACK_MODELS: set[str] = { ... }
_FALLBACK_MODEL_INFO: dict[str, dict[str, str]] = { ... }
VALID_MODELS = _FALLBACK_MODELS
MODEL_INFO = _FALLBACK_MODEL_INFO
```

**Update `_ensure_models_loaded()`** (lines 67-93):
```python
def _ensure_models_loaded() -> None:
    """Lazy load models from cache on first access.
    
    If cache is expired/missing, attempts SDK refresh.
    Raises SDKClientError if no models available.
    """
    global _models_loaded, _cached_models

    if _models_loaded:
        return

    from teambot.config.model_cache import is_cache_valid, load_cache

    cache = load_cache()
    if is_cache_valid(cache):
        _cached_models = {m.id: {"display": m.name, "category": m.category} for m in cache.models}
        _models_loaded = True
        logger.debug(f"Loaded {len(_cached_models)} models from cache")
        return

    # Cache expired or missing - try expired cache as fallback
    if cache and cache.models:
        _cached_models = {m.id: {"display": m.name, "category": m.category} for m in cache.models}
        _models_loaded = True
        logger.warning("Using expired cache - run '/models --refresh' to update")
        return

    # No cache at all - models will need to be fetched via refresh_models()
    _models_loaded = True  # Mark as loaded to prevent repeated attempts
    logger.warning("No model cache available - run '/models --refresh' to fetch models")
```

**Update `validate_model()`** (lines 95-121):
```python
def validate_model(model: str | None) -> bool:
    """Validate that a model name is supported by Copilot CLI."""
    if model is None or not isinstance(model, str):
        return False
    model = model.strip()
    if not model:
        return False

    _ensure_models_loaded()
    if _cached_models:
        return model in _cached_models
    
    # No models available - cannot validate
    logger.warning(f"Cannot validate model '{model}' - no models loaded")
    return False  # Fail validation if no model data available
```

**Update `get_available_models()`** (lines 124-136):
```python
def get_available_models() -> list[str]:
    """Get list of all available model names."""
    _ensure_models_loaded()
    if _cached_models:
        return sorted(_cached_models.keys())
    return []  # Return empty list, not fallback
```

**Update `get_model_info()`** (lines 139-151):
```python
def get_model_info(model: str) -> dict[str, str] | None:
    """Get display information for a model."""
    _ensure_models_loaded()
    if _cached_models and model in _cached_models:
        return _cached_models[model]
    return None  # No fallback
```

### Step 3: Update `/models` Command Error Handling

**File**: `src/teambot/repl/commands.py` (lines 209-270)

```python
async def handle_models(args: list[str]) -> CommandResult:
    """Handle /models command - list all available models."""
    if args and args[0] == "--refresh":
        return await _handle_models_refresh()

    models = get_available_models()
    
    # Handle no models available
    if not models:
        return CommandResult(
            output=(
                "[red]✗ No models available[/red]\n"
                "[yellow]Model cache is empty or expired.[/yellow]\n"
                "[dim]Run '/models --refresh' to fetch from SDK.[/dim]"
            ),
            success=False,
        )

    lines = ["Available Models:", ""]
    # ... rest of display logic (unchanged)
    
    # Remove the fallback message (line 263)
    # Delete: lines.append("  (Using fallback list - run /models --refresh to update)")
```

### Step 4: Update `/models --refresh` Error Handling

**File**: `src/teambot/repl/commands.py` (lines 273-296)

```python
async def _handle_models_refresh() -> CommandResult:
    """Handle /models --refresh to force cache update."""
    from teambot.config.schema import refresh_models

    try:
        success = await refresh_models()

        if success:
            count = len(get_available_models())
            return CommandResult(output=f"✓ Model cache refreshed: {count} models available.")
        else:
            return CommandResult(
                output=(
                    "[red]✗ Failed to refresh models[/red]\n"
                    "[dim]Check network connectivity and SDK installation.[/dim]\n"
                    "[dim]Run 'copilot --version' to verify SDK.[/dim]"
                ),
                success=False,
            )
    except Exception as e:
        return CommandResult(
            output=(
                f"[red]✗ Error refreshing models: {type(e).__name__}[/red]\n"
                "[dim]Run 'copilot --version' to verify SDK installation.[/dim]"
            ),
            success=False,
        )
```

---

## ⚠️ Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SDK unavailable at first use | Medium | High | Clear error message with steps to resolve |
| Config validation fails on fresh install | High | Medium | Allow validation to pass with warning, trigger lazy refresh |
| Breaking existing workflows | Low | Medium | Maintain API signatures, only change internal behavior |

### Config Validation Edge Case

**Issue**: If `teambot.json` specifies a `model` and cache is empty, validation will fail.

**Mitigation**: Update `loader.py` to allow unknown models with warning:
```python
def _validate_agent_model(self, agent_id: str, model: str | None) -> None:
    """Validate model if present."""
    if model is not None:
        if not validate_model(model):
            # Log warning instead of raising error if no cache
            if not is_using_cached_models():
                logger.warning(
                    f"Cannot validate model '{model}' for agent '{agent_id}' - "
                    "no model cache available. Run '/models --refresh' in REPL."
                )
            else:
                raise ConfigError(
                    f"Invalid model '{model}' for agent '{agent_id}'. "
                    f"Use '/models' command to see available models."
                )
```

---

## ✅ Task Implementation Requests

### High Priority (P0)

1. **Remove static fallback lists** from `schema.py`
   - Delete `_FALLBACK_MODELS` and `_FALLBACK_MODEL_INFO`
   - Delete `VALID_MODELS` and `MODEL_INFO` aliases
   - Update all dependent functions

2. **Update `_ensure_models_loaded()`** in `schema.py`
   - Allow expired cache usage with warning
   - Return empty state if no cache exists

3. **Update `handle_models()` and `_handle_models_refresh()`** in `commands.py`
   - Add proper error messages for no-models state
   - Remove "Using fallback list" message
   - Use consistent Rich markup pattern

4. **Add tier warning logging** in `_adapt_model_info()`
   - Log warning when tier is missing or invalid
   - Keep "standard" as display fallback

### Medium Priority (P1)

5. **Update config validation** in `loader.py`
   - Allow model validation to pass with warning when cache empty
   - Don't block startup if models can't be validated

6. **Add timeout to model fetch**
   - Use `120.0` seconds (consistent with execute timeout)
   - Produce specific timeout error message

### Lower Priority (P2)

7. **Add cache validation on load**
   - Validate required fields (id, name, category)
   - Skip invalid entries with warning

---

## 🔬 Potential Next Research

| Topic | Why | Priority |
|-------|-----|----------|
| SDK model list API details | Verify actual response format from production SDK | Low - current mock patterns match observed behavior |
| Performance impact | Measure first-access latency without cache | Low - async design mitigates blocking |

---

## 📚 References

### Internal Files
- Feature Spec: `.teambot/dynamic-model-discovery/artifacts/feature_spec.md`
- Current schema: `src/teambot/config/schema.py` (222 lines)
- SDK client: `src/teambot/copilot/sdk_client.py` (574 lines)
- Model cache: `src/teambot/config/model_cache.py` (232 lines)
- REPL commands: `src/teambot/repl/commands.py` (738 lines)
- Config loader: `src/teambot/config/loader.py` (lines 165-200)

### Test Files
- Cache tests: `tests/test_config/test_model_cache.py` (250 lines)
- SDK client tests: `tests/test_copilot/test_sdk_client.py` (1143 lines)

### Timeout Reference Values
- SDK execute: `120.0` seconds (`sdk_client.py:314`)
- Streaming max: `1800.0` seconds (`sdk_client.py:479`)
- CLI timeout: `300` seconds (`client.py:33`)
- Task default: `120.0` seconds (`tasks/models.py:75`)

---

## 📋 Research Validation

```
RESEARCH_VALIDATION: PASS
- Document: CREATED ✅
- Placeholders: 0 remaining ✅
- Technical Approach: DOCUMENTED ✅
- Entry Points: 5 traced, 5 covered ✅
- Test Infrastructure: RESEARCHED ✅
- Implementation Ready: YES ✅
```
