<!-- markdownlint-disable-file -->
# Release Changes: Enhanced Multi-Line Text Input

**Related Plan**: 20260210-enhanced-text-input-plan.instructions.md
**Implementation Date**: 2026-02-10

## Summary

Migrated TeamBot's InputPane widget from Textual's single-line `Input` to multi-line `TextArea`, enabling multi-line composition, word wrap, scrolling, and Enter-to-submit / Ctrl+Enter-for-newline keybindings while preserving history navigation and existing workflows.

## Changes

### Added

* `tests/test_ui/test_input_pane.py` — Added `TestMultiLineInput` class with 13 new tests covering: Submitted message API contract, Enter-submit, Ctrl+Enter/Alt+Enter newline insertion, conditional history navigation, multi-line submission, and multi-line history recall

### Modified

* `src/teambot/ui/widgets/input_pane.py` — Migrated from `Input` to `TextArea` base class; added custom `Submitted(Message)` with `.value`/`.input` attributes; replaced `on_input_submitted`/`on_key` with async `_on_key` handler for Enter-submit, Ctrl+Enter/Alt+Enter newline, and conditional Up/Down history; updated `_navigate_history` to use `.text` instead of `.value`
* `src/teambot/ui/styles.css` — Added `height: 5; min-height: 3; max-height: 10;` to `#prompt` for taller multi-line input area
* `tests/test_ui/test_input_pane.py` — Updated 4 existing `TestInputPane` tests: `.value` → `.text` assertions
* `tests/test_ui/test_app.py` — Updated `test_input_cleared_after_submit`: `.value` → `.text` assertion

### Removed

* `src/teambot/ui/widgets/input_pane.py` — Removed `on_input_submitted` and `on_key` methods (replaced by `_on_key`)

## Release Summary

**Total Files Affected**: 4

### Files Created (0)

### Files Modified (4)

* `src/teambot/ui/widgets/input_pane.py` — Widget migration from Input to TextArea with custom message and key handling
* `src/teambot/ui/styles.css` — Taller input area CSS
* `tests/test_ui/test_input_pane.py` — Updated existing tests + 13 new multi-line tests
* `tests/test_ui/test_app.py` — Updated assertion from .value to .text

### Files Removed (0)

### Dependencies & Infrastructure

* **New Dependencies**: None (TextArea already available in textual>=0.47.0)
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No deployment changes needed. The feature is fully contained within the Textual split-pane UI.