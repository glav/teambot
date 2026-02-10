<!-- markdownlint-disable-file -->
# Test Strategy: Enhanced Multi-Line Text Input

**Strategy Date**: 2026-02-10
**Feature Specification**: (Objective document — multi-line input for TeamBot split-pane UI)
**Research Reference**: .agent-tracking/research/20260210-enhanced-text-input-research.md
**Strategist**: Test Strategy Agent

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | Points To |
|--------|----------|-------|-----------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | 3 | TDD |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | 1 | TDD |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | 2 | TDD |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | 1 | Code-First |
| **Simplicity** | Is this straightforward CRUD or simple logic? | 1 | Code-First |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | 1 | Code-First |
| **Requirements Stability** | Are requirements likely to change during development? | 1 | Code-First |

### Score Totals

| Approach | Score | Threshold |
|----------|-------|-----------|
| **TDD** | **6** | ≥ 6 → TDD |
| **Code-First** | **4** | ≥ 5 → Code-First |

### Decision: **HYBRID**

TDD score hits threshold (6) while Code-First is close (4). The feature has well-defined requirements and critical user-facing behavior (Enter/submit, history navigation), but also straightforward widget migration and CSS work. **Hybrid** is optimal: TDD for core behavioral logic, Code-First for wiring/styling.

---

## Recommended Testing Approach

**Primary Approach**: **HYBRID**

### Rationale

The multi-line input feature involves migrating `InputPane` from Textual's `Input` to `TextArea`, which changes the base class, event model, and key handling. The core behavioral changes — Enter-to-submit, Ctrl+Enter for newline, conditional history navigation — are well-specified with clear acceptance criteria, making them ideal for TDD. These are the highest-risk areas where regressions would directly break the user experience.

However, the CSS layout changes, constructor wiring in `app.py`, and API property migrations (`.value` → `.text`) are mechanical and straightforward. Writing tests first for these would add little value; updating existing tests after implementation is more efficient.

The hybrid approach ensures critical behavior is locked down with tests-first confidence while allowing rapid iteration on the structural migration.

**Key Factors:**
* Complexity: **MEDIUM** — Widget migration with custom event handling
* Risk: **HIGH** — Directly affects primary user input path
* Requirements Clarity: **CLEAR** — 8 explicit success criteria in objective
* Time Pressure: **LOW** — Quality matters more than speed

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Low — history navigation logic is simple indexed traversal
* **Integration Depth**: Medium — widget change touches `input_pane.py`, `app.py`, `styles.css`, and all UI tests
* **State Management**: Medium — history state, cursor position state, current input preservation
* **Error Scenarios**: Low — graceful degradation for unsupported keybindings; no data loss risk

### Risk Profile
* **Business Criticality**: **HIGH** — Input is the primary user interaction point
* **User Impact**: Every user is affected — input widget is used on every command
* **Data Sensitivity**: None — no sensitive data involved
* **Failure Cost**: **HIGH** — Broken input = unusable application

### Requirements Clarity
* **Specification Completeness**: **COMPLETE** — 8 success criteria clearly defined
* **Acceptance Criteria Quality**: **PRECISE** — Specific keybindings, cursor position behaviors
* **Edge Cases Identified**: 6 documented (cursor position variants, empty history, paste)
* **Dependencies Status**: **STABLE** — Textual 7.4.0 is installed; TextArea API is verified

---

## Test Strategy by Component

### 1. InputPane Key Handling (`_on_key` override) — **TDD** 🔴

**Approach**: TDD
**Rationale**: This is the core behavioral change. Enter-to-submit, Ctrl+Enter-for-newline, and conditional history navigation are the highest-risk, most user-facing behaviors. Writing tests first ensures the contract is locked down before implementation.

**Test Requirements:**
* Coverage Target: **95%**
* Test Types: Unit (via Textual pilot)
* Critical Scenarios:
  * Enter key submits text and clears input
  * Enter on empty input does not submit
  * Ctrl+Enter inserts a newline character
  * Alt+Enter inserts a newline character (fallback)
  * Up arrow on first line triggers history backward
  * Up arrow on non-first line moves cursor up (no history)
  * Down arrow on last line triggers history forward
  * Down arrow on non-last line moves cursor down (no history)
  * Single-line content: Up/Down behave like old Input (history)
* Edge Cases:
  * Empty history + Up arrow = no crash, no change
  * Multi-line content in history recalled correctly
  * Current input preserved when navigating history

**Testing Sequence (TDD):**
1. Write test: `test_enter_submits_text` — Enter posts Submitted with text content
2. Write test: `test_enter_clears_input` — Input is empty after submit
3. Implement Enter handling in `_on_key`
4. Write test: `test_ctrl_enter_inserts_newline` — Ctrl+Enter adds `\n`
5. Implement Ctrl+Enter handling
6. Write test: `test_history_up_only_on_first_line` — Up triggers history only at row 0
7. Write test: `test_history_down_only_on_last_line` — Down triggers history only at last row
8. Implement conditional history navigation
9. Refactor and verify all tests pass

### 2. Custom Submitted Message — **TDD** 🔴

**Approach**: TDD
**Rationale**: The custom `Submitted` message must preserve the API contract (`event.value`, `event.input`) used by `app.py`. A failing test first ensures backward compatibility.

**Test Requirements:**
* Coverage Target: **100%**
* Test Types: Unit
* Critical Scenarios:
  * `Submitted` message has `.value` attribute with text content
  * `Submitted` message has `.input` attribute referencing the widget
  * `event.input.clear()` works (TextArea.clear())

**Testing Sequence (TDD):**
1. Write test: `test_submitted_message_has_value` — verify `.value`
2. Write test: `test_submitted_message_has_input_ref` — verify `.input`
3. Implement `class Submitted(Message)` inside `InputPane`

### 3. History Navigation Logic (`_navigate_history`) — **Code-First** 🟢

**Approach**: Code-First (update existing)
**Rationale**: The history logic is unchanged algorithmically — only the property access changes from `.value` to `.text`. The 4 existing tests already cover this behavior comprehensively. Update them after migration.

**Test Requirements:**
* Coverage Target: **90%** (existing tests provide this)
* Test Types: Unit (existing tests updated)
* Critical Scenarios:
  * Up arrow retrieves most recent command
  * Up+Up retrieves second most recent
  * Up+Down returns to most recent
  * Empty history does not crash
  * Current input preserved during navigation

**Testing Sequence (Code-First):**
1. Migrate `_navigate_history` to use `self.text` instead of `self.value`
2. Update existing 4 tests: `.value` assertions → `.text` assertions
3. Verify all pass

### 4. App Integration (`app.py` handler) — **Code-First** 🟢

**Approach**: Code-First
**Rationale**: The custom `Submitted` message preserves the `event.value` / `event.input.clear()` API. No functional changes are needed in `app.py`'s `handle_input()`. Existing tests verify routing behavior.

**Test Requirements:**
* Coverage Target: **80%** (existing tests)
* Test Types: Integration (existing tests updated)
* Critical Scenarios:
  * Input echoed to output after submit
  * Input cleared after submit
  * Agent command routes to executor
  * System command dispatches correctly

**Testing Sequence (Code-First):**
1. Verify existing tests still pass after widget migration
2. Update `test_input_cleared_after_submit`: `.value` → `.text`
3. No new tests needed

### 5. CSS & Layout (`styles.css`) — **Code-First** 🟢

**Approach**: Code-First
**Rationale**: CSS is visual — verify by running the app and checking existing layout tests. No TDD value for static styling.

**Test Requirements:**
* Coverage Target: N/A (visual)
* Test Types: Existing layout tests (`test_app_displays_both_panes`, `test_status_panel_between_header_and_prompt`)
* Critical Scenarios:
  * `#prompt` widget renders in app
  * Layout hierarchy preserved (header → status → prompt)

**Testing Sequence (Code-First):**
1. Update CSS with height properties
2. Verify existing layout tests pass
3. Manual visual check

---

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0 + pytest-asyncio 0.23.0
* **Version**: textual[dev] 7.4.0
* **Configuration**: `pyproject.toml` → `[tool.pytest.ini_options]`
* **Runner**: `uv run pytest tests/test_ui/`

### Testing Tools Required
* **Mocking**: `unittest.mock` (MagicMock, AsyncMock) — for executor/router in integration tests
* **Assertions**: Built-in pytest `assert` — matches all existing tests
* **Coverage**: pytest-cov with `--cov=src/teambot --cov-report=term-missing` (configured in pyproject.toml)
* **Test Data**: Inline strings (commands like `"first"`, `"@pm test"`) — matches existing pattern
* **UI Testing**: Textual's `app.run_test()` + `pilot` API — `pilot.press()`, `pilot.click()`, `pilot.pause()`

### Test Organization
* **Test Location**: `tests/test_ui/test_input_pane.py` (primary), `tests/test_ui/test_app.py` (integration)
* **Naming Convention**: `test_*.py` files, `Test*` classes, `test_*` methods
* **Fixture Strategy**: `conftest.py` provides `mock_executor`, `mock_router`
* **Setup/Teardown**: Textual `async with app.run_test() as pilot:` context manager

---

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 80% minimum (project standard)
* **Integration Coverage**: 80% (project standard)
* **Critical Path Coverage**: 100% (Enter-submit, history navigation)
* **Error Path Coverage**: 80%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `InputPane._on_key` (key handling) | 95% | — | **CRITICAL** | TDD — all key paths tested |
| `InputPane.Submitted` (custom message) | 100% | — | **CRITICAL** | TDD — API contract |
| `InputPane._navigate_history` (history) | 90% | — | HIGH | Existing tests cover this |
| `app.py:handle_input` (app integration) | — | 80% | HIGH | Existing tests updated |
| `styles.css` (layout) | — | Visual | MEDIUM | Existing layout tests |

### Critical Test Scenarios

1. **Enter Submits Input** (Priority: **CRITICAL**)
   * Description: Pressing Enter posts `Submitted` message with `.value` = text content
   * Test Type: Unit
   * Success Criteria: `Submitted` message received by app; `.value` matches typed text
   * Test Approach: TDD

2. **Enter Clears Input After Submit** (Priority: **CRITICAL**)
   * Description: After Enter, the TextArea content is empty
   * Test Type: Unit
   * Success Criteria: `input_pane.text == ""`
   * Test Approach: TDD

3. **Ctrl+Enter Inserts Newline** (Priority: **HIGH**)
   * Description: Pressing Ctrl+Enter inserts `\n` at cursor without submitting
   * Test Type: Unit
   * Success Criteria: `input_pane.text` contains `\n`; no `Submitted` message posted
   * Test Approach: TDD

4. **History Up on First Line Only** (Priority: **CRITICAL**)
   * Description: Up arrow triggers history only when `cursor_at_first_line` is True
   * Test Type: Unit
   * Success Criteria: On first line → shows previous command; on other lines → cursor moves up
   * Test Approach: TDD

5. **History Down on Last Line Only** (Priority: **CRITICAL**)
   * Description: Down arrow triggers history only when `cursor_at_last_line` is True
   * Test Type: Unit
   * Success Criteria: On last line → shows next in history; on other lines → cursor moves down
   * Test Approach: TDD

6. **Multi-Line Content Submitted Intact** (Priority: **HIGH**)
   * Description: Multi-line text (from paste or Ctrl+Enter) is submitted with newlines preserved
   * Test Type: Integration
   * Success Criteria: `event.value` contains `\n` characters
   * Test Approach: TDD

### Edge Cases to Cover

* **Empty input + Enter**: No `Submitted` message posted (matches current behavior)
* **Empty history + Up**: No crash, text unchanged
* **Multi-line history recall**: Full multi-line text restored when navigating history
* **Current input preserved**: Typing partial input, navigating history, returning restores partial input
* **Single-line Up/Down**: Behaves identically to old `Input` widget (history navigation)

### Error Scenarios

* **Unsupported terminal keybinding**: Ctrl+Enter/Alt+Enter not recognized → no error, just no newline inserted. Paste still works.
* **Very long input**: TextArea handles scrolling natively — no special handling needed

---

## Test Data Strategy

### Test Data Requirements
* **Command strings**: Inline short strings (`"first"`, `"second"`, `"@pm test"`) — matches existing tests
* **Multi-line strings**: `"line1\nline2"` for history and submission tests

### Test Data Management
* **Storage**: Inline in test functions (no external test data files)
* **Generation**: Manual — simple strings
* **Isolation**: Each test creates a fresh `TeamBotApp()` instance
* **Cleanup**: Automatic via Textual's `run_test()` context manager

---

## Example Test Patterns

### Existing Pattern from Codebase

**File**: `tests/test_ui/test_input_pane.py:9-34`
**Pattern**: Textual pilot-based widget interaction test

```python
@pytest.mark.asyncio
async def test_history_navigation_up(self):
    """Up arrow shows previous command."""
    from teambot.ui.app import TeamBotApp

    app = TeamBotApp()
    async with app.run_test() as pilot:
        input_pane = app.query_one("#prompt")

        # Submit some commands to build history
        await pilot.click("#prompt")
        await pilot.press("f", "i", "r", "s", "t")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.click("#prompt")
        await pilot.press("s", "e", "c", "o", "n", "d")
        await pilot.press("enter")
        await pilot.pause()

        # Press up arrow to get previous command
        await pilot.click("#prompt")
        await pilot.press("up")
        await pilot.pause()

        assert input_pane.value == "second"  # Will change to .text
```

**Key Conventions:**
* Import `TeamBotApp` inside test (avoids module-level import issues)
* Use `app.run_test()` context manager
* `pilot.click("#prompt")` to focus widget before key presses
* `pilot.pause()` after actions to allow event processing
* Assert against widget properties directly

### Recommended New Test Structure (TDD)

```python
class TestMultiLineInput:
    """Tests for multi-line input behavior."""

    @pytest.mark.asyncio
    async def test_enter_submits_text(self):
        """Enter key submits text via Submitted message."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            output = app.query_one("#output")
            await pilot.click("#prompt")
            await pilot.press("h", "e", "l", "l", "o")
            await pilot.press("enter")
            await pilot.pause()

            # Command should appear in output (echoed)
            assert len(output.lines) > 0

    @pytest.mark.asyncio
    async def test_ctrl_enter_inserts_newline(self):
        """Ctrl+Enter inserts newline without submitting."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#prompt")
            output = app.query_one("#output")
            initial_lines = len(output.lines)

            await pilot.click("#prompt")
            await pilot.press("l", "i", "n", "e", "1")
            await pilot.press("ctrl+enter")
            await pilot.press("l", "i", "n", "e", "2")
            await pilot.pause()

            # Should have newline in text, not submitted
            assert "\n" in input_pane.text
            assert len(output.lines) == initial_lines  # No new output
```

---

## Success Criteria

### Test Implementation Complete When:
- [ ] All 5 critical scenarios have TDD tests written and passing
- [ ] All 4 existing history tests updated (`.value` → `.text`) and passing
- [ ] Coverage targets met per component (95% key handling, 100% message, 90% history)
- [ ] All edge cases tested (empty input, empty history, multi-line history)
- [ ] Tests follow existing codebase conventions (pilot pattern, inline imports)
- [ ] `uv run pytest tests/test_ui/` passes with no failures
- [ ] Overall project `uv run pytest` passes (no regressions)

### Test Quality Indicators:
* Tests are readable with descriptive docstrings
* Tests are fast (Textual pilot tests run in <1s each)
* Tests are independent (fresh `TeamBotApp()` per test)
* Failures clearly indicate which behavior broke
* No excessive mocking — test real widget behavior via pilot

---

## Implementation Guidance

### For TDD Components (Key Handling, Submitted Message):
1. Write failing test for Enter-to-submit
2. Implement minimal `_on_key` with Enter handling
3. Write failing test for Ctrl+Enter newline
4. Add Ctrl+Enter handling
5. Write failing tests for conditional history
6. Add cursor position checks
7. Refactor when all tests pass

### For Code-First Components (History migration, CSS, App wiring):
1. Migrate `InputPane` base class and constructor
2. Update `_navigate_history` to use `.text`
3. Update CSS with height properties
4. Run existing tests — fix `.value` → `.text` assertions
5. Verify all pass

### For Hybrid Integration:
1. Start with TDD components (key handling)
2. Proceed to Code-First migration
3. Run full test suite: `uv run pytest tests/test_ui/`
4. Run full project suite: `uv run pytest`
5. Lint: `uv run ruff check .` and `uv run ruff format .`

---

## Considerations and Trade-offs

### Selected Approach Benefits:
* Critical user-facing behavior (Enter, history, newline) is regression-proof via TDD
* Mechanical migration work (`.value` → `.text`, CSS) proceeds efficiently without test-first overhead
* Existing test suite provides safety net for app integration

### Accepted Trade-offs:
* Ctrl+Enter/Alt+Enter tests may not exercise real terminal key sequences in CI (pilot simulates keys)
* Visual CSS changes are not automatically tested (rely on existing layout tests + manual check)

### Risk Mitigation:
* TDD for key handling ensures the most critical behaviors are locked down first
* Custom `Submitted` message preserves API contract — app.py doesn't need changes
* Running full `uv run pytest` after all changes catches any cross-module regressions

---

## References

* **Research Doc**: [.agent-tracking/research/20260210-enhanced-text-input-research.md](./../research/20260210-enhanced-text-input-research.md)
* **Test Examples**: `tests/test_ui/test_input_pane.py`, `tests/test_ui/test_app.py`, `tests/test_ui/test_integration.py`
* **Test Config**: `pyproject.toml` `[tool.pytest.ini_options]`
* **Textual TextArea Docs**: https://textual.textualize.io/widgets/text_area/

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow recommended approach per component

---

**Strategy Status**: DRAFT
**Approved By**: PENDING
**Ready for Planning**: YES
