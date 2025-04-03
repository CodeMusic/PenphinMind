from typing import Dict, Any
import json
import os

DEFAULT_CONFIG = {
    "minds": {
        "auto": {
            "name": "PenphinMind",
            "device_id": "auto",
            "connection": {
                "type": "tcp",
                "ip": "auto",  # Will use auto-discovery
                "port": "auto"
            },
            "llm": {
                "default_model": "qwen2.5-0.5b-prefill",
                "temperature": 0.7,
                "max_tokens": 127,
                "persona": "You are a helpful assistant named {name}."
            }
        },
        "alpha": {
            "name": "DolphinMind",
            "device_id": "alpha",
            "connection": {
                "type": "tcp",
                "ip": "192.168.1.100",  # Example fixed IP
                "port": 8008
            },
            "llm": {
                "default_model": "qwen2.5-0.5b-prefill",
                "temperature": 0.5,
                "max_tokens": 127,
                "persona": "You are a logical analyzer focused on systematic thinking."
            }
        },
        "beta": {
            "name": "PenguinMind",
            "device_id": "beta",
            "connection": {
                "type": "tcp",
                "ip": "192.168.1.101",
                "port": 8008
            },
            "llm": {
                "default_model": "qwen2.5-0.5b-prefill",
                "temperature": 0.8,
                "max_tokens": 127,
                "persona": "You are a creative explorer focused on innovative solutions."
            }
        }
    },
    "logging": {
        "level": "INFO",
        "file": "penphin.log",
        "format": "%(asctime)s [%(levelname)s] %(message)s"
    },
    "system": {
        "default_mind": "auto",
        "hardware_refresh_rate": 60,
        "connection_timeout": 5.0,
        "retry_attempts": 3
    }
}

def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from file or use defaults"""
    config = DEFAULT_CONFIG.copy()
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path) as f:
                user_config = json.load(f)
                # Deep merge user config with defaults
                _deep_update(config, user_config)
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}")
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
    config = load_config()
    if not mind_id:
        mind_id = config["system"]["default_mind"]
    return config["minds"].get(mind_id, config["minds"]["auto"]) 