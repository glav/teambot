<!-- markdownlint-disable-file -->
# Test Strategy: Enhanced .env File Loading

**Strategy Date**: 2026-02-24
**Feature Specification**: .teambot/enhanced-env-file/artifacts/feature_spec.md
**Research Reference**: N/A (leveraging existing codebase patterns and python-dotenv documentation)
**Strategist**: Test Strategy Agent

## Recommended Testing Approach

**Primary Approach**: TDD (Test-Driven Development)

### Rationale

This feature modifies critical CLI startup flow where `.env` files must be loaded before any configuration parsing. The requirements are exceptionally well-defined with 8 explicit acceptance test scenarios (AT-001 through AT-008), making TDD the optimal approach. Key factors supporting TDD:

1. **Requirements are crystal clear**: The specification includes precise acceptance criteria with specific expected behaviors, error messages, and exit codes
2. **High risk of regression**: Changes to `main()` flow affect all CLI invocations - tests must capture current behavior before modifications
3. **Critical timing requirements**: `.env` loading must occur before argparse; early arg extraction logic needs thorough testing

**Key Factors:**
* Complexity: MEDIUM (argument parsing timing, parent traversal logic)
* Risk: HIGH (affects all CLI users and startup behavior)
* Requirements Clarity: CLEAR (8 detailed acceptance scenarios with Given/When/Then format)
* Time Pressure: LOW (quality and backward compatibility are priority)

## Testing Approach Decision Matrix

### Factor Scoring (Score each factor 0-3)

| Factor | Question | Assessment | TDD Points | Code-First Points |
|--------|----------|------------|------------|-------------------|
| **Requirements Clarity** | Are requirements well-defined with clear acceptance criteria? | YES - 8 AT scenarios with precise criteria | 3 | 0 |
| **Complexity** | Is the feature algorithm-heavy or has complex business logic? | MEDIUM - parent traversal algorithm, arg extraction timing | 2 | 0 |
| **Risk Level** | Is this mission-critical or high-impact if it fails? | HIGH - affects all CLI startup; breaking change would impact all users | 3 | 0 |
| **Exploratory Nature** | Is this a proof-of-concept or experimental work? | NO - well-defined feature with clear requirements | 0 | 0 |
| **Simplicity** | Is this straightforward CRUD or simple logic? | NO - conditional logic with multiple paths and precedence rules | 0 | 0 |
| **Time Pressure** | Is rapid iteration more important than comprehensive testing? | NO - backward compatibility is critical | 0 | 0 |
| **Requirements Stability** | Are requirements likely to change during development? | STABLE - spec approved with detailed acceptance criteria | 0 | 0 |

### Score Summary

| Score Type | Points |
|------------|--------|
| **TDD Score** | **8** |
| **Code-First Score** | **0** |

### Decision Thresholds

| TDD Score | Code-First Score | Recommendation |
|-----------|------------------|----------------|
| ≥ 6 | < 4 | **TDD** |

**Decision**: TDD (score 8 >> threshold 6)

## Feature Analysis Summary

### Complexity Assessment
* **Algorithm Complexity**: MEDIUM - Parent directory traversal with git root detection and depth limiting
* **Integration Depth**: HIGH - Must integrate with argparse timing and existing `main()` flow
* **State Management**: LOW - Stateless loading; environment variables are process-global
* **Error Scenarios**: MEDIUM - Missing file validation, mutual exclusivity enforcement, traversal limits

### Risk Profile
* **Business Criticality**: HIGH - Credential loading affects notifications, API access
* **User Impact**: HIGH - All users rely on `.env` loading; uvx users currently broken
* **Data Sensitivity**: HIGH - `.env` files contain API tokens and secrets
* **Failure Cost**: MEDIUM - Silent credential failures cause confusing downstream errors

### Requirements Clarity
* **Specification Completeness**: COMPLETE - 9 functional requirements with acceptance criteria
* **Acceptance Criteria Quality**: PRECISE - 8 detailed AT scenarios in Given/When/Then format
* **Edge Cases Identified**: 6 documented (mutual exclusivity, missing file, parent traversal limits, uvx invocation)
* **Dependencies Status**: STABLE - python-dotenv already in pyproject.toml; argparse is stdlib

## Test Strategy by Component

### Component 1: Early Argument Extraction - TDD

**Approach**: TDD
**Rationale**: Argument extraction must occur before argparse runs to influence `.env` loading. This timing-sensitive logic requires precise testing to ensure it handles all valid arg combinations.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Extract `--env-file /path` from sys.argv
  * Extract `--no-env` flag from sys.argv
  * Handle args appearing before command (`teambot --no-env init`)
  * Handle args with `=` syntax (`--env-file=/path`)
  * Detect mutual exclusivity and raise appropriate error
* Edge Cases:
  * `--env-file` without value (argparse-like error)
  * `--env-file` at end of argv without value
  * Both `--env-file` and `--no-env` present (mutual exclusivity)

**Testing Sequence (TDD)**:
1. Write test for extracting `--env-file path` returning Path object
2. Write test for extracting `--no-env` returning True
3. Write test for mutual exclusivity error
4. Write test for missing value after `--env-file`
5. Implement `extract_env_args(argv: list[str]) -> tuple[Path | None, bool]`
6. Refactor for clarity

### Component 2: Parent Directory Traversal - TDD

**Approach**: TDD
**Rationale**: Traversal logic must correctly walk up directory tree, stop at git root, and respect depth limit. This algorithm has clear testable behaviors.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit
* Critical Scenarios:
  * Find `.env` in current directory
  * Find `.env` in parent directory when not in cwd
  * Stop at git root (`.git` directory present)
  * Stop after 10 levels even without git root
  * Return files in correct order (parent first, cwd last for proper override)
* Edge Cases:
  * No `.env` files found at any level
  * Deeply nested directory (>10 levels)
  * Git root at filesystem root
  * Symlinked directories

**Testing Sequence (TDD)**:
1. Write test for `find_env_files(Path)` returning empty list when no `.env` exists
2. Write test for finding `.env` in cwd only
3. Write test for finding `.env` in parent when cwd has none
4. Write test for returning [parent, cwd] when both exist
5. Write test for stopping at git root
6. Write test for stopping after 10 levels
7. Implement `find_env_files(start_dir: Path, limit: int = 10) -> list[Path]`

### Component 3: Environment Loading Logic - TDD

**Approach**: TDD
**Rationale**: Core loading function orchestrates all behaviors and must handle all precedence rules correctly.

**Test Requirements:**
* Coverage Target: 95%
* Test Types: Unit (with mocked load_dotenv), Integration (with real temp files)
* Critical Scenarios:
  * `--no-env` prevents any loading
  * `--env-file path` loads only specified file
  * `--env-file /nonexistent` raises FileNotFoundError with clear message
  * Default behavior loads cwd + parents with correct override order
  * Variables from cwd override parent (cwd precedence)
* Edge Cases:
  * Empty `.env` file
  * `.env` file with syntax errors (python-dotenv handles gracefully)
  * Unicode content in `.env` file

**Testing Sequence (TDD)**:
1. Write test for `load_environment(no_env=True)` calling nothing
2. Write test for `load_environment(env_file=Path)` calling load_dotenv with explicit path
3. Write test for `load_environment(env_file=Path("/missing"))` raising FileNotFoundError
4. Write test for default behavior calling `find_env_files()` and loading in order
5. Write test for proper override behavior (cwd wins conflicts)
6. Implement `load_environment(env_file: Path | None, no_env: bool) -> None`

### Component 4: CLI Integration - TDD

**Approach**: TDD
**Rationale**: Integration into `main()` must preserve backward compatibility and work with all commands.

**Test Requirements:**
* Coverage Target: 90%
* Test Types: Integration
* Critical Scenarios:
  * `teambot --no-env init` works correctly
  * `teambot --env-file .env run obj.md` works correctly
  * `teambot --env-file nonexistent status` exits with code 1
  * `teambot --env-file x --no-env init` exits with code 2 (argparse mutual exclusivity)
  * Default `teambot run obj.md` loads cwd `.env` (backward compatible)
* Edge Cases:
  * `--env-file` arg appears after command (should still work as global arg)
  * Help flag combined with env args

**Testing Sequence (TDD)**:
1. Write test for parser accepting `--env-file` and `--no-env` as global args
2. Write test for mutual exclusivity enforcement by argparse
3. Write test for `main()` calling `load_environment()` before `create_parser()`
4. Write integration test validating environment variable availability
5. Refactor and integrate into `cli.py`

### Component 5: Acceptance Tests - TDD

**Approach**: TDD (write first, validate implementation)
**Rationale**: Spec provides 8 detailed acceptance scenarios that should be converted to pytest tests before implementation.

**Test Requirements:**
* Coverage Target: 100% of acceptance scenarios
* Test Types: Acceptance (marked with `@pytest.mark.acceptance`)
* Critical Scenarios:
  * AT-001: Default CWD loading
  * AT-002: Parent directory merge
  * AT-003: Explicit `--env-file` path
  * AT-004: `--env-file` missing file error
  * AT-005: `--no-env` disables loading
  * AT-006: Mutual exclusivity error
  * AT-007: All commands support flags
  * AT-008: uvx invocation loads CWD `.env`
* Edge Cases:
  * Real filesystem with temp directories
  * Environment isolation between tests

## Test Infrastructure

### Existing Test Framework
* **Framework**: pytest
* **Version**: (from pyproject.toml)
* **Configuration**: `pyproject.toml` [tool.pytest.ini_options]
* **Runner**: `uv run pytest`

### Testing Tools Required
* **Mocking**: `unittest.mock` (patch, MagicMock) - for mocking `load_dotenv`, `sys.argv`
* **Assertions**: pytest native assertions
* **Coverage**: pytest-cov - Target: 85%+ overall, 95% for core modules
* **Test Data**: Temporary directories with real `.env` files (pytest `tmp_path` fixture)
* **Fixtures**: Shared fixtures in `tests/conftest.py`

### Test Organization
* **Unit Tests Location**: `tests/test_env_loader.py` (new module)
* **Integration Tests Location**: `tests/test_cli.py` (extend existing)
* **Acceptance Tests Location**: `tests/test_env_loading_acceptance.py` (new file)
* **Naming Convention**: `test_<scenario>` for functions, `Test<Component>` for classes
* **Fixture Strategy**: Use `tmp_path` for filesystem tests; `monkeypatch` for env vars
* **Setup/Teardown**: Use pytest fixtures for temp directories and env cleanup

## Coverage Requirements

### Overall Targets
* **Unit Test Coverage**: 95% (for new `env_loader.py` module)
* **Integration Coverage**: 90% (for CLI integration points)
* **Critical Path Coverage**: 100% (all 8 acceptance scenarios)
* **Error Path Coverage**: 95% (all error conditions defined in spec)

### Component-Specific Targets

| Component | Unit % | Integration % | Priority | Notes |
|-----------|--------|---------------|----------|-------|
| `extract_env_args()` | 95% | N/A | CRITICAL | Arg parsing before argparse |
| `find_env_files()` | 95% | 90% | HIGH | Parent traversal logic |
| `load_environment()` | 95% | 90% | CRITICAL | Core loading orchestration |
| `main()` integration | N/A | 90% | CRITICAL | Backward compatibility |
| CLI parser updates | 90% | 95% | HIGH | Global arg support |

### Critical Test Scenarios

Priority test scenarios that MUST be covered:

1. **Backward Compatibility** (Priority: CRITICAL)
   * **Description**: Existing behavior without new args must be preserved
   * **Test Type**: Integration
   * **Success Criteria**: `teambot run obj.md` loads cwd `.env` exactly as before
   * **Test Approach**: TDD - write regression test first

2. **--env-file Explicit Loading** (Priority: CRITICAL)
   * **Description**: Explicit path loads only that file, ignores auto-discovery
   * **Test Type**: Unit + Integration
   * **Success Criteria**: Only specified file loaded; cwd `.env` ignored
   * **Test Approach**: TDD

3. **--env-file Missing File Error** (Priority: CRITICAL)
   * **Description**: Clear error when explicit path doesn't exist
   * **Test Type**: Unit + Integration
   * **Success Criteria**: Exit code 1, message contains path
   * **Test Approach**: TDD

4. **--no-env Disables All Loading** (Priority: CRITICAL)
   * **Description**: No `.env` files loaded when flag present
   * **Test Type**: Unit + Integration
   * **Success Criteria**: Environment unmodified by `.env` files
   * **Test Approach**: TDD

5. **Mutual Exclusivity** (Priority: HIGH)
   * **Description**: `--env-file` and `--no-env` cannot both be used
   * **Test Type**: Unit
   * **Success Criteria**: argparse error with "mutually exclusive" message
   * **Test Approach**: TDD

6. **Parent Directory Merge** (Priority: HIGH)
   * **Description**: Parent `.env` provides defaults; cwd overrides
   * **Test Type**: Integration
   * **Success Criteria**: Parent-only vars present; conflict vars use cwd value
   * **Test Approach**: TDD

### Edge Cases to Cover

* **Empty `.env` file**: Should be handled gracefully (no errors, no vars loaded)
* **`.env` at filesystem root**: Traversal should handle edge boundary correctly
* **Symlinked `.env`**: Should follow symlinks correctly
* **Read permission denied**: Should raise appropriate error
* **Concurrent `.env` modification**: Not a concern (single-threaded startup)

### Error Scenarios

* **FileNotFoundError for `--env-file`**: "Error: Environment file not found: /path"
* **Mutual exclusivity error**: argparse standard error format with "mutually exclusive"
* **Permission denied**: Standard OS error propagation with context

## Test Data Strategy

### Test Data Requirements
* `.env` files with known KEY=value pairs for validation
* Parent/child directory structures with multiple `.env` files
* Git repository structures (for git root detection)

### Test Data Management
* **Storage**: Created dynamically via `tmp_path` fixture
* **Generation**: Programmatic creation in test setup
* **Isolation**: Each test gets fresh `tmp_path` directory
* **Cleanup**: Automatic via pytest `tmp_path` lifecycle

### Example Test Data

```python
# tests/test_env_loader.py
def test_parent_merge(tmp_path):
    """Parent .env provides defaults, cwd overrides conflicts."""
    parent = tmp_path
    child = tmp_path / "subdir"
    child.mkdir()
    
    (parent / ".env").write_text("PARENT_VAR=parent\nSHARED=parent\n")
    (child / ".env").write_text("CHILD_VAR=child\nSHARED=child\n")
    
    # ... test logic
```

## Example Test Patterns

### Example from Codebase

**File**: `tests/test_cli.py`
**Pattern**: CLI command testing with monkeypatch

```python
class TestCLIParser:
    """Tests for CLI argument parsing."""

    def test_parser_verbose_flag(self):
        """Parser recognizes verbose flag."""
        from teambot.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["-v", "init"])

        assert args.verbose is True
```

**Key Conventions:**
* Class-based test organization (`Test<Component>`)
* Docstrings explain what is being tested
* Use `monkeypatch` for environment and cwd changes
* Import modules inside test functions (lazy loading pattern used in some tests)

### Recommended Test Structure for New Module

```python
# tests/test_env_loader.py
"""Unit tests for env_loader module."""

import os
from pathlib import Path
from unittest.mock import patch, call

import pytest


class TestExtractEnvArgs:
    """Tests for early argument extraction from sys.argv."""

    def test_extract_env_file_with_path(self):
        """--env-file path is extracted correctly."""
        from teambot.env_loader import extract_env_args
        
        env_file, no_env = extract_env_args(["teambot", "--env-file", ".env", "run"])
        
        assert env_file == Path(".env")
        assert no_env is False

    def test_extract_no_env_flag(self):
        """--no-env flag is extracted correctly."""
        from teambot.env_loader import extract_env_args
        
        env_file, no_env = extract_env_args(["teambot", "--no-env", "init"])
        
        assert env_file is None
        assert no_env is True

    def test_mutual_exclusivity_raises(self):
        """Both --env-file and --no-env raises error."""
        from teambot.env_loader import extract_env_args, EnvArgsError
        
        with pytest.raises(EnvArgsError, match="mutually exclusive"):
            extract_env_args(["teambot", "--env-file", ".env", "--no-env", "run"])


class TestFindEnvFiles:
    """Tests for parent directory traversal."""

    def test_no_env_files_returns_empty(self, tmp_path, monkeypatch):
        """Returns empty list when no .env files exist."""
        from teambot.env_loader import find_env_files
        
        result = find_env_files(tmp_path)
        
        assert result == []

    def test_finds_cwd_env_file(self, tmp_path):
        """Finds .env in current directory."""
        from teambot.env_loader import find_env_files
        
        (tmp_path / ".env").write_text("TEST=value")
        
        result = find_env_files(tmp_path)
        
        assert result == [tmp_path / ".env"]

    def test_finds_parent_and_cwd(self, tmp_path):
        """Returns [parent, cwd] when both have .env files."""
        from teambot.env_loader import find_env_files
        
        child = tmp_path / "subdir"
        child.mkdir()
        (tmp_path / ".env").write_text("PARENT=1")
        (child / ".env").write_text("CHILD=1")
        
        result = find_env_files(child)
        
        assert result == [tmp_path / ".env", child / ".env"]


class TestLoadEnvironment:
    """Tests for main environment loading function."""

    def test_no_env_skips_loading(self):
        """--no-env prevents all .env loading."""
        from teambot.env_loader import load_environment
        
        with patch("teambot.env_loader.load_dotenv") as mock_load:
            load_environment(env_file=None, no_env=True)
        
        mock_load.assert_not_called()

    def test_env_file_loads_explicit_path(self, tmp_path):
        """--env-file loads only the specified file."""
        from teambot.env_loader import load_environment
        
        env_path = tmp_path / "custom.env"
        env_path.write_text("CUSTOM=yes")
        
        with patch("teambot.env_loader.load_dotenv") as mock_load:
            load_environment(env_file=env_path, no_env=False)
        
        mock_load.assert_called_once_with(env_path)

    def test_env_file_missing_raises(self, tmp_path):
        """--env-file with missing path raises FileNotFoundError."""
        from teambot.env_loader import load_environment
        
        missing = tmp_path / "nonexistent.env"
        
        with pytest.raises(FileNotFoundError, match="Environment file not found"):
            load_environment(env_file=missing, no_env=False)
```

### Acceptance Test Pattern

```python
# tests/test_env_loading_acceptance.py
"""Acceptance tests for enhanced .env file loading feature.

Core logic is tested directly; selective mocking is used for external dependencies.
"""

import argparse
import os

import pytest


@pytest.mark.acceptance
class TestEnvLoadingAcceptance:
    """Acceptance test scenarios from feature specification."""

    def test_at_001_default_cwd_loading(self, tmp_path, monkeypatch):
        """AT-001: .env loads from current working directory by default."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("TEST_VAR=hello")
        
        # Clear any existing value
        monkeypatch.delenv("TEST_VAR", raising=False)
        
        from teambot.env_loader import load_environment
        load_environment(env_file=None, no_env=False)
        
        assert os.environ.get("TEST_VAR") == "hello"

    def test_at_002_parent_directory_merge(self, tmp_path, monkeypatch):
        """AT-002: Parent .env provides defaults, child overrides conflicts."""
        child = tmp_path / "child"
        child.mkdir()
        monkeypatch.chdir(child)
        
        (tmp_path / ".env").write_text("PARENT_VAR=parent\nSHARED_VAR=parent")
        (child / ".env").write_text("CHILD_VAR=child\nSHARED_VAR=child")
        
        # Clear any existing values
        for var in ["PARENT_VAR", "CHILD_VAR", "SHARED_VAR"]:
            monkeypatch.delenv(var, raising=False)
        
        from teambot.env_loader import load_environment
        load_environment(env_file=None, no_env=False)
        
        assert os.environ.get("PARENT_VAR") == "parent"
        assert os.environ.get("CHILD_VAR") == "child"
        assert os.environ.get("SHARED_VAR") == "child"  # child wins

    def test_at_005_no_env_disables_loading(self, tmp_path, monkeypatch):
        """AT-005: --no-env prevents all .env loading."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("SHOULD_NOT_LOAD=yes")
        
        # Clear any existing value
        monkeypatch.delenv("SHOULD_NOT_LOAD", raising=False)
        
        from teambot.env_loader import load_environment
        load_environment(env_file=None, no_env=True)
        
        assert os.environ.get("SHOULD_NOT_LOAD") is None
```

## Success Criteria

### Test Implementation Complete When:
* [x] All 8 acceptance scenarios have tests (AT-001 through AT-008)
* [ ] Unit tests for `extract_env_args()` at 95% coverage
* [ ] Unit tests for `find_env_files()` at 95% coverage
* [ ] Unit tests for `load_environment()` at 95% coverage
* [ ] Integration tests for CLI parser updates
* [ ] Integration tests for `main()` flow changes
* [ ] Backward compatibility regression tests passing
* [ ] All tests follow codebase conventions (class-based, docstrings)
* [ ] CI/CD runs tests with `uv run pytest`

### Test Quality Indicators:
* Tests are readable and self-documenting (clear docstrings)
* Tests are fast and reliable (no flakiness from filesystem timing)
* Tests are independent (each test uses fresh `tmp_path`)
* Failures clearly indicate the problem (specific assertions)
* Mock/stub usage is appropriate and minimal (mock `load_dotenv`, real filesystem)

## Implementation Guidance

### For All Components (TDD):
1. Write failing test for simplest case
2. Implement minimal code to pass
3. Write test for next case (error handling, edge case)
4. Implement and refactor
5. Continue until all acceptance criteria covered
6. Run full test suite to verify no regressions

### Test Execution Order:
1. **Unit tests first**: `test_env_loader.py` for the new module
2. **Integration tests second**: CLI parser and main() integration
3. **Acceptance tests last**: End-to-end validation with real filesystem

### Module Structure Suggestion:
```
src/teambot/
├── env_loader.py  # NEW: All env loading logic
└── cli.py         # MODIFIED: Import and call env_loader

tests/
├── test_env_loader.py          # NEW: Unit tests for env_loader
├── test_cli.py                 # EXTENDED: Parser tests for new args
└── test_env_loading_acceptance.py  # NEW: Acceptance tests
```

## Considerations and Trade-offs

### Selected Approach Benefits:
* TDD ensures all acceptance criteria are testable before implementation
* High coverage target (95%) matches risk level of startup flow changes
* Real filesystem tests validate actual python-dotenv behavior
* Backward compatibility tests prevent regression

### Accepted Trade-offs:
* Tests with real filesystem are slower than pure mocks
* Some tests require git repo setup for traversal limit testing
* AT-008 (uvx invocation) may need manual verification in addition to automated test

### Risk Mitigation:
* Backward compatibility test written first to catch any regression
* Environment variable cleanup in fixtures prevents test pollution
* `tmp_path` isolation ensures tests don't affect real `.env` files

## References

* **Feature Spec**: [.teambot/enhanced-env-file/artifacts/feature_spec.md](./feature_spec.md)
* **Spec Review**: [.teambot/enhanced-env-file/artifacts/spec_review.md](./spec_review.md)
* **Test Examples**: tests/test_cli.py, tests/test_init_scaffolds_acceptance.py
* **Test Config**: pyproject.toml [tool.pytest.ini_options]
* **python-dotenv docs**: https://pypi.org/project/python-dotenv/

## Next Steps

1. ✅ Test strategy approved and documented
2. ➡️ Proceed to **Step 5**: Task Planning (`sdd.5-task-planner-for-feature.prompt.md`)
3. 📋 Task planner will incorporate this strategy into implementation phases
4. 🔍 Implementation will follow TDD approach: tests first for each component

---

**Strategy Status**: APPROVED
**Approved By**: PENDING
**Ready for Planning**: YES
