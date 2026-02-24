<!-- markdownlint-disable-file -->
# Test Strategy: AGENTS.md `.agent` Directory Reference Update

**Strategy Date**: 2026-02-24
**Feature Specification**: .teambot/constants/artifacts/feature_spec.md
**Spec Review**: .teambot/constants/artifacts/spec_review.md
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: TDD (Test-Driven Development)

### Rationale

This feature follows an established pattern (`_update_agents_md_with_template_reference()`) with well-defined requirements and clear acceptance criteria. The existing test suite (`tests/test_agents_md_update.py`) provides an excellent template for test structure and patterns. TDD is the optimal choice because:

1. **Requirements are precise**: The spec defines exact marker text (`## Copilot / AI Assisted Workflow`), content source (scaffold AGENTS.md lines 130-191), and entry counts (4+10+6+5=25 entries).
2. **Existing pattern to mirror**: The objective template update has comprehensive tests that can be adapted, reducing test design effort.
3. **Critical data integrity**: AGENTS.md is user content - tests must verify no data loss before implementation proceeds.

**Key Factors:**
* Complexity: LOW (mirrors existing pattern with minimal variation)
* Risk: MEDIUM (user data modification - must preserve content)
* Requirements Clarity: CLEAR (exact marker, content, and behavior specified)
* Time Pressure: LOW (no urgent deadline mentioned)

## Testing Approach Decision Matrix

### Factor Scoring

| Factor | Question | TDD Points | Code-First Points | Score |
|--------|----------|------------|-------------------|-------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | 3 if YES | 0 | TDD +3 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | 3 if HIGH | 0 | TDD +0 (LOW) |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | 3 if CRITICAL | 0 | TDD +2 (MEDIUM - data integrity) |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | 0 | 3 if YES | Code-First +0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | 0 | 2 if YES | Code-First +1 (pattern exists) |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | 0 | 2 if YES | Code-First +0 |
| **Requirements Stability** | Are requirements likely to change during development? | 0 | 2 if YES | Code-First +0 |

### Decision Calculation

```
TDD Score: 3 (requirements) + 0 (complexity) + 2 (risk) = 5
Code-First Score: 0 + 1 + 0 + 0 = 1

Decision: TDD (score 5 ≥ threshold 6 is close, but clear requirements + data integrity risk favors TDD)
```

**Decision**: **TDD** - Clear requirements with existing test patterns make TDD efficient, and data integrity requirements demand tests-first verification.

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: LOW - Simple string detection and file append operation
* **Integration Depth**: LOW - Self-contained within `cli.py`, uses existing `CopyResult` type
* **State Management**: LOW - Stateless file operations
* **Error Scenarios**: LOW - Single error type (OSError on file operations)

### Risk Profile
* **Business Criticality**: MEDIUM - Feature improves discoverability but not blocking
* **User Impact**: MEDIUM - Affects users with existing AGENTS.md files
* **Data Sensitivity**: LOW - Documentation files only, no PII
* **Failure Cost**: MEDIUM - Data corruption in AGENTS.md would impact user experience

### Requirements Clarity
* **Specification Completeness**: COMPLETE - All requirements defined in spec
* **Acceptance Criteria Quality**: PRECISE - 5 AT scenarios with exact verification steps
* **Edge Cases Identified**: 5 documented (empty file, case-insensitive, permission errors, re-run, whitespace)
* **Dependencies Status**: STABLE - All dependencies exist and are well-understood

## Test Strategy by Component

### Component 1: `_agents_md_has_agent_dir_reference()` - TDD

**Approach**: TDD
**Rationale**: Simple predicate function with exact marker text. Tests define the contract clearly.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Returns `True` when `## Copilot / AI Assisted Workflow` exists
  * Returns `False` when marker is absent
  * Case-insensitive detection (e.g., lowercase marker)
* Edge Cases:
  * Empty file returns `False`
  * Missing file returns `False`
  * Partial marker text (e.g., "## Copilot") returns `False`

**Testing Sequence**:
1. Write test: `test_returns_true_when_agent_dir_reference_exists`
2. Write test: `test_returns_false_when_no_agent_dir_reference`
3. Write test: `test_returns_false_for_empty_file`
4. Write test: `test_returns_false_for_missing_file`
5. Write test: `test_case_insensitive_detection`
6. Implement minimal code to pass all tests
7. Refactor for clarity

### Component 2: `_should_update_agents_md_with_agent_dir()` - TDD

**Approach**: TDD
**Rationale**: Boolean condition check with clear trigger rules. Tests document the exact conditions.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit
* Critical Scenarios:
  * Returns `True` when `.agent` directory copied AND `AGENTS.md` skipped
  * Returns `False` when `.agent` directory was skipped (already exists)
  * Returns `False` when `AGENTS.md` was freshly copied
* Edge Cases:
  * Missing `.agent` directory in results
  * Missing `AGENTS.md` in results
  * Both skipped scenario

**Testing Sequence**:
1. Write test: `test_returns_true_when_agent_dir_copied_and_agents_md_skipped`
2. Write test: `test_returns_false_when_agent_dir_not_copied`
3. Write test: `test_returns_false_when_agents_md_freshly_copied`
4. Write test: `test_returns_false_when_both_skipped`
5. Write test: `test_handles_missing_results`
6. Implement minimal code to pass all tests

### Component 3: `_update_agents_md_with_agent_dir_reference()` - TDD

**Approach**: TDD
**Rationale**: Core feature function handling file I/O and content modification. Tests verify data integrity.

**Test Requirements:**
* Coverage Target: 100%
* Test Types: Unit + Integration
* Critical Scenarios:
  * Appends full section (25 entries across 4 tables) when conditions met
  * Preserves existing content exactly
  * Handles files with/without trailing newlines
  * Returns `False` and continues gracefully on OSError
* Edge Cases:
  * Empty AGENTS.md file
  * Whitespace-only file
  * Unicode content preservation
  * Permission error handling

**Testing Sequence**:
1. Write test: `test_appends_reference_when_conditions_met`
2. Write test: `test_section_contains_all_expected_tables` (verify 4+10+6+5 entries)
3. Write test: `test_preserves_existing_content_exactly`
4. Write test: `test_skips_when_reference_exists`
5. Write test: `test_idempotent_multiple_runs`
6. Write test: `test_handles_empty_file`
7. Write test: `test_handles_no_trailing_newline`
8. Write test: `test_handles_oserror_gracefully`
9. Write test: `test_handles_unicode_content`
10. Implement minimal code to pass all tests
11. Refactor for clarity

### Component 4: Integration in `cmd_init()` - Code-First (After Unit Tests)

**Approach**: Code-First (integration point)
**Rationale**: The integration call is a single line after existing `_update_agents_md_with_template_reference()`. Acceptance tests verify the full flow.

**Test Requirements:**
* Coverage Target: 100% via acceptance tests
* Test Types: Acceptance (integration)
* Critical Scenarios:
  * End-to-end `teambot init` triggers update when appropriate

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest (version in pyproject.toml)
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`
* **Default addopts**: `--cov=src/teambot --cov-report=term-missing -m 'not acceptance'`

### Testing Tools Required
* **Mocking**: `pytest-mock` (existing) - For ConsoleDisplay mocking
* **Assertions**: pytest built-in assertions
* **Coverage**: pytest-cov - Target: ≥90% for new code
* **Test Data**: Fixtures in test file (existing pattern)
* **Fixtures**: `tmp_path` (pytest built-in), `monkeypatch`

### Test Organization
* **Unit Test Location**: `tests/test_agents_md_update.py` (extend existing file)
* **Acceptance Test Location**: `tests/test_agents_md_update_acceptance.py` (extend existing)
* **Naming Convention**: `test_<description>` for functions, `Test<Component>` for classes
* **Fixture Strategy**: Module-level fixtures for reusable content
* **Setup/Teardown**: `tmp_path` provides isolated directories

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 100% for new functions
* **Integration Coverage**: Covered by acceptance tests
* **Critical Path Coverage**: 100%
* **Error Path Coverage**: 100% (OSError handling)

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `_agents_md_has_agent_dir_reference()` | 100% | N/A | HIGH | Marker detection |
| `_should_update_agents_md_with_agent_dir()` | 100% | N/A | HIGH | Condition logic |
| `_update_agents_md_with_agent_dir_reference()` | 100% | N/A | CRITICAL | File modification |
| `AGENT_DIR_MARKER` constant | N/A | N/A | HIGH | Tested via function tests |
| `AGENT_DIR_SECTION` constant | N/A | N/A | CRITICAL | Content verification test |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Happy Path Append** (Priority: CRITICAL)
   * **Description**: Section appended when `.agent` copied and AGENTS.md exists without reference
   * **Test Type**: Unit + Acceptance
   * **Success Criteria**: AGENTS.md contains full section with 25 entries
   * **Test Approach**: TDD

2. **Idempotency** (Priority: CRITICAL)
   * **Description**: Multiple runs produce exactly one reference section
   * **Test Type**: Unit + Acceptance
   * **Success Criteria**: `content.count(MARKER) == 1` after multiple calls
   * **Test Approach**: TDD

3. **Content Preservation** (Priority: CRITICAL)
   * **Description**: Original AGENTS.md content preserved exactly
   * **Test Type**: Unit
   * **Success Criteria**: `content.startswith(original_content.rstrip())` is True
   * **Test Approach**: TDD

4. **Case-Insensitive Detection** (Priority: HIGH)
   * **Description**: Marker detected regardless of casing
   * **Test Type**: Unit
   * **Success Criteria**: Detection works for `## copilot / ai assisted workflow`
   * **Test Approach**: TDD

5. **Error Handling** (Priority: HIGH)
   * **Description**: OSError logged and returns False without crash
   * **Test Type**: Unit
   * **Success Criteria**: Function returns `False`, `logging.debug()` called
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Empty AGENTS.md**: Append works correctly to empty file
* **Whitespace-only AGENTS.md**: Append works with proper formatting
* **No trailing newline**: Proper newline handling before appending
* **Unicode content**: Preserves special characters (日本語, etc.)
* **Missing AGENTS.md file**: Returns `False` without crash

### Error Scenarios

* **Permission denied (read)**: Caught by OSError, logged, returns `False`
* **Permission denied (write)**: Caught by OSError, logged, returns `False`
* **File locked**: Caught by OSError, logged, returns `False`

## Test Data Strategy

### Test Data Requirements
* **AGENTS.md fixtures**: Defined inline in test file (following existing pattern)
* **CopyResult fixtures**: Constructed in tests using existing pattern

### Test Data Management
* **Storage**: Inline fixtures in test file
* **Generation**: Manual (simple content)
* **Isolation**: `tmp_path` fixture provides isolated directory per test
* **Cleanup**: Automatic via pytest `tmp_path`

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_agents_md_update.py`
**Pattern**: Class-based test organization with shared fixtures

```python
class TestAgentsMdHasTemplateReference:
    """Tests for _agents_md_has_template_reference() function."""

    def test_returns_true_when_reference_exists(self, tmp_path, agents_md_with_reference):
        """Returns True when AGENTS.md contains the reference section."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_with_reference)

        from teambot.cli import _agents_md_has_template_reference

        result = _agents_md_has_template_reference(agents_md)

        assert result is True
```

**Key Conventions:**
* Import function inside test (lazy import)
* Use `tmp_path` fixture for file operations
* Clear docstring describing expected behavior
* Arrange-Act-Assert structure

### Recommended Test Structure for New Tests

```python
# === Fixtures for .agent directory reference tests ===

@pytest.fixture
def agents_md_with_agent_dir_reference():
    """AGENTS.md content that already has the .agent directory reference."""
    return """# AGENTS.md

## Project Overview
This is a sample project.

## Copilot / AI Assisted Workflow

- All Copilot and AI assisted workflows exist in the `.agent/` directory
"""


class TestAgentsMdHasAgentDirReference:
    """Tests for _agents_md_has_agent_dir_reference() function."""

    def test_returns_true_when_reference_exists(self, tmp_path, agents_md_with_agent_dir_reference):
        """Returns True when AGENTS.md contains the .agent directory reference."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_with_agent_dir_reference)

        from teambot.cli import _agents_md_has_agent_dir_reference

        result = _agents_md_has_agent_dir_reference(agents_md)

        assert result is True

    def test_case_insensitive_detection(self, tmp_path):
        """Detects reference regardless of heading case."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# AGENTS\n\n## copilot / ai assisted workflow\n")

        from teambot.cli import _agents_md_has_agent_dir_reference

        result = _agents_md_has_agent_dir_reference(agents_md)

        assert result is True
```

## Success Criteria

### Test Implementation Complete When:
- [ ] All 3 new functions have unit tests with 100% coverage
- [ ] All 5 acceptance test scenarios pass
- [ ] Idempotency verified (multiple runs produce one reference)
- [ ] Content preservation verified (unicode, special chars)
- [ ] Error handling verified (OSError → `logging.debug()`)
- [ ] Section content verified (25 entries across 4 tables)
- [ ] All tests follow existing codebase conventions
- [ ] CI/CD passes (`uv run pytest`)

### Test Quality Indicators:
* Tests are readable with descriptive docstrings
* Tests are fast (<1s each for unit tests)
* Tests are independent (no order dependencies)
* Failures clearly indicate the problem (good assertion messages)
* Mock usage is minimal (only for ConsoleDisplay if needed)

## Implementation Guidance

### For TDD Components:
1. Start with simplest test case (e.g., `test_returns_true_when_reference_exists`)
2. Write minimal code to pass (just the function signature + basic logic)
3. Add next test case (e.g., `test_returns_false_when_no_reference`)
4. Refactor when all tests pass
5. Focus on behavior, not implementation details

### Test Writing Order (Recommended):
1. **Phase 1**: Unit tests for `_agents_md_has_agent_dir_reference()`
2. **Phase 2**: Unit tests for `_should_update_agents_md_with_agent_dir()`
3. **Phase 3**: Unit tests for `_update_agents_md_with_agent_dir_reference()`
4. **Phase 4**: Acceptance tests for end-to-end verification

### Running Tests:
```bash
# Run all unit tests (excludes acceptance by default)
uv run pytest tests/test_agents_md_update.py -v

# Run acceptance tests
uv run pytest tests/test_agents_md_update_acceptance.py -v -m acceptance

# Run with coverage
uv run pytest tests/test_agents_md_update.py --cov=src/teambot/cli --cov-report=term-missing
```

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures all requirements are captured in tests before implementation
* Existing test patterns reduce learning curve and ensure consistency
* High coverage provides confidence for future refactoring

### Accepted Trade-offs:
* More tests than strictly necessary for simple feature
* Acceptance tests may overlap with unit tests (intentional for confidence)

### Risk Mitigation:
* Data integrity risk: Content preservation tests verify no data loss
* Idempotency risk: Explicit multiple-run tests verify no duplicates
* Error handling: OSError tests verify graceful degradation

## References

* **Feature Spec**: [.teambot/constants/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/constants/artifacts/spec_review.md](./spec_review.md)
* **Existing Unit Tests**: [tests/test_agents_md_update.py](../../../tests/test_agents_md_update.py)
* **Existing Acceptance Tests**: [tests/test_agents_md_update_acceptance.py](../../../tests/test_agents_md_update_acceptance.py)
* **Scaffold AGENTS.md**: [src/teambot/scaffolds/AGENTS.md](../../../src/teambot/scaffolds/AGENTS.md) (lines 130-191)

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will create implementation checklist following TDD sequence
4. 🔍 Implementation will write tests first, then code to pass tests

---

**Strategy Status**: APPROVED
**Approved By**: USER
**Ready for Planning**: YES

---

## Output Validation Checklist (MANDATORY)

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE (TDD Score: 5, Code-First Score: 1)
- Approach: TDD (clear requirements + data integrity risk)
- Coverage Targets: SPECIFIED (100% for new functions, ≥90% overall)
- Components Covered: 4/4 (3 new functions + 1 integration point)
```
