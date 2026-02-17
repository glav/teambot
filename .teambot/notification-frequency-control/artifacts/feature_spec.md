<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Notification Frequency Control - Feature Specification Document
Version 1.0 | Status **Draft** | Owner TBD | Team TeamBot | Target 0.3.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-02-17 |
| Problem & Users | 100% | None | 2026-02-17 |
| Scope | 100% | None | 2026-02-17 |
| Requirements | 100% | None | 2026-02-17 |
| Metrics & Risks | 100% | None | 2026-02-17 |
| Research | 0% | Pending implementation | 2026-02-17 |
| Test Strategy | 100% | None | 2026-02-17 |
| Task Planning | 0% | Pending implementation | 2026-02-17 |
| Finalization | 0% | Pending implementation | 2026-02-17 |
Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context
TeamBot's real-time notification system (introduced in v0.2.0) currently offers only two approaches for filtering notifications: receive all events (default) or manually specify individual event types in an `events` array. This creates friction for users who want meaningful notification control without memorizing internal event names.

### Core Opportunity
Implement **notification mode presets** — named, semantic groupings of event types that allow users to configure notification verbosity with a single setting:

1. `stages_only` — Receive only workflow stage transitions (lowest volume)
2. `agent_status` — Receive stage events plus agent lifecycle updates (medium volume)
3. `all` — Receive all notification events (current default, highest volume)

This transforms notification configuration from a technical exercise into an intuitive choice based on user needs.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-NFC-001 | Reduce notification fatigue for users who only need high-level progress | UX | All events or manual filtering | 60-80% fewer notifications with `stages_only` | MVP | P0 |
| G-NFC-002 | Simplify notification configuration | UX | Requires knowledge of event names | Single `notification_mode` setting | MVP | P0 |
| G-NFC-003 | Enable per-channel verbosity control | Flexibility | Same events to all channels | Different modes per channel | MVP | P0 |
| G-NFC-004 | Preserve backwards compatibility | Stability | N/A | Existing configs unchanged | MVP | P0 |
| G-NFC-005 | Self-documenting configuration | UX | Opaque event names | Semantic mode names | MVP | P1 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Define mode-to-events mapping | Constant dict maps modes to event sets | P0 | TBD |
| Implement mode expansion in config.py | `notification_mode` expands to event set | P0 | TBD |
| Add precedence logic | `events` array overrides `notification_mode` | P0 | TBD |
| Extend `teambot init` wizard | Mode selection step added | P1 | TBD |
| Update documentation | README and config schema updated | P1 | TBD |
| Add validation | Invalid mode values produce clear errors | P0 | TBD |

---

## 2. Problem Definition

### Current Situation
- **Notification system exists**: EventBus with TelegramChannel implemented in v0.2.0
- **Binary filtering**: Users either receive all events or manually list individual event types
- **Event knowledge required**: To filter, users must know internal event names like `stage_changed`, `agent_running`, etc.
- **No semantic grouping**: No way to express "notify me only when stages change"
- **Same verbosity everywhere**: All channels receive the same events unless manually configured differently

### Problem Statement
Users running multi-stage, multi-agent workflows receive excessive notifications (50+ per workflow run), causing notification fatigue. The current configuration requires technical knowledge of event internals to reduce volume. There is no simple way to say "I only want stage-level updates" without listing specific event types.

### Root Causes
* Initial notification system designed for completeness, not volume control
* Event taxonomy not exposed as user-facing concepts
* No abstraction layer between user intent and event filtering
* Per-channel configuration exists but requires identical manual effort per channel

### Impact of Inaction
* Users disable notifications entirely due to volume
* Mobile users overwhelmed by frequent buzzes
* Critical events (failures, stage changes) buried in routine updates
* Adoption friction for users expecting "set verbosity level" UX pattern
* Support burden explaining event type names

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| **Project Manager** | Know when stages complete, don't care about agent details | Receives 50+ messages per workflow | High - needs `stages_only` |
| **DevOps/Ops Team** | Monitor agent health, catch failures quickly | Must track agent lifecycle without noise | High - needs `agent_status` |
| **Developer (debugging)** | Full visibility into every event | No pain point with current `all` default | Low - current behavior works |
| **Mobile User** | Minimal interruptions, critical updates only | Phone buzzes constantly during workflow | High - needs `stages_only` |
| **Team Channel Admin** | Configure appropriate verbosity for team channel | Must manually curate event lists | Medium - needs simple presets |

### User Journeys

#### Journey 1: Project Manager — Stage-Level Visibility
1. PM runs `teambot init` to configure notifications
2. Selects `stages_only` mode when prompted
3. Starts long workflow: `teambot run objectives/feature.md`
4. Phone receives: "🚀 Starting: Feature Development"
5. Phone receives: "📌 Stage: SPEC" (only when stages change)
6. Phone receives: "✅ Completed: Feature Development"
7. Total notifications: 16 (one per stage + start/end) instead of 50+

#### Journey 2: Ops Team — Agent Health Monitoring
1. Ops engineer configures `agent_status` mode on ops channel
2. Same workflow runs
3. Channel receives stage transitions AND agent lifecycle events
4. "🔄 builder-1 started" / "✅ builder-1 completed"
5. "❌ reviewer FAILED" — immediate visibility for intervention
6. Total notifications: ~30 (stages + agent events)

#### Journey 3: Existing User — No Changes Required
1. User has existing `teambot.json` with `events: ["stage_changed", "agent_failed"]`
2. Updates TeamBot to new version
3. Configuration continues to work exactly as before
4. No migration needed, no behavior changes

---

## 4. Scope

### In Scope
* **Notification mode presets**: Define `NOTIFICATION_MODES` constant mapping mode names to event sets
* **Mode expansion logic**: In `_create_channel()`, expand `notification_mode` to `subscribed_events` set
* **Precedence rules**: Explicit `events` array overrides `notification_mode`; missing both defaults to `all`
* **Configuration validation**: Invalid mode values raise `ValueError` with clear message
* **Init wizard extension**: Add mode selection step to notification setup flow
* **Documentation updates**: README notifications section, config schema documentation
* **Unit tests**: Cover all modes, precedence logic, validation, edge cases

### Out of Scope (This Phase)
* **Custom mode definitions**: Users cannot define their own named presets
* **Dynamic mode switching**: Mode is set at configuration time, not runtime
* **Event aggregation/batching**: Reducing frequency by grouping rapid events
* **Per-event priority levels**: No "critical only" filtering beyond presets
* **UI for mode selection**: CLI wizard only; no web/GUI configuration
* **Mode inheritance**: No global mode that channels inherit from

### Assumptions
1. Three modes (`stages_only`, `agent_status`, `all`) cover primary use cases
2. Users understand the hierarchy: `stages_only` ⊂ `agent_status` ⊂ `all`
3. Named presets are preferable to numeric verbosity levels (1/2/3)
4. Existing notification channel infrastructure (`subscribed_events`) supports this without modification
5. Init wizard is the appropriate place for mode selection (vs. separate command)

### Constraints
* **No breaking changes**: Existing `events` array configurations must work unchanged
* **Minimal code impact**: Changes isolated to `config.py` and `cli.py`
* **Extensible design**: Adding future event types to mode presets requires only constant updates
* **Clear error messages**: Invalid mode values must produce actionable error text

---

## 5. Product Overview

### Value Proposition
**For TeamBot users** who want notification control without technical complexity, **Notification Frequency Control** provides intuitive mode presets (`stages_only`, `agent_status`, `all`) that reduce configuration effort from "memorize 10+ event names" to "choose your verbosity level."

### Differentiators
* **Semantic naming**: Mode names describe behavior, not implementation
* **Per-channel flexibility**: Different channels can have different modes
* **Zero migration**: Existing configurations continue to work
* **Extensible**: New event types automatically included in `all`; easy to update presets

### Configuration Schema

#### New `notification_mode` Field
```json
{
  "notifications": {
    "enabled": true,
    "channels": [
      {
        "type": "telegram",
        "token": "${TELEGRAM_TOKEN}",
        "chat_id": "${TELEGRAM_PM_CHAT}",
        "notification_mode": "stages_only"
      },
      {
        "type": "telegram",
        "token": "${TELEGRAM_TOKEN}",
        "chat_id": "${TELEGRAM_OPS_CHAT}",
        "notification_mode": "agent_status"
      },
      {
        "type": "telegram",
        "token": "${TELEGRAM_TOKEN}",
        "chat_id": "${TELEGRAM_DEBUG_CHAT}",
        "notification_mode": "all"
      }
    ]
  }
}
```

#### Precedence Examples
```json
// Example 1: Mode only — expands to preset events
{ "notification_mode": "stages_only" }
// → subscribed_events = {"stage_changed", "orchestration_started", "orchestration_completed"}

// Example 2: Events only — uses explicit list (existing behavior)
{ "events": ["stage_changed", "agent_failed"] }
// → subscribed_events = {"stage_changed", "agent_failed"}

// Example 3: Both specified — events wins
{ "notification_mode": "all", "events": ["agent_failed"] }
// → subscribed_events = {"agent_failed"}

// Example 4: Neither specified — defaults to all
{ }
// → subscribed_events = None (all events)
```

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance Criteria | Notes |
|-------|-------|-------------|-------|----------|----------|---------------------|-------|
| FR-NFC-001 | Mode Presets Definition | Define `NOTIFICATION_MODES` constant with three modes mapping to event sets | G-NFC-002 | All | P0 | `stages_only` → 3 events, `agent_status` → 6 events, `all` → None (all) | Constant in `config.py` |
| FR-NFC-002 | Mode Expansion | When `notification_mode` is set, expand to corresponding event set | G-NFC-002 | All | P0 | Channel receives only events in expanded set | In `_create_channel()` |
| FR-NFC-003 | Events Precedence | When both `events` and `notification_mode` specified, `events` takes precedence | G-NFC-004 | Existing users | P0 | Explicit `events` array overrides any mode setting | Documented behavior |
| FR-NFC-004 | Default to All | When neither `events` nor `notification_mode` specified, default to all events | G-NFC-004 | Existing users | P0 | Existing configs with no filtering continue to receive all events | Backwards compatible |
| FR-NFC-005 | Mode Validation | Invalid `notification_mode` value raises `ValueError` with clear message | G-NFC-005 | All | P0 | Error message lists valid modes | On config load |
| FR-NFC-006 | Init Wizard Mode Step | `teambot init` notification setup offers mode selection | G-NFC-002 | New users | P1 | Users can select from 3 modes during setup | After channel config |
| FR-NFC-007 | Per-Channel Mode | Each channel can have its own `notification_mode` setting | G-NFC-003 | Team admins | P0 | Different channels receive different event volumes | Independent config |

### Mode-to-Events Mapping

```python
NOTIFICATION_MODES: dict[str, set[str] | None] = {
    "stages_only": {
        "stage_changed",
        "orchestration_started",
        "orchestration_completed",
    },
    "agent_status": {
        "stage_changed",
        "orchestration_started",
        "orchestration_completed",
        "agent_running",
        "agent_complete",
        "agent_failed",
    },
    "all": None,  # None means all events (no filtering)
}
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-NFC-001 | Maintainability | Mode presets defined in single location | One constant dict | P0 | Code review | Easy to update when adding events |
| NFR-NFC-002 | Extensibility | Adding new event to preset requires only constant update | < 5 lines changed | P0 | Change analysis | No logic changes needed |
| NFR-NFC-003 | Usability | Invalid mode error message lists valid options | Error includes `stages_only`, `agent_status`, `all` | P0 | Unit test | Actionable error |
| NFR-NFC-004 | Compatibility | Existing configs work without modification | 100% backwards compatible | P0 | Integration test | No migration required |
| NFR-NFC-005 | Documentation | Mode descriptions in README and config schema | All modes documented | P1 | Doc review | Include use case guidance |

---

## 8. Data & Analytics

### Configuration Data
| Field | Type | Values | Default | Notes |
|-------|------|--------|---------|-------|
| `notification_mode` | string (optional) | `stages_only`, `agent_status`, `all` | N/A (falls through to `all` behavior) | Per-channel setting |
| `events` | array (optional) | List of event type strings | N/A | Existing field, takes precedence |

### Validation Rules
1. If `notification_mode` present, must be one of defined modes
2. If `events` present, used directly (mode ignored)
3. If neither present, all events passed through

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| `src/teambot/notifications/config.py` | Code | High | TBD | Low | Well-isolated changes |
| `src/teambot/notifications/channels/telegram.py` | Code | Low | TBD | Low | No changes needed; receives `subscribed_events` |
| `src/teambot/cli.py` | Code | Medium | TBD | Low | Init wizard extension |
| Existing `subscribed_events` parameter | API | High | TBD | Low | Already supports set filtering |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-NFC-001 | Users confused by mode vs. events | Low | Medium | Clear documentation; `events` precedence is intuitive | TBD | Open |
| R-NFC-002 | Future event types not in presets | Medium | Low | Document process for updating mode definitions; `all` always includes new events | TBD | Open |
| R-NFC-003 | Init wizard becomes too long | Low | Low | Mode selection is single optional step | TBD | Open |
| R-NFC-004 | Mode names not intuitive | Low | Low | Names chosen for clarity; user testing recommended | TBD | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification
* **Configuration data**: Non-sensitive (mode names, event type names)
* **No PII involved**: Feature affects event filtering logic only
* **No new secrets**: Uses existing token/credential infrastructure

### Security Considerations
* Mode names validated against allowlist (no injection risk)
* No change to secret handling (env var resolution unchanged)

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard Python package update | No infrastructure changes |
| Rollback | Previous version works with existing configs | No migration to reverse |
| Monitoring | N/A | No new external dependencies |
| Alerting | N/A | Local config validation only |
| Support | Document mode selection guidance | FAQ: "Which mode should I use?" |

---

## 13. Rollout & Launch Plan

### Phases
| Phase | Description | Gate Criteria | Owner |
|-------|-------------|---------------|-------|
| Implementation | Add mode expansion logic and validation | Unit tests passing | TBD |
| Init Wizard | Extend `teambot init` with mode selection | CLI integration test | TBD |
| Documentation | Update README and config docs | Doc review complete | TBD |
| Release | Include in next minor version | All tests green, docs updated | TBD |

### Feature Flags
None required — feature is backwards compatible by design.

---

## 14. Acceptance Test Scenarios

### AT-NFC-001: Stages Only Mode Filters Correctly
**Description**: User configures `stages_only` mode and receives only stage-level events
**Preconditions**: TeamBot configured with `notification_mode: "stages_only"` on Telegram channel
**Steps**:
1. Start workflow: `teambot run objectives/test.md`
2. Workflow progresses through multiple stages with agent activity
3. Observe notifications received
**Expected Result**: Notifications received only for `stage_changed`, `orchestration_started`, `orchestration_completed`
**Verification**: No `agent_running`, `agent_complete`, or `agent_failed` notifications received

### AT-NFC-002: Agent Status Mode Includes Agent Events
**Description**: User configures `agent_status` mode and receives stage + agent lifecycle events
**Preconditions**: TeamBot configured with `notification_mode: "agent_status"` on Telegram channel
**Steps**:
1. Start workflow: `teambot run objectives/test.md`
2. Workflow progresses with agents starting, completing, and potentially failing
3. Observe notifications received
**Expected Result**: Notifications for stages AND agent lifecycle (`agent_running`, `agent_complete`, `agent_failed`)
**Verification**: Both stage and agent notifications received; other event types (if any) excluded

### AT-NFC-003: Events Array Overrides Mode
**Description**: When both `events` and `notification_mode` specified, `events` takes precedence
**Preconditions**: Channel config has both `notification_mode: "all"` and `events: ["agent_failed"]`
**Steps**:
1. Start workflow that includes agent failures
2. Observe notifications received
**Expected Result**: Only `agent_failed` notifications received
**Verification**: Stage events NOT received despite `all` mode setting

### AT-NFC-004: Backwards Compatibility — No Mode Specified
**Description**: Existing configuration without `notification_mode` continues to work
**Preconditions**: Channel config has no `notification_mode` and no `events` array
**Steps**:
1. Start workflow with existing (pre-feature) configuration
2. Observe notifications received
**Expected Result**: All notification events received (current default behavior)
**Verification**: Behavior identical to v0.2.0

### AT-NFC-005: Invalid Mode Produces Clear Error
**Description**: Invalid `notification_mode` value shows helpful error message
**Preconditions**: Channel config has `notification_mode: "invalid_mode"`
**Steps**:
1. Run `teambot run` or load config
**Expected Result**: `ValueError` raised with message listing valid modes
**Verification**: Error message includes `stages_only`, `agent_status`, `all`

### AT-NFC-006: Init Wizard Mode Selection
**Description**: `teambot init` offers mode selection during notification setup
**Preconditions**: Running `teambot init` with Telegram notification setup
**Steps**:
1. Run `teambot init`
2. Complete Telegram channel configuration
3. Observe mode selection prompt
**Expected Result**: User presented with mode choices and description of each
**Verification**: Selected mode written to `teambot.json` correctly

### AT-NFC-007: Per-Channel Independent Modes
**Description**: Different channels can have different modes
**Preconditions**: Two Telegram channels configured with different modes
**Steps**:
1. Configure channel A with `stages_only`, channel B with `all`
2. Start workflow
3. Observe notifications on both channels
**Expected Result**: Channel A receives stage events only; Channel B receives all events
**Verification**: Event counts differ between channels as expected

---

## 15. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| — | None | — | — | — |

All questions resolved during specification phase.

---

## 16. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-17 | BA Agent | Initial specification | Created |

---

## 17. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|---------------------|
| REF-001 | Specification | `docs/feature-specs/realtime-notifications.md` | Original notification system spec | N/A |
| REF-002 | Code | `src/teambot/notifications/config.py` | Current config loading implementation | N/A |
| REF-003 | Code | `src/teambot/notifications/templates.py` | Event types and templates | N/A |
| REF-004 | Problem Statement | `.teambot/notification-frequency-control/artifacts/problem_statement.md` | Business problem definition | N/A |

---

## Appendix A: Event Type Inventory

Current event types emitted by TeamBot:

| Event Type | Description | Included In |
|------------|-------------|-------------|
| `orchestration_started` | Workflow begins | `stages_only`, `agent_status`, `all` |
| `orchestration_completed` | Workflow ends | `stages_only`, `agent_status`, `all` |
| `stage_changed` | Stage transition | `stages_only`, `agent_status`, `all` |
| `agent_running` | Agent starts task | `agent_status`, `all` |
| `agent_complete` | Agent finishes task | `agent_status`, `all` |
| `agent_failed` | Agent task fails | `agent_status`, `all` |
| `parallel_group_start` | Parallel stage group begins | `all` |
| `parallel_group_complete` | Parallel stage group ends | `all` |
| `parallel_stage_complete` | Individual parallel stage completes | `all` |
| `parallel_stage_failed` | Individual parallel stage fails | `all` |
| `acceptance_test_stage_complete` | Acceptance tests finish | `all` |
| `acceptance_test_max_iterations_reached` | Max fix iterations hit | `all` |
| `review_progress` | Review stage progress | `all` |
| `custom_message` | Custom notification | `all` |

---

## Appendix B: Implementation Notes

### Recommended Code Location
```
src/teambot/notifications/config.py:
  - Add NOTIFICATION_MODES constant (top of file)
  - Modify _create_channel() to expand mode to events

src/teambot/cli.py:
  - Extend notification setup wizard in init flow
```

### Validation Implementation
```python
def _expand_notification_mode(mode: str) -> set[str] | None:
    """Expand notification mode to event set."""
    if mode not in NOTIFICATION_MODES:
        valid_modes = ", ".join(sorted(NOTIFICATION_MODES.keys()))
        raise ValueError(
            f"Invalid notification_mode '{mode}'. "
            f"Valid modes: {valid_modes}"
        )
    return NOTIFICATION_MODES[mode]
```

<!-- markdown-table-prettify-ignore-end -->
