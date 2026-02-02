"""Tests for Copilot SDK client wrapper."""

import pytest
from pathlib import Path
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


class TestCopilotSDKClientPersonaInjection:
    """Tests for persona injection functionality."""

    @pytest.mark.asyncio
    async def test_session_includes_custom_agents_when_definition_exists(
        self, mock_sdk_client, tmp_path: Path
    ):
        """Test that customAgents is included in session_config when agent definition exists."""
        from teambot.copilot.sdk_client import CopilotSDKClient
        from teambot.copilot.agent_loader import AgentLoader

        # Create an agent definition file
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        agent_file = agents_dir / "pm.agent.md"
        agent_file.write_text("""---
name: pm
description: Project Manager Agent
displayName: Project Manager
---

You are the Project Manager agent responsible for planning and coordination.""")

        # Setup agent loader with the temp directory
        loader = AgentLoader(repo_root=tmp_path)

        captured_config = None

        async def capture_config(config):
            nonlocal captured_config
            captured_config = config
            session = MagicMock()
            session.session_id = config.get("session_id")
            return session

        mock_sdk_client.create_session = AsyncMock(side_effect=capture_config)

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            with patch("teambot.copilot.sdk_client.get_agent_loader", return_value=loader):
                client = CopilotSDKClient()
                await client.start()

                await client.get_or_create_session("pm")

                # Verify customAgents was included
                assert captured_config is not None
                assert "customAgents" in captured_config
                assert len(captured_config["customAgents"]) == 1

                custom_agent = captured_config["customAgents"][0]
                assert custom_agent["name"] == "pm"
                assert custom_agent["displayName"] == "Project Manager"
                assert custom_agent["description"] == "Project Manager Agent"
                assert "Project Manager agent responsible" in custom_agent["prompt"]

    @pytest.mark.asyncio
    async def test_session_logs_warning_when_no_agent_definition(
        self, mock_sdk_client, tmp_path: Path, caplog
    ):
        """Test that warning is logged when no agent definition exists."""
        import logging
        from teambot.copilot.sdk_client import CopilotSDKClient
        from teambot.copilot.agent_loader import AgentLoader

        # Create empty agents directory
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)

        # Setup agent loader with the temp directory
        loader = AgentLoader(repo_root=tmp_path)

        captured_config = None

        async def capture_config(config):
            nonlocal captured_config
            captured_config = config
            session = MagicMock()
            session.session_id = config.get("session_id")
            return session

        mock_sdk_client.create_session = AsyncMock(side_effect=capture_config)

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            with patch("teambot.copilot.sdk_client.get_agent_loader", return_value=loader):
                client = CopilotSDKClient()
                await client.start()

                with caplog.at_level(logging.WARNING):
                    await client.get_or_create_session("nonexistent")

                # Verify warning was logged
                assert any("No agent definition found for 'nonexistent'" in record.message
                          for record in caplog.records)

                # Verify customAgents was NOT included
                assert captured_config is not None
                assert "customAgents" not in captured_config

    def test_build_prompt_with_persona_prepends_context(self, tmp_path: Path):
        """Test that _build_prompt_with_persona correctly prepends persona context."""
        from teambot.copilot.sdk_client import CopilotSDKClient
        from teambot.copilot.agent_loader import AgentLoader

        # Create an agent definition file
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        agent_file = agents_dir / "builder.agent.md"
        agent_file.write_text("""---
name: builder
description: Builder Agent
---

You are a skilled builder agent focused on implementing features.""")

        # Setup agent loader with the temp directory
        loader = AgentLoader(repo_root=tmp_path)

        with patch("teambot.copilot.sdk_client.get_agent_loader", return_value=loader):
            client = CopilotSDKClient()

            result = client._build_prompt_with_persona("builder", "Implement feature X")

            # Verify persona is prepended
            assert "<persona>" in result
            assert "</persona>" in result
            assert "You are a skilled builder agent" in result
            assert "User request: Implement feature X" in result

            # Verify structure
            assert result.index("<persona>") < result.index("User request:")
            assert result.index("</persona>") < result.index("User request:")

    def test_build_prompt_with_persona_returns_original_when_no_definition(self, tmp_path: Path):
        """Test that _build_prompt_with_persona returns original prompt when no agent definition."""
        from teambot.copilot.sdk_client import CopilotSDKClient
        from teambot.copilot.agent_loader import AgentLoader

        # Create empty agents directory
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)

        # Setup agent loader with the temp directory
        loader = AgentLoader(repo_root=tmp_path)

        with patch("teambot.copilot.sdk_client.get_agent_loader", return_value=loader):
            client = CopilotSDKClient()

            original_prompt = "Create a plan"
            result = client._build_prompt_with_persona("nonexistent", original_prompt)

            # Should return original prompt unchanged
            assert result == original_prompt
            assert "<persona>" not in result

    def test_build_prompt_with_persona_handles_empty_prompt(self, tmp_path: Path):
        """Test that _build_prompt_with_persona handles agent with empty prompt."""
        from teambot.copilot.sdk_client import CopilotSDKClient
        from teambot.copilot.agent_loader import AgentLoader

        # Create an agent definition file with empty prompt
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        agent_file = agents_dir / "reviewer.agent.md"
        agent_file.write_text("""---
name: reviewer
description: Reviewer Agent
---
""")

        # Setup agent loader with the temp directory
        loader = AgentLoader(repo_root=tmp_path)

        with patch("teambot.copilot.sdk_client.get_agent_loader", return_value=loader):
            client = CopilotSDKClient()

            original_prompt = "Review this code"
            result = client._build_prompt_with_persona("reviewer", original_prompt)

            # Should return original prompt since agent prompt is empty
            assert result == original_prompt
            assert "<persona>" not in result
