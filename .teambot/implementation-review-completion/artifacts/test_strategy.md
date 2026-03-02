<!-- markdownlint-disable-file -->
# Test Strategy: Implementation Review Completion Check

**Strategy Date**: 2026-03-02
**Feature Specification**: .teambot/implementation-review-completion/artifacts/feature_spec.md
**Research Reference**: .teambot/implementation-review-completion/artifacts/spec_review.md
**Strategist**: Builder-2 (Test Strategy)

## Recommended Testing Approach

**Primary Approach**: **CODE_FIRST** — Code-First (Test-After) for all components

### Rationale

This feature is a **prompt-only implementation** requiring no code changes to the TeamBot application. The deliverable is a single Markdown prompt file (`sdd.7b-implementation-review.prompt.md`) and a one-line YAML configuration update. There are no algorithms, data structures, or application logic to unit test—the "code" is natural language instructions for the reviewer agent.

Testing for prompt-based features focuses on **validation** rather than traditional unit testing: ensuring the prompt file exists, follows the required structure, contains required sections, and that the stages.yaml configuration correctly references it. These checks are straightforward validation tests that should be written after the prompt is authored.

The feature specification already includes 7 detailed acceptance test scenarios (AT-001 through AT-003 explicitly, plus implicit validation tests). Since prompts are primarily validated through workflow execution rather than unit tests, Code-First allows rapid prompt authoring followed by validation that the file meets structural requirements.

**Key Factors:**
* Complexity: **LOW** — Single prompt file + one-line YAML change
* Risk: **MEDIUM** — Affects workflow behavior but no application logic changes
* Requirements Clarity: **CLEAR** — Detailed prompt structure specification in FR section
* Time Pressure: **LOW** — Quality over speed

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Score | Points To |
|--------|----------|-------|-----------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | 3 | TDD |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | 0 | Code-First (no code) |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | 1 | TDD (medium risk) |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | 0 | Code-First |
| **Simplicity** | Is this straightforward CRUD or simple logic? | 3 | Code-First (prompt file) |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | 1 | Code-First |
| **Requirements Stability** | Are requirements likely to change during development? | 0 | Code-First |

**TDD Score: 4** | **Code-First Score: 4**

However, the deciding factor is that **there is no application code to TDD**. The deliverable is a prompt file (Markdown) that cannot have unit tests written before it exists. TDD is inapplicable to prompt authoring.

**Decision**: CODE_FIRST (prompt-only implementation, no code to TDD)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: NONE — No code, only Markdown prompt file
* **Integration Depth**: LOW — Single reference in stages.yaml
* **State Management**: NONE — Prompt file is stateless instructions
* **Error Scenarios**: MINIMAL — File existence, YAML syntax validity

### Risk Profile
* **Business Criticality**: MEDIUM — Improves workflow integrity but existing flow continues working
* **User Impact**: MEDIUM — Affects reviewer agent behavior in IMPLEMENTATION_REVIEW stage
* **Data Sensitivity**: NONE — No user data involved
* **Failure Cost**: LOW — Worst case: reviewer uses generic approach (current behavior)

### Requirements Clarity
* **Specification Completeness**: COMPLETE — All 5 FRs defined with explicit prompt structure
* **Acceptance Criteria Quality**: PRECISE — 7 acceptance criteria with measurable outcomes
* **Edge Cases Identified**: 3 documented (partial completion, missing artifacts, iteration handling)
* **Dependencies Status**: STABLE — Only depends on existing stages.yaml and .agent-tracking paths

## Test Strategy by Component

### Component 1: Prompt File Creation — **CODE_FIRST** 🟢

**Approach**: Code-First (Write prompt, then validate)
**Rationale**: A Markdown prompt file cannot be "tested" before it's written. The prompt is the implementation. Validation tests verify structural requirements are met.

**Test Requirements:**
* Coverage Target: N/A (no code coverage applicable)
* Test Types: Validation (file existence, structure)
* Critical Scenarios:
  * Prompt file exists at `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md`
  * YAML frontmatter is valid with required fields (description, agent, tools)
  * Pre-Code-Review Checklist section is present
  * Rejection Format section is present
  * Approval Format section is present
* Edge Cases:
  * None — prompt structure is deterministic

**Testing Sequence (Code-First):**
1. Author complete prompt file following specification
2. Validate YAML frontmatter syntax
3. Validate required sections exist via text search
4. Manual review of prompt quality

### Component 2: stages.yaml Configuration Update — **CODE_FIRST** 🟢

**Approach**: Code-First (Update YAML, then validate)
**Rationale**: One-line change to reference the new prompt. Validation ensures YAML remains valid and prompt path is correct.

**Test Requirements:**
* Coverage Target: 100% (single field validation)
* Test Types: Validation (YAML syntax, path correctness)
* Critical Scenarios:
  * IMPLEMENTATION_REVIEW stage has `prompt_template` field set
  * `prompt_template` value matches prompt file path
  * YAML syntax remains valid after change
  * Existing tests continue to pass
* Edge Cases:
  * None — single field change

**Testing Sequence (Code-First):**
1. Update stages.yaml line 326 with prompt path
2. Validate YAML syntax with Python yaml parser
3. Run existing test suite to confirm no regressions

### Component 3: Validation Tests — **CODE_FIRST** 🟢

**Approach**: Code-First
**Rationale**: Write validation tests after implementation to confirm deliverables meet requirements.

**Test Requirements:**
* Coverage Target: 100% of validation criteria
* Test Types: Acceptance validation
* Critical Scenarios:
  * AT-001: Prompt rejects incomplete plan with task list
  * AT-002: Prompt approves complete plan and proceeds to code review
  * AT-003: Iteration loop works (reject → builder fixes → re-review)
* Edge Cases:
  * Partially complete plan (some phases done, some not)
  * Missing changes log artifact

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest 7.4.0+
* **Version**: As specified in pyproject.toml
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: None required (no application code to mock)
* **Assertions**: Built-in pytest assertions
* **Coverage**: N/A (no code coverage for Markdown files)
* **Test Data**: Sample plan files with `[x]` and `[ ]` items

### Test Organization
* **Test Location**: `tests/test_implementation_review_prompt.py` (optional validation tests)
* **Naming Convention**: `test_*.py`, `Test*` classes, `test_*` functions
* **Fixture Strategy**: Use pathlib to read prompt file contents
* **Setup/Teardown**: None required

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: N/A (no application code changes)
* **Validation Coverage**: 100% of structural requirements
* **Critical Path Coverage**: 100% (prompt file exists, stages.yaml references it)
* **Error Path Coverage**: N/A (no error handling code)

### Component-Specific Targets

| Component | Unit % | Validation % | Priority | Notes |
|-----------|--------|--------------|----------|-------|
| Prompt file | N/A | 100% | CRITICAL | Structure validation |
| stages.yaml | N/A | 100% | CRITICAL | Reference validation |
| YAML syntax | N/A | 100% | CRITICAL | Parse validation |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Prompt File Existence** (Priority: CRITICAL)
   * **Description**: Verify `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md` exists
   * **Test Type**: Validation
   * **Success Criteria**: File exists and is readable
   * **Test Approach**: Code-First

2. **YAML Frontmatter Validity** (Priority: CRITICAL)
   * **Description**: Verify prompt has valid YAML frontmatter with required fields
   * **Test Type**: Validation
   * **Success Criteria**: frontmatter contains description, agent, tools fields
   * **Test Approach**: Code-First

3. **Pre-Code-Review Checklist Section** (Priority: CRITICAL)
   * **Description**: Verify prompt contains blocking pre-check section
   * **Test Type**: Validation
   * **Success Criteria**: Section header "Pre-Code-Review Checklist" present
   * **Test Approach**: Code-First

4. **Rejection Format Section** (Priority: CRITICAL)
   * **Description**: Verify prompt contains rejection format template
   * **Test Type**: Validation
   * **Success Criteria**: Contains "REJECTED" format with incomplete task list
   * **Test Approach**: Code-First

5. **stages.yaml Reference** (Priority: CRITICAL)
   * **Description**: Verify stages.yaml IMPLEMENTATION_REVIEW has prompt_template
   * **Test Type**: Validation
   * **Success Criteria**: `prompt_template: .agent/commands/sdd/sdd.7b-implementation-review.prompt.md`
   * **Test Approach**: Code-First

6. **Backward Compatibility** (Priority: CRITICAL)
   * **Description**: Existing test suite passes
   * **Test Type**: Regression
   * **Success Criteria**: `uv run pytest` returns 0 exit code
   * **Test Approach**: Validation

### Edge Cases to Cover

* **Empty plan file**: Prompt should detect and report no tasks found
* **All tasks complete `[x]`**: Prompt proceeds to code review section
* **Mixed completion states**: Prompt lists only incomplete `[ ]` items

### Error Scenarios

* **Prompt file missing**: stages.yaml reference fails to resolve (manual check)
* **Invalid YAML frontmatter**: Linting catches syntax errors
* **stages.yaml syntax error**: Validation catches via YAML parser

## Test Data Strategy

### Test Data Requirements
* **Prompt file**: The actual authored prompt file
* **stages.yaml**: The actual modified stages.yaml
* **Sample plans**: Example plan files with various completion states (for manual testing)

### Test Data Management
* **Storage**: Files in repository at specified paths
* **Generation**: Manual authoring
* **Isolation**: Tests read from actual repository paths
* **Cleanup**: No cleanup required (testing file contents, not creating files)

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_stages_yaml_acceptance.py`
**Pattern**: Validation tests for stages.yaml content

```python
class TestStagesYamlAcceptanceScenarios:
    """Acceptance tests for stages.yaml schema improvement."""

    @pytest.fixture
    def stages_yaml_content(self) -> str:
        """Load the actual stages.yaml content."""
        stages_path = Path("stages.yaml")
        return stages_path.read_text(encoding="utf-8")

    def test_at_001_allowed_personas_documentation_accuracy(
        self, stages_yaml_content: str, tmp_path: Path
    ) -> None:
        """AT-001: Verify allowed_personas documentation matches enforcement behavior."""
        pattern = r"#\s*allowed_personas\s*-.*"
        match = re.search(pattern, stages_yaml_content)
        assert match is not None, "allowed_personas field not found in schema reference"
```

**Key Conventions:**
* Use fixtures to load file contents
* Use regex patterns for content validation
* Clear assertion messages

### Recommended Test Structure

```python
"""Validation tests for Implementation Review Completion Check feature."""

import re
from pathlib import Path

import pytest
import yaml


class TestImplementationReviewPromptValidation:
    """Validation tests for sdd.7b-implementation-review.prompt.md."""

    @pytest.fixture
    def prompt_path(self) -> Path:
        """Path to the implementation review prompt."""
        return Path(".agent/commands/sdd/sdd.7b-implementation-review.prompt.md")

    @pytest.fixture
    def prompt_content(self, prompt_path: Path) -> str:
        """Load the prompt file content."""
        return prompt_path.read_text(encoding="utf-8")

    def test_prompt_file_exists(self, prompt_path: Path) -> None:
        """Prompt file exists at expected location."""
        assert prompt_path.exists(), f"Prompt file not found: {prompt_path}"

    def test_yaml_frontmatter_valid(self, prompt_content: str) -> None:
        """Prompt has valid YAML frontmatter with required fields."""
        # Extract frontmatter between --- delimiters
        match = re.match(r"^---\n(.*?)\n---", prompt_content, re.DOTALL)
        assert match is not None, "YAML frontmatter not found"

        frontmatter = yaml.safe_load(match.group(1))
        assert "description" in frontmatter, "Missing 'description' field"
        assert "agent" in frontmatter, "Missing 'agent' field"
        assert "tools" in frontmatter, "Missing 'tools' field"

    def test_pre_check_section_exists(self, prompt_content: str) -> None:
        """Prompt contains Pre-Code-Review Checklist section."""
        assert "Pre-Code-Review Checklist" in prompt_content or "pre-check" in prompt_content.lower()

    def test_rejection_format_exists(self, prompt_content: str) -> None:
        """Prompt contains rejection format template."""
        assert "REJECTED" in prompt_content or "Rejection Format" in prompt_content

    def test_approval_format_exists(self, prompt_content: str) -> None:
        """Prompt contains approval format template."""
        assert "APPROVED" in prompt_content or "Approval Format" in prompt_content


class TestStagesYamlPromptReference:
    """Validation tests for stages.yaml prompt_template reference."""

    @pytest.fixture
    def stages_config(self) -> dict:
        """Load stages.yaml configuration."""
        stages_path = Path("stages.yaml")
        return yaml.safe_load(stages_path.read_text(encoding="utf-8"))

    def test_implementation_review_has_prompt_template(self, stages_config: dict) -> None:
        """IMPLEMENTATION_REVIEW stage has prompt_template configured."""
        impl_review = stages_config["stages"]["IMPLEMENTATION_REVIEW"]
        assert impl_review.get("prompt_template") is not None, (
            "prompt_template should not be null"
        )

    def test_prompt_template_path_is_correct(self, stages_config: dict) -> None:
        """prompt_template path matches expected prompt file."""
        impl_review = stages_config["stages"]["IMPLEMENTATION_REVIEW"]
        expected = ".agent/commands/sdd/sdd.7b-implementation-review.prompt.md"
        assert impl_review.get("prompt_template") == expected
```

## Success Criteria

### Test Implementation Complete When:
* [ ] Prompt file exists at `.agent/commands/sdd/sdd.7b-implementation-review.prompt.md`
* [ ] Prompt has valid YAML frontmatter (description, agent, tools)
* [ ] Prompt contains Pre-Code-Review Checklist section
* [ ] Prompt contains Rejection Format template
* [ ] Prompt contains Approval Format template
* [ ] stages.yaml line 326 references prompt path
* [ ] All existing tests pass (`uv run pytest`)
* [ ] Linting passes (`uv run ruff check .` and `uv run ruff format --check .`)

### Test Quality Indicators:
* Validation tests verify structural requirements
* Tests are simple and deterministic
* No mocking required (validating static files)
* Clear assertion messages indicate failures

## Implementation Guidance

### For Code-First Components (All):
1. Author the prompt file following specification Section 6
2. Update stages.yaml to reference the prompt
3. Run validation tests to confirm structure
4. Run existing test suite to confirm no regressions
5. Run linting to ensure code quality

### Test File Organization:
```
tests/
├── test_implementation_review_prompt.py  # Optional validation tests
└── test_stages_yaml_acceptance.py        # Existing (may extend)
```

### Manual Testing Approach:
Since this is a prompt-only feature, functional testing happens via workflow execution:
1. Create a test objective with incomplete plan
2. Run TeamBot through IMPLEMENTATION stage
3. Verify IMPLEMENTATION_REVIEW triggers rejection
4. Complete tasks and re-run
5. Verify IMPLEMENTATION_REVIEW proceeds to code review

## Considerations and Trade-offs

### Selected Approach Benefits:
* Fast implementation — no test overhead for prompt authoring
* Validation tests confirm structural requirements
* Existing test suite validates no regressions
* Prompt quality is validated through workflow execution

### Accepted Trade-offs:
* No unit tests for prompt logic (prompt execution is not testable)
* Functional validation requires manual workflow execution
* Prompt effectiveness can only be measured through actual agent behavior

### Risk Mitigation:
* **Prompt structure errors**: Validation tests catch missing sections
* **YAML syntax errors**: Python yaml parser catches during test
* **Regressions**: Full existing test suite runs after changes

## References

* **Feature Spec**: [.teambot/implementation-review-completion/artifacts/feature_spec.md]
* **Spec Review**: [.teambot/implementation-review-completion/artifacts/spec_review.md]
* **Test Examples**: `tests/test_stages_yaml_acceptance.py`
* **Test Standards**: `pyproject.toml` [tool.pytest.ini_options]

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate Code-First sequence into implementation phases
4. 🔍 Implementation will author prompt first, then validate

---

**Strategy Status**: DRAFT
**Approved By**: PENDING
**Ready for Planning**: YES

---

## 🔐 Approval Request

I have completed the test strategy analysis for **Implementation Review Completion Check**.

**Summary:**
- **Approach**: CODE_FIRST (TDD Score: 4, Code-First Score: 4, but no code to TDD)
- **Coverage Target**: 100% validation of structural requirements
- **Components**: 3 (prompt file, stages.yaml, validation tests)
- **Critical Scenarios**: 6
- **Key Insight**: Prompt-only feature — no application code to unit test

**Decision: CODE_FIRST for all components**

This feature creates a Markdown prompt file and updates one line in stages.yaml. There is no application code to TDD. Testing focuses on validating that deliverables meet structural requirements.

### ✅ Ready for Task Planning

Please confirm:

- [ ] I have reviewed the test strategy
- [ ] I agree with the Code-First approach for this prompt-only feature
- [ ] I approve proceeding to Task Planning phase

**Type "APPROVED" to proceed, or describe any concerns.**

---

## Validation Checklist

```
TEST_STRATEGY_VALIDATION: PASS
- Document: CREATED
- Decision Matrix: COMPLETE (TDD: 4, Code-First: 4, deciding factor: no code)
- Approach: CODE_FIRST (prompt-only implementation)
- Coverage Targets: SPECIFIED (100% validation of structural requirements)
- Components Covered: 3/3
```
