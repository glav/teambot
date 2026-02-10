<!-- markdownlint-disable-file -->
# Test Strategy: Unknown Agent ID Validation

**Strategy Date**: 2026-02-09
**Feature Specification**: .teambot/unknown-agent-validation/artifacts/feature_spec.md
**Research Reference**: .agent-tracking/research/20260209-unknown-agent-validation-research.md
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: CODE_FIRST

### Testing Approach Decision Matrix

#### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | Points To |
|--------|----------|:-----:|-----------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | 3 | TDD |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | 0 | — |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | 0 | — |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | 0 | — |
| **Simplicity** | Is this straightforward CRUD or simple logic? | 2 | Code-First |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | 1 | Code-First |
| **Requirements Stability** | Are requirements likely to change during development? | 0 | — |

| | Score | Threshold |
|--|:-----:|:---------:|
| **TDD** | 3 | ≥ 6 |
| **Code-First** | 5 | ≥ 5 ✅ |

**Decision**: Code-First (score 5 ≥ threshold 5, TDD score 3 < 6)

### Rationale

This feature is a targeted bug fix adding simple validation guards (set-membership checks) and early-return patterns. The implementation is straightforward — each change is 5-15 lines of code using established patterns already present in the codebase. The requirements are crystal clear (7 functional requirements, 7 acceptance scenarios), but the logic itself is trivially simple, not algorithm-heavy or business-critical.

Code-First is optimal here because the validation logic is so straightforward that writing the guard clauses first, then adding comprehensive tests to confirm all paths are covered, is faster and equally rigorous. The existing test infrastructure already has excellent patterns for both executor and agent state tests that can be directly followed.

TDD was considered but rejected because the implementation is a simple pattern repetition (import constants, loop over IDs, check set membership, return error). Writing tests first would not reveal new design insights — the design is already fully specified in the research document.

**Key Factors:**
* Complexity: **LOW** — set membership checks and early returns
* Risk: **MEDIUM** — bug fix that could regress valid commands if done wrong
* Requirements Clarity: **CLEAR** — 7 FRs, 7 acceptance tests, exact error formats specified
* Time Pressure: **MODERATE** — targeted fix, not a large feature

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Low — O(1) set lookups, no business logic
* **Integration Depth**: Medium — touches 3 files across 2 subsystems (tasks, ui)
* **State Management**: None — stateless validation checks
* **Error Scenarios**: Simple — one error type (unknown agent) with consistent format

### Risk Profile
* **Business Criticality**: Medium — prevents confusing silent failures
* **User Impact**: All users who mistype agent IDs
* **Data Sensitivity**: None — agent IDs are system-internal identifiers
* **Failure Cost**: Low if validation is missing (status quo), Medium if valid agents are rejected (regression)

### Requirements Clarity
* **Specification Completeness**: COMPLETE — 7 functional requirements with acceptance criteria
* **Acceptance Criteria Quality**: PRECISE — exact error message format specified
* **Edge Cases Identified**: 7 documented (aliases, multi-agent, pipeline, background, typos)
* **Dependencies Status**: STABLE — VALID_AGENTS and AGENT_ALIASES are static constants

## Test Strategy by Component

### Component 1: TaskExecutor.execute() Validation — CODE_FIRST

**Approach**: Code-First
**Rationale**: The validation block is a simple guard clause using an established local-import pattern already present in the same file (line 199). Implement the ~15-line guard, then add tests to confirm all command shapes are rejected.

**Test Requirements:**
* Coverage Target: 100% of new validation code
* Test Types: Unit (async)
* Critical Scenarios:
  * Unknown agent rejected on simple executor path
  * Unknown agent rejected on background path
  * Unknown agent rejected in multi-agent command
  * Unknown agent rejected in pipeline command
  * Valid alias (`@project_manager`) accepted through executor
  * All 6 valid agents accepted (regression)
  * Error message matches expected format
* Edge Cases:
  * Mixed valid/invalid in multi-agent: `@pm,fake task` — entire command rejected
  * Unknown agent in second pipeline stage: `@pm task -> @fake task`
  * Alias in multi-agent: `@project_manager,ba task`

**Testing Sequence** (Code-First):
1. Implement validation guard in `execute()` method
2. Add `test_execute_rejects_unknown_agent` — basic rejection
3. Add `test_execute_rejects_unknown_agent_background` — background path
4. Add `test_execute_rejects_unknown_in_multiagent` — multi-agent rejection
5. Add `test_execute_rejects_unknown_in_pipeline` — pipeline rejection
6. Add `test_execute_accepts_valid_alias` — alias resolution
7. Add `test_execute_accepts_all_valid_agents` — regression guard
8. Add `test_execute_error_message_format` — message format verification

### Component 2: TeamBotApp._handle_agent_command() Validation — CODE_FIRST

**Approach**: Code-First
**Rationale**: Mirrors the executor validation pattern exactly. The split-pane app is harder to unit test (Textual UI framework), so validation is best verified through the executor tests which cover the same logic. The app validation is defence-in-depth.

**Test Requirements:**
* Coverage Target: Covered indirectly via executor tests (same validation logic)
* Test Types: No separate unit tests needed — the validation logic is identical to executor
* Critical Scenarios:
  * Validation occurs before `set_running()` or `execute_streaming()` is called
* Edge Cases:
  * Multi-agent streaming path validates all IDs before starting any streams

**Testing Sequence** (Code-First):
1. Implement validation guard in `_handle_agent_command()` method
2. Verify manually or via integration test that unknown agent shows error in UI
3. No additional unit tests — covered by executor test suite

### Component 3: AgentStatusManager Guard — CODE_FIRST

**Approach**: Code-First
**Rationale**: Adding a one-line guard (`if agent_id not in DEFAULT_AGENTS: return`) to three methods. Straightforward defence-in-depth that prevents ghost entries.

**Test Requirements:**
* Coverage Target: 100% of new guard code
* Test Types: Unit (synchronous)
* Critical Scenarios:
  * `set_running("fake-agent", "task")` does not create status entry
  * `set_idle("fake-agent")` does not create status entry
  * `set_model("fake-agent", "gpt-4")` does not create status entry
  * `set_running("pm", "task")` still works (regression)
  * `set_completed("pm")` still works after running (regression)
* Edge Cases:
  * `set_streaming("fake-agent")` — calls `_update()` internally, should be guarded
  * Agent already in `_statuses` dict is not affected by guard (only auto-creation blocked)

**Testing Sequence** (Code-First):
1. Implement guards in `_update()`, `set_idle()`, `set_model()`
2. Add `test_update_ignores_unknown_agent` — `set_running()` guard
3. Add `test_set_idle_ignores_unknown_agent` — `set_idle()` guard
4. Add `test_set_model_ignores_unknown_agent` — `set_model()` guard
5. Add `test_default_agents_still_auto_created` — regression check

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest with pytest-asyncio, pytest-mock, pytest-cov
* **Configuration**: `pyproject.toml` (lines 41-48)
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock.AsyncMock` — for SDK client in executor tests
* **Assertions**: Built-in pytest `assert` — direct comparisons
* **Coverage**: pytest-cov — target 80%+ overall (project standard)
* **Test Data**: Inline — commands constructed via `parse_command()` helper

### Test Organization
* **Test Location**: `tests/` (mirrors `src/` structure)
* **Naming Convention**: `test_*.py` files, `Test*` classes, `test_*` methods
* **Fixture Strategy**: Inline setup per test (no shared fixtures needed)
* **Setup/Teardown**: None needed — tests are stateless

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 100% of new validation code
* **Integration Coverage**: Not applicable (no new integrations)
* **Critical Path Coverage**: 100% — all command shapes covered
* **Error Path Coverage**: 100% — error message format verified

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|:------:|:-------------:|:--------:|-------|
| `TaskExecutor.execute()` validation | 100% | — | CRITICAL | 7 new tests |
| `app.py` validation | — | — | HIGH | Covered by executor tests (same logic) |
| `AgentStatusManager` guard | 100% | — | HIGH | 4 new tests |

### Critical Test Scenarios

1. **Unknown Agent Rejected via Executor** (Priority: CRITICAL)
   * **Description**: `@unknown-agent task` returns `ExecutionResult(success=False)` with error
   * **Test Type**: Unit (async)
   * **Success Criteria**: `result.success is False` and `result.error` contains `"Unknown agent: 'unknown-agent'"`
   * **Test Approach**: Code-First

2. **Multi-Agent with Invalid ID Rejects Entire Command** (Priority: CRITICAL)
   * **Description**: `@pm,fake task` rejects without executing any agent
   * **Test Type**: Unit (async)
   * **Success Criteria**: `result.success is False`, `mock_sdk.execute.call_count == 0`
   * **Test Approach**: Code-First

3. **Pipeline with Invalid Agent Rejects** (Priority: CRITICAL)
   * **Description**: `@fake -> @pm task` rejects without executing any stage
   * **Test Type**: Unit (async)
   * **Success Criteria**: `result.success is False`, `mock_sdk.execute.call_count == 0`
   * **Test Approach**: Code-First

4. **Valid Alias Accepted** (Priority: HIGH)
   * **Description**: `@project_manager task` succeeds through executor
   * **Test Type**: Unit (async)
   * **Success Criteria**: `result.success is True`, `mock_sdk.execute.assert_called_once()`
   * **Test Approach**: Code-First

5. **Ghost Agent Prevention** (Priority: HIGH)
   * **Description**: `set_running("fake", "task")` does not create entry
   * **Test Type**: Unit (sync)
   * **Success Criteria**: `manager.get("fake") is None`
   * **Test Approach**: Code-First

### Edge Cases to Cover

* **Mixed valid/invalid multi-agent**: `@pm,unknown task` → entire command rejected, PM does not execute
* **Unknown agent in later pipeline stage**: `@pm Plan -> @fake Build` → entire pipeline rejected
* **Background with unknown agent**: `@unknown task &` → error returned, no background task created
* **Alias in pipeline**: `@project_manager Plan -> @builder-1 Build` → accepted (alias resolved)

### Error Scenarios

* **Single unknown agent**: Returns `Unknown agent: 'unknown-agent'. Valid agents: ba, builder-1, builder-2, pm, reviewer, writer`
* **Unknown in multi-agent**: Returns error for first invalid ID found, entire command rejected
* **Unknown in pipeline**: Returns error for first invalid ID found across all stages, no stages execute
* **Non-agent command type**: Unchanged behavior — returns `"Not an agent command"` error

## Test Data Strategy

### Test Data Requirements
* **Commands**: Generated via `parse_command()` from string input (same pattern as existing tests)
* **SDK Client**: `AsyncMock()` with configurable return values
* **AgentStatusManager**: Fresh instance per test (initializes with DEFAULT_AGENTS)

### Test Data Management
* **Storage**: Inline in test functions
* **Generation**: Manual construction via `parse_command()` helper
* **Isolation**: Each test creates its own executor/manager instances
* **Cleanup**: None needed — no shared state

## Example Test Patterns

### Existing Pattern from Codebase

**File**: `tests/test_tasks/test_executor.py` (lines 24-36)
**Pattern**: Create mock SDK → create executor → parse command → execute → assert

```python
@pytest.mark.asyncio
async def test_execute_simple_command(self):
    """Test executing simple @agent command."""
    mock_sdk = AsyncMock()
    mock_sdk.execute = AsyncMock(return_value="Task completed")

    executor = TaskExecutor(sdk_client=mock_sdk)
    cmd = parse_command("@pm Create a plan")

    result = await executor.execute(cmd)

    assert result.success
    assert "Task completed" in result.output
    mock_sdk.execute.assert_called_once()
```

**Key Conventions:**
* Use `AsyncMock()` for SDK client
* Use `parse_command()` to create Command objects from strings
* Assert on `result.success`, `result.output`, `result.error`
* Use `@pytest.mark.asyncio` for async tests
* Group tests in `Test*` classes by theme

### Recommended Test Structure for New Tests

```python
class TestTaskExecutorAgentValidation:
    """Tests for unknown agent ID validation in TaskExecutor."""

    @pytest.mark.asyncio
    async def test_execute_rejects_unknown_agent(self):
        """Unknown agent ID returns error via executor."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@unknown-agent do something &")

        result = await executor.execute(cmd)

        assert not result.success
        assert "Unknown agent: 'unknown-agent'" in result.error
        assert "Valid agents:" in result.error
        mock_sdk.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_rejects_unknown_in_multiagent(self):
        """Multi-agent with invalid ID rejects entire command."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command("@pm,fake-agent do something")

        result = await executor.execute(cmd)

        assert not result.success
        assert "fake-agent" in result.error
        mock_sdk.execute.assert_not_called()
```

```python
class TestAgentStatusManagerGuard:
    """Tests for ghost agent prevention in AgentStatusManager."""

    def test_update_ignores_unknown_agent(self):
        """set_running for unknown agent does not create entry."""
        manager = AgentStatusManager()
        manager.set_running("fake-agent", "task")
        assert manager.get("fake-agent") is None

    def test_default_agents_still_auto_created(self):
        """Known agents still work after guard is added."""
        manager = AgentStatusManager()
        manager.set_running("pm", "plan authentication")
        status = manager.get("pm")
        assert status.state == AgentState.RUNNING
```

## Success Criteria

### Test Implementation Complete When:
- [ ] All 7 executor validation tests pass
- [ ] All 4 agent state guard tests pass
- [ ] All existing 943+ tests continue to pass
- [ ] Coverage of new validation code is 100%
- [ ] Error messages match specified format
- [ ] Tests follow existing codebase conventions (pytest, AsyncMock, parse_command)
- [ ] No flaky tests introduced

### Test Quality Indicators:
* Tests are readable and self-documenting (descriptive names + docstrings)
* Tests are fast (< 1s each — no I/O, no sleeps)
* Tests are independent (each creates own executor/manager)
* Failures clearly indicate which validation path broke
* Mock usage is minimal (only SDK client)

## Implementation Guidance

### For All Components (Code-First):
1. Implement validation guard in production code
2. Run `uv run pytest` to verify no regressions
3. Add new test class with all test cases
4. Run `uv run pytest` again to verify new tests pass
5. Run `uv run ruff check .` and `uv run ruff format .` for clean code

### Implementation Order:
1. **TaskExecutor.execute()** — highest impact, covers all advanced paths
2. **AgentStatusManager guards** — defence-in-depth
3. **app.py validation** — split-pane UI path
4. **Tests** — all at once after implementation

## Considerations and Trade-offs

### Selected Approach Benefits:
* Fast implementation — simple guards, no test-first overhead for trivial logic
* Comprehensive test coverage still achieved after implementation
* Follows existing codebase patterns exactly

### Accepted Trade-offs:
* No test-first safety net — mitigated by running existing tests between changes
* app.py validation not separately unit tested — mitigated by identical logic in executor tests

### Risk Mitigation:
* Run full test suite after each file change to catch regressions immediately
* Error message format is tested explicitly to prevent drift
* All 6 valid agents tested in regression guard

## References

* **Feature Spec**: [.teambot/unknown-agent-validation/artifacts/feature_spec.md](../../.teambot/unknown-agent-validation/artifacts/feature_spec.md)
* **Research Doc**: [.agent-tracking/research/20260209-unknown-agent-validation-research.md](./../research/20260209-unknown-agent-validation-research.md)
* **Executor Tests**: `tests/test_tasks/test_executor.py`
* **Agent State Tests**: `tests/test_ui/test_agent_state.py`

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow Code-First approach per component

---

**Strategy Status**: DRAFT
**Approved By**: PENDING
**Ready for Planning**: YES
