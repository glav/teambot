<!-- markdownlint-disable-file -->
# Task Details: Model Cache Auto-Setup and Login Validation

## Research Reference

**Source Research**: .agent-tracking/research/20260219-model-cache-auto-setup-research.md

---

## Phase 1: Unit Tests (TDD)

### Task 1.1: Create unit tests for blocking auth check

Create unit tests in `tests/test_cli.py` that define the expected behavior of `_check_copilot_authentication_blocking()`.

* **Files**:
  * `tests/test_cli.py` - Add new test class `TestRunAuthCheck`
* **Success**:
  * Test class `TestRunAuthCheck` exists
  * Tests for auth success returning True
  * Tests for auth failure returning False with error message
  * Tests for exception handling (graceful failure)
  * Tests initially fail (no implementation)
* **Research References**:
  * .agent-tracking/research/20260219-model-cache-auto-setup-research.md (Lines 519-570) - Test patterns and examples
  * .teambot/model-cache-auto/artifacts/test_strategy.md (Lines 79-103) - Component 1 test requirements
* **Dependencies**:
  * None

**Test Cases to Create:**

```python
class TestRunAuthCheck:
    """Tests for authentication check in cmd_run flow."""

    def test_auth_check_blocking_returns_true_when_authenticated(self, capsys):
        """Blocking auth check returns True when user is authenticated."""
        # Mock _check_auth_async to return (True, None)
        # Call _check_copilot_authentication_blocking(display)
        # Assert returns True
        # Assert no error output
        
    def test_auth_check_blocking_returns_false_when_not_authenticated(self, capsys):
        """Blocking auth check returns False with guidance when not authenticated."""
        # Mock _check_auth_async to return (False, "Not authenticated")
        # Call _check_copilot_authentication_blocking(display)
        # Assert returns False
        # Assert output contains "not authenticated"
        # Assert output contains "copilot auth"
        
    def test_auth_check_blocking_handles_exception_gracefully(self, capsys):
        """Blocking auth check returns False on exception."""
        # Mock _check_auth_async to raise Exception
        # Call _check_copilot_authentication_blocking(display)
        # Assert returns False
        # Assert output contains guidance
```

---

### Task 1.2: Create unit tests for cache missing detection

Create unit tests that verify cache detection logic integrates with `cmd_run()` flow.

* **Files**:
  * `tests/test_cli.py` - Add tests to `TestRunModelCache` class
* **Success**:
  * Tests for missing cache file detection
  * Tests for empty cache (models: []) detection
  * Tests for valid cache no-op
  * Tests initially fail (no implementation)
* **Research References**:
  * .agent-tracking/research/20260219-model-cache-auto-setup-research.md (Lines 386-420) - Cache detection approach
  * .teambot/model-cache-auto/artifacts/test_strategy.md (Lines 104-126) - Component 2 test requirements
* **Dependencies**:
  * None

**Test Cases to Create:**

```python
class TestRunModelCache:
    """Tests for model cache auto-refresh in cmd_run flow."""

    def test_ensure_cache_returns_immediately_when_valid(self, tmp_path, monkeypatch):
        """_ensure_model_cache returns immediately when cache is valid."""
        # Setup valid cache file
        # Mock is_cache_valid to return True
        # Call _ensure_model_cache(display)
        # Assert no refresh triggered
        # Assert no output
        
    def test_ensure_cache_detects_missing_file(self, tmp_path, monkeypatch, capsys):
        """_ensure_model_cache detects when cache file doesn't exist."""
        # No cache file
        # Mock load_cache to return None
        # Mock _refresh_model_cache to return True
        # Call _ensure_model_cache(display)
        # Assert refresh triggered
        # Assert "Refreshing model cache" in output
        
    def test_ensure_cache_detects_empty_models(self, tmp_path, monkeypatch, capsys):
        """_ensure_model_cache treats empty models as missing."""
        # Create cache with {"models": []}
        # Mock is_cache_valid to return False
        # Mock _refresh_model_cache to return True
        # Call _ensure_model_cache(display)
        # Assert refresh triggered
```

---

### Task 1.3: Create unit tests for auto-refresh flow

Create unit tests for the auto-refresh behavior including success and failure paths.

* **Files**:
  * `tests/test_cli.py` - Add tests to `TestRunModelCache` class
* **Success**:
  * Tests for successful refresh continuing workflow
  * Tests for failed refresh showing guidance
  * Tests for network failure scenario
  * Tests initially fail (no implementation)
* **Research References**:
  * .agent-tracking/research/20260219-model-cache-auto-setup-research.md (Lines 422-503) - Refresh flow approach
  * .teambot/model-cache-auto/artifacts/test_strategy.md (Lines 127-154) - Component 3 test requirements
* **Dependencies**:
  * None

**Test Cases to Create:**

```python
    def test_ensure_cache_continues_after_successful_refresh(self, tmp_path, monkeypatch, capsys):
        """Successful cache refresh allows workflow to continue."""
        # Mock load_cache to return None (missing)
        # Mock _refresh_model_cache to return True
        # Call _ensure_model_cache(display)
        # Assert function completes without error
        # Assert "Refreshing model cache" in output
        
    def test_ensure_cache_continues_even_if_refresh_fails(self, tmp_path, monkeypatch, capsys):
        """Failed cache refresh continues - let ConfigLoader handle errors."""
        # Mock load_cache to return None (missing)
        # Mock _refresh_model_cache to return False
        # Call _ensure_model_cache(display)
        # Assert function completes without error
        # Refresh function handles its own error messaging
```

---

## Phase 2: Core Implementation

### Task 2.1: Implement `_check_copilot_authentication_blocking()` function

Add a new helper function that performs a blocking auth check suitable for `cmd_run()`.

* **Files**:
  * `src/teambot/cli.py` - Add function after existing `_check_copilot_authentication()` (around line 115)
* **Success**:
  * Function defined with proper docstring
  * Returns True when authenticated
  * Returns False with error message when not authenticated
  * Handles exceptions gracefully with debug logging
  * All Task 1.1 tests pass
* **Research References**:
  * .agent-tracking/research/20260219-model-cache-auto-setup-research.md (Lines 295-372) - Scenario 1 implementation details
  * .agent-tracking/research/20260219-model-cache-auto-setup-research.md (Lines 659-688) - Helper function code example
* **Dependencies**:
  * Task 1.1 (tests exist)

**Implementation:**

```python
def _check_copilot_authentication_blocking(display: ConsoleDisplay) -> bool:
    """Check Copilot authentication status (blocking version for cmd_run).
    
    Unlike _check_copilot_authentication which continues with warnings,
    this version treats authentication failure as a blocking error.
    
    Args:
        display: Console display for output.
        
    Returns:
        True if authenticated, False otherwise (blocks execution).
    """
    try:
        is_auth, error = asyncio.run(_check_auth_async())
        
        if is_auth:
            return True
        else:
            display.print_error("Copilot not authenticated")
            if error and "not available" not in error.lower():
                display.print_error(f"  {error}")
            display.print_info("Run 'copilot auth' to authenticate")
            return False
    except Exception as e:
        logging.debug(f"Could not check authentication: {e}")
        display.print_error("Could not verify authentication status")
        display.print_info("Run 'copilot auth' to ensure you're authenticated")
        return False
```

**Insert Location**: After `_check_copilot_authentication()` function (around line 115)

---

### Task 2.2: Implement `_ensure_model_cache()` function

Add a helper function that checks cache validity and triggers refresh if needed.

* **Files**:
  * `src/teambot/cli.py` - Add function after `_check_copilot_authentication_blocking()` (around line 140)
* **Success**:
  * Function defined with proper docstring
  * Returns immediately if cache is valid
  * Displays "Refreshing model cache..." when refresh needed
  * Calls existing `_refresh_model_cache()` for refresh
  * Non-blocking on refresh failure (let ConfigLoader report errors)
  * All Task 1.2 and Task 1.3 tests pass
* **Research References**:
  * .agent-tracking/research/20260219-model-cache-auto-setup-research.md (Lines 386-503) - Scenario 2 implementation details
  * .agent-tracking/research/20260219-model-cache-auto-setup-research.md (Lines 690-717) - Helper function code example
* **Dependencies**:
  * Task 1.2, Task 1.3 (tests exist)

**Implementation:**

```python
def _ensure_model_cache(display: ConsoleDisplay) -> None:
    """Ensure model cache is available, refreshing if needed.
    
    Checks if model cache exists and is valid. If missing or expired,
    automatically refreshes from SDK with status feedback.
    
    This is non-blocking - if refresh fails, execution continues
    and ConfigLoader will report specific validation errors.
    
    Args:
        display: Console display for output.
    """
    from teambot.config.model_cache import is_cache_valid, load_cache
    
    cache = load_cache()
    
    if is_cache_valid(cache):
        # Cache exists and valid, no action needed
        return
    
    # Cache missing or expired - need to refresh
    if cache is None:
        display.print_info("Refreshing model cache...")
    else:
        display.print_info("Model cache expired, refreshing...")
    
    _refresh_model_cache(display)
```

**Insert Location**: After `_check_copilot_authentication_blocking()` function

---

### Task 2.3: Integrate auth check and cache ensure into `cmd_run()`

Modify `cmd_run()` to call auth check and cache ensure before config loading.

* **Files**:
  * `src/teambot/cli.py` - Modify `cmd_run()` function (around lines 394-410)
* **Success**:
  * Auth check called before config loading
  * Auth failure returns 1 immediately
  * Cache ensure called after auth check, before config loading
  * Existing behavior preserved when cache valid
  * All unit tests pass
* **Research References**:
  * .agent-tracking/research/20260219-model-cache-auto-setup-research.md (Lines 619-655) - Modified cmd_run() example
  * .agent-tracking/research/20260219-model-cache-auto-setup-research.md (Lines 163-167) - Code path trace showing insertion point
* **Dependencies**:
  * Task 2.1, Task 2.2

**Modification to cmd_run():**

Find the `cmd_run()` function (currently around line 394). Add the auth check and cache ensure after the function signature and docstring, BEFORE the config path checks:

```python
def cmd_run(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    """Run TeamBot with an objective."""
    config_path = Path(args.config)
    teambot_dir = Path(".teambot")

    # ==========================================
    # NEW: Authentication check (blocking)
    # ==========================================
    if not _check_copilot_authentication_blocking(display):
        return 1

    # ==========================================
    # NEW: Ensure model cache available
    # ==========================================
    _ensure_model_cache(display)

    # ==========================================
    # Existing code continues below unchanged
    # ==========================================
    if not config_path.exists():
        display.print_error(f"Configuration not found: {config_path}")
        # ... rest of existing code
```

**Key Points:**
- Insert AFTER `teambot_dir = Path(".teambot")` line
- Insert BEFORE `if not config_path.exists():` check
- Auth check must be first (blocking, returns 1 on failure)
- Cache ensure is second (non-blocking)

---

## Phase 3: Acceptance Tests

### Task 3.1: Create acceptance test file with AT-001 to AT-005 scenarios

Create a new acceptance test file covering all feature specification scenarios.

* **Files**:
  * `tests/test_model_cache_auto_acceptance.py` - NEW FILE
* **Success**:
  * File created with proper docstring
  * AT-001: First run with missing cache auto-refreshes
  * AT-002: Unauthenticated user gets clear error
  * AT-003: Network failure shows guidance
  * AT-004: Valid cache has no refresh output
  * AT-005: Empty cache triggers refresh
  * All 5 acceptance tests pass
* **Research References**:
  * .agent-tracking/research/20260219-model-cache-auto-setup-research.md (Lines 519-615) - Test patterns
  * .teambot/model-cache-auto/artifacts/test_strategy.md (Lines 220-260) - Critical test scenarios
  * .teambot/model-cache-auto/artifacts/feature_spec.md (Lines 293-390) - Acceptance test specifications
* **Dependencies**:
  * Phase 2 completion

**Test File Structure:**

```python
"""Acceptance tests for Model Cache Auto-Setup and Login Validation.

Core logic is tested directly; selective mocking is used for external dependencies.
"""

import argparse
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


class TestModelCacheAutoSetupAcceptance:
    """Acceptance test scenarios for model cache auto-setup."""

    # =========================================================================
    # AT-001: First Run After Installation (Happy Path)
    # =========================================================================

    def test_at_001_missing_cache_triggers_refresh(self, tmp_path, monkeypatch, capsys):
        """AT-001: Missing cache triggers auto-refresh during teambot run."""
        from teambot.cli import ConsoleDisplay, cmd_run
        from teambot.config.default_config import create_default_config

        monkeypatch.chdir(tmp_path)
        
        # Setup: create config but no cache
        (tmp_path / ".teambot").mkdir()
        config = create_default_config()
        config_path = tmp_path / "teambot.json"
        # Write minimal config
        import json
        with open(config_path, "w") as f:
            json.dump({"agents": [], "default_model": None}, f)
        
        # Mock auth success, refresh success
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                with patch("teambot.cli.load_cache", return_value=None):
                    with patch("teambot.cli.is_cache_valid", return_value=False):
                        # Mock interactive mode to avoid hanging
                        with patch("teambot.cli.run_interactive_mode"):
                            args = argparse.Namespace(config="teambot.json", objective=None, resume=False)
                            display = ConsoleDisplay()
                            
                            result = cmd_run(args, display)

        captured = capsys.readouterr()
        assert "Refreshing model cache" in captured.out
        # May fail on other config issues, but refresh was triggered
        
    # =========================================================================
    # AT-002: Unauthenticated User
    # =========================================================================

    def test_at_002_unauthenticated_stops_with_clear_error(self, tmp_path, monkeypatch, capsys):
        """AT-002: Unauthenticated user gets clear error with guidance."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)
        
        # Setup: create config file
        (tmp_path / "teambot.json").write_text('{"agents": []}')
        
        # Mock auth failure
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(False, "Not authenticated"))):
            args = argparse.Namespace(config="teambot.json", objective=None, resume=False)
            display = ConsoleDisplay()
            
            result = cmd_run(args, display)

        assert result == 1
        captured = capsys.readouterr()
        assert "not authenticated" in captured.out.lower()
        assert "copilot auth" in captured.out.lower()
        
    # =========================================================================
    # AT-003: Network Failure During Cache Refresh
    # =========================================================================

    def test_at_003_network_failure_shows_guidance(self, tmp_path, monkeypatch, capsys):
        """AT-003: Cache refresh failure shows error with guidance."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)
        
        # Setup: config exists but no cache
        (tmp_path / ".teambot").mkdir()
        (tmp_path / "teambot.json").write_text('{"agents": [], "default_model": null}')
        
        # Mock auth success, refresh failure
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=False)):
                with patch("teambot.cli.load_cache", return_value=None):
                    with patch("teambot.cli.is_cache_valid", return_value=False):
                        args = argparse.Namespace(config="teambot.json", objective=None, resume=False)
                        display = ConsoleDisplay()
                        
                        result = cmd_run(args, display)

        captured = capsys.readouterr()
        assert "Refreshing model cache" in captured.out
        # Refresh failed - function handles its own error messages
        
    # =========================================================================
    # AT-004: Returning User With Valid Cache (No-Op)
    # =========================================================================

    def test_at_004_valid_cache_no_refresh_output(self, tmp_path, monkeypatch, capsys):
        """AT-004: Valid cache skips refresh - no delay or messages."""
        from teambot.cli import ConsoleDisplay, cmd_run

        monkeypatch.chdir(tmp_path)
        
        # Setup: config and valid cache
        (tmp_path / ".teambot").mkdir()
        (tmp_path / "teambot.json").write_text('{"agents": [], "default_model": null}')
        
        # Mock auth success, valid cache
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli.is_cache_valid", return_value=True):
                with patch("teambot.cli.run_interactive_mode"):
                    args = argparse.Namespace(config="teambot.json", objective=None, resume=False)
                    display = ConsoleDisplay()
                    
                    result = cmd_run(args, display)

        captured = capsys.readouterr()
        assert "Refreshing model cache" not in captured.out
        
    # =========================================================================
    # AT-005: Cache Exists But Empty
    # =========================================================================

    def test_at_005_empty_cache_triggers_refresh(self, tmp_path, monkeypatch, capsys):
        """AT-005: Empty cache treated same as missing - triggers refresh."""
        from teambot.cli import ConsoleDisplay, cmd_run
        from teambot.config.model_cache import ModelCache

        monkeypatch.chdir(tmp_path)
        
        # Setup: config exists, cache with empty models
        (tmp_path / ".teambot").mkdir()
        (tmp_path / "teambot.json").write_text('{"agents": [], "default_model": null}')
        
        # Create empty cache
        empty_cache = ModelCache(models=[], timestamp=0, sdk_version="1.0")
        
        # Mock auth success, empty cache detected
        with patch("teambot.cli._check_auth_async", AsyncMock(return_value=(True, None))):
            with patch("teambot.cli.load_cache", return_value=empty_cache):
                with patch("teambot.cli.is_cache_valid", return_value=False):
                    with patch("teambot.cli._refresh_model_cache_async", AsyncMock(return_value=True)):
                        with patch("teambot.cli.run_interactive_mode"):
                            args = argparse.Namespace(config="teambot.json", objective=None, resume=False)
                            display = ConsoleDisplay()
                            
                            result = cmd_run(args, display)

        captured = capsys.readouterr()
        assert "Refreshing model cache" in captured.out or "expired" in captured.out.lower()
```

---

## Phase 4: Validation & Cleanup

### Task 4.1: Run full test suite and verify no regressions

Execute the complete test suite to ensure no regressions were introduced.

* **Files**:
  * None (validation only)
* **Success**:
  * All existing tests pass
  * All new tests pass
  * No test failures
* **Research References**:
  * AGENTS.md - Test running instructions
* **Dependencies**:
  * Phase 3 completion

**Commands to Execute:**

```bash
# Run all tests
uv run pytest

# Run with coverage to verify new code coverage
uv run pytest --cov=src/teambot --cov-report=term-missing

# Verify new test coverage specifically
uv run pytest tests/test_cli.py tests/test_model_cache_auto_acceptance.py -v
```

---

### Task 4.2: Run linters and format code

Ensure code quality standards are met.

* **Files**:
  * All modified files
* **Success**:
  * ruff check passes
  * ruff format check passes
* **Research References**:
  * AGENTS.md - Linting instructions
* **Dependencies**:
  * Task 4.1

**Commands to Execute:**

```bash
# Format code
uv run ruff format .

# Check linting
uv run ruff check . --fix

# Verify format check passes
uv run ruff format --check .
```

---

### Task 4.3: Manual verification of key scenarios

Verify the feature works as expected in real usage.

* **Files**:
  * None (manual testing)
* **Success**:
  * Auth failure shows clear message
  * Missing cache triggers refresh
  * Valid cache has no delay
* **Research References**:
  * .teambot/model-cache-auto/artifacts/feature_spec.md (Lines 293-390) - Acceptance criteria
* **Dependencies**:
  * Task 4.2

**Manual Test Steps:**

1. **Unauthenticated test** (if possible):
   - Temporarily invalidate auth
   - Run `uv run teambot run`
   - Verify error message mentions "copilot auth"

2. **Missing cache test**:
   - Delete `.teambot/model_cache.json` if exists
   - Run `uv run teambot run`
   - Verify "Refreshing model cache..." appears
   
3. **Valid cache test**:
   - Ensure cache exists
   - Run `uv run teambot run`
   - Verify no refresh messages appear

---

## Dependencies

* pytest >=7.4.0
* pytest-mock
* pytest-asyncio
* pytest-cov
* ruff
* uv

## Success Criteria

* All Phase 1 unit tests pass
* All Phase 2 implementation complete
* All Phase 3 acceptance tests pass
* All Phase 4 validation checks pass
* No regressions in existing tests
* Code formatted and linted
* Feature works as specified in manual verification
