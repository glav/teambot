# Problem Statement: Notification UX Improvements

## Executive Summary

TeamBot's notification system lacks visibility into orchestration run lifecycle events and provides no mechanism for users to verify their notification configuration before starting long-running workflows.

---

## Business Problem

### Current State

TeamBot has a functional notification system with:
- EventBus for async event dispatch to multiple channels
- Telegram channel implementation with HTML-formatted templates
- Event types for stage transitions, parallel execution, and agent status

**However, significant UX gaps exist:**

| Gap | User Impact |
|-----|-------------|
| **No run start/end notifications** | Users don't know when orchestration begins or completes without watching the terminal |
| **No way to test notification config** | Users must start a full orchestration run to verify notifications work |
| **Missing objective context** | Notifications lack clear identification of which objective is being worked on |

### Pain Points

1. **Blind Configuration**: Users configure Telegram tokens and chat IDs but have no way to confirm the setup works until they run a full workflow—which may take 30+ minutes.

2. **Lack of Run Context**: When users have multiple TeamBot runs or workflows, notifications don't clearly indicate which objective they relate to.

3. **Missing Lifecycle Visibility**: Users step away from their terminal and miss when a run starts or finishes. They have no push notification marking these key milestones.

---

## Goals

### Primary Goals

| # | Goal | Business Value |
|---|------|----------------|
| G1 | **Header notifications on run start** | Users receive immediate confirmation that orchestration has begun with objective identification |
| G2 | **Footer notifications on run complete** | Users receive clear notification when work is done, enabling them to review results promptly |
| G3 | **`/notify` REPL command** | Users can validate notification configuration in seconds rather than waiting for a full run |

### Secondary Goals

| # | Goal | Business Value |
|---|------|----------------|
| G4 | Clear feedback in both terminal UI and notification channels | Consistent UX across all interfaces |
| G5 | Graceful handling of missing configuration | Helpful error messages guide users to proper setup |

---

## Success Criteria

### Header/Footer Notifications

- [ ] **SC-1**: When an orchestration run starts, a header notification is sent to all configured channels with the objective name/description (e.g., "🚀 Starting: Realtime Notifications objective")
- [ ] **SC-2**: When an orchestration run completes, a footer notification is sent summarizing completion (e.g., "✅ Completed: Realtime Notifications objective")
- [ ] **SC-3**: Header/footer messages appear both in the output pane (terminal UI) and via notifications
- [ ] **SC-4**: If objective information is missing, notifications gracefully fall back to generic "orchestration run" text

### `/notify` Command

- [ ] **SC-5**: `/notify <message>` sends the provided message through all configured notification channels
- [ ] **SC-6**: `/notify` without a message displays usage help
- [ ] **SC-7**: `/notify` provides clear feedback in the REPL indicating success or failure
- [ ] **SC-8**: If notifications are not configured, `/notify` displays a helpful error message guiding users to run `teambot init` or configure the `notifications` section

### Documentation & Quality

- [ ] **SC-9**: `/help` command output includes `/notify` in the command list
- [ ] **SC-10**: All new functionality has test coverage following existing `pytest`/`pytest-mock` patterns

---

## Stakeholders

| Stakeholder | Interest | Priority |
|-------------|----------|----------|
| **TeamBot Users** | Want timely visibility into run status without watching terminal | High |
| **DevOps Engineers** | Need to verify notification integrations work before committing to workflows | High |
| **Project Managers** | Want audit trail of when objectives start/complete | Medium |

---

## Constraints

### Technical Constraints

1. **Must integrate with existing `EventBus`** — Use current pub/sub pattern, not parallel systems
2. **Must use `NotificationChannel` protocol** — Work with Telegram and future channels
3. **Must not break existing notifications** — All current event types must continue working
4. **Graceful degradation** — Missing objective info should not cause errors

### Scope Constraints

1. Only notification UX improvements — no changes to core orchestration logic
2. REPL command implementation — no new CLI flags or subcommands
3. Existing test patterns — use `pytest` with `pytest-mock`

---

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| `EventBus` | Internal | ✅ Available |
| `NotificationChannel` protocol | Internal | ✅ Available |
| `MessageTemplates` | Internal | ✅ Available (needs new templates) |
| `SystemCommands` dispatcher | Internal | ✅ Available (needs new handler) |
| Telegram channel | Internal | ✅ Implemented |

---

## Assumptions

1. **EventBus is accessible from REPL context** — The `/notify` command handler will have access to an EventBus instance (may need dependency injection)
2. **Objective information is available at run start** — The execution loop has access to objective name/description when beginning orchestration
3. **Synchronous emission is acceptable for `/notify`** — Using `emit_sync()` for manual notifications aligns with existing patterns
4. **Single notification per lifecycle event** — Header sent once at start, footer sent once at completion (not per-stage)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| EventBus not accessible from REPL | Medium | High | Verify dependency injection path; may need refactoring |
| Objective name not available in execution context | Low | Medium | Design fallback text; check execution_loop.py for available context |
| Rate limiting on notification channels | Low | Low | Use existing retry/backoff logic in EventBus |

---

## Measurable Outcomes

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Configuration validation time** | < 5 seconds with `/notify` vs 30+ min with full run | Manual testing |
| **Run lifecycle visibility** | 100% of runs have start/end notifications | Automated tests |
| **User error recovery** | Helpful error message on misconfiguration | Usability testing |

---

## Appendix: Current Architecture

### Event Flow

```
User triggers orchestration
         │
         ▼
┌─────────────────┐
│ ExecutionLoop   │ ─── emits: stage_changed, parallel_group_*, etc.
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    EventBus     │ ─── async dispatch with retry
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TelegramChannel │ ─── formats via MessageTemplates, sends HTTP
└─────────────────┘
```

### New Events Needed

| Event Type | Trigger Point | Data Payload |
|------------|---------------|--------------|
| `orchestration_started` | ExecutionLoop.run() start | `{objective_name, objective_path}` |
| `orchestration_completed` | ExecutionLoop.run() success | `{objective_name, status, duration}` |
| `custom_message` | `/notify` command | `{message}` |

---

*Document created: Business Problem Stage*
*Objective: Notification UX Improvements*
