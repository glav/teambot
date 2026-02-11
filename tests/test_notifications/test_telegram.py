"""Tests for TelegramChannel."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from teambot.notifications.channels.telegram import TelegramChannel
from teambot.notifications.event_bus import RateLimitError
from teambot.notifications.events import NotificationEvent


class TestTelegramChannelProperties:
    """Tests for TelegramChannel properties."""

    def test_name_is_telegram(self) -> None:
        """Channel name is 'telegram'."""
        channel = TelegramChannel()
        assert channel.name == "telegram"

    def test_enabled_when_credentials_set(self, monkeypatch) -> None:
        """Channel is enabled when env vars are set."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        channel = TelegramChannel()
        assert channel.enabled is True

    def test_disabled_when_missing_token(self, monkeypatch) -> None:
        """Channel is disabled when token missing."""
        monkeypatch.delenv("TEAMBOT_TELEGRAM_TOKEN", raising=False)
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        channel = TelegramChannel()
        assert channel.enabled is False

    def test_disabled_when_missing_chat_id(self, monkeypatch) -> None:
        """Channel is disabled when chat_id missing."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.delenv("TEAMBOT_TELEGRAM_CHAT_ID", raising=False)

        channel = TelegramChannel()
        assert channel.enabled is False


class TestTelegramChannelSupportsEvent:
    """Tests for TelegramChannel.supports_event()."""

    def test_supports_all_when_no_filter(self) -> None:
        """With no filter, supports all events."""
        channel = TelegramChannel()
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_failed") is True
        assert channel.supports_event("any_event") is True

    def test_supports_only_subscribed_events(self) -> None:
        """With filter, supports only listed events."""
        channel = TelegramChannel(subscribed_events={"stage_changed", "agent_failed"})
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_failed") is True
        assert channel.supports_event("agent_complete") is False


class TestTelegramChannelFormat:
    """Tests for TelegramChannel.format()."""

    def test_format_uses_templates(self) -> None:
        """format() uses MessageTemplates to render."""
        channel = TelegramChannel()
        event = NotificationEvent(
            event_type="stage_changed",
            data={"stage": "SETUP"},
            feature_name="test",
        )

        result = channel.format(event)

        assert "Stage:" in result
        assert "SETUP" in result

    def test_format_truncates_long_messages(self) -> None:
        """Long messages are truncated to MAX_MESSAGE_LENGTH."""
        channel = TelegramChannel()
        event = NotificationEvent(
            event_type="review_progress",
            data={"stage": "TEST", "message": "x" * 5000},
            feature_name="test",
        )

        result = channel.format(event)

        assert len(result) <= TelegramChannel.MAX_MESSAGE_LENGTH
        assert "truncated" in result


class TestTelegramChannelSend:
    """Tests for TelegramChannel.send()."""

    @pytest.mark.asyncio
    async def test_send_dry_run(self, caplog) -> None:
        """dry_run=True logs message without HTTP call."""
        import logging

        caplog.set_level(logging.INFO)
        channel = TelegramChannel(dry_run=True)
        event = NotificationEvent(
            event_type="stage_changed",
            data={"stage": "SETUP"},
        )

        result = await channel.send(event)

        assert result is True
        assert "[DRY RUN]" in caplog.text

    @pytest.mark.asyncio
    async def test_send_missing_credentials(self, monkeypatch, caplog) -> None:
        """Missing credentials returns False."""
        monkeypatch.delenv("TEAMBOT_TELEGRAM_TOKEN", raising=False)
        monkeypatch.delenv("TEAMBOT_TELEGRAM_CHAT_ID", raising=False)

        channel = TelegramChannel()
        event = NotificationEvent(event_type="test", data={})

        result = await channel.send(event)

        assert result is False
        assert "not configured" in caplog.text

    @pytest.mark.asyncio
    async def test_send_success(self, monkeypatch) -> None:
        """Successful send returns True."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        channel = TelegramChannel()
        event = NotificationEvent(
            event_type="stage_changed",
            data={"stage": "SETUP"},
        )

        # Mock httpx client
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        channel._client = mock_client

        result = await channel.send(event)

        assert result is True
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_rate_limit(self, monkeypatch) -> None:
        """HTTP 429 raises RateLimitError."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        channel = TelegramChannel()
        event = NotificationEvent(event_type="test", data={})

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"parameters": {"retry_after": 30}}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        channel._client = mock_client

        with pytest.raises(RateLimitError) as exc_info:
            await channel.send(event)

        assert exc_info.value.retry_after == 30

    @pytest.mark.asyncio
    async def test_send_api_error(self, monkeypatch, caplog) -> None:
        """API error returns False and logs."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        channel = TelegramChannel()
        event = NotificationEvent(event_type="test", data={})

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"description": "Bad Request"}
        mock_response.text = "Bad Request"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        channel._client = mock_client

        result = await channel.send(event)

        assert result is False
        assert "API error" in caplog.text

    @pytest.mark.asyncio
    async def test_send_rate_limit_non_json_response(self, monkeypatch, caplog) -> None:
        """HTTP 429 with non-JSON body uses default retry_after."""
        import logging

        caplog.set_level(logging.WARNING)
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        channel = TelegramChannel()
        event = NotificationEvent(event_type="test", data={})

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "<html>Rate Limited</html>"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        channel._client = mock_client

        with pytest.raises(RateLimitError) as exc_info:
            await channel.send(event)

        # Should use default retry_after value
        assert exc_info.value.retry_after == 1.0
        assert "Failed to parse retry_after" in caplog.text

    @pytest.mark.asyncio
    async def test_send_api_error_non_json_response(self, monkeypatch, caplog) -> None:
        """API error with non-JSON body falls back to response.text."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "test-token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "12345")

        channel = TelegramChannel()
        event = NotificationEvent(event_type="test", data={})

        mock_response = MagicMock()
        mock_response.status_code = 502
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "<html><body>Bad Gateway</body></html>"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        channel._client = mock_client

        result = await channel.send(event)

        assert result is False
        assert "Bad Gateway" in caplog.text


class TestTelegramChannelPoll:
    """Tests for TelegramChannel.poll()."""

    @pytest.mark.asyncio
    async def test_poll_returns_none(self) -> None:
        """poll() returns None (not implemented)."""
        channel = TelegramChannel()

        result = await channel.poll()

        assert result is None


class TestTelegramChannelClose:
    """Tests for TelegramChannel.close()."""

    @pytest.mark.asyncio
    async def test_close_closes_client(self) -> None:
        """close() closes the HTTP client."""
        channel = TelegramChannel()
        mock_client = AsyncMock()
        channel._client = mock_client

        await channel.close()

        mock_client.aclose.assert_called_once()
        assert channel._client is None
