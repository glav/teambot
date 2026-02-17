<!-- markdownlint-disable-file -->
# Research: Notification Frequency Control

**Date**: 2026-02-17  
**Feature**: Notification Frequency Control (Notification Mode Presets)  
**Objective**: `.teambot/notification-frequency-control`

---

## 📋 Research Scope

### Goals
Enable users to configure notification frequency using named presets (`stages_only`, `agent_status`, `all`) rather than manually specifying individual event names.

### Questions to Answer
1. What event types exist and how are they grouped?
2. Where is notification configuration loaded and applied?
3. How does channel filtering currently work?
4. What code paths need modification?
5. How should precedence work between `notification_mode` and `events`?

### Success Criteria
- Clear understanding of existing notification architecture
- Identified all code changes needed
- Defined event groupings for each mode
- Entry point analysis complete
- Test strategy identified

---

## 📊 Event Type Inventory

### All Notification Event Types

Based on analysis of `src/teambot/notifications/templates.py` (Lines 24-48) and `src/teambot/orchestration/` files:

| Event Type | Description | Category |
|------------|-------------|----------|
| `orchestration_started` | Workflow begins | 🏷️ Stage |
| `orchestration_completed` | Workflow ends | 🏷️ Stage |
| `stage_changed` | Stage transition | 🏷️ Stage |
| `agent_running` | Agent started task | 👤 Agent Status |
| `agent_complete` | Agent finished successfully | 👤 Agent Status |
| `agent_failed` | Agent task failed | 👤 Agent Status |
| `parallel_group_start` | Parallel stages began | 🔄 All |
| `parallel_group_complete` | Parallel stages finished | 🔄 All |
| `parallel_stage_complete` | Individual parallel stage done | 🔄 All |
| `parallel_stage_failed` | Individual parallel stage failed | 🔄 All |
| `acceptance_test_stage_complete` | Acceptance tests ran | 🔄 All |
| `acceptance_test_max_iterations_reached` | Max fix retries hit | 🔄 All |
| `review_progress` | Review cycle update | 🔄 All |
| `custom_message` | User `@notify` message | 🔄 All |

### 📌 Proposed Mode Groupings

```python
# In src/teambot/notifications/modes.py (NEW FILE)

NOTIFICATION_MODES = {
    "stages_only": {
        "stage_changed",
        "orchestration_started", 
        "orchestration_completed",
    },
    "agent_status": {
        # Includes stages_only events
        "stage_changed",
        "orchestration_started",
        "orchestration_completed",
        # Plus agent lifecycle events
        "agent_running",
        "agent_complete",
        "agent_failed",
    },
    "all": None,  # None = no filtering, accept all events
}
```

**Rationale:**
- `stages_only` (3 events): Lowest frequency - only major workflow milestones
- `agent_status` (6 events): Medium frequency - adds agent lifecycle visibility
- `all` (None/all events): Highest frequency - current default behavior

---

## 🏗️ Architecture Analysis

### Current Configuration Flow

```
teambot.json                     # User configuration
    ↓
create_event_bus_from_config()   # src/teambot/notifications/config.py:79-106
    ↓
_create_channel()                # src/teambot/notifications/config.py:109-138
    ↓
TelegramChannel(                 # src/teambot/notifications/channels/telegram.py:28-48
    subscribed_events=set(...)   # ← Event filtering applied here
)
    ↓
channel.supports_event()         # src/teambot/notifications/channels/telegram.py:71-75
```

### Key Code Locations

| File | Lines | Purpose |
|------|-------|---------|
| `src/teambot/notifications/config.py` | 79-106 | `create_event_bus_from_config()` - Entry point |
| `src/teambot/notifications/config.py` | 109-138 | `_create_channel()` - Channel instantiation |
| `src/teambot/notifications/channels/telegram.py` | 28-48 | `__init__()` - Accepts `subscribed_events` |
| `src/teambot/notifications/channels/telegram.py` | 71-75 | `supports_event()` - Event filtering logic |
| `src/teambot/cli.py` | 117-172 | `_setup_telegram_notifications()` - Init wizard |

### Current Event Filtering Logic

From `src/teambot/notifications/channels/telegram.py` (Lines 71-75):

```python
def supports_event(self, event_type: str) -> bool:
    """Check if this channel handles the event type."""
    if self._subscribed_events is None:
        return True  # No filter = accept all
    return event_type in self._subscribed_events
```

**Key Insight:** `subscribed_events=None` means accept ALL events. This is the current default.

---

## 🔀 Entry Point Analysis

### User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `teambot.json` config load | `config.py:create_event_bus_from_config()` → `_create_channel()` | ✅ YES | ✅ YES |
| `teambot init` wizard | `cli.py:_setup_telegram_notifications()` | ✅ YES | ✅ YES |
| Programmatic config | Direct call to `create_event_bus_from_config()` | ✅ YES | ✅ YES (same path) |

### Code Path Traces

#### Entry Point 1: Config File Loading (`teambot run`)

1. User runs: `teambot run objectives/task.md`
2. Handled by: `cli.py:cmd_run()` (Lines 206-280)
3. Loads config: `json.load()` → `teambot.json`
4. Creates event bus: `config.py:create_event_bus_from_config()` (Lines 79-106)
5. Creates channel: `config.py:_create_channel()` (Lines 109-138)
6. Applies filter: `resolved.get("events", [])` → `subscribed_events` (Line 122)
7. **Implementation Point**: Need to check for `notification_mode` before `events`

#### Entry Point 2: Init Wizard (`teambot init`)

1. User runs: `teambot init`
2. Handled by: `cli.py:cmd_init()` (Lines 175-202)
3. Prompts for notifications: `_should_setup_notifications()` (Lines 99-114)
4. Configures Telegram: `_setup_telegram_notifications()` (Lines 117-172)
5. Writes config: `config["notifications"] = {...}`
6. **Implementation Point**: Add mode selection prompt after channel setup

### Coverage Verification

- [x] Config file loading covered by `_create_channel()`
- [x] Init wizard covered by `_setup_telegram_notifications()`
- [x] No hidden entry points found

---

## 💡 Implementation Approach

### Selected Approach: Mode Expansion at Channel Creation

**Decision**: Expand `notification_mode` to `subscribed_events` set in `_create_channel()`.

**Rationale:**
1. Single point of change for mode resolution
2. Channels remain mode-agnostic (receive set of events)
3. Precedence logic in one place
4. No changes needed to `TelegramChannel` class

### Code Changes Required

#### 1. New File: `src/teambot/notifications/modes.py`

```python
"""Notification mode definitions and event groupings."""

from __future__ import annotations

from typing import Literal

NotificationMode = Literal["stages_only", "agent_status", "all"]

# Event type groupings by mode
STAGES_ONLY_EVENTS = frozenset({
    "stage_changed",
    "orchestration_started",
    "orchestration_completed",
})

AGENT_STATUS_EVENTS = STAGES_ONLY_EVENTS | frozenset({
    "agent_running",
    "agent_complete",
    "agent_failed",
})

NOTIFICATION_MODES: dict[NotificationMode, frozenset[str] | None] = {
    "stages_only": STAGES_ONLY_EVENTS,
    "agent_status": AGENT_STATUS_EVENTS,
    "all": None,  # None means no filtering
}

def resolve_notification_mode(mode: str) -> frozenset[str] | None:
    """Resolve a mode name to its event set.
    
    Args:
        mode: One of "stages_only", "agent_status", "all"
        
    Returns:
        Set of event types, or None for all events
        
    Raises:
        ValueError: If mode is not recognized
    """
    if mode not in NOTIFICATION_MODES:
        valid = ", ".join(sorted(NOTIFICATION_MODES.keys()))
        raise ValueError(f"Invalid notification_mode '{mode}'. Valid modes: {valid}")
    return NOTIFICATION_MODES[mode]
```

#### 2. Modify: `src/teambot/notifications/config.py`

Update `_create_channel()` (Lines 109-138):

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
        
        # Determine subscribed events (precedence: events > notification_mode > default)
        subscribed: set[str] | None = None
        
        if "events" in resolved and resolved["events"]:
            # Explicit events array takes precedence
            subscribed = set(resolved["events"])
        elif "notification_mode" in resolved:
            # Mode-based filtering
            mode_events = resolve_notification_mode(resolved["notification_mode"])
            subscribed = set(mode_events) if mode_events else None
        # else: subscribed=None → accept all events (default)

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

#### 3. Modify: `src/teambot/cli.py`

Update `_setup_telegram_notifications()` to add mode selection:

```python
def _setup_telegram_notifications(config: dict, display: ConsoleDisplay) -> bool:
    """Guide user through Telegram notification setup."""
    # ... existing credential setup code ...

    # After getting chat_id_env, add mode selection:
    display.print_success("")
    display.print_success("=== Notification Frequency ===")
    display.print_success("Choose how many notifications to receive:")
    display.print_success("  1. stages_only  - Major milestones only (recommended)")
    display.print_success("  2. agent_status - Stage + agent lifecycle events")
    display.print_success("  3. all          - All events (verbose)")
    display.print_success("")
    
    mode_input = input("Notification mode [1/2/3, default: 1]: ").strip()
    mode_map = {"1": "stages_only", "2": "agent_status", "3": "all", "": "stages_only"}
    notification_mode = mode_map.get(mode_input, "stages_only")

    # Add notifications config with mode
    config["notifications"] = {
        "enabled": True,
        "channels": [
            {
                "type": "telegram",
                "token": f"${{{token_env}}}",
                "chat_id": f"${{{chat_id_env}}}",
                "notification_mode": notification_mode,
            }
        ],
    }
    # ... rest of function ...
```

#### 4. Documentation Updates

- `docs/guides/notifications.md`: Add `notification_mode` section
- `README.md`: Mention notification modes if applicable

---

## 🧪 Testing Strategy Research

### Existing Test Infrastructure

| Item | Value |
|------|-------|
| **Framework** | pytest 7.4+ with pytest-asyncio |
| **Location** | `tests/test_notifications/` |
| **Pattern** | `test_*.py` files, class-based tests |
| **Coverage** | coverage.py, 80% target |
| **Runner** | `uv run pytest` |

### Test Files to Modify/Create

| File | Purpose | Action |
|------|---------|--------|
| `tests/test_notifications/test_modes.py` | NEW - Test mode definitions | Create |
| `tests/test_notifications/test_config.py` | Test config loading with modes | Modify |
| `tests/test_cli.py` | Test init wizard mode selection | Modify (if exists) |

### Test Patterns Found

From `tests/test_notifications/test_config.py` (Lines 172-195):

```python
def test_applies_event_filter(self, monkeypatch) -> None:
    """Applies event filter from config."""
    monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
    monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

    config = {
        "notifications": {
            "enabled": True,
            "channels": [
                {
                    "type": "telegram",
                    "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                    "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                    "events": ["stage_changed"],
                }
            ],
        }
    }

    result = create_event_bus_from_config(config)

    channel = result._channels[0]
    assert channel.supports_event("stage_changed") is True
    assert channel.supports_event("agent_failed") is False
```

### Proposed Test Cases

#### 1. `test_modes.py` (NEW)

```python
class TestNotificationModes:
    """Tests for notification mode definitions."""

    def test_stages_only_contains_expected_events(self) -> None:
        """stages_only mode includes stage lifecycle events."""
        from teambot.notifications.modes import STAGES_ONLY_EVENTS
        
        assert "stage_changed" in STAGES_ONLY_EVENTS
        assert "orchestration_started" in STAGES_ONLY_EVENTS
        assert "orchestration_completed" in STAGES_ONLY_EVENTS
        assert "agent_running" not in STAGES_ONLY_EVENTS

    def test_agent_status_is_superset_of_stages_only(self) -> None:
        """agent_status mode includes all stages_only events."""
        from teambot.notifications.modes import STAGES_ONLY_EVENTS, AGENT_STATUS_EVENTS
        
        assert STAGES_ONLY_EVENTS.issubset(AGENT_STATUS_EVENTS)
        assert "agent_running" in AGENT_STATUS_EVENTS
        assert "agent_complete" in AGENT_STATUS_EVENTS
        assert "agent_failed" in AGENT_STATUS_EVENTS

    def test_resolve_notification_mode_valid(self) -> None:
        """resolve_notification_mode returns correct event set."""
        from teambot.notifications.modes import resolve_notification_mode
        
        assert resolve_notification_mode("stages_only") is not None
        assert resolve_notification_mode("all") is None  # None = no filter

    def test_resolve_notification_mode_invalid_raises(self) -> None:
        """resolve_notification_mode raises ValueError for invalid mode."""
        from teambot.notifications.modes import resolve_notification_mode
        import pytest
        
        with pytest.raises(ValueError, match="Invalid notification_mode"):
            resolve_notification_mode("invalid_mode")
```

#### 2. `test_config.py` Additions

```python
class TestNotificationModeConfig:
    """Tests for notification_mode in channel config."""

    def test_notification_mode_stages_only(self, monkeypatch) -> None:
        """notification_mode: stages_only filters to stage events."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "notification_mode": "stages_only",
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)
        channel = result._channels[0]
        
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("orchestration_started") is True
        assert channel.supports_event("agent_running") is False

    def test_notification_mode_agent_status(self, monkeypatch) -> None:
        """notification_mode: agent_status includes agent events."""
        # Similar structure...

    def test_notification_mode_all(self, monkeypatch) -> None:
        """notification_mode: all accepts all events."""
        # ...
        assert channel.supports_event("any_custom_event") is True

    def test_events_takes_precedence_over_mode(self, monkeypatch) -> None:
        """Explicit events array overrides notification_mode."""
        # Config with both events and notification_mode
        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "notification_mode": "all",
                        "events": ["stage_changed"],  # Explicit filter
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)
        channel = result._channels[0]
        
        # events should take precedence
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_running") is False

    def test_invalid_notification_mode_raises(self, monkeypatch) -> None:
        """Invalid notification_mode raises ValueError."""
        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "notification_mode": "invalid",
                    }
                ],
            }
        }
        
        with pytest.raises(ValueError):
            create_event_bus_from_config(config)

    def test_default_is_all_when_no_mode_or_events(self, monkeypatch) -> None:
        """Default behavior (no mode, no events) accepts all events."""
        # Current backwards-compatible behavior
```

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `modes.py` | TDD | Well-defined, static mappings - write tests first |
| `config.py` changes | TDD | Precedence logic is clear - test first |
| `cli.py` init wizard | Code-First | Interactive I/O, harder to test-first |
| Documentation | N/A | No code testing needed |

---

## ⚠️ Potential Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Invalid mode in config crashes | High | Validate early with clear error message |
| Breaking existing `events` configs | High | Explicit precedence: `events` > `notification_mode` |
| Mode names confusing | Medium | Clear documentation + wizard help text |
| New event types not in modes | Low | `all` mode exists; document how to add events |

---

## 📁 File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `src/teambot/notifications/modes.py` | NEW | Mode definitions and resolver |
| `src/teambot/notifications/config.py` | MODIFY | Add mode resolution in `_create_channel()` |
| `src/teambot/cli.py` | MODIFY | Add mode selection to init wizard |
| `docs/guides/notifications.md` | MODIFY | Document `notification_mode` option |
| `tests/test_notifications/test_modes.py` | NEW | Test mode definitions |
| `tests/test_notifications/test_config.py` | MODIFY | Test mode config loading |

---

## ✅ Task Implementation Requests

### Core Implementation Tasks

1. **Create `modes.py` module**
   - Define `STAGES_ONLY_EVENTS`, `AGENT_STATUS_EVENTS`
   - Define `NOTIFICATION_MODES` mapping
   - Implement `resolve_notification_mode()` function
   - Add type hints and docstrings

2. **Update `config.py` channel creation**
   - Import `resolve_notification_mode`
   - Add precedence logic: `events` > `notification_mode` > default
   - Handle `ValueError` for invalid modes

3. **Update CLI init wizard**
   - Add mode selection prompt after credentials
   - Default to `stages_only` (recommended for new users)
   - Include `notification_mode` in generated config

4. **Write unit tests**
   - `test_modes.py`: Mode definitions and resolver
   - `test_config.py`: Mode config loading and precedence

5. **Update documentation**
   - `docs/guides/notifications.md`: Document modes and usage
   - Configuration reference table update

---

## 🔮 Potential Next Research

1. **Future channel implementations**: How should modes work with Slack/Teams channels?
2. **Per-mode templates**: Should message format differ by mode?
3. **Mode migration tool**: Help users convert existing `events` arrays to modes?

---

## 📚 References

| Resource | Location |
|----------|----------|
| Existing notification config | `src/teambot/notifications/config.py` |
| Telegram channel implementation | `src/teambot/notifications/channels/telegram.py` |
| Event templates | `src/teambot/notifications/templates.py` |
| CLI init wizard | `src/teambot/cli.py:117-172` |
| Notification guide | `docs/guides/notifications.md` |
| Existing config tests | `tests/test_notifications/test_config.py` |
