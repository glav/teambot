# Agent Output Header Styling Enhancement

## Overview

Improve visual differentiation between agent output sections in the output pane by using colored headers with icons and consistent delimiter styling.

## Problem Statement

Current agent output headers use identical plain-text formatting:
```
=== Output from @pm (task a41b13a2) ===
=== Output from @ba (task b52c24b3) ===
=== Your Task ===
```

This makes it difficult to quickly distinguish between different agents' output sections.

## Target Format

```
━━━ 📋 @pm (task a41b13a2) ━━━━━━━━━━━━━━━  ← blue text
[output content]

━━━ 📊 @ba (task b52c24b3) ━━━━━━━━━━━━━━━  ← cyan text  
[output content]

━━━ 🎯 Your Task ━━━━━━━━━━━━━━━━━━━━━━━━━  ← distinct color (white/bold)
[task prompt]
```

## Requirements

| ID  | Requirement                                          | Priority |
|-----|------------------------------------------------------|----------|
| R1  | Use agent icon from `AGENT_ICONS` mapping            | Must     |
| R2  | Use agent color from `PERSONA_COLORS` mapping        | Must     |
| R3  | Include task ID in parentheses                       | Must     |
| R4  | Use `━` (heavy horizontal line U+2501) as delimiter  | Must     |
| R5  | "Your Task" section should be visually distinct      | Must     |
| R6  | Maintain existing error/missing output handling      | Must     |

## File to Modify

- `src/teambot/tasks/output_injector.py` (lines 48-66)

## Dependencies

Existing assets to leverage:
- `AGENT_ICONS` from `src/teambot/visualization/console.py`
- `PERSONA_COLORS` from `src/teambot/visualization/console.py`
- `get_agent_style()` function for color/icon lookup

## Acceptance Criteria

- [ ] Agent headers display with correct icon for each agent type
- [ ] Headers are colorized per agent persona
- [ ] Task ID remains visible in header
- [ ] "Your Task" section uses distinct styling (🎯 icon, bold/white)
- [ ] Error states display correctly with new styling
- [ ] Missing output states display correctly with new styling
- [ ] Existing tests pass

## Out of Scope

- Changes to the output pane widget itself
- Changes to handoff separator styling
- Changes to streaming output display
