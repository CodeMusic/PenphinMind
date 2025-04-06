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
import sys

# Get the project root directory (where config.py is located)
PROJECT_ROOT = Path(__file__).parent
CONFIG_FILE = PROJECT_ROOT / "config.json"

# Add SystemJournelingManager after defining PROJECT_ROOT
sys.path.insert(0, str(PROJECT_ROOT))
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel

# Initialize journaling manager with default level first
journaling_manager = SystemJournelingManager()

class AudioOutputType(str, Enum):
    """Audio output device types"""
    WAVESHARE = "waveshare"
    LOCAL_LLM = "local_llm"

class Config:
    """Configuration settings for PenphinMind"""
    def __init__(self):
        journaling_manager.recordScope("MentalConfiguration.__init__")
        
        # Initialize default values
        self._init_defaults()
        
        # Serial settings with defaults
        self.serial_settings = {
            "port": "COM7",
            "baud_rate": 115200,
            "timeout": 1.0,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
            "xonxoff": False,
            "rtscts": False,
            "dsrdtr": False
        }
        
        # Load configuration from config.json
        self._load_config()
        
        # Load environment variables (these override config file settings)
        self._load_env_vars()
        
        # Update journaling manager with configured log level
        self._update_journaling_level()
        
        journaling_manager.recordInfo("Mental configuration initialized")
        
        # Default persona/system message
        self.persona = "You are a helpful assistant named Penphin."

    def _init_defaults(self):
        """Initialize default configuration values"""
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        self.audio_device_controls = {
            "volume": 100,
            "mute": False,
            "input_device": "default",
            "output_device": "default",
            "latency": 0.1,
            "buffer_size": 2048
        }
        
        # Visual settings
        self.visual_height = 32
        self.visual_width = 64
        self.visual_fps = 30
        
        # LED Matrix settings
        self.led_matrix = {
            "rows": 64,
            "cols": 64,
            "chain_length": 1,
            "parallel": 1,
            "hardware_mapping": "regular",
            "brightness": 30,
            "disable_hardware_pulsing": True,
            "gpio_slowdown": 2,
            "pwm_lsb_nanoseconds": 130,
            "pwm_bits": 11
        }
        
        # Splash screen settings
        self.splash_screen = {
            "enabled": True,
            "background_color": (0, 0, 32),  # Dark blue
            "text_color": (255, 255, 255),  # White
            "accent_color": (100, 180, 255),  # Light blue
            "header_text": "PENPHIN",
            "subheader_text": "MIND",
            "show_circuit_pattern": True,
            "loading_steps": [
                {
                    "event": "visual_init", 
                    "progress": 10, 
                    "text": "Loading visual cortex...",
                    "symbol": "👁️",  # Eye symbol for visual cortex
                    "symbol_color": (180, 180, 255)  # Light blue for visual
                },
                {
                    "event": "matrix_init", 
                    "progress": 25, 
                    "text": "Initializing LED matrix...",
                    "symbol": "▢",  # Square symbol for LED matrix
                    "symbol_color": (255, 100, 100)  # Reddish for LEDs
                },
                {
                    "event": "connection", 
                    "progress": 40, 
                    "text": "Connecting components...",
                    "symbol": "≈",  # Wave symbol for connection
                    "symbol_color": (100, 255, 100)  # Green for connection
                },
                {
                    "event": "synaptic_init", 
                    "progress": 60, 
                    "text": "Starting synaptic pathways...",
                    "symbol": "⟷",  # Double arrow for pathways
                    "symbol_color": (255, 200, 100)  # Orange for synaptic
                },
                {
                    "event": "neural_init", 
                    "progress": 80, 
                    "text": "Preparing neural networks...",
                    "symbol": "⦿",  # Circle with dot for neurons
                    "symbol_color": (200, 100, 255)  # Purple for neural
                },
                {
                    "event": "mind_init", 
                    "progress": 95, 
                    "text": "Starting mind processes...",
                    "symbol": "🧠",  # Brain symbol for mind
                    "symbol_color": (255, 255, 100)  # Yellow for mind
                },
                {
                    "event": "complete", 
                    "progress": 100, 
                    "text": "System ready",
                    "symbol": "✓",  # Checkmark for complete
                    "symbol_color": (100, 255, 100)  # Green for complete
                }
            ],
            "symbols": ["👁️", "▢", "≈", "⟷", "⦿", "🧠", "✓"],  # Default symbols as fallback
            "completion_color": (0, 32, 0),  # Dark green
            "completion_text": ["SYSTEM", "READY"]
        }
        
        # Motor settings
        self.motor_speed = 100
        self.motor_acceleration = 50
        
        # System settings
        self.debug_mode = False
        self.log_level = "DEBUG"
        self.log_file = str(PROJECT_ROOT / "logs" / "penphin.log")
        
        # ADB settings
        self.adb_path = "adb"  # Default to system adb

    def _load_config(self) -> None:
        """Load configuration from config.json"""
        journaling_manager.recordScope("MentalConfiguration._load_config")
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                    
                # Load corpus callosum settings
                if "corpus_callosum" in config_data:
                    cc_config = config_data["corpus_callosum"]
                    
                    # Load ADB path
                    if "adb_path" in cc_config:
                        self.adb_path = cc_config["adb_path"]
                    
                    # Load serial settings
                    if "serial_settings" in cc_config:
                        self.serial_settings.update(cc_config["serial_settings"])
                        journaling_manager.recordInfo(f"Loaded serial settings: {self.serial_settings}")
                    
                    # Load logging settings
                    if "logging" in cc_config:
                        if "level" in cc_config["logging"]:
                            self.log_level = cc_config["logging"]["level"]
                            journaling_manager.recordInfo(f"Loaded log level: {self.log_level}")
                
                # Load visual cortex settings including splash screen
                if "visual_cortex" in config_data:
                    vc_config = config_data["visual_cortex"]
                    
                    # Load LED matrix settings
                    if "led_matrix" in vc_config:
                        led_config = vc_config["led_matrix"]
                        
                        # Create a dictionary to store matrix settings
                        self.led_matrix = {
                            "rows": led_config.get("rows", 64),
                            "cols": led_config.get("cols", 64),
                            "chain_length": led_config.get("chain_length", 1),
                            "parallel": led_config.get("parallel", 1),
                            "hardware_mapping": led_config.get("hardware_mapping", "regular"),
                            "brightness": led_config.get("brightness", 30),
                            "disable_hardware_pulsing": led_config.get("disable_hardware_pulsing", True),
                            "gpio_slowdown": led_config.get("gpio_slowdown", 2),
                            "pwm_lsb_nanoseconds": led_config.get("pwm_lsb_nanoseconds", 130),
                            "pwm_bits": led_config.get("pwm_bits", 11)
                        }
                        journaling_manager.recordInfo("Loaded LED matrix settings from config.json")
                    
                    # Load splash screen settings
                    if "splash_screen" in vc_config:
                        splash_config = vc_config["splash_screen"]
                        
                        # Convert array values back to tuples where needed (for colors)
                        for key in ["background_color", "text_color", "accent_color", "completion_color"]:
                            if key in splash_config and isinstance(splash_config[key], list):
                                splash_config[key] = tuple(splash_config[key])
                        
                        # Convert colors in loading steps
                        if "loading_steps" in splash_config:
                            for step in splash_config["loading_steps"]:
                                if "symbol_color" in step and isinstance(step["symbol_color"], list):
                                    step["symbol_color"] = tuple(step["symbol_color"])
                        
                        # Update splash screen settings
                        self.splash_screen.update(splash_config)
                        journaling_manager.recordInfo("Loaded splash screen settings from config.json")
                    
                journaling_manager.recordInfo(f"Configuration loaded from {CONFIG_FILE}")
            else:
                journaling_manager.recordWarning(f"Config file not found at {CONFIG_FILE}, using defaults")
                
        except Exception as e:
            journaling_manager.recordError(f"Error loading config.json: {e}")
            import traceback
            journaling_manager.recordError(f"Traceback: {traceback.format_exc()}")

    def save(self) -> bool:
        """Save current configuration to JSON file"""
        try:
            # Convert tuples to lists for JSON serialization
            def convert_tuples(obj):
                if isinstance(obj, tuple):
                    return list(obj)
                elif isinstance(obj, dict):
                    return {k: convert_tuples(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_tuples(i) for i in obj]
                else:
                    return obj
            
            # Prepare splash screen config (convert tuples to lists)
            splash_screen_config = convert_tuples(self.splash_screen)
            
            # Ensure the config structure matches the expected format
            config_data = {
                "corpus_callosum": {
                    "adb_path": self.adb_path,
                    "serial_settings": self.serial_settings,
                    "api_keys": {
                        "openai": "",
                        "elevenlabs": ""
                    },
                    "logging": {
                        "level": self.log_level,
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    }
                },
                "visual_cortex": {
                    "led_matrix": self.led_matrix,
                    "splash_screen": splash_screen_config
                }
                # Add other sections as needed...
            }
            
            # Ensure directory exists
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with pretty formatting
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            
            journaling_manager.recordInfo(f"Configuration saved to {CONFIG_FILE}")
            return True
        except Exception as e:
            journaling_manager.recordError(f"Error saving config: {e}")
            return False

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
            
        # System settings
        if "PENPHIN_DEBUG_MODE" in os.environ:
            self.debug_mode = os.environ["PENPHIN_DEBUG_MODE"].lower() == "true"
            journaling_manager.recordDebug(f"Loaded debug mode from env: {self.debug_mode}")
        if "PENPHIN_LOG_LEVEL" in os.environ:
            self.log_level = os.environ["PENPHIN_LOG_LEVEL"]
            journaling_manager.recordDebug(f"Loaded log level from env: {self.log_level}")
            
        # Serial settings from environment
        if "PENPHIN_SERIAL_PORT" in os.environ:
            self.serial_settings["port"] = os.environ["PENPHIN_SERIAL_PORT"]
        if "PENPHIN_SERIAL_BAUD" in os.environ:
            self.serial_settings["baud_rate"] = int(os.environ["PENPHIN_SERIAL_BAUD"])
        if "PENPHIN_SERIAL_TIMEOUT" in os.environ:
            self.serial_settings["timeout"] = float(os.environ["PENPHIN_SERIAL_TIMEOUT"])
            
        journaling_manager.recordInfo("Environment variables loaded successfully")

    def _update_journaling_level(self):
        """Update the journaling manager with the configured log level"""
        try:
            # Convert string level to SystemJournelingLevel enum
            if self.log_level.upper() == "DEBUG":
                level = SystemJournelingLevel.DEBUG
            elif self.log_level.upper() == "INFO":
                level = SystemJournelingLevel.INFO
            elif self.log_level.upper() == "WARNING":
                level = SystemJournelingLevel.WARNING
            elif self.log_level.upper() == "ERROR":
                level = SystemJournelingLevel.ERROR
            else:
                level = SystemJournelingLevel.INFO
                
            # Update journaling manager level
            journaling_manager.setLevel(level)
            print(f"[CONFIG] Updated journaling level to {level.name}")
            
        except Exception as e:
            print(f"[CONFIG] Error updating journaling level: {e}")
            # Fallback to INFO level
            journaling_manager.setLevel(SystemJournelingLevel.INFO)

# Global config instance
CONFIG = Config()

# System-wide configuration reference
CONFIG_SYSTEM = {
    # System settings
    "log_level": "INFO",
    "debug_mode": False,
    
    # Default connection timeouts
    "default_timeout": 5.0,
    
    # Audio hardware settings
    "audio_sample_rate": 16000,
    "audio_channels": 1,
    
    # Device settings
    "audio_device_controls": {
        "volume": 100,
        "mute": False
    },
    
    # Serial settings
    "serial_settings": {
        "port": "auto",
        "baud_rate": 115200,
        "timeout": 1.0
    }
}

# Add the get_mind_config function if not already present
import importlib.util
import os
from typing import Dict, Any

def get_mind_config(mind_id: str = None) -> Dict[str, Any]:
    """
    Get configuration for a specific mind
    
    This function delegates to Mind/mind_config.py's get_mind_by_id
    to maintain a clean separation between mind-specific and system-wide configs.
    
    Note: For new code, prefer using get_mind_by_id() directly from Mind.mind_config 
    to avoid potential circular imports. This function is maintained for backward 
    compatibility with existing code.
    
    Args:
        mind_id: ID of the mind to retrieve, or None for default
        
    Returns:
        Dict containing the mind configuration
    """
    from Mind.mind_config import get_mind_by_id
    return get_mind_by_id(mind_id) 