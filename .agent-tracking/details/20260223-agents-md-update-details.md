<!-- markdownlint-disable-file -->
# Task Details: AGENTS.md Objective Template Reference Update

## Research Reference

**Source Research**: .teambot/pseudocode/artifacts/research.md
**Test Strategy**: .teambot/pseudocode/artifacts/test_strategy.md

---

## Phase 1: TDD Unit Tests

### Task 1.1: Create unit test file structure

Create the test file with proper imports, fixtures, and class structure.

* **Files**:
  * `tests/test_agents_md_update.py` - New unit test file for AGENTS.md update logic
* **Success**:
  * File exists with proper pytest imports
  * Fixtures defined for test data
  * Test classes organized by function
* **Research References**:
  * .teambot/pseudocode/artifacts/research.md (Lines 55-86) - Test infrastructure patterns
  * .teambot/pseudocode/artifacts/test_strategy.md (Lines 245-278) - Fixture examples
* **Dependencies**:
  * None

**Implementation Guidance**:
```python
"""Tests for AGENTS.md update functionality in teambot init."""
import pytest
from pathlib import Path
from teambot.scaffolds import CopyResult


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

TeamBot provides an objective template for defining development tasks:

| File | Description |
|------|-------------|
| `docs/sdd-objective-template.md` | Template for creating TeamBot objectives. |
"""


@pytest.fixture
def empty_agents_md():
    """Empty AGENTS.md file."""
    return ""
```

---

### Task 1.2: Write `_agents_md_has_template_reference()` tests

Write tests for the detection function that checks if AGENTS.md already has the template reference.

* **Files**:
  * `tests/test_agents_md_update.py` - Add `TestAgentsMdHasTemplateReference` class
* **Success**:
  * Tests cover: has reference, no reference, empty file, case variations
  * All tests initially fail (no implementation)
* **Research References**:
  * .teambot/pseudocode/artifacts/research.md (Lines 299-306) - Detection logic specification
  * .teambot/pseudocode/artifacts/test_strategy.md (Lines 324-338) - Test patterns
* **Dependencies**:
  * Task 1.1 completion

**Test Cases**:
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

    def test_returns_false_when_no_reference(self, tmp_path, agents_md_without_reference):
        """Returns False when AGENTS.md lacks the reference section."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_without_reference)
        
        from teambot.cli import _agents_md_has_template_reference
        result = _agents_md_has_template_reference(agents_md)
        
        assert result is False

    def test_returns_false_for_empty_file(self, tmp_path):
        """Returns False for empty AGENTS.md."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("")
        
        from teambot.cli import _agents_md_has_template_reference
        result = _agents_md_has_template_reference(agents_md)
        
        assert result is False
```

---

### Task 1.3: Write `_should_update_agents_md()` tests

Write tests for the trigger condition function that checks CopyResult list.

* **Files**:
  * `tests/test_agents_md_update.py` - Add `TestShouldUpdateAgentsMd` class
* **Success**:
  * Tests cover all combinations: template copied + agents skipped, template not copied, agents copied
  * All tests initially fail
* **Research References**:
  * .teambot/pseudocode/artifacts/research.md (Lines 351-380) - Trigger logic and edge cases
* **Dependencies**:
  * Task 1.2 completion

**Test Cases**:
```python
class TestShouldUpdateAgentsMd:
    """Tests for _should_update_agents_md() function."""

    def test_returns_true_when_template_copied_and_agents_skipped(self):
        """Returns True when template copied AND AGENTS.md skipped."""
        from teambot.cli import _should_update_agents_md
        
        results = [
            CopyResult("sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]
        
        assert _should_update_agents_md(results) is True

    def test_returns_false_when_template_not_copied(self):
        """Returns False when template was not copied (already exists)."""
        from teambot.cli import _should_update_agents_md
        
        results = [
            CopyResult("sdd-objective-template.md", Path("docs/sdd-objective-template.md"), False, "skipped_exists"),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]
        
        assert _should_update_agents_md(results) is False

    def test_returns_false_when_agents_freshly_copied(self):
        """Returns False when AGENTS.md was freshly copied (has reference)."""
        from teambot.cli import _should_update_agents_md
        
        results = [
            CopyResult("sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"),
            CopyResult("AGENTS.md", Path("AGENTS.md"), True, "copied"),
        ]
        
        assert _should_update_agents_md(results) is False
```

---

### Task 1.4: Write `_update_agents_md_with_template_reference()` tests

Write tests for the main update function.

* **Files**:
  * `tests/test_agents_md_update.py` - Add `TestUpdateAgentsMdWithTemplateReference` class
* **Success**:
  * Tests cover: successful append, reference already exists (skip), content preservation
  * All tests initially fail
* **Research References**:
  * .teambot/pseudocode/artifacts/research.md (Lines 250-278) - Function signature and behavior
  * .teambot/pseudocode/artifacts/test_strategy.md (Lines 339-369) - Test patterns
* **Dependencies**:
  * Task 1.3 completion

**Test Cases**:
```python
class TestUpdateAgentsMdWithTemplateReference:
    """Tests for _update_agents_md_with_template_reference() function."""

    def test_appends_reference_when_conditions_met(self, tmp_path, agents_md_without_reference):
        """Appends reference section when all conditions are met."""
        from teambot.cli import _update_agents_md_with_template_reference
        from teambot.scaffolds import CopyResult
        
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_without_reference)
        
        results = [
            CopyResult("sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]
        
        updated = _update_agents_md_with_template_reference(results, tmp_path, display=None)
        
        assert updated is True
        content = agents_md.read_text()
        assert "## Objective Template" in content
        assert "docs/sdd-objective-template.md" in content

    def test_skips_when_reference_exists(self, tmp_path, agents_md_with_reference):
        """Skips update when reference already exists."""
        from teambot.cli import _update_agents_md_with_template_reference
        from teambot.scaffolds import CopyResult
        
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_with_reference)
        original_content = agents_md.read_text()
        
        results = [
            CopyResult("sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]
        
        updated = _update_agents_md_with_template_reference(results, tmp_path, display=None)
        
        assert updated is False
        assert agents_md.read_text() == original_content

    def test_preserves_existing_content_exactly(self, tmp_path, agents_md_without_reference):
        """Original content is preserved exactly after update."""
        from teambot.cli import _update_agents_md_with_template_reference
        from teambot.scaffolds import CopyResult
        
        agents_md = tmp_path / "AGENTS.md"
        original = "# AGENTS\n\n## Section 1\n\nContent with special chars: 日本語\n"
        agents_md.write_text(original)
        
        results = [
            CopyResult("sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]
        
        _update_agents_md_with_template_reference(results, tmp_path, display=None)
        
        content = agents_md.read_text()
        assert content.startswith(original.rstrip("\n"))
```

---

### Task 1.5: Write idempotency tests

Write tests verifying no duplicate sections on multiple runs.

* **Files**:
  * `tests/test_agents_md_update.py` - Add to existing test class
* **Success**:
  * Tests verify exactly one reference section after multiple calls
* **Research References**:
  * .teambot/pseudocode/artifacts/test_strategy.md (Lines 186-193) - Idempotency requirements
* **Dependencies**:
  * Task 1.4 completion

**Test Cases**:
```python
    def test_idempotent_multiple_runs(self, tmp_path, agents_md_without_reference):
        """Running update multiple times produces exactly one reference."""
        from teambot.cli import _update_agents_md_with_template_reference
        from teambot.scaffolds import CopyResult
        
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text(agents_md_without_reference)
        
        results = [
            CopyResult("sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]
        
        # Run multiple times
        _update_agents_md_with_template_reference(results, tmp_path, display=None)
        _update_agents_md_with_template_reference(results, tmp_path, display=None)
        _update_agents_md_with_template_reference(results, tmp_path, display=None)
        
        content = agents_md.read_text()
        count = content.count("## Objective Template")
        assert count == 1, f"Expected 1 reference, found {count}"
```

---

### Task 1.6: Write edge case tests

Write tests for edge cases: empty file, whitespace-only, no trailing newline.

* **Files**:
  * `tests/test_agents_md_update.py` - Add edge case tests
* **Success**:
  * Tests cover empty, whitespace-only, no trailing newline scenarios
* **Research References**:
  * .teambot/pseudocode/artifacts/test_strategy.md (Lines 216-223) - Edge case list
* **Dependencies**:
  * Task 1.5 completion

**Test Cases**:
```python
    def test_handles_empty_file(self, tmp_path):
        """Appends reference to empty AGENTS.md."""
        from teambot.cli import _update_agents_md_with_template_reference
        from teambot.scaffolds import CopyResult
        
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("")
        
        results = [
            CopyResult("sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]
        
        updated = _update_agents_md_with_template_reference(results, tmp_path, display=None)
        
        assert updated is True
        content = agents_md.read_text()
        assert "## Objective Template" in content

    def test_handles_no_trailing_newline(self, tmp_path):
        """Handles AGENTS.md without trailing newline."""
        from teambot.cli import _update_agents_md_with_template_reference
        from teambot.scaffolds import CopyResult
        
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# AGENTS\n\nSome content")  # No trailing newline
        
        results = [
            CopyResult("sdd-objective-template.md", Path("docs/sdd-objective-template.md"), True, "copied"),
            CopyResult("AGENTS.md", Path("AGENTS.md"), False, "skipped_exists"),
        ]
        
        _update_agents_md_with_template_reference(results, tmp_path, display=None)
        
        content = agents_md.read_text()
        # Should have proper separation
        assert "\n\n## Objective Template" in content or content.startswith("## Objective Template")
```

---

## Phase 2: Core Implementation

### Task 2.1: Add constants for section content and marker

Add module-level constants for the template reference section content and detection marker.

* **Files**:
  * `src/teambot/cli.py` - Add constants near top of file (after imports, before functions)
* **Success**:
  * Constants defined: `OBJECTIVE_TEMPLATE_SECTION`, `OBJECTIVE_TEMPLATE_MARKER`
  * Constants match bundled AGENTS.md content
* **Research References**:
  * .teambot/pseudocode/artifacts/research.md (Lines 300-320) - Section content specification
* **Dependencies**:
  * Phase 1 completion

**Implementation**:
```python
# Constants for AGENTS.md template reference update
OBJECTIVE_TEMPLATE_MARKER = "## Objective Template"

OBJECTIVE_TEMPLATE_SECTION = """
## Objective Template

TeamBot provides an objective template for defining development tasks:

| File | Description |
|------|-------------|
| `docs/sdd-objective-template.md` | Template for creating TeamBot objectives. Copy this file and fill in the sections to define your development task. Run with `teambot run objectives/my-objective.md`. |
"""
```

---

### Task 2.2: Implement `_agents_md_has_template_reference()` function

Implement the detection function that checks if AGENTS.md contains the reference.

* **Files**:
  * `src/teambot/cli.py` - Add function after constants
* **Success**:
  * Function correctly detects presence/absence of marker
  * Tests in `TestAgentsMdHasTemplateReference` pass
* **Research References**:
  * .teambot/pseudocode/artifacts/research.md (Lines 302-306) - Detection logic
* **Dependencies**:
  * Task 2.1 completion

**Implementation**:
```python
def _agents_md_has_template_reference(agents_md_path: Path) -> bool:
    """Check if AGENTS.md already has the objective template reference.
    
    Args:
        agents_md_path: Path to AGENTS.md file
        
    Returns:
        True if the template reference section exists, False otherwise
    """
    try:
        content = agents_md_path.read_text(encoding="utf-8")
        return OBJECTIVE_TEMPLATE_MARKER in content
    except (OSError, IOError):
        return False
```

---

### Task 2.3: Implement `_should_update_agents_md()` function

Implement the trigger condition function that evaluates CopyResult list.

* **Files**:
  * `src/teambot/cli.py` - Add function after detection function
* **Success**:
  * Function correctly evaluates trigger conditions
  * Tests in `TestShouldUpdateAgentsMd` pass
* **Research References**:
  * .teambot/pseudocode/artifacts/research.md (Lines 351-371) - Trigger logic specification
* **Dependencies**:
  * Task 2.2 completion

**Implementation**:
```python
def _should_update_agents_md(results: list) -> bool:
    """Determine if AGENTS.md should be updated with template reference.
    
    Update is triggered when:
    1. sdd-objective-template.md was successfully copied (newly added)
    2. AGENTS.md exists but was skipped (not overwritten)
    
    Args:
        results: List of CopyResult from scaffold copying
        
    Returns:
        True if AGENTS.md should be updated
    """
    template_copied = False
    agents_md_skipped = False
    
    for result in results:
        if result.source == "sdd-objective-template.md" and result.copied:
            template_copied = True
        if result.source == "AGENTS.md" and result.reason == "skipped_exists":
            agents_md_skipped = True
    
    return template_copied and agents_md_skipped
```

---

### Task 2.4: Implement `_update_agents_md_with_template_reference()` function

Implement the main update function that appends the template reference section.

* **Files**:
  * `src/teambot/cli.py` - Add main function
* **Success**:
  * Function appends section when conditions met
  * Function preserves existing content
  * Function is idempotent
  * All unit tests pass
* **Research References**:
  * .teambot/pseudocode/artifacts/research.md (Lines 250-278) - Function specification
  * .teambot/pseudocode/artifacts/research.md (Lines 322-331) - Update logic
* **Dependencies**:
  * Task 2.3 completion

**Implementation**:
```python
def _update_agents_md_with_template_reference(
    results: list,
    target_root: Path,
    display,
) -> bool:
    """Update AGENTS.md with objective template reference if needed.
    
    Only updates if:
    1. AGENTS.md exists but was skipped (not force-overwritten)
    2. sdd-objective-template.md was successfully copied
    3. AGENTS.md doesn't already have the template reference
    
    Args:
        results: Copy results from scaffold operation
        target_root: Root directory (typically Path.cwd())
        display: Console display for user feedback (can be None)
        
    Returns:
        True if AGENTS.md was updated, False if skipped
    """
    if not _should_update_agents_md(results):
        return False
    
    agents_md_path = target_root / "AGENTS.md"
    
    if not agents_md_path.exists():
        return False
    
    if _agents_md_has_template_reference(agents_md_path):
        if display:
            display.print_info("  AGENTS.md already has objective template reference")
        return False
    
    try:
        content = agents_md_path.read_text(encoding="utf-8")
        # Ensure proper newline separation
        if content and not content.endswith("\n"):
            content += "\n"
        content += OBJECTIVE_TEMPLATE_SECTION.strip() + "\n"
        agents_md_path.write_text(content, encoding="utf-8")
        
        if display:
            display.print_success("  Updated AGENTS.md with objective template reference")
        return True
    except (OSError, IOError) as e:
        logging.debug(f"Failed to update AGENTS.md: {e}")
        return False
```

---

## Phase 3: CLI Integration

### Task 3.1: Integrate `_update_agents_md_with_template_reference()` into `cmd_init()`

Call the update function in `cmd_init()` after the scaffold copy loop.

* **Files**:
  * `src/teambot/cli.py` - Modify `cmd_init()` function (after Line ~431)
* **Success**:
  * Update function called after scaffold results loop
  * Integration point is after display of copy results
* **Research References**:
  * .teambot/pseudocode/artifacts/research.md (Lines 274-278) - Integration point
  * .teambot/pseudocode/artifacts/research.md (Lines 164-172) - Post-processing pattern
* **Dependencies**:
  * Phase 2 completion

**Integration Location** (after scaffold result display loop):
```python
    # Existing code ends around Line 431
    
    # Update AGENTS.md with template reference if applicable
    _update_agents_md_with_template_reference(results, Path.cwd(), display)
```

---

### Task 3.2: Add display messages for update/skip scenarios

Ensure appropriate user feedback is displayed.

* **Files**:
  * `src/teambot/cli.py` - Messages already in function, verify display passed
* **Success**:
  * Success message shown when AGENTS.md updated
  * Info message shown when reference already exists
  * No message when update not triggered
* **Research References**:
  * .teambot/pseudocode/artifacts/research.md (Lines 164-172) - Display pattern
* **Dependencies**:
  * Task 3.1 completion

**Verification**: Ensure `display` parameter is passed correctly from `cmd_init()`:
```python
_update_agents_md_with_template_reference(results, Path.cwd(), display)
```

---

## Phase 4: Acceptance Tests and Validation

### Task 4.1: Write acceptance tests for AGENTS.md update scenarios

Write acceptance tests covering end-to-end scenarios.

* **Files**:
  * `tests/test_agents_md_update_acceptance.py` - New acceptance test file
* **Success**:
  * AT-001: Template copied + existing AGENTS.md → section appended
  * AT-002: Re-run → no duplicate section
  * AT-003: Force init → no update needed (bundled has section)
  * AT-004: Template already exists → no update triggered
* **Research References**:
  * .teambot/pseudocode/artifacts/research.md (Lines 423-430) - Acceptance test scenarios
  * .teambot/pseudocode/artifacts/test_strategy.md (Lines 420-425) - Test organization
* **Dependencies**:
  * Phase 3 completion

**Acceptance Test Structure**:
```python
"""Acceptance tests for AGENTS.md objective template reference update.

Core logic is tested directly; selective mocking is used for external dependencies.
"""
import pytest
from pathlib import Path
import argparse


@pytest.mark.acceptance
class TestAgentsMdUpdateAcceptance:
    """Acceptance tests for AGENTS.md update during teambot init."""

    def test_at_001_appends_reference_when_template_copied_to_existing_agents(
        self, tmp_path, monkeypatch
    ):
        """AT-001: Section appended when template newly copied and AGENTS.md exists."""
        # Arrange: Create existing AGENTS.md without reference
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n\n## Development\n")
        (tmp_path / "docs").mkdir()
        
        # Act: Run init
        from teambot.cli import cmd_init
        args = argparse.Namespace(force=False)
        cmd_init(args)
        
        # Assert: Reference added
        content = agents_md.read_text()
        assert "## Objective Template" in content
        assert "docs/sdd-objective-template.md" in content

    def test_at_002_no_duplicate_on_rerun(self, tmp_path, monkeypatch):
        """AT-002: Running init twice produces exactly one reference."""
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n")
        (tmp_path / "docs").mkdir()
        
        from teambot.cli import cmd_init
        args = argparse.Namespace(force=False)
        
        # Run twice
        cmd_init(args)
        cmd_init(args)
        
        content = agents_md.read_text()
        count = content.count("## Objective Template")
        assert count == 1
```

---

### Task 4.2: Validate overall test coverage and quality

Run full test suite and verify coverage targets.

* **Files**:
  * No new files - validation only
* **Success**:
  * All tests pass: `uv run pytest -v`
  * Coverage ≥95% for new code
  * Lint passes: `uv run ruff check . && uv run ruff format --check .`
* **Research References**:
  * .teambot/pseudocode/artifacts/test_strategy.md (Lines 162-175) - Coverage targets
* **Dependencies**:
  * Task 4.1 completion

**Validation Commands**:
```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/teambot/cli --cov-report=term-missing tests/test_agents_md_update.py tests/test_agents_md_update_acceptance.py

# Lint check
uv run ruff check .
uv run ruff format --check .
```

---

## Dependencies

* pytest 7.4.0+
* pytest-cov
* pytest-mock
* `tmp_path` pytest fixture

## Success Criteria

* All unit tests pass with 95%+ coverage for new functions
* All acceptance tests pass
* Existing tests unaffected
* Lint checks pass
* `teambot init` correctly updates AGENTS.md when conditions met
* Idempotent behavior verified
