from enum import Enum
from pathlib import Path
import json
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

# Get the directory containing this script (project root)
PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))

class AudioOutputType(Enum):
    """Audio output device types"""
    LLM = "LLM"
    WAVESHARE = "WAVESHARE"

class ConfigError(Exception):
    """Configuration related errors"""
    pass

class Config:
    """Configuration manager that loads and validates JSON config"""
    
    DEFAULT_CONFIG = {
        "audio": {
            "output_type": "LLM",
            "sample_rate": 16000,
            "channels": 1,
            "device": "default",
            "volume": 80
        },
        "serial": {
            "baud_rate": 115200,
            "timeout": 2.0,
            "max_retries": 3,
            "retry_delay": 1.0,
            "default_port": "/dev/ttyUSB0"
        },
        "paths": {
            "audio_cache": "cache/audio",
            "models": "models",
            "logs": "logs"
        },
        "logging": {
            "level": "INFO",
            "file": "logs/penphinos.system.log"
        }
    }
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._config_path = PROJECT_ROOT / "config.json"
        self.load()
        
    def load(self, config_path: Optional[Path] = None) -> None:
        """
        Load configuration from JSON file
        
        Args:
            config_path: Optional alternative config file path
        """
        if config_path:
            self._config_path = config_path
            
        try:
            if self._config_path.exists():
                with open(self._config_path) as f:
                    loaded_config = json.load(f)
                    # Merge with defaults, preserving loaded values
                    self._config = self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
            else:
                logger.warning(f"Config file {self._config_path} not found, using defaults")
                self._config = self.DEFAULT_CONFIG.copy()
                
            # Create necessary directories
            self._ensure_directories_exist()
            self.save()  # Create or update config file
                
            self._validate_config()
            
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading config: {e}")
            
    def _ensure_directories_exist(self):
        """Create necessary directories if they don't exist"""
        paths = [
            self.audio_cache_path,
            self.models_path,
            self.log_file.parent
        ]
        
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
            
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults"""
        merged = default.copy()
        
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
                
        return merged
            
    def _validate_config(self) -> None:
        """Validate configuration values"""
        audio = self._config.get("audio", {})
        
        # Validate audio output type
        try:
            AudioOutputType(audio.get("output_type", "LLM"))
        except ValueError as e:
            raise ConfigError(f"Invalid audio output type: {e}")
            
        # Validate numeric values
        if not isinstance(audio.get("sample_rate", 16000), int):
            raise ConfigError("Sample rate must be an integer")
        if not isinstance(audio.get("volume", 100), int):
            raise ConfigError("Volume must be an integer")
            
        # Validate paths
        paths = self._config.get("paths", {})
        for path_name, path_str in paths.items():
            if not isinstance(path_str, str):
                raise ConfigError(f"Invalid path for {path_name}")
                
    def save(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self._config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            raise ConfigError(f"Error saving config: {e}")
            
    @property
    def audio_output_type(self) -> AudioOutputType:
        """Get audio output type"""
        return AudioOutputType(self._config["audio"]["output_type"])
        
    @property
    def audio_device(self) -> str:
        """Get audio device"""
        return self._config["audio"]["device"]
        
    @property
    def audio_sample_rate(self) -> int:
        """Get audio sample rate"""
        return self._config["audio"]["sample_rate"]
        
    @property
    def audio_channels(self) -> int:
        """Get audio channels"""
        return self._config["audio"]["channels"]
        
    @property
    def audio_volume(self) -> int:
        """Get audio volume"""
        return self._config["audio"]["volume"]
        
    @property
    def serial_baud_rate(self) -> int:
        """Get serial baud rate"""
        return self._config["serial"]["baud_rate"]
        
    @property
    def serial_timeout(self) -> float:
        """Get serial timeout"""
        return self._config["serial"]["timeout"]
        
    @property
    def serial_max_retries(self) -> int:
        """Get serial max retries"""
        return self._config["serial"]["max_retries"]
        
    @property
    def serial_retry_delay(self) -> float:
        """Get serial retry delay"""
        return self._config["serial"]["retry_delay"]
        
    @property
    def serial_default_port(self) -> str:
        """Get serial default port"""
        return self._config["serial"]["default_port"]
        
    @property
    def audio_cache_path(self) -> Path:
        """Get audio cache path"""
        return PROJECT_ROOT / self._config["paths"]["audio_cache"]
        
    @property
    def models_path(self) -> Path:
        """Get models path"""
        return PROJECT_ROOT / self._config["paths"]["models"]
        
    @property
    def log_level(self) -> str:
        """Get log level"""
        return self._config["logging"]["level"]
        
    @property
    def log_file(self) -> Path:
        """Get log file path"""
        return PROJECT_ROOT / self._config["logging"]["file"]
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get any configuration value by key"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
# Global configuration instance
CONFIG = Config() 