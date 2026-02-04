"""TDD tests for SDK streaming execution.

These tests define the streaming behavior contract.
Write these BEFORE implementation (TDD).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestExecuteStreaming:
    """Tests for execute_streaming method."""

    @pytest.mark.asyncio
    async def test_receives_delta_events(
        self, mock_streaming_session, mock_event_types, mock_event_data
    ):
        """Verify on_chunk callback receives each delta."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        # Track chunks received
        chunks_received = []

        def on_chunk(chunk):
            chunks_received.append(chunk)

        # Create client with mock
        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            # Schedule events to fire after send() is called
            async def fire_events():
                await asyncio.sleep(0.01)  # Let execute_streaming set up
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("Hello "),
                )
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("World!"),
                )
                mock_streaming_session.fire_event(mock_event_types.SESSION_IDLE, None)

            asyncio.create_task(fire_events())

            result = await client.execute_streaming("pm", "Test prompt", on_chunk)

            assert chunks_received == ["Hello ", "World!"]
            assert result == "Hello World!"

    @pytest.mark.asyncio
    async def test_completes_on_session_idle(
        self, mock_streaming_session, mock_event_types, mock_event_data
    ):
        """Verify streaming completes when SESSION_IDLE received."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            async def fire_events():
                await asyncio.sleep(0.01)
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("Done"),
                )
                mock_streaming_session.fire_event(mock_event_types.SESSION_IDLE, None)

            asyncio.create_task(fire_events())

            result = await client.execute_streaming("pm", "Test", lambda _: None)

            # Should complete and return accumulated content
            assert result == "Done"

    @pytest.mark.asyncio
    async def test_handles_session_error(
        self, mock_streaming_session, mock_event_types, mock_event_data
    ):
        """Verify SESSION_ERROR raises SDKClientError."""
        from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            async def fire_error():
                await asyncio.sleep(0.01)
                mock_streaming_session.fire_event(
                    mock_event_types.SESSION_ERROR,
                    mock_event_data.error("TestError", "Something went wrong"),
                )

            asyncio.create_task(fire_error())

            with pytest.raises(SDKClientError, match="TestError"):
                await client.execute_streaming("pm", "Test", lambda _: None)

    @pytest.mark.asyncio
    async def test_accumulates_content(
        self, mock_streaming_session, mock_event_types, mock_event_data
    ):
        """Verify all chunks accumulated into return value."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            async def fire_events():
                await asyncio.sleep(0.01)
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("A"),
                )
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("B"),
                )
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("C"),
                )
                mock_streaming_session.fire_event(mock_event_types.SESSION_IDLE, None)

            asyncio.create_task(fire_events())

            result = await client.execute_streaming("pm", "Test", lambda _: None)

            assert result == "ABC"

    @pytest.mark.asyncio
    async def test_unsubscribes_on_complete(
        self, mock_streaming_session, mock_event_types, mock_event_data
    ):
        """Verify event listener unsubscribed after completion."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            # Check handlers before
            assert len(mock_streaming_session._handlers) == 0

            async def fire_events():
                await asyncio.sleep(0.01)
                # Handler should be registered now
                assert len(mock_streaming_session._handlers) == 1
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("Done"),
                )
                mock_streaming_session.fire_event(mock_event_types.SESSION_IDLE, None)

            asyncio.create_task(fire_events())

            await client.execute_streaming("pm", "Test", lambda _: None)

            # Handler should be unsubscribed after completion
            assert len(mock_streaming_session._handlers) == 0

    @pytest.mark.asyncio
    async def test_unsubscribes_on_error(
        self, mock_streaming_session, mock_event_types, mock_event_data
    ):
        """Verify event listener unsubscribed even on error."""
        from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            async def fire_error():
                await asyncio.sleep(0.01)
                mock_streaming_session.fire_event(
                    mock_event_types.SESSION_ERROR,
                    mock_event_data.error("Error", "Failed"),
                )

            asyncio.create_task(fire_error())

            with pytest.raises(SDKClientError):
                await client.execute_streaming("pm", "Test", lambda _: None)

            # Handler should still be unsubscribed
            assert len(mock_streaming_session._handlers) == 0

    @pytest.mark.asyncio
    async def test_filters_empty_deltas(
        self, mock_streaming_session, mock_event_types, mock_event_data
    ):
        """Verify None or empty delta_content is skipped."""
        from types import SimpleNamespace

        from teambot.copilot.sdk_client import CopilotSDKClient

        chunks_received = []

        def on_chunk(chunk):
            chunks_received.append(chunk)

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            async def fire_events():
                await asyncio.sleep(0.01)
                # Valid chunk
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("A"),
                )
                # Empty string chunk - should be skipped
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta(""),
                )
                # None delta_content - should be skipped
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    SimpleNamespace(delta_content=None, message_id="msg-123"),
                )
                # Valid chunk
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("B"),
                )
                mock_streaming_session.fire_event(mock_event_types.SESSION_IDLE, None)

            asyncio.create_task(fire_events())

            result = await client.execute_streaming("pm", "Test", on_chunk)

            # Only non-empty chunks should be received
            assert chunks_received == ["A", "B"]
            assert result == "AB"

    @pytest.mark.asyncio
    async def test_handles_abort_event(
        self, mock_streaming_session, mock_event_types, mock_event_data
    ):
        """Verify ABORT event is handled gracefully."""
        from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            async def fire_abort():
                await asyncio.sleep(0.01)
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("Partial"),
                )
                mock_streaming_session.fire_event(mock_event_types.ABORT, None)

            asyncio.create_task(fire_abort())

            with pytest.raises(SDKClientError, match="aborted"):
                await client.execute_streaming("pm", "Test", lambda _: None)


class TestBackwardCompatibility:
    """Tests for backward compatible execute()."""

    @pytest.mark.asyncio
    async def test_execute_returns_complete_response(
        self, mock_streaming_session, mock_event_types, mock_event_data
    ):
        """Verify execute() returns complete response using streaming internally."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            async def fire_events():
                await asyncio.sleep(0.01)
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("Hello "),
                )
                mock_streaming_session.fire_event(
                    mock_event_types.ASSISTANT_MESSAGE_DELTA,
                    mock_event_data.delta("World!"),
                )
                mock_streaming_session.fire_event(mock_event_types.SESSION_IDLE, None)

            asyncio.create_task(fire_events())

            # Use old execute() API
            result = await client.execute("pm", "Test prompt")

            assert result == "Hello World!"

    @pytest.mark.asyncio
    async def test_execute_api_signature_unchanged(self):
        """Verify execute() has same signature as before."""
        import inspect

        from teambot.copilot.sdk_client import CopilotSDKClient

        sig = inspect.signature(CopilotSDKClient.execute)
        params = list(sig.parameters.keys())

        # Should have: self, agent_id, prompt, timeout
        assert "agent_id" in params
        assert "prompt" in params
        assert "timeout" in params


class TestCancelRequest:
    """Tests for cancel_current_request."""

    @pytest.mark.asyncio
    async def test_cancel_calls_abort(self, mock_streaming_session):
        """Verify cancel calls session.abort()."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            # Create a session first
            await client.get_or_create_session("pm")

            # Cancel
            result = await client.cancel_current_request("pm")

            assert result is True
            mock_streaming_session.abort.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_returns_true_on_success(self, mock_streaming_session):
        """Verify cancel returns True when aborted."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()
            await client.get_or_create_session("pm")

            result = await client.cancel_current_request("pm")

            assert result is True

    @pytest.mark.asyncio
    async def test_cancel_returns_false_no_session(self):
        """Verify cancel returns False if no session exists."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            # No session created for "unknown"
            result = await client.cancel_current_request("unknown")

            assert result is False

    @pytest.mark.asyncio
    async def test_cancel_handles_abort_exception(self, mock_streaming_session):
        """Verify cancel handles exceptions gracefully."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        mock_streaming_session.abort = AsyncMock(side_effect=Exception("Abort failed"))

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.create_session = AsyncMock(return_value=mock_streaming_session)
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()
            await client.get_or_create_session("pm")

            # Should return False on exception, not raise
            result = await client.cancel_current_request("pm")

            assert result is False
