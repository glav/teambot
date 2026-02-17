<!-- markdownlint-disable-file -->
# Release Changes: Default Agent Context Reference Extraction Bug Fix

**Related Plan**: 20260217-default-agent-context-refs-plan.instructions.md
**Implementation Date**: 2026-02-17

## Summary

Bug fix to ensure `$agent` context references are correctly extracted when using default agent routing (without explicit `@agent` prefix). This enables referenced agent outputs to be injected into prompts for commands like `Incorporate feedback from $reviewer`.

## Changes

### Added

* `src/teambot/repl/parser.py` - Added `extract_references()` helper function to extract `$agent` references from content string

### Modified

* `src/teambot/repl/loop.py` - Added import for `extract_references` and use it when creating Command for default agent routing
* `src/teambot/ui/app.py` - Added import for `extract_references` and use it when creating Command for default agent routing
* `src/teambot/repl/router.py` - Added import for `extract_references` and use it when creating Command for default agent routing
* `tests/test_repl/test_parser.py` - Added `TestExtractReferences` class with 11 unit tests for the helper function
* `tests/test_integration/test_shared_context.py` - Added 2 integration tests for default agent + reference extraction

### Removed

## Release Summary

**Total Files Affected**: 6

### Files Created (0)

### Files Modified (6)

* `src/teambot/repl/parser.py` - Added `extract_references()` helper function
* `src/teambot/repl/loop.py` - Fixed default agent Command creation to extract references
* `src/teambot/ui/app.py` - Fixed default agent Command creation to extract references
* `src/teambot/repl/router.py` - Fixed default agent Command creation to extract references
* `tests/test_repl/test_parser.py` - Added 11 unit tests for `extract_references()`
* `tests/test_integration/test_shared_context.py` - Added 2 integration tests

### Files Removed (0)

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No special deployment considerations. This is a pure bug fix with no breaking changes.

