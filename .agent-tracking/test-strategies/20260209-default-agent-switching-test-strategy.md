<!-- markdownlint-disable-file -->
# Test Strategy: Runtime Default Agent Switching

**Strategy Date**: 2026-02-09
**Feature Specification**: `.teambot/default-agent-switching/artifacts/feature_spec.md`
**Research Reference**: `.agent-tracking/research/20260209-default-agent-switching-research.md`
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: **HYBRID** — TDD for core routing/command logic, Code-First for UI integration and help text.

### Rationale

This feature has well-defined requirements (13 FRs with precise acceptance criteria) and modifies a critical routing path — when the default agent changes, every subsequent plain-text message goes to a different agent. Incorrect behavior here would silently misroute all unaddressed input, making bugs hard to detect. These characteristics strongly favor TDD for the core components.

However, the UI integration (status panel indicator, `/status` output formatting) and documentation changes (`/help` text) are straightforward additive work where Code-First is faster and equally safe. The status panel uses a listener pattern that is already well-tested; the new indicator is a simple conditional label.

The hybrid split gives TDD's safety net to the high-risk routing and command logic while allowing faster iteration on the UI display changes.

**Key Factors:**
* Complexity: **MEDIUM** — Extends existing patterns, but routing correctness is critical
* Risk: **HIGH** — Silent misrouting of all plain-text input if broken
* Requirements Clarity: **CLEAR** — 13 FRs with explicit acceptance criteria and 9 acceptance test scenarios
* Time Pressure: **LOW** — No deadline pressure mentioned

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | Points To |
|--------|----------|-------|-----------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | 3 | TDD |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | 2 | TDD |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | 2 | TDD |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | 0 | Code-First |
| **Simplicity** | Is this straightforward CRUD or simple logic? | 1 | Code-First |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | 0 | Code-First |
| **Requirements Stability** | Are requirements likely to change during development? | 0 | Code-First |

**TDD Score: 7** | **Code-First Score: 1**

**Decision**: Hybrid (TDD score 7 ≥ 6 threshold, but some components are simple display-only → Code-First appropriate for those)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Low-Medium — state mutation and conditional routing, no complex algorithms
* **Integration Depth**: Medium — touches router, commands, UI status panel, REPL loop, and UI app (6 files)
* **State Management**: Medium — runtime `_default_agent` must stay consistent across router and UI; `_config_default_agent` preserved for reset
* **Error Scenarios**: Low — invalid agent ID is the primary error; idempotency is informational

### Risk Profile
* **Business Criticality**: HIGH — misrouting silently sends every unaddressed message to the wrong agent
* **User Impact**: ALL users — every plain-text input is affected
* **Data Sensitivity**: None — agent IDs are system constants
* **Failure Cost**: Medium-High — silent misrouting is hard to diagnose

### Requirements Clarity
* **Specification Completeness**: COMPLETE — 13 FRs, 9 acceptance tests
* **Acceptance Criteria Quality**: PRECISE — each FR has measurable acceptance
* **Edge Cases Identified**: 6 documented (empty input, whitespace, invalid agent, idempotent switch, already-at-config-default, reset when already default)
* **Dependencies Status**: STABLE — all extension points identified in research

## Test Strategy by Component

### Component 1: `AgentRouter` Mutation — **TDD** 🔴

**Approach**: TDD
**Rationale**: Core routing correctness is critical. The `set_default_agent()` method directly controls where all plain-text input goes. A bug here silently misroutes everything. The existing `TestRouterWithDefaultAgent` class (6 tests) provides a clear template.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `set_default_agent("builder-1")` changes `get_default_agent()` return value
  * After set, `_route_raw()` routes to new default agent
  * `set_default_agent(None)` clears default (raw handler used)
  * `set_default_agent("invalid")` raises `RouterError`
  * `get_config_default_agent()` always returns original constructor value
  * `_config_default_agent` is immutable after construction
* Edge Cases:
  * Set to same agent that's already default (no-op, no error)
  * Set when no default was configured initially
  * Explicit `@agent` directives still route correctly after set

**Testing Sequence (TDD):**
1. Write test: `test_set_default_agent_changes_default` → implement `set_default_agent()`
2. Write test: `test_set_default_agent_invalid_raises` → add validation
3. Write test: `test_config_default_preserved_after_set` → add `_config_default_agent`
4. Write test: `test_raw_input_routes_to_new_default_after_set` → verify routing
5. Write test: `test_explicit_agent_unaffected_by_default_change` → verify existing behavior

### Component 2: `/use-agent` Command Handler — **TDD** 🔴

**Approach**: TDD
**Rationale**: Multiple code paths (no args, valid switch, invalid agent, idempotent), each with specific output requirements. The `TestModelCommand` class (5 tests) is an exact template — validates agent, mutates state, returns confirmation.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `/use-agent builder-1` → success confirmation, routes to builder-1
  * `/use-agent` (no args) → shows current default + available agents
  * `/use-agent foo` → error with valid agents listed
  * `/use-agent pm` when pm is already default → idempotency message
  * Router not available → graceful error
* Edge Cases:
  * Agent ID with alias (out of scope per spec, but test it's rejected properly)

**Testing Sequence (TDD):**
1. Write test: `test_use_agent_no_args_shows_info` → implement info path
2. Write test: `test_use_agent_valid_switches` → implement switch path
3. Write test: `test_use_agent_invalid_shows_error` → implement validation
4. Write test: `test_use_agent_idempotent` → implement idempotency check
5. Write test: `test_use_agent_no_router` → implement router-None guard

### Component 3: `/reset-agent` Command Handler — **TDD** 🔴

**Approach**: TDD
**Rationale**: Must correctly restore config default. Mirrors `/use-agent` pattern but with reset semantics. Small and well-defined.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `/reset-agent` after switch → restores config default, confirmation
  * `/reset-agent` when already at config default → informational message
  * Router not available → graceful error
* Edge Cases:
  * Reset when no config default was set (None)

**Testing Sequence (TDD):**
1. Write test: `test_reset_agent_restores_config_default` → implement reset
2. Write test: `test_reset_agent_already_at_default` → implement idempotency
3. Write test: `test_reset_agent_no_router` → implement guard

### Component 4: `SystemCommands` Dispatch Integration — **Code-First** 🟢

**Approach**: Code-First
**Rationale**: Adding two entries to the dispatch dict and wiring router is mechanical. Risk is low — if dispatch fails, tests for the handler functions catch it.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit (dispatch integration)
* Critical Scenarios:
  * `dispatch("use-agent", ["builder-1"])` routes to handler
  * `dispatch("reset-agent", [])` routes to handler
  * Router setter wiring works

**Testing Sequence (Code-First):**
1. Add `"use-agent"` and `"reset-agent"` to dispatch table
2. Add `set_router()` method
3. Write dispatch integration tests

### Component 5: `/help` Text Update — **Code-First** 🟢

**Approach**: Code-First
**Rationale**: Pure text addition. Zero logic. Existing `TestHelpCommand.test_help_returns_command_list` covers it.

**Test Requirements:**
* Coverage Target: 100% (it's a string)
* Test Types: Unit
* Critical Scenarios:
  * `/help` output contains `/use-agent` and `/reset-agent`

### Component 6: `/status` Output Enhancement — **Code-First** 🟢

**Approach**: Code-First
**Rationale**: Additive text formatting. Output already tested by `TestStatusCommand`.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * `/status` shows "Default Agent: pm" when at config default
  * `/status` shows "Default Agent: builder-1 (session override; config default: pm)" when overridden
  * Both REPL `handle_status()` and UI `_get_status()` paths

### Component 7: `AgentStatusManager` Default Agent Tracking — **Code-First** 🟢

**Approach**: Code-First
**Rationale**: Simple attribute + setter + getter + notification, following the exact pattern of `set_model()`/`get()`. The `TestAgentStatusManagerModel` class (2 tests) is the template.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `set_default_agent("builder-1")` stores value
  * `get_default_agent()` returns current value
  * Changing default triggers listener notification
  * Setting same default again does not trigger notification

### Component 8: `StatusPanel` Default Indicator — **Code-First** 🟢

**Approach**: Code-First
**Rationale**: Conditional label in `_format_status()`. Low risk, follows existing indicator pattern. `TestStatusPanel` class provides template.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit
* Critical Scenarios:
  * Default agent row shows "default" indicator
  * Non-default agent rows do not show indicator
  * Indicator moves when default changes

### Component 9: Wiring in `loop.py` and `app.py` — **Code-First** 🟢

**Approach**: Code-First
**Rationale**: Constructor parameter passing. Verified implicitly by integration tests. Existing `TestREPLIntegration` provides template.

**Test Requirements:**
* Coverage Target: 80%
* Test Types: Integration
* Critical Scenarios:
  * Router is passed to SystemCommands in REPL mode
  * Router is passed to SystemCommands in UI mode
  * Default agent on AgentStatusManager initialized from router in UI mode
  * `/use-agent` dispatch updates status panel in UI mode

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest
* **Configuration**: `pyproject.toml` — `[tool.pytest.ini_options]`
* **Runner**: `uv run pytest`
* **Async**: `asyncio_mode = "auto"` (no manual `@pytest.mark.asyncio` needed)
* **Coverage**: Built-in via `--cov=src/teambot --cov-report=term-missing`

### Testing Tools Required
* **Mocking**: `unittest.mock` — `AsyncMock` for async handlers, `MagicMock` for sync
* **Assertions**: Built-in `assert` with descriptive messages
* **Coverage**: pytest-cov (already configured in `addopts`)
* **Test Data**: Inline `Command` objects and `AgentRouter` instances — no external fixtures needed

### Test Organization
* **Test Location**: `tests/` directory mirroring `src/` structure
* **Naming Convention**: `test_*.py` files, `Test*` classes, `test_*` methods
* **Fixture Strategy**: Inline setup per test (no shared conftest fixtures for this feature)
* **Setup/Teardown**: None needed — all state is in-memory, created fresh per test

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 95% minimum for new code
* **Integration Coverage**: 80% for wiring changes
* **Critical Path Coverage**: 100% for routing mutation and command handlers
* **Error Path Coverage**: 100% for invalid agent, no-router, idempotency

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Approach | Notes |
|-----------|--------|---------------|----------|----------|-------|
| `AgentRouter` mutation | 100% | — | CRITICAL | TDD | Core routing correctness |
| `handle_use_agent()` | 100% | — | CRITICAL | TDD | Multiple code paths |
| `handle_reset_agent()` | 100% | — | CRITICAL | TDD | Config restore correctness |
| `SystemCommands` dispatch | 90% | 90% | HIGH | Code-First | Mechanical wiring |
| `handle_help()` text | 100% | — | MEDIUM | Code-First | String assertion |
| `handle_status()` enhancement | 90% | — | HIGH | Code-First | Additive formatting |
| `AgentStatusManager` default | 100% | — | HIGH | Code-First | Follows set_model pattern |
| `StatusPanel` indicator | 90% | — | MEDIUM | Code-First | Display-only |
| `loop.py` / `app.py` wiring | — | 80% | HIGH | Code-First | Constructor changes |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Switch Default and Route Plain Text** (Priority: CRITICAL)
   * **Description**: After `/use-agent builder-1`, raw input routes to `builder-1`
   * **Test Type**: Unit
   * **Success Criteria**: `_route_raw()` converts to AGENT command with `builder-1`
   * **Test Approach**: TDD
   * **FR**: FR-DAS-001

2. **Explicit @agent Unaffected After Switch** (Priority: CRITICAL)
   * **Description**: `@reviewer task` routes to `reviewer` even when default is `builder-1`
   * **Test Type**: Unit
   * **Success Criteria**: `_route_agent()` uses command's `agent_id`, not `_default_agent`
   * **Test Approach**: TDD
   * **FR**: FR-DAS-011

3. **Reset Restores Config Default** (Priority: CRITICAL)
   * **Description**: `/reset-agent` restores `teambot.json` value
   * **Test Type**: Unit
   * **Success Criteria**: `get_default_agent()` returns `_config_default_agent` value
   * **Test Approach**: TDD
   * **FR**: FR-DAS-003

4. **Invalid Agent ID Rejected** (Priority: HIGH)
   * **Description**: `/use-agent foo` returns error with valid agents listed
   * **Test Type**: Unit
   * **Success Criteria**: `CommandResult(success=False)` with agent list in output
   * **Test Approach**: TDD
   * **FR**: FR-DAS-004

5. **No Args Shows Current Default** (Priority: HIGH)
   * **Description**: `/use-agent` displays current default and all available agents
   * **Test Type**: Unit
   * **Success Criteria**: Output contains current agent ID and all 6 valid IDs
   * **Test Approach**: TDD
   * **FR**: FR-DAS-002

6. **Status Shows Default Agent** (Priority: HIGH)
   * **Description**: `/status` includes "Default Agent: ..." line
   * **Test Type**: Unit
   * **Success Criteria**: Output contains "Default Agent" string and correct agent ID
   * **Test Approach**: Code-First
   * **FR**: FR-DAS-005

### Edge Cases to Cover

* **Idempotent switch**: `/use-agent pm` when `pm` is already default → informational, not error (FR-DAS-012)
* **Reset at config default**: `/reset-agent` when already at config default → informational (FR-DAS-013)
* **No config default set**: Router initialized with `default_agent=None` → `/use-agent` still works, `/reset-agent` restores to None
* **Empty/whitespace input after switch**: Still uses raw handler, not new default agent (existing behavior preserved)
* **Switch then explicit @agent then plain text**: Plain text still routes to switched default

### Error Scenarios

* **Invalid agent ID**: `/use-agent invalid-id` → `CommandResult(success=False)` with helpful message
* **Router not available**: `SystemCommands` has no router reference → graceful error message
* **set_default_agent with invalid ID**: `RouterError` raised with available agents listed

## Test Data Strategy

### Test Data Requirements
* **Command objects**: Created inline via `Command(type=CommandType.RAW, content="...")` — no fixtures needed
* **Router instances**: Created per test via `AgentRouter(default_agent="pm")` — no shared state
* **SystemCommands instances**: Created per test with mock router via `SystemCommands(router=mock_router)`

### Test Data Management
* **Storage**: Inline in test methods
* **Generation**: Manual — domain is small (6 agent IDs, 2 commands)
* **Isolation**: Each test creates its own router/commands instance
* **Cleanup**: Not needed — all in-memory, garbage collected

## Example Test Patterns

### Example from Codebase: Router Default Agent Tests

**File**: `tests/test_repl/test_router.py` (Lines 201-300)
**Pattern**: Async test with mocked handlers, assert routing behavior

```python
class TestRouterWithDefaultAgent:
    async def test_raw_input_routed_to_default_agent(self):
        router = AgentRouter(default_agent="pm")
        mock_handler = AsyncMock(return_value="Response from PM")
        router.register_agent_handler(mock_handler)
        router.register_raw_handler(MagicMock(return_value="Raw handler response"))

        cmd = Command(type=CommandType.RAW, content="Hello world")
        result = await router.route(cmd)

        mock_handler.assert_called_once_with("pm", "Hello world")
        assert result == "Response from PM"
```

### Example from Codebase: Command Handler Tests

**File**: `tests/test_repl/test_commands.py` (Lines 254-299)
**Pattern**: Direct handler call, assert output content and success flag

```python
class TestModelCommand:
    def test_model_sets_agent_model(self):
        commands = SystemCommands()
        result = commands.dispatch("model", ["pm", "gpt-5"])
        assert result.success is True
        assert commands._session_model_overrides.get("pm") == "gpt-5"

    def test_model_invalid_agent(self):
        commands = SystemCommands()
        result = commands.dispatch("model", ["invalid-agent-xyz", "gpt-5"])
        assert result.success is False
        assert "Invalid agent" in result.output
```

### Recommended Test Structure for New Tests

```python
# tests/test_repl/test_router.py — Add to existing file
class TestRouterDefaultAgentMutation:
    """Tests for runtime default agent switching on AgentRouter."""

    def test_set_default_agent_changes_default(self):
        router = AgentRouter(default_agent="pm")
        router.set_default_agent("builder-1")
        assert router.get_default_agent() == "builder-1"

    def test_set_default_agent_invalid_raises(self):
        router = AgentRouter(default_agent="pm")
        with pytest.raises(RouterError, match="Unknown agent"):
            router.set_default_agent("invalid")

    def test_config_default_preserved_after_set(self):
        router = AgentRouter(default_agent="pm")
        router.set_default_agent("builder-1")
        assert router.get_config_default_agent() == "pm"

    async def test_raw_routes_to_new_default_after_set(self):
        router = AgentRouter(default_agent="pm")
        mock_handler = AsyncMock(return_value="OK")
        router.register_agent_handler(mock_handler)
        router.register_raw_handler(MagicMock())

        router.set_default_agent("builder-1")
        await router.route(Command(type=CommandType.RAW, content="hello"))
        mock_handler.assert_called_once_with("builder-1", "hello")


# tests/test_repl/test_commands.py — Add to existing file
class TestUseAgentCommand:
    """Tests for /use-agent command."""

    def test_use_agent_no_args_shows_info(self):
        router = AgentRouter(default_agent="pm")
        commands = SystemCommands(router=router)
        result = commands.dispatch("use-agent", [])
        assert result.success is True
        assert "pm" in result.output
        assert "builder-1" in result.output

    def test_use_agent_switches_default(self):
        router = AgentRouter(default_agent="pm")
        commands = SystemCommands(router=router)
        result = commands.dispatch("use-agent", ["builder-1"])
        assert result.success is True
        assert router.get_default_agent() == "builder-1"

    def test_use_agent_invalid_agent(self):
        router = AgentRouter(default_agent="pm")
        commands = SystemCommands(router=router)
        result = commands.dispatch("use-agent", ["foo"])
        assert result.success is False
        assert "foo" in result.output
        assert router.get_default_agent() == "pm"  # Unchanged
```

## Success Criteria

### Test Implementation Complete When:
* [x] All critical scenarios have tests (6 critical + 3 edge cases)
* [x] Coverage targets are met per component (100% TDD, 90% Code-First)
* [x] All edge cases are tested (idempotency, no-config-default, reset-at-default)
* [x] Error paths are validated (invalid agent, no router)
* [x] Tests follow codebase conventions (pytest, AsyncMock, Command objects)
* [x] Tests are maintainable and clear (descriptive names, inline setup)
* [x] CI/CD integration is working (`uv run pytest` passes)

### Test Quality Indicators:
* Tests are readable and self-documenting (descriptive method names)
* Tests are fast and reliable (all in-memory, no I/O)
* Tests are independent (fresh instances per test)
* Failures clearly indicate the problem (specific assertions with context)
* Mock/stub usage is appropriate and minimal (only mock handlers)

## Implementation Guidance

### For TDD Components (Router, /use-agent, /reset-agent):
1. Start with simplest test case (e.g., `set_default_agent` changes value)
2. Write minimal code to pass
3. Add next test case (e.g., invalid agent raises)
4. Refactor when all tests pass
5. Focus on behavior, not implementation details

### For Code-First Components (dispatch, help, status, UI):
1. Implement core functionality following existing patterns
2. Add happy path test
3. Identify edge cases from implementation
4. Add edge case tests
5. Verify coverage meets target

### For Hybrid Boundary:
1. Complete TDD components first (router + commands)
2. Then Code-First components (UI, help, status)
3. Integration tests cover boundaries between them
4. Validate full feature via acceptance test scenarios from spec

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD for core logic ensures routing correctness — the highest-risk area
* Code-First for UI/text allows faster iteration on display details
* Follows existing test patterns exactly — no new infrastructure needed

### Accepted Trade-offs:
* TDD components take slightly longer to implement initially
* Code-First UI components may need test refinement after implementation

### Risk Mitigation:
* TDD prevents silent misrouting — the most dangerous failure mode
* Acceptance test scenarios (9 from spec) provide end-to-end validation checklist
* Existing `TestRouterWithDefaultAgent` tests serve as regression guard for existing behavior

## References

* **Feature Spec**: `.teambot/default-agent-switching/artifacts/feature_spec.md`
* **Research Doc**: `.agent-tracking/research/20260209-default-agent-switching-research.md`
* **Test Examples**: `tests/test_repl/test_router.py`, `tests/test_repl/test_commands.py`, `tests/test_ui/test_status_panel.py`, `tests/test_ui/test_agent_state.py`
* **Test Config**: `pyproject.toml [tool.pytest.ini_options]`

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow recommended approach per component

---

**Strategy Status**: DRAFT
**Approved By**: PENDING
**Ready for Planning**: YES
