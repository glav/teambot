<!-- markdownlint-disable-file -->
# Release Changes: Real-Time Notification System

**Related Plan**: 20260211-realtime-notifications-plan.instructions.md
**Implementation Date**: 2026-02-11

## Summary

Implemented real-time notification system for TeamBot with Telegram channel support, pluggable NotificationChannel protocol, and EventBus for decoupled event routing. The system sends notifications via Telegram when workflow stages complete, agent tasks finish, or errors occur.

## Changes

### Added

* `src/teambot/notifications/__init__.py` - Module exports for notification system
* `src/teambot/notifications/events.py` - NotificationEvent dataclass for event payloads
* `src/teambot/notifications/protocol.py` - NotificationChannel Protocol (duck-typed interface)
* `src/teambot/notifications/event_bus.py` - EventBus with subscribe/unsubscribe/emit and retry logic
* `src/teambot/notifications/templates.py` - MessageTemplates for rich HTML formatting
* `src/teambot/notifications/config.py` - Env var resolver and EventBus factory
* `src/teambot/notifications/channels/__init__.py` - Channel exports
* `src/teambot/notifications/channels/telegram.py` - TelegramChannel implementation with httpx
* `tests/test_notifications/__init__.py` - Test module
* `tests/test_notifications/conftest.py` - Shared test fixtures
* `tests/test_notifications/test_events.py` - NotificationEvent tests
* `tests/test_notifications/test_protocol.py` - Protocol tests
* `tests/test_notifications/test_event_bus.py` - EventBus tests (100% coverage)
* `tests/test_notifications/test_templates.py` - MessageTemplates tests
* `tests/test_notifications/test_telegram.py` - TelegramChannel tests (94% coverage)
* `tests/test_notifications/test_config.py` - Config function tests (100% coverage)
* `tests/test_config/test_loader.py::TestNotificationsConfigValidation` - 11 validation tests

### Modified

* `pyproject.toml` - Added `httpx>=0.27.0` dependency
* `src/teambot/__init__.py` - Bumped version from 0.1.0 to 0.2.0
* `src/teambot/config/loader.py` - Added notification config validation and defaults
* `src/teambot/cli.py` - Integrated EventBus with on_progress callback, added notification setup wizard
* `src/teambot/notifications/event_bus.py` - Added emit_sync() method for sync callbacks
* `tests/test_e2e.py` - Updated version check to 0.2.0
* `tests/test_notifications/test_event_bus.py` - Added emit_sync tests

### Removed

_(No removals)_

## Release Summary

**Total Files Affected**: 22

### Files Created (17)

* `src/teambot/notifications/__init__.py` - Module exports
* `src/teambot/notifications/events.py` - Event dataclass
* `src/teambot/notifications/protocol.py` - Channel protocol
* `src/teambot/notifications/event_bus.py` - Event routing with retry
* `src/teambot/notifications/templates.py` - Message formatting
* `src/teambot/notifications/config.py` - Config utilities
* `src/teambot/notifications/channels/__init__.py` - Channel exports
* `src/teambot/notifications/channels/telegram.py` - Telegram implementation
* `tests/test_notifications/__init__.py` - Test module
* `tests/test_notifications/conftest.py` - Test fixtures
* `tests/test_notifications/test_events.py` - Event tests
* `tests/test_notifications/test_protocol.py` - Protocol tests
* `tests/test_notifications/test_event_bus.py` - EventBus tests
* `tests/test_notifications/test_templates.py` - Template tests
* `tests/test_notifications/test_telegram.py` - Telegram tests
* `tests/test_notifications/test_config.py` - Config tests

### Files Modified (5)

* `pyproject.toml` - Added httpx dependency
* `src/teambot/__init__.py` - Version bump
* `src/teambot/config/loader.py` - Notification validation
* `src/teambot/cli.py` - EventBus integration and init wizard
* `tests/test_e2e.py` - Version check update

### Files Removed (0)

_(None)_

### Dependencies & Infrastructure

* **New Dependencies**: `httpx>=0.27.0` (async HTTP with connection pooling)
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: New `notifications` section in teambot.json schema

### Deployment Notes

Users must set environment variables for Telegram notifications:
```bash
export TEAMBOT_TELEGRAM_TOKEN='your-bot-token'
export TEAMBOT_TELEGRAM_CHAT_ID='your-chat-id'
```

Run `teambot init` and answer 'y' to "Enable real-time notifications?" to configure.
