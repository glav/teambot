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
        "critical_failure": (
            "🚨 <b>CRITICAL FAILURE</b>\n"
            "📂 <code>{feature_name}</code>\n"
            "📌 Stage: {stage}\n"
            "❌ Missing: <code>{artifact}</code>\n"
            "🔧 Recovery:\n{recovery_steps}"
        ),
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
        # Orchestration lifecycle events
        "orchestration_started": "🚀 <b>Starting</b>: {objective_name}",
        "orchestration_completed": (
            "✅ <b>Completed</b>: {objective_name}\n⏱️ Duration: {duration}"
        ),
        "custom_message": "📢 {message}",
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
        # Use event.data stage if present (e.g. parallel_stage_complete carries its own
        # stage), otherwise fall back to event.stage (the bus-tracked current stage).
        if "stage" not in context:
            if event.stage is not None:
                context["stage"] = html.escape(event.stage)
            else:
                context["stage"] = "Unknown"

        # Add computed emoji fields (emojis and hardcoded strings are safe)
        if event.event_type == "parallel_group_complete":
            all_success = event.data.get("all_success", False)
            context["emoji"] = STATUS_EMOJI["success"] if all_success else STATUS_EMOJI["warning"]
            context["status"] = "All passed" if all_success else "Some failed"
        elif event.event_type == "acceptance_test_stage_complete":
            failed = event.data.get("failed", 0)
            context["emoji"] = STATUS_EMOJI["success"] if failed == 0 else STATUS_EMOJI["failure"]
        elif event.event_type == "orchestration_started":
            # Fallback for missing objective_name
            if "objective_name" not in context or not context["objective_name"]:
                context["objective_name"] = "orchestration run"
        elif event.event_type == "orchestration_completed":
            # Fallback for missing objective_name
            if "objective_name" not in context or not context["objective_name"]:
                context["objective_name"] = "orchestration run"
            # Format duration from seconds
            duration_secs = event.data.get("duration_seconds", 0)
            minutes = int(duration_secs // 60)
            seconds = int(duration_secs % 60)
            context["duration"] = f"{minutes}m {seconds}s"
        elif event.event_type == "critical_failure":
            # Format recovery_steps as numbered list
            raw_steps = event.data.get("recovery_steps", [])
            if isinstance(raw_steps, list) and raw_steps:
                formatted_steps = []
                for i, step in enumerate(raw_steps, 1):
                    escaped_step = html.escape(str(step))
                    formatted_steps.append(f"  {i}. {escaped_step}")
                context["recovery_steps"] = "\n".join(formatted_steps)
            else:
                context["recovery_steps"] = "  No recovery steps available"

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
