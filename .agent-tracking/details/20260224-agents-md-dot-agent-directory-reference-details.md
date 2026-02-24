<!-- markdownlint-disable-file -->
# Task Details: AGENTS.md `.agent` Directory Reference Update

## Research Reference

**Source Research**: .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md

---

## Phase 1: Unit Tests (TDD)

### Task 1.1: Write tests for `_agents_md_has_agent_directory_reference()`

Write unit tests for the detection function that checks if AGENTS.md already contains the `.agent` directory reference section.

* **Files**:
  * `tests/test_agents_md_update.py` - Extend with new test class `TestAgentsMdHasAgentDirectoryReference`

* **Test Cases**:
  1. `test_returns_true_when_reference_exists` - Marker "## Copilot / AI Assisted Workflow" present
  2. `test_returns_false_when_no_reference` - Marker absent
  3. `test_returns_false_for_empty_file` - Empty AGENTS.md
  4. `test_returns_false_for_missing_file` - File doesn't exist
  5. `test_case_insensitive_detection` - Marker with different casing (e.g., "## copilot / ai assisted workflow")

* **Test Pattern** (from research Lines 426-449):
```python
class TestAgentsMdHasAgentDirectoryReference:
    """Tests for _agents_md_has_agent_directory_reference() function."""

    def test_returns_true_when_reference_exists(self, tmp_path):
        """Returns True when AGENTS.md contains the .agent directory reference."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# Project\n\n## Copilot / AI Assisted Workflow\n\nContent here.")

        from teambot.cli import _agents_md_has_agent_directory_reference

        result = _agents_md_has_agent_directory_reference(agents_md)

        assert result is True
```

* **Success**:
  * All 5 test cases written
  * Tests fail with ImportError (function doesn't exist yet) - expected for TDD
* **Research References**:
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 426-449) - Test pattern
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 528-535) - Required test cases
* **Dependencies**:
  * None

---

### Task 1.2: Write tests for `_should_update_agents_md_with_agent_directory()`

Write unit tests for the trigger condition function.

* **Files**:
  * `tests/test_agents_md_update.py` - Add test class `TestShouldUpdateAgentsMdWithAgentDirectory`

* **Test Cases**:
  1. `test_returns_true_when_agent_dir_copied_and_agents_skipped` - Trigger condition met
  2. `test_returns_false_when_agent_dir_not_copied` - `.agent` already existed
  3. `test_returns_false_when_agents_freshly_copied` - AGENTS.md was just copied (not skipped)
  4. `test_returns_false_when_agent_dir_skipped_not_empty` - `.agent` had content (skipped_not_empty)
  5. `test_handles_empty_results_list` - Edge case with empty list

* **Test Pattern** (from research Lines 325-339):
```python
class TestShouldUpdateAgentsMdWithAgentDirectory:
    """Tests for _should_update_agents_md_with_agent_directory() function."""

    def test_returns_true_when_agent_dir_copied_and_agents_skipped(self, tmp_path):
        """Returns True when .agent copied and AGENTS.md skipped."""
        from teambot.scaffolds import CopyResult
        from teambot.cli import _should_update_agents_md_with_agent_directory

        results = [
            CopyResult(source=".agent", target=tmp_path / ".agent", copied=True, reason="copied"),
            CopyResult(source="AGENTS.md", target=tmp_path / "AGENTS.md", copied=False, reason="skipped_exists"),
        ]

        result = _should_update_agents_md_with_agent_directory(results)

        assert result is True
```

* **Success**:
  * All 5 test cases written
  * Tests fail with ImportError (function doesn't exist yet)
* **Research References**:
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 325-339) - Existing pattern
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 536-541) - Required test cases
* **Dependencies**:
  * None

---

### Task 1.3: Write tests for `_update_agents_md_with_agent_directory_reference()`

Write unit tests for the main update function.

* **Files**:
  * `tests/test_agents_md_update.py` - Add test class `TestUpdateAgentsMdWithAgentDirectoryReference`

* **Test Cases**:
  1. `test_appends_reference_when_conditions_met` - Happy path
  2. `test_skips_when_reference_exists` - Idempotent behavior
  3. `test_preserves_existing_content_exactly` - Non-destructive
  4. `test_returns_false_when_conditions_not_met` - Preconditions check
  5. `test_idempotent_multiple_runs` - Safe to re-run
  6. `test_handles_empty_file` - Edge case
  7. `test_handles_no_trailing_newline` - Edge case
  8. `test_handles_permission_error` - Graceful error handling

* **Test Pattern** (from research Lines 349-383):
```python
class TestUpdateAgentsMdWithAgentDirectoryReference:
    """Tests for _update_agents_md_with_agent_directory_reference() function."""

    def test_appends_reference_when_conditions_met(self, tmp_path):
        """Appends .agent directory reference when all conditions are met."""
        from teambot.scaffolds import CopyResult
        from teambot.cli import (
            _update_agents_md_with_agent_directory_reference,
            AGENT_DIRECTORY_MARKER,
        )

        # Arrange
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n\n## Development\n")
        results = [
            CopyResult(source=".agent", target=tmp_path / ".agent", copied=True, reason="copied"),
            CopyResult(source="AGENTS.md", target=tmp_path / "AGENTS.md", copied=False, reason="skipped_exists"),
        ]

        # Act
        result = _update_agents_md_with_agent_directory_reference(results, tmp_path, None)

        # Assert
        assert result is True
        content = agents_md.read_text()
        assert AGENT_DIRECTORY_MARKER in content
        assert "# My Project" in content  # Original content preserved
```

* **Success**:
  * All 8 test cases written
  * Tests fail with ImportError (function doesn't exist yet)
* **Research References**:
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 349-383) - Existing pattern
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 542-551) - Required test cases
* **Dependencies**:
  * None

---

## Phase 2: Implementation

### Task 2.1: Add `AGENT_DIRECTORY_MARKER` and `AGENT_DIRECTORY_SECTION` constants

Add constants to `cli.py` for the `.agent` directory reference section.

* **Files**:
  * `src/teambot/cli.py` - Add constants after line 45 (after `OBJECTIVE_TEMPLATE_SECTION`)

* **Implementation**:
```python
# Constants for AGENTS.md .agent directory reference update
AGENT_DIRECTORY_MARKER = "## Copilot / AI Assisted Workflow"

AGENT_DIRECTORY_SECTION = """
## Copilot / AI Assisted Workflow

- All Copilot and AI assisted workflows exist in the `.agent/` directory
- SDD (Spec-Driven Development) workflow in `.agent/commands/sdd/`
- Artifacts tracked in `.agent-tracking/`

### `.agent` directory structure

The `.agent` directory contains commands, instructions, and standards used by AI-assisted workflows.

#### Commands (`commands/`)

Prompt files invoked as slash commands (e.g. `/sdd:0-initialize`).

| Path | Description |
|------|-------------|
| `commands/azdo/azdo.generate-pr-description.prompt.md` | Generates pull request descriptions using Azure DevOps templates. |
| `commands/docs/docs.create-adr.prompt.md` | Creates architecture decision records following organisational standards. |
| `commands/project/proj.sprint-planning.prompt.md` | Builds sprint plans for software engineering teams to deliver implementation engagements. |
| `commands/setup/setup.agents-md-creation.prompt.md` | Generates or updates the `AGENTS.md` file for the repository. |

**Spec-Driven Development (SDD) workflow** (`commands/sdd/`)

A sequential workflow with quality gates for taking a feature from specification through to implementation.

| Path | Description |
|------|-------------|
| `commands/sdd/README.md` | Documents the SDD workflow overview and its 9 sequential steps. |
| `commands/sdd/sdd.0-initialize.prompt.md` | Initialises the SDD workflow by verifying prerequisites and creating tracking directories. |
| `commands/sdd/sdd.1-create-feature-spec.prompt.md` | Guides creation of feature specifications with Q&A and reference integration. |
| `commands/sdd/sdd.2-review-spec.prompt.md` | Reviews and validates specifications before the research phase. |
| `commands/sdd/sdd.3-research-feature.prompt.md` | Conducts comprehensive research and analysis for the feature. |
| `commands/sdd/sdd.4-determine-test-strategy.prompt.md` | Analyses specs and research to recommend an optimal testing strategy. |
| `commands/sdd/sdd.5-task-planner-for-feature.prompt.md` | Creates actionable implementation plans for the feature. |
| `commands/sdd/sdd.6-review-plan.prompt.md` | Reviews and validates implementation plans before execution. |
| `commands/sdd/sdd.7-task-implementer-for-feature.prompt.md` | Implements task plans with progressive tracking and change records. |
| `commands/sdd/sdd.8-post-implementation-review.prompt.md` | Performs post-implementation review and final validation. |

#### Instructions (`instructions/`)

Contextual guidelines automatically applied to AI interactions.

| Path | Description |
|------|-------------|
| `instructions/prompt.instructions.md` | Guidelines for creating high-quality prompt files for GitHub Copilot. |
| `instructions/bash/bash.instructions.md` | Instructions for bash script implementation with established conventions. |
| `instructions/bash/bash.md` | Guidelines for secure, maintainable bash scripting practices. |
| `instructions/bicep/bicep-standards.md` | Coding standards and best practices for Bicep Infrastructure as Code. |
| `instructions/bicep/bicep.instructions.md` | Instructions for Bicep infrastructure implementation. |
| `instructions/bicep/bicep.md` | Structural guidelines for Bicep development. |

#### Standards (`standards/`)

Templates and standards referenced by commands and instructions.

| Path | Description |
|------|-------------|
| `standards/decision-record-standards.md` | Standards for creating decision records capturing architectural and policy decisions. |
| `standards/decision-record-template.md` | Template for decision records with status, deciders, context, and consequences. |
| `standards/feature-spec-template.md` | Template for feature specification documents with progress tracking. |
| `standards/research-feature-template.md` | Template for task research documents with implementation analysis. |
| `standards/task-planning-template.md` | Template for task checklists with overview and implementation instructions. |
"""
```

* **Success**:
  * Constants added after existing `OBJECTIVE_TEMPLATE_SECTION`
  * Constants exported from module (usable in tests)
* **Research References**:
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 89-160) - Full constant content
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 274-295) - Pattern from existing constants
* **Dependencies**:
  * None

---

### Task 2.2: Implement `_agents_md_has_agent_directory_reference()` function

Implement the detection function following existing pattern.

* **Files**:
  * `src/teambot/cli.py` - Add function after `_agents_md_has_template_reference()` (around line 62)

* **Implementation**:
```python
def _agents_md_has_agent_directory_reference(agents_md_path: Path) -> bool:
    """Check if AGENTS.md already has the .agent directory reference.

    Args:
        agents_md_path: Path to AGENTS.md file

    Returns:
        True if the .agent directory section exists, False otherwise
    """
    try:
        content = agents_md_path.read_text(encoding="utf-8")
        # Case-insensitive check to avoid duplicate sections if heading casing differs
        return AGENT_DIRECTORY_MARKER.casefold() in content.casefold()
    except OSError:
        return False
```

* **Success**:
  * Function exists and is importable
  * All Task 1.1 tests pass
* **Research References**:
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 165-180) - Function implementation
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 302-315) - Existing pattern
* **Dependencies**:
  * Task 2.1 (needs `AGENT_DIRECTORY_MARKER` constant)

---

### Task 2.3: Implement `_should_update_agents_md_with_agent_directory()` function

Implement the trigger condition function.

* **Files**:
  * `src/teambot/cli.py` - Add function after `_should_update_agents_md()` (around line 87)

* **Implementation**:
```python
def _should_update_agents_md_with_agent_directory(results: list[CopyResult]) -> bool:
    """Determine if AGENTS.md should be updated with .agent directory reference.

    Update is triggered when:
    1. .agent directory was successfully copied (newly added)
    2. AGENTS.md exists but was skipped (not overwritten)

    Args:
        results: List of CopyResult from scaffold copying

    Returns:
        True if AGENTS.md should be updated
    """
    agent_dir_copied = False
    agents_md_skipped = False

    for result in results:
        if result.source == ".agent" and result.copied:
            agent_dir_copied = True
        if result.source == "AGENTS.md" and result.reason == "skipped_exists":
            agents_md_skipped = True

    return agent_dir_copied and agents_md_skipped
```

* **Success**:
  * Function exists and is importable
  * All Task 1.2 tests pass
* **Research References**:
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 184-208) - Function implementation
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 325-339) - Existing pattern
* **Dependencies**:
  * Task 2.2

---

### Task 2.4: Implement `_update_agents_md_with_agent_directory_reference()` function

Implement the main update function.

* **Files**:
  * `src/teambot/cli.py` - Add function after `_update_agents_md_with_template_reference()` (around line 136)

* **Implementation**:
```python
def _update_agents_md_with_agent_directory_reference(
    results: list[CopyResult],
    target_root: Path,
    display: ConsoleDisplay | None,
) -> bool:
    """Update AGENTS.md with .agent directory reference if needed.

    Only updates if:
    1. AGENTS.md exists but was skipped (not force-overwritten)
    2. .agent directory was successfully copied
    3. AGENTS.md doesn't already have the .agent directory reference

    Args:
        results: Copy results from scaffold operation
        target_root: Root directory (typically Path.cwd())
        display: Console display for user feedback (can be None)

    Returns:
        True if AGENTS.md was updated, False if skipped
    """
    if not _should_update_agents_md_with_agent_directory(results):
        return False

    agents_md_path = target_root / "AGENTS.md"

    if not agents_md_path.exists():
        return False

    if _agents_md_has_agent_directory_reference(agents_md_path):
        if display:
            display.print_info("  AGENTS.md already has .agent directory reference")
        return False

    try:
        content = agents_md_path.read_text(encoding="utf-8")
        # Ensure proper newline separation
        if content and not content.endswith("\n"):
            content += "\n"
        content += AGENT_DIRECTORY_SECTION.strip() + "\n"
        agents_md_path.write_text(content, encoding="utf-8")

        if display:
            display.print_success("  Updated AGENTS.md with .agent directory reference")
        return True
    except OSError as e:
        logging.debug(f"Failed to update AGENTS.md with .agent reference: {e}")
        return False
```

* **Success**:
  * Function exists and is importable
  * All Task 1.3 tests pass
* **Research References**:
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 213-260) - Function implementation
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 349-383) - Existing pattern
* **Dependencies**:
  * Task 2.3

---

### Task 2.5: Integrate in `cmd_init()` function

Add the call to the new update function in `cmd_init()`.

* **Files**:
  * `src/teambot/cli.py` - Add call after existing `_update_agents_md_with_template_reference()` call (around line 555)

* **Implementation**:
```python
# Update AGENTS.md with template reference if applicable
_update_agents_md_with_template_reference(results, Path.cwd(), display)

# Update AGENTS.md with .agent directory reference if applicable
_update_agents_md_with_agent_directory_reference(results, Path.cwd(), display)
```

* **Success**:
  * Call added after existing template reference update
  * `teambot init` triggers the new update function
* **Research References**:
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 262-270) - Integration point
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 42-49) - Code path trace
* **Dependencies**:
  * Task 2.4

---

## Phase 3: Acceptance Tests

### Task 3.1: Write acceptance tests for `.agent` directory reference scenarios

Add end-to-end acceptance tests.

* **Files**:
  * `tests/test_agents_md_update_acceptance.py` - Add new test methods

* **Test Cases**:
  1. `test_at_007_appends_agent_dir_reference_when_newly_copied` - Main scenario: `.agent` newly copied, AGENTS.md exists
  2. `test_at_008_no_agent_dir_reference_when_dir_exists` - Skip when `.agent` already existed
  3. `test_at_009_no_duplicate_agent_dir_reference` - Idempotent on re-run
  4. `test_at_010_both_references_added_on_fresh_existing_agents` - Both template AND `.agent` refs added

* **Test Pattern** (from research Lines 483-507):
```python
@pytest.mark.acceptance
def test_at_007_appends_agent_dir_reference_when_newly_copied(
    self, tmp_path, monkeypatch
):
    """AT-007: .agent directory reference appended when directory newly copied and AGENTS.md exists."""
    import argparse
    from teambot.cli import ConsoleDisplay, cmd_init, AGENT_DIRECTORY_MARKER

    # Arrange
    monkeypatch.chdir(tmp_path)
    agents_md = tmp_path / "AGENTS.md"
    agents_md.write_text("# My Project\n\n## Development\n")
    # Note: .agent directory does NOT exist yet

    # Act
    args = argparse.Namespace(force=False)
    display = ConsoleDisplay()
    result = cmd_init(args, display)

    # Assert
    assert result == 0
    content = agents_md.read_text()
    assert AGENT_DIRECTORY_MARKER in content
    assert "# My Project" in content  # Original content preserved
```

* **Success**:
  * All 4 acceptance test cases written
  * Tests pass: `uv run pytest tests/test_agents_md_update_acceptance.py -v -m acceptance`
* **Research References**:
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 483-507) - Acceptance test pattern
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 553-557) - Required scenarios
* **Dependencies**:
  * Phase 2 completion

---

## Phase 4: Validation

### Task 4.1: Run full test suite

Run the complete test suite to ensure no regressions.

* **Commands**:
```bash
uv run pytest --cov=src/teambot --cov-report=term-missing
```

* **Success**:
  * All tests pass (1050+ existing + new tests)
  * Coverage maintained at 80%+
* **Research References**:
  * .agent-tracking/research/20260224-agents-md-dot-agent-directory-reference-research.md (Lines 409-420) - Test configuration
* **Dependencies**:
  * Phase 3 completion

---

### Task 4.2: Run linting and formatting

Ensure code meets quality standards.

* **Commands**:
```bash
uv run ruff format .
uv run ruff check . --fix
uv run ruff format --check .
```

* **Success**:
  * No lint errors
  * Code formatted correctly
  * `ruff format --check .` passes
* **Research References**:
  * AGENTS.md (Lines 100-102) - Clean commits requirement
* **Dependencies**:
  * Task 4.1

---

## Dependencies

* pytest 7.4.0+ (test framework)
* ruff 0.8.0+ (linter/formatter)
* Existing `_update_agents_md_with_template_reference()` pattern in `cli.py`

## Success Criteria

* All unit tests pass
* All acceptance tests pass
* Full test suite passes with no regressions
* Code passes linting (`uv run ruff check .`)
* Code passes formatting check (`uv run ruff format --check .`)
* `teambot init` correctly updates AGENTS.md when `.agent/` is newly copied
