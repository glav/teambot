<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Worktree Workflow Enhancement - Feature Specification Document
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
TeamBot's `--worktree` option creates isolated Git worktrees for development tasks, enabling parallel work without branch switching. The current implementation validates objective file existence in the source repository but fails to migrate the file to the newly created worktree, causing workflow failures.

### Core Opportunity
Enable seamless worktree workflows where objective files are automatically available in the newly created worktree, regardless of their commit status in the source repository. Additionally, provide flexibility for users to specify the base branch for worktree creation.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Automatically copy objective files to worktrees when missing | Feature | Manual copy required | Automatic copy | v0.2.0 | P0 |
| G-002 | Support staged (uncommitted) objective files in worktree workflow | Feature | Only committed files work | Staged + committed | v0.2.0 | P0 |
| G-003 | Allow users to specify base branch for worktree creation | Feature | Current branch only | User-specified branch | v0.2.0 | P1 |
| G-004 | Maintain backward compatibility with existing worktree workflows | Quality | Current behavior | No breaking changes | v0.2.0 | P0 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Improve worktree reliability | Zero failures due to missing objective files | P0 | Builder |
| Enhance worktree flexibility | Users can specify any local branch as base | P1 | Builder |
| Ensure quality | 80%+ unit test coverage on new code | P0 | Reviewer |

## 2. Problem Definition

### Current Situation
TeamBot's `--worktree` option provides isolated development environments but has a critical gap:

1. **Validation timing**: Objective file existence is checked at lines 627-630 in `cli.py` *before* worktree creation
2. **Directory change**: After worktree creation, `os.chdir(worktree_path)` changes the working directory (line 641)
3. **Path resolution failure**: Relative objective paths become invalid in the new context
4. **No migration**: The objective file is never copied to the worktree

### Problem Statement
When a user runs `teambot run --worktree objective.md`, the worktree is created successfully, but execution fails because the objective file does not exist in the worktree. This forces users to manually copy files or use absolute paths, degrading the developer experience.

### Root Causes
* Objective file validation occurs in source repository context before worktree creation
* No path re-resolution or file migration after `chdir` to worktree
* Worktree branches from current HEAD, which may not contain the objective file
* No mechanism to specify an alternate base branch

### Impact of Inaction
* Developers experience silent failures after worktree creation
* CI/CD pipelines fail unpredictably with relative paths
* Teams cannot leverage worktrees for new objectives (staged files)
* Manual workarounds degrade developer productivity

## 3. Users & Personas
| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| Solo Developer | Work on multiple features in parallel using worktrees | Worktree creation succeeds but run fails; must manually copy files | High - daily workflow disruption |
| Team Lead | Automate feature branch workflows with CI/CD | Pipelines fail when objectives use relative paths | High - CI reliability |
| New Contributor | Quickly start working on assigned tasks | Confusion when worktree command appears to succeed but fails later | Medium - onboarding friction |

### Journeys
**Current Journey (Broken)**:
1. Developer creates `objectives/feature-x.md`
2. Runs `teambot run --worktree objectives/feature-x.md`
3. Worktree created at `.teambot-worktrees/feat-feature-x/`
4. TeamBot changes to worktree directory
5. ❌ Objective file not found → execution fails

**Target Journey (Fixed)**:
1. Developer creates `objectives/feature-x.md`
2. Runs `teambot run --worktree objectives/feature-x.md`
3. Worktree created at `.teambot-worktrees/feat-feature-x/`
4. TeamBot detects objective missing in worktree
5. ✅ Objective copied from source → execution continues

## 4. Scope

### In Scope
* Detecting when objective file is missing in worktree after creation
* Copying objective file from source repository to worktree (committed or staged)
* Handling working directory file content (not just staged content)
* Adding `--base-branch` CLI option for worktree base specification
* Logging/output messages when file copy occurs
* Cross-platform compatibility (Linux, macOS, Windows)
* Respecting Windows 260-character path limit validation
* Creating parent directories in worktree if needed

### Out of Scope (justified)
* **Syncing other files**: Beyond current scope; objective file is the critical path item
* **Automatic worktree cleanup**: Separate feature; no user request
* **Multiple objective files**: TeamBot currently operates on single objective per run
* **Remote branch support for `--base-branch`**: Adds complexity; local branches sufficient for MVP

### Assumptions
* Git CLI is installed and available on PATH
* Commands are run from within a valid Git repository
* User has read/write permissions in both source repo and worktree location
* Objective file path is provided as a CLI argument (not auto-discovered)

### Constraints
* Must use Python 3.11+ features only
* Must integrate with existing Click CLI framework
* Must not modify Git repository state (no auto-commits)
* Must pass existing test suite without regression
* Must respect Windows 260-character path validation already in place

## 5. Product Overview

### Value Proposition
For TeamBot users who work with Git worktrees, this enhancement eliminates manual file management by automatically ensuring objective files are available in newly created worktrees, enabling immediate productivity.

### Differentiators
* Zero-friction worktree workflows—objective files "just work"
* Support for in-progress work (staged files copied to worktree)
* Flexible base branch selection for advanced workflows

### UX / UI
This is a CLI enhancement. User interaction:

```bash
# Basic usage (unchanged, but now works reliably)
teambot run --worktree objectives/my-task.md

# New option: specify base branch
teambot run --worktree --base-branch main objectives/my-task.md

# Output when file is copied
[INFO] Objective file copied to worktree: .teambot-worktrees/feat-my-task/objectives/my-task.md
```

UX Status: CLI-only, no visual UI required

## 6. Functional Requirements
| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Detect missing objective in worktree | After worktree creation and directory change, check if objective file exists at the resolved path | G-001 | All | P0 | File existence check returns False when file missing | Runs after `os.chdir()` |
| FR-002 | Copy objective from source repo | When objective missing in worktree, copy file content from source repository to worktree | G-001, G-002 | All | P0 | File copied with identical content; parent dirs created | Use `shutil.copy2` to preserve metadata |
| FR-003 | Handle staged objective files | Copy working directory version of objective file (handles staged + modified) | G-002 | Solo Dev | P0 | Staged-only and modified files copied correctly | Read from filesystem, not Git index |
| FR-004 | Log file copy operations | Output INFO-level message when objective file is copied to worktree | G-001 | All | P1 | Log message includes source and destination paths | Use existing logging infrastructure |
| FR-005 | Add --base-branch option | New CLI option to specify which branch the worktree should be based on | G-003 | Team Lead | P1 | `git worktree add -b <new> --base=<base>` | Validates branch exists before use |
| FR-006 | Validate base branch exists | Before worktree creation, verify specified base branch exists locally | G-003 | All | P1 | Clear error message if branch not found | Use `git rev-parse --verify` |
| FR-007 | Preserve backward compatibility | When no `--base-branch` specified, use current behavior (branch from HEAD) | G-004 | All | P0 | Existing commands work identically | No default value change |
| FR-008 | Create parent directories | If objective file path includes subdirectories, create them in worktree before copy | G-001 | All | P0 | `mkdir -p` equivalent behavior | Use `pathlib.Path.mkdir(parents=True)` |

### Feature Hierarchy
```plain
Worktree Workflow Enhancement
├── Objective File Migration
│   ├── FR-001: Detect missing objective
│   ├── FR-002: Copy from source
│   ├── FR-003: Handle staged files
│   ├── FR-004: Log copy operations
│   └── FR-008: Create parent directories
├── Base Branch Selection
│   ├── FR-005: --base-branch option
│   └── FR-006: Branch validation
└── Compatibility
    └── FR-007: Backward compatibility
```

## 7. Non-Functional Requirements
| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Performance | File copy operation should be imperceptible | < 100ms for typical objective file | P1 | Benchmark with 10KB file | Objective files typically < 50KB |
| NFR-002 | Reliability | File copy must not corrupt content | Byte-for-byte identical | P0 | Hash comparison in tests | Use `shutil.copy2` |
| NFR-003 | Maintainability | New code follows existing patterns | Consistent with `worktree/manager.py` style | P1 | Code review checklist | Use `pathlib` throughout |
| NFR-004 | Compatibility | Works on Linux, macOS, Windows | Tests pass on all platforms | P0 | CI matrix testing | GitHub Actions matrix |
| NFR-005 | Compatibility | Respects Windows path limits | Path validation before file ops | P0 | Unit tests with long paths | Use existing validation |
| NFR-006 | Observability | Copy operations are traceable | INFO log with source/dest paths | P1 | Log verification in tests | Standard Python logging |
| NFR-007 | Testability | Unit test coverage on new code | ≥ 80% line coverage | P0 | pytest-cov report | TDD approach |

## 8. Data & Analytics

### Inputs
* Objective file path (CLI argument)
* Source repository root path
* Worktree destination path
* Optional: `--base-branch` value

### Outputs / Events
* Copied objective file in worktree
* Log messages for copy operations
* Error messages for failures

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|--------|---------|-------|
| `worktree.objective.copied` | File successfully copied | `{source, dest, size_bytes}` | Track feature usage | Builder |
| `worktree.objective.already_exists` | File exists in worktree | `{path}` | Track no-op cases | Builder |
| `worktree.base_branch.specified` | User provides --base-branch | `{branch_name}` | Track option adoption | Builder |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Worktree success rate | Reliability | Unknown (failures not tracked) | 100% for valid inputs | Per release | Test suite |
| Test coverage (new code) | Quality | N/A | ≥ 80% | Per PR | pytest-cov |
| Backward compatibility | Quality | All tests pass | All tests pass | Per PR | CI pipeline |

## 9. Dependencies
| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| Git CLI | External | Critical | System | Low - ubiquitous | Fail fast with clear error |
| Click CLI | Internal | High | TeamBot | Low - stable | Pin version in pyproject.toml |
| Existing worktree manager | Internal | High | TeamBot | Low - well-tested | Extend, don't replace |
| pathlib (stdlib) | Internal | Medium | Python | None | Standard library |
| shutil (stdlib) | Internal | Medium | Python | None | Standard library |

## 10. Risks & Mitigations
| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Path handling differs across platforms | High | Medium | Use `pathlib` consistently; test on all platforms via CI | Builder | Open |
| R-002 | File permission issues on copy | Medium | Low | Preserve permissions with `shutil.copy2`; log errors clearly | Builder | Open |
| R-003 | Race condition with staged files | Low | Low | Copy file content directly, not Git index reference | Builder | Open |
| R-004 | Worktree creation fails but file already copied | Medium | Low | Create directories; copy file only after successful worktree creation | Builder | Open |
| R-005 | Objective file larger than expected | Low | Low | No size limit; trust user's file; log size in metrics | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
* Objective files: User-generated content, potentially containing project details
* No PII expected in standard usage
* Files remain local to user's filesystem

### PII Handling
N/A - No PII collection or processing

### Threat Considerations
* **Path traversal**: Validate objective path doesn't escape repository root
* **Symlink attacks**: Use `pathlib.resolve()` to canonicalize paths
* **Permission escalation**: Copy preserves source permissions, no elevation

### Regulatory / Compliance
N/A - Local CLI tool with no network transmission of user data

## 12. Operational Considerations
| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Standard pip/uv install | No additional dependencies |
| Rollback | Previous version via pip | Version pinning supported |
| Monitoring | Local logs only | INFO level for copy operations |
| Alerting | N/A | Local CLI tool |
| Support | GitHub Issues | Standard TeamBot support channel |
| Capacity Planning | N/A | Local file operations only |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|--------------|-------|
| Development | TBD | All FRs implemented | Builder |
| Testing | TBD | 80%+ coverage, all tests pass | Reviewer |
| Documentation | TBD | README updated, CHANGELOG entry | Writer |
| Release | TBD | PR merged to main | PM |

### Feature Flags
N/A - Feature is additive and backward compatible; no flag needed

### Communication Plan
* CHANGELOG entry describing new behavior
* README update for `--base-branch` option

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| (none) | All questions resolved during problem analysis | - | - | Resolved |

## 15. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-02-24 | BA Agent | Initial specification created | Creation |

## 16. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Analysis | `src/teambot/cli.py:599-666` | Worktree creation flow | N/A |
| REF-002 | Analysis | `src/teambot/worktree/manager.py` | WorktreeContext, create_worktree() | N/A |
| REF-003 | Requirements | User objective | Goals and success criteria | N/A |
| REF-004 | Internal | Problem statement | Root cause analysis | N/A |

### Citation Usage
* FR-001 derived from REF-001 analysis (line 627-630 validation timing)
* Root causes derived from REF-002 analysis (manager.py behavior)
* Goals and scope derived from REF-003 (user objective)

## 17. Appendices

### Glossary
| Term | Definition |
|------|-----------|
| Worktree | A Git feature allowing multiple working directories attached to a single repository |
| Source repository | The original Git repository where the command is executed |
| Objective file | A markdown file defining the development task for TeamBot |
| Staged file | A file added to Git's staging area but not yet committed |
| Base branch | The branch from which a new worktree branch is created |

### Additional Notes
* Implementation should follow TDD approach as specified in objective
* Existing worktree tests in `tests/test_worktree/` provide patterns to follow

---

## Acceptance Test Scenarios

### AT-001: Automatic Copy - Committed Objective File
**Description**: User creates worktree with committed objective file that doesn't exist in worktree
**Preconditions**: Git repository with committed objective file `objectives/task.md` on current branch
**Steps**:
1. User runs `teambot run --worktree objectives/task.md`
2. Worktree is created at `.teambot-worktrees/feat-task/`
3. TeamBot detects objective file missing in worktree
4. TeamBot copies objective file to worktree
**Expected Result**: Objective file exists at `.teambot-worktrees/feat-task/objectives/task.md` with identical content
**Verification**: File hash matches source; INFO log message confirms copy

### AT-002: Automatic Copy - Staged But Uncommitted Objective File
**Description**: User creates worktree with a newly staged (not committed) objective file
**Preconditions**: Git repository; `objectives/new-task.md` created and staged but not committed
**Steps**:
1. User runs `git add objectives/new-task.md` (file staged)
2. User runs `teambot run --worktree objectives/new-task.md`
3. Worktree is created (file won't exist because not in any branch)
4. TeamBot copies working directory version to worktree
**Expected Result**: Worktree contains `objectives/new-task.md` with working directory content
**Verification**: File content matches source repository working directory version

### AT-003: Base Branch Specification
**Description**: User specifies a different base branch for worktree creation
**Preconditions**: Git repository with `main` and `develop` branches; currently on `develop`
**Steps**:
1. User runs `teambot run --worktree --base-branch main objectives/task.md`
2. Worktree is created branching from `main` instead of `develop`
**Expected Result**: New branch is based on `main`; `git log` shows `main` as ancestor
**Verification**: `git merge-base` confirms `main` is ancestor of worktree branch

### AT-004: Invalid Base Branch Error
**Description**: User specifies a non-existent base branch
**Preconditions**: Git repository; branch `nonexistent` does not exist
**Steps**:
1. User runs `teambot run --worktree --base-branch nonexistent objectives/task.md`
**Expected Result**: Clear error message: "Branch 'nonexistent' not found"
**Verification**: Exit code non-zero; no worktree created

### AT-005: Backward Compatibility - Objective Exists in Worktree
**Description**: Existing behavior preserved when objective file already exists in worktree
**Preconditions**: Git repository; objective file committed and present on all branches
**Steps**:
1. User runs `teambot run --worktree objectives/task.md`
2. Worktree is created (file exists because it's committed)
**Expected Result**: No file copy occurs; no copy log message; execution proceeds normally
**Verification**: No "copied" log message; original worktree creation behavior

### AT-006: Cross-Platform Path Handling
**Description**: Path handling works correctly on Windows with subdirectories
**Preconditions**: Windows system; objective file at `objectives/features/task.md`
**Steps**:
1. User runs `teambot run --worktree objectives/features/task.md`
2. Worktree created; subdirectory `objectives/features/` must be created
3. Objective file copied to correct location
**Expected Result**: `objectives/features/task.md` exists in worktree
**Verification**: Path separators correct for OS; parent directories created

---

Generated 2026-02-24T00:36:00Z by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
