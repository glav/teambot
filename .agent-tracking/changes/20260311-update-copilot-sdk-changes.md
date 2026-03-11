<!-- markdownlint-disable-file -->
# Release Changes: Update GitHub Copilot SDK to 0.1.32

**Related Plan**: 20260311-update-copilot-sdk-plan.instructions.md
**Implementation Date**: 2026-03-11

## Summary

Updated the `github-copilot-sdk` dependency from version 0.1.23 to 0.1.32. This is a dependency version bump that includes bug fixes and improvements from the upstream SDK. The Python version requirement was updated from >=3.10 to >=3.11 to align with the SDK's requirements. TeamBot version was bumped from 0.4.0 to 0.4.1 (PATCH bump for dependency update).

## Changes

### Added

* No new files added

### Modified

* `pyproject.toml` - Updated SDK dependency (0.1.23 → 0.1.32), Python requirement (>=3.10 → >=3.11), and version (0.4.0 → 0.4.1)
* `src/teambot/__init__.py` - Bumped version from 0.4.0 to 0.4.1
* `uv.lock` - Regenerated with new SDK version 0.1.32
* `.github/workflows/ci.yml` - Removed Python 3.10 from CI matrix (no longer supported)
* `tests/test_acceptance_distribution.py` - Updated version assertions (0.4.0 → 0.4.1, Python >=3.10 → >=3.11)
* `tests/test_sdk_upgrade_acceptance.py` - Updated SDK version assertions (0.1.23 → 0.1.32)
* `tests/test_e2e.py` - Updated version assertion (0.4.0 → 0.4.1)
* `tests/test_distribution.py` - Updated Python version assertion (>=3.10 → >=3.11)

### Removed

* No files removed

## Release Summary

**Total Files Affected**: 8

### Files Created (0)

* None

### Files Modified (8)

* `pyproject.toml` - SDK version, Python requirement, TeamBot version
* `src/teambot/__init__.py` - TeamBot version
* `uv.lock` - Dependency lock with new SDK
* `.github/workflows/ci.yml` - CI matrix Python versions
* `tests/test_acceptance_distribution.py` - Version and Python assertions
* `tests/test_sdk_upgrade_acceptance.py` - SDK version assertions
* `tests/test_e2e.py` - Version assertion
* `tests/test_distribution.py` - Python version assertion

### Files Removed (0)

* None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: `github-copilot-sdk` 0.1.23 → 0.1.32
* **Infrastructure Changes**: CI workflow updated to drop Python 3.10 support
* **Configuration Updates**: Minimum Python version raised to 3.11

### Deployment Notes

* Applications using TeamBot must run on Python 3.11 or higher
* The SDK upgrade is backward compatible - no API changes required in TeamBot code
* All 2038 tests pass with the new SDK version
