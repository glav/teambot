# Executor Header Styling Fix

## Overview

Complete the agent output header styling enhancement by updating `executor.py` to use the same styled headers already implemented in `output_injector.py`.

## Problem Statement

The original specification ([option-b-colored-headers.md](./option-b-colored-headers.md)) identified `output_injector.py` as the file to modify. That file was correctly updated, but `executor.py` **also generates agent output headers independently** and was not updated.

### Current State (executor.py)

```
=== @pm ===
[output content]

=== @ba ===
[output content]
```

### Expected State (matching output_injector.py)

```
━━━ 📋 @pm (task a41b13a2) ━━━━━━━━━━━━━━━  ← blue text
[output content]

━━━ 📊 @ba (task b52c24b3) ━━━━━━━━━━━━━━━  ← cyan text  
[output content]
```

## Root Cause

Headers are generated in two places:
1. ✅ `output_injector.py` - Updated with styled headers
2. ❌ `executor.py` - Still uses plain `=== @{agent_id} ===` format

## Files to Modify

| File | Lines | Current Code |
|------|-------|--------------|
| `src/teambot/tasks/executor.py` | 355 | `f"=== @{task.agent_id} ===\n{result.output}"` |
| `src/teambot/tasks/executor.py` | 360 | `f"=== @{task.agent_id} ===\n[Failed: {result.error}]"` |
| `src/teambot/tasks/executor.py` | 480 | `f"=== @{task.agent_id} ===\n{task.result.output}"` |
| `src/teambot/tasks/executor.py` | 518 | `f"=== @{task.agent_id} ===\n{result.output}"` |
| `src/teambot/tasks/executor.py` | 523 | `f"=== @{task.agent_id} ===\n[Skipped: {result.error}]"` |
| `src/teambot/tasks/executor.py` | 528 | `f"=== @{task.agent_id} ===\n[Failed: {result.error}]"` |

## Requirements

| ID  | Requirement                                                    | Priority |
|-----|----------------------------------------------------------------|----------|
| R1  | Extract header formatting from `OutputInjector` to shared utility | Should |
| R2  | Update all 6 header locations in `executor.py`                  | Must     |
| R3  | Include task ID in header (available as `task.id`)              | Must     |
| R4  | Use agent icon and color from `get_agent_style()`               | Must     |
| R5  | Use `━` (heavy horizontal line U+2501) as delimiter             | Must     |
| R6  | Maintain existing error/failure message content                 | Must     |

## Suggested Implementation Approach

### Option A: Shared Utility Function (Recommended)

1. Create a shared function `format_agent_header(agent_id: str, task_id: str) -> str` in a utility module (e.g., `src/teambot/tasks/formatting.py` or within `output_injector.py`)
2. Have both `OutputInjector` and `executor.py` use this function
3. Reduces code duplication and ensures consistency

### Option B: Direct Import

1. Import `OutputInjector` in `executor.py`
2. Call `OutputInjector()._format_header(agent_id, task_id)` at each location
3. Simpler but slightly awkward API (calling private method)

## Dependencies

- `get_agent_style()` from `src/teambot/visualization/console.py`
- `AGENT_ICONS` and `PERSONA_COLORS` mappings (used by `get_agent_style`)

## Acceptance Criteria

- [ ] All 6 header locations in `executor.py` use styled format
- [ ] Headers display correct icon per agent type
- [ ] Headers display correct color per agent type  
- [ ] Task ID is visible in each header
- [ ] Error/failure messages remain intact (only header changes)
- [ ] No code duplication between `executor.py` and `output_injector.py`
- [ ] Existing tests pass
- [ ] Manual verification shows styled headers in output pane

## Out of Scope

- Changes to `output_injector.py` styling (already correct)
- Changes to handoff separator styling
- Changes to streaming output display

## Related Documents

- [option-b-colored-headers.md](./option-b-colored-headers.md) - Original specification
