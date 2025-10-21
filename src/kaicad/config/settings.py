from __future__ import annotations

import json
import logging
import os
import sys
import threading
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger("kaicad.config.settings")

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


def get_config_dir() -> Path:
    """Get platform-specific config directory"""
    if sys.platform == "win32":
        # Windows: %APPDATA%\kAIcad
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "kAIcad"
        return Path.home() / "AppData" / "Roaming" / "kAIcad"
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/kAIcad
        return Path.home() / "Library" / "Application Support" / "kAIcad"
    else:
        # Linux/Unix: ~/.config/kAIcad
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "kAIcad"
        return Path.home() / ".config" / "kAIcad"


CONFIG_DIR = get_config_dir()
CONFIG_PATH = CONFIG_DIR / "config.json"
KEYRING_SERVICE = "kAIcad"
KEYRING_USERNAME = "openai_api_key"


@dataclass
class Settings:
    openai_model: str = "gpt-4o-mini"  # Use real model name (efficient and cost-effective)
    openai_temperature: float = 0.0  # Conservative default for deterministic behavior
    openai_api_key: str = ""
    default_project: str = str(Path.cwd())
    dock_right: bool = True
    
    def __post_init__(self) -> None:
        """Initialize thread lock for thread-safe operations"""
        self._lock = threading.RLock()

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from config file and keyring"""
        settings_dict = {}

        # Load from config file
        try:
            if CONFIG_PATH.exists():
                data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                settings_dict = data
        except Exception:
            pass

        # Try to load API key from keyring first (if env var not set)
        api_key = ""
        
        # Environment variable takes highest precedence
        api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Fall back to keyring if env var not set
        if not api_key and KEYRING_AVAILABLE:
            try:
                stored_key = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
                if stored_key:
                    api_key = stored_key
            except Exception:
                pass

        # Fall back to config file if still not found
        if not api_key:
            api_key = settings_dict.get("openai_api_key", "")

        # Override with env vars if set
        model = os.getenv("OPENAI_MODEL", settings_dict.get("openai_model", cls.openai_model))
        temp = float(os.getenv("OPENAI_TEMPERATURE", str(settings_dict.get("openai_temperature", 0.0))) or 0.0)
        default_project = settings_dict.get("default_project", str(Path.cwd()))
        dock_right = settings_dict.get("dock_right", True)

        return cls(
            openai_model=model,
            openai_temperature=temp,
            openai_api_key=api_key,
            default_project=default_project,
            dock_right=dock_right,
        )

    def save(self) -> None:
        """Save settings to config file and keyring (thread-safe)"""
        with self._lock:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)

            # Save API key to keyring if available
            if KEYRING_AVAILABLE and self.openai_api_key:
                try:
                    keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, self.openai_api_key)
                except Exception as e:
                    logger.warning(f"Failed to save API key to keyring: {e}")

            # Save other settings to config file (exclude API key if using keyring)
            config_data = asdict(self)
            if KEYRING_AVAILABLE and self.openai_api_key:
                # Don't store API key in plain text if keyring is available
                config_data["openai_api_key"] = ""

            CONFIG_PATH.write_text(json.dumps(config_data, indent=2), encoding="utf-8")

    def apply_env(self) -> None:
        """Apply settings to environment variables (thread-safe)"""
        with self._lock:
            if self.openai_model:
                os.environ["OPENAI_MODEL"] = self.openai_model
            os.environ["OPENAI_TEMPERATURE"] = str(self.openai_temperature)
            if self.openai_api_key:
                os.environ["OPENAI_API_KEY"] = self.openai_api_key
