<!-- markdownlint-disable-file -->

# Remove Overlay Feature - Implementation Details

**Date**: 2026-02-13
**Plan Reference**: `.agent-tracking/plans/20260213-remove-overlay-plan.instructions.md`
**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 114-337)

---

## Table of Contents

1. [Phase 1: Delete Overlay Tests](#phase-1-delete-overlay-tests) (Lines 15-45)
2. [Phase 2: Delete Core Overlay Module](#phase-2-delete-core-overlay-module) (Lines 47-95)
3. [Phase 3: REPL Integration Cleanup](#phase-3-repl-integration-cleanup) (Lines 97-170)
4. [Phase 4: Config Loader Cleanup](#phase-4-config-loader-cleanup) (Lines 172-220)
5. [Phase 5: Documentation Cleanup](#phase-5-documentation-cleanup) (Lines 222-265)
6. [Phase 6: Final Validation](#phase-6-final-validation) (Lines 267-310)

---

## Phase 1: Delete Overlay Tests

**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 119-136)

### Task 1.1: Delete test_overlay.py

**File**: `tests/test_visualization/test_overlay.py`
**Action**: Delete entire file (571 lines)
**Rationale**: Tests overlay functionality being removed

**Command**:
```bash
rm tests/test_visualization/test_overlay.py
```

**Success Criteria**: File no longer exists

---

### Task 1.2: Delete test_commands_overlay.py

**File**: `tests/test_repl/test_commands_overlay.py`
**Action**: Delete entire file (141 lines)
**Rationale**: Tests /overlay command being removed

**Command**:
```bash
rm tests/test_repl/test_commands_overlay.py
```

**Success Criteria**: File no longer exists

---

## Phase 2: Delete Core Overlay Module

**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 119-124, 141-162)

### Task 2.1: Delete overlay.py

**File**: `src/teambot/visualization/overlay.py`
**Action**: Delete entire file (603 lines)
**Rationale**: Core overlay renderer module no longer needed

**Command**:
```bash
rm src/teambot/visualization/overlay.py
```

**Success Criteria**: File no longer exists

---

### Task 2.2: Update visualization/__init__.py

**File**: `src/teambot/visualization/__init__.py`
**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 141-162)

**Current Code** (approximate):
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
1. Remove the overlay import line entirely
2. Remove `OverlayRenderer`, `OverlayState`, `OverlayPosition` from `__all__`

**Target Code**:
```python
__all__ = [
    "ConsoleDisplay",
    "AgentStatus",
    "PERSONA_COLORS",
    "StartupAnimation",
    "play_startup_animation",
]
```

**Success Criteria**: No import errors when importing from teambot.visualization

---

## Phase 3: REPL Integration Cleanup

**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 165-199)

### Task 3.1: Update commands.py

**File**: `src/teambot/repl/commands.py`
**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 165-179)

**Changes Required**:

| Line(s) | Current | Action |
|---------|---------|--------|
| 3 | `/overlay` in docstring | Remove from docstring |
| ~17 | `TYPE_CHECKING` import of `OverlayRenderer` | Remove import |
| ~105 | `/overlay` in `/help` output | Remove from help list |
| 536-602 | `handle_overlay()` function | Delete entire function |
| ~615 | `overlay` parameter in `SystemCommands.__init__()` | Remove parameter |
| ~624 | Overlay docstring | Remove docstring |
| ~630 | `self._overlay` assignment | Remove assignment |
| 652-658 | `set_overlay()` method | Delete method |
| ~687 | `"overlay": self.overlay` in handlers dict | Remove entry |
| 742-744 | `overlay()` property method | Delete method |

**Pattern - Removing from handlers dict**:
```python
# Before
handlers = {
    "help": self.help,
    "overlay": self.overlay,  # Remove this line
    "models": self.models,
}

# After
handlers = {
    "help": self.help,
    "models": self.models,
}
```

**Success Criteria**: No overlay references remain in commands.py

---

### Task 3.2: Update loop.py

**File**: `src/teambot/repl/loop.py`
**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 182-199)

**Changes Required**:

| Line(s) | Current | Action |
|---------|---------|--------|
| ~27 | `from teambot.visualization.overlay import...` | Remove import |
| ~38 | "Persistent status overlay" in docstring | Remove from docstring |
| ~45 | `enable_overlay: bool = True` parameter | Remove parameter |
| ~53 | Docstring for `enable_overlay` | Remove docstring entry |
| 74-89 | Overlay configuration/initialization block | Remove block |
| 155-173 | `_on_task_complete()` overlay calls | Replace with console.print |
| 175-181 | `_on_task_started()` overlay call | Remove overlay call |
| 183-195 | `_on_stage_change()`, `_on_pipeline_complete()` | Remove overlay calls |
| 197-204 | `_on_stage_output()` | Use console.print directly |
| 300-306 | Overlay startup/supported checks | Remove checks |
| 420-423 | Overlay cleanup in `_cleanup()` | Remove cleanup |
| ~484 | "with overlay" comment | Remove comment |

**Pattern - Replacing overlay.print_with_overlay with console.print**:
```python
# Before
def _on_task_complete(self, task: Task, result: TaskResult) -> None:
    self._overlay.on_task_completed(task, result)
    if result.success:
        self._overlay.print_with_overlay(
            f"\n[green]✓ Task #{task.id} completed (@{task.agent_id})[/green]"
        )

# After
def _on_task_complete(self, task: Task, result: TaskResult) -> None:
    if result.success:
        self._console.print(
            f"\n[green]✓ Task #{task.id} completed (@{task.agent_id})[/green]"
        )
```

**Success Criteria**: No overlay references remain in loop.py, REPL starts successfully

---

## Phase 4: Config Loader Cleanup

**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 201-228)

### Task 4.1: Update loader.py

**File**: `src/teambot/config/loader.py`
**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 201-210)

**Changes Required**:

| Line(s) | Current | Action |
|---------|---------|--------|
| 26-31 | `VALID_OVERLAY_POSITIONS` constant | Delete constant |
| 151-153 | Overlay validation call | Remove call |
| 213-228 | `_validate_overlay()` method | Delete entire method |
| 295-302 | Overlay defaults in `_apply_defaults()` | Remove block |

**Pattern - Removing validation call**:
```python
# Before
def _validate(self, config: dict[str, Any]) -> None:
    # ... other validation ...
    if "overlay" in config:
        self._validate_overlay(config["overlay"])

# After
def _validate(self, config: dict[str, Any]) -> None:
    # ... other validation ...
    # (overlay validation removed)
```

**Success Criteria**: Config loads without overlay options, no validation errors

---

### Task 4.2: Update test_loader.py

**File**: `tests/test_config/test_loader.py`
**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 212-217)

**Changes Required**:

Delete entire `TestOverlayConfig` class (approximately lines 187-267), which includes:
- `test_overlay_defaults_applied`
- `test_overlay_position_valid`
- `test_overlay_position_invalid`
- `test_overlay_enabled_bool`
- `test_overlay_disabled`

**Success Criteria**: Config tests pass without overlay tests

---

## Phase 5: Documentation Cleanup

**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 225-241)

### Task 5.1: Update architecture.md

**File**: `docs/guides/architecture.md`
**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 225-233)

**Changes Required**:

| Line(s) | Current | Action |
|---------|---------|--------|
| ~134-135 | "Status Overlay Updates" in diagram | Remove from diagram |
| ~140-141 | Overlay bullet point in Features | Remove bullet |
| ~252-254 | "Status Overlay" section | Delete entire section |

**Success Criteria**: No overlay references in architecture.md

---

### Task 5.2: Update development.md

**File**: `docs/guides/development.md`
**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 237-241)

**Changes Required**:

| Line(s) | Current | Action |
|---------|---------|--------|
| ~47 | "status overlay" in visualization description | Remove mention |

**Success Criteria**: No overlay references in development.md

---

### Task 5.3: Delete Feature Spec

**File**: `docs/feature-specs/persistent-status-overlay.md`
**Action**: Delete entire file
**Rationale**: Feature specification for removed feature

**Command**:
```bash
rm docs/feature-specs/persistent-status-overlay.md
```

**Success Criteria**: File no longer exists

---

## Phase 6: Final Validation

**Research Reference**: `.teambot/remove-overlay/artifacts/research.md` (Lines 387-464)

### Task 6.1: Run Full Test Suite

**Commands**:
```bash
# Run all tests
uv run pytest

# Expected: All tests pass, coverage ≥ 80%
```

**Success Criteria**:
- Exit code 0
- All tests pass
- No import errors
- Coverage report shows ≥ 80%

---

### Task 6.2: Run Linting and Formatting

**Commands**:
```bash
# Check linting
uv run ruff check .

# Format code
uv run ruff format -- .
```

**Success Criteria**:
- No lint errors
- Code properly formatted
- Exit code 0

---

### Task 6.3: Verify No Orphan References

**Commands**:
```bash
# Check source code
grep -ri "overlay" src/teambot/ --include="*.py"

# Check tests
grep -ri "overlay" tests/ --include="*.py"

# Check docs (should only have intentional references if any)
grep -ri "overlay" docs/
```

**Success Criteria**:
- No matches in source code (src/)
- No matches in tests (tests/)
- No matches in docs/ (or only intentional changelog entries)

---

## Quick Reference Commands

```bash
# Phase 1: Delete tests
rm tests/test_visualization/test_overlay.py
rm tests/test_repl/test_commands_overlay.py

# Phase 2: Delete module
rm src/teambot/visualization/overlay.py

# Phase 5: Delete spec
rm docs/feature-specs/persistent-status-overlay.md

# Phase 6: Validation
uv run pytest
uv run ruff check .
uv run ruff format -- .
grep -ri "overlay" src/teambot/ --include="*.py"
grep -ri "overlay" tests/ --include="*.py"
```

---

## Troubleshooting

| Issue | Cause | Resolution |
|-------|-------|------------|
| Import error after deletion | Orphan import statement | Search and remove import |
| Test failure | Missing cleanup | Check test for overlay dependency |
| Lint error | Unused import | Remove unused import statement |
| REPL won't start | Loop.py still references overlay | Complete Task 3.2 |

---

**Document Status**: Ready for Implementation
**Author**: Task Planner Agent
