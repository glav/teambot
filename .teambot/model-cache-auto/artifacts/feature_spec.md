<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Model Cache Auto-Setup and Login Validation - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target v0.2.x | Lifecycle Specification

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-19 |
| Problem & Users | ✅ | None | 2026-02-19 |
| Scope | ✅ | None | 2026-02-19 |
| Requirements | ✅ | None | 2026-02-19 |
| Metrics & Risks | ✅ | None | 2026-02-19 |
| Operationalization | ✅ | None | 2026-02-19 |
| Finalization | ✅ | None | 2026-02-19 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot is a CLI tool that orchestrates multi-agent AI workflows using the GitHub Copilot CLI. The `teambot run` command initiates workflow execution, but currently assumes users have already authenticated with Copilot and populated the model cache. This creates a frustrating first-run experience where valid configurations fail with confusing errors.

### Core Opportunity
Enable `teambot run` to automatically validate authentication and populate the model cache when missing, providing a seamless "just works" experience for new and returning users.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Seamless first-run experience | User Experience | Manual steps required | Zero manual steps | v0.2.x | P0 |
| G-002 | Clear authentication error messaging | User Experience | Confusing "Invalid model" error | Actionable "Run copilot auth" message | v0.2.x | P0 |
| G-003 | Automatic cache recovery | Reliability | Manual refresh required | Auto-refresh when missing | v0.2.x | P0 |
| G-004 | Maintain existing performance | Performance | Current startup time | No degradation when cache exists | v0.2.x | P1 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Eliminate first-run failures | 0 model validation errors for authenticated users | P0 | Builder |
| Improve error clarity | Auth errors include "copilot auth" instruction | P0 | Builder |
| Ensure backward compatibility | All existing tests pass | P0 | Builder |

## 2. Problem Definition

### Current Situation
When users execute `teambot run` for the first time after installation, they encounter:

```
Configuration error: Invalid model 'claude-sonnet-4' for agent 'pm'. 
Use '/models' command to see available models.
```

The `cmd_run()` function in `src/teambot/cli.py`:
1. Checks if Copilot CLI is installed (line 783-785)
2. Loads configuration via `ConfigLoader.load()` (line 399-409)
3. Validates models during config loading (triggers `_ensure_models_loaded()`)

Unlike `cmd_init()`, the `cmd_run()` function does NOT:
- Check Copilot authentication status
- Refresh the model cache when missing

### Problem Statement
`teambot run` fails with opaque errors when the model cache is missing or expired, requiring users to know undocumented commands (`/models --refresh`) to resolve the issue. Additionally, unauthenticated users receive model validation errors instead of clear authentication guidance.

### Root Causes
* **No authentication check in run flow** - `_check_copilot_authentication()` exists but is only called in `cmd_init()`
* **No automatic cache initialization** - `_refresh_model_cache()` exists but is only called in `cmd_init()`
* **Error messaging assumes cache exists** - Model validation errors don't distinguish between "missing cache" and "invalid model"

### Impact of Inaction
* New users abandon TeamBot due to frustrating first-run experience
* Support burden increases with "it doesn't work" issues
* User trust erodes when valid configurations fail inexplicably
* Returning users encounter unexpected failures after cache expiration (24+ hours)

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| **New User** | Run TeamBot immediately after installation | Confusing error on first run; doesn't know manual steps | High - First impression determines adoption |
| **Returning User** | Continue workflow after break (24+ hours) | Unexpected failure after cache expires | Medium - Interrupts established workflow |
| **CI/CD Pipeline** | Automated TeamBot execution | Silent failures without actionable guidance | Medium - Blocks automation |
| **Developer** | Quick iteration with TeamBot | Manual cache management overhead | Low - Can workaround but friction adds up |

### Journeys

**New User Journey (Current State):**
1. Install TeamBot and Copilot CLI ✅
2. Run `copilot auth` ✅
3. Run `teambot init` ✅
4. Run `teambot run objectives/task.md` ❌ "Invalid model" error
5. Search for solution, find undocumented command
6. Run `/models --refresh` manually
7. Retry `teambot run` ✅

**New User Journey (Target State):**
1. Install TeamBot and Copilot CLI ✅
2. Run `copilot auth` ✅
3. Run `teambot init` ✅
4. Run `teambot run objectives/task.md` ✅ (auto-refreshes cache)

## 4. Scope

### In Scope
* Authentication check before model validation in `cmd_run()`
* Automatic model cache refresh when cache is missing or empty
* User feedback during cache refresh ("Refreshing model cache...")
* Clear error messages for authentication and network failures
* Unit tests for new authentication check flow
* Acceptance tests for auto-refresh behavior
* Integration with existing `_check_copilot_authentication()` and `_refresh_model_cache()` functions

### Out of Scope (justified)
* **Automatic re-authentication** - Security concern; users must explicitly run `copilot auth`
* **Background/scheduled cache refresh** - Adds complexity; synchronous refresh is sufficient
* **Changes to `teambot init`** - Already handles auth check and cache refresh correctly
* **Cache refresh during `teambot status`** - Read-only command; should not trigger side effects
* **Expired cache handling** - Existing warning behavior is acceptable; auto-refresh only for missing cache

### Assumptions
* `_check_copilot_authentication()` returns `False` when not authenticated (verified in code)
* `_refresh_model_cache()` is idempotent and safe to call multiple times
* Users accept 2-5 second delay for one-time cache population
* Console output ("Refreshing model cache...") is preferable to silent delay

### Constraints
* **No breaking changes** - Existing `teambot init` and `teambot run` behavior must be preserved when cache exists
* **Fast authentication check** - Must complete in < 2 seconds
* **Graceful degradation** - Network failures must not crash the application
* **Existing function reuse** - Must use `_check_copilot_authentication()` and `_refresh_model_cache()` without modification

## 5. Product Overview

### Value Proposition
For TeamBot users who want a frictionless first-run experience, Model Cache Auto-Setup eliminates manual cache management by automatically validating authentication and refreshing the model cache when needed, unlike the current flow which fails with confusing errors.

### Differentiators
* **Fail-fast with clarity** - Authentication errors stop immediately with actionable guidance
* **Self-healing** - Recoverable issues (missing cache) resolved automatically
* **Transparent operation** - Users see what's happening during auto-refresh
* **Zero regression** - Existing users see no change to their workflow

### UX / UI
**Console Output Additions:**

| Scenario | Output |
|----------|--------|
| Auth check (success) | No output (silent success) |
| Auth check (failure) | `"Error: Copilot CLI not authenticated. Run 'copilot auth' first."` |
| Cache refresh (starting) | `"Refreshing model cache..."` |
| Cache refresh (success) | `"Model cache refreshed successfully."` |
| Cache refresh (failure) | `"Error: Could not refresh model cache. Check network and retry."` |

UX Status: Specified

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Auth Check Before Run | `teambot run` checks Copilot CLI authentication before loading config | G-002 | All | P0 | Auth check executes before `ConfigLoader.load()` | Reuse `_check_copilot_authentication()` |
| FR-002 | Auth Failure Stops Execution | If auth check fails, `teambot run` exits with error code 1 and clear message | G-002 | All | P0 | Exit message includes "Run 'copilot auth' first" | No further processing after auth failure |
| FR-003 | Cache Missing Detection | `teambot run` detects when model cache file is missing or empty | G-003 | All | P0 | Detection occurs after auth check, before config load | Check `model_cache.py` state |
| FR-004 | Auto Cache Refresh | When cache is missing, automatically call `_refresh_model_cache()` | G-001, G-003 | All | P0 | Equivalent to `/models --refresh` behavior | Only when cache missing, not expired |
| FR-005 | Refresh Status Output | Display "Refreshing model cache..." during refresh operation | G-001 | All | P1 | User sees progress indication | Use existing ConsoleDisplay |
| FR-006 | Refresh Success Continuation | After successful refresh, `teambot run` proceeds normally | G-001 | All | P0 | Command completes workflow | No user intervention required |
| FR-007 | Refresh Failure Handling | If refresh fails, exit with clear error and guidance | G-002 | All | P0 | Error includes retry/network guidance | Don't proceed with stale/missing cache |
| FR-008 | Cache Exists No-Op | When valid cache exists, skip auth check display and refresh | G-004 | Returning User | P0 | No startup delay when cache valid | Preserve existing performance |

### Feature Hierarchy
```plain
cmd_run()
├── Pre-execution Checks
│   ├── check_copilot_cli() [existing]
│   ├── _check_copilot_authentication() [NEW: add to flow]
│   └── model_cache_exists_check() [NEW: add logic]
│       └── _refresh_model_cache() [conditional call]
├── Config Loading [existing]
└── Workflow Execution [existing]
```

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Performance | Auth check completes quickly | < 2 seconds | P0 | Time `_check_copilot_authentication()` | Use existing async implementation |
| NFR-002 | Performance | No startup delay when cache exists | 0ms additional latency | P0 | Compare startup time before/after | Skip unnecessary checks |
| NFR-003 | Reliability | Network failures don't crash app | Exit gracefully with code 1 | P0 | Test with network disabled | Catch all exceptions |
| NFR-004 | Reliability | Auth check timeout | < 5 seconds | P1 | Kill hung checks | Prevent indefinite blocking |
| NFR-005 | Maintainability | Reuse existing functions | 0 new network/auth code | P0 | Code review | Use `_check_copilot_authentication()`, `_refresh_model_cache()` |
| NFR-006 | Observability | Log auth and refresh operations | Debug-level logging | P2 | Review logs | Aid troubleshooting |

## 8. Data & Analytics

### Inputs
* Copilot CLI authentication state (via `CopilotSDKClient`)
* Model cache file presence (`~/.teambot/model_cache.json` or configured path)
* Model cache file contents (empty vs populated)

### Outputs / Events
* Console messages (auth status, refresh progress)
* Exit codes (0 success, 1 auth failure, 1 refresh failure)
* Updated model cache file (after successful refresh)

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|--------|---------|-------|
| auth_check_start | Before auth check | timestamp | Performance tracking | Builder |
| auth_check_result | After auth check | success: bool, duration_ms | Success rate monitoring | Builder |
| cache_refresh_start | Before refresh | cache_missing: bool | Usage pattern | Builder |
| cache_refresh_result | After refresh | success: bool, duration_ms | Reliability monitoring | Builder |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| First-run success rate | Outcome | Unknown (assumed low) | 100% for authenticated users | Per release | User reports |
| Auth error clarity | Qualitative | Confusing | Actionable | Per release | User feedback |
| Startup time (cache exists) | Performance | Current | No increase | Per release | Benchmark |
| Auto-refresh success rate | Reliability | N/A | > 95% | Weekly | Logs |

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| Copilot CLI | External | Critical | GitHub | API changes | Version pin, graceful fallback |
| `_check_copilot_authentication()` | Internal | Critical | TeamBot | None | Existing, tested function |
| `_refresh_model_cache()` | Internal | Critical | TeamBot | None | Existing, tested function |
| Network connectivity | External | Medium | User | Unavailable | Clear error messaging |
| `ConsoleDisplay` | Internal | Low | TeamBot | None | Existing utility |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Auth check slows startup for all users | Medium | Low | Only check when cache missing | Builder | Open |
| R-002 | Network timeout blocks startup indefinitely | High | Low | Add timeout to auth check (5s) | Builder | Open |
| R-003 | Refresh fails silently, user confused | Medium | Low | Clear error with actionable guidance | Builder | Open |
| R-004 | Breaking change to existing workflows | High | Low | Extensive test coverage, skip when cache exists | Builder | Open |
| R-005 | Copilot CLI API changes break auth check | Medium | Low | Try-catch with fallback behavior | Builder | Open |

## 11. Privacy, Security & Compliance

### Data Classification
* **Model cache**: Public (list of available model names)
* **Authentication state**: Sensitive (handled by Copilot CLI, not stored)

### PII Handling
No PII is processed or stored by this feature.

### Threat Considerations
* **Auth bypass**: Feature adds a check, doesn't weaken security
* **Cache poisoning**: Model cache validated against Copilot API
* **Network interception**: Copilot CLI handles TLS

### Regulatory / Compliance
| Regulation | Applicability | Action | Owner | Status |
|-----------|--------------|--------|-------|--------|
| N/A | Not applicable | None required | - | Complete |

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Standard Python package update | No infrastructure changes |
| Rollback | Revert to previous version | Standard pip/uv rollback |
| Monitoring | CLI exit codes, user error reports | No new infrastructure needed |
| Alerting | N/A for CLI tool | User-initiated runs |
| Support | Document new behavior in README | FAQ for common issues |
| Capacity Planning | N/A | Client-side only |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|--------------|-------|
| Implementation | TBD | All FRs implemented | Builder |
| Testing | TBD | All tests pass, coverage > 80% | Builder |
| Review | TBD | Code review approved | Reviewer |
| Release | TBD | Merged to main, CI green | PM |

### Feature Flags
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|--------|----------------|
| N/A | No feature flags needed | - | - |

### Communication Plan
Update README with new auto-refresh behavior and troubleshooting guide.

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| - | None | - | - | - |

## 15. Acceptance Test Scenarios

### AT-001: First Run After Installation (Happy Path)
**Description**: User runs `teambot run` for the first time with valid authentication but no model cache
**Preconditions**:
- TeamBot and Copilot CLI installed
- User authenticated via `copilot auth`
- Model cache file does not exist (`~/.teambot/model_cache.json` missing)
- Valid `teambot.json` configuration exists
- Objective file exists

**Steps**:
1. User runs `teambot run objectives/sample-task.md`
2. System checks Copilot authentication (passes)
3. System detects missing model cache
4. System displays "Refreshing model cache..."
5. System refreshes model cache from Copilot API
6. System displays "Model cache refreshed successfully."
7. System loads configuration and validates models
8. Workflow execution begins

**Expected Result**: `teambot run` completes successfully without user intervention
**Verification**: Exit code 0, workflow enters SETUP stage, no "Invalid model" errors

---

### AT-002: Unauthenticated User
**Description**: User attempts `teambot run` without Copilot authentication
**Preconditions**:
- TeamBot and Copilot CLI installed
- User NOT authenticated (no `copilot auth` run)
- Model cache may or may not exist

**Steps**:
1. User runs `teambot run objectives/sample-task.md`
2. System checks Copilot authentication (fails)
3. System displays error: "Error: Copilot CLI not authenticated. Run 'copilot auth' first."
4. System exits immediately

**Expected Result**: Clear error message with actionable guidance
**Verification**: Exit code 1, message contains "copilot auth", no model validation attempted

---

### AT-003: Network Failure During Cache Refresh
**Description**: Cache refresh fails due to network unavailability
**Preconditions**:
- TeamBot and Copilot CLI installed
- User authenticated via `copilot auth`
- Model cache file does not exist
- Network unavailable (simulated)

**Steps**:
1. User runs `teambot run objectives/sample-task.md`
2. System checks Copilot authentication (passes)
3. System detects missing model cache
4. System displays "Refreshing model cache..."
5. System attempts refresh, fails due to network
6. System displays error: "Error: Could not refresh model cache. Check network connection and try again."
7. System exits

**Expected Result**: Clear error with network-related guidance
**Verification**: Exit code 1, message suggests network check, no workflow execution

---

### AT-004: Returning User With Valid Cache (No-Op)
**Description**: User with existing valid cache experiences no change
**Preconditions**:
- TeamBot configured and previously used
- Model cache exists and is valid
- User authenticated

**Steps**:
1. User runs `teambot run objectives/sample-task.md`
2. System detects valid cache exists
3. System skips auth check display and cache refresh
4. System loads configuration normally
5. Workflow execution begins

**Expected Result**: Startup time unchanged, no refresh messages displayed
**Verification**: Exit code 0, no "Refreshing model cache..." output, startup time within baseline

---

### AT-005: Cache Exists But Empty
**Description**: Cache file exists but contains no models
**Preconditions**:
- Model cache file exists but is empty (`{}` or `{"models": []}`)
- User authenticated

**Steps**:
1. User runs `teambot run objectives/sample-task.md`
2. System checks Copilot authentication (passes)
3. System detects cache is empty
4. System displays "Refreshing model cache..."
5. System refreshes cache successfully
6. Workflow execution begins

**Expected Result**: Empty cache treated same as missing cache
**Verification**: Exit code 0, cache populated after refresh, workflow proceeds

## 16. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-02-19 | BA Agent | Initial specification | Creation |

## 17. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Code | src/teambot/cli.py | Existing `_check_copilot_authentication()` and `_refresh_model_cache()` functions | Use existing implementations |
| REF-002 | Code | src/teambot/config/model_cache.py | Cache file operations | Reference for cache detection |
| REF-003 | Code | src/teambot/config/schema.py | Model validation flow | Integration point |
| REF-004 | Document | .teambot/model-cache-auto/artifacts/problem_statement.md | Problem definition and user stories | Source of requirements |

### Citation Usage
Problem statement and user stories derived from REF-004. Implementation approach informed by analysis of REF-001 through REF-003.

## 18. Technical Context

### Target Codebase
| File | Purpose |
|------|---------|
| `src/teambot/cli.py` | CLI entry point; `cmd_run()` function to be modified |
| `src/teambot/config/schema.py` | Model validation and cache loading |
| `src/teambot/config/model_cache.py` | Cache file operations |
| `src/teambot/config/loader.py` | Configuration loading |

### Primary Language/Framework
Python (existing codebase)

### Testing Approach
**Test-Driven Development (TDD)** - Write tests first, then implement

### Existing Functions to Reuse
| Function | Location | Returns | Console Output |
|----------|----------|---------|----------------|
| `_check_copilot_authentication(display)` | cli.py:89-115 | `bool` | Success/warning messages |
| `_refresh_model_cache(display)` | cli.py:41-63 | `bool` | Success/warning messages |
| `check_copilot_cli()` | cli.py | `bool` | None (returns status only) |

## 19. Appendices

### Glossary
| Term | Definition |
|------|-----------|
| Model cache | JSON file storing list of available Copilot models |
| Copilot CLI | GitHub Copilot command-line interface |
| Auth check | Verification that user is authenticated with Copilot |

### Additional Notes
The implementation should add pre-execution checks to `cmd_run()` following the pattern established by `cmd_init()`, which already calls both `_check_copilot_authentication()` and `_refresh_model_cache()` during initialization.

---

Generated 2026-02-19 by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
