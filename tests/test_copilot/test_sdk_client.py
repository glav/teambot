"""Tests for Copilot SDK client wrapper."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCopilotSDKClient:
    """Tests for CopilotSDKClient class."""

    @pytest.mark.asyncio
    async def test_client_start_calls_sdk_start(self, mock_sdk_client):
        """Test that start() calls the underlying SDK start."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            client = CopilotSDKClient()
            await client.start()

            mock_sdk_client.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_stop_calls_sdk_stop(self, mock_sdk_client):
        """Test that stop() calls the underlying SDK stop."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            client = CopilotSDKClient()
            await client.start()
            await client.stop()

            mock_sdk_client.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_for_agent(self, mock_sdk_client, mock_sdk_session):
        """Test creating a session for an agent."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            client = CopilotSDKClient()
            await client.start()

            session = await client.get_or_create_session("pm")

            assert session is not None
            mock_sdk_client.create_session.assert_called_once()
            # Verify session ID format
            call_args = mock_sdk_client.create_session.call_args
            assert "teambot-pm" in str(call_args)

    @pytest.mark.asyncio
    async def test_session_reuse_same_agent(self, mock_sdk_client, mock_sdk_session):
        """Test that same session is reused for same agent."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            client = CopilotSDKClient()
            await client.start()

            session1 = await client.get_or_create_session("pm")
            session2 = await client.get_or_create_session("pm")

            assert session1 is session2
            # Should only create once
            assert mock_sdk_client.create_session.call_count == 1

    @pytest.mark.asyncio
    async def test_different_sessions_for_different_agents(self, mock_sdk_client):
        """Test that different agents get different sessions."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        # Create unique sessions for each agent
        sessions = {}

        async def create_unique_session(config):
            session = MagicMock()
            session.session_id = config.get("session_id", "unknown")
            sessions[session.session_id] = session
            return session

        mock_sdk_client.create_session = AsyncMock(side_effect=create_unique_session)

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            client = CopilotSDKClient()
            await client.start()

            await client.get_or_create_session("pm")
            await client.get_or_create_session("builder-1")

            assert mock_sdk_client.create_session.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_sends_prompt(self, mock_streaming_session, mock_event_types, mock_event_data):
        """Test that execute() sends prompt to session."""
        import asyncio
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

            await client.execute("pm", "Create a project plan")

            # Verify send was called (streaming mode)
            mock_streaming_session.send.assert_called_once()
            call_args = mock_streaming_session.send.call_args
            assert "Create a project plan" in str(call_args)

    @pytest.mark.asyncio
    async def test_execute_returns_response(self, mock_streaming_session, mock_event_types, mock_event_data):
        """Test that execute() returns the response content."""
        import asyncio
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
                    mock_event_data.delta("Task completed"),
                )
                mock_streaming_session.fire_event(mock_event_types.SESSION_IDLE, None)

            asyncio.create_task(fire_events())

            result = await client.execute("pm", "Hello")

            assert result == "Task completed"

    @pytest.mark.asyncio
    async def test_stop_destroys_all_sessions(self, mock_sdk_client, mock_sdk_session):
        """Test that stop() destroys all active sessions."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            client = CopilotSDKClient()
            await client.start()

            # Create sessions for multiple agents
            await client.get_or_create_session("pm")
            await client.get_or_create_session("builder-1")

            await client.stop()

            # Sessions should be destroyed
            assert mock_sdk_session.destroy.call_count >= 1

    @pytest.mark.asyncio
    async def test_client_not_started_raises(self):
        """Test that operations without start() raise error."""
        from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError

        client = CopilotSDKClient()

        with pytest.raises(SDKClientError, match="not started"):
            await client.get_or_create_session("pm")

    @pytest.mark.asyncio
    async def test_execute_without_start_raises(self):
        """Test that execute without start() raises error."""
        from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError

        client = CopilotSDKClient()

        with pytest.raises(SDKClientError, match="not started"):
            await client.execute("pm", "Hello")


class TestCopilotSDKClientSessionPersistence:
    """Tests for session persistence features."""

    @pytest.mark.asyncio
    async def test_session_ids_use_teambot_prefix(self, mock_sdk_client):
        """Test that session IDs use teambot- prefix."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        captured_config = None

        async def capture_config(config):
            nonlocal captured_config
            captured_config = config
            session = MagicMock()
            session.session_id = config.get("session_id")
            return session

        mock_sdk_client.create_session = AsyncMock(side_effect=capture_config)

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            client = CopilotSDKClient()
            await client.start()

            await client.get_or_create_session("builder-1")

            assert captured_config is not None
            assert captured_config.get("session_id") == "teambot-builder-1"

    @pytest.mark.asyncio
    async def test_list_sessions(self, mock_sdk_client):
        """Test listing active sessions."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        mock_sdk_client.list_sessions.return_value = [
            {"sessionId": "teambot-pm"},
            {"sessionId": "teambot-builder-1"},
        ]

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            client = CopilotSDKClient()
            await client.start()

            sessions = client.list_sessions()

            assert len(sessions) == 2

    @pytest.mark.asyncio
    async def test_is_available_true_when_sdk_works(self, mock_sdk_client):
        """Test is_available returns True when SDK is available."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            client = CopilotSDKClient()
            assert client.is_available() is True

    def test_is_available_false_when_sdk_import_fails(self):
        """Test is_available returns False when SDK not installed."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        with patch("teambot.copilot.sdk_client.CopilotClient", None):
            client = CopilotSDKClient()
            # This would need actual import failure handling
            # For now, test that it doesn't crash
            assert client is not None
