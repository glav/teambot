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
        config_file.write_text('''
        {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "overlay": {"position": "bottom-left"}
        }
        ''')

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["overlay"]["position"] == "bottom-left"

    def test_overlay_position_invalid(self, tmp_path):
        """Test invalid overlay position raises error."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text('''
        {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "overlay": {"position": "middle"}
        }
        ''')

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="Invalid overlay position"):
            loader.load(config_file)

    def test_overlay_enabled_bool(self, tmp_path):
        """Test overlay enabled must be boolean."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text('''
        {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "overlay": {"enabled": "yes"}
        }
        ''')

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="must be a boolean"):
            loader.load(config_file)

    def test_overlay_disabled(self, tmp_path):
        """Test overlay can be disabled."""
        from teambot.config.loader import ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text('''
        {
            "agents": [{"id": "pm", "persona": "project_manager"}],
            "overlay": {"enabled": false}
        }
        ''')

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["overlay"]["enabled"] is False


class TestDefaultAgentConfig:
    """Tests for default_agent configuration."""

    def test_default_agent_valid(self, tmp_path):
        """Test valid default_agent configuration."""
        from teambot.config.loader import ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text('''
        {
            "agents": [
                {"id": "pm", "persona": "project_manager"},
                {"id": "ba", "persona": "business_analyst"}
            ],
            "default_agent": "pm"
        }
        ''')

        loader = ConfigLoader()
        config = loader.load(config_file)

        assert config["default_agent"] == "pm"

    def test_default_agent_not_in_agents_raises(self, tmp_path):
        """Test default_agent not in agents list raises error."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text('''
        {
            "agents": [
                {"id": "pm", "persona": "project_manager"}
            ],
            "default_agent": "unknown"
        }
        ''')

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="Invalid default_agent"):
            loader.load(config_file)

    def test_default_agent_not_string_raises(self, tmp_path):
        """Test default_agent must be a string."""
        from teambot.config.loader import ConfigError, ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text('''
        {
            "agents": [
                {"id": "pm", "persona": "project_manager"}
            ],
            "default_agent": 123
        }
        ''')

        loader = ConfigLoader()
        with pytest.raises(ConfigError, match="must be a string"):
            loader.load(config_file)

    def test_default_agent_optional(self, tmp_path):
        """Test default_agent is optional."""
        from teambot.config.loader import ConfigLoader

        config_file = tmp_path / "teambot.json"
        config_file.write_text('''
        {
            "agents": [
                {"id": "pm", "persona": "project_manager"}
            ]
        }
        ''')

        loader = ConfigLoader()
        config = loader.load(config_file)

        # Should not have default_agent key if not specified
        assert "default_agent" not in config
