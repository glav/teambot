"""Tests for model validation in config schema."""

import json
import time
from unittest.mock import patch

import pytest


@pytest.fixture
def reset_model_state():
    """Reset model cache state between tests."""
    from teambot.config.schema import reset_model_cache

    reset_model_cache()
    yield
    reset_model_cache()


@pytest.fixture
def mock_model_cache(tmp_path, reset_model_state):
    """Create a valid model cache for testing.

    Since static fallback has been removed, tests need cached data.
    """
    cache_dir = tmp_path / ".teambot"
    cache_dir.mkdir()
    cache_file = cache_dir / "model_cache.json"
    cache_data = {
        "models": [
            # Claude models
            {"id": "claude-sonnet-4.5", "name": "Claude Sonnet 4.5", "category": "standard"},
            {"id": "claude-haiku-4.5", "name": "Claude Haiku 4.5", "category": "fast"},
            {"id": "claude-opus-4.5", "name": "Claude Opus 4.5", "category": "premium"},
            {"id": "claude-sonnet-4", "name": "Claude Sonnet 4", "category": "standard"},
            # Gemini models
            {
                "id": "gemini-3-pro-preview",
                "name": "Gemini 3 Pro (Preview)",
                "category": "standard",
            },
            # GPT models
            {"id": "gpt-5.2-codex", "name": "GPT-5.2-Codex", "category": "standard"},
            {"id": "gpt-5.2", "name": "GPT-5.2", "category": "standard"},
            {"id": "gpt-5.1-codex-max", "name": "GPT-5.1-Codex-Max", "category": "standard"},
            {"id": "gpt-5.1-codex", "name": "GPT-5.1-Codex", "category": "standard"},
            {"id": "gpt-5.1", "name": "GPT-5.1", "category": "standard"},
            {"id": "gpt-5", "name": "GPT-5", "category": "standard"},
            {"id": "gpt-5.1-codex-mini", "name": "GPT-5.1-Codex-Mini", "category": "fast"},
            {"id": "gpt-5-mini", "name": "GPT-5 mini", "category": "fast"},
            {"id": "gpt-4.1", "name": "GPT-4.1", "category": "fast"},
        ],
        "timestamp": time.time(),
        "sdk_version": "1.0.0",
    }
    cache_file.write_text(json.dumps(cache_data))

    # Return a context manager for patching
    return tmp_path


class TestModelValidation:
    """Tests for validate_model function."""

    def test_validate_model_valid_claude(self, mock_model_cache):
        """Valid Claude models return True when cached."""
        from teambot.config.schema import validate_model

        with patch("teambot.config.model_cache.Path.cwd", return_value=mock_model_cache):
            assert validate_model("claude-sonnet-4.5") is True
            assert validate_model("claude-haiku-4.5") is True
            assert validate_model("claude-opus-4.5") is True
            assert validate_model("claude-sonnet-4") is True

    def test_validate_model_valid_gpt(self, mock_model_cache):
        """Valid GPT models return True when cached."""
        from teambot.config.schema import validate_model

        with patch("teambot.config.model_cache.Path.cwd", return_value=mock_model_cache):
            assert validate_model("gpt-5.2-codex") is True
            assert validate_model("gpt-5.2") is True
            assert validate_model("gpt-5.1-codex-max") is True
            assert validate_model("gpt-5.1-codex") is True
            assert validate_model("gpt-5.1") is True
            assert validate_model("gpt-5") is True
            assert validate_model("gpt-5.1-codex-mini") is True
            assert validate_model("gpt-5-mini") is True
            assert validate_model("gpt-4.1") is True

    def test_validate_model_valid_gemini(self, mock_model_cache):
        """Valid Gemini models return True when cached."""
        from teambot.config.schema import validate_model

        with patch("teambot.config.model_cache.Path.cwd", return_value=mock_model_cache):
            assert validate_model("gemini-3-pro-preview") is True

    def test_validate_model_invalid(self, mock_model_cache):
        """Invalid model names return False."""
        from teambot.config.schema import validate_model

        with patch("teambot.config.model_cache.Path.cwd", return_value=mock_model_cache):
            assert validate_model("invalid-model") is False
            assert validate_model("gpt-4") is False  # old model
            assert validate_model("claude-3") is False  # old model

    def test_validate_model_none(self, reset_model_state):
        """None returns False."""
        from teambot.config.schema import validate_model

        assert validate_model(None) is False

    def test_validate_model_empty_string(self, reset_model_state):
        """Empty string returns False."""
        from teambot.config.schema import validate_model

        assert validate_model("") is False

    def test_validate_model_whitespace(self, reset_model_state):
        """Whitespace-only returns False."""
        from teambot.config.schema import validate_model

        assert validate_model("  ") is False
        assert validate_model("\t") is False

    def test_validate_model_returns_false_without_cache(self, reset_model_state, tmp_path):
        """Returns False for any model when no cache exists."""
        from teambot.config.schema import validate_model

        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            # Without static fallback, validation fails without cache
            assert validate_model("gpt-5") is False
            assert validate_model("claude-opus-4.5") is False


class TestGetAvailableModels:
    """Tests for get_available_models function."""

    def test_returns_all_models(self, mock_model_cache):
        """Returns complete list of cached models."""
        from teambot.config.schema import get_available_models

        with patch("teambot.config.model_cache.Path.cwd", return_value=mock_model_cache):
            models = get_available_models()

        assert len(models) == 14
        assert "gpt-5" in models
        assert "claude-opus-4.5" in models

    def test_returns_sorted_list(self, mock_model_cache):
        """Returns models in sorted order."""
        from teambot.config.schema import get_available_models

        with patch("teambot.config.model_cache.Path.cwd", return_value=mock_model_cache):
            models = get_available_models()

        assert models == sorted(models)

    def test_returns_empty_list_without_cache(self, reset_model_state, tmp_path):
        """Returns empty list when no cache exists."""
        from teambot.config.schema import get_available_models

        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            models = get_available_models()

        # Without static fallback, returns empty list
        assert models == []


class TestGetModelInfo:
    """Tests for get_model_info function."""

    def test_returns_info_for_valid_model(self, mock_model_cache):
        """Returns display info for valid model."""
        from teambot.config.schema import get_model_info

        with patch("teambot.config.model_cache.Path.cwd", return_value=mock_model_cache):
            info = get_model_info("claude-opus-4.5")

        assert info is not None
        assert "display" in info
        assert "category" in info
        assert info["display"] == "Claude Opus 4.5"
        assert info["category"] == "premium"

    def test_returns_none_for_invalid_model(self, mock_model_cache):
        """Returns None for invalid model."""
        from teambot.config.schema import get_model_info

        with patch("teambot.config.model_cache.Path.cwd", return_value=mock_model_cache):
            assert get_model_info("invalid-model") is None

    def test_returns_none_without_cache(self, reset_model_state, tmp_path):
        """Returns None for any model when no cache exists."""
        from teambot.config.schema import get_model_info

        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            # Without static fallback, returns None
            assert get_model_info("gpt-5") is None


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

    def test_returns_empty_when_cache_missing(self, reset_model_state, tmp_path):
        """Test that empty list is returned when no cache (no static fallback)."""
        from teambot.config.schema import (
            get_available_models,
            reset_model_cache,
        )

        # Reset and mock empty cache dir
        reset_model_cache()

        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            models = get_available_models()

        # Without static fallback, returns empty list
        assert models == []

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
