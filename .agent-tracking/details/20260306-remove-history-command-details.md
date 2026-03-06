<!-- markdownlint-disable-file -->

# Task Details: Remove /history Command

**Research Reference**: `.agent-tracking/research/20260306-remove-history-command-research.md`

This document provides detailed implementation instructions for each task in the removal plan.

---

## Phase 1: Remove Command Implementation

### Task 1.1: Delete handle_history() Function

**File**: `src/teambot/repl/commands.py`

**Action**: Delete Lines 167-198 (entire function)

**Current Code** (Lines 167-198 of commands.py, documented in research Lines 195-228):
```python
def handle_history(args: list[str], history: list[dict[str, Any]]) -> CommandResult:
    """Handle /history command.
    
    Args:
        args: Optional agent filter.
        history: Command history list.
        
    Returns:
        CommandResult with history.
    """
    # ... (32 lines of implementation)
```

**After**: Entire function removed

**Verification**: `python -m py_compile src/teambot/repl/commands.py`

---

### Task 1.2: Delete history() Method

**File**: `src/teambot/repl/commands.py`

**Action**: Delete Lines 772-774 (entire method)

**Current Code** (Lines 772-774 of commands.py, documented in research Lines 183-188):
```python
def history(self, args: list[str]) -> CommandResult:
    """Handle /history command."""
    return handle_history(args, self._history)
```

**After**: Entire method removed

**Verification**: Ensure no references to `self.history` remain in class

---

### Task 1.3: Remove Dispatch Entry

**File**: `src/teambot/repl/commands.py`

**Action**: Remove Line 726 from handlers dictionary

**Current Code** (Lines 723-738 of commands.py, documented in research Lines 164-174):
```python
handlers = {
    "help": self.help,
    "status": self.status,
    "history": self.history,  # ❌ REMOVE THIS LINE
    "quit": self.quit,
    "exit": self.quit,  # Alias
    # ... other handlers
}
```

**After**:
```python
handlers = {
    "help": self.help,
    "status": self.status,
    "quit": self.quit,
    "exit": self.quit,  # Alias
    # ... other handlers
}
```

**Verification**: Dictionary syntax remains valid (commas correct)

---

### Task 1.4: Remove Help Text

**File**: `src/teambot/repl/commands.py`

**Action**: Remove Line 115 from help text string

**Current Code** (Lines 97-129 of commands.py, documented in research Lines 234-263):
```python
return CommandResult(
    output=f"""TeamBot v{__version__} (Copilot SDK: {sdk_version})

Available commands:
  # ... other commands ...
  /tokens        - Show session token usage (`/cost` is alias, `-d` for details)
  /history       - Show command history  # ❌ REMOVE THIS LINE
  /quit          - Exit interactive mode
# ... rest of help text ...
```

**After**:
```python
return CommandResult(
    output=f"""TeamBot v{__version__} (Copilot SDK: {sdk_version})

Available commands:
  # ... other commands ...
  /tokens        - Show session token usage (`/cost` is alias, `-d` for details)
  /quit          - Exit interactive mode
# ... rest of help text ...
```

**Verification**: No orphaned `/history` string in help output

---

### Task 1.5: Update Module Docstring

**File**: `src/teambot/repl/commands.py`

**Action**: Update Line 3 to remove `/history`

**Current Code** (Lines 1-4 of commands.py, documented in research Lines 268-276):
```python
"""System commands for TeamBot REPL.

Provides /help, /status, /history, /quit, /tasks, /models, /model commands.
"""
```

**After**:
```python
"""System commands for TeamBot REPL.

Provides /help, /status, /quit, /tasks, /models, /model commands.
"""
```

**Verification**: Docstring syntax valid

---

## Phase 2: Update Test Suite

### Task 2.1: Delete TestHistoryCommand Class

**File**: `tests/test_repl/test_commands.py`

**Action**: Delete entire class (Lines ~101-153, exact range may vary)

**Current Code** (documented in research Lines 540-554):
```python
class TestHistoryCommand:
    """Tests for /history command."""
    
    def test_history_empty(self):
        # ...
    
    def test_history_with_entries(self):
        # ...
    
    def test_history_filter_by_agent(self):
        # ...
    
    def test_history_limit_entries(self):
        # ...
```

**After**: Entire class removed

**Verification**: No syntax errors, remaining test classes intact

---

### Task 2.2: Update Help Test

**File**: `tests/test_repl/test_commands.py`

**Action**: Remove `/history` assertion from `test_help_returns_command_list()` (Line ~29)

**Current Code** (documented in research Lines 560-571):
```python
def test_help_returns_command_list(self):
    """Test /help returns list of commands."""
    result = handle_help([])
    
    assert result.success is True
    assert "@agent" in result.output
    assert "/help" in result.output
    assert "/status" in result.output
    assert "/history" in result.output  # ❌ REMOVE THIS ASSERTION
    assert "/quit" in result.output
```

**After**: Remove the `/history` assertion line

**Verification**: Test still passes with assertion removed

---

### Task 2.3: Delete Dispatch Test

**File**: `tests/test_repl/test_commands.py`

**Action**: Delete `test_dispatch_history()` method (Lines ~208-213)

**Current Code** (documented in research Lines 591-598):
```python
async def test_dispatch_history(self):
    """Test dispatching /history."""
    commands = SystemCommands()
    result = await commands.dispatch("history", [])
    
    assert result.success is True
```

**After**: Entire method removed

**Verification**: Remaining dispatch tests intact

---

### Task 2.4: Update Parser Tests

**File**: `tests/test_repl/test_parser.py`

**Action**: Delete or modify 3 test methods using `/history` as examples (Lines 113-149)

**Option A - Delete** (documented in research Lines 605-614):
```python
# DELETE:
def test_parse_history_command(self):
    """Test parsing /history command."""
    result = parse_command("/history")
    
    assert result.type == CommandType.SYSTEM
    assert result.command == "history"
    assert result.args == []
```

**Option B - Modify** (documented in research Lines 616-625):
```python
# CHANGE TO:
def test_parse_tasks_command(self):
    """Test parsing /tasks command."""
    result = parse_command("/tasks")
    
    assert result.type == CommandType.SYSTEM
    assert result.command == "tasks"
    assert result.args == []
```

**Recommendation**: Use Option A (delete) if test coverage is redundant; use Option B if test structure is valuable.

Apply same approach to:
- `test_parse_command_with_args` (Lines ~135-141)
- `test_parse_command_with_multiple_args` (Lines ~143-149)

**Verification**: All parser tests pass after changes

---

### Task 2.5: Run Full Test Suite

**Action**: Execute REPL test suite and verify all tests pass

**Commands**:
```bash
# Run REPL tests
uv run pytest tests/test_repl/ -v

# Expected: All tests pass, no failures
```

**Success Criteria**:
- Zero test failures
- Zero syntax errors
- Test count decreased by number of deleted tests (4-7 tests)

**Verification**: Console output shows "X passed"

---

## Phase 3: Update Documentation

### Task 3.1: Update Interactive Mode Spec

**File**: `docs/feature-specs/teambot-interactive-mode.md`

**Actions** (documented in research Lines 692-709):

1. **Line ~79**: Update system commands table
   ```markdown
   <!-- BEFORE -->
   | System Commands | `/help`, `/status`, `/history`, `/quit` | P0 |
   
   <!-- AFTER -->
   | System Commands | `/help`, `/status`, `/quit` | P0 |
   ```

2. **Lines ~165-166**: Delete command example rows
   ```markdown
   <!-- DELETE THESE LINES -->
   | `/history` | Show recent actions | `/history` |
   | `/history <agent>` | Show agent-specific history | `/history builder-1` |
   ```

3. **Line ~185**: Update functional requirement
   ```markdown
   | FR-IM-004 | System Commands | Implement `/help`, `/status`, `/quit` | P0 | All commands work as documented |
   ```

4. **Lines ~304-305**: Remove from help text example
   ```markdown
   <!-- DELETE THESE LINES -->
   /history             - Show recent actions (all agents)
   /history <agent>     - Show history for specific agent
   ```

**Verification**: No `/history` references remain in file

---

### Task 3.2: Update Stages Cleanup Doc

**File**: `docs/feature-specs/file-orchestration-stages-cleanup.md`

**Action**: Remove Line ~178 from active commands table (documented in research Lines 722-730)

```markdown
<!-- DELETE THIS ROW -->
| `/history` | ✅ Active | Shows command history |
```

**Verification**: No `/history` command references remain

---

### Task 3.3: Check Architecture Guide

**File**: `docs/guides/architecture.md`

**Action**: Check Line ~279 and remove ONLY if it's about the command (documented in research Lines 714-720)

**Decision Logic**:
- If text says: `.teambot/{feature}/history/` → **KEEP** (directory path)
- If text says: `/history command` → **REMOVE**

**Verification**: Use grep to check for any command references

---

### Task 3.4: Verify No Orphaned References

**Action**: Search for remaining `/history` references

**Commands** (documented in research Lines 735-740):
```bash
# Search docs for /history command references
grep -r "/history" docs/ | grep -v ".teambot/history/" | grep -v "node_modules"

# Expected: Zero matches (or only this objective's spec file)
```

**Success Criteria**: No `/history` command references in documentation

**Note**: References to `.teambot/history/` directory are acceptable (workflow artifacts, not command)

---

## Phase 4: Integration Verification

### Task 4.1: Test Unknown Command Handling

**Action**: Manually test that `/history` returns unknown command error

**Test Steps**:
1. Start TeamBot REPL: `uv run teambot`
2. Enter command: `/history`
3. Expected output: `Unknown command: /history. Type /help for available commands.`

**Code Reference** (documented in research Lines 469-479):
The existing unknown command handler (Lines 742-745 of commands.py) automatically handles unregistered commands:
```python
if handler is None:
    return CommandResult(
        output=f"Unknown command: /{command}. Type /help for available commands.",
        success=False,
    )
```

**Verification**: Error message displayed correctly

---

### Task 4.2: Verify Help Output

**Action**: Verify `/help` no longer lists `/history`

**Test Steps**:
1. In REPL, enter: `/help`
2. Check output for `/history` string
3. Expected: No `/history` in output

**Verification**: `/history` absent from help text

---

### Task 4.3: Run Full Test Suite

**Action**: Execute complete test suite with coverage

**Commands**:
```bash
# Run all tests with coverage
uv run pytest --cov=src/teambot --cov-report=term-missing

# Expected: 1050 tests pass (minus deleted tests), 80% coverage maintained
```

**Success Criteria**:
- All tests pass
- Coverage ≥ 80%
- No test failures related to `/history` removal

**Verification**: Console output shows "X passed" with no failures

---

### Task 4.4: Verify No Broken References

**Action**: Check for any broken imports or undefined references

**Commands**:
```bash
# Check for imports of handle_history
grep -r "handle_history" src/ tests/

# Check for calls to .history() method
grep -r "\.history(" src/ tests/

# Expected: Zero matches
```

**Success Criteria**: No references to removed code remain

**Verification**: Grep returns no results

---

## Success Criteria Summary

All tasks complete when:
- [ ] All code references to `/history` removed from `src/teambot/repl/commands.py`
- [ ] `/history` absent from `/help` output
- [ ] All tests pass (1050 tests minus deleted tests)
- [ ] No broken imports or references
- [ ] Documentation has zero `/history` command references
- [ ] `/history` returns "Unknown command" error
- [ ] History tracking infrastructure (`.teambot/history/`) untouched

## Preserved Components

**DO NOT REMOVE** (documented in research Lines 308-326):
- `AgentRouter._history` list (used for tracking)
- `AgentRouter.get_history()` method
- `SystemCommands.set_history()` method
- `SystemCommands._history` attribute
- History recording logic in router
- `test_history_shared_with_commands` test (tests integration, not command)

These components support the history tracking infrastructure for workflow artifacts, which is separate from the `/history` command.
