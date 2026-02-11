"""Message templates for notification channels."""

from __future__ import annotations

import html
from typing import Any

from teambot.notifications.events import NotificationEvent

# Status emojis
STATUS_EMOJI = {
    "success": "✅",
    "failure": "❌",
    "warning": "⚠️",
    "running": "🔄",
    "info": "ℹ️",
}


class MessageTemplates:
    """Template renderer for notification messages."""

    # Templates use HTML format for Telegram compatibility
    TEMPLATES: dict[str, str] = {
        "stage_changed": ("📌 <b>Stage: {stage}</b>\n📂 <code>{feature_name}</code>"),
        "agent_running": ("🔄 <b>{agent_id}</b> started\n📋 Task: <i>{task}</i>"),
        "agent_complete": "✅ <b>{agent_id}</b> completed",
        "agent_failed": ("❌ <b>{agent_id}</b> FAILED\n📂 <code>{feature_name}</code>"),
        "parallel_group_start": ("🚀 <b>Parallel Group: {group}</b>\n📊 Stages: {stages}"),
        "parallel_group_complete": ("{emoji} <b>Parallel Group: {group}</b>\nStatus: {status}"),
        "parallel_stage_complete": "✅ <b>{stage}</b> completed (agent: {agent})",
        "parallel_stage_failed": "❌ <b>{stage}</b> FAILED (agent: {agent})",
        "acceptance_test_stage_complete": (
            "{emoji} <b>Acceptance Tests</b>\n"
            "📊 Results: {passed}/{total} passed\n"
            "📂 <code>{feature_name}</code>"
        ),
        "acceptance_test_max_iterations_reached": (
            "⚠️ <b>Max Fix Iterations Reached</b>\n"
            "Acceptance tests still failing after {iterations_used} attempts."
        ),
        "review_progress": ("📝 <b>Review Progress</b>\nStage: {stage}\n{message}"),
    }

    def render(self, event: NotificationEvent) -> str:
        """Render event using appropriate template.

        Args:
            event: The notification event to render

        Returns:
            Formatted message string
        """
        template = self.TEMPLATES.get(event.event_type) or self._default_template()

        # Build context from event - escape all string values from event.data
        context: dict[str, Any] = {
            key: html.escape(value) if isinstance(value, str) else value
            for key, value in event.data.items()
        }

        # Escape event-provided string fields
        context["event_type"] = html.escape(event.event_type)
        context["feature_name"] = html.escape(event.feature_name or "Unknown")
        # Use event.stage first, fallback to already-escaped event.data stage, or "Unknown"
        if event.stage is not None:
            context["stage"] = html.escape(event.stage)
        elif "stage" not in context:
            context["stage"] = "Unknown"

        # Add computed emoji fields (emojis and hardcoded strings are safe)
        if event.event_type == "parallel_group_complete":
            all_success = event.data.get("all_success", False)
            context["emoji"] = STATUS_EMOJI["success"] if all_success else STATUS_EMOJI["warning"]
            context["status"] = "All passed" if all_success else "Some failed"
        elif event.event_type == "acceptance_test_stage_complete":
            failed = event.data.get("failed", 0)
            context["emoji"] = STATUS_EMOJI["success"] if failed == 0 else STATUS_EMOJI["failure"]

        # Format stages list if present
        if "stages" in context and isinstance(context["stages"], list):
            escaped_stages = [html.escape(str(s)) for s in context["stages"]]
            context["stages"] = ", ".join(escaped_stages)

        # Safe format - use fallback for missing keys
        try:
            return template.format(**context).strip()
        except KeyError as e:
            return f"📢 Event: {html.escape(event.event_type)}\n(Missing: {e})"

    def _default_template(self) -> str:
        """Get fallback template for unknown events."""
        return "📢 <b>{event_type}</b>\n📂 <code>{feature_name}</code>"
