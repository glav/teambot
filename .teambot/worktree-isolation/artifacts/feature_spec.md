<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# TeamBot Worktree Isolation - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target v0.2.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-23 |
| Problem & Users | ✅ | None | 2026-02-23 |
| Scope | ✅ | None | 2026-02-23 |
| Requirements | ✅ | None | 2026-02-23 |
| Metrics & Risks | ✅ | None | 2026-02-23 |
| Operationalization | ✅ | None | 2026-02-23 |
| Finalization | ✅ | None | 2026-02-23 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot is a CLI tool that orchestrates collaborative multi-agent AI workflows for software development. Currently, all objectives execute within the user's main working directory, limiting users to one active objective at a time and requiring manual worktree management for parallel feature development.

### Core Opportunity
Enable isolated, parallel objective execution by integrating Git worktree management into the `teambot run` workflow. This unlocks the ability to start multiple features simultaneously without branch conflicts, uncommitted file clashes, or manual worktree orchestration—laying the foundation for autonomous multi-objective execution.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Enable parallel feature development without manual worktree management | Business | 0 concurrent objectives | Unlimited concurrent objectives | Release | P0 |
| G-002 | Zero impact on main working directory when using worktree mode | User Experience | Main dir always modified | Main dir unchanged | Release | P0 |
| G-003 | Seamless resume capability within worktree context | Reliability | Resume requires manual navigation | Resume auto-detects context | Release | P1 |
| G-004 | Clear visual feedback of worktree/branch context | Usability | No context shown | Always visible in REPL and stage headers | Release | P1 |

### Objectives (Optional)
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Foundation for multi-objective | Single worktree mode working reliably | P0 | Builder |
| Cross-platform support | Works on Linux, macOS, Windows | P0 | Builder |

## 2. Problem Definition

### Current Situation
TeamBot executes all objectives within the user's main working directory. When running `teambot run objectives/my-feature.md`:
- All generated files are created in the active checkout
- Branch changes occur in the main repository
- Workflow state files (`.teambot/`) are shared across all objectives
- Users must wait for Feature A to complete before starting Feature B

### Problem Statement
**Developers using TeamBot cannot work on multiple features in parallel** because the tool lacks workspace isolation. This forces sequential feature development, blocks context-switching, and requires manual Git worktree management for users who need isolation—defeating TeamBot's automation promise.

### Root Causes
* TeamBot assumes a single active objective at a time
* No integration with Git worktree functionality
* State files (`.teambot/`) are not scoped to specific objectives or branches
* CLI does not support directory/context switching during execution

### Impact of Inaction
- **Velocity loss**: Teams wait for one feature to complete before starting another
- **Manual overhead**: Power users must manage worktrees manually, negating automation benefits
- **CI limitations**: Cannot queue multiple autonomous objectives without custom orchestration
- **Competitive disadvantage**: Other AI dev tools may offer parallel execution first

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| **Solo Developer** | Run multiple objectives for different features while one is in review | Must wait for PR review before starting new work; loses context when switching | High - Primary user of parallel development |
| **Team Lead** | Queue objectives for overnight autonomous execution | Cannot batch multiple objectives; morning review requires manual worktree setup | Medium - Enables team productivity gains |
| **CI/Automation User** | Run TeamBot in CI pipelines for multiple features | Pipeline conflicts when parallel jobs modify same directory | Medium - Enables scalable automation |

### Journeys (Optional)
**Solo Developer Journey (Current)**:
1. Run `teambot run objectives/feature-a.md`
2. Feature A completes → creates PR
3. Wait for review (blocked)
4. After merge → run `teambot run objectives/feature-b.md`

**Solo Developer Journey (With Worktree)**:
1. Run `teambot run objectives/feature-a.md --worktree`
2. Feature A runs in isolated worktree
3. Immediately run `teambot run objectives/feature-b.md --worktree`
4. Both features develop in parallel
5. Review and merge independently

## 4. Scope

### In Scope
* `--worktree` flag for `teambot run` command
* `--branch <name>` flag for explicit branch naming
* Automatic worktree creation at `.teambot-worktrees/<branch-name>/`
* Automatic feature branch creation from current HEAD
* State isolation: `.teambot/` scoped to worktree directory
* Visual indicators in REPL prompt (e.g., `teambot [worktree: feat/foo] >`)
* Visual indicators in file-based stage headers (e.g., `Stage: IMPLEMENTATION [worktree: feat/foo]`)
* Resume support within worktree context (`teambot run --resume`)
* Error handling for Git unavailable, branch conflicts, path length limits
* Documentation: CLI help text, README section, usage guide

### Out of Scope (justify if empty)
* **Automatic cleanup of merged worktrees**: Future feature; users manually delete for now
* **Parallel execution of multiple objectives in single command**: Phase 2; this feature enables it
* **PR creation workflow integration**: Separate feature; worktree just provides isolation
* **Worktree management commands** (`teambot worktree list/delete`): Future convenience feature
* **Support for worktrees based on existing remote branches**: Requires fetch logic; add later

### Assumptions
* Git CLI (version 2.5+) is installed on all target systems
* Users have write access to repository root for `.teambot-worktrees/` directory
* Repository is not bare (worktrees cannot be created in bare repos)
* Objective files are accessible via relative paths from worktree (Git handles this)
* Users will manually merge and delete worktrees after reviewing completed objectives

### Constraints
* Must not modify main working directory when `--worktree` is used
* Must work on Linux, macOS, and Windows (Git Bash)
* Windows: Must validate path lengths do not exceed 260-character limit
* No new heavy dependencies (use subprocess to Git CLI, not GitPython)
* Branch name conflicts must fail with clear error (no automatic resolution)

## 5. Product Overview

### Value Proposition
**For** developers using TeamBot **who** need to work on multiple features simultaneously, **TeamBot Worktree Isolation** is a CLI enhancement **that** automatically creates and manages Git worktrees for each objective, **unlike** manual worktree management **which** requires multiple terminal commands and mental overhead to track which worktree maps to which feature.

### Differentiators (Optional)
* Automatic branch naming derived from objective filename
* State files automatically scoped to worktree (no configuration required)
* Visual indicators always show current worktree/branch context
* Seamless resume support within worktree context

### UX / UI (Conditional)
**REPL Prompt Enhancement**:
- Current: `teambot > `
- With worktree: `teambot [feat/my-feature] > ` or `teambot (worktree: feat/my-feature) > `

**Stage Header Enhancement** (file-based orchestration):
- Current: `━━━ 📋 @pm (task 1) ━━━`
- With worktree: `━━━ 📋 @pm (task 1) [worktree: feat/my-feature] ━━━`

UX Status: Design complete

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|-------------|-------|----------|----------|------------|-------|
| FR-001 | Worktree flag | `--worktree` flag triggers isolated execution mode | G-001, G-002 | All | P0 | `teambot run obj.md --worktree` creates worktree and runs objective within it | Core feature |
| FR-002 | Worktree location | Worktree created at `.teambot-worktrees/<branch-name>/` relative to repo root | G-002 | All | P0 | Worktree directory exists at expected path after command starts | Predictable location |
| FR-003 | Auto branch naming | Branch name derived from objective filename: `objective-foo.md` → `feat/foo` | G-001 | All | P0 | Branch name matches expected pattern for given filename | Convention over config |
| FR-004 | Explicit branch naming | `--branch <name>` flag overrides auto-derived branch name | G-001 | All | P1 | `--branch custom-name` creates branch `custom-name` | User control |
| FR-005 | State isolation | History and state files scoped to worktree's `.teambot/` directory | G-001, G-002 | All | P0 | Main directory's `.teambot/` unchanged; worktree has its own `.teambot/` | No cross-contamination |
| FR-006 | Worktree persistence | Worktree remains after completion (success or failure) for user review | G-001 | All | P0 | Directory exists after `teambot run` exits | User decides cleanup |
| FR-007 | Resume in worktree | `teambot run --resume` works within worktree context | G-003 | Solo Dev | P1 | Resume from worktree directory succeeds; resumes correct objective | Seamless recovery |
| FR-008 | Backward compatibility | Running without `--worktree` behaves exactly as current implementation | G-001 | All | P0 | All existing tests pass; no behavior change without flag | No regression |
| FR-009 | REPL worktree indicator | REPL prompt shows branch/worktree context when in worktree mode | G-004 | Solo Dev | P1 | Prompt includes `[feat/my-feature]` or similar | Visual clarity |
| FR-010 | Stage header indicator | File-based orchestration stage headers include worktree context | G-004 | All | P1 | Headers show `[worktree: feat/my-feature]` | Visual clarity |
| FR-011 | Git availability check | Detect if Git CLI is available before attempting worktree creation | G-001 | All | P0 | Clear error: "Git is required for --worktree mode but was not found" | Fast fail |
| FR-012 | Branch conflict detection | Detect if branch already exists and fail with guidance | G-001 | All | P0 | Error: "Branch 'feat/foo' already exists. Use --branch to specify a different name" | Prevent confusion |
| FR-013 | Path length validation | On Windows, validate total path length before worktree creation | G-001 | All | P1 | Error with guidance if path would exceed 260 chars | Windows support |

### Feature Hierarchy (Optional)
```plain
teambot run --worktree
├── Worktree Creation (FR-001, FR-002)
│   ├── Branch Naming (FR-003, FR-004)
│   ├── Validation (FR-011, FR-012, FR-013)
│   └── State Isolation (FR-005)
├── Execution Context
│   ├── Worktree Persistence (FR-006)
│   ├── Resume Support (FR-007)
│   └── Backward Compatibility (FR-008)
└── Visual Indicators
    ├── REPL Prompt (FR-009)
    └── Stage Headers (FR-010)
```

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Performance | Worktree creation should not significantly delay objective start | < 5 seconds on SSD | P1 | Timing test in acceptance suite | Git worktree add is fast |
| NFR-002 | Reliability | Worktree creation must be atomic (no partial state on failure) | 100% rollback on failure | P0 | Unit tests with failure injection | Clean failure handling |
| NFR-003 | Compatibility | Must work on Linux, macOS, Windows (Git Bash) | Passes CI on all platforms | P0 | Matrix CI build | Cross-platform |
| NFR-004 | Compatibility | Windows path length must not exceed 260 characters | Validation before creation | P1 | Unit test with long paths | Windows limitation |
| NFR-005 | Maintainability | New code follows existing project patterns | Uses subprocess pattern from review_iterator.py | P1 | Code review | Consistency |
| NFR-006 | Testability | Unit tests mock Git subprocess calls | 90%+ coverage on new module | P0 | pytest-cov report | Standard practice |
| NFR-007 | Testability | One acceptance test with real Git operations | Exercises full workflow in temp repo | P1 | Acceptance test passes | End-to-end validation |
| NFR-008 | Security | No secrets or credentials stored in worktree paths | Path contains only objective-derived names | P0 | Code review | Secure by design |
| NFR-009 | Observability | Worktree operations logged at DEBUG level | Log entries for create, switch, detect | P2 | Log inspection | Debugging support |

## 8. Data & Analytics (Conditional)

### Inputs
- Objective file path (to derive branch name)
- Optional `--branch` flag value
- Git repository state (current branch, existing branches)

### Outputs / Events
- Worktree directory created
- Branch created
- Objective execution artifacts (within worktree)

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|---------|---------|-------|
| worktree_created | After successful worktree creation | branch_name, worktree_path, objective_file | Track feature adoption | Telemetry |
| worktree_error | On worktree creation failure | error_type, error_message | Track error rate | Telemetry |
| worktree_resume | On successful resume in worktree | branch_name, stage_resumed | Track resume usage | Telemetry |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Feature adoption | Usage | 0% | 20% of `teambot run` invocations | 30 days post-release | CLI telemetry (if implemented) |
| Error rate | Quality | N/A | < 5% of worktree invocations fail preventably | Ongoing | Error logs |
| Test coverage | Quality | N/A | ≥ 90% for new worktree module | Release | pytest-cov |
| User issues | Quality | N/A | 0 worktree-related issues | 14 days post-release | GitHub Issues |

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| Git CLI (2.5+) | External | High | User environment | Low - widely available | Document requirement; validate at runtime |
| `cli.py` argument parsing | Internal | High | TeamBot | Low - well-defined extension point | Follow existing patterns |
| `orchestration/execution_loop.py` | Internal | High | TeamBot | Medium - requires path changes | Parameterize `teambot_dir` |
| `repl/loop.py` prompt rendering | Internal | Medium | TeamBot | Low - isolated change | Add optional context parameter |
| `tasks/formatting.py` header rendering | Internal | Medium | TeamBot | Low - isolated change | Add optional context parameter |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Windows 260-char path limit exceeded | Medium | Medium | Validate path length before creation; suggest shorter branch names | Builder | Open |
| R-002 | User confusion about which directory they're in | Low | Medium | Clear visual indicators in prompt and headers; documentation | Builder | Open |
| R-003 | Nested Git repositories (submodules) | Medium | Low | Detect and warn; document limitation | Builder | Open |
| R-004 | Disk space accumulation from old worktrees | Low | Medium | Document cleanup instructions; future `teambot worktree clean` | Builder | Open |
| R-005 | Git version too old (< 2.5) | Medium | Low | Version check at runtime with clear error | Builder | Open |
| R-006 | Worktree creation fails mid-operation | Medium | Low | Atomic operation pattern; rollback on failure | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
- **Branch names**: Derived from objective filenames (user content, not sensitive)
- **Worktree paths**: Local filesystem paths (no PII)
- **State files**: Same classification as existing `.teambot/` content

### PII Handling
No PII is collected or stored by this feature. Branch names and paths contain only objective-derived identifiers.

### Threat Considerations
- **Path traversal**: Branch names are sanitized to prevent directory traversal attacks
- **Symlink attacks**: Git worktree operations are trusted; no custom symlink handling
- **Command injection**: Branch names passed to subprocess are validated/escaped

### Regulatory / Compliance (Conditional)
| Regulation | Applicability | Action | Owner | Status |
|------------|---------------|--------|-------|--------|
| N/A | No regulatory requirements for local CLI tool | None | - | N/A |

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard `pip install` or `uv sync` | No new deployment considerations |
| Rollback | Remove `--worktree` flag usage | Feature is additive; existing behavior unchanged |
| Monitoring | DEBUG-level logging for worktree operations | Standard logging infrastructure |
| Alerting | N/A | Local CLI tool, no alerting infrastructure |
| Support | Document common issues in troubleshooting guide | FAQ for path limits, cleanup, etc. |
| Capacity Planning | Disk space for worktrees (full repo copy) | Document in usage guide |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|---------------|-------|
| Implementation | TBD | All functional requirements implemented | Builder |
| Testing | TBD | Unit tests pass, acceptance test passes, coverage ≥ 90% | Builder |
| Documentation | TBD | CLI help, README, usage guide updated | Writer |
| Review | TBD | Code review approved, post-implementation review complete | Reviewer |
| Release | TBD | All tests pass in CI, documentation merged | PM |

### Feature Flags (Conditional)
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|---------|-----------------|
| N/A | Feature is opt-in via `--worktree` flag | Disabled (requires flag) | N/A |

### Communication Plan (Optional)
- Update CHANGELOG with feature description
- Add section to README.md
- Create `docs/guides/worktree-usage.md`

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| - | None at this time | - | - | Resolved |

## 15. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-23 | BA Agent | Initial specification | Created |

## 16. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Artifact | `.teambot/worktree-isolation/artifacts/problem_statement.md` | Business problem definition, goals, requirements | Source of truth for business context |
| REF-002 | Code | `src/teambot/cli.py` | Current CLI structure, `teambot run` command | Implementation reference |
| REF-003 | Code | `src/teambot/orchestration/review_iterator.py` | Existing Git subprocess pattern | Implementation pattern |
| REF-004 | Code | `src/teambot/repl/loop.py` | REPL prompt rendering | Integration point |
| REF-005 | Code | `src/teambot/tasks/formatting.py` | Stage header formatting | Integration point |

### Citation Usage
All requirements derived from user objective and problem statement analysis. Implementation patterns based on existing codebase exploration.

## 17. Acceptance Test Scenarios

### AT-001: Basic Worktree Creation and Execution
**Description**: User runs objective with `--worktree` flag and objective executes in isolated worktree
**Preconditions**: Git repository with clean working directory; objective file exists
**Steps**:
1. User runs: `teambot run objectives/my-feature.md --worktree`
2. TeamBot creates branch `feat/my-feature` from current HEAD
3. TeamBot creates worktree at `.teambot-worktrees/feat/my-feature/`
4. TeamBot executes objective within worktree directory
5. Objective completes (success or failure)
**Expected Result**: Worktree exists with objective artifacts; main directory unchanged
**Verification**: 
- `.teambot-worktrees/feat/my-feature/` exists
- `.teambot-worktrees/feat/my-feature/.teambot/` contains state files
- Main directory's `.teambot/` unchanged from before command

### AT-002: Explicit Branch Naming
**Description**: User specifies custom branch name with `--branch` flag
**Preconditions**: Git repository; objective file exists
**Steps**:
1. User runs: `teambot run objectives/my-feature.md --worktree --branch custom-branch`
2. TeamBot creates branch `custom-branch` (not `feat/my-feature`)
3. TeamBot creates worktree at `.teambot-worktrees/custom-branch/`
**Expected Result**: Branch and worktree use explicit name
**Verification**: `git branch --list custom-branch` shows branch exists

### AT-003: Branch Conflict Error
**Description**: User attempts to create worktree with branch name that already exists
**Preconditions**: Branch `feat/existing` already exists in repository
**Steps**:
1. User runs: `teambot run objectives/existing.md --worktree`
2. TeamBot detects branch `feat/existing` already exists
**Expected Result**: Clear error message with guidance
**Verification**: Error message contains "Branch 'feat/existing' already exists" and suggests `--branch`

### AT-004: Resume in Worktree Context
**Description**: User resumes interrupted objective from within worktree
**Preconditions**: Worktree exists with partial objective state (interrupted execution)
**Steps**:
1. User navigates to `.teambot-worktrees/feat/my-feature/`
2. User runs: `teambot run --resume`
3. TeamBot detects worktree context and resumes from saved state
**Expected Result**: Execution continues from last saved stage
**Verification**: Stage output shows resumed stage, not restart from beginning

### AT-005: REPL Prompt Shows Worktree Context
**Description**: Interactive mode shows worktree/branch in prompt
**Preconditions**: Running in worktree mode (interactive)
**Steps**:
1. User runs: `teambot run --worktree` (no objective, interactive mode)
2. REPL starts within worktree
3. User observes prompt
**Expected Result**: Prompt includes branch indicator
**Verification**: Prompt displays `[feat/my-feature]` or `(worktree: feat/my-feature)`

### AT-006: Backward Compatibility (No Worktree Flag)
**Description**: Running without `--worktree` behaves exactly as before
**Preconditions**: Standard Git repository; objective file exists
**Steps**:
1. User runs: `teambot run objectives/my-feature.md` (no `--worktree`)
2. Objective executes in main working directory
**Expected Result**: No worktree created; state in main `.teambot/`
**Verification**: 
- `.teambot-worktrees/` does not exist
- `.teambot/` in main directory contains state files

### AT-007: Git Not Available Error
**Description**: Attempting `--worktree` when Git is not installed
**Preconditions**: Git CLI not in PATH
**Steps**:
1. User runs: `teambot run objectives/my-feature.md --worktree`
**Expected Result**: Clear error message about Git requirement
**Verification**: Error message contains "Git is required for --worktree mode"

## 18. Appendices (Optional)

### Glossary
| Term | Definition |
|------|------------|
| Worktree | A linked working directory attached to a Git repository, allowing multiple branches to be checked out simultaneously |
| Objective | A markdown file defining a development task for TeamBot to execute |
| Feature branch | A Git branch created for developing a specific feature, typically named `feat/<name>` |

### Branch Naming Convention
| Objective Filename | Derived Branch Name |
|--------------------|---------------------|
| `my-feature.md` | `feat/my-feature` |
| `objective-foo.md` | `feat/foo` |
| `add-login-page.md` | `feat/add-login-page` |
| `fix-bug-123.md` | `feat/fix-bug-123` |

### CLI Usage Examples
```bash
# Basic worktree usage
teambot run objectives/my-feature.md --worktree

# Explicit branch name
teambot run objectives/my-feature.md --worktree --branch feat/custom-name

# Resume in worktree (from within worktree directory)
cd .teambot-worktrees/feat/my-feature/
teambot run --resume

# Check worktree status
ls -la .teambot-worktrees/
git worktree list
```

### Additional Notes
- This feature is the foundation for future autonomous multi-objective execution
- Worktree cleanup is intentionally left to users to allow review before deletion
- State isolation ensures no cross-contamination between parallel objectives

---
Generated 2026-02-23 by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
