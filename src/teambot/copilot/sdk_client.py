"""Copilot SDK client wrapper for TeamBot interactive mode."""

import asyncio
import logging
import os
from typing import Any, Callable, Optional

try:
    from copilot import CopilotClient  # type: ignore
    from copilot.generated.session_events import SessionEventType  # type: ignore

    SDK_AVAILABLE = True
except ImportError:
    CopilotClient = None  # SDK not installed
    SessionEventType = None
    SDK_AVAILABLE = False


logger = logging.getLogger(__name__)


class SDKClientError(Exception):
    """Error raised by SDK client operations."""

    pass


class CopilotSDKClient:
    """Wrapper around the Copilot SDK for agent communication.

    Provides session management per agent with TeamBot-specific
    session ID prefixing for persistence across restarts.
    """

    SESSION_PREFIX = "teambot-"

    def __init__(self):
        """Initialize the SDK client wrapper."""
        self._client: Any = None
        self._sessions: dict[str, Any] = {}
        self._started = False
        self._authenticated = False

    def is_available(self) -> bool:
        """Check if the Copilot SDK is available.

        Returns:
            True if SDK is installed and can be used.
        """
        return CopilotClient is not None

    async def start(self) -> None:
        """Start the SDK client.

        Raises:
            SDKClientError: If SDK is not available.
        """
        if not self.is_available():
            raise SDKClientError("Copilot SDK not available - install github-copilot-sdk")

        self._client = CopilotClient()
        await self._client.start()
        self._started = True

        # Check authentication status
        await self._check_auth()

    async def _check_auth(self) -> None:
        """Check and store authentication status."""
        if not self._client:
            return

        try:
            status = await self._client.get_auth_status()
            self._authenticated = status.get("isAuthenticated", False)
        except Exception:
            self._authenticated = False

    def is_authenticated(self) -> bool:
        """Check if Copilot is authenticated.

        Returns:
            True if authenticated.
        """
        return self._authenticated

    async def stop(self) -> None:
        """Stop the SDK client and clean up all sessions."""
        if not self._started:
            return

        # Destroy all active sessions
        for session in self._sessions.values():
            try:
                await session.destroy()
            except Exception:
                pass  # Best effort cleanup

        self._sessions.clear()

        if self._client:
            await self._client.stop()
            self._client = None

        self._started = False

    async def get_or_create_session(self, agent_id: str) -> Any:
        """Get an existing session or create a new one for an agent.

        Args:
            agent_id: The agent identifier (e.g., 'pm', 'builder-1').

        Returns:
            The SDK session object.

        Raises:
            SDKClientError: If client is not started.
        """
        if not self._started:
            raise SDKClientError("Client not started - call start() first")

        session_id = f"{self.SESSION_PREFIX}{agent_id}"

        # Return cached session if exists
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Create new session with TeamBot prefix
        session = await self._client.create_session(
            {
                "session_id": session_id,
                "streaming": True,
            }
        )

        self._sessions[session_id] = session
        return session

    async def execute(self, agent_id: str, prompt: str, timeout: float = 120.0) -> str:
        """Execute a prompt for a specific agent.

        Uses streaming internally but returns complete response.
        The timeout parameter is kept for API compatibility but is not
        enforced when streaming is enabled.

        Args:
            agent_id: The agent identifier.
            prompt: The prompt to send.
            timeout: Timeout in seconds (kept for API compatibility).

        Returns:
            The response content from the SDK.

        Raises:
            SDKClientError: If client is not started or error occurs.
        """
        if not self._started:
            raise SDKClientError("Client not started - call start() first")

        # Check if streaming is disabled via env var
        if os.environ.get("TEAMBOT_STREAMING", "").lower() == "false":
            # Fallback to blocking mode
            session = await self.get_or_create_session(agent_id)
            try:
                response = await session.send_and_wait({"prompt": prompt, "timeout": timeout})
                return response.data.content
            except asyncio.TimeoutError:
                raise SDKClientError(f"Request timed out after {timeout}s")
            except Exception as e:
                raise SDKClientError(f"SDK error: {e}")

        # Use streaming (default)
        return await self.execute_streaming(agent_id, prompt, on_chunk=lambda _: None)

    async def execute_streaming(
        self,
        agent_id: str,
        prompt: str,
        on_chunk: Callable[[str], None] | None = None,
    ) -> str:
        """Execute a prompt with streaming output.

        Sends prompt and streams response chunks via callback.
        Does not timeout - runs until completion or cancellation.

        Args:
            agent_id: The agent identifier.
            prompt: The prompt to send.
            on_chunk: Optional callback invoked for each streaming chunk.

        Returns:
            Complete accumulated response content.

        Raises:
            SDKClientError: If client is not started or error occurs.
        """
        if not self._started:
            raise SDKClientError("Client not started - call start() first")

        session = await self.get_or_create_session(agent_id)

        accumulated: list[str] = []
        done = asyncio.Event()
        error_holder: list[Optional[Exception]] = [None]

        def on_event(event):
            """Handle streaming events from SDK."""
            event_type = event.type

            # Normalize event type to string for comparison
            event_type_str = str(event_type)
            if hasattr(event_type, "value"):
                event_type_str = str(event_type.value)
            elif hasattr(event_type, "name"):
                event_type_str = str(event_type.name)

            # Normalize to uppercase for comparison
            event_type_upper = event_type_str.upper().replace(".", "_").replace("-", "_")

            logger.debug(f"SDK event received: {event_type} -> normalized: {event_type_upper}")

            # Check specifically for ASSISTANT_MESSAGE_DELTA (not REASONING_DELTA)
            if "ASSISTANT_MESSAGE_DELTA" in event_type_upper:
                # Extract delta content
                delta_content = getattr(event.data, "delta_content", None)
                if delta_content is None:
                    delta_content = getattr(event.data, "content", None)
                if delta_content is None:
                    delta_content = getattr(event.data, "text", None)

                if delta_content:  # Skip None or empty
                    accumulated.append(delta_content)
                    if on_chunk:
                        on_chunk(delta_content)
                    logger.debug(f"Chunk received: {delta_content[:50]}...")

            # Check for completion events
            elif "SESSION_IDLE" in event_type_upper:
                logger.debug("Session idle/complete - finishing")
                done.set()

            # Check for error events
            elif "SESSION_ERROR" in event_type_upper or "ERROR" in event_type_upper:
                error_type = getattr(event.data, "error_type", "Unknown")
                message = getattr(event.data, "message", "Unknown error")
                logger.error(f"SDK error: {error_type}: {message}")
                error_holder[0] = SDKClientError(f"{error_type}: {message}")
                done.set()

            # Check for abort events
            elif "ABORT" in event_type_upper:
                logger.debug("Request aborted")
                error_holder[0] = SDKClientError("Request aborted")
                done.set()

        # Subscribe to events
        unsubscribe = session.on(on_event)

        try:
            # Send prompt (non-blocking)
            logger.debug(f"Sending prompt to {agent_id}: {prompt[:50]}...")
            await session.send({"prompt": prompt})

            # Wait for completion with a very long timeout (30 min)
            # This is a safety net - streaming should complete naturally
            logger.debug("Waiting for completion...")
            try:
                await asyncio.wait_for(done.wait(), timeout=1800.0)  # 30 min max
            except asyncio.TimeoutError:
                logger.warning(f"Streaming timeout after 30 minutes for {agent_id}")
                raise SDKClientError("Streaming timeout - no completion event received")

            logger.debug(f"Done waiting, accumulated {len(accumulated)} chunks")

            # Check for errors
            if error_holder[0]:
                raise error_holder[0]

            return "".join(accumulated)

        finally:
            # Always unsubscribe to prevent memory leaks
            unsubscribe()

    async def cancel_current_request(self, agent_id: str) -> bool:
        """Cancel the current request for an agent.

        Uses session.abort() to stop the in-progress request.
        The session remains valid for future requests.

        Args:
            agent_id: The agent identifier.

        Returns:
            True if request was cancelled, False if no session or error.
        """
        session_id = f"{self.SESSION_PREFIX}{agent_id}"
        session = self._sessions.get(session_id)

        if not session:
            return False

        try:
            await session.abort()
            return True
        except Exception:
            return False

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions known to the SDK.

        Returns:
            List of session info dicts.
        """
        if not self._client:
            return []

        return self._client.list_sessions()
