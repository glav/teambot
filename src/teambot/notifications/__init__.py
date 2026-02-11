"""Real-time notification system for TeamBot.

This module provides a pluggable notification system for sending
real-time updates as workflow stages complete, agent tasks finish,
or errors occur.

Components:
- NotificationEvent: Event data structure
- NotificationChannel: Protocol for notification channels
- EventBus: Pub/sub event routing
- TelegramChannel: Telegram Bot API implementation
- MessageTemplates: Event message formatting
"""

from teambot.notifications.channels.telegram import TelegramChannel
from teambot.notifications.event_bus import EventBus, RateLimitError
from teambot.notifications.events import NotificationEvent
from teambot.notifications.protocol import NotificationChannel
from teambot.notifications.templates import MessageTemplates

__all__ = [
    "NotificationEvent",
    "NotificationChannel",
    "EventBus",
    "RateLimitError",
    "MessageTemplates",
    "TelegramChannel",
]
