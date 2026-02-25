# Objective: Enhanced .env File Loading

## Objective

**Goal**: Improve `.env` file loading to work reliably when TeamBot is invoked via `uvx` or from subdirectories, and allow explicit `.env` file path specification via CLI argument.

**Problem Statement**: When TeamBot is installed and invoked via `uvx --from git+https://...`, the current `load_dotenv()` call may not reliably find `.env` files in the user's current working directory. Additionally, users invoking TeamBot from a subdirectory (e.g., `./src/app/`) cannot easily load a `.env` file from the project root.

**Success Criteria**:
- [ ] `.env` files are loaded from the current working directory when present
- [ ] Parent directory `.env` files can provide additional variables not in cwd `.env` (merge behavior)
- [ ] New `--env-file` CLI argument allows explicit `.env` file path specification
- [ ] New `--no-env` CLI flag disables all `.env` file loading (useful for CI)
- [ ] `--env-file` and `--no-env` arguments work with all commands (init, run, status)
- [ ] Clear error message if `--env-file` path does not exist
- [ ] Existing functionality and tests continue to pass
- [ ] Documentation updated to describe new `--env-file` and `--no-env` options
- [ ] Manual verification that `uvx`-invoked TeamBot loads `.env` from cwd

---

## Technical Context

**Target Codebase**: `/workspaces/teambot/src/teambot/cli.py`

**Primary Language/Framework**: Python / argparse

**Testing Preference**: TDD

**Key Constraints**:
- Must maintain backward compatibility with existing behavior
- `.env` loading must happen before any config parsing
- `--env-file` should be a global argument available to all subcommands
- If `--env-file` is specified but file doesn't exist, fail with clear error
- If `--env-file` is not specified, use default behavior (cwd + parent search)

---

## Implementation Guidance

### CLI Arguments

Add global/parent-level arguments:
```
--env-file PATH    Path to .env file to load (default: auto-detect from cwd)
--no-env           Disable .env file loading entirely (useful for CI environments)
```

Note: `--env-file` and `--no-env` are mutually exclusive.

### Loading Logic

1. If `--no-env` is provided:
   - Skip all `.env` loading entirely
2. If `--env-file` is provided:
   - Verify file exists; if not, exit with error message
   - Call `load_dotenv(path)` with the explicit path only (no parent search)
3. If neither flag is provided (default behavior):
   - First, call `load_dotenv(Path.cwd() / ".env")` to explicitly load from cwd
   - Then, call `load_dotenv()` with `override=False` to allow parent directory search
   - This merges variables: cwd `.env` takes precedence, parent `.env` provides additional vars not already set

**Precedence Behavior**: When both cwd and parent `.env` files exist, variables in cwd `.env` take precedence. Variables defined only in parent `.env` are still loaded (merge, not replace).

### Edge Cases to Handle

- `--env-file` with relative path (should resolve relative to cwd)
- `--env-file` with absolute path
- `.env` file with syntax errors (let python-dotenv handle naturally)
- Running from symlinked directories
- `--env-file` and `--no-env` used together (should error with clear message)

### Implementation Note: Argument Parsing Timing

Currently, `load_dotenv()` is called **before** `parser.parse_args()` in `main()`. To support `--env-file` and `--no-env`, the implementation must either:

1. **Pre-parse** these specific arguments before full parsing (e.g., scan `sys.argv` for `--env-file` or `--no-env`), OR
2. **Move** the `load_dotenv()` call to after `parse_args()` but before command dispatch

Option 1 is recommended to maintain the current flow where env vars are available during all argument processing.

---

## Additional Context

**Use Case Example**:
```bash
# User has alias:
alias teambot='uvx --from git+https://github.com/glav/teambot teambot'

# Running from project root - should auto-detect .env
cd /projects/myapp
teambot run objectives/feature.md

# Running from subdirectory - needs explicit path
cd /projects/myapp/src/components
teambot --env-file ../../.env run objectives/feature.md

# Or with absolute path
teambot --env-file /projects/myapp/.env run objectives/feature.md
```

**Related Files**:
- `src/teambot/cli.py` - Main CLI entry point, `main()` function, `create_parser()`
- `tests/test_cli.py` - CLI tests

**Dependencies**:
- `python-dotenv` (already installed)

---

## Acceptance Testing

### uvx Simulation Test

Create an acceptance test that validates the primary use case:

1. Create a temporary directory with a `.env` file containing test variables
2. Simulate running TeamBot from that directory (set `os.getcwd()` context)
3. Verify the env vars from `.env` are loaded
4. This validates the fix works regardless of package installation location

### Test Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| `.env` in cwd only | Variables loaded from cwd |
| `.env` in parent only | Variables loaded from parent (default search) |
| `.env` in both cwd and parent | Merge: cwd takes precedence, parent fills gaps |
| `--env-file /path/to/.env` | Only specified file loaded |
| `--env-file missing.env` | Exit with error: "Error: .env file not found: missing.env" |
| `--no-env` | No `.env` loading, env vars from shell only |
| `--env-file X --no-env` | Exit with error: mutually exclusive arguments |
| No `.env` anywhere | Silent no-op (current behavior preserved) |
