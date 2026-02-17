<!-- markdownlint-disable-file -->
# Research: Default Agent Context Reference Extraction Bug

**Date:** 2026-02-17  
**Feature:** Default Agent + `$agent` Context Reference Extraction  
**Status:** ✅ Complete  

---

## 📋 Research Scope

### Problem Statement

When a user types `Incorporate the feedback from $reviewer` without specifying an `@agent` prefix, and a default agent (e.g., `pm`) is configured, the `$reviewer` context reference is **NOT** correctly extracted. The `references` field in the `Command` object remains empty, so the `TaskExecutor` never injects the referenced agent's output.

**Works:** `@pm Incorporate the feedback from $reviewer` → references = `["reviewer"]`  
**Fails:** `Incorporate the feedback from $reviewer` (with default agent) → references = `[]`

### Success Criteria

- [ ] `$reviewer` extracted when using default agent routing
- [ ] Multiple references (`$reviewer and $ba`) extracted correctly
- [ ] Escaped references (`\$reviewer`) still ignored
- [ ] Pipeline inputs (`tell joke -> @notify`) continue working
- [ ] Both `repl/loop.py` and `ui/app.py` fixed consistently
- [ ] `repl/router.py` also fixed for completeness
- [ ] All existing tests pass; new tests cover this scenario

---

## 🔍 Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Extracts References? | Fix Required? |
|-------------|-----------|---------------------|---------------|
| `@pm task $ba` (explicit) | `parse_command()` → `_parse_agent_command()` | ✅ YES | ❌ NO |
| `task $ba` (default agent, REPL) | `loop.py:309-314` → manually creates `Command` | ❌ **NO** | ✅ **YES** |
| `task $ba` (default agent, UI) | `app.py:140-146` → manually creates `Command` | ❌ **NO** | ✅ **YES** |
| `task $ba` (router raw) | `router.py:200-207` → manually creates `Command` | ❌ **NO** | ✅ **YES** |
| `task -> @notify` (pipeline) | `loop.py:304-307` uses `prepend_default_agent` + `parse_command` | ✅ YES | ❌ NO |

### Code Path Trace

#### Entry Point 1: Explicit `@pm Summarize $ba`

1. User enters: `@pm Summarize $ba`
2. Handled by: `parse_command()` (parser.py:99-126)
3. Routes to: `_parse_agent_command()` (parser.py:159-237)
4. **Extracts references:** Lines 219-225 use `REFERENCE_PATTERN.findall(content)`
5. Returns: `Command(references=["ba"])`
6. Reaches: `TaskExecutor.execute()` → `_execute_simple()` → `_inject_references()`
7. ✅ **Works correctly**

#### Entry Point 2: Raw `Summarize $ba` with default agent (loop.py)

1. User enters: `Summarize $ba`
2. Handled by: `REPLLoop.run()` (loop.py:274-340)
3. Parsed as: `Command(type=RAW, content="Summarize $ba")`
4. At lines 300-314: Converts to AGENT command **manually**:
   ```python
   command = Command(
       type=CommandType.AGENT,
       agent_id=default_agent,
       agent_ids=[default_agent],
       content=command.content,
       # ❌ references NOT populated!
   )
   ```
5. Routes to: `_handle_advanced_command()` or `_router.route()`
6. ❌ **BUG**: `command.references` is empty list (default)

#### Entry Point 3: Raw `Summarize $ba` with default agent (app.py)

1. User enters: `Summarize $ba` in Textual UI
2. Handled by: `TeamBotApp.handle_input()` (app.py:107-154)
3. At lines 140-146: Same manual `Command` creation:
   ```python
   agent_command = Command(
       type=CommandType.AGENT,
       agent_id=default_agent,
       agent_ids=[default_agent],
       content=command.content,
       # ❌ references NOT populated!
   )
   ```
4. ❌ **BUG**: Same issue as loop.py

#### Entry Point 4: Raw routing via AgentRouter

1. User enters: `Summarize $ba` 
2. Handled by: `AgentRouter.route()` → `_route_raw()` (router.py:184-213)
3. At lines 200-206: Same manual `Command` creation without references
4. Routes to: `_route_agent()` → agent handler (simple execution path)
5. ❌ **BUG**: References not extracted (though this path goes through simpler handler)

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| `loop.py:309-314` | Default agent commands don't inject `$ref` outputs | Add reference extraction |
| `app.py:140-146` | Same issue in Textual UI | Add reference extraction |
| `router.py:200-206` | Same issue in router (less critical since router uses simple path) | Add reference extraction for consistency |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## 🛠️ Technical Analysis

### Root Cause

The `REFERENCE_PATTERN` regex and extraction logic exist only inside:
1. `_parse_agent_command()` (lines 219-225)
2. `_parse_pipeline()` (lines 303-312)

When raw input is converted to an agent command **manually** (without going through the parser), the reference extraction is skipped.

### Existing Reference Extraction Logic

**Location:** `src/teambot/repl/parser.py`, lines 219-225

```python
# Detect $agent references in content
references = []
if content:
    matches = REFERENCE_PATTERN.findall(content)
    # Deduplicate while preserving order
    seen = set()
    references = [r for r in matches if not (r in seen or seen.add(r))]
```

**Pattern:** `REFERENCE_PATTERN = re.compile(r"(?<!\\)\$([a-zA-Z][a-zA-Z0-9_-]*)")`

- Matches `$pm`, `$builder-1`, `$ba`
- Ignores escaped `\$pm` (negative lookbehind)
- Ignores `$100` (must start with letter)

### Executor Reference Handling

**Location:** `src/teambot/tasks/executor.py`, lines 316-335

```python
if command.references:
    # Validate all referenced agents exist
    invalid_refs = [ref for ref in command.references if ...]
    if invalid_refs:
        return ExecutionResult(success=False, error=...)
    
    # Wait for any referenced agents that are currently running
    await self._wait_for_references(command.references)
    
    # Build prompt with injected outputs
    prompt = self._inject_references(command.content, command.references)
```

**Key Insight:** The executor relies entirely on `command.references` being populated. If it's empty, no injection happens.

---

## ✅ Recommended Approach

### Solution: Create a Public Helper Function

**Add to `parser.py`:**

```python
def extract_references(content: str | None) -> list[str]:
    """Extract $agent references from content.

    Args:
        content: Text potentially containing $agent references.

    Returns:
        List of agent IDs referenced (deduplicated, order preserved).
    """
    if not content:
        return []
    matches = REFERENCE_PATTERN.findall(content)
    # Deduplicate while preserving order
    seen = set()
    return [r for r in matches if not (r in seen or seen.add(r))]
```

**Update `loop.py` (lines 309-314):**

```python
from teambot.repl.parser import extract_references

# ... in the raw-to-agent conversion:
command = Command(
    type=CommandType.AGENT,
    agent_id=default_agent,
    agent_ids=[default_agent],
    content=command.content,
    references=extract_references(command.content),  # ← ADD THIS
)
```

**Update `app.py` (lines 140-146):** Same pattern.

**Update `router.py` (lines 200-206):** Same pattern.

### Why This Approach?

| Alternative | Pros | Cons |
|-------------|------|------|
| **Helper function** (chosen) | Reuses existing pattern, minimal code duplication, easy to test | None significant |
| Re-parse through `parse_command` | Full parsing behavior | Would require constructing fake `@agent content` string; more overhead |
| Inline extraction in each file | Works | Code duplication across 3 files |

### Implementation Tasks

1. **Add `extract_references()` helper** to `parser.py`
2. **Refactor `_parse_agent_command()`** to use the helper (optional but clean)
3. **Fix `loop.py`** lines 309-314 to call `extract_references()`
4. **Fix `app.py`** lines 140-146 to call `extract_references()`
5. **Fix `router.py`** lines 200-206 to call `extract_references()`
6. **Add unit tests** for `extract_references()` function
7. **Add integration tests** for default agent + references scenario

---

## 🧪 Testing Strategy Research

### Existing Test Infrastructure

| Aspect | Details |
|--------|---------|
| **Framework** | pytest 7.4+ with pytest-mock, pytest-asyncio |
| **Location** | `tests/` directory (mirrors `src/` structure) |
| **Naming** | `test_*.py` files, `test_*` functions |
| **Runner** | `uv run pytest` |
| **Coverage** | coverage.py, ~80% target |

### Relevant Test Files

| File | Purpose | Lines |
|------|---------|-------|
| `tests/test_repl/test_parser.py` | Parser unit tests | 278-351 (references) |
| `tests/test_integration/test_shared_context.py` | Integration tests for `$agent` | 1-203 |
| `tests/test_default_agent_acceptance.py` | Default agent acceptance tests | 1-287 |
| `tests/test_tasks/test_executor.py` | TaskExecutor tests | Various |

### Test Patterns Found

**From `tests/test_repl/test_parser.py`:**

```python
def test_parse_single_reference(self):
    """Test parsing single $agent reference."""
    result = parse_command("@pm Summarize $ba output")
    assert result.references == ["ba"]
    assert "$ba" in result.content

def test_parse_multiple_references(self):
    """Test parsing multiple references."""
    result = parse_command("@reviewer Check $builder-1 against $pm")
    assert result.references == ["builder-1", "pm"]
```

**From `tests/test_integration/test_shared_context.py`:**

```python
@pytest.mark.asyncio
async def test_full_workflow_with_references(self, mock_sdk):
    """Test complete workflow: BA → PM references BA → Builder references PM."""
    # ... sets up mock SDK, runs commands through TaskExecutor
    assert "=== Output from @ba ===" in pm_call[1]
```

### New Tests Required

1. **Unit test for `extract_references()` helper:**
   ```python
   def test_extract_references_single():
       assert extract_references("Summarize $ba output") == ["ba"]
   
   def test_extract_references_multiple():
       assert extract_references("Check $ba and $pm") == ["ba", "pm"]
   
   def test_extract_references_escaped():
       assert extract_references(r"Use \$pm safely") == []
   
   def test_extract_references_none():
       assert extract_references(None) == []
   ```

2. **Integration test for default agent + references:**
   ```python
   @pytest.mark.asyncio
   async def test_default_agent_with_references(self, mock_sdk):
       """Default agent routing extracts $agent references."""
       executor = TaskExecutor(sdk_client=mock_sdk)
       
       # Run BA first
       await executor.execute(parse_command("@ba Analyze requirements"))
       
       # Create raw command that would be routed to default agent
       raw_cmd = Command(
           type=CommandType.AGENT,
           agent_id="pm",
           agent_ids=["pm"],
           content="Summarize $ba",
           references=extract_references("Summarize $ba"),  # Fixed behavior
       )
       result = await executor.execute(raw_cmd)
       
       # Verify BA output was injected
       call_args = mock_sdk.execute.call_args
       assert "=== Output from @ba ===" in call_args[0][1]
   ```

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `extract_references()` helper | **Code-First** | Simple utility function, easy to verify |
| Integration in loop.py | **Code-First** | Bug fix, behavior already defined |
| Integration in app.py | **Code-First** | Same fix, different entry point |

---

## 📁 File References

### Files to Modify

| File | Lines | Change |
|------|-------|--------|
| `src/teambot/repl/parser.py` | After line 93 | Add `extract_references()` helper |
| `src/teambot/repl/parser.py` | 219-225 | Refactor to use helper (optional) |
| `src/teambot/repl/loop.py` | 15-22 | Add import for `extract_references` |
| `src/teambot/repl/loop.py` | 309-314 | Add `references=extract_references(...)` |
| `src/teambot/ui/app.py` | 14-22 | Add import for `extract_references` |
| `src/teambot/ui/app.py` | 140-146 | Add `references=extract_references(...)` |
| `src/teambot/repl/router.py` | 10 | Add import for `extract_references` |
| `src/teambot/repl/router.py` | 200-206 | Add `references=extract_references(...)` |

### Files for New Tests

| File | Purpose |
|------|---------|
| `tests/test_repl/test_parser.py` | Add tests for `extract_references()` |
| `tests/test_integration/test_shared_context.py` | Add test for default agent + refs |

---

## ⚠️ Risks and Considerations

### Low Risk

- **Scope is narrow**: Only 3 locations need the fix
- **Pattern is established**: Reference extraction logic already works in parser
- **Tests exist**: Can verify no regression

### Edge Cases to Verify

| Case | Expected | Test |
|------|----------|------|
| `$pm` (single ref) | `["pm"]` | ✅ Existing test |
| `$ba and $pm` (multiple) | `["ba", "pm"]` | ✅ Existing test |
| `\$pm` (escaped) | `[]` | ⚠️ Need to add test |
| `$100` (number) | `[]` | ✅ Existing test |
| Empty content | `[]` | ⚠️ Need to add test |
| `None` content | `[]` | ⚠️ Need to add test |

---

## 📝 Task Implementation Requests

### High Priority (Bug Fix)

1. **Create `extract_references()` helper in `parser.py`**
   - Location: After `REFERENCE_PATTERN` definition (~line 95)
   - Export in module's public API

2. **Fix `loop.py` Command creation**
   - Location: Lines 309-314
   - Add `references=extract_references(command.content)`

3. **Fix `app.py` Command creation**
   - Location: Lines 140-146
   - Add `references=extract_references(command.content)`

4. **Fix `router.py` Command creation**
   - Location: Lines 200-206
   - Add `references=extract_references(command.content)`

### Medium Priority (Tests)

5. **Add unit tests for `extract_references()`**
   - File: `tests/test_repl/test_parser.py`
   - Cover: single, multiple, escaped, none, empty

6. **Add integration test for default agent + references**
   - File: `tests/test_integration/test_shared_context.py`
   - Cover: end-to-end flow with default agent routing

### Low Priority (Cleanup)

7. **Refactor `_parse_agent_command()` to use helper** (optional)
   - Reduces code duplication
   - Makes logic more testable

---

## 🔮 Potential Next Research

No further research needed. The bug is well-understood and the fix is straightforward.

---

## ✅ Research Validation

```
RESEARCH_VALIDATION: PASS
- Document: CREATED
- Placeholders: 0 remaining
- Technical Approach: DOCUMENTED (helper function + 3 file fixes)
- Entry Points: 4 traced, 3 need fixes
- Test Infrastructure: RESEARCHED (pytest, existing patterns found)
- Implementation Ready: YES
```
