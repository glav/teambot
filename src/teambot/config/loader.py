"""Configuration loader for TeamBot JSON configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from teambot.config.schema import validate_model


class ConfigError(Exception):
    """Raised when configuration is invalid."""

    pass


VALID_PERSONAS = {
    "project_manager",
    "business_analyst",
    "technical_writer",
    "builder",
    "reviewer",
}

NOTIFICATION_CHANNEL_TYPES = {"telegram"}

REQUIRED_CHANNEL_FIELDS = {
    "telegram": {"token", "chat_id"},
}


def create_default_config() -> dict[str, Any]:
    """Create default configuration with MVP agents."""
    return {
        "teambot_dir": ".teambot",
        "agents": [
            {
                "id": "pm",
                "persona": "project_manager",
                "display_name": "Project Manager",
                "parallel_capable": False,
                "workflow_stages": ["setup", "planning", "coordination"],
            },
            {
                "id": "ba",
                "persona": "business_analyst",
                "display_name": "Business Analyst",
                "parallel_capable": False,
                "workflow_stages": ["business_problem", "spec"],
            },
            {
                "id": "writer",
                "persona": "technical_writer",
                "display_name": "Technical Writer",
                "parallel_capable": False,
                "workflow_stages": ["documentation"],
            },
            {
                "id": "builder-1",
                "persona": "builder",
                "display_name": "Builder (Primary)",
                "parallel_capable": True,
                "workflow_stages": ["implementation", "testing"],
            },
            {
                "id": "builder-2",
                "persona": "builder",
                "display_name": "Builder (Secondary)",
                "parallel_capable": True,
                "workflow_stages": ["implementation", "testing"],
            },
            {
                "id": "reviewer",
                "persona": "reviewer",
                "display_name": "Reviewer",
                "parallel_capable": False,
                "workflow_stages": ["review"],
            },
        ],
        "workflow": {
            "stages": [
                "setup",
                "business_problem",
                "spec",
                "review",
                "research",
                "test_strategy",
                "plan",
                "implementation",
                "test",
                "post_review",
            ]
        },
    }


class ConfigLoader:
    """Loads and validates TeamBot configuration from JSON files."""

    def load(self, config_path: Path) -> dict[str, Any]:
        """Load and validate configuration from JSON file."""
        if not config_path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        try:
            content = config_path.read_text(encoding="utf-8")
            config = json.loads(content)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in configuration: {e}") from e

        self._validate(config)
        self._apply_defaults(config)

        return config

    def save(self, config: dict[str, Any], config_path: Path) -> None:
        """Save configuration to JSON file."""
        config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    def _validate(self, config: dict[str, Any]) -> None:
        """Validate configuration structure."""
        # Check required fields
        if "agents" not in config:
            raise ConfigError("Configuration must have 'agents' field")

        agents = config["agents"]
        if not isinstance(agents, list):
            raise ConfigError("'agents' must be a list")

        # Validate each agent
        seen_ids: set[str] = set()
        for agent in agents:
            self._validate_agent(agent, seen_ids)

        # Validate default_agent if present
        if "default_agent" in config:
            self._validate_default_agent(config["default_agent"], seen_ids)

        # Validate default_model if present
        if "default_model" in config:
            self._validate_default_model(config["default_model"])

        # Validate animation config if present
        if "show_startup_animation" in config:
            if not isinstance(config["show_startup_animation"], bool):
                raise ConfigError("'show_startup_animation' must be a boolean")

        # Validate notifications config if present
        if "notifications" in config:
            self._validate_notifications(config["notifications"])

    def _validate_agent(self, agent: dict[str, Any], seen_ids: set[str]) -> None:
        """Validate a single agent configuration."""
        if "id" not in agent:
            raise ConfigError("Each agent must have an 'id' field")

        agent_id = agent["id"]
        if agent_id in seen_ids:
            raise ConfigError(f"Duplicate agent id: {agent_id}")
        seen_ids.add(agent_id)

        if "persona" not in agent:
            raise ConfigError(f"Agent {agent_id} must have a 'persona' field")

        persona = agent["persona"]
        if persona not in VALID_PERSONAS:
            raise ConfigError(
                f"Invalid persona '{persona}' for agent {agent_id}. "
                f"Valid personas: {VALID_PERSONAS}"
            )

        # Validate model if present
        model = agent.get("model")
        if model is not None and not validate_model(model):
            raise ConfigError(
                f"Invalid model '{model}' for agent '{agent_id}'. "
                f"Use '/models' command to see available models."
            )

    def _validate_default_agent(self, default_agent: str, seen_ids: set[str]) -> None:
        """Validate default_agent configuration."""
        if not isinstance(default_agent, str):
            raise ConfigError("'default_agent' must be a string")

        if default_agent not in seen_ids:
            raise ConfigError(
                f"Invalid default_agent '{default_agent}'. Agent must be defined in 'agents' list."
            )

    def _validate_default_model(self, default_model: str) -> None:
        """Validate global default_model configuration."""
        if not isinstance(default_model, str):
            raise ConfigError("'default_model' must be a string")

        if not validate_model(default_model):
            raise ConfigError(
                f"Invalid default_model '{default_model}'. "
                f"Use '/models' command to see available models."
            )

    def _validate_notifications(self, notifications: dict[str, Any]) -> None:
        """Validate notifications configuration."""
        if not isinstance(notifications, dict):
            raise ConfigError("'notifications' must be an object")

        if "enabled" in notifications:
            if not isinstance(notifications["enabled"], bool):
                raise ConfigError("'notifications.enabled' must be a boolean")

        if "channels" in notifications:
            channels = notifications["channels"]
            if not isinstance(channels, list):
                raise ConfigError("'notifications.channels' must be a list")

            for i, channel in enumerate(channels):
                self._validate_notification_channel(channel, i)

    def _validate_notification_channel(self, channel: dict[str, Any], index: int) -> None:
        """Validate a single notification channel configuration."""
        if not isinstance(channel, dict):
            raise ConfigError(f"notifications.channels[{index}] must be an object")

        if "type" not in channel:
            raise ConfigError(f"notifications.channels[{index}] must have a 'type' field")

        channel_type = channel["type"]
        if channel_type not in NOTIFICATION_CHANNEL_TYPES:
            raise ConfigError(
                f"Invalid channel type '{channel_type}' at notifications.channels[{index}]. "
                f"Valid types: {NOTIFICATION_CHANNEL_TYPES}"
            )

        # Validate required fields for this channel type
        required = REQUIRED_CHANNEL_FIELDS.get(channel_type, set())
        for field in required:
            if field not in channel:
                raise ConfigError(
                    f"notifications.channels[{index}] (type: {channel_type}) "
                    f"is missing required field '{field}'"
                )

        # Validate dry_run if present
        if "dry_run" in channel:
            if not isinstance(channel["dry_run"], bool):
                raise ConfigError(f"'dry_run' in notifications.channels[{index}] must be a boolean")

        # Validate events filter if present
        if "events" in channel:
            events = channel["events"]
            if not isinstance(events, list):
                raise ConfigError(f"'events' in notifications.channels[{index}] must be a list")

    def _apply_defaults(self, config: dict[str, Any]) -> None:
        """Apply default values for missing optional fields."""
        if "teambot_dir" not in config:
            config["teambot_dir"] = ".teambot"

        for agent in config.get("agents", []):
            if "display_name" not in agent:
                agent["display_name"] = agent["id"].replace("-", " ").title()
            if "parallel_capable" not in agent:
                agent["parallel_capable"] = False
            if "workflow_stages" not in agent:
                agent["workflow_stages"] = []

        # Apply animation defaults
        if "show_startup_animation" not in config:
            config["show_startup_animation"] = True

        # Apply notifications defaults
        if "notifications" in config:
            notifications = config["notifications"]
            if "enabled" not in notifications:
                notifications["enabled"] = True
            if "channels" not in notifications:
                notifications["channels"] = []
            for channel in notifications.get("channels", []):
                if "dry_run" not in channel:
                    channel["dry_run"] = False
