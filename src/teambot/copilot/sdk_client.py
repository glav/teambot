"""Copilot SDK client wrapper for TeamBot interactive mode."""

import asyncio
from typing import Any

try:
    from copilot import CopilotClient  # type: ignore
except ImportError:
    CopilotClient = None  # SDK not installed


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

        Args:
            agent_id: The agent identifier.
            prompt: The prompt to send.
            timeout: Timeout in seconds (default 120s).

        Returns:
            The response content from the SDK.

        Raises:
            SDKClientError: If client is not started or timeout occurs.
        """
        if not self._started:
            raise SDKClientError("Client not started - call start() first")

        session = await self.get_or_create_session(agent_id)
        try:
            response = await session.send_and_wait({"prompt": prompt, "timeout": timeout})
            return response.data.content
        except asyncio.TimeoutError:
            raise SDKClientError(f"Request timed out after {timeout}s")
        except Exception as e:
            raise SDKClientError(f"SDK error: {e}")

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions known to the SDK.

        Returns:
            List of session info dicts.
        """
        if not self._client:
            return []

        return self._client.list_sessions()
