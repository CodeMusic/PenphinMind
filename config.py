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
    """Configuration error"""
    pass

class Config:
    """Configuration manager for PenphinOS"""
    
    def __init__(self):
        self.config_file = Path("config.json")
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_file.exists():
            return self._get_default_config()
            
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
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
            "llm": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 150,
                "temperature": 0.7,
                "system_prompt": "You are PenphinOS, a bicameral AI assistant."
            },
            "tts": {
                "voice_id": "default",
                "speed": 1.0,
                "pitch": 1.0
            },
            "asr": {
                "language": "en",
                "model_type": "whisper"
            },
            "device": {
                "input_device": None,
                "output_device": None
            },
            "led_matrix": {
                "rows": 64,
                "cols": 64,
                "max_brightness": 50,
                "gpio_slowdown": 4,
                "chain_length": 1,
                "parallel": 1,
                "pwm_bits": 11,
                "scan_mode": 0,
                "pwm_lsb_nanoseconds": 130,
                "rgb_sequence": "RGB"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "log_level": "INFO"
        }
        
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key"""
        return self.config["api_keys"]["openai"]
        
    @property
    def elevenlabs_api_key(self) -> str:
        """Get ElevenLabs API key"""
        return self.config["api_keys"]["elevenlabs"]
        
    @property
    def llm_model(self) -> str:
        """Get LLM model name"""
        return self.config["llm"]["model"]
        
    @property
    def llm_max_tokens(self) -> int:
        """Get LLM max tokens"""
        return self.config["llm"]["max_tokens"]
        
    @property
    def llm_temperature(self) -> float:
        """Get LLM temperature"""
        return self.config["llm"]["temperature"]
        
    @property
    def llm_system_prompt(self) -> str:
        """Get LLM system prompt"""
        return self.config["llm"]["system_prompt"]
        
    @property
    def audio_sample_rate(self) -> int:
        """Get audio sample rate"""
        return self.config["audio"]["sample_rate"]
        
    @property
    def audio_channels(self) -> int:
        """Get audio channels"""
        return self.config["audio"]["channels"]
        
    @property
    def audio_chunk_size(self) -> int:
        """Get audio chunk size"""
        return self.config["audio"]["chunk_size"]
        
    @property
    def tts_voice_id(self) -> str:
        """Get TTS voice ID"""
        return self.config["tts"]["voice_id"]
        
    @property
    def tts_speed(self) -> float:
        """Get TTS speed"""
        return self.config["tts"]["speed"]
        
    @property
    def tts_pitch(self) -> float:
        """Get TTS pitch"""
        return self.config["tts"]["pitch"]
        
    @property
    def asr_language(self) -> str:
        """Get ASR language"""
        return self.config["asr"]["language"]
        
    @property
    def asr_model_type(self) -> str:
        """Get ASR model type"""
        return self.config["asr"]["model_type"]
        
    @property
    def input_device(self) -> Optional[str]:
        """Get input device name"""
        return self.config["device"]["input_device"]
        
    @property
    def output_device(self) -> Optional[str]:
        """Get output device name"""
        return self.config["device"]["output_device"]
        
    @property
    def led_rows(self) -> int:
        """Get LED matrix rows"""
        return self.config["led_matrix"]["rows"]
        
    @property
    def led_cols(self) -> int:
        """Get LED matrix columns"""
        return self.config["led_matrix"]["cols"]
        
    @property
    def led_max_brightness(self) -> int:
        """Get LED matrix maximum brightness (0-100)"""
        return min(100, max(0, self.config["led_matrix"]["max_brightness"]))
        
    @property
    def led_gpio_slowdown(self) -> int:
        """Get LED matrix GPIO slowdown"""
        return self.config["led_matrix"]["gpio_slowdown"]
        
    @property
    def led_chain_length(self) -> int:
        """Get LED matrix chain length"""
        return self.config["led_matrix"]["chain_length"]
        
    @property
    def led_parallel(self) -> int:
        """Get LED matrix parallel configuration"""
        return self.config["led_matrix"]["parallel"]
        
    @property
    def led_pwm_bits(self) -> int:
        """Get LED matrix PWM bits"""
        return self.config["led_matrix"]["pwm_bits"]
        
    @property
    def led_scan_mode(self) -> int:
        """Get LED matrix scan mode"""
        return self.config["led_matrix"]["scan_mode"]
        
    @property
    def led_pwm_lsb_nanoseconds(self) -> int:
        """Get LED matrix PWM LSB nanoseconds"""
        return self.config["led_matrix"]["pwm_lsb_nanoseconds"]
        
    @property
    def led_rgb_sequence(self) -> str:
        """Get LED matrix RGB sequence"""
        return self.config["led_matrix"]["rgb_sequence"]
        
    @property
    def log_level(self) -> str:
        """Get logging level"""
        return self.config["logging"]["level"]
        
    def save(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            
    def update(self, key: str, value: Any) -> None:
        """Update configuration value"""
        keys = key.split('.')
        current = self.config
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = value
        self.save()

# Create global config instance
CONFIG = Config() 