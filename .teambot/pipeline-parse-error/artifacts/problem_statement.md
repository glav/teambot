# Problem Statement: Pipeline Parse Error in REPL Parser

## Business Problem

Users interacting with TeamBot's REPL encounter unexpected parser errors when they casually mention the `->` operator (arrow syntax) within quoted strings in their messages. The parser incorrectly interprets these quoted occurrences as pipeline operator syntax, causing:

1. **False positive parse errors** - Messages like `@pm explain the '->' operator` fail with "Invalid pipeline stage" errors
2. **Broken user workflows** - Users cannot discuss, explain, or document the pipeline syntax itself using natural language
3. **Confusing error messages** - Users receive pipeline-related errors when they did not intend to create a pipeline

## Current Behavior

The REPL parser uses `PIPELINE_PATTERN = re.compile(r"\s*->\s*@")` to detect pipeline syntax. This pattern:

- ✅ Correctly identifies valid pipelines: `@pm task -> @builder implement`
- ❌ Incorrectly triggers on quoted arrows: `@pm explain the '->' operator`
- ❌ Does not distinguish between literal `->` text and operator syntax

## Affected Use Cases

| Use Case | Example Input | Expected | Actual |
|----------|---------------|----------|--------|
| Discussing pipeline syntax | `@pm explain how '->' works` | Normal command | Parse error |
| Double-quoted arrows | `@pm the "->" operator chains agents` | Normal command | Parse error |
| Nested quotes | `@pm describe the '"->"' syntax` | Normal command | Parse error |
| Mixed quoted/unquoted | `@pm explain "->" -> @builder implement` | Pipeline with quoted text in first stage | Undefined behavior |

## Business Goals

### Primary Goal
Enable users to discuss, document, or mention the `->` operator in messages without triggering pipeline parsing—while maintaining full backward compatibility with valid pipeline syntax.

### Success Metrics

1. **Zero false positives** - Quoted `->` patterns are never parsed as pipelines
2. **Full backward compatibility** - All existing valid pipeline commands continue to work
3. **100% test coverage** - All edge cases documented and tested
4. **Clear error messages** - When pipelines are genuinely malformed, errors remain helpful

## Stakeholders

| Role | Interest |
|------|----------|
| End Users | Can use natural language including arrow symbols without errors |
| Developers | Clear, maintainable parser logic with comprehensive tests |
| QA | Testable acceptance criteria for all quoting scenarios |

## Constraints

1. **Backward compatibility required** - Existing pipeline syntax must continue to work exactly as before
2. **Quoting styles** - Must handle single quotes (`'`), double quotes (`"`), and nested quotes
3. **Multiple arrows** - Messages may contain both quoted and unquoted `->` operators; only unquoted should trigger pipelines
4. **Parser error messages** - Must remain helpful for genuinely malformed pipelines
5. **Existing tests** - All current parser tests must continue to pass

## Dependencies

- **Source file**: `/workspaces/teambot/src/teambot/repl/parser.py`
- **Test files**: 
  - `/workspaces/teambot/tests/test_repl/test_parser.py`
  - `/workspaces/teambot/tests/test_repl/test_parser_extended.py`
- **Pattern definitions**: `PIPELINE_PATTERN`, `RAW_PIPELINE_PATTERN`

## Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC-01 | `'->'` patterns inside single quotes are NOT parsed as pipelines | Unit test |
| AC-02 | `"->"` patterns inside double quotes are NOT parsed as pipelines | Unit test |
| AC-03 | Nested quotes (e.g., `"the '->' operator"`) are handled correctly | Unit test |
| AC-04 | Multiple `->` in one message: quoted ones ignored, unquoted ones trigger pipeline | Unit test |
| AC-05 | Valid pipeline syntax (`@pm task -> @builder implement`) works unchanged | Regression test |
| AC-06 | Empty pipeline stages still produce clear error messages | Unit test |
| AC-07 | All existing parser tests pass without modification | Test suite |
| AC-08 | New test cases added for all quoted arrow edge cases | Code review |

## Out of Scope

- Escape sequences for `->` (e.g., `\->`) - not requested
- Other quote types (backticks, curly quotes) - not requested
- Multi-line quoted strings spanning pipeline operators - not requested
- Changes to pipeline execution behavior - only parsing is affected

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Regex complexity increases significantly | Medium | Low | Keep solution simple; add comprehensive tests |
| Edge cases in nested quotes | Medium | Medium | Document known limitations; test thoroughly |
| Performance impact from complex parsing | Low | Low | Benchmark if concerned; simple state machine sufficient |

## Recommended Approach

Based on requirements analysis, the solution should:

1. **Pre-process input** to identify and protect quoted regions before pipeline detection
2. **Apply pipeline pattern** only to unquoted portions of the input
3. **Preserve original text** when constructing Command objects
4. **Add comprehensive test coverage** for all quoting scenarios following TDD

---

**Document Version**: 1.0  
**Stage**: Business Problem  
**Next Stage**: SPEC (Feature Specification)
