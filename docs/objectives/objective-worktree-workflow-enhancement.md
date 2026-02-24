# Worktree Workflow Enhancement

## Objective

**Goal**: Enhance the `--worktree` option to support objectives that exist only in the source repository (staged or committed) and allow branching from a specified base branch.

**Problem Statement**: When using `teambot run <objective> --worktree`, the worktree is created from the current HEAD (typically main). If the objective file exists only in a feature branch (staged or committed but not in main), the workflow fails with "Objective file not found" because the worktree doesn't contain the objective file. This creates friction in the typical workflow where users draft an objective in a branch before running file-based orchestration.

**Success Criteria**:
- [ ] If the objective file doesn't exist in the newly created worktree but exists in the source repository, it is copied to the worktree automatically
- [ ] A new `--base-branch` option allows users to specify which branch to base the worktree on (defaults to current behavior)
- [ ] Clear logging/output indicates when an objective file is copied to the worktree
- [ ] Existing worktree functionality remains backward compatible
- [ ] Unit tests cover the new functionality with 80%+ coverage
- [ ] Acceptance tests validate the end-to-end workflow

---

## Technical Context

**Target Codebase**: 
- `src/teambot/cli.py` - CLI argument parsing and worktree orchestration
- `src/teambot/worktree/manager.py` - Worktree creation and management

**Primary Language/Framework**: Python 3.11+ / Click CLI

**Testing Preference**: TDD - Write tests first, then implement

**Key Constraints**:
- Must not break existing `--worktree` workflows
- Must handle both staged and committed objective files in source repo
- Must work cross-platform (Linux, macOS, Windows)
- Path handling must respect Windows 260-character limit validation already in place

---

## Additional Context

### Current Worktree Flow (cli.py lines 600-641)
1. Validate Git is available and in a Git repository
2. Derive branch name from objective filename
3. Call `WorktreeManager.create_worktree(repo_root, branch_name)`
4. Change working directory to the worktree
5. Attempt to read objective file (fails if file doesn't exist)

### Proposed Changes

**1. Copy Objective File (Required)**
After creating the worktree, check if the objective file exists in the worktree. If not, but it exists in the source repository (either staged or as a working file), copy it to the worktree.

```
# Pseudocode
if not objective_exists_in_worktree:
    if objective_exists_in_source:
        copy_file(source_objective, worktree_objective)
        log("[OK] Copied objective file to worktree")
    else:
        raise error("Objective file not found in source or worktree")
```

**2. Base Branch Option (Required)**
Add `--base-branch` CLI option to specify the branch to base the worktree on:

```bash
# Branch from current HEAD (default - whatever branch you're on)
teambot run objective.md --worktree

# Branch from a specific branch (explicit)
teambot run objective.md --worktree --base-branch main
```

### `--base-branch` Behavior
| Scenario | Command | Result |
|----------|---------|--------|
| On `main`, no flag | `teambot run obj.md --worktree` | Worktree branches from `main` |
| On `feat/my-branch`, no flag | `teambot run obj.md --worktree` | Worktree branches from `feat/my-branch` |
| On any branch, with flag | `teambot run obj.md --worktree --base-branch main` | Worktree branches from `main` |

**Default behavior**: When `--base-branch` is omitted, the worktree branches from the **current HEAD** (whatever branch/commit you're currently on). This preserves existing behavior and is intuitive - if you're working on `feat/my-branch` and want to spawn a worktree, it will naturally branch from your current work.

This requires updating `git worktree add -b <new-branch> <path>` to `git worktree add -b <new-branch> <path> <base-branch>`.

**Implementation detail** - Update `WorktreeManager.create_worktree()` signature:
```python
# Current signature
def create_worktree(repo_root, branch_name, base_dir=WORKTREE_BASE_DIR)

# New signature  
def create_worktree(repo_root, branch_name, base_dir=WORKTREE_BASE_DIR, base_branch=None)

# Command construction change (around line 199-200)
cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_path)]
if base_branch:
    cmd.append(base_branch)
```

### Related Files
- `src/teambot/worktree/manager.py` - `create_worktree()` function (lines 156-216)
- `src/teambot/worktree/manager.py` - `derive_branch_name()` function (lines 41-77)
- `tests/test_worktree/test_manager.py` - Existing worktree tests

### File Source Precedence
When copying the objective file to the worktree, use this priority:
1. **Working directory** (uncommitted changes) - matches what user sees
2. **Staged version** - if working directory doesn't have it
3. **Committed version in current branch** - fallback

### Edge Cases to Handle
1. Objective file exists in worktree already - no action needed
2. Objective file exists only in source working directory (uncommitted)
3. Objective file exists only staged in source
4. Objective file doesn't exist anywhere - error with clear message
5. `--base-branch` specified but branch doesn't exist - error with clear message
6. Parent directories for objective don't exist in worktree - create them
7. Worktree already exists when `--base-branch` is specified - use existing worktree (ignore base-branch, it only applies at creation time)

### Key Acceptance Test Scenario
```
Given: User is on branch `feature/my-work`
  And: User creates objective file `docs/objectives/my-task.md`
  And: User stages the file with `git add`
  And: File is NOT committed

When: User runs `teambot run docs/objectives/my-task.md --worktree`

Then: Worktree is created successfully
  And: Objective file is copied from source to worktree
  And: Log shows "[OK] Copied objective file to worktree"
  And: TeamBot proceeds with orchestration
```

---

## Notes

- **Stage configuration**: The workflow stages are defined in `stages.yaml`
- **Artifacts**: Generated artifacts will be saved to `.teambot/worktree-workflow/`
- **Testing**: Run with `uv run pytest tests/test_worktrees/` for focused testing
