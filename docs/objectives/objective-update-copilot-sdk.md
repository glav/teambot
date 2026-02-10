## Objective

Update the GitHub Copilot SDK dependency (`github-copilot-sdk`) from version 0.1.16 to the latest release version 0.1.23.

**Goal**:

- TeamBot currently depends on `github-copilot-sdk==0.1.16`, which is several releases behind the latest stable version (0.1.23).
- Update the pinned dependency to `github-copilot-sdk==0.1.23` to pick up bug fixes, new features, and improvements from the upstream SDK.
- Notable changes in the upgrade path (0.1.16 → 0.1.23) include:
  - Python minimum version bumped to 3.9+ (#151)
  - Added `list_sessions()` method to the Python SDK client (#153)
  - Consistent use of Dataclasses in the Python SDK (#216)
  - Added `githubToken` and `useLoggedInUser` options to all SDK clients (#237)
  - Added hooks and user input handlers to all SDKs (#269)
  - Added `reasoning_effort` support to all SDK clients (#302)
  - Cached `list_models` to prevent rate limiting under concurrency (#300)
  - Replaced `Literal` model type with `string` in Python `SessionConfig` (#325)
  - Various bug fixes including JSON-RPC pipe reads >64KB (#31) and escape issues (#56)
- Ensure that all existing TeamBot functionality remains working after the upgrade.
- Ensure all existing tests pass with the new SDK version.
- Display the installed `github-copilot-sdk` version in the `/help` command output so users can quickly identify which SDK version TeamBot is running against. Currently, the `/help` command (in `src/teambot/repl/commands.py`, `handle_help()`) does not show any version information. The SDK version should be displayed alongside the existing help content (e.g. as a header line or footer line such as "Copilot SDK: 0.1.23").

**Problem Statement**:

- Running an outdated SDK version means TeamBot misses out on upstream bug fixes, performance improvements, and new capabilities.
- Newer SDK features (hooks, user input handlers, reasoning effort support, cached model listing) may be valuable for future TeamBot development.
- Staying current with dependencies reduces the risk of a large, painful upgrade later and ensures compatibility with the latest Copilot CLI.

**Success Criteria**:

- [ ] `pyproject.toml` updated to depend on `github-copilot-sdk==0.1.23`.
- [ ] `uv.lock` regenerated to reflect the new dependency version.
- [ ] All existing tests pass (`uv run pytest`) with no regressions.
- [ ] Linting passes (`uv run ruff check .`).
- [ ] Any breaking API changes from the SDK upgrade are identified and adapted in TeamBot source code.
- [ ] The TeamBot CLI starts and runs successfully with the updated SDK (`uv run teambot --help`).
- [ ] The `/help` command output includes the installed `github-copilot-sdk` version (e.g. "Copilot SDK: 0.1.23").
- [ ] File orchestration functionality is verified to work correctly with the updated SDK (agent lifecycle, workflow state machine, message routing, history management).

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically `pyproject.toml`, `uv.lock`, and any files in `src/teambot/copilot/` that interface with the SDK, plus `src/teambot/repl/commands.py` for the `/help` command enhancement.

**Primary Language/Framework**:

- Python, using the `github-copilot-sdk` package.

**Testing Preference**:

- Follow existing patterns — run the full test suite (`uv run pytest`) and linting (`uv run ruff check .`) to catch regressions.

**Key Constraints**:

- This is a dependency version bump; minimize code changes beyond what is required for compatibility.
- If the new SDK introduces breaking changes to APIs that TeamBot uses, adapt the TeamBot code to the new API while maintaining existing behaviour.
- Do not adopt new SDK features in this objective — focus solely on upgrading and ensuring compatibility. New feature adoption should be handled in separate objectives.

---

## Additional Context

- The SDK changelog and release notes are available at: https://github.com/github/copilot-sdk/releases
- The SDK's Python package is published as `github-copilot-sdk` on PyPI.
- TeamBot's SDK integration code lives primarily in `src/teambot/copilot/` — review this directory for any usage of APIs that may have changed.
- The `Literal` model type was replaced with `string` in `SessionConfig` (#325) — check if TeamBot relies on the old `Literal` type for model selection.
- The Dataclass migration (#216) may change how SDK objects are constructed or accessed — verify TeamBot's usage patterns are compatible.
- After updating `pyproject.toml`, run `uv lock` to regenerate the lockfile, then `uv sync` to install the new version.
- The `/help` command is implemented in `src/teambot/repl/commands.py` in the `handle_help()` function (around line 33). It currently does not display any version information. The SDK version can be retrieved at runtime via `importlib.metadata.version("github-copilot-sdk")` or by reading it from the installed package metadata. Display it as part of the help output header or footer.

---
