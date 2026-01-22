"""Messaging package for inter-agent communication."""

from teambot.messaging.protocol import AgentMessage, MessageType
from teambot.messaging.router import MessageRouter, RoutingError

__all__ = ["AgentMessage", "MessageType", "MessageRouter", "RoutingError"]
