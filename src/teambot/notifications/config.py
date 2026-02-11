"""Notification configuration loading and env var resolution."""

from __future__ import annotations

import os
import re
from typing import Any, TypeVar, overload

ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")

_T = TypeVar("_T")


@overload
def resolve_env_vars(value: str) -> str: ...


@overload
def resolve_env_vars(value: _T) -> _T: ...  # noqa: UP047


def resolve_env_vars(value: Any) -> Any:
    """Resolve ${VAR} patterns in string values.

    Args:
        value: String potentially containing ${VAR} patterns, or any other type
               (non-string values are returned unchanged)

    Returns:
        String with env vars resolved (empty string if var not set),
        or the original value if not a string
    """
    if not isinstance(value, str):
        return value

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, "")

    return ENV_VAR_PATTERN.sub(replacer, value)


def resolve_config_secrets(config: Any) -> Any:
    """Recursively resolve env vars in config dict/list.

    Args:
        config: Config dict, list, or value

    Returns:
        Config with all ${VAR} patterns resolved
    """
    if isinstance(config, dict):
        return {k: resolve_config_secrets(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [resolve_config_secrets(v) for v in config]
    elif isinstance(config, str):
        return resolve_env_vars(config)
    return config


def create_event_bus_from_config(
    config: dict[str, Any],
    feature_name: str | None = None,
):
    """Create EventBus with channels from config.

    Args:
        config: Loaded teambot config dict
        feature_name: Feature name for context

    Returns:
        Configured EventBus, or None if notifications disabled
    """
    from teambot.notifications.event_bus import EventBus

    notifications = config.get("notifications", {})

    if not notifications.get("enabled", False):
        return None

    bus = EventBus(feature_name=feature_name)

    for channel_config in notifications.get("channels", []):
        channel = _create_channel(channel_config)
        if channel:
            bus.subscribe(channel)

    return bus


def _create_channel(channel_config: dict[str, Any]):
    """Create channel instance from config."""
    from teambot.notifications.channels.telegram import TelegramChannel

    channel_type = channel_config.get("type")

    if channel_type == "telegram":
        # Resolve env var references
        resolved = resolve_config_secrets(channel_config)
        subscribed = set(resolved.get("events", []))
        return TelegramChannel(
            subscribed_events=subscribed if subscribed else None,
            dry_run=resolved.get("dry_run", False),
        )

    return None
