<!-- markdownlint-disable-file -->
# Release Changes: Fix Pipeline Parse Error in REPL Parser

**Related Plan**: .teambot/pipeline-parse-error/artifacts/implementation_plan.md
**Implementation Date**: 2026-03-03

## Summary

Fix the REPL parser to correctly distinguish between pipeline operator syntax (`-> @agent`) and casual mentions of `->` in quoted strings by implementing quote-aware parsing helpers. Added apostrophe detection to avoid false positives from contractions like "what's".

## Changes

### Added

* `tests/test_repl/test_parser.py` - Added 3 new test classes: `TestQuoteAwareHelpers` (6 tests), `TestQuotedPipelineHandling` (9 tests), `TestQuotedDefaultAgentPipeline` (3 tests) for quote-aware pipeline parsing
* `src/teambot/repl/parser.py` - Added `_is_in_quotes()`, `_is_apostrophe()`, `_has_pipeline_outside_quotes()`, `_split_pipeline_quote_aware()` helper functions for quote-aware parsing

### Modified

* `src/teambot/repl/parser.py` - Updated `_parse_agent_command()`, `_parse_pipeline()`, and `needs_default_agent_for_pipeline()` to use quote-aware helpers

### Removed

## Release Summary

**Total Files Affected**: 2

### Files Created (0)

### Files Modified (2)

* `src/teambot/repl/parser.py` - Added 4 helper functions, modified 3 existing functions for quote-aware pipeline parsing
* `tests/test_repl/test_parser.py` - Added 18 new tests in 3 new test classes

### Files Removed (0)

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No deployment considerations - this is a pure code fix with no configuration changes.

