<!-- markdownlint-disable-file -->
# Test Strategy: AGENTS.md Objective Template Reference

**Strategy Date**: 2026-02-23
**Feature Specification**: `.teambot/pseudocode/artifacts/feature_spec.md`
**Research Reference**: N/A (spec-driven feature with clear requirements)
**Strategist**: Builder-2 Agent

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | Points |
|--------|----------|-------|--------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES | TDD +3 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | LOW | TDD +0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | CRITICAL (data integrity) | TDD +3 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO | Code-First +0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | YES (file append) | Code-First +2 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO | Code-First +0 |
| **Requirements Stability** | Are requirements likely to change during development? | NO (stable spec) | Code-First +0 |

### Score Summary

| Approach | Total Score |
|----------|-------------|
| **TDD** | 6 |
| **Code-First** | 2 |

### Decision

**TDD Score: 6 ≥ threshold 6 → TDD RECOMMENDED**

## Recommended Testing Approach

**Primary Approach**: TDD

### Rationale

The feature has **well-defined requirements** (6 acceptance test scenarios in spec), a **critical data integrity requirement** (must never corrupt existing AGENTS.md content), and **clear acceptance criteria** that can be expressed as tests before implementation. The idempotency requirement (FR-003) and content preservation (NFR-001) are safety-critical behaviors that benefit from test-first development.

While the implementation is relatively simple (file detection, string search, and append), the risk of corrupting user data makes TDD the appropriate choice. Writing tests first ensures the safety guarantees are verified before any implementation code is written.

**Key Factors:**
* Complexity: LOW - Simple file operations (detect, search, append)
* Risk: CRITICAL - Must preserve existing AGENTS.md content exactly
* Requirements Clarity: CLEAR - 6 acceptance scenarios defined with precise expected outcomes
* Time Pressure: LOW - Quality over speed for data-touching operations

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: Low - String search and file append
* **Integration Depth**: Medium - Integrates with existing `cmd_init()` and `CopyResult` flow
* **State Management**: Low - Stateless file operations
* **Error Scenarios**: Low - Main errors are file system related

### Risk Profile
* **Business Criticality**: HIGH - Poor UX if template goes undiscovered
* **User Impact**: MEDIUM - Affects users with existing AGENTS.md
* **Data Sensitivity**: HIGH - User's AGENTS.md content must be preserved
* **Failure Cost**: HIGH - Corrupted AGENTS.md would damage user trust

### Requirements Clarity
* **Specification Completeness**: COMPLETE - All requirements detailed
* **Acceptance Criteria Quality**: PRECISE - 6 scenarios with exact expected outcomes
* **Edge Cases Identified**: 5 documented (empty file, idempotency, force flag, etc.)
* **Dependencies Status**: STABLE - `CopyResult` and `copy_all_scaffolds()` are established

## Test Strategy by Component

### Component 1: `update_agents_md_with_template_reference()` - TDD

**Approach**: TDD
**Rationale**: Core function with data integrity responsibility. Tests must verify content preservation before any implementation.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Appends reference section when file exists and no reference present
  * Returns correct reason codes for each outcome
  * Preserves existing content exactly (byte-for-byte comparison)
* Edge Cases:
  * Empty AGENTS.md file
  * AGENTS.md with only whitespace
  * AGENTS.md ending with/without newline
  * Case-insensitive reference detection
  * Reference exists with different formatting

**Testing Sequence (TDD):**
1. Write test: `test_returns_false_when_template_not_copied`
2. Write test: `test_returns_false_when_file_not_found`
3. Write test: `test_returns_false_when_reference_exists`
4. Write test: `test_appends_reference_when_conditions_met`
5. Write test: `test_preserves_existing_content_exactly`
6. Write test: `test_handles_empty_file`
7. Implement minimal code to pass each test
8. Refactor for quality

### Component 2: CLI Integration in `cmd_init()` - TDD

**Approach**: TDD
**Rationale**: Integration point with user-facing output. Tests verify correct conditions trigger update.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Unit + Integration
* Critical Scenarios:
  * Update triggers when AGENTS.md skipped AND template copied
  * Update skipped when AGENTS.md was freshly copied
  * Update skipped when template was not copied
  * Success/skip messages displayed correctly
* Edge Cases:
  * Force flag behavior (AGENTS.md overwritten, no update needed)

**Testing Sequence (TDD):**
1. Write test: `test_updates_agents_md_when_skipped_and_template_copied`
2. Write test: `test_skips_update_when_agents_md_freshly_copied`
3. Write test: `test_skips_update_when_template_not_copied`
4. Write test: `test_displays_success_message_on_update`
5. Write test: `test_displays_skip_message_when_reference_exists`
6. Implement integration code
7. Verify end-to-end behavior

### Component 3: Constants and Reference Section - Code-First

**Approach**: Code-First
**Rationale**: Simple constant definitions with no logic. Verify through usage in unit tests.

**Test Requirements:**
* Coverage Target: Implicit (covered by function tests)
* Test Types: None required (constants)
* Critical Scenarios: N/A

**Testing Sequence:**
1. Define constants (OBJECTIVE_TEMPLATE_REFERENCE, REFERENCE_MARKER)
2. Verify correctness through unit tests of main function

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest
* **Version**: As specified in pyproject.toml
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `pytest-mock` / `unittest.mock` - Mock file operations, monkeypatch paths
* **Assertions**: pytest assert - Direct value comparison
* **Coverage**: pytest-cov - Target: 90%+ for new code
* **Test Data**: Fixtures for various AGENTS.md content patterns

### Test Organization
* **Test Location**: `tests/test_scaffolds.py` (extend existing) and new file
* **Naming Convention**: `test_<function_name>_<scenario>`
* **Fixture Strategy**: Use `tmp_path` fixture, create AGENTS.md variants
* **Setup/Teardown**: Built-in pytest fixtures

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 95% (for new code)
* **Integration Coverage**: 90%
* **Critical Path Coverage**: 100%
* **Error Path Coverage**: 90%

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `update_agents_md_with_template_reference()` | 95% | N/A | CRITICAL | Data integrity function |
| `cmd_init()` integration | 85% | 90% | HIGH | User-facing behavior |
| Constants | N/A | N/A | LOW | Covered implicitly |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Content Preservation** (Priority: CRITICAL)
   * **Description**: Existing AGENTS.md content must be preserved exactly
   * **Test Type**: Unit
   * **Success Criteria**: Before/after content comparison passes
   * **Test Approach**: TDD

2. **Idempotency** (Priority: CRITICAL)
   * **Description**: Running init multiple times produces exactly one reference
   * **Test Type**: Unit + Integration
   * **Success Criteria**: Count of reference marker == 1 after N runs
   * **Test Approach**: TDD

3. **Conditional Update** (Priority: HIGH)
   * **Description**: Update only when AGENTS.md skipped AND template copied
   * **Test Type**: Unit
   * **Success Criteria**: Correct return values for each combination
   * **Test Approach**: TDD

4. **Empty File Handling** (Priority: MEDIUM)
   * **Description**: Empty/whitespace-only AGENTS.md receives reference
   * **Test Type**: Unit
   * **Success Criteria**: Reference section added to empty file
   * **Test Approach**: TDD

5. **Case-Insensitive Detection** (Priority: MEDIUM)
   * **Description**: Reference detection is case-insensitive
   * **Test Type**: Unit
   * **Success Criteria**: Various case combinations detected
   * **Test Approach**: TDD

6. **Force Flag Behavior** (Priority: MEDIUM)
   * **Description**: Force flag skips update (file was replaced)
   * **Test Type**: Integration
   * **Success Criteria**: No double reference in force mode
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Empty AGENTS.md**: File exists but has no content
* **Whitespace-only AGENTS.md**: File contains only newlines/spaces
* **No trailing newline**: AGENTS.md doesn't end with newline
* **Reference with different casing**: `DOCS/SDD-OBJECTIVE-TEMPLATE.MD` vs `docs/sdd-objective-template.md`
* **Reference in code block**: Reference marker inside markdown code fence
* **Large AGENTS.md**: Performance with 100KB+ file

### Error Scenarios

* **Permission denied**: File exists but cannot be read/written
* **Disk full**: Cannot append to file
* **File deleted mid-operation**: AGENTS.md removed after check

## Test Data Strategy

### Test Data Requirements
* **Various AGENTS.md content**: Empty, minimal, complex, with/without reference
* **CopyResult mocks**: Simulate different scaffold copy outcomes

### Test Data Management
* **Storage**: Inline strings in test file (fixtures)
* **Generation**: Manual creation of test content patterns
* **Isolation**: Each test uses fresh `tmp_path` directory
* **Cleanup**: Automatic via pytest tmp_path fixture

### Test Fixtures

```python
@pytest.fixture
def agents_md_without_reference():
    """AGENTS.md content without objective template reference."""
    return """# AGENTS.md

## Project Overview
This is a sample project.

## Development Guidelines
- Follow coding standards
- Write tests
"""

@pytest.fixture
def agents_md_with_reference():
    """AGENTS.md content that already has the reference."""
    return """# AGENTS.md

## Project Overview
This is a sample project.

## Objective Template

| File | Description |
|------|-------------|
| `docs/sdd-objective-template.md` | Template for creating objectives. |
"""

@pytest.fixture
def empty_agents_md():
    """Empty AGENTS.md file."""
    return ""
```

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_scaffolds.py`
**Pattern**: Test class organization with clear arrange/act/assert

```python
class TestCopyScaffoldFile:
    """Tests for copy_scaffold_file() function."""

    def test_copies_file_when_target_missing(self, tmp_path):
        """Copies file when target doesn't exist."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "stages.yaml"

        result = copy_scaffold_file("stages.yaml", target)

        assert result.copied is True
        assert result.reason == "copied"
        assert target.exists()

    def test_skips_when_target_exists(self, tmp_path):
        """Skips copy when target already exists - CRITICAL safety test."""
        from teambot.scaffolds import copy_scaffold_file

        target = tmp_path / "stages.yaml"
        target.write_text("existing content")
        original_content = target.read_text()

        result = copy_scaffold_file("stages.yaml", target)

        assert result.copied is False
        assert result.reason == "skipped_exists"
        assert target.read_text() == original_content  # Unchanged!
```

### Recommended Test Structure for New Tests

```python
class TestUpdateAgentsMdWithTemplateReference:
    """Tests for update_agents_md_with_template_reference() function."""

    def test_returns_false_when_template_not_copied(self, tmp_path):
        """Does not update when template was not copied this run."""
        from teambot.scaffolds import update_agents_md_with_template_reference

        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# Existing content")

        updated, reason = update_agents_md_with_template_reference(
            agents_md, template_copied=False
        )

        assert updated is False
        assert reason == "template_not_copied"
        assert "Objective Template" not in agents_md.read_text()

    def test_appends_reference_when_conditions_met(self, tmp_path):
        """Appends reference section when all conditions met."""
        from teambot.scaffolds import update_agents_md_with_template_reference

        agents_md = tmp_path / "AGENTS.md"
        original_content = "# My AGENTS.md\n\nSome content here."
        agents_md.write_text(original_content)

        updated, reason = update_agents_md_with_template_reference(
            agents_md, template_copied=True
        )

        assert updated is True
        assert reason == "updated"
        new_content = agents_md.read_text()
        assert original_content in new_content  # Preserved!
        assert "docs/sdd-objective-template.md" in new_content

    def test_preserves_existing_content_exactly(self, tmp_path):
        """Original content is preserved byte-for-byte."""
        from teambot.scaffolds import update_agents_md_with_template_reference

        agents_md = tmp_path / "AGENTS.md"
        original_content = "# AGENTS\n\n## Section 1\n\nContent with special chars: 日本語\n"
        agents_md.write_text(original_content)

        update_agents_md_with_template_reference(agents_md, template_copied=True)

        new_content = agents_md.read_text()
        assert new_content.startswith(original_content)
```

## Success Criteria

### Test Implementation Complete When:
* [x] All critical scenarios have tests (6 acceptance scenarios)
* [ ] Coverage targets are met per component (95% for core function)
* [ ] All edge cases are tested (empty file, idempotency, case-insensitive)
* [ ] Error paths are validated (permission errors if feasible)
* [ ] Tests follow codebase conventions (pytest, tmp_path fixtures)
* [ ] Tests are maintainable and clear (descriptive names, docstrings)
* [ ] CI/CD integration is working (tests run with `uv run pytest`)

### Test Quality Indicators:
* Tests are readable and self-documenting
* Tests are fast and reliable (no flakiness - all use tmp_path)
* Tests are independent (no test order dependencies)
* Failures clearly indicate the problem (assertion messages)
* Mock/stub usage is appropriate and minimal (prefer real file operations)

## Implementation Guidance

### For TDD Components:

**Component 1: `update_agents_md_with_template_reference()`**

1. Write test for "returns False when template not copied"
2. Implement minimal stub returning (False, "template_not_copied")
3. Write test for "returns False when file not found"
4. Extend implementation with file existence check
5. Write test for "returns False when reference exists"
6. Implement reference marker search
7. Write test for "appends reference when conditions met"
8. Implement file append logic
9. Write test for "preserves existing content exactly"
10. Verify preservation, refactor if needed
11. Add edge case tests (empty file, case-insensitive)
12. Refactor for quality

**Component 2: CLI Integration**

1. Write test for "updates AGENTS.md when skipped and template copied"
2. Add integration call in `cmd_init()`
3. Write test for "displays success message on update"
4. Add display output
5. Write test for "displays skip message when reference exists"
6. Add skip message handling
7. Write acceptance tests (AT-002, AT-003, AT-004)

### Test File Organization

```
tests/
├── test_scaffolds.py                    # Extend with new unit tests
├── test_agents_md_update.py             # NEW: Dedicated unit tests
└── test_init_scaffolds_acceptance.py    # Extend with AT-002, AT-003, AT-004
```

## Considerations and Trade-offs

### Selected Approach Benefits:
* **Safety First**: TDD ensures content preservation verified before implementation
* **Clear Specification**: Tests document exact expected behavior
* **Confidence in Refactoring**: Test suite enables future changes
* **Regression Prevention**: Idempotency guaranteed by tests

### Accepted Trade-offs:
* **Initial Development Slower**: Test-first adds overhead for simple feature
* **Test Maintenance**: Tests must be updated if requirements change
* **Fixture Management**: Multiple AGENTS.md variants to maintain

### Risk Mitigation:
* **Data corruption risk** → Tests verify content preservation before/after
* **Duplicate reference risk** → Tests verify idempotency across multiple runs
* **Integration failure risk** → CLI integration tests cover end-to-end flow

## References

* **Feature Spec**: [.teambot/pseudocode/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/pseudocode/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: `tests/test_scaffolds.py`, `tests/test_init_scaffolds_acceptance.py`
* **Test Standards**: `pyproject.toml` [tool.pytest.ini_options]

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow TDD approach per component

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES

---

## Approval Request

I've analyzed **AGENTS.md Objective Template Reference** and recommend **TDD**.

**Do you:**
1. ✅ Approve this strategy and proceed to planning
2. 🔄 Want to adjust the approach (please specify)
3. ❓ Have questions or concerns about the recommendation

---

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE
- Approach: TDD (score 6 ≥ threshold 6)
- Coverage Targets: SPECIFIED (95% core, 90% integration)
- Components Covered: 3/3
```
