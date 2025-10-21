"""Tests for the ModelRegistry."""

import pytest
from kaicad.core.model_registry import ModelRegistry


def test_model_registry_get_available_models():
    """Test that ModelRegistry returns available models."""
    models = ModelRegistry.get_available_models()
    
    assert isinstance(models, list)
    assert len(models) > 0
    # Should contain real models
    assert any("gpt-4" in m for m in models)


def test_model_registry_get_planning_models():
    """Test that planning models support JSON mode."""
    models = ModelRegistry.get_available_models_for_planning()
    
    assert isinstance(models, list)
    assert len(models) > 0
    # All should be valid models
    for model in models:
        config = ModelRegistry.get_model_config(model)
        assert config is not None
        assert config.supports_json_mode is True


def test_model_registry_get_chat_models():
    """Test that chat models are returned."""
    models = ModelRegistry.get_available_models_for_chat()
    
    assert isinstance(models, list)
    assert len(models) > 0


def test_model_registry_get_model_config():
    """Test getting config for specific models."""
    config = ModelRegistry.get_model_config("gpt-4o-mini")
    
    assert config is not None
    assert config.name == "gpt-4o-mini"
    assert config.supports_json_mode is True


def test_model_registry_invalid_model():
    """Test that invalid models return None."""
    config = ModelRegistry.get_model_config("nonexistent-model")
    
    assert config is None


def test_model_registry_is_valid_model():
    """Test model validation."""
    assert ModelRegistry.is_valid_model("gpt-4o-mini") is True
    assert ModelRegistry.is_valid_model("gpt-4") is True
    assert ModelRegistry.is_valid_model("nonexistent") is False
    assert ModelRegistry.is_valid_model("gpt-5") is False  # Fantasy model


def test_model_registry_get_default_model():
    """Test that default model is valid."""
    default = ModelRegistry.get_default_model()
    
    assert default == "gpt-4o-mini"
    assert ModelRegistry.is_valid_model(default) is True


def test_model_registry_get_display_name():
    """Test getting display names for models."""
    display_name = ModelRegistry.get_model_display_name("gpt-4o-mini")
    
    assert "gpt-4o-mini" in display_name
    assert len(display_name) > len("gpt-4o-mini")  # Should have description


def test_model_registry_caching():
    """Test that model list is cached."""
    ModelRegistry.clear_cache()
    
    models1 = ModelRegistry.get_available_models()
    models2 = ModelRegistry.get_available_models()
    
    # Should return same list (cached)
    assert models1 is models2


def test_model_registry_no_fantasy_models():
    """Test that fantasy models (gpt-5, etc.) are not in the registry."""
    models = ModelRegistry.get_available_models()
    
    # Fantasy models should NOT exist
    assert "gpt-5" not in models
    assert "gpt-5-mini" not in models
    assert "gpt-5-nano" not in models
    assert "gpt-5-pro" not in models
    
    # Validation should fail for fantasy models
    assert ModelRegistry.is_valid_model("gpt-5") is False
    assert ModelRegistry.is_valid_model("gpt-5-mini") is False
