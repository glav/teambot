<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# AGENTS.md `.agent` Directory Reference Update - Feature Specification
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target v0.2.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-24 |
| Problem & Users | ✅ | None | 2026-02-24 |
| Scope | ✅ | None | 2026-02-24 |
| Requirements | ✅ | None | 2026-02-24 |
| Metrics & Risks | ✅ | None | 2026-02-24 |
| Operationalization | ✅ | None | 2026-02-24 |
| Finalization | ✅ | None | 2026-02-24 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot's `teambot init` command copies scaffold files to user repositories, including the `.agent/` directory containing AI-assisted workflow tooling (commands, instructions, standards). When users have an existing `AGENTS.md` file, the scaffold `AGENTS.md` is correctly skipped to preserve user content. However, the user's `AGENTS.md` is not updated to document the newly copied `.agent/` directory structure.

### Core Opportunity
Automatically update existing `AGENTS.md` files with `.agent/` directory documentation when the directory is successfully copied, ensuring users and AI agents can discover and utilize the AI-assisted workflows.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Enable discoverability of `.agent/` directory in user's AGENTS.md | Functional | 0% (no reference added) | 100% (reference added when applicable) | v0.2.0 | P0 |
| G-002 | Maintain data integrity of existing AGENTS.md content | Quality | N/A | Zero data loss | v0.2.0 | P0 |
| G-003 | Ensure idempotent operation (safe re-runs) | Reliability | N/A | No duplicates on re-run | v0.2.0 | P0 |
| G-004 | Handle errors gracefully without crashing init | Resilience | N/A | Log warning, continue init | v0.2.0 | P1 |

## 2. Problem Definition

### Current Situation
When `teambot init` runs on a repository with an existing `AGENTS.md`:
1. The `.agent/` directory is successfully copied (if not already present)
2. The scaffold `AGENTS.md` is skipped (preserving user content)
3. **Gap**: User's `AGENTS.md` remains unchanged, lacking documentation for `.agent/`

A similar pattern already exists for the objective template (`sdd-objective-template.md`):
- When copied, `_update_agents_md_with_template_reference()` appends an "Objective Template" section
- Uses marker detection (`OBJECTIVE_TEMPLATE_MARKER`) for idempotency
- Handles file errors gracefully via `logging.debug()`

### Problem Statement
Users who run `teambot init` on existing repositories with `AGENTS.md` files do not receive documentation about the `.agent/` directory's AI-assisted workflows, reducing discoverability and AI agent effectiveness.

### Root Causes
* No equivalent update logic exists for `.agent/` directory (only for objective template)
* The pattern established by `_update_agents_md_with_template_reference()` was not extended to directory copies

### Impact of Inaction
* Users remain unaware of `.agent/` capabilities (25 files across 4 categories)
* AI agents (Copilot CLI) cannot reference `.agent/` structure from user's AGENTS.md
* Support burden increases as users ask "how do I use .agent?"
* Inconsistent experience between fresh installs (full AGENTS.md) and existing repos (partial)

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| **Developer** (primary) | Discover available AI workflows; understand `.agent/` structure | Hidden tooling; must manually explore directory | High - primary user of TeamBot |
| **AI Agent** (Copilot CLI) | Access accurate AGENTS.md context for repository interactions | Missing `.agent/` documentation in user's AGENTS.md | High - affects AI assistance quality |
| **Team Lead** | Ensure team uses standardized workflows | Inconsistent documentation across repos | Medium - affects team adoption |

## 4. Scope

### In Scope
* Detect when `.agent/` directory was successfully copied AND `AGENTS.md` was skipped
* Append the full `.agent/` directory reference section (lines 130-191 from scaffold AGENTS.md)
* Implement idempotency via marker detection (case-insensitive)
* Handle file permission errors gracefully (log via `logging.debug()`)
* Unit tests following TDD approach
* Acceptance tests for end-to-end verification

### Out of Scope
* Modifying the `.agent/` directory structure itself
* Changing how scaffold directories are copied in `scaffolds.py`
* Updating AGENTS.md for other scaffold items (beyond objective template and `.agent/`)
* Custom positioning of appended sections (always append to end)
* GUI or interactive prompts for the update

### Assumptions
* The canonical `.agent/` directory reference content is in `src/teambot/scaffolds/AGENTS.md` lines 130-191
* Content should be appended to the end of AGENTS.md (consistent with objective template pattern)
* Case-insensitive marker detection is acceptable (consistent with existing implementation)
* The section marker will be `## Copilot / AI Assisted Workflow` (first line of the section)

### Constraints
* Must not corrupt or break existing AGENTS.md files (preserve all content)
* Must be idempotent (safe to run multiple times)
* Must handle varied AGENTS.md structures gracefully
* Must follow existing pattern in `_update_agents_md_with_template_reference()`
* Error handling must use `logging.debug()` (not crash)

## 5. Product Overview

### Value Proposition
For **developers using TeamBot** who **have existing AGENTS.md files**, this feature **automatically documents the `.agent/` directory** so that **AI workflows are discoverable without manual file editing**.

### Technical Stack
* **Primary Language**: Python (existing codebase)
* **Target Files**: `src/teambot/cli.py`
* **Testing Framework**: pytest with pytest-mock, pytest-cov
* **Testing Approach**: TDD (Test-Driven Development)

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance Criteria | Notes |
|-------|-------|-------------|-------|----------|----------|---------------------|-------|
| FR-001 | Detect `.agent/` copy condition | Detect when `.agent/` directory was copied AND `AGENTS.md` was skipped | G-001 | Developer | P0 | Returns True only when both conditions met | Mirror `_should_update_agents_md()` pattern |
| FR-002 | Check for existing reference | Check if AGENTS.md already contains `.agent/` directory reference | G-003 | Developer | P0 | Case-insensitive check for marker; returns True/False | Use `## Copilot / AI Assisted Workflow` as marker |
| FR-003 | Append reference section | Append full `.agent/` directory reference section to AGENTS.md | G-001 | Developer, AI Agent | P0 | Content matches scaffold AGENTS.md lines 130-191; proper newline handling | Extract content from scaffold file or define as constant |
| FR-004 | Preserve existing content | Preserve all existing AGENTS.md content when appending | G-002 | Developer | P0 | Original content unchanged; new section appended at end | Handle files with/without trailing newlines |
| FR-005 | Idempotent operation | Skip update if reference already exists | G-003 | Developer | P0 | Running multiple times produces exactly one reference section | Use marker detection before append |
| FR-006 | Handle file errors | Handle file permission/read errors gracefully | G-004 | Developer | P1 | Errors logged via `logging.debug()`; init continues; returns False | Mirror existing OSError handling pattern |
| FR-007 | Display user feedback | Show appropriate message when AGENTS.md is updated or skipped | G-001 | Developer | P2 | Success message on update; info message if already present | Use ConsoleDisplay methods |

### Content Specification

The appended section must include the **exact content** from `src/teambot/scaffolds/AGENTS.md` lines 130-191:

**Section Structure:**
```markdown
## Copilot / AI Assisted Workflow

- All Copilot and AI assisted workflows exist in the `.agent/` directory
- SDD (Spec-Driven Development) workflow in `.agent/commands/sdd/`
- Artifacts tracked in `.agent-tracking/`

### `.agent` directory structure

The `.agent` directory contains commands, instructions, and standards used by AI-assisted workflows.

#### Commands (`commands/`)
[4 entries table]

**Spec-Driven Development (SDD) workflow** (`commands/sdd/`)
[10 entries table]

#### Instructions (`instructions/`)
[6 entries table]

#### Standards (`standards/`)
[5 entries table]
```

**Entry Counts (for verification):**
| Section | Entry Count |
|---------|-------------|
| Commands (`commands/`) | 4 |
| SDD workflow (`commands/sdd/`) | 10 |
| Instructions (`instructions/`) | 6 |
| Standards (`standards/`) | 5 |
| **Total** | **25** |

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Reliability | No data loss in AGENTS.md | 0 bytes lost | P0 | Compare before/after file sizes; verify content preserved | Critical - user data |
| NFR-002 | Maintainability | Follow existing code patterns | 100% pattern adherence | P0 | Code review; function signature consistency | Mirror `_update_agents_md_with_template_reference()` |
| NFR-003 | Performance | No noticeable delay during init | <100ms additional time | P2 | Not a concern for file append operation | Single file I/O |
| NFR-004 | Testability | Comprehensive test coverage | ≥90% for new code | P1 | pytest-cov report | TDD approach ensures this |
| NFR-005 | Security | Handle file permissions safely | No crashes on permission errors | P1 | Exception handling tests | Log and continue |

## 8. Data & Analytics

### Inputs
* `results: list[CopyResult]` - Results from `copy_all_scaffolds()`
* `target_root: Path` - Repository root directory
* Existing `AGENTS.md` file content

### Outputs
* Updated `AGENTS.md` file (appended section)
* Boolean return value indicating success/skip
* Console output via `ConsoleDisplay`
* Debug log entries on errors

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| `src/teambot/cli.py` | Code | High | TeamBot | Low | Existing, stable module |
| `src/teambot/scaffolds.py` | Code | High | TeamBot | Low | Provides `CopyResult` type |
| `src/teambot/scaffolds/AGENTS.md` | Data | High | TeamBot | Low | Canonical content source |
| pytest infrastructure | Testing | Medium | TeamBot | Low | Existing test setup |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Data corruption in AGENTS.md | High | Low | Preserve content; append only; test with varied inputs | Builder | Open |
| R-002 | Duplicate sections on re-run | Medium | Low | Marker detection before append; idempotency tests | Builder | Open |
| R-003 | Encoding issues with special characters | Medium | Low | Use UTF-8 encoding explicitly; test with unicode | Builder | Open |
| R-004 | Content drift from scaffold AGENTS.md | Low | Medium | Extract content from scaffold file OR define as constant with version comment | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
* No sensitive data handled
* AGENTS.md contains documentation only

### PII Handling
* No PII involved

### Threat Considerations
* File permission handling prevents crashes
* No external network calls

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard package update | No special deployment steps |
| Rollback | Standard version rollback | Feature is additive |
| Monitoring | N/A | Local CLI tool |
| Alerting | N/A | Local CLI tool |
| Support | Documentation update | Add to init command docs |
| Capacity Planning | N/A | Single file operation |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|---------------|-------|
| Implementation | TBD | All tests pass; code review approved | Builder |
| Testing | TBD | 90%+ coverage; acceptance tests pass | Builder |
| Documentation | TBD | README updated if needed | Writer |
| Release | TBD | Merged to main | PM |

## 14. Acceptance Test Scenarios

### AT-001: Fresh Repository with `.agent/` Copy
**Description**: User runs `teambot init` on repository with existing AGENTS.md, and `.agent/` is copied
**Preconditions**: Repository has AGENTS.md without `.agent/` reference; no `.agent/` directory
**Steps**:
1. User runs `teambot init`
2. `.agent/` directory is copied (new)
3. `AGENTS.md` is skipped (exists)
4. System detects both conditions
**Expected Result**: AGENTS.md is updated with full `.agent/` directory reference section
**Verification**: 
- AGENTS.md contains "## Copilot / AI Assisted Workflow" heading
- Section includes Commands table (4 entries), SDD table (10 entries), Instructions table (6 entries), Standards table (5 entries)
- Original content is preserved

### AT-002: Re-run After Previous Update
**Description**: User runs `teambot init` multiple times after `.agent/` was already copied
**Preconditions**: Repository has AGENTS.md with existing `.agent/` reference from previous run
**Steps**:
1. User runs `teambot init` (second time)
2. `.agent/` directory exists (skipped)
3. `AGENTS.md` exists (skipped)
**Expected Result**: No duplicate section added; info message displayed
**Verification**:
- AGENTS.md contains exactly one "## Copilot / AI Assisted Workflow" section
- Console shows "AGENTS.md already has .agent directory reference" (or similar)

### AT-003: Permission Error Handling
**Description**: User runs `teambot init` when AGENTS.md is not writable
**Preconditions**: AGENTS.md exists and is read-only; `.agent/` directory to be copied
**Steps**:
1. User runs `teambot init`
2. `.agent/` directory is copied
3. System attempts to update AGENTS.md
4. Write operation fails (permission denied)
**Expected Result**: Error logged via `logging.debug()`; init continues; no crash
**Verification**:
- `teambot init` completes without exception
- Debug log contains error message
- Other scaffold operations succeed

### AT-004: AGENTS.md Already Has Reference (Case Insensitive)
**Description**: User has manually added `.agent/` reference with different casing
**Preconditions**: AGENTS.md contains "## copilot / ai assisted workflow" (lowercase)
**Steps**:
1. User runs `teambot init`
2. `.agent/` directory is copied
3. System checks for existing reference
**Expected Result**: Detected as existing; no update performed
**Verification**:
- Case-insensitive match succeeds
- Original content unchanged
- No duplicate section

### AT-005: Empty AGENTS.md File
**Description**: User has empty AGENTS.md file
**Preconditions**: AGENTS.md exists but is empty; no `.agent/` directory
**Steps**:
1. User runs `teambot init`
2. `.agent/` directory is copied
3. AGENTS.md is skipped (exists)
**Expected Result**: Reference section appended to empty file
**Verification**:
- AGENTS.md now contains the reference section
- File is valid markdown

## 15. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| - | - | - | - | All resolved |

## 16. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-24 | BA Agent | Initial specification | Creation |

## 17. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Code | `src/teambot/cli.py:48-136` | Existing objective template update pattern | N/A |
| REF-002 | Code | `src/teambot/scaffolds/AGENTS.md:130-191` | Canonical `.agent/` directory reference content | N/A |
| REF-003 | Code | `tests/test_agents_md_update.py` | Existing test patterns for AGENTS.md updates | N/A |
| REF-004 | Doc | `.teambot/constants/artifacts/problem_statement.md` | Problem definition | N/A |

---

## Implementation Notes for Builder

### Recommended Implementation Approach

1. **New Constants** (add near existing `OBJECTIVE_TEMPLATE_MARKER`):
   ```python
   AGENT_DIR_MARKER = "## Copilot / AI Assisted Workflow"
   
   AGENT_DIR_SECTION = """
   ## Copilot / AI Assisted Workflow
   
   - All Copilot and AI assisted workflows exist in the `.agent/` directory
   ...
   [Full content from scaffold AGENTS.md lines 130-191]
   """
   ```

2. **New Functions** (mirror existing pattern):
   - `_agents_md_has_agent_dir_reference(agents_md_path: Path) -> bool`
   - `_should_update_agents_md_with_agent_dir(results: list[CopyResult]) -> bool`
   - `_update_agents_md_with_agent_dir_reference(results, target_root, display) -> bool`

3. **Integration Point**:
   - Call new function in `cmd_init()` after `_update_agents_md_with_template_reference()`
   - Line ~555 in current `cli.py`

4. **Test Files**:
   - Add tests to existing `tests/test_agents_md_update.py` OR create `tests/test_agents_md_agent_dir_update.py`
   - Create `tests/test_agents_md_agent_dir_update_acceptance.py` for acceptance tests

---

**VALIDATION_STATUS: PASS**
- Placeholders: 0 remaining
- Sections Complete: 17/17
- Technical Stack: DEFINED (Python, pytest, TDD)
- Testing Approach: DEFINED (TDD)
- Acceptance Tests: 5 scenarios defined

<!-- markdown-table-prettify-ignore-end -->
