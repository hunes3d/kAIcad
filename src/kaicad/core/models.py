"""Model registry for supported OpenAI models with their capabilities and limits."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ModelConfig:
    """Configuration for an OpenAI model."""

    name: str
    max_tokens: int
    supports_json_mode: bool
    supports_response_format: bool
    context_window: int
    cost_per_1k_input: float  # USD
    cost_per_1k_output: float  # USD
    description: str

    @property
    def is_valid(self) -> bool:
        """Check if this model configuration is valid."""
        return bool(self.name and self.max_tokens > 0)


# Registry of supported models
_MODEL_REGISTRY: Dict[str, ModelConfig] = {
    "gpt-4": ModelConfig(
        name="gpt-4",
        max_tokens=8192,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=8192,
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06,
        description="Most capable model, best for complex schematics",
    ),
    "gpt-4-turbo": ModelConfig(
        name="gpt-4-turbo",
        max_tokens=4096,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=128000,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        description="Fast and capable, good for most tasks",
    ),
    "gpt-4o": ModelConfig(
        name="gpt-4o",
        max_tokens=4096,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=128000,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        description="Optimized for speed and cost",
    ),
    "gpt-4o-mini": ModelConfig(
        name="gpt-4o-mini",
        max_tokens=4096,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=128000,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        description="Smallest and fastest, great for simple tasks",
    ),
    # Placeholder names for compatibility (map to real models)
    "gpt-5": ModelConfig(
        name="gpt-4",
        max_tokens=8192,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=8192,
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06,
        description="Alias for gpt-4 (most capable)",
    ),
    "gpt-5-mini": ModelConfig(
        name="gpt-4o-mini",
        max_tokens=4096,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=128000,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        description="Alias for gpt-4o-mini (recommended default)",
    ),
    "gpt-5-nano": ModelConfig(
        name="gpt-4o-mini",
        max_tokens=4096,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=128000,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        description="Alias for gpt-4o-mini (fastest)",
    ),
}


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """Get configuration for a model by name.

    Args:
        model_name: Name of the model (e.g., "gpt-4", "gpt-5-mini")

    Returns:
        ModelConfig if found, None otherwise
    """
    return _MODEL_REGISTRY.get(model_name)


def get_real_model_name(model_name: str) -> str:
    """Get the real OpenAI model name from an alias.

    Args:
        model_name: Model name or alias

    Returns:
        Real model name to use with OpenAI API
    """
    config = get_model_config(model_name)
    if config:
        return config.name
    return model_name  # Return as-is if not in registry


def is_model_supported(model_name: str) -> bool:
    """Check if a model is supported.

    Args:
        model_name: Name of the model

    Returns:
        True if model is in registry, False otherwise
    """
    return model_name in _MODEL_REGISTRY


def list_supported_models() -> list[str]:
    """Get list of all supported model names.

    Returns:
        List of model names
    """
    return list(_MODEL_REGISTRY.keys())


def get_default_model() -> str:
    """Get the default model name.

    Returns:
        Default model name (gpt-5-mini -> gpt-4o-mini)
    """
    return "gpt-5-mini"


def validate_model_for_json(model_name: str) -> tuple[bool, str]:
    """Validate that a model supports JSON mode.

    Args:
        model_name: Name of the model to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    config = get_model_config(model_name)
    if not config:
        return False, f"Model '{model_name}' is not supported. Supported models: {', '.join(list_supported_models())}"

    if not config.supports_json_mode:
        return False, f"Model '{model_name}' does not support JSON mode (required for plan generation)"

    return True, ""


# Public API
__all__ = [
    "ModelConfig",
    "get_model_config",
    "get_real_model_name",
    "is_model_supported",
    "list_supported_models",
    "get_default_model",
    "validate_model_for_json",
]
