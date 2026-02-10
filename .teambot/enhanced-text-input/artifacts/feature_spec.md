<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Enhanced Multi-Line Text Input - Feature Specification Document
Version 0.1 | Status Draft | Owner TBD | Team TeamBot | Target TBD | Lifecycle Discovery

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-02-10 |
| Problem & Users | 100% | None | 2026-02-10 |
| Scope | 100% | None | 2026-02-10 |
| Requirements | 100% | None | 2026-02-10 |
| Metrics & Risks | 100% | None | 2026-02-10 |
| Operationalization | 80% | Rollout details TBD | 2026-02-10 |
| Finalization | 0% | Pending review | - |
Unresolved Critical Questions: 0 | TBDs: 1

---

## 1. Executive Summary

### Context
TeamBot is a CLI tool that orchestrates a team of 6 specialized AI agent personas through a Rich/Textual TUI. Users interact with agents by typing commands into an `InputPane` widget — a subclass of `textual.widgets.Input` — which is a **single-line text entry field** docked at the bottom of the left pane. This was adequate for short commands like `@pm plan the sprint` but is fundamentally limiting for the structured, multi-line content that developers routinely need to share with agents.

### Core Opportunity
Replace the single-line `InputPane` with a multi-line text input widget (based on `textual.widgets.TextArea`) that allows users to compose, paste, and edit structured content — code snippets, error messages, detailed instructions — directly in the input field. This removes the most significant friction point in the current input experience.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Support multi-line text entry in the input field | Functional | Single-line only | Multi-line with newline insertion | MVP | P0 |
| G-002 | Provide a taller, visible composition area | UX | 1 visible line | 3–5 visible lines | MVP | P0 |
| G-003 | Enable word wrap in the input field | UX | Horizontal scroll only | Soft wrap within visible width | MVP | P0 |
| G-004 | Support vertical scrolling for large input | UX | No scrolling (single line) | Scroll when content exceeds visible area | MVP | P1 |
| G-005 | Provide intuitive keybindings for newline vs. submit | UX | Enter submits (only action) | Enter submits; Alt+Enter / Ctrl+Enter inserts newline | MVP | P0 |
| G-006 | Preserve command history navigation | UX | Up/Down navigate history | Up/Down navigate history when cursor at first/last line | MVP | P0 |
| G-007 | Maintain backward compatibility | Technical | All existing workflows work | Zero regression in existing functionality | MVP | P0 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Migrate InputPane from Input to TextArea-based widget | Multi-line input functional with all keybindings | P0 | TBD |
| Preserve InputPane.Submitted event contract | app.py handle_input() works without modification | P0 | TBD |
| Implement cursor-aware history navigation | History triggers only at document boundaries | P0 | TBD |
| Validate with existing test suite | 1084+ tests pass, new tests cover multi-line scenarios | P0 | TBD |

---

## 2. Problem Definition

### Current Situation
The `InputPane` widget (`src/teambot/ui/widgets/input_pane.py`) extends `textual.widgets.Input`, which is a single-line text entry field by design. It is docked at the bottom of the left pane (30% width) via CSS `#prompt { dock: bottom; }`. Users type commands and press Enter to submit. Up/Down arrows navigate command history unconditionally.

The current input flow:
1. User types in the single-line `InputPane`
2. Enter triggers `Input.Submitted` → `InputPane.on_input_submitted()` stores in history
3. `app.py:handle_input()` receives `InputPane.Submitted`, extracts `event.value`, parses via `parse_command()`, routes to agent or system handler
4. `event.input.clear()` clears the field

### Problem Statement
Developers frequently need to share multi-line content with agents — code snippets, stack traces, error messages, structured instructions — but the single-line input field forces them to flatten everything into one line, losing the formatting and structure that agents need to produce accurate responses. There is no way to insert a newline, no room to review longer input, and no word wrap for readability.

### Root Causes
* `textual.widgets.Input` is architecturally single-line — it cannot be extended to support multiple lines
* No alternative multi-line input widget has been integrated into the UI
* The Enter key is exclusively bound to submission with no alternative for newline insertion
* The UI layout allocates minimal height to the input area

### Impact of Inaction
* **Reduced agent response quality**: Agents receive poorly-formatted single-line prompts lacking structural context
* **User friction**: Developers resort to external editors or pre-formatting workarounds that break their TUI workflow
* **Competitive gap**: Modern developer tools universally support multi-line input; a single-line field feels outdated
* **Adoption barrier**: New users encountering this limitation may perceive the tool as immature

---

## 3. Users & Personas
| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| Developer (primary) | Share code, errors, and structured text with agents | Cannot paste multi-line content; loses formatting | High — affects every session involving code |
| Team Lead | Compose detailed agent instructions | Cannot review or edit longer prompts before submission | Medium — affects complex planning tasks |
| New User | Intuitive, modern input experience | Expects multi-line support; finds single-line limiting | High — first-impression adoption risk |

### Journeys
**Current Journey (frustrated)**: Developer encounters error → copies stack trace → pastes into TeamBot → content flattened to single line → agent receives garbled context → poor response → developer reformats manually.

**Target Journey (smooth)**: Developer encounters error → copies stack trace → pastes into TeamBot → all lines preserved in visible input area → reviews and adds context → submits → agent receives well-formatted input → accurate response.

---

## 4. Scope

### In Scope
* Migrate `InputPane` from `textual.widgets.Input` to a `textual.widgets.TextArea`-based multi-line widget
* Implement Enter-to-submit and Alt+Enter/Ctrl+Enter-to-insert-newline keybindings
* Set input field height to show 3–5 visible lines
* Enable soft word wrap (default in TextArea)
* Implement cursor-position-aware history navigation (Up on first line, Down on last line)
* Preserve `InputPane.Submitted` event contract consumed by `app.py:handle_input()`
* Update CSS styling for the taller input area
* Add unit tests for new multi-line behavior
* Add acceptance tests for end-to-end multi-line workflows

### Out of Scope (justify if empty)
* **Syntax highlighting in input field** — adds complexity; can be a future enhancement
* **User-configurable input field height** — fixed height is sufficient for MVP
* **Rich rendering of multi-line content in output pane** — simple truncation is acceptable; output rendering is a separate concern
* **File attachment or drag-and-drop** — unrelated to text input enhancement
* **Input field resizing via mouse drag** — terminal mouse interaction is unreliable across emulators
* **Placeholder text animation or rich formatting** — cosmetic; not user-requested

### Assumptions
* A-001: Users run modern terminal emulators (iTerm2, Windows Terminal, GNOME Terminal, VS Code terminal) that correctly transmit Alt+Enter and/or Ctrl+Enter key sequences
* A-002: The majority of multi-line input is under 50 lines; very large pastes (100+) are an edge case where scroll support is sufficient
* A-003: A fixed input height of 3–5 lines is adequate without user-configurable sizing
* A-004: The `textual.widgets.TextArea` widget (available since Textual 0.38.0, soft wrap since 0.48.0) is stable and suitable for this use case — the project requires `textual>=0.47.0`
* A-005: The command parser (`parse_command()` in `repl/parser.py`) already handles multi-line content via `re.DOTALL` flag on regex patterns

### Constraints
* C-001: Must work within the Textual TUI framework — no external dependencies
* C-002: `textual.widgets.TextArea` has a different API from `Input` — no `.value` property (uses `.text`), no `Input.Submitted` event, different key handling
* C-003: Shift+Enter is indistinguishable from Enter in most terminal emulators — cannot be used as newline binding
* C-004: Up/Down arrow keys have dual meaning in a multi-line widget (cursor movement vs. history navigation) — must be disambiguated
* C-005: The input area shares vertical space with the header and status panel in a 30%-width left pane — taller input reduces status visibility
* C-006: The `InputPane.Submitted` event contract and `event.value` / `event.input` interface consumed by `app.py:handle_input()` must be preserved or adapted with minimal changes

---

## 5. Product Overview

### Value Proposition
Multi-line text input transforms TeamBot from a command-line-style tool into a composition-friendly interface where developers can share structured content — code, errors, instructions — exactly as intended, resulting in dramatically better agent responses and a smoother workflow.

### UX / UI

#### Visual Layout (Before → After)

**Before** (single-line):
```
┌─────────────────┬─────────────────────────────────┐
│  TeamBot        │                                 │
│  Status Panel   │         OutputPane              │
│  (full height)  │                                 │
├─────────────────┤                                 │
│ > _             │  ← single-line input            │
└─────────────────┴─────────────────────────────────┘
```

**After** (multi-line):
```
┌─────────────────┬─────────────────────────────────┐
│  TeamBot        │                                 │
│  Status Panel   │         OutputPane              │
│  (reduced ht)   │                                 │
├─────────────────┤                                 │
│ @pm review this │                                 │
│ code snippet:   │  ← 3-5 line input area          │
│ def hello():    │     with word wrap + scroll      │
│   print("hi")   │                                 │
│ _               │                                 │
└─────────────────┴─────────────────────────────────┘
```

#### Keybinding Summary
| Action | Key | Context |
|--------|-----|---------|
| Submit input | Enter | Always — primary action |
| Insert newline | Alt+Enter | Always — secondary action |
| Insert newline (alt) | Ctrl+Enter | Always — alternative binding |
| History: previous command | Up Arrow | Only when cursor is on **first line** of input |
| History: next command | Down Arrow | Only when cursor is on **last line** of input |
| Cursor: move up | Up Arrow | When cursor is NOT on first line |
| Cursor: move down | Down Arrow | When cursor is NOT on last line |

UX Status: Specified

---

## 6. Functional Requirements
| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Multi-line text entry | The input field accepts and displays content spanning multiple lines. Users can type or paste multi-line content. | G-001 | All | P0 | Paste a 5-line code snippet; all 5 lines appear in the input field | Core capability |
| FR-002 | Taller input area | The input field renders 3–5 visible lines of content, replacing the single-line field. | G-002 | All | P0 | Input field visually shows at least 3 lines; CSS height is explicitly set | Layout change |
| FR-003 | Word wrap | Text wraps within the visible width of the input field. No horizontal scrolling. | G-003 | All | P0 | Type a line longer than field width; text wraps to next visual line | TextArea `soft_wrap=True` (default) |
| FR-004 | Vertical scrolling | When content exceeds the visible area, the input field scrolls vertically. | G-004 | All | P1 | Paste 20+ lines; scroll up/down within the field | Built into TextArea's ScrollView base |
| FR-005 | Enter submits input | Pressing Enter submits the current input content (all lines) to the command handler. | G-005 | All | P0 | Type multi-line content, press Enter; content is submitted and field cleared | Override TextArea default (which inserts newline) |
| FR-006 | Alt+Enter inserts newline | Pressing Alt+Enter inserts a newline character at the cursor position. | G-005 | All | P0 | Press Alt+Enter; cursor moves to new line; content is NOT submitted | Custom keybinding on TextArea subclass |
| FR-007 | Ctrl+Enter inserts newline | Pressing Ctrl+Enter inserts a newline character at the cursor position (alternative binding). | G-005 | All | P1 | Press Ctrl+Enter; cursor moves to new line; same as Alt+Enter | Redundant binding for terminal compatibility |
| FR-008 | History navigation (Up) | Pressing Up arrow when cursor is on the **first line** of the input navigates to the previous command in history. When cursor is on any other line, Up moves cursor up one line. | G-006 | All | P0 | With multi-line content: Up on line 2 moves cursor to line 1; Up on line 1 loads previous history entry | Cursor-position-aware |
| FR-009 | History navigation (Down) | Pressing Down arrow when cursor is on the **last line** of the input navigates to the next command in history. When cursor is on any other line, Down moves cursor down one line. | G-006 | All | P0 | With multi-line content: Down on line 1 moves cursor to line 2; Down on last line loads next history entry | Cursor-position-aware |
| FR-010 | History preserves current input | When starting history navigation from non-empty multi-line input, the current content is saved and restored when navigating back (Down past newest). | G-006 | All | P0 | Type 3 lines, press Up (on first line) to see history, press Down to return; original 3 lines restored | Existing behavior, adapted for multi-line |
| FR-011 | Submitted event contract | The widget posts an event compatible with the existing `@on(InputPane.Submitted)` handler in `app.py`. The event exposes `.value` (string content) and `.input` (widget reference with `.clear()` method). | G-007 | N/A | P0 | `app.py:handle_input()` receives multi-line content via `event.value` without code changes (or minimal adapter changes) | API compatibility |
| FR-012 | Clear after submission | After submission, the input field is cleared (all lines removed, cursor at position 0,0). | G-007 | All | P0 | Submit multi-line content; field is empty afterward | `.clear()` method on TextArea |
| FR-013 | Placeholder text | The input field displays placeholder text (e.g., `@agent task or /command`) when empty. | G-007 | New User | P1 | Empty field shows placeholder; placeholder disappears on focus/typing | TextArea does not natively support placeholder — may need custom implementation or static hint |
| FR-014 | No line numbers in input | The input field does NOT show line numbers (gutter). | G-002 | All | P0 | Input field has no gutter/line number column | `show_line_numbers=False` (default) |
| FR-015 | No syntax highlighting | The input field does NOT apply syntax highlighting. | G-002 | All | P0 | All text renders in uniform style | `language=None` (default) |

### Feature Hierarchy
```plain
Enhanced Multi-Line Text Input
├── Widget Migration (FR-001, FR-002, FR-003, FR-004, FR-014, FR-015)
│   ├── Replace Input with TextArea subclass
│   ├── Set height to 3-5 lines
│   └── Configure soft wrap, no gutter, no syntax highlighting
├── Keybinding System (FR-005, FR-006, FR-007)
│   ├── Override Enter → submit
│   ├── Bind Alt+Enter → insert newline
│   └── Bind Ctrl+Enter → insert newline (alternative)
├── History Navigation (FR-008, FR-009, FR-010)
│   ├── Detect cursor on first/last line
│   ├── Conditionally trigger history vs. cursor movement
│   └── Save/restore multi-line content during navigation
├── API Compatibility (FR-011, FR-012)
│   ├── Post InputPane.Submitted with .value and .input
│   └── Implement .clear() for full content removal
└── Polish (FR-013)
    └── Placeholder text when empty
```

---

## 7. Non-Functional Requirements
| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Performance | Input rendering must not introduce visible lag | < 16ms frame time during typing (60fps) | P0 | Manual testing: type rapidly in multi-line field; no perceptible lag | TextArea is optimized for this |
| NFR-002 | Performance | Paste of large content must complete without hang | Paste 100 lines completes in < 1s | P1 | Test: paste 100-line text; field populates without freeze | TextArea handles large documents |
| NFR-003 | Usability | Keybindings must be discoverable | Placeholder or status hint shows "Alt+Enter: new line" | P1 | Visual inspection: hint visible to new users | Could be placeholder text or tooltip |
| NFR-004 | Compatibility | Must work in major terminal emulators | iTerm2, Windows Terminal, GNOME Terminal, VS Code terminal | P0 | Manual test in each emulator: Alt+Enter inserts newline, Enter submits | Alt+Enter may not work in all; Ctrl+Enter as fallback |
| NFR-005 | Reliability | No data loss on submission | Submitted content equals content visible in input field | P0 | Automated test: compare submitted `event.value` with known multi-line input | Critical correctness requirement |
| NFR-006 | Maintainability | Widget code follows existing codebase patterns | Single file, < 150 lines, clear docstrings | P1 | Code review | Match input_pane.py style |
| NFR-007 | Accessibility | Input field remains keyboard-navigable | Tab focuses input; all actions available via keyboard | P0 | Manual test: navigate to input via Tab, compose and submit content | No mouse required |
| NFR-008 | Layout | Input area must not collapse status panel at 80×24 terminal | Status panel shows at least 2 agent statuses at minimum terminal size | P1 | Manual test: resize terminal to 80×24; verify both panels visible | Height constraint |

---

## 8. Data & Analytics (Conditional)

### Inputs
* User-typed text (multi-line strings)
* Pasted content from clipboard
* History entries (list of previously submitted strings)

### Outputs / Events
* `InputPane.Submitted` event containing the full multi-line text as `event.value`
* Command parsed by `parse_command()` (already supports multi-line via `re.DOTALL`)

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Multi-line submissions | Usage | 0% of submissions | Measurable adoption | 30 days post-release | N/A (no telemetry) |
| Test suite pass rate | Quality | 100% (1084 tests) | 100% (1084+ tests) | At merge | pytest |
| New test coverage | Quality | 0 multi-line tests | ≥ 10 new tests covering FR-001 through FR-012 | At merge | pytest --cov |

---

## 9. Dependencies
| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| `textual>=0.47.0` | Library | High | Textual team | TextArea API may change in future versions | Pin minimum version; test against latest |
| `textual.widgets.TextArea` | API | High | Textual team | TextArea available since 0.38.0, soft wrap since 0.48.0; project requires ≥0.47.0 which may need bump to ≥0.48.0 for soft wrap | Verify installed version supports `soft_wrap`; bump minimum if needed |
| `src/teambot/ui/app.py` | Internal | High | TeamBot team | `handle_input()` consumes `InputPane.Submitted` event | Preserve event contract or update handler |
| `src/teambot/repl/parser.py` | Internal | Low | TeamBot team | Already supports multi-line via `re.DOTALL` | No changes expected |
| `src/teambot/ui/styles.css` | Internal | Medium | TeamBot team | CSS must be updated for taller input area | Straightforward height change |
| `tests/test_ui/test_input_pane.py` | Internal | Medium | TeamBot team | Existing tests must be adapted for TextArea API | Update test assertions for new widget type |

---

## 10. Risks & Mitigations
| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | TextArea API differs significantly from Input — `event.value` vs `.text`, no `Submitted` event, different key handling | High | High | Create adapter layer: custom `Submitted` message class, property aliases, `_on_key` override for Enter | TBD | Open |
| R-002 | Alt+Enter not captured correctly in some terminal emulators (e.g., some Linux terminals send escape sequence differently) | Medium | Medium | Support both Alt+Enter AND Ctrl+Enter as newline bindings; document supported terminals | TBD | Open |
| R-003 | History navigation UX confusion — users unsure when Up/Down moves cursor vs. navigates history | Medium | Medium | Only trigger history at document boundaries (first line for Up, last line for Down); consistent with multi-line editors | TBD | Open |
| R-004 | Taller input area reduces visible status panel at small terminal sizes (80×24) | Low | Medium | Cap input height at 5 lines; test at minimum terminal size; ensure status panel gets remaining space | TBD | Open |
| R-005 | Textual minimum version may need bump from ≥0.47.0 to ≥0.48.0 for TextArea soft wrap support | Low | Medium | Check if soft_wrap is available in 0.47.0; if not, bump dependency | TBD | Open |
| R-006 | Placeholder text not natively supported by TextArea widget | Low | High | Implement custom placeholder via overlay Static widget or conditional rendering when TextArea is empty | TBD | Open |
| R-007 | Existing UI tests (`test_input_pane.py`) rely on Input-specific APIs (e.g., `pilot.press("f", "i", "r", "s", "t")` to type characters) | Medium | High | Update tests to use TextArea-compatible input methods | TBD | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification
User input text is transient and local. No data is persisted beyond the session history list (in-memory). No PII is collected or transmitted by the input widget.

### PII Handling
Not applicable — input content is processed locally and passed to the Copilot CLI for agent execution. No additional PII handling is introduced by this feature.

### Threat Considerations
No new attack surface. The input widget processes text locally within the Textual framework. Content is passed to `parse_command()` which already handles untrusted input.

---

## 12. Operational Considerations
| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Standard release via `uv sync` | No new dependencies; TextArea is built into Textual |
| Rollback | Revert to previous `input_pane.py` and CSS | Single-file change; clean rollback path |
| Monitoring | N/A | Client-side TUI; no server monitoring |
| Alerting | N/A | No alerting infrastructure |
| Support | Document keybindings in README and `/help` command | Users need to discover Alt+Enter |
| Capacity Planning | N/A | Local execution only |

---

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Gate Criteria | Owner |
|-------|--------------|-------|
| Implementation | FR-001 through FR-012 implemented; unit tests pass | TBD |
| Integration Testing | Existing 1084+ tests pass; new acceptance tests pass | TBD |
| Manual Validation | Tested in iTerm2, VS Code terminal, GNOME Terminal | TBD |
| Release | Merged to main; documentation updated | TBD |

### Communication Plan
Update `/help` command output to document new keybindings. Add a note to README about multi-line input support.

---

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| Q-001 | Should the Textual minimum version be bumped from ≥0.47.0 to ≥0.48.0 for soft_wrap support? | TBD | Before implementation | Open |

All other questions from the discovery phase have been resolved and incorporated into requirements.

---

## 15. Acceptance Test Scenarios

### AT-001: Paste Multi-Line Code Snippet
**Description**: User pastes a multi-line code snippet into the input field and submits it to an agent
**Preconditions**: TeamBot TUI is running, input field is focused, clipboard contains a 5-line Python function
**Steps**:
1. User pastes clipboard content (Ctrl+V) into the input field
2. All 5 lines appear in the input field with line breaks preserved
3. User prefixes content with `@builder-1 review this code:` on the first line (using Alt+Enter after the prefix to keep the code on subsequent lines)
4. User presses Enter to submit
**Expected Result**: The full multi-line content (prefix + 5 lines of code) is submitted to builder-1 agent. Input field is cleared.
**Verification**: `event.value` in `handle_input()` contains the complete multi-line string with `\n` separators. Agent receives all lines.

### AT-002: Enter Submits, Alt+Enter Inserts Newline
**Description**: User composes a multi-line message using Alt+Enter for line breaks, then submits with Enter
**Preconditions**: TeamBot TUI is running, input field is empty and focused
**Steps**:
1. User types `@pm plan the following:`
2. User presses Alt+Enter (newline inserted, NOT submitted)
3. User types `- Add authentication`
4. User presses Alt+Enter (newline inserted)
5. User types `- Add logging`
6. User presses Enter (content submitted)
**Expected Result**: Three lines are submitted as a single command. The PM agent receives all three lines. Input field is cleared.
**Verification**: Output pane echoes the command. No submission occurred at steps 2 or 4. Submission occurred only at step 6.

### AT-003: History Navigation in Multi-Line Context
**Description**: User composes multi-line input, navigates history, then returns to current input
**Preconditions**: User has previously submitted at least one command (e.g., `@pm hello`). Input field is empty.
**Steps**:
1. User types `line one` then Alt+Enter then `line two` (2-line input)
2. Cursor is on line 2. User presses Up arrow → cursor moves to line 1 (normal cursor movement)
3. Cursor is now on line 1. User presses Up arrow → history loads previous command (`@pm hello`), replacing input
4. User presses Down arrow → original 2-line input is restored (`line one\nline two`)
**Expected Result**: Up/Down on interior lines move the cursor. Up on first line and Down on last line trigger history navigation. Original multi-line input is preserved through history navigation.
**Verification**: Assert input content at each step matches expected state.

### AT-004: Single-Line Workflow Backward Compatibility
**Description**: Existing single-line commands continue to work identically
**Preconditions**: TeamBot TUI is running
**Steps**:
1. User types `@pm create a plan` (single line, no Alt+Enter used)
2. User presses Enter
3. Command is submitted, parsed, and routed to PM agent
4. User presses Up arrow
5. Previous command `@pm create a plan` is loaded into input
**Expected Result**: Single-line workflows work exactly as before. No behavioral difference for users who don't use multi-line features.
**Verification**: Identical to current test assertions in `test_input_pane.py`

### AT-005: Word Wrap and Scrolling
**Description**: Long text wraps and excessive content scrolls vertically
**Preconditions**: TeamBot TUI is running, input field is focused
**Steps**:
1. User types a line that exceeds the input field width (e.g., 200 characters)
2. Text wraps to the next visual line (no horizontal scrollbar)
3. User pastes 20 lines of content
4. Input field shows the most recent lines; user can scroll up to see earlier lines
**Expected Result**: Word wrap is active. Vertical scrolling works. No horizontal scrolling is required.
**Verification**: Visual inspection confirms wrap. All 20 lines are accessible via scrolling.

### AT-006: Ctrl+Enter as Alternative Newline Binding
**Description**: Ctrl+Enter works as an alternative to Alt+Enter for inserting newlines
**Preconditions**: TeamBot TUI is running, input field is focused
**Steps**:
1. User types `first line`
2. User presses Ctrl+Enter
3. Newline is inserted; cursor moves to new line
4. User types `second line`
5. User presses Enter to submit
**Expected Result**: Ctrl+Enter inserts a newline (same as Alt+Enter). Enter submits both lines.
**Verification**: Submitted content contains `first line\nsecond line`

---

## 16. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 0.1 | 2026-02-10 | BA Agent | Initial specification draft | Creation |

---

## 17. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Code | `src/teambot/ui/widgets/input_pane.py` | Current InputPane implementation — extends `textual.widgets.Input` with history navigation | N/A |
| REF-002 | Code | `src/teambot/ui/app.py:100-141` | `handle_input()` — consumes `InputPane.Submitted`, extracts `event.value`, routes to agent/system handlers | N/A |
| REF-003 | Code | `src/teambot/ui/styles.css:32-34` | CSS for `#prompt` — `dock: bottom` | N/A |
| REF-004 | Code | `src/teambot/repl/parser.py` | `parse_command()` uses `re.DOTALL` — already supports multi-line content | N/A |
| REF-005 | Documentation | Textual TextArea widget docs | TextArea API: `.text` property, `soft_wrap`, `cursor_location`, `Changed`/`SelectionChanged` messages, key bindings | N/A |
| REF-006 | Code | `tests/test_ui/test_input_pane.py` | Existing tests: history up/down, empty history, preserves current input | N/A |
| REF-007 | Artifact | `.teambot/enhanced-text-input/artifacts/problem_statement.md` | Business problem analysis with pain points, goals, and risk assessment | N/A |
| REF-008 | Documentation | Textual TextArea bindings | Default bindings: up/down move cursor, no Enter-to-submit, Tab for focus or indent | N/A |

### Citation Usage
All functional requirements trace to REF-001 through REF-006 for current-state analysis. TextArea API details (FR-003, FR-004, FR-012, FR-014, FR-015) reference REF-005 and REF-008. Problem definition references REF-007.

---

## 18. Appendices

### Glossary
| Term | Definition |
|------|-----------|
| InputPane | Current single-line input widget in TeamBot (`textual.widgets.Input` subclass) |
| TextArea | Textual's built-in multi-line text editing widget (`textual.widgets.TextArea`) |
| Soft wrap | Text wrapping at the visible width boundary without inserting actual newline characters |
| Gutter | The column showing line numbers on the left side of a TextArea (disabled for input) |
| History navigation | Using Up/Down arrows to cycle through previously submitted commands |
| Submitted event | Custom Textual message posted when user presses Enter to submit input content |

### Technical Implementation Notes

#### TextArea API Differences from Input
| Aspect | `Input` (current) | `TextArea` (target) |
|--------|-------------------|---------------------|
| Content access | `.value` (str) | `.text` (str property) |
| Submission event | `Input.Submitted` (built-in) | None — must implement custom |
| Clear method | `.clear()` | `.clear()` (available) |
| Enter key | Submits | Inserts newline (must override) |
| Up/Down keys | Free for history | Move cursor (must conditionally override) |
| Placeholder | Native support | Not natively supported |
| Cursor position | N/A (single line) | `.cursor_location` → `(row, col)` tuple |
| Word wrap | N/A | `soft_wrap=True` (default) |
| Line numbers | N/A | `show_line_numbers=False` (default) |
| Base class | `Widget` | `ScrollView` |

#### Key Implementation Strategy
1. **Subclass TextArea**: Create new `InputPane` that extends `TextArea` instead of `Input`
2. **Override `_on_key`**: Intercept Enter (submit), Alt+Enter/Ctrl+Enter (newline), Up/Down (conditional history)
3. **Custom Submitted message**: Define `InputPane.Submitted` dataclass message with `.value` and `.input` attributes
4. **Cursor boundary detection**: Use `cursor_location[0]` to detect first line (row 0) and last line (`document.line_count - 1`)
5. **History storage**: Reuse existing `_history` list and `_navigate_history()` logic
6. **CSS update**: Change `#prompt` height from auto to explicit 5-line height

Generated 2026-02-10T04:15:00Z by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
