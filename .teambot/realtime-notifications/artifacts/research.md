<!-- markdownlint-disable-file -->
# Research: Real-Time Notification System

**Date:** 2026-02-11  
**Feature:** Real-Time Notifications via Telegram  
**Status:** ✅ Research Complete

---

## Table of Contents

1. [Research Scope](#research-scope)
2. [Entry Point Analysis](#entry-point-analysis)
3. [Event Infrastructure Research](#event-infrastructure-research)
4. [NotificationChannel Protocol Design](#notificationchannel-protocol-design)
5. [EventBus Implementation](#eventbus-implementation)
6. [Telegram Bot API Integration](#telegram-bot-api-integration)
7. [Configuration Schema Design](#configuration-schema-design)
8. [CLI Init Flow Enhancement](#cli-init-flow-enhancement)
9. [Testing Strategy Research](#testing-strategy-research)
10. [Implementation Recommendations](#implementation-recommendations)
11. [Task Implementation Requests](#task-implementation-requests)
12. [Potential Next Research](#potential-next-research)

---

## Research Scope

### Objectives
- Design a pluggable `NotificationChannel` protocol for extensibility
- Implement a lightweight `EventBus` connecting `on_progress` callbacks to notification channels
- Integrate Telegram Bot API for outbound-only notifications
- Extend `teambot.json` schema for notification configuration
- Add optional notification setup to `teambot init` command
- Ensure graceful failure handling without interrupting workflows

### Success Criteria
- [ ] `NotificationChannel` protocol defined with `send()`, `format()`, `poll()` methods
- [ ] `EventBus` with subscribe/unsubscribe semantics
- [ ] `TelegramChannel` sends rich HTML notifications via outbound HTTP only
- [ ] Notifications fire on 10+ event types
- [ ] Message templates per event type
- [ ] Configuration with env var substitution (`${VAR}`)
- [ ] `teambot init` guides Telegram setup
- [ ] Graceful failure handling with exponential backoff
- [ ] `dry_run` mode for testing
- [ ] `httpx` as HTTP client dependency
- [ ] 80%+ test coverage for new code

### Assumptions
- No inbound connections (webhooks, long-polling) in initial implementation
- Telegram is the only channel implemented; others designed-for
- Version bump from `0.1.0` → `0.2.0`

---

## Entry Point Analysis

### 🔍 User Input Entry Points

| Entry Point | Code Path | Reaches Feature? | Implementation Required? |
|-------------|-----------|------------------|-------------------------|
| `teambot run objective.md` | cli.py:cmd_run → _run_orchestration → ExecutionLoop.run() | YES ✅ | YES - Hook EventBus to on_progress |
| `teambot run --resume` | cli.py:_run_orchestration_resume → ExecutionLoop.run() | YES ✅ | YES - Same hook point |
| `teambot init` | cli.py:cmd_init | YES ✅ | YES - Add notification setup step |
| Interactive REPL | repl/loop.py → executor.py | NO ❌ | NO - REPL doesn't fire workflow events |

### Code Path Trace

#### Entry Point 1: `teambot run objective.md`
1. User runs: `teambot run docs/objectives/my-task.md`
2. Handled by: `cli.py:cmd_run()` (Lines 107-178)
3. Creates: `ExecutionLoop` instance (Lines 219-228)
4. Calls: `_run_orchestration_async()` with `on_progress` callback (Lines 181-198)
5. Reaches: `ExecutionLoop.run()` which emits events via `on_progress` ✅

#### Entry Point 2: `teambot run --resume`
1. User runs: `teambot run --resume`
2. Handled by: `cli.py:_run_orchestration_resume()` (Lines 316-403)
3. Calls: `_run_orchestration_resume_async()` with `on_progress` callback
4. Reaches: `ExecutionLoop.run()` ✅

#### Entry Point 3: `teambot init`
1. User runs: `teambot init`
2. Handled by: `cli.py:cmd_init()` (Lines 68-104)
3. Currently: Creates default config, directories
4. Need to add: Optional notification setup step ✅

### Coverage Gaps

| Gap | Impact | Required Fix |
|-----|--------|--------------|
| None identified | N/A | All entry points covered |

### ✅ Implementation Scope Verification

- [x] All entry points from acceptance test scenarios are traced
- [x] All code paths that should trigger feature are identified
- [x] Coverage gaps are documented with required fixes

---

## Event Infrastructure Research

### Current Event System Architecture

The orchestration layer uses a callback-based event system via `on_progress: Callable[[str, Any], None]`.

**Location:** `src/teambot/orchestration/progress.py` (Lines 11-65)

```python
def create_progress_callback(
    status_manager: AgentStatusManager,
    on_stage: Callable[[str], None] | None = None,
    on_time: Callable[[str, str], None] | None = None,
) -> Callable[[str, Any], None]:
```

### 📋 Complete Event Type Inventory

Found **22 distinct event types** emitted across orchestration modules:

#### Stage Events (Primary Notification Triggers)
| Event Type | Emitted From | Data Fields | Notification Priority |
|------------|--------------|-------------|----------------------|
| `stage_changed` | execution_loop.py:168 | `{stage: str}` | 🔴 HIGH |
| `parallel_group_start` | execution_loop.py:262 | `{group: str, stages: list[str]}` | 🟡 MEDIUM |
| `parallel_group_complete` | execution_loop.py:276, 302 | `{group: str, all_success: bool}` | 🔴 HIGH |
| `parallel_stage_start` | parallel_stage_executor.py:73 | `{stage: str, agent: str}` | 🟡 MEDIUM |
| `parallel_stage_complete` | parallel_stage_executor.py:124 | `{stage: str, agent: str}` | 🔴 HIGH |
| `parallel_stage_failed` | parallel_stage_executor.py:124 | `{stage: str, agent: str}` | 🔴 HIGH |

#### Agent Events
| Event Type | Emitted From | Data Fields | Notification Priority |
|------------|--------------|-------------|----------------------|
| `agent_running` | execution_loop.py:711, 758 | `{agent_id: str, task: str}` | 🟢 LOW |
| `agent_streaming` | parallel_executor.py:66 | `{agent_id: str, chunk: str}` | ⚪ SKIP |
| `agent_complete` | execution_loop.py:716, 770 | `{agent_id: str}` | 🟡 MEDIUM |
| `agent_failed` | parallel_executor.py:86 | `{agent_id: str, error: str}` | 🔴 HIGH |
| `agent_cancelled` | parallel_executor.py:81 | `{agent_id: str}` | 🟡 MEDIUM |
| `agent_idle` | progress.py:39 | `{agent_id: str}` | ⚪ SKIP |

#### Review Events
| Event Type | Emitted From | Data Fields | Notification Priority |
|------------|--------------|-------------|----------------------|
| `review_progress` | execution_loop.py:791 | `{stage: str, message: str}` | 🟡 MEDIUM |

#### Acceptance Test Events
| Event Type | Emitted From | Data Fields | Notification Priority |
|------------|--------------|-------------|----------------------|
| `acceptance_test_stage_start` | execution_loop.py:353 | `{stage: str}` | 🟡 MEDIUM |
| `acceptance_test_stage_complete` | execution_loop.py:428 | `{stage, passed, failed, total, duration}` | 🔴 HIGH |
| `acceptance_test_iteration` | execution_loop.py:473 | `{iteration, max_iterations, failed_count}` | 🟡 MEDIUM |
| `acceptance_test_fix_start` | execution_loop.py:530 | `{iteration, failed_count, failed_tests}` | 🟡 MEDIUM |
| `acceptance_test_fix_complete` | execution_loop.py:555 | `{iteration}` | 🟡 MEDIUM |
| `acceptance_test_max_iterations_reached` | execution_loop.py:518 | `{iterations_used, failed_count}` | 🔴 HIGH |
| `acceptance_test_validation_start` | acceptance_test_executor.py:250 | `{scenario_count}` | 🟢 LOW |
| `runtime_validation_start` | acceptance_test_executor.py:315 | `{total_scenarios}` | 🟢 LOW |
| `runtime_scenario_start` | acceptance_test_executor.py:351 | `{scenario_id, scenario_name}` | 🟢 LOW |
| `runtime_scenario_complete` | acceptance_test_executor.py:439 | `{scenario_id, success, ...}` | 🟡 MEDIUM |
| `runtime_validation_complete` | acceptance_test_executor.py:454 | `{passed, failed, total}` | 🔴 HIGH |

#### Time Events
| Event Type | Emitted From | Data Fields | Notification Priority |
|------------|--------------|-------------|----------------------|
| `time_update` | (managed externally) | `{elapsed: str, remaining: str}` | ⚪ SKIP |

### Key Finding: Current Event Flow

```
ExecutionLoop.run()
    ├── on_progress("stage_changed", {...})
    ├── _execute_work_stage()
    │   ├── on_progress("agent_running", {...})
    │   └── on_progress("agent_complete", {...})
    ├── _execute_review_stage()
    │   └── on_progress("review_progress", {...})
    └── _execute_parallel_group()
        └── on_progress("parallel_group_start/complete", {...})
```

**Recommendation:** Insert EventBus as a wrapper around or subscriber to `on_progress`.

---

## NotificationChannel Protocol Design

### Protocol Definition (Recommended Approach)

Using Python's `typing.Protocol` for structural subtyping (duck typing with type safety):

```python
# src/teambot/notifications/protocol.py

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class NotificationChannel(Protocol):
    """Protocol for notification channels (Telegram, Teams, GitHub, etc.)."""

    @property
    def name(self) -> str:
        """Unique channel identifier (e.g., 'telegram', 'teams')."""
        ...

    @property
    def enabled(self) -> bool:
        """Whether channel is currently enabled."""
        ...

    async def send(self, event: NotificationEvent) -> bool:
        """Send notification for event. Returns True if successful."""
        ...

    def format(self, event: NotificationEvent) -> str:
        """Format event into channel-specific message format."""
        ...

    def supports_event(self, event_type: str) -> bool:
        """Check if channel subscribes to this event type."""
        ...

    async def poll(self) -> list[IncomingMessage] | None:
        """Poll for incoming messages (future two-way support). Return None if not supported."""
        ...
```

### Event Data Structure

```python
# src/teambot/notifications/events.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class NotificationEvent:
    """Event data for notifications."""
    
    event_type: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    stage: str | None = None
    agent: str | None = None
    duration: float | None = None  # seconds
    success: bool | None = None
    artifacts: list[str] = field(default_factory=list)
    summary: str | None = None


@dataclass
class IncomingMessage:
    """Message received from a channel (future two-way support)."""
    
    channel: str
    sender_id: str
    text: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
```

### Rationale for Protocol Choice

| Alternative | Pros | Cons | Selected? |
|-------------|------|------|-----------|
| **Abstract Base Class (ABC)** | Explicit inheritance, clear hierarchy | Requires inheritance, less flexible | ❌ |
| **Protocol (typing.Protocol)** | Duck typing, structural subtyping, no inheritance required | Slightly newer (Python 3.8+) | ✅ |
| **Simple dict-based** | Maximum flexibility | No type safety, error-prone | ❌ |

**Selected:** `typing.Protocol` — Matches Python 3.10+ requirement, enables duck typing while maintaining type safety.

---

## EventBus Implementation

### Design Requirements

1. Subscribe channels to specific event types
2. Fire events without blocking main workflow
3. Handle channel failures gracefully
4. Support dry_run mode per channel

### Recommended Implementation

```python
# src/teambot/notifications/event_bus.py

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from teambot.notifications.events import NotificationEvent
    from teambot.notifications.protocol import NotificationChannel

logger = logging.getLogger(__name__)


class EventBus:
    """Routes events to subscribed notification channels."""

    def __init__(self, max_retry: int = 3, retry_base_delay: float = 1.0):
        self._channels: list[NotificationChannel] = []
        self._max_retry = max_retry
        self._retry_base_delay = retry_base_delay

    def subscribe(self, channel: NotificationChannel) -> None:
        """Add a channel to receive events."""
        self._channels.append(channel)
        logger.info(f"Subscribed channel: {channel.name}")

    def unsubscribe(self, channel_name: str) -> None:
        """Remove a channel by name."""
        self._channels = [c for c in self._channels if c.name != channel_name]
        logger.info(f"Unsubscribed channel: {channel_name}")

    async def emit(self, event: NotificationEvent) -> None:
        """Emit event to all subscribed channels (non-blocking)."""
        tasks = []
        for channel in self._channels:
            if channel.enabled and channel.supports_event(event.event_type):
                tasks.append(self._send_with_retry(channel, event))
        
        if tasks:
            # Fire and forget - don't wait, don't block
            asyncio.create_task(self._gather_sends(tasks))

    async def _gather_sends(self, tasks: list) -> None:
        """Gather all send tasks, log any failures."""
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Notification send failed: {result}")

    async def _send_with_retry(
        self, channel: NotificationChannel, event: NotificationEvent
    ) -> bool:
        """Send with exponential backoff retry for rate limits."""
        for attempt in range(self._max_retry):
            try:
                return await channel.send(event)
            except RateLimitError as e:
                if attempt < self._max_retry - 1:
                    delay = self._retry_base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max retries exceeded for {channel.name}: {e}")
                    return False
            except Exception as e:
                logger.error(f"Notification failed for {channel.name}: {e}")
                return False
        return False


class RateLimitError(Exception):
    """Raised when API rate limit is hit (HTTP 429)."""
    pass
```

### Integration Point

The EventBus should be created once and passed to `ExecutionLoop.run()` as an additional callback layer:

```python
# In cli.py or orchestration setup

async def _run_orchestration_async(...):
    event_bus = create_event_bus_from_config(config)
    
    def on_progress_with_notifications(event_type: str, data: dict) -> None:
        # Original UI update
        original_on_progress(event_type, data)
        # Also emit to notification channels
        asyncio.create_task(event_bus.emit(
            NotificationEvent(event_type=event_type, data=data)
        ))
```

---

## Telegram Bot API Integration

### API Overview

**Base URL:** `https://api.telegram.org/bot<token>/<method>`

**Method for sending:** `sendMessage`

**Documentation:** https://core.telegram.org/bots/api

### sendMessage API

```
POST https://api.telegram.org/bot<token>/sendMessage

Parameters:
- chat_id (required): Unique identifier for target chat
- text (required): Message text (0-4096 characters)
- parse_mode (optional): "HTML" or "MarkdownV2"
- disable_web_page_preview (optional): boolean
- disable_notification (optional): boolean
```

### Response Format

```json
{
  "ok": true,
  "result": {
    "message_id": 123,
    "chat": {"id": -1001234567890, "type": "supergroup"},
    "date": 1707609600,
    "text": "..."
  }
}
```

### Error Handling

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 200 | Success | ✅ |
| 400 | Bad request | Log error, don't retry |
| 401 | Unauthorized | Invalid token, log critical |
| 403 | Forbidden | Bot blocked or chat access denied |
| 429 | Too Many Requests | Rate limit - use `retry_after` header |
| 500+ | Server error | Retry with backoff |

### TelegramChannel Implementation

```python
# src/teambot/notifications/channels/telegram.py

from __future__ import annotations

import os
import logging
from typing import Any

import httpx

from teambot.notifications.events import NotificationEvent, IncomingMessage
from teambot.notifications.event_bus import RateLimitError

logger = logging.getLogger(__name__)


class TelegramChannel:
    """Telegram notification channel via Bot API."""

    def __init__(
        self,
        token_env_var: str = "TEAMBOT_TELEGRAM_TOKEN",
        chat_id_env_var: str = "TEAMBOT_TELEGRAM_CHAT_ID",
        subscribed_events: list[str] | None = None,
        dry_run: bool = False,
    ):
        self._token_env = token_env_var
        self._chat_id_env = chat_id_env_var
        self._subscribed = set(subscribed_events or self._default_events())
        self._dry_run = dry_run
        self._client: httpx.AsyncClient | None = None
        self._templates = MessageTemplates()

    @property
    def name(self) -> str:
        return "telegram"

    @property
    def enabled(self) -> bool:
        return bool(self._get_token() and self._get_chat_id())

    def supports_event(self, event_type: str) -> bool:
        return event_type in self._subscribed

    async def send(self, event: NotificationEvent) -> bool:
        """Send notification to Telegram."""
        message = self.format(event)
        
        if self._dry_run:
            logger.info(f"[DRY RUN] Telegram notification:\n{message}")
            return True

        token = self._get_token()
        chat_id = self._get_chat_id()
        
        if not token or not chat_id:
            logger.warning("Telegram credentials not configured")
            return False

        if not self._client:
            self._client = httpx.AsyncClient(timeout=30.0)

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            response = await self._client.post(url, json=payload)
            
            if response.status_code == 429:
                retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                raise RateLimitError(f"Rate limited, retry after {retry_after}s")
            
            response.raise_for_status()
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Telegram API error: {e.response.status_code} - {e.response.text}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Telegram request failed: {e}")
            return False

    def format(self, event: NotificationEvent) -> str:
        """Format event using HTML template."""
        return self._templates.render(event)

    async def poll(self) -> list[IncomingMessage] | None:
        """Not implemented - future two-way support."""
        return None

    def _get_token(self) -> str | None:
        return os.environ.get(self._token_env)

    def _get_chat_id(self) -> str | None:
        return os.environ.get(self._chat_id_env)

    @staticmethod
    def _default_events() -> list[str]:
        return [
            "stage_changed",
            "stage_complete",
            "agent_complete",
            "agent_failed",
            "parallel_stage_start",
            "parallel_stage_complete",
            "parallel_stage_failed",
            "parallel_group_complete",
            "review_progress",
            "acceptance_test_stage_complete",
            "acceptance_test_max_iterations_reached",
        ]
```

### Message Templates

```python
# src/teambot/notifications/templates.py

from teambot.notifications.events import NotificationEvent


class MessageTemplates:
    """HTML message templates for Telegram notifications."""

    TEMPLATES = {
        "stage_changed": """
🔄 <b>Stage: {stage}</b>
Workflow advancing to next stage.
""",
        "agent_complete": """
✅ <b>Agent Complete</b>
Agent <code>{agent_id}</code> finished task.
""",
        "agent_failed": """
❌ <b>Agent Failed</b>
Agent <code>{agent_id}</code> encountered an error.
<pre>{error}</pre>
""",
        "parallel_stage_complete": """
✅ <b>Parallel Stage Complete</b>
Stage <b>{stage}</b> completed by <code>{agent}</code>.
""",
        "parallel_stage_failed": """
❌ <b>Parallel Stage Failed</b>
Stage <b>{stage}</b> failed for <code>{agent}</code>.
""",
        "parallel_group_complete": """
{emoji} <b>Parallel Group Complete</b>
Group: <b>{group}</b>
All stages succeeded: {all_success}
""",
        "acceptance_test_stage_complete": """
{emoji} <b>Acceptance Tests {status}</b>
Passed: {passed}/{total}
Failed: {failed}
Duration: {duration}
""",
        "acceptance_test_max_iterations_reached": """
⚠️ <b>Max Fix Iterations Reached</b>
Acceptance tests still failing after {iterations_used} attempts.
Failed tests: {failed_count}
""",
        "review_progress": """
📝 <b>Review Progress</b>
Stage: {stage}
{message}
""",
    }

    def render(self, event: NotificationEvent) -> str:
        """Render event using appropriate template."""
        template = self.TEMPLATES.get(event.event_type, self._default_template())
        
        # Build context from event
        context = {**event.data}
        context["event_type"] = event.event_type
        
        # Add computed fields
        if event.event_type == "parallel_group_complete":
            context["emoji"] = "✅" if event.data.get("all_success") else "⚠️"
        elif event.event_type == "acceptance_test_stage_complete":
            passed = event.data.get("passed", 0)
            failed = event.data.get("failed", 0)
            context["emoji"] = "✅" if failed == 0 else "❌"
            context["status"] = "Passed" if failed == 0 else "Failed"
        
        try:
            return template.format(**context).strip()
        except KeyError as e:
            return f"📢 Event: {event.event_type}\nData: {event.data}"

    def _default_template(self) -> str:
        return "📢 <b>{event_type}</b>\n{data}"
```

---

## Configuration Schema Design

### Proposed Schema Addition

```json
{
  "agents": [...],
  "notifications": {
    "enabled": true,
    "channels": [
      {
        "type": "telegram",
        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
        "events": [
          "stage_changed",
          "agent_failed",
          "parallel_group_complete",
          "acceptance_test_stage_complete"
        ],
        "dry_run": false
      }
    ]
  }
}
```

### Environment Variable Substitution

Pattern: `${ENV_VAR_NAME}` resolved at runtime.

```python
# src/teambot/config/env_resolver.py

import os
import re


ENV_VAR_PATTERN = re.compile(r'\$\{([A-Z_][A-Z0-9_]*)\}')


def resolve_env_vars(value: str) -> str:
    """Resolve ${VAR} patterns in string values."""
    if not isinstance(value, str):
        return value
    
    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, "")
    
    return ENV_VAR_PATTERN.sub(replacer, value)


def resolve_config_secrets(config: dict) -> dict:
    """Recursively resolve env vars in config."""
    if isinstance(config, dict):
        return {k: resolve_config_secrets(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [resolve_config_secrets(v) for v in config]
    elif isinstance(config, str):
        return resolve_env_vars(config)
    return config
```

### ConfigLoader Extension

Add validation for `notifications` section in `loader.py`:

```python
def _validate_notifications(self, notifications: dict) -> None:
    """Validate notifications configuration."""
    if not isinstance(notifications, dict):
        raise ConfigError("'notifications' must be an object")
    
    if "channels" in notifications:
        channels = notifications["channels"]
        if not isinstance(channels, list):
            raise ConfigError("'notifications.channels' must be a list")
        
        for i, channel in enumerate(channels):
            self._validate_notification_channel(channel, i)

def _validate_notification_channel(self, channel: dict, index: int) -> None:
    """Validate a single notification channel config."""
    if "type" not in channel:
        raise ConfigError(f"Channel {index} must have 'type' field")
    
    channel_type = channel["type"]
    valid_types = {"telegram"}  # Add more as implemented
    
    if channel_type not in valid_types:
        raise ConfigError(
            f"Invalid channel type '{channel_type}'. Valid: {valid_types}"
        )
```

---

## CLI Init Flow Enhancement

### Current Init Flow (cli.py:68-104)

1. Check for existing config
2. Create default config
3. Create `.teambot` directories
4. Display agents

### Enhanced Init Flow

Add optional notification setup after directory creation:

```python
def cmd_init(args: argparse.Namespace, display: ConsoleDisplay) -> int:
    """Initialize TeamBot configuration."""
    # ... existing config creation ...
    
    # Optional: Notification setup
    if _should_setup_notifications(display):
        _setup_telegram_notifications(config, display)
    
    # Save config
    loader.save(config, config_path)
    
    # ... rest of existing code ...


def _should_setup_notifications(display: ConsoleDisplay) -> bool:
    """Ask user if they want to set up notifications."""
    display.console.print("\n[bold]Enable real-time notifications?[/bold]")
    display.console.print("Receive updates on Telegram when stages complete.\n")
    
    response = input("Set up notifications? [y/N]: ").strip().lower()
    return response in ("y", "yes")


def _setup_telegram_notifications(config: dict, display: ConsoleDisplay) -> None:
    """Guide user through Telegram bot setup."""
    display.console.print("\n[bold blue]📱 Telegram Setup[/bold blue]")
    display.console.print("1. Open Telegram and message @BotFather")
    display.console.print("2. Send /newbot and follow prompts")
    display.console.print("3. Copy the bot token\n")
    
    token_input = input("Bot token (or press Enter to skip): ").strip()
    
    if not token_input:
        display.print_warning("Skipping Telegram setup")
        return
    
    display.console.print("\n4. Add your bot to a group or get your chat ID")
    display.console.print("   (Message @userinfobot to get your ID)\n")
    
    chat_id_input = input("Chat ID: ").strip()
    
    if not chat_id_input:
        display.print_warning("Skipping Telegram setup")
        return
    
    # Add notifications config
    config["notifications"] = {
        "enabled": True,
        "channels": [
            {
                "type": "telegram",
                "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
            }
        ]
    }
    
    display.print_success("Telegram notifications configured!")
    display.console.print("\n[yellow]⚠️  Set these environment variables:[/yellow]")
    display.console.print(f"   export TEAMBOT_TELEGRAM_TOKEN='{token_input}'")
    display.console.print(f"   export TEAMBOT_TELEGRAM_CHAT_ID='{chat_id_input}'")
    display.console.print("\n   Add them to your .env file or shell profile.\n")
```

---

## Testing Strategy Research

### Existing Test Infrastructure

**Framework:** pytest 7.4.0 with pytest-cov, pytest-mock, pytest-asyncio  
**Location:** `tests/` directory mirroring `src/teambot/` structure  
**Naming:** `test_*.py` pattern  
**Runner:** `uv run pytest` (from pyproject.toml)  
**Coverage:** 80% target

### Test Patterns Found

**File:** `tests/test_orchestration/test_progress.py` (Lines 1-254)
- Uses `Mock` for callbacks
- Verifies event handling via state checks
- Tests parallel group events separately

**File:** `tests/conftest.py` (Lines 1-185)
- `AsyncMock` for async SDK client
- `MockStreamingSession` for event streaming
- Fixtures for temp directories

**File:** `tests/test_config/test_loader.py` (Lines 1-515)
- Tests valid/invalid config loading
- Tests default value application
- Tests validation error messages

### Testing Approach Recommendation

| Component | Approach | Rationale |
|-----------|----------|-----------|
| `NotificationChannel` Protocol | TDD | Well-defined interface, critical |
| `EventBus` | TDD | Core infrastructure, needs reliability |
| `TelegramChannel` | Code-First + Mocks | External API, mock httpx |
| `MessageTemplates` | TDD | Template rendering, easy to test |
| Config validation | TDD | Follows existing pattern |
| CLI init flow | Code-First | Interactive, harder to test |

### Test Plan

```
tests/
└── test_notifications/
    ├── __init__.py
    ├── conftest.py           # Shared fixtures
    ├── test_protocol.py      # Protocol interface tests
    ├── test_events.py        # Event dataclass tests
    ├── test_event_bus.py     # EventBus tests
    ├── test_telegram.py      # TelegramChannel tests (mocked)
    ├── test_templates.py     # Message template tests
    └── test_config.py        # Notification config validation
```

### Key Test Cases

```python
# test_event_bus.py

class TestEventBus:
    async def test_emit_sends_to_subscribed_channels(self):
        """emit() sends event to channels that support the event type."""
        
    async def test_emit_skips_disabled_channels(self):
        """emit() does not send to disabled channels."""
        
    async def test_emit_does_not_block(self):
        """emit() returns immediately without waiting for sends."""
        
    async def test_retry_on_rate_limit(self):
        """Rate limit errors trigger exponential backoff retry."""
        
    async def test_max_retries_exceeded_logs_error(self):
        """After max retries, logs error but doesn't raise."""


# test_telegram.py

class TestTelegramChannel:
    async def test_send_success(self, mock_httpx):
        """Successful send returns True."""
        
    async def test_send_dry_run_logs_only(self):
        """dry_run=True logs message but doesn't send."""
        
    async def test_send_missing_credentials_returns_false(self):
        """Missing env vars returns False gracefully."""
        
    async def test_send_rate_limit_raises(self, mock_httpx):
        """429 response raises RateLimitError."""
        
    async def test_format_uses_template(self):
        """format() uses correct template for event type."""
```

### Coverage Requirements

- Unit tests: 85% minimum for new code
- Integration tests: Test EventBus → TelegramChannel flow with mocked HTTP

---

## Implementation Recommendations

### Module Structure

```
src/teambot/notifications/
├── __init__.py
├── protocol.py        # NotificationChannel protocol
├── events.py          # NotificationEvent, IncomingMessage
├── event_bus.py       # EventBus implementation
├── templates.py       # MessageTemplates
├── channels/
│   ├── __init__.py
│   └── telegram.py    # TelegramChannel
└── config.py          # Notification config loading/validation
```

### Dependency Addition

Add to `pyproject.toml`:

```toml
dependencies = [
    # ... existing ...
    "httpx>=0.27.0",
]
```

### Integration Approach

1. **Minimal changes to existing code** — Add EventBus as optional callback wrapper
2. **Lazy initialization** — Only create Telegram client when needed
3. **Fail-safe** — All notification errors logged, never propagated

### Version Bump

Update `src/teambot/__init__.py`:

```python
__version__ = "0.2.0"
```

---

## Task Implementation Requests

### Phase 1: Core Infrastructure
1. ✅ Create `src/teambot/notifications/` module structure
2. ✅ Implement `NotificationEvent` dataclass in `events.py`
3. ✅ Implement `NotificationChannel` protocol in `protocol.py`
4. ✅ Implement `EventBus` in `event_bus.py`
5. ✅ Write tests for EventBus (TDD)

### Phase 2: Telegram Channel
6. ✅ Add `httpx` dependency to `pyproject.toml`
7. ✅ Implement `TelegramChannel` in `channels/telegram.py`
8. ✅ Implement `MessageTemplates` in `templates.py`
9. ✅ Write tests for TelegramChannel (mocked HTTP)

### Phase 3: Configuration
10. ✅ Implement env var resolver in `config/env_resolver.py`
11. ✅ Add notification config validation to `ConfigLoader`
12. ✅ Write tests for config validation

### Phase 4: Integration
13. ✅ Create EventBus factory from config
14. ✅ Integrate EventBus with `on_progress` in `cli.py`
15. ✅ Add notification setup to `cmd_init()`

### Phase 5: Finalization
16. ✅ Update version to `0.2.0`
17. ✅ Run full test suite, ensure 80%+ coverage
18. ✅ Update documentation

---

## Potential Next Research

### Completed ✅
- EventBus design patterns
- Telegram Bot API integration
- Environment variable resolution
- Test infrastructure patterns

### Future Considerations (Not in Scope)
- **TeamsChannel** — Adaptive Cards via Power Automate Workflow URLs
- **GitHubChannel** — Issue/PR comments via `gh` CLI
- **Two-way communication** — Telegram long-polling for commands
- **Webhook mode** — For high-traffic scenarios (requires port exposure)

---

## References

| Topic | Source | Notes |
|-------|--------|-------|
| Telegram Bot API | https://core.telegram.org/bots/api | sendMessage, rate limits |
| httpx library | https://www.python-httpx.org/ | Async HTTP client |
| Python Protocol | PEP 544 | Structural subtyping |
| Existing events | src/teambot/orchestration/ | 22 event types identified |
| Test patterns | tests/test_orchestration/ | pytest + AsyncMock |
| Config patterns | src/teambot/config/loader.py | Validation + defaults |
