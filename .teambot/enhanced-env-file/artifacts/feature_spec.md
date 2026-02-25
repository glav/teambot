<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Enhanced .env File Loading - Feature Specification Document
Version 1.0 | Status DRAFT | Owner BA Agent | Team TeamBot Core | Target v0.2.0 | Lifecycle Development

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
TeamBot is a CLI tool that wraps the GitHub Copilot CLI to enable collaborative, multi-agent AI workflows. It relies on environment variables (loaded from `.env` files) for sensitive configuration like notification tokens and feature flags. Currently, `.env` loading uses python-dotenv's default behavior, which only searches the current working directory.

### Core Opportunity
Improve developer experience by making `.env` file loading reliable across all invocation methods (`uvx`, direct execution, subdirectory invocation) while providing explicit control for CI/CD environments and power users.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Load `.env` files reliably from cwd regardless of invocation method | Reliability | Fails with `uvx` | 100% success | v0.2.0 | P0 |
| G-002 | Allow explicit `.env` file path specification via CLI | Flexibility | Not available | `--env-file` arg | v0.2.0 | P0 |
| G-003 | Provide mechanism to disable `.env` loading for CI | CI-Friendly | Not available | `--no-env` flag | v0.2.0 | P0 |
| G-004 | Support hierarchical `.env` inheritance (parent + child merge) | Ergonomics | Single file only | Merge behavior | v0.2.0 | P1 |

### Technical Context
| Aspect | Value |
|--------|-------|
| **Target Codebase** | `src/teambot/cli.py` |
| **Primary Language** | Python 3.10+ |
| **Framework** | argparse for CLI parsing |
| **Testing Approach** | TDD (Test-Driven Development) |
| **Key Dependency** | python-dotenv v1.0.0+ (already installed) |

## 2. Problem Definition

### Current Situation
- `load_dotenv()` is called at line 1289 of `cli.py` without parameters
- Default behavior only searches the immediate current working directory
- No CLI mechanism exists to specify an explicit `.env` file path
- No way to disable `.env` loading for CI/CD pipelines
- Parent directory `.env` files are never considered

### Problem Statement
When TeamBot is invoked via `uvx` or from a project subdirectory, the `.env` file in the project root is not found, causing missing credentials and silent configuration failures. CI/CD pipelines have no way to prevent `.env` pollution, and monorepo users cannot leverage hierarchical configuration inheritance.

### Root Causes
* `load_dotenv()` default behavior searches only the immediate cwd
* No argument parsing occurs before `.env` loading, so CLI flags cannot influence loading
* No parent directory traversal logic exists

### Impact of Inaction
- Developers experience frustrating silent failures when credentials aren't loaded
- CI/CD pipelines produce inconsistent builds due to uncontrolled environment pollution
- Monorepo users must duplicate configuration across directories
- `uvx` users (the modern Python packaging approach) cannot use TeamBot reliably

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| **Local Developer** | Run TeamBot from any project directory with credentials loaded | `.env` not found when running from subdirectory | High - blocks primary workflow |
| **DevOps Engineer** | Predictable CI builds without env pollution | Cannot disable `.env` loading, unpredictable behavior | High - affects pipeline reliability |
| **Monorepo User** | Share common config at root, override per-project | No merge behavior, must duplicate config | Medium - maintenance burden |
| **Power User** | Use `.env` files in non-standard locations | No way to specify explicit path | Medium - workarounds required |

### User Journeys

**Journey 1: Subdirectory Invocation**
1. Developer has `.env` at project root with `TEAMBOT_TELEGRAM_TOKEN`
2. Developer `cd`s into `src/components/` to work on a feature
3. Developer runs `teambot run ../objectives/my-task.md`
4. **Current**: Token not loaded, notifications silently fail
5. **Expected**: Token loaded from parent `.env`, notifications work

**Journey 2: CI Pipeline**
1. CI system checks out repository
2. Repository contains `.env-sample` (tracked) and `.env` (untracked locally)
3. CI runs `teambot run objectives/build.md`
4. **Current**: May load stale/unexpected `.env` if one exists
5. **Expected**: `teambot --no-env run objectives/build.md` ensures clean environment

## 4. Scope

### In Scope
* New `--env-file <PATH>` global CLI argument for explicit path specification
* New `--no-env` global CLI flag to disable all `.env` loading
* Parent-to-child `.env` merge behavior (parent provides defaults, cwd overrides)
* Clear error message when `--env-file` path does not exist
* Documentation updates for new CLI options
* Unit and integration tests following TDD approach

### Out of Scope (with justification)
* **Multiple `--env-file` arguments**: Adds complexity; users can merge files externally. Consider for future iteration.
* **`.env.local`, `.env.production` variants**: Common pattern but not critical for MVP. Consider for future iteration.
* **Encryption or secret management**: Out of scope for a CLI tool; use external secret managers.
* **Environment variable validation**: Beyond loading; validation should be in config parsing layer.
* **Unlimited parent traversal**: Security concern; limit to reasonable depth (e.g., 10 directories or git root).

### Assumptions
* `python-dotenv` library supports `dotenv_path` parameter for explicit loading
* `python-dotenv` `override=False` parameter enables merge behavior
* Users understand precedence: explicit `--env-file` > cwd `.env` > parent `.env`
* Git root detection (if used for traversal limit) is reliable

### Constraints
| Constraint | Rationale |
|------------|-----------|
| Backward compatible | Existing users without new CLI args must see identical behavior |
| Load before config parsing | Environment vars may be referenced in `teambot.json` via `${VAR}` syntax |
| Global arguments | `--env-file` and `--no-env` must work with all subcommands (init, run, status) |
| Fail-fast on invalid `--env-file` | Clear error preferred over silent fallback to default behavior |
| Pre-argument-parsing | `.env` loading must occur before argparse runs (env vars may affect defaults) |

## 5. Product Overview

### Value Proposition
TeamBot's enhanced `.env` loading provides reliable, predictable environment configuration across all invocation methods while giving users explicit control when needed—whether specifying a custom path or disabling loading entirely for CI.

### Differentiators
* **Merge behavior**: Unlike simple override, parent + child merge provides hierarchical configuration
* **CI-friendly**: Explicit `--no-env` flag for clean, reproducible builds
* **Fail-fast**: Clear errors for missing files instead of silent failures

### CLI Interface
```
teambot [--env-file PATH] [--no-env] [--verbose] [--no-animation] <command> [args]

Global Options:
  --env-file PATH    Load environment from specific .env file (disables auto-discovery)
  --no-env           Disable all .env file loading
  --verbose          Enable verbose output
  --no-animation     Disable startup animation
  --version          Show version

Commands:
  init               Initialize TeamBot configuration
  run                Run TeamBot with an objective
  status             Show TeamBot status
```

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance Criteria | Notes |
|-------|-------|-------------|-------|----------|----------|---------------------|-------|
| FR-001 | CWD .env Loading | Load `.env` file from current working directory when present | G-001 | All | P0 | Given `.env` exists in cwd, when TeamBot starts, then vars are loaded into `os.environ` | Default python-dotenv behavior |
| FR-002 | Parent Directory Merge | Load parent directory `.env` files with merge behavior (parent provides defaults, cwd overrides) | G-004 | Monorepo User | P1 | Given `.env` in both cwd and parent with different vars, when TeamBot starts, then both sets of vars are available; cwd takes precedence for conflicts | Use `override=False` for parent files |
| FR-003 | Explicit --env-file | New `--env-file PATH` global argument loads only the specified file | G-002 | Power User | P0 | Given `--env-file /path/to/.env` specified, when TeamBot starts, then only that file is loaded (no cwd/parent discovery) | Mutually exclusive with `--no-env` |
| FR-004 | --env-file Validation | If `--env-file` path does not exist, exit with clear error | G-002 | Power User | P0 | Given `--env-file /nonexistent`, when TeamBot starts, then exit code 1 with message "Error: Environment file not found: /nonexistent" | Must fail before any other processing |
| FR-005 | --no-env Flag | New `--no-env` global flag disables all `.env` file loading | G-003 | DevOps | P0 | Given `--no-env` specified, when TeamBot starts, then no `.env` files are loaded regardless of cwd/parent presence | Mutually exclusive with `--env-file` |
| FR-006 | Mutual Exclusivity | `--env-file` and `--no-env` are mutually exclusive | G-002, G-003 | All | P0 | Given both `--env-file` and `--no-env` specified, when TeamBot starts, then exit with error "Error: --env-file and --no-env are mutually exclusive" | argparse mutually_exclusive_group |
| FR-007 | Global Arguments | `--env-file` and `--no-env` work with all commands (init, run, status) | G-002, G-003 | All | P0 | Given `teambot --no-env init`, `teambot --env-file .env run obj.md`, `teambot --no-env status`, then all succeed with appropriate env handling | Add to main parser, not subparsers |
| FR-008 | Load Before Config | `.env` loading occurs before `teambot.json` config parsing | G-001 | All | P0 | Given `teambot.json` references `${TEAMBOT_TOKEN}` and `.env` defines it, when config loads, then substitution succeeds | Critical for config interpolation |
| FR-009 | Parent Traversal Limit | Parent directory search stops at git root or after 10 levels, whichever comes first | G-004 | Monorepo User | P1 | Given deeply nested directory, when loading, then traversal stops at reasonable boundary | Security and performance safeguard |

### Precedence Rules
1. `--no-env` → No files loaded
2. `--env-file PATH` → Only specified file loaded
3. Default (no flags) → cwd `.env` + parent `.env` files merged (cwd wins conflicts)

### Feature Hierarchy
```
Enhanced .env Loading
├── Default Behavior (no args)
│   ├── Load cwd/.env
│   └── Merge parent/.env files (up to git root or 10 levels)
├── --env-file PATH
│   ├── Load specified file only
│   └── Error if file missing
└── --no-env
    └── Skip all .env loading
```

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Performance | `.env` loading must not add noticeable startup delay | < 50ms additional time | P1 | Benchmark before/after | Parent traversal is O(n) where n ≤ 10 |
| NFR-002 | Reliability | `.env` loading must work identically across invocation methods | 100% consistency: direct, uvx, pipx | P0 | Test all invocation methods | Core requirement |
| NFR-003 | Maintainability | Code changes must be localized to cli.py and new env_loader module | Single responsibility | P1 | Code review | Avoid scattered changes |
| NFR-004 | Testability | All .env loading logic must be unit testable without file system | 100% mockable | P0 | Test coverage report | Use dependency injection |
| NFR-005 | Backward Compatibility | Existing behavior without new args must be preserved | Zero breaking changes | P0 | Regression test suite | Critical constraint |
| NFR-006 | Security | Parent traversal must not escape repository boundary | Stop at git root or 10 levels | P1 | Security review | Prevent loading sensitive files outside project |
| NFR-007 | Usability | Error messages must be actionable | Include file path and suggestion | P1 | UX review | "Error: File not found: X. Use --no-env to skip loading." |

## 8. Data & Analytics

### Inputs
| Input | Source | Format |
|-------|--------|--------|
| `.env` file(s) | File system | KEY=value pairs per python-dotenv spec |
| `--env-file` argument | CLI | Absolute or relative file path |
| `--no-env` flag | CLI | Boolean flag |

### Outputs / Events
| Output | Destination | Format |
|--------|-------------|--------|
| Environment variables | `os.environ` | String key-value pairs |
| Error messages | stderr | Human-readable text |
| Verbose loading info | stdout (if -v) | "Loaded .env from: /path" |

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|---------|---------|-------|
| env_file_loaded | `.env` file successfully loaded | `{path, var_count}` | Debug and troubleshooting | CLI |
| env_file_skipped | `.env` file not found (default behavior) | `{search_path}` | Debug | CLI |
| env_file_error | `--env-file` path not found | `{path, error}` | Error tracking | CLI |
| env_loading_disabled | `--no-env` flag used | `{}` | Usage analytics | CLI |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Successful .env loads | Reliability | N/A (new tracking) | 100% when file exists | Per invocation | Instrumentation |
| --env-file usage | Adoption | 0% | Track usage | Monthly | CLI analytics |
| --no-env usage | Adoption | 0% | Track usage | Monthly | CLI analytics |
| uvx invocation success | Reliability | Unreliable | 100% | Per invocation | Manual testing |

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| python-dotenv v1.0.0+ | Library | High | PyPI | Low - stable library | Already in pyproject.toml |
| argparse | Standard Library | High | Python | None | Part of Python stdlib |
| pathlib | Standard Library | High | Python | None | Part of Python stdlib |
| Git (for root detection) | Optional | Low | System | Medium - not always available | Fallback to directory limit |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Breaking change to existing behavior | High | Low | Comprehensive regression tests; default behavior unchanged | Dev Team | Open |
| R-002 | Confusing precedence rules | Medium | Medium | Clear documentation with examples; verbose mode shows what was loaded | BA/Writer | Open |
| R-003 | Performance impact from parent traversal | Low | Low | Limit to 10 directories; stop at git root | Dev Team | Open |
| R-004 | Security: loading .env outside project | Medium | Low | Git root detection; directory limit; never traverse above project root | Dev Team | Open |
| R-005 | Argument parsing order issue | Medium | Medium | Early argument extraction before full argparse; manual sys.argv inspection | Dev Team | Open |

## 11. Privacy, Security & Compliance

### Data Classification
- `.env` files may contain **sensitive credentials** (API tokens, secrets)
- Environment variables are **process-scoped** (not persisted by TeamBot)

### PII Handling
- TeamBot does not read or log `.env` file contents
- Variable names may be logged in verbose mode; values are never logged

### Threat Considerations
| Threat | Mitigation |
|--------|------------|
| Loading malicious .env from parent directory | Limit traversal to git root; users control their file system |
| Exposing secrets in logs | Never log variable values; only log file paths |
| Path traversal attack via --env-file | Validate path exists; no special path handling |

### Regulatory / Compliance
Not applicable - local development tool; no data transmission or storage.

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | pip/uvx install | Standard Python package distribution |
| Rollback | Revert to previous version | No persistent state changes |
| Monitoring | Verbose mode shows load status | `teambot -v run ...` |
| Alerting | N/A | CLI tool, no runtime alerting |
| Support | Documentation + error messages | Self-service troubleshooting |
| Capacity Planning | N/A | Single-user CLI tool |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Target | Gate Criteria | Owner |
|-------|--------|---------------|-------|
| Implementation | Week 1 | All FRs implemented, unit tests pass | Builder |
| Integration Testing | Week 1 | Integration tests pass, manual verification | Builder |
| Documentation | Week 1 | README and docs updated | Writer |
| Release | Week 2 | All tests pass, docs reviewed | PM |

### Feature Flags
Not applicable - features are CLI flags, not runtime toggles.

### Communication Plan
- Update README.md with new CLI options
- Add examples to docs/guides/
- Note in CHANGELOG.md

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| - | - | - | - | All resolved |

## 15. Acceptance Test Scenarios

### AT-001: Default CWD Loading
**Description**: Verify `.env` loads from current working directory by default
**Preconditions**: `.env` file exists in cwd with `TEST_VAR=hello`
**Steps**:
1. Create `.env` in test directory with `TEST_VAR=hello`
2. Run `teambot status` from that directory
3. Check `os.environ.get('TEST_VAR')`
**Expected Result**: `TEST_VAR` equals `hello`
**Verification**: Environment variable is set before config loading

### AT-002: Parent Directory Merge
**Description**: Verify parent `.env` provides defaults, child overrides
**Preconditions**: Parent has `PARENT_VAR=parent` and `SHARED_VAR=parent`; Child has `CHILD_VAR=child` and `SHARED_VAR=child`
**Steps**:
1. Create parent directory with `.env` containing `PARENT_VAR=parent`, `SHARED_VAR=parent`
2. Create child directory with `.env` containing `CHILD_VAR=child`, `SHARED_VAR=child`
3. Run `teambot status` from child directory
**Expected Result**: `PARENT_VAR=parent`, `CHILD_VAR=child`, `SHARED_VAR=child` (child wins)
**Verification**: All three variables present with correct precedence

### AT-003: Explicit --env-file Path
**Description**: Verify `--env-file` loads only the specified file
**Preconditions**: Custom `.env` at `/tmp/custom.env` with `CUSTOM_VAR=custom`; cwd has `.env` with `CWD_VAR=cwd`
**Steps**:
1. Create `/tmp/custom.env` with `CUSTOM_VAR=custom`
2. Create cwd `.env` with `CWD_VAR=cwd`
3. Run `teambot --env-file /tmp/custom.env status`
**Expected Result**: `CUSTOM_VAR=custom` is set; `CWD_VAR` is NOT set
**Verification**: Only specified file is loaded, cwd ignored

### AT-004: --env-file Missing File Error
**Description**: Verify clear error when `--env-file` path doesn't exist
**Preconditions**: No file at `/nonexistent/.env`
**Steps**:
1. Run `teambot --env-file /nonexistent/.env status`
**Expected Result**: Exit code 1, stderr contains "Environment file not found: /nonexistent/.env"
**Verification**: Program exits immediately with actionable error

### AT-005: --no-env Disables Loading
**Description**: Verify `--no-env` prevents all `.env` loading
**Preconditions**: `.env` exists in cwd with `TEST_VAR=hello`
**Steps**:
1. Create `.env` in cwd with `TEST_VAR=hello`
2. Unset `TEST_VAR` if already in environment
3. Run `teambot --no-env status`
**Expected Result**: `TEST_VAR` is NOT in environment
**Verification**: No `.env` files loaded despite presence

### AT-006: Mutual Exclusivity Error
**Description**: Verify `--env-file` and `--no-env` cannot be used together
**Preconditions**: None
**Steps**:
1. Run `teambot --env-file .env --no-env status`
**Expected Result**: Exit code 2, stderr contains "mutually exclusive"
**Verification**: argparse enforces mutual exclusivity

### AT-007: All Commands Support Flags
**Description**: Verify `--env-file` and `--no-env` work with init, run, status
**Preconditions**: `.env` exists with `TEST_VAR=hello`
**Steps**:
1. Run `teambot --no-env init --force` (or without --force if not initialized)
2. Run `teambot --no-env run objectives/test.md` (with valid objective)
3. Run `teambot --no-env status`
**Expected Result**: All commands accept the flag and execute normally
**Verification**: No argument parsing errors; flag is respected

### AT-008: uvx Invocation Loads CWD .env
**Description**: Verify `uvx teambot` loads `.env` from current directory
**Preconditions**: `.env` in cwd with `UVX_TEST=success`
**Steps**:
1. Create `.env` with `UVX_TEST=success`
2. Run `uvx teambot status` (or `uvx run teambot status` depending on setup)
3. Verify variable is loaded
**Expected Result**: `UVX_TEST=success` is available
**Verification**: uvx invocation works identically to direct invocation

## 16. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-24 | BA Agent | Initial specification | Created |

## 17. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Problem Statement | `.teambot/enhanced-env-file/artifacts/problem_statement.md` | Business problem and goals | Source of truth |
| REF-002 | Existing Code | `src/teambot/cli.py:1289` | Current `load_dotenv()` call | Baseline for changes |
| REF-003 | Library Docs | python-dotenv documentation | API for explicit paths and override behavior | N/A |

### Citation Usage
- Problem definition and goals derived from REF-001
- Current implementation analysis from REF-002
- Technical approach informed by REF-003

## 18. Glossary

| Term | Definition |
|------|------------|
| cwd | Current working directory |
| `.env` | dotenv format file containing KEY=value environment variable definitions |
| python-dotenv | Python library for loading `.env` files into `os.environ` |
| Merge behavior | Loading multiple `.env` files where earlier files provide defaults and later files override |
| uvx | Modern Python package runner (uv ecosystem) |

## 19. Implementation Notes

### Suggested Technical Approach
1. **Early argument extraction**: Before `argparse.parse_args()`, manually inspect `sys.argv` for `--env-file` and `--no-env`
2. **New module**: Create `src/teambot/env_loader.py` with `load_environment(env_file: Path | None, no_env: bool) -> None`
3. **Parent traversal**: Implement `find_env_files(start_dir: Path, limit: int = 10) -> list[Path]` that walks up to git root or limit
4. **Load order**: Load parent files first with `override=False`, then cwd with `override=True`
5. **Integration**: Call `load_environment()` at top of `main()` before `create_parser()`

### Test Strategy (TDD)
1. Write unit tests for `find_env_files()` with mocked file system
2. Write unit tests for `load_environment()` with mocked `load_dotenv`
3. Write integration tests that create real temp directories with `.env` files
4. Write acceptance tests validating end-to-end CLI behavior

---

Generated 2026-02-24T23:12:00Z by BA Agent (mode: spec-creation)
<!-- markdown-table-prettify-ignore-end -->
