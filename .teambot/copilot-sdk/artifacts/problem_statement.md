# Problem Statement: Upgrade github-copilot-sdk from 0.1.16 to 0.1.23

## Business Problem

TeamBot depends on `github-copilot-sdk==0.1.16`, which is **7 patch releases behind** the latest stable version (0.1.23). Running on a stale SDK version exposes TeamBot to:

1. **Known bugs** that have already been fixed upstream (e.g., JSON-RPC pipe reads >64 KB, escape issues).
2. **Missing improvements** such as cached `list_models` to prevent rate limiting under concurrency — directly relevant to TeamBot's multi-agent architecture where concurrent SDK calls are common.
3. **Ecosystem drift** — as the SDK evolves, the gap between TeamBot's pinned version and the latest grows, making future upgrades progressively harder and riskier.
4. **Lack of version visibility** — users and developers currently have no way to determine which SDK version TeamBot is running against, complicating troubleshooting and support.

## Scope

### In Scope

| Area | Details |
|------|---------|
| **Dependency bump** | Update `pyproject.toml` pin from `0.1.16` to `0.1.23`; regenerate `uv.lock`. |
| **API compatibility** | Identify and adapt to any breaking changes in the SDK APIs that TeamBot uses (see integration surface below). |
| **Regression testing** | Full test suite (`uv run pytest`, 1084+ tests) and linting (`uv run ruff check .`) must pass. |
| **Version display** | Add the installed `github-copilot-sdk` version to the `/help` command output in `src/teambot/repl/commands.py`. |

### Out of Scope

- Adopting **new** SDK features (e.g., `githubToken`/`useLoggedInUser` options, hooks, user input handlers, `reasoning_effort`). These should be evaluated in separate objectives.
- Changes to the CLI-based `CopilotClient` wrapper (`src/teambot/copilot/client.py`) — it does not use the SDK.
- Performance benchmarking or load testing.

## Current Integration Surface

TeamBot's SDK integration is concentrated in a small set of files. These are the areas at risk from breaking changes:

| File | SDK Dependency | Risk |
|------|----------------|------|
| `src/teambot/copilot/sdk_client.py` | `CopilotClient`, `SessionEventType`, session lifecycle (`start`, `stop`, `create_session`, `send_and_wait`, `send`, `on`, `destroy`, `abort`, `list_sessions`) | **High** — primary integration point |
| `src/teambot/repl/loop.py` | Imports `CopilotSDKClient`, `SDKClientError` | **Low** — wrapper around sdk_client |
| `src/teambot/cli.py` | Initializes `CopilotSDKClient` | **Low** — wrapper around sdk_client |
| `tests/test_copilot/test_sdk_client.py` | Mocks SDK classes and methods | **Medium** — mocks may need updating if SDK API signatures change |
| `tests/test_copilot/test_sdk_streaming.py` | Mocks streaming event types | **Medium** — event type enums may have changed |

## Notable Upstream Changes (0.1.16 → 0.1.23)

| Change | PR | Impact Assessment |
|--------|-----|-------------------|
| Python minimum version bumped to 3.9+ | #151 | **Low** — TeamBot already requires Python ≥3.10 (`pyproject.toml`). |
| Added `list_sessions()` method | #153 | **Low** — TeamBot already uses `list_sessions()`, so this was likely backported or available. Verify no signature change. |
| Consistent Dataclass usage in Python SDK | #216 | **Medium** — if response objects changed from dicts to dataclasses, TeamBot's attribute access patterns may need adaptation. |
| Added `githubToken` and `useLoggedInUser` options | #237 | **Low** — additive; no adoption needed. |
| Added hooks and user input handlers | #269 | **Low** — additive; no adoption needed. |
| Added `reasoning_effort` support | #302 | **Low** — additive; no adoption needed. |
| Cached `list_models` to prevent rate limiting | #300 | **Low** — beneficial, no code changes needed. |
| Replaced `Literal` model type with `string` in `SessionConfig` | #325 | **Medium** — if TeamBot passes model names via `Literal` types, the type interface may have changed. |
| JSON-RPC pipe reads >64 KB fix | #31 | **Low** — bug fix, no code changes needed. |
| Escape issues fix | #56 | **Low** — bug fix, no code changes needed. |

## Goals

1. **Update dependency**: Pin `github-copilot-sdk==0.1.23` in `pyproject.toml` and regenerate `uv.lock`.
2. **Maintain compatibility**: All existing TeamBot functionality (agent lifecycle, workflow state machine, message routing, history management, REPL, streaming) continues to work.
3. **Pass all tests**: Full suite of 1084+ tests passes with zero regressions.
4. **Pass linting**: `uv run ruff check .` reports no errors.
5. **Display SDK version**: `/help` command shows the installed SDK version (e.g., `Copilot SDK: 0.1.23`).

## Success Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | `pyproject.toml` depends on `github-copilot-sdk==0.1.23` | Inspect file |
| 2 | `uv.lock` reflects the new version | Inspect file |
| 3 | All existing tests pass | `uv run pytest` — 0 failures |
| 4 | Linting passes | `uv run ruff check .` — 0 errors |
| 5 | Breaking API changes identified and adapted | Code review of `sdk_client.py` |
| 6 | TeamBot CLI starts successfully | `uv run teambot --help` |
| 7 | `/help` output includes SDK version | Manual or test verification |
| 8 | Orchestration functionality intact | Existing orchestration tests pass |

## Assumptions

1. The `github-copilot-sdk` 0.1.23 package is available in the configured package index.
2. TeamBot's Python version requirement (≥3.10) satisfies the SDK's new minimum (3.9+).
3. The SDK's `CopilotClient` constructor, `start()`, `stop()`, `create_session()`, and session methods (`send_and_wait`, `send`, `on`, `destroy`, `abort`) retain backward-compatible signatures.
4. `SessionEventType` enum values used by TeamBot (`ASSISTANT_MESSAGE_DELTA`, `SESSION_IDLE`, `SESSION_ERROR`, `ABORT`) are still present.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| SDK API breaking changes in session/client methods | Medium | Review SDK changelog; adapt `sdk_client.py` as needed |
| Dataclass migration changes response object access patterns | Medium | Test response handling; update attribute access if needed |
| New transitive dependencies conflict with existing ones | Low | `uv sync` will surface conflicts; resolve as needed |
| SDK version not discoverable at runtime via `importlib.metadata` | Low | Fall back to `pkg_resources` or hardcoded version |

## Dependencies

- Access to the `github-copilot-sdk` 0.1.23 package from the package index.
- `uv` tool for dependency resolution and lock file regeneration.
- Full test suite must be runnable in the development environment.
