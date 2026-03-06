<!-- markdownlint-disable-file -->
# Task Research Document: Remove /history Command

This research document provides comprehensive analysis for removing the unused `/history` command from TeamBot REPL. The command is redundant (shell provides native history), adds maintenance overhead, and is not used in production workflows.

## Task Implementation Requests
* Remove `handle_history()` function from `src/teambot/repl/commands.py` (Lines 167-198)
* Remove `history()` method from `SystemCommands` class (Lines 772-774)
* Remove `"history": self.history` entry from dispatch handlers dictionary (Line 726)
* Remove `/history` from help text in `handle_help()` function (Line 115)
* Remove or update 4 test methods in `TestHistoryCommand` class
* Remove or update 4 test methods related to `/history` parsing in `test_parser.py`
* Remove or update 1 test method in `test_loop.py` about history sharing
* Remove or update 1 test method in `test_commands.py` about dispatching history
* Remove assertion checking for `/history` in help output (Line 29 of test_commands.py)
* Remove `/history` references from 3 documentation files
* Update module docstring to remove mention of `/history` (Line 3 of commands.py)

## Scope and Success Criteria
* **Scope**: Remove all code, tests, and documentation related to the `/history` REPL command while preserving other functionality
* **Assumptions**:
  * The `/history` command has zero or near-zero production usage
  * No production workflows depend on `/history` output
  * The history tracking infrastructure (`.teambot/history/` directory for workflow artifacts) is separate and should remain
  * All other REPL commands must remain functional after removal
* **Success Criteria**:
  * ✅ All code references to `/history` command removed from `src/teambot/repl/commands.py`
  * ✅ `/history` no longer appears in `/help` command output
  * ✅ All tests pass after removal (except tests explicitly testing `/history`)
  * ✅ No broken imports or references remain
  * ✅ Documentation contains zero references to `/history` command
  * ✅ Attempting to use `/history` returns "Unknown command" error

## Outline
1. **Testing Infrastructure Research** - Test framework, patterns, coverage requirements
2. **Entry Point Analysis** - All code paths where `/history` can be invoked
3. **Code Architecture** - Implementation details and dependencies
4. **Documentation References** - All docs mentioning `/history`
5. **Testing Strategy** - Code-First approach with targeted test updates
6. **Implementation Guidance** - Step-by-step removal plan

### Potential Next Research
* No additional research required - all implementation details are documented below

## Research Executed

### Testing Infrastructure Research
* **Framework**: pytest 9.0.2 with pytest-asyncio 1.3.0
  * **Location**: `tests/` directory (mirrors `src/` structure)
  * **Naming**: `test_*.py` pattern with `Test*` classes
  * **Runner**: `uv run pytest` (from pyproject.toml)
  * **Coverage**: pytest-cov with `--cov=src/teambot --cov-report=term-missing` flags
  * **Async Support**: `asyncio_mode = "auto"` for automatic async test handling

### Test Patterns Found
* **File**: `tests/test_repl/test_commands.py` (Lines 1-220)
  * Uses `unittest.mock.MagicMock` for mocking dependencies
  * Test classes group related tests (e.g., `TestHistoryCommand`)
  * Direct instantiation of `SystemCommands()` for testing
  * Manual setting of internal state (e.g., `commands._history = []`)
  * Assertion patterns check both `result.success` and output content
  * Async tests use `@pytest.mark.asyncio` decorator and `async def`
  
* **File**: `tests/test_repl/test_parser.py` (Lines 113-149)
  * Tests command parsing with `parse_command()` function
  * Checks `result.type`, `result.command`, `result.args` attributes
  * Tests both simple commands and commands with arguments
  * No mocking required (pure parsing logic)

* **File**: `tests/test_repl/test_loop.py` (Lines 193-201)
  * Tests integration between components (router and commands)
  * Creates `REPLLoop()` instance and manipulates internal state
  * Verifies shared state between components

### Coverage Standards
* **General Coverage Target**: 80% (based on existing test suite achieving ~80% coverage as documented in AGENTS.md)
* **Critical Paths**: All command dispatch paths must remain covered
* **Test Update Strategy**: Remove tests specifically for `/history`; ensure other tests still pass

### Testing Approach Recommendation
* **Command Removal**: Code-First (straightforward deletion)
* **Help Text Update**: Code-First (simple string removal)
* **Test Updates**: Code-First (remove obsolete tests)
* **Integration Verification**: Code-First (run existing test suite)

**Rationale**: This is a pure deletion task with well-defined scope. The feature being removed has comprehensive test coverage, so removing those tests and verifying the remaining suite passes is sufficient. No new logic is being added that would benefit from TDD.

## Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| Direct command: `/history` | `loop.py:run()` → `parser.py:parse_command()` → `router.py:route()` → `commands.py:dispatch()` → `commands.py:history()` → `commands.py:handle_history()` | ✅ YES | ✅ YES - Remove handler |
| Direct command with args: `/history pm` | Same as above with args passed through | ✅ YES | ✅ YES - Remove handler |
| Help listing: `/help` | `loop.py:run()` → `commands.py:dispatch()` → `commands.py:help()` → `commands.py:handle_help()` | ✅ YES (displays `/history`) | ✅ YES - Remove from help text |

### Code Path Trace

#### Entry Point 1: Direct `/history` Command
1. User enters: `/history`
2. Handled by: `src/teambot/repl/loop.py:REPLLoop.run()` (reads user input)
3. Routes to: `src/teambot/repl/parser.py:parse_command()` (Lines ~113-119) - parses as `CommandType.SYSTEM` with `command="history"`
4. Routes to: `src/teambot/repl/router.py:route()` - dispatches to system handler
5. Routes to: `src/teambot/repl/commands.py:SystemCommands.dispatch()` (Lines 711-751) - looks up `"history"` in handlers dict (Line 726)
6. Routes to: `src/teambot/repl/commands.py:SystemCommands.history()` (Lines 772-774) - wrapper method
7. Reaches: `src/teambot/repl/commands.py:handle_history()` (Lines 167-198) ✅ **TARGET FOR REMOVAL**

#### Entry Point 2: `/history` with Agent Filter
1. User enters: `/history pm`
2. Same path as Entry Point 1, but `args=["pm"]` passed through all layers
3. Reaches: `handle_history(args=["pm"], history)` which filters results ✅ **TARGET FOR REMOVAL**

#### Entry Point 3: Help Text Display
1. User enters: `/help`
2. Routes to: `commands.py:handle_help()` (Lines 42-130)
3. Line 115 contains: `  /history       - Show command history` ✅ **TARGET FOR REMOVAL**
4. Help text displayed to user showing `/history` as available command

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| ❌ None identified | All entry points traced | All code paths covered by implementation plan |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that trigger `/history` feature are identified  
- [x] Coverage gaps documented (none found)
- [x] Implementation scope covers all entry points

**Entry Point Analysis Result**: ✅ **COMPLETE** - All `/history` invocation paths identified and removal strategy covers all entry points.

## Key Discoveries

### Project Structure

**REPL Command Architecture** (`src/teambot/repl/`):
```
src/teambot/repl/
├── commands.py       # System command handlers (MODIFY)
├── loop.py          # Main REPL loop (NO CHANGES NEEDED)
├── parser.py        # Command parsing (parser works generically - NO CHANGES for history removal)
└── router.py        # Command routing (NO CHANGES NEEDED)
```

**Key Files to Modify**:
1. ✅ `src/teambot/repl/commands.py` - Remove handler function, method, and help text
2. ✅ `tests/test_repl/test_commands.py` - Remove/update test methods
3. ✅ `tests/test_repl/test_parser.py` - Remove/update parsing tests
4. ✅ `tests/test_repl/test_loop.py` - Remove/update integration tests
5. ✅ `docs/feature-specs/teambot-interactive-mode.md` - Remove `/history` references
6. ✅ `docs/feature-specs/file-orchestration-stages-cleanup.md` - Remove `/history` references  
7. ✅ `docs/guides/architecture.md` - Remove `/history` references

### Implementation Patterns

#### ✅ **Pattern 1: Command Handler Registration**

Commands are registered in the `SystemCommands.dispatch()` method via a handlers dictionary:

```python
# src/teambot/repl/commands.py (Lines 723-738)
handlers = {
    "help": self.help,
    "status": self.status,
    "history": self.history,  # ❌ REMOVE THIS LINE
    "quit": self.quit,
    "exit": self.quit,  # Alias
    "tasks": self.tasks,
    # ... other handlers ...
}
```

**Implementation**: Remove `"history": self.history,` from the dictionary (Line 726).

#### ✅ **Pattern 2: Command Handler Method**

Each command has a method in `SystemCommands` class that delegates to a standalone function:

```python
# src/teambot/repl/commands.py (Lines 772-774)
def history(self, args: list[str]) -> CommandResult:
    """Handle /history command."""
    return handle_history(args, self._history)
```

**Implementation**: Delete the entire `history()` method (Lines 772-774).

#### ✅ **Pattern 3: Standalone Handler Function**

The actual implementation lives in a standalone function:

```python
# src/teambot/repl/commands.py (Lines 167-198)
def handle_history(args: list[str], history: list[dict[str, Any]]) -> CommandResult:
    """Handle /history command.
    
    Args:
        args: Optional agent filter.
        history: Command history list.
        
    Returns:
        CommandResult with history.
    """
    if not history:
        return CommandResult(output="No command history.")
    
    # Filter by agent if specified
    if args:
        agent_filter = args[0]
        history = [h for h in history if h.get("agent_id") == agent_filter]
        if not history:
            return CommandResult(output=f"No history for agent: {agent_filter}")
    
    # Show last 20 entries
    entries = history[-20:]
    lines = ["Command History:", ""]
    for entry in entries:
        agent = entry.get("agent_id", "?")
        content = entry.get("content", "")
        # Truncate long content
        if len(content) > 50:
            content = content[:47] + "..."
        lines.append(f"  @{agent:12} {content}")
    
    return CommandResult(output="\n".join(lines))
```

**Implementation**: Delete the entire `handle_history()` function (Lines 167-198).

#### ✅ **Pattern 4: Help Text Entry**

Commands are documented in the help text string:

```python
# src/teambot/repl/commands.py (Lines 97-129)
return CommandResult(
    output=f"""TeamBot v{__version__} (Copilot SDK: {sdk_version})

Available commands:
  @agent <task>  - Send task to agent (pm, ba, writer, builder-1, builder-2, reviewer)
  @notify <msg>  - Send notification to all channels (use in pipelines)
  /help          - Show this help message
  /help agent    - Show agent-specific help
  /help parallel - Show parallel execution help
  /status        - Show agent status with models
  /models        - List available AI models
  /model <a> <m> - Set model for agent in session
  /tasks         - List running/completed tasks
  /task <id>     - View task details
  /cancel <id>   - Cancel pending task
  /use-agent <id> - Set default agent for plain text input
  /reset-agent   - Reset default agent to config value
  /tokens        - Show session token usage (`/cost` is alias, `-d` for details)
  /history       - Show command history  # ❌ REMOVE THIS LINE
  /quit          - Exit interactive mode
# ... rest of help text ...
```

**Implementation**: Remove Line 115: `  /history       - Show command history`

#### ✅ **Pattern 5: Module Docstring**

Module docstrings document available commands:

```python
# src/teambot/repl/commands.py (Lines 1-4)
"""System commands for TeamBot REPL.

Provides /help, /status, /history, /quit, /tasks, /models, /model commands.
"""
```

**Implementation**: Remove `/history` from Line 3 docstring.

### Complete Examples

#### Example 1: Command Removal Flow

**Before Removal**:
```python
# User types: /history pm
# 1. Parser recognizes system command
# 2. Router dispatches to SystemCommands.dispatch()
# 3. Dispatch looks up "history" in handlers dict
# 4. Calls self.history(["pm"])
# 5. history() calls handle_history(["pm"], self._history)
# 6. Returns formatted history output
```

**After Removal**:
```python
# User types: /history pm
# 1. Parser recognizes system command
# 2. Router dispatches to SystemCommands.dispatch()
# 3. Dispatch looks up "history" in handlers dict → NOT FOUND
# 4. Returns: CommandResult(output="Unknown command: /history. Type /help for available commands.", success=False)
```

Source: `src/teambot/repl/commands.py:742-745` (unknown command handler)

#### Example 2: History Sharing Pattern (UNAFFECTED)

**Important**: The history tracking infrastructure used by other commands remains unchanged:

```python
# src/teambot/repl/loop.py (Lines 96-97)
# Share history with commands
self._commands.set_history(self._router._history)
```

This pattern allows `SystemCommands` to access the command history for the `/history` command. After removal:
- ✅ The `_history` attribute remains on both `AgentRouter` and `SystemCommands`
- ✅ History is still tracked for other purposes (e.g., potential future features)
- ✅ The `set_history()` method can remain (harmless) or be removed in a separate cleanup

**Do NOT remove**:
- `AgentRouter._history` list (used for tracking)
- `AgentRouter.get_history()` method
- `SystemCommands.set_history()` method
- `SystemCommands._history` attribute
- History recording logic in router

Source: `src/teambot/repl/router.py` (history tracking methods)

### API and Schema Documentation

#### CommandResult Schema

All command handlers return `CommandResult`:

```python
@dataclass
class CommandResult:
    """Result from a system command.
    
    Attributes:
        output: Text output to display.
        success: Whether command succeeded.
        should_exit: Whether REPL should exit.
    """
    output: str
    success: bool = True
    should_exit: bool = False
```

Source: `src/teambot/repl/commands.py:27-39`

No changes required to this schema.

### Configuration Examples

No configuration files require changes for this removal. The `/history` command has no configuration dependencies.

## Technical Scenarios

### 1. Remove `/history` Command Implementation

Remove all code implementing the `/history` command from the REPL while preserving all other functionality.

**Requirements:**
* Remove handler function, method, and dispatch registration
* Remove help text reference
* Preserve all other REPL commands
* Ensure unknown command error is returned if user tries `/history`

**Preferred Approach:**
Code-First deletion with verification via existing test suite.

```text
src/teambot/repl/commands.py
├── Delete lines 167-198 (handle_history function)
├── Delete lines 772-774 (history method)
├── Delete line 726 ("history": self.history entry)
├── Delete line 115 (/history help text)
└── Update line 3 (module docstring - remove /history)
```

**Mermaid Diagram: Command Dispatch Flow After Removal**

```mermaid
sequenceDiagram
    participant User
    participant Loop as REPLLoop
    participant Parser
    participant Router
    participant Commands as SystemCommands
    
    User->>Loop: /history
    Loop->>Parser: parse_command("/history")
    Parser->>Router: CommandType.SYSTEM, "history", []
    Router->>Commands: dispatch("history", [])
    
    Note over Commands: handlers.get("history")<br/>returns None
    
    Commands->>Router: CommandResult(output="Unknown command", success=False)
    Router->>Loop: Error result
    Loop->>User: "Unknown command: /history"
```

**Implementation Details:**

**Step 1: Remove Handler Function**

Delete Lines 167-198 in `src/teambot/repl/commands.py`:

```python
# DELETE THIS ENTIRE FUNCTION:
def handle_history(args: list[str], history: list[dict[str, Any]]) -> CommandResult:
    # ... (32 lines total)
```

**Step 2: Remove Method Wrapper**

Delete Lines 772-774 in `src/teambot/repl/commands.py`:

```python
# DELETE THIS METHOD:
def history(self, args: list[str]) -> CommandResult:
    """Handle /history command."""
    return handle_history(args, self._history)
```

**Step 3: Remove Dispatch Registration**

Remove Line 726 in `src/teambot/repl/commands.py`:

```python
handlers = {
    "help": self.help,
    "status": self.status,
    # "history": self.history,  # ❌ DELETE THIS LINE
    "quit": self.quit,
    # ...
}
```

**Step 4: Remove Help Text**

Remove Line 115 in `src/teambot/repl/commands.py`:

```python
  /tokens        - Show session token usage (`/cost` is alias, `-d` for details)
  # /history       - Show command history  # ❌ DELETE THIS LINE
  /quit          - Exit interactive mode
```

**Step 5: Update Module Docstring**

Update Line 3 in `src/teambot/repl/commands.py`:

```python
# BEFORE:
"""System commands for TeamBot REPL.

Provides /help, /status, /history, /quit, /tasks, /models, /model commands.
"""

# AFTER:
"""System commands for TeamBot REPL.

Provides /help, /status, /quit, /tasks, /models, /model commands.
"""
```

**Step 6: Verify Unknown Command Handling**

The existing unknown command handler (Lines 742-745) will automatically handle `/history`:

```python
if handler is None:
    return CommandResult(
        output=f"Unknown command: /{command}. Type /help for available commands.",
        success=False,
    )
```

No changes needed here - this already handles any unregistered command.

#### Considered Alternatives (Removed After Selection)

**Alternative 1: Deprecate with Warning** - Not selected because:
- Command has zero usage (no user impact)
- No migration path needed
- Clean removal is simpler than deprecation cycle

**Alternative 2: Keep for Future Use** - Not selected because:
- No planned future use identified
- Shell provides better native history (up/down arrows, Ctrl+R)
- Maintenance burden not justified by speculative value

### 2. Update Test Suite

Remove tests specifically for `/history` command and update tests that assert its presence in help output.

**Requirements:**
* Remove 4 test methods in `TestHistoryCommand` class
* Remove 3 test methods in `test_parser.py` for `/history` parsing
* Update test asserting `/history` in help output
* Remove integration test for history sharing (or keep if other commands need it)
* Remove dispatch test for `/history`
* Ensure remaining tests pass

**Preferred Approach:**
Code-First test removal with full test suite verification.

```text
tests/test_repl/test_commands.py
├── DELETE TestHistoryCommand class (Lines 101-153)
│   ├── test_history_empty
│   ├── test_history_with_entries
│   ├── test_history_filter_by_agent
│   └── test_history_limit_entries
├── UPDATE test_help_returns_command_list (Line 29)
│   └── Remove assertion: assert "/history" in result.output
└── DELETE test_dispatch_history (Lines 208-213)

tests/test_repl/test_parser.py
├── DELETE test_parse_history_command (Lines 113-119)
├── UPDATE test_parse_command_with_args (Lines 135-141)
│   └── Change from /history to different command example
└── UPDATE test_parse_command_with_multiple_args (Lines 143-149)
    └── Change from /history to different command example

tests/test_repl/test_loop.py
└── EVALUATE test_history_shared_with_commands (Lines 193-201)
    └── Remove if only used for /history command
```

**Implementation Details:**

**Step 1: Remove TestHistoryCommand Class**

Delete entire class from `tests/test_repl/test_commands.py` (Lines ~101-153):

```python
# DELETE THIS ENTIRE CLASS:
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

**Step 2: Update Help Test**

Modify Line 29 in `tests/test_repl/test_commands.py`:

```python
# BEFORE:
def test_help_returns_command_list(self):
    """Test /help returns list of commands."""
    result = handle_help([])
    
    assert result.success is True
    assert "@agent" in result.output
    assert "/help" in result.output
    assert "/status" in result.output
    assert "/history" in result.output  # ❌ REMOVE THIS ASSERTION
    assert "/quit" in result.output

# AFTER:
def test_help_returns_command_list(self):
    """Test /help returns list of commands."""
    result = handle_help([])
    
    assert result.success is True
    assert "@agent" in result.output
    assert "/help" in result.output
    assert "/status" in result.output
    # /history assertion removed - command no longer exists
    assert "/quit" in result.output
```

**Step 3: Remove Dispatch Test**

Delete `test_dispatch_history` method from `tests/test_repl/test_commands.py` (Lines ~208-213):

```python
# DELETE THIS TEST:
async def test_dispatch_history(self):
    """Test dispatching /history."""
    commands = SystemCommands()
    result = await commands.dispatch("history", [])
    
    assert result.success is True
```

**Step 4: Update Parser Tests**

In `tests/test_repl/test_parser.py`:

**Option A** - Delete test (if not reusable):
```python
# DELETE Lines 113-119:
def test_parse_history_command(self):
    """Test parsing /history command."""
    result = parse_command("/history")
    
    assert result.type == CommandType.SYSTEM
    assert result.command == "history"
    assert result.args == []
```

**Option B** - Modify to test different command (if test structure is valuable):
```python
# MODIFY Lines 113-119:
def test_parse_tasks_command(self):
    """Test parsing /tasks command."""
    result = parse_command("/tasks")
    
    assert result.type == CommandType.SYSTEM
    assert result.command == "tasks"
    assert result.args == []
```

Similar updates for `test_parse_command_with_args` (Lines 135-141) and `test_parse_command_with_multiple_args` (Lines 143-149) - either delete or change to test `/status pm` or similar.

**Step 5: Evaluate History Sharing Test**

Check if `test_history_shared_with_commands` in `tests/test_repl/test_loop.py` (Lines 193-201) is only for `/history` command:

```python
async def test_history_shared_with_commands(self):
    """Test history is shared between router and commands."""
    repl = REPLLoop()
    
    # Add to router history
    repl._router._history.append({"agent_id": "pm", "content": "test"})
    
    # Should be visible in commands
    assert len(repl._commands._history) == 1
```

**Decision**: ✅ **KEEP THIS TEST** - It verifies the integration between router and commands for history tracking, which may be used by other features in the future. It's not testing `/history` command functionality, just the shared state pattern.

**Step 6: Run Full Test Suite**

```bash
uv run pytest tests/test_repl/ -v
```

Ensure all remaining tests pass after removals.

#### Considered Alternatives (Removed After Selection)

No alternatives - straightforward test removal is the only approach.

### 3. Update Documentation

Remove all references to `/history` command from documentation files.

**Requirements:**
* Remove `/history` from interactive mode feature spec
* Remove `/history` from architecture guide
* Remove `/history` from stages cleanup doc
* Preserve references to `.teambot/history/` directory (workflow artifacts, not command)

**Preferred Approach:**
Code-First documentation updates with grep verification.

```text
Documentation Files to Update:
├── docs/feature-specs/teambot-interactive-mode.md
│   ├── Line 79: Remove from system commands table
│   ├── Lines 165-166: Remove command examples
│   ├── Line 185: Remove from functional requirements
│   └── Lines 304-305: Remove from help text example
├── docs/guides/architecture.md
│   └── Line 279: Only if it's about command (not directory path)
└── docs/feature-specs/file-orchestration-stages-cleanup.md
    └── Line 178: Remove from active commands table
```

**Implementation Details:**

**Step 1: Update Interactive Mode Spec**

File: `docs/feature-specs/teambot-interactive-mode.md`

```markdown
<!-- Line 79: Remove from table -->
| System Commands | `/help`, `/status`, `/quit` | P0 |

<!-- Lines 165-166: Remove these rows -->
<!-- DELETE:
| `/history` | Show recent actions | `/history` |
| `/history <agent>` | Show agent-specific history | `/history builder-1` |
-->

<!-- Line 185: Update requirement -->
| FR-IM-004 | System Commands | Implement `/help`, `/status`, `/quit` | P0 | All commands work as documented |

<!-- Lines 304-305: Remove from help text -->
<!-- DELETE:
/history             - Show recent actions (all agents)
/history <agent>     - Show history for specific agent
-->
```

**Step 2: Update Architecture Guide**

File: `docs/guides/architecture.md`

```markdown
<!-- Line 279: ONLY remove if it's about the command -->
<!-- If it says: ".teambot/{feature}/history/" - KEEP (directory path) -->
<!-- If it says: "/history command" - REMOVE -->
```

**Step 3: Update Stages Cleanup Doc**

File: `docs/feature-specs/file-orchestration-stages-cleanup.md`

```markdown
<!-- Line 178: Remove from active commands table -->
<!-- DELETE:
| `/history` | ✅ Active | Shows command history |
-->
```

**Step 4: Verify No Orphaned References**

```bash
# Search for remaining /history references (excluding directory paths)
grep -r "/history" docs/ | grep -v ".teambot/history/" | grep -v "node_modules"

# Expected: Zero matches (or only remove-history-command.md spec itself)
```

**Step 5: Preserve Workflow History References**

✅ **DO NOT REMOVE** references to `.teambot/history/` directory - this is for workflow artifact storage, NOT the `/history` command:

```markdown
<!-- KEEP THESE TYPES OF REFERENCES: -->
* **History logging**: All agent outputs saved to `.teambot/history/`
* Creates directories: `.teambot/history`, `.teambot/state`
```

#### Considered Alternatives (Removed After Selection)

No alternatives - documentation must be updated to match implementation.

---

## Output Validation Checklist

- [x] **Research Document Created**: `.agent-tracking/research/20260306-remove-history-command-research.md` exists
- [x] **All Placeholders Replaced**: No `{{placeholder}}` tokens remain in document
- [x] **Technical Approach Documented**: Code-First deletion with test verification
- [x] **Code Patterns Found**: 5 implementation patterns identified with line numbers
- [x] **Entry Point Analysis Complete**: 3 entry points traced, all coverage verified ✅
- [x] **Test Infrastructure Researched**: pytest framework, patterns, and conventions documented
- [x] **Line References Valid**: All references point to actual code (verified via view tool)
- [x] **Single Recommended Approach**: Code-First deletion approach selected
- [x] **Implementation Guidance Ready**: Step-by-step removal plan documented for all 3 scenarios

**RESEARCH_VALIDATION**: ✅ **PASS**
- Document: ✅ CREATED
- Placeholders: 0 remaining
- Technical Approach: ✅ DOCUMENTED (Code-First deletion)
- Entry Points: 3 traced, 3 covered ✅ COMPLETE
- Test Infrastructure: ✅ RESEARCHED (pytest with async support)
- Implementation Ready: ✅ YES (11 task items documented)
