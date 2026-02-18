# Research Summary: @notify Command Mode Bypass

**Full Research Document**: `.agent-tracking/research/20260218-notify-bypass-mode-filtering-research.md`

---

## 🎯 Problem

The `@notify <msg>` command currently respects `notification_mode` filtering. When a channel uses `notification_mode: stages_only` or `agent_status`, the `custom_message` event type is filtered out, causing `@notify` to silently fail.

**Expected behavior**: `@notify` should **always** send when notifications are enabled and channels are configured, bypassing mode filtering.

---

## ✅ Recommended Solution

**Location**: `src/teambot/notifications/config.py` → `_create_channel()` function (Lines 128-138)

**Change**: After mode-based event set resolution, always add `custom_message` to the subscribed events set.

```python
# After line 137 in config.py:
if subscribed is not None:
    subscribed.add("custom_message")
```

**Why this works**:
- Explicit `events: []` still blocks everything (subscribed is empty set, not None)
- Explicit `events: [custom_message]` unchanged (events array takes precedence)
- `notification_mode: all` unchanged (subscribed is None = accept all)
- `notification_mode: stages_only/agent_status` now includes `custom_message` ✅

---

## 📁 Files to Modify

| File | Change |
|------|--------|
| `src/teambot/notifications/config.py` | Add `custom_message` to mode-based subscribed sets |
| `tests/test_notifications/test_config.py` | Add `TestCustomMessageBypassMode` test class |

---

## 🧪 Test Cases Required

1. `stages_only` mode includes `custom_message`
2. `agent_status` mode includes `custom_message`
3. Explicit `events: []` still blocks `custom_message`
4. `notification_mode: all` unchanged (accepts everything)

---

## 📊 Entry Points Verified

All `@notify` entry points converge at `executor.py:_handle_notify()` → `event_bus.emit_sync()` → `channel.supports_event()`. The fix location covers all paths.

---

## ➡️ Next Steps

1. Run **Step 4** (`sdd.4-determine-test-strategy.prompt.md`) to create formal test strategy
2. After test strategy approval, proceed to **Step 5** (`sdd.5-task-planner-for-feature.prompt.md`)
