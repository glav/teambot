<!-- markdownlint-disable-file -->
# Test Strategy: Dynamic Model Discovery

**Strategy Date**: 2026-02-16
**Feature Specification**: .teambot/dynamic-model-discovery/artifacts/feature_spec.md
**Spec Review Reference**: .teambot/dynamic-model-discovery/artifacts/spec_review.md
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: CODE_FIRST

### Rationale

This feature involves refactoring existing code to remove static fallback lists and enforce SDK-only model discovery. The changes are largely about removing code paths rather than introducing complex new algorithms. The requirements are well-defined but the implementation involves modifying existing behavior across multiple files, making it better suited to implement first and then verify through comprehensive tests.

The feature also involves error handling changes where the exact error message formats and user experience need to be observed during implementation. A code-first approach allows faster iteration on the error UX while ensuring test coverage validates the final behavior.

**Key Factors:**
* Complexity: MEDIUM (refactoring existing code, not new algorithms)
* Risk: HIGH (model validation affects entire TeamBot workflow)
* Requirements Clarity: CLEAR (detailed spec with 8 functional requirements)
* Time Pressure: LOW (no rushed deadline mentioned)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Assessment | TDD Points | Code-First Points |
|--------|------------|------------|-------------------|
| **Requirements Clarity** | YES - Clear acceptance criteria per FR | +3 | 0 |
| **Complexity** | MEDIUM - Refactoring not algorithm-heavy | +1 | 0 |
| **Risk Level** | HIGH - Model selection is critical path | +3 | 0 |
| **Exploratory Nature** | NO - Well-defined behavior changes | 0 | 0 |
| **Simplicity** | PARTIAL - Mostly removing code, updating interfaces | 0 | +1 |
| **Time Pressure** | LOW - No urgent deadline | 0 | 0 |
| **Requirements Stability** | STABLE - Spec approved, requirements frozen | 0 | 0 |

### Score Calculation

```
TDD Score: 3 + 1 + 3 = 7
Code-First Score: 1

Raw Decision: TDD (score 7 > threshold 6)
```

### Override Justification: CODE_FIRST

Despite TDD scoring higher, CODE_FIRST is recommended because:

1. **Existing test coverage is strong** - `test_schema.py` (19 tests), `test_model_cache.py` (14 tests), `test_sdk_client.py` (substantial coverage) already exist
2. **Feature is largely subtractive** - Removing fallback code paths is easier to verify after implementation
3. **Error message UX iteration** - The new error messages (FR-004) benefit from seeing them in action first
4. **Existing patterns to follow** - Tests for similar functionality already exist and should be extended

**Final Decision: CODE_FIRST** - Implement changes, then update/extend existing tests

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: LOW - No new algorithms, refactoring existing model resolution
* **Integration Depth**: MEDIUM - Touches sdk_client, schema, model_cache, and REPL commands
* **State Management**: MEDIUM - In-memory cache state, file-based cache persistence
* **Error Scenarios**: HIGH - Multiple SDK failure modes, cache corruption, timeout handling

### Risk Profile
* **Business Criticality**: HIGH - Model selection affects all agent interactions
* **User Impact**: MEDIUM - Affects `/models` command and model validation
* **Data Sensitivity**: LOW - Model metadata only, no user data
* **Failure Cost**: MEDIUM - Could block users if SDK unavailable and no cache

### Requirements Clarity
* **Specification Completeness**: COMPLETE - 8 FRs with detailed acceptance criteria
* **Acceptance Criteria Quality**: PRECISE - Measurable outcomes per requirement
* **Edge Cases Identified**: 6 documented (AT scenarios)
* **Dependencies Status**: STABLE - SDK API is established

## Test Strategy by Component

### Component 1: `schema.py` - SDK-Only Model Functions - CODE_FIRST

**Approach**: Code-First
**Rationale**: Existing tests cover current behavior; update tests after removing fallback paths

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * `get_available_models()` returns empty list when no cache and SDK unavailable
  * `validate_model()` returns False for all models when no data source
  * `get_model_info()` returns None when model not in cache
  * `refresh_models()` raises/logs error on SDK failure (no silent fallback)
* Edge Cases:
  * Expired cache with SDK failure (Open Question #1 - allow with warning)
  * Corrupted cache triggers SDK refresh attempt
  * Empty model list from SDK logs warning

**Testing Sequence** (Code-First):
1. Remove `_FALLBACK_MODELS` and `_FALLBACK_MODEL_INFO`
2. Update `_ensure_models_loaded()` to not use fallback
3. Run existing tests - expect failures for fallback behavior
4. Update tests to verify SDK-only behavior
5. Add new tests for error paths

### Component 2: `sdk_client.py` - Tier Extraction Fix - CODE_FIRST

**Approach**: Code-First
**Rationale**: Fix to `_adapt_model_info()` is straightforward; add targeted tests after

**Test Requirements:**
* Coverage Target: 85%
* Test Types: Unit
* Critical Scenarios:
  * `_adapt_model_info()` extracts tier from `capabilities.tier` (dataclass)
  * `_adapt_model_info()` extracts tier from `capabilities["tier"]` (dict)
  * Missing tier logs warning, uses `standard` for display only
  * `list_models()` returns empty list on SDK error
  * `list_models()` respects timeout (120s consistent with execute)
* Edge Cases:
  * `capabilities` is None
  * `capabilities.tier` is empty string
  * `capabilities.tier` is invalid value (not fast/standard/premium)

**Testing Sequence** (Code-First):
1. Implement tier extraction fix with logging
2. Add tests for various SDK response formats
3. Verify existing streaming tests still pass

### Component 3: `model_cache.py` - Cache Validation - CODE_FIRST

**Approach**: Code-First
**Rationale**: Add validation to existing save/load; extend current tests

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * `load_cache()` validates each model has `id`, `name`, `category`
  * Invalid entries are logged and skipped
  * Corrupted cache returns None (triggers SDK refresh)
  * Cache with missing fields treated as invalid
* Edge Cases:
  * Model with empty `id` field
  * Model with invalid `category` value
  * Cache file with extra unexpected fields (should not break)

**Testing Sequence** (Code-First):
1. Add validation logic to `load_cache()`
2. Run existing tests (should pass)
3. Add tests for validation edge cases

### Component 4: `commands.py` - `/models` Error Handling - CODE_FIRST

**Approach**: Code-First
**Rationale**: Error message formatting needs visual verification first

**Test Requirements:**
* Coverage Target: 80%
* Test Types: Unit + Integration
* Critical Scenarios:
  * `/models` with valid cache shows models and cache age
  * `/models` with no cache and no SDK shows error (not fallback)
  * `/models --refresh` success shows model count
  * `/models --refresh` failure shows actionable error message
  * Error messages follow Rich formatting pattern `[red]✗ ...[/red]`
* Edge Cases:
  * SDK timeout produces specific timeout message
  * Connection error shows "Check network connectivity"

**Testing Sequence** (Code-First):
1. Update `handle_models()` to remove fallback message
2. Add error handling for SDK-only failure case
3. Update `_handle_models_refresh()` error messages
4. Add/update tests for new error paths

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest (version via pyproject.toml)
* **Async Support**: pytest-asyncio with `asyncio_mode = "auto"`
* **Configuration**: pyproject.toml (lines 47-49)
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (AsyncMock, MagicMock, patch)
* **Assertions**: pytest built-in assertions
* **Coverage**: pytest-cov - Target: 80%+ (maintain existing)
* **Test Data**: Mock SDK responses, temporary cache files

### Test Organization
* **Test Location**: `tests/test_config/`, `tests/test_copilot/`, `tests/test_repl/`
* **Naming Convention**: `test_*.py` files, `test_*` functions
* **Fixture Strategy**: `conftest.py` with shared fixtures
* **Setup/Teardown**: pytest fixtures with `tmp_path`, `monkeypatch`

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 80% (minimum, maintain existing baseline)
* **Integration Coverage**: 70% (key user flows)
* **Critical Path Coverage**: 100% (model validation, error handling)
* **Error Path Coverage**: 90% (all SDK failure modes)

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `schema.py` | 90% | - | CRITICAL | Core model validation |
| `sdk_client.py` (`_adapt_model_info`) | 85% | - | HIGH | Tier extraction |
| `model_cache.py` | 90% | - | HIGH | Cache validation |
| `commands.py` (models) | 80% | 70% | MEDIUM | Error messages |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **SDK Failure with Empty Cache** (Priority: CRITICAL)
   * **Description**: User runs `/models` when SDK unavailable and no cache exists
   * **Test Type**: Integration
   * **Success Criteria**: Error message displayed, no fallback list shown
   * **Test Approach**: Code-First

2. **Tier Extraction from SDK** (Priority: CRITICAL)
   * **Description**: `_adapt_model_info()` correctly extracts tier from various response formats
   * **Test Type**: Unit
   * **Success Criteria**: Tier matches SDK `capabilities.tier` value
   * **Test Approach**: Code-First

3. **Model Validation Without Fallback** (Priority: CRITICAL)
   * **Description**: `validate_model()` returns False when no models available
   * **Test Type**: Unit
   * **Success Criteria**: No silent use of hardcoded list
   * **Test Approach**: Code-First

4. **Cache Validation on Load** (Priority: HIGH)
   * **Description**: Invalid cache entries are skipped with logging
   * **Test Type**: Unit
   * **Success Criteria**: Partial cache loaded, invalid entries logged
   * **Test Approach**: Code-First

5. **Expired Cache with SDK Failure** (Priority: HIGH)
   * **Description**: When cache expired and SDK fails, expired cache used with warning
   * **Test Type**: Integration
   * **Success Criteria**: Models displayed with warning about stale data
   * **Test Approach**: Code-First

6. **Premium Model Display** (Priority: HIGH)
   * **Description**: Premium tier models appear in correct section
   * **Test Type**: Unit
   * **Success Criteria**: Models with `category="premium"` under PREMIUM header
   * **Test Approach**: Code-First

### Edge Cases to Cover

* **Empty SDK response**: `list_models()` returns `[]`, logged as warning
* **SDK timeout**: Produces specific timeout error message
* **Cache with invalid tier**: Logged as warning, treated as standard
* **Model ID with whitespace**: `validate_model("  gpt-5  ")` handles trim
* **Concurrent cache access**: File locking not required (single-process)
* **Cache file permissions error**: Logged, treated as no cache

### Error Scenarios

* **SDKClientError on list_models**: Caught, logged, returns empty list (current behavior retained)
* **SDK not started**: `list_models()` returns empty list
* **Connection refused**: Wrapped in SDKClientError with clear message
* **Invalid JSON in cache**: Returns None, triggers SDK refresh
* **Missing cache directory**: Created on save, returns None on load

## Test Data Strategy

### Test Data Requirements
* **Mock SDK models**: List of `TeamBotModelInfo` objects with various tiers
* **Mock cache files**: JSON files with valid/invalid/expired timestamps
* **Mock SDK client**: AsyncMock for `list_models()`, `start()`, `stop()`

### Test Data Management
* **Storage**: Inline in test files or pytest fixtures
* **Generation**: Factory functions (`mock_sdk_response`, etc.)
* **Isolation**: `tmp_path` fixture for cache files
* **Cleanup**: Automatic via pytest fixture teardown

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_config/test_schema.py:121-153`
**Pattern**: Testing cached model discovery with mocked cache path

```python
def test_uses_cached_models_when_available(self, reset_model_state, tmp_path):
    """Test that cached models are used when cache is valid."""
    import json
    import time

    from teambot.config.schema import (
        get_available_models,
        reset_model_cache,
    )

    # Create mock cache
    cache_dir = tmp_path / ".teambot"
    cache_dir.mkdir()
    cache_file = cache_dir / "model_cache.json"
    cache_data = {
        "models": [
            {"id": "new-model-1", "name": "New Model 1", "category": "standard"},
            {"id": "new-model-2", "name": "New Model 2", "category": "premium"},
        ],
        "timestamp": time.time(),
        "sdk_version": "1.0.0",
    }
    cache_file.write_text(json.dumps(cache_data))

    reset_model_cache()

    with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
        models = get_available_models()

    assert "new-model-1" in models
    assert "new-model-2" in models
```

**Key Conventions:**
* Use `tmp_path` fixture for temporary directories
* Use `patch` to mock `Path.cwd()` for cache location
* Use `reset_model_cache()` to clear state between tests
* JSON files written directly for cache testing

### Recommended Test Structure

```python
class TestSDKOnlyModelDiscovery:
    """Tests for SDK-only model discovery (no fallback)."""

    @pytest.fixture
    def reset_model_state(self):
        """Reset model cache state between tests."""
        from teambot.config.schema import reset_model_cache
        reset_model_cache()
        yield
        reset_model_cache()

    def test_no_fallback_when_cache_missing(self, reset_model_state, tmp_path):
        """Verify empty list returned when no cache and SDK unavailable."""
        from teambot.config.schema import get_available_models, reset_model_cache
        
        reset_model_cache()
        
        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            models = get_available_models()
        
        # Should NOT contain fallback models
        assert "gpt-5" not in models
        assert models == []

    def test_validate_model_returns_false_when_no_data(self, reset_model_state, tmp_path):
        """Verify validate_model returns False for all when no data source."""
        from teambot.config.schema import reset_model_cache, validate_model
        
        reset_model_cache()
        
        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            # All models should be invalid when no source
            assert validate_model("gpt-5") is False
            assert validate_model("claude-opus-4.5") is False
```

## Success Criteria

### Test Implementation Complete When:
* [ ] All critical scenarios have tests (6 scenarios identified)
* [ ] Coverage targets are met per component (90%/85%/90%/80%)
* [ ] All edge cases are tested (6 edge cases)
* [ ] Error paths are validated (5 error scenarios)
* [ ] Tests follow codebase conventions (pytest, fixtures)
* [ ] Tests are maintainable and clear
* [ ] CI passes (`uv run pytest`)

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast and reliable (no flakiness)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem
* Mock/stub usage is appropriate and minimal

## Implementation Guidance

### For Code-First Components (All):

1. **Remove fallback code** from `schema.py`
2. **Run existing tests** - expect some failures for fallback behavior
3. **Update failing tests** to expect SDK-only behavior
4. **Add new tests** for error paths and edge cases
5. **Verify coverage** meets targets

### Specific Implementation Order:

1. **`sdk_client.py`** - Fix `_adapt_model_info()` tier extraction
   - Add logging for missing/invalid tier
   - Tests: Verify tier extraction variants

2. **`model_cache.py`** - Add cache validation
   - Validate `id`, `name`, `category` on load
   - Tests: Invalid cache handling

3. **`schema.py`** - Remove fallback lists
   - Delete `_FALLBACK_MODELS`, `_FALLBACK_MODEL_INFO`
   - Update `_ensure_models_loaded()` to not fallback
   - Tests: Update all affected tests

4. **`commands.py`** - Update error messages
   - Remove "Using fallback list" message
   - Add SDK error handling
   - Tests: Error message formatting

## Considerations and Trade-offs

### Selected Approach Benefits:
* Faster initial implementation pace
* Leverage existing test infrastructure
* Natural evolution of existing test patterns
* Error message UX can be iterated

### Accepted Trade-offs:
* Tests written after code may miss some edge cases initially
* Risk of testing implementation rather than behavior (mitigate with spec review)
* May need test updates as implementation evolves

### Risk Mitigation:
* Run existing tests frequently during implementation
* Use spec acceptance criteria as test oracles
* Review tests against AT scenarios before completion

## References

* **Feature Spec**: [.teambot/dynamic-model-discovery/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/dynamic-model-discovery/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: 
  - `tests/test_config/test_schema.py` - Model validation tests
  - `tests/test_config/test_model_cache.py` - Cache tests
  - `tests/test_copilot/test_sdk_client.py` - SDK client tests
  - `tests/test_repl/test_commands.py` - Command handler tests
* **Test Infrastructure**: `tests/conftest.py` - Shared fixtures

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow CODE_FIRST approach per component

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES
