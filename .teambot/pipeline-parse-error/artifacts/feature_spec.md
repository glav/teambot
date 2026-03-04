<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Pipeline Parse Error Fix - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target v0.2.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-03-03 |
| Problem & Users | ✅ | None | 2026-03-03 |
| Scope | ✅ | None | 2026-03-03 |
| Requirements | ✅ | None | 2026-03-03 |
| Metrics & Risks | ✅ | None | 2026-03-03 |
| Operationalization | ✅ | None | 2026-03-03 |
| Finalization | ✅ | None | 2026-03-03 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot's REPL parser supports pipeline syntax (`@agent1 task -> @agent2 task`) to chain agent commands. The parser uses regex pattern matching to detect the `->` operator followed by `@agent`. This works correctly for actual pipelines but fails when users casually mention `->` within quoted strings in their messages.

### Core Opportunity
Enable users to discuss, document, and explain the pipeline syntax itself within agent commands without triggering false pipeline parsing—improving usability while maintaining full backward compatibility.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Eliminate false positive pipeline detection for quoted arrows | Functional | Fails on quoted arrows | Zero false positives | v0.2.0 | P0 |
| G-002 | Maintain 100% backward compatibility with valid pipeline syntax | Functional | Working | No regressions | v0.2.0 | P0 |
| G-003 | Achieve comprehensive test coverage for quoting edge cases | Quality | Partial | 100% edge cases tested | v0.2.0 | P1 |

## 2. Problem Definition

### Current Situation
The REPL parser uses `PIPELINE_PATTERN = re.compile(r"\s*->\s*@")` to detect pipeline syntax. This pattern performs a simple substring match without considering whether the `->` characters appear inside quoted strings.

### Problem Statement
Users cannot discuss, explain, or document the pipeline syntax itself using natural language within agent commands. When users include `'->'` or `"->"` in their messages (even within quotes), the parser incorrectly interprets these as pipeline operators, causing parse errors or unexpected behavior.

### Root Causes
* The pipeline detection regex does not account for quoted string boundaries
* No pre-processing step exists to identify and protect quoted regions
* The parser treats all `-> @` sequences identically regardless of context

### Impact of Inaction
* Users receive confusing parse errors when discussing pipeline syntax
* Documentation and explanation workflows are broken
* User trust in the REPL decreases due to unexpected behavior
* Support burden increases due to unclear error messages

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| Developer User | Discuss pipeline syntax with agents, get help understanding `->` operator | Cannot mention `->` in quotes without parse errors | High - blocks learning/documentation workflows |
| Technical Writer | Document TeamBot features including pipeline syntax | Writing about `->` triggers errors | Medium - workarounds exist but are frustrating |
| Power User | Chain complex pipelines with explanatory text | Mixed quoted/unquoted arrows cause undefined behavior | High - unpredictable results |

## 4. Scope

### In Scope
* Modify pipeline detection to skip `->` patterns inside single-quoted strings (`'...'`)
* Modify pipeline detection to skip `->` patterns inside double-quoted strings (`"..."`)
* Handle nested quotes (e.g., `"the '->' operator"`)
* Handle multiple `->` in one message where some are quoted and some are not
* Add comprehensive test coverage following TDD approach
* Maintain all existing parser functionality

### Out of Scope (justify if empty)
* Escape sequences for `->` (e.g., `\->`) - Not requested in requirements
* Other quote types (backticks, curly quotes) - Not standard in this context
* Multi-line quoted strings spanning pipeline operators - Edge case not requested
* Changes to pipeline execution behavior - Only parsing is affected
* Performance optimization - Current scale does not require it

### Assumptions
* Single and double quotes are the only quoting mechanisms users expect
* Balanced quotes are required (unclosed quotes are user errors)
* The parser should be forgiving: unclosed quotes result in treating `->` as literal text, not as pipeline

### Constraints
* Must maintain backward compatibility with all existing valid pipeline syntax
* All existing parser tests must continue to pass without modification
* Parser error messages for genuinely malformed pipelines must remain helpful
* Solution must be implemented in Python, consistent with existing codebase

## 5. Product Overview

### Value Proposition
Users can freely discuss, document, and explain pipeline syntax within their agent commands without encountering unexpected parse errors, while all valid pipeline functionality continues to work exactly as before.

### Technical Approach
The solution should pre-process input to identify quoted regions before applying pipeline detection. Only `-> @agent` patterns outside quoted regions should trigger pipeline parsing.

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|-------------|-------|----------|----------|------------|-------|
| FR-001 | Single-quoted arrow ignored | `'->'` or `'-> @agent'` inside single quotes must NOT trigger pipeline parsing | G-001 | All | P0 | Input `@pm explain '->'` parses as single agent command with content | Core requirement |
| FR-002 | Double-quoted arrow ignored | `"->"` or `"-> @agent"` inside double quotes must NOT trigger pipeline parsing | G-001 | All | P0 | Input `@pm explain "->"` parses as single agent command with content | Core requirement |
| FR-003 | Nested quotes handled | Nested quote patterns like `"the '->' operator"` must be handled correctly | G-001 | All | P1 | Inner quotes don't affect outer quote boundary detection | Edge case |
| FR-004 | Mixed quoted/unquoted | When message contains both quoted and unquoted `->`, only unquoted triggers pipeline | G-001, G-002 | Power User | P1 | `@pm explain "->" -> @builder implement` parses as 2-stage pipeline | Complex scenario |
| FR-005 | Valid pipelines unchanged | Standard pipeline syntax `@agent1 task -> @agent2 task` continues to work exactly as before | G-002 | All | P0 | All existing pipeline tests pass | Backward compat |
| FR-006 | Unquoted arrows still work | `@pm task -> @builder implement` without quotes parses as pipeline | G-002 | All | P0 | Existing behavior preserved | Backward compat |
| FR-007 | Error messages preserved | Genuinely malformed pipelines produce helpful error messages | G-002 | All | P1 | Empty stage errors, unknown agent errors remain clear | UX requirement |
| FR-008 | Raw pipeline detection | `needs_default_agent_for_pipeline()` respects quoted regions | G-001, G-002 | All | P1 | `"explain ->" -> @notify` correctly identified, `"explain '->' syntax"` not | Helper function |

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Performance | Parser latency must not increase significantly | < 10% increase for typical inputs | P2 | Benchmark comparison | Simple state machine should have negligible overhead |
| NFR-002 | Maintainability | Solution code must be clear and well-documented | Code review approval | P1 | Peer review | Comments explaining quote-handling logic |
| NFR-003 | Reliability | All existing tests must pass | 100% pass rate | P0 | CI pipeline | No regressions |
| NFR-004 | Testability | All edge cases must have dedicated test cases | 100% requirement coverage | P0 | Test audit | TDD approach required |

## 8. Test Strategy

### Testing Approach
**TDD (Test-Driven Development)** - Add failing tests first, then implement the fix.

### Test Categories

#### Unit Tests (New)
| Test ID | Description | Input | Expected Output |
|---------|-------------|-------|-----------------|
| UT-001 | Single-quoted arrow not pipeline | `@pm explain the '->' operator` | `is_pipeline=False`, content contains `'->'` |
| UT-002 | Double-quoted arrow not pipeline | `@pm the "->" chains agents` | `is_pipeline=False`, content contains `"->"` |
| UT-003 | Nested quotes handled | `@pm describe the '"->"' syntax` | `is_pipeline=False`, content preserved |
| UT-004 | Quoted arrow with @agent not pipeline | `@pm explain '-> @builder' syntax` | `is_pipeline=False` |
| UT-005 | Mixed: quoted ignored, unquoted triggers | `@pm explain "->" -> @builder do it` | `is_pipeline=True`, 2 stages |
| UT-006 | Multiple quoted arrows | `@pm '->'->'->'->'` | `is_pipeline=False` |
| UT-007 | Unclosed quote treats as literal | `@pm explain '-> @builder` | `is_pipeline=False` (forgiving) |
| UT-008 | Empty quotes around arrow | `@pm '' -> @builder task` | `is_pipeline=True` (arrow outside quotes) |
| UT-009 | Raw pipeline with quoted content | `explain "->" -> @notify` | `needs_default_agent_for_pipeline=True` |
| UT-010 | Raw input all quoted | `explain the '->' operator` | `needs_default_agent_for_pipeline=False` |

#### Regression Tests (Existing)
All tests in `tests/test_repl/test_parser.py` and `tests/test_repl/test_parser_extended.py` must continue to pass.

## 9. Acceptance Test Scenarios

### AT-001: Discussing Pipeline Syntax
**Description**: User asks an agent to explain the pipeline operator
**Preconditions**: REPL is running, default agent configured
**Steps**:
1. User enters: `@pm explain how the '->' operator works in TeamBot`
2. Parser processes the input
3. Command is routed to PM agent
**Expected Result**: Command parsed as single agent command, PM receives full content including `'->'`
**Verification**: `result.is_pipeline == False` and `'->'` appears in `result.content`

### AT-002: Mixed Quoted and Unquoted Pipeline
**Description**: User explains syntax and then actually uses a pipeline
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@pm document the "->" syntax -> @writer format it nicely`
2. Parser processes the input
3. Command is routed as pipeline
**Expected Result**: Parsed as 2-stage pipeline; first stage content includes `"->"`, second stage goes to writer
**Verification**: `result.is_pipeline == True`, `len(result.pipeline) == 2`, `'"->"' in result.pipeline[0].content`

### AT-003: Valid Pipeline Still Works
**Description**: Standard pipeline usage continues to work
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@pm create a plan -> @builder-1 implement it -> @reviewer check it`
2. Parser processes the input
**Expected Result**: Parsed as 3-stage pipeline
**Verification**: `result.is_pipeline == True`, `len(result.pipeline) == 3`, agents are `['pm', 'builder-1', 'reviewer']`

### AT-004: Nested Quotes Edge Case
**Description**: User uses nested quotes around arrow
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@pm the syntax is "use '->' between agents"`
2. Parser processes the input
**Expected Result**: Parsed as single command, no pipeline
**Verification**: `result.is_pipeline == False`, full quoted string preserved in content

### AT-005: Error Message Quality Preserved
**Description**: Malformed pipeline still produces helpful error
**Preconditions**: REPL is running
**Steps**:
1. User enters: `@pm task -> @invalid-agent-xyz do something`
2. Parser processes the input
**Expected Result**: ParseError raised with helpful message about unknown agent
**Verification**: Exception message includes "Unknown agent" and lists valid agents

## 10. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| parser.py | Source Code | Critical | TeamBot | Low | Well-understood module |
| PIPELINE_PATTERN regex | Internal | Critical | TeamBot | Medium | May need replacement or wrapper |
| RAW_PIPELINE_PATTERN regex | Internal | Critical | TeamBot | Medium | May need replacement or wrapper |
| pytest | Test Framework | Required | External | Low | Stable dependency |
| Existing test suite | Tests | Critical | TeamBot | Low | Must all pass |

## 11. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Regex complexity increases significantly | Low | Medium | Use simple character-by-character scan instead of complex regex | Builder | Open |
| R-002 | Edge cases in nested quotes cause incorrect parsing | Medium | Medium | Document limitations; comprehensive test suite | Builder | Open |
| R-003 | Performance degradation on long inputs | Low | Low | Benchmark; optimize only if needed | Builder | Open |
| R-004 | Breaking changes to existing behavior | High | Low | TDD approach; run full test suite continuously | Builder | Open |
| R-005 | Unclosed quotes handling ambiguity | Low | Medium | Define clear behavior: treat as literal text | Builder | Open |

## 12. Privacy, Security & Compliance

### Data Classification
Not applicable - this feature affects parsing logic only, no data storage or transmission.

### PII Handling
Not applicable - parser processes transient command text only.

### Threat Considerations
Not applicable - no security-sensitive changes.

## 13. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard release process | No special deployment needs |
| Rollback | Standard rollback | Previous version can be restored |
| Monitoring | Existing error logging | Parser errors already logged |
| Alerting | N/A | No new alerts needed |
| Support | Documentation update | Help text may reference quoting |
| Capacity Planning | N/A | No capacity impact |

## 14. Rollout & Launch Plan

### Phases / Milestones
| Phase | Gate Criteria | Owner |
|-------|---------------|-------|
| 1. Test Creation | All failing tests written per TDD | Builder |
| 2. Implementation | All tests passing | Builder |
| 3. Code Review | PR approved | Reviewer |
| 4. Merge & Release | CI passes, merged to main | Team |

## 15. Open Questions

| Q ID | Question | Owner | Status |
|------|----------|-------|--------|
| - | None - all requirements clear | - | - |

## 16. Implementation Guidance

### Recommended Approach
1. **Create helper function** `find_unquoted_pipeline_operator(text: str) -> int | None`
   - Scans text character-by-character
   - Tracks quote state (in single quote, in double quote, or unquoted)
   - Returns index of first unquoted `-> @` pattern, or None if not found

2. **Modify `_parse_agent_command`**
   - Replace `PIPELINE_PATTERN.search(input_text)` with call to helper function
   - If helper returns None, treat as non-pipeline command

3. **Modify `_parse_pipeline`**
   - Update splitting logic to only split on unquoted `-> @` sequences
   - Preserve quoted content intact in stage content

4. **Modify `needs_default_agent_for_pipeline`**
   - Apply same quote-aware logic

### Quote State Machine
```
State: NORMAL | IN_SINGLE | IN_DOUBLE

NORMAL + ' → IN_SINGLE
NORMAL + " → IN_DOUBLE
IN_SINGLE + ' → NORMAL
IN_DOUBLE + " → NORMAL
NORMAL + -> @ → PIPELINE DETECTED
IN_SINGLE + -> @ → IGNORED
IN_DOUBLE + -> @ → IGNORED
```

### File Locations
- **Source**: `src/teambot/repl/parser.py`
- **Tests**: `tests/test_repl/test_parser.py` (add new test class)

## 17. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-03-03 | BA Agent | Initial specification | Creation |

## 18. References & Provenance

| Ref ID | Type | Source | Summary |
|--------|------|--------|---------|
| REF-001 | Source Code | src/teambot/repl/parser.py | Current parser implementation |
| REF-002 | Tests | tests/test_repl/test_parser.py | Existing parser tests |
| REF-003 | Tests | tests/test_repl/test_parser_extended.py | Extended parser tests |
| REF-004 | Problem Statement | .teambot/pipeline-parse-error/artifacts/problem_statement.md | Business problem definition |

---

## VALIDATION_STATUS: PASS
- Placeholders: 0 remaining
- Sections Complete: 18/18
- Technical Stack: DEFINED (Python)
- Testing Approach: DEFINED (TDD)
- Acceptance Tests: 5 scenarios defined

---

Generated 2026-03-03 by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
