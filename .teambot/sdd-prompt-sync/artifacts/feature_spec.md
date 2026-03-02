<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# SDD Prompt Sync - Feature Specification Document
Version 1.0 | Status DRAFT | Owner BA Agent | Team TeamBot Core | Target v0.2.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-03-02 |
| Problem & Users | ✅ | None | 2026-03-02 |
| Scope | ✅ | None | 2026-03-02 |
| Requirements | ✅ | None | 2026-03-02 |
| Metrics & Risks | ✅ | None | 2026-03-02 |
| Operationalization | ✅ | None | 2026-03-02 |
| Finalization | ✅ | None | 2026-03-02 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot orchestrates a multi-agent AI workflow using a `stages.yaml` configuration that maps 14 workflow stages to SDD prompt files located in `.agent/commands/sdd/`. These prompt files provide instructions for each agent during workflow execution. The current `teambot init` command copies the entire `.agent/` directory as a single unit, which means new prompt files from TeamBot upgrades are not added if the directory already exists, and using `--force` overwrites all user customizations.

### Core Opportunity
Enable seamless TeamBot upgrades by implementing incremental synchronization of SDD prompt files during `teambot init`, combined with runtime validation to detect mismatches before workflow execution. This preserves user customizations while ensuring new prompt files are automatically added.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Enable incremental prompt file sync during init | Functional | 0% new files added if .agent exists | 100% missing files added | v0.2.0 | P0 |
| G-002 | Validate stages.yaml ↔ prompt file sync at runtime | Functional | No validation | Validation before workflow start | v0.2.0 | P0 |
| G-003 | Provide actionable error messages with remediation steps | UX | Generic errors | Specific fix commands | v0.2.0 | P0 |
| G-004 | Preserve backward compatibility with existing scaffold behavior | Compatibility | Current behavior | No breaking changes | v0.2.0 | P0 |
| G-005 | Enable transparent change tracking during sync | Observability | No visibility | Summary of added/skipped files | v0.2.0 | P1 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Reduce upgrade friction | Users can upgrade TeamBot without losing customizations | P0 | Builder |
| Improve error diagnostics | 100% of validation errors include remediation command | P0 | Builder |
| Maintain trust | Zero reports of unexpected file overwrites | P0 | QA |

## 2. Problem Definition

### Current Situation
After running `teambot init`, the `.agent/commands/sdd/` directory contains SDD prompt files that are referenced by `stages.yaml`. The current scaffold copy behavior:

1. **`copy_scaffold_directory()`** copies the entire `.agent/` directory only if it doesn't exist OR is empty
2. **With `--force`**: Completely replaces the `.agent/` directory, destroying all user customizations
3. **Without `--force`**: Skips the entire directory if it exists with content, missing any new prompt files

### Problem Statement
When TeamBot ships new workflow stages with corresponding prompt files, users with existing installations cannot receive these new files without destroying their customizations. Additionally, there is no validation to detect when `stages.yaml` references prompt files that don't exist, leading to runtime failures that are difficult to diagnose.

### Root Causes
* The `.agent/` directory is treated as an atomic unit during scaffolding, not as a collection of individually manageable files
* No validation layer exists between `stages.yaml` configuration and the prompt files it references
* The scaffold copy logic has no concept of "incremental sync" - only full copy or skip

### Impact of Inaction
* **User frustration**: Users must manually copy new prompt files after each TeamBot upgrade
* **Workflow failures**: Missing prompt files cause cryptic runtime errors
* **Adoption barrier**: Users hesitant to upgrade TeamBot for fear of losing customizations
* **Support burden**: Increased support requests for "workflow not working" issues

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| **TeamBot User** | Keep customized prompts while getting new features | Forced to choose between customizations and upgrades | High - Primary beneficiary |
| **TeamBot Maintainer** | Ship new stages/prompts without breaking existing users | No way to incrementally deliver new prompt files | High - Enables sustainable evolution |
| **AI Agent** | Load correct prompt for each workflow stage | Fails when referenced prompt file missing | High - Direct workflow impact |
| **New User** | Get started quickly with working defaults | N/A (current flow works for new users) | Low - No change needed |

### Journeys

**Upgrade Journey (Current - Broken)**:
1. User has TeamBot v0.1 with customized prompt files
2. User upgrades to TeamBot v0.2 which ships new stages
3. User runs `teambot init` → `.agent/` skipped (exists)
4. User runs `teambot run` → Fails with "prompt file not found"
5. User debugs, eventually discovers missing file
6. User manually copies file from package → Works

**Upgrade Journey (Target - Seamless)**:
1. User has TeamBot v0.1 with customized prompt files
2. User upgrades to TeamBot v0.2 which ships new stages
3. User runs `teambot init` → New prompt files added, customizations preserved
4. User sees: "Added 2 new prompt files, skipped 8 existing files"
5. User runs `teambot run` → Works immediately

## 4. Scope

### In Scope
* Incremental sync of SDD prompt files (`.agent/commands/sdd/sdd.*.prompt.md`) during `teambot init`
* Runtime validation of `stages.yaml` → prompt file references before workflow execution
* Actionable error messages with specific remediation commands
* Warning-only detection of orphaned prompt files (files not referenced by any stage)
* Sync summary display during `teambot init`
* Integration with existing `teambot status` command for sync health check

### Out of Scope (justified)
* **Automatic conflict resolution / merge logic** - Too complex for MVP; user decides
* **Prompt file versioning** - No value without broader version management strategy
* **Schema validation of prompt content** - File existence sufficient; content validation is different concern
* **Custom stages.yaml paths** - Edge case; can add later if requested
* **Remote prompt repositories** - Requires network dependency; out of scope
* **Partial sync CLI options** (e.g., `--sync-prompts=sdd.5-*`) - Over-engineering for MVP

### Assumptions
* `stages.yaml` is always located at repository root
* Prompt files follow naming pattern `sdd.*.prompt.md`
* Users want to preserve their customizations by default
* The bundled scaffold files in the TeamBot package are always the "source of truth" for defaults

### Constraints
* **Python 3.11+** - Can use modern Python features (Path, dataclasses, etc.)
* **Click CLI framework** - Must integrate with existing CLI patterns in `cli.py`
* **No new dependencies** - Must use standard library only
* **TDD approach** - Tests must be written first per project testing preference
* **Backward compatible** - Existing `copy_scaffold_directory()` behavior unchanged

## 5. Product Overview

### Value Proposition
**For** TeamBot users **who** customize their SDD prompt files, **the** SDD Prompt Sync feature **provides** seamless upgrades and early validation **that** preserves customizations while ensuring workflow integrity, **unlike** the current all-or-nothing scaffold copy approach.

### Differentiators
* **Incremental by default** - Only missing files are added; no opt-in required
* **Validation before failure** - Catch mismatches before workflow runs, not during
* **Actionable errors** - Every error message includes a fix command

### UX / UI
**CLI Output During Init**:
```
✓ Syncing SDD prompt files...
  Added: sdd.9-new-stage.prompt.md (new)
  Skipped: sdd.0-initialize.prompt.md (exists)
  Skipped: sdd.1-create-feature-spec.prompt.md (exists)
  ...
  Summary: 1 added, 9 skipped, 0 errors
```

**Validation Error Output**:
```
✗ Validation failed: stages.yaml references missing prompt files

  Missing files:
    - .agent/commands/sdd/sdd.9-new-stage.prompt.md (required by CLEANUP stage)

  To fix, run one of:
    teambot init              # Add missing files (preserves customizations)
    teambot init --force      # Reset all files to defaults
```

UX Status: Defined

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance Criteria | Notes |
|-------|-------|-------------|-------|----------|----------|---------------------|-------|
| FR-001 | Incremental Prompt Sync | During `teambot init`, sync individual SDD prompt files from bundled scaffolds to `.agent/commands/sdd/`, adding only files that don't exist | G-001, G-004 | User, Maintainer | P0 | Given existing `.agent/commands/sdd/` with 8 files, when bundled scaffold has 10 files, then 2 new files are copied and 8 existing files are preserved | Core feature |
| FR-002 | Sync Summary Display | After sync operation, display summary showing files added, skipped, and any errors | G-005 | User | P1 | Given sync completes, then output shows count of added/skipped files and lists each file with its status | Rich console output |
| FR-003 | Runtime Validation - Missing Prompts | Before workflow execution in `teambot run`, validate all `prompt_template` paths in `stages.yaml` exist | G-002 | Agent, User | P0 | Given `stages.yaml` references `sdd.9-foo.prompt.md` that doesn't exist, when `teambot run` executes, then validation fails with error listing missing file and stage | Blocking error |
| FR-004 | Runtime Validation - Orphaned Prompts | Detect prompt files in `.agent/commands/sdd/` matching `sdd.*.prompt.md` that are not referenced by any stage | G-002 | User, Maintainer | P2 | Given `sdd.legacy.prompt.md` exists but no stage references it, when validation runs, then warning is displayed listing orphaned files | Warning only, not blocking |
| FR-005 | Actionable Error Messages | All validation errors must include specific remediation commands | G-003 | User | P0 | Given validation fails, then error message includes at least one `teambot` command to resolve the issue | Example: "Run `teambot init` to add missing files" |
| FR-006 | Force Sync Override | When `--force` flag is used with `teambot init`, reset all SDD prompt files to bundled defaults | G-004 | User | P1 | Given user runs `teambot init --force`, then all SDD prompt files are replaced with bundled versions | Preserves existing `--force` semantics |
| FR-007 | Validation in Status Command | Add prompt sync health check to `teambot status` output | G-002 | User | P2 | Given user runs `teambot status`, then output includes section showing matched, missing, and orphaned prompt files | Part of existing status command |
| FR-008 | Skip Validation Flag | Allow users to bypass validation with `--skip-prompt-validation` flag on `teambot run` | G-004 | User | P2 | Given user runs `teambot run --skip-prompt-validation`, then workflow starts without prompt file validation | Escape hatch for edge cases |

### Feature Hierarchy
```
SDD Prompt Sync
├── Incremental Sync (FR-001, FR-002, FR-006)
│   ├── sync_prompt_files() - Individual file sync
│   ├── get_prompt_mappings() - Extract prompt_template paths from stages.yaml
│   └── Sync summary display
├── Runtime Validation (FR-003, FR-004, FR-005, FR-008)
│   ├── validate_prompt_files() - Check all references exist
│   ├── detect_orphaned_prompts() - Find unreferenced files
│   └── Actionable error formatting
└── Status Integration (FR-007)
    └── prompt_sync_status() - Health check output
```

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Performance | Sync operation must complete quickly | < 500ms for 20 files | P1 | Benchmark test | File I/O bound |
| NFR-002 | Performance | Validation must not add noticeable latency | < 100ms overhead | P1 | Benchmark test | Runs on every `teambot run` |
| NFR-003 | Reliability | Sync must be atomic per file | No partial file writes | P0 | Unit test | Use temp file + rename pattern |
| NFR-004 | Reliability | Validation must handle missing directories gracefully | No crashes if `.agent/` missing | P0 | Unit test | Return appropriate error |
| NFR-005 | Maintainability | New module must follow existing code patterns | Passes ruff check, 80%+ test coverage | P0 | CI pipeline | Match scaffolds.py style |
| NFR-006 | Usability | Error messages must be understandable by non-experts | Include example commands, not just error codes | P0 | Manual review | Follow existing CLI patterns |
| NFR-007 | Compatibility | Must work on Windows, macOS, Linux | Pass tests on all platforms | P1 | CI matrix | Use pathlib for paths |

## 8. Data & Analytics

### Inputs
* `stages.yaml` - Source of truth for stage → prompt mappings (YAML)
* Bundled scaffold files in TeamBot package (`src/teambot/scaffolds/.agent/commands/sdd/`)
* User's `.agent/commands/sdd/` directory (if exists)

### Outputs / Events
* Sync results: List of files added, skipped, or errored
* Validation results: Lists of missing files, orphaned files

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|---------|---------|-------|
| `prompt_sync_completed` | After sync in init | `{added: int, skipped: int, errors: int}` | Track sync adoption | Maintainer |
| `prompt_validation_failed` | Validation finds issues | `{missing: list, orphaned: list}` | Track failure modes | Maintainer |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Upgrade success rate | Outcome | Unknown | 95% of upgrades require no manual intervention | 30 days post-release | User feedback |
| Validation error actionability | Quality | 0% | 100% of errors include fix command | Continuous | Code review |
| Sync performance | Technical | N/A | < 500ms | Continuous | Benchmark tests |

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| `stages.yaml` schema | Input | High | TeamBot Core | Schema changes could break parsing | Version schema, validate structure |
| `scaffolds.py` | Integration | High | TeamBot Core | Must extend without breaking | Add new functions, don't modify existing |
| `cli.py` | Integration | High | TeamBot Core | Must integrate with existing commands | Follow established patterns |
| `workflow/stages.py` | Integration | Medium | TeamBot Core | May need to expose stage loading | Use existing public APIs |
| `pathlib` | Library | Low | Python stdlib | None | Standard library, stable |
| `shutil` | Library | Low | Python stdlib | None | Standard library, stable |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Users unaware sync feature exists | Medium | Medium | Display sync summary prominently during init, document in --help | Builder | Open |
| R-002 | False positives in orphan detection | Medium | Low | Only match `sdd.*.prompt.md` pattern, exclude README.md and non-SDD files | Builder | Open |
| R-003 | Performance overhead on large repos | Low | Low | Cache validation results per workflow run, lazy load stages.yaml | Builder | Open |
| R-004 | Breaking changes to stages.yaml format | High | Low | Validate stages.yaml structure before processing, fail gracefully with clear error | Builder | Open |
| R-005 | File permission issues on sync | Medium | Low | Handle PermissionError gracefully, report which files failed | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
**Internal** - All data is local configuration files; no PII or sensitive data involved.

### PII Handling
None - Feature operates on configuration files only, no user data processed.

### Threat Considerations
* **Path traversal**: Validate all paths stay within expected directories
* **Symlink attacks**: Use `Path.resolve()` to resolve symlinks before operations
* **File permission escalation**: Preserve original file permissions on copy

### Regulatory / Compliance
N/A - No regulatory requirements apply to local file synchronization.

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Bundled with TeamBot package | No separate deployment |
| Rollback | N/A - local file operations | User can manually restore files |
| Monitoring | CLI output provides status | No external monitoring needed |
| Alerting | N/A | Local CLI tool |
| Support | Error messages include fix commands | Self-service resolution |
| Capacity Planning | N/A | Local file operations |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|---------------|-------|
| Implementation | Week 1 | All FR implemented with tests | Builder |
| Review | Week 2 | Code review passed, coverage > 80% | Reviewer |
| Integration | Week 2 | Integrated with cli.py, scaffolds.py | Builder |
| Acceptance Testing | Week 2 | All acceptance tests pass | QA |
| Release | Week 3 | Part of TeamBot v0.2.0 | Maintainer |

### Feature Flags
N/A - Feature is always enabled; no gradual rollout needed for CLI tool.

### Communication Plan
* Update AGENTS.md with new sync behavior
* Add section to README.md explaining upgrade process
* Include in v0.2.0 release notes

## 14. Acceptance Test Scenarios

### AT-001: Incremental Sync Adds Missing Files
**Description**: User upgrades TeamBot and runs init to get new prompt files while preserving customizations
**Preconditions**: 
- User has existing `.agent/commands/sdd/` with 8 customized prompt files
- TeamBot bundled scaffold has 10 prompt files (8 matching + 2 new)
**Steps**:
1. User runs `teambot init` (without --force)
2. Observe sync output
3. Check `.agent/commands/sdd/` directory contents
**Expected Result**: 
- 2 new files are copied to user's directory
- 8 existing files are unchanged (customizations preserved)
- Summary shows "2 added, 8 skipped"
**Verification**: 
- `ls .agent/commands/sdd/ | wc -l` returns 10
- MD5 checksums of original 8 files unchanged
- New files match bundled scaffold content

### AT-002: Validation Blocks Run When Prompt Missing
**Description**: User's stages.yaml references a prompt file that doesn't exist
**Preconditions**:
- User has `stages.yaml` at repo root
- `stages.yaml` contains stage with `prompt_template: .agent/commands/sdd/sdd.99-missing.prompt.md`
- File `sdd.99-missing.prompt.md` does not exist
**Steps**:
1. User runs `teambot run objectives/test.md`
2. Observe error output
**Expected Result**:
- Command exits with non-zero status
- Error message lists missing file path
- Error message lists stage name that requires the file
- Error includes remediation: "Run `teambot init` to add missing files"
**Verification**:
- Exit code is 1
- Output contains "sdd.99-missing.prompt.md"
- Output contains "teambot init"

### AT-003: Orphaned Files Warning (Non-Blocking)
**Description**: User has prompt files not referenced by any stage
**Preconditions**:
- `.agent/commands/sdd/sdd.legacy.prompt.md` exists
- No stage in `stages.yaml` references this file
**Steps**:
1. User runs `teambot run objectives/test.md`
2. Observe warning output
3. Workflow continues to execute
**Expected Result**:
- Warning displays listing orphaned file
- Workflow proceeds normally (not blocked)
- Exit code is 0 (assuming workflow succeeds)
**Verification**:
- Output contains "sdd.legacy.prompt.md" with warning indicator
- Workflow enters SETUP stage

### AT-004: Status Command Shows Sync Health
**Description**: User checks prompt sync status without running workflow
**Preconditions**:
- TeamBot initialized in repo
- Mix of matched, missing, and orphaned prompt files
**Steps**:
1. User runs `teambot status`
2. Observe prompt sync section
**Expected Result**:
- Output includes "Prompt Sync Status" section
- Lists matched files with ✓
- Lists missing files with ✗
- Lists orphaned files with ⚠
**Verification**:
- Output contains expected symbols and file names

### AT-005: Force Flag Resets All Prompt Files
**Description**: User wants to reset all prompts to defaults
**Preconditions**:
- User has customized `.agent/commands/sdd/sdd.0-initialize.prompt.md`
- Custom file differs from bundled scaffold
**Steps**:
1. User runs `teambot init --force`
2. Check prompt file contents
**Expected Result**:
- All prompt files replaced with bundled scaffold versions
- Customizations are removed
- Summary indicates files were replaced
**Verification**:
- MD5 of user's file matches MD5 of bundled scaffold file

### AT-006: Skip Validation Flag Bypasses Check
**Description**: User runs workflow bypassing prompt validation
**Preconditions**:
- `stages.yaml` references missing prompt file
**Steps**:
1. User runs `teambot run objectives/test.md --skip-prompt-validation`
2. Observe output
**Expected Result**:
- Validation is skipped
- Workflow attempts to start (may fail later when loading missing prompt)
**Verification**:
- No validation error at startup
- Exit code depends on downstream behavior

## 15. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| Q-001 | Should validation be hard blocker or allow --skip-validation? | BA | Resolved | ✅ Decided: Hard blocker with escape hatch (FR-008) |
| Q-002 | Should we support partial sync patterns? | BA | Resolved | ✅ Decided: Out of scope for MVP |
| Q-003 | Should orphan detection include all files or only sdd.*.prompt.md? | BA | Resolved | ✅ Decided: Only sdd.*.prompt.md pattern |

## 16. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-03-02 | BA Agent | Initial specification from problem statement | Created |

## 17. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Artifact | `.teambot/sdd-prompt-sync/artifacts/problem_statement.md` | Business problem definition and goals | Source of requirements |
| REF-002 | Code | `src/teambot/scaffolds.py` | Current scaffold copy behavior | Implementation context |
| REF-003 | Config | `stages.yaml` | Workflow stage definitions with prompt_template mappings | Source of truth for stage→prompt mapping |
| REF-004 | Code | `src/teambot/cli.py` | Current init command implementation | Integration point |

### Citation Usage
- Problem statement (REF-001) provided goals G-001 through G-005 and success criteria
- scaffolds.py (REF-002) informed FR-001 and FR-006 design for backward compatibility
- stages.yaml (REF-003) defines the prompt_template field structure used in FR-003

## 18. Appendices

### Glossary
| Term | Definition |
|------|------------|
| SDD | Spec-Driven Development - TeamBot's workflow methodology |
| Prompt file | Markdown file containing instructions for an AI agent at a specific workflow stage |
| Scaffold | Template files bundled with TeamBot that are copied to user's repository during init |
| Orphaned file | A prompt file that exists but is not referenced by any stage in stages.yaml |
| Incremental sync | Copying only files that don't exist, preserving existing files |

### Technical Notes

**Proposed Module Structure**:
```
src/teambot/
├── prompt_sync.py          # New module for sync and validation logic
│   ├── sync_prompt_files()
│   ├── validate_prompt_files()
│   ├── detect_orphaned_prompts()
│   └── get_prompt_mappings()
├── scaffolds.py            # Existing - no modifications needed
└── cli.py                  # Existing - integrate new functions
```

**Sync Algorithm**:
```python
def sync_prompt_files(target_root: Path, force: bool = False) -> list[SyncResult]:
    scaffold_dir = get_scaffolds_dir() / ".agent" / "commands" / "sdd"
    target_dir = target_root / ".agent" / "commands" / "sdd"
    
    results = []
    for scaffold_file in scaffold_dir.glob("sdd.*.prompt.md"):
        target_file = target_dir / scaffold_file.name
        if target_file.exists() and not force:
            results.append(SyncResult(scaffold_file.name, "skipped"))
        else:
            shutil.copy2(scaffold_file, target_file)
            results.append(SyncResult(scaffold_file.name, "added"))
    return results
```

Generated 2026-03-02T21:55:00Z by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
