<!-- markdownlint-disable-file -->

# Implementation Details: Real-Time Notification System

## Research Reference

- **Source**: [.agent-tracking/research/20260211-realtime-notifications-research.md](../research/20260211-realtime-notifications-research.md)
- **Test Strategy**: [.agent-tracking/test-strategies/20260211-realtime-notifications-test-strategy.md](../test-strategies/20260211-realtime-notifications-test-strategy.md)

---

## Task 1.1: Create Module Structure

### File Operations
- **Create**: `src/teambot/notifications/__init__.py`
- **Create**: `src/teambot/notifications/protocol.py`
- **Create**: `src/teambot/notifications/events.py`
- **Create**: `src/teambot/notifications/event_bus.py`
- **Create**: `src/teambot/notifications/templates.py`
- **Create**: `src/teambot/notifications/config.py`
- **Create**: `src/teambot/notifications/channels/__init__.py`
- **Create**: `src/teambot/notifications/channels/telegram.py`

### Specification

Create the module structure:

```
src/teambot/notifications/
├── __init__.py          # Public exports
├── protocol.py          # NotificationChannel Protocol
├── events.py            # NotificationEvent dataclass
├── event_bus.py         # EventBus implementation
├── templates.py         # MessageTemplates
├── config.py            # Config loading, env var resolution
└── channels/
    ├── __init__.py      # Channel exports
    └── telegram.py      # TelegramChannel implementation
```

### Success Criteria
- All directories and files created
- Empty files with docstrings only (implementation in later tasks)

### Dependencies
- None

---

## Task 1.2: Implement NotificationEvent Dataclass

### File Operations
- **Modify**: `src/teambot/notifications/events.py`

### Specification

```python
# src/teambot/notifications/events.py
"""Notification event data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class NotificationEvent:
    """Event data for notifications.
    
    Attributes:
        event_type: Type of event (e.g., "stage_changed", "agent_failed")
        data: Event-specific data dictionary
        timestamp: When the event occurred
        stage: Current workflow stage (optional)
        agent: Agent ID if applicable (optional)
        feature_name: Feature/objective name for context (optional)
    """
    
    event_type: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    stage: str | None = None
    agent: str | None = None
    feature_name: str | None = None
```

### Test Requirements (TDD)
Create `tests/test_notifications/test_events.py`:
- Test event creation with required fields
- Test event creation with all optional fields
- Test default timestamp generation
- Test empty data dict handling

### Success Criteria
- NotificationEvent creates with required fields
- Optional fields default correctly
- Timestamp auto-generated when not provided

### Dependencies
- Task 1.1 (module structure)

---

## Task 1.3: Implement NotificationChannel Protocol

### File Operations
- **Modify**: `src/teambot/notifications/protocol.py`

### Specification

```python
# src/teambot/notifications/protocol.py
"""Notification channel protocol definition."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from teambot.notifications.events import NotificationEvent


@runtime_checkable
class NotificationChannel(Protocol):
    """Protocol for notification channels (Telegram, Teams, GitHub, etc.).
    
    Implementers must provide:
    - name: Channel identifier
    - enabled: Whether channel is active
    - send(): Async method to deliver notification
    - format(): Convert event to channel-specific format
    - supports_event(): Check if channel handles this event type
    - poll(): Optional method for future two-way communication
    """

    @property
    def name(self) -> str:
        """Unique channel identifier (e.g., 'telegram', 'teams')."""
        ...

    @property
    def enabled(self) -> bool:
        """Whether channel is currently enabled and configured."""
        ...

    async def send(self, event: NotificationEvent) -> bool:
        """Send notification for event.
        
        Args:
            event: The notification event to send
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        ...

    def format(self, event: NotificationEvent) -> str:
        """Format event into channel-specific message format.
        
        Args:
            event: The notification event to format
            
        Returns:
            Formatted message string (HTML for Telegram, Markdown for others)
        """
        ...

    def supports_event(self, event_type: str) -> bool:
        """Check if channel subscribes to this event type.
        
        Args:
            event_type: Event type identifier
            
        Returns:
            True if channel should receive this event type
        """
        ...

    async def poll(self) -> list[dict[str, Any]] | None:
        """Poll for incoming messages (future two-way support).
        
        Returns:
            List of incoming messages, or None if polling not supported
        """
        ...
```

### Test Requirements (TDD)
Create `tests/test_notifications/test_protocol.py`:
- Test mock class satisfies Protocol
- Test `@runtime_checkable` works with isinstance()
- Test partial implementation fails isinstance check

### Success Criteria
- Protocol defines all required methods
- `@runtime_checkable` decorator applied
- Mock implementation can satisfy protocol

### Dependencies
- Task 1.2 (NotificationEvent)

---

## Task 1.4: Implement EventBus

### File Operations
- **Modify**: `src/teambot/notifications/event_bus.py`

### Specification

```python
# src/teambot/notifications/event_bus.py
"""Event bus for notification dispatching."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from teambot.notifications.events import NotificationEvent

if TYPE_CHECKING:
    from teambot.notifications.protocol import NotificationChannel

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when a channel encounters rate limiting."""
    
    def __init__(self, retry_after: float = 1.0):
        self.retry_after = retry_after
        super().__init__(f"Rate limited, retry after {retry_after}s")


class EventBus:
    """Pub/sub event bus for notification channels.
    
    Sits between ExecutionLoop.on_progress callbacks and notification channels.
    All sends are fire-and-forget to never block the workflow.
    """
    
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0

    def __init__(self, feature_name: str | None = None):
        """Initialize event bus.
        
        Args:
            feature_name: Current feature/objective name for context
        """
        self._channels: list[NotificationChannel] = []
        self._feature_name = feature_name
        self._current_stage: str | None = None

    def subscribe(self, channel: NotificationChannel) -> None:
        """Subscribe a channel to receive events.
        
        Args:
            channel: NotificationChannel implementation
        """
        if channel not in self._channels:
            self._channels.append(channel)
            logger.debug(f"Subscribed channel: {channel.name}")

    def unsubscribe(self, channel_name: str) -> None:
        """Remove a channel subscription by name.
        
        Args:
            channel_name: Name of channel to remove
        """
        self._channels = [c for c in self._channels if c.name != channel_name]
        logger.debug(f"Unsubscribed channel: {channel_name}")

    def set_stage(self, stage_name: str) -> None:
        """Update current stage context."""
        self._current_stage = stage_name

    async def emit(self, event: NotificationEvent) -> None:
        """Emit an event to all subscribed channels.
        
        This method is fire-and-forget - channel failures do not propagate.
        Events are dispatched concurrently to all matching channels.
        
        Args:
            event: The notification event to emit
        """
        if not self._channels:
            return

        # Update context from event
        if event.event_type == "stage_changed":
            self._current_stage = event.data.get("stage")

        # Add context to event
        if event.feature_name is None:
            event.feature_name = self._feature_name
        if event.stage is None:
            event.stage = self._current_stage

        # Dispatch to all matching channels concurrently
        for channel in self._channels:
            if channel.enabled and channel.supports_event(event.event_type):
                # Fire and forget - don't await
                asyncio.create_task(self._safe_send(channel, event))

    async def _safe_send(self, channel: NotificationChannel, event: NotificationEvent) -> None:
        """Send notification with retry and error handling.
        
        Errors are logged but never propagated to avoid blocking workflow.
        """
        backoff = self.INITIAL_BACKOFF
        
        for attempt in range(self.MAX_RETRIES):
            try:
                await channel.send(event)
                return  # Success
            except RateLimitError as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = e.retry_after or backoff
                    logger.warning(
                        f"Channel {channel.name} rate limited, "
                        f"retry {attempt + 1}/{self.MAX_RETRIES} in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                    backoff *= 2
                else:
                    logger.error(
                        f"Channel {channel.name} max retries exceeded for {event.event_type}"
                    )
            except Exception as e:
                logger.error(f"Channel {channel.name} send failed: {e}")
                return  # Don't retry on non-rate-limit errors

    def create_progress_callback(self):
        """Create an on_progress callback that emits to this bus.
        
        Returns:
            Callback function compatible with ExecutionLoop.run(on_progress=...)
        """
        def on_progress(event_type: str, data: dict[str, Any]) -> None:
            event = NotificationEvent(event_type=event_type, data=data)
            asyncio.create_task(self.emit(event))
        
        return on_progress
```

### Success Criteria
- `subscribe()` adds channels to internal list
- `unsubscribe()` removes channels by name
- `emit()` dispatches to all matching enabled channels
- `emit()` is non-blocking (fire-and-forget)
- Retry logic with exponential backoff works
- `RateLimitError` triggers retry
- Max retries exceeded logs error, doesn't raise

### Dependencies
- Task 1.2 (NotificationEvent)
- Task 1.3 (NotificationChannel Protocol)

---

## Task 1.5: Write EventBus Tests

### File Operations
- **Create**: `tests/test_notifications/__init__.py`
- **Create**: `tests/test_notifications/conftest.py`
- **Create**: `tests/test_notifications/test_event_bus.py`

### Specification

Create comprehensive tests for EventBus following existing patterns from `tests/test_orchestration/test_progress.py`.

Key test cases:
1. `test_subscribe_adds_channel` - Channel added to list
2. `test_unsubscribe_removes_channel` - Channel removed by name
3. `test_emit_calls_channel_send` - Enabled channels receive events
4. `test_emit_skips_disabled_channel` - Disabled channels skipped
5. `test_emit_skips_unsupported_event` - Channel filters by event type
6. `test_emit_is_nonblocking` - Emit returns immediately
7. `test_retry_on_rate_limit` - RateLimitError triggers retry
8. `test_max_retries_exceeded` - Logs error after 3 attempts
9. `test_channel_exception_logged` - Other exceptions logged, not raised

### Test Pattern Reference
See `tests/test_orchestration/test_progress.py` lines 14-50 for event handling test patterns.

### Success Criteria
- All 9 test cases implemented
- Tests pass with `uv run pytest tests/test_notifications/test_event_bus.py -v`
- 95% coverage of EventBus class

### Dependencies
- Task 1.4 (EventBus implementation)

---

## Task 2.1: Add httpx Dependency

### File Operations
- **Modify**: `pyproject.toml`

### Specification

Add httpx to dependencies:

```toml
# pyproject.toml line ~12
dependencies = [
  "python-dotenv>=1.0.0",
  "python-frontmatter>=1.0.0",
  "rich>=13.0.0",
  "github-copilot-sdk==0.1.23",
  "textual>=0.47.0",
  "httpx>=0.27.0",
]
```

### Commands
```bash
uv lock
uv sync
uv run python -c "import httpx; print(httpx.__version__)"
```

### Success Criteria
- `httpx>=0.27.0` in pyproject.toml
- `uv lock` succeeds
- `uv sync` succeeds
- httpx imports correctly

### Dependencies
- Task 1.5 (Phase 1 complete)

---

## Task 2.2: Implement MessageTemplates

### File Operations
- **Modify**: `src/teambot/notifications/templates.py`

### Specification

```python
# src/teambot/notifications/templates.py
"""Message templates for notification channels."""

from __future__ import annotations

from typing import Any

from teambot.notifications.events import NotificationEvent


# Status emojis
STATUS_EMOJI = {
    "success": "✅",
    "failure": "❌",
    "warning": "⚠️",
    "running": "🔄",
    "info": "ℹ️",
}


class MessageTemplates:
    """Template renderer for notification messages."""
    
    # Templates use HTML format for Telegram compatibility
    TEMPLATES: dict[str, str] = {
        "stage_changed": (
            "📌 <b>Stage: {stage}</b>\n"
            "📂 <code>{feature_name}</code>"
        ),
        "agent_running": (
            "🔄 <b>{agent_id}</b> started\n"
            "📋 Task: <i>{task}</i>"
        ),
        "agent_complete": (
            "✅ <b>{agent_id}</b> completed"
        ),
        "agent_failed": (
            "❌ <b>{agent_id}</b> FAILED\n"
            "📂 <code>{feature_name}</code>"
        ),
        "parallel_group_start": (
            "🚀 <b>Parallel Group: {group}</b>\n"
            "📊 Stages: {stages}"
        ),
        "parallel_group_complete": (
            "{emoji} <b>Parallel Group: {group}</b>\n"
            "Status: {status}"
        ),
        "parallel_stage_complete": (
            "✅ <b>{stage}</b> completed (agent: {agent})"
        ),
        "parallel_stage_failed": (
            "❌ <b>{stage}</b> FAILED (agent: {agent})"
        ),
        "acceptance_test_stage_complete": (
            "{emoji} <b>Acceptance Tests</b>\n"
            "📊 Results: {passed}/{total} passed\n"
            "📂 <code>{feature_name}</code>"
        ),
        "acceptance_test_max_iterations_reached": (
            "⚠️ <b>Max Fix Iterations Reached</b>\n"
            "Acceptance tests still failing after {iterations_used} attempts."
        ),
        "review_progress": (
            "📝 <b>Review Progress</b>\n"
            "Stage: {stage}\n"
            "{message}"
        ),
    }

    def render(self, event: NotificationEvent) -> str:
        """Render event using appropriate template.
        
        Args:
            event: The notification event to render
            
        Returns:
            Formatted message string
        """
        template = self.TEMPLATES.get(event.event_type, self._default_template())
        
        # Build context from event
        context: dict[str, Any] = {**event.data}
        context["event_type"] = event.event_type
        context["feature_name"] = event.feature_name or "Unknown"
        context["stage"] = event.stage or event.data.get("stage", "Unknown")
        
        # Add computed emoji fields
        if event.event_type == "parallel_group_complete":
            all_success = event.data.get("all_success", False)
            context["emoji"] = STATUS_EMOJI["success"] if all_success else STATUS_EMOJI["warning"]
            context["status"] = "All passed" if all_success else "Some failed"
        elif event.event_type == "acceptance_test_stage_complete":
            failed = event.data.get("failed", 0)
            context["emoji"] = STATUS_EMOJI["success"] if failed == 0 else STATUS_EMOJI["failure"]
        
        # Format stages list if present
        if "stages" in context and isinstance(context["stages"], list):
            context["stages"] = ", ".join(context["stages"])
        
        # Safe format - use fallback for missing keys
        try:
            return template.format(**context).strip()
        except KeyError as e:
            return f"📢 Event: {event.event_type}\n(Missing: {e})"

    def _default_template(self) -> str:
        """Get fallback template for unknown events."""
        return "📢 <b>{event_type}</b>\n📂 <code>{feature_name}</code>"
```

### Test Requirements (TDD)
- Test render for each event type
- Test emoji substitution based on success/failure
- Test fallback for unknown event type
- Test handling of missing keys

### Success Criteria
- All event types have templates
- Emoji logic correct for success/failure states
- Fallback works for unknown events
- Missing keys handled gracefully

### Dependencies
- Task 2.1 (httpx installed)

---

## Task 2.3: Implement TelegramChannel

### File Operations
- **Modify**: `src/teambot/notifications/channels/telegram.py`

### Specification

```python
# src/teambot/notifications/channels/telegram.py
"""Telegram notification channel implementation."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from teambot.notifications.events import NotificationEvent
from teambot.notifications.event_bus import RateLimitError
from teambot.notifications.templates import MessageTemplates

logger = logging.getLogger(__name__)


class TelegramChannel:
    """Telegram Bot API notification channel.
    
    Sends notifications via outbound HTTP POST to Telegram's sendMessage API.
    Never exposes ports or accepts inbound connections.
    """
    
    API_BASE = "https://api.telegram.org/bot{token}/sendMessage"
    MAX_MESSAGE_LENGTH = 4096  # Telegram limit

    def __init__(
        self,
        token_env_var: str = "TEAMBOT_TELEGRAM_TOKEN",
        chat_id_env_var: str = "TEAMBOT_TELEGRAM_CHAT_ID",
        subscribed_events: set[str] | None = None,
        dry_run: bool = False,
    ):
        """Initialize Telegram channel.
        
        Args:
            token_env_var: Environment variable name for bot token
            chat_id_env_var: Environment variable name for chat ID
            subscribed_events: Event types to handle (None = all)
            dry_run: If True, log messages instead of sending
        """
        self._token_env_var = token_env_var
        self._chat_id_env_var = chat_id_env_var
        self._subscribed_events = subscribed_events
        self._dry_run = dry_run
        self._templates = MessageTemplates()
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "telegram"

    @property
    def enabled(self) -> bool:
        """Check if required environment variables are set."""
        return bool(self._get_token() and self._get_chat_id())

    def _get_token(self) -> str | None:
        return os.environ.get(self._token_env_var)

    def _get_chat_id(self) -> str | None:
        return os.environ.get(self._chat_id_env_var)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    def supports_event(self, event_type: str) -> bool:
        """Check if this channel handles the event type."""
        if self._subscribed_events is None:
            return True
        return event_type in self._subscribed_events

    def format(self, event: NotificationEvent) -> str:
        """Format event as HTML message for Telegram."""
        message = self._templates.render(event)
        # Truncate if too long
        if len(message) > self.MAX_MESSAGE_LENGTH:
            message = message[:self.MAX_MESSAGE_LENGTH - 20] + "\n... (truncated)"
        return message

    async def send(self, event: NotificationEvent) -> bool:
        """Send notification via Telegram Bot API.
        
        Raises:
            RateLimitError: On HTTP 429 with retry_after
        """
        message = self.format(event)
        
        if self._dry_run:
            logger.info(f"[DRY RUN] Telegram notification:\n{message}")
            return True
        
        token = self._get_token()
        chat_id = self._get_chat_id()
        
        if not token or not chat_id:
            logger.warning("Telegram credentials not configured")
            return False
        
        url = self.API_BASE.format(token=token)
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        
        try:
            client = await self._get_client()
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                logger.debug(f"Telegram notification sent: {event.event_type}")
                return True
            elif response.status_code == 429:
                # Rate limited
                retry_after = response.json().get("parameters", {}).get("retry_after", 1.0)
                raise RateLimitError(retry_after=retry_after)
            else:
                error = response.json().get("description", response.text)
                logger.error(f"Telegram API error: {error}")
                return False
                
        except httpx.TimeoutException:
            logger.error("Telegram request timed out")
            return False
        except httpx.RequestError as e:
            logger.error(f"Telegram request error: {e}")
            return False

    async def poll(self) -> list[dict[str, Any]] | None:
        """Polling not implemented - returns None."""
        return None

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
```

### Success Criteria
- Implements NotificationChannel protocol
- send() uses httpx for HTTP POST
- Rate limit (429) raises RateLimitError
- dry_run mode logs without HTTP call
- Missing credentials returns False gracefully
- Timeout/connection errors logged, not raised

### Dependencies
- Task 2.1 (httpx installed)
- Task 2.2 (MessageTemplates)

---

## Task 2.4: Write TelegramChannel Tests

### File Operations
- **Create**: `tests/test_notifications/test_telegram.py`

### Specification

Test cases with mocked httpx:
1. `test_send_success` - 200 response returns True
2. `test_send_dry_run` - Logs message, no HTTP call
3. `test_send_missing_credentials` - Returns False
4. `test_send_rate_limit` - 429 raises RateLimitError
5. `test_send_api_error` - 4xx/5xx logs error, returns False
6. `test_send_timeout` - Timeout logged, returns False
7. `test_format_uses_templates` - format() uses MessageTemplates
8. `test_supports_event_all` - None subscribes to all
9. `test_supports_event_filtered` - Set filters events
10. `test_message_truncation` - Long messages truncated

### Success Criteria
- All 10 test cases pass
- 90% coverage of TelegramChannel

### Dependencies
- Task 2.3 (TelegramChannel implementation)

---

## Task 3.1: Implement Env Var Resolver

### File Operations
- **Modify**: `src/teambot/notifications/config.py`

### Specification

```python
# src/teambot/notifications/config.py
"""Notification configuration loading and env var resolution."""

from __future__ import annotations

import os
import re
from typing import Any

from teambot.notifications.event_bus import EventBus
from teambot.notifications.channels.telegram import TelegramChannel


ENV_VAR_PATTERN = re.compile(r'\$\{([A-Z_][A-Z0-9_]*)\}')


def resolve_env_vars(value: str) -> str:
    """Resolve ${VAR} patterns in string values.
    
    Args:
        value: String potentially containing ${VAR} patterns
        
    Returns:
        String with env vars resolved (empty string if var not set)
    """
    if not isinstance(value, str):
        return value
    
    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, "")
    
    return ENV_VAR_PATTERN.sub(replacer, value)


def resolve_config_secrets(config: Any) -> Any:
    """Recursively resolve env vars in config dict/list.
    
    Args:
        config: Config dict, list, or value
        
    Returns:
        Config with all ${VAR} patterns resolved
    """
    if isinstance(config, dict):
        return {k: resolve_config_secrets(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [resolve_config_secrets(v) for v in config]
    elif isinstance(config, str):
        return resolve_env_vars(config)
    return config
```

### Test Requirements (TDD)
- Test single env var resolution
- Test multiple env vars in one string
- Test missing env var resolves to empty
- Test nested dict resolution
- Test list resolution
- Test non-string passthrough

### Success Criteria
- `${VAR}` patterns resolved from os.environ
- Missing vars resolve to empty string
- Nested structures handled recursively

### Dependencies
- Task 2.4 (Phase 2 complete)

---

## Task 3.2: Add Notification Config Validation

### File Operations
- **Modify**: `src/teambot/config/loader.py`

### Specification

Add to ConfigLoader:

```python
# Add constant at top
NOTIFICATION_CHANNEL_TYPES = {"telegram"}

# Add to _validate() method (after overlay validation, ~line 147)
if "notifications" in config:
    self._validate_notifications(config["notifications"])

# Add new method
def _validate_notifications(self, notifications: dict[str, Any]) -> None:
    """Validate notifications configuration."""
    if not isinstance(notifications, dict):
        raise ConfigError("'notifications' must be an object")
    
    if "enabled" in notifications:
        if not isinstance(notifications["enabled"], bool):
            raise ConfigError("'notifications.enabled' must be a boolean")
    
    if "channels" in notifications:
        if not isinstance(notifications["channels"], list):
            raise ConfigError("'notifications.channels' must be a list")
        
        for i, channel in enumerate(notifications["channels"]):
            self._validate_notification_channel(channel, i)

def _validate_notification_channel(self, channel: dict[str, Any], index: int) -> None:
    """Validate a single notification channel config."""
    if not isinstance(channel, dict):
        raise ConfigError(f"Notification channel {index} must be an object")
    
    if "type" not in channel:
        raise ConfigError(f"Notification channel {index} must have 'type' field")
    
    channel_type = channel["type"]
    if channel_type not in NOTIFICATION_CHANNEL_TYPES:
        raise ConfigError(
            f"Invalid notification channel type '{channel_type}'. "
            f"Valid types: {NOTIFICATION_CHANNEL_TYPES}"
        )
    
    # Type-specific validation
    if channel_type == "telegram":
        if "token" not in channel:
            raise ConfigError(f"Telegram channel {index} must have 'token' field")
        if "chat_id" not in channel:
            raise ConfigError(f"Telegram channel {index} must have 'chat_id' field")
    
    if "dry_run" in channel:
        if not isinstance(channel["dry_run"], bool):
            raise ConfigError(f"Channel {index} 'dry_run' must be a boolean")
    
    if "events" in channel:
        if not isinstance(channel["events"], list):
            raise ConfigError(f"Channel {index} 'events' must be a list")

# Add to _apply_defaults() method
if "notifications" not in config:
    config["notifications"] = {"enabled": False, "channels": []}
```

### Success Criteria
- `notifications` section validated
- Channel type checked against NOTIFICATION_CHANNEL_TYPES
- Required fields (type, token, chat_id for telegram) validated
- dry_run must be boolean
- events must be list

### Dependencies
- Task 3.1 (env var resolver)

---

## Task 3.3: Write Config Validation Tests

### File Operations
- **Modify**: `tests/test_config/test_loader.py`

### Specification

Add new test class:

```python
class TestNotificationConfig:
    """Tests for notification configuration validation."""

    def test_valid_notifications_config(self, tmp_path):
        """Valid notifications config loads successfully."""
        ...

    def test_notifications_enabled_must_be_bool(self, tmp_path):
        """notifications.enabled must be boolean."""
        ...

    def test_channel_missing_type_raises(self, tmp_path):
        """Channel without type raises ConfigError."""
        ...

    def test_channel_invalid_type_raises(self, tmp_path):
        """Invalid channel type raises ConfigError."""
        ...

    def test_telegram_missing_token_raises(self, tmp_path):
        """Telegram channel without token raises ConfigError."""
        ...

    def test_telegram_missing_chat_id_raises(self, tmp_path):
        """Telegram channel without chat_id raises ConfigError."""
        ...

    def test_channel_dry_run_must_be_bool(self, tmp_path):
        """Channel dry_run must be boolean."""
        ...

    def test_channel_events_must_be_list(self, tmp_path):
        """Channel events must be list."""
        ...

    def test_notifications_defaults_applied(self, tmp_path):
        """Missing notifications gets default."""
        ...
```

### Success Criteria
- All 9 test cases pass
- 95% coverage of notification validation code

### Dependencies
- Task 3.2 (config validation)

---

## Task 4.1: Create EventBus Factory

### File Operations
- **Modify**: `src/teambot/notifications/config.py`

### Specification

Add factory function:

```python
def create_event_bus_from_config(
    config: dict[str, Any],
    feature_name: str | None = None,
) -> EventBus | None:
    """Create EventBus with channels from config.
    
    Args:
        config: Loaded teambot config dict
        feature_name: Feature name for context
        
    Returns:
        Configured EventBus, or None if notifications disabled
    """
    notifications = config.get("notifications", {})
    
    if not notifications.get("enabled", False):
        return None
    
    bus = EventBus(feature_name=feature_name)
    
    for channel_config in notifications.get("channels", []):
        channel = _create_channel(channel_config)
        if channel:
            bus.subscribe(channel)
    
    return bus


def _create_channel(channel_config: dict[str, Any]):
    """Create channel instance from config."""
    channel_type = channel_config.get("type")
    
    if channel_type == "telegram":
        # Resolve env var references
        resolved = resolve_config_secrets(channel_config)
        subscribed = set(resolved.get("events", []))
        return TelegramChannel(
            subscribed_events=subscribed if subscribed else None,
            dry_run=resolved.get("dry_run", False),
        )
    
    return None
```

### Success Criteria
- Returns None if notifications disabled
- Creates TelegramChannel from config
- Applies event filtering
- Applies dry_run setting

### Dependencies
- Task 3.3 (config validation complete)

---

## Task 4.2: Integrate EventBus with on_progress

### File Operations
- **Modify**: `src/teambot/cli.py`

### Specification

Modify `_run_orchestration()` and `_run_orchestration_resume()`:

```python
# Add import at top of cli.py
from teambot.notifications.config import create_event_bus_from_config

# In _run_orchestration() after loop creation (~line 226):
# Create notification bus if configured
event_bus = create_event_bus_from_config(config, feature_name=loop.feature_name)

# Modify on_progress callback to also emit to event bus
def on_progress(event_type: str, data: dict) -> None:
    # Existing console updates...
    if event_type == "stage_changed":
        display.print_success(f"Stage: {data.get('stage', 'unknown')}")
    # ... rest of existing handlers ...
    
    # Emit to notification bus (non-blocking)
    if event_bus:
        from teambot.notifications.events import NotificationEvent
        event = NotificationEvent(event_type=event_type, data=data)
        asyncio.create_task(event_bus.emit(event))

# Same pattern in _run_orchestration_resume()
```

### Success Criteria
- EventBus created from config if notifications enabled
- on_progress emits to EventBus
- Emission is non-blocking (asyncio.create_task)
- Existing console output unchanged

### Dependencies
- Task 4.1 (EventBus factory)

---

## Task 4.3: Add Notification Setup to cmd_init()

### File Operations
- **Modify**: `src/teambot/cli.py`

### Specification

Add after existing init logic:

```python
def _should_setup_notifications(display: ConsoleDisplay) -> bool:
    """Ask user if they want to setup notifications."""
    display.console.print("\n[bold]📬 Real-Time Notifications[/bold]")
    display.console.print(
        "Would you like to receive Telegram notifications when stages complete?"
    )
    response = display.console.input("[y/N]: ").strip().lower()
    return response in ("y", "yes")


def _setup_telegram_notifications(display: ConsoleDisplay) -> dict | None:
    """Interactive Telegram setup wizard."""
    display.console.print(
        "\n[bold]Step 1: Create a Telegram Bot[/bold]\n"
        "  1. Open Telegram and search for @BotFather\n"
        "  2. Send /newbot and follow prompts\n"
        "  3. Copy the bot token\n"
    )
    
    ready = display.console.input("Ready? [y/N]: ").strip().lower()
    if ready not in ("y", "yes"):
        return None
    
    display.console.print(
        "\n[bold]Step 2: Get Your Chat ID[/bold]\n"
        "  1. Start a chat with your bot\n"
        "  2. Send any message\n"
        "  3. Visit: https://api.telegram.org/bot<TOKEN>/getUpdates\n"
        "  4. Find 'chat':{'id': XXXXXX}\n"
    )
    
    ready = display.console.input("Ready? [y/N]: ").strip().lower()
    if ready not in ("y", "yes"):
        return None
    
    config = {
        "enabled": True,
        "channels": [
            {
                "type": "telegram",
                "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                "events": [
                    "stage_changed",
                    "agent_failed",
                    "parallel_group_complete",
                    "acceptance_test_stage_complete",
                ],
            }
        ],
    }
    
    display.print_success("✅ Notification config created!")
    display.console.print(
        "\n[bold yellow]Set these environment variables:[/bold yellow]\n\n"
        "  export TEAMBOT_TELEGRAM_TOKEN='your-token-here'\n"
        "  export TEAMBOT_TELEGRAM_CHAT_ID='your-chat-id'\n"
    )
    
    return config


# Update cmd_init() to call notification setup:
def cmd_init(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    # ... existing code ...
    
    # After saving default config:
    if _should_setup_notifications(display):
        notif_config = _setup_telegram_notifications(display)
        if notif_config:
            config["notifications"] = notif_config
            loader.save(config, config_path)
    
    # ... rest of existing code ...
```

### Success Criteria
- User can skip notification setup
- Wizard guides through Telegram bot creation
- Config saved with env var references
- Clear instructions for setting env vars

### Dependencies
- Task 4.2 (integration complete)

---

## Task 5.1: Bump Version to 0.2.0

### File Operations
- **Modify**: `src/teambot/__init__.py`

### Specification

Change version:

```python
# FROM:
__version__ = "0.1.0"

# TO:
__version__ = "0.2.0"
```

### Success Criteria
- Version is "0.2.0"

### Dependencies
- Task 4.3 (Phase 4 complete)

---

## Task 5.2: Run Full Test Suite

### Commands
```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

### Success Criteria
- All tests pass (expect ~1100+ tests)
- No ruff errors
- No format issues

### Dependencies
- Task 5.1 (version bumped)

---

## Task 5.3: Verify Coverage Targets

### Commands
```bash
uv run pytest tests/test_notifications/ --cov=src/teambot/notifications --cov-report=term-missing
```

### Success Criteria
- Overall notifications module: 90%+
- EventBus: 95%+
- TelegramChannel: 90%+
- MessageTemplates: 100%
- Env resolver: 100%

### Dependencies
- Task 5.2 (tests passing)
