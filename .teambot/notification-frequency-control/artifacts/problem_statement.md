# Business Problem Statement: Notification Frequency Control

## Problem Definition

**Current State:**

TeamBot's notification system currently provides only two filtering approaches:
1. **All events** — Users receive every notification event (default when no `events` array is specified)
2. **Explicit event list** — Users must manually specify individual event types in an `events` array

This creates friction for users who want meaningful notification control without needing to understand the internal event taxonomy.

**Pain Points:**

| Issue | Impact |
|-------|--------|
| **Notification fatigue** | Users monitoring long-running workflows receive high volumes of messages, reducing signal-to-noise ratio |
| **Configuration complexity** | Specifying individual event names requires documentation lookup and is error-prone |
| **Lack of semantic grouping** | No intuitive way to say "notify me only when stages change" or "notify me of agent failures" |
| **Channel inflexibility** | Users who want different verbosity levels on different channels must manually curate separate event lists |

**Example Scenario:**

A user runs a 14-stage workflow with multiple agents per stage. With the current "all events" default:
- They receive ~50+ notifications per workflow run
- Critical events (stage changes, failures) are buried in routine updates
- Mobile users especially suffer from notification overload

---

## Business Goals

| # | Goal | Measurable Outcome |
|---|------|--------------------|
| 1 | **Reduce notification fatigue** | Users can receive 60-80% fewer notifications with `stages_only` mode |
| 2 | **Simplify configuration** | Users select from 3 named presets instead of memorizing 10+ event types |
| 3 | **Enable per-channel granularity** | Different channels (e.g., Telegram personal vs. team) can have different verbosity levels |
| 4 | **Preserve backwards compatibility** | Existing configurations continue to work without modification |
| 5 | **Self-documenting configuration** | Mode names (`stages_only`, `agent_status`, `all`) clearly communicate behavior |

---

## Stakeholders

| Stakeholder | Interest |
|-------------|----------|
| **End Users** | Less noise, actionable notifications, simple configuration |
| **DevOps/Ops Teams** | Clear stage-level visibility without agent-level chatter |
| **Developers** | Full visibility when debugging agent behavior |
| **Project Managers** | High-level progress tracking without technical detail |

---

## Proposed Solution Overview

Introduce a `notification_mode` configuration option per notification channel with three preset values:

### Mode Definitions

| Mode | Events Included | Use Case |
|------|-----------------|----------|
| `stages_only` | `stage_changed`, `orchestration_started`, `orchestration_completed` | Executive/PM visibility — know when stages change |
| `agent_status` | All `stages_only` events + `agent_running`, `agent_complete`, `agent_failed` | Ops/developer monitoring — track agent lifecycle |
| `all` | All notification events | Full debugging — see everything (current default) |

### Precedence Rules

1. If `events` array is specified → use explicit event list (backwards compatibility)
2. Else if `notification_mode` is specified → expand to preset event list
3. Else → default to `all` mode (backwards compatibility)

### Configuration Example

```json
{
  "notifications": {
    "enabled": true,
    "channels": [
      {
        "type": "telegram",
        "token": "${TELEGRAM_TOKEN}",
        "chat_id": "${TELEGRAM_CHAT_ID}",
        "notification_mode": "stages_only"
      },
      {
        "type": "telegram",
        "token": "${TELEGRAM_TOKEN}",
        "chat_id": "${TELEGRAM_OPS_CHAT_ID}",
        "notification_mode": "agent_status"
      }
    ]
  }
}
```

---

## Success Criteria

| # | Criterion | Validation Method |
|---|-----------|-------------------|
| 1 | `notification_mode` accepts `stages_only`, `agent_status`, `all` | Unit tests verify mode parsing |
| 2 | `stages_only` emits exactly: `stage_changed`, `orchestration_started`, `orchestration_completed` | Unit test with mock channel |
| 3 | `agent_status` emits: stages_only events + `agent_running`, `agent_complete`, `agent_failed` | Unit test with mock channel |
| 4 | `all` emits all events (unchanged behavior) | Regression test |
| 5 | Explicit `events` array overrides `notification_mode` | Precedence unit test |
| 6 | Missing both `notification_mode` and `events` defaults to `all` | Backwards compatibility test |
| 7 | Invalid `notification_mode` value produces clear error message | Validation test |
| 8 | `teambot init` wizard offers mode selection | CLI integration test |
| 9 | Documentation updated with mode descriptions | Documentation review |

---

## Constraints & Assumptions

### Constraints

- **No breaking changes** — Existing `events` array configurations must work unchanged
- **Minimal code impact** — Changes isolated to config loading and channel instantiation
- **Extensible design** — Adding future event types to mode presets should require only constant updates

### Assumptions

- Users understand the hierarchy: `stages_only` ⊂ `agent_status` ⊂ `all`
- Named presets are preferable to numeric verbosity levels for discoverability
- The three proposed modes cover the primary use cases identified from user feedback

---

## Out of Scope

The following are explicitly excluded from this feature:

- **Custom mode definitions** — Users cannot define their own named presets
- **Dynamic mode switching** — Mode is set at configuration time, not runtime
- **Event aggregation/batching** — Reducing notification frequency by grouping events
- **New notification channels** — This feature only affects event filtering, not channel types
- **Event priority levels** — No "critical only" filtering beyond the defined presets

---

## Dependencies

| Dependency | Impact |
|------------|--------|
| `src/teambot/notifications/config.py` | Mode expansion logic added here |
| `src/teambot/notifications/channels/telegram.py` | Receives expanded event set |
| `src/teambot/cli.py` | Init wizard updated for mode selection |
| `teambot.json` schema | New `notification_mode` field documented |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Users confused by mode vs. events | Medium | Low | Clear documentation; `events` takes precedence |
| Future event types not in presets | Low | Medium | Document process for updating mode definitions |
| Init wizard complexity increases | Low | Low | Mode selection is single optional step |

---

## Document Metadata

| Field | Value |
|-------|-------|
| Author | Business Analyst Agent |
| Stage | BUSINESS_PROBLEM |
| Created | 2026-02-17 |
| Status | Draft |
