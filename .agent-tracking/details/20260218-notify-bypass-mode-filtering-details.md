<!-- markdownlint-disable-file -->
# Implementation Details: @notify Command Bypass Mode Filtering

**Research Reference**: `.agent-tracking/research/20260218-notify-bypass-mode-filtering-research.md`
**Test Strategy Reference**: `.teambot/notify-command/artifacts/test_strategy.md`
**Plan Reference**: `.agent-tracking/plans/20260218-notify-bypass-mode-filtering-plan.instructions.md`

---

## Phase 1: Test Setup (TDD)

### Task T1.1: Add `TestCustomMessageBypassMode` Test Class

**File**: `tests/test_notifications/test_config.py`
**Research Reference**: Lines 325-388

#### Test Class Location

Add after existing test classes in the file. Search for the last class definition and add after it.

#### Test Implementation

```python
class TestCustomMessageBypassMode:
    """Tests for custom_message bypass of notification_mode filtering."""

    def test_stages_only_mode_includes_custom_message(self, monkeypatch):
        """custom_message is added to stages_only mode event set."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")
        
        channel_config = {
            "type": "telegram",
            "notification_mode": "stages_only",
        }
        channel = _create_channel(channel_config)
        
        # custom_message should bypass mode filtering
        assert channel.supports_event("custom_message") is True
        # Stage events should still work
        assert channel.supports_event("stage_changed") is True
        # Other events should still be filtered
        assert channel.supports_event("agent_running") is False

    def test_agent_status_mode_includes_custom_message(self, monkeypatch):
        """custom_message is added to agent_status mode event set."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")
        
        channel_config = {
            "type": "telegram",
            "notification_mode": "agent_status",
        }
        channel = _create_channel(channel_config)
        
        # custom_message should bypass mode filtering
        assert channel.supports_event("custom_message") is True
        # Agent status events should work
        assert channel.supports_event("agent_complete") is True
        # Parallel group events should be filtered
        assert channel.supports_event("parallel_group_start") is False

    def test_explicit_empty_events_no_custom_message(self, monkeypatch):
        """Explicit events: [] still blocks everything including custom_message."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")
        
        channel_config = {
            "type": "telegram",
            "events": [],  # Explicitly disable all
        }
        channel = _create_channel(channel_config)
        
        # Explicit empty events array should block everything
        assert channel.supports_event("custom_message") is False
        assert channel.supports_event("stage_changed") is False

    def test_all_mode_unchanged(self, monkeypatch):
        """all mode still accepts everything (subscribed=None)."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")
        
        channel_config = {
            "type": "telegram",
            "notification_mode": "all",
        }
        channel = _create_channel(channel_config)
        
        # All mode accepts everything
        assert channel.supports_event("custom_message") is True
        assert channel.supports_event("any_other_event") is True
```

#### Success Criteria for T1.1

- [ ] Test class added to `test_config.py`
- [ ] 4 test methods present
- [ ] Tests use `monkeypatch` fixture for env vars
- [ ] Tests import `_create_channel` from module

---

## Phase 2: Implementation

### Task T2.1: Modify `_create_channel()` Function

**File**: `src/teambot/notifications/config.py`
**Research Reference**: Lines 403-433

#### Current Code (Lines 128-138)

```python
subscribed: set[str] | None = None

if "events" in resolved:
    # Explicit events array takes precedence
    # Empty list means disable all events
    subscribed = set(resolved["events"]) if resolved["events"] else set()
elif "notification_mode" in resolved:
    # Mode-based filtering
    mode_events = resolve_notification_mode(resolved["notification_mode"])
    subscribed = set(mode_events) if mode_events else None
# else: subscribed=None → accept all events (default, backwards compatible)
```

#### Modified Code

Add the following lines AFTER the mode resolution block (after the `elif "notification_mode"` block, before the comment about `subscribed=None`):

```python
subscribed: set[str] | None = None

if "events" in resolved:
    # Explicit events array takes precedence
    # Empty list means disable all events
    subscribed = set(resolved["events"]) if resolved["events"] else set()
elif "notification_mode" in resolved:
    # Mode-based filtering
    mode_events = resolve_notification_mode(resolved["notification_mode"])
    subscribed = set(mode_events) if mode_events else None
    # Always allow custom_message for explicit @notify commands
    # This ensures @notify bypasses mode filtering while preserving
    # the ability to disable all notifications with events: []
    if subscribed is not None:
        subscribed.add("custom_message")
# else: subscribed=None → accept all events (default, backwards compatible)
```

#### Change Summary

| Location | Change |
|----------|--------|
| After line with `subscribed = set(mode_events)` | Add 4 lines: comment + conditional add |

#### Logic Explanation

1. **Only applies to mode-based filtering**: The code is inside the `elif "notification_mode"` branch
2. **Does not affect explicit `events` arrays**: The `if "events" in resolved` branch is separate
3. **Does not affect `all` mode**: When mode is `all`, `mode_events` returns `None`, so `subscribed` is `None` (no filter)
4. **Preserves empty set behavior**: We only add to `subscribed` if it's not `None` (explicit events can still disable all)

#### Success Criteria for T2.1

- [ ] 4 lines added to `_create_channel()` function
- [ ] Added after mode resolution, inside `elif "notification_mode"` block
- [ ] Comment explains the bypass behavior
- [ ] No syntax errors

---

## Phase 3: Validation

### Task T3.1: Run New Bypass Tests

**Command**:
```bash
uv run pytest tests/test_notifications/test_config.py::TestCustomMessageBypassMode -v
```

**Expected Output**:
```
tests/test_notifications/test_config.py::TestCustomMessageBypassMode::test_stages_only_mode_includes_custom_message PASSED
tests/test_notifications/test_config.py::TestCustomMessageBypassMode::test_agent_status_mode_includes_custom_message PASSED
tests/test_notifications/test_config.py::TestCustomMessageBypassMode::test_explicit_empty_events_no_custom_message PASSED
tests/test_notifications/test_config.py::TestCustomMessageBypassMode::test_all_mode_unchanged PASSED
```

**Success Criteria**:
- [ ] All 4 tests pass
- [ ] No warnings related to the change

### Task T3.2: Run Regression Test Suite

**Command**:
```bash
uv run pytest tests/test_notifications/ -v
```

**Expected Output**:
- All existing tests pass
- No new failures introduced

**Key Test Files to Verify**:
| File | Expected |
|------|----------|
| `test_config.py` | All pass (including new tests) |
| `test_modes.py` | All pass (unchanged) |
| `test_telegram.py` | All pass (unchanged) |
| `test_event_bus.py` | All pass (unchanged) |

**Success Criteria**:
- [ ] All notification tests pass
- [ ] No regressions in mode filtering tests

### Task T3.3: Lint and Format

**Commands**:
```bash
uv run ruff format .
uv run ruff check . --fix
```

**Expected Output**:
- No formatting changes needed (or auto-fixed)
- No lint errors

**Success Criteria**:
- [ ] Code formatted
- [ ] No lint errors

---

## Phase 4: Documentation

### Task T4.1: Update Documentation (If Exists)

**Check for file**:
```bash
ls -la docs/guides/notifications.md 2>/dev/null
```

**If file exists**, add the following section:

```markdown
### @notify Command Behavior

The `@notify <message>` command always delivers notifications when:
- `notifications.enabled` is `true`
- At least one notification channel is configured

The `@notify` command **bypasses** `notification_mode` filtering. This means even with `notification_mode: stages_only`, explicit `@notify` messages will be delivered.

To completely disable `@notify`, either:
- Set `notifications.enabled: false`
- Remove all channel configurations
- Set `events: []` on the channel (explicitly disables all events)
```

**Success Criteria**:
- [ ] Documentation updated if file exists
- [ ] Bypass behavior clearly explained

---

## Implementation Verification

### Final Verification Commands

```bash
# 1. Verify syntax
python -c "from teambot.notifications.config import _create_channel; print('OK')"

# 2. Run all notification tests
uv run pytest tests/test_notifications/ -v

# 3. Run executor tests (verify @notify integration)
uv run pytest tests/test_tasks/test_executor.py -v -k notify

# 4. Lint check
uv run ruff check src/teambot/notifications/config.py
```

### Acceptance Test Verification

After implementation, manually verify these scenarios work:

| Scenario | Expected Result |
|----------|-----------------|
| `notification_mode: stages_only` + `@notify "test"` | Message sent ✅ |
| `notification_mode: agent_status` + `@notify "test"` | Message sent ✅ |
| `notification_mode: all` + `@notify "test"` | Message sent ✅ (unchanged) |
| `events: []` + `@notify "test"` | "No notification channels" ❌ |
| `enabled: false` + `@notify "test"` | "Notifications disabled" ❌ |

---

## Rollback Instructions

If implementation causes issues:

1. **Revert config.py**:
   ```bash
   git checkout src/teambot/notifications/config.py
   ```

2. **Remove test class** from `test_config.py`:
   - Delete `TestCustomMessageBypassMode` class

3. **Verify baseline**:
   ```bash
   uv run pytest tests/test_notifications/ -v
   ```

---

## Evidence Checklist

After completion, verify:

- [ ] Research document consulted: Lines 403-433 for implementation
- [ ] Test strategy followed: TDD approach per Lines 40-56
- [ ] Tests written before implementation (TDD red phase)
- [ ] Implementation minimal (~3 lines of code)
- [ ] All tests pass (TDD green phase)
- [ ] Code linted and formatted
