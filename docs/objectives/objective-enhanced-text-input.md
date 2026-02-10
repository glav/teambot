## Objective

Enhancement of the teambot user text input to support multi-line entry, improved visibility, and better usability for copy/pasting and structuring user queries.

**Goal**:
- Currently the text input in teambot is a single-line entry field which makes it difficult to compose longer, structured queries or paste multi-line content such as code snippets, error messages, or detailed instructions.
- With that in mind, the goal here is to do the following:
  - Allow multi-line input in the teambot user input field for easier copy/pasting and user query structure.
  - Extend the text entry box so it is taller (shows a few lines) and allows word wrap with scrolling for larger text entry.
  - Ensure the input experience supports intuitive line breaks (e.g. Alt+Enter, Ctrl+Enter, or Textual-specific bindings) while still allowing Enter to submit.

**Problem Statement**:
- Users cannot easily paste or compose multi-line content in the current single-line input field.
- The current input box is too small to provide adequate visibility of the text being entered, especially for longer queries.
- There is no word wrap in the input, forcing users to scroll horizontally to review their input before submission.
- Copy/pasting multi-line content (code blocks, logs, structured text) is awkward and often loses formatting or structure.

**Scope**:
- This objective applies to **both** the Textual split-pane UI and the legacy REPL:
  - **Split-pane UI**: Enhanced `InputPane` in `src/teambot/ui/widgets/input_pane.py` to support multi-line input using `TextArea` widget with Alt+Enter, Ctrl+Enter, and Shift+Enter key combinations.
  - **Legacy REPL**: Added backslash continuation support in `src/teambot/repl/loop.py` to allow multi-line input in legacy mode (lines ending with `\` continue on the next line).

**Success Criteria**:
- [ ] The text input field supports multi-line entry, allowing users to type or paste content spanning multiple lines.
- [ ] The text input box is visually taller, showing several lines of content at once rather than a single line.
- [ ] Word wrap is enabled in the input field so text wraps within the visible area instead of requiring horizontal scrolling.
- [ ] Vertical scrolling is supported when content exceeds the visible area of the input box.
- [ ] A clear key combination (e.g. Alt+Enter or Ctrl+Enter for new line, Enter to submit) is supported and intuitive to users. Note: Shift+Enter is generally not distinguishable from Enter in most terminal emulators.
- [ ] Command history navigation (Up/Down arrow) continues to work correctly — e.g. history is triggered only when the cursor is on the first or last line of the input.
- [ ] Existing single-line input workflows are not broken or degraded.
- [ ] Submitted multi-line content display does not change — simple truncation in the output pane is acceptable for now.

---

## Technical Context

**Target Codebase**: Existing teambot

**Primary Language/Framework**: Existing - python

**Testing Preference**: Hybrid

**Key Constraints**:
- Ensure no degradation of terminal and text-based experience, especially teambot output formatting.
- Must work within Rich/Textual TUI constraints and maintain compatibility with the existing UI layout.
- Input submission behavior must remain intuitive (Enter to submit should still be the primary action).

**Technical Risks / Considerations**:
- The current input is built on `textual.widgets.Input` (single-line by design) in `src/teambot/ui/widgets/input_pane.py`. Achieving multi-line support will require migrating to `textual.widgets.TextArea` (or a custom multi-line widget), which has different APIs, event handling, and styling. This is the primary implementation risk.
- Shift+Enter is generally **not distinguishable from Enter** in most terminal emulators at the escape-code level. Alternative keybindings such as `Alt+Enter`, `Ctrl+Enter`, or Textual-specific bindings should be evaluated.
- Up/Down arrow keys are currently used for command history navigation. In a multi-line `TextArea`, Up/Down move the cursor between lines. History navigation must be reconciled — e.g. only trigger history when the cursor is on the first line (Up) or last line (Down) of the input.

---

## Additional Context

- The specific key combination for new line vs submit should be evaluated during implementation. Shift+Enter is not viable in most terminals; prefer `Alt+Enter`, `Ctrl+Enter`, or other Textual-detectable bindings.
- Consider whether the input box height should be fixed or dynamically resize based on content.
- Word wrap should respect word boundaries to maintain readability.
- Scrolling behavior should be smooth and allow the user to review all entered content before submission.
- Submitted multi-line content should be displayed as-is with simple truncation in the output pane — no special rendering changes are needed at this stage.
- The teambot version number should be incremented appropriately according to semantic versioning (this is a backwards-compatible feature addition, so a **minor** version bump is expected).

---
