"""Centralized model registry for OpenAI models.

This module provides a single source of truth for available models,
replacing hard-coded fantasy model names with real OpenAI models.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from openai import OpenAI

from kaicad.core.models import ModelConfig

logger = logging.getLogger(__name__)


# Real OpenAI models we support (no fantasy names)
_REAL_MODEL_REGISTRY: Dict[str, ModelConfig] = {
    "gpt-4": ModelConfig(
        name="gpt-4",
        max_tokens=8192,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=8192,
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06,
        description="Most capable GPT-4 model, best for complex schematics",
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
        description="Optimized GPT-4 for speed and cost",
    ),
    "gpt-4o-mini": ModelConfig(
        name="gpt-4o-mini",
        max_tokens=4096,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=128000,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        description="Efficient and fast, great for simple tasks (recommended)",
    ),
}

# Fallback models if OpenAI API query fails
_FALLBACK_MODEL_LIST = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4"]


class ModelRegistry:
    """Central registry for OpenAI models with dynamic fetching capabilities."""

    _cached_models: Optional[List[str]] = None

    @staticmethod
    def get_available_models() -> List[str]:
        """Get list of available model names.

        First tries to fetch from OpenAI API, falls back to known list.
        Results are cached to avoid repeated API calls.

        Returns:
            List of available model names
        """
        if ModelRegistry._cached_models is not None:
            return ModelRegistry._cached_models

        try:
            # Try to fetch real models from OpenAI
            client = OpenAI()
            models = client.models.list()
            available = [
                m.id
                for m in models.data
                if m.id.startswith("gpt-4") and m.id in _REAL_MODEL_REGISTRY
            ]
            if available:
                logger.info(f"Fetched {len(available)} models from OpenAI API")
                ModelRegistry._cached_models = sorted(
                    available, key=lambda x: _REAL_MODEL_REGISTRY[x].cost_per_1k_input
                )
                return ModelRegistry._cached_models
        except Exception as e:
            logger.debug(f"Could not fetch models from OpenAI API: {e}")

        # Fallback to known models
        logger.info("Using fallback model list")
        ModelRegistry._cached_models = _FALLBACK_MODEL_LIST
        return ModelRegistry._cached_models

    @staticmethod
    def get_available_models_for_planning() -> List[str]:
        """Get models suitable for plan generation (requires JSON mode).

        Returns:
            List of model names that support JSON mode
        """
        all_models = ModelRegistry.get_available_models()
        return [
            model
            for model in all_models
            if model in _REAL_MODEL_REGISTRY
            and _REAL_MODEL_REGISTRY[model].supports_json_mode
        ]

    @staticmethod
    def get_available_models_for_chat() -> List[str]:
        """Get models suitable for chat conversations.

        Returns:
            List of model names suitable for chat
        """
        # For now, all models support chat
        return ModelRegistry.get_available_models()

    @staticmethod
    def get_model_config(model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            ModelConfig if found, None otherwise
        """
        return _REAL_MODEL_REGISTRY.get(model_name)

    @staticmethod
    def is_valid_model(model_name: str) -> bool:
        """Check if a model name is valid.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model is in registry, False otherwise
        """
        return model_name in _REAL_MODEL_REGISTRY

    @staticmethod
    def get_default_model() -> str:
        """Get the recommended default model.

        Returns:
            Default model name (gpt-4o-mini for cost efficiency)
        """
        return "gpt-4o-mini"

    @staticmethod
    def get_model_display_name(model_name: str) -> str:
        """Get a human-friendly display name for a model.

        Args:
            model_name: Name of the model

        Returns:
            Display name with description if available
        """
        config = ModelRegistry.get_model_config(model_name)
        if config:
            return f"{model_name} - {config.description}"
        return model_name

    @staticmethod
    def clear_cache() -> None:
        """Clear cached model list to force refresh."""
        ModelRegistry._cached_models = None


# Public API
__all__ = [
    "ModelRegistry",
]
