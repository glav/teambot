# Problem Statement: @notify Command Bypass for notification_mode Filtering

## Business Problem

### Current Situation

TeamBot's notification system uses a `notification_mode` setting (`stages_only`, `agent_status`, `all`) to control the volume of automated notifications during file-based orchestration workflows. This filtering mechanism successfully reduces notification noise from automated events like stage transitions and agent status updates.

However, the `@notify <msg>` command—which allows users to send explicit, intentional messages—is currently subject to the same mode-based filtering. This creates a user experience problem:

**When `notification_mode` is set to `stages_only` or `agent_status`, explicit `@notify` messages are silently dropped**, even though:
- Notifications are enabled (`notifications.enabled: true`)
- A valid channel is configured
- The user explicitly requested the notification

### Impact

| Stakeholder | Impact |
|-------------|--------|
| **Users** | Cannot send explicit notifications when using restrictive modes, leading to confusion and missed communications |
| **Workflow Operators** | Must choose between notification noise reduction (`stages_only`) OR the ability to send explicit messages—cannot have both |
| **Teams** | Important manual notifications may be lost, reducing trust in the notification system |

### Root Cause

The `custom_message` event type (used by `@notify`) is treated identically to automated events in the filtering logic. The `notification_mode` preset expansion (`resolve_notification_mode()`) does not include `custom_message` in modes other than `all`, causing explicit user requests to be filtered out.

---

## Goals

### Primary Goal

Enable `@notify <msg>` to deliver notifications reliably when the notification system is enabled and configured, **regardless of `notification_mode` setting**.

### Secondary Goals

1. **Preserve Existing Filtering**: The `notification_mode` setting must continue to filter automated events (`stage_changed`, `agent_running`, etc.) as before
2. **Maintain Backwards Compatibility**: Channels with explicit `events` arrays should continue to work as expected
3. **Minimal Change**: The fix should be surgical—no large refactors or architectural changes

---

## Success Criteria

| # | Criterion | Verification Method |
|---|-----------|---------------------|
| 1 | `@notify <msg>` sends when `notifications.enabled: true` and at least one channel is configured, **regardless of `notification_mode`** | Unit test |
| 2 | `@notify <msg>` does NOT send when `notifications.enabled: false` | Unit test (existing behavior preserved) |
| 3 | `@notify <msg>` shows "No notification channels configured" when enabled but no channels exist | Unit test (existing behavior preserved) |
| 4 | `notification_mode` continues to filter other event types (`stage_changed`, `agent_running`, etc.) as before | Unit tests (existing tests pass) |
| 5 | Unit tests cover the new bypass behavior for `custom_message` events | New test cases added |
| 6 | Existing notification mode tests continue to pass | CI pipeline green |
| 7 | Documentation updated to clarify that `@notify` bypasses mode filtering | Documentation review |

---

## Scope

### In Scope

- Modify event filtering logic to treat `custom_message` as a special case that bypasses `notification_mode` filtering
- Add unit tests for the new bypass behavior
- Update documentation to clarify `@notify` behavior

### Out of Scope

- Changes to how explicit `events` arrays work on channels
- Changes to `notifications.enabled` behavior
- Changes to channel configuration structure
- Refactoring of the notification architecture

---

## Assumptions

1. The `custom_message` event type is **only** triggered by explicit `@notify` commands (never by automated workflows)
2. Users who use `@notify` expect the message to be delivered when notifications are enabled
3. The current behavior (filtering `custom_message`) is unintentional, not a deliberate design choice

---

## Dependencies

| Dependency | Description |
|------------|-------------|
| `src/teambot/notifications/modes.py` | Contains `notification_mode` resolution logic |
| `src/teambot/notifications/config.py` | Contains channel configuration and event filtering |
| `src/teambot/tasks/executor.py` | Contains `_handle_notify()` implementation |
| Existing test suite | Must remain passing |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing `notification_mode` filtering | Low | High | Comprehensive test coverage; regression tests |
| Unexpected behavior with explicit `events` arrays | Low | Medium | Verify bypass only applies to mode-based filtering, not explicit arrays |
| Documentation not updated | Medium | Low | Include documentation in acceptance criteria |

---

## Stakeholder Alignment

- **Users**: Expect `@notify` to work when notifications are enabled
- **Maintainers**: Expect minimal, well-tested changes
- **Operators**: Expect backwards compatibility with existing configurations

---

## Recommendation

Proceed to the **SPEC** stage to define the detailed technical specification for implementing the `custom_message` bypass behavior.
