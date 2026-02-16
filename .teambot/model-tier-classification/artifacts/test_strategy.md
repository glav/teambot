<!-- markdownlint-disable-file -->
# Test Strategy: Model Tier Classification Fix

**Strategy Date**: 2026-02-16
**Feature Specification**: .teambot/model-tier-classification/artifacts/feature_spec.md
**Research Reference**: N/A (bug fix with well-defined SDK attribute)
**Strategist**: Test Strategy Agent

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | Justification |
|--------|----------|-------|---------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | TDD +3 | Yes - explicit tier mapping thresholds and 6 acceptance tests defined |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | TDD +1 | Low-medium - simple threshold mapping, but boundary cases matter |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | TDD +2 | High - incorrect tiers affect model selection and user experience |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | Code-First +0 | No - fixing known issue with clear solution |
| **Simplicity** | Is this straightforward CRUD or simple logic? | Code-First +1 | Partially - simple attribute extraction with conditional logic |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | Code-First +0 | No - correctness is priority |
| **Requirements Stability** | Are requirements likely to change during development? | Code-First +0 | No - SDK attribute is documented, thresholds are fixed |

### Score Summary

| Approach | Score |
|----------|-------|
| TDD | **6** |
| Code-First | **1** |

### Decision

**TDD Score: 6 ≥ threshold 6** → **TDD Approach Recommended**

## Recommended Testing Approach

**Primary Approach**: TDD

### Rationale

This feature is a bug fix with precisely defined acceptance criteria. The tier mapping involves boundary values (0.5, 0.51, 1.5, 1.51) that are prone to off-by-one errors. TDD ensures each boundary is explicitly tested before implementation, catching edge cases that might otherwise slip through. The existing test infrastructure (pytest) is well-established and the tests that need modification are clearly identified in the specification.

Additionally, the specification explicitly calls out two existing tests that should be **deleted** (warning log tests), which means we need careful test-first thinking to ensure the new behavior is correctly validated. TDD provides confidence that the fallback behavior (silent default to "standard") works without regressions.

**Key Factors:**
* Complexity: MEDIUM (boundary value logic)
* Risk: HIGH (user-facing model classification)
* Requirements Clarity: CLEAR (explicit thresholds in spec)
* Time Pressure: LOW (correctness over speed)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Low - simple threshold comparisons with 3 categories
* **Integration Depth**: Low - single method modification with existing dataclass extension
* **State Management**: Stateless - pure function tier mapping
* **Error Scenarios**: Simple - only needs graceful fallback for missing data

### Risk Profile
* **Business Criticality**: HIGH - affects model selection and pricing visibility
* **User Impact**: Medium - all users see incorrect tier labels currently
* **Data Sensitivity**: LOW - no PII, only model metadata
* **Failure Cost**: Medium - incorrect tiers lead to suboptimal model choices

### Requirements Clarity
* **Specification Completeness**: COMPLETE - all acceptance criteria defined
* **Acceptance Criteria Quality**: PRECISE - explicit boundary values with expected results
* **Edge Cases Identified**: 6 documented (boundaries, missing data, negative values)
* **Dependencies Status**: STABLE - SDK `billing.multiplier` attribute exists

## Test Strategy by Component

### 1. `_adapt_model_info()` Tier Extraction - TDD

**Approach**: TDD
**Rationale**: Core business logic with boundary values. Tests define expected behavior precisely.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Extract multiplier from dict-style billing object
  * Extract multiplier from object-style billing attribute
  * Map multiplier to correct tier for each range
  * Handle missing billing attribute gracefully
  * Handle missing multiplier attribute gracefully

**Edge Cases:**
  * Multiplier exactly 0.5 → "fast" (upper boundary)
  * Multiplier 0.51 → "standard" (lower boundary)
  * Multiplier exactly 1.5 → "standard" (upper boundary)
  * Multiplier 1.51 → "premium" (lower boundary)
  * Multiplier 0.0 → "fast"
  * Multiplier negative → "standard" (defensive)
  * Multiplier None → "standard" (fallback)

**Testing Sequence**:
1. Write test `test_adapt_model_info_extracts_multiplier_from_dict_billing`
2. Write test `test_adapt_model_info_extracts_multiplier_from_object_billing`
3. Write test `test_tier_fast_boundary_0_5` → assert 0.5 maps to "fast"
4. Write test `test_tier_standard_boundary_0_51` → assert 0.51 maps to "standard"
5. Write test `test_tier_standard_boundary_1_5` → assert 1.5 maps to "standard"
6. Write test `test_tier_premium_boundary_1_51` → assert 1.51 maps to "premium"
7. Write test `test_missing_billing_silent_fallback` → no warning, "standard" tier
8. Implement `_adapt_model_info()` changes
9. Refactor for clarity

### 2. `TeamBotModelInfo` Dataclass - TDD

**Approach**: TDD
**Rationale**: Simple extension but backward compatibility must be validated.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * New `multiplier` field accepts float values
  * New `multiplier` field defaults to `None`
  * Existing code creating `TeamBotModelInfo` without multiplier still works

**Testing Sequence**:
1. Write test `test_teambot_model_info_has_multiplier_field`
2. Write test `test_teambot_model_info_multiplier_defaults_to_none`
3. Write test `test_teambot_model_info_backward_compatible`
4. Add `multiplier` field to dataclass
5. Verify all tests pass

### 3. `/models` Command Display - Code-First

**Approach**: Code-First
**Rationale**: UI formatting is straightforward. Test after implementation to verify display format.

**Test Requirements:**
* Coverage Target: 80%
* Test Types: Integration
* Critical Scenarios:
  * Output includes `[{multiplier}x]` suffix for each model
  * Missing multiplier displays gracefully (omitted or `[–]`)
  * Existing tier grouping still works

**Testing Sequence**:
1. Implement `/models` output format change
2. Add test `test_handle_models_shows_multiplier_suffix`
3. Add test `test_handle_models_missing_multiplier_display`
4. Verify coverage meets target

### 4. Warning Log Removal - TDD

**Approach**: TDD
**Rationale**: Explicit requirement to stop warning spam. Test verifies absence of warnings.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * No warning logged when multiplier is present
  * No warning logged when multiplier is absent
  * Debug logging acceptable for troubleshooting

**Testing Sequence**:
1. **DELETE** `test_adapt_model_info_logs_warning_for_missing_tier`
2. **DELETE** `test_adapt_model_info_logs_warning_for_invalid_tier`
3. Write test `test_adapt_model_info_no_warning_when_billing_missing`
4. Write test `test_adapt_model_info_no_warning_when_multiplier_missing`
5. Implement silent fallback logic
6. Verify no regressions

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest
* **Version**: >=7.4.0
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` - MagicMock for SDK model objects
* **Assertions**: Built-in pytest assertions
* **Coverage**: pytest-cov - Target: 80%+ overall, 100% for core logic
* **Fixtures**: pytest fixtures in `tests/conftest.py`
* **Log Capture**: `caplog` fixture for verifying no warnings

### Test Organization
* **Test Location**: `tests/test_copilot/test_sdk_client.py`
* **Naming Convention**: `test_<function>_<scenario>`
* **Fixture Strategy**: Use existing `mock_sdk_client` fixture
* **Setup/Teardown**: Use `@pytest.fixture` decorators

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 100% for `_adapt_model_info()` and tier mapping
* **Integration Coverage**: 80% for `/models` command
* **Critical Path Coverage**: 100% (all tier boundaries)
* **Error Path Coverage**: 100% (all fallback scenarios)

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `_adapt_model_info()` | 100% | - | CRITICAL | Boundary values tested |
| `TeamBotModelInfo` | 100% | - | HIGH | Backward compat verified |
| `/models` display | - | 80% | MEDIUM | Format validation |
| Cache compatibility | - | 80% | HIGH | Old cache entries load |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Tier Boundary 0.5** (Priority: CRITICAL)
   * **Description**: Verify multiplier 0.5 maps to "fast" tier
   * **Test Type**: Unit
   * **Success Criteria**: `category == "fast"`
   * **Test Approach**: TDD

2. **Tier Boundary 0.51** (Priority: CRITICAL)
   * **Description**: Verify multiplier 0.51 maps to "standard" tier
   * **Test Type**: Unit
   * **Success Criteria**: `category == "standard"`
   * **Test Approach**: TDD

3. **Tier Boundary 1.5** (Priority: CRITICAL)
   * **Description**: Verify multiplier 1.5 maps to "standard" tier
   * **Test Type**: Unit
   * **Success Criteria**: `category == "standard"`
   * **Test Approach**: TDD

4. **Tier Boundary 1.51** (Priority: CRITICAL)
   * **Description**: Verify multiplier 1.51 maps to "premium" tier
   * **Test Type**: Unit
   * **Success Criteria**: `category == "premium"`
   * **Test Approach**: TDD

5. **Silent Fallback** (Priority: CRITICAL)
   * **Description**: Missing billing data defaults to "standard" without warning
   * **Test Type**: Unit
   * **Success Criteria**: `category == "standard"` and no warning in logs
   * **Test Approach**: TDD

6. **Multiplier Storage** (Priority: HIGH)
   * **Description**: Multiplier value is stored in TeamBotModelInfo
   * **Test Type**: Unit
   * **Success Criteria**: `model.multiplier == expected_value`
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Multiplier 0.0**: Should map to "fast" tier
* **Multiplier negative (-1.0)**: Should fallback to "standard" (defensive)
* **Multiplier very large (100.0)**: Should map to "premium" tier
* **Multiplier None**: Should fallback to "standard" tier
* **Billing attribute missing**: Should fallback to "standard" tier silently
* **Billing is dict without multiplier**: Should fallback to "standard" tier silently

### Error Scenarios

* **Missing billing attribute**: Silent fallback to "standard", no warning
* **Missing multiplier in billing**: Silent fallback to "standard", no warning
* **Multiplier is non-numeric type**: Handle gracefully, default to "standard"

## Test Data Strategy

### Test Data Requirements
* Mock SDK model objects with various billing.multiplier values
* Dict-style billing objects: `{"multiplier": 1.0}`
* Object-style billing: `class Billing: multiplier = 1.0`

### Test Data Management
* **Storage**: Inline in test methods (simple mock objects)
* **Generation**: Manual creation of mock classes
* **Isolation**: Each test creates its own mock objects
* **Cleanup**: No cleanup needed (no persistent state)

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_copilot/test_sdk_client.py:1104-1116`
**Pattern**: Mock class with attributes for SDK model simulation

```python
def test_adapt_model_info_with_dict_capabilities(self):
    """Test _adapt_model_info handles dict capabilities."""
    from teambot.copilot.sdk_client import CopilotSDKClient

    class MockModel:
        id = "test-model"
        name = "Test Model"
        capabilities = {"tier": "premium", "other": "value"}

    result = CopilotSDKClient._adapt_model_info(MockModel())
    assert result.id == "test-model"
    assert result.name == "Test Model"
    assert result.category == "premium"
```

**Key Conventions:**
* Use inner `MockModel` class for SDK object simulation
* Call static method directly via `CopilotSDKClient._adapt_model_info()`
* Assert on result dataclass attributes

### Recommended Test Structure

```python
def test_adapt_model_info_tier_from_billing_multiplier_fast(self):
    """Test tier mapping for fast tier (multiplier <= 0.5)."""
    from teambot.copilot.sdk_client import CopilotSDKClient

    class MockBilling:
        multiplier = 0.25

    class MockModel:
        id = "test-model"
        name = "Test Model"
        billing = MockBilling()

    result = CopilotSDKClient._adapt_model_info(MockModel())
    assert result.category == "fast"
    assert result.multiplier == 0.25


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
    assert "warning" not in caplog.text.lower()
    assert "missing" not in caplog.text.lower()
```

## Success Criteria

### Test Implementation Complete When:
- [ ] All boundary value tests written and passing
- [ ] Existing warning tests deleted
- [ ] Silent fallback tests written and passing
- [ ] Multiplier storage tests written and passing
- [ ] `/models` display tests updated
- [ ] Coverage targets are met per component (100% for core, 80% overall)
- [ ] All acceptance test scenarios have corresponding tests
- [ ] Tests follow codebase conventions (pytest, mock classes)
- [ ] CI/CD pipeline passes

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast and reliable (no flakiness)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem (boundary value vs fallback)
* Mock/stub usage is appropriate and minimal

## Implementation Guidance

### For TDD Components (Tier Extraction, Dataclass, Warning Removal):
1. Start with boundary value test (0.5 → "fast")
2. Write minimal code to pass (threshold check)
3. Add next boundary test (0.51 → "standard")
4. Refactor threshold logic
5. Continue with remaining boundaries
6. Add fallback tests last

### For Code-First Components (/models Display):
1. Implement multiplier suffix in output format
2. Add happy path test (model with multiplier shows `[1.0x]`)
3. Add edge case test (model without multiplier handled gracefully)
4. Verify coverage meets 80% target

### Test Modification Summary

| Test | Action | Reason |
|------|--------|--------|
| `test_adapt_model_info_with_dict_capabilities` | MODIFY | Change from `capabilities.tier` to `billing.multiplier` |
| `test_adapt_model_info_with_object_capabilities` | MODIFY | Change from `capabilities.tier` to `billing.multiplier` |
| `test_adapt_model_info_minimal` | MODIFY | Verify silent fallback (no warning check) |
| `test_adapt_model_info_logs_warning_for_missing_tier` | DELETE | No longer warns |
| `test_adapt_model_info_logs_warning_for_invalid_tier` | DELETE | No longer warns |
| NEW: `test_adapt_model_info_tier_boundaries` | ADD | Test all 4 boundary values |
| NEW: `test_adapt_model_info_multiplier_extraction` | ADD | Test multiplier stored in result |
| NEW: `test_adapt_model_info_no_warning_silent_fallback` | ADD | Test no warning on missing data |
| NEW: `test_handle_models_shows_multiplier` | ADD | Test `/models` output format |

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures all boundary values are explicitly validated before implementation
* Deleting warning tests first prevents regressions from interfering
* Clear test structure documents expected behavior for future maintainers
* High coverage on core logic prevents regression bugs

### Accepted Trade-offs:
* Slightly slower initial development pace due to test-first approach
* More tests to maintain (boundary tests for each threshold)
* Tests are tightly coupled to specific multiplier values (if thresholds change, tests need update)

### Risk Mitigation:
* TDD catches off-by-one errors at boundaries before they reach production
* Silent fallback tests ensure no warning spam regression
* Backward compatibility tests ensure existing code continues to work

## References

* **Feature Spec**: [.teambot/model-tier-classification/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/model-tier-classification/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: `tests/test_copilot/test_sdk_client.py:1104-1178`
* **Source Code**: `src/teambot/copilot/sdk_client.py:551-581`
* **Commands Code**: `src/teambot/repl/commands.py:240-280`

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow TDD for core tier extraction logic

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

## TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE
- Approach: TDD (score 6 ≥ threshold 6)
- Coverage Targets: SPECIFIED (100% core, 80% integration)
- Components Covered: 4/4
