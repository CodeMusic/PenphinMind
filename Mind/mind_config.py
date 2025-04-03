"""
Minds Configuration Management

This module handles loading and managing multiple mind configurations from minds_config.json
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path

# Path to minds_config.json in the project root (not in Mind folder)
MINDS_CONFIG_PATH = Path(__file__).parent.parent / "minds_config.json"

# Default minds configuration
DEFAULT_MINDS_CONFIG = {
    "minds": {
        "auto": {
            "name": "PenphinMind",
            "device_id": "auto",
            "connection": {
                "type": "tcp",
                "ip": "auto",
                "port": "auto"
            },
            "llm": {
                "default_model": "qwen2.5-0.5b-prefill",
                "temperature": 0.7,
                "max_tokens": 127,
                "persona": "You are a helpful assistant named {name}."
            }
        }
    },
    "system": {
        "default_mind": "auto"
    }
}

# Cache for minds config
_minds_config_cache = None

def load_minds_config() -> Dict[str, Any]:
    """Load multiple mind configurations from minds_config.json
    
    Returns:
        Dict containing all mind configurations
    """
    global _minds_config_cache
    
    # Return cached config if available
    if _minds_config_cache is not None:
        return _minds_config_cache
    
    # Start with default config
    minds_config = DEFAULT_MINDS_CONFIG.copy()
    
    # Try to load from file
    if MINDS_CONFIG_PATH.exists():
        try:
            with open(MINDS_CONFIG_PATH) as f:
                user_minds_config = json.load(f)
                # Deep merge user config with defaults
                _deep_update(minds_config, user_minds_config)
            print(f"Minds config loaded from {MINDS_CONFIG_PATH}")
        except Exception as e:
            print(f"Error loading minds config from {MINDS_CONFIG_PATH}: {e}")
            print("Using default minds configuration")
    else:
        print(f"Minds config file not found at {MINDS_CONFIG_PATH}")
        print("Using default minds configuration")
    
    # Cache the loaded config
    _minds_config_cache = minds_config
    return minds_config

def _deep_update(base: Dict, update: Dict) -> None:
    """Recursively update a dictionary"""
    for key, value in update.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_update(base[key], value)
        else:
            base[key] = value

def get_mind_by_id(mind_id: Optional[str] = None) -> Dict[str, Any]:
    """Get configuration for a specific mind
    
    Args:
        mind_id: ID of the mind to retrieve, or None for default
        
    Returns:
        Dict containing a single mind's configuration, not the entire minds structure
    """
    minds_config = load_minds_config()
    
    # If no mind_id provided, use the default
    if mind_id is None:
        mind_id = minds_config["system"]["default_mind"]
    
    # Return the requested mind config, falling back to "auto" if not found
    mind_config = minds_config["minds"].get(mind_id, minds_config["minds"]["auto"])
    
    # Add the mind_id to the configuration so the Mind object knows its own id
    mind_config["mind_id"] = mind_id
    
    return mind_config

def get_available_minds() -> List[str]:
    """Get list of available mind IDs
    
    Returns:
        List of mind IDs from configuration
    """
    minds_config = load_minds_config()
    return list(minds_config["minds"].keys())

def get_default_mind_id() -> str:
    """Get the default mind ID from configuration
    
    Returns:
        Default mind ID
    """
    minds_config = load_minds_config()
    return minds_config["system"]["default_mind"]

def set_default_mind(mind_id: str) -> bool:
    """Set the default mind ID
    
    Args:
        mind_id: The mind ID to set as default
        
    Returns:
        bool: Success status
    """
    minds_config = load_minds_config()
    
    # Verify the mind_id exists
    if mind_id not in minds_config["minds"]:
        return False
    
    # Update the default
    minds_config["system"]["default_mind"] = mind_id
    
    # Save to file
    try:
        with open(MINDS_CONFIG_PATH, 'w') as f:
            json.dump(minds_config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving minds config: {e}")
        return False

# For backward compatibility
load_mind_config = load_minds_config 