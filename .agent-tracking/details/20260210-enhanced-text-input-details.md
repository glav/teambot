<!-- markdownlint-disable-file -->
# Implementation Details: Enhanced Multi-Line Text Input

**Research Reference**: [.agent-tracking/research/20260210-enhanced-text-input-research.md](../research/20260210-enhanced-text-input-research.md)
**Plan Reference**: [.agent-tracking/plans/20260210-enhanced-text-input-plan.instructions.md](../plans/20260210-enhanced-text-input-plan.instructions.md)
**Test Strategy**: [.agent-tracking/test-strategies/20260210-enhanced-text-input-test-strategy.md](../test-strategies/20260210-enhanced-text-input-test-strategy.md)

---

## Task 1.1: Write Submitted Message API Contract Tests

### Purpose
Verify the custom `InputPane.Submitted` message preserves the API contract used by `app.py:handle_input()` (Research Lines 159-175).

### Test File
`tests/test_ui/test_input_pane.py` — add to new `TestMultiLineInput` class.

### Tests to Write

**test_submitted_message_has_value**: Instantiate `InputPane.Submitted(input=mock, value="hello")` and assert `msg.value == "hello"`.

**test_submitted_message_has_input_ref**: Instantiate `InputPane.Submitted(input=widget, value="x")` and assert `msg.input is widget`.

### Key Points
- Import `InputPane` from `teambot.ui.widgets.input_pane`
- The `Submitted` class must inherit from `textual.message.Message`
- Both `.value` and `.input` are required for backward compatibility with `app.py:103,105,141` (Research Lines 196-201)

### Success Criteria
- Tests fail initially (message class not yet implemented)
- Tests verify both `.value` (str) and `.input` (widget reference) attributes

---

## Task 1.2: Write Enter-to-Submit Tests

### Purpose
Verify Enter key submits text via custom `Submitted` message and clears input (Research Lines 114-127).

### Test File
`tests/test_ui/test_input_pane.py` — add to `TestMultiLineInput` class.

### Tests to Write

**test_enter_submits_text**:
```python
@pytest.mark.asyncio
async def test_enter_submits_text(self):
    """Enter key submits text and echoes to output."""
    from teambot.ui.app import TeamBotApp

    app = TeamBotApp()
    async with app.run_test() as pilot:
        output = app.query_one("#output")
        await pilot.click("#prompt")
        await pilot.press("h", "e", "l", "l", "o")
        await pilot.press("enter")
        await pilot.pause()
        # Command should appear in output (echoed by handle_input)
        assert len(output.lines) > 0
```

**test_enter_clears_input**:
```python
@pytest.mark.asyncio
async def test_enter_clears_input(self):
    """Input is cleared after Enter submission."""
    from teambot.ui.app import TeamBotApp

    app = TeamBotApp()
    async with app.run_test() as pilot:
        input_pane = app.query_one("#prompt")
        await pilot.click("#prompt")
        await pilot.press("h", "i")
        await pilot.press("enter")
        await pilot.pause()
        assert input_pane.text == ""
```

**test_enter_on_empty_does_not_submit**:
```python
@pytest.mark.asyncio
async def test_enter_on_empty_does_not_submit(self):
    """Enter on empty input does not produce output."""
    from teambot.ui.app import TeamBotApp

    app = TeamBotApp()
    async with app.run_test() as pilot:
        output = app.query_one("#output")
        initial_lines = len(output.lines)
        await pilot.click("#prompt")
        await pilot.press("enter")
        await pilot.pause()
        assert len(output.lines) == initial_lines
```

### Success Criteria
- Tests use `.text` property (TextArea) not `.value` (Input)
- Tests fail initially (InputPane still extends Input)

---

## Task 1.3: Write Ctrl+Enter / Alt+Enter Newline Tests

### Purpose
Verify Ctrl+Enter and Alt+Enter insert newlines without submitting (Research Lines 112-143).

### Test File
`tests/test_ui/test_input_pane.py` — add to `TestMultiLineInput` class.

### Tests to Write

**test_ctrl_enter_inserts_newline**:
```python
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
        assert "line1" in input_pane.text
        assert "line2" in input_pane.text
        assert len(output.lines) == initial_lines  # Not submitted
```

**test_alt_enter_inserts_newline**: Same pattern but with `pilot.press("alt+enter")`.

### Key Points
- Terminal support for `ctrl+enter` varies (Research Lines 130-143); test via Textual pilot which simulates key events
- Both bindings should produce identical behavior (insert `\n`)

### Success Criteria
- Tests verify `"\n"` is present in `input_pane.text`
- Tests verify no `Submitted` message was posted (output unchanged)

---

## Task 1.4: Write Conditional History Navigation Tests

### Purpose
Verify Up/Down arrow history is conditional on cursor position (Research Lines 147-176).

### Test File
`tests/test_ui/test_input_pane.py` — add to `TestMultiLineInput` class.

### Tests to Write

**test_history_up_only_on_first_line**:
```python
@pytest.mark.asyncio
async def test_history_up_only_on_first_line(self):
    """Up arrow triggers history only when cursor is on first line."""
    from teambot.ui.app import TeamBotApp

    app = TeamBotApp()
    async with app.run_test() as pilot:
        input_pane = app.query_one("#prompt")

        # Submit a command to build history
        await pilot.click("#prompt")
        await pilot.press("p", "r", "e", "v")
        await pilot.press("enter")
        await pilot.pause()

        # Type multi-line content: "line1\nline2"
        await pilot.click("#prompt")
        await pilot.press("l", "i", "n", "e", "1")
        await pilot.press("ctrl+enter")
        await pilot.press("l", "i", "n", "e", "2")
        await pilot.pause()

        # Cursor is on line 2 (last line). Up should move cursor, NOT trigger history.
        await pilot.press("up")
        await pilot.pause()

        # Content should still be the multi-line text (not replaced by history)
        assert "line1" in input_pane.text
        assert "line2" in input_pane.text
```

**test_history_down_only_on_last_line**: Similar — submit history, type multi-line, move cursor to first line, press Down — should move cursor not trigger history.

**test_single_line_up_down_is_history**:
```python
@pytest.mark.asyncio
async def test_single_line_up_down_is_history(self):
    """Single-line content: Up/Down behaves like old Input (history)."""
    from teambot.ui.app import TeamBotApp

    app = TeamBotApp()
    async with app.run_test() as pilot:
        input_pane = app.query_one("#prompt")

        # Submit two commands
        await pilot.click("#prompt")
        await pilot.press("f", "i", "r", "s", "t")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.click("#prompt")
        await pilot.press("s", "e", "c", "o", "n", "d")
        await pilot.press("enter")
        await pilot.pause()

        # On single-line (empty), up should get history
        await pilot.click("#prompt")
        await pilot.press("up")
        await pilot.pause()
        assert input_pane.text == "second"
```

### Key Points
- `cursor_at_first_line` and `cursor_at_last_line` are TextArea built-in properties (Research Lines 97-102)
- For single-line content, both properties are True simultaneously, so both Up and Down trigger history

### Success Criteria
- Tests verify conditional behavior based on cursor position
- Tests verify single-line behavior matches old `Input` behavior

---

## Task 2.1: Migrate InputPane Base Class

### Purpose
Change `InputPane` from extending `Input` to extending `TextArea` (Research Lines 69-82).

### File
`src/teambot/ui/widgets/input_pane.py`

### Changes

**Replace imports (line 3)**:
```python
# Before:
from textual.widgets import Input

# After:
from textual import events
from textual.message import Message
from textual.widgets import TextArea
```

**Replace class declaration (line 6)**:
```python
# Before:
class InputPane(Input):

# After:
class InputPane(TextArea):
```

**Update constructor (lines 9-13)**:
```python
# Before:
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._history: list[str] = []
    self._history_index: int = -1
    self._current_input: str = ""

# After:
def __init__(self, placeholder: str = "", **kwargs):
    super().__init__(
        soft_wrap=True,
        show_line_numbers=False,
        **kwargs,
    )
    self.placeholder = placeholder
    self._history: list[str] = []
    self._history_index: int = -1
    self._current_input: str = ""
```

### Key Points
- `TextArea.__init__` does not accept `placeholder` as a positional/kwarg in the constructor the same way `Input` does — it's set as a property after construction (Research Lines 97-102, Evidence #11)
- `soft_wrap=True` is the default but explicit for clarity
- `show_line_numbers=False` is the default but explicit to prevent gutter display
- The `id` kwarg passes through via `**kwargs` to `Widget.__init__`

### Success Criteria
- `InputPane` instantiates without errors
- `InputPane(placeholder="...", id="prompt")` works in `app.py:97`

---

## Task 2.2: Implement Custom Submitted Message

### Purpose
Create a `Submitted` message class that preserves the API contract used by `app.py:handle_input()` (Research Lines 83-95).

### File
`src/teambot/ui/widgets/input_pane.py`

### Implementation

Add inside the `InputPane` class body (after class docstring, before `__init__`):

```python
class Submitted(Message):
    """Posted when user presses Enter to submit input."""

    def __init__(self, input: "InputPane", value: str) -> None:
        super().__init__()
        self.input = input
        self.value = value
```

### API Contract Verification

| Usage in app.py | Custom Message | Works? |
|-----------------|---------------|--------|
| `event.value.strip()` (line 103) | `self.value` = str | ✅ |
| `event.input.clear()` (line 105, 141) | `self.input` = InputPane (has `.clear()`) | ✅ |
| `@on(InputPane.Submitted)` (line 100) | `InputPane.Submitted` exists | ✅ |

### Success Criteria
- `InputPane.Submitted` is importable
- Message has `.value` (str) and `.input` (InputPane ref) attributes
- T1.1 tests pass

---

## Task 2.3: Implement _on_key Handler

### Purpose
Override `_on_key` to intercept Enter (submit), Ctrl+Enter/Alt+Enter (newline), and conditional history navigation (Research Lines 114-176).

### File
`src/teambot/ui/widgets/input_pane.py`

### Implementation

Remove old methods `on_input_submitted` (lines 15-20) and `on_key` (lines 22-29). Replace with:

```python
async def _on_key(self, event: events.Key) -> None:
    """Handle key events for submit, newline, and history."""
    if event.key == "enter":
        # Submit: post Submitted message
        event.stop()
        event.prevent_default()
        text = self.text
        if text.strip():
            self._history.append(text)
        self._history_index = -1
        self._current_input = ""
        self.post_message(self.Submitted(self, text))
        self.clear()
        return

    if event.key in ("ctrl+enter", "alt+enter"):
        # Insert newline at cursor position
        event.stop()
        event.prevent_default()
        self.insert("\n")
        return

    if event.key == "up" and self.cursor_at_first_line:
        # History backward (only when cursor on first line)
        event.stop()
        event.prevent_default()
        self._navigate_history(1)
        return

    if event.key == "down" and self.cursor_at_last_line:
        # History forward (only when cursor on last line)
        event.stop()
        event.prevent_default()
        self._navigate_history(-1)
        return

    # All other keys: default TextArea behavior
    await super()._on_key(event)
```

### Key Decisions
- `event.stop()` prevents the event from bubbling to parent widgets
- `event.prevent_default()` prevents TextArea's default Enter behavior (inserting `\n`)
- History is stored before clearing, preserving existing behavior from `on_input_submitted`
- The `Submitted` message is posted with the original text (before clear) to match `Input.Submitted` behavior
- The widget clears itself directly (not relying on `app.py` to clear) for immediate feedback, but `app.py` also calls `event.input.clear()` which is a no-op on already-empty TextArea

### Success Criteria
- Enter submits and clears
- Ctrl+Enter / Alt+Enter insert newline
- Up on first line / Down on last line trigger history
- Up/Down in middle of multi-line content move cursor normally
- T1.2, T1.3, T1.4 tests pass

---

## Task 2.4: Migrate _navigate_history to .text

### Purpose
Update `_navigate_history` to use `self.text` instead of `self.value` (Research Lines 178-195).

### File
`src/teambot/ui/widgets/input_pane.py`

### Changes

Line 43: `self._current_input = self.value` → `self._current_input = self.text`

Line 58: `self.value = self._current_input` → `self.text = self._current_input`

Line 61: `self.value = self._history[-(self._history_index + 1)]` → `self.text = self._history[-(self._history_index + 1)]`

### Key Points
- `TextArea.text` is a read/write property that replaces `Input.value` (Research Evidence #8)
- Setting `self.text = "..."` replaces all content in the TextArea
- Algorithmic logic of `_navigate_history` is unchanged

### Success Criteria
- History navigation sets TextArea content correctly
- Existing history tests pass after updating assertions to `.text`

---

## Task 3.1: Update CSS for Taller Input

### Purpose
Make the input area visually taller to show multiple lines (Research Lines 210-237).

### File
`src/teambot/ui/styles.css`

### Changes

Replace lines 32-34:
```css
/* Before: */
#prompt {
    dock: bottom;
}

/* After: */
#prompt {
    dock: bottom;
    height: 5;
    min-height: 3;
    max-height: 10;
}
```

### Rationale
- `height: 5` — shows ~5 lines of text, sufficient for most multi-line inputs
- `min-height: 3` — ensures usability in small terminals
- `max-height: 10` — prevents input from consuming the entire left panel
- `dock: bottom` — maintained, anchors input at bottom

### Success Criteria
- `#prompt` widget renders with increased height
- Existing layout tests pass (`test_app_displays_both_panes`, `test_status_panel_between_header_and_prompt`)

---

## Task 3.2: Verify app.py Compatibility

### Purpose
Confirm `app.py:handle_input()` works without changes due to custom `Submitted` message API preservation.

### File
`src/teambot/ui/app.py` — read-only verification, no changes expected.

### Verification Checklist

| Line | Code | Works With Custom Message? |
|------|------|---------------------------|
| 100 | `@on(InputPane.Submitted)` | ✅ `InputPane.Submitted` exists as nested class |
| 103 | `command_text = event.value.strip()` | ✅ Custom message has `.value` (str) |
| 105 | `event.input.clear()` | ✅ Custom message has `.input` (InputPane with `.clear()`) |
| 141 | `event.input.clear()` | ✅ Same as above |

### Expected Outcome
- No changes needed in `app.py`
- The `@on(InputPane.Submitted)` decorator will catch the custom message
- Run `uv run pytest tests/test_ui/test_app.py` to confirm

### Success Criteria
- All app integration tests pass without modifying `app.py`

---

## Task 4.1: Update Existing Tests .value → .text

### Purpose
Update all existing test assertions that reference `.value` to use `.text` (TextArea property).

### Files and Changes

**`tests/test_ui/test_input_pane.py`** — 4 changes in `TestInputPane` class:
- Line 34: `assert input_pane.value == "second"` → `assert input_pane.text == "second"`
- Line 61: `assert input_pane.value == "second"` → `assert input_pane.text == "second"`
- Line 78: `assert input_pane.value == ""` → `assert input_pane.text == ""`
- Line 105: `assert input_pane.value == "new"` → `assert input_pane.text == "new"`

**`tests/test_ui/test_app.py`** — 1 change in `TestTeamBotApp` class:
- Line 51: `assert input_pane.value == ""` → `assert input_pane.text == ""`

### Key Points
- Only assertion lines change — test logic and structure remain identical
- `pilot.press("enter")` behavior changes: in old `Input`, it triggers `Input.Submitted`; in new `InputPane(TextArea)`, it triggers `_on_key` which posts custom `InputPane.Submitted` — the app handler catches the same event name

### Success Criteria
- All 4 existing `TestInputPane` tests pass
- `test_input_cleared_after_submit` passes

---

## Task 4.2: Add Multi-Line Submission Integration Test

### Purpose
Verify that multi-line content composed via Ctrl+Enter is submitted intact with newlines preserved.

### File
`tests/test_ui/test_input_pane.py` — add to `TestMultiLineInput` class.

### Test

```python
@pytest.mark.asyncio
async def test_multiline_content_submitted_intact(self):
    """Multi-line content is submitted with newlines preserved."""
    from teambot.ui.app import TeamBotApp

    app = TeamBotApp()
    async with app.run_test() as pilot:
        output = app.query_one("#output")
        input_pane = app.query_one("#prompt")

        await pilot.click("#prompt")
        await pilot.press("l", "i", "n", "e", "1")
        await pilot.press("ctrl+enter")
        await pilot.press("l", "i", "n", "e", "2")
        await pilot.press("enter")
        await pilot.pause()

        # Input should be cleared after submit
        assert input_pane.text == ""
        # Output should have content (echoed)
        assert len(output.lines) > 0
```

### Success Criteria
- Multi-line text submitted and echoed to output
- Input cleared after submission
- Newlines in submitted text don't break command routing

---

## Task 4.3: Add Multi-Line History Recall Test

### Purpose
Verify that multi-line content is stored in history and recalled correctly.

### File
`tests/test_ui/test_input_pane.py` — add to `TestMultiLineInput` class.

### Test

```python
@pytest.mark.asyncio
async def test_multiline_history_recall(self):
    """Multi-line content is stored and recalled from history."""
    from teambot.ui.app import TeamBotApp

    app = TeamBotApp()
    async with app.run_test() as pilot:
        input_pane = app.query_one("#prompt")

        # Submit multi-line content
        await pilot.click("#prompt")
        await pilot.press("l", "i", "n", "e", "1")
        await pilot.press("ctrl+enter")
        await pilot.press("l", "i", "n", "e", "2")
        await pilot.press("enter")
        await pilot.pause()

        # Navigate history to recall it
        await pilot.click("#prompt")
        await pilot.press("up")
        await pilot.pause()

        # Should recall full multi-line text
        assert "line1" in input_pane.text
        assert "line2" in input_pane.text
        assert "\n" in input_pane.text
```

### Success Criteria
- Multi-line text stored in `_history` list
- Up arrow on empty input (first line = last line) triggers history
- Full multi-line text restored including newlines

---

## Task 5.1: Full Test Suite + Lint

### Purpose
Verify no regressions across the entire test suite and code passes linting.

### Commands

```bash
# Full test suite
uv run pytest

# Lint
uv run ruff check .
uv run ruff format .
```

### Expected Outcome
- All ~1084+ tests pass
- Zero lint errors
- Zero formatting issues

### Troubleshooting
- If non-UI tests fail: likely unrelated to this feature — check if they were already failing
- If UI tests fail: check `.value` vs `.text` assertions, check `Submitted` message API
- If lint fails: check imports (remove unused `Input` import, ensure new imports are at top)

### Success Criteria
- `uv run pytest` → all pass
- `uv run ruff check .` → no errors
- `uv run ruff format .` → no changes needed

---

## Task 5.2: Manual Visual Check

### Purpose
Visually confirm the enhanced input pane renders correctly in a terminal.

### Steps

1. Run `uv run teambot init` or launch TeamBot in a terminal
2. Verify input box is visually taller (~5 lines)
3. Type text and verify word wrap works
4. Press Enter — text submits, input clears
5. Try Ctrl+Enter — newline inserted (terminal dependent)
6. Try Alt+Enter — newline inserted (terminal dependent)
7. Type single-line command, press Up — history navigation works
8. Type multi-line content, press Up on second line — cursor moves up (not history)

### Expected Result
- Taller input box at bottom of left panel
- Word wrap active
- Enter submits, Ctrl+Enter adds newline
- History works on single-line, cursor movement works on multi-line

### Success Criteria
- Visual confirmation that the feature works as intended
- Document any terminal-specific keybinding issues (informational only)
