<!-- markdownlint-disable-file -->
# Task Details: Fix Pipeline Parse Error in REPL Parser

## Research Reference

**Source Research**: .agent-tracking/research/20260303-pipeline-parse-error-research.md
**Test Strategy**: .teambot/pipeline-parse-error/artifacts/test_strategy.md

---

## Phase 1: Test Implementation (TDD - RED Phase)

### Task 1.1: Create test class for quote-aware helper functions

Add a new test class `TestQuoteAwareHelpers` to test the internal helper functions.

* **Files**:
  * `tests/test_repl/test_parser.py` - Add new test class at end of file

* **Test Functions to Create**:

```python
class TestQuoteAwareHelpers:
    """Tests for quote-aware helper functions."""

    def test_is_in_quotes_double(self):
        """Position inside double quotes detected."""
        from teambot.repl.parser import _is_in_quotes
        text = 'before "inside" after'
        assert _is_in_quotes(text, 0) is False   # 'b'
        assert _is_in_quotes(text, 8) is True    # 'i'
        assert _is_in_quotes(text, 16) is False  # 'a'

    def test_is_in_quotes_single(self):
        """Position inside single quotes detected."""
        from teambot.repl.parser import _is_in_quotes
        text = "before 'inside' after"
        assert _is_in_quotes(text, 0) is False
        assert _is_in_quotes(text, 8) is True
        assert _is_in_quotes(text, 16) is False

    def test_is_in_quotes_nested(self):
        """Inner quotes don't close outer quotes."""
        from teambot.repl.parser import _is_in_quotes
        text = '''before "outer 'inner' outer" after'''
        assert _is_in_quotes(text, 8) is True    # 'o' in outer
        assert _is_in_quotes(text, 15) is True   # 'i' - still in double quotes
        assert _is_in_quotes(text, 22) is True   # second 'o' - still in double
        assert _is_in_quotes(text, 30) is False  # 'a' in after

    def test_has_pipeline_outside_quotes_true(self):
        """Detects pipeline outside quotes."""
        from teambot.repl.parser import _has_pipeline_outside_quotes
        assert _has_pipeline_outside_quotes("@pm task -> @builder") is True

    def test_has_pipeline_outside_quotes_false(self):
        """No pipeline when arrow is quoted."""
        from teambot.repl.parser import _has_pipeline_outside_quotes
        assert _has_pipeline_outside_quotes('@pm "-> @builder" syntax') is False

    def test_split_pipeline_respects_quotes(self):
        """Split only happens outside quotes."""
        from teambot.repl.parser import _split_pipeline_quote_aware
        parts = _split_pipeline_quote_aware('@pm "-> @ba" -> @builder')
        assert len(parts) == 2
        assert parts[0] == '@pm "-> @ba"'
        assert parts[1] == '@builder'
```

* **Success**:
  * Test class added to test file
  * Tests fail with ImportError (functions don't exist yet)
* **Research References**:
  * .agent-tracking/research/20260303-pipeline-parse-error-research.md (Lines 514-554) - Test patterns
* **Dependencies**: None

### Task 1.2: Create test class for quoted pipeline handling

Add test class `TestQuotedPipelineHandling` for end-to-end quoted pipeline tests.

* **Files**:
  * `tests/test_repl/test_parser.py` - Add new test class

* **Test Functions to Create** (UT-001 through UT-008):

```python
class TestQuotedPipelineHandling:
    """Tests for pipeline detection with quoted strings."""

    def test_double_quoted_arrow_not_pipeline(self):
        """UT-002: Arrow inside double quotes is not a pipeline."""
        result = parse_command('@pm explain "-> @builder-1" syntax')
        
        assert result.is_pipeline is False
        assert result.agent_id == "pm"
        assert '"-> @builder-1"' in result.content

    def test_single_quoted_arrow_not_pipeline(self):
        """UT-001: Arrow inside single quotes is not a pipeline."""
        result = parse_command("@pm explain '-> @builder-1' syntax")
        
        assert result.is_pipeline is False
        assert result.agent_id == "pm"
        assert "'-> @builder-1'" in result.content

    def test_nested_quotes_handled(self):
        """UT-003: Inner quotes of different type don't close outer."""
        result = parse_command("@pm explain \"the '-> @notify' syntax\"")
        
        assert result.is_pipeline is False
        assert "'-> @notify'" in result.content

    def test_quoted_arrow_with_agent_mention(self):
        """UT-004: Quoted arrow with agent mention not pipeline."""
        result = parse_command("@pm explain '-> @builder' syntax")
        
        assert result.is_pipeline is False
        assert result.agent_id == "pm"

    def test_mixed_quoted_and_unquoted_arrows(self):
        """UT-005: Quoted arrows ignored, unquoted arrows split."""
        result = parse_command('@pm explain "-> @ba" then -> @builder-1 implement')
        
        assert result.is_pipeline is True
        assert len(result.pipeline) == 2
        assert '"-> @ba"' in result.pipeline[0].content
        assert result.pipeline[1].agent_ids == ["builder-1"]

    def test_multiple_quoted_arrows_no_pipeline(self):
        """UT-006: Multiple quoted arrows do not create pipeline."""
        result = parse_command('@pm compare "-> @ba" with "-> @notify"')
        
        assert result.is_pipeline is False
        assert '"-> @ba"' in result.content
        assert '"-> @notify"' in result.content

    def test_unclosed_quote_treats_rest_as_quoted(self):
        """UT-007: Unclosed quote protects remaining content."""
        result = parse_command('@pm explain "-> @builder-1 is cool')
        
        assert result.is_pipeline is False

    def test_empty_quotes_around_arrow(self):
        """UT-008: Empty quotes before arrow, unquoted arrow works."""
        result = parse_command("@pm '' -> @builder task")
        
        assert result.is_pipeline is True
        assert len(result.pipeline) == 2

    def test_quoted_content_with_real_pipeline(self):
        """Quoted content before real pipeline works."""
        result = parse_command('@pm "task description" -> @builder-1 implement')
        
        assert result.is_pipeline is True
        assert len(result.pipeline) == 2
        assert '"task description"' in result.pipeline[0].content
        assert result.pipeline[1].agent_ids == ["builder-1"]
```

* **Success**:
  * Test class added to test file
  * Tests fail (confirming the bug exists)
* **Research References**:
  * .agent-tracking/research/20260303-pipeline-parse-error-research.md (Lines 436-494) - Test cases
  * .teambot/pipeline-parse-error/artifacts/test_strategy.md (Lines 239-249) - Edge cases
* **Dependencies**: None

### Task 1.3: Create test class for default agent pipeline with quotes

Add test class `TestQuotedDefaultAgentPipeline` for `needs_default_agent_for_pipeline()`.

* **Files**:
  * `tests/test_repl/test_parser.py` - Add new test class

* **Test Functions to Create** (UT-009, UT-010):

```python
class TestQuotedDefaultAgentPipeline:
    """Tests for default agent pipeline detection with quotes."""

    def test_quoted_arrow_no_default_agent_needed(self):
        """UT-010: Quoted arrow doesn't trigger default agent prepend."""
        assert needs_default_agent_for_pipeline('explain "-> @notify" to me') is False

    def test_unquoted_arrow_needs_default_agent(self):
        """Unquoted arrow triggers default agent prepend."""
        assert needs_default_agent_for_pipeline("tell joke -> @notify") is True

    def test_mixed_quotes_only_unquoted_counts(self):
        """UT-009: Only unquoted arrows trigger default agent."""
        assert needs_default_agent_for_pipeline('explain "-> @ba" then -> @notify') is True
```

* **Success**:
  * Test class added to test file
  * Tests fail for quote scenarios
* **Research References**:
  * .agent-tracking/research/20260303-pipeline-parse-error-research.md (Lines 495-510) - Test patterns
* **Dependencies**: None

### Task 1.4: Verify all new tests fail (confirming bug exists)

Run new tests to confirm they fail and detect the bug.

* **Commands**:
```bash
# Run new test classes (expect failures)
uv run pytest tests/test_repl/test_parser.py::TestQuotedPipelineHandling -v
uv run pytest tests/test_repl/test_parser.py::TestQuotedDefaultAgentPipeline -v
```

* **Success**:
  * All quoted arrow tests fail (expected - bug not fixed yet)
  * Failure messages confirm incorrect pipeline detection
* **Research References**:
  * .teambot/pipeline-parse-error/artifacts/test_strategy.md (Lines 362-376) - TDD RED phase
* **Dependencies**: Tasks 1.1, 1.2, 1.3

---

## Phase 2: Core Implementation (TDD - GREEN Phase)

### Task 2.1: Implement `_is_in_quotes()` helper function

Add helper function to check if a position is inside quoted string.

* **Files**:
  * `src/teambot/repl/parser.py` - Add function after line 97 (after REFERENCE_PATTERN)

* **Implementation**:

```python
def _is_in_quotes(text: str, pos: int) -> bool:
    """Check if position in text is inside a quoted string.
    
    Args:
        text: The text to check.
        pos: Position to check (0-indexed).
        
    Returns:
        True if position is inside single or double quotes.
    """
    in_single = False
    in_double = False
    for i, char in enumerate(text):
        if i >= pos:
            break
        if char == '"' and not in_single:
            in_double = not in_double
        elif char == "'" and not in_double:
            in_single = not in_single
    return in_single or in_double
```

* **Success**:
  * Function added to parser.py
  * `TestQuoteAwareHelpers::test_is_in_quotes_*` tests pass
* **Research References**:
  * .agent-tracking/research/20260303-pipeline-parse-error-research.md (Lines 182-195) - Pattern 1
* **Dependencies**: Phase 1 completion

### Task 2.2: Implement `_has_pipeline_outside_quotes()` helper function

Add helper function to detect pipeline pattern outside quotes.

* **Files**:
  * `src/teambot/repl/parser.py` - Add function after `_is_in_quotes()`

* **Implementation**:

```python
def _has_pipeline_outside_quotes(text: str) -> bool:
    """Check if text contains -> @ pattern outside quoted strings.
    
    Args:
        text: The text to check.
        
    Returns:
        True if unquoted pipeline pattern found.
    """
    i = 0
    in_single = False
    in_double = False
    while i < len(text):
        char = text[i]
        if char == '"' and not in_single:
            in_double = not in_double
        elif char == "'" and not in_double:
            in_single = not in_single
        elif not (in_single or in_double):
            rest = text[i:]
            if re.match(r'\s*->\s*@', rest):
                return True
        i += 1
    return False
```

* **Success**:
  * Function added to parser.py
  * `test_has_pipeline_outside_quotes_*` tests pass
* **Research References**:
  * .agent-tracking/research/20260303-pipeline-parse-error-research.md (Lines 198-216) - Pattern 2
* **Dependencies**: Task 2.1

### Task 2.3: Implement `_split_pipeline_quote_aware()` helper function

Add helper function to split on pipeline pattern only when outside quotes.

* **Files**:
  * `src/teambot/repl/parser.py` - Add function after `_has_pipeline_outside_quotes()`

* **Implementation**:

```python
def _split_pipeline_quote_aware(text: str) -> list[str]:
    """Split text by -> @ pattern only when outside quotes.
    
    Args:
        text: Text potentially containing pipeline operators.
        
    Returns:
        List of parts split at unquoted -> @ patterns.
        The @ is preserved at the start of each subsequent part.
    """
    parts = []
    current_start = 0
    i = 0
    in_single = False
    in_double = False
    
    while i < len(text):
        char = text[i]
        if char == '"' and not in_single:
            in_double = not in_double
        elif char == "'" and not in_double:
            in_single = not in_single
        elif not (in_single or in_double):
            rest = text[i:]
            match = re.match(r'\s*->\s*(?=@)', rest)
            if match:
                parts.append(text[current_start:i])
                i += match.end()
                current_start = i
                continue
        i += 1
    
    if current_start < len(text):
        parts.append(text[current_start:])
    
    return parts
```

* **Success**:
  * Function added to parser.py
  * `test_split_pipeline_respects_quotes` test passes
* **Research References**:
  * .agent-tracking/research/20260303-pipeline-parse-error-research.md (Lines 219-248) - Pattern 3
* **Dependencies**: Task 2.1

---

## Phase 3: Parser Integration

### Task 3.1: Update `_parse_agent_command()` to use `_has_pipeline_outside_quotes()`

Replace naive regex search with quote-aware detection.

* **Files**:
  * `src/teambot/repl/parser.py` - Modify line 193

* **Change**:

```python
# Before (line 193):
if PIPELINE_PATTERN.search(input_text):
    return _parse_pipeline(input_text)

# After:
if _has_pipeline_outside_quotes(input_text):
    return _parse_pipeline(input_text)
```

* **Success**:
  * `test_double_quoted_arrow_not_pipeline` passes
  * `test_single_quoted_arrow_not_pipeline` passes
  * `test_nested_quotes_handled` passes
* **Research References**:
  * .agent-tracking/research/20260303-pipeline-parse-error-research.md (Lines 384-389) - Integration point 4
* **Dependencies**: Phase 2 completion

### Task 3.2: Update `_parse_pipeline()` to use `_split_pipeline_quote_aware()`

Replace naive regex split with quote-aware splitting.

* **Files**:
  * `src/teambot/repl/parser.py` - Modify line 274

* **Change**:

```python
# Before (line 274):
parts = re.split(r"\s*->\s*(?=@)", input_text)

# After:
parts = _split_pipeline_quote_aware(input_text)
```

* **Success**:
  * `test_mixed_quoted_and_unquoted_arrows` passes
  * `test_quoted_content_with_real_pipeline` passes
  * Stage content correctly preserves quoted strings
* **Research References**:
  * .agent-tracking/research/20260303-pipeline-parse-error-research.md (Lines 395-401) - Integration point 5
* **Dependencies**: Task 3.1

### Task 3.3: Update `needs_default_agent_for_pipeline()` to use quote-aware detection

Update function to use quote-aware pattern detection.

* **Files**:
  * `src/teambot/repl/parser.py` - Modify lines 152-164

* **Change**:

```python
# Before (line 164):
return RAW_PIPELINE_PATTERN.match(input_text) is not None

# After:
# First check basic pattern (starts without @ or /), then verify unquoted pipeline
if not RAW_PIPELINE_PATTERN.match(input_text):
    return False
return _has_pipeline_outside_quotes(input_text)
```

* **Success**:
  * `test_quoted_arrow_no_default_agent_needed` passes
  * `test_mixed_quotes_only_unquoted_counts` passes
  * Existing default agent pipeline behavior preserved
* **Research References**:
  * .agent-tracking/research/20260303-pipeline-parse-error-research.md (Lines 403-415) - Integration point 6
* **Dependencies**: Phase 2 completion

---

## Phase 4: Regression Verification

### Task 4.1: Run full parser test suite

Verify all existing parser tests still pass.

* **Commands**:
```bash
uv run pytest tests/test_repl/test_parser.py -v
```

* **Success**:
  * All 73+ existing tests pass
  * No regressions in pipeline, background, multi-agent functionality
  * All valid pipeline patterns still work
* **Research References**:
  * .teambot/pipeline-parse-error/artifacts/test_strategy.md (Lines 374-376) - Regression verification
* **Dependencies**: Phase 3 completion

### Task 4.2: Run extended parser tests

Verify extended syntax tests pass.

* **Commands**:
```bash
uv run pytest tests/test_repl/test_parser_extended.py -v
```

* **Success**:
  * All extended tests pass
  * `TestDependencyOperator` tests (lines 103-158) all pass
* **Research References**:
  * .agent-tracking/research/20260303-pipeline-parse-error-research.md (Lines 105-108) - Extended test patterns
* **Dependencies**: Task 4.1

### Task 4.3: Verify coverage meets 95% target

Run tests with coverage and verify target met.

* **Commands**:
```bash
uv run pytest tests/test_repl/test_parser.py tests/test_repl/test_parser_extended.py \
    --cov=src/teambot/repl/parser --cov-report=term-missing
```

* **Success**:
  * Coverage >= 95% for parser.py
  * New helper functions have 100% coverage
  * No uncovered critical paths
* **Research References**:
  * .teambot/pipeline-parse-error/artifacts/test_strategy.md (Lines 186-201) - Coverage targets
* **Dependencies**: Task 4.2

---

## Phase 5: Final Validation and Cleanup

### Task 5.1: Run linting and formatting

Ensure code quality standards met.

* **Commands**:
```bash
uv run ruff format -- .
uv run ruff check . --fix
uv run ruff format --check .
```

* **Success**:
  * No ruff errors
  * Code formatted correctly
  * All checks pass
* **Research References**:
  * AGENTS.md (Lines 100-102) - Clean commit standards
* **Dependencies**: Phase 4 completion

### Task 5.2: Verify all success criteria met

Final checklist verification.

* **Verification Checklist**:
  - [ ] `-> @agent` patterns inside single quotes not parsed as pipelines
  - [ ] `-> @agent` patterns inside double quotes not parsed as pipelines
  - [ ] Nested quotes handled correctly
  - [ ] Multiple `->` with some quoted, some not - handled correctly
  - [ ] Valid pipeline syntax works: `@pm task -> @builder implement`
  - [ ] All existing parser tests pass
  - [ ] New tests cover UT-001 through UT-010
  - [ ] Coverage >= 95%
  - [ ] Code passes linting

* **Success**:
  * All checklist items verified
  * Feature complete and ready for review
* **Research References**:
  * .teambot/pipeline-parse-error/artifacts/feature_spec.md - Success criteria
* **Dependencies**: Task 5.1

---

## Dependencies

* Python 3.9+
* pytest 7.4.0+
* pytest-cov
* ruff

## Success Criteria

* Quote-aware pipeline detection implemented
* All existing tests pass (backward compatibility)
* All new quote edge case tests pass
* Coverage >= 95%
* Code passes linting
