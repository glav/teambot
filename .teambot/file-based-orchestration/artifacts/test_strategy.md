<!-- markdownlint-disable-file -->
# Test Strategy: File-Based Orchestration Critical Failure Handling

**Strategy Date**: 2026-02-25
**Feature Specification**: .teambot/file-based-orchestration/artifacts/feature_spec.md
**Specification Review Reference**: .teambot/file-based-orchestration/artifacts/spec_review.md
**Strategist**: Builder-2 (Test Strategy Agent)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Assessment | TDD Points | Code-First Points |
|--------|----------|------------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES - 8 FRs with detailed acceptance criteria, 7 AT scenarios | 3 | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | HIGH - Multiple validation paths, state machine integration, notification routing | 3 | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | CRITICAL - Safety mechanism to prevent wasted time/API costs | 3 | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO - Well-defined requirements, existing patterns to follow | 0 | 0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | NO - Multiple components, state transitions, notification integration | 0 | 0 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO - User explicitly requested TDD approach | 0 | 0 |
| **Requirements Stability** | Are requirements likely to change during development? | NO - Spec approved with 9/10 completeness score | 0 | 0 |

### Decision Calculation

```
TDD Score: 9 (Requirements Clarity: 3 + Complexity: 3 + Risk Level: 3)
Code-First Score: 0

Decision: TDD (score 9 ≥ threshold 6)
```

## Recommended Testing Approach

**Primary Approach**: TDD (Test-Driven Development)

### Rationale

This feature implements critical safety mechanisms for TeamBot's file-based orchestration. Missing artifact validation is a fail-fast safety feature where incorrect behavior (silent continuation) causes wasted time, API costs, and user confusion. TDD is the optimal approach because:

1. **Clear Requirements**: The specification includes 8 functional requirements with explicit acceptance criteria and 7 detailed acceptance test scenarios (AT-001 through AT-007). This level of clarity makes writing tests first natural and efficient.

2. **High Risk, High Visibility**: This is the exact type of feature where TDD excels—catching edge cases early prevents the feature that prevents silent failures from itself failing silently.

3. **User Preference**: The objective explicitly states "TDD - these are critical safety mechanisms that must be thoroughly tested before implementation."

**Key Factors:**
* Complexity: HIGH (validation logic, state machine integration, notification routing, path resolution)
* Risk: CRITICAL (safety mechanism - must not fail silently)
* Requirements Clarity: CLEAR (8 FRs, 7 ATs, detailed templates in appendix)
* Time Pressure: LOW (quality over speed for safety features)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: MEDIUM - Artifact path resolution with multiple search locations, pattern matching
* **Integration Depth**: HIGH - Integrates with ExecutionLoop, EventBus, orchestration state, notification channels
* **State Management**: MEDIUM - Extends orchestration_state.json with failure_reason, status transitions
* **Error Scenarios**: HIGH - Multiple failure modes (missing file, wrong path, lookup failure, notification failure)

### Risk Profile
* **Business Criticality**: CRITICAL - Prevents wasted time and API costs
* **User Impact**: HIGH - All TeamBot users affected when workflows fail
* **Data Sensitivity**: LOW - File paths and stage names only (no PII)
* **Failure Cost**: HIGH - If validation fails silently, defeats entire feature purpose

### Requirements Clarity
* **Specification Completeness**: COMPLETE (9/10 per review)
* **Acceptance Criteria Quality**: PRECISE (7 detailed AT scenarios)
* **Edge Cases Identified**: 4+ documented (path normalization, unicode, resume scenarios)
* **Dependencies Status**: STABLE (EventBus, orchestration_state.json patterns established)

## Test Strategy by Component

### 1. Artifact Validator (FR-001, FR-008) - TDD

**Approach**: TDD
**Rationale**: Core safety logic with clear inputs/outputs. Validation rules are well-defined in spec.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Required artifact exists → validation passes
  * Required artifact missing → validation fails with structured error
  * Optional artifact missing → validation passes (no regression)
  * Multiple required artifacts, one missing → fails immediately
  * Path normalization (hyphens, case) → consistent lookup
* Edge Cases:
  * Unicode characters in artifact names
  * Symlinks to artifacts
  * Empty artifact files (should exist-check pass)
  * Artifact directory doesn't exist

**Testing Sequence (TDD):**
1. Test: `test_validate_passes_when_artifact_exists`
2. Test: `test_validate_fails_when_required_artifact_missing`
3. Test: `test_validate_returns_structured_error_with_path_and_stage`
4. Test: `test_validate_distinguishes_required_vs_optional`
5. Implement: `ArtifactValidator.validate_stage_artifacts()`

### 2. Error Message Formatter (FR-002) - TDD

**Approach**: TDD
**Rationale**: Template-based output with strict format requirements. Easy to test-first.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Error message contains artifact path
  * Error message contains requiring stage
  * Error message contains creating stage
  * Error message contains resolution guidance
  * Error message format matches template in spec appendix
* Edge Cases:
  * Long artifact paths (wrapping/truncation)
  * Stage names with underscores

**Testing Sequence (TDD):**
1. Test: `test_error_message_contains_artifact_path`
2. Test: `test_error_message_contains_stage_names`
3. Test: `test_error_message_contains_resolution_guidance`
4. Test: `test_error_message_matches_template_format`
5. Implement: `format_missing_artifact_error()`

### 3. Critical Failure Notification (FR-003) - TDD

**Approach**: TDD
**Rationale**: Extends existing EventBus patterns. Clear event type and payload requirements.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit + Integration
* Critical Scenarios:
  * `critical_failure` event emitted on validation failure
  * Event payload contains required fields (artifact_path, stage, expected_from_stage, feature_name)
  * Telegram channel receives notification
  * Notification template renders correctly
* Edge Cases:
  * EventBus not configured → graceful degradation
  * Notification send fails → logged, doesn't block

**Testing Sequence (TDD):**
1. Test: `test_critical_failure_event_emitted_on_missing_artifact`
2. Test: `test_critical_failure_event_payload_contains_required_fields`
3. Test: `test_telegram_template_renders_critical_failure`
4. Implement: Add `critical_failure` event type and template

### 4. Failure State Persistence (FR-004) - TDD

**Approach**: TDD
**Rationale**: Extends existing `_save_state()` pattern. Clear schema extension.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * State saved with `status: "failed"`
  * State includes `failure_reason` field
  * Failure reason contains artifact details
  * Existing state fields preserved
* Edge Cases:
  * Write permission denied → exception handling
  * Concurrent state writes

**Testing Sequence (TDD):**
1. Test: `test_save_state_sets_status_failed_on_validation_failure`
2. Test: `test_save_state_includes_failure_reason`
3. Test: `test_failure_reason_contains_artifact_details`
4. Implement: Extend `ExecutionLoop._save_state()` with failure_reason

### 5. Resume After Failure (FR-005) - TDD

**Approach**: TDD
**Rationale**: Critical user journey. Must validate before continuing.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit + Integration
* Critical Scenarios:
  * Resume re-validates artifacts before continuing
  * Resume succeeds when artifact now exists
  * Resume fails again if artifact still missing
  * Resume clears previous failure_reason on success
* Edge Cases:
  * Resume from different stage than failure stage
  * Multiple artifacts required, only some fixed

**Testing Sequence (TDD):**
1. Test: `test_resume_validates_artifacts_before_continuing`
2. Test: `test_resume_succeeds_when_artifact_now_exists`
3. Test: `test_resume_fails_if_artifact_still_missing`
4. Implement: Extend `ExecutionLoop.resume()` with pre-validation

### 6. Unified Artifact Path Resolver (FR-006) - TDD

**Approach**: TDD
**Rationale**: Single source of truth. Must handle all edge cases consistently.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Resolves artifact in `.teambot/{feature}/artifacts/`
  * Resolves artifact in `docs/feature-specs/`
  * Returns first found location
  * Returns None with search locations when not found
  * Consistent path normalization (hyphens, case)
* Edge Cases:
  * Feature name with spaces
  * Feature name with unicode
  * Nested artifact paths
  * Relative vs absolute paths

**Testing Sequence (TDD):**
1. Test: `test_resolver_finds_artifact_in_teambot_dir`
2. Test: `test_resolver_finds_artifact_in_docs_dir`
3. Test: `test_resolver_returns_first_match`
4. Test: `test_resolver_normalizes_paths_consistently`
5. Test: `test_resolver_returns_none_with_searched_locations`
6. Implement: `UnifiedArtifactResolver.resolve()`

### 7. Diagnostic Logging (FR-007) - TDD

**Approach**: TDD
**Rationale**: Observable behavior via log capture. Easy to test.

**Test Requirements:**
* Coverage Target: 85%
* Test Types: Unit
* Critical Scenarios:
  * Debug log includes paths searched
  * Debug log includes patterns tried
  * Debug log includes files found
  * Logging doesn't affect return value
* Edge Cases:
  * Logging disabled → no exception

**Testing Sequence (TDD):**
1. Test: `test_resolver_logs_paths_searched_on_failure`
2. Test: `test_resolver_logs_patterns_tried`
3. Test: `test_resolver_logs_files_found`
4. Implement: Add `logging.debug()` calls to resolver

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: Specified in pyproject.toml
* **Configuration**: pyproject.toml `[tool.pytest.ini_options]`
* **Runner**: `uv run pytest`
* **Async Support**: pytest-asyncio (asyncio_mode = "auto")

### Testing Tools Required
* **Mocking**: unittest.mock (MagicMock, AsyncMock, patch) - standard usage per conftest.py
* **Assertions**: pytest built-in assertions - follow existing patterns
* **Coverage**: pytest-cov - Target: 80% minimum (existing standard)
* **Test Data**: tmp_path fixtures, structured test state files

### Test Organization
* **Test Location**: `tests/test_orchestration/` for core logic
* **Naming Convention**: `test_*.py` files, `test_*` functions
* **Fixture Strategy**: Shared fixtures in `conftest.py`, test-specific in test files
* **Setup/Teardown**: pytest fixtures with `tmp_path` for file isolation

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% (minimum for safety-critical code)
* **Integration Coverage**: 80%
* **Critical Path Coverage**: 100%
* **Error Path Coverage**: 90%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| ArtifactValidator | 95% | 80% | CRITICAL | Core safety logic |
| ErrorMessageFormatter | 100% | N/A | HIGH | Template compliance |
| CriticalFailureNotification | 90% | 85% | HIGH | EventBus integration |
| FailureStatePersistence | 90% | 80% | HIGH | State file compliance |
| ResumeValidation | 90% | 85% | HIGH | User journey critical |
| UnifiedPathResolver | 95% | 80% | HIGH | Replaces scattered logic |
| DiagnosticLogging | 85% | N/A | MEDIUM | Observability |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **AT-001: Missing Implementation Plan Halts Stage** (Priority: CRITICAL)
   * **Description**: IMPLEMENTATION stage halts before agent execution when `implementation_plan.md` missing
   * **Test Type**: Integration
   * **Success Criteria**: No agent invoked; error message displayed; notification emitted; state saved with failure
   * **Test Approach**: TDD

2. **AT-002: Error Message Contains All Elements** (Priority: CRITICAL)
   * **Description**: Error message format includes artifact path, requiring stage, creating stage, resolution
   * **Test Type**: Unit
   * **Success Criteria**: Parse message, assert all 4 elements present
   * **Test Approach**: TDD

3. **AT-003: Critical Failure Triggers Notification** (Priority: HIGH)
   * **Description**: `critical_failure` event emitted via EventBus
   * **Test Type**: Unit + Integration
   * **Success Criteria**: Mock EventBus receives `emit_sync` with correct payload
   * **Test Approach**: TDD

4. **AT-004: State Persists Failure Reason** (Priority: HIGH)
   * **Description**: orchestration_state.json updated with `status: "failed"` and `failure_reason`
   * **Test Type**: Unit
   * **Success Criteria**: JSON parse, assert fields present
   * **Test Approach**: TDD

5. **AT-005: Resume After Fix** (Priority: HIGH)
   * **Description**: Workflow resumes successfully after artifact provided
   * **Test Type**: Integration
   * **Success Criteria**: Create missing artifact, resume, workflow proceeds
   * **Test Approach**: TDD

6. **AT-006: No Regression for Complete Workflows** (Priority: CRITICAL)
   * **Description**: Existing workflows with all artifacts pass without validation errors
   * **Test Type**: Integration
   * **Success Criteria**: Run existing integration tests; all pass
   * **Test Approach**: Run existing test suite

7. **AT-007: Unified Resolver Finds All Locations** (Priority: HIGH)
   * **Description**: Single resolver checks all configured paths consistently
   * **Test Type**: Unit
   * **Success Criteria**: Artifact found in each location type
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Path normalization**: Hyphenated names, CamelCase, snake_case consistency
* **Unicode in paths**: Feature names with non-ASCII characters
* **Empty artifacts**: File exists but is empty (should pass existence check)
* **Symlinked artifacts**: Symlink to actual file should resolve
* **Concurrent access**: Multiple resume attempts

### Error Scenarios

* **ValidationError on missing artifact**: Structured error with all context
* **Notification send failure**: Logged but doesn't block workflow halt
* **State write failure**: Exception raised with clear message
* **Resolver finds no locations**: Returns None plus list of searched paths

## Test Data Strategy

### Test Data Requirements
* **Objective files**: Sample objective markdown with feature names
* **Artifact files**: Minimal valid markdown files for each artifact type
* **State files**: orchestration_state.json with various statuses
* **stages.yaml**: Default config with artifact definitions

### Test Data Management
* **Storage**: Created dynamically via `tmp_path` fixture
* **Generation**: Pytest fixtures in conftest.py
* **Isolation**: Each test uses isolated tmp_path directory
* **Cleanup**: Automatic via pytest tmp_path lifecycle

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_orchestration/test_execution_loop.py`
**Pattern**: Async test with fixtures, state verification

```python
class TestExecutionLoopStatePersistence:
    """Tests for state persistence and resume."""

    @pytest.fixture
    def mock_sdk_client(self) -> AsyncMock:
        """Create mock SDK client."""
        client = AsyncMock()
        client.execute_streaming.return_value = "VERIFIED_APPROVED: Done."
        return client

    @pytest.mark.asyncio
    async def test_save_state_contains_required_fields(
        self, objective_file: Path, teambot_dir: Path, mock_sdk_client: AsyncMock
    ) -> None:
        """Saved state contains all required fields."""
        loop = ExecutionLoop(
            objective_path=objective_file,
            config={},
            teambot_dir=teambot_dir,
        )

        loop.cancel()
        await loop.run(mock_sdk_client)

        state_file = loop.teambot_dir / "orchestration_state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))

        assert "objective_file" in state
        assert "current_stage" in state
        assert "status" in state
```

**Key Conventions:**
* Class-based test organization by feature area
* Fixtures for common setup (mock_sdk_client, tmp_path derivatives)
* `@pytest.mark.asyncio` for async tests
* Type hints on test methods
* Docstrings describing what's being tested

### Recommended Test Structure for This Feature

```python
"""Tests for artifact validation (TDD)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from teambot.orchestration.artifact_validator import (
    ArtifactValidator,
    ValidationError,
)


class TestArtifactValidatorValidation:
    """Tests for ArtifactValidator.validate_stage_artifacts()."""

    @pytest.fixture
    def validator(self, tmp_path: Path) -> ArtifactValidator:
        """Create validator instance."""
        return ArtifactValidator(teambot_dir=tmp_path, feature_name="test-feature")

    def test_validate_passes_when_required_artifact_exists(
        self, validator: ArtifactValidator, tmp_path: Path
    ) -> None:
        """Validation passes when required artifact file exists."""
        # Arrange
        artifacts_dir = tmp_path / "test-feature" / "artifacts"
        artifacts_dir.mkdir(parents=True)
        (artifacts_dir / "implementation_plan.md").write_text("# Plan")

        # Act
        result = validator.validate_stage_artifacts(
            stage="IMPLEMENTATION",
            required_artifacts=["implementation_plan.md"]
        )

        # Assert
        assert result.is_valid is True
        assert result.missing_artifacts == []

    def test_validate_fails_when_required_artifact_missing(
        self, validator: ArtifactValidator
    ) -> None:
        """Validation fails with structured error when artifact missing."""
        # Act
        result = validator.validate_stage_artifacts(
            stage="IMPLEMENTATION",
            required_artifacts=["implementation_plan.md"]
        )

        # Assert
        assert result.is_valid is False
        assert len(result.missing_artifacts) == 1
        assert "implementation_plan.md" in result.missing_artifacts[0].path
        assert result.missing_artifacts[0].requiring_stage == "IMPLEMENTATION"
```

## Success Criteria

### Test Implementation Complete When:
- [ ] All 7 acceptance test scenarios have passing tests
- [ ] Coverage targets met per component (90%+ for critical)
- [ ] All edge cases documented above have tests
- [ ] Error paths validated for all failure modes
- [ ] Tests follow codebase conventions (class-based, typed, docstrings)
- [ ] Tests are maintainable and clear
- [ ] CI passes: `uv run pytest && uv run ruff check . && uv run ruff format --check .`

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast (<100ms per unit test)
* Tests are reliable (no flakiness)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem
* Mock/stub usage is appropriate and minimal

## Implementation Guidance

### For TDD Components (All):
1. Write failing test for simplest case first
2. Write minimal code to make test pass
3. Write next test (more complex case)
4. Refactor when tests pass, keeping them green
5. Focus on behavior, not implementation details
6. Test public API, not internal methods

### Test File Organization:
```
tests/
└── test_orchestration/
    ├── test_artifact_validator.py      # FR-001, FR-008
    ├── test_error_formatter.py         # FR-002
    ├── test_critical_failure.py        # FR-003
    ├── test_failure_persistence.py     # FR-004
    ├── test_resume_validation.py       # FR-005
    ├── test_artifact_resolver.py       # FR-006, FR-007
    └── conftest.py                     # Shared fixtures
```

### Test Fixture Strategy:
* Add shared fixtures to `tests/test_orchestration/conftest.py`
* Use `tmp_path` for all file system operations
* Create `sample_stages_config` fixture with artifact definitions
* Create `teambot_dir_with_artifacts` fixture for happy path tests

## Considerations and Trade-offs

### Selected Approach Benefits:
* Tests document expected behavior before code exists
* Immediate regression safety for safety-critical code
* Forces clean API design (testable = usable)
* User-requested approach matches feature characteristics

### Accepted Trade-offs:
* Slower initial development pace (mitigated by clear requirements)
* Requires discipline to write tests first (offset by clear spec)
* May discover spec gaps during test writing (feature, not bug)

### Risk Mitigation:
* High test coverage prevents the validation feature from silently failing
* TDD ensures all error paths are explicitly tested
* Integration tests verify end-to-end user journeys work

## References

* **Feature Spec**: [.teambot/file-based-orchestration/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/file-based-orchestration/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: `tests/test_orchestration/test_execution_loop.py`, `tests/test_notifications/test_event_bus.py`
* **Test Standards**: `pyproject.toml [tool.pytest.ini_options]`
* **stages.yaml**: Repository root `stages.yaml`

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this TDD strategy into implementation phases
4. 🔍 Implementation will write tests first for each component

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

## Approval Request

I've analyzed **File-Based Orchestration Critical Failure Handling** and recommend **TDD**.

**Decision Matrix Summary:**
- TDD Score: 9 (threshold: 6)
- Code-First Score: 0

**Do you:**
1. ✅ Approve this strategy and proceed to planning
2. 🔄 Want to adjust the approach (please specify)
3. ❓ Have questions or concerns about the recommendation

---

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE
- Approach: TDD (score 9 justification: Requirements Clarity + Complexity + Risk Level)
- Coverage Targets: SPECIFIED (90%+ for critical, 85%+ for high priority)
- Components Covered: 7/7
```
