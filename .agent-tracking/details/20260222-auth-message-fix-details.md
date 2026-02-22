<!-- markdownlint-disable-file -->
# Task Details: Fix Authentication Command Message

## Research Reference

**Source Research**: .teambot/auth-message/artifacts/research.md
**Test Strategy**: .teambot/auth-message/artifacts/test_strategy.md

## Phase 1: Source Code Updates

### Task 1.1: Update `_check_copilot_authentication()` primary message

Update the authentication guidance message in the `_check_copilot_authentication()` function.

* **Files**:
  * `src/teambot/cli.py` line 108 - Primary auth failure message
* **Change**:
  ```python
  # FROM:
  display.print_info("  Run 'copilot auth' to authenticate")
  # TO:
  display.print_info("  Run 'copilot login' to authenticate")
  ```
* **Success**:
  * Line 108 contains `copilot login` instead of `copilot auth`
* **Research References**:
  * .teambot/auth-message/artifacts/research.md (Lines 122-127) - Source code analysis

### Task 1.2: Update `_check_copilot_authentication()` exception message

Update the exception handler message in the `_check_copilot_authentication()` function.

* **Files**:
  * `src/teambot/cli.py` line 114 - Exception handler message
* **Change**:
  ```python
  # FROM:
  display.print_info("Run 'copilot auth' to ensure you're authenticated")
  # TO:
  display.print_info("Run 'copilot login' to ensure you're authenticated")
  ```
* **Success**:
  * Line 114 contains `copilot login` instead of `copilot auth`
* **Research References**:
  * .teambot/auth-message/artifacts/research.md (Lines 122-127) - Source code analysis

### Task 1.3: Update `_check_copilot_authentication_blocking()` primary message

Update the authentication guidance message in the blocking auth check function.

* **Files**:
  * `src/teambot/cli.py` line 139 - Primary auth failure message (blocking)
* **Change**:
  ```python
  # FROM:
  display.print_info("Run 'copilot auth' to authenticate")
  # TO:
  display.print_info("Run 'copilot login' to authenticate")
  ```
* **Success**:
  * Line 139 contains `copilot login` instead of `copilot auth`
* **Research References**:
  * .teambot/auth-message/artifacts/research.md (Lines 122-127) - Source code analysis

### Task 1.4: Update `_check_copilot_authentication_blocking()` exception message

Update the exception handler message in the blocking auth check function.

* **Files**:
  * `src/teambot/cli.py` line 144 - Exception handler message (blocking)
* **Change**:
  ```python
  # FROM:
  display.print_info("Run 'copilot auth' to ensure you're authenticated")
  # TO:
  display.print_info("Run 'copilot login' to ensure you're authenticated")
  ```
* **Success**:
  * Line 144 contains `copilot login` instead of `copilot auth`
* **Research References**:
  * .teambot/auth-message/artifacts/research.md (Lines 122-127) - Source code analysis

### Task 1.5: Update `check_copilot_installed()` installation message

Update the installation guidance message when Copilot CLI is not found.

* **Files**:
  * `src/teambot/cli.py` line 239 - Installation warning message
* **Change**:
  ```python
  # FROM:
  display.print_warning("After installing, authenticate with: copilot auth")
  # TO:
  display.print_warning("After installing, authenticate with: copilot login")
  ```
* **Success**:
  * Line 239 contains `copilot login` instead of `copilot auth`
* **Research References**:
  * .teambot/auth-message/artifacts/research.md (Lines 122-127) - Source code analysis

## Phase 2: Documentation Updates

### Task 2.1: Update README.md

Update the prerequisites section with correct authentication command.

* **Files**:
  * `README.md` line 17 - Prerequisites section
* **Change**:
  ```markdown
  <!-- FROM: -->
  - **GitHub Copilot CLI** - [Install Copilot CLI](https://githubnext.com/projects/copilot-cli/) and authenticate with `copilot auth`
  <!-- TO: -->
  - **GitHub Copilot CLI** - [Install Copilot CLI](https://githubnext.com/projects/copilot-cli/) and authenticate with `copilot login`
  ```
* **Success**:
  * Line 17 contains `copilot login` instead of `copilot auth`
* **Research References**:
  * .teambot/auth-message/artifacts/research.md (Lines 129-131) - Documentation analysis

### Task 2.2: Update installation guide

Update the installation guide with correct authentication commands.

* **Files**:
  * `docs/guides/installation.md` line 17 - Quick start command
  * `docs/guides/installation.md` line 227 - Troubleshooting section
* **Changes**:
  ```markdown
  <!-- Line 17 FROM: -->
  copilot auth  # Authenticate if needed
  <!-- Line 17 TO: -->
  copilot login  # Authenticate if needed

  <!-- Line 227 FROM: -->
  copilot auth
  <!-- Line 227 TO: -->
  copilot login
  ```
* **Success**:
  * Both lines contain `copilot login` instead of `copilot auth`
* **Research References**:
  * .teambot/auth-message/artifacts/research.md (Lines 133-135) - Documentation analysis

## Phase 3: Test Assertion Updates

### Task 3.1: Update test_cli.py assertions

Update test assertions to verify the new `copilot login` output.

* **Files**:
  * `tests/test_cli.py` line 609 - First auth check test
  * `tests/test_cli.py` line 629 - Second auth check test
* **Changes**:
  ```python
  # Line 609 FROM:
  assert "copilot auth" in captured.out.lower()
  # Line 609 TO:
  assert "copilot login" in captured.out.lower()

  # Line 629 FROM:
  assert "copilot auth" in captured.out.lower()
  # Line 629 TO:
  assert "copilot login" in captured.out.lower()
  ```
* **Success**:
  * Both assertions check for `copilot login`
* **Research References**:
  * .teambot/auth-message/artifacts/research.md (Lines 136-139) - Test file analysis

### Task 3.2: Update test_acceptance_validation.py assertions

Update acceptance test assertions and docstring.

* **Files**:
  * `tests/test_acceptance_validation.py` line 118 - Docstring
  * `tests/test_acceptance_validation.py` line 155 - Assertion
  * `tests/test_acceptance_validation.py` line 156 - Error message
  * `tests/test_acceptance_validation.py` line 408 - Assertion
* **Changes**:
  ```python
  # Line 118 (docstring) FROM:
  """AT-002: Unauthenticated user sees clear error with 'copilot auth' guidance.
  # Line 118 TO:
  """AT-002: Unauthenticated user sees clear error with 'copilot login' guidance.

  # Line 155 FROM:
  assert "copilot auth" in captured.out.lower(), (
  # Line 155 TO:
  assert "copilot login" in captured.out.lower(), (

  # Line 156 FROM:
  f"Expected 'copilot auth' guidance in: {captured.out}"
  # Line 156 TO:
  f"Expected 'copilot login' guidance in: {captured.out}"

  # Line 408 FROM:
  assert "copilot auth" in captured.out.lower()
  # Line 408 TO:
  assert "copilot login" in captured.out.lower()
  ```
* **Success**:
  * All 4 occurrences updated to `copilot login`
* **Research References**:
  * .teambot/auth-message/artifacts/research.md (Lines 140-143) - Test file analysis

### Task 3.3: Update test_init_model_config_acceptance.py assertions

Update init model config acceptance test assertions.

* **Files**:
  * `tests/test_init_model_config_acceptance.py` line 115 - First assertion
  * `tests/test_init_model_config_acceptance.py` line 135 - Second assertion
* **Changes**:
  ```python
  # Line 115 FROM:
  assert "not authenticated" in captured.out.lower() or "copilot auth" in captured.out.lower()
  # Line 115 TO:
  assert "not authenticated" in captured.out.lower() or "copilot login" in captured.out.lower()

  # Line 135 FROM:
  assert "copilot auth" in output_lower or "github_token" in output_lower
  # Line 135 TO:
  assert "copilot login" in output_lower or "github_token" in output_lower
  ```
* **Success**:
  * Both assertions check for `copilot login`
* **Research References**:
  * .teambot/auth-message/artifacts/research.md (Lines 145-148) - Test file analysis

### Task 3.4: Update test_model_cache_auto_acceptance.py assertion

Update model cache auto acceptance test assertion.

* **Files**:
  * `tests/test_model_cache_auto_acceptance.py` line 110 - Assertion
* **Change**:
  ```python
  # Line 110 FROM:
  assert "copilot auth" in captured.out.lower()
  # Line 110 TO:
  assert "copilot login" in captured.out.lower()
  ```
* **Success**:
  * Assertion checks for `copilot login`
* **Research References**:
  * .teambot/auth-message/artifacts/research.md (Lines 149-150) - Test file analysis

## Phase 4: Validation

### Task 4.1: Run affected tests

Execute the test suite for all affected test files.

* **Command**:
  ```bash
  uv run pytest tests/test_cli.py tests/test_acceptance_validation.py tests/test_init_model_config_acceptance.py tests/test_model_cache_auto_acceptance.py -v
  ```
* **Success**:
  * All tests pass (exit code 0)
  * No failures or errors
* **Dependencies**:
  * Phase 1 and Phase 3 completion

### Task 4.2: Verify no remaining occurrences

Search for any remaining `copilot auth` strings in the codebase.

* **Command**:
  ```bash
  grep -r "copilot auth" src/ tests/ docs/ README.md
  ```
* **Success**:
  * Command returns no output (empty result)
  * Exit code 1 (no matches found)
* **Dependencies**:
  * Task 4.1 completion

### Task 4.3: Run linting checks

Verify code formatting and linting passes.

* **Commands**:
  ```bash
  uv run ruff check .
  uv run ruff format --check .
  ```
* **Success**:
  * Both commands pass (exit code 0)
  * No formatting or linting errors
* **Dependencies**:
  * Task 4.2 completion

## Dependencies

* Python 3.12+ - Runtime environment
* uv - Package manager for running pytest and ruff
* pytest - Test framework
* ruff - Linter and formatter

## Success Criteria

* All 17 occurrences of `copilot auth` replaced with `copilot login`
* All existing tests pass without changes to test logic
* `grep -r "copilot auth" src/ tests/ docs/ README.md` returns no matches
* `uv run ruff check .` and `uv run ruff format --check .` pass
