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
from .FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Get the project root directory (where config.py is located)
PROJECT_ROOT = Path(__file__).parent

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class AudioOutputType(str, Enum):
    """Audio output device types"""
    WAVESHARE = "waveshare"
    LOCAL_LLM = "local_llm"

class MentalConfiguration:
    """
    Configuration settings for the PenphinMind system
    """
    def __init__(self):
        journaling_manager.recordScope("MentalConfiguration.__init__")
        
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
        
        # LLM service settings
        self.llm_service = {
            "ip": "10.0.0.154",
            "port": 10001,
            "timeout": 5.0
        }
        
        # System settings
        self.debug_mode = False
        self.log_level = "DEBUG"
        self.log_file = str(PROJECT_ROOT / "logs" / "penphin.log")
        
        # Serial communication settings
        self.serial_baud_rate = 115200
        self.serial_timeout = 1.0
        self.serial_port = None  # Will be auto-detected
        
        # Load configuration from config.json
        self._load_config_json()
        
        # Load environment variables
        self._load_env_vars()
        
        journaling_manager.recordInfo("Mental configuration initialized")
        
    def _load_config_json(self) -> None:
        """Load configuration from config.json"""
        journaling_manager.recordScope("MentalConfiguration._load_config_json")
        try:
            config_path = PROJECT_ROOT / "config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    
                # Load LLM service settings from corpus_callosum section
                if "corpus_callosum" in config_data and "llm_service" in config_data["corpus_callosum"]:
                    llm_service_config = config_data["corpus_callosum"]["llm_service"]
                    self.llm_service.update({
                        "ip": llm_service_config.get("ip", self.llm_service["ip"]),
                        "port": llm_service_config.get("port", self.llm_service["port"]),
                        "timeout": llm_service_config.get("timeout", self.llm_service["timeout"])
                    })
                    journaling_manager.recordDebug(f"Loaded LLM service config: {self.llm_service}")
                    
        except Exception as e:
            journaling_manager.recordError(f"Error loading config.json: {e}")
            
    def _load_env_vars(self) -> None:
        """Load configuration from environment variables"""
        journaling_manager.recordScope("MentalConfiguration._load_env_vars")
        
        # Audio settings
        if "PENPHIN_SAMPLE_RATE" in os.environ:
            self.sample_rate = int(os.environ["PENPHIN_SAMPLE_RATE"])
            journaling_manager.recordDebug(f"Loaded sample rate from env: {self.sample_rate}")
        if "PENPHIN_CHANNELS" in os.environ:
            self.channels = int(os.environ["PENPHIN_CHANNELS"])
            journaling_manager.recordDebug(f"Loaded channels from env: {self.channels}")
        if "PENPHIN_CHUNK_SIZE" in os.environ:
            self.chunk_size = int(os.environ["PENPHIN_CHUNK_SIZE"])
            journaling_manager.recordDebug(f"Loaded chunk size from env: {self.chunk_size}")
            
        # Audio device controls
        if "PENPHIN_AUDIO_VOLUME" in os.environ:
            self.audio_device_controls["volume"] = int(os.environ["PENPHIN_AUDIO_VOLUME"])
            journaling_manager.recordDebug(f"Loaded audio volume from env: {self.audio_device_controls['volume']}")
        if "PENPHIN_AUDIO_MUTE" in os.environ:
            self.audio_device_controls["mute"] = os.environ["PENPHIN_AUDIO_MUTE"].lower() == "true"
            journaling_manager.recordDebug(f"Loaded audio mute from env: {self.audio_device_controls['mute']}")
        if "PENPHIN_AUDIO_INPUT" in os.environ:
            self.audio_device_controls["input_device"] = os.environ["PENPHIN_AUDIO_INPUT"]
            journaling_manager.recordDebug(f"Loaded audio input device from env: {self.audio_device_controls['input_device']}")
        if "PENPHIN_AUDIO_OUTPUT" in os.environ:
            self.audio_device_controls["output_device"] = os.environ["PENPHIN_AUDIO_OUTPUT"]
            journaling_manager.recordDebug(f"Loaded audio output device from env: {self.audio_device_controls['output_device']}")
        if "PENPHIN_AUDIO_LATENCY" in os.environ:
            self.audio_device_controls["latency"] = float(os.environ["PENPHIN_AUDIO_LATENCY"])
            journaling_manager.recordDebug(f"Loaded audio latency from env: {self.audio_device_controls['latency']}")
        if "PENPHIN_AUDIO_BUFFER" in os.environ:
            self.audio_device_controls["buffer_size"] = int(os.environ["PENPHIN_AUDIO_BUFFER"])
            journaling_manager.recordDebug(f"Loaded audio buffer size from env: {self.audio_device_controls['buffer_size']}")
            
        # Visual settings
        if "PENPHIN_VISUAL_HEIGHT" in os.environ:
            self.visual_height = int(os.environ["PENPHIN_VISUAL_HEIGHT"])
            journaling_manager.recordDebug(f"Loaded visual height from env: {self.visual_height}")
        if "PENPHIN_VISUAL_WIDTH" in os.environ:
            self.visual_width = int(os.environ["PENPHIN_VISUAL_WIDTH"])
            journaling_manager.recordDebug(f"Loaded visual width from env: {self.visual_width}")
        if "PENPHIN_VISUAL_FPS" in os.environ:
            self.visual_fps = int(os.environ["PENPHIN_VISUAL_FPS"])
            journaling_manager.recordDebug(f"Loaded visual FPS from env: {self.visual_fps}")
            
        # Motor settings
        if "PENPHIN_MOTOR_SPEED" in os.environ:
            self.motor_speed = int(os.environ["PENPHIN_MOTOR_SPEED"])
            journaling_manager.recordDebug(f"Loaded motor speed from env: {self.motor_speed}")
        if "PENPHIN_MOTOR_ACCELERATION" in os.environ:
            self.motor_acceleration = int(os.environ["PENPHIN_MOTOR_ACCELERATION"])
            journaling_manager.recordDebug(f"Loaded motor acceleration from env: {self.motor_acceleration}")
            
        # LLM settings
        if "PENPHIN_LLM_MODEL" in os.environ:
            self.llm_model = os.environ["PENPHIN_LLM_MODEL"]
            journaling_manager.recordDebug(f"Loaded LLM model from env: {self.llm_model}")
        if "PENPHIN_LLM_TEMPERATURE" in os.environ:
            self.llm_temperature = float(os.environ["PENPHIN_LLM_TEMPERATURE"])
            journaling_manager.recordDebug(f"Loaded LLM temperature from env: {self.llm_temperature}")
        if "PENPHIN_LLM_MAX_TOKENS" in os.environ:
            self.llm_max_tokens = int(os.environ["PENPHIN_LLM_MAX_TOKENS"])
            journaling_manager.recordDebug(f"Loaded LLM max tokens from env: {self.llm_max_tokens}")
            
        # LLM service settings
        if "PENPHIN_LLM_SERVICE_IP" in os.environ:
            self.llm_service["ip"] = os.environ["PENPHIN_LLM_SERVICE_IP"]
            journaling_manager.recordDebug(f"Loaded LLM service IP from env: {self.llm_service['ip']}")
        if "PENPHIN_LLM_SERVICE_PORT" in os.environ:
            self.llm_service["port"] = int(os.environ["PENPHIN_LLM_SERVICE_PORT"])
            journaling_manager.recordDebug(f"Loaded LLM service port from env: {self.llm_service['port']}")
        if "PENPHIN_LLM_SERVICE_TIMEOUT" in os.environ:
            self.llm_service["timeout"] = float(os.environ["PENPHIN_LLM_SERVICE_TIMEOUT"])
            journaling_manager.recordDebug(f"Loaded LLM service timeout from env: {self.llm_service['timeout']}")
            
        # System settings
        if "PENPHIN_DEBUG_MODE" in os.environ:
            self.debug_mode = os.environ["PENPHIN_DEBUG_MODE"].lower() == "true"
            journaling_manager.recordDebug(f"Loaded debug mode from env: {self.debug_mode}")
        if "PENPHIN_LOG_LEVEL" in os.environ:
            self.log_level = os.environ["PENPHIN_LOG_LEVEL"]
            journaling_manager.recordDebug(f"Loaded log level from env: {self.log_level}")
            
        # Serial communication settings
        if "PENPHIN_SERIAL_BAUD_RATE" in os.environ:
            self.serial_baud_rate = int(os.environ["PENPHIN_SERIAL_BAUD_RATE"])
            journaling_manager.recordDebug(f"Loaded serial baud rate from env: {self.serial_baud_rate}")
        if "PENPHIN_SERIAL_TIMEOUT" in os.environ:
            self.serial_timeout = float(os.environ["PENPHIN_SERIAL_TIMEOUT"])
            journaling_manager.recordDebug(f"Loaded serial timeout from env: {self.serial_timeout}")
        if "PENPHIN_SERIAL_PORT" in os.environ:
            self.serial_port = os.environ["PENPHIN_SERIAL_PORT"]
            journaling_manager.recordDebug(f"Loaded serial port from env: {self.serial_port}")
            
        journaling_manager.recordInfo("Environment variables loaded successfully")

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
            "llm_service": self.llm_service,
            "system": {
                "debug_mode": self.debug_mode,
                "log_level": self.log_level
            },
            "serial": {
                "baud_rate": self.serial_baud_rate,
                "timeout": self.serial_timeout,
                "port": self.serial_port
            }
        }

# Create global configuration instance
CONFIG = MentalConfiguration() 