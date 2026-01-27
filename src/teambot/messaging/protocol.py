"""Message protocol definitions for inter-agent communication."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageType(Enum):
    """Types of messages that can be sent between agents."""

    TASK_ASSIGN = "task_assign"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    STATUS_UPDATE = "status_update"
    CONTEXT_SHARE = "context_share"
    SHUTDOWN = "shutdown"


@dataclass
class AgentMessage:
    """Message sent between agents via queues."""

    type: MessageType
    source_agent: str
    target_agent: str
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Serialize message to dictionary for queue transport."""
        return {
            "type": self.type.value,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMessage":
        """Deserialize message from dictionary."""
        try:
            msg_type = MessageType(data["type"])
        except ValueError as e:
            raise ValueError(f"Invalid message type: {data['type']}") from e

        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()

        return cls(
            type=msg_type,
            source_agent=data["source_agent"],
            target_agent=data["target_agent"],
            payload=data.get("payload", {}),
            correlation_id=data.get("correlation_id", str(uuid.uuid4())),
            timestamp=timestamp,
        )
