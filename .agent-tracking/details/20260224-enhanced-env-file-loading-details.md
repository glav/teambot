<!-- markdownlint-disable-file -->
# Task Details: Enhanced .env File Loading

## Research Reference

**Source Research**: .teambot/enhanced-env-file/artifacts/research.md
**Test Strategy**: .teambot/enhanced-env-file/artifacts/test_strategy.md
**Feature Spec**: .teambot/enhanced-env-file/artifacts/feature_spec.md

---

## Phase 1: Unit Tests (TDD - Write First)

### Task 1.1: Create test file and write tests for `extract_env_args()`

Create `tests/test_env_loader.py` with comprehensive tests for the argument extraction function.

* **Files**:
  * `tests/test_env_loader.py` - NEW: Unit tests for env_loader module
* **Test Cases**:
  ```python
  class TestExtractEnvArgs:
      def test_no_env_args_returns_defaults(self):
          """No env args returns (EnvArgs(None, False), original argv)."""
      
      def test_extract_env_file_with_space(self):
          """--env-file /path extracts correctly."""
      
      def test_extract_env_file_with_equals(self):
          """--env-file=/path extracts correctly."""
      
      def test_extract_no_env_flag(self):
          """--no-env sets no_env=True."""
      
      def test_both_args_extracted(self):
          """Both args extracted (validation happens elsewhere)."""
      
      def test_preserves_other_args(self):
          """Other args remain in cleaned argv."""
      
      def test_env_file_before_command(self):
          """teambot --env-file .env run works."""
      
      def test_env_file_missing_value(self):
          """--env-file at end without value handles gracefully."""
  ```
* **Success**:
  * Tests import from `teambot.env_loader`
  * Tests define expected behavior clearly
  * Tests use pytest assertions
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/research.md (Lines 248-283) - extract_env_args implementation
  * .teambot/enhanced-env-file/artifacts/test_strategy.md (Lines 371-397) - Test patterns
* **Dependencies**:
  * None

---

### Task 1.2: Write tests for `find_env_files()`

Add tests for parent directory traversal logic.

* **Files**:
  * `tests/test_env_loader.py` - Extend with FindEnvFiles tests
* **Test Cases**:
  ```python
  class TestFindEnvFiles:
      def test_no_env_files_returns_empty(self, tmp_path):
          """Returns empty list when no .env files exist."""
      
      def test_finds_cwd_env_file(self, tmp_path):
          """Finds .env in current directory."""
      
      def test_finds_parent_env_file(self, tmp_path):
          """Finds .env in parent when cwd has none."""
      
      def test_finds_both_parent_and_cwd(self, tmp_path):
          """Returns [cwd, parent] when both have .env files."""
      
      def test_stops_at_git_root(self, tmp_path):
          """Stops traversal at directory with .git."""
      
      def test_respects_max_depth(self, tmp_path):
          """Stops after max_depth directories."""
      
      def test_order_is_cwd_to_parent(self, tmp_path):
          """Returns files ordered from cwd (first) to farthest parent (last)."""
  ```
* **Success**:
  * Tests use `tmp_path` fixture for filesystem isolation
  * Tests verify correct file ordering
  * Tests verify traversal limits
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/research.md (Lines 302-339) - find_env_files implementation
  * .teambot/enhanced-env-file/artifacts/test_strategy.md (Lines 403-433) - FindEnvFiles test patterns
* **Dependencies**:
  * None (can run parallel with Task 1.1)

---

### Task 1.3: Write tests for `load_environment()`

Add tests for the main loading function.

* **Files**:
  * `tests/test_env_loader.py` - Extend with LoadEnvironment tests
* **Test Cases**:
  ```python
  class TestLoadEnvironment:
      def test_no_env_skips_loading(self):
          """no_env=True prevents all .env loading."""
      
      def test_explicit_env_file_loads_only_that_file(self, tmp_path):
          """env_file parameter loads only specified file."""
      
      def test_explicit_env_file_not_found_raises(self, tmp_path):
          """env_file pointing to missing file raises FileNotFoundError."""
      
      def test_error_message_contains_path(self, tmp_path):
          """FileNotFoundError message includes the missing path."""
      
      def test_default_loads_from_cwd(self, tmp_path, monkeypatch):
          """Default behavior loads .env from cwd."""
      
      def test_default_merges_parent_files(self, tmp_path, monkeypatch):
          """Default behavior merges parent .env files."""
      
      def test_cwd_overrides_parent_conflicts(self, tmp_path, monkeypatch):
          """CWD .env values override parent .env for same key."""
      
      def test_returns_list_of_loaded_files(self, tmp_path, monkeypatch):
          """Returns list of Path objects for loaded files."""
  ```
* **Success**:
  * Tests mock `load_dotenv` where appropriate
  * Tests verify actual environment variable values for integration tests
  * Tests use `monkeypatch` for environment isolation
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/research.md (Lines 342-391) - load_environment implementation
  * .teambot/enhanced-env-file/artifacts/test_strategy.md (Lines 435-467) - LoadEnvironment test patterns
* **Dependencies**:
  * None (can run parallel with Tasks 1.1, 1.2)

---

## Phase 2: Core Implementation

### Task 2.1: Create `src/teambot/env_loader.py` with module skeleton

Create the new module file with imports and type definitions.

* **Files**:
  * `src/teambot/env_loader.py` - NEW: Environment file loading utilities
* **Implementation**:
  ```python
  """Environment file loading utilities for TeamBot CLI."""
  
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
      """Extract --env-file and --no-env from argv before argparse runs."""
      raise NotImplementedError("Implement in Task 2.2")
  
  
  def find_git_root() -> Path | None:
      """Find the git repository root, or None if not in a repo."""
      raise NotImplementedError("Implement in Task 2.3")
  
  
  def find_env_files(start_dir: Path | None = None, max_depth: int = 10) -> list[Path]:
      """Find .env files from start_dir up to git root or max_depth."""
      raise NotImplementedError("Implement in Task 2.3")
  
  
  def load_environment(
      env_file: Path | None = None,
      no_env: bool = False,
      verbose: bool = False,
  ) -> list[Path]:
      """Load environment variables from .env files."""
      raise NotImplementedError("Implement in Task 2.4")
  ```
* **Success**:
  * Module imports correctly: `from teambot.env_loader import EnvArgs, extract_env_args`
  * Type hints are correct
  * Docstrings describe purpose
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/research.md (Lines 227-240) - Module structure
* **Dependencies**:
  * None

---

### Task 2.2: Implement `extract_env_args()` function

Implement the argument extraction logic.

* **Files**:
  * `src/teambot/env_loader.py` - Replace placeholder with implementation
* **Implementation**:
  ```python
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
              # Missing value - leave for argparse to error
              cleaned.append(arg)
              i += 1
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
  ```
* **Success**:
  * All Task 1.1 tests pass
  * Handles both `--env-file /path` and `--env-file=/path` formats
  * Preserves all non-env arguments in cleaned list
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/research.md (Lines 248-283) - Full implementation
* **Dependencies**:
  * Task 2.1 (module skeleton)

---

### Task 2.3: Implement `find_env_files()` function

Implement parent directory traversal with git root detection.

* **Files**:
  * `src/teambot/env_loader.py` - Implement find_git_root and find_env_files
* **Implementation**:
  ```python
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
      if git_root:
          git_root = git_root.resolve()
      
      env_files = []
      current = start_dir
      depth = 0
      
      while depth < max_depth:
          env_file = current / ".env"
          if env_file.is_file():
              env_files.append(env_file)
          
          # Stop at git root (inclusive - check git root's .env first)
          if git_root and current == git_root:
              break
          
          # Stop at filesystem root
          parent = current.parent
          if parent == current:
              break
          
          current = parent
          depth += 1
      
      return env_files
  ```
* **Success**:
  * All Task 1.2 tests pass
  * Correctly stops at git root
  * Correctly respects max_depth
  * Returns files in cwd-to-parent order
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/research.md (Lines 286-339) - Full implementation
  * .teambot/enhanced-env-file/artifacts/research.md (Lines 478-489) - Git root pattern from existing codebase
* **Dependencies**:
  * Task 2.2

---

### Task 2.4: Implement `load_environment()` function

Implement the main loading function with merge behavior.

* **Files**:
  * `src/teambot/env_loader.py` - Implement load_environment
* **Implementation**:
  ```python
  def load_environment(
      env_file: Path | None = None,
      no_env: bool = False,
      verbose: bool = False,
  ) -> list[Path]:
      """Load environment variables from .env files.
      
      Precedence:
      1. no_env=True → No files loaded
      2. env_file specified → Only that file loaded
      3. Default → cwd .env + parent .env files (merged, cwd wins conflicts)
      
      Args:
          env_file: Explicit path to load (disables auto-discovery)
          no_env: If True, skip all loading
          verbose: If True, log loaded files (reserved for future use)
      
      Returns:
          List of loaded .env file paths (in load order)
      
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
          # First file (farthest parent) sets initial values
          # Subsequent files (closer to cwd) override
          load_dotenv(ef, override=True)
          loaded.append(ef)
      
      # Return in cwd-to-parent order (same as find_env_files)
      return list(reversed(loaded))
  ```
* **Success**:
  * All Task 1.3 tests pass
  * `no_env=True` loads nothing
  * Explicit `env_file` loads only that file
  * Missing explicit file raises FileNotFoundError with path in message
  * Default behavior merges with cwd winning conflicts
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/research.md (Lines 342-391) - Full implementation
  * .teambot/enhanced-env-file/artifacts/research.md (Lines 179-221) - python-dotenv API
* **Dependencies**:
  * Task 2.3

---

## Phase 3: CLI Integration

### Task 3.1: Add `--env-file` and `--no-env` arguments to CLI parser

Modify `create_parser()` to include the new global arguments.

* **Files**:
  * `src/teambot/cli.py` - Modify create_parser function
* **Implementation**:
  1. Add import at top of file:
     ```python
     from teambot.env_loader import EnvArgs, extract_env_args, load_environment
     ```
  2. In `create_parser()`, after line ~529 (after `--no-animation`), add:
     ```python
     # Environment file arguments (mutually exclusive)
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
     ```
* **Success**:
  * `teambot --help` shows `--env-file` and `--no-env` options
  * `teambot --env-file .env --no-env init` fails with "mutually exclusive" error
  * Arguments appear in main parser (not subparsers)
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/research.md (Lines 399-411) - CLI integration pattern
  * .teambot/enhanced-env-file/artifacts/feature_spec.md (Lines 133-148) - CLI interface spec
* **Dependencies**:
  * Phase 2 completion

---

### Task 3.2: Update `main()` function to use `load_environment()`

Replace the current `load_dotenv()` call with the new loading logic.

* **Files**:
  * `src/teambot/cli.py` - Modify main function
* **Implementation**:
  Replace the `main()` function (starting around line 1286):
  ```python
  def main() -> int:
      """Main CLI entry point."""
      # Extract env args BEFORE argparse (they affect env loading)
      env_args, cleaned_argv = extract_env_args()
      
      # Validate mutual exclusivity (belt-and-suspenders - argparse also checks)
      if env_args.env_file and env_args.no_env:
          sys.stderr.write("Error: --env-file and --no-env are mutually exclusive\n")
          return 2
      
      # Load environment variables from .env files
      try:
          load_environment(env_args.env_file, env_args.no_env)
      except FileNotFoundError as e:
          sys.stderr.write(f"Error: {e}\n")
          return 1
      
      # Update sys.argv for argparse (env args already consumed)
      sys.argv = cleaned_argv
      
      parser = create_parser()
      args = parser.parse_args()
      # ... rest of function unchanged
  ```
* **Success**:
  * `teambot --env-file nonexistent.env status` exits with code 1 and clear error
  * `teambot --no-env status` runs without loading any .env files
  * Existing `teambot status` behavior unchanged (loads cwd .env)
  * All existing CLI tests still pass
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/research.md (Lines 413-433) - main() integration
  * .teambot/enhanced-env-file/artifacts/feature_spec.md (Lines 163-168) - Precedence rules
* **Dependencies**:
  * Task 3.1

---

## Phase 4: Integration Tests

### Task 4.1: Add CLI parser tests for new arguments

Extend `tests/test_cli.py` with tests for the new arguments.

* **Files**:
  * `tests/test_cli.py` - Add TestEnvArguments class
* **Test Cases**:
  ```python
  class TestEnvArguments:
      """Tests for --env-file and --no-env CLI arguments."""
  
      def test_parser_accepts_env_file(self):
          """Parser recognizes --env-file argument."""
          from teambot.cli import create_parser
          parser = create_parser()
          args = parser.parse_args(["--env-file", ".env", "init"])
          assert args.env_file == Path(".env")
  
      def test_parser_accepts_no_env(self):
          """Parser recognizes --no-env flag."""
          from teambot.cli import create_parser
          parser = create_parser()
          args = parser.parse_args(["--no-env", "init"])
          assert args.no_env is True
  
      def test_env_file_and_no_env_mutually_exclusive(self):
          """--env-file and --no-env cannot be used together."""
          from teambot.cli import create_parser
          parser = create_parser()
          with pytest.raises(SystemExit):
              parser.parse_args(["--env-file", ".env", "--no-env", "init"])
  
      def test_env_file_works_with_all_commands(self):
          """--env-file works with init, run, status."""
          from teambot.cli import create_parser
          parser = create_parser()
          for cmd in ["init", "status"]:
              args = parser.parse_args(["--env-file", ".env", cmd])
              assert args.env_file == Path(".env")
  ```
* **Success**:
  * All parser tests pass
  * Mutual exclusivity enforced by argparse
* **Research References**:
  * tests/test_cli.py (Lines 1-75) - Existing parser test patterns
  * .teambot/enhanced-env-file/artifacts/test_strategy.md (Lines 336-351) - Parser test examples
* **Dependencies**:
  * Phase 3 completion

---

### Task 4.2: Add end-to-end integration tests

Add tests that validate the full CLI flow with real temp directories.

* **Files**:
  * `tests/test_cli.py` - Extend TestEnvArguments class
* **Test Cases**:
  ```python
  class TestEnvLoadingIntegration:
      """Integration tests for .env loading in CLI."""
  
      def test_main_loads_cwd_env_file(self, tmp_path, monkeypatch):
          """main() loads .env from current directory."""
          (tmp_path / ".env").write_text("INTEGRATION_TEST_VAR=loaded")
          monkeypatch.chdir(tmp_path)
          monkeypatch.delenv("INTEGRATION_TEST_VAR", raising=False)
          
          # Run enough of main to trigger loading
          from teambot.env_loader import load_environment
          load_environment()
          
          assert os.environ.get("INTEGRATION_TEST_VAR") == "loaded"
  
      def test_no_env_flag_prevents_loading(self, tmp_path, monkeypatch):
          """--no-env prevents .env loading."""
          (tmp_path / ".env").write_text("SHOULD_NOT_LOAD=yes")
          monkeypatch.chdir(tmp_path)
          monkeypatch.delenv("SHOULD_NOT_LOAD", raising=False)
          
          from teambot.env_loader import load_environment
          load_environment(no_env=True)
          
          assert os.environ.get("SHOULD_NOT_LOAD") is None
  
      def test_env_file_flag_loads_specific_file(self, tmp_path, monkeypatch):
          """--env-file loads only specified file."""
          custom = tmp_path / "custom.env"
          custom.write_text("CUSTOM_VAR=custom")
          (tmp_path / ".env").write_text("CWD_VAR=cwd")
          monkeypatch.chdir(tmp_path)
          monkeypatch.delenv("CUSTOM_VAR", raising=False)
          monkeypatch.delenv("CWD_VAR", raising=False)
          
          from teambot.env_loader import load_environment
          load_environment(env_file=custom)
          
          assert os.environ.get("CUSTOM_VAR") == "custom"
          assert os.environ.get("CWD_VAR") is None
  ```
* **Success**:
  * Integration tests pass with real filesystem
  * Environment variables correctly loaded/not loaded based on flags
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/test_strategy.md (Lines 471-533) - Acceptance test patterns
* **Dependencies**:
  * Task 4.1

---

## Phase 5: Acceptance Tests

### Task 5.1: Create acceptance test file with AT-001 through AT-008

Create comprehensive acceptance tests matching the specification.

* **Files**:
  * `tests/test_env_loading_acceptance.py` - NEW: Acceptance tests
* **Test Cases**:
  ```python
  """Acceptance tests for enhanced .env file loading feature.
  
  Core logic is tested directly; selective mocking is used for external dependencies.
  """
  
  import os
  from pathlib import Path
  
  import pytest
  
  
  @pytest.mark.acceptance
  class TestEnvLoadingAcceptance:
      """Acceptance test scenarios from feature specification."""
  
      def test_at_001_default_cwd_loading(self, tmp_path, monkeypatch):
          """AT-001: .env loads from current working directory by default."""
          # Setup
          monkeypatch.chdir(tmp_path)
          (tmp_path / ".env").write_text("TEST_VAR=hello")
          monkeypatch.delenv("TEST_VAR", raising=False)
          
          # Execute
          from teambot.env_loader import load_environment
          loaded = load_environment()
          
          # Verify
          assert os.environ.get("TEST_VAR") == "hello"
          assert tmp_path / ".env" in loaded
  
      def test_at_002_parent_directory_merge(self, tmp_path, monkeypatch):
          """AT-002: Parent .env provides defaults, child overrides conflicts."""
          # Setup
          child = tmp_path / "child"
          child.mkdir()
          monkeypatch.chdir(child)
          
          (tmp_path / ".env").write_text("PARENT_VAR=parent\nSHARED_VAR=parent")
          (child / ".env").write_text("CHILD_VAR=child\nSHARED_VAR=child")
          
          for var in ["PARENT_VAR", "CHILD_VAR", "SHARED_VAR"]:
              monkeypatch.delenv(var, raising=False)
          
          # Execute
          from teambot.env_loader import load_environment
          load_environment()
          
          # Verify
          assert os.environ.get("PARENT_VAR") == "parent"
          assert os.environ.get("CHILD_VAR") == "child"
          assert os.environ.get("SHARED_VAR") == "child"  # child wins
  
      def test_at_003_explicit_env_file_path(self, tmp_path, monkeypatch):
          """AT-003: --env-file loads only the specified file."""
          # Setup
          monkeypatch.chdir(tmp_path)
          custom = tmp_path / "custom.env"
          custom.write_text("CUSTOM_VAR=custom")
          (tmp_path / ".env").write_text("CWD_VAR=cwd")
          
          monkeypatch.delenv("CUSTOM_VAR", raising=False)
          monkeypatch.delenv("CWD_VAR", raising=False)
          
          # Execute
          from teambot.env_loader import load_environment
          load_environment(env_file=custom)
          
          # Verify
          assert os.environ.get("CUSTOM_VAR") == "custom"
          assert os.environ.get("CWD_VAR") is None
  
      def test_at_004_env_file_missing_error(self, tmp_path):
          """AT-004: --env-file with missing path raises clear error."""
          missing = tmp_path / "nonexistent.env"
          
          from teambot.env_loader import load_environment
          
          with pytest.raises(FileNotFoundError) as exc_info:
              load_environment(env_file=missing)
          
          assert "nonexistent.env" in str(exc_info.value)
  
      def test_at_005_no_env_disables_loading(self, tmp_path, monkeypatch):
          """AT-005: --no-env prevents all .env loading."""
          # Setup
          monkeypatch.chdir(tmp_path)
          (tmp_path / ".env").write_text("SHOULD_NOT_LOAD=yes")
          monkeypatch.delenv("SHOULD_NOT_LOAD", raising=False)
          
          # Execute
          from teambot.env_loader import load_environment
          loaded = load_environment(no_env=True)
          
          # Verify
          assert os.environ.get("SHOULD_NOT_LOAD") is None
          assert loaded == []
  
      def test_at_006_mutual_exclusivity(self):
          """AT-006: --env-file and --no-env are mutually exclusive in parser."""
          from teambot.cli import create_parser
          
          parser = create_parser()
          with pytest.raises(SystemExit) as exc_info:
              parser.parse_args(["--env-file", ".env", "--no-env", "status"])
          
          assert exc_info.value.code == 2  # argparse error code
  
      def test_at_007_all_commands_support_flags(self):
          """AT-007: --env-file and --no-env work with init, run, status."""
          from teambot.cli import create_parser
          
          parser = create_parser()
          
          # Test with init
          args = parser.parse_args(["--no-env", "init"])
          assert args.no_env is True
          
          # Test with status
          args = parser.parse_args(["--env-file", ".env", "status"])
          assert args.env_file == Path(".env")
  
      # AT-008 (uvx invocation) requires manual verification - documented in Phase 6
  ```
* **Success**:
  * All 7 automated acceptance tests pass
  * Tests marked with `@pytest.mark.acceptance`
  * AT-008 documented for manual verification
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/feature_spec.md (Lines 299-375) - Full AT scenarios
  * .teambot/enhanced-env-file/artifacts/test_strategy.md (Lines 471-533) - Acceptance test patterns
* **Dependencies**:
  * Phase 4 completion

---

## Phase 6: Documentation & Validation

### Task 6.1: Update README.md with new CLI options

Add documentation for the new CLI flags.

* **Files**:
  * `README.md` - Update CLI usage section
* **Content to Add**:
  ```markdown
  ### Environment Configuration
  
  TeamBot automatically loads environment variables from `.env` files:
  
  ```bash
  # Default: loads .env from current directory + parent directories
  teambot run objectives/my-task.md
  
  # Load from specific file only
  teambot --env-file /path/to/.env run objectives/my-task.md
  
  # Disable .env loading (useful for CI)
  teambot --no-env run objectives/my-task.md
  ```
  
  **Precedence**: When multiple `.env` files exist, values are merged with the
  current directory taking precedence over parent directories.
  ```
* **Success**:
  * README documents `--env-file` and `--no-env` options
  * Examples show common use cases
  * Precedence rules explained
* **Research References**:
  * .teambot/enhanced-env-file/artifacts/feature_spec.md (Lines 133-148) - CLI interface spec
* **Dependencies**:
  * Phase 5 completion

---

### Task 6.2: Run full test suite and validate coverage

Run all tests and verify coverage targets are met.

* **Commands**:
  ```bash
  # Run full test suite
  uv run pytest
  
  # Check coverage for new module
  uv run pytest --cov=src/teambot/env_loader --cov-report=term-missing
  
  # Run linting
  uv run ruff check .
  uv run ruff format --check .
  ```
* **Success**:
  * All existing tests pass (no regressions)
  * New `env_loader.py` has 95%+ coverage
  * No linting errors
* **Dependencies**:
  * Task 6.1

---

### Task 6.3: Manual verification of uvx invocation (AT-008)

Manually verify that uvx-installed TeamBot loads .env correctly.

* **Steps**:
  1. Create `.env` file with `UVX_TEST=success`
  2. Run `uvx teambot status` (or install and run via uvx)
  3. Verify environment variable was loaded
* **Success**:
  * `uvx teambot` invocation loads `.env` from cwd
  * Behavior matches direct `teambot` invocation
* **Dependencies**:
  * Task 6.2

---

## Dependencies

* python-dotenv v1.0.0+ (already in pyproject.toml line 17)
* pytest with pytest-cov, pytest-mock (in dev dependencies lines 27-30)
* argparse (Python stdlib)
* pathlib (Python stdlib)
* subprocess (Python stdlib)

## Success Criteria

* All 62 existing CLI tests continue to pass
* New `env_loader.py` module has 95%+ unit test coverage
* All 8 acceptance test scenarios pass (7 automated + 1 manual)
* `--env-file` and `--no-env` work with all commands
* Documentation updated
* Linting passes
