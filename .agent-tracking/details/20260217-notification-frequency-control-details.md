<!-- markdownlint-disable-file -->
# Implementation Details: Notification Frequency Control

## Research Reference

- **Source**: `.teambot/notification-frequency-control/artifacts/research.md`
- **Test Strategy**: `.teambot/notification-frequency-control/artifacts/test_strategy.md`
- **Feature Spec**: `.teambot/notification-frequency-control/artifacts/feature_spec.md`

---

## Phase 1: Core Infrastructure (TDD)

### Task 1.1: Write test for NOTIFICATION_MODES constant

**File**: `tests/test_notifications/test_modes.py` (NEW)

**Test Requirements**:
- Verify `NOTIFICATION_MODES` dict exists with 3 keys
- Verify `stages_only` contains exactly 3 events
- Verify `agent_status` contains exactly 6 events
- Verify `agent_status` is superset of `stages_only`
- Verify `all` maps to `None` (no filtering)

**Code Pattern** (from research Lines 379-415):
```python
"""Tests for notification mode definitions."""

import pytest

from teambot.notifications.modes import (
    NOTIFICATION_MODES,
    STAGES_ONLY_EVENTS,
    AGENT_STATUS_EVENTS,
    resolve_notification_mode,
)


class TestNotificationModeConstants:
    """Tests for notification mode constant definitions."""

    def test_notification_modes_has_three_modes(self) -> None:
        """NOTIFICATION_MODES contains exactly three mode definitions."""
        assert len(NOTIFICATION_MODES) == 3
        assert "stages_only" in NOTIFICATION_MODES
        assert "agent_status" in NOTIFICATION_MODES
        assert "all" in NOTIFICATION_MODES

    def test_stages_only_contains_stage_events(self) -> None:
        """stages_only mode contains exactly 3 stage lifecycle events."""
        assert "stage_changed" in STAGES_ONLY_EVENTS
        assert "orchestration_started" in STAGES_ONLY_EVENTS
        assert "orchestration_completed" in STAGES_ONLY_EVENTS
        assert len(STAGES_ONLY_EVENTS) == 3

    def test_agent_status_is_superset_of_stages_only(self) -> None:
        """agent_status mode includes all stages_only events plus agent events."""
        assert STAGES_ONLY_EVENTS.issubset(AGENT_STATUS_EVENTS)
        assert "agent_running" in AGENT_STATUS_EVENTS
        assert "agent_complete" in AGENT_STATUS_EVENTS
        assert "agent_failed" in AGENT_STATUS_EVENTS
        assert len(AGENT_STATUS_EVENTS) == 6

    def test_all_mode_is_none(self) -> None:
        """all mode maps to None (no filtering)."""
        assert NOTIFICATION_MODES["all"] is None
```

**Success Criteria**:
- Test file created
- Test imports fail (module doesn't exist yet) — expected in TDD

---

### Task 1.2: Create modes.py module with mode definitions

**File**: `src/teambot/notifications/modes.py` (NEW)

**Implementation** (from research Lines 185-228):
```python
"""Notification mode definitions and event groupings."""

from __future__ import annotations

from typing import Literal

NotificationMode = Literal["stages_only", "agent_status", "all"]

# Event type groupings by mode
STAGES_ONLY_EVENTS: frozenset[str] = frozenset({
    "stage_changed",
    "orchestration_started",
    "orchestration_completed",
})

AGENT_STATUS_EVENTS: frozenset[str] = STAGES_ONLY_EVENTS | frozenset({
    "agent_running",
    "agent_complete",
    "agent_failed",
})

NOTIFICATION_MODES: dict[NotificationMode, frozenset[str] | None] = {
    "stages_only": STAGES_ONLY_EVENTS,
    "agent_status": AGENT_STATUS_EVENTS,
    "all": None,  # None means no filtering
}
```

**Success Criteria**:
- File created at `src/teambot/notifications/modes.py`
- `uv run pytest tests/test_notifications/test_modes.py::TestNotificationModeConstants` passes

---

### Task 1.3: Write tests for resolve_notification_mode() function

**File**: `tests/test_notifications/test_modes.py` (append)

**Test Requirements**:
- Valid modes return correct event set
- `all` returns `None`
- Invalid mode raises `ValueError`
- Error message lists valid modes

**Code Pattern**:
```python
class TestResolveNotificationMode:
    """Tests for resolve_notification_mode function."""

    def test_resolve_stages_only_returns_event_set(self) -> None:
        """resolve_notification_mode('stages_only') returns stage events."""
        result = resolve_notification_mode("stages_only")
        
        assert result is not None
        assert "stage_changed" in result
        assert len(result) == 3

    def test_resolve_agent_status_returns_event_set(self) -> None:
        """resolve_notification_mode('agent_status') returns agent events."""
        result = resolve_notification_mode("agent_status")
        
        assert result is not None
        assert "agent_running" in result
        assert len(result) == 6

    def test_resolve_all_returns_none(self) -> None:
        """resolve_notification_mode('all') returns None (no filter)."""
        result = resolve_notification_mode("all")
        
        assert result is None

    def test_invalid_mode_raises_value_error(self) -> None:
        """Invalid mode raises ValueError with valid modes listed."""
        with pytest.raises(ValueError) as exc_info:
            resolve_notification_mode("invalid_mode")
        
        error_msg = str(exc_info.value)
        assert "invalid_mode" in error_msg
        assert "stages_only" in error_msg
        assert "agent_status" in error_msg
        assert "all" in error_msg
```

**Success Criteria**:
- Tests added to `test_modes.py`
- Tests fail (function not implemented yet) — expected in TDD

---

### Task 1.4: Implement resolve_notification_mode() with validation

**File**: `src/teambot/notifications/modes.py` (append)

**Implementation**:
```python
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

**Success Criteria**:
- Function implemented
- `uv run pytest tests/test_notifications/test_modes.py` passes (all tests)

---

## Phase 2: Config Integration (TDD)

### Task 2.1: Write test for stages_only mode config loading

**File**: `tests/test_notifications/test_config.py` (append)

**Test Pattern** (from test strategy Lines 354-384):
```python
class TestNotificationModeConfig:
    """Tests for notification_mode in channel config."""

    def test_stages_only_mode_expands_to_stage_events(self, monkeypatch) -> None:
        """notification_mode: 'stages_only' expands to stage event set."""
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
        assert channel.supports_event("orchestration_completed") is True
        assert channel.supports_event("agent_running") is False
        assert channel.supports_event("agent_failed") is False
```

**Success Criteria**:
- Test added to `test_config.py`
- Test fails (feature not implemented yet)

---

### Task 2.2: Write test for agent_status mode config loading

**File**: `tests/test_notifications/test_config.py`

**Implementation**:
```python
    def test_agent_status_mode_expands_to_agent_events(self, monkeypatch) -> None:
        """notification_mode: 'agent_status' expands to agent event set."""
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
                        "notification_mode": "agent_status",
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_running") is True
        assert channel.supports_event("agent_complete") is True
        assert channel.supports_event("agent_failed") is True
```

---

### Task 2.3: Write test for all mode config loading

**File**: `tests/test_notifications/test_config.py`

**Implementation**:
```python
    def test_all_mode_accepts_all_events(self, monkeypatch) -> None:
        """notification_mode: 'all' accepts all events."""
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
                        "notification_mode": "all",
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        # All mode = no filtering, accepts any event
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_running") is True
        assert channel.supports_event("custom_event") is True
```

---

### Task 2.4: Write test for events precedence over notification_mode

**File**: `tests/test_notifications/test_config.py`

**Implementation** (from test strategy Lines 385-409):
```python
    def test_events_array_takes_precedence_over_mode(self, monkeypatch) -> None:
        """Explicit events array overrides notification_mode."""
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
                        "notification_mode": "all",
                        "events": ["agent_failed"],  # Explicit filter overrides mode
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        assert channel.supports_event("agent_failed") is True
        assert channel.supports_event("stage_changed") is False  # Not in events array
```

---

### Task 2.5: Write test for default behavior (neither specified)

**File**: `tests/test_notifications/test_config.py`

**Implementation**:
```python
    def test_default_accepts_all_when_no_mode_or_events(self, monkeypatch) -> None:
        """Default behavior (no mode, no events) accepts all events."""
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
                        # No events, no notification_mode
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        # Default = all events (backwards compatible)
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_running") is True
        assert channel.supports_event("any_future_event") is True
```

---

### Task 2.6: Write test for invalid mode error message

**File**: `tests/test_notifications/test_config.py`

**Implementation** (from test strategy Lines 413-442):
```python
    def test_invalid_notification_mode_raises_value_error(self, monkeypatch) -> None:
        """Invalid notification_mode raises ValueError with valid modes listed."""
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
                        "notification_mode": "invalid_mode",
                    }
                ],
            }
        }

        with pytest.raises(ValueError) as exc_info:
            create_event_bus_from_config(config)

        error_message = str(exc_info.value)
        assert "invalid_mode" in error_message
        assert "stages_only" in error_message
        assert "agent_status" in error_message
        assert "all" in error_message
```

---

### Task 2.7: Implement mode expansion in _create_channel()

**File**: `src/teambot/notifications/config.py`

**Current Code** (Lines 109-138):
```python
def _create_channel(channel_config: dict[str, Any]):
    """Create channel instance from config."""
    from teambot.notifications.channels.telegram import TelegramChannel

    channel_type = channel_config.get("type")

    if channel_type == "telegram":
        # Extract env var names from ${VAR} patterns
        token_env_var = extract_env_var_name(channel_config.get("token", ""))
        chat_id_env_var = extract_env_var_name(channel_config.get("chat_id", ""))

        # Resolve other config values
        resolved = resolve_config_secrets(channel_config)
        subscribed = set(resolved.get("events", []))

        # Build kwargs for TelegramChannel
        kwargs = {
            "subscribed_events": subscribed if subscribed else None,
            "dry_run": resolved.get("dry_run", False),
        }
        # ...
```

**Updated Implementation**:
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
        
        if "events" in resolved and resolved["events"]:
            # Explicit events array takes precedence
            subscribed = set(resolved["events"])
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

**Success Criteria**:
- All Phase 2 tests pass
- Existing notification tests still pass (backwards compatibility)

---

## Phase 3: Init Wizard (Code-First)

### Task 3.1: Add mode selection prompt to _setup_telegram_notifications()

**File**: `src/teambot/cli.py`

**Current Code** (Lines 117-172):
The wizard collects token and chat_id env var names, then writes config.

**Updated Implementation** — Insert mode selection after chat_id collection (before writing config):
```python
def _setup_telegram_notifications(config: dict, display: ConsoleDisplay) -> bool:
    """Guide user through Telegram notification setup."""
    # ... existing code for token and chat_id ...
    
    # After getting chat_id_env (around line 146), add:
    
    # Mode selection
    display.print_success("")
    display.print_success("=== Notification Frequency ===")
    display.print_success("Choose how many notifications to receive:")
    display.print_success("  1. stages_only  - Major milestones only (recommended for low noise)")
    display.print_success("  2. agent_status - Stage + agent lifecycle events")
    display.print_success("  3. all          - All events (verbose, good for debugging)")
    display.print_success("")
    
    mode_input = input("Notification mode [1/2/3, default: 1]: ").strip()
    mode_map = {"1": "stages_only", "2": "agent_status", "3": "all", "": "stages_only"}
    notification_mode = mode_map.get(mode_input, "stages_only")

    # Update config writing to include notification_mode:
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
    
    # ... rest of existing code ...
```

**Success Criteria**:
- Running `teambot init` shows mode selection after credentials
- Generated `teambot.json` includes `notification_mode` field

---

### Task 3.2: Add integration test for init wizard mode selection

**File**: `tests/test_cli.py` (or appropriate test file)

**Implementation**:
```python
class TestInitWizardNotificationMode:
    """Tests for notification mode selection in init wizard."""

    def test_init_wizard_includes_notification_mode_in_config(
        self, tmp_path, monkeypatch
    ) -> None:
        """Init wizard writes notification_mode to config."""
        # Mock stdin for interactive input
        # Simulate: Y (enable notifications), Enter (defaults), 1 (stages_only)
        inputs = iter(["y", "", "", "", "1"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        
        # ... rest of test setup and assertions ...
        
        # Verify config file contains notification_mode
        config = json.loads((tmp_path / "teambot.json").read_text())
        channel = config["notifications"]["channels"][0]
        assert "notification_mode" in channel
        assert channel["notification_mode"] == "stages_only"
```

**Success Criteria**:
- Integration test passes
- Manual verification: `teambot init` flow works correctly

---

## Phase 4: Documentation & Validation

### Task 4.1: Update notifications documentation

**File**: `docs/guides/notifications.md`

**Add Section**:
```markdown
## Notification Modes

Instead of listing individual event types, you can use notification mode presets
to control how many notifications you receive:

| Mode | Events | Use Case |
|------|--------|----------|
| `stages_only` | Stage transitions, workflow start/end | Low noise, major milestones only |
| `agent_status` | Stages + agent lifecycle (start/complete/fail) | Monitor agent health |
| `all` | All notification events | Full visibility, debugging |

### Configuration Example

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
      }
    ]
  }
}
```

### Precedence Rules

1. **`events` array** (if specified) takes precedence over `notification_mode`
2. **`notification_mode`** expands to its preset event set
3. **Default** (neither specified) accepts all events

This ensures backwards compatibility — existing configurations with `events` arrays
continue to work unchanged.
```

---

### Task 4.2: Run full test suite for backwards compatibility

**Validation Commands**:
```bash
# Run all notification tests
uv run pytest tests/test_notifications/ -v

# Run with coverage
uv run pytest tests/test_notifications/ --cov=src/teambot/notifications --cov-report=term-missing

# Lint and format
uv run ruff format .
uv run ruff check . --fix

# Full test suite
uv run pytest
```

**Success Criteria**:
- All existing notification tests pass (no regressions)
- New tests pass
- Coverage ≥ 90% for new code
- No lint errors

---

## Files Summary

| File | Action | Description |
|------|--------|-------------|
| `src/teambot/notifications/modes.py` | CREATE | Mode definitions and resolver |
| `src/teambot/notifications/config.py` | MODIFY | Add mode expansion in `_create_channel()` |
| `src/teambot/cli.py` | MODIFY | Add mode selection to init wizard |
| `tests/test_notifications/test_modes.py` | CREATE | Tests for mode definitions |
| `tests/test_notifications/test_config.py` | MODIFY | Tests for mode config loading |
| `docs/guides/notifications.md` | MODIFY | Document notification modes |

---

## Edge Cases to Handle

| Edge Case | Expected Behavior |
|-----------|-------------------|
| Empty `events` array with `notification_mode` set | Empty `events` wins → no notifications |
| `notification_mode` with typo (e.g., "STAGES_ONLY") | `ValueError` with valid modes listed |
| Both `events` and `notification_mode` specified | `events` takes precedence |
| Neither specified | Default to `None` (all events) |
| Multiple channels with different modes | Each channel filters independently |
