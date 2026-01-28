<!-- markdownlint-disable-file -->
# Test Strategy: Split-Pane Terminal Interface

**Strategy Date**: 2026-01-28
**Feature Specification**: docs/feature-specs/split-pane-interface.md
**Research Reference**: .agent-tracking/research/20260128-split-pane-interface-research.md
**Strategist**: Test Strategy Agent

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Assessment | TDD Points | Code-First Points |
|--------|------------|------------|-------------------|
| **Requirements Clarity** | Well-defined with 15 FRs and acceptance criteria | 3 | 0 |
| **Complexity** | Medium-High: Textual integration, async events, widget state | 2 | 0 |
| **Risk Level** | Medium: UX feature, not data-critical | 1 | 0 |
| **Exploratory Nature** | Partial: New UI framework (Textual) requires prototyping | 0 | 2 |
| **Simplicity** | No: Multi-component UI with async coordination | 0 | 0 |
| **Time Pressure** | Moderate: No urgent deadline | 0 | 1 |
| **Requirements Stability** | Stable: Spec approved, clear scope | 0 | 0 |

### Decision Thresholds

| TDD Score | Code-First Score | Recommendation |
|-----------|------------------|----------------|
| **6** | **3** | **HYBRID** |

**Decision**: HYBRID (TDD Score 6 = threshold, Code-First Score 3 < 5)

---

## Recommended Testing Approach

**Primary Approach**: HYBRID

### Rationale

The Split-Pane Terminal Interface feature warrants a **Hybrid testing approach** because it combines well-defined integration requirements with exploratory UI widget development.

**TDD for integration and critical paths**: The integration between Textual app and existing TaskExecutor/Router has clear requirements and callbacks. These integration points are critical - if output doesn't route correctly to the OutputPane, the feature fails. TDD ensures these contracts are validated before implementation.

**Code-First for Textual widgets**: The InputPane and OutputPane widgets involve visual/UX exploration that benefits from rapid prototyping. Textual's `pilot` test framework is designed for testing apps *after* they're built. Trying to TDD complex UI widgets often leads to testing implementation details rather than behavior.

**Key Factors:**
* Complexity: MEDIUM-HIGH (multi-component async UI)
* Risk: MEDIUM (UX feature, graceful fallback exists)
* Requirements Clarity: CLEAR (15 FRs with acceptance criteria)
* Time Pressure: MODERATE (no urgent deadline)

---

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Low - primarily event routing and display logic
* **Integration Depth**: High - bridges Textual ↔ existing REPL/TaskExecutor
* **State Management**: Medium - widget state, command history, output buffer
* **Error Scenarios**: Medium - terminal compatibility, resize edge cases, fallback mode

### Risk Profile
* **Business Criticality**: MEDIUM - Core UX improvement, not data-critical
* **User Impact**: High - affects all interactive mode users
* **Data Sensitivity**: None - UI display only, no PII
* **Failure Cost**: Low-Medium - fallback to legacy mode exists

### Requirements Clarity
* **Specification Completeness**: COMPLETE (15 FRs, 8 NFRs documented)
* **Acceptance Criteria Quality**: PRECISE (measurable targets like "< 100ms latency")
* **Edge Cases Identified**: 5+ documented (resize, narrow terminal, output overflow)
* **Dependencies Status**: STABLE (Textual framework well-documented)

---

## Test Strategy by Component

### 1. TeamBotApp (Main Application) - HYBRID

**Approach**: Code-First for structure, TDD for event handlers

**Rationale**: The app's `compose()` method is visual/structural - prototype first. Event handlers (`on_input_submitted`, `_handle_task_complete`) have clear contracts - use TDD.

**Test Requirements:**
* Coverage Target: 85%
* Test Types: Unit + Integration
* Critical Scenarios:
  * App launches and displays both panes
  * Input submission triggers command routing
  * Task completion writes to output pane
* Edge Cases:
  * Empty input submission
  * Invalid command format
  * Rapid successive inputs

**Testing Sequence** (Hybrid):
1. Prototype app structure with `compose()`
2. Write TDD tests for `handle_input()` behavior
3. Write TDD tests for `_handle_task_complete()` callback
4. Add integration test verifying full input→output flow

### 2. InputPane Widget - CODE_FIRST

**Approach**: Code-First then stabilize with tests

**Rationale**: Widget extends Textual's `Input` class. Visual behavior and command history navigation benefit from interactive prototyping before locking down tests.

**Test Requirements:**
* Coverage Target: 80%
* Test Types: Unit (Textual pilot)
* Critical Scenarios:
  * Text input captured correctly
  * Command history navigation (up/down arrows)
  * Input cleared after submission
* Edge Cases:
  * Empty history navigation
  * Very long input (>100 chars)
  * Special characters in input

**Testing Sequence** (Code-First):
1. Implement InputPane with history logic
2. Manually verify behavior
3. Add pilot tests for history navigation
4. Add tests for edge cases
5. Validate 80% coverage

### 3. OutputPane Widget - CODE_FIRST

**Approach**: Code-First then stabilize with tests

**Rationale**: Widget extends `RichLog`. Auto-scroll, timestamp formatting, and status indicators are visual - prototype first, then test.

**Test Requirements:**
* Coverage Target: 80%
* Test Types: Unit (Textual pilot)
* Critical Scenarios:
  * Messages display with correct timestamp format
  * Auto-scroll to bottom on new content
  * Status indicators (✓, ✗, ℹ) render correctly
* Edge Cases:
  * Very long messages (word wrap)
  * Rapid message flood (10+ messages/second)
  * Rich markup in messages

**Testing Sequence** (Code-First):
1. Implement OutputPane with timestamp/status logic
2. Manually verify auto-scroll and formatting
3. Add pilot tests for message writing
4. Add tests for edge cases
5. Validate 80% coverage

### 4. REPL→Textual Integration - TDD

**Approach**: TDD (critical path)

**Rationale**: Integration between `parse_command()`, `Router`, `TaskExecutor`, and Textual app callbacks is the critical path. Clear contracts exist. Failures here break the feature.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Integration
* Critical Scenarios:
  * Agent command (`@pm task`) routes to executor, result to OutputPane
  * System command (`/status`) routes to commands, result to OutputPane
  * Background task completion callback writes to OutputPane
* Edge Cases:
  * Command parsing failure
  * Executor timeout/error
  * Concurrent commands

**Testing Sequence** (TDD):
1. Write test: "agent command routes to executor"
2. Implement routing logic to pass
3. Write test: "system command displays in output"
4. Implement system routing
5. Write test: "task callback writes to output"
6. Implement callback registration
7. Refactor for clean architecture

### 5. Fallback Mode - TDD

**Approach**: TDD (well-defined requirements)

**Rationale**: Fallback logic has clear trigger conditions (terminal < 80 cols, unsupported terminal). TDD ensures all conditions are handled.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Terminal < 80 columns triggers fallback
  * `TEAMBOT_LEGACY_MODE=true` forces fallback
  * Unsupported terminal (no TTY) triggers fallback
* Edge Cases:
  * Exactly 80 columns (boundary)
  * Terminal resize during operation
  * Missing TERM environment variable

**Testing Sequence** (TDD):
1. Write test: "narrow terminal triggers fallback"
2. Implement width check
3. Write test: "legacy mode flag forces fallback"
4. Implement flag check
5. Write test: "non-TTY triggers fallback"
6. Implement TTY check
7. Validate 95% coverage

### 6. `/clear` Command - TDD

**Approach**: TDD (simple, clear requirement)

**Rationale**: New command with single clear behavior. Perfect TDD candidate.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * `/clear` clears output pane content
  * Input pane unaffected by `/clear`

**Testing Sequence** (TDD):
1. Write test: "clear command clears output"
2. Implement command handler
3. Write test: "clear preserves input"
4. Verify isolation
5. Validate 100% coverage

---

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: Per pyproject.toml dependencies
* **Configuration**: `pyproject.toml` lines 40-46
* **Runner**: `uv run pytest --cov=src/teambot --cov-report=term-missing`

### Testing Tools Required
* **Mocking**: `unittest.mock` (MagicMock, AsyncMock, patch) - standard patterns
* **Assertions**: pytest built-in assertions - existing pattern
* **Coverage**: pytest-cov - Target: 85% overall for new code
* **Test Data**: Fixtures in conftest.py - extend with Textual mocks
* **Textual Testing**: `textual[dev]` package provides `pilot` test driver

### New Test Dependencies
Add to `pyproject.toml` dev dependencies:
```toml
[dependency-groups]
dev = [
  # ... existing ...
  "textual[dev]>=0.47.0",  # NEW: Includes pilot for testing
]
```

### Test Organization
* **Test Location**: `tests/test_ui/` (new directory mirroring `src/teambot/ui/`)
* **Naming Convention**: `test_*.py` pattern (existing)
* **Fixture Strategy**: Extend `conftest.py` with Textual app fixtures
* **Setup/Teardown**: Use Textual's async test context

### New Test Directory Structure
```
tests/
├── test_ui/                    # NEW
│   ├── __init__.py
│   ├── conftest.py             # Textual-specific fixtures
│   ├── test_app.py             # TeamBotApp tests
│   ├── test_input_pane.py      # InputPane widget tests
│   ├── test_output_pane.py     # OutputPane widget tests
│   └── test_integration.py     # End-to-end UI tests
├── test_repl/
│   └── test_loop.py            # UPDATE: Add fallback mode tests
```

---

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 85% (minimum) for new `ui/` module
* **Integration Coverage**: 80% for REPL↔Textual integration
* **Critical Path Coverage**: 100% for command routing and callbacks
* **Error Path Coverage**: 90% for fallback scenarios

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| TeamBotApp | 85% | 90% | CRITICAL | Core application |
| InputPane | 80% | - | HIGH | Widget testing via pilot |
| OutputPane | 80% | - | HIGH | Widget testing via pilot |
| Integration (Router→App) | - | 90% | CRITICAL | Critical path |
| Fallback Mode | 95% | - | HIGH | Edge case handling |
| `/clear` Command | 100% | - | MEDIUM | Simple, complete coverage |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Command Input to Output Flow** (Priority: CRITICAL)
   * **Description**: User submits `@pm task`, output appears in right pane
   * **Test Type**: Integration
   * **Success Criteria**: Output contains task result within 100ms of completion
   * **Test Approach**: TDD

2. **Background Task Completion** (Priority: CRITICAL)
   * **Description**: Task completes async, callback writes to OutputPane
   * **Test Type**: Integration
   * **Success Criteria**: Callback invoked, output written without blocking
   * **Test Approach**: TDD

3. **Fallback Mode Trigger** (Priority: HIGH)
   * **Description**: Narrow terminal (<80 cols) falls back to legacy mode
   * **Test Type**: Unit
   * **Success Criteria**: Legacy REPL launched, no Textual error
   * **Test Approach**: TDD

4. **Input Pane Stability** (Priority: HIGH)
   * **Description**: Output writes don't disrupt input pane
   * **Test Type**: Integration
   * **Success Criteria**: Input cursor position preserved after output
   * **Test Approach**: Code-First (visual verification + pilot test)

### Edge Cases to Cover

* **Rapid input**: Multiple commands submitted within 100ms
* **Large output**: 1000+ line output from single command
* **Terminal resize**: Window resized during operation
* **Special characters**: Unicode, emoji in commands and output
* **Empty commands**: Submit with no input

### Error Scenarios

* **Executor failure**: SDK client throws exception → error message in output
* **Parse failure**: Invalid command syntax → error message, input preserved
* **Terminal disconnection**: Graceful shutdown without crash
* **Output buffer overflow**: 10,000+ lines → oldest lines pruned

---

## Test Data Strategy

### Test Data Requirements
* **Command fixtures**: Standard `@agent task` and `/command` examples
* **Output fixtures**: Sample agent responses, multi-line output, Rich markup
* **Terminal size mocks**: Various dimensions (80x24, 120x40, 60x20)
* **Error responses**: SDK errors, parse errors, timeout errors

### Test Data Management
* **Storage**: `tests/test_ui/fixtures/` directory
* **Generation**: Programmatic via conftest.py fixtures
* **Isolation**: Each test gets fresh app instance (Textual handles this)
* **Cleanup**: Textual pilot auto-cleans after each test

---

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_visualization/test_overlay.py` (Lines 72-80)
**Pattern**: Mocking terminal dimensions, verifying initialization

```python
class TestOverlayRendererInit:
    """Tests for OverlayRenderer initialization."""

    def test_default_init(self):
        """Test default initialization."""
        with patch.object(OverlayRenderer, "_check_terminal_support", return_value=True):
            renderer = OverlayRenderer()
            assert renderer.is_enabled is True
            assert renderer.state.position == OverlayPosition.TOP_RIGHT
```

**Key Conventions:**
* Class-based test organization (`Test*` prefix)
* Descriptive docstrings
* `patch` for external dependencies
* Clear assert statements

### Recommended Test Structure for Textual

**Pattern**: Using Textual's `pilot` test driver

```python
# tests/test_ui/test_app.py
import pytest
from textual.pilot import Pilot

from teambot.ui.app import TeamBotApp


class TestTeamBotApp:
    """Tests for TeamBotApp main application."""

    @pytest.mark.asyncio
    async def test_app_displays_both_panes(self):
        """Test that app shows input and output panes."""
        app = TeamBotApp()
        async with app.run_test() as pilot:
            # Verify both panes exist
            assert app.query_one("#input-pane") is not None
            assert app.query_one("#output") is not None

    @pytest.mark.asyncio
    async def test_input_submission_shows_in_output(self):
        """Test that submitted input appears in output pane."""
        app = TeamBotApp()
        async with app.run_test() as pilot:
            # Type and submit command
            await pilot.type("@pm create plan")
            await pilot.press("enter")
            
            # Verify output contains the command echo
            output = app.query_one("#output")
            assert "@pm create plan" in output.lines[-1]

    @pytest.mark.asyncio
    async def test_command_history_navigation(self):
        """Test up arrow navigates command history."""
        app = TeamBotApp()
        async with app.run_test() as pilot:
            # Submit two commands
            await pilot.type("first command")
            await pilot.press("enter")
            await pilot.type("second command")
            await pilot.press("enter")
            
            # Press up arrow to get last command
            await pilot.press("up")
            
            input_pane = app.query_one("#prompt")
            assert input_pane.value == "second command"
```

### Recommended Integration Test Structure

```python
# tests/test_ui/test_integration.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from teambot.ui.app import TeamBotApp
from teambot.tasks.executor import TaskExecutor


class TestTextualREPLIntegration:
    """Integration tests for Textual ↔ REPL components."""

    @pytest.fixture
    def mock_executor(self):
        """Create mock executor with callback capture."""
        executor = MagicMock(spec=TaskExecutor)
        executor.execute = AsyncMock(return_value=MagicMock(
            success=True,
            output="Task completed",
            task_id="task-1"
        ))
        return executor

    @pytest.mark.asyncio
    async def test_agent_command_routes_to_executor(self, mock_executor):
        """Test @agent command is sent to TaskExecutor."""
        app = TeamBotApp(executor=mock_executor)
        async with app.run_test() as pilot:
            await pilot.type("@pm create plan")
            await pilot.press("enter")
            
            # Allow async processing
            await pilot.pause()
            
            mock_executor.execute.assert_called_once()
            call_args = mock_executor.execute.call_args
            assert call_args[0][0].agent_id == "pm"

    @pytest.mark.asyncio
    async def test_task_callback_writes_to_output(self, mock_executor):
        """Test task completion callback writes to output pane."""
        app = TeamBotApp(executor=mock_executor)
        callback_captured = None
        
        # Capture the callback registration
        def capture_callback(cb):
            nonlocal callback_captured
            callback_captured = cb
        
        mock_executor.on_task_completed = capture_callback
        
        async with app.run_test() as pilot:
            # Simulate task completion
            mock_task = MagicMock(agent_id="pm", id="task-1")
            await callback_captured(mock_task, "Plan created")
            
            output = app.query_one("#output")
            assert "Plan created" in str(output.lines)
```

---

## Success Criteria

### Test Implementation Complete When:
* [x] All critical scenarios have tests (6 scenarios defined)
* [ ] Coverage targets are met per component (85% unit, 80% integration)
* [ ] All edge cases are tested (5 edge cases defined)
* [ ] Error paths are validated (4 error scenarios)
* [ ] Tests follow codebase conventions (class-based, docstrings)
* [ ] Tests are maintainable and clear (descriptive names)
* [ ] CI/CD integration is working (pytest in existing workflow)

### Test Quality Indicators:
* Tests are readable and self-documenting (docstrings + clear names)
* Tests are fast and reliable (Textual pilot runs in <1s per test)
* Tests are independent (fresh app instance per test)
* Failures clearly indicate the problem (descriptive assertions)
* Mock/stub usage is appropriate and minimal (mock external deps only)

---

## Implementation Guidance

### For TDD Components (Integration, Fallback, /clear):
1. Start with simplest test case (e.g., "narrow terminal triggers fallback")
2. Write minimal code to pass
3. Add next test case (e.g., "legacy flag forces fallback")
4. Refactor when all tests pass
5. Focus on behavior, not implementation

### For Code-First Components (InputPane, OutputPane, App structure):
1. Implement core functionality with Textual
2. Manually test in terminal (`uv run teambot run`)
3. Identify edge cases from usage
4. Add pilot tests for critical behaviors
5. Verify coverage meets target

### For Hybrid Approach:
1. Start with TDD for integration layer (Router→App callbacks)
2. Prototype widgets with Code-First (InputPane, OutputPane)
3. Add pilot tests once widget behavior is stable
4. Ensure integration tests cover widget boundaries
5. Validate overall feature behavior with end-to-end test

---

## Considerations and Trade-offs

### Selected Approach Benefits:
* **TDD for integration**: Ensures critical callback contracts work before UI
* **Code-First for widgets**: Allows visual iteration on UX
* **Textual pilot**: Purpose-built for testing Textual apps

### Accepted Trade-offs:
* Widget tests come after implementation (may miss some edge cases initially)
* Integration tests may need updating as widget API stabilizes
* Code-First widgets need discipline to add tests after prototyping

### Risk Mitigation:
* TDD on integration ensures core functionality works regardless of widget changes
* Coverage targets (85%+) ensure comprehensive testing even with Code-First
* Fallback mode TDD ensures graceful degradation always works

---

## References

* **Feature Spec**: [docs/feature-specs/split-pane-interface.md](../../docs/feature-specs/split-pane-interface.md)
* **Research Doc**: [.agent-tracking/research/20260128-split-pane-interface-research.md](./../research/20260128-split-pane-interface-research.md)
* **Test Examples**: `tests/test_visualization/test_overlay.py`, `tests/test_repl/test_loop.py`
* **Textual Testing Docs**: https://textual.textualize.io/guide/testing/

---

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow recommended approach per component

---

**Strategy Status**: APPROVED
**Approved By**: User (2026-01-28)
**Ready for Planning**: YES
