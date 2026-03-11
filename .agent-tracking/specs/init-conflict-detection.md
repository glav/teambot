<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Init Conflict Detection - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target Next Release | Lifecycle Specification

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-03-10 |
| Problem & Users | ✅ | None | 2026-03-10 |
| Scope | ✅ | None | 2026-03-10 |
| Requirements | ✅ | None | 2026-03-10 |
| Metrics & Risks | ✅ | None | 2026-03-10 |
| Operationalization | ✅ | None | 2026-03-10 |
| Finalization | ✅ | None | 2026-03-10 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary
### Context
TeamBot's `teambot init` command copies scaffold files (`.agent/`, `stages.yaml`, `AGENTS.md`, etc.) to initialize a project for TeamBot workflows. Currently, when the target directory already contains files, the command uses simple "exists/not-exists" logic that may silently skip conflicting content without clear user guidance.

### Core Opportunity
Enhance `teambot init` to intelligently detect conflicting or stale files in the target `.agent/` directory and provide clear, actionable remediation options at runtime. This prevents confusion when scaffold files have been renamed/renumbered between versions.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Detect conflicting scaffold files during init | Feature | No detection | Full detection | Release | P0 |
| G-002 | Provide interactive remediation options | UX | No prompts | 3 clear options | Release | P0 |
| G-003 | Preserve existing content with backup option | Safety | No backup | Timestamped backup | Release | P1 |
| G-004 | Maintain backward compatibility | Stability | N/A | No breaking changes | Release | P0 |

## 2. Problem Definition
### Current Situation
When `teambot init` encounters a non-empty `.agent/` directory:
- `copy_scaffold_directory()` returns `skipped_not_empty` and does nothing
- User sees warning: "Skipped (not empty): .agent"
- No indication of *what* conflicts exist or *why* it matters
- No remediation options beyond manually using `--force` flag

### Problem Statement
Users who have previously initialized TeamBot, or inherited a project with older scaffolds, cannot easily understand or resolve conflicts between their existing `.agent/` files and updated scaffold versions. This leads to confusion, stale prompts in their workflow, and potential workflow failures.

### Root Causes
* Conflict detection only checks if directory is empty, not file-level conflicts
* No analysis of numbered prefix patterns (e.g., `sdd.4-*.prompt.md`) that indicate version mismatches
* No interactive remediation - user must know to use `--force` flag
* No backup mechanism to preserve existing customizations

### Impact of Inaction
* Users run workflows with outdated/mismatched SDD prompts
* Silent failures when stages reference prompts that don't exist
* Loss of user customizations when they resort to `--force`
* Confusion about what "skipped_not_empty" means and how to resolve

## 3. Users & Personas
| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| New TeamBot User | Initialize project quickly | Inherited old `.agent/` directory from template | High |
| Upgrading User | Get latest scaffold files | Don't want to lose customizations | High |
| CI/CD Pipeline | Automated init in fresh environment | Needs deterministic behavior | Medium |

## 4. Scope
### In Scope
* Conflict detection in `.agent/` directory during `teambot init`
* Detection of files with same numbered prefix but different names
* Interactive prompt with Replace/Backup/Skip options
* Backup mechanism to `.agent-tracking/backups/<timestamp>/`
* Documentation updates

### Out of Scope
* Conflict detection for non-`.agent/` scaffold files (`stages.yaml`, `AGENTS.md`)
* Content-level diff/merge capabilities
* Automatic conflict resolution without user interaction
* Migration scripts for specific version upgrades

### Assumptions
* Users have terminal access for interactive prompts
* Numbered prefix pattern (e.g., `sdd.4-`) is reliable indicator of conflicts
* `.agent-tracking/` directory is appropriate location for backups

### Constraints
* Must not break existing `--force` flag behavior
* Detection must be fast (file listing only, no content parsing)
* Must work cross-platform (Windows, macOS, Linux)
* Interactive prompts disabled when `--force` is used

## 5. Product Overview
### Value Proposition
Clear, actionable conflict detection that helps users understand and resolve scaffold mismatches, with safe backup options to preserve customizations.

### Differentiators
* Intelligent pattern-based conflict detection (not just exists/not-exists)
* Interactive remediation at detection time
* Safe backup before destructive operations

## 6. Functional Requirements
| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Detect directory conflicts | When `.agent/` exists and is non-empty, analyze contents for conflicts | G-001 | All | P0 | Returns list of conflicting files | |
| FR-002 | Identify numbered prefix conflicts | Find files where numbered prefix matches but rest of name differs (e.g., existing `sdd.4-old-name.prompt.md` vs scaffold `sdd.4-new-name.prompt.md`) | G-001 | All | P0 | Correctly identifies prefix overlaps | |
| FR-003 | Display conflict summary | Show clear list of conflicting files with explanation | G-001, G-002 | All | P0 | User understands what conflicts and why | |
| FR-004 | Interactive remediation prompt | Present 3 options: Replace, Backup, Skip | G-002 | Interactive users | P0 | Prompt appears, accepts valid input | |
| FR-005 | Replace option | Clear `.agent/` directory and copy new scaffolds (equivalent to `--force`) | G-002 | All | P0 | Directory replaced, new scaffolds copied | |
| FR-006 | Backup option | Move existing `.agent/` to `.agent-tracking/backups/<timestamp>/` then copy new scaffolds | G-002, G-003 | Upgrading users | P0 | Backup created, new scaffolds copied | |
| FR-007 | Skip option | Keep existing files, continue with warning | G-002 | All | P0 | No changes made, warning displayed | |
| FR-008 | Maintain existing behavior | `skipped_not_empty` behavior preserved for truly unrelated content (no conflicts detected) | G-004 | CI/CD | P1 | Non-conflict cases unchanged | |
| FR-009 | Force flag bypass | When `--force` is used, skip conflict detection and replace directly | G-004 | CI/CD | P0 | No prompt shown with --force | |

### Feature Hierarchy
```plain
Init Conflict Detection
├── Conflict Detection
│   ├── Directory existence check
│   ├── File enumeration
│   └── Numbered prefix pattern matching
├── Conflict Reporting
│   ├── Conflict list formatting
│   └── Explanation text
├── Interactive Remediation
│   ├── Option display
│   ├── User input handling
│   └── Option execution
│       ├── Replace (clear + copy)
│       ├── Backup (move + copy)
│       └── Skip (warning only)
└── Integration
    ├── CLI integration
    └── Force flag handling
```

## 7. Non-Functional Requirements
| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Performance | Conflict detection completes quickly | < 100ms for typical directory | P1 | Timing tests | File listing only, no content parsing |
| NFR-002 | Reliability | Detection works on all platforms | Windows, macOS, Linux | P0 | CI tests on all platforms | Use pathlib for cross-platform paths |
| NFR-003 | Usability | Conflict messages are clear and actionable | User understands issue without docs | P0 | User testing | Include remediation steps in message |
| NFR-004 | Maintainability | Conflict patterns are configurable | Pattern list in code, not hardcoded strings | P2 | Code review | Easy to add new conflict patterns |
| NFR-005 | Security | Backup directory is outside prompt reference paths | Backups in `.agent-tracking/` not `.agent/` | P0 | Path verification | Prevents AI from reading old conflicting prompts |

## 8. Data & Analytics
### Inputs
* Target directory path
* Scaffold directory contents (bundled with package)
* User input for remediation option

### Outputs / Events
* List of detected conflicts (if any)
* Copy/backup operation results
* User's remediation choice

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|--------|---------|-------|
| conflicts_detected | Conflicts found during init | conflict_count, conflict_types | Track frequency of conflicts | CLI |
| remediation_chosen | User selects option | option (replace/backup/skip) | Track user preferences | CLI |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Conflict detection coverage | Quality | 0% | 100% of numbered prefix conflicts | Release | Tests |
| User remediation success | UX | N/A | Users resolve conflicts on first attempt | 30 days | Support tickets |

## 9. Dependencies
| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| pathlib | Library | High | Python stdlib | Low | Standard library, stable |
| Click | Library | High | External | Low | Already in use for CLI |
| shutil | Library | High | Python stdlib | Low | Standard library, stable |

## 10. Risks & Mitigations
| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Backup directory grows unbounded | Low | Medium | Document cleanup in docs, consider retention policy later | Dev | Open |
| R-002 | False positive conflict detection | Medium | Low | Conservative pattern matching, clear conflict explanation | Dev | Open |
| R-003 | Interactive prompt breaks CI/CD | High | Low | Force flag bypasses prompts, document CI usage | Dev | Open |

## 11. Privacy, Security & Compliance
### Data Classification
No sensitive data involved. Operates only on local filesystem.

### PII Handling
N/A - No personal data processed.

### Threat Considerations
* Path traversal: Backup destination validated to be within `.agent-tracking/`
* Symlink attacks: Use `shutil.move()` which handles symlinks safely

## 12. Operational Considerations
| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Part of `teambot` package | No separate deployment |
| Rollback | N/A - CLI command | Users can restore from backup |
| Monitoring | N/A - CLI tool | No runtime monitoring needed |
| Alerting | N/A | |
| Support | Document in CLI help and user guide | |
| Capacity Planning | N/A | Local filesystem only |

## 13. Rollout & Launch Plan
### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|--------------|-------|
| Implementation | TBD | All tests pass, code review approved | Builder |
| Documentation | TBD | User guide updated | Writer |
| Release | TBD | Merged to main | PM |

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| - | - | - | - | - |

## 15. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-03-10 | BA Agent | Initial specification | Creation |

## 16. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Code | src/teambot/scaffolds.py | Current scaffold copy logic | N/A |
| REF-002 | Code | src/teambot/cli.py:691-770 | Current cmd_init() implementation | N/A |
| REF-003 | Code | src/teambot/prompt_sync.py | SDD prompt sync logic | N/A |

## 17. Acceptance Test Scenarios

### AT-001: Simple Conflict Detection
**Description**: User runs init when `.agent/` contains files with conflicting numbered prefixes
**Preconditions**: Directory `.agent/commands/sdd/` exists with `sdd.4-old-planner.prompt.md`
**Steps**:
1. User runs `teambot init`
2. System detects conflict with scaffold `sdd.4-task-planner-for-feature.prompt.md`
3. System displays conflict summary listing both files
4. System prompts for remediation choice
**Expected Result**: User sees clear conflict explanation and 3 remediation options
**Verification**: Prompt displays correctly, options are selectable

### AT-002: Backup Option Creates Valid Backup
**Description**: User chooses backup option during conflict resolution
**Preconditions**: `.agent/` exists with customized files
**Steps**:
1. User runs `teambot init`
2. Conflict detected, user selects "Backup" option
3. System moves `.agent/` to `.agent-tracking/backups/<timestamp>/`
4. System copies new scaffolds to `.agent/`
**Expected Result**: Backup created with timestamp, new scaffolds in place
**Verification**: Both directories exist with correct contents

### AT-003: Replace Option Clears Directory
**Description**: User chooses replace option (equivalent to --force)
**Preconditions**: `.agent/` exists with old files
**Steps**:
1. User runs `teambot init`
2. Conflict detected, user selects "Replace" option
3. System clears `.agent/` and copies new scaffolds
**Expected Result**: `.agent/` contains only new scaffold files
**Verification**: Old files removed, new files present

### AT-004: Skip Option Preserves Existing
**Description**: User chooses to skip and keep existing files
**Preconditions**: `.agent/` exists with user's customized files
**Steps**:
1. User runs `teambot init`
2. Conflict detected, user selects "Skip" option
3. System continues without modifying `.agent/`
**Expected Result**: `.agent/` unchanged, warning displayed
**Verification**: Files unchanged, warning in output

### AT-005: Force Flag Bypasses Prompt
**Description**: Using --force skips interactive conflict detection
**Preconditions**: `.agent/` exists with conflicting files
**Steps**:
1. User runs `teambot init --force`
2. System replaces files without prompting
**Expected Result**: No interactive prompt, files replaced directly
**Verification**: No prompt displayed, new scaffolds in place

### AT-006: No Conflict When Patterns Match
**Description**: Init proceeds normally when no conflicts exist
**Preconditions**: `.agent/` is empty or contains non-conflicting files
**Steps**:
1. User runs `teambot init`
2. System copies scaffolds normally
**Expected Result**: Normal init behavior, no conflict prompt
**Verification**: Files copied, success message displayed

## 18. Appendices
### Glossary
| Term | Definition |
|------|-----------|
| Scaffold | Template files bundled with TeamBot for project initialization |
| Numbered prefix | Pattern like `sdd.4-` at start of filename indicating file version/order |
| Conflict | When existing file and scaffold have same numbered prefix but different names |

### Technical Notes
**Conflict Detection Algorithm**:
1. List all `*.prompt.md` files in existing `.agent/commands/sdd/`
2. Extract numbered prefix (e.g., `sdd.4-` from `sdd.4-old-name.prompt.md`)
3. Compare against scaffold prefixes
4. Report conflicts where prefix matches but full name differs

**Backup Directory Structure**:
```
.agent-tracking/
└── backups/
    └── 20260310-221500/
        └── .agent/
            └── commands/
                └── sdd/
                    └── sdd.4-old-planner.prompt.md
```

Generated 2026-03-10T22:15:00Z by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
