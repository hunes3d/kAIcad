"""Tests for settings module."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sidecar.settings import (
    KEYRING_AVAILABLE,
    KEYRING_SERVICE,
    KEYRING_USERNAME,
    Settings,
    get_config_dir,
)


def test_get_config_dir_windows():
    """Test that get_config_dir returns correct path on Windows."""
    with patch("sys.platform", "win32"):
        with patch.dict(os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}):
            config_dir = get_config_dir()
            assert str(config_dir) == "C:\\Users\\Test\\AppData\\Roaming\\kAIcad"


def test_get_config_dir_macos():
    """Test that get_config_dir returns correct path on macOS."""
    with patch("sys.platform", "darwin"):
        with patch("pathlib.Path.home", return_value=Path("/Users/test")):
            config_dir = get_config_dir()
            # Use PurePosixPath for consistent path representation
            from pathlib import PurePosixPath

            assert PurePosixPath(config_dir) == PurePosixPath("/Users/test/Library/Application Support/kAIcad")


def test_get_config_dir_linux():
    """Test that get_config_dir returns correct path on Linux."""
    with patch("sys.platform", "linux"):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/home/test/.config"}, clear=False):
            config_dir = get_config_dir()
            from pathlib import PurePosixPath

            assert PurePosixPath(config_dir) == PurePosixPath("/home/test/.config/kAIcad")


def test_get_config_dir_linux_no_xdg():
    """Test Linux fallback when XDG_CONFIG_HOME is not set."""
    with patch("sys.platform", "linux"):
        env_copy = os.environ.copy()
        env_copy.pop("XDG_CONFIG_HOME", None)
        with patch.dict(os.environ, env_copy, clear=True):
            with patch("pathlib.Path.home", return_value=Path("/home/test")):
                config_dir = get_config_dir()
                from pathlib import PurePosixPath

                assert PurePosixPath(config_dir) == PurePosixPath("/home/test/.config/kAIcad")


def test_settings_defaults():
    """Test that Settings has correct default values."""
    settings = Settings()

    assert settings.openai_model == "gpt-5-mini"
    assert settings.openai_temperature == 0.0
    assert settings.openai_api_key == ""
    assert settings.default_project == str(Path.cwd())
    assert settings.dock_right is True


def test_settings_load_from_env():
    """Test that Settings.load() reads from environment variables."""
    with patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "sk-test-env-key", "OPENAI_MODEL": "gpt-4o", "OPENAI_TEMPERATURE": "0.7"},
        clear=False,
    ):
        with patch("sidecar.settings.CONFIG_PATH") as mock_path:
            mock_path.exists.return_value = False
            # Also mock keyring to prevent it from returning a stored key
            with patch("sidecar.settings.keyring") as mock_keyring:
                mock_keyring.get_password.return_value = None

                settings = Settings.load()

                assert settings.openai_api_key == "sk-test-env-key"
                assert settings.openai_model == "gpt-4o"
                assert settings.openai_temperature == 0.7


def test_settings_load_from_config_file():
    """Test that Settings.load() reads from config file."""
    config_data = {
        "openai_model": "gpt-4o-mini",
        "openai_temperature": 0.5,
        "openai_api_key": "sk-test-file-key",
        "default_project": "/path/to/project",
        "dock_right": False,
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_path.write_text(json.dumps(config_data), encoding="utf-8")

        with patch("sidecar.settings.CONFIG_PATH", config_path):
            with patch("sidecar.settings.KEYRING_AVAILABLE", False):
                settings = Settings.load()

                assert settings.openai_model == "gpt-4o-mini"
                assert settings.openai_temperature == 0.5
                assert settings.openai_api_key == "sk-test-file-key"
                assert settings.default_project == "/path/to/project"
                assert settings.dock_right is False


def test_settings_load_env_overrides_config():
    """Test that environment variables override config file for model and temperature."""
    config_data = {
        "openai_model": "gpt-4o-mini",
        "openai_temperature": 0.3,
        "openai_api_key": "",  # Empty in config so env can override
    }

    # Save current env state
    old_model = os.environ.get("OPENAI_MODEL")
    old_temp = os.environ.get("OPENAI_TEMPERATURE")
    old_key = os.environ.get("OPENAI_API_KEY")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            with patch("sidecar.settings.CONFIG_PATH", config_path):
                with patch("sidecar.settings.KEYRING_AVAILABLE", False):
                    # Set environment variables
                    os.environ["OPENAI_MODEL"] = "gpt-4o"
                    os.environ["OPENAI_TEMPERATURE"] = "0.7"
                    os.environ["OPENAI_API_KEY"] = "sk-env-key"

                    settings = Settings.load()

                    # Env should override config for model and temp
                    # API key uses env when config is empty
                    assert settings.openai_model == "gpt-4o"
                    assert settings.openai_temperature == 0.7
                    assert settings.openai_api_key == "sk-env-key"
    finally:
        # Restore env
        if old_model is not None:
            os.environ["OPENAI_MODEL"] = old_model
        else:
            os.environ.pop("OPENAI_MODEL", None)
        if old_temp is not None:
            os.environ["OPENAI_TEMPERATURE"] = old_temp
        else:
            os.environ.pop("OPENAI_TEMPERATURE", None)
        if old_key is not None:
            os.environ["OPENAI_API_KEY"] = old_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)


def test_settings_load_with_keyring():
    """Test that Settings.load() uses keyring for API key."""
    if not KEYRING_AVAILABLE:
        pytest.skip("keyring not available")

    config_data = {"openai_model": "gpt-4o", "openai_api_key": ""}

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        config_path.write_text(json.dumps(config_data), encoding="utf-8")

        with patch("sidecar.settings.CONFIG_PATH", config_path):
            with patch("sidecar.settings.keyring") as mock_keyring:
                mock_keyring.get_password.return_value = "sk-keyring-key"

                settings = Settings.load()

                assert settings.openai_api_key == "sk-keyring-key"
                mock_keyring.get_password.assert_called_once_with(KEYRING_SERVICE, KEYRING_USERNAME)


def test_settings_save():
    """Test that Settings.save() writes to config file."""
    settings = Settings(
        openai_model="gpt-4o",
        openai_temperature=0.8,
        openai_api_key="sk-test-key",
        default_project="/test/project",
        dock_right=False,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "config"
        config_path = config_dir / "config.json"

        with patch("sidecar.settings.CONFIG_DIR", config_dir):
            with patch("sidecar.settings.CONFIG_PATH", config_path):
                with patch("sidecar.settings.KEYRING_AVAILABLE", False):
                    settings.save()

                    assert config_path.exists()
                    saved_data = json.loads(config_path.read_text(encoding="utf-8"))

                    assert saved_data["openai_model"] == "gpt-4o"
                    assert saved_data["openai_temperature"] == 0.8
                    assert saved_data["default_project"] == "/test/project"
                    assert saved_data["dock_right"] is False


def test_settings_save_with_keyring():
    """Test that Settings.save() uses keyring for API key."""
    if not KEYRING_AVAILABLE:
        pytest.skip("keyring not available")

    settings = Settings(openai_api_key="sk-secret-key")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        config_path = config_dir / "config.json"

        with patch("sidecar.settings.CONFIG_DIR", config_dir):
            with patch("sidecar.settings.CONFIG_PATH", config_path):
                with patch("sidecar.settings.keyring") as mock_keyring:
                    settings.save()

                    # API key should be saved to keyring
                    mock_keyring.set_password.assert_called_once_with(
                        KEYRING_SERVICE, KEYRING_USERNAME, "sk-secret-key"
                    )

                    # API key should NOT be in config file
                    saved_data = json.loads(config_path.read_text(encoding="utf-8"))
                    assert saved_data["openai_api_key"] == ""


def test_settings_apply_env():
    """Test that Settings.apply_env() sets environment variables."""
    settings = Settings(openai_model="gpt-4o", openai_temperature=0.9, openai_api_key="sk-apply-test")

    # Clear relevant env vars
    for key in ["OPENAI_MODEL", "OPENAI_TEMPERATURE", "OPENAI_API_KEY"]:
        os.environ.pop(key, None)

    settings.apply_env()

    assert os.environ["OPENAI_MODEL"] == "gpt-4o"
    assert os.environ["OPENAI_TEMPERATURE"] == "0.9"
    assert os.environ["OPENAI_API_KEY"] == "sk-apply-test"


def test_settings_load_invalid_config_file():
    """Test that Settings.load() handles corrupt config file gracefully."""
    old_model = os.environ.get("OPENAI_MODEL")

    try:
        # Clear OPENAI_MODEL to test defaults
        os.environ.pop("OPENAI_MODEL", None)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{ invalid json }", encoding="utf-8")

            with patch("sidecar.settings.CONFIG_PATH", config_path):
                with patch("sidecar.settings.KEYRING_AVAILABLE", False):
                    # Should not raise, should use defaults
                    settings = Settings.load()

                    assert settings.openai_model == "gpt-5-mini"  # default
    finally:
        if old_model is not None:
            os.environ["OPENAI_MODEL"] = old_model


def test_settings_save_keyring_error():
    """Test that Settings.save() handles keyring errors gracefully."""
    if not KEYRING_AVAILABLE:
        pytest.skip("keyring not available")

    settings = Settings(openai_api_key="sk-test")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        config_path = config_dir / "config.json"

        with patch("sidecar.settings.CONFIG_DIR", config_dir):
            with patch("sidecar.settings.CONFIG_PATH", config_path):
                with patch("sidecar.settings.keyring") as mock_keyring:
                    mock_keyring.set_password.side_effect = Exception("Keyring error")

                    # Should not raise, should still save config file
                    settings.save()

                    assert config_path.exists()


def test_settings_apply_env_empty_values():
    """Test that Settings.apply_env() handles empty API key."""
    settings = Settings(openai_model="", openai_api_key="")

    settings.apply_env()

    # Should set temperature even with empty model/key
    assert "OPENAI_TEMPERATURE" in os.environ
