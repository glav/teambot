"""Tests for model validation in config schema."""


class TestModelValidation:
    """Tests for validate_model function."""

    def test_validate_model_valid_claude(self):
        """Valid Claude models return True."""
        from teambot.config.schema import validate_model

        assert validate_model("claude-sonnet-4.5") is True
        assert validate_model("claude-haiku-4.5") is True
        assert validate_model("claude-opus-4.5") is True
        assert validate_model("claude-sonnet-4") is True

    def test_validate_model_valid_gpt(self):
        """Valid GPT models return True."""
        from teambot.config.schema import validate_model

        assert validate_model("gpt-5.2-codex") is True
        assert validate_model("gpt-5.2") is True
        assert validate_model("gpt-5.1-codex-max") is True
        assert validate_model("gpt-5.1-codex") is True
        assert validate_model("gpt-5.1") is True
        assert validate_model("gpt-5") is True
        assert validate_model("gpt-5.1-codex-mini") is True
        assert validate_model("gpt-5-mini") is True
        assert validate_model("gpt-4.1") is True

    def test_validate_model_valid_gemini(self):
        """Valid Gemini models return True."""
        from teambot.config.schema import validate_model

        assert validate_model("gemini-3-pro-preview") is True

    def test_validate_model_invalid(self):
        """Invalid model names return False."""
        from teambot.config.schema import validate_model

        assert validate_model("invalid-model") is False
        assert validate_model("gpt-4") is False  # old model
        assert validate_model("claude-3") is False  # old model

    def test_validate_model_none(self):
        """None returns False."""
        from teambot.config.schema import validate_model

        assert validate_model(None) is False

    def test_validate_model_empty_string(self):
        """Empty string returns False."""
        from teambot.config.schema import validate_model

        assert validate_model("") is False

    def test_validate_model_whitespace(self):
        """Whitespace-only returns False."""
        from teambot.config.schema import validate_model

        assert validate_model("  ") is False
        assert validate_model("\t") is False


class TestGetAvailableModels:
    """Tests for get_available_models function."""

    def test_returns_all_models(self):
        """Returns complete list of 14 models."""
        from teambot.config.schema import get_available_models

        models = get_available_models()
        assert len(models) == 14
        assert "gpt-5" in models
        assert "claude-opus-4.5" in models

    def test_returns_sorted_list(self):
        """Returns models in sorted order."""
        from teambot.config.schema import get_available_models

        models = get_available_models()
        assert models == sorted(models)


class TestGetModelInfo:
    """Tests for get_model_info function."""

    def test_returns_info_for_valid_model(self):
        """Returns display info for valid model."""
        from teambot.config.schema import get_model_info

        info = get_model_info("claude-opus-4.5")
        assert info is not None
        assert "display" in info
        assert "category" in info
        assert info["display"] == "Claude Opus 4.5"
        assert info["category"] == "premium"

    def test_returns_none_for_invalid_model(self):
        """Returns None for invalid model."""
        from teambot.config.schema import get_model_info

        assert get_model_info("invalid-model") is None
