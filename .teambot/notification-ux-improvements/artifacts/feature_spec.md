<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Notification UX Improvements - Feature Specification Document
Version 1.0 | Status Draft | Owner BA Agent | Team TeamBot | Target v0.2.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | ✅ | None | 2026-02-11 |
| Problem & Users | ✅ | None | 2026-02-11 |
| Scope | ✅ | None | 2026-02-11 |
| Requirements | ✅ | None | 2026-02-11 |
| Metrics & Risks | ✅ | None | 2026-02-11 |
| Operationalization | ✅ | None | 2026-02-11 |
| Finalization | ✅ | None | 2026-02-11 |
Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context
TeamBot is a CLI tool that orchestrates multi-agent AI workflows for software development. It includes a notification system (EventBus + NotificationChannel protocol) that sends updates via Telegram (and future channels) during orchestration runs. However, users lack visibility into when runs start/complete and have no way to verify notification configuration without running a full workflow.

### Core Opportunity
Improve notification UX by adding run lifecycle visibility (header/footer notifications) and a `/notify` REPL command for configuration validation, reducing user friction and enabling confident notification setup.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Users receive notification when orchestration run starts | UX | No notification | 100% of runs | v0.2.0 | High |
| G-002 | Users receive notification when orchestration run completes | UX | No notification | 100% of runs | v0.2.0 | High |
| G-003 | Users can validate notification config in <5 seconds | UX | 30+ min (full run) | <5 seconds | v0.2.0 | High |
| G-004 | Consistent messaging across terminal UI and notification channels | UX | Partial | 100% parity | v0.2.0 | Medium |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Header/footer notifications | Start/complete events emitted for all orchestration runs | High | Builder |
| `/notify` command | Command sends test message through all configured channels | High | Builder |
| Error handling | Helpful messages for missing/invalid notification config | Medium | Builder |

---

## 2. Problem Definition

### Current Situation
- TeamBot has a functional notification system with EventBus and Telegram channel
- Notifications are sent for stage changes, parallel execution, and agent status
- No notifications mark run start or completion
- No mechanism exists to test notification configuration without a full run

### Problem Statement
Users cannot verify their notification configuration works without starting a long-running orchestration workflow (30+ minutes). Additionally, users who step away from their terminal miss when runs start or complete because no push notifications mark these lifecycle events.

### Root Causes
- ExecutionLoop.run() does not emit start/complete events
- No `/notify` command exists in the REPL command dispatcher
- No templates exist for orchestration lifecycle events or custom messages

### Impact of Inaction
- Users waste time debugging notification configuration during important runs
- Users miss run completion, delaying their response to results
- Poor UX perception of TeamBot notification feature

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| **Developer** | Know when my run finishes so I can review results | Miss completion when away from terminal | High |
| **DevOps Engineer** | Verify Telegram integration before committing to workflow | Must run full workflow to test config | High |
| **Project Manager** | Track when objectives start/complete | No audit trail of run lifecycle | Medium |

### User Journeys

**Journey 1: Configuration Validation**
1. User configures Telegram token and chat_id in `teambot.json`
2. User opens REPL with `teambot run`
3. User types `/notify Test message` ← NEW
4. User sees "✅ Notification sent" in REPL
5. User receives test message on Telegram
6. User proceeds with confidence to run objective

**Journey 2: Run Lifecycle Visibility**
1. User starts orchestration with an objective
2. User receives "🚀 Starting: [Objective Name]" notification ← NEW
3. User steps away from terminal
4. Orchestration completes
5. User receives "✅ Completed: [Objective Name]" notification ← NEW
6. User returns to review results promptly

---

## 4. Scope

### In Scope
- New event types: `orchestration_started`, `orchestration_completed`, `custom_message`
- New templates for header/footer and custom message formatting
- `/notify <message>` REPL command implementation
- Command dispatch registration and `/help` update
- Terminal UI output for header/footer messages
- Graceful fallback when objective name is unavailable
- Error handling for missing notification configuration
- Test coverage for all new functionality

### Out of Scope
- New CLI subcommands or flags
- Changes to core orchestration logic
- New notification channels (Telegram only for now)
- Notification history/persistence
- Rich media in notifications (images, files)

### Assumptions
- EventBus instance is accessible from REPL command handler context
- Objective information (name/path) is available in ExecutionLoop context
- `emit_sync()` is appropriate for `/notify` command (non-blocking is acceptable)
- Single header at start, single footer at completion (not per-stage)

### Constraints
- Must use existing EventBus pub/sub pattern
- Must implement NotificationChannel protocol
- Must not break existing notification functionality
- Must follow existing test patterns (pytest + pytest-mock)

---

## 5. Product Overview

### Value Proposition
Enable TeamBot users to validate their notification configuration instantly and receive clear push notifications when orchestration runs start and complete, improving confidence and reducing time-to-awareness.

### Differentiators
- Zero-config test: `/notify` works with existing configuration
- Objective-aware: Header/footer include objective name for context
- Graceful degradation: Works even if objective info is missing

### UX Considerations
| Aspect | Requirement |
|--------|-------------|
| Terminal UI | Header/footer messages displayed in output pane |
| Notification format | Emoji-prefixed, clear identification of objective |
| Error messages | Actionable guidance (run `teambot init` or configure `notifications`) |
| Command feedback | Success/failure clearly indicated in REPL |

---

## 6. Functional Requirements

| FR ID | Title | Description | Goals | Personas | Priority | Acceptance Criteria | Notes |
|-------|-------|-------------|-------|----------|----------|---------------------|-------|
| FR-001 | Orchestration started event | Emit `orchestration_started` event when ExecutionLoop.run() begins | G-001 | All | High | Event contains objective_name, objective_path; sent to all channels | |
| FR-002 | Orchestration completed event | Emit `orchestration_completed` event when ExecutionLoop.run() succeeds | G-002 | All | High | Event contains objective_name, status, duration; sent to all channels | |
| FR-003 | Orchestration started template | Format `orchestration_started` event as "🚀 Starting: {objective_name}" | G-001, G-004 | All | High | Falls back to "orchestration run" if name missing | |
| FR-004 | Orchestration completed template | Format `orchestration_completed` event as "✅ Completed: {objective_name}" | G-002, G-004 | All | High | Falls back to "orchestration run" if name missing | |
| FR-005 | Custom message event | Support `custom_message` event type for arbitrary notifications | G-003 | All | High | Event contains user-provided message text | |
| FR-006 | Custom message template | Format `custom_message` event with user's message text | G-003, G-004 | All | High | Message displayed as-is (HTML escaped) | |
| FR-007 | /notify command handler | Implement `/notify <message>` command in SystemCommands | G-003 | DevOps | High | Sends message via EventBus; returns CommandResult | |
| FR-008 | /notify usage help | Display usage help when `/notify` called without arguments | G-003 | All | Medium | Shows "Usage: /notify <message>" | |
| FR-009 | /notify success feedback | Display success message in REPL after notification sent | G-003 | All | High | Shows "✅ Notification sent: {message}" | |
| FR-010 | /notify failure feedback | Display error message if notification delivery fails | G-003 | All | High | Shows "❌ Notification failed: {reason}" | |
| FR-011 | /notify missing config error | Display helpful error if notifications not configured | G-003 | All | High | Suggests running `teambot init` or configuring `notifications` section | |
| FR-012 | /help update | Add `/notify` to `/help` command output | G-003 | All | Medium | Shows `/notify <message>` with description | |
| FR-013 | Terminal UI header | Display header message in output pane when run starts | G-001, G-004 | All | Medium | Same content as notification | |
| FR-014 | Terminal UI footer | Display footer message in output pane when run completes | G-002, G-004 | All | Medium | Same content as notification | |

### Feature Hierarchy
```
notification-ux-improvements/
├── events/
│   ├── orchestration_started
│   ├── orchestration_completed
│   └── custom_message
├── templates/
│   ├── orchestration_started_template
│   ├── orchestration_completed_template
│   └── custom_message_template
├── commands/
│   ├── /notify handler
│   ├── /notify help
│   └── /help update
└── terminal-ui/
    ├── header display
    └── footer display
```

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|---------------|----------|------------|-------|
| NFR-001 | Performance | `/notify` command responds within 1 second | <1s latency | High | Manual test | Async emission acceptable |
| NFR-002 | Reliability | Notification delivery uses existing retry logic | 3 retries with exponential backoff | High | Unit test | Leverages EventBus retry |
| NFR-003 | Maintainability | New code follows existing patterns | 100% pattern compliance | High | Code review | Match templates.py, commands.py styles |
| NFR-004 | Security | User messages HTML-escaped before sending | No raw HTML injection | High | Unit test | Use html.escape() |
| NFR-005 | Observability | Log notification events for debugging | Structured logging | Medium | Code review | Follow existing logging pattern |
| NFR-006 | Accessibility | Error messages are clear and actionable | User can resolve without docs | Medium | UX review | Include specific guidance |

---

## 8. Data & Analytics

### Inputs
| Input | Source | Format |
|-------|--------|--------|
| Objective name | Objective file frontmatter or filename | String |
| Objective path | CLI argument or REPL context | File path |
| User message | `/notify` command argument | String |
| Notification config | `teambot.json` | JSON |

### Outputs / Events
| Event Type | Trigger | Data Fields |
|------------|---------|-------------|
| `orchestration_started` | ExecutionLoop.run() start | `objective_name`, `objective_path` |
| `orchestration_completed` | ExecutionLoop.run() success | `objective_name`, `status`, `duration_seconds` |
| `custom_message` | `/notify` command | `message` |

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|---------|---------|-------|
| orchestration_started | ExecutionLoop.run() entry | {objective_name, objective_path} | Run visibility | Builder |
| orchestration_completed | ExecutionLoop.run() exit | {objective_name, status, duration} | Run visibility | Builder |
| custom_message | /notify command | {message} | Config validation | Builder |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Config validation time | UX | 30+ min | <5 sec | Per use | Manual test |
| Lifecycle notification coverage | Reliability | 0% | 100% | Per run | Automated test |
| Error message clarity | UX | N/A | Actionable | Per error | User feedback |

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| EventBus | Internal | High | Existing | Low | Already implemented and stable |
| NotificationChannel protocol | Internal | High | Existing | Low | Well-defined interface |
| MessageTemplates | Internal | High | Existing | Low | Extend with new templates |
| SystemCommands dispatcher | Internal | High | Existing | Low | Add new handler |
| TelegramChannel | Internal | Medium | Existing | Low | Already supports custom events |
| ExecutionLoop | Internal | High | Existing | Low | Add event emission at start/end |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | EventBus not accessible from REPL context | High | Medium | Verify DI path; refactor if needed | Builder | Open |
| R-002 | Objective name not available in ExecutionLoop | Medium | Low | Design fallback text; check context | Builder | Open |
| R-003 | Rate limiting on Telegram | Low | Low | Use existing EventBus retry logic | Builder | Mitigated |
| R-004 | Breaking existing notifications | High | Low | Comprehensive regression tests | Builder | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification
- **Objective names**: Internal, non-sensitive
- **User messages via /notify**: User-controlled, potentially sensitive
- **Notification tokens**: Secrets, stored in config

### PII Handling
- No PII collected or transmitted by this feature
- User messages are passed through without modification (except HTML escaping)

### Threat Considerations
- **HTML injection**: Mitigated by html.escape() on all user input
- **Token exposure**: Tokens read from config, not logged
- **Message interception**: Relies on HTTPS for Telegram API

### Regulatory / Compliance
N/A - No regulatory requirements apply to this feature.

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Standard pip install | No new dependencies |
| Rollback | Remove new event emissions | Backward compatible |
| Monitoring | Existing structured logging | No new infrastructure |
| Alerting | N/A | User-facing feature |
| Support | Document `/notify` in user guide | Update docs/guides/ |
| Capacity Planning | N/A | Minimal additional load |

---

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Gate Criteria | Owner |
|-------|---------------|-------|
| Implementation | All FRs implemented | Builder |
| Testing | 100% test coverage on new code | Builder |
| Review | Code review approved | Reviewer |
| Documentation | User guide updated | Writer |
| Release | Merged to main | PM |

### Feature Flags
N/A - Feature is always enabled when notifications are configured.

### Communication Plan
- Update `docs/guides/notifications.md` with `/notify` usage
- Add section on run lifecycle notifications

---

## 14. Acceptance Test Scenarios

### AT-001: Header Notification on Run Start
**Description**: User starts orchestration and receives start notification
**Preconditions**: Notifications configured in teambot.json, Telegram channel enabled
**Steps**:
1. User runs `teambot run objectives/my-feature.md`
2. Orchestration begins
3. Observe notification channel
**Expected Result**: Telegram receives "🚀 Starting: my-feature objective"
**Verification**: Message appears in configured Telegram chat within 5 seconds

### AT-002: Footer Notification on Run Complete
**Description**: User completes orchestration and receives completion notification
**Preconditions**: Orchestration running with notifications configured
**Steps**:
1. Orchestration run completes successfully
2. Observe notification channel
**Expected Result**: Telegram receives "✅ Completed: my-feature objective"
**Verification**: Message appears in configured Telegram chat; includes run duration

### AT-003: /notify Command Success
**Description**: User sends test notification via REPL command
**Preconditions**: REPL running, notifications configured
**Steps**:
1. User enters `/notify Hello from TeamBot!`
2. Observe REPL output
3. Observe Telegram chat
**Expected Result**: 
- REPL shows "✅ Notification sent: Hello from TeamBot!"
- Telegram receives "Hello from TeamBot!"
**Verification**: Both outputs match expected text

### AT-004: /notify Without Message Shows Help
**Description**: User runs /notify without arguments
**Preconditions**: REPL running
**Steps**:
1. User enters `/notify` (no message)
2. Observe REPL output
**Expected Result**: REPL shows usage help "Usage: /notify <message>"
**Verification**: Help text is displayed, no notification sent

### AT-005: /notify With Missing Configuration
**Description**: User runs /notify without notification config
**Preconditions**: REPL running, no notifications section in teambot.json
**Steps**:
1. User enters `/notify Test message`
2. Observe REPL output
**Expected Result**: REPL shows error "❌ Notifications not configured. Run `teambot init` or add `notifications` section to teambot.json."
**Verification**: Error is actionable; guides user to resolution

### AT-006: Header/Footer with Missing Objective Name
**Description**: System handles missing objective information gracefully
**Preconditions**: Objective file lacks name/description
**Steps**:
1. Start orchestration with objective that has no frontmatter name
2. Observe notifications
**Expected Result**: Notifications use fallback "orchestration run" instead of objective name
**Verification**: No errors; generic text displayed

### AT-007: /help Includes /notify
**Description**: Help command lists /notify
**Preconditions**: REPL running
**Steps**:
1. User enters `/help`
2. Review command list
**Expected Result**: Output includes `/notify <message> - Send a test notification`
**Verification**: /notify appears in help output with description

---

## 15. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| - | - | - | - | All resolved |

---

## 16. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-11 | BA Agent | Initial specification | New |

---

## 17. References & Provenance

| Ref ID | Type | Source | Summary |
|--------|------|--------|---------|
| REF-001 | Problem Statement | .teambot/notification-ux-improvements/artifacts/problem_statement.md | Business problem analysis |
| REF-002 | Code | src/teambot/notifications/events.py | NotificationEvent dataclass |
| REF-003 | Code | src/teambot/notifications/templates.py | MessageTemplates pattern |
| REF-004 | Code | src/teambot/repl/commands.py | SystemCommands dispatcher |
| REF-005 | Code | src/teambot/orchestration/execution_loop.py | Event emission points |

---

## Appendix A: Implementation Reference

### New Event Types
```python
# Event type constants for new events
EVENT_ORCHESTRATION_STARTED = "orchestration_started"
EVENT_ORCHESTRATION_COMPLETED = "orchestration_completed"  
EVENT_CUSTOM_MESSAGE = "custom_message"
```

### Template Patterns
```python
# New templates to add to TEMPLATES dict
"orchestration_started": "🚀 <b>Starting</b>: {objective_name}",
"orchestration_completed": "✅ <b>Completed</b>: {objective_name}\n⏱️ Duration: {duration}",
"custom_message": "📢 {message}",
```

### Command Handler Pattern
```python
# Handler signature following existing pattern
def handle_notify(self, args: list[str]) -> CommandResult:
    if not args:
        return CommandResult(output="Usage: /notify <message>", success=False)
    # ... implementation
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| EventBus | Async pub/sub system for routing notification events |
| NotificationChannel | Protocol defining interface for notification delivery |
| REPL | Read-Eval-Print Loop; TeamBot's interactive command interface |
| Header notification | Notification sent when orchestration run starts |
| Footer notification | Notification sent when orchestration run completes |

---

Generated 2026-02-11 by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
