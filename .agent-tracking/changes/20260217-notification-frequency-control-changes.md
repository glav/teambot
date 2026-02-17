<!-- markdownlint-disable-file -->
# Release Changes: Notification Frequency Control

**Related Plan**: 20260217-notification-frequency-control-plan.instructions.md
**Implementation Date**: 2026-02-17

## Summary

Implement notification mode presets (`stages_only`, `agent_status`, `all`) that allow users to configure notification verbosity with a single setting, rather than manually specifying individual event names.

## Changes

### Added

* `src/teambot/notifications/modes.py` - New module with notification mode definitions (`STAGES_ONLY_EVENTS`, `AGENT_STATUS_EVENTS`, `NOTIFICATION_MODES`) and `resolve_notification_mode()` function
* `tests/test_notifications/test_modes.py` - Unit tests for notification mode constants and resolver function (8 tests)

### Modified

* `src/teambot/notifications/config.py` - Added `notification_mode` expansion logic in `_create_channel()` with precedence: `events` > `notification_mode` > default (all events)
* `tests/test_notifications/test_config.py` - Added `TestNotificationModeConfig` class with 6 tests for mode expansion and precedence logic
* `src/teambot/cli.py` - Added notification mode selection to `_setup_telegram_notifications()` wizard
* `tests/test_cli.py` - Added `TestInitNotificationMode` class with 3 tests for init wizard mode selection
* `docs/guides/notifications.md` - Added Notification Modes section with mode descriptions, configuration examples, and precedence rules

### Removed

## Release Summary

**Total Files Affected**: 7

### Files Created (2)

* `src/teambot/notifications/modes.py` - Notification mode definitions (STAGES_ONLY_EVENTS, AGENT_STATUS_EVENTS, NOTIFICATION_MODES) and resolve_notification_mode() function
* `tests/test_notifications/test_modes.py` - Unit tests for notification mode constants and resolver function (8 tests)

### Files Modified (5)

* `src/teambot/notifications/config.py` - Added notification_mode expansion logic in _create_channel() with precedence rules
* `src/teambot/cli.py` - Added notification mode selection to Telegram notification setup wizard
* `tests/test_notifications/test_config.py` - Added TestNotificationModeConfig class with 6 tests
* `tests/test_cli.py` - Added TestInitNotificationMode class with 3 tests
* `docs/guides/notifications.md` - Added Notification Modes section with mode descriptions, examples, and precedence rules

### Files Removed (0)

None

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: New `notification_mode` channel config option with values: `stages_only`, `agent_status`, `all`

### Deployment Notes

No special deployment considerations. Feature is backwards compatible - existing configurations with explicit `events` arrays continue to work unchanged.
