<!-- markdownlint-disable-file -->
# Release Changes: Copilot SDK Upgrade 0.1.16 → 0.1.23

**Related Plan**: N/A — direct implementation from research document
**Implementation Date**: 2026-02-10

## Summary

Upgraded the `github-copilot-sdk` dependency from 0.1.16 to 0.1.23, adapted one breaking API change (`GetAuthStatusResponse` changed from TypedDict to dataclass), updated the `list_sessions()` return type annotation, and added SDK version display to the `/help` command output.

## Changes

### Added

* `tests/test_repl/test_commands.py` - Added `test_help_shows_sdk_version` test asserting `"Copilot SDK:"` appears in help output

### Modified

* `pyproject.toml` - Updated `github-copilot-sdk` pin from `==0.1.16` to `==0.1.23`
* `uv.lock` - Regenerated to reflect new SDK version
* `src/teambot/copilot/sdk_client.py` - Changed `status.get("isAuthenticated", False)` to `getattr(status, "isAuthenticated", False)` in `_check_auth()` to handle dataclass response; updated `list_sessions()` return type from `list[dict[str, Any]]` to `list[Any]`
* `src/teambot/repl/commands.py` - Added `import importlib.metadata`; modified `handle_help()` to display SDK version in header line as "TeamBot Interactive Mode (Copilot SDK: X.Y.Z)"

### Removed

* None

## Release Summary

**Total Files Affected**: 5

### Files Created (0)

### Files Modified (5)

* `pyproject.toml` - Version pin bump
* `uv.lock` - Regenerated lockfile
* `src/teambot/copilot/sdk_client.py` - Breaking change fix + type annotation update
* `src/teambot/repl/commands.py` - SDK version in /help output
* `tests/test_repl/test_commands.py` - New test for SDK version in help

### Files Removed (0)

### Dependencies & Infrastructure

* **Updated Dependencies**: `github-copilot-sdk` 0.1.16 → 0.1.23
* **New Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No special deployment steps required. Standard `uv sync` will install the updated SDK.
