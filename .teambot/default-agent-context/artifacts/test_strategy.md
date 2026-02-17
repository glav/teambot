<!-- markdownlint-disable-file -->
# Test Strategy: Default Agent Context Reference Extraction

**Strategy Date**: 2026-02-17
**Feature Specification**: .teambot/default-agent-context/artifacts/feature_spec.md
**Spec Review**: .teambot/default-agent-context/artifacts/spec_review.md
**Strategist**: Test Strategy Agent (Builder-2)

---

## Testing Approach Decision Matrix

### Factor Scoring

| Factor | Question | Answer | TDD Points | Code-First Points |
|--------|----------|--------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES - Spec has 5 acceptance tests, 6 unit tests, exact code locations | 3 | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | LOW - Simple regex extraction reuse, no new algorithms | 0 | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | MEDIUM - Bug fix affecting user workflow, not data loss | 2 | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO - Targeted bug fix with known solution | 0 | 0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | YES - Extract existing logic into helper, call from 2 locations | 0 | 2 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO - Quality fix, not urgent | 0 | 0 |
| **Requirements Stability** | Are requirements likely to change during development? | STABLE - Bug fix, requirements are clear | 0 | 0 |

### Score Summary

| Metric | Score |
|--------|-------|
| **TDD Score** | 5 |
| **Code-First Score** | 2 |

### Decision

**TDD Score: 5, Code-First Score: 2**

Per decision matrix thresholds:
- TDD ≥ 6: Pure TDD
- Code-First ≥ 5: Pure Code-First  
- Otherwise: **Hybrid**

**Recommended Approach: HYBRID**

Since TDD score is 5 (one point below threshold) and Code-First score is 2 (well below threshold), this calls for a **Hybrid** approach:
- **TDD for core logic**: The new `extract_references()` helper function
- **Code-First for integration**: The fixes to `loop.py` and `app.py` (simple one-line additions)

---

## Recommended Testing Approach

**Primary Approach**: HYBRID (TDD for helper, Code-First for integration)

### Rationale

This is a targeted bug fix with clear requirements and a well-defined solution. The fix involves:
1. Extracting existing logic into a reusable `extract_references()` helper function
2. Calling that helper from two locations (`loop.py` and `app.py`)

The helper function deserves TDD because it encapsulates the reference extraction logic and will be the single source of truth. Having tests first ensures the function behaves correctly before integrating it. The integration points are trivial one-line changes (adding `references=extract_references(content)` to the `Command` constructor), making Code-First appropriate for those.

**Key Factors:**
* Complexity: LOW (reusing existing regex pattern)
* Risk: MEDIUM (affects user workflow, but not data integrity)
* Requirements Clarity: CLEAR (spec has exact code, line numbers, and test cases)
* Time Pressure: LOW (quality fix)

---

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: LOW - Uses existing `REFERENCE_PATTERN` regex, no new algorithms
* **Integration Depth**: LOW - Helper called from 2 locations, both simple insertions
* **State Management**: STATELESS - Pure function, no state
* **Error Scenarios**: MINIMAL - Only edge case is `None` input, returns empty list

### Risk Profile
* **Business Criticality**: MEDIUM - Affects productivity feature (default agent)
* **User Impact**: Moderate - Users relying on default agent + references affected
* **Data Sensitivity**: NONE - Only string manipulation, no PII
* **Failure Cost**: LOW - Silent failure (references not extracted), no data loss

### Requirements Clarity
* **Specification Completeness**: COMPLETE - All code locations, tests, and acceptance criteria documented
* **Acceptance Criteria Quality**: PRECISE - 5 acceptance tests, 6 unit tests with exact assertions
* **Edge Cases Identified**: 4 documented (None input, escaped refs, multiple refs, deduplication)
* **Dependencies Status**: STABLE - Uses existing `REFERENCE_PATTERN` from parser.py

---

## Test Strategy by Component

### Component 1: `extract_references()` Helper Function - TDD

**Approach**: TDD
**Rationale**: This is the core fix - a new public function that will be the single source of truth for reference extraction. Tests first ensure correct behavior and document expected outputs.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Single reference extraction (`$reviewer` → `["reviewer"]`)
  * Multiple references (`$pm and $ba` → `["pm", "ba"]`)
  * Deduplication preserving order (`$pm ... $ba ... $pm` → `["pm", "ba"]`)
  * Escaped references not extracted (`\$reviewer` → `[]`)
  * No references returns empty list
  * None input returns empty list
  * Hyphenated agents (`$builder-1` → `["builder-1"]`)

**Testing Sequence** (TDD):
1. Write test for single reference extraction
2. Implement `extract_references()` with REFERENCE_PATTERN
3. Write test for multiple references
4. Verify passing (pattern already handles this)
5. Write test for deduplication
6. Implement deduplication logic
7. Write test for escaped references
8. Verify passing (negative lookbehind already handles this)
9. Write test for None input
10. Add None check at function start
11. Refactor: Extract inline code from `_parse_agent_command()` to call `extract_references()`

### Component 2: `loop.py` Default Agent Fix - Code-First

**Approach**: Code-First
**Rationale**: This is a one-line addition to an existing code block. The change is adding `references=extract_references(command.content)` to the Command constructor at line ~313.

**Test Requirements:**
* Coverage Target: Integration test coverage
* Test Types: Unit + Integration
* Critical Scenarios:
  * Default agent routing with single reference
  * Default agent routing with multiple references
  * Default agent routing with escaped reference
  * Pipeline routing still works (calls `parse_command()` which already handles refs)

**Testing Sequence** (Code-First):
1. Implement the one-line fix in `loop.py`
2. Run existing tests to verify no regression
3. Add integration test for default agent + reference scenario
4. Verify reference extraction works end-to-end

### Component 3: `app.py` Default Agent Fix - Code-First

**Approach**: Code-First
**Rationale**: Identical to loop.py - one-line addition at line ~146.

**Test Requirements:**
* Coverage Target: Integration test coverage
* Test Types: Unit + Integration
* Critical Scenarios:
  * Default agent routing with reference in UI
  * Pipeline routing still works

**Testing Sequence** (Code-First):
1. Implement the one-line fix in `app.py`
2. Run existing UI tests to verify no regression
3. Add integration test for default agent + reference in UI mode

---

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: Defined in pyproject.toml dev dependencies
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `pytest-mock` (MagicMock, AsyncMock) - Used for SDK and console mocking
* **Assertions**: pytest native `assert` statements
* **Coverage**: `pytest-cov` - Target: maintain 80%+ overall
* **Async Support**: `pytest-asyncio` - Used for async test methods

### Test Organization
* **Test Location**: `tests/test_repl/` for parser and loop, `tests/test_ui/` for app
* **Naming Convention**: `test_*.py` files, `Test*` classes, `test_*` functions
* **Fixture Strategy**: Inline fixtures with `MagicMock`/`AsyncMock`, no shared conftest for this feature
* **Setup/Teardown**: Per-test setup via pytest fixtures

---

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 100% for `extract_references()` helper
* **Integration Coverage**: 80%+ for modified code paths in loop.py and app.py
* **Critical Path Coverage**: 100% for default agent + reference scenario
* **Error Path Coverage**: 100% for None input handling

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `extract_references()` | 100% | N/A | CRITICAL | New helper function, TDD |
| `loop.py` default agent | 80% | 90% | HIGH | One-line fix + existing coverage |
| `app.py` default agent | 80% | 90% | HIGH | One-line fix + existing coverage |
| `_parse_agent_command()` | 100% | N/A | MEDIUM | Refactor to call helper |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Single Reference with Default Agent** (Priority: CRITICAL)
   * **Description**: User input with `$reviewer` routed via default agent
   * **Test Type**: Unit + Integration
   * **Success Criteria**: `command.references == ["reviewer"]`
   * **Test Approach**: TDD for helper, Integration for loop.py

2. **Multiple References with Default Agent** (Priority: HIGH)
   * **Description**: User input with `$reviewer and $ba` routed via default agent
   * **Test Type**: Unit + Integration
   * **Success Criteria**: `command.references == ["reviewer", "ba"]`
   * **Test Approach**: TDD for helper, Integration for loop.py

3. **Escaped Reference Not Extracted** (Priority: HIGH)
   * **Description**: User input with `\$reviewer` (escaped)
   * **Test Type**: Unit
   * **Success Criteria**: `command.references == []`
   * **Test Approach**: TDD for helper

4. **Pipeline with Default Agent Still Works** (Priority: HIGH)
   * **Description**: Pipeline syntax continues through parse_command()
   * **Test Type**: Integration
   * **Success Criteria**: Pipeline parsed correctly, references extracted
   * **Test Approach**: Existing tests + spot check

5. **Explicit @agent Prefix Still Works** (Priority: CRITICAL)
   * **Description**: `@pm task $reviewer` continues to work
   * **Test Type**: Regression
   * **Success Criteria**: All existing test_parser.py tests pass
   * **Test Approach**: Run existing test suite

### Edge Cases to Cover

* **None Content**: `extract_references(None)` returns `[]`
* **Empty String**: `extract_references("")` returns `[]`
* **Dollar Amount**: `extract_references("Budget $100")` returns `[]` (number after $)
* **Duplicate References**: `extract_references("$pm ... $pm")` returns `["pm"]` (deduplicated)
* **Order Preservation**: `extract_references("$ba then $pm")` returns `["ba", "pm"]`

### Error Scenarios

* **No Error Scenarios**: This is pure data extraction with no failure modes beyond returning empty list

---

## Test Data Strategy

### Test Data Requirements
* **Input strings**: Simple inline strings in tests
* **Expected outputs**: Literal lists of agent IDs

### Test Data Management
* **Storage**: Inline in test files
* **Generation**: Manual, based on spec acceptance criteria
* **Isolation**: Each test is independent
* **Cleanup**: No cleanup needed (stateless)

---

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_repl/test_parser.py`
**Pattern**: Class-based test organization with descriptive docstrings

```python
class TestParseReferences:
    """Tests for $agent reference parsing."""

    def test_parse_single_reference(self):
        """Test parsing single $agent reference."""
        result = parse_command("@pm Summarize $ba output")

        assert result.references == ["ba"]
        assert "$ba" in result.content

    def test_parse_multiple_references(self):
        """Test parsing multiple references."""
        result = parse_command("@reviewer Check $builder-1 against $pm")

        assert result.references == ["builder-1", "pm"]

    def test_references_preserve_order(self):
        """Test references maintain discovery order."""
        result = parse_command("@pm Combine $writer with $ba and $reviewer")

        assert result.references == ["writer", "ba", "reviewer"]
```

**Key Conventions:**
* Class groups related tests
* Each test has descriptive docstring
* Simple `assert` statements
* Tests are self-contained

### Recommended Test Structure

```python
class TestExtractReferences:
    """Tests for extract_references helper function."""

    def test_extract_single_reference(self):
        """Extract single $agent reference from content."""
        result = extract_references("use $reviewer feedback")
        assert result == ["reviewer"]

    def test_extract_multiple_references(self):
        """Extract multiple $agent references preserving order."""
        result = extract_references("combine $reviewer and $ba")
        assert result == ["reviewer", "ba"]

    def test_extract_deduplicates_preserving_order(self):
        """Duplicate references are deduplicated, first occurrence wins."""
        result = extract_references("$pm said $ba but $pm again")
        assert result == ["pm", "ba"]

    def test_extract_excludes_escaped(self):
        """Escaped \\$agent references are not extracted."""
        result = extract_references("explain \\$reviewer syntax")
        assert result == []

    def test_extract_none_returns_empty(self):
        """None content returns empty list."""
        result = extract_references(None)
        assert result == []

    def test_extract_empty_string_returns_empty(self):
        """Empty string returns empty list."""
        result = extract_references("")
        assert result == []

    def test_extract_hyphenated_agent(self):
        """Hyphenated agent IDs are extracted correctly."""
        result = extract_references("use $builder-1 work")
        assert result == ["builder-1"]


class TestDefaultAgentReferences:
    """Tests for default agent routing with references."""

    def test_default_agent_command_includes_references(self):
        """Default agent routing populates references field."""
        content = "use $reviewer feedback"
        references = extract_references(content)
        command = Command(
            type=CommandType.AGENT,
            agent_id="pm",
            agent_ids=["pm"],
            content=content,
            references=references,
        )
        assert command.references == ["reviewer"]
```

---

## Success Criteria

### Test Implementation Complete When:
- [x] `extract_references()` helper has 100% test coverage
- [ ] All 7 unit tests for helper function pass
- [ ] `loop.py` fix has integration test
- [ ] `app.py` fix has integration test
- [ ] All existing tests pass (no regressions)
- [ ] Coverage remains at 80%+ overall
- [ ] Tests follow codebase conventions

### Test Quality Indicators:
* Tests are readable and self-documenting (descriptive names, docstrings)
* Tests are fast and reliable (no flakiness - stateless pure functions)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem (specific assertions)
* No mocking needed for helper function tests (pure function)

---

## Implementation Guidance

### For TDD Components (`extract_references()`):
1. Create `tests/test_repl/test_parser.py::TestExtractReferences` class
2. Write `test_extract_single_reference` first
3. Implement `extract_references()` in parser.py (extract from `_parse_agent_command()`)
4. Add tests for multiple, deduplication, escaped, None, empty, hyphenated
5. Verify all tests pass
6. Refactor `_parse_agent_command()` to call `extract_references()`
7. Run full test suite to verify no regressions

### For Code-First Components (`loop.py`, `app.py`):
1. Add `from teambot.repl.parser import extract_references` import
2. Add `references=extract_references(command.content)` to Command constructor
3. Run existing tests
4. Add integration tests for default agent + reference scenario

### For Hybrid Approach:
1. Start with TDD for `extract_references()` (Steps 1-5 above)
2. Proceed to Code-First for `loop.py` and `app.py` (Steps 6-8 above)
3. Run full test suite
4. Validate coverage targets met

---

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD for helper ensures correct behavior before integration
* Code-First for simple fixes avoids unnecessary ceremony
* Single source of truth for reference extraction eliminates duplication
* Minimal test additions (7-10 new tests) for targeted fix

### Accepted Trade-offs:
* Hybrid approach is slightly more complex to execute than pure TDD or Code-First
* Integration tests for UI (app.py) are slower than unit tests

### Risk Mitigation:
* Running full existing test suite after each change catches regressions
* TDD for helper function catches edge cases early
* Spec-defined test cases ensure complete coverage

---

## References

* **Feature Spec**: [.teambot/default-agent-context/artifacts/feature_spec.md](feature_spec.md)
* **Spec Review**: [.teambot/default-agent-context/artifacts/spec_review.md](spec_review.md)
* **Test Examples**: `tests/test_repl/test_parser.py:268-351` (TestParseReferences class)
* **Test Standards**: `pyproject.toml` [tool.pytest.ini_options]
* **Target Code**: 
  - `src/teambot/repl/parser.py:93` (REFERENCE_PATTERN)
  - `src/teambot/repl/parser.py:219-225` (existing extraction logic)
  - `src/teambot/repl/loop.py:308-314` (fix location)
  - `src/teambot/ui/app.py:139-146` (fix location)

---

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow recommended approach per component

---

**Strategy Status**: APPROVED
**Approved By**: Test Strategy Agent
**Ready for Planning**: YES

---

## 🔐 Approval Request

I've analyzed **Default Agent Context Reference Extraction** and recommend **HYBRID** (TDD for helper, Code-First for integration).

**Do you:**
1. ✅ Approve this strategy and proceed to planning
2. 🔄 Want to adjust the approach (please specify)
3. ❓ Have questions or concerns about the recommendation

---

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE
- Approach: HYBRID (TDD=5, Code-First=2, falls between thresholds)
- Coverage Targets: SPECIFIED (100% for helper, 80%+ for integration)
- Components Covered: 3/3 (extract_references, loop.py, app.py)
```
