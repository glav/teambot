<!-- markdownlint-disable-file -->
# Task Research Document: Fix Authentication Command Message

Update all error messages from incorrect `copilot auth` to correct `copilot login` command. The GitHub Copilot CLI uses `copilot login` for OAuth device flow authentication, but TeamBot displays the non-existent `copilot auth` command in error messages, causing user confusion.

## Task Implementation Requests

* **Replace `copilot auth` with `copilot login` in `src/teambot/cli.py`** (5 occurrences at lines 108, 114, 139, 144, 239)
* **Update README.md** (1 occurrence at line 17)
* **Update `docs/guides/installation.md`** (2 occurrences at lines 17, 227)
* **Update test assertions** (9 occurrences across 4 test files)

## Scope and Success Criteria

* **Scope**: All user-facing messages, documentation, and test assertions containing `copilot auth`
* **Out of Scope**: Historical artifacts in `.agent-tracking/`, objective files, orchestration state files
* **Assumptions**:
  1. `copilot login` is the correct and stable command per Copilot CLI help output
  2. No logic changes required - pure string replacement
  3. Existing test infrastructure is sufficient

* **Success Criteria**:
  * ✅ Zero occurrences of `copilot auth` in `src/teambot/cli.py`
  * ✅ Zero occurrences of `copilot auth` in `README.md` and `docs/guides/installation.md`
  * ✅ All test assertions updated to check for `copilot login`
  * ✅ All existing tests pass after changes
  * ✅ `grep -r "copilot auth" src/ tests/ docs/ README.md` returns no results

## Outline

1. [Task Implementation Requests](#task-implementation-requests)
2. [Scope and Success Criteria](#scope-and-success-criteria)
3. [Entry Point Analysis](#entry-point-analysis)
4. [Research Executed](#research-executed)
5. [Key Discoveries](#key-discoveries)
6. [Technical Scenarios](#technical-scenarios)

### Potential Next Research

* None - this is a straightforward string replacement task with no technical complexity

## Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `teambot run` (unauthenticated) | `cli.py:cmd_run()` → `_check_copilot_authentication_blocking()` | YES ✅ | YES - Lines 139, 144 |
| `teambot init` (unauthenticated) | `cli.py:cmd_init()` → `_check_copilot_authentication()` | YES ✅ | YES - Lines 108, 114 |
| `teambot init` (no Copilot CLI) | `cli.py:cmd_init()` → `check_copilot_installed()` | YES ✅ | YES - Line 239 |

### Code Path Trace

#### Entry Point 1: `teambot run` (Unauthenticated User)
1. User enters: `teambot run objectives/task.md`
2. Handled by: `cli.py:cmd_run()` (line 458)
3. Calls: `_check_copilot_authentication_blocking()` (lines 118-145)
4. On auth failure, displays message at lines 139, 144 ✅

#### Entry Point 2: `teambot init` (Unauthenticated User)
1. User enters: `teambot init`
2. Handled by: `cli.py:cmd_init()` (line ~200)
3. Calls: `_check_copilot_authentication()` (lines 87-115)
4. On auth failure, displays warning at lines 108, 114 ✅

#### Entry Point 3: `teambot init` (Copilot CLI Not Installed)
1. User enters: `teambot init`
2. Handled by: `cli.py:cmd_init()` → `check_copilot_installed()` (line ~230)
3. On missing CLI, displays warning at line 239 ✅

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| None identified | N/A | N/A |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

## Research Executed

### Testing Infrastructure Research

* **Framework**: pytest 7.4+ with pytest-mock and pytest-cov
  * Location: `tests/` directory (mirrors `src/teambot/` structure)
  * Naming: `test_*.py` pattern, test functions `test_*`
  * Runner: `uv run pytest` (from pyproject.toml)
  * Coverage: pytest-cov with 80% target

### Test Patterns Found

* **File**: `tests/test_cli.py` (Lines 605-630)
  * Tests `_check_copilot_authentication_blocking()` function
  * Uses `capsys.readouterr()` for output capture
  * Mocks `_check_auth_async` with AsyncMock
  * Assertions check for strings in `captured.out.lower()`

* **File**: `tests/test_acceptance_validation.py` (Lines 117-158)
  * AT-002 acceptance test for unauthenticated user flow
  * Creates temp directory with `tmp_path` fixture
  * Uses `monkeypatch.chdir()` for working directory
  * Asserts both exit code and output content

### Coverage Standards

* **Unit Tests**: 80% minimum (per pyproject.toml)
* **Acceptance Tests**: Marked with `@pytest.mark.acceptance`
* **Critical Paths**: Auth flow covered by existing AT-002 tests

### Testing Approach Recommendation

* **Code Changes**: Code-First (simple string replacement)
* **Verification**: Update existing assertions (no new tests needed)

**Rationale**: This is a pure string replacement with no logic changes. Existing tests comprehensively cover the auth flow - only assertions need updating to reflect new expected output.

### File Analysis

* `src/teambot/cli.py`
  * Line 108: `display.print_info("  Run 'copilot auth' to authenticate")` - in `_check_copilot_authentication()`
  * Line 114: `display.print_info("Run 'copilot auth' to ensure you're authenticated")` - exception handler
  * Line 139: `display.print_info("Run 'copilot auth' to authenticate")` - in `_check_copilot_authentication_blocking()`
  * Line 144: `display.print_info("Run 'copilot auth' to ensure you're authenticated")` - exception handler
  * Line 239: `display.print_warning("After installing, authenticate with: copilot auth")` - in `check_copilot_installed()`

* `README.md`
  * Line 17: `authenticate with \`copilot auth\``

* `docs/guides/installation.md`
  * Line 17: `copilot auth  # Authenticate if needed`
  * Line 227: `copilot auth`

* `tests/test_cli.py`
  * Line 609: `assert "copilot auth" in captured.out.lower()`
  * Line 629: `assert "copilot auth" in captured.out.lower()`

* `tests/test_acceptance_validation.py`
  * Line 118: docstring mentions `'copilot auth'`
  * Line 155: `assert "copilot auth" in captured.out.lower()`
  * Line 408: `assert "copilot auth" in captured.out.lower()`

* `tests/test_init_model_config_acceptance.py`
  * Line 115: `assert "not authenticated" in captured.out.lower() or "copilot auth" in captured.out.lower()`
  * Line 135: `assert "copilot auth" in output_lower or "github_token" in output_lower`

* `tests/test_model_cache_auto_acceptance.py`
  * Line 110: `assert "copilot auth" in captured.out.lower()`

### Code Search Results

* Pattern: `copilot auth` in source code
  * `src/teambot/cli.py`: 5 matches (lines 108, 114, 139, 144, 239)
  
* Pattern: `copilot auth` in documentation
  * `README.md`: 1 match (line 17)
  * `docs/guides/installation.md`: 2 matches (lines 17, 227)
  
* Pattern: `copilot auth` in tests
  * `tests/test_cli.py`: 2 matches (lines 609, 629)
  * `tests/test_acceptance_validation.py`: 3 matches (lines 118, 155, 408)
  * `tests/test_init_model_config_acceptance.py`: 2 matches (lines 115, 135)
  * `tests/test_model_cache_auto_acceptance.py`: 1 match (line 110)

### Project Conventions

* Standards referenced: AGENTS.md (Python testing with pytest)
* Instructions followed: Use `uv run pytest` for testing, `uv run ruff check .` and `uv run ruff format .` for linting

## Key Discoveries

### 📍 All Occurrences Summary

| Category | File | Line(s) | Current Text |
|----------|------|---------|--------------|
| 🔧 Source | `src/teambot/cli.py` | 108 | `Run 'copilot auth' to authenticate` |
| 🔧 Source | `src/teambot/cli.py` | 114 | `Run 'copilot auth' to ensure you're authenticated` |
| 🔧 Source | `src/teambot/cli.py` | 139 | `Run 'copilot auth' to authenticate` |
| 🔧 Source | `src/teambot/cli.py` | 144 | `Run 'copilot auth' to ensure you're authenticated` |
| 🔧 Source | `src/teambot/cli.py` | 239 | `authenticate with: copilot auth` |
| 📚 Docs | `README.md` | 17 | `authenticate with \`copilot auth\`` |
| 📚 Docs | `docs/guides/installation.md` | 17 | `copilot auth  # Authenticate if needed` |
| 📚 Docs | `docs/guides/installation.md` | 227 | `copilot auth` |
| 🧪 Test | `tests/test_cli.py` | 609, 629 | `assert "copilot auth" in captured.out.lower()` |
| 🧪 Test | `tests/test_acceptance_validation.py` | 155, 408 | `assert "copilot auth" in captured.out.lower()` |
| 🧪 Test | `tests/test_init_model_config_acceptance.py` | 115, 135 | `"copilot auth" in ...` |
| 🧪 Test | `tests/test_model_cache_auto_acceptance.py` | 110 | `assert "copilot auth" in captured.out.lower()` |

**Total: 17 occurrences across 7 files**

### Implementation Pattern

All changes follow the same simple pattern:
```python
# Before
"copilot auth"

# After
"copilot login"
```

### Verification Command

After implementation, verify with:
```bash
grep -r "copilot auth" src/ tests/ docs/ README.md
```
Expected result: No matches (empty output)

## Technical Scenarios

### 1. String Replacement in Source Code

Replace `copilot auth` with `copilot login` in all user-facing messages within `src/teambot/cli.py`.

**Requirements:**
* 5 occurrences at lines 108, 114, 139, 144, 239
* Maintain exact spacing and formatting
* No logic changes

**Preferred Approach:**
* Direct string replacement using sed or manual edit

```text
src/teambot/cli.py  # Update lines 108, 114, 139, 144, 239
```

**Implementation Details:**

```python
# Line 108 - Change from:
display.print_info("  Run 'copilot auth' to authenticate")
# To:
display.print_info("  Run 'copilot login' to authenticate")

# Line 114 - Change from:
display.print_info("Run 'copilot auth' to ensure you're authenticated")
# To:
display.print_info("Run 'copilot login' to ensure you're authenticated")

# Line 139 - Change from:
display.print_info("Run 'copilot auth' to authenticate")
# To:
display.print_info("Run 'copilot login' to authenticate")

# Line 144 - Change from:
display.print_info("Run 'copilot auth' to ensure you're authenticated")
# To:
display.print_info("Run 'copilot login' to ensure you're authenticated")

# Line 239 - Change from:
display.print_warning("After installing, authenticate with: copilot auth")
# To:
display.print_warning("After installing, authenticate with: copilot login")
```

### 2. Documentation Updates

Update documentation to reference correct `copilot login` command.

**Requirements:**
* README.md line 17
* docs/guides/installation.md lines 17 and 227

**Implementation Details:**

```markdown
<!-- README.md line 17 -->
# Before:
- **GitHub Copilot CLI** - [Install Copilot CLI](https://githubnext.com/projects/copilot-cli/) and authenticate with `copilot auth`
# After:
- **GitHub Copilot CLI** - [Install Copilot CLI](https://githubnext.com/projects/copilot-cli/) and authenticate with `copilot login`

<!-- docs/guides/installation.md line 17 -->
# Before:
copilot auth  # Authenticate if needed
# After:
copilot login  # Authenticate if needed

<!-- docs/guides/installation.md line 227 -->
# Before:
copilot auth
# After:
copilot login
```

### 3. Test Assertion Updates

Update all test assertions to verify `copilot login` instead of `copilot auth`.

**Requirements:**
* 9 assertions across 4 test files
* Maintain test logic unchanged

**Implementation Details:**

```python
# tests/test_cli.py
# Line 609 - Change from:
assert "copilot auth" in captured.out.lower()
# To:
assert "copilot login" in captured.out.lower()

# Line 629 - Change from:
assert "copilot auth" in captured.out.lower()
# To:
assert "copilot login" in captured.out.lower()

# tests/test_acceptance_validation.py
# Line 118 (docstring) - Change from:
"""AT-002: Unauthenticated user sees clear error with 'copilot auth' guidance.
# To:
"""AT-002: Unauthenticated user sees clear error with 'copilot login' guidance.

# Line 155 - Change from:
assert "copilot auth" in captured.out.lower(), (
# To:
assert "copilot login" in captured.out.lower(), (

# Line 156 - Change from:
f"Expected 'copilot auth' guidance in: {captured.out}"
# To:
f"Expected 'copilot login' guidance in: {captured.out}"

# Line 408 - Change from:
assert "copilot auth" in captured.out.lower()
# To:
assert "copilot login" in captured.out.lower()

# tests/test_init_model_config_acceptance.py
# Line 115 - Change from:
assert "not authenticated" in captured.out.lower() or "copilot auth" in captured.out.lower()
# To:
assert "not authenticated" in captured.out.lower() or "copilot login" in captured.out.lower()

# Line 135 - Change from:
assert "copilot auth" in output_lower or "github_token" in output_lower
# To:
assert "copilot login" in output_lower or "github_token" in output_lower

# tests/test_model_cache_auto_acceptance.py
# Line 110 - Change from:
assert "copilot auth" in captured.out.lower()
# To:
assert "copilot login" in captured.out.lower()
```

## Implementation Checklist

### Source Code (`src/teambot/cli.py`)
- [ ] Line 108: `copilot auth` → `copilot login`
- [ ] Line 114: `copilot auth` → `copilot login`
- [ ] Line 139: `copilot auth` → `copilot login`
- [ ] Line 144: `copilot auth` → `copilot login`
- [ ] Line 239: `copilot auth` → `copilot login`

### Documentation
- [ ] `README.md` line 17: `copilot auth` → `copilot login`
- [ ] `docs/guides/installation.md` line 17: `copilot auth` → `copilot login`
- [ ] `docs/guides/installation.md` line 227: `copilot auth` → `copilot login`

### Tests
- [ ] `tests/test_cli.py` line 609: assertion update
- [ ] `tests/test_cli.py` line 629: assertion update
- [ ] `tests/test_acceptance_validation.py` line 118: docstring update
- [ ] `tests/test_acceptance_validation.py` line 155-156: assertion + message update
- [ ] `tests/test_acceptance_validation.py` line 408: assertion update
- [ ] `tests/test_init_model_config_acceptance.py` line 115: assertion update
- [ ] `tests/test_init_model_config_acceptance.py` line 135: assertion update
- [ ] `tests/test_model_cache_auto_acceptance.py` line 110: assertion update

### Verification
- [ ] Run `uv run pytest tests/test_cli.py tests/test_acceptance_validation.py tests/test_init_model_config_acceptance.py tests/test_model_cache_auto_acceptance.py -v`
- [ ] Run `grep -r "copilot auth" src/ tests/ docs/ README.md` (expect no output)
- [ ] Run `uv run ruff check .` and `uv run ruff format --check .`
