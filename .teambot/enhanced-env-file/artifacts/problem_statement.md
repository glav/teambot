# Problem Statement: Enhanced .env File Loading

## Business Problem

TeamBot users experience **unreliable environment variable loading** when invoking the tool via `uvx` or from subdirectories within a project. This creates friction in developer workflows and CI/CD pipelines.

### Current State

- `load_dotenv()` is called without parameters, using default behavior
- Default behavior only searches the current working directory
- No mechanism to specify an explicit `.env` file path
- No way to disable `.env` loading for CI environments
- Parent directory `.env` files are not considered

### Pain Points

| User Scenario | Problem | Impact |
|--------------|---------|--------|
| Developer runs `uvx teambot run` from project subdirectory | `.env` in project root not found | Missing credentials, silent failures |
| CI pipeline needs clean environment | No way to disable `.env` loading | Unpredictable behavior, env pollution |
| Monorepo with shared + project-specific env vars | No merge behavior between parent and local `.env` | Duplicate config, maintenance burden |
| User has `.env` in non-standard location | No way to specify path | Workarounds required (cd, symlinks) |

---

## Business Goals

1. **Reliability**: `.env` files load predictably regardless of invocation method (`uvx`, direct, from subdirectory)
2. **Flexibility**: Users can specify explicit `.env` file paths when needed
3. **CI-Friendly**: Ability to disable `.env` loading for clean CI/CD environments
4. **Ergonomic Defaults**: Merge parent directory `.env` with local `.env` for hierarchical configuration

---

## Success Criteria

| ID | Criterion | Validation Method |
|----|-----------|-------------------|
| SC-1 | `.env` files load from current working directory when present | Manual test: create `.env` in cwd, verify vars loaded |
| SC-2 | Parent directory `.env` provides additional variables not in cwd `.env` (merge behavior) | Manual test: create parent and child `.env` with different vars, verify both loaded |
| SC-3 | `--env-file PATH` argument allows explicit `.env` file specification | CLI test: pass custom path, verify loaded |
| SC-4 | `--no-env` flag disables all `.env` file loading | CLI test: verify no `.env` vars loaded |
| SC-5 | `--env-file` and `--no-env` work with all commands (init, run, status) | Test all subcommands with both flags |
| SC-6 | Clear error message if `--env-file` path does not exist | CLI test: pass non-existent path, verify error |
| SC-7 | Existing functionality and tests continue to pass | Run full test suite |
| SC-8 | Documentation updated for new options | Review docs for completeness |
| SC-9 | `uvx`-invoked TeamBot loads `.env` from cwd | Manual verification with `uvx teambot` |

---

## Stakeholders

| Role | Interest |
|------|----------|
| **Developers** | Reliable local development with `.env` files |
| **DevOps/CI Engineers** | Predictable CI builds without env pollution |
| **Monorepo Users** | Hierarchical configuration inheritance |

---

## Scope

### In Scope

- New `--env-file <PATH>` global CLI argument
- New `--no-env` global CLI flag
- Parent-to-child `.env` merge behavior (parent provides defaults, child overrides)
- Error handling for missing `--env-file` path
- Documentation updates

### Out of Scope

- Multiple `--env-file` arguments (single file only)
- `.env.local`, `.env.production` variants (not in this iteration)
- Encryption or secret management
- Environment variable validation beyond loading

---

## Constraints

| Constraint | Rationale |
|------------|-----------|
| Backward compatible | Existing users without CLI args must see same behavior |
| Load before config parsing | Environment vars may be referenced in `teambot.json` |
| Global arguments | `--env-file` and `--no-env` must work with all subcommands |
| Fail-fast on invalid `--env-file` | Clear error better than silent fallback |

---

## Assumptions

1. `python-dotenv` library supports all required functionality (explicit path, override behavior)
2. Users understand `.env` file precedence (explicit > cwd > parent)
3. Current test suite provides adequate coverage for regression detection

---

## Dependencies

| Dependency | Status |
|------------|--------|
| `python-dotenv` (v1.0.0+) | ✅ Already in `pyproject.toml` |
| argparse | ✅ Already used in `cli.py` |

---

## Acceptance Criteria Summary

**Given** TeamBot is invoked from any directory  
**When** a `.env` file exists in the current working directory  
**Then** environment variables from that file are loaded

**Given** `--env-file /path/to/.env` is specified  
**When** the file exists  
**Then** only that file is loaded (no cwd/parent search)

**Given** `--env-file /path/to/.env` is specified  
**When** the file does NOT exist  
**Then** TeamBot exits with a clear error message

**Given** `--no-env` is specified  
**When** TeamBot starts  
**Then** no `.env` files are loaded regardless of location

**Given** `.env` exists in both cwd and parent directory  
**When** TeamBot loads environment  
**Then** variables from both files are merged (cwd takes precedence for conflicts)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking change to existing behavior | Low | High | Explicit backward compat testing |
| Confusing precedence rules | Medium | Medium | Clear documentation with examples |
| Performance impact from parent search | Low | Low | Limit search depth to project root |

---

## Measuring Success

- Zero regressions in existing test suite
- Manual verification of all 9 success criteria passes
- User feedback from `uvx` invocation scenarios
