## Objective

- Ensure `@notify <msg>` always sends a notification regardless of the `notification_mode` setting, since it represents an explicit user request to send a message.

**Goal**:

- The `@notify <msg>` command should always deliver notifications when notifications are enabled and configured, bypassing `notification_mode` filtering.
- Currently, file-based orchestration uses `notification_mode` (e.g., `stages_only`, `agent_status`, `all`) to control notification frequency and reduce noise from automated events.
- However, `@notify <msg>` is an explicit user request to send a specific message, which is fundamentally different from automated workflow events.
- The `custom_message` event type (used by `@notify`) should bypass mode-based filtering entirely.
- The only conditions under which `@notify` should NOT send are:
  1. `notifications.enabled` is `false`
  2. No notification channels are configured
- This change should not affect how `notification_mode` filters other event types — it only creates a special case for explicit `@notify` commands.

**Problem Statement**:

- The current implementation emits `@notify` messages as `custom_message` events through the EventBus.
- When a channel's `notification_mode` is set to `stages_only` or `agent_status`, the `custom_message` event type is filtered out because it's not in those mode's event sets.
- This means users who have set a notification mode to reduce noise are surprised when their explicit `@notify "Build complete!"` commands don't send.
- The filtering behavior makes sense for automated events (stage changes, agent lifecycle) but not for explicit user-initiated notifications.
- Users expect `@notify` to "just work" as long as notifications are turned on.

**Success Criteria**:

- [ ] `@notify <msg>` sends a notification when `notifications.enabled` is `true` and at least one channel is configured, regardless of `notification_mode`.
- [ ] `@notify <msg>` continues to NOT send when `notifications.enabled` is `false` (current behavior preserved).
- [ ] `@notify <msg>` continues to show "No notification channels configured" when enabled but no channels exist (current behavior preserved).
- [ ] The `notification_mode` setting continues to filter other event types (`stage_changed`, `agent_running`, etc.) as before.
- [ ] Unit tests cover the new bypass behavior for `custom_message` events.
- [ ] Existing notification mode tests continue to pass.
- [ ] Documentation is updated to clarify that `@notify` bypasses mode filtering.

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically `src/teambot/tasks/executor.py` (the `_execute_notify()` handler) and `src/teambot/notifications/` module (event filtering logic).

**Primary Language/Framework**:

- Python

**Testing Preference**:

- Follow current pattern (`pytest` with `pytest-mock`)

**Key Constraints**:

- Must not break existing `notification_mode` filtering for automated events.
- Must preserve backwards compatibility — channels using explicit `events` arrays should continue to work as expected.
- The fix should be minimal and surgical — avoid large refactors.

---

## Additional Context

### Current Behavior

When `@notify "message"` is executed in `executor.py`:

```python
event_bus.emit_sync("custom_message", {"message": message})
```

The EventBus routes to channels, which filter based on their `subscribed_events`:

- If `notification_mode: "stages_only"` → `subscribed_events = {"stage_changed", "orchestration_started", "orchestration_completed"}`
- `custom_message` ∉ `subscribed_events` → message is **filtered out**

### Desired Behavior

**Implemented Approach: Bypass filtering during channel creation in `config.py`**

When a `notification_mode` is configured, the `_create_channel()` function in `config.py` expands the mode to a set of event types and then adds `custom_message` to that set before creating the channel. This ensures `custom_message` events (from `@notify` commands) bypass mode filtering while preserving the ability to disable all notifications with an explicit `events: []` configuration:

```python
elif "notification_mode" in resolved:
    # Mode-based filtering
    mode_events = resolve_notification_mode(resolved["notification_mode"])
    subscribed = set(mode_events) if mode_events else None
    # Always allow custom_message for explicit @notify commands
    # This ensures @notify bypasses mode filtering while preserving
    # the ability to disable all notifications with events: []
    if subscribed is not None:
        subscribed.add("custom_message")
```

This approach maintains the existing architecture and respects the configuration precedence:
1. Explicit `events` array (highest priority) — unchanged by this fix
2. `notification_mode` preset expansion — now includes `custom_message`
3. Default to `None` (all events) — unchanged by this fix

### Files Likely to Change

- `src/teambot/notifications/config.py` — Modify `_create_channel()` to add `custom_message` to mode-based event sets
- `tests/test_notifications/test_config.py` — Add unit tests for bypass behavior
- `tests/test_notify_bypass_acceptance.py` — Add acceptance tests for `@notify` command
- `docs/guides/notifications.md` — Document that `@notify` bypasses mode filtering

### Event Reference

| Event Type | Filtered by Mode | Notes |
|------------|------------------|-------|
| `stage_changed` | ✓ | Automated workflow event |
| `orchestration_started` | ✓ | Automated workflow event |
| `orchestration_completed` | ✓ | Automated workflow event |
| `agent_running` | ✓ | Automated workflow event |
| `agent_complete` | ✓ | Automated workflow event |
| `agent_failed` | ✓ | Automated workflow event |
| `custom_message` | ✗ (proposed) | Explicit user request via `@notify` |

**Note**: The `all` mode uses `None` (no filtering), so `custom_message` already works when `notification_mode: "all"`. The issue only manifests with `stages_only` or `agent_status` modes.

---

## Task Breakdown

### Phase 1: Core Fix

- [ ] Identify where event filtering occurs (channel base class or individual channels)
- [ ] Modify filtering logic to always accept `custom_message` events
- [ ] Ensure change applies to all channel types (Telegram, future channels)

### Phase 2: Testing

- [ ] Add unit test: `@notify` sends when `notification_mode: "stages_only"`
- [ ] Add unit test: `@notify` sends when `notification_mode: "agent_status"`
- [ ] Add unit test: `@notify` still blocked when `enabled: false`
- [ ] Add unit test: `@notify` still shows warning when no channels configured
- [ ] Verify existing mode filtering tests still pass

### Phase 3: Documentation

- [ ] Update `docs/guides/notifications.md` to document bypass behavior
- [ ] Add note clarifying difference between automated events and `@notify`

---
