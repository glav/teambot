## Objective

**Goal**: Enhance `teambot init` to update existing AGENTS.md files with references to the `.agent` directory structure when the directory is copied.

**Problem Statement**:
- When `teambot init` runs in a repository that already has an AGENTS.md file, the scaffold copy is skipped (correctly preserving user content)
- However, this means existing AGENTS.md files never learn about the `.agent/` directory that was copied
- The `.agent` directory contains critical SDD (Spec-Driven Development) workflow files used for file-based orchestration
- Users with pre-existing AGENTS.md files miss out on having their AI agents know about these commands, instructions, and standards
- This creates an inconsistency: new repositories get AGENTS.md with `.agent` docs, but existing repos don't

**Success Criteria**:
- [ ] `teambot init` detects when AGENTS.md already exists and the `.agent/` directory was copied
- [ ] When both conditions are met, append/update AGENTS.md with a reference section for `.agent` directory
- [ ] The update includes the FULL directory structure matching `src/teambot/scaffolds/AGENTS.md` (lines 130-191)
- [ ] Section includes: Commands table (4 entries), SDD workflow table (10 entries), Instructions table (6 entries), Standards table (5 entries)
- [ ] If AGENTS.md already contains a reference to `.agent` directory, no duplicate is added
- [ ] File permission errors are handled gracefully (log debug, don't crash)
- [ ] All existing tests continue to pass
- [ ] New tests cover the AGENTS.md update logic for `.agent` directory

**Non-Goals** (explicitly out of scope):
- Restructuring or reformatting existing AGENTS.md content
- Parsing or validating AGENTS.md markdown structure beyond simple text search
- Interactive prompts asking user permission to update AGENTS.md
- Dynamically enumerating files in `.agent` directory (use static reference section)

---

## Technical Context

**Target Codebase**:
- `src/teambot/cli.py` - Main CLI containing `cmd_init()` function and existing AGENTS.md update logic
- `src/teambot/scaffolds.py` - Scaffold file/directory copying logic
- `src/teambot/scaffolds/AGENTS.md` - Bundled AGENTS.md template (canonical source for section content, lines 130-191)

**Primary Language/Framework**:
- Python (existing codebase)

**Testing Preference**:
- TDD - Write tests for `.agent` directory reference detection and update logic first

**Key Constraints**:
- Must not corrupt or break existing AGENTS.md files
- Update should be idempotent (safe to run multiple times)
- Should handle AGENTS.md files with different structures gracefully
- Must preserve all existing content in user's AGENTS.md
- Follow existing pattern established by `_update_agents_md_with_template_reference()`
- Handle file permission errors gracefully (log warning via `logging.debug()`, don't crash)

---

## Existing Pattern to Follow

The objective template reference logic in `cli.py` provides the pattern:

```python
# Constants
OBJECTIVE_TEMPLATE_MARKER = "## Objective Template"
OBJECTIVE_TEMPLATE_SECTION = """..."""

# Functions
def _agents_md_has_template_reference(agents_md_path: Path) -> bool: ...
def _should_update_agents_md(results: list[CopyResult]) -> bool: ...
def _update_agents_md_with_template_reference(...) -> bool: ...
```

The new implementation should mirror this pattern:
1. Add constants: `DOT_AGENT_DIRECTORY_MARKER` and `DOT_AGENT_DIRECTORY_SECTION`
2. Add detection function: `_agents_md_has_dot_agent_reference()`
3. Add condition function: `_should_update_agents_md_with_dot_agent_ref()`
4. Add update function: `_update_agents_md_with_dot_agent_reference()`
5. Call from `cmd_init()` after scaffold copying

---

## Implementation Approach

### 1. Constants Definition

**Marker** (for detection):
```python
# Use the primary section header for reliable detection
DOT_AGENT_DIRECTORY_MARKER = "## Copilot / AI Assisted Workflow"
```

**Section Content** (extract verbatim from `src/teambot/scaffolds/AGENTS.md` lines 130-191):
```python
DOT_AGENT_DIRECTORY_SECTION = """
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

### 2. Detection Logic

Check if AGENTS.md already contains `.agent` directory reference:
```python
def _agents_md_has_dot_agent_reference(agents_md_path: Path) -> bool:
    """Check if AGENTS.md already has .agent directory reference."""
    try:
        content = agents_md_path.read_text(encoding="utf-8")
        # Use case-insensitive check matching the existing pattern
        return DOT_AGENT_DIRECTORY_MARKER.casefold() in content.casefold()
    except OSError:
        return False
```

### 3. Trigger Conditions

Update AGENTS.md when:
1. `.agent` directory was successfully copied (result.source == ".agent" and result.copied)
2. AGENTS.md exists but was skipped (not overwritten)

```python
def _should_update_agents_md_with_dot_agent_ref(results: list[CopyResult]) -> bool:
    """Determine if AGENTS.md should be updated with .agent directory reference."""
    dot_agent_copied = False
    agents_md_skipped = False

    for result in results:
        if result.source == ".agent" and result.copied:
            dot_agent_copied = True
        if result.source == "AGENTS.md" and result.reason == "skipped_exists":
            agents_md_skipped = True

    return dot_agent_copied and agents_md_skipped
```

### 4. Console Output

```
✓ Copied .agent directory
⊘ Skipped AGENTS.md (already exists)
✓ Updated AGENTS.md with .agent directory reference
```

Or if already present:
```
✓ Copied .agent directory
⊘ Skipped AGENTS.md (already exists)
  AGENTS.md already has .agent directory reference
```

### 5. Section Ordering

When both objective template AND `.agent` directory sections are appended (both newly copied):
1. Objective Template section is appended first (existing logic)
2. `.agent` directory section is appended second

This results in a logical flow: general objective info → workflow details.

---

## Files to Modify

### src/teambot/cli.py

Add new constants and functions following the existing pattern:

```python
# New constants (after OBJECTIVE_TEMPLATE_SECTION)
DOT_AGENT_DIRECTORY_MARKER = "## Copilot / AI Assisted Workflow"
DOT_AGENT_DIRECTORY_SECTION = """..."""  # Full section from scaffold lines 130-191

# New functions (after _update_agents_md_with_template_reference)
def _agents_md_has_dot_agent_reference(agents_md_path: Path) -> bool:
    """Check if AGENTS.md already has .agent directory reference."""
    ...

def _should_update_agents_md_with_dot_agent_ref(results: list[CopyResult]) -> bool:
    """Determine if AGENTS.md should be updated with .agent directory reference."""
    ...

def _update_agents_md_with_dot_agent_reference(
    results: list[CopyResult],
    target_root: Path,
    display: ConsoleDisplay | None,
) -> bool:
    """Update AGENTS.md with .agent directory reference if needed.
    
    Handles OSError gracefully by logging via logging.debug() and returning False.
    """
    ...
```

Modify `cmd_init()`:
```python
# After existing _update_agents_md_with_template_reference call (line ~555)
_update_agents_md_with_template_reference(results, Path.cwd(), display)
_update_agents_md_with_dot_agent_reference(results, Path.cwd(), display)  # NEW
```

---

## Acceptance Test Scenarios

### Scenario 1: Fresh Repository (No AGENTS.md)

**Given**: A repository with no AGENTS.md
**When**: User runs `teambot init`
**Then**: 
- AGENTS.md is copied from scaffolds (already includes `.agent` directory docs)
- No additional update needed

### Scenario 2: Existing AGENTS.md Without .agent Reference

**Given**: A repository with existing AGENTS.md that doesn't mention `.agent` directory
**When**: User runs `teambot init`
**Then**:
- `.agent` directory is copied
- AGENTS.md is not overwritten
- AGENTS.md is updated with `.agent` directory reference section appended
- Console shows "Updated AGENTS.md with .agent directory reference"

### Scenario 3: Existing AGENTS.md With .agent Reference

**Given**: A repository with AGENTS.md that already contains "## Copilot / AI Assisted Workflow"
**When**: User runs `teambot init`
**Then**:
- No update to AGENTS.md
- Console shows "AGENTS.md already has .agent directory reference"

### Scenario 4: .agent Directory Already Exists, AGENTS.md Missing Reference

**Given**: A repository with existing `.agent` directory and existing AGENTS.md that doesn't mention `.agent`
**When**: User runs `teambot init`
**Then**:
- `.agent` directory is skipped (reason: "skipped_not_empty")
- AGENTS.md is skipped (reason: "skipped_exists")
- AGENTS.md is NOT updated (because `.agent` wasn't newly copied)

**Rationale**: This follows the pattern of the objective template reference logic - we only append documentation for files WE just added. If the user already had `.agent` directory, they may have customized it or have their own documentation. This avoids surprising users with modifications to their AGENTS.md for files they didn't just receive.

**Alternative Considered**: Always updating AGENTS.md if reference is missing. Rejected because it could add references to a different/customized `.agent` directory, causing confusion.

### Scenario 5: Re-running Init Multiple Times

**Given**: A repository where init was already run
**When**: User runs `teambot init` again multiple times
**Then**:
- AGENTS.md is not duplicated or corrupted
- `.agent` directory reference appears exactly once
- Operation is idempotent

### Scenario 6: Both Template and .agent Directory Copied

**Given**: A repository with existing AGENTS.md that has neither reference
**When**: User runs `teambot init` and both `sdd-objective-template.md` and `.agent` are copied
**Then**:
- Both reference sections are appended to AGENTS.md
- Objective Template section appears first
- `.agent` directory section appears second
- Each section appears exactly once
- Sections are properly separated with newlines

### Scenario 7: File Permission Error (Edge Case)

**Given**: A repository with AGENTS.md that has read-only permissions
**When**: User runs `teambot init` and `.agent` directory is copied
**Then**:
- Update attempt is made
- OSError is caught and logged via `logging.debug()`
- Function returns False (no crash)
- Init continues without failing
- No user-facing error shown (graceful degradation)

### Scenario 8: Minimal AGENTS.md File

**Given**: A repository with minimal AGENTS.md containing only `# AGENTS.md\n`
**When**: User runs `teambot init` and `.agent` directory is copied
**Then**:
- Section is appended correctly
- Proper newline separation between existing content and new section
- File remains valid markdown

### Scenario 9: Force Flag Behavior

**Given**: A repository with existing AGENTS.md and `.agent` directory
**When**: User runs `teambot init --force` (if flag exists, skip if not)
**Then**:
- AGENTS.md is overwritten with scaffold (includes `.agent` docs already)
- No append logic triggered (file was replaced, not skipped)
- Result is clean scaffold AGENTS.md

---

## Tasks Breakdown

### Phase 1: Add Constants and Detection Functions

- [ ] Add `DOT_AGENT_DIRECTORY_MARKER = "## Copilot / AI Assisted Workflow"` constant to cli.py
- [ ] Add `DOT_AGENT_DIRECTORY_SECTION` constant with verbatim content from scaffold lines 130-191
- [ ] Add `_agents_md_has_dot_agent_reference()` function
- [ ] Add `_should_update_agents_md_with_dot_agent_ref()` function
- [ ] Write unit tests for detection functions

### Phase 2: Implement Update Logic

- [ ] Add `_update_agents_md_with_dot_agent_reference()` function
- [ ] Handle OSError gracefully (log with `logging.debug()`, return False)
- [ ] Write unit tests for the update function
- [ ] Test idempotency (no duplicates when run multiple times)
- [ ] Test content preservation
- [ ] Test file permission error handling

### Phase 3: Integrate with Init Command

- [ ] Modify `cmd_init()` to call the new update function
- [ ] Add console output for update status
- [ ] Write integration tests for init scenarios

### Phase 4: Testing and Validation

- [ ] Unit tests for all new functions
- [ ] Integration tests for all acceptance scenarios (1-9)
- [ ] Verify existing tests still pass
- [ ] Test edge cases (empty AGENTS.md, minimal content, large files)
- [ ] Test interaction with objective template update (both appending in order)
- [ ] Test file permission error handling

---

## Additional Context

The `.agent` directory contains the SDD (Spec-Driven Development) workflow which is critical for TeamBot's file-based orchestration model. Having AI agents aware of these files enables them to:
- Use SDD commands for structured development workflows
- Follow established standards and templates
- Apply consistent instructions across interactions
- Guide users through the complete development lifecycle

This enhancement ensures that even repositories with pre-existing AGENTS.md files benefit from this knowledge after running `teambot init`, maintaining feature parity with newly initialized repositories.

## Related Objectives

- `objective-agents-md-objective-template-reference.md` - Similar pattern for objective template reference (completed)
