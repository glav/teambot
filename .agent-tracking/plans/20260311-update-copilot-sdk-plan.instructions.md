---
applyTo: '.agent-tracking/changes/20260311-update-copilot-sdk-changes.md'
---
<!-- markdownlint-disable-file -->
# Task Checklist: Update GitHub Copilot SDK to Latest Version

## Overview

Update the `github-copilot-sdk` dependency from version 0.1.23 to 0.1.32, update Python requirement to >=3.11, and bump TeamBot version to 0.4.1.

## Objectives

* Update `github-copilot-sdk` from 0.1.23 to 0.1.32
* Update Python requirement from >=3.10 to >=3.11 (SDK requirement)
* Bump TeamBot version from 0.4.0 to 0.4.1 (PATCH for dependency update)
* Regenerate `uv.lock` with new dependency
* Verify all tests and linting pass

## Research Summary

### Project Files
* `pyproject.toml` - Contains SDK dependency, Python requirement, and version
* `src/teambot/__init__.py` - Contains `__version__` that must stay in sync
* `src/teambot/copilot/sdk_client.py` - SDK integration (no changes needed)

### External References
* .agent-tracking/research/20260311-update-copilot-sdk-research.md - Comprehensive SDK upgrade analysis
* PyPI SDK Info (https://pypi.org/project/github-copilot-sdk/) - Latest version 0.1.32 confirmed

### Standards References
* Version sync required between `pyproject.toml` and `src/teambot/__init__.py`
* Use exact version pinning (`==X.Y.Z`) for reproducibility

## Implementation Checklist

### [x] Phase 1: Dependency and Version Updates

**Phase Objective**: Update all version references in configuration files

* [x] Task 1.1: Update SDK dependency version
  * Details: .agent-tracking/details/20260311-update-copilot-sdk-details.md (Lines 13-27)
  * Dependencies: None
  * Priority: CRITICAL

* [x] Task 1.2: Update Python version requirement
  * Details: .agent-tracking/details/20260311-update-copilot-sdk-details.md (Lines 29-43)
  * Dependencies: None
  * Priority: CRITICAL

* [x] Task 1.3: Bump TeamBot version in pyproject.toml
  * Details: .agent-tracking/details/20260311-update-copilot-sdk-details.md (Lines 45-59)
  * Dependencies: None
  * Priority: CRITICAL

* [x] Task 1.4: Bump TeamBot version in __init__.py
  * Details: .agent-tracking/details/20260311-update-copilot-sdk-details.md (Lines 61-75)
  * Dependencies: Task 1.3 (versions must match)
  * Priority: CRITICAL

#### Phase Gate: Phase 1 Complete When
- [x] All Phase 1 tasks marked complete
- [x] `pyproject.toml` has `github-copilot-sdk==0.1.32`
- [x] `pyproject.toml` has `requires-python = ">=3.11"`
- [x] `pyproject.toml` has `version = "0.4.1"`
- [x] `src/teambot/__init__.py` has `__version__ = "0.4.1"`

**Cannot Proceed If**: Version numbers don't match between files

### [x] Phase 2: Lock File Regeneration

**Phase Objective**: Regenerate dependency lock file with new SDK version

* [x] Task 2.1: Regenerate uv.lock
  * Details: .agent-tracking/details/20260311-update-copilot-sdk-details.md (Lines 79-93)
  * Dependencies: Phase 1 completion
  * Priority: CRITICAL

#### Phase Gate: Phase 2 Complete When
- [x] `uv sync` completes successfully
- [x] `uv.lock` contains `github-copilot-sdk==0.1.32`
- [x] No dependency resolution errors

**Cannot Proceed If**: `uv sync` fails

### [x] Phase 3: Verification (Code-First Testing)

**Phase Objective**: Verify upgrade hasn't introduced regressions

**Test Strategy**: Code-First - Tests run AFTER dependency changes

* [x] Task 3.1: Run full test suite
  * Details: .agent-tracking/details/20260311-update-copilot-sdk-details.md (Lines 97-111)
  * Dependencies: Phase 2 completion
  * Priority: CRITICAL

* [x] Task 3.2: Run SDK-specific tests
  * Details: .agent-tracking/details/20260311-update-copilot-sdk-details.md (Lines 113-127)
  * Dependencies: Task 3.1
  * Priority: HIGH

* [x] Task 3.3: Run linting checks
  * Details: .agent-tracking/details/20260311-update-copilot-sdk-details.md (Lines 129-143)
  * Dependencies: Phase 2 completion
  * Priority: HIGH

* [x] Task 3.4: Verify CLI startup
  * Details: .agent-tracking/details/20260311-update-copilot-sdk-details.md (Lines 145-159)
  * Dependencies: Phase 2 completion
  * Priority: HIGH

#### Phase Gate: Phase 3 Complete When
- [x] All tests pass (`uv run pytest`)
- [x] SDK tests pass (`uv run pytest tests/test_copilot/`)
- [x] Linting passes (`uv run ruff check .`)
- [x] Formatting passes (`uv run ruff format --check .`)
- [x] CLI starts (`uv run teambot --help`)

**Cannot Proceed If**: Any test or linting failures

## Dependencies

* `uv` package manager
* Python 3.11+
* `ruff` linter
* `pytest` test framework

## Success Criteria

* `github-copilot-sdk==0.1.32` in pyproject.toml
* `requires-python = ">=3.11"` in pyproject.toml
* TeamBot version 0.4.1 in both pyproject.toml and __init__.py
* `uv.lock` regenerated successfully
* All tests pass (102+ tests)
* Linting passes
* CLI starts without errors
