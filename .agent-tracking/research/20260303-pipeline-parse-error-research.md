<!-- markdownlint-disable-file -->
# Task Research Document: Fix Pipeline Parse Error in REPL Parser

The REPL parser incorrectly treats `-> @agent` patterns inside quoted strings as pipeline operators. When users write messages like `@pm explain the "-> @builder-1" syntax`, the parser splits on the quoted arrow and creates an invalid pipeline structure instead of treating the entire string as content for a single agent command.

## Task Implementation Requests

* Modify `PIPELINE_PATTERN` detection to be quote-aware (skip `-> @` inside single or double quotes)
* Modify `_parse_pipeline` function to use quote-aware splitting
* Update `needs_default_agent_for_pipeline` to also be quote-aware
* Add comprehensive tests for quoted arrow edge cases

## Scope and Success Criteria

* **Scope**: Parser changes in `src/teambot/repl/parser.py` only. Does not modify routing, execution, or UI logic.
* **Assumptions**:
  1. Quotes are not nested (e.g., `"outer 'inner' quote"` counts as one quoted region)
  2. Unclosed quotes should treat everything after the opening quote as quoted
  3. Both single (`'`) and double (`"`) quotes should be recognized
* **Success Criteria**:
  * `@pm explain "-> @builder-1" syntax` parses as single-agent command with full content
  * `@pm task -> @builder-1 implement` continues to parse as valid pipeline
  * `@pm "quoted" -> @builder-1 implement` parses as pipeline (arrow is outside quotes)
  * `@pm explain "-> @ba" then -> @builder-1` parses correctly with only unquoted arrow as pipeline separator
  * All existing parser tests pass
  * New tests cover quoted arrow edge cases

## Outline

1. Entry Point Analysis
2. Research Executed (Testing Infrastructure, Code Analysis)
3. Key Discoveries (Bug Analysis, Solution Approaches)
4. Technical Scenarios (Implementation Plan)
5. Testing Approach

### Potential Next Research

* None - research is complete for this focused parser fix

## Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches `_parse_pipeline`? | Implementation Required? |
|-------------|-----------|---------------------------|-------------------------|
| REPL Loop (legacy) | `loop.py:329` → `parse_command()` → `_parse_agent_command()` → `_parse_pipeline()` | YES | YES |
| REPL Loop (default agent pipeline) | `loop.py:342-345` → `needs_default_agent_for_pipeline()` → `parse_command()` | YES | YES |
| Split-pane UI | `app.py:160` → `parse_command()` → `_parse_pipeline()` | YES | YES |
| Split-pane UI (default agent) | `app.py:174-177` → `needs_default_agent_for_pipeline()` → `parse_command()` | YES | YES |
| Acceptance test executor | `acceptance_test_executor.py` → `parse_command()` | YES | YES |

### Code Path Trace

#### Entry Point 1: REPL Loop (loop.py)
1. User enters: `@pm explain "-> @builder-1" syntax`
2. Handled by: `loop.py:REPLLoop.run()` (line 329)
3. Calls: `parse_command(user_input)` from `parser.py`
4. Reaches: `_parse_agent_command()` → `PIPELINE_PATTERN.search()` → `_parse_pipeline()` ✅

#### Entry Point 2: Split-pane UI (app.py)
1. User enters: `@pm explain "-> @builder-1" syntax`
2. Handled by: `app.py:handle_input()` (line 160)
3. Calls: `parse_command(command_text)` from `parser.py`
4. Reaches: Same path as above ✅

#### Entry Point 3: Default Agent Pipeline Detection
1. User enters: `tell joke -> @notify` (raw input, default agent configured)
2. Handled by: `loop.py:342` or `app.py:174`
3. Calls: `needs_default_agent_for_pipeline(command.content)`
4. Uses: `RAW_PIPELINE_PATTERN` - also needs quote-awareness ✅

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| No quote-awareness in `PIPELINE_PATTERN.search()` | False positive pipeline detection | Add helper function |
| No quote-awareness in `re.split()` in `_parse_pipeline()` | Incorrect splitting | Replace with quote-aware split |
| No quote-awareness in `RAW_PIPELINE_PATTERN` | False positive for default agent prepend | Update detection logic |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

## Research Executed

### Testing Infrastructure Research

* **Framework**: pytest 7.4.0+
  * Location: `tests/` directory, mirrors `src/` structure
  * Naming: `test_*.py` files, `Test*` classes, `test_*` functions
  * Runner: `uv run pytest`
  * Coverage: `pytest-cov` with `--cov=src/teambot --cov-report=term-missing`

### Test Patterns Found

* **File**: `tests/test_repl/test_parser.py` (Lines 1-522)
  * Uses simple pytest assertions
  * Test classes group related tests (e.g., `TestParseAgentCommands`, `TestParseReferences`)
  * `pytest.raises` for error cases
  * No fixtures needed - parser functions are pure
  * Direct function calls with assertion checks

* **File**: `tests/test_repl/test_parser_extended.py` (Lines 1-205)
  * Tests extended syntax: background (`&`), multi-agent (`,`), pipeline (`->`)
  * `TestDependencyOperator` class covers pipeline tests (lines 103-158)
  * Pattern: parse input, assert `is_pipeline`, check `pipeline` stages

### Coverage Standards

* **Unit Tests**: 80% minimum (from pyproject.toml)
* **Parser Module**: Already well-tested, new tests should maintain coverage

### Testing Approach Recommendation

* **Quote-aware helper functions**: TDD (high complexity, clearly defined edge cases)
* **Integration with existing parser**: Code-First with immediate test validation

**Rationale**: The feature has well-defined success criteria with clear edge cases that map directly to test cases. TDD is appropriate for the helper functions, while integration changes can be validated against existing tests.

### File Analysis

* **`src/teambot/repl/parser.py`**
  * `PIPELINE_PATTERN` (Line 85): `re.compile(r"\s*->\s*@")` - simple pattern, needs context
  * `RAW_PIPELINE_PATTERN` (Line 89): `re.compile(r"^([^@/][^>]*?)\s*->\s*@")` - also needs fix
  * `_parse_agent_command()` (Lines 182-260): Calls `PIPELINE_PATTERN.search()` at line 193
  * `_parse_pipeline()` (Lines 263-346): Uses `re.split(r"\s*->\s*(?=@)", input_text)` at line 274
  * `needs_default_agent_for_pipeline()` (Lines 152-164): Uses `RAW_PIPELINE_PATTERN`

### Code Search Results

* `PIPELINE_PATTERN` usage:
  * `parser.py:85` - Definition
  * `parser.py:193` - Used in `_parse_agent_command()` to detect pipelines

* `_parse_pipeline` usage:
  * `parser.py:194` - Called from `_parse_agent_command()`
  * `parser.py:274` - Uses `re.split()` for splitting

* `needs_default_agent_for_pipeline` usage:
  * `parser.py:152-164` - Definition
  * `loop.py:342` - REPL loop default agent handling
  * `app.py:174` - Split-pane UI default agent handling

### Project Conventions

* Standards referenced: Python typing, docstrings for public functions
* Instructions followed: Minimal changes, maintain backward compatibility

## Key Discoveries

### Bug Analysis

**Problem**: The current implementation uses naive regex matching that doesn't understand string quoting context.

```python
# Current implementation (parser.py:193)
if PIPELINE_PATTERN.search(input_text):
    return _parse_pipeline(input_text)

# Current split (parser.py:274)
parts = re.split(r"\s*->\s*(?=@)", input_text)
```

**Example failure**:
```
Input: '@pm explain "-> @builder-1" syntax'
Current behavior:
  PIPELINE_PATTERN.search() returns True (matches inside quotes)
  re.split() produces: ['@pm explain "', '@builder-1" syntax']
  Result: Invalid 2-stage pipeline with broken content
  
Expected behavior:
  PIPELINE_PATTERN.search() should return False (arrow is in quotes)
  Result: Single-agent command with content 'explain "-> @builder-1" syntax'
```

### Implementation Patterns

**Pattern 1: Quote-aware position checking**
```python
def is_in_quotes(text: str, pos: int) -> bool:
    """Check if position is inside quoted string."""
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

**Pattern 2: Quote-aware pipeline detection**
```python
def has_pipeline_outside_quotes(text: str) -> bool:
    """Check if text contains -> @ pattern outside quotes."""
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

**Pattern 3: Quote-aware split**
```python
def split_pipeline_quote_aware(text: str) -> list[str]:
    """Split text by -> @ pattern only when outside quotes."""
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

### Complete Examples

**Test case validation (verified working)**:

| Input | Expected Pipeline? | Quote-aware Result | Match? |
|-------|-------------------|-------------------|--------|
| `@pm explain "-> @builder-1" syntax` | NO | NO | ✅ |
| `@pm explain '-> @builder-1' syntax` | NO | NO | ✅ |
| `@pm "pipeline: -> @notify" is cool` | NO | NO | ✅ |
| `@pm create plan -> @builder-1 implement` | YES | YES | ✅ |
| `@pm task -> @notify` | YES | YES | ✅ |
| `@pm "quoted task" -> @builder-1 implement` | YES | YES | ✅ |
| `@pm explain "-> @ba" then -> @builder-1 implement` | YES (one split) | YES (one split) | ✅ |

## Technical Scenarios

### 1. Add Quote-Aware Helper Functions

Add three new helper functions to `parser.py` that understand quoting context.

**Requirements:**
* Handle both single and double quotes
* Track quote state correctly (toggle on/off)
* Handle unclosed quotes gracefully (treat rest as quoted)
* Maintain existing function signatures where possible

**Preferred Approach:**
Create internal helper functions used by the existing parsing functions. This minimizes changes to the public API and keeps the fix localized.

```text
src/teambot/repl/parser.py
├── _is_in_quotes(text, pos) -> bool          # NEW
├── _has_pipeline_outside_quotes(text) -> bool # NEW
├── _split_pipeline_quote_aware(text) -> list  # NEW
├── parse_command()                            # No change
├── _parse_agent_command()                     # Use _has_pipeline_outside_quotes
├── _parse_pipeline()                          # Use _split_pipeline_quote_aware
└── needs_default_agent_for_pipeline()         # Use _has_pipeline_outside_quotes
```

**Implementation Details:**

1. Add `_is_in_quotes()` helper (not directly needed, but useful for testing):
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

2. Add `_has_pipeline_outside_quotes()` helper:
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

3. Add `_split_pipeline_quote_aware()` helper:
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

4. Update `_parse_agent_command()` (line 193):
```python
# Before:
if PIPELINE_PATTERN.search(input_text):
    return _parse_pipeline(input_text)

# After:
if _has_pipeline_outside_quotes(input_text):
    return _parse_pipeline(input_text)
```

5. Update `_parse_pipeline()` (line 274):
```python
# Before:
parts = re.split(r"\s*->\s*(?=@)", input_text)

# After:
parts = _split_pipeline_quote_aware(input_text)
```

6. Update `needs_default_agent_for_pipeline()` (line 164):
```python
# Before:
return RAW_PIPELINE_PATTERN.match(input_text) is not None

# After:
# First check the basic pattern, then verify it's not in quotes
if not RAW_PIPELINE_PATTERN.match(input_text):
    return False
# Find where the -> @ would be and check if it's quoted
return _has_pipeline_outside_quotes(input_text)
```

#### Considered Alternatives (Removed After Selection)

**Alternative 1: Regex-only solution with negative lookahead/behind**
- **Rejected because**: Python regex doesn't support variable-width lookbehind, and matching balanced quotes with regex is extremely complex and error-prone.

**Alternative 2: Preprocess input to escape quoted sections**
- **Rejected because**: Would require unescaping after parsing, adding complexity and potential for bugs in content reconstruction.

**Alternative 3: Full lexer/tokenizer**
- **Rejected because**: Over-engineered for this specific fix. The state-machine approach is sufficient and keeps changes minimal.

## Testing Approach

### New Test Cases Required

Add to `tests/test_repl/test_parser.py`:

```python
class TestQuotedPipelineHandling:
    """Tests for pipeline detection with quoted strings."""

    def test_double_quoted_arrow_not_pipeline(self):
        """Arrow inside double quotes is not a pipeline."""
        result = parse_command('@pm explain "-> @builder-1" syntax')
        
        assert result.is_pipeline is False
        assert result.agent_id == "pm"
        assert '"-> @builder-1"' in result.content

    def test_single_quoted_arrow_not_pipeline(self):
        """Arrow inside single quotes is not a pipeline."""
        result = parse_command("@pm explain '-> @builder-1' syntax")
        
        assert result.is_pipeline is False
        assert result.agent_id == "pm"
        assert "'-> @builder-1'" in result.content

    def test_quoted_content_with_real_pipeline(self):
        """Quoted content before real pipeline works."""
        result = parse_command('@pm "task description" -> @builder-1 implement')
        
        assert result.is_pipeline is True
        assert len(result.pipeline) == 2
        assert result.pipeline[0].content == '"task description"'
        assert result.pipeline[1].agent_ids == ["builder-1"]

    def test_mixed_quoted_and_unquoted_arrows(self):
        """Quoted arrows ignored, unquoted arrows split."""
        result = parse_command('@pm explain "-> @ba" then -> @builder-1 implement')
        
        assert result.is_pipeline is True
        assert len(result.pipeline) == 2
        assert '"-> @ba"' in result.pipeline[0].content
        assert result.pipeline[1].agent_ids == ["builder-1"]

    def test_multiple_quoted_arrows_no_pipeline(self):
        """Multiple quoted arrows do not create pipeline."""
        result = parse_command('@pm compare "-> @ba" with "-> @notify"')
        
        assert result.is_pipeline is False
        assert '"-> @ba"' in result.content
        assert '"-> @notify"' in result.content

    def test_unclosed_quote_treats_rest_as_quoted(self):
        """Unclosed quote protects remaining content."""
        result = parse_command('@pm explain "-> @builder-1 is cool')
        
        assert result.is_pipeline is False
        # The content should include the unclosed quote and everything after

    def test_nested_quotes_handled(self):
        """Inner quotes of different type don't close outer."""
        result = parse_command("@pm explain \"the '-> @notify' syntax\"")
        
        assert result.is_pipeline is False
        assert "'-> @notify'" in result.content


class TestQuotedDefaultAgentPipeline:
    """Tests for default agent pipeline detection with quotes."""

    def test_quoted_arrow_no_default_agent_needed(self):
        """Quoted arrow doesn't trigger default agent prepend."""
        # This raw input has arrow in quotes, not a real pipeline
        assert needs_default_agent_for_pipeline('explain "-> @notify" to me') is False

    def test_unquoted_arrow_needs_default_agent(self):
        """Unquoted arrow triggers default agent prepend."""
        assert needs_default_agent_for_pipeline("tell joke -> @notify") is True

    def test_mixed_quotes_only_unquoted_counts(self):
        """Only unquoted arrows trigger default agent."""
        assert needs_default_agent_for_pipeline('explain "-> @ba" then -> @notify') is True
```

### Test Helper Functions

```python
class TestQuoteAwareHelpers:
    """Tests for quote-aware helper functions."""

    def test_is_in_quotes_double(self):
        """Position inside double quotes detected."""
        text = 'before "inside" after'
        assert _is_in_quotes(text, 0) is False  # 'b'
        assert _is_in_quotes(text, 8) is True   # 'i'
        assert _is_in_quotes(text, 16) is False # 'a'

    def test_is_in_quotes_single(self):
        """Position inside single quotes detected."""
        text = "before 'inside' after"
        assert _is_in_quotes(text, 0) is False
        assert _is_in_quotes(text, 8) is True
        assert _is_in_quotes(text, 16) is False

    def test_is_in_quotes_nested(self):
        """Inner quotes don't close outer quotes."""
        text = '''before "outer 'inner' outer" after'''
        assert _is_in_quotes(text, 8) is True   # 'o' in outer
        assert _is_in_quotes(text, 15) is True  # 'i' - still in double quotes
        assert _is_in_quotes(text, 22) is True  # second 'o' - still in double
        assert _is_in_quotes(text, 30) is False # 'a' in after

    def test_has_pipeline_outside_quotes_true(self):
        """Detects pipeline outside quotes."""
        assert _has_pipeline_outside_quotes("@pm task -> @builder") is True

    def test_has_pipeline_outside_quotes_false(self):
        """No pipeline when arrow is quoted."""
        assert _has_pipeline_outside_quotes('@pm "-> @builder" syntax') is False

    def test_split_pipeline_respects_quotes(self):
        """Split only happens outside quotes."""
        parts = _split_pipeline_quote_aware('@pm "-> @ba" -> @builder')
        assert len(parts) == 2
        assert parts[0] == '@pm "-> @ba"'
        assert parts[1] == '@builder'
```

### Running Tests

```bash
# Run all parser tests
uv run pytest tests/test_repl/test_parser.py -v

# Run with coverage
uv run pytest tests/test_repl/test_parser.py --cov=src/teambot/repl/parser --cov-report=term-missing

# Run specific new tests
uv run pytest tests/test_repl/test_parser.py::TestQuotedPipelineHandling -v
```
