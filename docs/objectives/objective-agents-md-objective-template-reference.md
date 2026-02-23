## Objective

**Goal**: Enhance `teambot init` to update existing AGENTS.md files with a reference to the SDD objective template, and update this repository's AGENTS.md to document the template.

**Problem Statement**:
- When `teambot init` runs in a repository that already has an AGENTS.md file, the scaffold copy is skipped (correctly preserving user content)
- However, this means existing AGENTS.md files never learn about the `docs/sdd-objective-template.md` file that was copied
- Users with pre-existing AGENTS.md files miss out on having their AI agents know about the objective template
- The TeamBot repository's own AGENTS.md does not document the objective template file

**Success Criteria**:
- [ ] `teambot init` detects when AGENTS.md already exists and the sdd-objective-template.md was copied
- [ ] When both conditions are met, append/update AGENTS.md with a reference to the objective template
- [ ] The update includes the template's location and purpose (creating objectives for TeamBot)
- [ ] If AGENTS.md already contains a reference to the template, no duplicate is added
- [ ] This repository's AGENTS.md is updated to include a section documenting `docs/sdd-objective-template.md`
- [ ] All existing tests continue to pass
- [ ] New tests cover the AGENTS.md update logic

**Non-Goals** (explicitly out of scope):
- Restructuring or reformatting existing AGENTS.md content
- Adding references for other scaffold files (stages.yaml, .agent/, etc.)
- Parsing or validating AGENTS.md markdown structure beyond simple text search
- Interactive prompts asking user permission to update AGENTS.md

---

## Technical Context

**Target Codebase**:
- `src/teambot/cli.py` - Main CLI containing `cmd_init()` function
- `src/teambot/scaffolds.py` - Scaffold file copying logic
- `AGENTS.md` - This repository's AGENTS.md (to be updated)
- `src/teambot/scaffolds/AGENTS.md` - Bundled AGENTS.md template (to be updated)

**Primary Language/Framework**:
- Python (existing codebase)

**Testing Preference**:
- TDD - Write tests for AGENTS.md detection and update logic first

**Key Constraints**:
- Must not corrupt or break existing AGENTS.md files
- Update should be idempotent (safe to run multiple times)
- Should handle AGENTS.md files with different structures gracefully
- Must preserve all existing content in user's AGENTS.md

---

## Implementation Approach

### 1. AGENTS.md Update Logic

When `teambot init` runs:

```python
# Pseudocode
results = copy_all_scaffolds(...)
template_copied = any(
    r.source == "sdd-objective-template.md" and r.reason == "copied"
    for r in results
)
agents_md_skipped = any(
    r.source == "AGENTS.md" and r.reason == "skipped_exists"
    for r in results
)

# Check if AGENTS.md exists and doesn't already contain the reference
agents_md_path = Path.cwd() / "AGENTS.md"
if agents_md_skipped and agents_md_path.exists():
    content = agents_md_path.read_text()
    if "sdd-objective-template.md" not in content:
        update_agents_md_with_template_reference(agents_md_path)
```

### 2. Reference Section to Add

The following section should be appended to existing AGENTS.md files (if not already present):

```markdown
## Objective Template

TeamBot provides an objective template for defining development tasks:

| File | Description |
|------|-------------|
| `docs/sdd-objective-template.md` | Template for creating TeamBot objectives. Copy this file and fill in the sections to define your development task. Run with `teambot run objectives/my-objective.md`. |
```

### 3. Detection Logic

Before appending, check if AGENTS.md already contains a reference:
- Search for `sdd-objective-template.md` in the file content
- If found, skip the update (already documented)

### 4. Console Output

```
✓ Copied docs/sdd-objective-template.md
⊘ Skipped AGENTS.md (already exists)
✓ Updated AGENTS.md with objective template reference
```

Or if already present:
```
✓ Copied docs/sdd-objective-template.md
⊘ Skipped AGENTS.md (already exists)
⊘ AGENTS.md already references objective template
```

---

## Files to Modify

### This Repository's AGENTS.md

Add the following section after the "Repo Layout" section:

```markdown
## Objective Template

TeamBot provides an objective template for defining development tasks:

| File | Description |
|------|-------------|
| `docs/sdd-objective-template.md` | Template for creating TeamBot objectives. Copy this file and fill in the sections to define your development task. Run with `teambot run objectives/my-objective.md`. |
```

### Bundled AGENTS.md (src/teambot/scaffolds/AGENTS.md)

Update the bundled template to include the same section, so new repositories get it from the start.

### src/teambot/scaffolds.py

Add new function:

```python
def update_agents_md_with_template_reference(agents_md_path: Path) -> bool:
    """Append objective template reference to existing AGENTS.md.
    
    Returns True if updated, False if already contains reference.
    """
    content = agents_md_path.read_text()
    
    # Check if already referenced
    if "sdd-objective-template.md" in content:
        return False
    
    # Append section
    section = '''
## Objective Template

TeamBot provides an objective template for defining development tasks:

| File | Description |
|------|-------------|
| `docs/sdd-objective-template.md` | Template for creating TeamBot objectives. Copy this file and fill in the sections to define your development task. Run with `teambot run objectives/my-objective.md`. |
'''
    agents_md_path.write_text(content.rstrip() + "\n\n" + section.strip() + "\n")
    return True
```

### src/teambot/cli.py

Modify `cmd_init()` to call the update function when appropriate.

---

## Acceptance Test Scenarios

### Scenario 1: Fresh Repository (No AGENTS.md)

**Given**: A repository with no AGENTS.md
**When**: User runs `teambot init`
**Then**: 
- AGENTS.md is copied from scaffolds (already includes template reference)
- No additional update needed

### Scenario 2: Existing AGENTS.md Without Template Reference

**Given**: A repository with existing AGENTS.md that doesn't mention `sdd-objective-template.md`
**When**: User runs `teambot init`
**Then**:
- sdd-objective-template.md is copied
- AGENTS.md is not overwritten
- AGENTS.md is updated with template reference section appended
- Console shows "Updated AGENTS.md with objective template reference"

### Scenario 3: Existing AGENTS.md With Template Reference

**Given**: A repository with AGENTS.md that already mentions `sdd-objective-template.md`
**When**: User runs `teambot init`
**Then**:
- No update to AGENTS.md
- Console shows "AGENTS.md already references objective template"

### Scenario 4: Template Already Exists, AGENTS.md Missing Reference

**Given**: A repository with existing `docs/sdd-objective-template.md` and existing AGENTS.md that doesn't mention the template
**When**: User runs `teambot init`
**Then**:
- Neither file is copied (both already exist)
- AGENTS.md IS updated with template reference (because it's missing the reference)
- This handles edge cases like user manually re-adding the template file

### Scenario 5: Re-running Init Multiple Times

**Given**: A repository where init was already run
**When**: User runs `teambot init` again multiple times
**Then**:
- AGENTS.md is not duplicated or corrupted
- Template reference appears exactly once
- Operation is idempotent

---

## Tasks Breakdown

### Phase 1: Update Repository AGENTS.md Files

- [ ] Add "Objective Template" section to `/workspaces/teambot/AGENTS.md`
- [ ] Add "Objective Template" section to `src/teambot/scaffolds/AGENTS.md`
- [ ] Verify sections are consistent between both files

### Phase 2: Implement Update Logic

- [ ] Add `update_agents_md_with_template_reference()` function to scaffolds.py
- [ ] Write unit tests for the new function
- [ ] Test detection of existing reference (idempotency)
- [ ] Test content preservation

### Phase 3: Integrate with Init Command

- [ ] Modify `cmd_init()` to detect when AGENTS.md update is needed
- [ ] Add console output for update status
- [ ] Write integration tests for init scenarios

### Phase 4: Testing

- [ ] Unit tests for `update_agents_md_with_template_reference()`
- [ ] Integration tests for all acceptance scenarios
- [ ] Verify existing tests still pass
- [ ] Test edge cases (empty AGENTS.md, malformed content)

---

## Additional Context

The objective template (`docs/sdd-objective-template.md`) provides a structured format for defining TeamBot tasks. Having AI agents aware of this template enables them to:
- Suggest using the template when users want to define new tasks
- Understand the expected format for objectives
- Guide users through the template sections

This enhancement ensures that even repositories with pre-existing AGENTS.md files benefit from this knowledge after running `teambot init`.
