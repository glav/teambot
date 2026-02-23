# Business Problem Statement: Worktree Isolation for TeamBot

## Problem Definition

### Current State

TeamBot currently executes all objectives within the user's main working directory. When running `teambot run objectives/my-feature.md`, all generated files, branch changes, and workflow state are created directly in the active checkout. This creates several friction points:

1. **Blocked Parallel Development**: A user cannot start Feature B while Feature A is still in progress or under review. The working directory is "occupied" by Feature A's uncommitted changes and state.

2. **Risk of Cross-Contamination**: Workflow state files (`.teambot/`) and generated code from one objective may interfere with another, leading to confusing state or merge conflicts.

3. **Manual Worktree Management**: Power users who want isolation must manually create worktrees, navigate to them, and track which worktree corresponds to which objective—defeating TeamBot's automation promise.

4. **Interrupted Workflow Recovery**: If a user needs to context-switch urgently, they must either commit incomplete work, stash changes, or abandon the objective—all requiring manual intervention.

### Impact

| Stakeholder | Impact |
|-------------|--------|
| **Individual Developers** | Cannot multitask across features; must wait for one objective to complete before starting another |
| **Teams Using TeamBot** | Reduced velocity when multiple features need parallel development |
| **CI/Automation Users** | Cannot queue multiple objectives for autonomous execution without manual worktree orchestration |

### Root Cause

TeamBot lacks built-in **workspace isolation**. The tool assumes a single active objective at a time and does not manage Git worktrees or branch context automatically.

---

## Business Goals

### Primary Goal

Enable **isolated, parallel objective execution** by integrating Git worktree management into the `teambot run` workflow, so users can start multiple features without manual branch/worktree handling.

### Supporting Goals

1. **Zero Impact on Main Directory**: When `--worktree` is used, the user's current checkout remains untouched—no new files, no branch switches, no uncommitted changes.

2. **Seamless Resume Capability**: If an objective is interrupted, `teambot run --resume` should work correctly within the worktree context without manual navigation.

3. **Clear Visual Feedback**: Users must always know whether they are operating in a worktree and which branch/feature they are working on—both in interactive REPL mode and file-based orchestration output.

4. **Foundation for Autonomous Multi-Objective Execution**: This feature is the first step toward a future where users can run `teambot run objectives/*.md --worktree` and TeamBot delivers all features autonomously.

---

## Success Criteria

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-1 | Worktree creation | `teambot run objectives/foo.md --worktree` creates a worktree at `.teambot-worktrees/<branch-name>/` and runs the objective within it |
| FR-2 | Branch naming (auto) | Branch name derived from objective filename (e.g., `objective-foo.md` → `feat/foo`) |
| FR-3 | Branch naming (explicit) | `--branch <name>` flag allows user to specify branch name |
| FR-4 | State isolation | History and state files are scoped to the worktree (no cross-contamination) |
| FR-5 | Worktree persistence | On success or failure, worktree remains for user review/debugging |
| FR-6 | Resume support | `teambot run --resume` works within worktree context |
| FR-7 | Backward compatibility | Running without `--worktree` behaves exactly as today |
| FR-8 | Interactive indicator | REPL prompt/status bar shows worktree context (e.g., `[worktree: feat/my-feature]`) |
| FR-9 | File-based indicator | Stage output header includes worktree context (e.g., `Stage: IMPLEMENTATION [worktree: feat/my-feature]`) |

### Error Handling Requirements

| ID | Scenario | Expected Behavior |
|----|----------|-------------------|
| ER-1 | Git not available | Clear error message: "Git is required for --worktree mode but was not found" |
| ER-2 | Branch already exists | Fail with message: "Branch 'feat/foo' already exists. Use --branch to specify a different name or delete the existing branch" |
| ER-3 | Worktree creation fails | Surface Git's error message with context about what was attempted |
| ER-4 | Uncommitted changes in main | Allow worktree creation (worktrees are independent); optionally warn user |
| ER-5 | Path length exceeded (Windows) | Detect and fail early with guidance on shorter branch names |

### Non-Functional Requirements

| ID | Requirement | Criteria |
|----|-------------|----------|
| NF-1 | Cross-platform | Works on Linux, macOS, Windows (Git Bash) |
| NF-2 | Minimal dependencies | Use subprocess to Git CLI; no new heavy dependencies |
| NF-3 | Test coverage | Unit tests for worktree logic; acceptance test with real Git operations |
| NF-4 | Documentation | CLI help, README section, usage guide |

---

## Scope

### In Scope

- `--worktree` flag for `teambot run`
- `--branch <name>` flag for explicit branch naming
- Worktree creation at `.teambot-worktrees/<branch>/`
- Branch creation (new branch from current HEAD)
- State isolation (`.teambot/` scoped to worktree)
- Visual indicators in REPL and file-based output
- Error handling for common Git scenarios
- Documentation updates

### Out of Scope (Future Work)

- Automatic cleanup of merged worktrees
- Parallel execution of multiple objectives in a single command
- Integration with PR creation workflow
- Worktree management commands (`teambot worktree list`, `teambot worktree delete`)
- Support for worktrees based on existing remote branches

---

## Assumptions

1. **Git is installed** on all systems where TeamBot runs with `--worktree`
2. **Users have write access** to the repository root to create `.teambot-worktrees/`
3. **The repository is not bare** (worktrees cannot be created in bare repos)
4. **Objective files exist** relative to the main working directory and are copied/accessible from worktrees
5. **Users will manually merge or delete worktrees** after reviewing completed objectives

---

## Dependencies

| Dependency | Type | Risk |
|------------|------|------|
| Git CLI (`git worktree` command) | External | Low—Git 2.5+ required; widely available |
| File system permissions | Environment | Low—same permissions as current TeamBot usage |
| Existing `cli.py` command structure | Internal | Low—well-defined extension point |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Windows path length limits | Medium | Medium | Validate path length before creation; suggest shorter names |
| User confusion about worktree state | Medium | Low | Clear visual indicators; documentation |
| Nested Git repos edge case | Low | Medium | Detect and warn; fail gracefully |
| Disk space accumulation from old worktrees | Medium | Low | Document cleanup; consider future `teambot worktree clean` |

---

## Measurable Goals

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Feature adoption | 20% of `teambot run` invocations use `--worktree` within 30 days of release | CLI telemetry (if implemented) or user feedback |
| Error rate | <5% of `--worktree` invocations fail due to preventable errors | Error logging and user reports |
| Test coverage | ≥90% for new worktree module | pytest coverage report |
| User satisfaction | No "worktree-related" issues filed within 14 days | GitHub Issues tracking |

---

## Appendix: User Story

> **As a** developer using TeamBot,  
> **I want to** run an objective in an isolated Git worktree,  
> **So that** I can work on multiple features in parallel without branch conflicts or uncommitted file clashes in my main working directory.

### Example Workflow

```bash
# Start Feature A in a worktree
$ teambot run objectives/feature-a.md --worktree
# TeamBot creates .teambot-worktrees/feat/feature-a/ and runs there

# While Feature A is in progress, start Feature B
$ teambot run objectives/feature-b.md --worktree
# TeamBot creates .teambot-worktrees/feat/feature-b/ and runs there

# Review Feature A's output
$ cd .teambot-worktrees/feat/feature-a/
$ git log --oneline
# Merge when ready
$ git checkout main && git merge feat/feature-a
```

---

*Document Version: 1.0*  
*Stage: BUSINESS_PROBLEM*  
*Author: Business Analyst Agent*
