from typing import Dict, Any
import json
import os
from pathlib import Path

# Config file paths
CONFIG_FILE_PATH = Path(__file__).parent / "config.json"
MINDS_CONFIG_PATH = Path(__file__).parent / "minds_config.json"

# Default system config (not mind-specific)
DEFAULT_CONFIG = {
    "logging": {
        "level": "INFO",
        "file": "penphin.log",
        "format": "%(asctime)s [%(levelname)s] %(message)s"
    },
    "system": {
        "hardware_refresh_rate": 60,
        "connection_timeout": 5.0,
        "retry_attempts": 3
    }
}

def load_config() -> Dict[str, Any]:
    """Load system configuration from file or use defaults"""
    config = DEFAULT_CONFIG.copy()
    
    if CONFIG_FILE_PATH.exists():
        try:
            with open(CONFIG_FILE_PATH) as f:
                user_config = json.load(f)
                # Deep merge user config with defaults
                _deep_update(config, user_config)
            print(f"System config loaded from {CONFIG_FILE_PATH}")
        except Exception as e:
            print(f"Error loading config from {CONFIG_FILE_PATH}: {e}")
            print("Using default configuration")
    else:
        print(f"System config file not found at {CONFIG_FILE_PATH}")
        print("Using default configuration")
    
    return config

def _deep_update(base: Dict, update: Dict) -> None:
    """Recursively update a dictionary"""
    for key, value in update.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_update(base[key], value)
        else:
            base[key] = value

def get_mind_config(mind_id: str = None) -> Dict[str, Any]:
    """Get configuration for a specific mind"""
    from Mind.mind_config import load_minds_config, get_mind_by_id
    return get_mind_by_id(mind_id)

# Initialize global config
CONFIG = load_config() 