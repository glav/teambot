<!-- markdownlint-disable-file -->
# Release Changes: @notify Command Bypass Mode Filtering

**Related Plan**: 20260218-notify-bypass-mode-filtering-plan.instructions.md
**Implementation Date**: 2026-02-18

## Summary

Modify notification filtering to ensure `@notify <msg>` commands always deliver when notifications are enabled and channels are configured, bypassing `notification_mode` filtering.

## Changes

### Added

* `tests/test_notifications/test_config.py` - Added `TestCustomMessageBypassMode` test class with 4 tests for bypass behavior

### Modified

* `src/teambot/notifications/config.py` - Added `custom_message` bypass logic in `_create_channel()` function (4 lines)
* `docs/guides/notifications.md` - Added documentation for `@notify` mode bypass behavior

### Removed

(none)

## Release Summary

**Total Files Affected**: 3

### Files Created (0)

### Files Modified (3)

* `src/teambot/notifications/config.py` - Added `custom_message` to mode-based subscribed events for @notify bypass
* `tests/test_notifications/test_config.py` - Added `TestCustomMessageBypassMode` test class (4 tests)
* `docs/guides/notifications.md` - Documented @notify mode bypass behavior

### Files Removed (0)

### Dependencies & Infrastructure

* **New Dependencies**: None
* **Updated Dependencies**: None
* **Infrastructure Changes**: None
* **Configuration Updates**: None

### Deployment Notes

No deployment changes required. This is a behavioral fix in the notification filtering logic.
