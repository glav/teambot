"""Tests for model validation in config schema."""

from unittest.mock import patch

import pytest


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


class TestDynamicModelDiscovery:
    """Tests for dynamic model discovery with caching."""

    @pytest.fixture
    def reset_model_state(self):
        """Reset model cache state between tests."""
        from teambot.config.schema import reset_model_cache

        reset_model_cache()
        yield
        reset_model_cache()

    def test_uses_cached_models_when_available(self, reset_model_state, tmp_path):
        """Test that cached models are used when cache is valid."""
        import json
        import time

        from teambot.config.schema import (
            get_available_models,
            reset_model_cache,
        )

        # Create mock cache
        cache_dir = tmp_path / ".teambot"
        cache_dir.mkdir()
        cache_file = cache_dir / "model_cache.json"
        cache_data = {
            "models": [
                {"id": "new-model-1", "name": "New Model 1", "category": "standard"},
                {"id": "new-model-2", "name": "New Model 2", "category": "premium"},
            ],
            "timestamp": time.time(),
            "sdk_version": "1.0.0",
        }
        cache_file.write_text(json.dumps(cache_data))

        # Reset to force reload
        reset_model_cache()

        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            models = get_available_models()

        assert "new-model-1" in models
        assert "new-model-2" in models

    def test_uses_fallback_when_cache_missing(self, reset_model_state, tmp_path):
        """Test that fallback models are used when no cache."""
        from teambot.config.schema import (
            get_available_models,
            reset_model_cache,
        )

        # Reset and mock empty cache dir
        reset_model_cache()

        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            models = get_available_models()

        # Should use fallback
        assert "gpt-5" in models
        assert "claude-opus-4.5" in models
        assert len(models) == 14

    def test_validate_model_with_cached_data(self, reset_model_state, tmp_path):
        """Test validate_model uses cached models."""
        import json
        import time

        from teambot.config.schema import reset_model_cache, validate_model

        # Create mock cache with new model
        cache_dir = tmp_path / ".teambot"
        cache_dir.mkdir()
        cache_file = cache_dir / "model_cache.json"
        cache_data = {
            "models": [
                {"id": "claude-opus-4.6", "name": "Claude Opus 4.6", "category": "premium"},
            ],
            "timestamp": time.time(),
            "sdk_version": "1.0.0",
        }
        cache_file.write_text(json.dumps(cache_data))

        reset_model_cache()

        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            assert validate_model("claude-opus-4.6") is True

    def test_is_using_cached_models(self, reset_model_state, tmp_path):
        """Test is_using_cached_models function."""
        import json
        import time

        from teambot.config.schema import (
            get_available_models,
            is_using_cached_models,
            reset_model_cache,
        )

        # With no cache, should not be using cached
        reset_model_cache()
        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            get_available_models()  # Trigger load
            assert is_using_cached_models() is False

        # Create cache
        cache_dir = tmp_path / ".teambot"
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / "model_cache.json"
        cache_data = {
            "models": [{"id": "test", "name": "Test", "category": "standard"}],
            "timestamp": time.time(),
            "sdk_version": "1.0.0",
        }
        cache_file.write_text(json.dumps(cache_data))

        reset_model_cache()
        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            get_available_models()  # Trigger load
            assert is_using_cached_models() is True

    def test_get_model_info_with_cached_data(self, reset_model_state, tmp_path):
        """Test get_model_info uses cached metadata."""
        import json
        import time

        from teambot.config.schema import get_model_info, reset_model_cache

        cache_dir = tmp_path / ".teambot"
        cache_dir.mkdir()
        cache_file = cache_dir / "model_cache.json"
        cache_data = {
            "models": [
                {"id": "new-model", "name": "New Model Display", "category": "premium"},
            ],
            "timestamp": time.time(),
            "sdk_version": "1.0.0",
        }
        cache_file.write_text(json.dumps(cache_data))

        reset_model_cache()

        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            info = get_model_info("new-model")

        assert info is not None
        assert info["display"] == "New Model Display"
        assert info["category"] == "premium"
