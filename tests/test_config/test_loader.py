"""Tests for config loader - TDD approach."""

import json

import pytest


class TestConfigLoader:
    """Tests for ConfigLoader class."""

    def test_load_valid_config(self, tmp_path):
        """Load valid JSON configuration."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [
                {
                    "id": "pm",
                    "persona": "project_manager",
                    "display_name": "Project Manager",
                }
            ],
            "teambot_dir": ".teambot",
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["agents"][0]["id"] == "pm"

    def test_load_missing_file_raises(self):
        """Loading missing file raises ConfigError."""
        from pathlib import Path

        from teambot.config.loader import ConfigError, ConfigLoader

        loader = ConfigLoader()

        with pytest.raises(ConfigError):
            loader.load(Path("/nonexistent/config.json"))

    def test_load_invalid_json_raises(self, tmp_path):
        """Loading invalid JSON raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }")

        loader = ConfigLoader()

        with pytest.raises(ConfigError):
            loader.load(config_file)

    def test_validate_missing_agents_raises(self, tmp_path):
        """Config without agents field raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {"teambot_dir": ".teambot"}
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()

        with pytest.raises(ConfigError, match="agents"):
            loader.load(config_file)

    def test_validate_agent_missing_id_raises(self, tmp_path):
        """Agent without id field raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {"agents": [{"persona": "builder"}]}
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()

        with pytest.raises(ConfigError, match="id"):
            loader.load(config_file)

    def test_load_with_defaults(self, tmp_path):
        """Missing optional fields get defaults."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [
                {
                    "id": "builder-1",
                    "persona": "builder",
                }
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        # Should have default teambot_dir
        assert config.get("teambot_dir") == ".teambot"
        # Agent should have default display_name
        assert config["agents"][0].get("display_name") is not None


class TestDefaultConfig:
    """Tests for default configuration generation."""

    def test_create_default_config(self):
        """Create default config with MVP agents."""
        from teambot.config.loader import create_default_config

        config = create_default_config()

        assert "agents" in config
        # MVP has 6 agents: PM, BA, Writer, Builder x2, Reviewer
        assert len(config["agents"]) == 6

    def test_default_config_has_required_personas(self):
        """Default config includes all MVP personas."""
        from teambot.config.loader import create_default_config

        config = create_default_config()
        personas = {a["persona"] for a in config["agents"]}

        assert "project_manager" in personas
        assert "business_analyst" in personas
        assert "technical_writer" in personas
        assert "builder" in personas
        assert "reviewer" in personas

    def test_save_config(self, tmp_path):
        """Save configuration to file."""
        from teambot.config.loader import ConfigLoader, create_default_config

        config = create_default_config()
        config_file = tmp_path / "teambot.json"

        loader = ConfigLoader()
        loader.save(config, config_file)

        assert config_file.exists()
        loaded = json.loads(config_file.read_text())
        assert "agents" in loaded


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_agent_id_unique(self, tmp_path):
        """Agent IDs must be unique."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [
                {"id": "builder-1", "persona": "builder"},
                {"id": "builder-1", "persona": "builder"},  # Duplicate!
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()

        with pytest.raises(ConfigError, match="Duplicate"):
            loader.load(config_file)

    def test_validate_persona_type(self, tmp_path):
        """Persona must be a valid type."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [
                {"id": "agent-1", "persona": "invalid_persona_type"},
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()

        with pytest.raises(ConfigError, match="persona"):
            loader.load(config_file)


class TestOverlayConfig:
    """Tests for overlay configuration."""

    def test_overlay_defaults_applied(self, tmp_path):
        """Test overlay defaults are applied."""
        from teambot.config.loader import ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text('{"agents": [{"id": "pm", "persona": "project_manager"}]}')

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert "overlay" in config
        assert config["overlay"]["enabled"] is True
        assert config["overlay"]["position"] == "top-right"

    def test_overlay_position_valid(self, tmp_path):
        """Test valid overlay position."""
        from teambot.config.loader import ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text("""
        {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "overlay": {"position": "bottom-left"}
        }
        """)

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["overlay"]["position"] == "bottom-left"

    def test_overlay_position_invalid(self, tmp_path):
        """Test invalid overlay position raises error."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text("""
        {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "overlay": {"position": "middle"}
        }
        """)

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="Invalid overlay position"):
            loader.load(config_file)

    def test_overlay_enabled_bool(self, tmp_path):
        """Test overlay enabled must be boolean."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text("""
        {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "overlay": {"enabled": "yes"}
        }
        """)

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="must be a boolean"):
            loader.load(config_file)

    def test_overlay_disabled(self, tmp_path):
        """Test overlay can be disabled."""
        from teambot.config.loader import ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text("""
        {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "overlay": {"enabled": false}
        }
        """)

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["overlay"]["enabled"] is False


class TestDefaultAgentConfig:
    """Tests for default_agent configuration."""

    def test_default_agent_valid(self, tmp_path):
        """Test valid default_agent configuration."""
        from teambot.config.loader import ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text("""
        {
            "agents": [
                {"id": "pm", "persona": "project_manager"},
                {"id": "ba", "persona": "business_analyst"}
            ],
            "default_agent": "pm"
        }
        """)

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["default_agent"] == "pm"

    def test_default_agent_not_in_agents_raises(self, tmp_path):
        """Test default_agent not in agents list raises error."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text("""
        {
            "agents": [
                {"id": "pm", "persona": "project_manager"}
            ],
            "default_agent": "unknown"
        }
        """)

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="Invalid default_agent"):
            loader.load(config_file)

    def test_default_agent_not_string_raises(self, tmp_path):
        """Test default_agent must be a string."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text("""
        {
            "agents": [
                {"id": "pm", "persona": "project_manager"}
            ],
            "default_agent": 123
        }
        """)

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="must be a string"):
            loader.load(config_file)

    def test_default_agent_optional(self, tmp_path):
        """Test default_agent is optional."""
        from teambot.config.loader import ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text("""
        {
            "agents": [
                {"id": "pm", "persona": "project_manager"}
            ]
        }
        """)

        loader = ConfigLoader()
        config = loader.load(config_file)

        # Should not have default_agent key if not specified
        assert "default_agent" not in config


class TestAgentModelConfig:
    """Tests for agent model field in config loader."""

    def test_agent_with_valid_model(self, tmp_path):
        """Agent with valid model loads successfully."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [
                {
                    "id": "pm",
                    "persona": "project_manager",
                    "display_name": "Project Manager",
                    "model": "gpt-5",
                }
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["agents"][0]["model"] == "gpt-5"

    def test_agent_with_invalid_model_raises(self, tmp_path):
        """Agent with invalid model raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [
                {
                    "id": "pm",
                    "persona": "project_manager",
                    "display_name": "Project Manager",
                    "model": "invalid-model",
                }
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()

        with pytest.raises(ConfigError, match="Invalid model"):
            loader.load(config_file)

    def test_agent_without_model_is_valid(self, tmp_path):
        """Agent without model field is valid (optional)."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [
                {
                    "id": "pm",
                    "persona": "project_manager",
                    "display_name": "Project Manager",
                }
            ]
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["agents"][0].get("model") is None


class TestGlobalDefaultModel:
    """Tests for global default_model in config."""

    def test_valid_default_model(self, tmp_path):
        """Valid global default_model loads successfully."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "default_model": "claude-sonnet-4",
            "agents": [{"id": "pm", "persona": "project_manager", "display_name": "PM"}],
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["default_model"] == "claude-sonnet-4"

    def test_invalid_default_model_raises(self, tmp_path):
        """Invalid global default_model raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "default_model": "invalid-model",
            "agents": [{"id": "pm", "persona": "project_manager", "display_name": "PM"}],
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()

        with pytest.raises(ConfigError, match="Invalid default_model"):
            loader.load(config_file)

    def test_default_model_optional(self, tmp_path):
        """Config without default_model is valid."""
        from teambot.config.loader import ConfigLoader

        config_data = {"agents": [{"id": "pm", "persona": "project_manager", "display_name": "PM"}]}
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config.get("default_model") is None


class TestAnimationConfig:
    """Tests for show_startup_animation config validation."""

    def test_show_startup_animation_default_true(self, tmp_path):
        """Missing show_startup_animation defaults to True."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["show_startup_animation"] is True

    def test_show_startup_animation_validates_bool(self, tmp_path):
        """Valid boolean show_startup_animation passes validation."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "show_startup_animation": False,
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["show_startup_animation"] is False

    def test_invalid_show_startup_animation_raises_error(self, tmp_path):
        """Non-boolean show_startup_animation raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "show_startup_animation": "yes",
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="'show_startup_animation' must be a boolean"):
            loader.load(config_file)


class TestNotificationsConfigValidation:
    """Tests for notifications configuration validation."""

    def test_valid_notifications_config(self, tmp_path):
        """Valid notifications config passes validation."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {
                "enabled": True,
                "channels": [
                    {
                        "type": "telegram",
                        "token": "${TEAMBOT_TELEGRAM_TOKEN}",
                        "chat_id": "${TEAMBOT_TELEGRAM_CHAT_ID}",
                    }
                ],
            },
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["notifications"]["enabled"] is True
        assert len(config["notifications"]["channels"]) == 1

    def test_notifications_not_object_raises(self, tmp_path):
        """notifications must be an object."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": "invalid",
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="'notifications' must be an object"):
            loader.load(config_file)

    def test_notifications_enabled_not_bool_raises(self, tmp_path):
        """notifications.enabled must be boolean."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {"enabled": "yes"},
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="'notifications.enabled' must be a boolean"):
            loader.load(config_file)

    def test_channels_not_list_raises(self, tmp_path):
        """notifications.channels must be a list."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {"channels": "invalid"},
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="'notifications.channels' must be a list"):
            loader.load(config_file)

    def test_channel_missing_type_raises(self, tmp_path):
        """Channel without type raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {
                "channels": [{"token": "x", "chat_id": "y"}],
            },
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="must have a 'type' field"):
            loader.load(config_file)

    def test_channel_invalid_type_raises(self, tmp_path):
        """Invalid channel type raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {
                "channels": [{"type": "unknown"}],
            },
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="Invalid channel type 'unknown'"):
            loader.load(config_file)

    def test_telegram_missing_token_raises(self, tmp_path):
        """Telegram channel without token raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {
                "channels": [{"type": "telegram", "chat_id": "123"}],
            },
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="missing required field 'token'"):
            loader.load(config_file)

    def test_telegram_missing_chat_id_raises(self, tmp_path):
        """Telegram channel without chat_id raises ConfigError."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {
                "channels": [{"type": "telegram", "token": "abc"}],
            },
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="missing required field 'chat_id'"):
            loader.load(config_file)

    def test_dry_run_not_bool_raises(self, tmp_path):
        """dry_run must be boolean."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {
                "channels": [{"type": "telegram", "token": "x", "chat_id": "y", "dry_run": "yes"}],
            },
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="'dry_run' .* must be a boolean"):
            loader.load(config_file)

    def test_events_not_list_raises(self, tmp_path):
        """events filter must be a list."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {
                "channels": [{"type": "telegram", "token": "x", "chat_id": "y", "events": "all"}],
            },
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="'events' .* must be a list"):
            loader.load(config_file)

    def test_notifications_defaults_applied(self, tmp_path):
        """Defaults are applied to notifications config."""
        from teambot.config.loader import ConfigLoader

        config_data = {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "notifications": {
                "channels": [{"type": "telegram", "token": "x", "chat_id": "y"}],
            },
        }
        config_file = tmp_path / "teambot.json"
        config_file.write_text(json.dumps(config_data))

        loader = ConfigLoader()
        config = loader.load(config_file)

        # Default enabled=True
        assert config["notifications"]["enabled"] is True
        # Default dry_run=False
        assert config["notifications"]["channels"][0]["dry_run"] is False
