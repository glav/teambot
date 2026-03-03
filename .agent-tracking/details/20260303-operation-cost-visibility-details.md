<!-- markdownlint-disable-file -->
# Task Details: Operation Cost Visibility

## Research Reference

**Source Research**: .agent-tracking/research/20260303-operation-cost-visibility-research.md
**Test Strategy**: .teambot/operation-cost-visibility/artifacts/test_strategy.md

---

## Phase 1: Data Models (TDD)

### Task 1.1: Create TokenUsage Unit Tests

Create comprehensive unit tests for the TokenUsage dataclass before implementation (TDD).

* **Files**:
  * `tests/test_tokens/__init__.py` - Package init
  * `tests/test_tokens/test_models.py` - TokenUsage tests
* **Test Cases**:
  * `test_create_with_all_fields` - All token fields populated
  * `test_create_with_none_fields` - All fields None (unavailable)
  * `test_create_with_partial_data` - Some fields populated
  * `test_total_tokens_calculation` - Verify total = input + output
  * `test_total_tokens_when_none` - Returns None when both None
  * `test_to_dict_serialization` - JSON-ready dict output
  * `test_from_dict_deserialization` - Create from JSON dict
  * `test_from_sdk_usage` - Create from SDK Usage object
  * `test_addition_operator` - Aggregate two TokenUsage instances
  * `test_addition_with_none_values` - Handle None in aggregation
* **Success**:
  * Tests exist and initially fail (TDD red phase)
  * All test cases cover edge cases from test strategy
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 120-143) - SDK Usage dataclass structure
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 359-428) - TokenUsage design
* **Dependencies**:
  * None

---

### Task 1.2: Implement TokenUsage Dataclass

Implement the TokenUsage dataclass to make all tests pass (TDD green phase).

* **Files**:
  * `src/teambot/tokens/__init__.py` - Module init with exports
  * `src/teambot/tokens/models.py` - TokenUsage dataclass
* **Implementation**:
  ```python
  @dataclass
  class TokenUsage:
      input_tokens: int | None = None
      output_tokens: int | None = None
      cache_read_tokens: int | None = None
      cache_write_tokens: int | None = None
      
      @property
      def total_tokens(self) -> int | None: ...
      def to_dict(self) -> dict[str, Any]: ...
      @classmethod
      def from_dict(cls, data: dict) -> "TokenUsage": ...
      @classmethod
      def from_sdk_usage(cls, sdk_usage: Any) -> "TokenUsage": ...
      def __add__(self, other: "TokenUsage") -> "TokenUsage": ...
  ```
* **Success**:
  * All Task 1.1 tests pass
  * Dataclass properly handles None values
  * Addition operator correctly aggregates
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 359-428) - Complete implementation design
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 142) - Note about float→int conversion
* **Dependencies**:
  * Task 1.1 (tests must exist first)

---

### Task 1.3: Create TokenTracker Unit Tests

Create unit tests for TokenTracker class before implementation (TDD).

* **Files**:
  * `tests/test_tokens/test_tracker.py` - TokenTracker tests
* **Test Cases**:
  * `test_record_task_usage` - Record single task's token usage
  * `test_record_with_agent_id` - Associate usage with agent
  * `test_record_with_stage` - Associate usage with workflow stage
  * `test_get_total` - Calculate grand total across all tasks
  * `test_get_by_agent` - Get dict of usage by agent_id
  * `test_get_by_stage` - Get dict of usage by stage name
  * `test_empty_tracker` - Handle no recorded tasks
  * `test_all_none_usage` - Handle all tasks with None tokens
  * `test_mixed_availability` - Some tasks have tokens, some don't
  * `test_reset` - Clear all recorded data
* **Success**:
  * Tests exist and initially fail (TDD red phase)
  * Tests cover aggregation edge cases
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 337-357) - Data flow design
  * .teambot/operation-cost-visibility/artifacts/test_strategy.md (Lines 175-200) - Aggregation test requirements
* **Dependencies**:
  * Task 1.2 (TokenUsage must exist)

---

### Task 1.4: Implement TokenTracker Class

Implement TokenTracker to aggregate token usage across tasks.

* **Files**:
  * `src/teambot/tokens/tracker.py` - TokenTracker class
  * `src/teambot/tokens/__init__.py` - Add export
* **Implementation**:
  ```python
  class TokenTracker:
      def __init__(self) -> None:
          self._by_agent: dict[str, TokenUsage] = {}
          self._by_stage: dict[str, TokenUsage] = {}
          self._total: TokenUsage = TokenUsage()
          self._warning_logged: bool = False
      
      def record(
          self,
          usage: TokenUsage | None,
          agent_id: str,
          stage: str | None = None,
      ) -> None: ...
      
      def get_total(self) -> TokenUsage: ...
      def get_by_agent(self) -> dict[str, TokenUsage]: ...
      def get_by_stage(self) -> dict[str, TokenUsage]: ...
      def reset(self) -> None: ...
  ```
* **Success**:
  * All Task 1.3 tests pass
  * Aggregation is mathematically correct
  * None values handled gracefully
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 337-357) - Data flow
* **Dependencies**:
  * Task 1.3 (tests must exist first)

---

## Phase 2: SDK Integration (TDD)

### Task 2.1: Create SDK Extraction Unit Tests

Create tests for token extraction from SDK events before modifying SDK client.

* **Files**:
  * `tests/test_tokens/test_extraction.py` - Extraction tests
  * `tests/test_copilot/test_sdk_client_tokens.py` - SDK integration tests
* **Test Cases**:
  * `test_extract_from_assistant_usage_event` - Parse ASSISTANT_USAGE event
  * `test_extract_returns_none_when_no_usage` - Handle missing usage data
  * `test_extract_partial_data` - Handle partial token data
  * `test_extract_converts_float_to_int` - SDK uses float, we use int
  * `test_streaming_returns_token_usage` - execute_streaming returns usage
  * `test_streaming_returns_none_when_unavailable` - Graceful fallback
* **Success**:
  * Tests exist and initially fail (TDD red phase)
  * Mock SDK events defined correctly
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 144-163) - SDK event types
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 166-179) - Event data structure
  * .teambot/operation-cost-visibility/artifacts/test_strategy.md (Lines 102-126) - SDK extraction test requirements
* **Dependencies**:
  * Phase 1 completion

---

### Task 2.2: Modify SDK Client to Capture ASSISTANT_USAGE Events

Add token capture to the SDK client's event handler.

* **Files**:
  * `src/teambot/copilot/sdk_client.py` - Modify `_execute_streaming_once()`
* **Changes**:
  * Add `usage_holder: list[TokenUsage | None] = [None]` before event handler
  * Add handler for `ASSISTANT_USAGE` event type:
    ```python
    elif "ASSISTANT_USAGE" in event_type_upper:
        if hasattr(event.data, "input_tokens") and event.data.input_tokens is not None:
            from teambot.tokens.models import TokenUsage
            usage_holder[0] = TokenUsage(
                input_tokens=int(event.data.input_tokens) if event.data.input_tokens else None,
                output_tokens=int(event.data.output_tokens) if event.data.output_tokens else None,
                cache_read_tokens=int(event.data.cache_read_tokens) if event.data.cache_read_tokens else None,
                cache_write_tokens=int(event.data.cache_write_tokens) if event.data.cache_write_tokens else None,
            )
    ```
  * Update return to include usage: `return "".join(accumulated), usage_holder[0]`
  * Update method signature and callers
* **Success**:
  * All Task 2.1 tests pass
  * Existing SDK functionality unchanged
  * Token data captured when available
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 432-482) - SDK modification design
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 185-205) - Current SDK client structure
* **Dependencies**:
  * Task 2.1 (tests must exist first)

---

### Task 2.3: Create TaskResult token_usage Tests

Create tests for TaskResult extension before modifying the model.

* **Files**:
  * `tests/test_tasks/test_models.py` - Add new tests (or separate file)
* **Test Cases**:
  * `test_task_result_with_token_usage` - TaskResult with TokenUsage
  * `test_task_result_without_token_usage` - TaskResult with None (default)
  * `test_task_result_backward_compat` - Existing instantiation unchanged
  * `test_task_result_serialization_with_tokens` - JSON includes token_usage
  * `test_task_result_deserialization_missing_tokens` - Old JSON loads correctly
* **Success**:
  * Tests exist and initially fail (TDD red phase)
  * Backward compatibility explicitly tested
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 234-248) - TaskResult current structure
  * .teambot/operation-cost-visibility/artifacts/test_strategy.md (Lines 148-171) - TaskResult test requirements
* **Dependencies**:
  * Task 2.2 (TokenUsage must be available from SDK)

---

### Task 2.4: Add token_usage Field to TaskResult

Extend TaskResult dataclass with optional token_usage field.

* **Files**:
  * `src/teambot/tasks/models.py` - Add field to TaskResult
* **Changes**:
  ```python
  from teambot.tokens.models import TokenUsage
  
  @dataclass
  class TaskResult:
      task_id: str
      output: str
      success: bool
      error: str | None = None
      completed_at: datetime = field(default_factory=datetime.now)
      token_usage: TokenUsage | None = None  # NEW FIELD
  ```
  * Update `to_dict()` to include token_usage (if present)
  * Update `from_dict()` to handle missing token_usage (backward compat)
* **Success**:
  * All Task 2.3 tests pass
  * Existing code continues to work
  * New field is optional with None default
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 234-248) - Current structure
* **Dependencies**:
  * Task 2.3 (tests must exist first)

---

## Phase 3: Display Components (Code-First)

### Task 3.1: Implement Orchestration Summary Display

Create Rich-based token summary panel for orchestration runs.

* **Files**:
  * `src/teambot/tokens/display.py` - Display functions
  * `src/teambot/tokens/__init__.py` - Add export
* **Implementation**:
  ```python
  def render_token_summary(
      total: TokenUsage,
      by_agent: dict[str, TokenUsage],
      by_stage: dict[str, TokenUsage] | None = None,
  ) -> Panel:
      """Render token usage summary as Rich Panel."""
  ```
  * Shows total tokens with input/output breakdown
  * Shows per-agent breakdown with bar visualization
  * Shows per-stage breakdown (if provided)
  * Shows "n/a" when total.total_tokens is None
* **Success**:
  * Function returns valid Rich Panel
  * Panel displays correctly in terminal
  * "n/a" path works for unavailable data
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 486-543) - Display design
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 266-274) - Rich library patterns
* **Dependencies**:
  * Phase 2 completion

---

### Task 3.2: Implement Session Summary Display

Create brief session summary for interactive REPL exit.

* **Files**:
  * `src/teambot/tokens/display.py` - Add function
* **Implementation**:
  ```python
  def render_session_summary(total: TokenUsage) -> str:
      """Render brief session summary line."""
  ```
  * Single line format: "Session Token Usage: X tokens (prompt: Y | completion: Z)"
  * Shows "Session Token Usage: n/a" when unavailable
* **Success**:
  * Function returns formatted string
  * Handles None tokens gracefully
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 545-562) - Session summary design
* **Dependencies**:
  * Task 3.1

---

### Task 3.3: Add Display Unit Tests

Create structural tests for display functions (Code-First approach).

* **Files**:
  * `tests/test_tokens/test_display.py` - Display tests
* **Test Cases**:
  * `test_render_summary_panel_structure` - Panel contains expected sections
  * `test_render_summary_with_data` - Shows actual token values
  * `test_render_summary_unavailable` - Shows "n/a" when None
  * `test_render_summary_per_agent_breakdown` - Agent section present
  * `test_render_session_summary_format` - Correct string format
  * `test_render_session_summary_unavailable` - "n/a" in output
* **Success**:
  * Tests pass
  * Coverage ≥80% for display module
* **Research References**:
  * .teambot/operation-cost-visibility/artifacts/test_strategy.md (Lines 201-222) - Display test strategy
* **Dependencies**:
  * Task 3.2

---

## Phase 4: Integration & Configuration

### Task 4.1: Integrate TokenTracker with ExecutionLoop

Wire token tracking into the orchestration execution loop.

* **Files**:
  * `src/teambot/orchestration/execution_loop.py` - Add tracking
* **Changes**:
  * Create TokenTracker instance at start of run
  * After each task execution, record token usage:
    ```python
    if result.token_usage:
        self._token_tracker.record(
            result.token_usage,
            agent_id=task.agent_id,
            stage=current_stage.name,
        )
    ```
  * At end of `run()`, display summary:
    ```python
    from teambot.tokens.display import render_token_summary
    summary = render_token_summary(
        self._token_tracker.get_total(),
        self._token_tracker.get_by_agent(),
        self._token_tracker.get_by_stage(),
    )
    console.print(summary)
    ```
* **Success**:
  * Token summary displays at end of orchestration run
  * Tracking does not affect run performance
  * Works when config enables tracking
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 79-86) - Entry point 1 trace
* **Dependencies**:
  * Phase 3 completion

---

### Task 4.2: Integrate Session Tracking with REPL Loop

Add session-level token tracking to interactive REPL.

* **Files**:
  * `src/teambot/repl/loop.py` - Add tracking and exit display
* **Changes**:
  * Create module-level or instance TokenTracker for session
  * Record tokens after each command execution
  * Display summary in `_cleanup()` method (called on exit):
    ```python
    from teambot.tokens.display import render_session_summary
    summary = render_session_summary(self._token_tracker.get_total())
    console.print(summary)
    ```
  * Handle Ctrl+C gracefully (signal handler already exists)
* **Success**:
  * Session summary displays on `/exit`
  * Session summary displays on Ctrl+C
  * Tokens accumulate across multiple commands
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 88-101) - Entry points 2-3 trace
  * .teambot/operation-cost-visibility/artifacts/test_strategy.md (Lines 223-246) - Session tracking tests
* **Dependencies**:
  * Task 4.1

---

### Task 4.3: Add Token Data Persistence to WorkflowState

Persist token tracking data in workflow_state.json metadata.

* **Files**:
  * `src/teambot/workflow/state_machine.py` - Add persistence methods
  * `src/teambot/tokens/tracker.py` - Add to_dict() method
* **Changes**:
  * Add `TokenTracker.to_dict()`:
    ```python
    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "total": self._total.to_dict(),
            "by_agent": {k: v.to_dict() for k, v in self._by_agent.items()},
            "by_stage": {k: v.to_dict() for k, v in self._by_stage.items()},
        }
    ```
  * In WorkflowState saving, add token data to metadata:
    ```python
    state.metadata["token_tracking"] = token_tracker.to_dict()
    ```
  * In WorkflowState loading, handle missing token_tracking gracefully
* **Success**:
  * Token data saves to workflow_state.json
  * Token data loads correctly from existing state
  * Old state files without token_tracking load without error
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 209-229) - WorkflowState metadata
  * .teambot/operation-cost-visibility/artifacts/test_strategy.md (Lines 247-270) - Persistence tests
* **Dependencies**:
  * Task 4.1

---

### Task 4.4: Add token_tracking Configuration Option

Add config option to enable/disable token tracking.

* **Files**:
  * `src/teambot/config/loader.py` - Add validation
  * `src/teambot/config/schema.py` (if exists) - Add schema
  * `teambot.json` - Document option
* **Changes**:
  * Add validation in `_validate()`:
    ```python
    if "token_tracking" in config:
        self._validate_token_tracking(config["token_tracking"])
    
    def _validate_token_tracking(self, token_tracking: dict[str, Any]) -> None:
        if not isinstance(token_tracking, dict):
            raise ConfigError("'token_tracking' must be an object")
        if "enabled" in token_tracking:
            if not isinstance(token_tracking["enabled"], bool):
                raise ConfigError("'token_tracking.enabled' must be a boolean")
    ```
  * Add defaults in `_apply_defaults()`:
    ```python
    if "token_tracking" not in config:
        config["token_tracking"] = {}
    if "enabled" not in config["token_tracking"]:
        config["token_tracking"]["enabled"] = True  # Default: enabled
    ```
  * Check config before tracking in ExecutionLoop and REPL
* **Success**:
  * `token_tracking.enabled: false` disables all tracking
  * Default behavior is enabled
  * Invalid config raises clear error
* **Research References**:
  * .agent-tracking/research/20260303-operation-cost-visibility-research.md (Lines 277-299) - Config pattern
  * .teambot/operation-cost-visibility/artifacts/test_strategy.md (Lines 299-316) - Config tests
* **Dependencies**:
  * None (can run in parallel with Task 4.3)

---

## Phase 5: Validation & Acceptance

### Task 5.1: Create Acceptance Tests

Implement acceptance test scenarios from feature spec.

* **Files**:
  * `tests/test_token_tracking_acceptance.py` - Acceptance tests
* **Test Scenarios** (from feature spec):
  * **AT-001**: Orchestration run with token summary
    - Run orchestration with SDK mock returning tokens
    - Verify summary panel displayed at end
    - Verify total and per-agent breakdowns
  * **AT-002**: Interactive session with token summary
    - Run REPL commands with token data
    - Exit and verify session summary displayed
  * **AT-003**: Graceful degradation
    - Run with SDK returning None for tokens
    - Verify "n/a" displayed, no crash
    - Verify warning logged once
  * **AT-004**: Token data persistence
    - Run orchestration
    - Load workflow_state.json
    - Verify token_tracking in metadata
  * **AT-005**: Config disables tracking
    - Set `token_tracking.enabled: false`
    - Run orchestration
    - Verify no summary displayed
  * **AT-006**: Per-stage aggregation
    - Run multi-stage orchestration
    - Verify per-stage breakdown accurate
* **Success**:
  * All 6 acceptance tests pass
  * Tests use `@pytest.mark.acceptance` marker
* **Research References**:
  * .teambot/operation-cost-visibility/artifacts/feature_spec.md - Acceptance test scenarios
  * .teambot/operation-cost-visibility/artifacts/test_strategy.md (Lines 530-558) - Acceptance test pattern
* **Dependencies**:
  * Phase 4 completion

---

### Task 5.2: Validate Coverage Targets and Run Full Test Suite

Ensure coverage targets met and no regressions.

* **Files**:
  * None (validation task)
* **Commands**:
  ```bash
  # Run full test suite with coverage
  uv run pytest --cov=src/teambot --cov-report=term-missing
  
  # Run token module tests specifically
  uv run pytest tests/test_tokens/ --cov=src/teambot/tokens --cov-report=term-missing
  
  # Run acceptance tests
  uv run pytest -m acceptance -v
  ```
* **Targets**:
  * `src/teambot/tokens/` module: ≥90% coverage
  * Integration coverage: ≥80%
  * Zero test regressions
* **Success**:
  * All tests pass
  * Coverage targets met
  * No new warnings or errors
* **Research References**:
  * .teambot/operation-cost-visibility/artifacts/test_strategy.md (Lines 350-372) - Coverage requirements
* **Dependencies**:
  * Task 5.1

---

## Dependencies Summary

| Dependency | Type | Status |
|------------|------|--------|
| pytest 7.4.0+ | Dev dependency | ✅ Existing |
| pytest-cov | Dev dependency | ✅ Existing |
| pytest-asyncio | Dev dependency | ✅ Existing |
| rich 13.0.0+ | Runtime dependency | ✅ Existing |
| Copilot SDK | External | ✅ Confirmed (ASSISTANT_USAGE events) |

## Success Criteria Summary

| Criteria | Validation Method |
|----------|------------------|
| Token summary displays at orchestration end | Manual run + AT-001 |
| Session summary displays on REPL exit | Manual run + AT-002 |
| Per-agent breakdown accurate | AT-001, unit tests |
| Per-stage breakdown accurate | AT-006, unit tests |
| Graceful degradation works | AT-003 |
| Persistence works | AT-004 |
| Config option works | AT-005 |
| Coverage ≥90% for tokens module | `uv run pytest --cov` |
| No workflow disruption | All existing tests pass |
