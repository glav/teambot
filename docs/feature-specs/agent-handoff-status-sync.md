# Agent Handoff Status Synchronization - Feature Specification

Version 1.0 | Status: Draft | Priority: P0 | Parent: live-agent-status-panel.md

---

## 1. Executive Summary

### Context

The Live Agent Status Panel (see `live-agent-status-panel.md`) provides persistent visibility into agent states. However, during **multi-agent workflows** where one agent hands off work to another (e.g., `@pm` delegates to `@ba`), the status panel fails to update, leaving users unaware of which agent is currently active.

### Problem Statement

When an agent hands off to another agent, the left-side status panel does not reflect the transition. Users observe activity in the output pane from multiple agents but cannot correlate this with the status panel, breaking situational awareness.

### Example Scenario

1. User executes: `@pm tell me a joke`
2. PM processes request and hands off to BA for review
3. **Output pane**: Correctly shows PM → BA activity sequence
4. **Status panel**: Remains stale, does not show BA as active

### Goals

| Goal ID | Statement | Priority |
|---------|-----------|----------|
| G-001 | Status panel updates in real-time during agent handoffs | P0 |
| G-002 | Users can visually track which agent is currently active | P0 |
| G-003 | Handoff transitions are clearly indicated | P1 |

---

## 2. Problem Definition

### Current Behavior

- `TaskExecutor` and `TaskManager` do not integrate with `AgentStatusManager`
- Status updates only occur from `TeamBotApp._handle_agent_command()`
- Handoff-triggered tasks bypass the status notification flow
- Status panel remains frozen on the initial agent

### Root Cause

The `AgentStatusManager._notify()` listener pattern works correctly when called. The issue is that **executor callbacks for handoff tasks do not call the status manager** to update agent states.

### Impact

- Users lose track of workflow progress during multi-agent operations
- Contradictory information between output pane and status panel
- Reduced trust in status panel accuracy
- Defeats the purpose of persistent status visibility

---

## 3. Requirements

### Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-001 | Status panel updates when any agent transitions state | P0 | Panel reflects state change within 500ms |
| FR-002 | Handoff from agent A to agent B updates both agents | P0 | A shows COMPLETED/IDLE, B shows RUNNING |
| FR-003 | All state transitions trigger status updates | P0 | IDLE→RUNNING→STREAMING→COMPLETED/FAILED→IDLE all update |
| FR-004 | Handoff indicator displays during transition | P1 | Visual arrow/animation shows A → B handoff |

### Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-001 | Status updates occur within 500ms of actual state change | P0 |
| NFR-002 | No additional user action required to see updates | P0 |
| NFR-003 | Works for all 6 agent personas | P0 |

---

## 4. Scope

### In Scope

- Integrating `TaskExecutor` callbacks with `AgentStatusManager`
- Ensuring handoff-triggered tasks update agent status
- Updating previous agent to COMPLETED when handoff occurs
- Updating new agent to RUNNING when handoff task starts

### Out of Scope

- Changes to output pane behavior (already working)
- New status states beyond existing (IDLE, RUNNING, STREAMING, COMPLETED, FAILED)
- Modifications to the `/status` command

---

## 5. User Stories

### US-001: Real-time Handoff Visibility

**As a** TeamBot user  
**I want** the status panel to update when agents hand off to each other  
**So that** I always know which agent is currently working on my request

**Acceptance Criteria:**
- [ ] When PM hands off to BA, PM shows COMPLETED and BA shows RUNNING
- [ ] Status panel updates within 500ms of handoff
- [ ] Works for any agent-to-agent handoff combination

### US-002: Multi-Agent Workflow Tracking

**As a** user running complex multi-agent workflows  
**I want** to see the progression through multiple agents in the status panel  
**So that** I can monitor workflow progress at a glance

**Acceptance Criteria:**
- [ ] Sequential handoffs (A→B→C) update panel at each transition
- [ ] Parallel agent work shows multiple agents as RUNNING
- [ ] Final agent completion shows all agents return to IDLE

---

## 6. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| `live-agent-status-panel.md` | Parent Feature | Complete |
| `AgentStatusManager` | Component | Exists |
| `TaskExecutor` | Component | Requires Integration |
| `OverlayRenderer.set_pipeline_progress()` | Component | May need updates |

---

## 7. Test Strategy

### Test Cases

| ID | Scenario | Expected Result |
|----|----------|-----------------|
| TC-001 | Single agent task (no handoff) | Status updates correctly (baseline) |
| TC-002 | PM → BA handoff | PM shows COMPLETED, BA shows RUNNING |
| TC-003 | Three-agent chain (PM → BA → Builder) | Each transition updates panel |
| TC-004 | Parallel agents | Both show RUNNING simultaneously |
| TC-005 | Handoff with failure | Previous agent COMPLETED, new agent FAILED |

---

## 8. Implementation Notes

**For Builder Agents:**

Key integration points identified:
1. `src/teambot/ui/agent_state.py` - `AgentStatusManager` (works correctly)
2. `src/teambot/ui/app.py` - `_handle_agent_command()` (current status updates)
3. Task executor callbacks - **Missing integration point**
4. `src/teambot/visualization/overlay.py` - `on_task_started()` (line 525-527)

The executor callbacks need to call `AgentStatusManager.set_running()`, `set_streaming()`, `set_completed()`, etc. when handling handoff-triggered tasks.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-04 | BA Agent | Initial draft |
