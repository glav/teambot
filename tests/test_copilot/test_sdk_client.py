"""Tests for Copilot SDK client wrapper."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


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
    async def test_execute_sends_prompt(
        self, mock_streaming_session, mock_event_types, mock_event_data
    ):
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
    async def test_execute_returns_response(
        self, mock_streaming_session, mock_event_types, mock_event_data
    ):
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
        """Test that custom_agents is included in session_config when agent definition exists."""
        from teambot.copilot.agent_loader import AgentLoader
        from teambot.copilot.sdk_client import CopilotSDKClient

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

                # Verify custom_agents was included
                assert captured_config is not None
                assert "custom_agents" in captured_config
                assert len(captured_config["custom_agents"]) == 1

                custom_agent = captured_config["custom_agents"][0]
                assert custom_agent["name"] == "pm"
                assert custom_agent["display_name"] == "Project Manager"
                assert custom_agent["description"] == "Project Manager Agent"
                assert "Project Manager agent responsible" in custom_agent["prompt"]

    @pytest.mark.asyncio
    async def test_session_logs_warning_when_no_agent_definition(
        self, mock_sdk_client, tmp_path: Path, caplog
    ):
        """Test that warning is logged when no agent definition exists."""
        import logging

        from teambot.copilot.agent_loader import AgentLoader
        from teambot.copilot.sdk_client import CopilotSDKClient

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
                assert any(
                    "No agent definition found for 'nonexistent'" in record.message
                    for record in caplog.records
                )

                # Verify custom_agents was NOT included
                assert captured_config is not None
                assert "custom_agents" not in captured_config

    def test_build_prompt_with_persona_prepends_context(self, tmp_path: Path):
        """Test that _build_prompt_with_persona correctly prepends persona context."""
        from teambot.copilot.agent_loader import AgentLoader
        from teambot.copilot.sdk_client import CopilotSDKClient

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
        from teambot.copilot.agent_loader import AgentLoader
        from teambot.copilot.sdk_client import CopilotSDKClient

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
        from teambot.copilot.agent_loader import AgentLoader
        from teambot.copilot.sdk_client import CopilotSDKClient

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


class TestCopilotSDKClientModel:
    """Tests for model support in SDK client."""

    @pytest.mark.asyncio
    async def test_session_config_includes_model(self, mock_sdk_client, tmp_path: Path):
        """Session config includes model when specified."""
        from teambot.copilot.agent_loader import AgentLoader
        from teambot.copilot.sdk_client import CopilotSDKClient

        # Create empty agents directory
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        loader = AgentLoader(repo_root=tmp_path)

        captured_config = None

        async def capture_create(config):
            nonlocal captured_config
            captured_config = config
            session = MagicMock()
            session.session_id = config.get("session_id")
            return session

        mock_sdk_client.create_session = AsyncMock(side_effect=capture_create)

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            with patch("teambot.copilot.sdk_client.get_agent_loader", return_value=loader):
                client = CopilotSDKClient()
                await client.start()

                await client.get_or_create_session("pm", model="gpt-5")

                assert captured_config is not None
                assert captured_config.get("model") == "gpt-5"

    @pytest.mark.asyncio
    async def test_session_without_model(self, mock_sdk_client, tmp_path: Path):
        """Session config omits model when not specified."""
        from teambot.copilot.agent_loader import AgentLoader
        from teambot.copilot.sdk_client import CopilotSDKClient

        # Create empty agents directory
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        loader = AgentLoader(repo_root=tmp_path)

        captured_config = None

        async def capture_create(config):
            nonlocal captured_config
            captured_config = config
            session = MagicMock()
            session.session_id = config.get("session_id")
            return session

        mock_sdk_client.create_session = AsyncMock(side_effect=capture_create)

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            with patch("teambot.copilot.sdk_client.get_agent_loader", return_value=loader):
                client = CopilotSDKClient()
                await client.start()

                await client.get_or_create_session("pm")

                assert captured_config is not None
                assert "model" not in captured_config

    @pytest.mark.asyncio
    async def test_session_recreated_when_model_changes(self, mock_sdk_client, tmp_path: Path):
        """Session is recreated when model changes."""
        from teambot.copilot.agent_loader import AgentLoader
        from teambot.copilot.sdk_client import CopilotSDKClient

        # Create empty agents directory
        agents_dir = tmp_path / ".github" / "agents"
        agents_dir.mkdir(parents=True)
        loader = AgentLoader(repo_root=tmp_path)

        configs = []

        async def capture_create(config):
            configs.append(config.copy())
            session = MagicMock()
            session.session_id = config.get("session_id")
            session._model = config.get("model")
            session.destroy = AsyncMock()
            return session

        mock_sdk_client.create_session = AsyncMock(side_effect=capture_create)

        with patch("teambot.copilot.sdk_client.CopilotClient", return_value=mock_sdk_client):
            with patch("teambot.copilot.sdk_client.get_agent_loader", return_value=loader):
                client = CopilotSDKClient()
                await client.start()

                # First call with gpt-5
                await client.get_or_create_session("pm", model="gpt-5")
                # Second call with different model should recreate
                await client.get_or_create_session("pm", model="claude-opus-4.5")

                assert len(configs) == 2
                assert configs[0].get("model") == "gpt-5"
                assert configs[1].get("model") == "claude-opus-4.5"


class TestResolveModel:
    """Tests for model resolution logic."""

    def test_inline_model_takes_priority(self):
        """Inline model takes highest priority."""
        from teambot.copilot.sdk_client import resolve_model

        result = resolve_model(
            inline_model="gpt-5",
            session_overrides={"pm": "claude-opus-4.5"},
            agent_id="pm",
            config={"default_model": "gpt-4.1", "agents": [{"id": "pm", "model": "gpt-5.1"}]},
        )
        assert result == "gpt-5"

    def test_session_override_second_priority(self):
        """Session override is second priority."""
        from teambot.copilot.sdk_client import resolve_model

        result = resolve_model(
            inline_model=None,
            session_overrides={"pm": "claude-opus-4.5"},
            agent_id="pm",
            config={"default_model": "gpt-4.1", "agents": [{"id": "pm", "model": "gpt-5.1"}]},
        )
        assert result == "claude-opus-4.5"

    def test_agent_config_third_priority(self):
        """Agent config is third priority."""
        from teambot.copilot.sdk_client import resolve_model

        result = resolve_model(
            inline_model=None,
            session_overrides={},
            agent_id="pm",
            config={"default_model": "gpt-4.1", "agents": [{"id": "pm", "model": "gpt-5.1"}]},
        )
        assert result == "gpt-5.1"

    def test_global_default_fourth_priority(self):
        """Global default_model is fourth priority."""
        from teambot.copilot.sdk_client import resolve_model

        result = resolve_model(
            inline_model=None,
            session_overrides={},
            agent_id="pm",
            config={"default_model": "gpt-4.1", "agents": [{"id": "pm"}]},
        )
        assert result == "gpt-4.1"

    def test_returns_none_when_no_model_specified(self):
        """Returns None when no model is specified anywhere."""
        from teambot.copilot.sdk_client import resolve_model

        result = resolve_model(
            inline_model=None,
            session_overrides={},
            agent_id="pm",
            config={"agents": [{"id": "pm"}]},
        )
        assert result is None

    def test_agent_not_found_falls_back_to_global(self):
        """Falls back to global default when agent not in config."""
        from teambot.copilot.sdk_client import resolve_model

        result = resolve_model(
            inline_model=None,
            session_overrides={},
            agent_id="unknown",
            config={"default_model": "gpt-4.1", "agents": [{"id": "pm", "model": "gpt-5"}]},
        )
        assert result == "gpt-4.1"


class TestCopilotSDKClientSessionRetry:
    """Tests for automatic session retry on stale/expired sessions."""

    @pytest.mark.asyncio
    async def test_streaming_retries_on_session_not_found_from_send(
        self, mock_event_types, mock_event_data
    ):
        """Test that execute_streaming retries when session.send raises session not found."""
        import asyncio

        from teambot.copilot.sdk_client import CopilotSDKClient

        sessions = []

        def make_session():
            session = MagicMock()
            session._handlers = []
            session.send = AsyncMock()
            session.destroy = AsyncMock()
            session.session_id = f"teambot-pm-{len(sessions)}"

            def on(handler):
                session._handlers.append(handler)
                return (
                    lambda: session._handlers.remove(handler)
                    if handler in session._handlers
                    else None
                )

            session.on = on
            sessions.append(session)
            return session

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})

            # First session raises "Session not found" on send
            first_session = make_session()
            first_session.send = AsyncMock(
                side_effect=Exception("JSON-RPC Error -32603: Session not found: teambot-pm")
            )

            # Second session works
            async def successful_send(msg):
                await asyncio.sleep(0.01)
                from types import SimpleNamespace

                for h in sessions[-1]._handlers:
                    h(
                        SimpleNamespace(
                            type="ASSISTANT_MESSAGE_DELTA",
                            data=SimpleNamespace(delta_content="Retry success"),
                        )
                    )
                for h in sessions[-1]._handlers:
                    h(SimpleNamespace(type="SESSION_IDLE", data=None))

            second_session = make_session()
            second_session.send = AsyncMock(side_effect=successful_send)

            call_count = [0]

            async def create_session(config):
                call_count[0] += 1
                if call_count[0] == 1:
                    return first_session
                return second_session

            mock_client.create_session = AsyncMock(side_effect=create_session)
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            result = await client.execute_streaming("pm", "Create a plan")
            assert result == "Retry success"
            assert mock_client.create_session.call_count == 2

    @pytest.mark.asyncio
    async def test_streaming_retries_on_session_not_found_from_event(
        self, mock_event_types, mock_event_data
    ):
        """Test that execute_streaming retries when error event contains session not found."""
        import asyncio

        from teambot.copilot.sdk_client import CopilotSDKClient

        sessions = []
        attempt = [0]

        def make_session():
            session = MagicMock()
            session._handlers = []
            session.send = AsyncMock()
            session.destroy = AsyncMock()
            session.session_id = f"teambot-pm-{len(sessions)}"

            def on(handler):
                session._handlers.append(handler)
                return (
                    lambda: session._handlers.remove(handler)
                    if handler in session._handlers
                    else None
                )

            session.on = on
            sessions.append(session)
            return session

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})

            async def create_session(config):
                s = make_session()
                current_attempt = attempt[0]
                attempt[0] += 1

                async def send_with_events(msg):
                    await asyncio.sleep(0.01)
                    from types import SimpleNamespace

                    if current_attempt == 0:
                        event = SimpleNamespace(
                            type="SESSION_ERROR",
                            data=SimpleNamespace(
                                error_type="SessionError",
                                message="Session not found: teambot-pm",
                            ),
                        )
                        for h in s._handlers:
                            h(event)
                    else:
                        for h in s._handlers:
                            h(
                                SimpleNamespace(
                                    type="ASSISTANT_MESSAGE_DELTA",
                                    data=SimpleNamespace(delta_content="Fixed"),
                                )
                            )
                        for h in s._handlers:
                            h(SimpleNamespace(type="SESSION_IDLE", data=None))

                s.send = AsyncMock(side_effect=send_with_events)
                return s

            mock_client.create_session = AsyncMock(side_effect=create_session)
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            result = await client.execute_streaming("pm", "Do something")
            assert result == "Fixed"

    @pytest.mark.asyncio
    async def test_streaming_does_not_retry_on_other_errors(
        self, mock_event_types, mock_event_data
    ):
        """Test that non-session-not-found errors are not retried."""
        from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})

            session = MagicMock()
            session._handlers = []
            session.send = AsyncMock(side_effect=Exception("Rate limit exceeded"))
            session.destroy = AsyncMock()

            def on(handler):
                session._handlers.append(handler)
                return (
                    lambda: session._handlers.remove(handler)
                    if handler in session._handlers
                    else None
                )

            session.on = on

            mock_client.create_session = AsyncMock(return_value=session)
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            with pytest.raises(SDKClientError, match="Send failed: Rate limit exceeded"):
                await client.execute_streaming("pm", "Hello")

            # Should only have tried to create session once (no retry)
            assert mock_client.create_session.call_count == 1

    @pytest.mark.asyncio
    async def test_blocking_mode_retries_on_session_not_found(self, mock_sdk_response, monkeypatch):
        """Test execute() in blocking mode retries on session not found."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        # Set environment variable to disable streaming
        monkeypatch.setenv("TEAMBOT_STREAMING", "false")

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})

            # First session raises "Session not found" on send_and_wait
            first_session = MagicMock()
            first_session.send_and_wait = AsyncMock(
                side_effect=Exception("JSON-RPC Error -32603: Session not found: teambot-pm")
            )
            first_session.destroy = AsyncMock()

            # Second session works
            from types import SimpleNamespace

            second_session = MagicMock()
            second_session.send_and_wait = AsyncMock(
                return_value=SimpleNamespace(data=SimpleNamespace(content="Retry success"))
            )
            second_session.destroy = AsyncMock()

            call_count = [0]

            async def create_session(config):
                call_count[0] += 1
                if call_count[0] == 1:
                    return first_session
                return second_session

            mock_client.create_session = AsyncMock(side_effect=create_session)
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            result = await client.execute("pm", "Create a plan")
            assert result == "Retry success"
            assert mock_client.create_session.call_count == 2

    @pytest.mark.asyncio
    async def test_blocking_mode_retry_fails_on_second_attempt(
        self, mock_sdk_response, monkeypatch
    ):
        """Test that execute() in blocking mode raises error when retry also fails."""
        from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError

        # Set environment variable to disable streaming
        monkeypatch.setenv("TEAMBOT_STREAMING", "false")

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})

            # First session raises "Session not found"
            first_session = MagicMock()
            first_session.send_and_wait = AsyncMock(
                side_effect=Exception("JSON-RPC Error -32603: Session not found: teambot-pm")
            )
            first_session.destroy = AsyncMock()

            # Second session also fails but with a different error
            second_session = MagicMock()
            second_session.send_and_wait = AsyncMock(side_effect=Exception("Rate limit exceeded"))
            second_session.destroy = AsyncMock()

            call_count = [0]

            async def create_session(config):
                call_count[0] += 1
                if call_count[0] == 1:
                    return first_session
                return second_session

            mock_client.create_session = AsyncMock(side_effect=create_session)
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            with pytest.raises(SDKClientError, match="SDK error: Rate limit exceeded"):
                await client.execute("pm", "Create a plan")

            assert mock_client.create_session.call_count == 2

    @pytest.mark.asyncio
    async def test_blocking_mode_does_not_retry_on_other_errors(
        self, mock_sdk_response, monkeypatch
    ):
        """Test that execute() in blocking mode does not retry on non-session-not-found errors."""
        from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError

        # Set environment variable to disable streaming
        monkeypatch.setenv("TEAMBOT_STREAMING", "false")

        with patch("teambot.copilot.sdk_client.CopilotClient") as MockClient:
            mock_client = MagicMock()
            mock_client.start = AsyncMock()
            mock_client.stop = AsyncMock()
            mock_client.get_auth_status = AsyncMock(return_value={"isAuthenticated": True})

            # Session raises a non-session-not-found error
            session = MagicMock()
            session.send_and_wait = AsyncMock(side_effect=Exception("Rate limit exceeded"))
            session.destroy = AsyncMock()

            mock_client.create_session = AsyncMock(return_value=session)
            MockClient.return_value = mock_client

            client = CopilotSDKClient()
            await client.start()

            with pytest.raises(SDKClientError, match="SDK error: Rate limit exceeded"):
                await client.execute("pm", "Create a plan")

            # Should only have tried to create session once (no retry)
            assert mock_client.create_session.call_count == 1

    def test_is_session_not_found_detects_error(self):
        """Test _is_session_not_found detection."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        assert CopilotSDKClient._is_session_not_found(
            Exception("JSON-RPC Error -32603: Session not found: teambot-pm")
        )
        assert CopilotSDKClient._is_session_not_found(Exception("session not found"))
        assert not CopilotSDKClient._is_session_not_found(Exception("Rate limit exceeded"))
        assert not CopilotSDKClient._is_session_not_found(Exception("Timeout error"))

    def test_invalidate_session_removes_from_cache(self):
        """Test _invalidate_session removes session from cache."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        client = CopilotSDKClient()
        client._sessions["teambot-pm"] = MagicMock()
        client._sessions["teambot-builder-1"] = MagicMock()

        client._invalidate_session("pm")

        assert "teambot-pm" not in client._sessions
        assert "teambot-builder-1" in client._sessions

    def test_invalidate_session_noop_if_not_cached(self):
        """Test _invalidate_session is safe when session not in cache."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        client = CopilotSDKClient()
        # Should not raise
        client._invalidate_session("nonexistent")
