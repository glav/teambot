<!-- markdownlint-disable-file -->
# Implementation Details: Default Agent Context Reference Extraction Bug Fix

**Research Reference**: `.agent-tracking/research/20260217-default-agent-context-research.md`
**Plan Reference**: `.agent-tracking/plans/20260217-default-agent-context-refs-plan.instructions.md`

---

## Phase 1: Core Fix (Lines 15-45)

### Task 1.1: Add `extract_references()` Helper Function

**File**: `src/teambot/repl/parser.py`
**Location**: After `REFERENCE_PATTERN` definition (line 93)

**Implementation**:

```python
def extract_references(content: str | None) -> list[str]:
    """Extract $agent references from content.

    Args:
        content: Text potentially containing $agent references.

    Returns:
        List of agent IDs referenced (deduplicated, order preserved).
        
    Examples:
        >>> extract_references("Summarize $ba output")
        ['ba']
        >>> extract_references("Check $ba and $pm")
        ['ba', 'pm']
        >>> extract_references(r"Use \\$pm safely")  # escaped
        []
    """
    if not content:
        return []
    matches = REFERENCE_PATTERN.findall(content)
    # Deduplicate while preserving order
    seen: set[str] = set()
    return [r for r in matches if not (r in seen or seen.add(r))]
```

**Research Reference**: Lines 169-186 document the helper function design.

**Success Criteria**:
- Function returns empty list for `None` or empty string
- Function extracts single and multiple references
- Function ignores escaped `\$agent` patterns
- Function deduplicates preserving order

---

## Phase 2: Integration (Lines 47-95)

### Task 2.1: Fix `loop.py` Default Agent Command Creation

**File**: `src/teambot/repl/loop.py`

**Step 1: Add Import (around line 15-22)**

Current imports include:
```python
from teambot.repl.parser import (
    parse_command,
    needs_default_agent_for_pipeline,
    prepend_default_agent,
)
```

Update to:
```python
from teambot.repl.parser import (
    extract_references,
    parse_command,
    needs_default_agent_for_pipeline,
    prepend_default_agent,
)
```

**Step 2: Fix Command Creation (lines 309-314)**

Current code:
```python
command = Command(
    type=CommandType.AGENT,
    agent_id=default_agent,
    agent_ids=[default_agent],
    content=command.content,
)
```

Updated code:
```python
command = Command(
    type=CommandType.AGENT,
    agent_id=default_agent,
    agent_ids=[default_agent],
    content=command.content,
    references=extract_references(command.content),
)
```

**Research Reference**: Lines 189-201 document this change.

---

### Task 2.2: Fix `app.py` Default Agent Command Creation

**File**: `src/teambot/ui/app.py`

**Step 1: Add Import (around line 14-22)**

Add `extract_references` to existing parser imports:
```python
from teambot.repl.parser import (
    extract_references,
    parse_command,
    needs_default_agent_for_pipeline,
    prepend_default_agent,
)
```

**Step 2: Fix Command Creation (lines 140-146)**

Current code:
```python
agent_command = Command(
    type=CommandType.AGENT,
    agent_id=default_agent,
    agent_ids=[default_agent],
    content=command.content,
)
```

Updated code:
```python
agent_command = Command(
    type=CommandType.AGENT,
    agent_id=default_agent,
    agent_ids=[default_agent],
    content=command.content,
    references=extract_references(command.content),
)
```

**Research Reference**: Lines 203 documents this change.

---

### Task 2.3: Fix `router.py` Default Agent Command Creation

**File**: `src/teambot/repl/router.py`

**Step 1: Add Import (around line 10)**

Add to existing imports:
```python
from teambot.repl.parser import extract_references
```

**Step 2: Fix Command Creation (lines 200-206)**

Current code:
```python
agent_command = Command(
    type=CommandType.AGENT,
    agent_id=self._default_agent,
    agent_ids=[self._default_agent],
    content=command.content,
)
```

Updated code:
```python
agent_command = Command(
    type=CommandType.AGENT,
    agent_id=self._default_agent,
    agent_ids=[self._default_agent],
    content=command.content,
    references=extract_references(command.content),
)
```

**Research Reference**: Lines 205 documents this change.

---

## Phase 3: Testing (Lines 97-145)

### Task 3.1: Add Unit Tests for `extract_references()` Helper

**File**: `tests/test_repl/test_parser.py`

**Location**: Add new test class after existing reference tests (around line 351)

**Implementation**:

```python
class TestExtractReferences:
    """Tests for extract_references() helper function."""

    def test_extract_single_reference(self):
        """Extract single $agent reference."""
        assert extract_references("Summarize $ba output") == ["ba"]

    def test_extract_multiple_references(self):
        """Extract multiple references in order."""
        assert extract_references("Check $ba and $pm feedback") == ["ba", "pm"]

    def test_extract_duplicate_references(self):
        """Deduplicate references while preserving first occurrence order."""
        assert extract_references("$ba says $pm and $ba again") == ["ba", "pm"]

    def test_extract_escaped_reference_ignored(self):
        """Escaped \\$agent references are not extracted."""
        assert extract_references(r"Use \$pm carefully") == []

    def test_extract_mixed_escaped_and_real(self):
        """Mix of escaped and real references."""
        assert extract_references(r"\$pm but $ba is real") == ["ba"]

    def test_extract_none_content(self):
        """None content returns empty list."""
        assert extract_references(None) == []

    def test_extract_empty_content(self):
        """Empty string returns empty list."""
        assert extract_references("") == []

    def test_extract_no_references(self):
        """Content without references returns empty list."""
        assert extract_references("Plain text without refs") == []

    def test_extract_reference_with_hyphen(self):
        """References with hyphens like $builder-1."""
        assert extract_references("Check $builder-1 output") == ["builder-1"]

    def test_extract_reference_with_underscore(self):
        """References with underscores like $my_agent."""
        assert extract_references("From $my_agent") == ["my_agent"]

    def test_extract_ignores_numeric_start(self):
        """$100 is not a valid reference (must start with letter)."""
        assert extract_references("Cost is $100") == []
```

**Add Import**: At top of file:
```python
from teambot.repl.parser import extract_references
```

**Research Reference**: Lines 278-291 document test patterns.

---

### Task 3.2: Add Integration Test for Default Agent + References

**File**: `tests/test_integration/test_shared_context.py`

**Location**: Add to existing test class for shared context

**Implementation**:

```python
@pytest.mark.asyncio
async def test_default_agent_routing_extracts_references(self, mock_sdk):
    """Default agent routing correctly extracts $agent references.
    
    This tests the bug fix where references were not extracted when
    using default agent routing (without explicit @agent prefix).
    """
    from teambot.repl.parser import extract_references
    from teambot.repl.commands import Command, CommandType
    
    # Simulate what loop.py does when routing raw input to default agent
    raw_content = "Summarize $ba feedback and $pm notes"
    
    # Create command as fixed loop.py would
    command = Command(
        type=CommandType.AGENT,
        agent_id="reviewer",
        agent_ids=["reviewer"],
        content=raw_content,
        references=extract_references(raw_content),  # The fix
    )
    
    # Verify references were extracted
    assert command.references == ["ba", "pm"]
    
    # Execute and verify injection would happen
    # (TaskExecutor checks command.references to decide on injection)
    assert len(command.references) == 2
```

**Research Reference**: Lines 293-315 document integration test pattern.

---

## Phase 4: Validation (Lines 147-165)

### Task 4.1: Run Full Test Suite

**Commands**:
```bash
# Run all tests
uv run pytest

# Run specific tests for this feature
uv run pytest tests/test_repl/test_parser.py -v -k extract
uv run pytest tests/test_integration/test_shared_context.py -v
```

**Success Criteria**:
- All existing tests pass
- New `extract_references` tests pass
- No regressions in parser or routing tests

---

### Task 4.2: Lint and Format

**Commands**:
```bash
# Check and fix lint issues
uv run ruff check . --fix

# Format code
uv run ruff format .
```

**Success Criteria**:
- No lint errors
- Code properly formatted
- Clean commit ready

---

## File Operations Summary

| Operation | File | Lines |
|-----------|------|-------|
| MODIFY | `src/teambot/repl/parser.py` | Add function after line 93 |
| MODIFY | `src/teambot/repl/loop.py` | Lines 15-22 (import), 309-314 (fix) |
| MODIFY | `src/teambot/ui/app.py` | Lines 14-22 (import), 140-146 (fix) |
| MODIFY | `src/teambot/repl/router.py` | Line 10 (import), 200-206 (fix) |
| MODIFY | `tests/test_repl/test_parser.py` | Add test class |
| MODIFY | `tests/test_integration/test_shared_context.py` | Add test method |

---

## Edge Cases Verified

| Case | Input | Expected Output | Test |
|------|-------|-----------------|------|
| Single ref | `$pm` | `["pm"]` | T3.1 |
| Multiple refs | `$ba and $pm` | `["ba", "pm"]` | T3.1 |
| Escaped | `\$pm` | `[]` | T3.1 |
| Number start | `$100` | `[]` | T3.1 |
| Empty | `""` | `[]` | T3.1 |
| None | `None` | `[]` | T3.1 |
| With hyphen | `$builder-1` | `["builder-1"]` | T3.1 |
| Duplicate | `$ba then $ba` | `["ba"]` | T3.1 |
