"""Tests for message protocol - TDD approach."""

import pytest


class TestMessageType:
    """Tests for MessageType enum."""

    def test_message_types_exist(self):
        """Verify all required message types are defined."""
        from teambot.messaging.protocol import MessageType

        assert hasattr(MessageType, "TASK_ASSIGN")
        assert hasattr(MessageType, "TASK_COMPLETE")
        assert hasattr(MessageType, "TASK_FAILED")
        assert hasattr(MessageType, "STATUS_UPDATE")
        assert hasattr(MessageType, "CONTEXT_SHARE")
        assert hasattr(MessageType, "SHUTDOWN")

    def test_message_type_values_are_strings(self):
        """Message type values should be descriptive strings."""
        from teambot.messaging.protocol import MessageType

        assert MessageType.TASK_ASSIGN.value == "task_assign"
        assert MessageType.TASK_COMPLETE.value == "task_complete"
        assert MessageType.SHUTDOWN.value == "shutdown"


class TestAgentMessage:
    """Tests for AgentMessage dataclass."""

    def test_create_message_with_required_fields(self):
        """Create message with minimum required fields."""
        from teambot.messaging.protocol import AgentMessage, MessageType

        msg = AgentMessage(
            type=MessageType.TASK_ASSIGN,
            source_agent="orchestrator",
            target_agent="builder-1",
        )

        assert msg.type == MessageType.TASK_ASSIGN
        assert msg.source_agent == "orchestrator"
        assert msg.target_agent == "builder-1"
        assert msg.payload == {}
        assert msg.timestamp is not None
        assert msg.correlation_id is not None

    def test_create_message_with_all_fields(self):
        """Create message with all optional fields."""
        from teambot.messaging.protocol import AgentMessage, MessageType

        msg = AgentMessage(
            type=MessageType.TASK_COMPLETE,
            source_agent="builder-1",
            target_agent="orchestrator",
            payload={"result": "success"},
            correlation_id="task-123",
        )

        assert msg.target_agent == "orchestrator"
        assert msg.payload["result"] == "success"
        assert msg.correlation_id == "task-123"

    def test_message_has_unique_correlation_id(self):
        """Each message should have a unique correlation ID by default."""
        from teambot.messaging.protocol import AgentMessage, MessageType

        msg1 = AgentMessage(
            type=MessageType.STATUS_UPDATE,
            source_agent="pm",
            target_agent="orchestrator",
        )
        msg2 = AgentMessage(
            type=MessageType.STATUS_UPDATE,
            source_agent="pm",
            target_agent="orchestrator",
        )

        assert msg1.correlation_id != msg2.correlation_id

    def test_message_to_dict(self):
        """Message should be serializable to dict."""
        from teambot.messaging.protocol import AgentMessage, MessageType

        msg = AgentMessage(
            type=MessageType.STATUS_UPDATE,
            source_agent="pm",
            target_agent="orchestrator",
            payload={"status": "working"},
        )

        data = msg.to_dict()

        assert data["type"] == "status_update"
        assert data["source_agent"] == "pm"
        assert data["target_agent"] == "orchestrator"
        assert data["payload"]["status"] == "working"
        assert "timestamp" in data
        assert "correlation_id" in data

    def test_message_from_dict(self):
        """Message should be deserializable from dict."""
        from teambot.messaging.protocol import AgentMessage, MessageType

        data = {
            "type": "task_assign",
            "source_agent": "orchestrator",
            "target_agent": "builder-1",
            "payload": {"task": "implement feature"},
            "timestamp": "2026-01-22T10:00:00",
            "correlation_id": "test-123",
        }

        msg = AgentMessage.from_dict(data)

        assert msg.type == MessageType.TASK_ASSIGN
        assert msg.source_agent == "orchestrator"
        assert msg.target_agent == "builder-1"
        assert msg.payload["task"] == "implement feature"
        assert msg.correlation_id == "test-123"

    def test_message_from_dict_invalid_type_raises(self):
        """Invalid message type should raise ValueError."""
        from teambot.messaging.protocol import AgentMessage

        data = {
            "type": "invalid_type",
            "source_agent": "test",
            "target_agent": "test",
        }

        with pytest.raises(ValueError):
            AgentMessage.from_dict(data)

    def test_message_roundtrip(self):
        """Message should survive to_dict/from_dict roundtrip."""
        from teambot.messaging.protocol import AgentMessage, MessageType

        original = AgentMessage(
            type=MessageType.TASK_ASSIGN,
            source_agent="orchestrator",
            target_agent="builder-1",
            payload={"task": "test", "priority": 1},
            correlation_id="round-trip-test",
        )

        data = original.to_dict()
        restored = AgentMessage.from_dict(data)

        assert restored.type == original.type
        assert restored.source_agent == original.source_agent
        assert restored.target_agent == original.target_agent
        assert restored.payload == original.payload
        assert restored.correlation_id == original.correlation_id


class TestShutdownMessage:
    """Tests for shutdown sentinel message."""

    def test_create_shutdown_message(self):
        """Create a shutdown message for graceful termination."""
        from teambot.messaging.protocol import AgentMessage, MessageType

        msg = AgentMessage(
            type=MessageType.SHUTDOWN,
            source_agent="orchestrator",
            target_agent="builder-1",
        )

        assert msg.type == MessageType.SHUTDOWN

    def test_shutdown_message_is_sentinel(self):
        """Shutdown messages should be identifiable as sentinels."""
        from teambot.messaging.protocol import AgentMessage, MessageType

        msg = AgentMessage(
            type=MessageType.SHUTDOWN,
            source_agent="orchestrator",
            target_agent="all",
        )

        assert msg.type == MessageType.SHUTDOWN
        # Payload can carry shutdown reason if needed
        assert msg.payload == {} or msg.payload is not None
