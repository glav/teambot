"""Notification channel protocol definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
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
