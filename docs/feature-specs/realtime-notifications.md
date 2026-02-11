<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Real-Time Notifications - Feature Specification Document
Version 1.0 | Status **Draft** | Owner TBD | Team TeamBot | Target 0.2.0 | Lifecycle Development

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | 100% | None | 2026-02-11 |
| Problem & Users | 100% | None | 2026-02-11 |
| Scope | 100% | None | 2026-02-11 |
| Requirements | 100% | None | 2026-02-11 |
| Metrics & Risks | 100% | None | 2026-02-11 |
| Research | 0% | Pending implementation | 2026-02-11 |
| Test Strategy | 100% | None | 2026-02-11 |
| Task Planning | 0% | Pending implementation | 2026-02-11 |
| Finalization | 0% | Pending implementation | 2026-02-11 |
Unresolved Critical Questions: 0 | TBDs: 0

---

## 1. Executive Summary

### Context
TeamBot orchestrates multi-agent AI workflows that can run for extended periods (up to 8 hours). Users currently must remain at their terminal or periodically check status to know when workflow stages complete, agents finish tasks, or errors occur. This creates friction for developers who want to start a workflow and context-switch to other activities.

### Core Opportunity
Implement a **pluggable real-time notification system** that:
1. Emits notifications to external channels (starting with Telegram) when workflow events occur
2. Uses an EventBus architecture to decouple event emission from notification delivery
3. Provides rich-text formatted messages with context (stage, agent, duration, status, artifacts)
4. Integrates seamlessly with `teambot init` for guided setup
5. Handles failures gracefully without interrupting workflow execution

This transforms TeamBot from a terminal-bound tool into an **ambient-aware assistant** that keeps users informed wherever they are.

### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-RTN-001 | Users receive notifications within 5 seconds of workflow events | Core | No external notifications | Real-time delivery via Telegram | MVP | P0 |
| G-RTN-002 | Notifications include rich context (stage, agent, duration, status, artifacts) | UX | N/A | All events formatted with full context | MVP | P0 |
| G-RTN-003 | Zero infrastructure required on user machine | Ops | N/A | Outbound HTTP only, no exposed ports | MVP | P0 |
| G-RTN-004 | New notification channels addable without core changes | Extensibility | N/A | Protocol-based plugin architecture | MVP | P0 |
| G-RTN-005 | Notification failures never block workflow execution | Reliability | N/A | Isolated async delivery with fallback | MVP | P0 |
| G-RTN-006 | Secrets never stored in configuration files | Security | N/A | Environment variable resolution only | MVP | P0 |

### Objectives
| Objective | Key Result | Priority | Owner |
|-----------|------------|----------|-------|
| Implement NotificationChannel protocol | send(), format(), poll() methods defined | P0 | TBD |
| Build EventBus | Subscribe/unsubscribe, async fanout to channels | P0 | TBD |
| Implement TelegramChannel | HTML-formatted messages via Bot API | P0 | TBD |
| Extend teambot init | Optional Telegram setup wizard | P0 | TBD |
| Add httpx dependency | Async HTTP with connection pooling | P0 | TBD |
| Version bump | 0.1.0 → 0.2.0 | P0 | TBD |

---

## 2. Problem Definition

### Current Situation
- **Event infrastructure exists**: `ExecutionLoop` emits events via `on_progress(event_type, data)` callback
- **Single consumer**: Events routed only to `AgentStatusManager` for terminal UI updates
- **No external delivery**: No mechanism to send notifications outside the terminal
- **No configuration**: No way to configure notification channels or credentials
- **Tight coupling**: UI is the only event consumer; adding new consumers requires code changes

### Problem Statement
TeamBot users lack visibility into workflow execution when not actively monitoring the terminal. There is no mechanism to receive notifications on external channels (mobile, messaging apps, etc.) when stages complete, agents finish, or errors occur. This forces users to remain terminal-bound during long-running workflows.

### Root Causes
* Notification system not prioritized in initial MVP (terminal UI was sufficient for interactive use)
* Event architecture designed for single consumer (UI status panel)
* No configuration schema for external integrations
* Secret management not yet addressed

### Impact of Inaction
* Users cannot context-switch during long workflows
* No mobile/remote monitoring capability
* Missed opportunities for immediate error response
* TeamBot perceived as less capable than comparable tools with notifications
* Barrier to adoption for users expecting modern DevOps tooling patterns

---

## 3. Users & Personas

| Persona | Goals | Pain Points | Impact |
|---------|-------|-------------|--------|
| Solo Developer | Start workflows before leaving desk, get notified on phone | Must watch terminal or miss events | High - primary user |
| Team Lead | Monitor team workflows from anywhere | No visibility without terminal access | High - oversight role |
| Remote Worker | Start overnight workflows, check morning results | No push notifications for completion | High - async workflow |
| CI Integrator | Hook notifications into team channels | No programmatic event access | Medium - automation |

### User Journeys

#### Journey 1: Solo Developer - Evening Workflow
1. Developer starts long workflow: `teambot run objectives/refactor.md`
2. During `teambot init`, configured Telegram notifications
3. Steps away from desk, goes to dinner
4. Phone buzzes: "✅ SPEC complete (12m 34s) - 3 artifacts created"
5. Phone buzzes: "⚠️ IMPLEMENTATION_REVIEW needs attention - reviewer requested changes"
6. Returns to desk, addresses feedback knowing exactly what needs attention

#### Journey 2: Team Lead - Multi-Project Monitoring
1. Team lead has 3 TeamBot workflows running across projects
2. Each configured with team Telegram channel notifications
3. Works on other tasks while monitoring phone
4. Receives: "❌ api-gateway IMPLEMENTATION failed - tests failing"
5. Immediately investigates, provides guidance, workflow resumes

#### Journey 3: CI Integration
1. DevOps engineer configures TeamBot in CI pipeline
2. Sets `dry_run: true` initially to validate templates
3. Switches to live mode, notifications flow to team Slack (future channel)
4. Team receives real-time updates on automated workflows

---

## 4. Scope

### In Scope
* **NotificationChannel protocol**: Abstract base with `send()`, `format()`, optional `poll()`
* **EventBus implementation**: Subscribe/unsubscribe, async fanout, error isolation
* **TelegramChannel**: HTML-formatted messages via Bot API sendMessage endpoint
* **Configuration schema**: `notifications[]` in `teambot.json` with type, credentials, events
* **Environment variable substitution**: `${VAR_NAME}` syntax for secrets
* **Init wizard extension**: Optional Telegram setup step in `teambot init`
* **Error handling**: Retry with exponential backoff, graceful degradation
* **Dry run mode**: Log formatted messages without sending
* **Test coverage**: Unit tests for all new components
* **Version bump**: 0.1.0 → 0.2.0

### Out of Scope (This Phase)
* **TeamsChannel**: Designed-for but not implemented (future via Power Automate)
* **GitHubChannel**: Designed-for but not implemented (future via `gh` CLI)
* **SlackChannel**: Designed-for but not implemented (future via webhooks)
* **Two-way communication**: Poll() method stubbed but not implemented
* **Notification batching**: No debouncing or grouping of rapid events
* **Custom templates**: Default templates only; customization deferred
* **Web dashboard**: No browser-based notification UI
* **Desktop notifications**: No native OS notification integration

### Assumptions
1. Users have internet connectivity to reach Telegram API
2. Telegram Bot API rate limits (~30 msg/sec) exceed TeamBot's event frequency
3. Users can create Telegram bot via @BotFather (free, ~2 minutes)
4. Environment variable management is familiar to target developers
5. Existing `on_progress` callback can be wrapped without modification
6. `httpx` library is acceptable as new dependency

### Constraints
| Constraint | Rationale |
|-----------|-----------|
| Outbound HTTP only | Users must not configure firewalls or expose ports |
| No plain-text secrets | Security compliance; tokens from env vars only |
| Non-blocking delivery | Workflow execution is primary; notifications secondary |
| Backward compatible | Existing workflows, REPL, UI unchanged |
| Minimal dependencies | Only `httpx` added; no heavy frameworks |
| Python 3.10+ | Match existing project requirements |

---

## 5. Product Overview

### Value Proposition
**For developers running long TeamBot workflows**, Real-Time Notifications provides **immediate visibility into workflow progress** via their preferred messaging platform, **so they can context-switch freely** while maintaining awareness of important events.

### Differentiators
* **Zero infrastructure**: No servers, databases, or webhooks to configure
* **Pluggable architecture**: Add new channels without core code changes
* **Rich formatting**: Emoji status, bold text, code blocks, hyperlinks
* **Graceful degradation**: Notification failures never affect workflow
* **Developer-first**: Secrets via env vars, not config files

### UX / UI Considerations
| Aspect | Design Decision | Rationale |
|--------|-----------------|-----------|
| Init wizard | Interactive prompts for Telegram setup | Guides users through BotFather process |
| Message format | HTML with emoji prefixes | Telegram supports HTML; emojis provide instant status recognition |
| Dry run | Logs full formatted message | Allows testing templates without spamming channel |
| Error messages | Logged with context, never displayed in workflow output | Keep workflow output clean |

---

## 6. Functional Requirements

### FR-001: NotificationChannel Protocol
| Attribute | Value |
|-----------|-------|
| **ID** | FR-001 |
| **Title** | NotificationChannel Protocol Definition |
| **Description** | Define abstract protocol/interface for notification channels with required methods |
| **Goals** | G-RTN-004 (Extensibility) |
| **Personas** | CI Integrator, future channel implementers |
| **Priority** | P0 |
| **Acceptance Criteria** | 1. Protocol defines `send(event: NotificationEvent) -> bool` method<br>2. Protocol defines `format(event: NotificationEvent) -> str` method<br>3. Protocol defines optional `poll() -> list[Message]` method stub for future two-way communication<br>4. Protocol is runtime-checkable (`@runtime_checkable`)<br>5. New channels can implement protocol without modifying core code |
| **Notes** | Use `typing.Protocol` for structural subtyping |

### FR-002: EventBus Implementation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-002 |
| **Title** | EventBus for Notification Fanout |
| **Description** | Lightweight event bus connecting ExecutionLoop.on_progress to notification channels |
| **Goals** | G-RTN-001 (Real-time), G-RTN-004 (Extensibility) |
| **Personas** | All |
| **Priority** | P0 |
| **Acceptance Criteria** | 1. EventBus supports `subscribe(channel: NotificationChannel, events: list[str])` method<br>2. EventBus supports `unsubscribe(channel: NotificationChannel)` method<br>3. EventBus exposes `emit(event_type: str, data: dict)` method compatible with `on_progress` signature<br>4. EventBus delivers events asynchronously to all subscribed channels<br>5. EventBus isolates channel failures (one failure doesn't affect others)<br>6. EventBus filters events per channel based on subscription |
| **Notes** | Consider `asyncio.create_task` for non-blocking delivery |

### FR-003: TelegramChannel Implementation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-003 |
| **Title** | Telegram Notification Channel |
| **Description** | Implementation of NotificationChannel for Telegram Bot API |
| **Goals** | G-RTN-001 (Real-time), G-RTN-002 (Rich context), G-RTN-003 (Zero infrastructure) |
| **Personas** | Solo Developer, Team Lead, Remote Worker |
| **Priority** | P0 |
| **Acceptance Criteria** | 1. Uses Telegram Bot API `sendMessage` endpoint (outbound POST only)<br>2. Sends HTML-formatted messages (parse_mode=HTML)<br>3. Resolves bot token from environment variable at runtime<br>4. Resolves chat ID from environment variable at runtime<br>5. Includes emoji status prefix based on event type<br>6. Includes bold stage/agent names<br>7. Includes duration when available<br>8. Includes summary text when available<br>9. Includes artifact list as code-formatted paths<br>10. Never exposes ports or accepts inbound connections |
| **Notes** | Use `httpx.AsyncClient` for HTTP calls |

### FR-004: Event Type Coverage
| Attribute | Value |
|-----------|-------|
| **ID** | FR-004 |
| **Title** | Comprehensive Event Coverage |
| **Description** | Notifications fire on all major workflow events |
| **Goals** | G-RTN-001 (Real-time), G-RTN-002 (Rich context) |
| **Personas** | All |
| **Priority** | P0 |
| **Acceptance Criteria** | Notifications fire on:<br>1. `stage_started` - workflow stage begins<br>2. `stage_complete` - workflow stage completes successfully<br>3. `agent_started` - agent begins task<br>4. `agent_complete` - agent finishes task<br>5. `agent_failed` - agent task fails<br>6. `parallel_stage_start` - parallel group stage begins<br>7. `parallel_stage_complete` - parallel group stage completes<br>8. `parallel_stage_failed` - parallel group stage fails<br>9. `pipeline_complete` - entire workflow completes<br>10. `pipeline_timeout` - workflow exceeds time limit<br>11. `review_iteration` - review cycle iteration |
| **Notes** | Map existing `on_progress` event types to notification events |

### FR-005: Message Template System
| Attribute | Value |
|-----------|-------|
| **ID** | FR-005 |
| **Title** | Per-Event-Type Message Templates |
| **Description** | Each event type has its own formatting template |
| **Goals** | G-RTN-002 (Rich context) |
| **Personas** | All |
| **Priority** | P1 |
| **Acceptance Criteria** | 1. Default template exists for each event type<br>2. Templates support variable substitution (stage, agent, duration, status, summary, artifacts)<br>3. Templates are defined in code (not config) for MVP<br>4. Future: Templates can be customized per channel in config |
| **Notes** | Use Python f-strings or simple string.Template |

### FR-006: Configuration Schema Extension
| Attribute | Value |
|-----------|-------|
| **ID** | FR-006 |
| **Title** | Notifications Configuration Schema |
| **Description** | teambot.json supports notifications section with channel array |
| **Goals** | G-RTN-004 (Extensibility), G-RTN-006 (Security) |
| **Personas** | All |
| **Priority** | P0 |
| **Acceptance Criteria** | 1. `notifications` key in teambot.json is optional array<br>2. Each entry has `type` (string, e.g., "telegram")<br>3. Each entry has `enabled` (boolean, default true)<br>4. Each entry has `dry_run` (boolean, default false)<br>5. Each entry has channel-specific config (e.g., `token`, `chat_id`)<br>6. Each entry has `events` array (optional, defaults to all events)<br>7. Config loader validates schema and provides clear errors |
| **Notes** | Example config structure below |

**Example Configuration:**
```json
{
  "notifications": [
    {
      "type": "telegram",
      "enabled": true,
      "dry_run": false,
      "token": "${TEAMBOT_TELEGRAM_TOKEN}",
      "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
      "events": ["stage_complete", "agent_failed", "pipeline_complete"]
    }
  ]
}
```

### FR-007: Environment Variable Substitution
| Attribute | Value |
|-----------|-------|
| **ID** | FR-007 |
| **Title** | Secret Resolution from Environment |
| **Description** | Config values using `${VAR_NAME}` syntax resolved from environment variables |
| **Goals** | G-RTN-006 (Security) |
| **Personas** | All |
| **Priority** | P0 |
| **Acceptance Criteria** | 1. Syntax `${VAR_NAME}` in any string config value triggers env var lookup<br>2. Missing env var raises clear error at config load time<br>3. Nested/partial substitution supported: `prefix_${VAR}_suffix`<br>4. Only applies to notification credentials (token, chat_id, etc.)<br>5. Resolved values never logged or persisted |
| **Notes** | Use `os.environ.get()` with error handling |

### FR-008: Init Wizard Extension
| Attribute | Value |
|-----------|-------|
| **ID** | FR-008 |
| **Title** | Telegram Setup in teambot init |
| **Description** | Optional interactive step guides user through Telegram bot configuration |
| **Goals** | G-RTN-001 (Real-time), G-RTN-006 (Security) |
| **Personas** | Solo Developer, Remote Worker |
| **Priority** | P0 |
| **Acceptance Criteria** | 1. After standard init, prompt: "Enable real-time notifications? [y/N]"<br>2. If yes, explain: "You'll need a Telegram bot. Visit @BotFather..."<br>3. Prompt for bot token<br>4. Prompt for chat ID<br>5. Write config with `${TEAMBOT_TELEGRAM_TOKEN}` and `${TEAMBOT_TELEGRAM_CHAT_ID}` references<br>6. Output instructions for setting environment variables<br>7. Optionally test connection if env vars already set |
| **Notes** | Keep prompts concise; link to docs for detailed instructions |

### FR-009: Graceful Error Handling
| Attribute | Value |
|-----------|-------|
| **ID** | FR-009 |
| **Title** | Non-Blocking Notification Delivery |
| **Description** | Notification failures logged but never interrupt workflow |
| **Goals** | G-RTN-005 (Reliability) |
| **Personas** | All |
| **Priority** | P0 |
| **Acceptance Criteria** | 1. Network errors caught and logged with context<br>2. Invalid token/credentials logged with helpful message<br>3. Timeout (default 10s) prevents hanging<br>4. Failed notification logged but workflow continues<br>5. No exceptions propagate to ExecutionLoop<br>6. Error count tracked for observability |
| **Notes** | Use try/except around all HTTP calls |

### FR-010: Rate Limit Handling
| Attribute | Value |
|-----------|-------|
| **ID** | FR-010 |
| **Title** | Exponential Backoff for Rate Limits |
| **Description** | HTTP 429 responses trigger retry with exponential backoff |
| **Goals** | G-RTN-005 (Reliability) |
| **Personas** | All |
| **Priority** | P0 |
| **Acceptance Criteria** | 1. HTTP 429 response triggers retry<br>2. Retry delays: 1s, 2s, 4s (exponential backoff)<br>3. Maximum 3 retry attempts<br>4. After 3 failures, log and drop notification<br>5. Retry-After header respected if present<br>6. Other HTTP errors (4xx, 5xx) do not trigger retry |
| **Notes** | Telegram rate limit is generous (~30/sec) so this is defensive |

### FR-011: Dry Run Mode
| Attribute | Value |
|-----------|-------|
| **ID** | FR-011 |
| **Title** | Dry Run Configuration Option |
| **Description** | Channel config `dry_run: true` logs messages without sending |
| **Goals** | G-RTN-002 (Rich context) - aids template testing |
| **Personas** | CI Integrator |
| **Priority** | P0 |
| **Acceptance Criteria** | 1. `dry_run: true` in channel config enables mode<br>2. Formatted message logged with DEBUG level<br>3. No HTTP requests made in dry run mode<br>4. Log entry includes event type and full formatted content<br>5. Useful for testing templates and event filtering |
| **Notes** | Consider INFO level for visibility |

### FR-012: httpx Dependency
| Attribute | Value |
|-----------|-------|
| **ID** | FR-012 |
| **Title** | Add httpx Library |
| **Description** | Add httpx as project dependency for async HTTP |
| **Goals** | G-RTN-001 (Real-time), G-RTN-005 (Reliability) |
| **Personas** | N/A (technical) |
| **Priority** | P0 |
| **Acceptance Criteria** | 1. `httpx` added to `pyproject.toml` dependencies<br>2. Version pinned appropriately (e.g., `>=0.24,<1.0`)<br>3. No stdlib fallback required<br>4. Async client used for non-blocking requests |
| **Notes** | httpx chosen for async support, connection pooling, cleaner API than aiohttp |

### FR-013: Version Bump
| Attribute | Value |
|-----------|-------|
| **ID** | FR-013 |
| **Title** | Semantic Version Increment |
| **Description** | Bump version from 0.1.0 to 0.2.0 |
| **Goals** | N/A (release management) |
| **Personas** | N/A |
| **Priority** | P0 |
| **Acceptance Criteria** | 1. `src/teambot/__init__.py` version updated to `0.2.0`<br>2. Changelog entry added for 0.2.0<br>3. pyproject.toml version updated if specified there |
| **Notes** | Minor version for new functionality per semver |

---

## 7. Non-Functional Requirements

| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|-------------|--------------|----------|------------|-------|
| NFR-001 | Performance | Notification delivery latency | < 5 seconds from event to delivery | P0 | Measure round-trip in tests | Depends on network |
| NFR-002 | Performance | Notification delivery must not block workflow | 0ms added to stage execution time | P0 | Async delivery verified in tests | Use asyncio.create_task |
| NFR-003 | Reliability | Notification failures isolated | 100% workflow completion despite notification failures | P0 | Fault injection tests | Try/except wrapping |
| NFR-004 | Reliability | Rate limit handling | Survive 429 responses without data loss | P1 | Mock 429 responses in tests | Exponential backoff |
| NFR-005 | Security | No plain-text secrets in config | 0 secrets in teambot.json | P0 | Config audit | Env var substitution |
| NFR-006 | Security | No inbound network connections | 0 listening ports | P0 | Network scan | Outbound HTTP only |
| NFR-007 | Maintainability | New channel implementation | < 100 lines of code for new channel | P1 | Code review | Protocol-based design |
| NFR-008 | Observability | Failed notifications logged | 100% of failures logged with context | P0 | Log audit | Include event type, error |
| NFR-009 | Usability | Init wizard completion time | < 3 minutes for Telegram setup | P1 | User testing | Clear instructions |
| NFR-010 | Compatibility | No breaking changes to existing config | Existing teambot.json files work unchanged | P0 | Regression tests | notifications is optional |

---

## 8. Data & Analytics

### Inputs
| Data | Source | Format | Sensitivity |
|------|--------|--------|-------------|
| Workflow events | ExecutionLoop.on_progress | dict (event_type, data) | Low |
| Configuration | teambot.json | JSON | Low (secrets via env vars) |
| Environment variables | OS environment | String | High (contains tokens) |

### Outputs / Events
| Output | Destination | Format | Sensitivity |
|--------|-------------|--------|-------------|
| Notification messages | Telegram API | HTML string | Low (workflow metadata) |
| Debug logs | Console/file | Text | Low |
| Error logs | Console/file | Text with context | Low |

### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|---------|---------|-------|
| notification_sent | Successful delivery | channel_type, event_type, latency_ms | Track delivery success | Notifications module |
| notification_failed | Delivery failure | channel_type, event_type, error_type | Track failures | Notifications module |
| notification_retried | 429 retry | channel_type, attempt_number | Track rate limiting | Notifications module |
| notification_dropped | Max retries exceeded | channel_type, event_type | Track dropped messages | Notifications module |

### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Notification delivery rate | Ratio | N/A | > 99% | Per workflow | Logs |
| Notification latency | P95 | N/A | < 5s | Per workflow | Logs |
| Workflow impact | Delta | N/A | 0ms | Per stage | Timing |
| User adoption | Count | 0 | 10% of users | 30 days | Config presence |

---

## 9. Dependencies

| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|------------|------|-------------|-------|------|------------|
| httpx library | External package | High | PyPI | Package unavailable | Pin version, vendor if needed |
| Telegram Bot API | External service | Medium | Telegram | API changes/downtime | Version-pin behavior, graceful fallback |
| ExecutionLoop.on_progress | Internal code | High | TeamBot | Interface changes | Add EventBus as wrapper |
| Config loader | Internal code | High | TeamBot | Schema changes | Extend, don't replace |
| Environment variables | OS | Low | User | Misconfiguration | Clear error messages |

---

## 10. Risks & Mitigations

| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|----------|------------|------------|-------|--------|
| R-001 | Telegram API changes break channel | Medium | Low | Protocol allows swapping channels; version-pin API behavior | TBD | Open |
| R-002 | Rate limiting blocks notifications | Low | Low | Exponential backoff; events are informational | TBD | Open |
| R-003 | User misconfigures credentials | Low | Medium | Validate on init; clear error messages | TBD | Open |
| R-004 | Network unavailable | Low | Medium | Timeout + retry; never block workflow | TBD | Open |
| R-005 | Notification delivery slows workflow | High | Low | Async delivery with fire-and-forget | TBD | Open |
| R-006 | Secrets accidentally logged | High | Low | Never log resolved env vars; audit log statements | TBD | Open |

---

## 11. Privacy, Security & Compliance

### Data Classification
| Data Type | Classification | Handling |
|-----------|---------------|----------|
| Bot tokens | Secret | Env vars only, never logged |
| Chat IDs | Confidential | Env vars only, never logged |
| Stage names | Internal | Sent to Telegram, may be logged |
| Agent names | Internal | Sent to Telegram, may be logged |
| Artifact paths | Internal | Sent to Telegram (file paths only, not contents) |

### PII Handling
* No PII collected or transmitted
* Workflow metadata (stage names, durations) is non-sensitive
* File paths may reveal project structure (user's choice to enable notifications)

### Threat Considerations
| Threat | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Token exposure in logs | Low | High | Never log resolved env vars |
| Token exposure in config | Low | High | Env var substitution required |
| Unauthorized channel access | Low | Low | Token/chat_id pair provides auth |
| Man-in-the-middle | Very Low | Medium | Telegram API uses HTTPS |

### Regulatory / Compliance
| Regulation | Applicability | Action | Owner | Status |
|------------|--------------|--------|-------|--------|
| GDPR | Not applicable | No PII collected | N/A | N/A |
| SOC 2 | Optional | Secrets management documented | TBD | Open |

---

## 12. Operational Considerations

| Aspect | Requirement | Notes |
|--------|-------------|-------|
| Deployment | Package update via pip/uv | No infrastructure changes |
| Rollback | Disable notifications in config | Remove `notifications` section |
| Monitoring | Log analysis for failures | `notification_failed` events |
| Alerting | N/A (client-side tool) | Users observe own failures |
| Support | Documentation for setup | Troubleshooting guide |
| Capacity Planning | N/A | Outbound HTTP only |

---

## 13. Rollout & Launch Plan

### Phases / Milestones
| Phase | Gate Criteria | Owner |
|-------|---------------|-------|
| Development | All FRs implemented, tests passing | TBD |
| Internal Testing | Successful Telegram notifications on real workflow | TBD |
| Documentation | Setup guide, troubleshooting guide complete | TBD |
| Release | Version 0.2.0 published | TBD |
| Post-Launch | Monitor for issues, gather feedback | TBD |

### Feature Flags
| Flag | Purpose | Default | Sunset Criteria |
|------|---------|---------|-----------------|
| N/A | Notifications are config-driven, not flagged | N/A | N/A |

### Communication Plan
* README update with notifications section
* New guide: `docs/guides/notifications.md`
* Changelog entry for 0.2.0

---

## 14. Acceptance Test Scenarios

### AT-001: Basic Telegram Notification on Stage Complete
**Description**: User receives Telegram notification when workflow stage completes
**Preconditions**: 
- Telegram bot configured in teambot.json with env var references
- Environment variables TEAMBOT_TELEGRAM_TOKEN and TEAMBOT_TELEGRAM_CHAT_ID set
- Valid Telegram bot and chat exist
**Steps**:
1. Run `teambot run objectives/simple-task.md`
2. Workflow reaches BUSINESS_PROBLEM stage and completes
3. Observe Telegram chat
**Expected Result**: Telegram message received with:
- ✅ emoji prefix
- Bold stage name "BUSINESS_PROBLEM"
- Duration (e.g., "12m 34s")
- Agent name (e.g., "ba")
**Verification**: Message appears in Telegram chat within 5 seconds of stage completion

### AT-002: Notification Failure Does Not Block Workflow
**Description**: Workflow continues even when Telegram API is unreachable
**Preconditions**:
- Telegram configured but with invalid token
- Environment variables set (invalid values)
**Steps**:
1. Run `teambot run objectives/simple-task.md`
2. Workflow progresses through multiple stages
3. Each stage attempts notification (fails)
4. Workflow completes
**Expected Result**: 
- Workflow completes successfully (exit code 0)
- Log contains notification failure entries
- No user-visible errors in workflow output
**Verification**: Workflow completes; logs show notification errors

### AT-003: Dry Run Mode Logs Without Sending
**Description**: dry_run mode logs formatted messages without HTTP calls
**Preconditions**:
- Telegram configured with `dry_run: true`
- Verbose logging enabled
**Steps**:
1. Run `teambot run objectives/simple-task.md --verbose`
2. Workflow progresses through stages
3. Observe logs
**Expected Result**:
- Log entries contain "[DRY RUN]" prefix
- Full formatted message content visible
- No HTTP requests made (verifiable via network inspection)
**Verification**: Logs contain formatted messages; no Telegram messages received

### AT-004: Environment Variable Resolution
**Description**: Config loader resolves ${VAR_NAME} syntax from environment
**Preconditions**:
- teambot.json contains `"token": "${MY_TOKEN}"`
- Environment variable MY_TOKEN set to "test_value"
**Steps**:
1. Load configuration via ConfigLoader
2. Access notifications[0].token
**Expected Result**: Value is "test_value", not "${MY_TOKEN}"
**Verification**: Config loader returns resolved value

### AT-005: Missing Environment Variable Error
**Description**: Clear error when required env var not set
**Preconditions**:
- teambot.json contains `"token": "${MISSING_VAR}"`
- Environment variable MISSING_VAR not set
**Steps**:
1. Run `teambot run objectives/simple-task.md`
**Expected Result**:
- Clear error message: "Environment variable MISSING_VAR not set"
- Workflow does not start (or notifications disabled with warning)
**Verification**: Error message references specific variable name

### AT-006: Init Wizard Telegram Setup
**Description**: teambot init offers notification configuration
**Preconditions**: No existing teambot.json
**Steps**:
1. Run `teambot init`
2. Complete standard setup
3. When prompted "Enable real-time notifications?", enter "y"
4. Enter bot token when prompted
5. Enter chat ID when prompted
**Expected Result**:
- teambot.json created with notifications section
- Token value is "${TEAMBOT_TELEGRAM_TOKEN}" (not literal token)
- Console shows instructions for setting env vars
**Verification**: teambot.json contains env var references, not secrets

### AT-007: Multiple Event Types Filtered
**Description**: Channel only receives subscribed event types
**Preconditions**:
- Telegram configured with `events: ["pipeline_complete"]`
- Valid credentials
**Steps**:
1. Run `teambot run objectives/multi-stage-task.md`
2. Workflow progresses through multiple stages
3. Workflow completes
**Expected Result**:
- Only 1 Telegram message received (pipeline_complete)
- No messages for individual stage completions
**Verification**: Single message in Telegram chat

### AT-008: Rate Limit Retry Behavior
**Description**: HTTP 429 triggers exponential backoff retry
**Preconditions**:
- Telegram channel configured
- Test with mock that returns 429 twice, then 200
**Steps**:
1. Emit notification event
2. First attempt receives 429
3. After 1s delay, second attempt receives 429
4. After 2s delay, third attempt receives 200
**Expected Result**:
- Notification eventually delivered
- Total time ~3 seconds for retries
- Log shows retry attempts
**Verification**: Message delivered after retries; logs show backoff

---

## 15. Open Questions

| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|----------|--------|
| Q-001 | Should notifications include hyperlinks to artifacts (if remote)? | TBD | TBD | Deferred to future |
| Q-002 | Should we support notification filtering by stage (not just event type)? | TBD | TBD | Deferred to future |

---

## 16. Test Strategy

### Unit Tests
| Component | Test Focus | Mock Strategy |
|-----------|------------|---------------|
| NotificationChannel protocol | Protocol compliance, type checking | N/A (protocol tests) |
| EventBus | Subscribe/unsubscribe, event routing, error isolation | Mock channels |
| TelegramChannel.format() | Message formatting for each event type | N/A (pure function) |
| TelegramChannel.send() | HTTP call, error handling, retries | Mock httpx.AsyncClient |
| Config loader (notifications) | Schema validation, env var substitution | Mock os.environ |
| Env var resolver | ${VAR} syntax parsing, error cases | Mock os.environ |

### Integration Tests
| Scenario | Components | Mock Strategy |
|----------|------------|---------------|
| EventBus + TelegramChannel | Event flow from emit to format | Mock HTTP only |
| Config loading + channel creation | Full channel initialization | Mock HTTP only |
| ExecutionLoop + EventBus | Events trigger notifications | Mock HTTP only |

### Acceptance Tests
* See Section 14 for 8 acceptance test scenarios

### Test Patterns
* Follow existing `pytest` with `pytest-mock` patterns
* Use `@pytest.fixture` for channel and event bus setup
* Use `pytest.mark.asyncio` for async tests
* Minimum 80% code coverage for new modules

---

## 17. Changelog

| Version | Date | Author | Summary | Type |
|---------|------|--------|---------|------|
| 1.0 | 2026-02-11 | BA Agent | Initial specification | Creation |

---

## 18. References & Provenance

| Ref ID | Type | Source | Summary |
|--------|------|--------|---------|
| REF-001 | Code | src/teambot/orchestration/progress.py | Existing event callback architecture |
| REF-002 | Code | src/teambot/orchestration/execution_loop.py | on_progress integration point |
| REF-003 | Code | src/teambot/config/loader.py | Config loading patterns |
| REF-004 | API | https://core.telegram.org/bots/api#sendmessage | Telegram Bot API reference |
| REF-005 | Problem | .teambot/realtime-notifications/artifacts/problem_statement.md | Business problem definition |

---

## 19. Appendices

### Appendix A: Module Structure

```
src/teambot/notifications/
├── __init__.py           # Public API exports
├── protocol.py           # NotificationChannel protocol
├── event_bus.py          # EventBus implementation
├── channels/
│   ├── __init__.py
│   └── telegram.py       # TelegramChannel implementation
├── templates.py          # Message templates per event type
├── config.py             # Notification config loading, env var resolution
└── types.py              # NotificationEvent dataclass, enums
```

### Appendix B: Event-to-Template Mapping

| Event Type | Emoji | Template Structure |
|------------|-------|-------------------|
| stage_started | 🚀 | `🚀 <b>{stage}</b> started` |
| stage_complete | ✅ | `✅ <b>{stage}</b> complete ({duration})\n{summary}` |
| agent_started | 👤 | `👤 <b>{agent}</b> started on {stage}` |
| agent_complete | ✔️ | `✔️ <b>{agent}</b> finished ({duration})` |
| agent_failed | ❌ | `❌ <b>{agent}</b> failed on {stage}\n{error}` |
| parallel_stage_start | ⚡ | `⚡ Parallel: <b>{stage}</b> started ({agent})` |
| parallel_stage_complete | ⚡✅ | `⚡✅ Parallel: <b>{stage}</b> complete ({duration})` |
| parallel_stage_failed | ⚡❌ | `⚡❌ Parallel: <b>{stage}</b> failed\n{error}` |
| pipeline_complete | 🎉 | `🎉 <b>Pipeline complete!</b>\nTotal time: {duration}\nStages: {count}` |
| pipeline_timeout | ⏰ | `⏰ <b>Pipeline timeout</b> after {duration}` |
| review_iteration | 🔄 | `🔄 <b>{stage}</b> review iteration {n}/{max}` |

### Appendix C: Configuration Schema (JSON Schema)

```json
{
  "type": "object",
  "properties": {
    "notifications": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type"],
        "properties": {
          "type": { "type": "string", "enum": ["telegram"] },
          "enabled": { "type": "boolean", "default": true },
          "dry_run": { "type": "boolean", "default": false },
          "token": { "type": "string" },
          "chat_id": { "type": "string" },
          "events": {
            "type": "array",
            "items": { "type": "string" },
            "default": ["stage_complete", "agent_failed", "pipeline_complete", "pipeline_timeout"]
          }
        }
      }
    }
  }
}
```

### Glossary
| Term | Definition |
|------|------------|
| EventBus | Pub/sub component routing events to notification channels |
| NotificationChannel | Protocol defining interface for notification delivery |
| Bot Token | Secret token from @BotFather for Telegram API auth |
| Chat ID | Telegram chat/group identifier for message destination |
| Dry Run | Mode that logs messages without sending |

---

Generated 2026-02-11 by BA Agent (mode: specification)
<!-- markdown-table-prettify-ignore-end -->
