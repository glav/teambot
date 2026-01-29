<!-- markdownlint-disable-file -->
# Test Strategy: File-Based Orchestration

**Strategy Date**: 2026-01-29
**Feature Specification**: docs/feature-specs/file-based-orchestration.md
**Research Reference**: .agent-tracking/research/20260129-file-based-orchestration-research.md
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: HYBRID (TDD for core logic, Code-First for integration/UI)

### Testing Approach Decision Matrix

#### Factor Scoring

| Factor | Assessment | TDD Points | Code-First Points |
|--------|------------|------------|-------------------|
| **Requirements Clarity** | Well-defined with 21 FRs, clear acceptance criteria | 3 | 0 |
| **Complexity** | High - review iteration, parallel execution, state management | 3 | 0 |
| **Risk Level** | High - core autonomous feature, data loss risk on crash | 3 | 0 |
| **Exploratory Nature** | No - clear architecture from research | 0 | 0 |
| **Simplicity** | Mixed - core logic complex, some utilities simple | 0 | 1 |
| **Time Pressure** | Moderate - feature is significant | 0 | 1 |
| **Requirements Stability** | Stable - all questions resolved | 0 | 0 |

**TDD Score: 9** | **Code-First Score: 2**

**Decision**: HYBRID - TDD for core components (score 9 >> threshold), Code-First for simple utilities and UI integration

### Rationale

The file-based orchestration feature requires a **hybrid testing approach** due to its mixed complexity profile. The core execution logic (objective parsing, review iteration, state management) is algorithm-heavy with well-defined requirements, making it ideal for TDD. The review iteration system in particular has critical correctness requirements (max 4 iterations, failure handling) that benefit from test-first development.

However, some components like progress display integration and CLI wiring are straightforward integrations that will benefit from faster code-first iteration. The async parallel execution, while complex, builds on existing patterns in the codebase and can be tested effectively after implementation.

**Key Factors:**
* Complexity: HIGH - Multiple interacting components, state persistence, async execution
* Risk: HIGH - Core autonomous feature, user data at stake
* Requirements Clarity: CLEAR - 21 functional requirements with acceptance criteria
* Time Pressure: MODERATE - Significant feature but not urgent

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: HIGH - Review iteration logic, task partitioning, state transitions
* **Integration Depth**: MEDIUM - Uses existing Orchestrator, AgentRunner, WorkflowStateMachine
* **State Management**: HIGH - Complex state with persistence, resume, cancellation
* **Error Scenarios**: HIGH - Multiple failure modes (timeout, review failure, crash recovery)

### Risk Profile
* **Business Criticality**: HIGH - Core feature enabling autonomous operation
* **User Impact**: HIGH - Affects primary use case (daily objectives)
* **Data Sensitivity**: MEDIUM - Workflow state, objective content
* **Failure Cost**: HIGH - Lost work, corrupted state could lose hours of progress

### Requirements Clarity
* **Specification Completeness**: COMPLETE - 21 FRs, 8 NFRs defined
* **Acceptance Criteria Quality**: PRECISE - Measurable criteria per requirement
* **Edge Cases Identified**: 12+ documented (review failure, timeout, cancellation, etc.)
* **Dependencies Status**: STABLE - Builds on existing tested infrastructure

## Test Strategy by Component

### ObjectiveParser - TDD

**Approach**: TDD
**Rationale**: Well-defined input/output with clear parsing rules. Parsing logic is critical for correct objective interpretation.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Parse complete objective file with all sections
  * Parse minimal objective (title + goals only)
  * Handle missing optional sections gracefully
  * Extract success criteria with checkbox state
* Edge Cases:
  * Empty file
  * Malformed markdown
  * Missing H1 title
  * Duplicate section headers

**Testing Sequence (TDD)**:
1. Write test for title extraction from H1
2. Implement minimal title parsing
3. Write test for goals list extraction
4. Implement goals parsing
5. Write test for success criteria with checkboxes
6. Implement criteria parsing
7. Add tests for constraints, context sections
8. Implement remaining sections
9. Add error handling tests

### ReviewIterator - TDD

**Approach**: TDD
**Rationale**: Critical review logic with clear algorithm (max 4 iterations, approval detection, failure handling). High correctness requirements.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Approval on first iteration
  * Approval on iteration 2-4
  * Failure after 4 iterations with summary generation
  * Feedback incorporation between iterations
* Edge Cases:
  * Empty review feedback
  * Review timeout mid-iteration
  * Agent failure during work phase
  * Agent failure during review phase

**Testing Sequence (TDD)**:
1. Write test for single iteration approval
2. Implement basic iteration with approval check
3. Write test for iteration counter enforcement
4. Implement max iteration limit
5. Write test for failure summary generation
6. Implement failure report generation
7. Write test for feedback incorporation
8. Implement feedback routing
9. Add async cancellation tests

### TimeManager - TDD

**Approach**: TDD
**Rationale**: Simple but critical component. Clear requirements (8-hour limit, elapsed tracking). Easy to test-first.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Start/stop timing
  * Check expiration at boundary
  * Resume from elapsed time
  * Format elapsed/remaining for display
* Edge Cases:
  * Exactly at time limit
  * Resume past limit
  * Negative remaining time display

**Testing Sequence (TDD)**:
1. Write test for start() sets start time
2. Implement start()
3. Write test for elapsed_seconds calculation
4. Implement elapsed tracking
5. Write test for is_expired() at boundary
6. Implement expiration check
7. Write test for resume(prior_elapsed)
8. Implement resume capability

### ExecutionLoop - Code-First

**Approach**: Code-First
**Rationale**: Complex async coordination that benefits from implementation iteration. Integrates multiple components (parser, iterator, orchestrator). Easier to test holistically after implementation.

**Test Requirements:**
* Coverage Target: 85%
* Test Types: Integration, Unit
* Critical Scenarios:
  * Complete workflow execution (all 13 stages)
  * Cancellation mid-execution
  * Timeout enforcement
  * Resume from saved state
  * Review stage iteration delegation
* Edge Cases:
  * Objective file not found
  * State file corruption
  * Stage transition failure

**Testing Sequence (Code-First)**:
1. Implement core loop structure
2. Add happy path integration test
3. Implement cancellation handling
4. Add cancellation test
5. Implement timeout handling
6. Add timeout test
7. Add edge case tests for error scenarios

### ParallelExecutor - Code-First

**Approach**: Code-First
**Rationale**: Builds on existing async patterns in codebase. Complex async behavior easier to debug through implementation then test.

**Test Requirements:**
* Coverage Target: 85%
* Test Types: Unit, Integration
* Critical Scenarios:
  * Execute 2 tasks in parallel
  * Handle one task failure, other success
  * Respect concurrency limit
  * Cancellation of parallel tasks
* Edge Cases:
  * Empty task list
  * Single task (degenerates to sequential)
  * All tasks fail

**Testing Sequence (Code-First)**:
1. Implement parallel execution with asyncio.gather
2. Add test for 2 concurrent tasks
3. Implement error handling
4. Add test for partial failure
5. Implement cancellation
6. Add cancellation test

### Progress Integration - Code-First

**Approach**: Code-First
**Rationale**: UI integration with existing StatusPanel. Manual testing more valuable than unit tests for UI behavior.

**Test Requirements:**
* Coverage Target: 70%
* Test Types: Integration
* Critical Scenarios:
  * Progress callback updates agent state
  * Stage change updates display
  * Time updates display
* Edge Cases:
  * Rapid updates don't cause flicker
  * Long agent names truncated

**Testing Sequence (Code-First)**:
1. Implement progress callback creation
2. Wire to existing AgentStatusManager
3. Add integration test with mock orchestration
4. Manual testing for UI behavior

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.x
* **Version**: Configured in pyproject.toml
* **Configuration**: pyproject.toml [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (MagicMock, AsyncMock, patch)
* **Assertions**: pytest built-in assertions
* **Coverage**: pytest-cov, target 85% overall
* **Async Testing**: pytest-asyncio for async test functions
* **Test Data**: Fixtures in conftest.py, sample objectives

### Test Organization
* **Test Location**: `tests/test_orchestration/`
* **Naming Convention**: `test_*.py`, `Test*` classes, `test_*` functions
* **Fixture Strategy**: Shared fixtures in `tests/conftest.py`, module-specific in test files
* **Setup/Teardown**: pytest fixtures with `tmp_path` for file operations

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 85% minimum
* **Integration Coverage**: 75%
* **Critical Path Coverage**: 100% (review iteration, state persistence)
* **Error Path Coverage**: 80%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| ObjectiveParser | 95% | N/A | CRITICAL | Core parsing logic |
| ReviewIterator | 95% | 80% | CRITICAL | Review loop correctness |
| TimeManager | 100% | N/A | HIGH | Simple, full coverage easy |
| ExecutionLoop | 80% | 85% | CRITICAL | Complex integration |
| ParallelExecutor | 85% | 80% | HIGH | Async correctness |
| Progress callbacks | 70% | 70% | MEDIUM | UI integration |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Review Iteration Max Limit** (Priority: CRITICAL)
   * **Description**: Review stage exhausts 4 iterations and generates failure report
   * **Test Type**: Unit
   * **Success Criteria**: Failure report contains all iteration feedback, suggestions extracted
   * **Test Approach**: TDD

2. **State Persistence on Cancellation** (Priority: CRITICAL)
   * **Description**: Ctrl+C saves complete state for resume
   * **Test Type**: Integration
   * **Success Criteria**: State file contains current stage, elapsed time, iteration counts
   * **Test Approach**: Code-First

3. **Parallel Builder Execution** (Priority: HIGH)
   * **Description**: builder-1 and builder-2 execute concurrently
   * **Test Type**: Unit
   * **Success Criteria**: Both tasks run, results merged, timing shows concurrency
   * **Test Approach**: Code-First

4. **Complete Workflow Execution** (Priority: HIGH)
   * **Description**: Full 13-stage workflow completes successfully
   * **Test Type**: Integration
   * **Success Criteria**: Final state is COMPLETE, all artifacts generated
   * **Test Approach**: Code-First

5. **Objective Parsing with All Sections** (Priority: CRITICAL)
   * **Description**: Parse well-formed objective file
   * **Test Type**: Unit
   * **Success Criteria**: All fields extracted correctly
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Empty objective file**: Return error with clear message
* **Timeout at exactly 8 hours**: Stop cleanly, save state
* **Resume past time limit**: Reject with time exceeded error
* **Review approval on 4th iteration**: Accept, don't generate failure
* **Agent crash mid-task**: Fail task, continue workflow if possible
* **State file missing on resume**: Error with clear message
* **Parallel task conflict**: Tasks operate on separate files

### Error Scenarios

* **Copilot CLI unavailable**: Skip with warning, continue if possible
* **Network timeout during agent call**: Retry once, then fail task
* **Invalid stage transition**: Raise ValueError with allowed transitions
* **Malformed state file**: Error with backup suggestion

## Test Data Strategy

### Test Data Requirements
* **Objective files**: Sample objectives in `tests/fixtures/objectives/`
* **State files**: Sample state JSON in `tests/fixtures/states/`
* **Review feedback**: Mock responses for approval/rejection scenarios

### Test Data Management
* **Storage**: `tests/fixtures/` and inline in tests
* **Generation**: Fixtures create temp files via `tmp_path`
* **Isolation**: Each test gets fresh `tmp_path` directory
* **Cleanup**: pytest handles via fixture teardown

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_orchestrator.py`
**Pattern**: Class-based tests with fixtures, mocking process creation

```python
class TestOrchestrator:
    """Tests for Orchestrator class."""

    def test_create_orchestrator_with_config(self, sample_agent_config):
        """Orchestrator initializes with configuration."""
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        assert orch.config == config
        assert orch.agents == {}
        assert orch.main_queue is not None

    def test_spawn_agent_creates_queue(self, sample_agent_config):
        """Spawning agent creates dedicated queue."""
        from teambot.orchestrator import Orchestrator

        config = {"agents": [sample_agent_config]}
        orch = Orchestrator(config)

        with patch.object(orch, "_create_agent_process") as mock_create:
            mock_create.return_value = MagicMock()
            orch.spawn_agent(sample_agent_config)

        assert "builder-1" in orch.router.agent_queues
```

**Key Conventions:**
* Class-based test organization
* Descriptive docstrings for each test
* Fixtures for common setup (sample_agent_config)
* Mocking for external dependencies (process creation)
* Inline imports to isolate test dependencies

### Recommended Test Structure for New Components

```python
"""Tests for objective parser."""

import pytest
from pathlib import Path

from teambot.orchestration.objective_parser import (
    ParsedObjective,
    parse_objective_file,
)


@pytest.fixture
def sample_objective_file(tmp_path):
    """Create a sample objective file."""
    content = """# Objective: Test Feature

## Goals
1. Implement feature X
2. Add tests

## Success Criteria
- [ ] Feature works
- [x] Tests pass

## Constraints
- Use Python
"""
    path = tmp_path / "objective.md"
    path.write_text(content)
    return path


class TestObjectiveParser:
    """Tests for parse_objective_file function."""

    def test_parse_extracts_title(self, sample_objective_file):
        """Title extracted from H1 heading."""
        result = parse_objective_file(sample_objective_file)
        assert result.title == "Test Feature"

    def test_parse_extracts_goals(self, sample_objective_file):
        """Goals extracted as list."""
        result = parse_objective_file(sample_objective_file)
        assert len(result.goals) == 2
        assert "Implement feature X" in result.goals

    def test_parse_extracts_criteria_with_status(self, sample_objective_file):
        """Success criteria include completion status."""
        result = parse_objective_file(sample_objective_file)
        assert len(result.success_criteria) == 2
        assert result.success_criteria[0].completed is False
        assert result.success_criteria[1].completed is True

    def test_parse_missing_file_raises(self, tmp_path):
        """Missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_objective_file(tmp_path / "nonexistent.md")
```

## Success Criteria

### Test Implementation Complete When:
* [x] All critical scenarios have tests
* [x] Coverage targets are met per component
* [x] All edge cases are tested
* [x] Error paths are validated
* [x] Tests follow codebase conventions
* [x] Tests are maintainable and clear
* [x] CI/CD integration is working

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast and reliable (no flakiness)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem
* Mock/stub usage is appropriate and minimal

## Implementation Guidance

### For TDD Components (ObjectiveParser, ReviewIterator, TimeManager):
1. Start with simplest test case
2. Write minimal code to pass
3. Add next test case
4. Refactor when all tests pass
5. Focus on behavior, not implementation

### For Code-First Components (ExecutionLoop, ParallelExecutor, Progress):
1. Implement core functionality
2. Add happy path test
3. Identify edge cases from implementation
4. Add edge case tests
5. Verify coverage meets target

### For Hybrid Approach:
1. Start with TDD components (ObjectiveParser, ReviewIterator, TimeManager)
2. These provide foundation for integration
3. Proceed to Code-First components
4. Ensure integration tests cover boundaries
5. Validate overall feature behavior

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD for critical parsing/iteration ensures correctness from start
* Code-First for async integration allows faster iteration
* Clear component boundaries enable parallel development
* High coverage targets catch regressions early

### Accepted Trade-offs:
* TDD slower initial velocity for some components
* Code-First components may need test retrofitting
* Integration tests may be slower to run
* Mock complexity for async operations

### Risk Mitigation:
* TDD on review iteration prevents costly bugs in core logic
* State persistence testing prevents data loss scenarios
* Parallel execution testing prevents race conditions

## References

* **Feature Spec**: [docs/feature-specs/file-based-orchestration.md](../../docs/feature-specs/file-based-orchestration.md)
* **Research Doc**: [.agent-tracking/research/20260129-file-based-orchestration-research.md](./../research/20260129-file-based-orchestration-research.md)
* **Test Examples**: tests/test_orchestrator.py, tests/test_workflow/test_state_machine.py
* **Test Standards**: pyproject.toml [tool.pytest.ini_options]

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow recommended approach per component

---

**Strategy Status**: DRAFT
**Approved By**: PENDING
**Ready for Planning**: YES (pending approval)
