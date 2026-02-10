<!-- markdownlint-disable-file -->

# 🔬 Research: Enhanced Multi-Line Text Input for TeamBot

**Date:** 2026-02-10
**Status:** ✅ Complete
**Feature:** Multi-line text input in TeamBot split-pane UI

---

## 📋 Table of Contents

1. [Scope & Objectives](#scope--objectives)
2. [Entry Point Analysis](#entry-point-analysis)
3. [Current Implementation Analysis](#current-implementation-analysis)
4. [Technical Approach: Migrate Input → TextArea](#technical-approach-migrate-input--textarea)
5. [Key Binding Strategy](#key-binding-strategy)
6. [History Navigation Reconciliation](#history-navigation-reconciliation)
7. [API Migration Map](#api-migration-map)
8. [CSS & Layout Changes](#css--layout-changes)
9. [Testing Strategy Research](#testing-strategy-research)
10. [Task Implementation Requests](#task-implementation-requests)
11. [Potential Next Research](#potential-next-research)

---

## Scope & Objectives

### Research Questions

1. ✅ What widget migration is needed for multi-line input? (`Input` → `TextArea`)
2. ✅ How should Enter (submit) vs newline (Ctrl+Enter) be handled?
3. ✅ How should Up/Down history navigation coexist with multi-line cursor movement?
4. ✅ What API differences exist between `Input` and `TextArea`?
5. ✅ What CSS/layout changes are needed for a taller input box?
6. ✅ What test infrastructure changes are required?

### Assumptions

- Only the **split-pane UI** (`TeamBotApp` / Textual) is in scope; legacy `REPLLoop` is unchanged
- The parser layer (`parse_command`) already supports multiline input via `re.DOTALL`
- Textual version 7.4.0 is installed (TextArea available since 0.38.0, soft-wrap since 0.48.0)
- Terminal compatibility for keybindings varies; the approach must gracefully degrade

### Success Criteria

- [x] Technical approach validated with evidence
- [x] All entry points traced
- [x] API differences documented
- [x] Key binding strategy selected with rationale
- [x] Testing approach researched

---

## Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|---|---|---|---|
| **Split-pane UI** (Textual `InputPane`) | `InputPane` → `InputPane.Submitted` → `app.handle_input()` → `parse_command()` | ✅ YES | ✅ YES — migrate widget |
| **Legacy REPL** (`Prompt.ask()`) | `loop.py:368` → `parse_command()` | ❌ NO | ❌ NO — out of scope |
| **Programmatic** (test pilot) | `pilot.press()` → widget events | ✅ YES | ✅ YES — update tests |

### Code Path Trace

#### Entry Point 1: Split-Pane UI (Primary Target)

1. User types in `InputPane` widget (`src/teambot/ui/widgets/input_pane.py:6`)
2. Pressing Enter triggers `Input.Submitted` event (line 15)
3. Caught by `@on(InputPane.Submitted)` in `app.py:100`
4. Handler `handle_input()` reads `event.value.strip()` (line 103)
5. Calls `parse_command(command_text)` (line 114)
6. Routes to agent/system handler (lines 116-141)
7. Clears input: `event.input.clear()` (line 141)

**Impact:** Must replace `Input.Submitted` with custom `Submitted` message from `TextArea`-based widget. Must change `event.value` → access `text` property. Must change `event.input.clear()` to work with `TextArea.clear()`.

#### Entry Point 2: Legacy REPL (No Change Needed)

1. `REPLLoop._get_input()` → `Prompt.ask()` (loop.py:368-369)
2. Returns single-line string
3. Feeds into `parse_command()` (loop.py:316)

**No implementation needed.** This path is completely separate.

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| None identified | — | — |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## Current Implementation Analysis

### InputPane Widget (`src/teambot/ui/widgets/input_pane.py`)

```python
# Current: extends textual.widgets.Input (single-line)
class InputPane(Input):
    """Input pane with command history navigation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._history: list[str] = []
        self._history_index: int = -1
        self._current_input: str = ""
```

**Key behaviors (Lines 6-61):**

| Feature | Implementation | Line(s) |
|---|---|---|
| Widget base class | `textual.widgets.Input` | 3, 6 |
| Submit event | `on_input_submitted(event)` → stores in `_history` | 15-20 |
| History: Up arrow | `on_key` → `_navigate_history(1)` | 24-26 |
| History: Down arrow | `on_key` → `_navigate_history(-1)` | 27-29 |
| Read value | `self.value` / `event.value` | 17, 43, 58, 61 |
| Write value | `self.value = ...` | 58, 61 |

### App Integration (`src/teambot/ui/app.py`)

**Submit handler (Lines 100-141):**
```python
@on(InputPane.Submitted)
async def handle_input(self, event) -> None:
    command_text = event.value.strip()    # reads event.value
    # ... parse and route ...
    event.input.clear()                    # clears via event.input
```

**Key API dependencies:**
- `event.value` — text content from submit event
- `event.input` — reference to the widget that emitted the event
- `event.input.clear()` — clears the widget

### CSS Styling (`src/teambot/ui/styles.css`)

```css
#prompt {
    dock: bottom;      /* Single-line: docked at bottom of left panel */
}
```

No explicit height set — defaults to single-line `Input` height.

### Parser Support for Multiline ✅

```python
# src/teambot/repl/parser.py:79-82
AGENT_PATTERN = re.compile(r"^@([a-zA-Z][a-zA-Z0-9,_-]*)\s*(.*)", re.DOTALL)
SYSTEM_PATTERN = re.compile(r"^/([a-zA-Z][a-zA-Z0-9-]*)\s*(.*)", re.DOTALL)
```

**Both patterns use `re.DOTALL`** — the `.*` matches across newlines. Multi-line content is already fully supported at the parser level. ✅ No parser changes needed.

---

## Technical Approach: Migrate Input → TextArea

### ✅ Selected Approach: Subclass `TextArea` with Custom Submit Behavior

Replace `InputPane(Input)` with `InputPane(TextArea)`, overriding `_on_key` to intercept Enter for submission and providing custom keybindings for newline insertion.

### Rationale

| Criteria | `TextArea` subclass |
|---|---|
| Multi-line editing | ✅ Native support |
| Soft wrapping | ✅ Built-in (`soft_wrap=True` default) |
| Vertical scrolling | ✅ Inherits from `ScrollView` |
| Paste multi-line content | ✅ Works natively |
| Undo/Redo | ✅ Built-in (`Ctrl+Z`/`Ctrl+Y`) |
| Placeholder text | ✅ Supported via `placeholder` parameter |
| Key interception | ✅ Override `_on_key` method |
| Cursor position queries | ✅ `cursor_at_first_line`, `cursor_at_last_line` |

### TextArea API (Verified against Textual 7.4.0)

| Property/Method | Description |
|---|---|
| `text` (property, r/w) | Full text content (replaces `Input.value`) |
| `clear()` | Clears all content |
| `insert(text)` | Inserts text at cursor position |
| `cursor_location` | `(row, col)` tuple |
| `cursor_at_first_line` | `bool` — cursor on first line |
| `cursor_at_last_line` | `bool` — cursor on last line |
| `document.line_count` | Number of lines in document |
| `soft_wrap` | `bool` — word wrapping (default: `True`) |
| `placeholder` | Placeholder text when empty |
| `show_line_numbers` | `bool` — show gutter (default: `False`) |

### Messages Available

| Message | Exists? | Notes |
|---|---|---|
| `TextArea.Changed` | ✅ Yes | Fired on content change |
| `TextArea.SelectionChanged` | ✅ Yes | Fired on cursor/selection change |
| `TextArea.Submitted` | ❌ **No** | Must create custom message |

### Custom `Submitted` Message Design

```python
from textual.message import Message
from textual.widgets import TextArea

class InputPane(TextArea):
    class Submitted(Message):
        """Posted when user presses Enter to submit input."""
        def __init__(self, input: "InputPane", value: str) -> None:
            super().__init__()
            self.input = input    # Widget reference (compat with Input.Submitted)
            self.value = value    # Text content (compat with Input.Submitted)
```

This preserves the API contract used by `app.py:handle_input()`:
- `event.value` → works ✅
- `event.input` → works ✅
- `event.input.clear()` → `TextArea.clear()` works ✅

---

## Key Binding Strategy

### ✅ Selected: Enter Submits, Ctrl+Enter / Alt+Enter Inserts Newline

| Key | Action | Terminal Support |
|---|---|---|
| **Enter** | Submit input | ✅ Universal |
| **Ctrl+Enter** | Insert newline | ⚠️ Modern terminals (kitty protocol) |
| **Alt+Enter** | Insert newline (fallback) | ⚠️ Many terminals (ESC+CR sequence) |
| **Paste** | Multi-line paste works natively | ✅ Universal |

### Implementation

Override `_on_key` in the `InputPane` subclass:

```python
async def _on_key(self, event: events.Key) -> None:
    if event.key == "enter":
        # Submit: post Submitted message, prevent newline insertion
        event.stop()
        event.prevent_default()
        text = self.text.strip()
        self.post_message(self.Submitted(self, self.text))
        return

    if event.key in ("ctrl+enter", "alt+enter"):
        # Insert newline
        event.stop()
        event.prevent_default()
        self.insert("\n")
        return

    # History navigation (conditional on cursor position)
    if event.key == "up" and self.cursor_at_first_line:
        self._navigate_history(1)
        event.stop()
        event.prevent_default()
        return

    if event.key == "down" and self.cursor_at_last_line:
        self._navigate_history(-1)
        event.stop()
        event.prevent_default()
        return

    # All other keys: default TextArea behavior
    await super()._on_key(event)
```

### Terminal Compatibility Notes

- **Standard terminals** (xterm, GNOME Terminal, macOS Terminal): `Enter` sends `\r`. `Ctrl+Enter` may not be distinguishable. `Alt+Enter` typically sends `ESC` + `\r` which Textual may parse as `alt+enter` or as two separate events.
- **Modern terminals** (kitty, WezTerm, foot, iTerm2 with kitty protocol): Full modifier support via CSI sequences. `Ctrl+Enter` sends `\x1b[13;5u`, parsed as `ctrl+enter`. `Alt+Enter` sends `\x1b[13;3u`, parsed as `alt+enter`.
- **Paste**: Multi-line paste works universally in `TextArea` regardless of terminal. This is the primary way most users will enter multi-line content.

### Degradation Strategy

If neither `Ctrl+Enter` nor `Alt+Enter` works in a user's terminal:
- They can still **paste** multi-line content (the primary use case)
- Single-line usage continues to work identically to before

---

## History Navigation Reconciliation

### Problem

In `Input` (single-line), Up/Down always navigate history. In `TextArea` (multi-line), Up/Down move the cursor between lines. These must be reconciled.

### ✅ Selected Approach: Conditional History Based on Cursor Position

| Cursor Position | Up Arrow | Down Arrow |
|---|---|---|
| First line of document | 🔼 **Navigate history backward** | ↓ Move cursor down |
| Middle line | ↑ Move cursor up | ↓ Move cursor down |
| Last line of document | ↑ Move cursor up | 🔽 **Navigate history forward** |
| Single-line content (first AND last) | 🔼 **Navigate history backward** | 🔽 **Navigate history forward** |

### Implementation Using TextArea Properties

```python
# cursor_at_first_line: True when cursor is on row 0
# cursor_at_last_line: True when cursor is on the last row

if event.key == "up" and self.cursor_at_first_line:
    self._navigate_history(1)     # Go back in history
    event.stop()
    event.prevent_default()
    return

if event.key == "down" and self.cursor_at_last_line:
    self._navigate_history(-1)    # Go forward in history
    event.stop()
    event.prevent_default()
    return
```

This is intuitive because:
- On a single-line entry (most commands), Up/Down works exactly like before
- On multi-line content, Up/Down naturally move between lines, with history only at the edges
- This matches the behavior of multi-line inputs in Slack, Discord, and VS Code terminal

### History Storage

History entries will store the full multi-line text string. The `_navigate_history` method changes from setting `self.value` to setting `self.text`:

```python
def _navigate_history(self, direction: int) -> None:
    # Same logic, but use self.text instead of self.value
    if self._history_index == -1 and direction > 0:
        self._current_input = self.text    # was: self.value

    # ... (index calculation unchanged) ...

    if self._history_index == -1:
        self.text = self._current_input    # was: self.value = ...
    else:
        self.text = self._history[-(self._history_index + 1)]  # was: self.value = ...
```

---

## API Migration Map

### Property/Method Changes

| Usage Location | Old (Input) | New (TextArea) | File:Line |
|---|---|---|---|
| Read content | `self.value` | `self.text` | `input_pane.py:43,58,61` |
| Write content | `self.value = x` | `self.text = x` | `input_pane.py:58,61` |
| Submit event value | `event.value` | `event.value` (custom msg) | `app.py:103` |
| Clear input | `event.input.clear()` | `event.input.clear()` ✅ (same) | `app.py:105,141` |
| Constructor | `Input(placeholder=..., id=...)` | `TextArea(id=..., soft_wrap=True)` | `app.py:97` |
| Placeholder | `placeholder="..."` kwarg | `placeholder="..."` kwarg ✅ | `app.py:97` |
| Submit handler | `on_input_submitted(event)` | Removed — submit via `_on_key` | `input_pane.py:15` |
| Key handler | `on_key(event)` | `_on_key(event)` (async) | `input_pane.py:22` |

### Event Handler in App

```python
# BEFORE (app.py:100):
@on(InputPane.Submitted)
async def handle_input(self, event) -> None:
    command_text = event.value.strip()
    # ...
    event.input.clear()

# AFTER: Same! Custom Submitted message preserves API
@on(InputPane.Submitted)
async def handle_input(self, event) -> None:
    command_text = event.value.strip()    # ✅ works (custom message has .value)
    # ...
    event.input.clear()                    # ✅ works (TextArea has .clear())
```

### Widget Export (`src/teambot/ui/widgets/__init__.py`)

No changes needed — `InputPane` is still exported from the same location with the same name.

---

## CSS & Layout Changes

### Current CSS (`src/teambot/ui/styles.css:32-34`)

```css
#prompt {
    dock: bottom;
}
```

### Required Changes

```css
#prompt {
    dock: bottom;
    height: 5;           /* Show ~5 lines of text */
    min-height: 3;        /* At minimum 3 lines visible */
    max-height: 10;       /* Cap at 10 lines */
}
```

**Rationale:**
- `height: 5` — shows enough lines for typical multi-line input without dominating the left panel
- `min-height: 3` — ensures usability even in small terminals
- `max-height: 10` — prevents the input from consuming the entire panel
- `dock: bottom` — kept, anchors input at bottom of left panel

### TextArea Component Styling

To make the `TextArea` blend with the existing UI, additional CSS may be helpful:

```css
#prompt {
    dock: bottom;
    height: 5;
    min-height: 3;
    max-height: 10;
    border: none;         /* Remove TextArea default border if present */
    padding: 0;           /* Tight fit within panel */
}
```

### Visual Considerations

- `TextArea` default theme is `"css"` — inherits from app theme, no color clashes
- `show_line_numbers=False` (default) — appropriate for input, not code editing
- `soft_wrap=True` (default) — text wraps within visible area ✅
- `highlight_cursor_line=False` — may want to disable for cleaner input feel

---

## Testing Strategy Research

### Existing Test Infrastructure

| Item | Value |
|---|---|
| **Framework** | pytest 7.4.0 + pytest-asyncio 0.23.0 |
| **Location** | `tests/test_ui/` directory |
| **Pattern** | `test_*.py` files with `Test*` classes |
| **Runner** | `uv run pytest` (addopts: `--cov=src/teambot --cov-report=term-missing`) |
| **Async mode** | `asyncio_mode = "auto"` — all `@pytest.mark.asyncio` tests |
| **UI testing** | Textual's `app.run_test()` + `pilot` API |
| **Textual dep** | `textual[dev]>=0.47.0` (provides testing tools) |

### Existing Test Files Affected

| File | Tests | Impact |
|---|---|---|
| `tests/test_ui/test_input_pane.py` | 4 tests (history navigation) | 🔴 **Major rewrite** — API changes |
| `tests/test_ui/test_app.py` | 12 tests (app integration) | 🟡 **Moderate update** — `.value` → `.text` |
| `tests/test_ui/test_integration.py` | 5 tests (command routing) | 🟡 **Moderate update** — submit behavior |
| `tests/test_ui/conftest.py` | 2 fixtures | ✅ No change |

### Test Patterns Found

**Pattern 1: Textual Pilot Test** (from `test_input_pane.py:9-34`)
```python
@pytest.mark.asyncio
async def test_history_navigation_up(self):
    app = TeamBotApp()
    async with app.run_test() as pilot:
        input_pane = app.query_one("#prompt")
        await pilot.click("#prompt")
        await pilot.press("f", "i", "r", "s", "t")
        await pilot.press("enter")
        await pilot.pause()
        assert input_pane.value == "second"   # ← changes to .text
```

**Pattern 2: Widget Query** (from `test_app.py:50-51`)
```python
input_pane = app.query_one("#prompt")
assert input_pane.value == ""    # ← changes to input_pane.text == ""
```

### Test Changes Required

#### `test_input_pane.py` — History Navigation Tests

All 4 tests need `.value` → `.text` changes:
- `test_history_navigation_up` (line 34): `input_pane.value` → `input_pane.text`
- `test_history_navigation_down` (line 61): same
- `test_empty_history_no_crash` (line 78): same
- `test_history_preserves_current_input` (line 105): same

#### `test_app.py` — App Tests

- `test_input_cleared_after_submit` (line 51): `input_pane.value == ""` → `input_pane.text == ""`

#### New Tests Needed

| Test | Purpose |
|---|---|
| `test_multiline_paste` | Verify pasting multi-line text works |
| `test_ctrl_enter_inserts_newline` | Verify Ctrl+Enter adds newline |
| `test_enter_submits_multiline` | Verify Enter submits full multi-line content |
| `test_history_up_on_first_line_only` | Up arrow triggers history only when on first line |
| `test_history_down_on_last_line_only` | Down arrow triggers history only when on last line |
| `test_up_arrow_moves_cursor_in_multiline` | Up arrow moves cursor when not on first line |
| `test_submitted_event_has_value` | Custom Submitted message has `.value` attribute |
| `test_submitted_event_has_input_ref` | Custom Submitted message has `.input` reference |
| `test_placeholder_shown` | Placeholder text displayed when empty |

### Testing Approach Recommendation

| Component | Approach | Rationale |
|---|---|---|
| **InputPane widget** | Hybrid (update existing + new) | Existing tests cover history; add multiline-specific tests |
| **App integration** | Update existing | Minimal API surface change (`.value` → `.text`) |
| **Key bindings** | New tests | Novel functionality not previously tested |

### Coverage Standards

- **Unit Tests**: Match existing 80% coverage target
- **Critical Paths**: Enter-submit, Ctrl+Enter-newline, history navigation ← 100% required

---

## Task Implementation Requests

### Task 1: Migrate `InputPane` from `Input` to `TextArea`

**File:** `src/teambot/ui/widgets/input_pane.py`

**Changes:**
1. Change import from `textual.widgets.Input` to `textual.widgets.TextArea`
2. Import `Message` from `textual.message` and `events` from `textual`
3. Change class base: `InputPane(TextArea)` instead of `InputPane(Input)`
4. Add constructor params: `soft_wrap=True`, `show_line_numbers=False`, pass `id`/`placeholder` through
5. Define `class Submitted(Message)` with `input` and `value` attributes
6. Override `_on_key(event)`:
   - `"enter"` → stop + prevent_default + post `Submitted` message
   - `"ctrl+enter"` / `"alt+enter"` → stop + prevent_default + `self.insert("\n")`
   - `"up"` when `cursor_at_first_line` → history backward
   - `"down"` when `cursor_at_last_line` → history forward
   - All else → `await super()._on_key(event)`
7. Remove `on_input_submitted` method (replaced by `_on_key` Enter handling)
8. Remove `on_key` method (merged into `_on_key`)
9. Update `_navigate_history`: `self.value` → `self.text`
10. Update `on_input_submitted` history storage equivalent to be in the `_on_key` Enter handler

### Task 2: Update `app.py` Compose Method

**File:** `src/teambot/ui/app.py`

**Change at line 97:**
```python
# No functional change needed in handle_input() — custom Submitted message preserves API
# But compose() may need kwargs update if TextArea constructor differs
yield InputPane(placeholder="@agent task or /command", id="prompt")
```

The `InputPane` constructor should pass `placeholder` and `id` to `TextArea.__init__()`.

### Task 3: Update CSS for Taller Input

**File:** `src/teambot/ui/styles.css`

**Change lines 32-34:**
```css
#prompt {
    dock: bottom;
    height: 5;
    min-height: 3;
    max-height: 10;
}
```

### Task 4: Update Existing Tests

**Files:** `tests/test_ui/test_input_pane.py`, `tests/test_ui/test_app.py`, `tests/test_ui/test_integration.py`

- Replace `.value` assertions with `.text`
- Verify `enter` still triggers submission
- Verify history navigation still works

### Task 5: Add New Multi-Line Tests

**File:** `tests/test_ui/test_input_pane.py`

Add tests for:
- Ctrl+Enter inserts newline
- Enter submits multi-line content
- History navigation is conditional on cursor position
- Pasting multi-line content works
- Custom `Submitted` message API compatibility

---

## Potential Next Research

### 1. 🔍 Dynamic Height Resizing

**What:** Auto-resize the input pane height as the user types more lines (like Slack's input box grows).
**Why:** Fixed `height: 5` may waste space for single-line commands or be too small for very long inputs.
**Approach:** Watch `TextArea.Changed` events, calculate `document.line_count`, and dynamically set `styles.height`.
**Status:** Deferred — not in current scope. Start with fixed height.

### 2. 🔍 Visual Hint for Newline Keybinding

**What:** Show a hint like "Ctrl+Enter for new line" in the placeholder or status bar.
**Why:** Users may not discover the newline keybinding.
**Status:** Could be added as a placeholder suffix or status bar text. Low effort.

### 3. 🔍 Legacy REPL Multi-Line Support

**What:** Enable multi-line input in the legacy `REPLLoop` (non-Textual mode).
**Why:** Users in legacy mode also benefit from multi-line input.
**Approach:** Would require replacing `rich.prompt.Prompt.ask()` with a different input method (e.g., `prompt_toolkit`).
**Status:** Out of scope for this feature.

---

## Evidence Log

| # | Finding | Source | Verified |
|---|---|---|---|
| 1 | `InputPane` extends `textual.widgets.Input` | `src/teambot/ui/widgets/input_pane.py:3,6` | ✅ |
| 2 | Textual 7.4.0 installed, `TextArea` available | `uv.lock`, `pyproject.toml:12` | ✅ |
| 3 | `TextArea` has no `Submitted` message | `python -c "hasattr(TextArea, 'Submitted')"` → False | ✅ |
| 4 | `TextArea` has `cursor_at_first_line`, `cursor_at_last_line` | Python REPL verification | ✅ |
| 5 | Parser uses `re.DOTALL` — multiline already supported | `src/teambot/repl/parser.py:79,82` | ✅ |
| 6 | TextArea `_on_key` maps `"enter"` → `"\n"` insertion | `TextArea._on_key` source inspection | ✅ |
| 7 | Enter key in TextArea BINDINGS: NOT listed (handled in `_on_key`) | `TextArea.BINDINGS` inspection | ✅ |
| 8 | `TextArea.text` property replaces `Input.value` | Textual docs + Python REPL verification | ✅ |
| 9 | `TextArea.clear()` exists | Textual docs | ✅ |
| 10 | `TextArea.insert()` exists for programmatic insertion | Textual docs | ✅ |
| 11 | `TextArea` constructor accepts `placeholder`, `soft_wrap`, `id`, `show_line_numbers` | Textual docs | ✅ |
| 12 | Test suite uses `app.run_test()` + `pilot` pattern | `tests/test_ui/test_input_pane.py:15` | ✅ |
| 13 | App handler uses `event.value` and `event.input.clear()` | `src/teambot/ui/app.py:103,105,141` | ✅ |
| 14 | CSS `#prompt` has `dock: bottom` with no height | `src/teambot/ui/styles.css:32-34` | ✅ |
| 15 | Kitty protocol modifier support exists in Textual's XTermParser | `_xterm_parser.py:288-303` modifiers parsing | ✅ |
| 16 | `ctrl+enter` binding is syntactically valid in Textual | `Binding('ctrl+enter', ...)` succeeds | ✅ |
