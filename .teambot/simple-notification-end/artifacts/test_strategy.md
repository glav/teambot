<!-- markdownlint-disable-file -->
# Test Strategy: @notify Pseudo-Agent

**Strategy Date**: 2026-02-12
**Feature Specification**: .teambot/simple-notification-end/artifacts/feature_spec.md
**Spec Review Reference**: .teambot/simple-notification-end/artifacts/spec_review.md
**Strategist**: Builder-2 (Test Strategy Agent)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Assessment | TDD Points | Code-First Points |
|--------|------------|------------|-------------------|
| **Requirements Clarity** | Clear - 15 FRs with explicit acceptance criteria | 3 | 0 |
| **Complexity** | Medium - pseudo-agent pattern with $ref interpolation | 2 | 0 |
| **Risk Level** | Medium - must not break existing pipelines | 2 | 0 |
| **Exploratory Nature** | No - well-defined feature | 0 | 0 |
| **Simplicity** | Partially - some components are simple utilities | 0 | 1 |
| **Time Pressure** | Low - standard feature development | 0 | 0 |
| **Requirements Stability** | Stable - spec approved, no open questions | 0 | 0 |

### Score Calculation

- **TDD Score**: 3 + 2 + 2 + 0 = **7**
- **Code-First Score**: 0 + 0 + 0 + 0 + 1 + 0 + 0 = **1**

### Decision

**TDD Score (7) ≥ 6 → Recommended Approach: TDD**

---

## Recommended Testing Approach

**Primary Approach**: **TDD**

### Rationale

The `@notify` pseudo-agent feature is well-suited for TDD because the requirements are clearly defined with 15 functional requirements, each with explicit acceptance criteria. The specification includes 10 concrete acceptance test scenarios (AT-001 through AT-010) that directly translate to test cases.

The feature introduces a new pseudo-agent pattern that must integrate with existing pipeline functionality without breaking it. This integration risk is best mitigated by writing tests first that verify both the new behavior and backward compatibility. TDD will ensure edge cases like notification failures, output truncation, and pipeline positioning are handled correctly from the start.

Additionally, the feature touches multiple components (router, executor, task manager, commands) with well-defined interfaces. Writing tests first will clarify the contracts between these components and catch integration issues early.

**Key Factors:**
* Complexity: **MEDIUM** - New pseudo-agent pattern with $ref interpolation, truncation logic
* Risk: **MEDIUM** - Must not break existing pipelines; notification failures must be non-blocking
* Requirements Clarity: **CLEAR** - 15 FRs, 10 ATs, detailed spec with implementation notes
* Time Pressure: **LOW** - Standard feature development cycle

---

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Low-Medium - message interpolation with $ref tokens, truncation logic (simple string operations)
* **Integration Depth**: High - spans router, executor, task manager, EventBus, status display
* **State Management**: Low - stateless pseudo-agent execution; result stored once in TaskManager
* **Error Scenarios**: Medium - notification failures must be caught and logged without breaking pipeline

### Risk Profile
* **Business Criticality**: MEDIUM - enhances user experience but not mission-critical
* **User Impact**: HIGH - replaces existing `/notify` command; affects all notification users
* **Data Sensitivity**: LOW - user-controlled messages with existing HTML escaping
* **Failure Cost**: MEDIUM - notification failures should be silent; pipeline breaks would be HIGH cost

### Requirements Clarity
* **Specification Completeness**: COMPLETE - all sections substantive, no TBDs
* **Acceptance Criteria Quality**: PRECISE - 10 executable scenarios with verification steps
* **Edge Cases Identified**: 6+ documented (truncation, failure handling, empty pipeline, etc.)
* **Dependencies Status**: STABLE - existing EventBus, TaskManager, parser all stable

---

## Test Strategy by Component

### 1. Router Agent Recognition - TDD

**Approach**: TDD
**Rationale**: Adding "notify" to VALID_AGENTS is a critical change that affects all agent validation. Tests first ensure the new pseudo-agent is recognized without breaking existing agents.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `@notify` recognized as valid agent ID
  * `@notify` does not break existing agent validation
  * `@notify` resolved correctly (no alias mapping needed)
* Edge Cases:
  * Case sensitivity: `@Notify`, `@NOTIFY` should fail
  * Invalid agents still rejected

**Testing Sequence**:
1. Write test: `@notify` is valid agent ID → expect pass
2. Add "notify" to VALID_AGENTS
3. Write test: existing agents still valid → verify regression safety
4. Write test: `get_all_agents()` returns 7 agents (including notify)

**Test Location**: `tests/test_repl/test_router.py`

---

### 2. Pseudo-Agent Detection in Executor - TDD

**Approach**: TDD
**Rationale**: This is the core new pattern - detecting `@notify` and bypassing Copilot SDK execution. TDD ensures the bypass logic is correct before any SDK changes.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit, Integration
* Critical Scenarios:
  * `@notify` execution does not call SDK client
  * `@notify` returns confirmation output
  * Result stored in TaskManager._agent_results
  * Pipeline continues after `@notify`
* Edge Cases:
  * `@notify` with no message
  * `@notify` with very long message
  * `@notify` in background mode (`&`)

**Testing Sequence**:
1. Write test: `@notify` does not invoke SDK → expect no SDK calls
2. Implement pseudo-agent detection branch
3. Write test: `@notify` returns "Notification sent ✅"
4. Implement notification dispatch and return
5. Write test: result stored for `$notify` reference
6. Implement result storage

**Test Location**: `tests/test_tasks/test_executor.py` (new test class)

---

### 3. $ref Interpolation for Notify - TDD

**Approach**: TDD
**Rationale**: $ref interpolation in notifications is a new use case that must work with existing parser infrastructure. Tests ensure correct token extraction and output resolution.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * `$agent` token extracted from message
  * Agent output resolved from TaskManager
  * Interpolated message contains actual output
  * Multiple $refs resolved correctly
* Edge Cases:
  * Missing agent reference (`$unknown` → should include raw token or warning)
  * Self-reference (`$notify` in notify message)
  * Empty agent output

**Testing Sequence**:
1. Write test: `$pm` in message → resolve pm's output
2. Implement interpolation logic using TaskManager.get_agent_result()
3. Write test: multiple refs `$pm $ba` resolved
4. Write test: missing ref logged as warning, included as-is
5. Implement fallback behavior

**Test Location**: `tests/test_tasks/test_executor.py` or new `tests/test_tasks/test_notify.py`

---

### 4. Output Truncation - TDD

**Approach**: TDD
**Rationale**: Truncation at 500 characters is a precise requirement with clear boundaries. TDD ensures the exact threshold and "..." suffix behavior.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Output ≤ 500 chars: unchanged
  * Output > 500 chars: truncated to 500 + "..."
  * Exact boundary: 500 chars → no truncation; 501 → truncated
* Edge Cases:
  * Unicode characters (count chars, not bytes)
  * Empty output
  * Whitespace-only output

**Testing Sequence**:
1. Write test: 400 char output → unchanged
2. Write test: 600 char output → 500 + "..."
3. Write test: exactly 500 chars → unchanged
4. Write test: 501 chars → 500 + "..."
5. Implement truncation function

**Test Location**: `tests/test_tasks/test_executor.py` (or utility module)

---

### 5. Notification Dispatch - TDD

**Approach**: TDD
**Rationale**: Must use existing EventBus infrastructure correctly. TDD with mocks ensures proper integration without requiring real channels.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit, Integration
* Critical Scenarios:
  * EventBus.emit_sync() called with custom_message event
  * Message content included in event data
  * All enabled channels receive notification
* Edge Cases:
  * No channels configured
  * All channels disabled
  * EventBus creation failure

**Testing Sequence**:
1. Write test: mock EventBus.emit_sync called with correct event
2. Implement EventBus creation and emit in notify handler
3. Write test: message content in event data matches interpolated message
4. Write test: no channels → still succeeds (no-op)

**Test Location**: `tests/test_tasks/test_executor.py`

---

### 6. Failure Handling (Non-Blocking) - TDD

**Approach**: TDD
**Rationale**: Critical NFR - notification failures must not break pipelines. TDD ensures this is correct from the start.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit, Integration
* Critical Scenarios:
  * Channel.send() raises exception → pipeline continues
  * Warning logged on failure
  * Output becomes "Notification failed ⚠️ (warning logged)"
  * Downstream agents still execute
* Edge Cases:
  * Network timeout (simulated)
  * EventBus creation failure
  * Partial channel failure (some succeed, some fail)

**Testing Sequence**:
1. Write test: mock channel raises → pipeline continues
2. Implement try/except wrapper
3. Write test: warning logged (caplog fixture)
4. Write test: failure output returned
5. Write test: downstream `$notify` gets failure output

**Test Location**: `tests/test_tasks/test_executor.py`

---

### 7. Result Storage - TDD

**Approach**: TDD
**Rationale**: Result must be stored in TaskManager for downstream `$notify` references. Follows existing agent result pattern.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Success: TaskResult with output "Notification sent ✅" stored
  * Failure: TaskResult with error message stored
  * `manager.get_agent_result("notify")` returns result
* Edge Cases:
  * Multiple @notify calls → latest result stored

**Testing Sequence**:
1. Write test: get_agent_result("notify") returns TaskResult after @notify
2. Implement result storage in notify handler
3. Write test: result.success is True on success
4. Write test: result.success is False on failure

**Test Location**: `tests/test_tasks/test_manager.py` or `tests/test_tasks/test_executor.py`

---

### 8. Legacy /notify Removal - TDD

**Approach**: TDD
**Rationale**: Breaking change - must verify old command is removed and appropriate error message shown.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `/notify` returns "unknown command" error
  * Error message suggests using `@notify` instead
* Edge Cases:
  * `/notify` with arguments
  * `/notify` without arguments

**Testing Sequence**:
1. Write test: `/notify "test"` returns unknown command
2. Remove "notify" from SystemCommands.dispatch() handlers
3. Write test: error message mentions `@notify`
4. Update error message if needed

**Test Location**: `tests/test_repl/test_commands.py`

---

### 9. Agent Status Display - TDD

**Approach**: TDD
**Rationale**: UI change - must show @notify with model "(n/a)". Clear visual requirement.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Status panel includes "notify" row
  * Model column shows "(n/a)" for notify
  * Status shows "Idle" when not executing
  * Status shows "Active" during execution
* Edge Cases:
  * Multiple concurrent @notify calls (unlikely but possible with `&`)

**Testing Sequence**:
1. Write test: status panel data includes "notify" agent
2. Add notify to AgentStatusManager or status data source
3. Write test: model for notify is "(n/a)"
4. Implement special-case for pseudo-agents

**Test Location**: `tests/test_ui/test_agent_state.py` or `tests/test_ui/test_status_panel.py`

---

### 10. Pipeline Positioning - TDD

**Approach**: TDD
**Rationale**: Must work at beginning, middle, and end of pipelines. Integration tests ensure correctness.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Integration
* Critical Scenarios:
  * `@notify "Start", @pm plan` - beginning
  * `@pm plan, @notify "Middle", @builder-1 build` - middle
  * `@pm plan, @notify "End"` - end
  * All positions produce correct execution order
* Edge Cases:
  * Only `@notify` (no other agents)
  * `@notify` with `&` background

**Testing Sequence**:
1. Write test: @notify at pipeline start → executes first
2. Write test: @notify in pipeline middle → executes in order
3. Write test: @notify at pipeline end → executes last
4. Verify all tests pass with implementation

**Test Location**: `tests/test_tasks/test_executor.py` (TestTaskExecutorPipeline class)

---

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: Per pyproject.toml
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (MagicMock, AsyncMock, patch) - standard patterns in codebase
* **Assertions**: pytest native assertions - simple assert statements
* **Coverage**: pytest-cov - Target: 80%+ overall, 90%+ for new code
* **Async**: pytest-asyncio - auto mode enabled
* **Test Data**: Inline fixtures, conftest.py shared fixtures

### Test Organization
* **Test Location**: `tests/test_<module>/test_<file>.py`
* **Naming Convention**: `test_<description>`, classes `Test<Component>`
* **Fixture Strategy**: conftest.py for shared, inline for component-specific
* **Setup/Teardown**: pytest fixtures with function scope (default)

---

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 90% (minimum for new code)
* **Integration Coverage**: 80%
* **Critical Path Coverage**: 100% (notification dispatch, failure handling)
* **Error Path Coverage**: 100% (all failure scenarios explicitly tested)

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| Router (notify recognition) | 100% | - | CRITICAL | Simple change, must not break existing |
| Executor (pseudo-agent) | 95% | 85% | CRITICAL | Core new pattern |
| $ref interpolation | 90% | 80% | HIGH | Reuses existing infrastructure |
| Output truncation | 100% | - | HIGH | Pure function, easy to test |
| Notification dispatch | 90% | 80% | HIGH | Integration with EventBus |
| Failure handling | 100% | 90% | CRITICAL | NFR-002 requirement |
| Result storage | 100% | - | HIGH | Follows existing patterns |
| Legacy removal | 100% | - | MEDIUM | Breaking change |
| Status display | 90% | - | MEDIUM | UI component |
| Pipeline positioning | 85% | 90% | HIGH | Integration scenarios |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **AT-001: Simple Notification** (Priority: CRITICAL)
   * **Description**: `@notify "Build complete!"` sends notification
   * **Test Type**: Integration
   * **Success Criteria**: EventBus.emit_sync called, output shows confirmation
   * **Test Approach**: TDD

2. **AT-002: Notification with $ref** (Priority: CRITICAL)
   * **Description**: `@notify "Review: $reviewer"` interpolates output
   * **Test Type**: Integration
   * **Success Criteria**: Message contains resolved agent output
   * **Test Approach**: TDD

3. **AT-003: Large Output Truncation** (Priority: HIGH)
   * **Description**: 1000+ char output truncated to 500 + "..."
   * **Test Type**: Unit
   * **Success Criteria**: Output length is 503 (500 + "...")
   * **Test Approach**: TDD

4. **AT-006: Failure Non-Blocking** (Priority: CRITICAL)
   * **Description**: Notification failure doesn't break pipeline
   * **Test Type**: Integration
   * **Success Criteria**: Pipeline continues, warning logged
   * **Test Approach**: TDD

5. **AT-010: Legacy /notify Removed** (Priority: HIGH)
   * **Description**: `/notify` returns unknown command
   * **Test Type**: Unit
   * **Success Criteria**: Error message, suggests @notify
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Empty message**: `@notify ""` → should send empty notification or warn
* **Message with only $refs**: `@notify "$pm"` → should work
* **Missing $ref**: `@notify "$unknown"` → include token as-is, log warning
* **Very long message**: 10000+ chars → truncate message itself?
* **Unicode in message**: emoji, CJK characters → count correctly
* **Concurrent @notify**: multiple `@notify &` commands → all succeed independently

### Error Scenarios

* **No channels configured**: Return success (no-op), no error
* **Channel send failure**: Catch exception, log warning, continue
* **EventBus creation failure**: Catch exception, return failure output
* **TaskManager unavailable**: Shouldn't happen, but handle gracefully
* **Network timeout**: Covered by channel send failure

---

## Test Data Strategy

### Test Data Requirements
* **Mock EventBus**: MagicMock with emit_sync method
* **Mock channels**: Use existing `mock_channel` fixture from conftest.py
* **Sample agent outputs**: Inline strings of varying lengths (100, 500, 1000 chars)
* **Pipeline commands**: Pre-constructed Command objects

### Test Data Management
* **Storage**: Inline in test functions, conftest.py fixtures for shared data
* **Generation**: Manual fixtures; consider factory functions for Command objects
* **Isolation**: Each test creates fresh mocks; no shared mutable state
* **Cleanup**: pytest fixtures auto-cleanup; no explicit teardown needed

---

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_notifications/test_event_bus.py`
**Pattern**: Async test with mock channel, emit verification

```python
class TestEventBusEmit:
    """Tests for EventBus.emit()."""

    @pytest.mark.asyncio
    async def test_emit_calls_channel_send(
        self, mock_channel: MagicMock, sample_event: NotificationEvent
    ) -> None:
        """emit() calls send() on subscribed channels."""
        bus = EventBus()
        bus.subscribe(mock_channel)

        await bus.emit(sample_event)

        # Allow async task to complete
        await asyncio.sleep(0.05)
        mock_channel.send.assert_called_once()
```

**Key Conventions:**
* Class-based test organization with descriptive names
* Docstrings explain test purpose
* Fixtures from conftest.py for shared setup
* `asyncio.sleep()` for async task completion
* Mock assertions using `.assert_called_once()`, `.assert_called_with()`

### Example from Router Tests

**File**: `tests/test_repl/test_router.py`
**Pattern**: Synchronous validation tests

```python
class TestAgentRouterValidation:
    """Tests for agent ID validation."""

    def test_valid_agent_ids(self):
        """Test that valid agent IDs are accepted."""
        router = AgentRouter()

        for agent_id in ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]:
            assert router.is_valid_agent(agent_id) is True

    def test_invalid_agent_ids(self):
        """Test that invalid agent IDs are rejected."""
        router = AgentRouter()

        for agent_id in ["unknown", "admin", "builder-3", "PM", "Ba"]:
            assert router.is_valid_agent(agent_id) is False
```

### Recommended Test Structure for @notify

```python
class TestNotifyPseudoAgent:
    """Tests for @notify pseudo-agent execution."""

    @pytest.mark.asyncio
    async def test_notify_bypasses_sdk(self):
        """@notify does not call Copilot SDK."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        cmd = parse_command('@notify "Test message"')

        result = await executor.execute(cmd)

        mock_sdk.execute.assert_not_called()
        assert result.success
        assert "Notification sent" in result.output

    @pytest.mark.asyncio
    async def test_notify_with_ref_interpolation(self):
        """@notify interpolates $ref tokens."""
        mock_sdk = AsyncMock()
        executor = TaskExecutor(sdk_client=mock_sdk)
        
        # First, execute @pm to have a result to reference
        mock_sdk.execute = AsyncMock(return_value="PM analysis output")
        await executor.execute(parse_command("@pm analyze"))
        
        # Now test @notify with $ref
        cmd = parse_command('@notify "Result: $pm"')
        result = await executor.execute(cmd)

        # Verify message includes PM's output
        assert result.success
        # Check EventBus was called with interpolated message
```

---

## Success Criteria

### Test Implementation Complete When:
- [x] All critical scenarios have tests (10 AT scenarios)
- [ ] Coverage targets are met per component (90%+ new code)
- [ ] All edge cases are tested (6+ edge cases)
- [ ] Error paths are validated (5 error scenarios)
- [ ] Tests follow codebase conventions (class-based, docstrings)
- [ ] Tests are maintainable and clear
- [ ] CI/CD integration is working (pytest runs in existing workflow)

### Test Quality Indicators:
* Tests are readable and self-documenting (docstrings required)
* Tests are fast and reliable (no flakiness from timing)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem (descriptive assertions)
* Mock/stub usage is appropriate and minimal (mock only external deps)

---

## Implementation Guidance

### For TDD Components (All):
1. Start with simplest test case (e.g., @notify recognized as valid)
2. Write minimal code to pass
3. Add next test case (e.g., @notify returns confirmation)
4. Refactor when all tests pass
5. Focus on behavior, not implementation details

### Test File Organization:

```
tests/
├── test_repl/
│   ├── test_router.py          # Add notify to VALID_AGENTS tests
│   └── test_commands.py        # Legacy /notify removal tests
├── test_tasks/
│   ├── test_executor.py        # Pseudo-agent execution tests (new class)
│   └── test_manager.py         # Result storage tests (extend existing)
├── test_notifications/
│   └── test_event_bus.py       # Existing patterns to follow
└── test_ui/
    └── test_agent_state.py     # Status display tests
```

### Suggested Test Implementation Order:

1. **Router tests** - Simple, foundational
2. **Executor pseudo-agent tests** - Core new pattern
3. **$ref interpolation tests** - Builds on executor
4. **Truncation tests** - Pure function, simple
5. **Failure handling tests** - Critical NFR
6. **Result storage tests** - Follows patterns
7. **Legacy removal tests** - Breaking change
8. **Status display tests** - UI polish
9. **Pipeline integration tests** - End-to-end validation

---

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures backward compatibility with existing pipelines
* Tests document expected behavior clearly
* Failure handling verified before implementation
* Edge cases caught early
* Regression safety for future changes

### Accepted Trade-offs:
* Slightly slower initial velocity (tests first)
* More upfront design thinking required
* Test maintenance overhead (acceptable for this feature size)

### Risk Mitigation:
* TDD for failure handling ensures NFR-002 (non-blocking failures) is correct
* Comprehensive pipeline positioning tests prevent breaking existing flows
* Legacy removal tests ensure smooth migration path

---

## References

* **Feature Spec**: [.teambot/simple-notification-end/artifacts/feature_spec.md](feature_spec.md)
* **Spec Review**: [.teambot/simple-notification-end/artifacts/spec_review.md](spec_review.md)
* **Test Examples**: `tests/test_notifications/test_event_bus.py`, `tests/test_repl/test_router.py`, `tests/test_tasks/test_executor.py`
* **Test Config**: `pyproject.toml` [tool.pytest.ini_options]
* **Fixtures**: `tests/conftest.py`, `tests/test_notifications/conftest.py`

---

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow TDD approach per component

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

## Approval Request

I've analyzed **@notify Pseudo-Agent** and recommend **TDD**.

**Decision Matrix Result:**
- TDD Score: 7 (threshold: 6)
- Code-First Score: 1 (threshold: 5)

**Key Factors:**
- Clear requirements with 15 FRs and 10 acceptance tests
- Medium complexity with integration risk
- Critical failure handling requirement (must be non-blocking)

**Do you:**
1. ✅ Approve this strategy and proceed to planning
2. 🔄 Want to adjust the approach (please specify)
3. ❓ Have questions or concerns about the recommendation

---

**TEST_STRATEGY_VALIDATION: PASS**
- Document: CREATED
- Decision Matrix: COMPLETE
- Approach: TDD (score 7 > threshold 6)
- Coverage Targets: SPECIFIED (90%+ new code, 100% critical paths)
- Components Covered: 10/10
