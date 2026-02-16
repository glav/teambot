"""Configuration schema definitions for TeamBot."""

import logging

logger = logging.getLogger(__name__)

# JSON schema for configuration validation will be defined here
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "agents": {"type": "array"},
        "workflow": {"type": "object"},
    },
    "required": ["agents"],
}

# Module-level state for lazy loading
# Models come exclusively from SDK via cache - no static fallback
_models_loaded = False
_cached_models: dict[str, dict[str, str]] = {}


def _ensure_models_loaded() -> None:
    """Lazy load models from cache on first access.

    Checks cache validity and loads models. If cache is expired,
    uses expired cache data with warning. If no cache exists,
    models will be empty until refresh_models() is called.

    No static fallback - all model data comes from SDK via cache.
    """
    global _models_loaded, _cached_models

    if _models_loaded:
        return

    from teambot.config.model_cache import is_cache_valid, load_cache

    cache = load_cache()
    if is_cache_valid(cache):
        # Use cached models (valid cache)
        _cached_models = {
            m.id: {
                "display": m.name,
                "category": m.category,
                "multiplier": getattr(m, "multiplier", None),
            }
            for m in cache.models
        }
        _models_loaded = True
        logger.debug(f"Loaded {len(_cached_models)} models from cache")
        return

    # Cache expired - still use it but warn user
    if cache and cache.models:
        _cached_models = {
            m.id: {
                "display": m.name,
                "category": m.category,
                "multiplier": getattr(m, "multiplier", None),
            }
            for m in cache.models
        }
        _models_loaded = True
        logger.warning("Using expired model cache - run '/models --refresh' to update")
        return

    # No cache at all - models will need refresh
    _models_loaded = True  # Mark loaded to prevent repeated attempts
    logger.warning("No model cache available - run '/models --refresh' to fetch models")


def validate_model(model: str | None) -> bool:
    """Validate that a model name is supported by Copilot CLI.

    Uses dynamically discovered models from SDK cache.
    Returns False if no models are loaded (cache empty).

    Args:
        model: Model name to validate.

    Returns:
        True if model is valid, False otherwise.
    """
    if model is None:
        return False
    if not isinstance(model, str):
        return False
    model = model.strip()
    if not model:
        return False

    _ensure_models_loaded()
    if _cached_models:
        return model in _cached_models

    # No models available - cannot validate
    logger.warning(f"Cannot validate model '{model}' - no models loaded from SDK")
    return False


def get_available_models() -> list[str]:
    """Get list of all available model names.

    Returns models from SDK cache. Returns empty list if
    no cache is available (user should run '/models --refresh').

    Returns:
        Sorted list of valid model names, or empty list.
    """
    _ensure_models_loaded()
    if _cached_models:
        return sorted(_cached_models.keys())
    return []  # No fallback - SDK cache is the only source


def get_model_info(model: str) -> dict[str, str] | None:
    """Get display information for a model.

    Args:
        model: Model name.

    Returns:
        Dict with 'display' and 'category' keys, or None if model not found.
    """
    _ensure_models_loaded()
    if _cached_models and model in _cached_models:
        return _cached_models[model]
    return None  # No fallback - SDK cache is the only source


def is_using_cached_models() -> bool:
    """Check if currently using cached (dynamic) models.

    Returns:
        True if using cached models, False if using fallback.
    """
    _ensure_models_loaded()
    return bool(_cached_models)


async def refresh_models() -> bool:
    """Refresh model cache from SDK.

    Fetches models from SDK and updates cache. This is async
    because SDK operations are async.

    Returns:
        True if refresh succeeded, False otherwise.
    """
    global _models_loaded, _cached_models

    try:
        from teambot.config.model_cache import save_cache
        from teambot.copilot.sdk_client import CopilotSDKClient

        client = CopilotSDKClient()
        if not client.is_available():
            logger.warning("SDK not available, cannot refresh models")
            return False

        await client.start()
        try:
            models = await client.list_models()
            if not models:
                logger.warning("SDK returned no models")
                return False

            # Get SDK version for cache metadata
            try:
                import importlib.metadata

                sdk_version = importlib.metadata.version("github-copilot-sdk")
            except Exception:
                sdk_version = "unknown"

            # Save to cache
            if save_cache(models, sdk_version):
                # Update in-memory state
                _cached_models = {
                    m.id: {
                        "display": m.name,
                        "category": m.category,
                        "multiplier": getattr(m, "multiplier", None),
                    }
                    for m in models
                }
                _models_loaded = True
                logger.info(f"Refreshed {len(models)} models from SDK")
                return True
            return False
        finally:
            await client.stop()
    except Exception as e:
        logger.warning(f"Failed to refresh models: {type(e).__name__}")
        return False


def reset_model_cache() -> None:
    """Reset in-memory model cache state.

    Useful for testing or forcing a reload on next access.
    """
    global _models_loaded, _cached_models
    _models_loaded = False
    _cached_models = {}
