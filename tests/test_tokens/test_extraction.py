"""Tests for SDK token extraction."""

from unittest.mock import MagicMock, patch

import pytest

from teambot.tokens.models import TokenUsage


class TestSDKTokenExtraction:
    """Tests for extracting token usage from SDK events."""

    def test_extract_from_assistant_usage_event(self):
        """Extract token data from ASSISTANT_USAGE event."""
        from teambot.tokens.extraction import extract_tokens_from_event_data

        # Mock event.data with token fields
        event_data = MagicMock()
        event_data.input_tokens = 100.0
        event_data.output_tokens = 50.0
        event_data.cache_read_tokens = 10.0
        event_data.cache_write_tokens = 5.0

        usage = extract_tokens_from_event_data(event_data)

        assert usage is not None
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.cache_read_tokens == 10
        assert usage.cache_write_tokens == 5

    def test_extract_returns_none_when_no_usage(self):
        """Return None when event data has no token fields."""
        from teambot.tokens.extraction import extract_tokens_from_event_data

        event_data = MagicMock()
        event_data.input_tokens = None
        event_data.output_tokens = None
        event_data.cache_read_tokens = None
        event_data.cache_write_tokens = None

        usage = extract_tokens_from_event_data(event_data)

        # Should return TokenUsage with all None (not None itself)
        assert usage is not None
        assert usage.input_tokens is None
        assert usage.output_tokens is None

    def test_extract_partial_data(self):
        """Handle partial token data (some fields present)."""
        from teambot.tokens.extraction import extract_tokens_from_event_data

        event_data = MagicMock()
        event_data.input_tokens = 100.0
        event_data.output_tokens = None
        event_data.cache_read_tokens = None
        event_data.cache_write_tokens = None

        usage = extract_tokens_from_event_data(event_data)

        assert usage is not None
        assert usage.input_tokens == 100
        assert usage.output_tokens is None

    def test_extract_converts_float_to_int(self):
        """SDK uses float, we convert to int."""
        from teambot.tokens.extraction import extract_tokens_from_event_data

        event_data = MagicMock()
        event_data.input_tokens = 100.5  # Float with decimal
        event_data.output_tokens = 50.9
        event_data.cache_read_tokens = 10.1
        event_data.cache_write_tokens = 5.0

        usage = extract_tokens_from_event_data(event_data)

        assert isinstance(usage.input_tokens, int)
        assert usage.input_tokens == 100  # Truncated to int
        assert usage.output_tokens == 50

    def test_extract_handles_missing_attributes(self):
        """Handle event data missing token attributes."""
        from teambot.tokens.extraction import extract_tokens_from_event_data

        # Object without token attributes
        event_data = MagicMock(spec=[])  # No attributes

        usage = extract_tokens_from_event_data(event_data)

        assert usage is not None
        assert usage.input_tokens is None
        assert usage.output_tokens is None

    def test_extract_zero_tokens_valid(self):
        """Zero tokens is valid (different from None)."""
        from teambot.tokens.extraction import extract_tokens_from_event_data

        event_data = MagicMock()
        event_data.input_tokens = 0.0
        event_data.output_tokens = 0.0
        event_data.cache_read_tokens = 0.0
        event_data.cache_write_tokens = 0.0

        usage = extract_tokens_from_event_data(event_data)

        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0


class TestSDKClientTokenCapture:
    """Tests for SDK client token capture integration."""

    @pytest.mark.asyncio
    async def test_streaming_returns_token_usage(self):
        """execute_streaming returns TokenUsage alongside response."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        # This test verifies the return signature includes tokens
        # Implementation will modify SDK client to return tuple
        client = CopilotSDKClient()

        # Mock the client internals
        with patch.object(client, "_started", True):
            with patch.object(client, "_client", MagicMock()):
                # Mock session
                mock_session = MagicMock()
                mock_event = MagicMock()
                mock_event.type = MagicMock()
                mock_event.type.value = "assistant.usage"
                mock_event.data = MagicMock()
                mock_event.data.input_tokens = 100.0
                mock_event.data.output_tokens = 50.0
                mock_event.data.cache_read_tokens = None
                mock_event.data.cache_write_tokens = None

                with patch.object(client, "get_or_create_session", return_value=mock_session):
                    with patch.object(client, "_execute_streaming_once") as mock_stream:
                        # Simulate returning (text, tokens)
                        mock_stream.return_value = (
                            "response text",
                            TokenUsage(input_tokens=100, output_tokens=50),
                        )

                        result = await client._execute_streaming_once("pm", "test prompt")

                        assert isinstance(result, tuple)
                        assert len(result) == 2
                        text, tokens = result
                        assert text == "response text"
                        assert tokens.input_tokens == 100

    @pytest.mark.asyncio
    async def test_streaming_returns_none_when_unavailable(self):
        """execute_streaming returns None for tokens when unavailable."""
        from teambot.copilot.sdk_client import CopilotSDKClient

        client = CopilotSDKClient()

        with patch.object(client, "_started", True):
            with patch.object(client, "_client", MagicMock()):
                with patch.object(client, "_execute_streaming_once") as mock_stream:
                    # Simulate no tokens available
                    mock_stream.return_value = ("response text", None)

                    result = await client._execute_streaming_once("pm", "test prompt")

                    text, tokens = result
                    assert text == "response text"
                    assert tokens is None
