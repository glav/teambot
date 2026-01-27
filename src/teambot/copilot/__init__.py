"""Copilot CLI integration module."""

from teambot.copilot.client import CopilotClient, CopilotResult
from teambot.copilot.sdk_client import CopilotSDKClient, SDKClientError

__all__ = ["CopilotClient", "CopilotResult", "CopilotSDKClient", "SDKClientError"]
