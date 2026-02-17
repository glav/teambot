## Objective

- Provide granular control over notification frequency and event filtering during file-based orchestration runs, reducing notification noise while preserving visibility into critical workflow events.

**Goal**:

- Users should be able to configure which categories of notification events are sent, rather than receiving all events or manually listing individual event types.
- Three notification modes should be supported:
  1. **stages_only** — Notifications for stage start and completion events only (lowest frequency)
  2. **agent_status** — Notifications for agent task lifecycle events (started, completed, failed) in addition to stage events (medium frequency)
  3. **all** — All notification events are sent (current default behavior, highest frequency)
- The notification mode should be configurable per-channel, allowing different channels to receive different levels of detail.
- The configuration should be intuitive and self-documenting, using named presets rather than requiring users to memorize individual event names.
- Backwards compatibility must be preserved — existing configurations with explicit `events` arrays should continue to work.

**Problem Statement**:

- The current notification system sends events for every stage change, agent lifecycle event, parallel execution event, and review iteration — which can result in overwhelming notification volume, especially on longer workflows or channels shared by multiple users.
- Users have no simple way to reduce notification frequency without manually specifying a filtered list of event types in their configuration.
- Different use cases require different notification granularity:
  - A user running TeamBot in the background may only want to know when major stages complete
  - A team monitoring a shared channel may want agent-level visibility for debugging
  - A power user debugging a workflow may want all events
- The current `events` array approach requires users to know all event type names and manually maintain the list.

**Success Criteria**:

- [ ] A new `notification_mode` configuration option is supported in channel configuration with values: `stages_only`, `agent_status`, or `all`.
- [ ] `stages_only` mode sends only: `stage_changed`, `orchestration_started`, `orchestration_completed`.
- [ ] `agent_status` mode sends: all events in `stages_only` plus `agent_running`, `agent_complete`, `agent_failed`.
- [ ] `all` mode sends all notification events (current default behavior).
- [ ] If neither `notification_mode` nor `events` is specified, default to `all` for backwards compatibility.
- [ ] If both `notification_mode` and `events` are specified, `events` takes precedence (explicit filter overrides preset).
- [ ] The `notification_mode` setting is documented in the configuration schema and README.
- [ ] The `teambot init` notification setup wizard offers the mode selection as an additional step.
- [ ] Existing configurations using explicit `events` arrays continue to work unchanged.
- [ ] Unit tests cover all three modes and the precedence logic.
- [ ] Documentation is updated to explain the new modes and when to use each.

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically the notification module (`src/teambot/notifications/`), configuration loading (`src/teambot/notifications/config.py`), event bus (`src/teambot/notifications/event_bus.py`), and CLI init flow (`src/teambot/cli.py`).

**Primary Language/Framework**:

- Python

**Testing Preference**:

- Follow current pattern (`pytest` with `pytest-mock`)

**Key Constraints**:

- Must not break existing notification functionality or configuration formats.
- Must preserve backwards compatibility with existing `events` array configurations.
- The mode presets must be easily extensible if new event types are added in the future.
- Configuration validation should provide clear error messages for invalid mode values.

---

## Additional Context

### Configuration Schema Extension

The existing channel configuration schema:

```json
{
  "notifications": {
    "enabled": true,
    "channels": [
      {
        "type": "telegram",
        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
        "events": ["stage_changed", "agent_complete"],
        "dry_run": false
      }
    ]
  }
}
```

Extended with `notification_mode`:

```json
{
  "notifications": {
    "enabled": true,
    "channels": [
      {
        "type": "telegram",
        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
        "notification_mode": "stages_only",
        "dry_run": false
      }
    ]
  }
}
```

### Event Categories

| Mode | Events Included |
|------|-----------------|
| `stages_only` | `stage_changed`, `orchestration_started`, `orchestration_completed` |
| `agent_status` | All `stages_only` events + `agent_running`, `agent_complete`, `agent_failed` |
| `all` | All `agent_status` events + parallel execution, testing, review, and custom events |

### Complete Event Reference

| Event Type | `stages_only` | `agent_status` | `all` |
|------------|:-------------:|:--------------:|:-----:|
| **Orchestration** | | | |
| `orchestration_started` | ✓ | ✓ | ✓ |
| `orchestration_completed` | ✓ | ✓ | ✓ |
| **Stage Lifecycle** | | | |
| `stage_changed` | ✓ | ✓ | ✓ |
| **Agent Lifecycle** | | | |
| `agent_running` | | ✓ | ✓ |
| `agent_complete` | | ✓ | ✓ |
| `agent_failed` | | ✓ | ✓ |
| **Parallel Execution** | | | |
| `parallel_group_start` | | | ✓ |
| `parallel_group_complete` | | | ✓ |
| `parallel_stage_complete` | | | ✓ |
| `parallel_stage_failed` | | | ✓ |
| **Testing/QA** | | | |
| `acceptance_test_stage_complete` | | | ✓ |
| `acceptance_test_max_iterations_reached` | | | ✓ |
| **Review & Custom** | | | |
| `review_progress` | | | ✓ |
| `custom_message` | | | ✓ |

**Approximate notification counts** (14-stage workflow):
- `stages_only`: ~16 notifications (start + 14 stage changes + complete)
- `agent_status`: ~30-50 notifications (depends on agent count per stage)
- `all`: ~50-100+ notifications (includes parallel groups, review iterations, acceptance loops)

### Precedence Rules

1. If `events` array is specified → use explicit list (existing behavior)
2. If `notification_mode` is specified (and no `events`) → expand to corresponding event list
3. If neither is specified → default to `all` (all events)

### CLI Init Wizard Extension

When configuring notifications, add a step:

```
? Notification frequency:
  ○ stages_only - Only stage start/completion (quietest)
  ○ agent_status - Stage and agent lifecycle events
  ● all - All notification events (default)
```

### Files Likely to Change

- `src/teambot/notifications/config.py` — Add mode expansion logic
- `src/teambot/notifications/events.py` — Define mode-to-events mappings
- `src/teambot/cli.py` — Update init wizard
- `tests/test_notifications/` — Add tests for new modes
- `docs/guides/notifications.md` — Document new configuration option

---
