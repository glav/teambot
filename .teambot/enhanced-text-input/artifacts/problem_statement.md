# Problem Statement: Multi-Line Text Input for TeamBot

## Business Problem

TeamBot's text input is a **single-line entry field** (`textual.widgets.Input`) docked at the bottom of the left pane. This design creates friction for users who need to compose structured queries, paste multi-line content (code snippets, error messages, stack traces), or write detailed instructions to agents.

### Pain Points

| Pain Point | Impact | Frequency |
|---|---|---|
| **Cannot paste multi-line content** | Users must flatten code snippets, error logs, and structured text into a single line—losing formatting and context that agents need to produce accurate responses. | Every session involving code or logs |
| **No visible composition area** | The single-line field offers no room to review or edit longer input before submission. Users cannot see what they've typed beyond the visible width. | Every session with non-trivial queries |
| **No word wrap** | Long text scrolls horizontally, making it impossible to read the full input without cursor movement. | Frequent for detailed instructions |
| **No intuitive line breaks** | There is no supported key combination to insert a newline. Users who press Enter submit prematurely. | Every attempt at multi-line input |

### Who Is Affected

- **All TeamBot users** — anyone composing agent queries longer than a few words.
- **Developers** — the primary user base, who routinely need to share code, errors, and structured text with agents.

### Business Impact

- **Reduced input quality**: Agents receive poorly-formatted, single-line prompts that lack the structure needed for accurate responses.
- **Workflow friction**: Users resort to workarounds (external editors, pre-formatting) that break their flow within the TUI.
- **Adoption risk**: New users expect modern multi-line input in a developer tool; a single-line field feels limiting.

---

## Goals

### Primary Goal

> Enable multi-line text input in TeamBot so users can compose, paste, and edit structured content directly in the input field.

### Measurable Objectives

1. **Multi-line entry**: The input field accepts and displays content spanning multiple lines.
2. **Taller input area**: The field renders several visible lines (not a single line), giving users room to compose.
3. **Word wrap**: Text wraps within the visible area — no horizontal scrolling required.
4. **Vertical scrolling**: When content exceeds the visible height, users can scroll vertically.
5. **Intuitive keybindings**: A clear key combination inserts newlines (e.g., Alt+Enter or Ctrl+Enter) while Enter continues to submit.
6. **History navigation preserved**: Up/Down arrow history works correctly — history triggers only when the cursor is on the first line (Up) or last line (Down).
7. **No regression**: Existing single-line workflows, command parsing, output formatting, and agent routing remain unchanged.

---

## Success Criteria

| # | Criterion | Validation Method |
|---|---|---|
| SC-1 | The input field supports multi-line entry (type or paste multiple lines) | Manual test: paste a 5-line code snippet; all lines appear in the field |
| SC-2 | The input box is visually taller, showing several lines at once | Visual inspection: field height shows ≥ 3 lines of content |
| SC-3 | Word wrap is enabled — text wraps within the visible area | Manual test: type a line longer than the field width; text wraps to next visual line |
| SC-4 | Vertical scrolling works when content exceeds visible area | Manual test: paste 20+ lines; scroll up/down within the field |
| SC-5 | A documented key combination inserts newlines (Enter submits) | Manual test: press Alt+Enter (or Ctrl+Enter) — newline inserted; press Enter — input submitted |
| SC-6 | Command history navigation works: Up on first line → previous command; Down on last line → next command; Up/Down within multi-line content → cursor movement | Automated + manual tests covering all cursor positions |
| SC-7 | Existing single-line input workflows are not broken | Existing test suite passes (1084+ tests); single-line commands submit and route correctly |
| SC-8 | Multi-line submitted content does not break output display | Manual test: submit multi-line input; output pane renders without layout corruption (truncation is acceptable) |

---

## Current State Analysis

### Architecture (as-is)

```
InputPane (extends textual.widgets.Input)
├── Single-line text entry
├── Enter → on_input_submitted() → posts InputPane.Submitted
├── Up/Down → _navigate_history() (unconditional)
├── History stored in _history list, indexed by _history_index
└── Docked bottom of left pane (#prompt { dock: bottom })
```

**Key file**: `src/teambot/ui/widgets/input_pane.py`
**App integration**: `src/teambot/ui/app.py` — `handle_input()` listens for `InputPane.Submitted`
**Styling**: `src/teambot/ui/styles.css` — `#prompt { dock: bottom; }`

### Constraints

1. **Widget migration required**: `textual.widgets.Input` is single-line by design. Achieving multi-line support requires migrating to `textual.widgets.TextArea` (or a similar multi-line widget), which has a different API surface (events, value access, key handling).
2. **Terminal keybinding limitations**: Shift+Enter is **not distinguishable from Enter** in most terminal emulators. Newline insertion must use an alternative binding (Alt+Enter, Ctrl+Enter, or a Textual-specific binding).
3. **History navigation conflict**: Up/Down arrows serve dual purposes in a multi-line field (cursor movement vs. history navigation). These must be disambiguated based on cursor position.
4. **Layout impact**: A taller input area reduces vertical space available for the status panel. The layout must remain usable at typical terminal sizes (80×24 minimum).
5. **API compatibility**: The `InputPane.Submitted` event contract and `event.value` / `event.input` interface consumed by `app.py:handle_input()` must be preserved or adapted.

### Dependencies

- **Textual framework**: The solution depends on capabilities provided by the installed version of `textual`. The `TextArea` widget availability and API should be verified.
- **Rich library**: Output rendering uses Rich; multi-line input content must not introduce rendering issues.
- **Existing test suite**: 1084+ tests must continue to pass after the change.

---

## Assumptions

1. Users primarily interact with TeamBot via modern terminal emulators (iTerm2, Windows Terminal, GNOME Terminal, VS Code integrated terminal) that support Alt+Enter or Ctrl+Enter key sequences.
2. The majority of multi-line input will be under 50 lines; very large pastes (100+ lines) are an edge case where scroll support is sufficient.
3. The input field height can be fixed at a reasonable default (e.g., 3–5 visible lines) without needing user-configurable sizing in this iteration.
4. Simple truncation of multi-line content in the output pane is acceptable for the initial release; rich multi-line output rendering is out of scope.

---

## Out of Scope

- Syntax highlighting in the input field.
- User-configurable input field height.
- Rich rendering of multi-line content in the output pane.
- File attachment or drag-and-drop input.
- Input field resizing via mouse drag.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `TextArea` widget API differs significantly from `Input`, causing integration issues | High | Medium | Spike/prototype the widget swap early; define adapter interface |
| Alt+Enter / Ctrl+Enter not captured correctly in some terminal emulators | Medium | Medium | Support multiple bindings; document supported terminals |
| History navigation UX becomes confusing with cursor-position-based disambiguation | Medium | Low | Clear status bar hint showing available actions; user testing |
| Taller input area reduces usable space for status panel at small terminal sizes | Low | Low | Set a reasonable max height; test at 80×24 |

---

## Stakeholder Sign-Off

- [ ] Product / User representative confirms problem statement accuracy
- [ ] Technical lead confirms feasibility within Textual framework constraints
- [ ] QA confirms success criteria are testable
