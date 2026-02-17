"""Tests for notification config functions."""

from __future__ import annotations

from teambot.notifications.config import (
    create_event_bus_from_config,
    extract_env_var_name,
    resolve_config_secrets,
    resolve_env_vars,
)


class TestExtractEnvVarName:
    """Tests for extract_env_var_name function."""

    def test_extract_simple_pattern(self) -> None:
        """Extract env var name from ${VAR} pattern."""
        result = extract_env_var_name("${MY_TOKEN}")

        assert result == "MY_TOKEN"

    def test_extract_from_string_with_text(self) -> None:
        """Extract env var name even with surrounding text."""
        result = extract_env_var_name("prefix ${TOKEN} suffix")

        assert result == "TOKEN"

    def test_extract_first_match(self) -> None:
        """Extract first env var name when multiple present."""
        result = extract_env_var_name("${VAR1} and ${VAR2}")

        assert result == "VAR1"

    def test_no_pattern_returns_none(self) -> None:
        """Returns None when no ${} pattern found."""
        result = extract_env_var_name("regular text")

        assert result is None

    def test_partial_pattern_returns_none(self) -> None:
        """Returns None for partial patterns like $VAR."""
        result = extract_env_var_name("$VAR without braces")

        assert result is None

    def test_non_string_returns_none(self) -> None:
        """Returns None for non-string values."""
        assert extract_env_var_name(123) is None
        assert extract_env_var_name(None) is None
        assert extract_env_var_name(True) is None


class TestResolveEnvVars:
    """Tests for resolve_env_vars function."""

    def test_resolve_single_var(self, monkeypatch) -> None:
        """Single env var resolved."""
        monkeypatch.setenv("TEST_VAR", "test-value")

        result = resolve_env_vars("${TEST_VAR}")

        assert result == "test-value"

    def test_resolve_multiple_vars(self, monkeypatch) -> None:
        """Multiple env vars in one string."""
        monkeypatch.setenv("VAR1", "hello")
        monkeypatch.setenv("VAR2", "world")

        result = resolve_env_vars("${VAR1} ${VAR2}")

        assert result == "hello world"

    def test_missing_var_empty_string(self, monkeypatch) -> None:
        """Missing env var resolves to empty string."""
        monkeypatch.delenv("MISSING_VAR", raising=False)

        result = resolve_env_vars("${MISSING_VAR}")

        assert result == ""

    def test_non_var_pattern_unchanged(self) -> None:
        """Text without ${} pattern unchanged."""
        result = resolve_env_vars("regular text")

        assert result == "regular text"

    def test_partial_pattern_unchanged(self) -> None:
        """Partial pattern like $VAR unchanged."""
        result = resolve_env_vars("$VAR without braces")

        assert result == "$VAR without braces"

    def test_non_string_passthrough(self) -> None:
        """Non-string values pass through unchanged."""
        assert resolve_env_vars(123) == 123
        assert resolve_env_vars(None) is None
        assert resolve_env_vars(True) is True


class TestResolveConfigSecrets:
    """Tests for resolve_config_secrets function."""

    def test_resolve_nested_dict(self, monkeypatch) -> None:
        """Nested dict has values resolved."""
        monkeypatch.setenv("TOKEN", "secret-token")

        config = {"auth": {"token": "${TOKEN}"}}
        result = resolve_config_secrets(config)

        assert result["auth"]["token"] == "secret-token"

    def test_resolve_list_values(self, monkeypatch) -> None:
        """List values are resolved."""
        monkeypatch.setenv("ITEM", "resolved")

        config = {"items": ["${ITEM}", "static"]}
        result = resolve_config_secrets(config)

        assert result["items"] == ["resolved", "static"]

    def test_non_string_values_unchanged(self) -> None:
        """Non-string values in config unchanged."""
        config = {"count": 42, "enabled": True}
        result = resolve_config_secrets(config)

        assert result == {"count": 42, "enabled": True}


class TestCreateEventBusFromConfig:
    """Tests for create_event_bus_from_config function."""

    def test_returns_none_when_disabled(self) -> None:
        """Returns None when notifications disabled."""
        config = {"notifications": {"enabled": False}}

        result = create_event_bus_from_config(config)

        assert result is None

    def test_returns_none_when_no_notifications(self) -> None:
        """Returns None when no notifications section."""
        config = {}

        result = create_event_bus_from_config(config)

        assert result is None

    def test_creates_bus_when_enabled(self, monkeypatch) -> None:
        """Creates EventBus when enabled."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config, feature_name="test")

        assert result is not None
        assert len(result._channels) == 1
        assert result._feature_name == "test"

    def test_applies_event_filter(self, monkeypatch) -> None:
        """Applies event filter from config."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "events": ["stage_changed"],
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_failed") is False

    def test_applies_dry_run(self, monkeypatch) -> None:
        """Applies dry_run setting from config."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "dry_run": True,
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        assert channel._dry_run is True

    def test_uses_custom_env_var_names(self, monkeypatch) -> None:
        """Uses custom env var names from config."""
        monkeypatch.setenv("MY_CUSTOM_TOKEN", "custom-token")
        monkeypatch.setenv("MY_CUSTOM_CHAT_ID", "custom-123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${MY_CUSTOM_TOKEN}",
                        "chat_id": "${MY_CUSTOM_CHAT_ID}",
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        assert channel._token_env_var == "MY_CUSTOM_TOKEN"
        assert channel._chat_id_env_var == "MY_CUSTOM_CHAT_ID"
        assert channel.enabled is True

    def test_defaults_to_standard_env_vars_when_no_pattern(self, monkeypatch) -> None:
        """Uses default env var names when config doesn't have ${} patterns."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        # Missing token/chat_id fields, should use defaults
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        # Should still use defaults when fields are missing
        assert channel._token_env_var == "TEAMBOT_TELEGRAM_TOKEN"
        assert channel._chat_id_env_var == "TEAMBOT_TELEGRAM_CHAT_ID"

    def test_ignores_unknown_channel_type(self) -> None:
        """Unknown channel types are ignored."""
        config = {
            "notifications": {
                "enabled": True,
                "channels": [{"type": "unknown"}],
            }
        }

        result = create_event_bus_from_config(config)

        assert result is not None
        assert len(result._channels) == 0


class TestNotificationModeConfig:
    """Tests for notification_mode in channel config."""

    def test_stages_only_mode_expands_to_stage_events(self, monkeypatch) -> None:
        """notification_mode: 'stages_only' expands to stage event set."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "notification_mode": "stages_only",
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("orchestration_started") is True
        assert channel.supports_event("orchestration_completed") is True
        assert channel.supports_event("agent_running") is False
        assert channel.supports_event("agent_failed") is False

    def test_agent_status_mode_expands_to_agent_events(self, monkeypatch) -> None:
        """notification_mode: 'agent_status' expands to agent event set."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "notification_mode": "agent_status",
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_running") is True
        assert channel.supports_event("agent_complete") is True
        assert channel.supports_event("agent_failed") is True
        assert channel.supports_event("parallel_group_start") is False

    def test_all_mode_accepts_all_events(self, monkeypatch) -> None:
        """notification_mode: 'all' accepts all events."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "notification_mode": "all",
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        # All mode = no filtering, accepts any event
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_running") is True
        assert channel.supports_event("custom_event") is True

    def test_events_array_takes_precedence_over_mode(self, monkeypatch) -> None:
        """Explicit events array overrides notification_mode."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "notification_mode": "all",
                        "events": ["agent_failed"],  # Explicit filter overrides mode
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        assert channel.supports_event("agent_failed") is True
        assert channel.supports_event("stage_changed") is False  # Not in events array

    def test_default_accepts_all_when_no_mode_or_events(self, monkeypatch) -> None:
        """Default behavior (no mode, no events) accepts all events."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        # No events, no notification_mode
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        # Default = all events (backwards compatible)
        assert channel.supports_event("stage_changed") is True
        assert channel.supports_event("agent_running") is True
        assert channel.supports_event("any_future_event") is True

    def test_invalid_notification_mode_raises_value_error(self, monkeypatch) -> None:
        """Invalid notification_mode raises ValueError with valid modes listed."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "notification_mode": "invalid_mode",
                    }
                ],
            }
        }

        import pytest

        with pytest.raises(ValueError) as exc_info:
            create_event_bus_from_config(config)

        error_message = str(exc_info.value)
        assert "invalid_mode" in error_message
        assert "stages_only" in error_message
        assert "agent_status" in error_message
        assert "all" in error_message

    def test_empty_events_array_disables_all_notifications(self, monkeypatch) -> None:
        """Empty events array disables all notifications."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "events": [],  # Empty list should disable all events
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        # Empty events list should disable all events
        assert channel.supports_event("stage_changed") is False
        assert channel.supports_event("agent_running") is False
        assert channel.supports_event("any_event") is False

    def test_empty_events_array_overrides_notification_mode(self, monkeypatch) -> None:
        """Empty events array takes precedence over notification_mode."""
        monkeypatch.setenv("TEAMBOT_TELEGRAM_TOKEN", "token")
        monkeypatch.setenv("TEAMBOT_TELEGRAM_CHAT_ID", "123")

        config = {
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                        "notification_mode": "all",  # Mode says accept all
                        "events": [],  # Empty array should override mode
                    }
                ],
            }
        }

        result = create_event_bus_from_config(config)

        channel = result._channels[0]
        # Empty events array should override notification_mode
        assert channel.supports_event("stage_changed") is False
        assert channel.supports_event("agent_running") is False
