"""Telegram notification channel implementation."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from teambot.notifications.event_bus import RateLimitError
from teambot.notifications.events import NotificationEvent
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
            message = message[: self.MAX_MESSAGE_LENGTH - 20] + "\n... (truncated)"
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
            # Log error type without exposing URL (which contains token)
            logger.error(f"Telegram request error: {type(e).__name__}")
            return False

    async def poll(self) -> list[dict[str, Any]] | None:
        """Polling not implemented - returns None."""
        return None

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
