## Objective

- Enable TeamBot to run objectives in isolated Git worktrees, providing clean branch separation and laying the foundation for parallel multi-feature development.

**Goal**:

- Add a `--worktree` flag to `teambot run` that automatically creates a Git worktree for the objective, runs the entire workflow within that worktree, and leaves the user's main working directory untouched.
- This is the **first step** toward autonomous multi-feature development where a user can specify multiple objectives and TeamBot delivers them all without manual intervention.
- The worktree approach solves the isolation problem: Feature B can be started while Feature A is still in review, without branch conflicts or uncommitted file clashes.

**Problem Statement**:

- Currently, TeamBot runs objectives in the user's main working directory, meaning:
  - Only one objective can run at a time per clone.
  - Uncommitted changes in the working directory may conflict with objective work.
  - Starting a new feature requires the previous one to be fully merged or stashed.
- Git worktrees provide a lightweight solution: multiple working directories from a single repository, each on a different branch.
- By integrating worktrees into TeamBot, we enable parallel development workflows without requiring users to manually manage multiple clones.

**Success Criteria**:
- [ ] `teambot run objectives/foo.md --worktree` creates a worktree, feature branch, and runs the objective there.
- [ ] The worktree is created at `.teambot-worktrees/<branch-name>/` relative to the repository root.
- [ ] The feature branch name is derived from the objective filename by default (e.g., `objective-foo.md` → `feat/foo`).
- [ ] An optional `--branch <name>` flag allows explicit branch naming.
- [ ] TeamBot's history and state files are scoped to the worktree (no cross-contamination with main directory).
- [ ] On successful completion, the worktree remains for user review; user decides when to merge/delete.
- [ ] On failure or interruption, the worktree remains intact for debugging; `teambot run --resume` works within the worktree context.
- [ ] Running without `--worktree` behaves exactly as today (no regression).
- [ ] Clear error messages if Git is not available, worktree creation fails, or branch already exists.
- [ ] **Interactive CLI indicator**: When running in worktree mode, the REPL prompt or status bar displays the branch name and/or a visual indicator (e.g., `[worktree: feat/my-feature]` or branch name in prompt).
- [ ] **File-based orchestration indicator**: When running file-based orchestration in worktree mode, the stage output header includes worktree context (e.g., `Stage: IMPLEMENTATION [worktree: feat/my-feature]` or similar).
- [ ] Documentation updated: CLI help, README, and a brief guide on worktree usage.
- [ ] All existing tests pass; new tests cover worktree creation, branch naming, error cases, and resume behaviour.

---

## Technical Context

**Target Codebase**:

- TeamBot — primarily `src/teambot/cli.py`, potentially new `src/teambot/worktree/` module

**Primary Language/Framework**:

- Python (subprocess calls to Git CLI, or GitPython if already a dependency)

**Testing Preference**:

- Follow current pattern (pytest with pytest-mock); mock Git subprocess calls in unit tests; consider one acceptance test that exercises real Git operations in a temp repo.

**Key Constraints**:
- Must not modify the user's main working directory when `--worktree` is used.
- Must work on all platforms TeamBot supports (Linux, macOS, Windows with Git Bash). On Windows, validate that worktree paths do not exceed 260-character path length limits given the nested structure.
- Should not add heavy dependencies — prefer subprocess to Git CLI over adding GitPython if not already present.
- Worktree path must avoid conflicts if multiple objectives use similar names — fail with clear error if branch already exists (user resolves).
- Must handle edge cases: uncommitted changes in main, branch name collisions, nested Git repos.

---

## Additional Context

### Worktree Lifecycle

```
teambot run objectives/my-feature.md --worktree
  │
  ├─► git worktree add .teambot-worktrees/feat-my-feature -b feat/my-feature
  │
  ├─► cd .teambot-worktrees/feat-my-feature
  │
  ├─► [Run full TeamBot workflow in this directory]
  │
  └─► On completion: print summary, worktree remains
        User runs: git worktree remove .teambot-worktrees/feat-my-feature
        (or TeamBot future command: teambot worktree clean)
```

### Branch Naming Derivation

| Objective Filename | Default Branch |
|--------------------|----------------|
| `objective-user-auth.md` | `feat/user-auth` |
| `objective-fix-login-bug.md` | `feat/fix-login-bug` |
| `my-feature.md` | `feat/my-feature` |

Prefix `objective-` is stripped if present. `feat/` prefix is added.

> **Note on naming**: Branch names use `/` (e.g., `feat/my-feature`). Worktree directory names use `-` since `/` is not filesystem-safe (e.g., `.teambot-worktrees/feat-my-feature/`).

### State Isolation

- `.teambot/` directory is created *inside* the worktree, not in the main repo.
- This ensures each objective's history, artifacts, and state are fully isolated.
- `teambot status` when run from a worktree shows only that objective's status.
- `.teambot-worktrees/` should be added to the repository's `.gitignore` to prevent accidental commits.

---

## Future Roadmap (Not In Scope for This Objective)

The following features are **out of scope** for this MVP but represent the intended evolution. They are documented here to inform architectural decisions and ensure the MVP design does not preclude them.

### Phase 2: Worktree Visibility & Management

**`teambot worktree list`** — List all TeamBot-managed worktrees and their status.

```bash
$ teambot worktree list
┌─────────────────────────────────────┬──────────────┬─────────────────┬────────────┐
│ Worktree                            │ Branch       │ Objective       │ Status     │
├─────────────────────────────────────┼──────────────┼─────────────────┼────────────┤
│ .teambot-worktrees/feat-user-auth   │ feat/user-auth │ user-auth.md   │ COMPLETE   │
│ .teambot-worktrees/feat-api-cache   │ feat/api-cache │ api-cache.md   │ RUNNING    │
└─────────────────────────────────────┴──────────────┴─────────────────┴────────────┘
```

**`teambot worktree clean`** — Remove completed worktrees (with confirmation).

**`teambot status --all`** — Aggregate status across all active worktrees.

> **Architecture Note**: Cross-worktree status aggregation may require a central registry file (e.g., `.teambot/worktree-registry.json` in the main repo) to track active worktrees. This should be evaluated during Phase 2 planning — MVP's per-worktree state isolation should not preclude this.

### Phase 3: Parallel Objective Execution

**Batch Mode** — Run multiple objectives in parallel worktrees:

```bash
teambot run objectives/ --batch --worktree
```

- Discovers all `*.md` files in the objectives directory.
- Creates a worktree per objective.
- Runs them in parallel (respecting system resource limits).
- Aggregates results.

**Concurrency Control**:
- `--max-parallel N` to limit concurrent objectives.
- Queue system for objectives beyond the limit.

### Phase 4: Multi-Team Coordinator

**Coordinator Agent** — A meta-orchestrator that:
- Spawns independent TeamBot "teams" (PM, BA, Builders, Reviewer) per worktree.
- Routes cross-objective dependencies (e.g., "Feature B depends on Feature A's API").
- Handles merge coordination when parallel features touch the same files.
- Provides unified progress dashboard.

This phase is speculative and depends on validating Phases 1-3. The key architectural decision is whether coordination happens via:
- **Shared state file** (simpler, single-machine).
- **Message queue** (supports distributed execution).

### Phase 5: Auto-PR & Integration

**Auto-PR Creation** — On objective completion:
- Automatically create a draft PR from the feature branch.
- Populate PR description from objective + generated artifacts.
- Link to TeamBot run artifacts.

**Auto-Merge (Optional)** — If all checks pass and configured:
- Auto-merge when CI is green.
- Configurable via `teambot.json`:
  ```json
  {
    "worktree": {
      "auto_pr": true,
      "auto_merge": false
    }
  }
  ```

---

## Design Decisions Required

The following decisions must be explicitly addressed during the PLAN stage:

1. **Git interaction method**: Use raw `subprocess` calls to Git CLI (preferred for minimal dependencies) or GitPython library (if richer Git object model is needed). Recommend subprocess for MVP.

2. **Worktree path structure**: Confirm `.teambot-worktrees/` as the directory name. Consider whether this should be configurable in `teambot.json`.

3. **Branch collision handling**: If `feat/my-feature` already exists:
   - Option A: Fail with clear error message (safest, user resolves).
   - Option B: Append suffix (e.g., `feat/my-feature-2`) with warning.
   - Recommend Option A for MVP.

4. **Working directory context**: When TeamBot runs in a worktree, all file paths must be relative to the worktree root. Verify that `orchestrator.py`, `history/`, and artifact paths handle this correctly (they should, since they use `Path.cwd()`, but this needs validation).

5. **Cleanup policy**: Worktrees are left on disk after completion. Document the manual cleanup command (`git worktree remove`). Defer `teambot worktree clean` to Phase 2.

6. **Resume behaviour**: If `teambot run --resume` is invoked from the main directory but the objective was running in a worktree, should it:
   - Option A: Error with "run this command from the worktree directory".
   - Option B: Auto-detect and switch to worktree context.
   - Recommend Option A for MVP simplicity.

7. **Notification of worktree location**: After worktree creation, clearly print the path so the user knows where work is happening. Consider: should subsequent log output indicate the worktree context?

---

## Implementation Notes

### Suggested Module Structure

```
src/teambot/
├── worktree/
│   ├── __init__.py
│   ├── manager.py       # WorktreeManager class
│   └── naming.py        # Branch name derivation logic
```

### WorktreeManager Responsibilities

- `create(objective_path, branch_name=None) -> WorktreeInfo`
- `list() -> list[WorktreeInfo]`
- `remove(worktree_path) -> None`
- `get_worktree_for_objective(objective_path) -> Optional[WorktreeInfo]`

### CLI Changes

```python
@run.command()
@click.option("--worktree", is_flag=True, help="Run in isolated Git worktree")
@click.option("--branch", default=None, help="Feature branch name (default: derived from objective)")
def run(objective, worktree, branch, ...):
    if worktree:
        wt_info = worktree_manager.create(objective, branch)
        os.chdir(wt_info.path)
    # ... existing run logic
```

---
