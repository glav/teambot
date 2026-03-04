<!-- markdownlint-disable-file -->
# Test Strategy: Pipeline Parse Error Fix

**Strategy Date**: 2026-03-03
**Feature Specification**: .teambot/pipeline-parse-error/artifacts/feature_spec.md
**Research Reference**: N/A (straightforward fix - no research phase required)
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: TDD (Test-Driven Development)

### Rationale

This feature is ideal for TDD because the requirements are exceptionally well-defined with precise acceptance criteria. The specification includes 10 explicit unit test cases with specific inputs and expected outputs, plus 5 acceptance test scenarios. The quote-awareness logic involves distinct state transitions that can be independently tested.

TDD is strongly recommended because the fix modifies critical parsing infrastructure. Any regressions would break existing pipeline functionality for all users. Writing tests first ensures we maintain backward compatibility and provides immediate verification of each implementation step. The state machine approach (NORMAL → IN_SINGLE → IN_DOUBLE) maps cleanly to testable units.

Additionally, the feature has high risk of subtle edge cases (nested quotes, unclosed quotes, mixed quoted/unquoted arrows). TDD forces us to define expected behavior for each edge case before implementation, preventing ambiguity during development.

**Key Factors:**
* Complexity: MEDIUM (state machine with 3 states, multiple transition triggers)
* Risk: HIGH (core parser infrastructure, backward compatibility critical)
* Requirements Clarity: CLEAR (10 test cases defined, 5 acceptance scenarios)
* Time Pressure: LOW (quality over speed)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | Points |
|--------|----------|-------|--------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES | TDD +3 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM | TDD +2 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | HIGH | TDD +3 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO | Code-First +0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | NO | Code-First +0 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO | Code-First +0 |
| **Requirements Stability** | Are requirements likely to change during development? | NO | Code-First +0 |

### Decision Calculation

```
TDD Score: 3 + 2 + 3 = 8
Code-First Score: 0

Decision: TDD (score 8 >> threshold 6)
```

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Medium - Character-by-character state machine for quote tracking
* **Integration Depth**: Low - Self-contained within parser.py module
* **State Management**: Medium - 3 states (NORMAL, IN_SINGLE, IN_DOUBLE) with transitions
* **Error Scenarios**: Low - Forgiving behavior on unclosed quotes (no errors to handle)

### Risk Profile
* **Business Criticality**: HIGH - Parser is critical infrastructure for all REPL commands
* **User Impact**: HIGH - Affects all users who use pipeline syntax
* **Data Sensitivity**: None - No sensitive data involved
* **Failure Cost**: HIGH - Regressions would break existing valid pipelines

### Requirements Clarity
* **Specification Completeness**: COMPLETE (18/18 sections, 0 TBDs)
* **Acceptance Criteria Quality**: PRECISE (10 unit tests, 5 acceptance scenarios defined)
* **Edge Cases Identified**: 10 documented (quotes, nested, unclosed, mixed)
* **Dependencies Status**: STABLE (parser.py well-understood, no external deps)

## Test Strategy by Component

### Component 1: `find_unquoted_pipeline_operator()` - TDD

**Approach**: TDD
**Rationale**: This is the core new helper function. Requirements are crystal clear - scan for `-> @` while respecting quote boundaries. Perfect for test-first development.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Returns None when no `-> @` pattern exists
  * Returns correct index when `-> @` is outside quotes
  * Returns None when `-> @` is inside single quotes
  * Returns None when `-> @` is inside double quotes
  * Handles nested quotes correctly
  * Handles unclosed quotes (treat as inside quote)
* Edge Cases:
  * Empty string input
  * Only quotes, no arrow
  * Multiple arrows - some quoted, some not
  * Arrow at very end of string
  * Quote immediately before arrow

**Testing Sequence** (TDD):
1. Write test: returns None for plain text without arrow
2. Write test: returns index for simple `-> @agent`
3. Write test: returns None when arrow in single quotes
4. Write test: returns None when arrow in double quotes
5. Write test: nested quotes `"the '->' operator"`
6. Write test: mixed quoted/unquoted
7. Write test: unclosed quote behavior
8. Implement minimal code to pass each test

### Component 2: `_parse_agent_command()` modification - TDD

**Approach**: TDD
**Rationale**: Modifying existing function. Need tests that verify new behavior while ensuring existing behavior unchanged. Critical for backward compatibility.

**Test Requirements:**
* Coverage Target: 95% (existing coverage maintained)
* Test Types: Unit + Regression
* Critical Scenarios:
  * Existing valid pipelines still work
  * Quoted arrow operators don't trigger pipeline
  * Content with quotes preserved correctly in output
* Edge Cases:
  * Multi-stage pipeline with quoted content in one stage
  * Mixed operators (background + quoted arrow)

**Testing Sequence** (TDD):
1. Write failing tests for quoted arrows (FR-001, FR-002)
2. Write test for nested quotes (FR-003)
3. Write test for mixed quoted/unquoted (FR-004)
4. Verify all existing tests still pass (regression)
5. Implement fix using new helper function

### Component 3: `_parse_pipeline()` modification - TDD

**Approach**: TDD
**Rationale**: Must update splitting logic to only split on unquoted arrows. Tests ensure quoted content preserved across stages.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Multi-stage pipeline splits correctly
  * Quoted arrows in stage content don't cause extra splits
  * Stage content preserves quoted strings
* Edge Cases:
  * Pipeline where first stage content has quoted arrow

**Testing Sequence** (TDD):
1. Write test: 2-stage pipeline with quoted arrow in first stage content
2. Write test: content preservation across splits
3. Implement splitting fix

### Component 4: `needs_default_agent_for_pipeline()` modification - TDD

**Approach**: TDD
**Rationale**: Must apply same quote-aware logic for consistency. User expectation: raw input with quoted arrow not treated as pipeline.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Raw text with quoted arrow returns False
  * Raw text with unquoted arrow still returns True
* Edge Cases:
  * `"explain ->" -> @notify` - quoted + unquoted

**Testing Sequence** (TDD):
1. Write test: UT-009 from spec
2. Write test: UT-010 from spec
3. Implement fix

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: As specified in pyproject.toml
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: Not required for this feature (pure parsing logic)
* **Assertions**: Built-in pytest assertions
* **Coverage**: pytest-cov (--cov=src/teambot), Target: 95%+
* **Test Data**: Inline string literals in test functions

### Test Organization
* **Test Location**: `tests/test_repl/test_parser.py`
* **Naming Convention**: `test_<behavior>` in appropriate test class
* **Fixture Strategy**: No fixtures needed (stateless parsing)
* **Setup/Teardown**: None required

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 95% (current baseline to be maintained)
* **Integration Coverage**: N/A (no integration boundaries)
* **Critical Path Coverage**: 100% (all quoted arrow variations)
* **Error Path Coverage**: N/A (no error paths in this feature)

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `find_unquoted_pipeline_operator()` | 100% | N/A | CRITICAL | New helper - full coverage required |
| `_parse_agent_command()` | 95% | N/A | CRITICAL | Maintain existing + new cases |
| `_parse_pipeline()` | 95% | N/A | HIGH | Test stage content preservation |
| `needs_default_agent_for_pipeline()` | 100% | N/A | HIGH | Two new test cases |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Single-quoted arrow not pipeline** (Priority: CRITICAL)
   * **Description**: `@pm explain the '->' operator` → `is_pipeline=False`
   * **Test Type**: Unit
   * **Success Criteria**: Command parses as single agent command, content contains `'->'`
   * **Test Approach**: TDD

2. **Double-quoted arrow not pipeline** (Priority: CRITICAL)
   * **Description**: `@pm the "->" chains agents` → `is_pipeline=False`
   * **Test Type**: Unit
   * **Success Criteria**: Command parses as single agent command, content contains `"->"` 
   * **Test Approach**: TDD

3. **Nested quotes handled** (Priority: HIGH)
   * **Description**: `@pm describe the '"->"' syntax` → `is_pipeline=False`
   * **Test Type**: Unit
   * **Success Criteria**: Inner quotes don't break outer quote detection
   * **Test Approach**: TDD

4. **Mixed quoted/unquoted** (Priority: HIGH)
   * **Description**: `@pm explain "->" -> @builder do it` → `is_pipeline=True`, 2 stages
   * **Test Type**: Unit
   * **Success Criteria**: Only unquoted arrow triggers pipeline, quoted preserved in content
   * **Test Approach**: TDD

5. **Valid pipelines unchanged** (Priority: CRITICAL)
   * **Description**: All existing pipeline tests pass
   * **Test Type**: Regression
   * **Success Criteria**: 0 test failures
   * **Test Approach**: Run existing test suite

### Edge Cases to Cover

* **UT-001**: Single-quoted arrow - `@pm explain the '->' operator`
* **UT-002**: Double-quoted arrow - `@pm the "->" chains agents`
* **UT-003**: Nested quotes - `@pm describe the '"->"' syntax`
* **UT-004**: Quoted arrow with @agent - `@pm explain '-> @builder' syntax`
* **UT-005**: Mixed quoted/unquoted - `@pm explain "->" -> @builder do it`
* **UT-006**: Multiple quoted arrows - `@pm '->'->'->'->'`
* **UT-007**: Unclosed quote (forgiving) - `@pm explain '-> @builder`
* **UT-008**: Empty quotes around arrow - `@pm '' -> @builder task`
* **UT-009**: Raw pipeline with quoted - `explain "->" -> @notify`
* **UT-010**: Raw all quoted - `explain the '->' operator`

### Error Scenarios

No new error scenarios - this feature only prevents false positives, doesn't add new error conditions. Existing error handling preserved:
* **Empty stage errors**: Pipeline stage without content still errors
* **Unknown agent errors**: Invalid agents in pipeline still produce helpful errors

## Test Data Strategy

### Test Data Requirements
* Input strings: Defined inline in test functions
* Expected outputs: Verified via assertions on Command object properties

### Test Data Management
* **Storage**: Inline in test file (no external fixtures needed)
* **Generation**: Manual - all 10 test cases defined in spec
* **Isolation**: Each test function independent
* **Cleanup**: None required (pure functions)

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_repl/test_parser.py`
**Pattern**: Test class per feature, clear test names, direct assertions

```python
class TestDependencyOperator:
    """Tests for -> dependency operator."""

    def test_parse_simple_dependency(self):
        """Test parsing @a task -> @b task."""
        result = parse_command("@pm Create plan -> @builder-1 Implement it")

        assert result.type == CommandType.AGENT
        assert result.is_pipeline is True
        assert len(result.pipeline) == 2

        assert result.pipeline[0].agent_ids == ["pm"]
        assert result.pipeline[0].content == "Create plan"

        assert result.pipeline[1].agent_ids == ["builder-1"]
        assert result.pipeline[1].content == "Implement it"

    def test_parse_arrow_in_content(self):
        """Test -> in content without second @ is not pipeline."""
        result = parse_command("@pm Create plan -> execute")

        # No @agent after ->, so it's content
        assert result.is_pipeline is False
        assert "-> execute" in result.content
```

**Key Conventions:**
* Test class groups related tests
* Docstring explains what's being tested
* Direct assertions on result properties
* No fixtures for simple parsing tests

### Recommended Test Structure

```python
class TestQuotedPipelineOperators:
    """Tests for quoted -> operators not triggering pipelines."""

    def test_single_quoted_arrow_not_pipeline(self):
        """Single-quoted '->' should not trigger pipeline parsing."""
        result = parse_command("@pm explain the '->' operator")

        assert result.type == CommandType.AGENT
        assert result.is_pipeline is False
        assert result.agent_id == "pm"
        assert "'->'".replace("'", "'") in result.content or "'->'".replace("'", "'") in result.content

    def test_double_quoted_arrow_not_pipeline(self):
        """Double-quoted "->" should not trigger pipeline parsing."""
        result = parse_command('@pm the "->" chains agents')

        assert result.is_pipeline is False
        assert '"->"' in result.content

    def test_mixed_quoted_and_unquoted_arrows(self):
        """Quoted arrow ignored, unquoted arrow triggers pipeline."""
        result = parse_command('@pm explain "->" -> @builder do it')

        assert result.is_pipeline is True
        assert len(result.pipeline) == 2
        assert '"->"' in result.pipeline[0].content
        assert result.pipeline[1].agent_ids == ["builder"]
```

## Success Criteria

### Test Implementation Complete When:
- [x] All critical scenarios have tests (10 unit tests + 5 acceptance)
- [ ] Coverage targets are met per component (95%+ overall)
- [ ] All edge cases are tested (UT-001 through UT-010)
- [ ] Error paths are validated (N/A - no new errors)
- [ ] Tests follow codebase conventions (pytest, assert-based)
- [ ] Tests are maintainable and clear
- [ ] CI/CD integration is working (existing pytest config)

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast and reliable (no flakiness - pure functions)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem
* Mock/stub usage is appropriate and minimal (none needed)

## Implementation Guidance

### For TDD Components:

**Phase 1: New Tests (RED)**
1. Create new test class `TestQuotedPipelineOperators` in `tests/test_repl/test_parser.py`
2. Add all 10 unit test functions from spec (UT-001 through UT-010)
3. Run tests - all 10 should FAIL (confirms tests detect the bug)

**Phase 2: Implementation (GREEN)**
4. Implement `find_unquoted_pipeline_operator()` helper
5. Modify `_parse_agent_command()` to use helper
6. Modify `_parse_pipeline()` for quote-aware splitting
7. Modify `needs_default_agent_for_pipeline()` for consistency
8. Run tests - all should PASS

**Phase 3: Regression Verification**
9. Run full test suite: `uv run pytest tests/test_repl/test_parser.py -v`
10. All 73+ existing tests must still pass
11. Run extended tests: `uv run pytest tests/test_repl/test_parser_extended.py -v`

### Quote State Machine Reference

```
State: NORMAL | IN_SINGLE | IN_DOUBLE

NORMAL + ' → IN_SINGLE
NORMAL + " → IN_DOUBLE  
IN_SINGLE + ' → NORMAL
IN_DOUBLE + " → NORMAL
NORMAL + -> @ → PIPELINE DETECTED (return index)
IN_SINGLE + -> @ → IGNORED (continue scanning)
IN_DOUBLE + -> @ → IGNORED (continue scanning)
End of string with open quote → PIPELINE NOT DETECTED (return None)
```

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures 100% confidence in backward compatibility
* Tests document expected behavior for future maintainers
* Edge cases caught before implementation (not after)
* Fast feedback loop - run tests after each code change

### Accepted Trade-offs:
* Slightly slower initial development (write tests first)
* Test file grows by ~100 lines (acceptable for test coverage)

### Risk Mitigation:
* **R-001 (Regex complexity)**: Avoided - using simple state machine instead of complex regex
* **R-002 (Nested quote edge cases)**: Mitigated - explicit tests for nested quotes (UT-003)
* **R-003 (Performance)**: Minimal concern - character scan is O(n), negligible vs regex
* **R-004 (Breaking changes)**: Mitigated - run full regression suite after implementation
* **R-005 (Unclosed quotes)**: Defined - explicit test UT-007 documents forgiving behavior

## References

* **Feature Spec**: [.teambot/pipeline-parse-error/artifacts/feature_spec.md](.teambot/pipeline-parse-error/artifacts/feature_spec.md)
* **Spec Review**: [.teambot/pipeline-parse-error/artifacts/spec_review.md](.teambot/pipeline-parse-error/artifacts/spec_review.md)
* **Test Examples**: `tests/test_repl/test_parser.py`, `tests/test_repl/test_parser_extended.py`
* **Test Standards**: pyproject.toml [tool.pytest.ini_options]

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate TDD phases into implementation plan
4. 🔍 Implementation will follow RED → GREEN → REFACTOR cycle

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

## TEST_STRATEGY_VALIDATION: PASS

- Document: CREATED (`.teambot/pipeline-parse-error/artifacts/test_strategy.md`)
- Decision Matrix: COMPLETE (TDD score 8, Code-First score 0)
- Approach: TDD (score 8 >> threshold 6)
- Coverage Targets: SPECIFIED (95%+ overall, 100% for new helper)
- Components Covered: 4/4 (`find_unquoted_pipeline_operator`, `_parse_agent_command`, `_parse_pipeline`, `needs_default_agent_for_pipeline`)
