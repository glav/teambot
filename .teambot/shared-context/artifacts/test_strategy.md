<!-- markdownlint-disable-file -->
# Test Strategy: Shared Context Reference Syntax (`$agent`)

**Strategy Date**: 2026-02-03  
**Feature Specification**: N/A (Objective-based)  
**Research Reference**: `.agent-tracking/research/20260203-shared-context-research.md`  
**Strategist**: Builder-1 (Test Strategy Agent)  

---

## Recommended Testing Approach

**Primary Approach**: **HYBRID** (TDD for core logic, Code-First for integrations)

---

## Testing Approach Decision Matrix

### Factor Scoring

| Factor | Question | Assessment | TDD Points | Code-First Points |
|--------|----------|------------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES - Syntax clearly defined (`$pm`), behavior specified | **3** | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM - Parser regex + async waiting logic | **2** | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | HIGH - Core user interaction feature | **2** | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO - Well-researched approach | 0 | 0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | PARTIALLY - Some components are simple | 0 | **1** |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | LOW - Quality matters | 0 | 0 |
| **Requirements Stability** | Are requirements likely to change during development? | STABLE - Syntax locked in | 0 | 0 |

### Score Summary

| Score Type | Total |
|------------|-------|
| **TDD Score** | **7** |
| **Code-First Score** | **1** |

### Decision Threshold Analysis

| TDD Score | Code-First Score | Threshold | Recommendation |
|-----------|------------------|-----------|----------------|
| 7 | 1 | TDD ≥ 6, Code-First < 4 | **TDD** qualifies |

**However**, given the mixed nature of components (parser: simple, async waiting: complex), the recommendation is **HYBRID**:
- **TDD** for: Parser reference detection, result storage, output injection
- **Code-First** for: Overlay updates, README documentation, routing changes

---

## Rationale

The shared context reference feature (`$agent` syntax) has **well-defined requirements** with clear acceptance criteria. The syntax is explicitly specified (`$pm`, `$ba`, `$builder-1`), and the expected behavior (wait for referenced agent, inject output) is documented in the research.

The feature has **moderate complexity** centered on:
1. **Regex parsing** - detecting `$agent` patterns (well-suited for TDD)
2. **Async waiting** - waiting for running tasks to complete (requires careful testing)
3. **Result storage** - tracking latest results by agent ID (critical data path)

The risk profile is **high** because this affects the core user interaction loop - a bug here could break the entire REPL experience. TDD provides the safety net needed for confident refactoring.

**Key Factors:**
* **Complexity**: MEDIUM - Mix of simple (regex) and complex (async waiting)
* **Risk**: HIGH - Core REPL functionality
* **Requirements Clarity**: CLEAR - Syntax and behavior well-specified
* **Time Pressure**: LOW - Quality is priority

---

## Feature Analysis Summary

### Complexity Assessment

| Aspect | Assessment | Details |
|--------|------------|---------|
| **Algorithm Complexity** | LOW-MEDIUM | Regex pattern matching + deduplication |
| **Integration Depth** | MEDIUM | Touches parser, executor, manager, overlay |
| **State Management** | MEDIUM | Agent results dictionary, waiting state |
| **Error Scenarios** | MEDIUM | Missing results, no running task, invalid agent |

### Risk Profile

| Factor | Level | Rationale |
|--------|-------|-----------|
| **Business Criticality** | HIGH | Core user-facing syntax |
| **User Impact** | HIGH | All interactive users affected |
| **Data Sensitivity** | LOW | No sensitive data involved |
| **Failure Cost** | MEDIUM-HIGH | Broken commands = poor UX |

### Requirements Clarity

| Factor | Status | Notes |
|--------|--------|-------|
| **Specification Completeness** | COMPLETE | Syntax and behavior defined |
| **Acceptance Criteria Quality** | PRECISE | 4 clear success criteria |
| **Edge Cases Identified** | 6 documented | Multiple refs, no output, running task |
| **Dependencies Status** | STABLE | Existing infrastructure is mature |

---

## Test Strategy by Component

### 1. Parser Reference Detection - **TDD** 🔴

**File**: `src/teambot/repl/parser.py`

**Approach**: TDD  
**Rationale**: Clear input/output contract, easy to test in isolation, critical correctness requirement

**Test Requirements:**
* Coverage Target: **95%**
* Test Types: Unit
* Critical Scenarios:
  * Single reference: `@pm task $ba` → references=["ba"]
  * Multiple references: `@pm task $ba $writer` → references=["ba", "writer"]
  * Hyphenated agent: `@pm task $builder-1` → references=["builder-1"]
  * No reference: `@pm task` → references=[]
  * Duplicate deduplication: `$ba $ba` → references=["ba"]
* Edge Cases:
  * `$` in non-reference context (e.g., `$100`)
  * Reference at end of content
  * Reference in multiline content

**Testing Sequence (TDD):**
1. Write test: `test_parse_single_reference`
2. Implement: Add `REFERENCE_PATTERN` regex
3. Write test: `test_parse_multiple_references`
4. Implement: Extract all matches
5. Write test: `test_parse_duplicate_references_deduplicated`
6. Implement: Deduplication logic
7. Refactor for clarity

---

### 2. Command Dataclass Extension - **TDD** 🔴

**File**: `src/teambot/repl/parser.py` (Command class)

**Approach**: TDD  
**Rationale**: Data structure change, must be verified before dependent code

**Test Requirements:**
* Coverage Target: **100%**
* Test Types: Unit
* Critical Scenarios:
  * Command has `references` field
  * Default value is empty list
  * References populated from parsing

**Testing Sequence (TDD):**
1. Write test: `test_command_has_references_field`
2. Add field to dataclass
3. Write test: `test_command_references_default_empty`
4. Verify default factory

---

### 3. TaskManager Agent Result Storage - **TDD** 🔴

**File**: `src/teambot/tasks/manager.py`

**Approach**: TDD  
**Rationale**: Critical data path, must work correctly for feature to function

**Test Requirements:**
* Coverage Target: **90%**
* Test Types: Unit
* Critical Scenarios:
  * Result stored by agent_id on task completion
  * Latest result overwrites previous
  * `get_agent_result()` returns correct result
  * `get_running_task_for_agent()` finds running task
  * Returns None when no result/task exists
* Edge Cases:
  * Multiple tasks for same agent
  * Agent with no completed tasks

**Testing Sequence (TDD):**
1. Write test: `test_agent_result_stored_on_completion`
2. Add `_agent_results` dict and update in `execute_task()`
3. Write test: `test_get_agent_result_returns_latest`
4. Implement `get_agent_result()` method
5. Write test: `test_get_running_task_for_agent`
6. Implement `get_running_task_for_agent()` method

---

### 4. TaskExecutor Reference Handling - **TDD** 🔴

**File**: `src/teambot/tasks/executor.py`

**Approach**: TDD  
**Rationale**: Complex async logic, high failure cost, needs regression safety

**Test Requirements:**
* Coverage Target: **85%**
* Test Types: Unit + Integration
* Critical Scenarios:
  * Reference waits for running task
  * Reference injects completed output
  * Multiple references handled
  * No output available - graceful fallback
* Edge Cases:
  * Reference to agent that never ran
  * Reference to failed task
  * Concurrent references

**Testing Sequence (TDD):**
1. Write test: `test_reference_injects_output`
2. Implement `_inject_references()` method
3. Write test: `test_reference_waits_for_running_task`
4. Implement `_wait_for_references()` async method
5. Write test: `test_reference_no_output_available`
6. Add fallback placeholder text
7. Write test: `test_multiple_references`
8. Verify iteration over references list

---

### 5. REPL Loop Routing - **Code-First** 🟢

**File**: `src/teambot/repl/loop.py`

**Approach**: Code-First  
**Rationale**: Simple conditional change, low risk, easy to verify manually

**Test Requirements:**
* Coverage Target: **70%**
* Test Types: Integration
* Critical Scenarios:
  * Command with references routes to executor
  * Command without references uses existing path
* Edge Cases:
  * References combined with background (&)
  * References in pipeline stages

**Testing Sequence (Code-First):**
1. Implement routing condition change
2. Write integration test verifying routing
3. Verify existing tests still pass

---

### 6. TaskStatus WAITING State - **TDD** 🔴

**File**: `src/teambot/tasks/models.py`

**Approach**: TDD  
**Rationale**: Enum change, must verify `is_terminal()` still works

**Test Requirements:**
* Coverage Target: **100%**
* Test Types: Unit
* Critical Scenarios:
  * WAITING status exists
  * WAITING is not terminal
  * Task can transition through WAITING → RUNNING

**Testing Sequence (TDD):**
1. Write test: `test_waiting_status_exists`
2. Add WAITING to enum
3. Write test: `test_waiting_is_not_terminal`
4. Verify `is_terminal()` returns False for WAITING

---

### 7. Overlay Status Display - **Code-First** 🟢

**File**: `src/teambot/visualization/overlay.py`

**Approach**: Code-First  
**Rationale**: UI component, visual verification important, low algorithmic complexity

**Test Requirements:**
* Coverage Target: **70%**
* Test Types: Unit
* Critical Scenarios:
  * Waiting count displayed
  * Waiting-for relationship shown
  * Status updates on wait start/end

**Testing Sequence (Code-First):**
1. Implement waiting state fields
2. Implement display logic
3. Write tests verifying output format
4. Visual testing in REPL

---

### 8. README Documentation - **Code-First** 🟢

**File**: `README.md`

**Approach**: Code-First  
**Rationale**: Documentation, no code logic, manual review sufficient

**Test Requirements:**
* Coverage Target: N/A
* Test Types: Manual review
* Critical Scenarios:
  * Syntax documented with examples
  * Comparison table with `->` syntax
  * Use case guidance

---

## Test Infrastructure

### Existing Test Framework

| Aspect | Details |
|--------|---------|
| **Framework** | pytest |
| **Version** | Latest (via pyproject.toml) |
| **Configuration** | `pyproject.toml [tool.pytest.ini_options]` |
| **Runner** | `uv run pytest` |
| **Async Support** | `asyncio_mode = "auto"` |

### Testing Tools Required

| Tool | Usage |
|------|-------|
| **Mocking** | `unittest.mock.AsyncMock`, `MagicMock` |
| **Assertions** | pytest built-in assertions |
| **Coverage** | `pytest-cov` (already configured) |
| **Fixtures** | `tests/conftest.py` shared fixtures |
| **Test Data** | Inline test data, fixture factories |

### Test Organization

| Aspect | Convention |
|--------|------------|
| **Test Location** | `tests/` (mirrors `src/teambot/`) |
| **Naming Convention** | `test_*.py`, `Test*` classes, `test_*` functions |
| **Fixture Strategy** | Shared fixtures in `conftest.py` |
| **Setup/Teardown** | pytest fixtures with `yield` |

---

## Coverage Requirements

### Overall Targets

| Metric | Target |
|--------|--------|
| **Unit Test Coverage** | 85% minimum |
| **Integration Coverage** | 70% |
| **Critical Path Coverage** | 100% |
| **Error Path Coverage** | 80% |

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Approach |
|-----------|--------|---------------|----------|----------|
| Parser (references) | 95% | - | CRITICAL | TDD |
| Command dataclass | 100% | - | HIGH | TDD |
| TaskManager (agent results) | 90% | - | CRITICAL | TDD |
| TaskExecutor (ref handling) | 85% | 70% | CRITICAL | TDD |
| REPL Loop (routing) | 70% | 80% | HIGH | Code-First |
| TaskStatus (WAITING) | 100% | - | MEDIUM | TDD |
| Overlay (waiting display) | 70% | - | MEDIUM | Code-First |

### Critical Test Scenarios

**Priority CRITICAL:**

1. **Reference Detection in Parser**
   * **Description**: Parser correctly extracts `$agent` references from content
   * **Test Type**: Unit
   * **Success Criteria**: `references` list contains all referenced agent IDs
   * **Test Approach**: TDD

2. **Output Injection from Reference**
   * **Description**: Referenced agent's output is prepended to prompt
   * **Test Type**: Unit + Integration
   * **Success Criteria**: SDK receives prompt with injected output
   * **Test Approach**: TDD

3. **Wait for Running Task**
   * **Description**: Executor waits for referenced agent's running task
   * **Test Type**: Integration
   * **Success Criteria**: Referencing task starts only after referenced task completes
   * **Test Approach**: TDD

4. **Routing Through Executor**
   * **Description**: Commands with references go through TaskExecutor
   * **Test Type**: Integration
   * **Success Criteria**: Simple `@pm $ba` routes to executor, not direct SDK
   * **Test Approach**: Code-First

### Edge Cases to Cover

| Edge Case | Expected Behavior |
|-----------|------------------|
| No output available for referenced agent | Inject placeholder: `[No output available]` |
| Reference to agent that never ran | Same placeholder, no error |
| Duplicate references (`$ba $ba`) | Deduplicated to single reference |
| Reference with invalid agent ID | Pass through, let router validate |
| Reference in pipeline stage | Detect and handle in pipeline parsing |
| `$` in non-reference context (`$100`) | Do not treat as reference |

### Error Scenarios

| Scenario | Expected Handling |
|----------|-------------------|
| Referenced agent task fails | Inject failure message, continue execution |
| Timeout waiting for running task | Eventually complete (configurable timeout) |
| Invalid reference syntax | Ignore, treat as literal text |

---

## Test Data Strategy

### Test Data Requirements

| Data Type | Strategy |
|-----------|----------|
| Commands | Inline strings in tests |
| TaskResult | Factory fixture or inline construction |
| Mock SDK responses | `AsyncMock` return values |

### Test Data Management

| Aspect | Strategy |
|--------|----------|
| **Storage** | Inline in test files |
| **Generation** | Manual creation, fixtures for common patterns |
| **Isolation** | Each test creates own data |
| **Cleanup** | pytest fixtures with `yield` |

---

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_repl/test_parser.py`  
**Pattern**: Class-based grouping, arrange-act-assert

```python
class TestParseAgentCommands:
    """Tests for @agent command parsing."""

    def test_parse_agent_command_basic(self):
        """Test parsing basic @agent command."""
        result = parse_command("@pm Create a project plan")

        assert result.type == CommandType.AGENT
        assert result.agent_id == "pm"
        assert result.content == "Create a project plan"
```

**Key Conventions:**
* Descriptive class names grouping related tests
* Clear docstrings explaining test purpose
* Simple arrange-act-assert structure
* Direct assertions without helper methods

### Recommended Test Structure for This Feature

**Parser Reference Tests:**

```python
class TestParseReferences:
    """Tests for $agent reference parsing."""

    def test_parse_single_reference(self):
        """Test parsing single $agent reference."""
        result = parse_command("@pm Summarize $ba output")
        
        assert result.references == ["ba"]
        assert "$ba" in result.content

    def test_parse_multiple_references(self):
        """Test parsing multiple references."""
        result = parse_command("@reviewer Check $builder-1 against $pm")
        
        assert result.references == ["builder-1", "pm"]

    def test_parse_hyphenated_reference(self):
        """Test parsing reference with hyphenated agent ID."""
        result = parse_command("@pm Use $builder-1 work")
        
        assert result.references == ["builder-1"]

    def test_parse_no_reference(self):
        """Test command without references."""
        result = parse_command("@pm Create a plan")
        
        assert result.references == []

    def test_parse_duplicate_references_deduplicated(self):
        """Test duplicate references are deduplicated."""
        result = parse_command("@pm Check $ba then verify $ba again")
        
        assert result.references == ["ba"]
```

**Executor Reference Tests:**

```python
class TestExecutorReferences:
    """Tests for $ref execution."""

    @pytest.mark.asyncio
    async def test_reference_injects_output(self):
        """Test that referenced output is injected."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")
        
        executor = TaskExecutor(sdk_client=mock_sdk)
        
        # First, run a task for ba
        cmd1 = parse_command("@ba Analyze requirements")
        await executor.execute(cmd1)
        
        # Now reference ba's output
        cmd2 = parse_command("@pm Summarize $ba")
        await executor.execute(cmd2)
        
        # Check that PM received BA's output
        call_args = mock_sdk.execute.call_args_list[-1]
        prompt = call_args[0][1]
        assert "=== Output from @ba ===" in prompt

    @pytest.mark.asyncio
    async def test_reference_waits_for_running_task(self):
        """Test that reference waits for running task."""
        import asyncio
        
        call_order = []
        
        async def tracked_execute(agent_id, prompt):
            call_order.append(f"{agent_id}_start")
            if agent_id == "ba":
                await asyncio.sleep(0.2)
            call_order.append(f"{agent_id}_end")
            return f"{agent_id} output"
        
        mock_sdk = AsyncMock()
        mock_sdk.execute = tracked_execute
        
        executor = TaskExecutor(sdk_client=mock_sdk)
        
        # Start BA in background
        cmd1 = parse_command("@ba Analyze &")
        await executor.execute(cmd1)
        
        # Small delay to ensure BA starts
        await asyncio.sleep(0.05)
        
        # PM references BA (should wait)
        cmd2 = parse_command("@pm Summarize $ba")
        await executor.execute(cmd2)
        
        # BA should complete before PM accesses its output
        ba_end_idx = call_order.index("ba_end")
        pm_start_idx = call_order.index("pm_start")
        assert ba_end_idx < pm_start_idx

    @pytest.mark.asyncio
    async def test_reference_no_output_available(self):
        """Test graceful handling when no output available."""
        mock_sdk = AsyncMock()
        mock_sdk.execute = AsyncMock(return_value="Done")
        
        executor = TaskExecutor(sdk_client=mock_sdk)
        
        # Reference agent that hasn't run
        cmd = parse_command("@pm Summarize $ba")
        result = await executor.execute(cmd)
        
        # Should still execute with placeholder
        call_args = mock_sdk.execute.call_args
        prompt = call_args[0][1]
        assert "[No output available]" in prompt or "not available" in prompt.lower()
```

---

## Success Criteria

### Test Implementation Complete When:

- [ ] All critical scenarios have tests
- [ ] Coverage targets are met per component
- [ ] All edge cases are tested
- [ ] Error paths are validated
- [ ] Tests follow codebase conventions (class grouping, docstrings)
- [ ] Tests are maintainable and clear
- [ ] CI passes with coverage report

### Test Quality Indicators:

| Indicator | Requirement |
|-----------|-------------|
| Readable | Self-documenting with docstrings |
| Fast | No flaky async timing issues |
| Independent | No test order dependencies |
| Clear failures | Assertion messages indicate problem |
| Minimal mocking | Mock only external dependencies |

---

## Implementation Guidance

### For TDD Components (Parser, TaskManager, Executor):

1. **Start with simplest test case** (single reference)
2. **Write minimal code to pass** (just the regex)
3. **Add next test case** (multiple references)
4. **Refactor when all tests pass** (deduplication)
5. **Focus on behavior, not implementation**

### For Code-First Components (REPL routing, Overlay):

1. **Implement core functionality** (routing condition)
2. **Add happy path test** (command routes correctly)
3. **Identify edge cases from implementation** (combined with &)
4. **Add edge case tests**
5. **Verify coverage meets target**

### For Hybrid Approach (Overall):

1. **Start with TDD components** (parser → manager → executor)
2. **Proceed to Code-First components** (routing → overlay)
3. **Ensure integration tests cover boundaries**
4. **Validate overall feature behavior end-to-end**

---

## Considerations and Trade-offs

### Selected Approach Benefits:

* **TDD for core logic** ensures correctness of critical paths
* **Code-First for UI/routing** allows faster iteration on visual elements
* **High coverage targets** provide regression safety for future changes
* **Async testing patterns** established in existing codebase

### Accepted Trade-offs:

* TDD may slow initial parser development slightly
* Code-First for overlay means less upfront test coverage
* Integration tests needed to verify full flow

### Risk Mitigation:

* **Parser bugs**: TDD catches regex edge cases early
* **Async race conditions**: Explicit timing tests with controlled execution
* **Breaking existing tests**: Run full suite after each component

---

## References

* **Research Doc**: [.agent-tracking/research/20260203-shared-context-research.md](../research/20260203-shared-context-research.md)
* **Test Examples**: 
  * `tests/test_repl/test_parser.py`
  * `tests/test_tasks/test_executor.py`
  * `tests/test_tasks/test_manager.py`
  * `tests/test_tasks/test_output_injector.py`
* **Test Config**: `pyproject.toml [tool.pytest.ini_options]`
* **Fixtures**: `tests/conftest.py`

---

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow recommended approach per component

---

**Strategy Status**: DRAFT  
**Approved By**: PENDING  
**Ready for Planning**: YES (pending approval)
