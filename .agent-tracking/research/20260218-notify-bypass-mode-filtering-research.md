<!-- markdownlint-disable-file -->
# Research: @notify Command Bypass Mode Filtering

**Date**: 2026-02-18  
**Feature**: `@notify` command should bypass `notification_mode` filtering  
**Specification**: `.teambot/notify-command/artifacts/feature_spec.md` (pending)

---

## 📋 Research Outline

1. [Problem Statement](#problem-statement)
2. [Entry Point Analysis](#entry-point-analysis)
3. [Current Implementation Analysis](#current-implementation-analysis)
4. [Technical Approach](#technical-approach)
5. [Testing Strategy Research](#testing-strategy-research)
6. [Implementation Guidance](#implementation-guidance)
7. [Task Implementation Requests](#task-implementation-requests)
8. [Potential Next Research](#potential-next-research)

---

## Problem Statement

### Current Behavior ❌

The `@notify <msg>` command currently respects `notification_mode` filtering. When a channel is configured with `notification_mode: stages_only`, the `custom_message` event type is **not** in the allowed event set, causing `@notify` to silently fail to deliver.

**Example scenario:**
```yaml
notifications:
  enabled: true
  channels:
    - type: telegram
      notification_mode: stages_only  # Only allows: stage_changed, orchestration_started, orchestration_completed
```

With this config, `@notify "Build completed!"` would **not** send because `custom_message` is not in `STAGES_ONLY_EVENTS`.

### Desired Behavior ✅

The `@notify <msg>` command should **always** send when:
1. `notifications.enabled` is `true`
2. At least one channel is configured (has credentials)

The `notification_mode` filtering should **not** apply to explicit user `@notify` commands.

### Success Criteria

| Criterion | Status |
|-----------|--------|
| `@notify` sends when `enabled=true` + channels configured, regardless of `notification_mode` | 🎯 Target |
| `@notify` shows "disabled" when `enabled=false` | ✅ Already works |
| `@notify` shows "no channels" when enabled but empty | ✅ Already works |
| `notification_mode` continues filtering other events normally | 🎯 Target |
| Unit tests cover bypass behavior | 🎯 Target |
| Existing tests pass | 🎯 Target |

---

## Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `@notify <msg>` (simple) | loop.py → router.py → executor.py | YES ✅ | YES |
| `@notify <msg> &` (background) | loop.py → executor.py | YES ✅ | YES |
| `@pm -> @notify <msg>` (pipeline) | loop.py → executor.py → manager.py | YES ✅ | YES |
| `@pm,@notify <msg>` (multi-agent) | loop.py → executor.py → manager.py | YES ✅ | YES |

### Code Path Trace

#### Entry Point 1: Simple `@notify <msg>` Command

1. User enters: `@notify Build finished!`
2. Parsed by: `parser.py:parse_command()` → `Command(agent_id="notify", content="Build finished!")`
3. Router checks: `router.py:_route_agent()` (Lines 160-175) → `notify` is in `VALID_AGENTS`
4. Routes to: `loop.py:_handle_agent_command()` OR `loop.py:_handle_advanced_command()` → `executor.py`
5. Executor detects: `executor.py:is_pseudo_agent("notify")` returns `True` (Line 23)
6. Executor calls: `executor.py:_handle_notify()` (Lines 172-230)
7. Creates EventBus: `config.py:create_event_bus_from_config()` (Lines 79-106)
8. Channel filtering: `config.py:_create_channel()` (Lines 109-154) applies `notification_mode`
9. **Filtering point**: `telegram.py:supports_event("custom_message")` (Lines 71-75) ← 🎯 **ISSUE HERE**
10. If `subscribed_events` contains `custom_message` → sends; otherwise → no-op

#### Entry Point 2: Background `@notify <msg> &`

Same path as above, but executed via `TaskManager.submit()` as background task.

#### Entry Point 3: Pipeline `@pm -> @notify <msg>`

1. Parser creates pipeline stages
2. `executor.py` processes each stage sequentially
3. When reaching `@notify` stage → `_handle_notify()` called with interpolated content
4. Same filtering issue applies

### Coverage Analysis

**All entry points converge at `executor.py:_handle_notify()` → `event_bus.emit_sync()` → `channel.supports_event()`**

The fix location is clear: the filtering happens in `TelegramChannel.supports_event()` method, controlled by `_subscribed_events` set built in `config.py:_create_channel()`.

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| `custom_message` not in mode event sets | `@notify` silently fails with restrictive modes | Add bypass logic |

### Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified  
- [x] Coverage gaps are documented with required fixes

---

## Current Implementation Analysis

### Notification Mode Filtering Flow

```
User Config                    Config Processing               Channel Behavior
────────────                   ─────────────────               ────────────────
notification_mode: stages_only → resolve_notification_mode()  → subscribed_events={stage_changed,...}
                               │                               │
                               └→ _create_channel()            └→ supports_event("custom_message")
                                  (config.py:128-138)             returns: custom_message in {stage_changed,...}
                                                                          = False ❌
```

### Key Files and Functions

| File | Function | Lines | Responsibility |
|------|----------|-------|----------------|
| `src/teambot/tasks/executor.py` | `_handle_notify()` | 172-230 | Entry point for @notify |
| `src/teambot/notifications/config.py` | `create_event_bus_from_config()` | 79-106 | Creates EventBus with channels |
| `src/teambot/notifications/config.py` | `_create_channel()` | 109-154 | Applies mode filtering to channel |
| `src/teambot/notifications/modes.py` | `resolve_notification_mode()` | 33-53 | Converts mode → event set |
| `src/teambot/notifications/channels/telegram.py` | `supports_event()` | 71-75 | Decides if event passes filter |
| `src/teambot/notifications/event_bus.py` | `emit_sync()` | 127-173 | Dispatches events to channels |

### Mode Event Sets (modes.py:10-30)

```python
STAGES_ONLY_EVENTS = frozenset({
    "stage_changed",
    "orchestration_started", 
    "orchestration_completed",
})  # 3 events - NO custom_message

AGENT_STATUS_EVENTS = STAGES_ONLY_EVENTS | frozenset({
    "agent_running",
    "agent_complete",
    "agent_failed",
})  # 6 events - NO custom_message

NOTIFICATION_MODES = {
    "stages_only": STAGES_ONLY_EVENTS,
    "agent_status": AGENT_STATUS_EVENTS,
    "all": None,  # None = no filtering
}
```

### Channel Filtering Logic (telegram.py:71-75)

```python
def supports_event(self, event_type: str) -> bool:
    """Check if this channel handles the event type."""
    if self._subscribed_events is None:
        return True  # No filter = accept all
    return event_type in self._subscribed_events
```

**Problem**: `custom_message` is not in any mode's event set, so with `stages_only` or `agent_status`, the channel rejects `@notify` events.

---

## Technical Approach

### 🎯 Selected Approach: Always Include `custom_message` in Subscribed Events

**Location**: `src/teambot/notifications/config.py:_create_channel()` (Lines 128-138)

**Rationale**: The simplest fix with minimal code changes. Add `custom_message` to `subscribed` set after mode resolution, ensuring explicit user notifications always pass filtering.

#### Implementation

```python
# Current code (config.py:128-138):
subscribed: set[str] | None = None

if "events" in resolved:
    subscribed = set(resolved["events"]) if resolved["events"] else set()
elif "notification_mode" in resolved:
    mode_events = resolve_notification_mode(resolved["notification_mode"])
    subscribed = set(mode_events) if mode_events else None

# PROPOSED FIX - Add after mode resolution:
# Always allow custom_message for explicit @notify commands
# unless subscribed is explicitly an empty set (events: [])
if subscribed is not None and len(subscribed) > 0:
    subscribed.add("custom_message")
```

#### Benefits

| Benefit | Description |
|---------|-------------|
| ✅ Minimal change | 2 lines of code |
| ✅ Surgical | Only affects mode-based filtering, not explicit `events` arrays |
| ✅ Backwards compatible | Empty `events: []` still disables all notifications |
| ✅ Clear intent | The added lines clearly show the bypass logic |
| ✅ No API changes | No new config options or function signatures |

#### Edge Cases Handled

| Configuration | Current Behavior | New Behavior |
|---------------|-----------------|--------------|
| `notification_mode: stages_only` | `@notify` blocked ❌ | `@notify` sends ✅ |
| `notification_mode: agent_status` | `@notify` blocked ❌ | `@notify` sends ✅ |
| `notification_mode: all` | `@notify` sends ✅ | `@notify` sends ✅ (no change) |
| `events: []` (empty) | All blocked ❌ | All blocked ❌ (no change) |
| `events: [custom_message]` | `@notify` sends ✅ | `@notify` sends ✅ (no change) |
| No mode/events specified | `@notify` sends ✅ | `@notify` sends ✅ (no change) |

### Alternative Approaches (Not Selected)

#### Alternative A: Modify modes.py to include custom_message

Add `custom_message` to all mode event sets.

**Rejected because**: Changes the meaning of modes (e.g., `stages_only` would no longer be "only stage events").

#### Alternative B: Bypass filtering at emit_sync() level

Check event type in `event_bus.py` and skip `supports_event()` for `custom_message`.

**Rejected because**: Violates single responsibility - EventBus shouldn't know about special event types.

#### Alternative C: New config option `always_allow_custom_message: true`

Add explicit config option to control behavior.

**Rejected because**: Adds complexity. The intended behavior should be default - explicit `@notify` should always work.

---

## Testing Strategy Research

### Existing Test Infrastructure

| Component | Details |
|-----------|---------|
| **Framework** | pytest 7.4.0+ |
| **Location** | `tests/` directory (mirrors `src/` structure) |
| **Naming** | `test_*.py` pattern |
| **Runner** | `uv run pytest` |
| **Coverage** | pytest-cov with 80% target |
| **Mocking** | pytest-mock with `MagicMock`, `AsyncMock`, `patch()` |

### Relevant Test Files

| File | Purpose | Lines |
|------|---------|-------|
| `tests/test_tasks/test_executor.py` | @notify handler tests | ~800+ |
| `tests/test_notifications/test_modes.py` | Mode filtering tests | 126 |
| `tests/test_notifications/test_config.py` | Config parsing tests | 400+ |
| `tests/test_notifications/test_telegram.py` | Telegram channel tests | ~300 |
| `tests/test_notify_acceptance_validation.py` | Acceptance tests | ~500 |

### Test Patterns Found

#### Pattern 1: Executor Tests (test_executor.py:35-77)

```python
class TestNotifyHandler:
    @pytest.fixture
    def mock_config(self):
        return {
            "notifications": {
                "enabled": True,
                "channels": [{"type": "telegram", "token": "test", "chat_id": "123"}],
            }
        }

    @pytest.mark.asyncio
    async def test_handle_notify_returns_confirmation(self, mock_config):
        executor = TaskExecutor(sdk_client=AsyncMock(), config=mock_config)
        with patch("teambot.tasks.executor.create_event_bus_from_config") as mock_create:
            mock_bus = MagicMock()
            mock_bus._channels = [MagicMock()]
            mock_create.return_value = mock_bus
            result = await executor._handle_notify("Test message", background=False)
            assert result.success
            assert "Notification sent" in result.output
```

#### Pattern 2: Config Tests (test_config.py style)

```python
class TestCreateEventBusFromConfig:
    def test_creates_bus_when_enabled(self):
        config = {"notifications": {"enabled": True, "channels": [...]}}
        bus = create_event_bus_from_config(config)
        assert bus is not None
```

#### Pattern 3: Telegram Channel Tests

```python
class TestTelegramSupportsEvent:
    def test_supports_event_no_filter(self):
        channel = TelegramChannel(subscribed_events=None)
        assert channel.supports_event("any_event") is True

    def test_supports_event_with_filter(self):
        channel = TelegramChannel(subscribed_events={"stage_changed"})
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("custom_message") is False
```

### New Tests Required

#### Test Suite: `tests/test_notifications/test_config.py`

Add to existing `TestCreateChannel` class:

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
        
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("custom_message") is True  # NEW: bypass
        assert channel.supports_event("agent_running") is False  # Still filtered

    def test_agent_status_mode_includes_custom_message(self, monkeypatch):
        """custom_message is added to agent_status mode event set."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")
        
        channel_config = {
            "type": "telegram",
            "notification_mode": "agent_status",
        }
        channel = _create_channel(channel_config)
        
        assert channel.supports_event("agent_complete") is True
        assert channel.supports_event("custom_message") is True  # NEW: bypass

    def test_explicit_empty_events_no_custom_message(self, monkeypatch):
        """Explicit events: [] still blocks everything including custom_message."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")
        
        channel_config = {
            "type": "telegram",
            "events": [],  # Explicitly disable all
        }
        channel = _create_channel(channel_config)
        
        assert channel.supports_event("custom_message") is False  # Explicit block

    def test_all_mode_unchanged(self, monkeypatch):
        """all mode still accepts everything (subscribed=None)."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")
        
        channel_config = {
            "type": "telegram",
            "notification_mode": "all",
        }
        channel = _create_channel(channel_config)
        
        assert channel.supports_event("custom_message") is True
        assert channel.supports_event("any_other_event") is True
```

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| Config `_create_channel()` | Code-First | Small, isolated change |
| Integration tests | Code-First | Extending existing patterns |

---

## Implementation Guidance

### Step-by-Step Implementation

#### Step 1: Modify `_create_channel()` in `config.py`

**File**: `src/teambot/notifications/config.py`  
**Lines**: 128-138

```python
# BEFORE (Lines 128-138):
subscribed: set[str] | None = None

if "events" in resolved:
    subscribed = set(resolved["events"]) if resolved["events"] else set()
elif "notification_mode" in resolved:
    mode_events = resolve_notification_mode(resolved["notification_mode"])
    subscribed = set(mode_events) if mode_events else None

# AFTER:
subscribed: set[str] | None = None

if "events" in resolved:
    # Explicit events array - honor exactly as specified
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
```

#### Step 2: Add Unit Tests

**File**: `tests/test_notifications/test_config.py`

Add `TestCustomMessageBypassMode` class with tests as documented above.

#### Step 3: Run Existing Tests

```bash
uv run pytest tests/test_notifications/test_config.py -v
uv run pytest tests/test_notifications/test_modes.py -v
uv run pytest tests/test_tasks/test_executor.py -v
```

#### Step 4: Update Documentation (Optional)

**File**: `docs/guides/notifications.md` (if exists)

Add note that `@notify` bypasses `notification_mode` filtering.

### Code References

| File | Lines | Purpose |
|------|-------|---------|
| `src/teambot/notifications/config.py` | 128-138 | Primary change location |
| `src/teambot/notifications/modes.py` | 10-30 | Mode definitions (reference only) |
| `src/teambot/notifications/channels/telegram.py` | 71-75 | `supports_event()` (no change needed) |
| `src/teambot/tasks/executor.py` | 205 | Emits `custom_message` (no change needed) |

### Potential Pitfalls

| Pitfall | Mitigation |
|---------|------------|
| Breaking `events: []` behavior | Check `len(subscribed) > 0` before adding |
| Type errors with `frozenset` | Mode events return `frozenset`, convert to `set` first |
| Affecting `all` mode | `all` returns `None`, so condition `subscribed is not None` handles it |

---

## Task Implementation Requests

### Primary Task

- [ ] **T1**: Modify `_create_channel()` in `config.py` to add `custom_message` to mode-based `subscribed` sets
  - File: `src/teambot/notifications/config.py`
  - Lines: 128-138
  - Add: `if subscribed is not None: subscribed.add("custom_message")` after mode resolution

### Testing Tasks

- [ ] **T2**: Add `TestCustomMessageBypassMode` test class to `tests/test_notifications/test_config.py`
  - Tests: `stages_only` mode, `agent_status` mode, explicit `events: []`, `all` mode unchanged
  - Follow existing test patterns in file

- [ ] **T3**: Run existing notification tests to verify no regressions
  - Command: `uv run pytest tests/test_notifications/ -v`

- [ ] **T4**: Run executor tests to verify @notify still works
  - Command: `uv run pytest tests/test_tasks/test_executor.py -v`

### Documentation Tasks (Optional)

- [ ] **T5**: Update notification documentation if `docs/guides/notifications.md` exists

### Artifacts

- [ ] **T6**: Copy research summary to `.teambot/notify-command/artifacts/research.md`

---

## Potential Next Research

All research for this feature is complete. The implementation approach is clear and minimal.

**No additional research required.**

---

## Evidence Log

| Source | Finding | Date |
|--------|---------|------|
| `src/teambot/tasks/executor.py:205` | `@notify` emits `custom_message` event | 2026-02-18 |
| `src/teambot/notifications/modes.py:10-30` | Mode event sets do not include `custom_message` | 2026-02-18 |
| `src/teambot/notifications/config.py:128-138` | Mode filtering applied during channel creation | 2026-02-18 |
| `src/teambot/notifications/channels/telegram.py:71-75` | `supports_event()` uses `_subscribed_events` | 2026-02-18 |
| `tests/test_notifications/test_config.py` | Test patterns for config functions | 2026-02-18 |
| `tests/test_tasks/test_executor.py:35-77` | `TestNotifyHandler` patterns | 2026-02-18 |

---

## Appendix: Full Code Context

### Current `_create_channel()` Function (config.py:109-154)

```python
def _create_channel(channel_config: dict[str, Any]):
    """Create channel instance from config."""
    from teambot.notifications.channels.telegram import TelegramChannel
    from teambot.notifications.modes import resolve_notification_mode

    channel_type = channel_config.get("type")

    if channel_type == "telegram":
        # Extract env var names from ${VAR} patterns
        token_env_var = extract_env_var_name(channel_config.get("token", ""))
        chat_id_env_var = extract_env_var_name(channel_config.get("chat_id", ""))

        # Resolve other config values
        resolved = resolve_config_secrets(channel_config)

        # Determine subscribed events with precedence:
        # 1. Explicit "events" array (highest priority)
        # 2. "notification_mode" preset expansion
        # 3. Default to None (all events) for backwards compatibility
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

        # Build kwargs for TelegramChannel
        kwargs = {
            "subscribed_events": subscribed,
            "dry_run": resolved.get("dry_run", False),
        }

        # Pass custom env var names if present
        if token_env_var:
            kwargs["token_env_var"] = token_env_var
        if chat_id_env_var:
            kwargs["chat_id_env_var"] = chat_id_env_var

        return TelegramChannel(**kwargs)

    return None
```
