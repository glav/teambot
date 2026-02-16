"""Tests for model cache module."""

import json
import time
from unittest.mock import patch

import pytest


class TestModelCache:
    """Tests for model cache functionality."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create a temporary .teambot directory for cache."""
        cache_dir = tmp_path / ".teambot"
        cache_dir.mkdir()
        return cache_dir

    @pytest.fixture
    def mock_cwd(self, tmp_path):
        """Mock cwd to use temp directory."""
        with patch("teambot.config.model_cache.Path.cwd", return_value=tmp_path):
            yield tmp_path

    def test_save_and_load_cache_roundtrip(self, mock_cwd, temp_cache_dir):
        """Test saving and loading cache round-trip."""
        from teambot.config.model_cache import load_cache, save_cache

        # Create test models
        class MockModel:
            def __init__(self, id, name, category):
                self.id = id
                self.name = name
                self.category = category

        models = [
            MockModel("gpt-5", "GPT-5", "standard"),
            MockModel("claude-opus-4.5", "Claude Opus 4.5", "premium"),
        ]

        # Save cache
        assert save_cache(models, "1.0.0") is True

        # Load cache
        cache = load_cache()
        assert cache is not None
        assert len(cache.models) == 2
        assert cache.sdk_version == "1.0.0"
        assert cache.timestamp > 0

        # Check model data
        model_ids = {m.id for m in cache.models}
        assert "gpt-5" in model_ids
        assert "claude-opus-4.5" in model_ids

    def test_load_cache_missing_file(self, mock_cwd):
        """Test loading returns None when file doesn't exist."""
        from teambot.config.model_cache import load_cache

        cache = load_cache()
        assert cache is None

    def test_load_cache_corrupted_json(self, mock_cwd, temp_cache_dir):
        """Test loading handles corrupted JSON gracefully."""
        from teambot.config.model_cache import load_cache

        cache_file = temp_cache_dir / "model_cache.json"
        cache_file.write_text("not valid json {")

        cache = load_cache()
        assert cache is None

    def test_cache_ttl_expiration(self, mock_cwd, temp_cache_dir):
        """Test cache expires after TTL."""
        from teambot.config.model_cache import (
            CachedModel,
            ModelCache,
            is_cache_valid,
        )

        # Create cache that expired 1 hour ago
        old_timestamp = time.time() - (25 * 60 * 60)  # 25 hours ago
        cache = ModelCache(
            models=[CachedModel("gpt-5", "GPT-5", "standard")],
            timestamp=old_timestamp,
            sdk_version="1.0.0",
        )

        assert is_cache_valid(cache) is False

    def test_cache_valid_within_ttl(self, mock_cwd, temp_cache_dir):
        """Test cache is valid within TTL."""
        from teambot.config.model_cache import (
            CachedModel,
            ModelCache,
            is_cache_valid,
        )

        # Create cache from 1 hour ago
        recent_timestamp = time.time() - (1 * 60 * 60)
        cache = ModelCache(
            models=[CachedModel("gpt-5", "GPT-5", "standard")],
            timestamp=recent_timestamp,
            sdk_version="1.0.0",
        )

        assert is_cache_valid(cache) is True

    def test_cache_ttl_from_env_var(self, mock_cwd, temp_cache_dir, monkeypatch):
        """Test TTL can be configured via environment variable."""
        from teambot.config.model_cache import (
            CachedModel,
            ModelCache,
            is_cache_valid,
        )

        # Set TTL to 1 hour via env var
        monkeypatch.setenv("TEAMBOT_MODEL_CACHE_TTL", "3600")

        # Create cache from 30 minutes ago (should be valid)
        recent = time.time() - (30 * 60)
        cache = ModelCache(
            models=[CachedModel("gpt-5", "GPT-5", "standard")],
            timestamp=recent,
            sdk_version="1.0.0",
        )
        assert is_cache_valid(cache) is True

        # Create cache from 2 hours ago (should be expired)
        old = time.time() - (2 * 60 * 60)
        cache_old = ModelCache(
            models=[CachedModel("gpt-5", "GPT-5", "standard")],
            timestamp=old,
            sdk_version="1.0.0",
        )
        assert is_cache_valid(cache_old) is False

    def test_clear_cache(self, mock_cwd, temp_cache_dir):
        """Test clearing cache file."""
        from teambot.config.model_cache import clear_cache, save_cache

        class MockModel:
            id = "test"
            name = "Test"
            category = "standard"

        save_cache([MockModel()], "1.0.0")

        cache_file = temp_cache_dir / "model_cache.json"
        assert cache_file.exists()

        assert clear_cache() is True
        assert not cache_file.exists()

    def test_clear_cache_nonexistent(self, mock_cwd):
        """Test clearing cache when file doesn't exist."""
        from teambot.config.model_cache import clear_cache

        # Should succeed even if file doesn't exist
        assert clear_cache() is True

    def test_get_cached_models_valid(self, mock_cwd, temp_cache_dir):
        """Test getting cached models when valid."""
        from teambot.config.model_cache import get_cached_models, save_cache

        class MockModel:
            def __init__(self, id, name, category):
                self.id = id
                self.name = name
                self.category = category

        models = [MockModel("gpt-5", "GPT-5", "standard")]
        save_cache(models, "1.0.0")

        cached = get_cached_models()
        assert len(cached) == 1
        assert cached[0].id == "gpt-5"

    def test_get_cached_models_expired(self, mock_cwd, temp_cache_dir):
        """Test getting cached models returns empty when expired."""
        from teambot.config.model_cache import get_cached_models

        # Write expired cache directly
        cache_file = temp_cache_dir / "model_cache.json"
        old_timestamp = time.time() - (25 * 60 * 60)
        cache_data = {
            "models": [{"id": "gpt-5", "name": "GPT-5", "category": "standard"}],
            "timestamp": old_timestamp,
            "sdk_version": "1.0.0",
        }
        cache_file.write_text(json.dumps(cache_data))

        cached = get_cached_models()
        assert cached == []

    def test_get_cache_timestamp(self, mock_cwd, temp_cache_dir):
        """Test getting cache timestamp."""
        from teambot.config.model_cache import get_cache_timestamp, save_cache

        class MockModel:
            id = "test"
            name = "Test"
            category = "standard"

        before = time.time()
        save_cache([MockModel()], "1.0.0")
        after = time.time()

        ts = get_cache_timestamp()
        assert ts is not None
        assert before <= ts <= after

    def test_get_cache_timestamp_missing(self, mock_cwd):
        """Test getting timestamp when no cache."""
        from teambot.config.model_cache import get_cache_timestamp

        ts = get_cache_timestamp()
        assert ts is None

    def test_save_cache_with_dicts(self, mock_cwd, temp_cache_dir):
        """Test saving cache with dict models."""
        from teambot.config.model_cache import load_cache, save_cache

        models = [
            {"id": "gpt-5", "name": "GPT-5", "category": "standard"},
            {"id": "claude-opus-4.5", "name": "Claude Opus", "category": "premium"},
        ]

        assert save_cache(models, "1.0.0") is True

        cache = load_cache()
        assert cache is not None
        assert len(cache.models) == 2

    def test_creates_cache_directory(self, mock_cwd):
        """Test cache dir is created if missing."""
        from teambot.config.model_cache import save_cache

        cache_dir = mock_cwd / ".teambot"
        assert not cache_dir.exists()

        class MockModel:
            id = "test"
            name = "Test"
            category = "standard"

        save_cache([MockModel()], "1.0.0")
        assert cache_dir.exists()
