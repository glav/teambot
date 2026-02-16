"""Model cache for dynamic model discovery.

Provides TTL-based caching of SDK model data for offline support
and lazy loading without startup overhead.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default cache TTL: 24 hours
DEFAULT_CACHE_TTL_SECONDS = 24 * 60 * 60

# Cache file location relative to project root
CACHE_FILE_NAME = "model_cache.json"
CACHE_DIR_NAME = ".teambot"


@dataclass
class CachedModel:
    """Cached model information.

    Attributes:
        id: Model identifier.
        name: Display name.
        category: Model tier (standard/fast/premium).
    """

    id: str
    name: str
    category: str


@dataclass
class ModelCache:
    """Cached model data with metadata.

    Attributes:
        models: List of cached models.
        timestamp: Unix timestamp when cache was created.
        sdk_version: SDK version that provided the data.
    """

    models: list[CachedModel]
    timestamp: float
    sdk_version: str


def _get_cache_ttl() -> int:
    """Get cache TTL from environment or default.

    Returns:
        TTL in seconds.
    """
    env_ttl = os.environ.get("TEAMBOT_MODEL_CACHE_TTL")
    if env_ttl:
        try:
            return int(env_ttl)
        except ValueError:
            logger.warning(f"Invalid TEAMBOT_MODEL_CACHE_TTL: {env_ttl}, using default")
    return DEFAULT_CACHE_TTL_SECONDS


def _get_cache_path() -> Path:
    """Get path to cache file.

    Returns:
        Path to model_cache.json in .teambot directory.
    """
    # Try to find .teambot directory in current working directory
    cwd = Path.cwd()
    cache_dir = cwd / CACHE_DIR_NAME
    return cache_dir / CACHE_FILE_NAME


def is_cache_valid(cache: ModelCache | None) -> bool:
    """Check if cache is valid (not expired).

    Args:
        cache: Cache data to check, or None.

    Returns:
        True if cache exists and is not expired.
    """
    if cache is None:
        return False

    ttl = _get_cache_ttl()
    age = time.time() - cache.timestamp
    return age < ttl


def load_cache() -> ModelCache | None:
    """Load model cache from disk.

    Returns:
        ModelCache if valid file exists, None otherwise.
    """
    cache_path = _get_cache_path()

    if not cache_path.exists():
        logger.debug(f"Cache file not found: {cache_path}")
        return None

    try:
        with cache_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        models = [
            CachedModel(
                id=m["id"],
                name=m["name"],
                category=m["category"],
            )
            for m in data.get("models", [])
        ]

        return ModelCache(
            models=models,
            timestamp=data.get("timestamp", 0),
            sdk_version=data.get("sdk_version", "unknown"),
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Corrupted cache file, ignoring: {type(e).__name__}")
        return None
    except OSError as e:
        logger.warning(f"Failed to read cache: {type(e).__name__}")
        return None


def save_cache(models: list[Any], sdk_version: str = "unknown") -> bool:
    """Save model list to cache file.

    Args:
        models: List of model objects with id, name, category attributes.
        sdk_version: SDK version string for tracking.

    Returns:
        True if saved successfully, False otherwise.
    """
    cache_path = _get_cache_path()

    # Ensure .teambot directory exists
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Convert models to dicts
        model_dicts = []
        for m in models:
            if hasattr(m, "id"):
                model_dicts.append(
                    {
                        "id": m.id,
                        "name": getattr(m, "name", m.id),
                        "category": getattr(m, "category", "standard"),
                    }
                )
            elif isinstance(m, dict):
                model_dicts.append(
                    {
                        "id": m.get("id", ""),
                        "name": m.get("name", m.get("id", "")),
                        "category": m.get("category", "standard"),
                    }
                )

        cache_data = {
            "models": model_dicts,
            "timestamp": time.time(),
            "sdk_version": sdk_version,
        }

        with cache_path.open("w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

        logger.debug(f"Saved {len(model_dicts)} models to cache")
        return True

    except OSError as e:
        logger.warning(f"Failed to save cache: {type(e).__name__}")
        return False


def clear_cache() -> bool:
    """Remove the cache file.

    Returns:
        True if cleared or didn't exist, False on error.
    """
    cache_path = _get_cache_path()

    if not cache_path.exists():
        return True

    try:
        cache_path.unlink()
        logger.debug("Cache cleared")
        return True
    except OSError as e:
        logger.warning(f"Failed to clear cache: {type(e).__name__}")
        return False


def get_cached_models() -> list[CachedModel]:
    """Get models from cache if valid.

    Returns:
        List of cached models, or empty list if cache invalid.
    """
    cache = load_cache()
    if is_cache_valid(cache):
        return cache.models
    return []


def get_cache_timestamp() -> float | None:
    """Get timestamp of current cache.

    Returns:
        Unix timestamp, or None if no cache.
    """
    cache = load_cache()
    if cache:
        return cache.timestamp
    return None
