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
        self._pending_tasks: set[asyncio.Task] = set()

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
                # Fire and forget - track task for graceful shutdown
                task = asyncio.create_task(self._safe_send(channel, event))
                self._pending_tasks.add(task)
                task.add_done_callback(self._pending_tasks.discard)

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

    def emit_sync(self, event_type: str, data: dict[str, Any]) -> None:
        """Synchronous wrapper for emit - schedules async emit on running loop.

        Safe to call from sync callbacks like on_progress.
        Does nothing if no event loop is running.

        Args:
            event_type: Event type identifier
            data: Event data dict
        """
        if not self._channels:
            return

        event = NotificationEvent(event_type=event_type, data=data)

        # Update context from event
        if event_type == "stage_changed":
            self._current_stage = data.get("stage")

        # Add context to event
        if event.feature_name is None:
            event.feature_name = self._feature_name
        if event.stage is None:
            event.stage = self._current_stage

        try:
            loop = asyncio.get_running_loop()
            for channel in self._channels:
                if channel.enabled and channel.supports_event(event_type):
                    task = loop.create_task(self._safe_send(channel, event))
                    self._pending_tasks.add(task)
                    task.add_done_callback(self._pending_tasks.discard)
        except RuntimeError:
            # No running event loop - skip notifications
            logger.debug("No event loop running, skipping notification")

    def create_progress_callback(self):
        """Create an on_progress callback that emits to this bus.

        Returns:
            Callback function compatible with ExecutionLoop.run(on_progress=...)
        """

        def on_progress(event_type: str, data: dict[str, Any]) -> None:
            self.emit_sync(event_type, data)

        return on_progress

    async def drain(self, timeout: float = 5.0) -> None:
        """Wait for all pending notification tasks to complete.

        This method should be called before shutting down to ensure
        in-flight notifications are delivered.

        Args:
            timeout: Maximum seconds to wait for tasks (default: 5.0)

        Returns:
            None. Logs warning if timeout is reached.
        """
        if not self._pending_tasks:
            return

        logger.debug(f"Draining {len(self._pending_tasks)} pending notification tasks")

        try:
            await asyncio.wait_for(
                asyncio.gather(*self._pending_tasks, return_exceptions=True),
                timeout=timeout,
            )
            logger.debug("All notification tasks completed")
        except TimeoutError:
            logger.warning(
                f"Notification drain timeout after {timeout}s, "
                f"{len(self._pending_tasks)} tasks still pending"
            )

    async def close(self, timeout: float = 5.0) -> None:
        """Close the event bus and wait for pending tasks.

        This method drains pending tasks and clears all channels.

        Args:
            timeout: Maximum seconds to wait for pending tasks (default: 5.0)
        """
        await self.drain(timeout=timeout)
        self._channels.clear()
        self._pending_tasks.clear()
        logger.debug("EventBus closed")
