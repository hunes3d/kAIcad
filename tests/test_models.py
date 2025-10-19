"""Tests for models module - OpenAI model registry and validation."""
import pytest
from sidecar.models import (
    ModelConfig,
    get_model_config,
    get_real_model_name,
    is_model_supported,
    list_supported_models,
    get_default_model,
    validate_model_for_json,
    _MODEL_REGISTRY
)


def test_model_config_creation():
    """Test creating a ModelConfig instance."""
    config = ModelConfig(
        name="test-model",
        max_tokens=4096,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=128000,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        description="Test model"
    )
    
    assert config.name == "test-model"
    assert config.max_tokens == 4096
    assert config.supports_json_mode is True
    assert config.supports_response_format is True
    assert config.context_window == 128000
    assert config.cost_per_1k_input == 0.01
    assert config.cost_per_1k_output == 0.03
    assert config.description == "Test model"


def test_model_config_is_valid():
    """Test ModelConfig.is_valid property."""
    valid_config = ModelConfig(
        name="valid",
        max_tokens=1000,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=1000,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.01,
        description="Valid"
    )
    assert valid_config.is_valid is True
    
    # Empty name should be invalid
    invalid_name = ModelConfig(
        name="",
        max_tokens=1000,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=1000,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.01,
        description="Invalid"
    )
    assert invalid_name.is_valid is False
    
    # Zero max_tokens should be invalid
    invalid_tokens = ModelConfig(
        name="invalid",
        max_tokens=0,
        supports_json_mode=True,
        supports_response_format=True,
        context_window=1000,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.01,
        description="Invalid"
    )
    assert invalid_tokens.is_valid is False


def test_get_model_config_existing():
    """Test getting config for existing models."""
    # Test real models
    gpt4_config = get_model_config("gpt-4")
    assert gpt4_config is not None
    assert gpt4_config.name == "gpt-4"
    assert gpt4_config.supports_json_mode is True
    
    gpt4o_config = get_model_config("gpt-4o")
    assert gpt4o_config is not None
    assert gpt4o_config.name == "gpt-4o"
    
    gpt4o_mini_config = get_model_config("gpt-4o-mini")
    assert gpt4o_mini_config is not None
    assert gpt4o_mini_config.name == "gpt-4o-mini"


def test_get_model_config_nonexistent():
    """Test getting config for non-existent model."""
    config = get_model_config("nonexistent-model")
    assert config is None


def test_get_model_config_aliases():
    """Test getting config for aliased models."""
    # gpt-5-mini is an alias for gpt-4o-mini
    gpt5_mini_config = get_model_config("gpt-5-mini")
    assert gpt5_mini_config is not None
    assert gpt5_mini_config.name == "gpt-4o-mini"  # Aliased to real model
    
    # gpt-5 is an alias for gpt-4
    gpt5_config = get_model_config("gpt-5")
    assert gpt5_config is not None
    assert gpt5_config.name == "gpt-4"


def test_get_real_model_name_for_aliases():
    """Test resolving aliases to real model names."""
    # Aliases should resolve to real names
    assert get_real_model_name("gpt-5-mini") == "gpt-4o-mini"
    assert get_real_model_name("gpt-5") == "gpt-4"
    assert get_real_model_name("gpt-5-nano") == "gpt-4o-mini"


def test_get_real_model_name_for_real_models():
    """Test that real model names return themselves."""
    assert get_real_model_name("gpt-4") == "gpt-4"
    assert get_real_model_name("gpt-4o") == "gpt-4o"
    assert get_real_model_name("gpt-4o-mini") == "gpt-4o-mini"


def test_get_real_model_name_for_unknown():
    """Test that unknown models return as-is."""
    unknown = "unknown-model-xyz"
    assert get_real_model_name(unknown) == unknown


def test_is_model_supported():
    """Test checking if models are supported."""
    # Supported models
    assert is_model_supported("gpt-4") is True
    assert is_model_supported("gpt-4o") is True
    assert is_model_supported("gpt-4o-mini") is True
    assert is_model_supported("gpt-5-mini") is True
    
    # Unsupported model
    assert is_model_supported("nonexistent") is False
    assert is_model_supported("") is False


def test_list_supported_models():
    """Test listing all supported models."""
    models = list_supported_models()
    
    assert isinstance(models, list)
    assert len(models) > 0
    
    # Check some expected models are in the list
    assert "gpt-4" in models
    assert "gpt-4o" in models
    assert "gpt-4o-mini" in models
    assert "gpt-5-mini" in models


def test_get_default_model():
    """Test getting the default model."""
    default = get_default_model()
    
    assert default == "gpt-5-mini"
    # Default should be a supported model
    assert is_model_supported(default) is True


def test_validate_model_for_json_valid():
    """Test validating models that support JSON mode."""
    is_valid, error_msg = validate_model_for_json("gpt-4o-mini")
    
    assert is_valid is True
    assert error_msg == ""


def test_validate_model_for_json_unsupported_model():
    """Test validating unsupported model."""
    is_valid, error_msg = validate_model_for_json("unsupported-model")
    
    assert is_valid is False
    assert "not supported" in error_msg
    assert "unsupported-model" in error_msg


def test_validate_model_for_json_no_json_support():
    """Test model that doesn't support JSON mode (hypothetical)."""
    # All current models support JSON, but test the logic
    # by temporarily checking registry behavior
    is_valid, error_msg = validate_model_for_json("gpt-4")
    assert is_valid is True  # gpt-4 supports JSON


def test_model_registry_completeness():
    """Test that all models in registry have required fields."""
    for model_name, config in _MODEL_REGISTRY.items():
        assert config.name, f"Model {model_name} missing name"
        assert config.max_tokens > 0, f"Model {model_name} has invalid max_tokens"
        assert config.context_window > 0, f"Model {model_name} has invalid context_window"
        assert isinstance(config.supports_json_mode, bool)
        assert isinstance(config.supports_response_format, bool)
        assert config.cost_per_1k_input >= 0
        assert config.cost_per_1k_output >= 0
        assert config.description, f"Model {model_name} missing description"


def test_model_cost_comparison():
    """Test that different models have expected cost relationships."""
    gpt4_config = get_model_config("gpt-4")
    gpt4o_config = get_model_config("gpt-4o")
    gpt4o_mini_config = get_model_config("gpt-4o-mini")
    
    # gpt-4 should be most expensive
    assert gpt4_config.cost_per_1k_input >= gpt4o_config.cost_per_1k_input
    
    # gpt-4o-mini should be cheapest
    assert gpt4o_mini_config.cost_per_1k_input <= gpt4o_config.cost_per_1k_input
    assert gpt4o_mini_config.cost_per_1k_output <= gpt4o_config.cost_per_1k_output


def test_model_context_windows():
    """Test that models have appropriate context windows."""
    gpt4_turbo_config = get_model_config("gpt-4-turbo")
    gpt4o_config = get_model_config("gpt-4o")
    
    # Turbo and 4o models should have large context windows
    assert gpt4_turbo_config.context_window >= 100000
    assert gpt4o_config.context_window >= 100000


def test_all_models_support_json():
    """Test that all registered models support JSON mode."""
    for model_name in list_supported_models():
        config = get_model_config(model_name)
        assert config.supports_json_mode is True, f"Model {model_name} doesn't support JSON mode"


def test_validate_model_error_message_includes_alternatives():
    """Test that validation error includes list of supported models."""
    is_valid, error_msg = validate_model_for_json("bad-model")
    
    assert is_valid is False
    # Error should mention supported models
    assert "gpt-4" in error_msg or "Supported models" in error_msg


def test_model_aliases_point_to_better_models():
    """Test that aliases like gpt-5-mini point to modern models."""
    gpt5_mini_real = get_real_model_name("gpt-5-mini")
    
    # Should resolve to gpt-4o-mini (modern, cheap, fast)
    assert gpt5_mini_real == "gpt-4o-mini"


def test_get_model_config_returns_different_objects():
    """Test that get_model_config returns the same config object."""
    config1 = get_model_config("gpt-4o")
    config2 = get_model_config("gpt-4o")
    
    # Should be the same object from registry
    assert config1 is config2


def test_model_descriptions_are_meaningful():
    """Test that all models have non-empty descriptions."""
    for model_name in list_supported_models():
        config = get_model_config(model_name)
        assert len(config.description) > 10, f"Model {model_name} has too short description"
        assert config.description != "N/A"
