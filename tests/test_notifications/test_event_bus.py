"""Tests for EventBus."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from teambot.notifications.event_bus import EventBus, RateLimitError
from teambot.notifications.events import NotificationEvent


class TestEventBusSubscribe:
    """Tests for EventBus.subscribe()."""

    def test_subscribe_adds_channel(self, mock_channel: MagicMock) -> None:
        """subscribe() adds channel to internal list."""
        bus = EventBus()

        bus.subscribe(mock_channel)

        assert len(bus._channels) == 1
        assert bus._channels[0].name == "test-channel"

    def test_subscribe_prevents_duplicates(self, mock_channel: MagicMock) -> None:
        """subscribe() does not add same channel twice."""
        bus = EventBus()

        bus.subscribe(mock_channel)
        bus.subscribe(mock_channel)

        assert len(bus._channels) == 1

    def test_subscribe_multiple_channels(self, mock_channel: MagicMock) -> None:
        """subscribe() can add multiple different channels."""
        bus = EventBus()
        channel2 = MagicMock()
        channel2.name = "channel-2"

        bus.subscribe(mock_channel)
        bus.subscribe(channel2)

        assert len(bus._channels) == 2


class TestEventBusUnsubscribe:
    """Tests for EventBus.unsubscribe()."""

    def test_unsubscribe_removes_channel(self, mock_channel: MagicMock) -> None:
        """unsubscribe() removes channel by name."""
        bus = EventBus()
        bus.subscribe(mock_channel)

        bus.unsubscribe("test-channel")

        assert len(bus._channels) == 0

    def test_unsubscribe_nonexistent_is_noop(self) -> None:
        """unsubscribe() with unknown name does nothing."""
        bus = EventBus()

        bus.unsubscribe("nonexistent")

        assert len(bus._channels) == 0


class TestEventBusEmit:
    """Tests for EventBus.emit()."""

    @pytest.mark.asyncio
    async def test_emit_calls_channel_send(
        self, mock_channel: MagicMock, sample_event: NotificationEvent
    ) -> None:
        """emit() calls send() on subscribed channels."""
        bus = EventBus()
        bus.subscribe(mock_channel)

        await bus.emit(sample_event)

        # Allow async task to complete
        await asyncio.sleep(0.05)
        mock_channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_skips_disabled_channel(
        self, disabled_channel: MagicMock, sample_event: NotificationEvent
    ) -> None:
        """emit() does not call send() on disabled channels."""
        bus = EventBus()
        bus.subscribe(disabled_channel)

        await bus.emit(sample_event)

        await asyncio.sleep(0.05)
        disabled_channel.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_emit_skips_unsupported_event(
        self, mock_channel: MagicMock, sample_event: NotificationEvent
    ) -> None:
        """emit() skips channels that don't support event type."""
        mock_channel.supports_event.return_value = False
        bus = EventBus()
        bus.subscribe(mock_channel)

        await bus.emit(sample_event)

        await asyncio.sleep(0.05)
        mock_channel.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_emit_with_no_channels(self, sample_event: NotificationEvent) -> None:
        """emit() with no channels is a no-op."""
        bus = EventBus()

        # Should not raise
        await bus.emit(sample_event)

    @pytest.mark.asyncio
    async def test_emit_is_nonblocking(self, mock_channel: MagicMock) -> None:
        """emit() returns immediately without waiting for send."""

        # Make send take a long time
        async def slow_send(event):
            await asyncio.sleep(5)
            return True

        mock_channel.send = slow_send
        bus = EventBus()
        bus.subscribe(mock_channel)

        event = NotificationEvent(event_type="test", data={})

        # emit() should return quickly even if send takes 5s
        start = time.time()
        await bus.emit(event)
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should be nearly instant

    @pytest.mark.asyncio
    async def test_emit_adds_context(self, mock_channel: MagicMock) -> None:
        """emit() adds feature_name and stage context to event."""
        bus = EventBus(feature_name="my-feature")
        bus.set_stage("IMPLEMENTATION")
        bus.subscribe(mock_channel)

        event = NotificationEvent(event_type="test", data={})
        await bus.emit(event)

        await asyncio.sleep(0.05)
        # Check that event was modified
        assert event.feature_name == "my-feature"
        assert event.stage == "IMPLEMENTATION"


class TestEventBusRetry:
    """Tests for EventBus retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, mock_channel: MagicMock) -> None:
        """RateLimitError triggers retry with backoff."""
        # First call raises, second succeeds
        mock_channel.send = AsyncMock(side_effect=[RateLimitError(retry_after=0.01), True])
        bus = EventBus()
        bus.subscribe(mock_channel)

        event = NotificationEvent(event_type="test", data={})
        await bus.emit(event)

        await asyncio.sleep(0.1)
        assert mock_channel.send.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_channel: MagicMock, caplog) -> None:
        """Max retries exceeded logs error."""
        mock_channel.send = AsyncMock(side_effect=RateLimitError(retry_after=0.01))
        bus = EventBus()
        bus.subscribe(mock_channel)

        event = NotificationEvent(event_type="test", data={})
        await bus.emit(event)

        await asyncio.sleep(0.2)
        assert mock_channel.send.call_count == EventBus.MAX_RETRIES
        assert "max retries exceeded" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_channel_exception_logged(self, mock_channel: MagicMock, caplog) -> None:
        """Non-rate-limit exceptions are logged, not retried."""
        mock_channel.send = AsyncMock(side_effect=Exception("Network error"))
        bus = EventBus()
        bus.subscribe(mock_channel)

        event = NotificationEvent(event_type="test", data={})
        await bus.emit(event)

        await asyncio.sleep(0.05)
        assert mock_channel.send.call_count == 1
        assert "send failed" in caplog.text.lower()


class TestEventBusEmitSync:
    """Tests for EventBus.emit_sync()."""

    @pytest.mark.asyncio
    async def test_emit_sync_sends_to_channel(self, mock_channel: MagicMock) -> None:
        """emit_sync() schedules async send on running loop."""
        bus = EventBus()
        bus.subscribe(mock_channel)

        bus.emit_sync("stage_changed", {"stage": "SETUP"})

        await asyncio.sleep(0.05)
        mock_channel.send.assert_called_once()
        call_args = mock_channel.send.call_args[0][0]
        assert call_args.event_type == "stage_changed"

    @pytest.mark.asyncio
    async def test_emit_sync_adds_context(self, mock_channel: MagicMock) -> None:
        """emit_sync() adds feature_name context."""
        bus = EventBus(feature_name="test-feature")
        bus.subscribe(mock_channel)

        bus.emit_sync("agent_complete", {"agent_id": "pm"})

        await asyncio.sleep(0.05)
        call_args = mock_channel.send.call_args[0][0]
        assert call_args.feature_name == "test-feature"

    def test_emit_sync_no_loop_is_noop(self, mock_channel: MagicMock) -> None:
        """emit_sync() without running loop does nothing."""
        bus = EventBus()
        bus.subscribe(mock_channel)

        # No event loop - should not raise
        bus.emit_sync("test", {})

        mock_channel.send.assert_not_called()


class TestEventBusProgressCallback:
    """Tests for EventBus.create_progress_callback()."""

    @pytest.mark.asyncio
    async def test_callback_emits_event(self, mock_channel: MagicMock) -> None:
        """Progress callback creates and emits event."""
        bus = EventBus()
        bus.subscribe(mock_channel)
        callback = bus.create_progress_callback()

        callback("stage_changed", {"stage": "SETUP"})

        await asyncio.sleep(0.05)
        mock_channel.send.assert_called_once()
        call_args = mock_channel.send.call_args[0][0]
        assert call_args.event_type == "stage_changed"
        assert call_args.data["stage"] == "SETUP"


class TestEventBusTaskTracking:
    """Tests for EventBus task tracking."""

    @pytest.mark.asyncio
    async def test_emit_tracks_pending_tasks(self, mock_channel: MagicMock) -> None:
        """emit() adds tasks to _pending_tasks."""

        # Make send slow so task stays pending
        async def slow_send(event):
            await asyncio.sleep(0.2)

        mock_channel.send = slow_send
        bus = EventBus()
        bus.subscribe(mock_channel)

        event = NotificationEvent(event_type="test", data={})
        await bus.emit(event)

        # Task should be pending
        assert len(bus._pending_tasks) == 1

        # Wait for task to complete
        await asyncio.sleep(0.3)
        assert len(bus._pending_tasks) == 0

    @pytest.mark.asyncio
    async def test_emit_sync_tracks_pending_tasks(self, mock_channel: MagicMock) -> None:
        """emit_sync() adds tasks to _pending_tasks."""

        # Make send slow so task stays pending
        async def slow_send(event):
            await asyncio.sleep(0.2)

        mock_channel.send = slow_send
        bus = EventBus()
        bus.subscribe(mock_channel)

        bus.emit_sync("test", {})

        # Give time for task to be scheduled
        await asyncio.sleep(0.05)
        assert len(bus._pending_tasks) == 1

        # Wait for task to complete
        await asyncio.sleep(0.3)
        assert len(bus._pending_tasks) == 0

    @pytest.mark.asyncio
    async def test_failed_tasks_are_removed(self, mock_channel: MagicMock) -> None:
        """Failed tasks are removed from _pending_tasks."""
        mock_channel.send = AsyncMock(side_effect=Exception("Error"))
        bus = EventBus()
        bus.subscribe(mock_channel)

        event = NotificationEvent(event_type="test", data={})
        await bus.emit(event)

        # Wait for task to fail
        await asyncio.sleep(0.1)
        assert len(bus._pending_tasks) == 0


class TestEventBusDrain:
    """Tests for EventBus.drain()."""

    @pytest.mark.asyncio
    async def test_drain_waits_for_pending_tasks(self, mock_channel: MagicMock) -> None:
        """drain() waits for all pending tasks to complete."""
        completed = []

        async def slow_send(event):
            await asyncio.sleep(0.1)
            completed.append(True)

        mock_channel.send = slow_send
        bus = EventBus()
        bus.subscribe(mock_channel)

        # Emit multiple events
        for i in range(3):
            event = NotificationEvent(event_type=f"test{i}", data={})
            await bus.emit(event)

        assert len(bus._pending_tasks) == 3
        assert len(completed) == 0

        # Drain should wait for all tasks
        await bus.drain(timeout=1.0)

        assert len(bus._pending_tasks) == 0
        assert len(completed) == 3

    @pytest.mark.asyncio
    async def test_drain_returns_immediately_with_no_tasks(self) -> None:
        """drain() with no pending tasks returns immediately."""
        bus = EventBus()

        import time

        start = time.time()
        await bus.drain(timeout=5.0)
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should be instant

    @pytest.mark.asyncio
    async def test_drain_timeout_logs_warning(self, mock_channel: MagicMock, caplog) -> None:
        """drain() logs warning if timeout is reached."""

        async def very_slow_send(event):
            await asyncio.sleep(10)

        mock_channel.send = very_slow_send
        bus = EventBus()
        bus.subscribe(mock_channel)

        event = NotificationEvent(event_type="test", data={})
        await bus.emit(event)

        # Give the task time to start
        await asyncio.sleep(0.01)

        # Drain with short timeout - increased for cross-platform reliability
        await bus.drain(timeout=1.0)

        assert "timeout" in caplog.text.lower()
        assert "still pending" in caplog.text.lower()


class TestEventBusClose:
    """Tests for EventBus.close()."""

    @pytest.mark.asyncio
    async def test_close_drains_and_clears(self, mock_channel: MagicMock) -> None:
        """close() drains tasks and clears channels."""
        completed = []

        async def slow_send(event):
            await asyncio.sleep(0.1)
            completed.append(True)

        mock_channel.send = slow_send
        bus = EventBus()
        bus.subscribe(mock_channel)

        event = NotificationEvent(event_type="test", data={})
        await bus.emit(event)

        assert len(bus._channels) == 1
        assert len(bus._pending_tasks) == 1

        await bus.close(timeout=1.0)

        assert len(bus._channels) == 0
        assert len(bus._pending_tasks) == 0
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_close_with_timeout(self, mock_channel: MagicMock, caplog) -> None:
        """close() respects timeout parameter."""

        async def very_slow_send(event):
            await asyncio.sleep(10)

        mock_channel.send = very_slow_send
        bus = EventBus()
        bus.subscribe(mock_channel)

        event = NotificationEvent(event_type="test", data={})
        await bus.emit(event)

        # Give the task time to start
        await asyncio.sleep(0.01)

        # Increased timeout for cross-platform reliability
        await bus.close(timeout=1.0)

        # Channels should still be cleared even with timeout
        assert len(bus._channels) == 0
        assert "timeout" in caplog.text.lower()
