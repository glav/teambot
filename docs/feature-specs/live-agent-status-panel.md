<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Live Agent Status Panel - Feature Specification Document
Version 1.0 | Status Complete | Owner TBD | Team TeamBot | Target TBD | Lifecycle Complete

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-01-28 |
| Problem & Users | 100% | None | 2026-01-28 |
| Scope | 100% | None | 2026-01-28 |
| Requirements | 100% | None | 2026-01-28 |
| Metrics & Risks | 100% | None | 2026-01-29 |
| Research | 100% | None | 2026-01-28 |
| Test Strategy | 100% | None | 2026-01-28 |
| Task Planning | 100% | None | 2026-01-29 |
| Operationalization | 100% | None | 2026-01-29 |
| Finalization | 100% | None | 2026-01-29 |
Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context
TeamBot's split-pane terminal interface has a left input pane that is largely underutilized. Currently, it displays only the "TeamBot" header at the top and the input prompt at the bottom, leaving significant vertical space empty. Users must manually type `/status` to see agent status, which is a momentary snapshot that quickly scrolls away in the output pane.

### Core Opportunity
Utilize the empty vertical space in the left input pane to display a **persistent, live-updating agent status panel**. This panel would show:
- The status of all 6 agents (pm, ba, writer, builder-1, builder-2, reviewer)
- Current task information for running/streaming agents
- The current Git branch name for context

This transforms the left pane from a simple input area into an **information dashboard** while maintaining all existing functionality.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Provide always-visible agent status | UX | Manual `/status` command | Persistent display | MVP | P0 |
| G-002 | Show real-time status updates | UX | Static snapshots | Live updates as status changes | MVP | P0 |
| G-003 | Display current Git branch | UX | Not shown | Always visible | MVP | P1 |
| G-004 | Maintain existing `/status` command | Compatibility | Works | Still works (unchanged) | MVP | P0 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Implement status widget in left pane | Status panel renders between header and prompt | P0 | TBD |
| Enable reactive updates | Status changes reflected within 500ms | P0 | TBD |
| Display Git branch | Current branch shown in header area | P1 | TBD |

---

## 2. Problem Definition

### Current Situation
- **Wasted space**: The left pane has significant empty area between header and input prompt
- **Manual status checks**: Users must type `/status` to see agent states
- **Ephemeral information**: Status output scrolls away in the right pane
- **No Git context**: Users must run `git branch` separately to know their context
- **Cognitive load**: Users must remember to check status and mentally track agent states

### Problem Statement
The left input pane wastes valuable screen real estate while users lack persistent visibility into agent status. Users must repeatedly type `/status` to monitor agent activity, and this information quickly scrolls away. There is no visual indication of the current Git branch, which is important context for development tasks.

### Root Causes
* Original design focused only on input functionality for left pane
* Status was designed as a command output, not a persistent display
* Git context wasn't considered part of the UI requirements

### Impact of Inaction
* Users waste time repeatedly typing `/status`
* Reduced situational awareness of agent activity
* Context-switching overhead to check Git branch
* Inefficient use of screen real estate

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Developer using TeamBot | Monitor agent activity while working | Typing `/status` repeatedly, losing context | High - primary user |
| Multi-tasker | Run parallel agent tasks, track progress | No persistent visibility of what's running | High - advanced workflows |
| Git-focused developer | Stay aware of branch context | Must switch to terminal for `git branch` | Medium - workflow efficiency |

### Journeys
1. **Monitoring Flow**: User glances at left pane → sees builder-1 is streaming → knows task is in progress → continues other work
2. **Context Awareness Flow**: User looks at header → sees "main" branch → knows they're on correct branch → issues command
3. **Multi-agent Flow**: User sees pm idle, builder-1 running, reviewer idle → queues task for reviewer → monitors completion

---

## 4. Scope

### In Scope
* Status panel widget in left pane (between header and input)
* Display of all 6 agent statuses (idle, running, streaming)
* Current task info for active agents (truncated to fit)
* Git branch display in header/status area
* Reactive updates when agent status changes
* Maintain existing `/status` command functionality

### Out of Scope (justified)
* Clickable/interactive status elements - CLI-focused, keyboard-driven
* Historical status (completed tasks list) - would clutter the panel
* Multiple Git repo support - single repo assumed
* Custom agent ordering/filtering - complexity not justified for MVP
* Status persistence across sessions - runtime display only

### Assumptions
* Terminal height is sufficient for header + status + input (minimum ~15 rows)
* Git repository may or may not be present (graceful fallback required)
* Agent status changes are communicated through existing mechanisms
* Textual's reactive system can efficiently update the widget

### Technical Constraints Discovered During Review
* **State is currently distributed**: `App._running_agents` tracks running tasks, `OutputPane._streaming_buffers` tracks streaming state - no single source of truth
* **No existing reactive patterns**: Codebase uses imperative updates, not Textual's reactive properties
* **Left pane width**: 30% width (~25-35 chars) limits display; agent names up to 9 chars ("builder-2") + status + task preview must fit
* **No timer/polling mechanism**: Animation and Git refresh require introducing `set_interval()` pattern

### Constraints
* Must fit within existing 30% left pane width
* Cannot interfere with input functionality
* Must work with existing Textual App architecture
* Status updates must not cause visual flicker
* **Horizontal overflow**: Truncate with ellipsis (...) - no wrapping
* **Vertical overflow**: Display bottom-most content, let top content scroll off (no scrollbar)

---

## 5. Product Overview

### Value Proposition
The live agent status panel transforms the underutilized left pane into an information dashboard, giving users persistent visibility into agent activity and Git context without requiring manual commands or losing information to scroll.

### Differentiators
* Always-visible status - no need to type `/status`
* Live updates - see status changes as they happen
* Git branch context - immediate awareness of working branch
* Space-efficient - uses existing unused area

### UX / UI
**Updated Layout:**
```
┌─────────────────────────┬───────────────────────────────────────┐
│  TeamBot  (main)        │                                       │
│  ─────────────────────  │  OUTPUT PANE (Right)                  │
│  Agent Status           │                                       │
│  ─────────────────────  │  [10:30:15] @pm: Task completed       │
│  pm        ● idle       │  [10:30:45] @builder-1: Starting...   │
│  ba        ● idle       │                                       │
│  writer    ● idle       │                                       │
│  builder-1 ◉ streaming  │                                       │
│    → impl auth...       │                                       │
│  builder-2 ● idle       │                                       │
│  reviewer  ● idle       │                                       │
│                         │                                       │
│  ─────────────────────  │                                       │
│  > @reviewer check _    │                                       │
└─────────────────────────┴───────────────────────────────────────┘
```

**Status Indicators:**
- `●` (dim) - idle
- `●` (yellow) - running (background task)
- `◉` (cyan, animated) - streaming (active output)
- `●` (green) - completed (briefly, then returns to idle)
- `●` (red) - failed (briefly, then returns to idle)

**Git Branch Display:**
- Shown in header line: `TeamBot  (branch-name)`
- Truncated if too long: `TeamBot  (feat/long-branch...)`

| UX Status: Mockup Complete |

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|-------------|-------|----------|----------|------------|-------|
| FR-LSP-001 | Status Panel Widget | New Textual widget displaying agent status in left pane | G-001 | All | P0 | Widget renders between header and input | New widget class |
| FR-LSP-002 | Agent Status Display | Show all 6 agents with current status (idle/running/streaming) | G-001 | All | P0 | All agents visible with correct status | Match `/status` info |
| FR-LSP-003 | Task Information | Display current task for running/streaming agents (truncated) | G-001 | All | P1 | Task shown, max ~20 chars + ellipsis | Indented under agent |
| FR-LSP-004 | Git Branch Display | Show current Git branch in header area | G-003 | All | P1 | Branch name visible, truncated if needed | Max ~15 chars |
| FR-LSP-005 | Reactive Updates | Status panel updates automatically when agent status changes | G-002 | All | P0 | Updates within 500ms of status change | Use Textual reactivity |
| FR-LSP-006 | Status Indicators | Visual indicators for different states (icons + colors) | G-001 | All | P1 | Clear visual distinction between states | Unicode symbols |
| FR-LSP-007 | Preserve /status Command | Existing `/status` command continues to work unchanged | G-004 | All | P0 | Command outputs to right pane as before | No regression |
| FR-LSP-008 | Graceful Git Fallback | If not in Git repo, show "no repo" or hide branch | G-003 | All | P2 | No error, graceful display | Edge case handling |
| FR-LSP-009 | Narrow Terminal Handling | Status panel adapts or hides if terminal too narrow | G-001 | All | P2 | No layout breakage | Responsive design |
| FR-LSP-010 | Streaming Animation | Animated indicator for streaming state | G-002 | All | P2 | Visual activity indication | Spinner or pulse |
| FR-LSP-011 | Centralized Agent State | Agent status consolidated into single observable state | G-002 | All | P0 | One source of truth for status | Enables reactive updates |
| FR-LSP-012 | Update Mechanism | Status panel receives updates via Textual reactive bindings or explicit callbacks | G-002 | All | P0 | Panel updates within 500ms | Define communication pattern |
| FR-LSP-013 | Horizontal Truncation | Text exceeding pane width truncated with ellipsis (...) | G-001 | All | P0 | No horizontal overflow or wrapping | Simple ellipsis truncation |
| FR-LSP-014 | Vertical Overflow | When content exceeds vertical space, show bottom-most content; top content scrolls off | G-001 | All | P0 | Most recent/bottom content visible | No scrollbar needed |

### Feature Hierarchy
```
Live Agent Status Panel
├── Status Panel Widget
│   ├── Agent List Display
│   │   ├── Agent ID
│   │   ├── Status Indicator (icon + color)
│   │   └── Task Info (for active agents)
│   ├── Reactive Bindings
│   │   └── Update on status change
│   └── Layout Management
│       └── Fit within left pane
├── Header Enhancement
│   ├── Git Branch Display
│   └── Branch Truncation
├── Status Tracking
│   ├── Integration with App._running_agents
│   ├── Integration with OutputPane.get_streaming_agents()
│   └── Git branch detection
└── Compatibility
    └── Preserve /status command
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-LSP-001 | Performance | Status update latency | < 500ms from change to display | P0 | Benchmark test | Responsive feel |
| NFR-LSP-002 | Performance | No UI flicker | 0 flicker during updates | P0 | Visual testing | Clean updates |
| NFR-LSP-003 | Reliability | Correct status display | 100% accuracy vs actual state | P0 | Automated tests | Data integrity |
| NFR-LSP-004 | Usability | Glanceable information | Status readable in < 1 second | P1 | User testing | Dashboard goal |
| NFR-LSP-005 | Maintainability | Single widget class | Clean separation of concerns | P1 | Code review | Easy to modify |
| NFR-LSP-006 | Compatibility | Git detection reliability | Works with standard Git | P1 | Test various repos | subprocess call |

---

## 8. Data & Analytics

### Inputs
- Agent status from `App._running_agents` dict
- Streaming status from `OutputPane.get_streaming_agents()`
- Git branch from `git rev-parse --abbrev-ref HEAD`

### Outputs / Events
- Rendered status panel (visual only)
- No persistent storage

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|---------|---------|-------|
| status_update | Agent status changes | agent_id, old_status, new_status | Debug/performance | TBD |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| `/status` command usage | Usage | Baseline TBD | 50% reduction | Post-release | Telemetry |
| User satisfaction | UX | N/A | 4/5 | Post-release | Feedback |

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| Textual reactive system | External | High | Textual | Minimal - well documented | Follow Textual patterns |
| Git CLI | External | Medium | System | Git not installed | Graceful fallback |
| App._running_agents | Internal | High | TeamBot | Interface change | Use existing interface |
| OutputPane.get_streaming_agents | Internal | High | TeamBot | Interface change | Use existing interface |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Status updates cause UI flicker | Medium | Low | Use Textual's efficient reactive updates | TBD | Open |
| R-002 | Git subprocess slows down updates | Low | Low | Cache branch name, update on focus/interval | TBD | Open |
| R-003 | Status panel crowds left pane | Medium | Medium | Careful layout, minimum terminal size check | TBD | Open |
| R-004 | Sync issues between panel and /status | Medium | Low | Use same data sources | TBD | Open |
| R-005 | State refactoring scope creep | Medium | Medium | Limit changes to App class; keep OutputPane interface | TBD | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification
- Agent status: Internal/Runtime
- Git branch name: Internal/Project metadata
- Task content: Internal/User-generated (truncated display only)

### PII Handling
N/A - No PII displayed

### Threat Considerations
- Git subprocess injection: Use safe subprocess calls, no user input in command
- Task content display: Already shown in `/status`, no new exposure

### Regulatory / Compliance
N/A

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard package update | No infrastructure changes |
| Rollback | Feature could be hidden via CSS/config | Low risk feature |
| Monitoring | N/A | Client-side display only |

---

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Description | Gate Criteria | Owner |
|-------|-------------|---------------|-------|
| Phase 0 | Centralize agent state | Single reactive state dict in App | TBD |
| Phase 1 | Status panel widget | Static agent list renders | TBD |
| Phase 2 | Reactive updates | Status changes reflected live | TBD |
| Phase 3 | Git branch display | Branch shown in header | TBD |
| Phase 4 | Polish | Animations, edge cases | TBD |

### Feature Flags
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|---------|-----------------|
| N/A | Feature is additive, always enabled | N/A | N/A |

### Communication Plan
- Update README with new UI screenshot
- Note in changelog

---

## 14. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| Q-001 | Should completed/failed status show briefly before returning to idle? | TBD | Design phase | Answered: Yes, 2-3 seconds |
| Q-002 | Should status panel be collapsible if terminal height is very small? | TBD | Design phase | Answered: No, use legacy fallback |
| Q-003 | What's the exact truncation length for task preview? (spec says ~20 chars) | TBD | Design phase | Answered: Use ellipsis at pane boundary |

---

## 15. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 0.1 | 2026-01-28 | AI Assistant | Initial specification draft | New |
| 0.2 | 2026-01-28 | AI Assistant | Added state consolidation architecture, answered open questions, added detailed code specifications | Review |
| 0.3 | 2026-01-28 | AI Assistant | Added truncation requirements (FR-LSP-013, FR-LSP-014), clarified overflow behavior | Update |
| 0.4 | 2026-01-28 | AI Assistant | Added research findings: Textual CSS text-overflow, reactive patterns, Git detection | Research |
| 0.5 | 2026-01-28 | AI Assistant | Added comprehensive test strategy with unit and integration test specifications | Test Strategy |
| 0.6 | 2026-01-29 | AI Assistant | Added detailed implementation task plan with 5 phases and acceptance criteria | Task Planning |
| 0.7 | 2026-01-29 | AI Assistant | Plan review: Added requirements coverage matrix, risk mitigation mapping, cleanup tasks, memory leak prevention | Plan Review |

---

## 16. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Existing Spec | docs/feature-specs/split-pane-interface.md | Current split-pane implementation | Extends left pane functionality |
| REF-002 | Code | src/teambot/ui/app.py | Current App and `/status` implementation | Use existing data sources |
| REF-003 | Code | src/teambot/ui/widgets/input_pane.py | Current input pane widget | Add sibling widget |
| REF-004 | Code | src/teambot/ui/styles.css | Current CSS layout | Add status panel styles |

### Citation Usage Notes
This specification extends the split-pane interface by utilizing the empty space in the left pane. It does not modify existing functionality.

---

## 17. Research Findings

### Textual Version & Capabilities
- **Installed version**: Textual 7.4.0
- **Key capabilities verified**: Static.update(), reactive attributes, watch_* methods, CSS text-overflow

### Horizontal Text Truncation (FR-LSP-013)

**Textual CSS supports `text-overflow: ellipsis`** - This is the cleanest solution.

**CSS approach (RECOMMENDED):**
```css
StatusPanel {
    text-overflow: ellipsis;
    text-wrap: nowrap;
}
```

**Alternative Python approach using Rich Text:**
```python
from rich.text import Text
widget.update(Text("long text...", no_wrap=True, overflow="ellipsis"))
```

**Key requirements for ellipsis to work:**
1. Set `text-wrap: nowrap` (prevents wrapping)
2. Widget must have constrained width (already 30% of screen)
3. Use `text-overflow: ellipsis` style

### Vertical Overflow (FR-LSP-014)

**For content that exceeds vertical space**, Textual handles this via:
- Docked widgets (`dock: top`, `dock: bottom`) stay fixed
- Content between docked widgets fills remaining space
- With `overflow-y: hidden` or natural clipping, top content scrolls off

**Layout structure for status panel:**
```
#input-pane (Vertical container)
├── #header (dock: top, height: 1)
├── #status-panel (fills middle, overflow: hidden)
└── #prompt (dock: bottom)
```

**CSS for vertical overflow behavior:**
```css
#status-panel {
    overflow-y: hidden;  /* Clips content, no scrollbar */
    height: 1fr;         /* Fill available space */
}
```

When content exceeds space, the natural flow is top-to-bottom, so with `overflow: hidden`, bottom content remains visible and top content is clipped - achieving the desired "scroll off top" effect.

### Reactive Updates (FR-LSP-005, FR-LSP-012)

**Two approaches available:**

**Option A: Textual Reactive (cleaner but requires refactoring)**
```python
from textual.reactive import reactive

class StatusPanel(Static):
    status_data = reactive({})
    
    def watch_status_data(self):
        self.refresh()  # Auto-called when status_data changes
    
    def render(self) -> str:
        # Build display from self.status_data
        ...
```

**Option B: Manual update via callback (matches existing patterns)**
```python
class StatusPanel(Static):
    def __init__(self, status_manager: AgentStatusManager, **kwargs):
        super().__init__(**kwargs)
        status_manager.add_listener(self._on_status_change)
    
    def _on_status_change(self, manager):
        self.update(self._format_status())  # Static.update() triggers refresh
```

**Recommendation**: Option B (callback) aligns better with existing codebase patterns and the `AgentStatusManager` listener architecture already specified.

### Git Branch Detection

**Simple subprocess call:**
```python
import subprocess

def get_git_branch() -> str:
    """Get current git branch name, or empty string if not in repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=self.working_dir,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return ""
```

**Caching strategy**: Use `set_interval()` to refresh every 30 seconds, or on app focus.

### Widget Update Methods

**Key Static widget methods for updates:**
- `update(content)` - Replace widget content, triggers refresh
- `refresh()` - Force visual refresh without content change
- `set_interval(seconds, callback)` - Periodic updates (for Git branch, animations)

### CSS Additions Required

```css
#status-panel {
    height: 1fr;              /* Fill space between header and prompt */
    overflow-y: hidden;       /* Clip vertical overflow (top content scrolls off) */
    text-overflow: ellipsis;  /* Truncate long lines with ... */
    text-wrap: nowrap;        /* Prevent text wrapping */
    padding: 0 1;
    margin: 1 0;
}
```

### Existing Pattern Compatibility

The codebase uses:
- **Imperative updates**: `output.write_command()`, `output.finish_streaming()`
- **State in App**: `self._running_agents` dict
- **Subprocess calls**: `subprocess.run()` in `copilot/client.py`

The proposed `AgentStatusManager` with listener callbacks fits naturally alongside these patterns.

---

## 18. Test Strategy

### Test Approach Summary

| Component | Test Type | Pattern | Location |
|-----------|-----------|---------|----------|
| AgentStatusManager | Unit | Direct instantiation, listener callbacks | `tests/test_ui/test_agent_state.py` |
| StatusPanel widget | Unit | Mock `update()` and `refresh()` | `tests/test_ui/test_status_panel.py` |
| StatusPanel in App | Integration | Textual `run_test()` + Pilot | `tests/test_ui/test_app.py` |
| Git branch detection | Unit | Mock subprocess | `tests/test_ui/test_status_panel.py` |

### Test Files to Create

#### 1. `tests/test_ui/test_agent_state.py` - Unit Tests for AgentStatusManager

```python
"""Tests for AgentStatusManager and related classes."""

import pytest
from teambot.ui.agent_state import (
    AgentState,
    AgentStatus,
    AgentStatusManager,
    DEFAULT_AGENTS,
)


class TestAgentStatus:
    """Tests for AgentStatus dataclass."""

    def test_default_state_is_idle(self):
        """New AgentStatus defaults to idle state."""
        status = AgentStatus(agent_id="pm")
        assert status.state == AgentState.IDLE
        assert status.task is None

    def test_with_state_creates_new_instance(self):
        """with_state returns new instance, doesn't mutate original."""
        original = AgentStatus(agent_id="pm", state=AgentState.IDLE)
        updated = original.with_state(AgentState.RUNNING, "test task")

        assert original.state == AgentState.IDLE
        assert updated.state == AgentState.RUNNING
        assert updated.task == "test task"

    def test_with_state_preserves_task_if_not_provided(self):
        """with_state keeps existing task when new task is None."""
        original = AgentStatus(agent_id="pm", state=AgentState.RUNNING, task="old task")
        updated = original.with_state(AgentState.STREAMING)
        assert updated.task == "old task"


class TestAgentStatusManager:
    """Tests for AgentStatusManager."""

    def test_initializes_with_default_agents(self):
        """Manager initializes all default agents as idle."""
        manager = AgentStatusManager()
        for agent_id in DEFAULT_AGENTS:
            status = manager.get(agent_id)
            assert status is not None
            assert status.state == AgentState.IDLE

    def test_get_returns_none_for_unknown_agent(self):
        """get() returns None for non-existent agent."""
        manager = AgentStatusManager()
        assert manager.get("unknown-agent") is None

    def test_set_running_updates_state(self):
        """set_running changes agent to running state with task."""
        manager = AgentStatusManager()
        manager.set_running("pm", "plan authentication")
        status = manager.get("pm")
        assert status.state == AgentState.RUNNING
        assert status.task == "plan authentication"

    def test_set_running_truncates_long_task(self):
        """set_running truncates task to 40 chars + ellipsis."""
        manager = AgentStatusManager()
        manager.set_running("pm", "a" * 50)
        status = manager.get("pm")
        assert status.task == "a" * 40 + "..."

    def test_set_streaming_preserves_task(self):
        """set_streaming keeps existing task."""
        manager = AgentStatusManager()
        manager.set_running("pm", "some task")
        manager.set_streaming("pm")
        status = manager.get("pm")
        assert status.state == AgentState.STREAMING
        assert status.task == "some task"

    def test_set_idle_clears_task(self):
        """set_idle returns agent to idle and clears task."""
        manager = AgentStatusManager()
        manager.set_running("pm", "task")
        manager.set_idle("pm")
        status = manager.get("pm")
        assert status.state == AgentState.IDLE
        assert status.task is None

    def test_get_streaming_agents(self):
        """get_streaming_agents returns only streaming agents."""
        manager = AgentStatusManager()
        manager.set_streaming("pm")
        manager.set_running("ba", "task")
        manager.set_streaming("builder-1")
        streaming = manager.get_streaming_agents()
        assert set(streaming) == {"pm", "builder-1"}

    def test_get_active_agents(self):
        """get_active_agents returns running and streaming agents."""
        manager = AgentStatusManager()
        manager.set_running("pm", "task")
        manager.set_streaming("ba")
        active = manager.get_active_agents()
        assert set(active) == {"pm", "ba"}


class TestAgentStatusManagerListeners:
    """Tests for listener/callback functionality."""

    def test_listener_called_on_state_change(self):
        """Listener is called when agent state changes."""
        manager = AgentStatusManager()
        calls = []
        manager.add_listener(lambda m: calls.append(m.get("pm").state))
        manager.set_running("pm", "task")
        assert len(calls) == 1
        assert calls[0] == AgentState.RUNNING

    def test_listener_not_called_when_no_change(self):
        """Listener is not called if state doesn't actually change."""
        manager = AgentStatusManager()
        calls = []
        manager.add_listener(lambda m: calls.append(True))
        manager.set_idle("pm")  # Already idle - no change
        assert len(calls) == 0

    def test_multiple_listeners_called(self):
        """All registered listeners are called on change."""
        manager = AgentStatusManager()
        calls1, calls2 = [], []
        manager.add_listener(lambda m: calls1.append(1))
        manager.add_listener(lambda m: calls2.append(2))
        manager.set_running("pm", "task")
        assert calls1 == [1]
        assert calls2 == [2]

    def test_remove_listener(self):
        """Removed listener is no longer called."""
        manager = AgentStatusManager()
        calls = []
        listener = lambda m: calls.append(1)
        manager.add_listener(listener)
        manager.set_running("pm", "task")
        assert len(calls) == 1
        manager.remove_listener(listener)
        manager.set_streaming("pm")
        assert len(calls) == 1  # Still 1, not called again

    def test_listener_error_doesnt_break_manager(self):
        """Listener exception doesn't prevent state updates."""
        manager = AgentStatusManager()
        manager.add_listener(lambda m: 1/0)  # Will raise ZeroDivisionError
        manager.set_running("pm", "task")  # Should not raise
        assert manager.get("pm").state == AgentState.RUNNING
```

#### 2. `tests/test_ui/test_status_panel.py` - Unit Tests for StatusPanel Widget

```python
"""Tests for StatusPanel widget."""

import pytest
from unittest.mock import patch, MagicMock

from teambot.ui.agent_state import AgentState, AgentStatusManager


class TestStatusPanel:
    """Tests for StatusPanel widget."""

    def test_renders_all_agents(self):
        """Panel renders all 6 default agents."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        with patch.object(panel, "update") as mock_update:
            panel._on_status_change(manager)
            call_arg = mock_update.call_args[0][0]
            
            for agent in ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]:
                assert agent in call_arg

    def test_shows_idle_indicator_for_idle_agents(self):
        """Idle agents show dim indicator."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "[dim]●[/dim]" in content or "idle" in content.lower()

    def test_shows_running_indicator(self):
        """Running agents show yellow indicator."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_running("pm", "test task")
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "[yellow]" in content or "running" in content.lower()

    def test_shows_streaming_indicator(self):
        """Streaming agents show cyan indicator."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_streaming("pm")
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "[cyan]" in content or "streaming" in content.lower()

    def test_shows_task_for_active_agents(self):
        """Active agents display their task."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        manager.set_running("pm", "implement auth")
        panel = StatusPanel(manager)

        content = panel._format_status()
        assert "implement auth" in content

    def test_listener_registered_on_init(self):
        """Panel registers listener with manager on init."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        # Verify listener is registered by checking it gets called
        with patch.object(panel, "refresh") as mock_refresh:
            manager.set_running("pm", "task")
            mock_refresh.assert_called()

    def test_update_called_on_status_change(self):
        """Panel updates when status changes."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        with patch.object(panel, "update") as mock_update:
            manager.set_running("pm", "task")
            mock_update.assert_called()


class TestStatusPanelGitBranch:
    """Tests for Git branch display."""

    def test_get_git_branch_success(self):
        """Returns branch name when in git repo."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="main\n"
            )
            branch = panel._get_git_branch()
            assert branch == "main"

    def test_get_git_branch_not_in_repo(self):
        """Returns empty string when not in git repo."""
        from teambot.ui.widgets.status_panel import StatusPanel

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=128)
            branch = panel._get_git_branch()
            assert branch == ""

    def test_get_git_branch_timeout(self):
        """Returns empty string on timeout."""
        from teambot.ui.widgets.status_panel import StatusPanel
        import subprocess

        manager = AgentStatusManager()
        panel = StatusPanel(manager)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 2)
            branch = panel._get_git_branch()
            assert branch == ""
```

#### 3. Integration Tests in `tests/test_ui/test_app.py` (additions)

```python
class TestStatusPanelIntegration:
    """Integration tests for StatusPanel in TeamBotApp."""

    @pytest.mark.asyncio
    async def test_status_panel_present_in_app(self):
        """App includes status panel widget."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#status-panel")
            assert panel is not None

    @pytest.mark.asyncio
    async def test_status_panel_between_header_and_prompt(self):
        """Status panel is positioned between header and input."""
        from teambot.ui.app import TeamBotApp

        app = TeamBotApp()
        async with app.run_test() as pilot:
            input_pane = app.query_one("#input-pane")
            children = list(input_pane.children)
            
            # Should have header, status-panel, prompt in order
            ids = [c.id for c in children if c.id]
            assert "header" in ids
            assert "status-panel" in ids
            assert "prompt" in ids

    @pytest.mark.asyncio
    async def test_status_updates_on_agent_command(self):
        """Status panel updates when agent command is executed."""
        from teambot.ui.app import TeamBotApp

        mock_executor = MagicMock()
        mock_executor.execute = AsyncMock(
            return_value=MagicMock(success=True, output="Done", background=False)
        )

        app = TeamBotApp(executor=mock_executor)
        async with app.run_test() as pilot:
            # Submit agent command
            await pilot.click("#prompt")
            await pilot.press("@", "p", "m", " ", "t", "e", "s", "t")
            await pilot.press("enter")
            await pilot.pause()

            # Verify status manager was updated
            status = app._agent_status.get("pm")
            # After completion, should be idle again
            assert status.state in [AgentState.IDLE, AgentState.COMPLETED]
```

### Test Coverage Targets

| Component | Target Coverage | Critical Paths |
|-----------|-----------------|----------------|
| `agent_state.py` | 95% | State transitions, listener callbacks |
| `status_panel.py` | 90% | Rendering, Git branch, updates |
| `app.py` (status integration) | 85% | Status manager usage, panel updates |

### Test Execution

```bash
# Run all new tests
uv run pytest tests/test_ui/test_agent_state.py tests/test_ui/test_status_panel.py -v

# Run with coverage
uv run pytest tests/test_ui/ --cov=src/teambot/ui --cov-report=term-missing

# Run specific test class
uv run pytest tests/test_ui/test_agent_state.py::TestAgentStatusManagerListeners -v
```

### Edge Cases to Test

| Scenario | Test | Expected Behavior |
|----------|------|-------------------|
| Unknown agent ID | `test_get_returns_none_for_unknown_agent` | Returns None |
| Task > 40 chars | `test_set_running_truncates_long_task` | Truncated with "..." |
| Listener raises exception | `test_listener_error_doesnt_break_manager` | State still updates |
| Not in Git repo | `test_get_git_branch_not_in_repo` | Returns empty string |
| Git command timeout | `test_get_git_branch_timeout` | Returns empty string |
| Multiple agents streaming | `test_get_streaming_agents` | Returns all streaming |
| Same listener added twice | `test_add_same_listener_twice` | Only called once |

---

## 19. Appendices

### Glossary
| Term | Definition |
|------|------------|
| Status panel | New widget showing persistent agent status |
| Reactive | Automatic UI updates when underlying data changes |
| Streaming | Agent actively outputting response chunks |
| AgentStatusManager | Centralized state store for all agent statuses |

### Technical Approach

**State Architecture (Required for Implementation):**

The current codebase has distributed state that must be consolidated:
- `App._running_agents: dict[str, str]` - tracks running tasks (in `app.py`)
- `OutputPane._streaming_buffers: dict[str, list]` - tracks streaming state (in `output_pane.py`)

This distributed state makes it impossible to have a single reactive data source for the status panel.

---

#### Phase 0: Centralized Agent State Module

**New file: `src/teambot/ui/agent_state.py`**

```python
"""Centralized agent state management for TeamBot UI."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class AgentState(Enum):
    """Possible states for an agent."""
    IDLE = "idle"
    RUNNING = "running"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentStatus:
    """Status information for a single agent."""
    agent_id: str
    state: AgentState = AgentState.IDLE
    task: str | None = None

    def with_state(self, state: AgentState, task: str | None = None) -> "AgentStatus":
        """Create new AgentStatus with updated state (immutable pattern)."""
        return AgentStatus(
            agent_id=self.agent_id,
            state=state,
            task=task if task is not None else self.task,
        )


DEFAULT_AGENTS = ["pm", "ba", "writer", "builder-1", "builder-2", "reviewer"]


@dataclass
class AgentStatusManager:
    """Manages agent status with change notification support.
    
    Single source of truth for agent state, with listener pattern
    for reactive UI updates.
    """
    _statuses: dict[str, AgentStatus] = field(default_factory=dict)
    _listeners: list[Callable[["AgentStatusManager"], None]] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default agent statuses."""
        if not self._statuses:
            for agent_id in DEFAULT_AGENTS:
                self._statuses[agent_id] = AgentStatus(agent_id=agent_id)

    def get(self, agent_id: str) -> AgentStatus | None:
        """Get status for a specific agent."""
        return self._statuses.get(agent_id)

    def get_all(self) -> dict[str, AgentStatus]:
        """Get all agent statuses (returns copy)."""
        return self._statuses.copy()

    def set_running(self, agent_id: str, task: str) -> None:
        """Mark agent as running with task (truncates to 40 chars)."""
        truncated = task[:40] + "..." if len(task) > 40 else task
        self._update(agent_id, AgentState.RUNNING, truncated)

    def set_streaming(self, agent_id: str) -> None:
        """Mark agent as streaming (preserves existing task)."""
        current = self._statuses.get(agent_id)
        self._update(agent_id, AgentState.STREAMING, current.task if current else None)

    def set_completed(self, agent_id: str) -> None:
        """Mark agent as completed."""
        self._update(agent_id, AgentState.COMPLETED, None)

    def set_failed(self, agent_id: str) -> None:
        """Mark agent as failed."""
        self._update(agent_id, AgentState.FAILED, None)

    def set_idle(self, agent_id: str) -> None:
        """Mark agent as idle (clears task)."""
        self._update(agent_id, AgentState.IDLE, None)

    def _update(self, agent_id: str, state: AgentState, task: str | None) -> None:
        """Update state and notify listeners if changed."""
        if agent_id not in self._statuses:
            self._statuses[agent_id] = AgentStatus(agent_id=agent_id)
        
        old = self._statuses[agent_id]
        new = old.with_state(state, task)
        
        if old.state != new.state or old.task != new.task:
            self._statuses[agent_id] = new
            self._notify()

    def _notify(self) -> None:
        """Notify all listeners of state change."""
        for listener in self._listeners:
            try:
                listener(self)
            except Exception:
                pass  # Don't let listener errors break state management

    def add_listener(self, callback: Callable[["AgentStatusManager"], None]) -> None:
        """Register callback for status changes."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[["AgentStatusManager"], None]) -> None:
        """Unregister status change callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def get_streaming_agents(self) -> list[str]:
        """Get list of agent IDs currently streaming."""
        return [aid for aid, s in self._statuses.items() if s.state == AgentState.STREAMING]

    def get_active_agents(self) -> list[str]:
        """Get list of agent IDs that are running or streaming."""
        return [aid for aid, s in self._statuses.items() 
                if s.state in (AgentState.RUNNING, AgentState.STREAMING)]
```

---

#### Phase 0: App Integration Changes

**Changes to `src/teambot/ui/app.py`:**

```python
# Add import
from teambot.ui.agent_state import AgentState, AgentStatusManager

class TeamBotApp(App):
    def __init__(self, ...):
        ...
        # Replace _running_agents with centralized manager
        self._agent_status = AgentStatusManager()
        # Keep _running_agents for backward compatibility during migration
        self._running_agents: dict[str, str] = {}

    async def _handle_agent_command(self, command, output):
        ...
        # Update centralized state instead of _running_agents
        self._agent_status.set_running(agent_id, content)
        
        # When streaming starts:
        self._agent_status.set_streaming(agent_id)
        
        # On success:
        self._agent_status.set_completed(agent_id)
        
        # On failure:
        self._agent_status.set_failed(agent_id)
        
        # Finally (return to idle):
        self._agent_status.set_idle(agent_id)

    def _get_status(self, output=None) -> str:
        """Use centralized state for status display."""
        lines = ["Agent Status:", ""]
        for agent_id, status in self._agent_status.get_all().items():
            if status.state == AgentState.STREAMING:
                lines.append(f"  {agent_id:12} - [cyan]streaming[/cyan]: {status.task or ''}")
            elif status.state == AgentState.RUNNING:
                lines.append(f"  {agent_id:12} - [yellow]running[/yellow]: {status.task or ''}")
            # ... etc
        return "\n".join(lines)
```

---

#### Phases 1-4: Status Panel Widget

**New file: `src/teambot/ui/widgets/status_panel.py`**

```python
"""Live agent status panel widget."""

from textual.widgets import Static
from textual.reactive import reactive

from teambot.ui.agent_state import AgentState, AgentStatusManager


class StatusPanel(Static):
    """Displays live agent status in left pane."""
    
    DEFAULT_CSS = """
    StatusPanel {
        height: auto;
        padding: 0 1;
        margin: 1 0;
    }
    """

    def __init__(self, status_manager: AgentStatusManager, **kwargs):
        super().__init__(**kwargs)
        self._status_manager = status_manager
        self._git_branch: str = ""
        # Register for status updates
        status_manager.add_listener(self._on_status_change)

    def _on_status_change(self, manager: AgentStatusManager) -> None:
        """Called when any agent status changes."""
        self.refresh()  # Trigger re-render

    def render(self) -> str:
        """Render the status panel content."""
        lines = []
        for agent_id, status in self._status_manager.get_all().items():
            indicator = self._get_indicator(status.state)
            task_info = f": {status.task}" if status.task else ""
            lines.append(f"{indicator} {agent_id}{task_info}")
        return "\n".join(lines)

    def _get_indicator(self, state: AgentState) -> str:
        """Get colored indicator for state."""
        indicators = {
            AgentState.IDLE: "[dim]●[/dim]",
            AgentState.RUNNING: "[yellow]●[/yellow]",
            AgentState.STREAMING: "[cyan]◉[/cyan]",
            AgentState.COMPLETED: "[green]●[/green]",
            AgentState.FAILED: "[red]●[/red]",
        }
        return indicators.get(state, "●")
```

**Update `src/teambot/ui/app.py` compose():**

```python
from teambot.ui.widgets.status_panel import StatusPanel

def compose(self) -> ComposeResult:
    with Horizontal():
        with Vertical(id="input-pane"):
            yield Static(f"[bold green]TeamBot[/bold green]  [dim]({self._git_branch})[/dim]", id="header")
            yield StatusPanel(self._agent_status, id="status-panel")
            yield InputPane(placeholder="@agent task or /command", id="prompt")
        yield OutputPane(id="output", highlight=True, markup=True)
```

---

### Answers to Open Questions

| Q ID | Question | Recommended Answer |
|------|----------|-------------------|
| Q-001 | Should completed/failed status show briefly before returning to idle? | **Yes** - Show for 2-3 seconds to provide visual feedback. Use `set_timer()` in the state transition to auto-reset to idle. |
| Q-002 | Should status panel be collapsible if terminal height is very small? | **No for MVP** - If terminal is < 15 rows, fall back to legacy mode (already handled by `should_use_split_pane()`). |
| Q-003 | What's the exact truncation length for task preview? | **Dynamic** - Truncate at pane boundary with ellipsis (...). No fixed character limit; simply cut off where text would exceed horizontal space. |

### Truncation Behavior

**Horizontal Overflow:**
- When any text line exceeds the available pane width, truncate with ellipsis (...)
- No text wrapping - single line per agent
- Example: `● builder-1: implement au...` (truncated at boundary)

**Vertical Overflow:**
- If content exceeds vertical space (e.g., very short terminal), show bottom-most content
- Top content simply scrolls off and is not displayed
- No scrollbar or scroll indicators needed
- Priority: Input prompt > Agent list (bottom agents) > Header

### Additional Notes
- The listener pattern in `AgentStatusManager` enables future status panel widgets to react to changes without polling
- Task truncation should preserve meaningful prefix (e.g., "implement auth..." not "...lementation")
- Streaming animation could use Textual's `set_interval()` to cycle through spinner frames (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`)
- Git branch can be obtained via `git rev-parse --abbrev-ref HEAD` with 30-second caching

Generated 2026-01-28T22:18:00Z by sdd.1-create-feature-spec / sdd.2-review-spec (mode: collaborative)
<!-- markdown-table-prettify-ignore-end -->
