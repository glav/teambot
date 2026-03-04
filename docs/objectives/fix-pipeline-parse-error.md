# Fix Pipeline Parse Error in REPL Parser

## Objective

**Goal**: Fix the REPL parser to correctly distinguish between pipeline operator syntax (`-> @agent`) and casual mentions of `->` in user messages.

**Problem Statement**: When a user's message contains the text `->` followed by `@` anywhere in their input (e.g., discussing the handoff operator syntax), the parser incorrectly treats it as a pipeline command. This causes a `ParseError: Invalid pipeline stage` when the text after `->` doesn't conform to valid pipeline syntax.

For example, this input causes the error:
```
@builder-2 it would seem that the '->' handoff operator causes issues when counting tokens. Documented syntax '@<agent> <input>' do not count tokens
```

The parser splits on `-> @` and tries to parse `@<agent> <input>' do not count tokens` as a pipeline stage, which fails.

**Success Criteria**:
- [ ] `-> @agent` patterns inside single or double quotes are not parsed as pipelines
- [ ] Nested quotes are handled correctly (e.g., `"the '->' operator"`)
- [ ] Multiple `->` in one message are handled correctly when some are quoted and some are not
- [ ] Valid pipeline syntax (`@pm task -> @builder implement`) continues to work correctly
- [ ] Parser returns appropriate error messages for genuinely malformed pipelines
- [ ] All existing parser tests pass
- [ ] New test cases cover the edge cases for quoted arrow operators

---

## Technical Context

**Target Codebase**: `/workspaces/teambot/src/teambot/repl/parser.py`

**Primary Language/Framework**: Python

**Testing Preference**: TDD - add failing tests first, then fix

**Key Constraints**:
- Must maintain backward compatibility with valid pipeline syntax
- Should handle various quoting styles: `'->'`, `"->"`
- Must not break existing agent command parsing
- Parser error messages should remain helpful

---

## Additional Context

### Root Cause Analysis

The issue is in `_parse_agent_command()` at line 193:
```python
if PIPELINE_PATTERN.search(input_text):
    return _parse_pipeline(input_text)
```

`PIPELINE_PATTERN = re.compile(r"\s*->\s*@")` uses `.search()` which finds the pattern anywhere in the input, including within quoted strings or prose discussion.

### Suggested Approaches

1. **Quote-aware parsing**: Skip `-> @` patterns that appear inside single or double quotes
2. **Smarter split**: Only treat `-> @` as a pipeline delimiter when it's at a "top level" (not inside quotes)
3. **Validate before splitting**: Check that the split would produce valid pipeline stages before committing to pipeline parsing

### Related Files

- `src/teambot/repl/parser.py` - Main parser logic
- `tests/test_repl/test_parser.py` - Parser tests

### Error Traceback Reference

```
ParseError: Invalid pipeline stage: @<agent> <input>' do not count tokens
```

Triggered in `_parse_pipeline()` at line 293 when `AGENT_PATTERN.match(part)` returns `None` for the malformed "stage".
