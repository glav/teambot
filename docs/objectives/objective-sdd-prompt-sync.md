# SDD Prompt Sync Objective

## Objective

**Goal**: Implement incremental SDD prompt file synchronization during `teambot init` and runtime validation to ensure `stages.yaml` and SDD prompt files stay in sync.

**Problem Statement**: When TeamBot's scaffold is updated with new SDD prompt files (e.g., `sdd.7b-implementation-review.prompt.md`), existing projects that run `teambot init` won't receive the new files. The `.agent/` directory copy is skipped if it already exists with content. This causes `stages.yaml` to reference prompt files that don't exist, leading to workflow execution failures that are difficult to diagnose (e.g., agent receives a `prompt_template` path but the file doesn't exist, causing silent failures or cryptic errors).

**Success Criteria**:

*Part A - Incremental Sync:*
- [ ] `teambot init` copies missing SDD prompt files to existing `.agent/commands/sdd/` directories
- [ ] Existing user-modified SDD prompt files are preserved (not overwritten)
- [ ] `sync_sdd_prompts()` returns `List[SyncResult]` with reasons `'copied'` / `'skipped_exists'` / `'source_missing'`, consistent with `CopyResult` vocabulary from `scaffolds.py`
- [ ] Sync results are displayed to user (files added vs skipped)

*Part B - Runtime Validation:*
- [ ] `teambot run` validates ALL `prompt_template` paths in `stages.yaml` exist before starting workflow
- [ ] Validation runs after configuration loading, before SETUP stage execution
- [ ] Null/empty `prompt_template` values are valid (stage doesn't use a prompt)
- [ ] Clear error messages with specific format (see Error Message Format below)

*Testing:*
- [ ] Comprehensive unit test coverage for sync and validation logic
- [ ] Acceptance tests per scenarios below

**Acceptance Tests**:
- [ ] AT-001: Run `teambot init` on project missing `sdd.7b-*.md` → file copied, success message shown
- [ ] AT-002: Run `teambot init` on project with modified `sdd.1-*.md` → file preserved, not overwritten
- [ ] AT-003: Run `teambot run` with missing prompt → clear error, exit code 1, suggests `teambot init`
- [ ] AT-004: Run `teambot run` with all prompts present → validation passes silently, workflow starts

---

## Technical Context

**Target Codebase**: `/workspaces/teambot/src/teambot/`

**Primary Language/Framework**: Python 3.11+ / argparse CLI

**Testing Preference**: TDD

**Key Constraints**:
- Must preserve existing scaffold copy behavior for backward compatibility
- Must not overwrite user customizations to existing prompt files
- Validation errors must provide actionable remediation steps
- Must integrate cleanly with existing `scaffolds.py` and `cli.py` modules

---

## Additional Context

### Current Behavior

The `copy_scaffold_directory()` function in `scaffolds.py` uses `shutil.copytree()` for directory copies:
- If target directory exists and is non-empty → returns `skipped_not_empty`
- No mechanism for incremental file sync within directories

### Proposed Solution

**Part A: Incremental SDD Prompt Sync (in `teambot init`)**

1. After standard scaffold copy, check if `.agent/commands/sdd/` exists
2. Compare scaffold SDD prompt files with user's directory
3. Copy only missing files (files in scaffold but not in user's directory)
4. Report which files were added vs skipped
5. Return appropriate `CopyResult` for new files

Implementation location: `src/teambot/prompt_sync.py` - function `sync_sdd_prompts()`

**Part B: Runtime Validation (in `teambot run`)**

1. After configuration loading, before SETUP stage execution, parse `stages.yaml`
2. Extract ALL `prompt_template` paths (not just `.agent/commands/sdd/`)
3. Skip validation for null/empty `prompt_template` values
4. Validate each referenced prompt file exists at the specified path
5. If any are missing:
   - Display clear error listing missing files (see Error Message Format)
   - Suggest running `teambot init` to sync missing prompts
   - Exit with non-zero status (exit code 1)

Implementation location: `src/teambot/prompt_sync.py` - validation functions `validate_prompt_files()` and `detect_orphaned_prompts()`

### Error Message Format

When prompts are missing, display:
```
Error: Missing prompt file(s) referenced in stages.yaml:
  - .agent/commands/sdd/sdd.7b-implementation-review.prompt.md (stage: IMPLEMENTATION_REVIEW)

Run 'teambot init' to sync missing SDD prompt files.
```

### Files Likely to Change

| File | Changes |
|------|---------|
| `src/teambot/prompt_sync.py` | `sync_sdd_prompts()`, `validate_prompt_files()`, `detect_orphaned_prompts()` |
| `src/teambot/cli.py` | Call sync in `cmd_init()`; call validation in `cmd_run()` before workflow starts |
| `tests/test_prompt_sync.py` | Unit tests for sync and validation |
| `tests/test_prompt_sync_acceptance.py` | Acceptance tests for sync scenarios |
| `tests/test_prompt_sync_acceptance_validation.py` | Acceptance tests for validation/orphan detection |

### Edge Cases to Handle

**Sync (Part A):**
- User has customized an existing prompt file → preserve it (never overwrite)
- User has deleted a prompt file intentionally → sync will restore it; document this behavior in `teambot init` output
- Scaffold source is missing (corrupted install) → graceful error with clear message

**Validation (Part B):**
- `stages.yaml` references prompt outside `.agent/commands/sdd/` → validate full path as specified
- `stages.yaml` not found → skip validation (already handled by existing flow)
- `stages.yaml` invalid YAML → existing error handling applies
- `prompt_template` is null/empty → valid, skip validation for that stage

### Implementation Notes

- `sync_sdd_prompts()` returns `List[SyncResult]` (defined in `prompt_sync.py`) using the same reason vocabulary as `CopyResult` from `scaffolds.py`
- Part A and Part B are separate deliverables with independent success criteria
- Consider whether existing `prerequisite_artifacts` mechanism in `stages.yaml` could be leveraged for validation

---

## Notes

- **Stage configuration**: Workflow stages are defined in `stages.yaml`
- **Related branch**: `glav/workflow-improvements` contains the new `sdd.7b` prompt that exposed this issue
