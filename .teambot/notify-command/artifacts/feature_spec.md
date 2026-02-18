<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# @notify Command Mode Bypass - Feature Specification Document
Version 1.0 | Status DRAFT | Owner BA Agent | Team TeamBot Core | Target v0.2.x | Lifecycle Implementation-Ready

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-18 |
| Problem & Users | ✅ | None | 2026-02-18 |
| Scope | ✅ | None | 2026-02-18 |
| Requirements | ✅ | None | 2026-02-18 |
| Metrics & Risks | ✅ | None | 2026-02-18 |
| Operationalization | ✅ | None | 2026-02-18 |
| Finalization | ✅ | None | 2026-02-18 |
Unresolved Critical Questions: 0 | TBDs: 0

## 1. Executive Summary

### Context
TeamBot's notification system uses `notification_mode` settings (`stages_only`, `agent_status`, `all`) to control notification volume during file-based orchestration workflows. This filtering successfully reduces noise from automated events. However, the `@notify <msg>` command—an explicit user request to send a message—is incorrectly subject to the same mode-based filtering, causing user messages to be silently dropped.

### Core Opportunity
Enable `@notify <msg>` to reliably deliver notifications when the system is enabled and configured, regardless of `notification_mode` setting. This distinguishes explicit user commands from automated workflow events while preserving existing filtering for automated notifications.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | @notify bypasses notification_mode filtering | Functional | Filtered by mode | Always delivered when enabled | v0.2.x | P0 |
| G-002 | Preserve existing mode filtering for automated events | Compatibility | Working | No regression | v0.2.x | P0 |
| G-003 | Maintain backwards compatibility with explicit events arrays | Compatibility | Working | No regression | v0.2.x | P1 |

### Objectives (Optional)
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| User trust in @notify | 100% delivery rate when enabled/configured | P0 | TeamBot Core |
| Zero regression | All existing notification tests pass | P0 | TeamBot Core |

## 2. Problem Definition

### Current Situation
TeamBot users can configure `notification_mode` to control automated notification frequency:
- `stages_only`: Only stage transition events
- `agent_status`: Stage events plus agent running/complete/failed
- `all`: All notification events (no filtering)

The `@notify <msg>` command emits a `custom_message` event type, which is treated identically to automated events in the filtering logic.

### Problem Statement
**When `notification_mode` is set to `stages_only` or `agent_status`, explicit `@notify` messages are silently dropped**, even when:
- Notifications are enabled (`notifications.enabled: true`)
- A valid channel is configured
- The user explicitly requested the notification

This violates user expectations: when a user types `@notify "Build complete!"`, they expect that message to be delivered.

### Root Causes
* The `custom_message` event type is not included in `STAGES_ONLY_EVENTS` or `AGENT_STATUS_EVENTS` mode presets
* The `supports_event()` filtering in `TelegramChannel` treats all event types equally
* No special-casing exists to distinguish explicit user requests from automated workflow events

### Impact of Inaction
- Users cannot rely on `@notify` when using noise-reducing notification modes
- Users must choose between notification noise reduction OR the ability to send explicit messages
- Reduced trust in the notification system leads to workarounds or abandonment

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| **Workflow Operator** | Use `stages_only` mode to reduce noise while still being able to send important messages manually | `@notify` commands silently fail | High - cannot communicate critical updates |
| **CI/CD Engineer** | Configure TeamBot for automated workflows with occasional manual notifications | Must use `all` mode (too noisy) or lose `@notify` capability | Medium - forced tradeoff |
| **Team Lead** | Receive only important notifications | May miss explicit `@notify` alerts from team members | Medium - communication gaps |

### Journeys (Optional)
1. **Current (broken)**: User sets `notification_mode: stages_only` → Types `@notify "Deployment ready"` → Message silently dropped → User confused why notification didn't arrive
2. **Expected (fixed)**: User sets `notification_mode: stages_only` → Types `@notify "Deployment ready"` → Message delivered → Automated events remain filtered

## 4. Scope

### In Scope
* Modify `supports_event()` logic to always accept `custom_message` event type (bypass mode filtering)
* Add unit tests for the new bypass behavior
* Update documentation to clarify `@notify` behavior
* Ensure explicit `events` arrays continue to work as expected

### Out of Scope (justify if empty)
* Changes to how explicit `events` arrays work on channels (users can still exclude `custom_message` explicitly if desired)
* Changes to `notifications.enabled` behavior (existing guard)
* Changes to channel configuration structure
* Refactoring of the notification architecture
* Adding new notification channels or event types

### Assumptions
* The `custom_message` event type is **only** triggered by explicit `@notify` commands (never by automated workflows)
* Users who use `@notify` expect the message to be delivered when notifications are enabled
* The current behavior (filtering `custom_message`) is unintentional, not a deliberate design choice

### Constraints
* Must be a minimal, surgical change—no large refactors
* Must not break any existing tests
* Python 3.10+ compatibility required

## 5. Product Overview

### Value Proposition
`@notify <msg>` becomes a reliable communication tool that works in all notification modes, enabling users to reduce automated notification noise while maintaining the ability to send explicit messages.

### Differentiators (Optional)
* Clear semantic distinction: automated events are filtered by mode; explicit user commands always go through
* Backwards compatible: existing configurations continue to work

### UX / UI (Conditional)
No UI changes required. The `@notify` command syntax remains unchanged. | UX Status: N/A

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | custom_message bypasses mode filtering | The `custom_message` event type must bypass `notification_mode` filtering in the `supports_event()` check | G-001 | All | P0 | `@notify` delivers when `notifications.enabled=true` and channel configured, regardless of `notification_mode` | Core requirement |
| FR-002 | Preserve disabled behavior | `@notify` must NOT send when `notifications.enabled` is `false` | G-002 | All | P0 | Existing behavior unchanged | Regression guard |
| FR-003 | Preserve no-channels behavior | `@notify` must show "No notification channels configured" when enabled but no channels exist | G-002 | All | P0 | Existing behavior unchanged | Regression guard |
| FR-004 | Mode filtering for other events | `notification_mode` must continue to filter `stage_changed`, `agent_running`, etc. as before | G-002 | All | P0 | All existing mode filtering tests pass | Regression guard |
| FR-005 | Explicit events array precedence | Channels with explicit `events` arrays can still exclude `custom_message` if desired | G-003 | CI/CD Engineer | P1 | Explicit `events: []` or `events: ["stage_changed"]` excludes `custom_message` | Edge case |

### Feature Hierarchy (Optional)
```plain
@notify Command Bypass
├── Core: FR-001 custom_message bypass
├── Guards: FR-002, FR-003, FR-004 regression prevention
└── Edge: FR-005 explicit events precedence
```

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Maintainability | Change must be minimal and localized | ≤20 lines of production code changed | P0 | Code review | Surgical fix |
| NFR-002 | Reliability | No regression in existing functionality | 100% existing tests pass | P0 | CI pipeline | Regression guard |
| NFR-003 | Performance | No measurable performance impact | No additional I/O or computation | P1 | Code review | Simple conditional check |
| NFR-004 | Testability | New behavior must be unit testable | New test cases added | P0 | Test coverage | Required |

## 8. Data & Analytics (Conditional)

### Inputs
- `custom_message` event emitted by `@notify` handler
- Channel `subscribed_events` configuration

### Outputs / Events
- Notification delivered to configured channels (or not, based on configuration)

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|--------|---------|-------|
| N/A | N/A | N/A | No new instrumentation needed | N/A |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| @notify delivery rate | Reliability | Unknown (filtered) | 100% when enabled/configured | Post-release | User feedback |
| Test coverage | Quality | Existing | ≥ existing + new cases | Pre-release | pytest-cov |

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| `src/teambot/notifications/channels/telegram.py` | Code | High | TeamBot Core | Low | Primary implementation location |
| `src/teambot/notifications/modes.py` | Code | Medium | TeamBot Core | Low | Reference only (no changes expected) |
| `src/teambot/notifications/config.py` | Code | Medium | TeamBot Core | Low | May need minor change for bypass logic |
| Existing test suite | Test | High | TeamBot Core | Low | Must pass unchanged |

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | Breaking existing notification_mode filtering | High | Low | Comprehensive test coverage; targeted change | Builder | Open |
| R-002 | Unexpected behavior with explicit events arrays | Medium | Low | Test explicit events override; document behavior | Builder | Open |
| R-003 | Documentation not updated | Low | Medium | Include docs update in acceptance criteria | Writer | Open |

## 11. Privacy, Security & Compliance

### Data Classification
No new data is collected or stored. The `@notify` message content is user-provided and transient.

### PII Handling
N/A - No PII changes. Existing message handling unchanged.

### Threat Considerations
N/A - No new attack surface. The change is internal filtering logic only.

### Regulatory / Compliance (Conditional)
| Regulation | Applicability | Action | Owner | Status |
|-----------|--------------|--------|-------|--------|
| N/A | N/A | N/A | N/A | N/A |

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Standard release process | No special deployment needs |
| Rollback | Revert commit | Simple code change, easy rollback |
| Monitoring | Existing notification logging | No additional monitoring needed |
| Alerting | N/A | No new alerts required |
| Support | Update user-facing docs | Clarify @notify behavior |
| Capacity Planning | N/A | No capacity impact |

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|--------------|-------|
| Implementation | TBD | Code complete, tests pass | Builder |
| Code Review | TBD | Approved PR | Reviewer |
| Documentation | TBD | Docs updated | Writer |
| Release | TBD | Merged to main | PM |

### Feature Flags (Conditional)
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|--------|----------------|
| N/A | N/A | N/A | Feature is always-on (no flag needed) |

### Communication Plan (Optional)
- Update CHANGELOG.md with behavior change
- Update notification documentation

## 14. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| (none) | All questions resolved | N/A | N/A | N/A |

## 15. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 1.0 | 2026-02-18 | BA Agent | Initial specification | Draft |

## 16. References & Provenance

| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | Problem Statement | .teambot/notify-command/artifacts/problem_statement.md | Business problem definition | N/A |
| REF-002 | Code Analysis | src/teambot/notifications/modes.py | Mode resolution logic | N/A |
| REF-003 | Code Analysis | src/teambot/notifications/channels/telegram.py | supports_event() implementation | N/A |
| REF-004 | Code Analysis | src/teambot/notifications/config.py | subscribed_events configuration | N/A |

### Citation Usage Notes
All code references verified against current main branch.

## 17. Acceptance Test Scenarios

### AT-001: @notify with stages_only mode
**Description**: User sends @notify when notification_mode is set to stages_only
**Preconditions**: 
- `notifications.enabled: true`
- `notification_mode: stages_only`
- At least one channel configured (e.g., Telegram)
**Steps**:
1. User enters: `@notify "Build deployment complete!"`
2. System processes the notification command
3. Observe notification delivery
**Expected Result**: Notification is delivered to configured channel despite stages_only mode
**Verification**: Channel receives message with content "Build deployment complete!"

### AT-002: @notify with agent_status mode
**Description**: User sends @notify when notification_mode is set to agent_status
**Preconditions**:
- `notifications.enabled: true`
- `notification_mode: agent_status`
- At least one channel configured
**Steps**:
1. User enters: `@notify "Manual checkpoint reached"`
2. System processes the notification command
**Expected Result**: Notification is delivered to configured channel despite agent_status mode
**Verification**: Channel receives the message

### AT-003: @notify with notifications disabled
**Description**: User sends @notify when notifications are disabled
**Preconditions**:
- `notifications.enabled: false`
- Channel configured
**Steps**:
1. User enters: `@notify "Test message"`
2. System processes the notification command
**Expected Result**: Notification is NOT sent; appropriate feedback shown
**Verification**: No notification delivered; user sees disabled message

### AT-004: @notify with no channels configured
**Description**: User sends @notify when no channels are configured
**Preconditions**:
- `notifications.enabled: true`
- `notifications.channels: []` (empty)
**Steps**:
1. User enters: `@notify "Test message"`
2. System processes the notification command
**Expected Result**: User sees "No notification channels configured" message
**Verification**: Appropriate error/info message returned

### AT-005: Automated events still filtered by mode
**Description**: Verify stage_changed events are still filtered by stages_only mode
**Preconditions**:
- `notifications.enabled: true`
- `notification_mode: stages_only`
- At least one channel configured
**Steps**:
1. Trigger a `stage_changed` event (stage transition)
2. Trigger an `agent_running` event (agent start)
3. Observe which notifications are delivered
**Expected Result**: `stage_changed` is delivered; `agent_running` is filtered out
**Verification**: Only stage transition notification received

### AT-006: Explicit events array can exclude custom_message
**Description**: Verify explicit events array takes precedence over bypass
**Preconditions**:
- `notifications.enabled: true`
- Channel configured with explicit `events: ["stage_changed"]` (excludes custom_message)
**Steps**:
1. User enters: `@notify "Test message"`
2. System processes the notification command
**Expected Result**: Notification is NOT delivered because channel explicitly excludes it
**Verification**: No notification received; explicit user configuration honored

## 18. Appendices (Optional)

### Glossary
| Term | Definition |
|------|-----------|
| `@notify` | TeamBot pseudo-agent command that sends an explicit user message as a notification |
| `custom_message` | The event type emitted by the `@notify` command |
| `notification_mode` | Configuration setting that controls which automated events generate notifications |
| `supports_event()` | Method on notification channels that determines if an event type should be delivered |

### Technical Implementation Notes

**Recommended Implementation Location**: `src/teambot/notifications/channels/telegram.py` in the `supports_event()` method

**Suggested Logic**:
```
def supports_event(self, event_type: str) -> bool:
    # custom_message always bypasses mode-based filtering
    # (but explicit events array can still exclude it)
    if event_type == "custom_message" and self._subscribed_events is not None:
        # Check if this is mode-based filtering (no explicit events array)
        # If so, bypass the filter
        ...
    
    if self._subscribed_events is None:
        return True
    return event_type in self._subscribed_events
```

**Alternative**: Add `custom_message` bypass logic in `config.py` when resolving `subscribed_events`, ensuring mode-based filters always include `custom_message`.

**Decision for Builder**: Choose the implementation approach that minimizes code changes while maintaining clarity.

Generated 2026-02-18 by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
