# Business Problem Statement: Real-Time Notifications

## Problem Definition

**TeamBot users lack visibility into workflow execution when not actively monitoring the terminal.**

TeamBot orchestrates multi-agent workflows that can run for extended periods (up to 8 hours). Currently, users must remain at their terminal or periodically check status to know when:
- Workflow stages complete or fail
- Individual agent tasks finish
- Errors or review iterations occur
- The entire pipeline completes

This creates a poor user experience for developers who want to:
- Start a workflow and switch contexts to other work
- Monitor workflows from mobile devices or other locations
- Receive immediate notification of failures requiring attention
- Get summaries of completed work without checking terminal output

## Business Goals

| Goal | Measurable Outcome |
|------|-------------------|
| **G1: Real-time awareness** | Users receive notifications within 5 seconds of workflow events occurring |
| **G2: Rich context** | Notifications include stage name, agent, duration, status, summary, and artifact list |
| **G3: Zero infrastructure** | No servers, databases, or inbound ports required on user's machine |
| **G4: Extensible platform** | New notification channels can be added without modifying core orchestration |
| **G5: Graceful degradation** | Notification failures never block or crash workflow execution |
| **G6: Secure by design** | No secrets stored in configuration files; environment variable resolution only |

## Target Users

1. **Solo developers** using TeamBot for personal projects who want to multitask
2. **Team leads** monitoring workflows started by team members
3. **Remote workers** who start long-running workflows before stepping away
4. **CI/automation integrators** who need event hooks for downstream processes

## Current State

### Existing Event Infrastructure

TeamBot already has a robust progress callback system in place:

```
ExecutionLoop.execute_all()
    └── on_progress(event_type, data) callback
            ├── agent_running, agent_complete, agent_failed
            ├── stage_changed
            ├── parallel_stage_start/complete/failed
            ├── acceptance_test_stage_start
            └── review_progress
```

The `progress.py` module routes these events to `AgentStatusManager` for UI updates. This architecture provides a natural integration point for external notifications.

### Gap Analysis

| Capability | Current State | Desired State |
|-----------|---------------|---------------|
| Event emission | ✅ Exists via `on_progress` callback | Keep as-is |
| Event fanout | ❌ Single callback, tightly coupled to UI | EventBus with multiple subscribers |
| External notifications | ❌ None | Telegram (initial), extensible to Teams/Slack/GitHub |
| Message formatting | ❌ None for external use | Rich templates per channel |
| Configuration | ❌ No notification config | `notifications` section in `teambot.json` |
| Secret management | N/A | Environment variable substitution |
| Failure handling | ❌ UI errors could affect workflow | Isolated; never blocks execution |

## Success Criteria

### Must Have (P0)

- [ ] **SC1**: `NotificationChannel` protocol with `send(event)`, `format(event)`, and optional `poll()` methods
- [ ] **SC2**: `EventBus` connecting `on_progress` callbacks to notification channels with subscribe/unsubscribe
- [ ] **SC3**: `TelegramChannel` sending HTML-formatted messages via Bot API (outbound HTTP only)
- [ ] **SC4**: Notifications fire on all major events: `stage_started`, `stage_complete`, `agent_started`, `agent_complete`, `agent_failed`, `parallel_stage_*`, `pipeline_complete`, `pipeline_timeout`, `review_iteration`
- [ ] **SC5**: Rich message formatting: emoji status, bold names, duration, summary, code-formatted artifacts
- [ ] **SC6**: `teambot.json` schema supports `notifications[]` with type, env-var credentials, event subscriptions
- [ ] **SC7**: Environment variable substitution (`${VAR_NAME}`) for all secret values
- [ ] **SC8**: `teambot init` optional step guides Telegram setup (BotFather token + chat ID)
- [ ] **SC9**: Graceful error handling: network errors logged, workflow continues unaffected
- [ ] **SC10**: Rate limit (HTTP 429) triggers exponential backoff retry (3 attempts max)
- [ ] **SC11**: `dry_run` config option logs formatted messages without sending
- [ ] **SC12**: `httpx` added as dependency for async HTTP with connection pooling
- [ ] **SC13**: Version bump from `0.1.0` → `0.2.0`

### Should Have (P1)

- [ ] **SC14**: Message template system allowing per-event-type customization
- [ ] **SC15**: Clear setup instructions output after `teambot init` configuration
- [ ] **SC16**: Comprehensive test coverage following existing `pytest` patterns

### Future Scope (Out of This Phase)

- TeamsChannel via Power Automate Workflow URLs
- GitHubChannel via `gh` CLI for issue/PR comments
- Two-way Telegram communication via long-polling
- Slack webhook integration
- Notification batching/debouncing for high-frequency events

## Constraints

| Constraint | Rationale |
|-----------|-----------|
| **Outbound HTTP only** | Users must not need to configure firewalls or expose local ports |
| **No plain-text secrets** | Security compliance; tokens must come from environment variables |
| **Non-blocking notifications** | Workflow execution is the primary value; notifications are secondary |
| **Backward compatible** | Existing workflows, REPL, and UI must continue functioning unchanged |
| **Minimal dependencies** | Only `httpx` added; no heavy frameworks or external services |

## Assumptions

1. Users have internet connectivity to reach notification APIs
2. Telegram Bot API rate limits (~30 messages/second) are sufficient for TeamBot's event frequency
3. Users can create a Telegram bot via @BotFather (free, takes ~2 minutes)
4. Environment variable management is familiar to target users (developers)
5. The existing `on_progress` callback in `ExecutionLoop` can be wrapped without modification

## Dependencies

| Dependency | Type | Impact |
|-----------|------|--------|
| `httpx` library | External | Async HTTP client; must be added to `pyproject.toml` |
| Telegram Bot API | External service | Must remain available; graceful fallback on failure |
| `ExecutionLoop.execute_all()` | Internal | EventBus integrates via existing `on_progress` parameter |
| `teambot.json` config loader | Internal | Must support new `notifications` schema section |
| Environment variable resolution | New capability | Required for secret management |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Telegram API changes | Low | Medium | Version-pin API behavior; protocol allows channel swaps |
| Rate limiting blocks notifications | Low | Low | Exponential backoff; events are informational, not critical |
| User misconfigures credentials | Medium | Low | Validate on init; clear error messages on send failure |
| Network unavailability | Medium | Low | Timeout + retry; never block workflow |

## Stakeholders

- **Primary**: Individual developers using TeamBot
- **Secondary**: Teams adopting TeamBot for shared workflows
- **Technical**: TeamBot maintainers adding future channels

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Product Owner | — | — | Pending |
| Tech Lead | — | — | Pending |
| Business Analyst | BA Agent | 2026-02-11 | ✅ Defined |
