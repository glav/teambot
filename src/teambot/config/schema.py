"""Configuration schema definitions for TeamBot."""

# JSON schema for configuration validation will be defined here
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "agents": {"type": "array"},
        "workflow": {"type": "object"},
    },
    "required": ["agents"],
}

# Valid models supported by GitHub Copilot CLI
# Source: copilot --help output, verified 2026-02-04
VALID_MODELS: set[str] = {
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

# Model display information
MODEL_INFO: dict[str, dict[str, str]] = {
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


def validate_model(model: str | None) -> bool:
    """Validate that a model name is supported by Copilot CLI.

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
    return model in VALID_MODELS


def get_available_models() -> list[str]:
    """Get list of all available model names.

    Returns:
        Sorted list of valid model names.
    """
    return sorted(VALID_MODELS)


def get_model_info(model: str) -> dict[str, str] | None:
    """Get display information for a model.

    Args:
        model: Model name.

    Returns:
        Dict with 'display' and 'category' keys, or None if invalid.
    """
    return MODEL_INFO.get(model)
