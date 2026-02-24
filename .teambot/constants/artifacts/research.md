<!-- markdownlint-disable-file -->
# Research: AGENTS.md `.agent` Directory Reference Update

## Document Metadata

| Field | Value |
|-------|-------|
| **Feature** | Update AGENTS.md with `.agent` directory reference during `teambot init` |
| **Date Created** | 2026-02-24 |
| **Status** | ✅ Research Complete |
| **Specification** | `.teambot/constants/artifacts/feature_spec.md` |

## Overview

This research analyzes the implementation approach for enhancing `teambot init` to update existing AGENTS.md files with a reference section describing the `.agent` directory structure when the `.agent/` directory is newly copied.

## Scope and Assumptions

### Scope
- ✅ Detect when AGENTS.md exists AND `.agent/` directory was newly copied
- ✅ Append `.agent` directory reference section from bundled template (Lines 130-191)
- ✅ Prevent duplicate sections (idempotent updates)
- ✅ Handle file permission errors gracefully
- ✅ Follow existing pattern from `_update_agents_md_with_template_reference()`

### Assumptions
- The bundled `src/teambot/scaffolds/AGENTS.md` (Lines 130-191) is the canonical source for section content
- The existing pattern for objective template reference updates provides the architectural blueprint
- The update must be non-destructive and preserve all existing user content

## Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `teambot init` | cli.py:cmd_init() → scaffolds.copy_all_scaffolds() → _update_agents_md_* | YES | YES |
| `teambot init --force` | cli.py:cmd_init() → scaffolds.copy_all_scaffolds() → _update_agents_md_* | YES (no update needed - AGENTS.md replaced) | NO |

### Code Path Trace

#### Entry Point 1: `teambot init` (Normal - `.agent` directory newly copied)
1. User runs: `teambot init`
2. Handled by: `cli.py:cmd_init()` (Line 507)
3. Calls: `scaffolds.copy_all_scaffolds(Path.cwd(), force=force)` (Line 542)
4. Returns: `list[CopyResult]` with results for all scaffold items
5. Currently calls: `_update_agents_md_with_template_reference(results, Path.cwd(), display)` (Line 555)
6. **NEW**: Should also call: `_update_agents_md_with_agent_directory_reference(results, Path.cwd(), display)`
7. Reaches: Feature implementation ✅

#### Entry Point 2: `teambot init --force` (Force mode)
1. User runs: `teambot init --force`
2. Both AGENTS.md and `.agent/` are copied fresh
3. Since AGENTS.md is newly copied from bundled template (which already has the section), no update needed
4. Feature logic: `.agent/` copied=True BUT AGENTS.md copied=True (not skipped) → No update required ✅

#### Entry Point 3: `teambot init` (Re-init - both exist)
1. User runs `teambot init` again (after removing `teambot.json`)
2. AGENTS.md exists → skipped_exists
3. `.agent/` exists and not empty → skipped_not_empty
4. Feature logic: `.agent/` NOT copied → No update required ✅

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| None identified | - | - |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

## Technical Approach

### Recommended Approach: Follow Existing Pattern

The existing implementation for `_update_agents_md_with_template_reference()` provides a complete architectural blueprint. The new feature should mirror this pattern exactly.

**Rationale:**
- ✅ Proven pattern already in codebase (tested with 16+ unit tests)
- ✅ Consistent code style and error handling
- ✅ Well-understood by existing tests
- ✅ Minimal code duplication with constants

### Implementation Components

#### 1. New Constants (cli.py, Lines 30-45 area)

```python
# Constants for AGENTS.md .agent directory reference update
AGENT_DIRECTORY_MARKER = "## Copilot / AI Assisted Workflow"

# Section content extracted from scaffolds/AGENTS.md (Lines 130-191)
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

#### 2. Detection Function (cli.py)

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

#### 3. Trigger Condition Function (cli.py)

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

#### 4. Update Function (cli.py)

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

#### 5. Integration in cmd_init() (cli.py, Line 555 area)

```python
# Update AGENTS.md with template reference if applicable
_update_agents_md_with_template_reference(results, Path.cwd(), display)

# Update AGENTS.md with .agent directory reference if applicable
_update_agents_md_with_agent_directory_reference(results, Path.cwd(), display)
```

## Existing Code Patterns

### Pattern 1: Constants Definition (cli.py, Lines 30-45)

**Source**: `src/teambot/cli.py` (Lines 30-45)

```python
# Constants for AGENTS.md template reference update
OBJECTIVE_TEMPLATE_MARKER = "## Objective Template"

OBJECTIVE_TEMPLATE_SECTION = """
## Objective Template

TeamBot provides an objective template for defining development tasks:

**File**: `docs/sdd-objective-template.md`

Copy this template, fill in the sections, then run:

```bash
teambot run objectives/my-feature.md
```
"""
```

**Key observations:**
- Marker is the section header used for detection
- Section content is the full markdown to append
- Multi-line string with proper formatting

### Pattern 2: Detection Function (cli.py, Lines 48-62)

**Source**: `src/teambot/cli.py` (Lines 48-62)

```python
def _agents_md_has_template_reference(agents_md_path: Path) -> bool:
    """Check if AGENTS.md already has the objective template reference."""
    try:
        content = agents_md_path.read_text(encoding="utf-8")
        # Perform case-insensitive check to avoid duplicate sections
        return OBJECTIVE_TEMPLATE_MARKER.casefold() in content.casefold()
    except OSError:
        return False
```

**Key observations:**
- Case-insensitive check via `.casefold()`
- Returns False on any OSError (graceful handling)
- UTF-8 encoding explicit

### Pattern 3: Trigger Condition Function (cli.py, Lines 65-87)

**Source**: `src/teambot/cli.py` (Lines 65-87)

```python
def _should_update_agents_md(results: list[CopyResult]) -> bool:
    """Determine if AGENTS.md should be updated with template reference."""
    template_copied = False
    agents_md_skipped = False

    for result in results:
        if result.source == "sdd-objective-template.md" and result.copied:
            template_copied = True
        if result.source == "AGENTS.md" and result.reason == "skipped_exists":
            agents_md_skipped = True

    return template_copied and agents_md_skipped
```

**Key observations:**
- Checks two conditions: resource copied AND AGENTS.md skipped
- Iterates through all results
- Uses `result.source` to identify scaffold items

### Pattern 4: Update Function (cli.py, Lines 90-136)

**Source**: `src/teambot/cli.py` (Lines 90-136)

```python
def _update_agents_md_with_template_reference(
    results: list[CopyResult],
    target_root: Path,
    display: ConsoleDisplay | None,
) -> bool:
    """Update AGENTS.md with objective template reference if needed."""
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
        if content and not content.endswith("\n"):
            content += "\n"
        content += OBJECTIVE_TEMPLATE_SECTION.strip() + "\n"
        agents_md_path.write_text(content, encoding="utf-8")

        if display:
            display.print_success("  Updated AGENTS.md with objective template reference")
        return True
    except OSError as e:
        logging.debug(f"Failed to update AGENTS.md: {e}")
        return False
```

**Key observations:**
- Early returns for quick failure
- Handles missing trailing newline
- Uses `logging.debug()` for error reporting (per repository memory)
- `display` can be None (for testing)

### Pattern 5: CopyResult Structure (scaffolds.py, Lines 11-17)

**Source**: `src/teambot/scaffolds.py` (Lines 11-17)

```python
class CopyResult(NamedTuple):
    """Result of a scaffold copy operation."""

    source: str
    target: Path
    copied: bool
    reason: str  # "copied", "skipped_exists", "source_missing", "skipped_not_empty"
```

**Key observations:**
- `source` is the scaffold item name (e.g., ".agent", "AGENTS.md")
- For directories, `reason` can be "skipped_not_empty"

## Testing Strategy Research

### Existing Test Infrastructure

| Aspect | Value |
|--------|-------|
| **Framework** | pytest 7.4.0 |
| **Location** | `tests/` directory |
| **Naming** | `test_*.py` pattern |
| **Runner** | `uv run pytest` |
| **Coverage** | coverage.py (in addopts) |
| **Default Options** | `--cov=src/teambot --cov-report=term-missing -m 'not acceptance'` |
| **Markers** | `acceptance` (excluded by default), `slow` |

### Test Patterns Found

#### Pattern 1: Unit Test Structure (test_agents_md_update.py)

**Source**: `tests/test_agents_md_update.py` (Lines 53-98)

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

**Key observations:**
- Uses `tmp_path` fixture for isolated filesystem
- Imports function inside test (lazy import pattern)
- Clear arrange-act-assert structure
- Descriptive docstrings

#### Pattern 2: Fixtures for Test Content (test_agents_md_update.py)

**Source**: `tests/test_agents_md_update.py` (Lines 12-47)

```python
@pytest.fixture
def agents_md_without_reference():
    """AGENTS.md content without objective template reference."""
    return """# AGENTS.md

## Project Overview
This is a sample project.
"""

@pytest.fixture
def agents_md_with_reference():
    """AGENTS.md content that already has the reference."""
    return """# AGENTS.md

## Project Overview
This is a sample project.

## Objective Template
...
"""
```

#### Pattern 3: Acceptance Tests (test_agents_md_update_acceptance.py)

**Source**: `tests/test_agents_md_update_acceptance.py` (Lines 11-37)

```python
@pytest.mark.acceptance
class TestAgentsMdUpdateAcceptance:
    """Acceptance tests for AGENTS.md update during teambot init."""

    def test_at_001_appends_reference_when_template_copied_to_existing_agents(
        self, tmp_path, monkeypatch
    ):
        """AT-001: Section appended when template newly copied and AGENTS.md exists."""
        from teambot.cli import ConsoleDisplay, cmd_init

        # Arrange
        monkeypatch.chdir(tmp_path)
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# My Project\n\n## Development\n")

        # Act
        args = argparse.Namespace(force=False)
        display = ConsoleDisplay()
        result = cmd_init(args, display)

        # Assert
        assert result == 0
        content = agents_md.read_text()
        assert "## Objective Template" in content
```

**Key observations:**
- Uses `@pytest.mark.acceptance` marker
- Uses `monkeypatch.chdir(tmp_path)` for directory isolation
- Creates `argparse.Namespace` directly
- Tests end-to-end through `cmd_init()`

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `_agents_md_has_agent_directory_reference()` | TDD | Simple function, well-defined behavior |
| `_should_update_agents_md_with_agent_directory()` | TDD | Clear trigger conditions to test |
| `_update_agents_md_with_agent_directory_reference()` | TDD | Complex integration, needs thorough coverage |
| Acceptance Tests | TDD | Validates full user scenarios |

### Required Test Cases

#### Unit Tests (test_agents_md_update.py - extend existing file)

1. **TestAgentsMdHasAgentDirectoryReference**
   - `test_returns_true_when_reference_exists` - marker present
   - `test_returns_false_when_no_reference` - marker absent
   - `test_returns_false_for_empty_file` - empty AGENTS.md
   - `test_returns_false_for_missing_file` - file doesn't exist
   - `test_case_insensitive_detection` - marker with different casing

2. **TestShouldUpdateAgentsMdWithAgentDirectory**
   - `test_returns_true_when_agent_dir_copied_and_agents_skipped` - trigger condition met
   - `test_returns_false_when_agent_dir_not_copied` - .agent already existed
   - `test_returns_false_when_agents_freshly_copied` - AGENTS.md was just copied
   - `test_returns_false_when_agent_dir_skipped_not_empty` - .agent had content
   - `test_handles_missing_results` - edge case

3. **TestUpdateAgentsMdWithAgentDirectoryReference**
   - `test_appends_reference_when_conditions_met` - happy path
   - `test_skips_when_reference_exists` - idempotent
   - `test_preserves_existing_content_exactly` - non-destructive
   - `test_returns_false_when_conditions_not_met` - preconditions
   - `test_idempotent_multiple_runs` - safe to re-run
   - `test_handles_empty_file` - edge case
   - `test_handles_no_trailing_newline` - edge case
   - `test_handles_permission_error` - graceful error handling

#### Acceptance Tests (test_agents_md_update_acceptance.py - extend existing file)

1. `test_at_007_appends_agent_dir_reference_when_newly_copied` - Main scenario
2. `test_at_008_no_agent_dir_reference_when_dir_exists` - Skip when .agent exists
3. `test_at_009_no_duplicate_agent_dir_reference` - Idempotent
4. `test_at_010_both_references_added_on_fresh_existing_agents` - Both template AND .agent refs

## Task Implementation Requests

### Task 1: Add Constants for `.agent` Directory Reference
- **File**: `src/teambot/cli.py`
- **Location**: After Line 45 (after `OBJECTIVE_TEMPLATE_SECTION`)
- **Content**: `AGENT_DIRECTORY_MARKER` and `AGENT_DIRECTORY_SECTION` constants
- **Source**: Copy content from `src/teambot/scaffolds/AGENTS.md` Lines 130-191

### Task 2: Implement Detection Function
- **File**: `src/teambot/cli.py`
- **Location**: After `_agents_md_has_template_reference()` (Line 62)
- **Function**: `_agents_md_has_agent_directory_reference(agents_md_path: Path) -> bool`
- **Pattern**: Follow `_agents_md_has_template_reference()`

### Task 3: Implement Trigger Condition Function
- **File**: `src/teambot/cli.py`
- **Location**: After `_should_update_agents_md()` (Line 87)
- **Function**: `_should_update_agents_md_with_agent_directory(results: list[CopyResult]) -> bool`
- **Pattern**: Follow `_should_update_agents_md()`

### Task 4: Implement Update Function
- **File**: `src/teambot/cli.py`
- **Location**: After `_update_agents_md_with_template_reference()` (Line 136)
- **Function**: `_update_agents_md_with_agent_directory_reference(results, target_root, display) -> bool`
- **Pattern**: Follow `_update_agents_md_with_template_reference()`

### Task 5: Integrate in cmd_init()
- **File**: `src/teambot/cli.py`
- **Location**: Line 555 (after existing template reference update)
- **Change**: Add call to `_update_agents_md_with_agent_directory_reference()`

### Task 6: Add Unit Tests
- **File**: `tests/test_agents_md_update.py`
- **Location**: Extend with new test classes
- **Coverage**: All functions from Tasks 2-4

### Task 7: Add Acceptance Tests
- **File**: `tests/test_agents_md_update_acceptance.py`
- **Location**: Add new test methods to existing class
- **Coverage**: End-to-end scenarios AT-007 through AT-010

## Potential Next Research

No additional research required. Implementation can proceed.

## References

| Source | Description | Lines |
|--------|-------------|-------|
| `src/teambot/cli.py` | Existing AGENTS.md update implementation | 30-136, 507-555 |
| `src/teambot/scaffolds.py` | CopyResult structure and scaffold copying | 11-17, 66-107, 150-165 |
| `src/teambot/scaffolds/AGENTS.md` | Canonical `.agent` directory section content | 130-191 |
| `tests/test_agents_md_update.py` | Unit test patterns | 1-342 |
| `tests/test_agents_md_update_acceptance.py` | Acceptance test patterns | 1-173 |
| `pyproject.toml` | Test configuration and markers | 53-63 |

## Implementation Readiness

| Criterion | Status |
|-----------|--------|
| Technical approach documented | ✅ |
| Code patterns identified | ✅ |
| Entry points traced | ✅ |
| Test strategy defined | ✅ |
| Implementation tasks specified | ✅ |

**Ready for Step 4 (Test Strategy) and Step 5 (Task Planning)**
