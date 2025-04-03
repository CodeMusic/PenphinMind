# PenphinMind Configuration System

This document explains how configuration works in the PenphinMind system.

## Configuration Structure

PenphinMind uses a dual-configuration approach, separating mind-specific configuration from system-wide configuration:

1. **Mind-specific Configuration**: For settings related to individual mind instances (identities, personas, connection details)
2. **System-wide Configuration**: For settings related to the overall system operation (hardware settings, logging, I/O devices)

## Mind-specific Configuration

### Files
- `minds_config.json`: Root level JSON file containing configurations for all available mind instances
- `Mind/mind_config.py`: Module that handles loading and managing mind-specific configurations

### Structure of `minds_config.json`
```json
{
    "minds": {
        "auto": {
            "name": "PenphinMind",
            "device_id": "auto",
            "connection": {
                "type": "tcp",
                "ip": "10.0.0.154",
                "port": 10001
            },
            "llm": {
                "default_model": "qwen2.5-0.5b-prefill",
                "temperature": 0.7,
                "max_tokens": 127,
                "persona": "You are a helpful assistant named {name}."
            }
        },
        "other_mind_id": { /* ... */ }
    },
    "system": {
        "default_mind": "auto"
    }
}
```

### Mind-specific Settings
- **Identity**: `name`, `device_id`
- **Connection**: Connection settings for the specific device this mind will use
  - `type`: Connection type (tcp, serial, etc.)
  - `ip`: IP address of the device
  - `port`: Port to connect to
- **LLM settings**: All LLM model and behavior settings:
  - `default_model`: The default model to use for this mind
  - `temperature`: LLM generation temperature for this mind
  - `max_tokens`: Maximum tokens to generate for this mind
  - `persona`: The system message/persona for this mind

### Usage
To access mind-specific configuration, use the functions from `Mind/mind_config.py`:

```python
from Mind.mind_config import get_mind_by_id, load_minds_config, get_default_mind_id

# Get configuration for a specific mind
mind_config = get_mind_by_id("auto")  # Or any other mind_id

# Get the default mind ID
default_mind_id = get_default_mind_id()

# Load all minds configuration
all_minds_config = load_minds_config()
```

## System-wide Configuration

### Files
- `config.json`: Root level JSON file containing system-wide configuration
- `config.py`: Module that handles loading and managing system-wide configuration

### Structure of `config.json`
```json
{
    "corpus_callosum": {
        "serial_settings": {
            "port": "COM7",
            "baud_rate": 115200
        },
        "logging": {
            "level": "DEBUG"
        }
    }
}
```

### System-wide Settings
- **Hardware settings**: Default serial port settings, audio devices, etc.
- **Logging settings**: Log levels, formats, etc.
- **Global timeout settings**: Default timeouts for various operations

### Usage
To access system-wide configuration, use the `CONFIG` instance from `config.py`:

```python
from config import CONFIG

# Access system-wide settings
log_level = CONFIG.log_level
serial_port = CONFIG.serial_settings["port"]
```

Alternatively, you can instantiate a new `Config` class for more explicit usage:

```python
from config import Config

# Create a Config instance
config = Config()

# Access system-wide settings
log_level = config.log_level
serial_port = config.serial_settings["port"]
```

## ⚠️ IMPORTANT: Configuration Import Warning

Never import CONFIG from `Mind.config` as this module doesn't exist and will cause errors:

```python
# ❌ WRONG - Will cause "ModuleNotFoundError: No module named 'Mind.config'"
from Mind.config import CONFIG  

# ✅ CORRECT - Use absolute import from project root
from config import CONFIG
```

This is a common source of errors in the codebase. Always use absolute imports for system-wide configuration.

## ⚠️ IMPORTANT: Circular Import Issues

Be careful of circular imports between `Mind/mind.py` and `Interaction/chat_manager.py`:

```python
# ❌ WRONG - Creates circular import
# In Mind/mind.py
from Interaction.chat_manager import ChatManager

# In Interaction/chat_manager.py
from Mind.mind import Mind  # This causes circular import
```

Instead, use lazy imports or dependency injection:

```python
# ✅ CORRECT - In Mind/mind.py
def get_chat_manager(self):
    """Lazy import to avoid circular dependency"""
    if self.chat_manager is None:
        from Interaction.chat_manager import ChatManager
        self.chat_manager = ChatManager(self)
    return self.chat_manager
```

## Best Practices

1. **Mind-specific vs. System-wide**:
   - Use mind-specific config for anything related to a particular mind's identity, behavior, or connection
   - Use system-wide config for hardware settings, logging, and defaults that apply across all minds

2. **Device Connection Settings**:
   - Different minds may connect to different devices or the same device differently
   - Keep all connection settings (IP, port, connection type) in mind-specific configuration
   - If needed, the default "auto" mind can be used when no specific mind is required

3. **LLM Configuration**:
   - All LLM-related settings should be in mind-specific config:
     - Model settings (name, temperature, max_tokens)
     - Connection settings to the specific LLM device
     - Persona and behavior settings 

4. **Referencing Configs**:
   - In the `Mind` class, use `get_mind_by_id()` function for mind-specific configuration
   - For system-wide settings, use **absolute imports** for the `CONFIG` object:
     ```python
     from config import CONFIG  # Good: absolute import
     from ..config import CONFIG  # Bad: relative import can cause circular dependencies
     ```

5. **Avoiding Circular Dependencies**:
   - Never import from `Mind` modules in `config.py`
   - Use absolute imports for configuration instead of relative imports
   - Use lazy imports (import inside functions) for modules that may cause circular dependencies
   - Consider using dependency injection for objects like ChatManager

6. **Extending Configuration**:
   - To add new mind-specific settings, update the `DEFAULT_MINDS_CONFIG` in `Mind/mind_config.py`
   - To add new system-wide settings, update the `_init_defaults` method in `Config` class in `config.py`

7. **Backward Compatibility**:
   - The `get_mind_config()` function in `config.py` delegates to `Mind/mind_config.py` for backward compatibility
   - Prefer using `get_mind_by_id()` directly from `Mind/mind_config` for new code


   Example:
~~~
"""
Configuration Usage Example

This file demonstrates the proper way to use both configuration systems in PenphinMind.
It follows best practices to avoid circular dependencies and maintain a clear separation
between mind-specific and system-wide configurations.
"""

from typing import Dict, Any

# System-wide configuration import
from config import CONFIG

# Mind-specific configuration imports
from Mind.mind_config import get_mind_by_id, get_default_mind_id, load_minds_config

def print_system_config_example():
    """Example of using system-wide configuration"""
    print("\n=== System-wide Configuration Example ===")
    print(f"Log Level: {CONFIG.log_level}")
    print(f"Debug Mode: {CONFIG.debug_mode}")
    
    print("\nSerial Settings:")
    print(f"  Port: {CONFIG.serial_settings['port']}")
    print(f"  Baud Rate: {CONFIG.serial_settings['baud_rate']}")
    print(f"  Timeout: {CONFIG.serial_settings['timeout']}s")
    
    print("\nAudio Settings:")
    print(f"  Sample Rate: {CONFIG.sample_rate}Hz")
    print(f"  Channels: {CONFIG.channels}")
    print(f"  Volume: {CONFIG.audio_device_controls['volume']}%")

def print_mind_config_example():
    """Example of using mind-specific configuration"""
    print("\n=== Mind-specific Configuration Example ===")
    
    # Get default mind ID
    default_mind_id = get_default_mind_id()
    print(f"Default Mind ID: {default_mind_id}")
    
    # Get config for the default mind
    mind_config = get_mind_by_id(default_mind_id)
    
    print(f"Mind Name: {mind_config['name']}")
    print(f"Device ID: {mind_config['device_id']}")
    
    print("\nConnection Settings:")
    print(f"  Type: {mind_config['connection']['type']}")
    print(f"  IP: {mind_config['connection']['ip']}")
    print(f"  Port: {mind_config['connection']['port']}")
    
    print("\nLLM Settings:")
    print(f"  Default Model: {mind_config['llm']['default_model']}")
    print(f"  Temperature: {mind_config['llm']['temperature']}")
    print(f"  Max Tokens: {mind_config['llm']['max_tokens']}")
    
    # Format the persona string if it contains placeholders
    persona = mind_config['llm']['persona']
    formatted_persona = persona.format(name=mind_config['name'])
    print(f"  Persona: {formatted_persona}")

def get_combined_config(mind_id: str = None) -> Dict[str, Any]:
    """
    Example function that combines mind-specific and system-wide settings
    
    This demonstrates how to properly use both configuration systems together.
    
    Args:
        mind_id: ID of the mind to use, or None for default
        
    Returns:
        Combined configuration dictionary
    """
    # Get mind-specific config
    mind_config = get_mind_by_id(mind_id)
    
    # Create a combined config
    combined_config = {
        # Mind-specific settings
        "name": mind_config["name"],
        "device_id": mind_config["device_id"],
        "connection": mind_config["connection"].copy(),
        "llm_settings": mind_config["llm"].copy(),
        
        # System-wide settings
        "debug": CONFIG.debug_mode,
        "log_level": CONFIG.log_level,
        "audio": {
            "sample_rate": CONFIG.sample_rate,
            "channels": CONFIG.channels,
            "volume": CONFIG.audio_device_controls["volume"]
        },
        "serial": CONFIG.serial_settings.copy()
    }
    
    return combined_config

def get_device_connection(mind_id: str = None) -> Dict[str, Any]:
    """
    Get connection settings for a specific mind or the default mind
    
    This demonstrates how to access device connection settings for
    a specific mind, with fallback to the default "auto" mind.
    
    Args:
        mind_id: ID of the mind to use, or None for default
        
    Returns:
        Connection settings dictionary
    """
    # Try to get the requested mind first
    if mind_id:
        try:
            mind_config = get_mind_by_id(mind_id)
            connection = mind_config.get("connection", {})
            print(f"Using connection settings from mind: {mind_id}")
            return connection
        except Exception as e:
            print(f"Error getting mind {mind_id}: {e}")
            # Fall through to default
    
    # Get the default mind as fallback
    default_mind = get_mind_by_id("auto")
    connection = default_mind.get("connection", {})
    print(f"Using connection settings from default mind: auto")
    return connection

if __name__ == "__main__":
    # Show examples of both configuration types
    print_system_config_example()
    print_mind_config_example()
    
    # Example of combining configurations
    print("\n=== Combined Configuration Example ===")
    combined = get_combined_config()
    print(f"Name: {combined['name']}")
    print(f"Log Level: {combined['log_level']}")
    print(f"LLM Model: {combined['llm_settings']['default_model']}")
    print(f"Connection IP: {combined['connection']['ip']}")
    
    # Example of getting device connection settings
    print("\n=== Device Connection Example ===")
    # Get connection for specific mind
    alpha_conn = get_device_connection("alpha")
    print(f"Alpha connection: {alpha_conn}")
    # Fallback to default mind
    unknown_conn = get_device_connection("unknown_mind")
    print(f"Unknown mind connection (using default): {unknown_conn}")
~~~