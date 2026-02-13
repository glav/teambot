<!-- markdownlint-disable-file -->

# Remove Overlay Feature - Research Document

**Date**: 2026-02-13  
**Feature**: Remove Overlay  
**Status**: ✅ Research Complete  
**Document Version**: 1.0

---

## Table of Contents

1. [Research Scope](#research-scope)
2. [Technical Approach](#technical-approach)
3. [Entry Point Analysis](#entry-point-analysis)
4. [Files to Delete](#files-to-delete)
5. [Files to Modify](#files-to-modify)
6. [Code Patterns & Examples](#code-patterns--examples)
7. [Testing Strategy](#testing-strategy)
8. [Implementation Guidance](#implementation-guidance)
9. [Risks & Mitigations](#risks--mitigations)
10. [Task Implementation Requests](#task-implementation-requests)

---

## Research Scope

### Objective

Remove the unused persistent status overlay feature from TeamBot to reduce codebase complexity and maintenance burden.

### Key Questions Answered

| Question | Answer |
|----------|--------|
| What files contain overlay code? | `overlay.py`, `commands.py`, `loop.py`, `loader.py`, `__init__.py` |
| How many lines of overlay code? | ~1,315 lines (603 + 571 + 141 tests) |
| Where is overlay integrated? | REPL loop, commands, config loader, visualization exports |
| What tests cover overlay? | 59 tests in 2 test files |
| Are there external dependencies? | No - uses Rich library (already used by other features) |

### Assumptions Validated

| Assumption | Status | Evidence |
|------------|--------|----------|
| Overlay is standalone feature | ✅ Verified | No other features depend on overlay classes |
| Tests are overlay-specific | ✅ Verified | Test files only test overlay functionality |
| Config validation is isolated | ✅ Verified | `_validate_overlay()` and `_apply_defaults()` are separate methods |
| REPL still works without overlay | ✅ Verified | Split-pane UI does not use overlay |

---

## Technical Approach

### Recommended Approach: Sequential Deletion with Incremental Testing

**Rationale**: The overlay feature is well-isolated with clear boundaries. A sequential deletion approach with testing after each phase ensures no regressions.

#### Implementation Phases

| Phase | Description | Files Affected |
|-------|-------------|----------------|
| 1️⃣ | Delete core overlay module and tests | `overlay.py`, test files |
| 2️⃣ | Remove visualization exports | `__init__.py` |
| 3️⃣ | Remove REPL integration | `loop.py`, `commands.py` |
| 4️⃣ | Remove config validation | `loader.py` |
| 5️⃣ | Remove config tests | `test_loader.py` |
| 6️⃣ | Update documentation | `architecture.md`, `development.md` |
| 7️⃣ | Delete feature spec | `persistent-status-overlay.md` |
| 8️⃣ | Final validation | Run full test suite + linting |

---

## Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Overlay? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `/overlay` command | `loop.py` → `commands.py:handle_overlay()` | YES | YES - Remove handler |
| `/help` command | `commands.py:handle_help()` | YES (shows /overlay) | YES - Remove from help |
| REPL initialization | `loop.py:REPLLoop.__init__()` | YES - Creates OverlayRenderer | YES - Remove creation |
| Task completion | `loop.py:_on_task_complete()` | YES - Calls overlay methods | YES - Remove callbacks |
| Pipeline stage change | `loop.py:_on_stage_change()` | YES - Updates overlay | YES - Remove callbacks |
| Config loading | `loader.py:_validate()` | YES - Validates overlay config | YES - Remove validation |

### Code Path Trace

#### Entry Point 1: `/overlay` Command
1. User enters: `/overlay`
2. Handled by: `loop.py:REPLLoop.run()` (line ~325)
3. Routes to: `router.py` → `commands.py:SystemCommands.dispatch()` (line 668)
4. Reaches: `commands.py:handle_overlay()` (lines 536-602) ✅

#### Entry Point 2: Task Event Callbacks
1. Task completes in TaskExecutor
2. Callback: `loop.py:_on_task_complete()` (lines 155-173)
3. Calls: `self._overlay.on_task_completed()` ✅

#### Entry Point 3: Config Loading
1. User has `teambot.json` with `overlay` key
2. Handled by: `loader.py:ConfigLoader.load()` (line 108)
3. Validates: `loader.py:_validate_overlay()` (lines 213-228)
4. Applies defaults: `loader.py:_apply_defaults()` (lines 295-302) ✅

### Coverage Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## Files to Delete

### Primary Files (Delete First)

| File | Lines | Purpose | Dependencies |
|------|-------|---------|--------------|
| `src/teambot/visualization/overlay.py` | 603 | Core overlay renderer | None external |
| `tests/test_visualization/test_overlay.py` | 571 | Overlay unit tests | Imports overlay classes |
| `tests/test_repl/test_commands_overlay.py` | 141 | REPL command tests | Imports overlay + commands |
| `docs/feature-specs/persistent-status-overlay.md` | TBD | Feature specification | None |

### Deletion Order

```
1. tests/test_visualization/test_overlay.py
2. tests/test_repl/test_commands_overlay.py
3. src/teambot/visualization/overlay.py
4. docs/feature-specs/persistent-status-overlay.md
```

**Rationale**: Delete tests first to avoid import errors during intermediate steps.

---

## Files to Modify

### `src/teambot/visualization/__init__.py` (Lines 1-16)

**Current Code** (lines 5-16):
```python
from teambot.visualization.overlay import OverlayPosition, OverlayRenderer, OverlayState

__all__ = [
    "ConsoleDisplay",
    "AgentStatus",
    "PERSONA_COLORS",
    "OverlayRenderer",
    "OverlayState",
    "OverlayPosition",
    "StartupAnimation",
    "play_startup_animation",
]
```

**Required Changes**:
- Remove line 5 (overlay import)
- Remove lines 11-13 (`OverlayRenderer`, `OverlayState`, `OverlayPosition` from `__all__`)

---

### `src/teambot/repl/commands.py` (Lines 1-761)

**Changes Required**:

1. **Line 3**: Remove `/overlay` from docstring
2. **Line 17**: Remove `TYPE_CHECKING` import of `OverlayRenderer`
3. **Line 105**: Remove `/overlay` from `/help` output
4. **Lines 536-602**: Delete `handle_overlay()` function entirely
5. **Line 615**: Remove `overlay` parameter from `SystemCommands.__init__()`
6. **Line 624**: Remove overlay docstring
7. **Line 630**: Remove `self._overlay` assignment
8. **Lines 652-658**: Delete `set_overlay()` method
9. **Line 687**: Remove `"overlay": self.overlay` from handlers dict
10. **Lines 742-744**: Delete `overlay()` method

---

### `src/teambot/repl/loop.py` (Lines 1-487)

**Changes Required**:

1. **Line 27**: Remove `from teambot.visualization.overlay import OverlayPosition, OverlayRenderer`
2. **Line 38**: Remove "Persistent status overlay" from docstring
3. **Line 45**: Remove `enable_overlay: bool = True` parameter
4. **Line 53**: Remove docstring for `enable_overlay`
5. **Lines 74-89**: Remove overlay configuration and initialization block
6. **Lines 155-173**: Modify `_on_task_complete()` to remove overlay calls
7. **Lines 175-181**: Modify `_on_task_started()` to remove overlay call
8. **Lines 183-195**: Remove `_on_stage_change()` and `_on_pipeline_complete()` overlay calls
9. **Lines 197-204**: Modify `_on_stage_output()` to use `self._console.print()` directly
10. **Lines 300-306**: Remove overlay startup/supported checks
11. **Lines 420-423**: Remove overlay cleanup in `_cleanup()`
12. **Line 484**: Remove "with overlay" comment

---

### `src/teambot/config/loader.py` (Lines 1-317)

**Changes Required**:

1. **Lines 26-31**: Delete `VALID_OVERLAY_POSITIONS` constant
2. **Lines 151-153**: Remove overlay validation call
3. **Lines 213-228**: Delete `_validate_overlay()` method entirely
4. **Lines 295-302**: Remove overlay defaults application block

---

### `tests/test_config/test_loader.py` (Lines 187-267)

**Changes Required**:

Delete entire `TestOverlayConfig` class (lines 187-267), which includes:
- `test_overlay_defaults_applied`
- `test_overlay_position_valid`
- `test_overlay_position_invalid`
- `test_overlay_enabled_bool`
- `test_overlay_disabled`

---

### `docs/guides/architecture.md` (Lines 1-300)

**Changes Required**:

1. **Lines 134-135**: Remove "Status Overlay Updates" from diagram
2. **Lines 140-141**: Remove overlay bullet point from Features list
3. **Lines 252-254**: Delete "Status Overlay" section entirely

---

### `docs/guides/development.md` (Lines 1-140)

**Changes Required**:

1. **Line 47**: Remove "status overlay" from visualization package description

---

## Code Patterns & Examples

### Pattern 1: Removing an Import and Export

**Before** (`visualization/__init__.py`):
```python
from teambot.visualization.overlay import OverlayPosition, OverlayRenderer, OverlayState

__all__ = [
    "ConsoleDisplay",
    "OverlayRenderer",  # Remove this
    "OverlayState",     # Remove this
    "OverlayPosition",  # Remove this
]
```

**After**:
```python
__all__ = [
    "ConsoleDisplay",
    "AgentStatus",
    "PERSONA_COLORS",
    "StartupAnimation",
    "play_startup_animation",
]
```

---

### Pattern 2: Removing a Command Handler from Dispatch

**Before** (`commands.py`):
```python
handlers = {
    "help": self.help,
    "overlay": self.overlay,  # Remove this line
    "models": self.models,
}
```

**After**:
```python
handlers = {
    "help": self.help,
    "models": self.models,
}
```

---

### Pattern 3: Replacing Overlay Print with Console Print

**Before** (`loop.py:_on_task_complete()`):
```python
def _on_task_complete(self, task: Task, result: TaskResult) -> None:
    self._overlay.on_task_completed(task, result)
    if result.success:
        self._overlay.print_with_overlay(
            f"\n[green]✓ Task #{task.id} completed (@{task.agent_id})[/green]"
        )
```

**After**:
```python
def _on_task_complete(self, task: Task, result: TaskResult) -> None:
    if result.success:
        self._console.print(
            f"\n[green]✓ Task #{task.id} completed (@{task.agent_id})[/green]"
        )
```

---

### Pattern 4: Removing Config Validation Method

**Before** (`loader.py`):
```python
def _validate(self, config: dict[str, Any]) -> None:
    # ... other validation ...
    if "overlay" in config:
        self._validate_overlay(config["overlay"])

def _validate_overlay(self, overlay: dict[str, Any]) -> None:
    """Validate overlay configuration."""
    if not isinstance(overlay, dict):
        raise ConfigError("'overlay' must be an object")
    # ... rest of method
```

**After**:
```python
def _validate(self, config: dict[str, Any]) -> None:
    # ... other validation ...
    # (overlay validation removed)
```

---

## Testing Strategy

### Existing Test Infrastructure

| Aspect | Value |
|--------|-------|
| **Framework** | pytest 9.0.2 |
| **Location** | `tests/` directory |
| **Runner** | `uv run pytest` |
| **Coverage Tool** | pytest-cov |
| **Current Coverage** | 80% |
| **Total Tests** | 1,455 tests |

### Overlay Tests to Delete

| Test File | Test Count | Lines |
|-----------|------------|-------|
| `tests/test_visualization/test_overlay.py` | 47 tests | 571 |
| `tests/test_repl/test_commands_overlay.py` | 12 tests | 141 |
| Config overlay tests (in `test_loader.py`) | 5 tests | ~80 |
| **Total** | **64 tests** | **~792** |

### Post-Removal Test Strategy

1. **Delete overlay-specific test files** (59 tests)
2. **Remove overlay config tests** from `test_loader.py` (5 tests)
3. **Run full test suite** to verify no regressions: `uv run pytest`
4. **Expected result**: All remaining tests pass

### Test Commands

```bash
# Verify tests pass before removal
uv run pytest

# After removal, run full suite
uv run pytest

# Check for overlay references (should return nothing)
grep -r "overlay" tests/ --include="*.py"

# Run linting
uv run ruff check .
uv run ruff format .
```

---

## Implementation Guidance

### Pre-Implementation Checklist

- [ ] Run baseline tests: `uv run pytest` (expect all 1,455 tests pass)
- [ ] Verify overlay tests exist and pass
- [ ] Create git branch for removal

### Implementation Order (Recommended)

```
Step 1: Delete test files
  └── tests/test_visualization/test_overlay.py
  └── tests/test_repl/test_commands_overlay.py

Step 2: Delete core module
  └── src/teambot/visualization/overlay.py

Step 3: Update visualization __init__.py
  └── Remove overlay imports and exports

Step 4: Update REPL commands.py
  └── Remove handle_overlay function
  └── Remove /overlay from help
  └── Remove overlay parameter from SystemCommands
  └── Remove overlay from dispatch handlers

Step 5: Update REPL loop.py
  └── Remove OverlayRenderer import
  └── Remove overlay initialization
  └── Replace overlay.print_with_overlay with console.print
  └── Remove overlay event callbacks
  └── Remove overlay cleanup

Step 6: Update config/loader.py
  └── Remove VALID_OVERLAY_POSITIONS
  └── Remove _validate_overlay method
  └── Remove overlay defaults in _apply_defaults

Step 7: Update tests/test_config/test_loader.py
  └── Remove TestOverlayConfig class (5 tests)

Step 8: Update documentation
  └── docs/guides/architecture.md (remove overlay section)
  └── docs/guides/development.md (remove overlay mention)

Step 9: Delete feature spec
  └── docs/feature-specs/persistent-status-overlay.md

Step 10: Final validation
  └── uv run pytest (all tests pass)
  └── uv run ruff check . (no lint errors)
  └── grep -r "overlay" src/ (no matches except maybe comments)
```

### Post-Implementation Validation

```bash
# Verify all tests pass
uv run pytest

# Verify linting passes
uv run ruff check .
uv run ruff format -- .

# Verify no orphan overlay references
grep -ri "overlay" src/teambot/ --include="*.py"
grep -ri "overlay" tests/ --include="*.py"

# Verify REPL starts (manual test)
uv run teambot init
uv run teambot run
# Type /help - should not show /overlay
# Type /overlay - should show "Unknown command"
```

---

## Risks & Mitigations

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Orphan imports cause failures | Medium | Low | Run tests after each phase |
| Documentation inconsistency | Low | Medium | Grep all docs for "overlay" |
| Missed callback in loop.py | Medium | Low | Trace all overlay method calls |
| Config tests fail after removal | Medium | Low | Remove config tests with overlay code |

### Rollback Plan

If issues arise, revert via git:
```bash
git checkout -- .
# or
git revert <commit-hash>
```

---

## Task Implementation Requests

### ✅ Ready for Implementation

| Task ID | Description | Priority | Est. Effort |
|---------|-------------|----------|-------------|
| T-001 | Delete overlay test files | High | 5 min |
| T-002 | Delete overlay.py module | High | 5 min |
| T-003 | Update visualization/__init__.py | High | 5 min |
| T-004 | Remove overlay from commands.py | High | 15 min |
| T-005 | Remove overlay from loop.py | High | 20 min |
| T-006 | Remove overlay from loader.py | High | 10 min |
| T-007 | Remove overlay tests from test_loader.py | High | 10 min |
| T-008 | Update architecture.md | Medium | 10 min |
| T-009 | Update development.md | Medium | 5 min |
| T-010 | Delete feature spec | Medium | 5 min |
| T-011 | Final validation (tests + lint) | High | 10 min |

**Total Estimated Effort**: ~1.5 hours

---

## Potential Next Research

No further research required. All technical questions are answered and implementation path is clear.

---

## References

| Ref | Type | Path | Description |
|-----|------|------|-------------|
| R-001 | Spec | `.teambot/remove-overlay/artifacts/feature_spec.md` | Feature specification |
| R-002 | Objective | `docs/objectives/objective-remove-overlay.md` | Original objective |
| R-003 | Source | `src/teambot/visualization/overlay.py` | Core overlay module |
| R-004 | Source | `src/teambot/repl/loop.py` | REPL integration |
| R-005 | Source | `src/teambot/repl/commands.py` | Command handler |
| R-006 | Source | `src/teambot/config/loader.py` | Config validation |
| R-007 | Test | `tests/test_visualization/test_overlay.py` | Overlay tests |
| R-008 | Test | `tests/test_repl/test_commands_overlay.py` | Command tests |
| R-009 | Doc | `docs/guides/architecture.md` | Architecture guide |

---

**Research completed**: 2026-02-13  
**Author**: @builder-1 (Research mode)
