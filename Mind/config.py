"""
Mental Configuration - Manages the mental architecture of PenphinMind
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import os

# Get the project root directory (where config.py is located)
PROJECT_ROOT = Path(__file__).parent

logger = logging.getLogger(__name__)

class AudioOutputType(str, Enum):
    """Audio output device types"""
    WAVESHARE = "waveshare"
    LOCAL_LLM = "local_llm"

class MentalConfiguration:
    """
    Configuration settings for the PenphinMind system
    """
    def __init__(self):
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        self.audio_device_controls = {
            "volume": 100,  # Volume level (0-100)
            "mute": False,  # Mute state
            "input_device": "default",  # Input device name
            "output_device": "default",  # Output device name
            "latency": 0.1,  # Audio latency in seconds
            "buffer_size": 2048  # Audio buffer size
        }
        
        # Visual settings
        self.visual_height = 32  # Height of LED matrix
        self.visual_width = 64   # Width of LED matrix
        self.visual_fps = 30     # Frames per second for visual updates
        
        # Motor settings
        self.motor_speed = 100    # Default motor speed (0-255)
        self.motor_acceleration = 50  # Default acceleration (0-255)
        
        # LLM settings
        self.llm_model = "gpt-3.5-turbo"
        self.llm_temperature = 0.7
        self.llm_max_tokens = 1000
        
        # System settings
        self.debug_mode = False
        self.log_level = "INFO"
        
        # Load environment variables
        self._load_env_vars()
        
    def _load_env_vars(self) -> None:
        """Load configuration from environment variables"""
        # Audio settings
        if "PENPHIN_SAMPLE_RATE" in os.environ:
            self.sample_rate = int(os.environ["PENPHIN_SAMPLE_RATE"])
        if "PENPHIN_CHANNELS" in os.environ:
            self.channels = int(os.environ["PENPHIN_CHANNELS"])
        if "PENPHIN_CHUNK_SIZE" in os.environ:
            self.chunk_size = int(os.environ["PENPHIN_CHUNK_SIZE"])
            
        # Audio device controls
        if "PENPHIN_AUDIO_VOLUME" in os.environ:
            self.audio_device_controls["volume"] = int(os.environ["PENPHIN_AUDIO_VOLUME"])
        if "PENPHIN_AUDIO_MUTE" in os.environ:
            self.audio_device_controls["mute"] = os.environ["PENPHIN_AUDIO_MUTE"].lower() == "true"
        if "PENPHIN_AUDIO_INPUT" in os.environ:
            self.audio_device_controls["input_device"] = os.environ["PENPHIN_AUDIO_INPUT"]
        if "PENPHIN_AUDIO_OUTPUT" in os.environ:
            self.audio_device_controls["output_device"] = os.environ["PENPHIN_AUDIO_OUTPUT"]
        if "PENPHIN_AUDIO_LATENCY" in os.environ:
            self.audio_device_controls["latency"] = float(os.environ["PENPHIN_AUDIO_LATENCY"])
        if "PENPHIN_AUDIO_BUFFER" in os.environ:
            self.audio_device_controls["buffer_size"] = int(os.environ["PENPHIN_AUDIO_BUFFER"])
            
        # Visual settings
        if "PENPHIN_VISUAL_HEIGHT" in os.environ:
            self.visual_height = int(os.environ["PENPHIN_VISUAL_HEIGHT"])
        if "PENPHIN_VISUAL_WIDTH" in os.environ:
            self.visual_width = int(os.environ["PENPHIN_VISUAL_WIDTH"])
        if "PENPHIN_VISUAL_FPS" in os.environ:
            self.visual_fps = int(os.environ["PENPHIN_VISUAL_FPS"])
            
        # Motor settings
        if "PENPHIN_MOTOR_SPEED" in os.environ:
            self.motor_speed = int(os.environ["PENPHIN_MOTOR_SPEED"])
        if "PENPHIN_MOTOR_ACCELERATION" in os.environ:
            self.motor_acceleration = int(os.environ["PENPHIN_MOTOR_ACCELERATION"])
            
        # LLM settings
        if "PENPHIN_LLM_MODEL" in os.environ:
            self.llm_model = os.environ["PENPHIN_LLM_MODEL"]
        if "PENPHIN_LLM_TEMPERATURE" in os.environ:
            self.llm_temperature = float(os.environ["PENPHIN_LLM_TEMPERATURE"])
        if "PENPHIN_LLM_MAX_TOKENS" in os.environ:
            self.llm_max_tokens = int(os.environ["PENPHIN_LLM_MAX_TOKENS"])
            
        # System settings
        if "PENPHIN_DEBUG_MODE" in os.environ:
            self.debug_mode = os.environ["PENPHIN_DEBUG_MODE"].lower() == "true"
        if "PENPHIN_LOG_LEVEL" in os.environ:
            self.log_level = os.environ["PENPHIN_LOG_LEVEL"].upper()
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "audio": {
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "chunk_size": self.chunk_size,
                "device_controls": self.audio_device_controls
            },
            "visual": {
                "height": self.visual_height,
                "width": self.visual_width,
                "fps": self.visual_fps
            },
            "motor": {
                "speed": self.motor_speed,
                "acceleration": self.motor_acceleration
            },
            "llm": {
                "model": self.llm_model,
                "temperature": self.llm_temperature,
                "max_tokens": self.llm_max_tokens
            },
            "system": {
                "debug_mode": self.debug_mode,
                "log_level": self.log_level
            }
        }

# Create global configuration instance
CONFIG = MentalConfiguration() 