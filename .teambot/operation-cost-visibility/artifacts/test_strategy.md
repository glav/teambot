<!-- markdownlint-disable-file -->
# Test Strategy: Operation Cost Visibility

**Strategy Date**: 2026-03-03
**Feature Specification**: .teambot/operation-cost-visibility/artifacts/feature_spec.md
**Research Reference**: N/A (research phase pending SDK investigation)
**Strategist**: Test Strategy Agent (Builder-2)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | Points | Rationale |
|--------|----------|-------|--------|-----------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES | TDD +3 | 14 FRs with specific acceptance criteria; 6 AT scenarios defined |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM | TDD +1 | Aggregation logic is straightforward; data flow spans multiple layers |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | HIGH | TDD +3 | Must not crash workflows (NFR-002); graceful degradation critical |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO | Code-First +0 | Well-defined feature with clear deliverables |
| **Simplicity** | Is this straightforward CRUD or simple logic? | PARTIAL | Code-First +1 | Display layer is simple; data layer has complexity |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO | Code-First +0 | Quality > speed; testing preference is TDD |
| **Requirements Stability** | Are requirements likely to change during development? | MODERATE | Code-First +1 | SDK data availability unknown; may need adjustment |

### Decision Calculation

```
TDD Score: 3 + 1 + 3 = 7
Code-First Score: 0 + 1 + 0 + 1 = 2

Decision: TDD (score 7 > threshold 6)
```

## Recommended Testing Approach

**Primary Approach**: HYBRID (TDD-first with Code-First for display)

### Rationale

While the decision matrix recommends TDD (score 7), a **Hybrid** approach is optimal for this feature because it spans multiple architectural layers with different characteristics:

1. **Data Capture Layer** (TDD): Token extraction from SDK/CLI responses requires precise behavior validation. Tests must verify correct parsing, edge cases (None, partial data), and error handling. TDD ensures the data model contract is established before implementation.

2. **Tracking Layer** (TDD): Aggregation logic for per-agent, per-stage, and total tokens requires mathematical correctness. Tests define expected outcomes before implementation, catching off-by-one and accumulation errors early.

3. **Display Layer** (Code-First): Rich console formatting is visual and iterative. Testing exact string output is brittle; structural tests after implementation are more practical.

4. **Configuration Layer** (Code-First): Simple boolean config option follows established patterns in codebase; minimal testing needed.

**Key Factors:**
* Complexity: MEDIUM (aggregation logic straightforward, but multi-layer integration)
* Risk: HIGH (must not break existing workflows)
* Requirements Clarity: CLEAR (14 FRs with acceptance criteria)
* Time Pressure: LOW (quality emphasized)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: LOW - Token aggregation is simple summation; no complex algorithms
* **Integration Depth**: MEDIUM - Touches SDK client, task models, orchestrator, workflow state, and display
* **State Management**: MEDIUM - Token data accumulates across task executions; persists to workflow state
* **Error Scenarios**: MEDIUM - Graceful degradation for unavailable data; single warning pattern

### Risk Profile
* **Business Criticality**: MEDIUM - Informational feature; not blocking workflows
* **User Impact**: HIGH - All users will see token summaries; bad data misleads
* **Data Sensitivity**: LOW - Token counts contain no PII
* **Failure Cost**: HIGH - Any crash or workflow disruption is unacceptable per NFR-002

### Requirements Clarity
* **Specification Completeness**: COMPLETE - 14 FRs fully documented
* **Acceptance Criteria Quality**: PRECISE - Each FR has measurable acceptance
* **Edge Cases Identified**: 6 documented (partial data, disabled config, empty runs)
* **Dependencies Status**: SOME_VOLATILITY - SDK token data availability unconfirmed

## Test Strategy by Component

### 1. TokenUsage Data Model (FR-001) - TDD

**Approach**: TDD
**Rationale**: Data model is the foundation; tests define the contract before implementation

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Create TokenUsage with all fields populated
  * Create TokenUsage with all fields None (unavailable)
  * Create TokenUsage with partial data (prompt_tokens only)
  * Total calculation when prompt + completion available
* Edge Cases:
  * Zero tokens (valid state)
  * None vs 0 distinction
  * Serialization to/from JSON

**Testing Sequence** (TDD):
1. Write test for TokenUsage instantiation with full data
2. Implement dataclass with three optional int fields
3. Write test for partial data handling
4. Verify None propagates correctly
5. Add JSON serialization tests
6. Implement to_dict/from_dict methods

### 2. SDK Token Extraction (FR-002) - TDD

**Approach**: TDD
**Rationale**: Critical data path; behavior must be precisely defined before touching SDK client

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit (mocked SDK responses)
* Critical Scenarios:
  * Extract tokens when response contains usage data
  * Return None when response lacks usage data
  * Handle SDK response structure variations
* Edge Cases:
  * Response with usage.prompt_tokens only
  * Response with unexpected usage structure
  * SDK error responses

**Testing Sequence** (TDD):
1. Write test expecting TokenUsage from mock response with usage field
2. Implement extraction logic in sdk_client.py
3. Write test for missing usage field returning None
4. Implement graceful fallback
5. Write test for partial usage data
6. Implement partial data handling

### 3. CLI Token Extraction (FR-003) - TDD

**Approach**: TDD
**Rationale**: Parsing stdout/stderr requires well-defined patterns; tests prevent regressions

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Parse tokens from structured CLI output (if available)
  * Return None when CLI output lacks token data
* Edge Cases:
  * Malformed output parsing
  * Empty output

**Testing Sequence** (TDD):
1. Write test for expected CLI output format (research-dependent)
2. Implement regex/parsing logic
3. Write test for missing token info
4. Implement None return path

### 4. TaskResult Token Field (FR-004, FR-005) - TDD

**Approach**: TDD
**Rationale**: TaskResult is core data model; tests ensure backward compatibility

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * TaskResult with token_usage populated
  * TaskResult without token_usage (None)
  * Existing TaskResult instantiation unchanged
* Edge Cases:
  * Serialization includes token_usage
  * Old TaskResult JSON loads correctly (backward compat)

**Testing Sequence** (TDD):
1. Write test verifying existing TaskResult tests still pass
2. Add optional token_usage field
3. Write test for TaskResult with TokenUsage
4. Verify field propagates correctly
5. Write serialization test
6. Ensure JSON compat

### 5. Token Aggregation (FR-006, FR-007, FR-008) - TDD

**Approach**: TDD
**Rationale**: Aggregation correctness is critical; tests define expected mathematical outcomes

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Aggregate by agent_id across multiple tasks
  * Aggregate by stage across multiple tasks
  * Calculate total from all tasks
  * Handle None token_usage in aggregation
* Edge Cases:
  * Single task run (total = task tokens)
  * All tasks have None tokens
  * Mixed available/unavailable tokens
  * Empty task list

**Testing Sequence** (TDD):
1. Write test: 2 tasks with tokens → correct per-agent totals
2. Implement per-agent aggregation function
3. Write test: tasks across stages → correct per-stage totals
4. Implement per-stage aggregation
5. Write test: aggregate returns grand total
6. Implement total aggregation
7. Write test: tasks with None tokens handled correctly
8. Implement None-safe accumulation

### 6. Orchestration Summary Display (FR-009) - Code-First

**Approach**: Code-First
**Rationale**: Visual output is iterative; testing exact Rich formatting is brittle

**Test Requirements:**
* Coverage Target: 80%
* Test Types: Unit + Visual verification
* Critical Scenarios:
  * Display shows total tokens
  * Display shows per-agent breakdown
  * Display shows per-stage breakdown
* Edge Cases:
  * Display shows "n/a" when all tokens unavailable
  * Display handles zero tokens gracefully

**Testing Sequence** (Code-First):
1. Implement Rich panel with token data
2. Add structural test verifying panel contains expected sections
3. Add test for "n/a" display path
4. Visual verification via manual run

### 7. Interactive Session Tracking (FR-010, FR-011) - TDD

**Approach**: TDD
**Rationale**: Session accumulation logic must be precise; tests define expected behavior

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit + Integration
* Critical Scenarios:
  * Tokens accumulate across multiple commands
  * Summary displayed on /exit
  * Summary displayed on Ctrl+C
* Edge Cases:
  * Session with zero commands
  * Session where all commands return None tokens

**Testing Sequence** (TDD):
1. Write test: session tracker accumulates tokens
2. Implement session token tracking in REPL
3. Write test: /exit triggers summary display
4. Implement /exit hook
5. Write test: Ctrl+C triggers summary
6. Implement signal handler integration

### 8. Workflow State Persistence (FR-012) - TDD

**Approach**: TDD
**Rationale**: Schema compatibility is critical; tests define expected JSON structure

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Token data saved to metadata.token_tracking
  * Token data loaded from existing state
  * Schema version included
* Edge Cases:
  * Old state files without token_tracking load correctly
  * Corrupted token_tracking section handled

**Testing Sequence** (TDD):
1. Write test: save_state includes token_tracking in metadata
2. Implement metadata serialization
3. Write test: load_state reads token_tracking
4. Implement metadata deserialization
5. Write test: missing token_tracking defaults to empty
6. Implement backward-compatible loading

### 9. Graceful Degradation (FR-013) - TDD

**Approach**: TDD
**Rationale**: Error handling behavior must be precisely defined; tests ensure no crashes

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit + Integration
* Critical Scenarios:
  * Token extraction failure returns None, no exception
  * Warning logged once per run, not per task
  * Workflow continues normally when tokens unavailable
* Edge Cases:
  * First task fails extraction → warning logged
  * Second task fails extraction → no additional warning
  * Display shows "n/a" correctly

**Testing Sequence** (TDD):
1. Write test: extraction exception caught, returns None
2. Implement try/except wrapper
3. Write test: warning logged once only
4. Implement warning flag mechanism
5. Write integration test: full run with unavailable data completes
6. Verify no crashes

### 10. Configuration Option (FR-014) - Code-First

**Approach**: Code-First
**Rationale**: Simple boolean config follows established patterns; minimal tests needed

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Config `enabled: true` enables tracking (default)
  * Config `enabled: false` disables all tracking
* Edge Cases:
  * Missing config section defaults to enabled
  * Invalid config value handling

**Testing Sequence** (Code-First):
1. Implement config loading with default
2. Add test for default enabled behavior
3. Add test for disabled behavior
4. Add test for missing section default

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: Defined in pyproject.toml
* **Configuration**: `pyproject.toml [tool.pytest.ini_options]`
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (MagicMock, AsyncMock, patch) - established pattern
* **Assertions**: Built-in pytest assertions - no additional library needed
* **Coverage**: `pytest-cov` - target from pyproject.toml `--cov=src/teambot`
* **Async**: `pytest-asyncio` with `asyncio_mode = "auto"` - existing pattern
* **Test Data**: Fixtures in conftest.py - follow established pattern

### Test Organization
* **Test Location**: `tests/` directory
* **Naming Convention**: `test_*.py` files, `Test*` classes, `test_*` functions
* **Fixture Strategy**: Shared fixtures in `tests/conftest.py`, module-specific in `tests/test_*/conftest.py`
* **Setup/Teardown**: pytest fixtures with `tmp_path`, `tmp_teambot_dir`

### New Test Modules

| Module | Purpose |
|--------|---------|
| `tests/test_tokens/__init__.py` | Token tracking package tests |
| `tests/test_tokens/test_models.py` | TokenUsage dataclass tests |
| `tests/test_tokens/test_extraction.py` | SDK/CLI extraction tests |
| `tests/test_tokens/test_aggregation.py` | Aggregation logic tests |
| `tests/test_tokens/test_display.py` | Summary display tests |
| `tests/test_tokens/test_persistence.py` | Workflow state integration tests |
| `tests/test_token_tracking_acceptance.py` | Acceptance test scenarios (AT-001 through AT-006) |

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% (minimum for core token module)
* **Integration Coverage**: 80%
* **Critical Path Coverage**: 100% (graceful degradation, aggregation)
* **Error Path Coverage**: 95%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| TokenUsage model | 100% | N/A | CRITICAL | Foundation dataclass |
| SDK extraction | 95% | 80% | CRITICAL | Primary data source |
| CLI extraction | 90% | 70% | MEDIUM | May not have data |
| TaskResult integration | 95% | 90% | CRITICAL | Core model change |
| Aggregation logic | 95% | 90% | CRITICAL | Mathematical correctness |
| Display (orchestration) | 80% | 70% | HIGH | Visual output |
| Display (interactive) | 85% | 80% | HIGH | Session summary |
| State persistence | 95% | 90% | HIGH | Data durability |
| Graceful degradation | 100% | 95% | CRITICAL | Zero crashes |
| Configuration | 90% | 80% | LOW | Simple boolean |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Token Aggregation Accuracy** (Priority: CRITICAL)
   * **Description**: Sum of per-agent tokens equals total tokens
   * **Test Type**: Unit
   * **Success Criteria**: Mathematical equality: Σ(agent_tokens) == total
   * **Test Approach**: TDD

2. **Graceful Degradation - No Crashes** (Priority: CRITICAL)
   * **Description**: Workflow completes when token data unavailable
   * **Test Type**: Integration
   * **Success Criteria**: Exit code 0; no exceptions raised
   * **Test Approach**: TDD

3. **Single Warning Log** (Priority: HIGH)
   * **Description**: Token unavailable warning logged once, not per task
   * **Test Type**: Unit
   * **Success Criteria**: Log contains exactly one warning message
   * **Test Approach**: TDD

4. **Backward Compatibility** (Priority: HIGH)
   * **Description**: Old TaskResult/WorkflowState loads correctly
   * **Test Type**: Unit
   * **Success Criteria**: No exceptions; default values applied
   * **Test Approach**: TDD

5. **Display Shows N/A** (Priority: HIGH)
   * **Description**: When tokens unavailable, display shows "n/a"
   * **Test Type**: Unit
   * **Success Criteria**: Output contains "n/a" string
   * **Test Approach**: Code-First

6. **Config Disables Tracking** (Priority: MEDIUM)
   * **Description**: Setting `enabled: false` prevents all tracking
   * **Test Type**: Unit
   * **Success Criteria**: No token extraction called; no display shown
   * **Test Approach**: Code-First

### Edge Cases to Cover

* **Zero tokens**: Valid scenario where model reports 0 tokens consumed
* **Partial data**: Only prompt_tokens available, completion_tokens is None
* **Empty run**: Workflow with no agent executions (no tasks)
* **Single task**: Workflow with exactly one task
* **All None**: Every task returns None for token_usage
* **Mixed availability**: Some tasks have tokens, others don't

### Error Scenarios

* **SDK extraction exception**: Catch and return None, log debug
* **JSON serialization error**: Handle gracefully in persistence
* **Invalid config value**: Use default (enabled: true)
* **State file corruption**: Load with empty token_tracking

## Test Data Strategy

### Test Data Requirements
* **TokenUsage samples**: Pre-defined fixtures with known values for aggregation tests
* **Mock SDK responses**: Fixtures simulating Copilot SDK response.data structure
* **TaskResult samples**: Existing fixtures extended with token_usage
* **WorkflowState samples**: JSON fixtures for persistence tests

### Test Data Management
* **Storage**: Inline in test files; complex fixtures in conftest.py
* **Generation**: Factory fixtures (e.g., `mock_sdk_response`, `create_token_usage`)
* **Isolation**: Each test creates own data; no shared mutable state
* **Cleanup**: pytest `tmp_path` fixture handles cleanup automatically

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_tasks/test_models.py`
**Pattern**: Dataclass testing with status transitions

```python
class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_result_success(self):
        """Test successful result."""
        result = TaskResult(task_id="t1", output="Hello", success=True)

        assert result.task_id == "t1"
        assert result.output == "Hello"
        assert result.success is True
        assert result.error is None

    def test_result_failure(self):
        """Test failed result."""
        result = TaskResult(task_id="t1", output="", success=False, error="Timeout")

        assert result.success is False
        assert result.error == "Timeout"
```

**Key Conventions:**
* Class-based test organization (`Test*` prefix)
* Descriptive test names with `test_*` prefix
* Single assertion focus per test
* Docstring describes what's being tested

### Recommended Test Structure

```python
"""Tests for TokenUsage dataclass."""

import pytest


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_create_with_all_fields(self):
        """TokenUsage can be created with all fields populated."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )

        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_create_with_none_fields(self):
        """TokenUsage can be created with None fields (unavailable)."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage(
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
        )

        assert usage.prompt_tokens is None
        assert usage.completion_tokens is None
        assert usage.total_tokens is None

    def test_partial_data_allowed(self):
        """TokenUsage allows partial data (some fields populated)."""
        from teambot.tokens.models import TokenUsage

        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=None,
            total_tokens=None,
        )

        assert usage.prompt_tokens == 100
        assert usage.completion_tokens is None
```

### Acceptance Test Pattern

**File**: `tests/test_notification_acceptance.py` (reference)
**Pattern**: Real implementation with mocked external dependencies

```python
"""Acceptance tests for Operation Cost Visibility.

Core logic is tested directly; selective mocking is used only for
external dependencies (Copilot SDK responses).
"""

import pytest


class TestTokenTrackingAcceptanceScenarios:
    """Acceptance test scenarios for token tracking feature."""

    @pytest.mark.acceptance
    def test_at_001_orchestration_run_shows_token_summary(self, tmp_path):
        """AT-001: User runs orchestration and sees token summary.

        Validates:
        - Token summary panel displayed at end of run
        - Summary contains total tokens
        - Summary contains per-agent breakdown
        """
        # Test implementation...
```

## Success Criteria

### Test Implementation Complete When:
* [x] All critical scenarios have tests (6 defined above)
* [ ] Coverage targets are met per component (90%+ for core)
* [ ] All edge cases are tested (6 defined above)
* [ ] Error paths are validated (4 error scenarios)
* [ ] Tests follow codebase conventions (pytest, class-based)
* [ ] Tests are maintainable and clear
* [ ] CI/CD integration is working (`uv run pytest`)

### Test Quality Indicators:
* Tests are readable and self-documenting (docstrings required)
* Tests are fast and reliable (mock external dependencies)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem (specific assertions)
* Mock/stub usage is appropriate and minimal (only SDK/CLI responses)

## Implementation Guidance

### For TDD Components:
1. Start with simplest test case (TokenUsage with all fields)
2. Write minimal code to pass (dataclass definition)
3. Add next test case (partial data)
4. Refactor when all tests pass
5. Focus on behavior, not implementation

### For Code-First Components:
1. Implement core functionality (Rich panel display)
2. Add happy path test (verify panel sections exist)
3. Identify edge cases from implementation ("n/a" display)
4. Add edge case tests
5. Verify coverage meets target (80%)

### For Hybrid Approach:
1. Identify TDD vs Code-First boundaries clearly (documented above)
2. Start with TDD components (TokenUsage, extraction, aggregation)
3. Proceed to Code-First components (display, config)
4. Ensure integration tests cover boundaries
5. Validate overall feature behavior with acceptance tests

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD for core logic ensures correctness before implementation
* Code-First for display avoids brittle string-matching tests
* Comprehensive coverage targets catch regressions
* Acceptance tests validate user-facing behavior

### Accepted Trade-offs:
* Display tests may miss visual formatting issues (mitigated by manual verification)
* SDK extraction tests depend on assumed response structure (research-dependent)
* Higher test coverage requires more development time

### Risk Mitigation:
* Graceful degradation tests ensure feature doesn't break workflows
* Backward compatibility tests prevent data loss
* Single warning pattern tests prevent log spam

## References

* **Feature Spec**: [.teambot/operation-cost-visibility/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/operation-cost-visibility/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: `tests/test_tasks/test_models.py`, `tests/test_notification_acceptance.py`
* **Test Standards**: `pyproject.toml [tool.pytest.ini_options]`

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow recommended approach per component

---

**Strategy Status**: APPROVED
**Approved By**: USER (pending)
**Ready for Planning**: YES

---

## Validation

TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE (TDD=7, Code-First=2 → Hybrid recommended)
- Approach: HYBRID (TDD for core logic, Code-First for display)
- Coverage Targets: SPECIFIED (90% unit, 80% integration)
- Components Covered: 10/10
