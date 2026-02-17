<!-- markdownlint-disable-file -->
# Release Changes: Map Repo Files to Package Location

**Related Plan**: 20260217-map-repo-files-plan.instructions.md
**Implementation Date**: 2026-02-17

## Summary

Enhance `teambot init` to automatically copy scaffolding files (stages.yaml, AGENTS.md, .agent/, .github/agents/, docs/sdd-objective-template.md) from the installed package to user repositories with conditional copying that never overwrites existing files.

## Changes

### Added

* `tests/test_scaffolds.py` - Unit test file for scaffolding copy operations with TDD class structure
* `tests/test_init_scaffolds_acceptance.py` - Acceptance test file for init scaffolding feature
* `src/teambot/scaffolds.py` - Complete module for scaffold file management with `get_scaffolds_dir()`, `CopyResult`, `copy_scaffold_file()`, `copy_scaffold_directory()`, and `copy_all_scaffolds()` functions
* `src/teambot/scaffolds/` - Directory containing bundled scaffold files (stages.yaml, AGENTS.md, agents/, .agent/)

### Modified

* `pyproject.toml` - Updated build include pattern to bundle scaffolds directory
* `src/teambot/cli.py` - Integrated scaffold copying into `cmd_init()` function with console output
* `README.md` - Updated Quick Start section with scaffold file documentation

### Removed

## Release Summary

**Total Files Affected**: 7

### Files Created (5)

* `tests/test_scaffolds.py` - Unit tests for scaffold module (19 tests)
* `tests/test_init_scaffolds_acceptance.py` - Acceptance tests for init scaffolding (4 tests)
* `src/teambot/scaffolds.py` - Scaffold file management module
* `src/teambot/scaffolds/` - Bundled scaffold files directory

### Files Modified (3)

* `pyproject.toml` - Added scaffold files to build include pattern
* `src/teambot/cli.py` - Integrated scaffold copying into cmd_init()
* `README.md` - Documented new init behavior and scaffold files

### Files Removed (0)

None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: Scaffold files bundled with package
* **Configuration Updates**: pyproject.toml build includes

### Deployment Notes

No special deployment considerations - standard package update. Scaffold files are included in wheel distribution.
