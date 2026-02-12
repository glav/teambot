# Real-Time Notifications

TeamBot can send real-time notifications to external channels when workflow events occur. This allows you to step away from the terminal and receive updates on your phone or team chat.

## Overview

The notification system uses an event-driven architecture that:

- Sends notifications within seconds of workflow events
- Uses outbound HTTP only (no ports exposed, no webhooks required)
- Keeps secrets in environment variables (never in config files)
- Fails gracefully without blocking workflow execution

## Supported Channels

| Channel | Status | Description |
|---------|--------|-------------|
| Telegram | ✅ Available | Bot API with HTML-formatted messages |
| Slack | 🔮 Planned | Via webhooks |
| Microsoft Teams | 🔮 Planned | Via Power Automate |
| GitHub | 🔮 Planned | Via `gh` CLI |

---

## Telegram Setup

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` to create a new bot
3. Follow the prompts to choose a name and username
4. Copy the **bot token** you receive (looks like `123456789:ABCdef...`)

> ⚠️ Keep your bot token secret. Anyone with the token can control your bot.

### Step 2: Get Your Chat ID

To receive notifications, you need the chat ID where messages should be sent.

> **Note:** The `getUpdates` endpoint only returns **new** messages since it was last called. If you get an empty result, it means there are no new messages—not that something is wrong.

1. Open this URL in your browser (replace `<TOKEN>` with your bot token):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
2. Send a message to your bot in Telegram (e.g., type "hello")
3. **Immediately** refresh the browser page with the getUpdates URL
4. Look for `"chat":{"id": <NUMBER>}` in the response
5. Copy the chat ID number (can be negative for group chats)

**Example response:**
```json
{
  "result": [{
    "message": {
      "chat": {
        "id": 123456789,
        "type": "private"
      }
    }
  }]
}
```

**Troubleshooting: Empty result `{"ok":true,"result":[]}`**

If you see an empty `result` array, it means there are no new messages since you last checked. To fix this:

1. Send a **fresh** message to your bot in Telegram
2. **Immediately** refresh the getUpdates URL in your browser
3. The message must be sent **after** you opened or last refreshed the URL

The timing matters because Telegram marks messages as "seen" when you call `getUpdates`.

### Step 3: Set Environment Variables

TeamBot reads credentials from environment variables:

```bash
export TEAMBOT_TELEGRAM_TOKEN='your-bot-token-here'
export TEAMBOT_TELEGRAM_CHAT_ID='your-chat-id-here'
```

Add these to your shell profile (`.bashrc`, `.zshrc`, etc.) for persistence.

### Step 4: Configure TeamBot

#### Option A: Use the Init Wizard

Run `teambot init` and answer "yes" when prompted for notifications:

```
Enable real-time notifications? [y/N]: y

=== Telegram Bot Setup ===
1. Open Telegram and search for @BotFather
2. Send /newbot and follow the prompts
3. Copy the bot token you receive

Ready to enter credentials? [Y/n]: y
Environment variable for bot token [TEAMBOT_TELEGRAM_TOKEN]: 
Environment variable for chat ID [TEAMBOT_TELEGRAM_CHAT_ID]: 

Notification configuration added!

IMPORTANT: Set these environment variables:
  export TEAMBOT_TELEGRAM_TOKEN='your-bot-token'
  export TEAMBOT_TELEGRAM_CHAT_ID='your-chat-id'
```

#### Option B: Manual Configuration

Add to your `teambot.json`:

```json
{
  "notifications": {
    "enabled": true,
    "channels": [
      {
        "type": "telegram",
        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}"
      }
    ]
  }
}
```

The `${VAR_NAME}` syntax references environment variables at runtime.

---

## Configuration Reference

### Full Configuration Schema

```json
{
  "notifications": {
    "enabled": true,
    "channels": [
      {
        "type": "telegram",
        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
        "events": ["stage_changed", "agent_complete", "agent_failed"],
        "dry_run": false
      }
    ]
  }
}
```

### Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `false` | Master switch for all notifications |
| `channels` | array | `[]` | List of channel configurations |

### Channel Fields (Telegram)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Must be `"telegram"` |
| `token` | string | Yes | Bot token (use `${ENV_VAR}` syntax) |
| `chat_id` | string | Yes | Chat ID (use `${ENV_VAR}` syntax) |
| `events` | array | No | Event types to receive (default: all) |
| `dry_run` | boolean | No | Log messages without sending (default: `false`) |

### Custom Environment Variable Names

You can use custom environment variable names:

```json
{
  "notifications": {
    "enabled": true,
    "channels": [
      {
        "type": "telegram",
        "token": "${MY_CUSTOM_TOKEN_VAR}",
        "chat_id": "${MY_CUSTOM_CHAT_VAR}"
      }
    ]
  }
}
```

---

## Event Types

You can filter which events trigger notifications using the `events` array.

| Event Type | Description | When Triggered |
|------------|-------------|----------------|
| `stage_changed` | Workflow entered a new stage | Stage transition |
| `agent_running` | Agent started a task | Task begins |
| `agent_complete` | Agent finished successfully | Task completes |
| `agent_failed` | Agent task failed | Error occurred |
| `parallel_group_start` | Parallel stages began | Parallel execution starts |
| `parallel_group_complete` | Parallel stages finished | All parallel stages done |
| `parallel_stage_complete` | Single parallel stage done | Individual stage completes |
| `parallel_stage_failed` | Single parallel stage failed | Individual stage fails |
| `acceptance_test_stage_complete` | Acceptance tests ran | Tests executed |
| `acceptance_test_max_iterations_reached` | Fix attempts exhausted | Max retries hit |
| `review_progress` | Review cycle update | Review iteration |

### Event Filtering Examples

**Only failures and completions:**
```json
{
  "events": ["agent_complete", "agent_failed", "parallel_group_complete"]
}
```

**Stage changes only:**
```json
{
  "events": ["stage_changed"]
}
```

**All events (default):**
```json
{
  // Omit "events" field to receive all notifications
}
```

---

## Message Format

Telegram notifications use HTML formatting with status emojis:

| Emoji | Meaning |
|-------|---------|
| ✅ | Success/Complete |
| ❌ | Failure/Error |
| ⚠️ | Warning |
| 🔄 | Running/In Progress |
| ℹ️ | Information |
| 📌 | Stage change |
| 🚀 | Parallel group start |

**Example messages:**

```
📌 Stage: IMPLEMENTATION
📂 api-refactor

✅ builder-1 completed

❌ builder-2 FAILED
📂 api-refactor
```

---

## Dry Run Mode

Test your configuration without sending real messages:

```json
{
  "notifications": {
    "enabled": true,
    "channels": [
      {
        "type": "telegram",
        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
        "dry_run": true
      }
    ]
  }
}
```

With `dry_run: true`, formatted messages are logged instead of sent:

```
INFO: [DRY RUN] Telegram notification:
📌 Stage: SPEC
📂 my-feature
```

---

## Troubleshooting

### No Notifications Received

1. **Check environment variables are set:**
   ```bash
   echo $TEAMBOT_TELEGRAM_TOKEN
   echo $TEAMBOT_TELEGRAM_CHAT_ID
   ```

2. **Verify `enabled: true`** in your config

3. **Test your bot manually:**
   ```bash
   curl -X POST "https://api.telegram.org/bot$TEAMBOT_TELEGRAM_TOKEN/sendMessage" \
     -d "chat_id=$TEAMBOT_TELEGRAM_CHAT_ID" \
     -d "text=Test message from TeamBot"
   ```

4. **Check TeamBot logs** for notification errors

### "Telegram credentials not configured"

Environment variables are not set or empty. Ensure:
- Variables are exported in your current shell
- Variable names match your config (default: `TEAMBOT_TELEGRAM_TOKEN`, `TEAMBOT_TELEGRAM_CHAT_ID`)

### "Telegram API error: Forbidden"

The bot cannot send to the specified chat. Common causes:
- Chat ID is wrong
- User hasn't started a conversation with the bot
- Bot was blocked by the user

**Fix:** Send any message to your bot first, then retry.

### "Telegram API error: Bad Request"

Invalid chat ID format. Ensure:
- Chat ID is a number (can be negative for groups)
- No extra spaces or characters

### Rate Limiting (HTTP 429)

TeamBot automatically handles rate limits with exponential backoff. If you see frequent rate limit warnings, consider filtering events to reduce volume.

### Notifications Delayed

Check your network connectivity. TeamBot uses a 30-second HTTP timeout. Slow networks may cause delays but won't block the workflow.

---

## Security Best Practices

1. **Never commit tokens to Git**
   - Use environment variables, not literal values
   - Add `.env` files to `.gitignore`

2. **Use dedicated bots per project**
   - Easier to revoke if compromised
   - Clearer message context

3. **Rotate tokens periodically**
   - Use @BotFather's `/revoke` command
   - Update environment variables

4. **Limit chat access**
   - Use private chats for sensitive projects
   - Create dedicated groups for team notifications

---

## Disabling Notifications

### Temporarily Disable

Set `enabled: false`:

```json
{
  "notifications": {
    "enabled": false,
    "channels": [...]
  }
}
```

### Completely Remove

Delete the `notifications` section from `teambot.json`.

---

## Next Steps

- [Configuration Guide](configuration.md) - Full configuration reference
- [Workflow Stages](workflow-stages.md) - Understanding workflow events
- [CLI Reference](cli-reference.md) - Command options
