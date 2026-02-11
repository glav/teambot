"""Tests for notification config functions."""

from __future__ import annotations

from teambot.notifications.config import (
    create_event_bus_from_config,
    resolve_config_secrets,
    resolve_env_vars,
)


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
