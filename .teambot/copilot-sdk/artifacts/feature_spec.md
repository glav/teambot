<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->

# Feature Specification: Upgrade github-copilot-sdk to 0.1.23

| Field | Value |
|-------|-------|
| **Spec ID** | copilot-sdk-upgrade |
| **Status** | Draft |
| **Author** | BA Agent |
| **Created** | 2026-02-10 |
| **Target Codebase** | TeamBot |
| **Primary Language** | Python 3.10+ |
| **Testing Approach** | Hybrid (run existing test suite; add targeted tests for `/help` SDK version display) |

---

## Executive Summary

### Context

TeamBot is a CLI tool that wraps the GitHub Copilot CLI to orchestrate a team of 6 specialized AI agent personas. It communicates with the Copilot backend via the `github-copilot-sdk` Python package. The SDK is currently pinned to version `0.1.16`, which is 7 releases behind the latest stable version (`0.1.23`).

### Opportunity

Upgrading to 0.1.23 delivers bug fixes (JSON-RPC pipe reads >64 KB, escape issues), performance improvements (cached `list_models` preventing rate limiting under concurrency — directly relevant to TeamBot's multi-agent architecture), and keeps TeamBot aligned with the upstream SDK to reduce future upgrade risk.

### Goals

| ID | Goal | Success Metric |
|----|------|----------------|
| G-001 | Update SDK dependency to 0.1.23 | `pyproject.toml` pin reads `github-copilot-sdk==0.1.23`; `uv.lock` regenerated |
| G-002 | Maintain full backward compatibility | All 1084+ existing tests pass with zero regressions |
| G-003 | Adapt to any breaking API changes | `sdk_client.py` works with new SDK; no runtime errors |
| G-004 | Add SDK version visibility to `/help` | `/help` command output includes installed SDK version string |
| G-005 | Clean linting | `uv run ruff check .` reports zero errors |

---

## Problem Definition

### Current Situation

- TeamBot depends on `github-copilot-sdk==0.1.16` (pinned in `pyproject.toml`, line 11).
- The SDK integration surface is small but critical — concentrated in `src/teambot/copilot/sdk_client.py` with supporting imports in `cli.py` and `repl/loop.py`.
- Users and developers have no way to determine which SDK version TeamBot is running against, complicating troubleshooting and support.

### Problem Statement

Running a stale SDK version exposes TeamBot to:

1. **Known bugs** already fixed upstream (JSON-RPC pipe reads >64 KB, escape issues).
2. **Rate limiting under concurrency** — the cached `list_models` fix (#300) directly addresses a problem that TeamBot's multi-agent architecture is prone to.
3. **Growing ecosystem drift** — the longer the gap, the harder and riskier future upgrades become.
4. **Opaque SDK versioning** — no visibility into which SDK version is active, hindering debugging.

### Impact

| Stakeholder | Impact |
|-------------|--------|
| Developers using TeamBot | May encounter SDK bugs that are already fixed upstream |
| TeamBot maintainers | Increasing technical debt from version gap; harder future upgrades |
| End users in multi-agent workflows | Potential rate limiting from uncached `list_models` calls |

---

## Scope

### In Scope

| Area | Description |
|------|-------------|
| Dependency update | Change `pyproject.toml` pin from `0.1.16` to `0.1.23`; regenerate `uv.lock` |
| API compatibility | Identify and adapt to any breaking changes in SDK APIs used by TeamBot |
| Test validation | Full test suite (1084+ tests) must pass; linting must pass |
| `/help` enhancement | Display installed `github-copilot-sdk` version in `/help` command output |

### Out of Scope

| Area | Rationale |
|------|-----------|
| Adopting new SDK features (`githubToken`, `useLoggedInUser`, hooks, `reasoning_effort`) | Separate objectives; this is strictly a compatibility upgrade |
| Changes to CLI-based `CopilotClient` (`src/teambot/copilot/client.py`) | Does not use the SDK |
| Performance benchmarking | Not required for a dependency bump |
| UI/TUI changes beyond `/help` | Not related to SDK upgrade |

---

## Integration Surface Analysis

### Files That Directly Use the SDK

| File | SDK Import/Usage | Risk Level |
|------|-----------------|------------|
| `src/teambot/copilot/sdk_client.py` | `from copilot import CopilotClient`; `from copilot.generated.session_events import SessionEventType`; full session lifecycle (`start`, `stop`, `create_session`, `send_and_wait`, `send`, `on`, `destroy`, `abort`, `list_sessions`, `get_auth_status`) | **High** |
| `src/teambot/copilot/__init__.py` | Re-exports `CopilotSDKClient`, `SDKClientError` | **Low** |
| `src/teambot/repl/loop.py` | Imports `CopilotSDKClient`, `SDKClientError` | **Low** |
| `src/teambot/cli.py` | Initializes `CopilotSDKClient` | **Low** |

### Test Files That Mock the SDK

| File | Mock Surface | Risk Level |
|------|-------------|------------|
| `tests/conftest.py` | `MockSDKResponse` (`.data.content`), `MockSDKSession` (`send_and_wait`, `destroy`, `on`), `MockStreamingSession`, `MockEventTypes`, `MockEventData` | **Medium** |
| `tests/test_copilot/test_sdk_client.py` | ~37 tests mocking `CopilotClient`, session methods, auth status, model resolution | **Medium** |
| `tests/test_copilot/test_sdk_streaming.py` | 14 tests mocking streaming events (`ASSISTANT_MESSAGE_DELTA`, `SESSION_IDLE`, `SESSION_ERROR`, `ABORT`) | **Medium** |

### SDK API Surface Used by TeamBot

| SDK Class/Method | TeamBot Usage Location | Notes |
|-----------------|----------------------|-------|
| `CopilotClient()` | `sdk_client.py:111` | Constructor |
| `client.start()` | `sdk_client.py:112` | Async |
| `client.stop()` | `sdk_client.py:152` | Async |
| `client.get_auth_status()` | `sdk_client.py:124` | Returns dict with `isAuthenticated` key |
| `client.create_session(config)` | `sdk_client.py:219` | Config dict with `session_id`, `streaming`, `model`, `customAgents` |
| `client.list_sessions()` | `sdk_client.py:486` | Synchronous call |
| `session.send_and_wait(dict)` | `sdk_client.py:298,308` | Blocking mode; response has `.data.content` |
| `session.send(dict)` | `sdk_client.py:428` | Non-blocking streaming mode |
| `session.on(callback)` | `sdk_client.py:422` | Event subscription; returns unsubscribe function |
| `session.destroy()` | `sdk_client.py:145,184` | Session cleanup |
| `session.abort()` | `sdk_client.py:472` | Cancel in-progress request |
| `SessionEventType` | `sdk_client.py:13` | Event type enum (used via string normalization) |

---

## Upstream Change Impact Assessment

### Changes from 0.1.16 → 0.1.23

| Change | PR | Impact | Required Action |
|--------|-----|--------|-----------------|
| Python min version → 3.9+ | #151 | **None** | TeamBot requires ≥3.10; already satisfied |
| Added `list_sessions()` | #153 | **None** | TeamBot already uses it; verify signature unchanged |
| Consistent Dataclass usage | #216 | **Medium** | Verify `get_auth_status()` return type; verify `response.data.content` access pattern still works; verify event `.data` attributes |
| Added `githubToken`/`useLoggedInUser` | #237 | **None** | Additive; no adoption needed |
| Added hooks and user input handlers | #269 | **None** | Additive; no adoption needed |
| Added `reasoning_effort` support | #302 | **None** | Additive; no adoption needed |
| Cached `list_models` | #300 | **Beneficial** | No code changes; improves concurrency behavior |
| `Literal` → `string` in `SessionConfig` | #325 | **Low** | TeamBot passes model as plain string already (`session_config["model"] = model`) |
| JSON-RPC pipe reads >64 KB fix | #31 | **Beneficial** | Bug fix; no code changes |
| Escape issues fix | #56 | **Beneficial** | Bug fix; no code changes |

### Key Risk: Dataclass Migration (#216)

The most likely source of breaking changes. Areas to verify:

1. **`get_auth_status()` return type** — currently accessed as `status.get("isAuthenticated", False)` (dict). If now a dataclass, would need `status.isAuthenticated` or similar.
2. **`send_and_wait()` response** — accessed as `response.data.content`. If response structure changed, attribute access may break.
3. **Streaming event data** — accessed via `getattr(event.data, "delta_content", None)` etc. TeamBot already uses `getattr` with fallbacks, which provides resilience.

---

## Functional Requirements

### FR-001: Update SDK Dependency Pin
**Priority**: P0 (Must Have)
**Goal**: G-001
**Description**: Update the `github-copilot-sdk` version pin in `pyproject.toml` from `0.1.16` to `0.1.23`.
**Acceptance Criteria**:
- `pyproject.toml` line 11 reads `"github-copilot-sdk==0.1.23"`
- No other dependency lines are modified

### FR-002: Regenerate Lock File
**Priority**: P0 (Must Have)
**Goal**: G-001
**Description**: Regenerate `uv.lock` to reflect the new SDK version and any transitive dependency changes.
**Acceptance Criteria**:
- `uv.lock` contains `github-copilot-sdk==0.1.23`
- `uv sync` completes without errors
- All transitive dependencies resolve cleanly

### FR-003: Adapt to Breaking API Changes
**Priority**: P0 (Must Have)
**Goal**: G-003
**Description**: If the SDK 0.1.23 introduces breaking changes to any API that TeamBot uses, adapt TeamBot code to work with the new API while preserving existing behavior.
**Acceptance Criteria**:
- `sdk_client.py` works correctly with SDK 0.1.23
- `get_auth_status()` response is handled correctly regardless of dict vs dataclass return type
- `send_and_wait()` response `.data.content` access works
- Streaming event data attribute access works
- `list_sessions()` call works
- Session lifecycle methods (`create_session`, `destroy`, `abort`) work
- No runtime errors when using the SDK

### FR-004: Display SDK Version in `/help` Output
**Priority**: P1 (Should Have)
**Goal**: G-004
**Description**: The `/help` command (in `src/teambot/repl/commands.py`, `handle_help()` function) should display the installed `github-copilot-sdk` version. This should appear when the user runs `/help` with no arguments (the general help view).
**Acceptance Criteria**:
- Running `/help` shows the SDK version (e.g., `Copilot SDK: 0.1.23`)
- The version is retrieved dynamically at runtime using `importlib.metadata.version("github-copilot-sdk")` (preferred) or equivalent
- If the SDK is not installed, a graceful fallback is shown (e.g., `Copilot SDK: not installed`)
- The version display does not break existing help output formatting
- The version appears as a header line or footer line in the help text

### FR-005: Pass Full Test Suite
**Priority**: P0 (Must Have)
**Goal**: G-002
**Description**: All existing tests must pass with the new SDK version without regressions.
**Acceptance Criteria**:
- `uv run pytest` completes with 0 failures
- No tests need to be skipped or disabled due to the upgrade
- If any mock objects in tests need updating (e.g., in `conftest.py`, `test_sdk_client.py`, `test_sdk_streaming.py`), they are updated to match the new SDK API while still testing the same behavior

### FR-006: Pass Linting
**Priority**: P0 (Must Have)
**Goal**: G-005
**Description**: All linting checks must pass after the upgrade.
**Acceptance Criteria**:
- `uv run ruff check .` reports zero errors
- `uv run ruff format --check .` reports no formatting issues

---

## Non-Functional Requirements

### NFR-001: Minimal Code Changes
**Priority**: P0
**Description**: This is a dependency version bump. Code changes must be limited to what is strictly required for SDK compatibility and the `/help` version display enhancement.
**Acceptance Criteria**:
- No new SDK features are adopted
- No refactoring beyond what is required for compatibility
- Changes are confined to `pyproject.toml`, `uv.lock`, `src/teambot/copilot/sdk_client.py` (if API changes), `src/teambot/repl/commands.py` (version display), and test files (if mock updates needed)

### NFR-002: No Performance Regression
**Priority**: P1
**Description**: The SDK upgrade should not introduce measurable performance degradation.
**Acceptance Criteria**:
- Test suite execution time remains within normal range (~90s)
- No new timeouts or delays in agent communication patterns

### NFR-003: Backward-Compatible Behavior
**Priority**: P0
**Description**: All existing TeamBot behaviors must remain unchanged after the upgrade.
**Acceptance Criteria**:
- Agent lifecycle (start, execute, stop) works identically
- Streaming mode works identically
- Blocking mode works identically
- Session management (create, cache, invalidate, retry) works identically
- Error handling patterns unchanged
- `uv run teambot --help` works

---

## Acceptance Test Scenarios

### AT-001: Dependency Update and Resolution
**Description**: Verify the SDK dependency updates cleanly
**Preconditions**: Clean working directory with `github-copilot-sdk==0.1.16` in `pyproject.toml`
**Steps**:
1. Update `pyproject.toml` to pin `github-copilot-sdk==0.1.23`
2. Run `uv sync`
3. Verify `uv.lock` contains the new version
**Expected Result**: `uv sync` completes without errors; `uv.lock` reflects 0.1.23
**Verification**: `grep "github-copilot-sdk" uv.lock` shows 0.1.23

### AT-002: Full Test Suite Passes
**Description**: All existing tests pass with the updated SDK
**Preconditions**: Dependencies synced with SDK 0.1.23
**Steps**:
1. Run `uv run pytest`
2. Review output for failures
**Expected Result**: All 1084+ tests pass with 0 failures, 0 errors
**Verification**: pytest exit code is 0; summary line shows all tests passed

### AT-003: Linting Passes
**Description**: Code passes all lint checks
**Preconditions**: All code changes applied
**Steps**:
1. Run `uv run ruff check .`
2. Run `uv run ruff format --check .`
**Expected Result**: Zero lint errors; zero format issues
**Verification**: Both commands exit with code 0

### AT-004: CLI Startup
**Description**: TeamBot CLI starts successfully with the updated SDK
**Preconditions**: Dependencies synced with SDK 0.1.23
**Steps**:
1. Run `uv run teambot --help`
**Expected Result**: TeamBot help output displays without errors
**Verification**: Exit code 0; help text displayed

### AT-005: `/help` Displays SDK Version
**Description**: The `/help` command shows the installed SDK version
**Preconditions**: TeamBot running in REPL mode (or tested via unit test calling `handle_help`)
**Steps**:
1. Call `handle_help([])` (general help, no arguments)
2. Inspect returned `CommandResult.output`
**Expected Result**: Output contains a line like `Copilot SDK: 0.1.23`
**Verification**: String `Copilot SDK:` appears in output; version matches installed package version

### AT-006: `/help agent` and `/help parallel` Unaffected
**Description**: Subcommand help views are not broken by the version display change
**Preconditions**: Code changes applied
**Steps**:
1. Call `handle_help(["agent"])`
2. Call `handle_help(["parallel"])`
**Expected Result**: Both return their existing help text unchanged
**Verification**: Output matches expected content; no SDK version line in subcommand views

### AT-007: SDK Client Lifecycle
**Description**: The SDK client starts, authenticates, and stops correctly with the new SDK version
**Preconditions**: Dependencies synced; SDK available
**Steps**:
1. Existing tests in `test_sdk_client.py` covering `start()`, `_check_auth()`, `stop()` pass
2. Existing tests covering session creation, caching, and invalidation pass
**Expected Result**: All lifecycle tests pass
**Verification**: `uv run pytest tests/test_copilot/test_sdk_client.py` — 0 failures

### AT-008: Streaming Mode
**Description**: Streaming event handling works correctly with the new SDK
**Preconditions**: Dependencies synced; SDK available
**Steps**:
1. Existing tests in `test_sdk_streaming.py` covering event types (`ASSISTANT_MESSAGE_DELTA`, `SESSION_IDLE`, `SESSION_ERROR`, `ABORT`) pass
2. Event data attribute access (`delta_content`, `error_type`, `message`) works
**Expected Result**: All streaming tests pass
**Verification**: `uv run pytest tests/test_copilot/test_sdk_streaming.py` — 0 failures

---

## Assumptions

1. The `github-copilot-sdk==0.1.23` package is available in the configured package index (PyPI or private registry).
2. TeamBot's Python ≥3.10 requirement satisfies the SDK's new ≥3.9 minimum.
3. The SDK's core client/session API (`CopilotClient`, `start`, `stop`, `create_session`, `send_and_wait`, `send`, `on`, `destroy`, `abort`) retains backward-compatible signatures or any changes are discoverable through test failures.
4. `importlib.metadata.version("github-copilot-sdk")` can retrieve the installed version at runtime.
5. The `SessionEventType` enum values used by TeamBot are still present (TeamBot uses string normalization as a resilience measure, reducing this risk).

---

## Risks and Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R-001 | Dataclass migration (#216) changes response object access patterns | Medium | High | TeamBot already uses `getattr` with fallbacks for event data; verify `get_auth_status()` and `send_and_wait()` response access |
| R-002 | `SessionConfig` type change (#325) breaks session creation | Low | Medium | TeamBot passes config as plain dict with string model names; verify `create_session()` still accepts dict |
| R-003 | New transitive dependencies conflict with existing deps | Low | Medium | `uv sync` will surface conflicts; resolve as needed |
| R-004 | SDK version not discoverable via `importlib.metadata` | Low | Low | Fall back to hardcoded "unknown" or try alternative discovery methods |
| R-005 | Test mocks no longer match real SDK API | Medium | Medium | Update mocks in `conftest.py` and test files to match new API while preserving test intent |

---

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| `github-copilot-sdk==0.1.23` on package index | External | Assumed available |
| `uv` tool installed | Tool | Available in dev environment |
| Full test suite runnable | Environment | Available (1084+ tests) |
| Problem statement (previous stage) | Artifact | ✅ Complete |

---

## Implementation Notes for Builders

> These notes are guidance for the implementation team. The BA does not prescribe implementation details but documents what was learned during analysis.

1. **`pyproject.toml` change is a single line** — line 11, change `0.1.16` to `0.1.23`.
2. **`sdk_client.py` uses defensive coding** — `getattr` with fallbacks for event data, `try/except` for auth check. This reduces breakage risk from dataclass migration.
3. **`get_auth_status()` (line 124-125)** uses `status.get("isAuthenticated", False)` — if return type changed from dict to dataclass, this `.get()` call will fail. This is the most likely breakage point.
4. **`handle_help()` in `commands.py`** returns a `CommandResult` with a multi-line string. The SDK version can be added as a header or footer line using `importlib.metadata.version("github-copilot-sdk")`.
5. **Test mocks in `conftest.py`** define `MockSDKResponse` with `.data.content` — verify this still matches the real SDK response shape.

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-10 | Initial specification | BA Agent |

<!-- markdown-table-prettify-ignore-end -->
