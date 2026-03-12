---
feature_name: update-copilot-sdk
language: python
framework: ""
test_preference: code-first
scope: small
acceptance_scenarios:
  - name: "SDK version updated in pyproject.toml"
    steps:
      - "Check current github-copilot-sdk version in pyproject.toml"
      - "Query PyPI for latest github-copilot-sdk version"
      - "Update pyproject.toml to latest version"
      - "Run uv lock to regenerate lockfile"
    expected: "pyproject.toml contains latest SDK version, uv.lock is updated"
  - name: "All tests pass with updated SDK"
    steps:
      - "Run uv sync to install updated dependencies"
      - "Run uv run pytest to execute test suite"
    expected: "All existing tests pass with no regressions"
  - name: "CLI starts successfully"
    steps:
      - "Run uv run teambot --help"
      - "Run uv run teambot --version"
    expected: "CLI starts and displays help/version without errors"
  - name: "Linting passes"
    steps:
      - "Run uv run ruff check ."
      - "Run uv run ruff format --check ."
    expected: "No linting or formatting errors"
  - name: "SDK integration works"
    steps:
      - "Import github_copilot_sdk in Python"
      - "Verify SDK classes/functions used by TeamBot are accessible"
      - "Run SDK-related tests in tests/test_copilot/"
    expected: "SDK initializes and TeamBot's SDK integration tests pass"
---

## Objective

Update the GitHub Copilot SDK dependency (`github-copilot-sdk`) from the current pinned version 0.1.23 to the latest release version available on PyPI.

**Goal**:

- TeamBot currently depends on `github-copilot-sdk==0.1.23`.
- Update the pinned dependency to the latest stable release to pick up bug fixes, new features, and improvements from the upstream SDK.
- Ensure that all existing TeamBot functionality remains working after the upgrade.
- Ensure all existing tests pass with the new SDK version.

**Problem Statement**:

- Running an outdated SDK version means TeamBot misses out on upstream bug fixes, performance improvements, and new capabilities.
- Staying current with dependencies reduces the risk of a large, painful upgrade later and ensures compatibility with the latest Copilot CLI.
- Newer SDK features may be valuable for future TeamBot development.

**Success Criteria**:

- [ ] `pyproject.toml` updated to depend on the latest `github-copilot-sdk` version (use exact pinning `==X.Y.Z` for reproducibility).
- [ ] `uv.lock` regenerated to reflect the new dependency version.
- [ ] All existing tests pass (`uv run pytest`) with no regressions.
- [ ] Linting passes (`uv run ruff check .` and `uv run ruff format --check .`).
- [ ] Any breaking API changes from the SDK upgrade are identified and adapted in TeamBot source code.
- [ ] The TeamBot CLI starts and runs successfully with the updated SDK (`uv run teambot --help`).
- [ ] SDK integration tests pass (`uv run pytest tests/test_copilot/`).
- [ ] TeamBot version bumped according to semver (PATCH bump for dependency update, e.g., 0.4.0 → 0.4.1) in both `pyproject.toml` and `src/teambot/__init__.py`.

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically `pyproject.toml`, `uv.lock`, `src/teambot/__init__.py` (version), and any files in `src/teambot/copilot/` that interface with the SDK.

**Primary Language/Framework**:

- Python, using the `github-copilot-sdk` package.

**Testing Preference**:

- Code-first — run the full test suite (`uv run pytest`) and linting (`uv run ruff check .`) to catch regressions.

**Key Constraints**:

- This is a dependency version bump; minimize code changes beyond what is required for compatibility.
- If the new SDK introduces breaking changes to APIs that TeamBot uses, adapt the TeamBot code to the new API while maintaining existing behaviour.
- Do not adopt new SDK features in this objective — focus solely on upgrading and ensuring compatibility. New feature adoption should be handled in separate objectives.
- Use exact version pinning (`==X.Y.Z`) rather than range constraints for reproducibility.
- Bump TeamBot version in **both** `pyproject.toml` and `src/teambot/__init__.py` (they must stay in sync).

---

## Additional Context

- The SDK's Python package is published as `github-copilot-sdk` on PyPI.
- To find the latest version and changelog, check PyPI: https://pypi.org/project/github-copilot-sdk/
- TeamBot's SDK integration code lives primarily in `src/teambot/copilot/` — review this directory for any usage of APIs that may have changed.
- After updating `pyproject.toml`, run `uv lock` to regenerate the lockfile, then `uv sync` to install the new version.

**Rollback Procedure**:

If the upgrade causes failures that cannot be quickly resolved:
1. Revert `pyproject.toml` to the previous SDK version (`github-copilot-sdk==0.1.23`)
2. Run `uv lock` to regenerate the lockfile
3. Run `uv sync` to restore the previous working state

---
