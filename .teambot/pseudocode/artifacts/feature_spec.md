<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# AGENTS.md Objective Template Reference - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target v0.2.0 | Lifecycle Design

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-22 |
| Problem & Users | ✅ | None | 2026-02-22 |
| Scope | ✅ | None | 2026-02-22 |
| Requirements | ✅ | None | 2026-02-22 |
| Metrics & Risks | ✅ | None | 2026-02-22 |
| Operationalization | ✅ | None | 2026-02-22 |
| Finalization | ✅ | None | 2026-02-22 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot's `teambot init` command copies scaffold files to user repositories, including `docs/sdd-objective-template.md` - a template that helps users structure development objectives for TeamBot's multi-agent workflow. Currently, when a user's `AGENTS.md` already exists (skipped during init), they receive no indication that the objective template exists or how to use it.

### Core Opportunity
Improve template discoverability by automatically appending a reference section to existing AGENTS.md files when the objective template is successfully copied, ensuring all users—regardless of whether they had a pre-existing AGENTS.md—learn about this valuable resource.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Improve template discoverability for users with existing AGENTS.md | Usability | 0% awareness | 100% awareness via AGENTS.md reference | v0.2.0 | High |
| G-002 | Maintain data integrity of existing AGENTS.md files | Quality | N/A | 100% content preservation | v0.2.0 | Critical |
| G-003 | Ensure idempotent behavior on repeated runs | Reliability | N/A | Zero duplicate references | v0.2.0 | High |
| G-004 | Self-document TeamBot repository with template reference | Documentation | Missing section | Section present in AGENTS.md | v0.2.0 | Medium |

## 2. Problem Definition

### Current Situation
When users run `teambot init`:
1. If `AGENTS.md` doesn't exist → copied from scaffold (includes template documentation)
2. If `AGENTS.md` exists → skipped (user misses template documentation)
3. `docs/sdd-objective-template.md` → copied regardless of AGENTS.md status

Result: Users with pre-existing AGENTS.md files don't discover the objective template.

### Problem Statement
Users who already have an AGENTS.md file in their repository do not receive documentation about the newly-copied `sdd-objective-template.md`, leading to underutilization of TeamBot's structured objective format and inconsistent objective quality across teams.

### Root Causes
* AGENTS.md copy is an all-or-nothing operation (copy or skip)
* No post-copy update mechanism exists for existing files
* Scaffold copy logic doesn't communicate dependencies between files

### Impact of Inaction
* Users create ad-hoc objective files without structure
* AI agents receive inconsistent objective formats, reducing workflow effectiveness
* Teams miss the standardized approach to defining development tasks
* Increased support burden as users ask "how do I create objectives?"

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| **New TeamBot User** | Set up TeamBot in existing repo quickly | Has AGENTS.md already; doesn't know about objective template | High - misses key onboarding resource |
| **Team Lead** | Ensure consistent objective format across team | Team members use different objective structures | High - workflow inconsistency |
| **Existing TeamBot User** | Re-initialize or update TeamBot setup | Running init again shouldn't break existing files | Medium - idempotency concern |
| **TeamBot Contributor** | Understand repository structure | AGENTS.md should document all key files | Low - documentation completeness |

## 4. Scope

### In Scope
* Detect when AGENTS.md exists during `teambot init`
* Detect when `sdd-objective-template.md` was successfully copied
* Append objective template reference section to existing AGENTS.md
* Idempotency check to prevent duplicate references
* Update TeamBot repository's own AGENTS.md with template documentation
* Update bundled scaffold AGENTS.md template (already done per analysis)
* Unit and integration tests for new functionality

### Out of Scope (justify if empty)
* Interactive prompts for AGENTS.md update (adds friction; append is safe)
* Complex AGENTS.md parsing/restructuring (risk of corruption)
* Updating AGENTS.md when template was NOT copied (no value)
* Modifying other scaffold files (not relevant to this feature)

### Assumptions
* A-001: AGENTS.md files use markdown format
* A-002: Appending a new section at end of file is acceptable
* A-003: String-based duplicate detection is sufficient
* A-004: Users expect `teambot init` to be additive, not destructive

### Constraints
* C-001: Must not corrupt or modify existing AGENTS.md content
* C-002: Must handle AGENTS.md files with different structures gracefully
* C-003: Must preserve all whitespace and formatting in existing content
* C-004: Python implementation using existing codebase patterns

## 5. Product Overview

### Value Proposition
For TeamBot users who have existing AGENTS.md files, the enhanced `teambot init` command automatically documents the objective template in their AGENTS.md, so they can discover and use the structured objective format without manual exploration.

### Differentiators
* Additive-only approach ensures zero risk of data loss
* Idempotent design allows safe re-runs
* Contextual update (only when template was actually copied)

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Detect existing AGENTS.md | Check if AGENTS.md exists at repository root before/after scaffold copy | G-001 | All | High | Returns boolean; does not modify file | Pre-condition check |
| FR-002 | Detect template copy success | Determine if `sdd-objective-template.md` was successfully copied during init | G-001 | All | High | Check `CopyResult.copied == True` for template | Uses existing `CopyResult` |
| FR-003 | Check for existing reference | Search AGENTS.md content for objective template reference marker | G-003 | Existing User | High | Returns True if marker found; case-insensitive | Idempotency check |
| FR-004 | Append template reference | Add "Objective Template" section to end of AGENTS.md | G-001, G-002 | New User, Team Lead | High | Content preserved + section added | Append only |
| FR-005 | Display update status | Show success/skip message in CLI output | G-001 | All | Medium | "Updated AGENTS.md" or "Skipped (reference exists)" | User feedback |
| FR-006 | Update repository AGENTS.md | Add template reference section to TeamBot's own AGENTS.md | G-004 | Contributor | Medium | Section present after implementation | One-time update |
| FR-007 | Handle missing AGENTS.md gracefully | If AGENTS.md doesn't exist (was just copied), skip update logic | G-002 | All | High | No error; no duplicate section in new file | Edge case |

### Feature Hierarchy
```plain
teambot init
└── Copy scaffolds (existing)
    └── AGENTS.md update feature (NEW)
        ├── FR-001: Detect existing AGENTS.md
        ├── FR-002: Detect template copy success  
        ├── FR-003: Check for existing reference
        ├── FR-004: Append template reference
        ├── FR-005: Display update status
        └── FR-007: Handle edge cases
```

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Reliability | Existing AGENTS.md content must never be modified | 100% content preservation | Critical | Comparison test: before vs after | Core safety guarantee |
| NFR-002 | Reliability | Operation must be idempotent | Zero duplicates after N runs | High | Run init 3x, verify single reference | Prevents clutter |
| NFR-003 | Performance | Update operation completes in < 100ms | < 100ms for typical AGENTS.md | Low | Timing test with 10KB file | Negligible overhead |
| NFR-004 | Maintainability | Reference section format defined as constant | Single source of truth | Medium | Code review | Easy to update |
| NFR-005 | Compatibility | Handle AGENTS.md with any structure | Works with empty, minimal, complex files | High | Test with varied inputs | Graceful handling |
| NFR-006 | Observability | Log update actions at DEBUG level | Logged when updated/skipped | Low | Log inspection | Debugging support |

## 8. Data & Analytics

### Inputs
* `AGENTS.md` file content (if exists)
* `CopyResult` list from `copy_all_scaffolds()`
* Repository root path

### Outputs / Events
* Modified `AGENTS.md` file (appended content)
* CLI status message (success/skipped)
* Debug log entry

### Reference Section Content
The appended section SHALL use this exact format:

```markdown

## Objective Template

TeamBot provides an objective template for defining development tasks:

| File | Description |
|------|-------------|
| `docs/sdd-objective-template.md` | Template for creating TeamBot objectives. Copy this file and fill in the sections to define your development task. Run with `teambot run objectives/my-objective.md`. |
```

### Duplicate Detection Marker
Check for presence of: `docs/sdd-objective-template.md`
* If this string exists anywhere in AGENTS.md, skip appending
* Case-insensitive search recommended

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| `src/teambot/scaffolds.py` | Code | High | TeamBot | Low | Already stable; provides CopyResult |
| `src/teambot/cli.py` | Code | High | TeamBot | Low | cmd_init() orchestrates flow |
| `CopyResult` namedtuple | Interface | High | TeamBot | Low | Existing stable interface |
| Existing test infrastructure | Test | Medium | TeamBot | Low | pytest + fixtures available |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Corrupting existing AGENTS.md content | Critical | Low | Append-only strategy; read before write; comprehensive tests | Builder | Open |
| R-002 | Breaking on unusual AGENTS.md formats | Medium | Low | Simple append; no parsing of existing structure | Builder | Open |
| R-003 | Duplicate references on repeated runs | Medium | Medium | String-based marker check before append | Builder | Open |
| R-004 | Performance impact on large files | Low | Very Low | Read-only scan; single append operation | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
* AGENTS.md: Repository documentation (Public/Internal depending on repo)
* No PII involved
* No secrets or credentials

### PII Handling
N/A - No PII processed or stored

### Threat Considerations
* File write operation - ensure atomic write or backup
* Path traversal - use Path objects with validation (already in codebase)

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Part of `teambot` package | No separate deployment |
| Rollback | Remove feature code | AGENTS.md changes are user-side |
| Monitoring | N/A | CLI tool, no persistent service |
| Alerting | N/A | CLI tool |
| Support | Document in README/AGENTS.md | Self-documenting |
| Capacity Planning | N/A | Local file operation |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|--------------|-------|
| Implementation | TBD | All FR implemented | Builder |
| Testing | TBD | All tests pass (existing + new) | Builder |
| Code Review | TBD | Approved by reviewer | Reviewer |
| Merge | TBD | CI green | Builder |

## 14. Acceptance Test Scenarios

### AT-001: Fresh Init with No Existing AGENTS.md
**Description**: User runs `teambot init` in a new repository with no AGENTS.md
**Preconditions**: 
- Repository has no `AGENTS.md`
- Repository has no `docs/sdd-objective-template.md`
**Steps**:
1. Run `teambot init`
2. Observe scaffold copy messages
3. Check `AGENTS.md` content
**Expected Result**: AGENTS.md is copied from scaffold (includes Objective Template section already)
**Verification**: `AGENTS.md` exists with "Objective Template" section from scaffold template

### AT-002: Init with Existing AGENTS.md and Template Copied
**Description**: User runs `teambot init` in a repository with existing AGENTS.md that doesn't mention the template
**Preconditions**:
- Repository has `AGENTS.md` (custom content, no template reference)
- Repository has no `docs/sdd-objective-template.md`
**Steps**:
1. Run `teambot init`
2. Observe that AGENTS.md is skipped (exists)
3. Observe that `docs/sdd-objective-template.md` is copied
4. Check `AGENTS.md` content
**Expected Result**: 
- Original AGENTS.md content preserved exactly
- New "Objective Template" section appended at end
- CLI shows "Updated AGENTS.md with objective template reference"
**Verification**: 
- Diff shows only appended section
- `docs/sdd-objective-template.md` string present in AGENTS.md

### AT-003: Idempotent Run - Reference Already Exists
**Description**: User runs `teambot init` multiple times
**Preconditions**:
- Repository has `AGENTS.md` with objective template reference (from previous init)
- Repository has `docs/sdd-objective-template.md`
**Steps**:
1. Run `teambot init` (first time - adds reference)
2. Run `teambot init` again (second time)
3. Run `teambot init` again (third time)
4. Check `AGENTS.md` content
**Expected Result**:
- Only ONE "Objective Template" section exists
- No duplicate references
- CLI shows "Skipped AGENTS.md update (reference exists)"
**Verification**: Count occurrences of `docs/sdd-objective-template.md` - must be exactly 1

### AT-004: Template Not Copied (Already Exists)
**Description**: User runs `teambot init` when template already exists
**Preconditions**:
- Repository has `AGENTS.md` (no template reference)
- Repository already has `docs/sdd-objective-template.md` (from previous init)
**Steps**:
1. Run `teambot init`
2. Observe that template is skipped (exists)
3. Check `AGENTS.md` content
**Expected Result**:
- AGENTS.md is NOT updated (template wasn't copied this run)
- Original AGENTS.md content unchanged
**Verification**: AGENTS.md unchanged from before init

### AT-005: Empty AGENTS.md File
**Description**: User has an empty AGENTS.md file
**Preconditions**:
- Repository has empty `AGENTS.md` (0 bytes or whitespace only)
- Repository has no `docs/sdd-objective-template.md`
**Steps**:
1. Run `teambot init`
2. Check `AGENTS.md` content
**Expected Result**:
- Objective Template section appended
- File now contains the section
**Verification**: File contains "Objective Template" section

### AT-006: Force Flag Behavior
**Description**: User runs `teambot init --force` with existing AGENTS.md
**Preconditions**:
- Repository has `AGENTS.md` (custom content)
- Repository has `docs/sdd-objective-template.md`
**Steps**:
1. Run `teambot init --force`
2. Check `AGENTS.md` content
**Expected Result**:
- AGENTS.md is OVERWRITTEN with scaffold template (force mode)
- No update logic runs (file was copied, not skipped)
**Verification**: AGENTS.md matches scaffold template exactly

## 15. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| - | - | - | - | - |

## 16. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-02-22 | BA Agent | Initial specification | Creation |

## 17. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Code | `src/teambot/cli.py:386-457` | `cmd_init()` function - orchestrates init flow | N/A |
| REF-002 | Code | `src/teambot/scaffolds.py` | Scaffold copy logic with `CopyResult` | N/A |
| REF-003 | Doc | `docs/sdd-objective-template.md` | Target template being documented | N/A |
| REF-004 | Doc | `AGENTS.md` | Repository AGENTS.md (already has section) | N/A |
| REF-005 | Problem | `.teambot/pseudocode/artifacts/problem_statement.md` | Business problem definition | N/A |

---

## Implementation Notes

### Suggested Implementation Approach

#### New Function: `update_agents_md_with_template_reference`

**Location**: `src/teambot/scaffolds.py` (or new file `src/teambot/agents_md.py`)

**Signature**:
```python
def update_agents_md_with_template_reference(
    agents_md_path: Path,
    template_copied: bool,
) -> tuple[bool, str]:
    """
    Update AGENTS.md with objective template reference if conditions met.
    
    Args:
        agents_md_path: Path to AGENTS.md file
        template_copied: Whether sdd-objective-template.md was copied this run
        
    Returns:
        Tuple of (updated: bool, reason: str)
        - (True, "updated") - Section was appended
        - (False, "reference_exists") - Already has reference
        - (False, "template_not_copied") - Template wasn't copied
        - (False, "file_not_found") - AGENTS.md doesn't exist
    """
```

#### Integration Point in `cmd_init()`

After the scaffold copy results loop (around line 432):
```python
# Check if we should update existing AGENTS.md
agents_md_path = Path("AGENTS.md")
agents_md_result = next((r for r in results if r.source == "AGENTS.md"), None)
template_result = next((r for r in results if r.source == "sdd-objective-template.md"), None)

if agents_md_result and not agents_md_result.copied and template_result and template_result.copied:
    # AGENTS.md existed (skipped) but template was copied
    updated, reason = update_agents_md_with_template_reference(agents_md_path, True)
    if updated:
        display.print_success("  Updated AGENTS.md with objective template reference")
    elif reason == "reference_exists":
        display.print_info("  AGENTS.md already references objective template")
```

### Reference Section Constant

```python
OBJECTIVE_TEMPLATE_REFERENCE = """
## Objective Template

TeamBot provides an objective template for defining development tasks:

| File | Description |
|------|-------------|
| `docs/sdd-objective-template.md` | Template for creating TeamBot objectives. Copy this file and fill in the sections to define your development task. Run with `teambot run objectives/my-objective.md`. |
"""

REFERENCE_MARKER = "docs/sdd-objective-template.md"
```

---

## Validation Status

```
VALIDATION_STATUS: PASS
- Placeholders: 0 remaining
- Sections Complete: 17/17
- Technical Stack: DEFINED (Python, existing codebase patterns)
- Testing Approach: DEFINED (TDD - tests first)
- Acceptance Tests: 6 scenarios defined
```

---

## ✅ Specification Complete: AGENTS.md Objective Template Reference

**📄 Files Created:**
* Specification: `.teambot/pseudocode/artifacts/feature_spec.md`
* Problem Statement: `.teambot/pseudocode/artifacts/problem_statement.md`

**🎯 Key Highlights:**
* Primary Goal: Improve template discoverability for users with existing AGENTS.md
* Target Users: TeamBot users initializing in existing repositories
* Technical Stack: Python (existing codebase)
* Testing Approach: TDD

**➡️ Recommended Next Step:**
Proceed to implementation phase. The specification is ready for a builder agent (`@builder-1` or `@builder-2`) to implement following TDD approach.

<!-- markdown-table-prettify-ignore-end -->
