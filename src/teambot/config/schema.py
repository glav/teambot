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

# Static fallback models (used when SDK and cache unavailable)
# Source: copilot --help output, verified 2026-02-04
_FALLBACK_MODELS: set[str] = {
    # Claude models
    "claude-sonnet-4.5",
    "claude-haiku-4.5",
    "claude-opus-4.5",
    "claude-sonnet-4",
    # Gemini models
    "gemini-3-pro-preview",
    # GPT models
    "gpt-5.2-codex",
    "gpt-5.2",
    "gpt-5.1-codex-max",
    "gpt-5.1-codex",
    "gpt-5.1",
    "gpt-5",
    "gpt-5.1-codex-mini",
    "gpt-5-mini",
    "gpt-4.1",
}

# Static fallback model info
_FALLBACK_MODEL_INFO: dict[str, dict[str, str]] = {
    "claude-sonnet-4.5": {"display": "Claude Sonnet 4.5", "category": "standard"},
    "claude-haiku-4.5": {"display": "Claude Haiku 4.5", "category": "fast"},
    "claude-opus-4.5": {"display": "Claude Opus 4.5", "category": "premium"},
    "claude-sonnet-4": {"display": "Claude Sonnet 4", "category": "standard"},
    "gemini-3-pro-preview": {"display": "Gemini 3 Pro (Preview)", "category": "standard"},
    "gpt-5.2-codex": {"display": "GPT-5.2-Codex", "category": "standard"},
    "gpt-5.2": {"display": "GPT-5.2", "category": "standard"},
    "gpt-5.1-codex-max": {"display": "GPT-5.1-Codex-Max", "category": "standard"},
    "gpt-5.1-codex": {"display": "GPT-5.1-Codex", "category": "standard"},
    "gpt-5.1": {"display": "GPT-5.1", "category": "standard"},
    "gpt-5": {"display": "GPT-5", "category": "standard"},
    "gpt-5.1-codex-mini": {"display": "GPT-5.1-Codex-Mini", "category": "fast"},
    "gpt-5-mini": {"display": "GPT-5 mini", "category": "fast"},
    "gpt-4.1": {"display": "GPT-4.1", "category": "fast"},
}

# Backward compatibility: expose static sets for imports
# NOTE: Use get_available_models() instead for dynamic discovery
VALID_MODELS = _FALLBACK_MODELS
MODEL_INFO = _FALLBACK_MODEL_INFO

# Module-level state for lazy loading
_models_loaded = False
_cached_models: dict[str, dict[str, str]] = {}


def _ensure_models_loaded() -> None:
    """Lazy load models from cache on first access.

    Checks cache validity and loads models. If cache is expired
    or missing, attempts async refresh via SDK (if available).
    Falls back to static list if SDK unavailable.
    """
    global _models_loaded, _cached_models

    if _models_loaded:
        return

    from teambot.config.model_cache import is_cache_valid, load_cache

    cache = load_cache()
    if is_cache_valid(cache):
        # Use cached models
        _cached_models = {m.id: {"display": m.name, "category": m.category} for m in cache.models}
        _models_loaded = True
        logger.debug(f"Loaded {len(_cached_models)} models from cache")
        return

    # Cache expired or missing - try to refresh from SDK
    # Note: This is synchronous; async refresh happens via refresh_models()
    logger.debug("Cache expired or missing, using fallback models")
    _models_loaded = True  # Mark loaded to prevent infinite recursion


def validate_model(model: str | None) -> bool:
    """Validate that a model name is supported by Copilot CLI.

    Uses dynamically discovered models when available, falls back
    to static list otherwise.

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

    # Try dynamic models first
    _ensure_models_loaded()
    if _cached_models:
        return model in _cached_models

    # Fallback to static list
    return model in _FALLBACK_MODELS


def get_available_models() -> list[str]:
    """Get list of all available model names.

    Returns dynamically discovered models when available,
    falls back to static list otherwise.

    Returns:
        Sorted list of valid model names.
    """
    _ensure_models_loaded()
    if _cached_models:
        return sorted(_cached_models.keys())
    return sorted(_FALLBACK_MODELS)


def get_model_info(model: str) -> dict[str, str] | None:
    """Get display information for a model.

    Args:
        model: Model name.

    Returns:
        Dict with 'display' and 'category' keys, or None if invalid.
    """
    _ensure_models_loaded()
    if _cached_models and model in _cached_models:
        return _cached_models[model]
    return _FALLBACK_MODEL_INFO.get(model)


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
                _cached_models = {m.id: {"display": m.name, "category": m.category} for m in models}
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
