<!-- markdownlint-disable-file -->
# Task Research Document: Enhanced .env File Loading

This research analyzes the implementation approach for enhancing TeamBot's `.env` file loading to work reliably with `uvx` invocations, subdirectory execution, explicit path specification (`--env-file`), and load disabling (`--no-env`).

## Task Implementation Requests

* **TIR-1**: Create `src/teambot/env_loader.py` module with `load_environment()` function
* **TIR-2**: Implement early argument extraction from `sys.argv` for `--env-file` and `--no-env`
* **TIR-3**: Implement parent directory `.env` traversal with git root / depth limit
* **TIR-4**: Add `--env-file` and `--no-env` arguments to CLI parser (mutually exclusive)
* **TIR-5**: Integrate `load_environment()` call at top of `main()` before `create_parser()`
* **TIR-6**: Write unit tests for `env_loader.py` (TDD approach)
* **TIR-7**: Write integration tests with real temp directories
* **TIR-8**: Write acceptance tests for all 8 AT scenarios

## Scope and Success Criteria

* **Scope**: Enhanced `.env` file loading for CLI invocations including uvx, subdirectories, explicit paths, and CI-friendly disabling
* **Out of Scope**: Multiple `--env-file` args, `.env.local/.env.production` variants, secret encryption

### Success Criteria

* ✅ `.env` files load from cwd regardless of invocation method (uvx, direct, pipx)
* ✅ Parent directory `.env` files merge with cwd (parent provides defaults, cwd overrides)
* ✅ `--env-file PATH` loads only the specified file
* ✅ `--env-file` with non-existent path fails fast with clear error
* ✅ `--no-env` disables all `.env` loading
* ✅ `--env-file` and `--no-env` are mutually exclusive
* ✅ All existing tests pass (62 CLI tests baseline)
* ✅ New functionality has 85%+ unit test coverage

## Outline

1. Entry Point Analysis
2. Current Implementation Analysis
3. python-dotenv API Research
4. Technical Implementation Approach
5. Testing Strategy
6. Key Discoveries

### Potential Next Research

* None - research is complete

## Research Executed

### Testing Infrastructure Research

* **Framework**: pytest 7.4.0+ with pytest-cov, pytest-mock, pytest-asyncio
  * Location: `tests/` directory mirroring `src/` structure
  * Naming: `test_*.py` pattern with class grouping `Test*`
  * Runner: `uv run pytest` (from pyproject.toml)
  * Coverage: coverage.py with 80% target (per pyproject.toml:62)

### Test Patterns Found

* **File**: `tests/test_cli.py` (Lines 1-75)
  * Uses `from teambot.cli import create_parser` for isolated parser tests
  * `argparse.Namespace` for mocking parsed args
  * `monkeypatch.chdir(tmp_path)` for directory isolation
  * `monkeypatch.setattr()` for mocking functions
  * Clear arrange-act-assert structure

* **File**: `tests/test_notification_acceptance.py` (Lines 1-80)
  * Uses `patch.dict(os.environ, {...})` for environment variable mocking
  * Tests real implementation with mocked external services
  * `@pytest.mark.asyncio` for async tests

* **File**: `tests/conftest.py` (Lines 1-185)
  * Shared fixtures: `temp_teambot_dir`, `sample_agent_config`, `sample_objective`
  * Mock SDK patterns for Copilot integration

### Coverage Standards

* **Unit Tests**: 85% minimum (per test patterns observed)
* **Integration Tests**: 70% minimum
* **Critical Paths**: 100% for core env loading logic

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `extract_env_args()` | TDD | Pure function, well-defined inputs/outputs |
| `find_env_files()` | TDD | Pure function with clear edge cases |
| `load_environment()` | TDD | Core logic, needs mocking of `load_dotenv` |
| CLI parser integration | Code-First | Extension of existing patterns |
| Acceptance tests | Code-First | End-to-end validation after unit tests |

**Rationale**: The feature has well-defined requirements with clear acceptance criteria, making TDD appropriate for core functions. Parser integration extends existing patterns, so Code-First is efficient.

---

## Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `teambot init` | `main()` → `load_dotenv()` → `cmd_init()` | YES ✅ | YES - wrap `load_dotenv()` call |
| `teambot run obj.md` | `main()` → `load_dotenv()` → `cmd_run()` | YES ✅ | YES - wrap `load_dotenv()` call |
| `teambot status` | `main()` → `load_dotenv()` → `cmd_status()` | YES ✅ | YES - wrap `load_dotenv()` call |
| `uvx teambot run` | Same as above (invokes `main()`) | YES ✅ | YES - same integration point |

### Code Path Trace

#### Entry Point: `teambot run obj.md`

1. User executes: `teambot run obj.md`
2. Entry via: `cli.py:main()` (Line 1286)
3. Current: `load_dotenv()` called at Line 1289 **without parameters**
4. Then: `parser = create_parser()` at Line 1291
5. Then: `args = parser.parse_args()` at Line 1292
6. Routes to: `cmd_run(args, display)` at Line 1304

**Problem**: `.env` loading happens **before** argument parsing, so `--env-file` and `--no-env` cannot influence loading with current design.

**Solution**: Extract `--env-file` and `--no-env` from `sys.argv` before `load_dotenv()` call.

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| No early arg extraction | `--env-file` / `--no-env` cannot affect loading | Extract from `sys.argv` manually |
| Single `load_dotenv()` call | No merge behavior, no explicit path | Replace with `load_environment()` |
| No parent traversal | Parent `.env` files ignored | Implement `find_env_files()` |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced (init, run, status, uvx)
- [x] All code paths that should trigger feature are identified (single `main()` entry)
- [x] Coverage gaps are documented with required fixes

---

## Current Implementation Analysis

### File: `src/teambot/cli.py` (Lines 1286-1313)

```python
def main() -> int:
    """Main CLI entry point."""
    # Load environment variables from .env file if it exists
    load_dotenv()  # ← Line 1289: No parameters, uses find_dotenv() default

    parser = create_parser()
    args = parser.parse_args()

    setup_logging(getattr(args, "verbose", False))
    # ... command dispatch
```

**Key Observations**:
1. `load_dotenv()` is called with **no parameters** (Line 1289)
2. Default behavior uses `find_dotenv()` which searches from the **module location**, not cwd
3. This is why `uvx` invocations fail - the module is installed in a different location
4. No mechanism to disable loading or specify explicit path

### Import Statement (Line 14)

```python
from dotenv import load_dotenv
```

### Global Arguments (Lines 527-529)

```python
parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
parser.add_argument("--no-animation", action="store_true", help="Disable startup animation")
```

Pattern for adding global arguments is clear. Need to add `--env-file` and `--no-env` here.

---

## python-dotenv API Research

### `load_dotenv()` Function (from `dotenv.main`)

```python
load_dotenv(
    dotenv_path: Union[str, 'os.PathLike[str]', None] = None,
    stream: Optional[IO[str]] = None,
    verbose: bool = False,
    override: bool = False,  # ← Key for merge behavior
    interpolate: bool = True,
    encoding: Optional[str] = 'utf-8'
) -> bool
```

**Key Parameters**:
- `dotenv_path`: Explicit path to `.env` file (if `None`, uses `find_dotenv()`)
- `override`: If `False`, existing env vars are NOT overwritten
- Returns `True` if at least one env var was set

### `find_dotenv()` Function

```python
find_dotenv(
    filename: str = '.env',
    raise_error_if_not_found: bool = False,
    usecwd: bool = False  # ← Key for uvx fix!
) -> str
```

**Critical Discovery** 🔍:
- `usecwd=False` (default): Searches from **caller's file location** (module install dir for uvx)
- `usecwd=True`: Searches from **current working directory** ← This fixes the uvx issue!

### Merge Behavior Implementation

```python
# 1. Load parent files first with override=False (sets defaults)
for parent_env in reversed(parent_env_files):
    load_dotenv(parent_env, override=False)

# 2. Load cwd file with override=True (wins conflicts)
if cwd_env.exists():
    load_dotenv(cwd_env, override=True)
```

---

## Technical Implementation Approach

### 1. New Module: `src/teambot/env_loader.py`

```python
"""Environment file loading utilities."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

from dotenv import load_dotenv


class EnvArgs(NamedTuple):
    """Parsed environment-related CLI arguments."""
    env_file: Path | None
    no_env: bool


def extract_env_args(argv: list[str] | None = None) -> tuple[EnvArgs, list[str]]:
    """Extract --env-file and --no-env from argv before argparse runs.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv)
    
    Returns:
        Tuple of (EnvArgs, cleaned_argv with env args removed)
    """
    if argv is None:
        argv = sys.argv
    
    env_file: Path | None = None
    no_env = False
    cleaned = []
    
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == '--env-file':
            if i + 1 < len(argv):
                env_file = Path(argv[i + 1])
                i += 2
                continue
        elif arg.startswith('--env-file='):
            env_file = Path(arg.split('=', 1)[1])
            i += 1
            continue
        elif arg == '--no-env':
            no_env = True
            i += 1
            continue
        cleaned.append(arg)
        i += 1
    
    return EnvArgs(env_file, no_env), cleaned


def find_git_root() -> Path | None:
    """Find the git repository root, or None if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def find_env_files(start_dir: Path | None = None, max_depth: int = 10) -> list[Path]:
    """Find .env files from start_dir up to git root or max_depth.
    
    Args:
        start_dir: Starting directory (defaults to cwd)
        max_depth: Maximum parent directories to traverse
    
    Returns:
        List of .env file paths, ordered from nearest (cwd) to farthest (parent)
    """
    if start_dir is None:
        start_dir = Path.cwd()
    
    start_dir = start_dir.resolve()
    git_root = find_git_root()
    
    env_files = []
    current = start_dir
    depth = 0
    
    while depth < max_depth:
        env_file = current / ".env"
        if env_file.is_file():
            env_files.append(env_file)
        
        # Stop at git root
        if git_root and current == git_root:
            break
        
        # Stop at filesystem root
        parent = current.parent
        if parent == current:
            break
        
        current = parent
        depth += 1
    
    return env_files


def load_environment(
    env_file: Path | None = None,
    no_env: bool = False,
    verbose: bool = False,
) -> list[Path]:
    """Load environment variables from .env files.
    
    Precedence:
    1. no_env=True → No files loaded
    2. env_file specified → Only that file loaded
    3. Default → cwd .env + parent .env files (merged)
    
    Args:
        env_file: Explicit path to load (disables auto-discovery)
        no_env: If True, skip all loading
        verbose: If True, log loaded files
    
    Returns:
        List of loaded .env file paths
    
    Raises:
        FileNotFoundError: If env_file is specified but doesn't exist
    """
    if no_env:
        return []
    
    if env_file is not None:
        if not env_file.exists():
            raise FileNotFoundError(f"Environment file not found: {env_file}")
        load_dotenv(env_file, override=True)
        return [env_file]
    
    # Default: auto-discovery with merge behavior
    env_files = find_env_files()
    
    if not env_files:
        return []
    
    # Load in reverse order: farthest parent first (provides defaults)
    # Then closer files override with override=True
    loaded = []
    for i, ef in enumerate(reversed(env_files)):
        # First file (farthest parent) can override nothing
        # Subsequent files override previous values
        is_first = i == 0
        load_dotenv(ef, override=not is_first)
        loaded.append(ef)
    
    return list(reversed(loaded))  # Return in cwd-to-parent order
```

### 2. CLI Integration: `src/teambot/cli.py`

```python
# At top of file, add import
from teambot.env_loader import EnvArgs, extract_env_args, load_environment

# In create_parser(), add mutually exclusive group after line 529
env_group = parser.add_mutually_exclusive_group()
env_group.add_argument(
    "--env-file",
    type=Path,
    metavar="PATH",
    help="Load environment from specific .env file (disables auto-discovery)",
)
env_group.add_argument(
    "--no-env",
    action="store_true",
    help="Disable all .env file loading",
)

# Replace main() function (starting at line 1286)
def main() -> int:
    """Main CLI entry point."""
    # Extract env args BEFORE argparse (they affect env loading)
    env_args, sys.argv = extract_env_args()
    
    # Validate mutual exclusivity
    if env_args.env_file and env_args.no_env:
        sys.stderr.write("Error: --env-file and --no-env are mutually exclusive\n")
        return 2
    
    # Load environment variables
    try:
        load_environment(env_args.env_file, env_args.no_env)
    except FileNotFoundError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1
    
    parser = create_parser()
    args = parser.parse_args()
    # ... rest unchanged
```

### 3. Architecture Diagram

```mermaid
flowchart TD
    A[User: teambot --env-file .env run obj.md] --> B[main()]
    B --> C[extract_env_args]
    C --> D{env_args.no_env?}
    D -->|Yes| E[Skip loading]
    D -->|No| F{env_args.env_file?}
    F -->|Yes| G[Load explicit file only]
    F -->|No| H[find_env_files]
    H --> I[Load with merge behavior]
    G --> J[create_parser]
    I --> J
    E --> J
    J --> K[parse_args]
    K --> L[Command dispatch]
```

---

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `src/teambot/env_loader.py` | **NEW** | Core env loading module (~120 lines) |
| `src/teambot/cli.py` | MODIFY | Import env_loader, add args, update `main()` |
| `tests/test_env_loader.py` | **NEW** | Unit tests for env_loader module |
| `tests/test_env_loading_acceptance.py` | **NEW** | Acceptance tests (AT-001 through AT-008) |

---

## Key Discoveries

### 1. Root Cause of uvx Failure

`find_dotenv()` default behavior (`usecwd=False`) searches from the module file location, not the current working directory. When installed via `uvx`, the module is in a virtual environment, so `.env` files in the project directory are never found.

**Fix**: Use explicit `Path.cwd() / ".env"` path instead of relying on `find_dotenv()`.

### 2. Existing Git Root Detection Pattern

The codebase already has git root detection in two places:
- `src/teambot/worktree/manager.py:140-153` - `get_repo_root()` static method
- `src/teambot/orchestration/review_iterator.py:58-73` - `_find_repo_root()` method

Both use the same pattern:
```python
result = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True,
    text=True,
    timeout=5,
)
```

**Decision**: Implement similar function in `env_loader.py` rather than importing to avoid circular dependencies.

### 3. Early Argument Extraction is Required

The spec requires `.env` loading before config parsing (FR-008). Since env vars may be referenced in `teambot.json` via `${VAR}` syntax, loading must happen before `parse_args()`. This necessitates manual `sys.argv` extraction.

### 4. Environment Variable Usage in Codebase

Found 18 `os.environ` usages across the codebase:
- `TEAMBOT_TELEGRAM_TOKEN` / `TEAMBOT_TELEGRAM_CHAT_ID` - Notifications
- `TEAMBOT_NO_ANIMATION` - Animation control
- `TEAMBOT_LEGACY_MODE` - Legacy UI mode
- `TEAMBOT_SPLIT_PANE` - Split pane mode
- `TEAMBOT_STREAMING` - Streaming mode
- `TEAMBOT_MODEL_CACHE_TTL` - Model cache TTL
- `TEAMBOT_ASCII_INDENT` - ASCII indent mode

All of these are read **after** `main()` starts, so the enhanced `.env` loading will correctly provide values for all of them.

### 5. Test Patterns for Environment Mocking

From `tests/test_notification_acceptance.py` (Lines 67-74):
```python
with (
    patch.dict(
        os.environ,
        {
            "TEAMBOT_TELEGRAM_TOKEN": "test-token-123",
            "TEAMBOT_TELEGRAM_CHAT_ID": "12345678",
        },
    ),
    # ... other mocks
):
```

This pattern should be used for testing environment variable loading.

---

## Complete Test Strategy

### Unit Tests (`tests/test_env_loader.py`)

| Test | Description |
|------|-------------|
| `test_extract_env_args_no_args` | Returns (None, False) with no env args |
| `test_extract_env_args_env_file` | Extracts `--env-file /path/.env` |
| `test_extract_env_args_env_file_equals` | Extracts `--env-file=/path/.env` |
| `test_extract_env_args_no_env` | Extracts `--no-env` flag |
| `test_extract_env_args_both` | Extracts both (for validation later) |
| `test_extract_env_args_preserves_other_args` | Other args unchanged in cleaned argv |
| `test_find_env_files_cwd_only` | Finds `.env` in cwd |
| `test_find_env_files_parent` | Finds `.env` in parent directories |
| `test_find_env_files_stops_at_git_root` | Stops traversal at git root |
| `test_find_env_files_max_depth` | Respects max_depth limit |
| `test_find_env_files_no_env_files` | Returns empty list when none found |
| `test_load_environment_no_env_skips_loading` | `no_env=True` loads nothing |
| `test_load_environment_explicit_file` | `env_file` loads only that file |
| `test_load_environment_explicit_file_not_found` | Raises FileNotFoundError |
| `test_load_environment_default_cwd` | Default loads from cwd |
| `test_load_environment_merge_parent` | Parent vars available, cwd overrides |

### Acceptance Tests (`tests/test_env_loading_acceptance.py`)

| ID | Test | Status |
|----|------|--------|
| AT-001 | Default CWD loading | Ready for implementation |
| AT-002 | Parent directory merge | Ready for implementation |
| AT-003 | Explicit --env-file path | Ready for implementation |
| AT-004 | --env-file missing file error | Ready for implementation |
| AT-005 | --no-env disables loading | Ready for implementation |
| AT-006 | Mutual exclusivity error | Ready for implementation |
| AT-007 | All commands support flags | Ready for implementation |
| AT-008 | uvx invocation loads cwd .env | Ready for implementation (manual) |

---

## Implementation Order (TDD)

1. **Write tests first** for `extract_env_args()` - pure function, easy to test
2. **Implement** `extract_env_args()` - make tests pass
3. **Write tests** for `find_env_files()` - mock subprocess for git root
4. **Implement** `find_env_files()` - make tests pass
5. **Write tests** for `load_environment()` - mock `load_dotenv`
6. **Implement** `load_environment()` - make tests pass
7. **Add CLI arguments** - extend `create_parser()` with mutually exclusive group
8. **Update `main()`** - integrate env loading
9. **Write acceptance tests** - validate end-to-end behavior
10. **Run full test suite** - ensure no regressions

---

## Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking existing behavior | High | Default behavior (no args) must match current `load_dotenv()` behavior |
| Arg extraction edge cases | Medium | Comprehensive unit tests for all arg formats |
| Git root detection fails | Low | Fallback to max_depth limit (10 directories) |
| Performance impact | Low | Git root detection is fast (<50ms); cache if needed |

---

## References

| Ref | Source | Summary |
|-----|--------|---------|
| Feature Spec | `.teambot/enhanced-env-file/artifacts/feature_spec.md` | Complete requirements and acceptance criteria |
| Current Implementation | `src/teambot/cli.py:1286-1313` | Existing `main()` and `load_dotenv()` call |
| python-dotenv API | `help(load_dotenv)` | Parameter documentation for explicit paths and override |
| Git Root Pattern | `src/teambot/worktree/manager.py:140-153` | Existing git root detection implementation |
| Test Patterns | `tests/test_cli.py`, `tests/conftest.py` | Existing pytest patterns and fixtures |

---

Generated 2026-02-24T23:17:00Z by Builder-1 (mode: research)
