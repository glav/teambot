<!-- markdownlint-disable-file -->

# Implementation Details: GitHub Copilot SDK Upgrade (0.1.16 → 0.1.23)

## Research Reference

- **Source**: [.agent-tracking/research/20260210-copilot-sdk-upgrade-research.md](../research/20260210-copilot-sdk-upgrade-research.md)
- **Test Strategy**: [.agent-tracking/test-strategies/20260210-copilot-sdk-upgrade-test-strategy.md](../test-strategies/20260210-copilot-sdk-upgrade-test-strategy.md)

---

## Task 1.1: Update `pyproject.toml` Version Pin

### File Operations
- **Modify**: `pyproject.toml` (line 11)

### Specification
Change the pinned SDK version:

```python
# FROM (line 11):
"github-copilot-sdk==0.1.16",

# TO:
"github-copilot-sdk==0.1.23",
```

### Success Criteria
- `pyproject.toml` contains `github-copilot-sdk==0.1.23`

---

## Task 1.2: Regenerate Lock File and Sync

### Commands
```bash
uv lock
uv sync
uv run python -c "import importlib.metadata; print(importlib.metadata.version('github-copilot-sdk'))"
```

### Expected Output
- `uv lock` exits 0, updates `uv.lock` with new SDK hash/version
- `uv sync` exits 0, installs SDK 0.1.23
- Version check prints `0.1.23`

### Success Criteria
- Lock file regenerated without dependency conflicts
- SDK 0.1.23 installed in environment

---

## Task 2.1: Fix `_check_auth()` Breaking Change

### File Operations
- **Modify**: `src/teambot/copilot/sdk_client.py` (line 125)

### Background (Research Lines 90-115)
In SDK 0.1.16, `get_auth_status()` returned a dict-like TypedDict. In SDK 0.1.23, it returns a `GetAuthStatusResponse` dataclass:

```python
@dataclass
class GetAuthStatusResponse:
    isAuthenticated: bool
    authType: str | None
    host: str | None
    login: str | None
    statusMessage: str | None
```

The current code uses `status.get("isAuthenticated", False)` which calls the dict `.get()` method. Dataclasses do not have a `.get()` method, so this raises `AttributeError`.

### Specification
Change line 125 of `src/teambot/copilot/sdk_client.py`:

```python
# CURRENT (line 125):
self._authenticated = status.get("isAuthenticated", False)

# CHANGE TO:
self._authenticated = getattr(status, "isAuthenticated", False)
```

### Rationale
`getattr()` is the safest approach because:
- Works with dataclass objects (production SDK 0.1.23): `getattr(dataclass, "isAuthenticated", False)` → attribute value
- Already wrapped in a try/except block for additional safety
- No new imports needed (`getattr` is a Python builtin)

### Test Impact
- Existing test `test_client_start_calls_sdk_start` (in `tests/test_copilot/test_sdk_client.py`) tests `start()` which calls `_check_auth()`
- Test mocks return dicts: `getattr(dict, "isAuthenticated", False)` returns `False` (dicts don't have `isAuthenticated` attr)
- This is acceptable: tests verify `start()` doesn't crash; `_authenticated` flag being `False` in tests is fine since no test asserts it's `True` via this path

### Success Criteria
- Line 125 uses `getattr(status, "isAuthenticated", False)`
- No import changes needed
- `start()` doesn't crash with SDK 0.1.23

### Dependencies
- Requires: Task 1.2 (SDK 0.1.23 installed)

---

## Task 2.2: Update `list_sessions()` Return Type Annotation

### File Operations
- **Modify**: `src/teambot/copilot/sdk_client.py` (line 477)

### Background (Research Lines 117-127)
In SDK 0.1.16, `CopilotClient.list_sessions()` didn't exist (TeamBot's wrapper called a non-existent method). In SDK 0.1.23, it exists and returns `list[SessionMetadata]` (a dataclass list), not `list[dict[str, Any]]`.

### Specification
Change line 477 of `src/teambot/copilot/sdk_client.py`:

```python
# CURRENT (line 477):
def list_sessions(self) -> list[dict[str, Any]]:

# CHANGE TO:
def list_sessions(self) -> list[Any]:
```

### Rationale
- The return type annotation should not promise `dict[str, Any]` when the SDK now returns dataclass objects
- Using `list[Any]` is honest about the passthrough nature of this wrapper
- TeamBot code that calls `list_sessions()` does not depend on the items being dicts

### Test Impact
- Existing test `test_list_sessions` (in `tests/test_copilot/test_sdk_client.py`) mocks the return value directly
- Conftest fixture at `tests/conftest.py` line 94 mocks `list_sessions = MagicMock(return_value=[])`
- No test changes needed — type annotations don't affect runtime behavior

### Success Criteria
- Return type annotation changed to `list[Any]`
- Existing tests pass unchanged

### Dependencies
- Requires: Task 1.2 (SDK 0.1.23 installed)

---

## Task 3.1: Add SDK Version to `/help` Command Output

### File Operations
- **Modify**: `src/teambot/repl/commands.py` (lines 1-7 for import, lines 83-115 for help output)

### Background (Research Lines 178-210)
The `/help` command currently shows `"TeamBot Interactive Mode"` as its header line. The objective requires displaying the installed SDK version alongside help content. `importlib.metadata.version()` is the correct approach because the SDK's `__version__` is hardcoded to `"0.1.0"` regardless of actual version.

### Specification

#### Step 1: Add import at top of file
Add `import importlib.metadata` to the imports section of `src/teambot/repl/commands.py`:

```python
# Add after line 1 (after the module docstring):
import importlib.metadata
```

#### Step 2: Create version helper
Add a helper function before `handle_help()`:

```python
def _get_sdk_version() -> str:
    """Get the installed Copilot SDK version."""
    try:
        return importlib.metadata.version("github-copilot-sdk")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"
```

#### Step 3: Modify help output header
Change the general help return in `handle_help()` (currently lines 83-115):

```python
# CURRENT (line 84):
        output="""TeamBot Interactive Mode

# CHANGE TO:
        output=f"""TeamBot Interactive Mode (Copilot SDK: {_get_sdk_version()})
```

### Important Notes
- Only the general help branch (the final `return` in `handle_help()`) needs modification
- Topic-specific help branches (`"agent"`, `"parallel"`, `"tasks"`) are NOT modified
- The f-string prefix is added to the triple-quoted string
- Error handling via try/except ensures graceful degradation if SDK is not installed

### Test Impact
- Existing tests check for `"@agent"`, `"/help"`, `"/status"`, etc. — all still present in output
- `test_help_unknown_topic` checks for `"Available commands"` or `"@agent"` — both still present
- New assertion needed: `"Copilot SDK:" in result.output` (see Task 4.3)

### Success Criteria
- `handle_help([]).output` starts with `"TeamBot Interactive Mode (Copilot SDK: 0.1.23)"`
- `PackageNotFoundError` is caught and falls back to `"unknown"`
- No changes to topic-specific help branches

### Dependencies
- None (can run in parallel with Phase 2)

---

## Task 4.1: Run Full Test Suite

### Commands
```bash
uv run pytest
```

### Expected Output
- All ~1084 tests pass
- 0 failures, 0 errors
- Coverage report shows ≥80%

### Failure Recovery
If tests fail:
1. Check if failure is in `test_copilot/` → likely SDK API change not caught in research
2. Check if failure is in `test_repl/` → likely help text assertion broken
3. Check if failure is unrelated → pre-existing issue, not a blocker

### Success Criteria
- Exit code 0
- 0 failures, 0 errors

### Dependencies
- Requires: Tasks 2.1, 2.2, 3.1 all complete

---

## Task 4.2: Run Linting

### Commands
```bash
uv run ruff check .
uv run ruff format --check .
```

### Expected Output
- Both commands exit 0
- No lint errors, no formatting issues

### Failure Recovery
If lint fails:
1. `E402` (mid-file import) → move `importlib.metadata` import to top of file
2. `F811` (redefinition) → ensure no duplicate imports
3. `I001` (import order) → run `uv run ruff check . --fix` and `uv run ruff format .`

### Success Criteria
- Exit code 0 for both commands

### Dependencies
- Requires: Task 4.1 (tests pass first)

---

## Task 4.3: Add Help Version Test Assertion

### File Operations
- **Modify**: `tests/test_repl/test_commands.py` (add new test method after line 51)

### Specification
Add a new test to the `TestHelpCommand` class:

```python
def test_help_shows_sdk_version(self):
    """Test /help output includes Copilot SDK version."""
    result = handle_help([])
    assert "Copilot SDK:" in result.output
```

### Placement
Insert after the `test_help_contains_use_agent_and_reset_agent` method (after line 51), within the `TestHelpCommand` class.

### Test Pattern
Follows existing codebase conventions:
- Direct function call (no HTTP clients or app setup)
- String presence assertion with `in` operator
- Descriptive method name explaining behavior
- Docstring on test method

### Success Criteria
- New test exists and passes
- Does not break existing tests
- Follows existing test file conventions

### Dependencies
- Requires: Task 3.1 (help output includes version)

---

## Task 4.4: CLI Smoke Test

### Commands
```bash
uv run teambot --help
```

### Expected Output
- No import errors
- Help text renders with available commands (init, run, status)
- Exit code 0

### Success Criteria
- CLI starts without ImportError or AttributeError
- Help text is displayed

### Dependencies
- Requires: Tasks 4.1, 4.2 pass
