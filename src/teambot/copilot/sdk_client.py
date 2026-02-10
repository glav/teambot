"""Copilot SDK client wrapper for TeamBot interactive mode."""

import asyncio
import logging
import os
from collections.abc import Callable
from typing import Any

from teambot.copilot.agent_loader import get_agent_loader

try:
    from copilot import CopilotClient  # type: ignore
    from copilot.generated.session_events import SessionEventType  # type: ignore

    SDK_AVAILABLE = True
except ImportError:
    CopilotClient = None  # SDK not installed
    SessionEventType = None
    SDK_AVAILABLE = False


logger = logging.getLogger(__name__)


def resolve_model(
    inline_model: str | None,
    session_overrides: dict[str, str],
    agent_id: str,
    config: dict[str, Any],
) -> str | None:
    """Resolve which model to use for an agent task.

    Priority (highest to lowest):
    1. Inline override (--model flag)
    2. Session override (/model command)
    3. Agent config (teambot.json agent.model)
    4. Global default (teambot.json default_model)
    5. None (use SDK default)

    Args:
        inline_model: Model specified in command (--model).
        session_overrides: Dict of agent_id -> model for session.
        agent_id: Agent identifier.
        config: TeamBot configuration dict.

    Returns:
        Resolved model name, or None to use SDK default.
    """
    # Priority 1: Inline override
    if inline_model:
        return inline_model

    # Priority 2: Session override
    if agent_id in session_overrides:
        return session_overrides[agent_id]

    # Priority 3: Agent config
    for agent in config.get("agents", []):
        if agent.get("id") == agent_id:
            if agent.get("model"):
                return agent["model"]
            break

    # Priority 4: Global default
    if config.get("default_model"):
        return config["default_model"]

    # Priority 5: SDK default
    return None


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

        self._ensure_binary_executable()
        self._client = CopilotClient()
        await self._client.start()
        self._started = True

        # Check authentication status
        await self._check_auth()

    @staticmethod
    def _ensure_binary_executable() -> None:
        """Ensure the bundled SDK binary has execute permission.

        Some SDK versions ship without the execute bit set on the
        bundled CLI binary, causing PermissionError on start.
        """
        import stat
        from pathlib import Path

        try:
            import copilot as _copilot_pkg

            pkg_dir = Path(_copilot_pkg.__file__).parent
            binary = pkg_dir / "bin" / "copilot"
            if binary.exists() and not os.access(binary, os.X_OK):
                binary.chmod(binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                logger.info(f"Fixed execute permission on SDK binary: {binary}")
        except Exception:
            pass  # Best effort — will fail with original PermissionError if needed

    async def _check_auth(self) -> None:
        """Check and store authentication status."""
        if not self._client:
            return

        try:
            status = await self._client.get_auth_status()
            # Handle both dict (test mocks) and dataclass (real SDK) responses
            if isinstance(status, dict):
                self._authenticated = status.get("isAuthenticated", False)
            else:
                self._authenticated = getattr(status, "isAuthenticated", False)
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

    async def get_or_create_session(self, agent_id: str, model: str | None = None) -> Any:
        """Get an existing session or create a new one for an agent.

        Configures the session with the agent's custom persona from
        .github/agents/{agent_id}.agent.md if available.

        Args:
            agent_id: The agent identifier (e.g., 'pm', 'builder-1').
            model: Optional model to use for this session.

        Returns:
            The SDK session object.

        Raises:
            SDKClientError: If client is not started.
        """
        if not self._started:
            raise SDKClientError("Client not started - call start() first")

        session_id = f"{self.SESSION_PREFIX}{agent_id}"

        # Return cached session if exists AND model matches
        if session_id in self._sessions:
            existing = self._sessions[session_id]
            # If model changed, destroy old session and create new one
            if model and getattr(existing, "_model", None) != model:
                try:
                    await existing.destroy()
                except Exception:
                    pass  # Best effort cleanup
                del self._sessions[session_id]
            else:
                return existing

        # Load agent definition from .github/agents/
        loader = get_agent_loader()
        agent_def = loader.get_agent(agent_id)

        # Build session config
        session_config: dict[str, Any] = {
            "session_id": session_id,
            "streaming": True,
        }

        # Add model if specified
        if model:
            session_config["model"] = model

        # Add custom agent definition if available
        if agent_def:
            session_config["custom_agents"] = [
                {
                    "name": agent_id,
                    "display_name": agent_def.display_name,
                    "description": agent_def.description,
                    "prompt": agent_def.prompt,
                }
            ]
            logger.info(f"Configured session with custom agent '{agent_id}'")
        else:
            logger.warning(f"No agent definition found for '{agent_id}', using defaults")

        session = await self._client.create_session(session_config)

        # Track model for cache invalidation
        session._model = model

        self._sessions[session_id] = session
        return session

    def _invalidate_session(self, agent_id: str) -> None:
        """Remove a cached session so it will be recreated on next use.

        Args:
            agent_id: The agent identifier.
        """
        session_id = f"{self.SESSION_PREFIX}{agent_id}"
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Invalidated stale session for '{agent_id}'")

    @staticmethod
    def _is_session_not_found(error: Exception) -> bool:
        """Check if an error indicates a stale/expired server-side session."""
        msg = str(error).lower()
        return "session not found" in msg

    def _build_prompt_with_persona(self, agent_id: str, user_prompt: str) -> str:
        """Build a prompt that includes the agent's persona context.

        Since the SDK doesn't reliably use custom_agents, we prepend
        the agent's persona to every prompt to ensure the LLM knows
        its identity and constraints.

        Args:
            agent_id: The agent identifier.
            user_prompt: The user's original prompt.

        Returns:
            Combined prompt with persona context.
        """
        loader = get_agent_loader()
        agent_def = loader.get_agent(agent_id)

        if not agent_def or not agent_def.prompt:
            return user_prompt

        # Prepend persona as system-like context
        return f"""<persona>
{agent_def.prompt}
</persona>

User request: {user_prompt}"""

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
            # Fallback to blocking mode - inject persona here
            full_prompt = self._build_prompt_with_persona(agent_id, prompt)
            try:
                session = await self.get_or_create_session(agent_id)
                response = await session.send_and_wait({"prompt": full_prompt, "timeout": timeout})
                return response.data.content
            except TimeoutError as e:
                raise SDKClientError(f"Request timed out after {timeout}s") from e
            except Exception as e:
                if self._is_session_not_found(e):
                    logger.warning(f"Session expired for '{agent_id}', recreating and retrying")
                    self._invalidate_session(agent_id)
                    try:
                        session = await self.get_or_create_session(agent_id)
                        response = await session.send_and_wait(
                            {"prompt": full_prompt, "timeout": timeout}
                        )
                        return response.data.content
                    except Exception as retry_e:
                        raise SDKClientError(f"SDK error: {retry_e}") from retry_e
                raise SDKClientError(f"SDK error: {e}") from e

        # Use streaming (default) - persona injection happens in execute_streaming
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
        Automatically retries once with a fresh session if the server
        reports the session as expired/not found.

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

        try:
            return await self._execute_streaming_once(agent_id, prompt, on_chunk)
        except SDKClientError as e:
            if self._is_session_not_found(e):
                logger.warning(f"Session expired for '{agent_id}', recreating and retrying")
                self._invalidate_session(agent_id)
                return await self._execute_streaming_once(agent_id, prompt, on_chunk)
            raise

    async def _execute_streaming_once(
        self,
        agent_id: str,
        prompt: str,
        on_chunk: Callable[[str], None] | None = None,
    ) -> str:
        """Execute a single streaming attempt (no retry)."""
        session = await self.get_or_create_session(agent_id)

        # Inject agent persona into the prompt
        full_prompt = self._build_prompt_with_persona(agent_id, prompt)

        accumulated: list[str] = []
        done = asyncio.Event()
        error_holder: list[Exception | None] = [None]

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
            # Send prompt with persona context (non-blocking)
            logger.debug(f"Sending prompt to {agent_id}: {prompt[:50]}...")
            try:
                await session.send({"prompt": full_prompt})
            except Exception as e:
                raise SDKClientError(f"Send failed: {e}") from e

            # Wait for completion with a very long timeout (30 min)
            # This is a safety net - streaming should complete naturally
            logger.debug("Waiting for completion...")
            try:
                await asyncio.wait_for(done.wait(), timeout=1800.0)  # 30 min max
            except TimeoutError as e:
                logger.warning(f"Streaming timeout after 30 minutes for {agent_id}")
                raise SDKClientError("Streaming timeout - no completion event received") from e

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

    def list_sessions(self) -> list[Any]:
        """List all sessions known to the SDK.

        Returns:
            List of session info objects.
        """
        if not self._client:
            return []

        return self._client.list_sessions()
