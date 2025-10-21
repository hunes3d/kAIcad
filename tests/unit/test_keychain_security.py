"""Tests for keychain storage security."""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile

from kaicad.config.settings import Settings, KEYRING_AVAILABLE


def test_keyring_stores_api_key_when_available():
    """Test that API key is stored in keyring when available."""
    if not KEYRING_AVAILABLE:
        pytest.skip("Keyring not available")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        
        with patch("kaicad.config.settings.CONFIG_PATH", config_path):
            with patch("kaicad.config.settings.KEYRING_AVAILABLE", True):
                with patch("kaicad.config.settings.keyring") as mock_keyring:
                    # Create and save settings
                    settings = Settings(openai_api_key="sk-test-key-123")
                    settings.save()
                    
                    # Verify keyring was called
                    mock_keyring.set_password.assert_called_once_with(
                        "kAIcad",
                        "openai_api_key", 
                        "sk-test-key-123"
                    )
                    
                    # Verify API key NOT in config file
                    if config_path.exists():
                        config_data = json.loads(config_path.read_text())
                        assert config_data.get("openai_api_key") == ""


def test_keyring_loads_api_key_when_available():
    """Test that API key is loaded from keyring when available."""
    if not KEYRING_AVAILABLE:
        pytest.skip("Keyring not available")
    
    # Ensure env var is not set
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            with patch("kaicad.config.settings.CONFIG_PATH", config_path):
                with patch("kaicad.config.settings.KEYRING_AVAILABLE", True):
                    with patch("kaicad.config.settings.keyring") as mock_keyring:
                        # Mock keyring returning stored key
                        mock_keyring.get_password.return_value = "sk-from-keyring"
                        
                        # Load settings
                        settings = Settings.load()
                        
                        # Verify keyring was queried
                        mock_keyring.get_password.assert_called_once_with(
                            "kAIcad",
                            "openai_api_key"
                        )
                        
                        # Verify API key loaded from keyring
                        assert settings.openai_api_key == "sk-from-keyring"
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key


def test_fallback_to_config_file_when_keyring_unavailable():
    """Test that API key falls back to config file when keyring unavailable."""
    # Remove env var so config file is used
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create config with API key
            config_data = {
                "openai_model": "gpt-4o-mini",
                "openai_temperature": 0.0,
                "openai_api_key": "sk-from-config-file",
                "default_project": str(Path.cwd()),
                "dock_right": True
            }
            config_path.write_text(json.dumps(config_data))
            
            with patch("kaicad.config.settings.CONFIG_PATH", config_path):
                with patch("kaicad.config.settings.KEYRING_AVAILABLE", False):
                    # Load settings
                    settings = Settings.load()
                    
                    # Verify API key loaded from config file
                    assert settings.openai_api_key == "sk-from-config-file"
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key


def test_no_plaintext_storage_with_keyring():
    """Test that API key is not stored in plaintext when keyring is available."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        
        with patch("kaicad.config.settings.CONFIG_PATH", config_path):
            with patch("kaicad.config.settings.KEYRING_AVAILABLE", True):
                with patch("kaicad.config.settings.keyring") as mock_keyring:
                    # Create and save settings
                    settings = Settings(openai_api_key="sk-secret-key")
                    settings.save()
                    
                    # Read config file directly
                    if config_path.exists():
                        config_text = config_path.read_text()
                        
                        # Verify secret key NOT in file
                        assert "sk-secret-key" not in config_text
                        
                        # Verify empty key in JSON
                        config_data = json.loads(config_text)
                        assert config_data.get("openai_api_key") == ""


def test_keyring_error_graceful_fallback():
    """Test that keyring errors are handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        
        with patch("kaicad.config.settings.CONFIG_PATH", config_path):
            with patch("kaicad.config.settings.KEYRING_AVAILABLE", True):
                with patch("kaicad.config.settings.keyring") as mock_keyring:
                    # Mock keyring raising error
                    mock_keyring.set_password.side_effect = Exception("Keyring error")
                    
                    # Should not raise - just log warning
                    settings = Settings(openai_api_key="sk-test")
                    settings.save()  # Should complete without error


def test_env_var_takes_precedence():
    """Test that environment variable takes precedence over keyring/config."""
    old_key = os.environ.get("OPENAI_API_KEY")
    try:
        os.environ["OPENAI_API_KEY"] = "sk-from-env"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            with patch("kaicad.config.settings.CONFIG_PATH", config_path):
                with patch("kaicad.config.settings.KEYRING_AVAILABLE", True):
                    with patch("kaicad.config.settings.keyring") as mock_keyring:
                        mock_keyring.get_password.return_value = "sk-from-keyring"
                        
                        # Load settings
                        settings = Settings.load()
                        
                        # Verify env var takes precedence
                        assert settings.openai_api_key == "sk-from-env"
    finally:
        if old_key:
            os.environ["OPENAI_API_KEY"] = old_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)
