## Objective

- Provide real-time notifications to users when TeamBot completes workflow stages, enabling users to stay informed without actively monitoring the terminal.

**Goal**:

- TeamBot should notify users in real-time as workflow stages complete, agent tasks finish, or errors occur — without requiring the user to be sitting in front of the terminal.
- Notifications should be rich-text formatted with stage name, agent, duration, status, summary, and artifacts.
- Telegram should be the first supported notification channel, chosen for its simplicity, zero-infrastructure requirements, and natural path to future two-way communication.
- The notification system should be designed around a pluggable `NotificationChannel` protocol so that additional channels (Teams, GitHub, Slack, etc.) can be added later without modifying core code.
- Notifications should fire per-stage — every workflow stage transition should send a notification to all configured channels.
- The `teambot init` command should offer an optional step to configure real-time notifications, guiding the user through Telegram bot setup (obtaining a bot token and chat ID).
- Notification secrets (bot tokens, chat IDs) must never be stored in configuration files — they must be resolved from environment variables.
- TeamBot must never expose ports or accept inbound connections when running locally. All notification delivery must be outbound-only HTTP requests.

**Problem Statement**:

- TeamBot workflows can run for extended periods across multiple stages (14 stages from SETUP to COMPLETE). Currently, the only way to monitor progress is to watch the terminal UI or run `/status`.
- Users who step away from their machine, work on other tasks, or run TeamBot on a remote/cloud machine have no way to know when stages complete, when errors occur, or when the full pipeline finishes.
- As TeamBot evolves toward supporting multiple team instances running in parallel, the need for out-of-band notifications becomes critical — users cannot watch multiple terminals simultaneously.
- The existing callback system (`ExecutionLoop.on_progress`) provides the right event data internally, but there is no mechanism to route these events to external notification services.

**Success Criteria**:
- [ ] A `NotificationChannel` protocol/interface is defined with `send(event)` and `format(event)` methods, plus an optional `poll()` method stub for future two-way communication.
- [ ] A lightweight `EventBus` is implemented that sits between `ExecutionLoop.on_progress` callbacks and notification channels, supporting subscribe/unsubscribe semantics.
- [ ] A `TelegramChannel` implementation sends rich HTML-formatted notifications via the Telegram Bot API using outbound HTTP only (no polling, no webhooks, no exposed ports).
- [ ] Notifications fire on both stage and agent events, including: `stage_started`, `stage_complete`, `agent_started`, `agent_complete`, `agent_failed`, `parallel_stage_start`, `parallel_stage_complete`, `parallel_stage_failed`, `pipeline_complete`, `pipeline_timeout`, and `review_iteration`. This ensures visibility into long-running stages with multiple agents and review iterations.
- [ ] Notification messages are rich-text formatted with: emoji status indicators, bold stage/agent names, duration, summary text, artifact list (code-formatted file paths), and hyperlinks where applicable.
- [ ] A message template system exists so that each event type has its own formatting template, and templates can be customised per channel.
- [ ] The `teambot.json` configuration schema supports a `notifications` section with an array of channel configurations, each specifying type, credentials (via env var references), and subscribed event types.
- [ ] Environment variable substitution (e.g., `${TEAMBOT_TELEGRAM_TOKEN}`) is supported in the notifications config for all secret values.
- [ ] The `teambot init` command includes a new optional step: "Enable real-time notifications?" — if yes, guides the user through Telegram bot setup (create bot via @BotFather, enter token, enter chat ID), and writes the config with env var references.
- [ ] `teambot init` outputs clear instructions for setting the required environment variables after configuration.
- [ ] The notification system gracefully handles failures (network errors, invalid tokens, rate limits) without interrupting the main workflow — errors are logged but do not block stage execution.
- [ ] Rate limit errors (HTTP 429) trigger exponential backoff retry (up to 3 attempts) before dropping the notification. Failed notifications are logged with details but never fail the overall workflow.
- [ ] A `dry_run` option is supported in channel configuration — when `true`, notifications are logged with full formatted content but not actually sent. Useful for testing templates and event filtering without spamming the channel.
- [ ] The `httpx` library is added as a dependency in `pyproject.toml` — chosen for its async support, cleaner API, and automatic connection pooling. No stdlib fallback is needed.
- [ ] The design explicitly accommodates future additions: a `TeamsChannel` (Adaptive Cards via Power Automate Workflow URLs), a `GitHubChannel` (issue/PR comments via `gh` CLI), and two-way communication via Telegram long-polling — without requiring changes to the core protocol or event bus.
- [ ] All new functionality has test coverage following existing test patterns (`pytest` with `pytest-mock`), including unit tests for the protocol, event bus, Telegram channel, message templates, and config loading.
- [ ] This change bumps the version from `0.1.0` to `0.2.0` (minor version increment per semver).

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically the orchestration layer (`src/teambot/orchestration/execution_loop.py`), CLI init flow (`src/teambot/cli.py`), configuration schema (`src/teambot/config/`), and a new `src/teambot/notifications/` module.

**Primary Language/Framework**:

- Python

**Testing Preference**:

- Follow current pattern (`pytest` with `pytest-mock`)

**Key Constraints**:
- Must not break existing workflow execution, REPL, or UI functionality.
- Must not expose any ports or accept inbound connections when running on a user's local machine.
- All outbound HTTP calls must be non-blocking relative to the main workflow — notification failures must not stall or crash stage execution.
- Secrets must be resolved from environment variables at runtime, never persisted in plain text in `teambot.json` or any other committed file.
- The `NotificationChannel` protocol must be designed for extensibility — adding a new channel should require only implementing the protocol and registering it in configuration, with no changes to core orchestration code.
- Only Telegram is implemented in this phase. Teams, GitHub, and other channels are designed-for but not built.

---

## Additional Context

### Architecture

The notification system introduces four new components in `src/teambot/notifications/`:

1. **`protocol.py`** — `NotificationChannel` Protocol class with:
   - `send(event: NotificationEvent) -> bool` — deliver a formatted notification
   - `format(event: NotificationEvent) -> str` — render event to channel-specific rich text
   - `poll() -> Optional[Command]` — stub for future two-way communication (raises `NotImplementedError` by default)

2. **`event_bus.py`** — Lightweight pub/sub `EventBus` that:
   - Accepts subscriptions from `NotificationChannel` instances with optional event type filters
   - Receives events from `ExecutionLoop.on_progress` callbacks
   - Dispatches to all matching subscribers asynchronously (fire-and-forget with error isolation)

3. **`telegram.py`** — `TelegramChannel` implementing the protocol:
   - Uses `httpx` to POST to `https://api.telegram.org/bot{token}/sendMessage`
   - HTML parse mode for rich text (bold, italic, code, links, blockquotes)
   - Handles rate limiting (Telegram allows ~30 messages/second to a chat) with exponential backoff retry
   - Supports `dry_run` mode for testing without sending

4. **`templates.py`** — Message templates per event type:
   - `stage_started` — emoji + stage name + assigned agent
   - `stage_complete` — emoji + stage + agent + duration + summary + artifacts
   - `agent_started` — emoji + agent name + task context
   - `agent_complete` — emoji + agent + duration + summary
   - `agent_failed` — error details + stage context
   - `parallel_stage_start` — emoji + parallel stage info + agents involved
   - `parallel_stage_complete` — emoji + parallel results summary
   - `parallel_stage_failed` — error details + which agent(s) failed
   - `pipeline_complete` — full run summary with all stages and total duration
   - `pipeline_timeout` — timeout details + last completed stage
   - `review_iteration` — review feedback summary + iteration count

### Configuration Schema

```json
{
  "notifications": {
    "enabled": true,
    "channels": [
      {
        "type": "telegram",
        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
        "events": ["stage_complete", "agent_complete", "agent_failed", "parallel_stage_complete", "pipeline_complete", "pipeline_timeout"],
        "dry_run": false
      }
    ]
  }
}
```

- `events` is optional — if omitted, all events are sent to that channel.
- `dry_run` is optional (default `false`) — when `true`, notifications are logged but not sent.
- `${VAR_NAME}` syntax triggers environment variable resolution at runtime.

### Integration Points

- **`ExecutionLoop.on_progress`** — existing callback that fires `stage_changed`, `agent_complete`, `agent_failed`, etc. The event bus subscribes here.
- **`teambot.json` schema** — extended with the `notifications` section. Config loader validates channel types and required fields.
- **`cli.py` init command** — extended with an optional notification setup wizard.

### Future Two-Way Path (Designed-for, Not Built)

The `poll()` method on `NotificationChannel` and the `CommandGateway` concept are placeholders for Phase 2 where:
- `TelegramChannel.poll()` calls `getUpdates` (long-polling, outbound-only, no ports)
- A `CommandGateway` feeds polled messages into the existing `AgentRouter`
- This enables remote interaction (sending commands via Telegram) without any infrastructure changes

### Telegram Setup Flow (for `teambot init`)

1. Ask: "Enable real-time notifications? [y/N]"
2. If yes, display instructions: "Create a Telegram bot via @BotFather and paste the bot token"
3. Prompt for bot token (validate format: numeric ID + colon + alphanumeric hash)
4. Chat ID discovery — offer two options:
   - **Auto-detect**: Prompt user to send any message to their bot, then call `getUpdates` API to retrieve the chat ID automatically
   - **Manual entry**: Allow user to paste a known chat ID directly (useful for groups or channels)
5. Write config with `${TEAMBOT_TELEGRAM_TOKEN}` and `${TEAMBOT_TELEGRAM_CHAT_ID}` references
6. Output: "Set these environment variables: export TEAMBOT_TELEGRAM_TOKEN=... export TEAMBOT_TELEGRAM_CHAT_ID=..."
7. Optionally send a test notification to confirm the setup works

---
