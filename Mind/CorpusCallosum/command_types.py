"""
Base command types for the neural command system
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any
import time
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class CommandType(Enum):
    """Types of neural commands supported by the system"""
    ASR = "asr"  # Automatic Speech Recognition
    TTS = "tts"  # Text to Speech
    VAD = "vad"  # Voice Activity Detection
    LLM = "llm"  # Large Language Model
    VLM = "vlm"  # Vision Language Model
    KWS = "kws"  # Keyword Spotting
    SYS = "sys"  # System Commands
    AUDIO = "audio"  # Audio Processing
    CAMERA = "camera"  # Camera Control
    YOLO = "yolo"  # Object Detection
    WHISPER = "whisper"  # Speech Recognition
    MELOTTS = "melotts"  # Neural TTS

@dataclass
class BaseCommand:
    """Base class for all neural commands"""
    command_type: CommandType
    action: str = "process"  # Default action for all commands
    
    def __post_init__(self):
        """Initialize command timestamp"""
        journaling_manager.recordScope("BaseCommand.__post_init__")
        try:
            if not isinstance(self.command_type, CommandType):
                journaling_manager.recordError(f"Invalid command type: {self.command_type}")
                raise ValueError("Command type must be a CommandType enum")
                
            self.timestamp: float = time.time()
            journaling_manager.recordDebug(f"Command timestamp set to: {self.timestamp}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing command: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary"""
        journaling_manager.recordScope("BaseCommand.to_dict")
        try:
            data = {
                "command_type": self.command_type.value,
                "action": self.action,
                "timestamp": self.timestamp
            }
            journaling_manager.recordDebug(f"Command converted to dict: {data}")
            return data
            
        except Exception as e:
            journaling_manager.recordError(f"Error converting command to dict: {e}")
            raise 