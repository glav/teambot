# Feature Spec: Persistent Status Overlay

## Overview

Add a persistent status display overlay to TeamBot's interactive mode that shows real-time agent and task status in a fixed terminal position without scrolling with output.

## Problem Statement

Currently, users must type `/status` to see agent and task status, interrupting their workflow. When agents are running tasks (especially background tasks), there's no visual indication of progress unless the user explicitly checks. This creates a disconnect between task activity and user awareness.

## Proposed Solution

Implement a compact, persistent overlay that:
1. Displays in a fixed terminal position (default: top-right)
2. Shows current agent activity with spinners
3. Shows task counts (running/pending/completed)
4. Updates on state changes (not polling)
5. Can be toggled on/off via `/overlay` command
6. Position is configurable via config file and runtime command

## User Stories

### US-1: See Agent Activity at a Glance
**As a** TeamBot user  
**I want** to see which agents are currently working  
**So that** I know the system is making progress without typing `/status`

### US-2: Monitor Task Progress
**As a** TeamBot user  
**I want** to see task counts in the overlay  
**So that** I can track how many tasks are running, pending, and completed

### US-3: Toggle Overlay Visibility
**As a** TeamBot user  
**I want** to hide/show the overlay  
**So that** I can maximize screen space when needed

### US-4: Customize Overlay Position
**As a** TeamBot user  
**I want** to configure where the overlay appears  
**So that** it doesn't interfere with my preferred terminal layout

## Functional Requirements

### FR-PSO-001: Overlay Display
The overlay SHALL be displayed in a fixed terminal position that does not scroll with output.

### FR-PSO-002: Default Position
The overlay SHALL default to the top-right corner of the terminal.

### FR-PSO-003: Compact Format
The overlay SHALL be compact (3-4 lines maximum) showing:
- Line 1: Active agent(s) with spinner (e.g., `⠋ @pm, @ba`)
- Line 2: Task counts (e.g., `Tasks: 2 running, 1 pending, 5 done`)
- Line 3: Optional status message or idle indicator

### FR-PSO-004: Spinner Animation
When agent(s) are executing, the overlay SHALL display an animated spinner.

### FR-PSO-005: State-Change Updates
The overlay SHALL update only when state changes occur (task start, complete, fail), not on a polling interval.

### FR-PSO-006: Toggle Command
The system SHALL provide `/overlay on` and `/overlay off` commands to toggle visibility.

### FR-PSO-007: Position Command
The system SHALL provide `/overlay position <pos>` command where `<pos>` is one of:
- `top-right` (default)
- `top-left`
- `bottom-right`
- `bottom-left`

### FR-PSO-008: Configuration File
The overlay position and default visibility SHALL be configurable in `teambot.json`:
```json
{
  "overlay": {
    "enabled": true,
    "position": "top-right"
  }
}
```

### FR-PSO-009: Status Command Unchanged
The `/status` command SHALL continue to work as before, showing detailed text output.

### FR-PSO-010: Idle State Display
When no tasks are running, the overlay SHALL show an idle indicator (e.g., `✓ Idle` or dim the display).

### FR-PSO-011: Terminal Size Handling
The overlay SHALL gracefully handle terminal resize events and reposition accordingly.

### FR-PSO-012: Spinner Animation Timer
The spinner animation SHALL use a separate async timer (100ms interval) that ONLY updates the spinner frame, not the full overlay content. The timer SHALL be active only when tasks are running.

### FR-PSO-013: Task Started Event
TaskExecutor SHALL be extended to support `on_task_started` callback for overlay updates when tasks begin.

### FR-PSO-014: Output Collision Handling
Before printing REPL output, the system SHALL clear the overlay region, print the output, then redraw the overlay to prevent visual artifacts.

## Non-Functional Requirements

### NFR-PSO-001: Performance
Overlay updates SHALL not impact REPL responsiveness (< 10ms render time).

### NFR-PSO-002: Terminal Compatibility
The overlay SHALL work on terminals supporting ANSI escape codes (xterm, iTerm2, Windows Terminal, VS Code terminal).

### NFR-PSO-003: Graceful Degradation
On terminals that don't support cursor positioning, the overlay SHALL be automatically disabled with a warning. If terminal width < 30 columns or height < 10 rows, overlay SHALL be automatically disabled.

## Technical Approach

### Terminal Rendering
Use ANSI escape sequences for cursor positioning:
- Save cursor: `\033[s`
- Restore cursor: `\033[u`
- Move to position: `\033[{row};{col}H`
- Clear to end of line: `\033[K`

### Rich Library Integration
Leverage Rich's `Live` display or implement custom rendering using Rich's console with cursor control.

### Event-Driven Updates
Subscribe to TaskManager events:
- `on_task_started(task)` - NEW: required for overlay
- `on_task_completed(task, result)`
- `on_task_failed(task, error)`

### Spinner Timer
```python
async def _run_spinner(self):
    """Async timer for spinner animation (100ms interval)."""
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    while self._has_running_tasks():
        self._state.spinner_frame = (self._state.spinner_frame + 1) % len(frames)
        self._render_overlay()
        await asyncio.sleep(0.1)
```

### Overlay State
```python
@dataclass
class OverlayState:
    enabled: bool = True
    position: str = "top-right"  # top-right, top-left, bottom-right, bottom-left
    active_agents: list[str] = field(default_factory=list)
    running_count: int = 0
    pending_count: int = 0
    completed_count: int = 0
    spinner_frame: int = 0
```

## Display Mockups

### Active State (Top-Right)
```
                                    ┌─────────────────────┐
                                    │ ⠋ @pm, @builder-1   │
                                    │ Tasks: 2⏳ 1⏸ 5✓   │
                                    └─────────────────────┘
teambot: @writer Create API docs &
Task #8 started in background
teambot: 
```

### Idle State
```
                                    ┌─────────────────────┐
                                    │ ✓ Idle              │
                                    │ Tasks: 0⏳ 0⏸ 8✓   │
                                    └─────────────────────┘
teambot: 
```

### Overlay Disabled
```
teambot: /overlay off
Overlay disabled. Use /overlay on to re-enable.
teambot: 
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `/overlay` | Show current overlay status and settings |
| `/overlay on` | Enable the overlay |
| `/overlay off` | Disable the overlay |
| `/overlay position <pos>` | Set position (top-right, top-left, bottom-right, bottom-left) |

## Configuration Schema

```json
{
  "overlay": {
    "enabled": true,
    "position": "top-right"
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Whether overlay is shown on startup |
| `position` | string | `"top-right"` | Overlay position |

## Out of Scope

- Mouse interaction with overlay
- Clickable elements in overlay
- Multiple overlays
- Custom overlay content/templates
- Overlay in non-interactive (batch) mode

## Dependencies

- Rich library (already used)
- Terminal supporting ANSI escape codes

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Terminal incompatibility | Overlay doesn't render correctly | Auto-detect capability, disable gracefully |
| Flicker during rapid updates | Poor UX | Batch updates, use double-buffering |
| Overlay obscures important output | User frustration | Allow toggle, configurable position |

## Success Criteria

1. Overlay displays correctly in VS Code terminal, iTerm2, and Windows Terminal
2. Spinner animates smoothly when agents are active
3. Task counts update immediately on state changes
4. Toggle and position commands work correctly
5. Configuration persists across sessions
6. No measurable impact on REPL performance

## Estimated Effort

| Phase | Effort |
|-------|--------|
| Overlay renderer (ANSI positioning + collision handling) | 2.5 hours |
| Event subscription from TaskManager + on_task_started | 1.5 hours |
| Spinner animation (async timer) | 1 hour |
| Commands (/overlay on/off/position) | 1 hour |
| Configuration support | 0.5 hours |
| Terminal compatibility detection | 1 hour |
| Testing (with terminal mocking) | 2.5 hours |
| **Total** | **~10 hours** |

## Open Questions

1. ~~Should the overlay show elapsed time for running tasks?~~ **No** - Keep compact; users can `/task <id>` for details
2. ~~Should there be a keyboard shortcut (e.g., Ctrl+O) to toggle?~~ **Yes** - Add as P2 enhancement
3. ~~Should the overlay auto-hide after inactivity?~~ **No** - Could confuse users; explicit toggle preferred

## Testing Strategy

1. **Unit tests:** Mock terminal dimensions, verify ANSI escape sequences in output
2. **Integration tests:** Use Rich's `Console(force_terminal=True, record=True)` to capture rendered output
3. **Manual tests:** VS Code terminal, iTerm2, Windows Terminal verification
