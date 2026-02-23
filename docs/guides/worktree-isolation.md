# Worktree Isolation Guide

TeamBot supports running objectives in isolated Git worktrees, enabling parallel feature development without branch conflicts or uncommitted file clashes.

## Overview

When you run TeamBot with `--worktree`, it automatically:

1. Creates a new Git branch from your current HEAD
2. Creates a worktree at `.teambot-worktrees/<branch-name>/`
3. Runs the entire workflow within that worktree
4. Keeps your main working directory untouched

This enables scenarios like starting Feature B while Feature A is still in review.

## Usage

### Basic Usage

```bash
# Run objective in isolated worktree
teambot run objectives/my-feature.md --worktree
```

The branch name is automatically derived from the objective filename:
- `objective-foo.md` → `feat/foo`
- `sdd-objective-auth.md` → `feat/auth`
- `my-feature.md` → `feat/my-feature`

### Custom Branch Name

```bash
# Use a custom branch name
teambot run objectives/my-feature.md --worktree --branch feat/custom-name

# Hotfix branches
teambot run objectives/bugfix.md --worktree --branch hotfix/critical-bug
```

## Visual Indicators

When running in worktree mode, TeamBot displays the branch context:

### REPL Prompt

```
🤖 [wt:feat/my-feature] > what is this codebase about?
```

### Stage Headers

```
╭─ Stage: IMPLEMENTATION [worktree: feat/my-feature] ─────────────╮
│ Executing implementation plan...                                │
╰─────────────────────────────────────────────────────────────────╯
```

### Status Panel

The status panel automatically shows the current Git branch, which updates when in a worktree.

## State Isolation

Each worktree has its own `.teambot/` directory, meaning:

- **Workflow state** is isolated per worktree
- **History files** are scoped to the worktree
- **No cross-contamination** between parallel features

```
main-repo/
├── .teambot/                    # Main repo state
│   └── workflow_state.json
└── .teambot-worktrees/
    └── feat-my-feature/
        ├── .teambot/            # Worktree-specific state
        │   └── workflow_state.json
        └── src/
```

## Resume Behavior

If a workflow is interrupted, you can resume from the worktree:

```bash
# Navigate to worktree
cd .teambot-worktrees/feat-my-feature/

# Resume
teambot run --resume
```

Or from the main directory with the worktree flag:

```bash
teambot run objectives/my-feature.md --worktree --resume
```

## After Completion

Worktrees persist after workflow completion for your review:

```bash
# Review changes
cd .teambot-worktrees/feat-my-feature/
git log --oneline main..HEAD

# Merge when ready
git checkout main
git merge feat/my-feature

# Clean up
git worktree remove .teambot-worktrees/feat-my-feature
git branch -d feat/my-feature
```

## Requirements

- **Git 2.5 or later** - Git worktrees were introduced in Git 2.5
- Check your version: `git --version`

## Error Handling

### Branch Already Exists

```
Error: Branch 'feat/my-feature' already exists.
Use --branch to specify a different name.
```

**Solution**: Use `--branch` to specify a unique branch name.

### Worktree Path Exists

```
Error: Worktree path already exists: .teambot-worktrees/feat-my-feature
Remove it or use a different --branch name.
```

**Solution**: Remove the existing worktree or use a different branch name.

### Git Not Found

```
Error: Git is required for --worktree mode but was not found
```

**Solution**: Install Git and ensure it's on your PATH.

### Git Version Too Old

```
Error: Git version 2.4 is too old. Git 2.5+ is required for worktree support.
```

**Solution**: Upgrade Git to version 2.5 or later.

### Path Too Long (Windows)

```
Error: Path length (275) exceeds limit (260)
Use --branch to specify a shorter branch name.
```

**Solution**: Use a shorter branch name with `--branch`.

## Best Practices

1. **Use descriptive objective filenames** - They become your branch names
2. **Clean up completed worktrees** - Use `git worktree remove` after merging
3. **Review before merging** - Worktrees persist for your review
4. **Keep worktree names short** - Especially on Windows (260-char path limit)

## See Also

- [CLI Reference](cli-reference.md) - Full command documentation
- [File-Based Orchestration](file-based-orchestration.md) - Running objectives
- [Objective Format](objective-format.md) - Writing objective files
