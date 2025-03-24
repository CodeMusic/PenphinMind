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
    """Main configuration class"""
    
    def __init__(self):
        self.config_path = Path("config.json")
        self.settings = self.load_config()
        
    def load_config(self) -> dict:
        """Load configuration from JSON file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return self.get_default_config()
        
    def save_config(self) -> None:
        """Save current configuration to JSON file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.settings, f, indent=4)
            
    def get_default_config(self) -> dict:
        """Get default configuration settings"""
        return {
            "api_keys": {
                "openai": "",
                "elevenlabs": ""
            },
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "chunk_size": 1024
            },
            "tts": {
                "default_voice": "default",
                "speed": 1.0,
                "pitch": 1.0
            },
            "asr": {
                "language": "en",
                "model": "whisper-1"
            }
        }

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
        audio = self.settings.get("audio", {})
        
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
        paths = self.settings.get("paths", {})
        for path_name, path_str in paths.items():
            if not isinstance(path_str, str):
                raise ConfigError(f"Invalid path for {path_name}")
                
    @property
    def audio_output_type(self) -> AudioOutputType:
        """Get audio output type"""
        return AudioOutputType(self.settings["audio"]["output_type"])
        
    @property
    def audio_device(self) -> str:
        """Get audio device"""
        return self.settings["audio"]["device"]
        
    @property
    def audio_sample_rate(self) -> int:
        """Get audio sample rate"""
        return self.settings["audio"]["sample_rate"]
        
    @property
    def audio_channels(self) -> int:
        """Get audio channels"""
        return self.settings["audio"]["channels"]
        
    @property
    def audio_volume(self) -> int:
        """Get audio volume"""
        return self.settings["audio"]["volume"]
        
    @property
    def serial_baud_rate(self) -> int:
        """Get serial baud rate"""
        return self.settings["serial"]["baud_rate"]
        
    @property
    def serial_timeout(self) -> float:
        """Get serial timeout"""
        return self.settings["serial"]["timeout"]
        
    @property
    def serial_max_retries(self) -> int:
        """Get serial max retries"""
        return self.settings["serial"]["max_retries"]
        
    @property
    def serial_retry_delay(self) -> float:
        """Get serial retry delay"""
        return self.settings["serial"]["retry_delay"]
        
    @property
    def serial_default_port(self) -> str:
        """Get serial default port"""
        return self.settings["serial"]["default_port"]
        
    @property
    def audio_cache_path(self) -> Path:
        """Get audio cache path"""
        return PROJECT_ROOT / self.settings["paths"]["audio_cache"]
        
    @property
    def models_path(self) -> Path:
        """Get models path"""
        return PROJECT_ROOT / self.settings["paths"]["models"]
        
    @property
    def log_level(self) -> str:
        """Get log level"""
        return self.settings["logging"]["level"]
        
    @property
    def log_file(self) -> Path:
        """Get log file path"""
        return PROJECT_ROOT / self.settings["logging"]["file"]
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get any configuration value by key"""
        keys = key.split('.')
        value = self.settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
# Global configuration instance
CONFIG = Config() 