## Objective

- Improve notification user experience by adding clear run context and a test command.

**Goal**:

- Add header/footer notifications when starting and completing orchestration runs, clearly identifying which objective is being worked on.
- Provide a `/notify <msg>` REPL command that sends a test notification, allowing users to verify their notification configuration before starting a full run.
- Both features should work with the existing notification system and all configured channels.

**Problem Statement**:

- During manual testing with real-time Telegram notifications, it became confusing to understand what notifications were related to — especially when running multiple objectives or returning to check messages later.
- There is no way to verify notification configuration without running a full orchestration workflow. Users must complete an entire run to discover if their Telegram token, chat ID, or other settings are correct.
- The lack of clear start/end markers makes it difficult to distinguish between separate runs in notification history.

**Success Criteria**:
- [ ] When an orchestration run starts, a header notification is sent to all configured channels with the objective name/description (e.g., "🚀 Starting: Realtime Notifications objective").
- [ ] When an orchestration run completes, a footer notification is sent summarizing completion (e.g., "✅ Completed: Realtime Notifications objective").
- [ ] The header/footer messages appear both in the output pane (terminal UI) and via notifications.
- [ ] A `/notify <message>` REPL command is implemented that sends the provided message through all configured notification channels.
- [ ] `/notify` without a message displays usage help.
- [ ] `/notify` provides clear feedback in the REPL indicating success or failure of the notification delivery.
- [ ] If notifications are not configured, `/notify` displays a helpful error message guiding users to run `teambot init` or configure the `notifications` section in `teambot.json`.
- [ ] The `/help` command output is updated to include `/notify`.
- [ ] All new functionality has test coverage following existing test patterns (`pytest` with `pytest-mock`).

---

## Technical Context

**Target Codebase**:

- TeamBot — specifically:
  - `src/teambot/orchestration/execution_loop.py` — for header/footer emission
  - `src/teambot/repl/commands.py` — for `/notify` command handler
  - `src/teambot/repl/router.py` — for command registration
  - `src/teambot/notifications/templates.py` — for new event templates
  - `src/teambot/notifications/events.py` — for new event types

**Primary Language/Framework**:

- Python

**Testing Preference**:

- Follow current pattern (`pytest` with `pytest-mock`)

**Key Constraints**:
- Must integrate with existing `EventBus` and `NotificationChannel` protocol.
- Must not break existing notification functionality.
- `/notify` command must work with all configured channels (Telegram and future channels).
- Header/footer should gracefully handle missing objective information (fall back to generic "orchestration run" text).

---

## Additional Context

### New Event Types

Add three new event types to `events.py`:

- `run_started` — fired when orchestration begins, includes objective name/path
- `run_completed` — fired when orchestration ends, includes objective name/path, overall status, and duration
- `run_failed` — fired when orchestration fails, includes objective name/path, last completed stage, and error details

### New Templates

Add templates in `templates.py`:

```python
"run_started": "🚀 <b>Starting:</b> {objective_name}",
"run_completed": "✅ <b>Completed:</b> {objective_name}\n⏱ Total duration: {duration}",
```

For failed runs:
```python
"run_failed": "❌ <b>Failed:</b> {objective_name}\n📍 Last stage: {last_stage}\n💥 Error: {error}",
```

### `/notify` Command

The command handler should:

1. Parse the message from command arguments
2. Check if notifications are configured (check `EventBus` or config)
3. Create a synthetic `NotificationEvent` with type `test_message`
4. Use `await event_bus.emit(event)` for dispatch (REPL runs in async context via `repl/loop.py`)
5. Report per-channel success/failure back to REPL

Example usage:
```
> /notify Testing notification setup!
✓ Notification sent: Telegram ✓

> /notify Testing with multiple channels
✓ Notification sent: Telegram ✓, Slack ✓

> /notify Testing with partial failure
⚠ Notification sent: Telegram ✓, Slack ✗ (connection timeout)

> /notify
Usage: /notify <message>
Sends a test notification to all configured channels.

> /notify Hello world
✗ No notification channels configured. Run `teambot init` to set up notifications.
```

### Template for Test Messages

```python
"test_message": "📬 <b>Test Notification</b>\n{message}",
```

### Integration Points

- **`ExecutionLoop`** — emit `run_started` event at the beginning of `execute()`, emit `run_completed` at the end
- **`cli.py` or orchestrator** — pass objective path/name to `ExecutionLoop` so it's available for the event
- **REPL commands** — add `handle_notify()` following the pattern of existing handlers like `handle_status()`
- **Command router** — register `/notify` command

### Output Pane Display

In addition to sending notifications, the header/footer should be displayed in the terminal output pane using the existing `console` or `RichDisplay` mechanisms:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Starting: Realtime Notifications objective
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

... workflow execution ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Completed: Realtime Notifications objective (12m 34s)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Duration Formatting

Use or create a `format_duration(seconds: float) -> str` utility that outputs human-readable durations:
- Under 1 minute: `45s`
- Under 1 hour: `12m 34s`
- 1 hour or more: `1h 23m 45s`

This utility should be placed in a shared location (e.g., `src/teambot/utils/formatting.py`) for reuse across templates and UI.

### Test Scenarios

Ensure test coverage for the following edge cases:

1. **Missing objective file** — run header/footer should fall back to "Orchestration run" or display the file path if title extraction fails
2. **Objective with no title** — graceful fallback to filename without extension
3. **Very long messages in `/notify`** — define max length (e.g., 4096 chars for Telegram) and truncate with `...` indicator if exceeded
4. **Multiple channels with mixed results** — verify per-channel success/failure reporting
5. **Notifications disabled** — `/notify` should detect and report appropriately
6. **Empty message after `/notify`** — show usage help

---
