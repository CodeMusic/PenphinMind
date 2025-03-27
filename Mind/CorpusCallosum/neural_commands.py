"""
Neural command system for PenphinMind
"""

from typing import Dict, Any, Type, Optional, List
from dataclasses import dataclass, field
import json
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from .command_types import BaseCommand, CommandType
from .command_loader import CommandLoader

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class ASRCommand(BaseCommand):
    """Automatic Speech Recognition commands"""
    def __init__(self, command_type: CommandType, input_audio: bytes, language: str = "en", model_type: str = "base"):
        journaling_manager.recordScope("ASRCommand.__init__")
        super().__init__(command_type)
        self.input_audio = input_audio
        self.language = language
        self.model_type = model_type
        journaling_manager.recordDebug(f"ASR command initialized with language: {self.language}, model: {self.model_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ASR command to dictionary"""
        journaling_manager.recordScope("ASRCommand.to_dict")
        data = super().to_dict()
        data.update({
            "input_audio": self.input_audio.hex() if self.input_audio else None,
            "language": self.language,
            "model_type": self.model_type
        })
        journaling_manager.recordDebug(f"Converted ASR command to dict: {data}")
        return data

class TTSCommand(BaseCommand):
    """Text-to-Speech command"""
    def __init__(self, command_type: CommandType, text: str, voice_id: str = "default", 
                 speed: float = 1.0, pitch: float = 1.0):
        journaling_manager.recordScope("TTSCommand.__init__")
        super().__init__(command_type)
        self.text = text
        self.voice_id = voice_id
        self.speed = speed
        self.pitch = pitch
        journaling_manager.recordDebug(f"TTS command initialized with voice: {voice_id}, speed: {speed}, pitch: {pitch}")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert TTS command to dictionary"""
        journaling_manager.recordScope("TTSCommand.to_dict")
        data = {
            "command_type": self.command_type.value,
            "text": self.text,
            "voice_id": self.voice_id,
            "speed": self.speed,
            "pitch": self.pitch
        }
        journaling_manager.recordDebug(f"Converted TTS command to dict: {data}")
        return data

class VADCommand(BaseCommand):
    """Voice Activity Detection commands"""
    def __init__(self, command_type: CommandType, audio_chunk: bytes, threshold: float = 0.5, frame_duration: int = 30):
        journaling_manager.recordScope("VADCommand.__init__")
        super().__init__(command_type)
        self.audio_chunk = audio_chunk
        self.threshold = threshold
        self.frame_duration = frame_duration
        journaling_manager.recordDebug(f"VAD command initialized with threshold: {self.threshold}, frame_duration: {self.frame_duration}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert VAD command to dictionary"""
        journaling_manager.recordScope("VADCommand.to_dict")
        data = super().to_dict()
        data.update({
            "audio_chunk": self.audio_chunk.hex(),
            "threshold": self.threshold,
            "frame_duration": self.frame_duration
        })
        journaling_manager.recordDebug(f"Converted VAD command to dict: {data}")
        return data

class LLMCommand(BaseCommand):
    """Large Language Model commands"""
    def __init__(
        self,
        command_type: CommandType,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.7,
        model: str = "gpt-3.5-turbo"
    ):
        journaling_manager.recordScope("LLMCommand.__init__")
        super().__init__(command_type)
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.model = model
        journaling_manager.recordDebug(f"LLM command initialized with model: {model}, max_tokens: {max_tokens}, temperature: {temperature}")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary for JSON serialization"""
        journaling_manager.recordScope("LLMCommand.to_dict")
        data = {
            "command_type": self.command_type.value,
            "prompt": self.prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "model": self.model
        }
        journaling_manager.recordDebug(f"Converted LLM command to dict: {data}")
        return data

class VLMCommand(BaseCommand):
    """Vision Language Model commands"""
    def __init__(self, command_type: CommandType, image_data: bytes, prompt: Optional[str] = None, task_type: str = "classify"):
        journaling_manager.recordScope("VLMCommand.__init__")
        super().__init__(command_type)
        self.image_data = image_data
        self.prompt = prompt
        self.task_type = task_type
        journaling_manager.recordDebug(f"VLM command initialized with task_type: {self.task_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert VLM command to dictionary"""
        journaling_manager.recordScope("VLMCommand.to_dict")
        data = super().to_dict()
        data.update({
            "image_data": self.image_data.hex(),
            "prompt": self.prompt,
            "task_type": self.task_type
        })
        journaling_manager.recordDebug(f"Converted VLM command to dict: {data}")
        return data

class KWSCommand(BaseCommand):
    """Keyword Spotting commands"""
    def __init__(self, command_type: CommandType, keywords: List[str], sensitivity: float = 0.5, audio_data: Optional[bytes] = None):
        journaling_manager.recordScope("KWSCommand.__init__")
        super().__init__(command_type)
        self.keywords = keywords
        self.sensitivity = sensitivity
        self.audio_data = audio_data
        journaling_manager.recordDebug(f"KWS command initialized with keywords: {self.keywords}, sensitivity: {self.sensitivity}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert KWS command to dictionary"""
        journaling_manager.recordScope("KWSCommand.to_dict")
        data = super().to_dict()
        data.update({
            "keywords": self.keywords,
            "sensitivity": self.sensitivity,
            "audio_data": self.audio_data.hex() if self.audio_data else None
        })
        journaling_manager.recordDebug(f"Converted KWS command to dict: {data}")
        return data

class SystemCommand(BaseCommand):
    """System control commands"""
    def __init__(self, command_type: CommandType, action: str, parameters: Dict[str, Any] = None):
        journaling_manager.recordScope("SystemCommand.__init__")
        super().__init__(command_type)
        self.action = action
        self.parameters = parameters or {}
        journaling_manager.recordDebug(f"System command initialized with action: {self.action}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system command to dictionary"""
        journaling_manager.recordScope("SystemCommand.to_dict")
        data = super().to_dict()
        data.update({
            "action": self.action,
            "parameters": self.parameters
        })
        journaling_manager.recordDebug(f"Converted system command to dict: {data}")
        return data
        
    def validate(self) -> bool:
        """Validate system command"""
        journaling_manager.recordScope("SystemCommand.validate")
        try:
            if not self.action:
                journaling_manager.recordError("System command missing action")
                return False
                
            if not isinstance(self.parameters, dict):
                journaling_manager.recordError("System command parameters must be a dictionary")
                return False
                
            journaling_manager.recordDebug("System command validated successfully")
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"Error validating system command: {e}")
            return False

class AudioCommand(BaseCommand):
    """Audio processing commands"""
    def __init__(self, command_type: CommandType, operation: str, audio_data: bytes, sample_rate: int = 16000, channels: int = 1):
        journaling_manager.recordScope("AudioCommand.__init__")
        super().__init__(command_type)
        self.operation = operation
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.channels = channels
        journaling_manager.recordDebug(f"Audio command initialized with operation: {self.operation}, sample_rate: {self.sample_rate}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Audio command to dictionary"""
        journaling_manager.recordScope("AudioCommand.to_dict")
        data = super().to_dict()
        data.update({
            "operation": self.operation,
            "audio_data": self.audio_data.hex(),
            "sample_rate": self.sample_rate,
            "channels": self.channels
        })
        journaling_manager.recordDebug(f"Converted Audio command to dict: {data}")
        return data

class CameraCommand(BaseCommand):
    """Camera control commands"""
    def __init__(self, command_type: CommandType, action: str, resolution: tuple = (640, 480), format: str = "RGB"):
        journaling_manager.recordScope("CameraCommand.__init__")
        super().__init__(command_type)
        self.action = action
        self.resolution = resolution
        self.format = format
        journaling_manager.recordDebug(f"Camera command initialized with action: {self.action}, resolution: {self.resolution}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Camera command to dictionary"""
        journaling_manager.recordScope("CameraCommand.to_dict")
        data = super().to_dict()
        data.update({
            "action": self.action,
            "resolution": list(self.resolution),
            "format": self.format
        })
        journaling_manager.recordDebug(f"Converted Camera command to dict: {data}")
        return data

class YOLOCommand(BaseCommand):
    """YOLO object detection commands"""
    def __init__(self, command_type: CommandType, image_data: bytes, confidence_threshold: float = 0.5, nms_threshold: float = 0.4):
        journaling_manager.recordScope("YOLOCommand.__init__")
        super().__init__(command_type)
        self.image_data = image_data
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        journaling_manager.recordDebug(f"YOLO command initialized with confidence: {self.confidence_threshold}, nms: {self.nms_threshold}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert YOLO command to dictionary"""
        journaling_manager.recordScope("YOLOCommand.to_dict")
        data = super().to_dict()
        data.update({
            "image_data": self.image_data.hex(),
            "confidence_threshold": self.confidence_threshold,
            "nms_threshold": self.nms_threshold
        })
        journaling_manager.recordDebug(f"Converted YOLO command to dict: {data}")
        return data

class WhisperCommand(BaseCommand):
    """Whisper speech recognition commands"""
    def __init__(self, command_type: CommandType, audio_data: bytes, language: Optional[str] = None, task: str = "transcribe"):
        journaling_manager.recordScope("WhisperCommand.__init__")
        super().__init__(command_type)
        self.audio_data = audio_data
        self.language = language
        self.task = task
        journaling_manager.recordDebug(f"Whisper command initialized with task: {self.task}, language: {self.language}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Whisper command to dictionary"""
        journaling_manager.recordScope("WhisperCommand.to_dict")
        data = super().to_dict()
        data.update({
            "audio_data": self.audio_data.hex(),
            "language": self.language,
            "task": self.task
        })
        journaling_manager.recordDebug(f"Converted Whisper command to dict: {data}")
        return data

class MeloTTSCommand(BaseCommand):
    """MeloTTS synthesis commands"""
    def __init__(self, command_type: CommandType, text: str, speaker_id: str = "default", language: str = "en", style: Optional[str] = None):
        journaling_manager.recordScope("MeloTTSCommand.__init__")
        super().__init__(command_type)
        self.text = text
        self.speaker_id = speaker_id
        self.language = language
        self.style = style
        journaling_manager.recordDebug(f"MeloTTS command initialized with speaker: {self.speaker_id}, language: {self.language}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert MeloTTS command to dictionary"""
        journaling_manager.recordScope("MeloTTSCommand.to_dict")
        data = super().to_dict()
        data.update({
            "text": self.text,
            "speaker_id": self.speaker_id,
            "language": self.language,
            "style": self.style
        })
        journaling_manager.recordDebug(f"Converted MeloTTS command to dict: {data}")
        return data

class CommandSerializer:
    """Handles command serialization/deserialization"""
    
    @staticmethod
    def serialize(command: BaseCommand) -> Dict[str, Any]:
        """Serialize command to dictionary format"""
        journaling_manager.recordScope("CommandSerializer.serialize", command=command)
        try:
            if not isinstance(command, BaseCommand):
                journaling_manager.recordError("Invalid command type")
                raise ValueError("Invalid command type")
                
            # Use the command's to_dict method if available
            if hasattr(command, 'to_dict'):
                data = command.to_dict()
                journaling_manager.recordDebug(f"Serialized command using to_dict: {data}")
                return data
                
            # Fallback to basic serialization
            data = {
                "command_type": command.command_type.value,
                **{k: v for k, v in command.__dict__.items() if not k.startswith('_')}
            }
            journaling_manager.recordDebug(f"Serialized command using fallback: {data}")
            return data
            
        except Exception as e:
            journaling_manager.recordError(f"Error serializing command: {e}")
            raise
            
    @staticmethod
    def deserialize(data: Dict[str, Any]) -> BaseCommand:
        """Deserialize command from dictionary format"""
        journaling_manager.recordScope("CommandSerializer.deserialize", data=data)
        try:
            if not isinstance(data, dict):
                journaling_manager.recordError("Invalid data type")
                raise ValueError("Invalid data type")
                
            command_type = CommandType(data["command_type"])
            command = CommandFactory.create_command(command_type, **data)
            
            journaling_manager.recordDebug(f"Deserialized command: {command_type}")
            return command
            
        except Exception as e:
            journaling_manager.recordError(f"Error deserializing command: {e}")
            raise
            
    @staticmethod
    def to_json(command: BaseCommand) -> str:
        """Serialize command to JSON string"""
        journaling_manager.recordScope("CommandSerializer.to_json", command=command)
        try:
            data = CommandSerializer.serialize(command)
            json_str = json.dumps(data)
            journaling_manager.recordDebug(f"Serialized command to JSON: {json_str}")
            return json_str
            
        except Exception as e:
            journaling_manager.recordError(f"Error serializing command to JSON: {e}")
            raise
            
    @staticmethod
    def from_json(json_str: str) -> BaseCommand:
        """Deserialize command from JSON string"""
        journaling_manager.recordScope("CommandSerializer.from_json", json_str=json_str)
        try:
            data = json.loads(json_str)
            command = CommandSerializer.deserialize(data)
            journaling_manager.recordDebug(f"Deserialized command from JSON: {command.command_type}")
            return command
            
        except Exception as e:
            journaling_manager.recordError(f"Error deserializing command from JSON: {e}")
            raise

class CommandFactory:
    """Factory for creating command instances"""
    
    def __init__(self):
        """Initialize the command factory"""
        journaling_manager.recordScope("CommandFactory.__init__")
        self.loader = CommandLoader()
        self.command_classes = self.loader.load_commands()
        
    def create_command(self, command_type: CommandType, **kwargs) -> BaseCommand:
        """Create a command instance"""
        journaling_manager.recordScope("CommandFactory.create_command", command_type=command_type, kwargs=kwargs)
        try:
            # Get the command class
            command_class = self.loader.get_command_class(command_type.value)
            
            # Create the command instance
            command = command_class(command_type=command_type, **kwargs)
            journaling_manager.recordDebug(f"Created command instance: {command}")
            return command
            
        except Exception as e:
            journaling_manager.recordError(f"Error creating command: {e}")
            raise
            
    def validate_command(self, command_type: CommandType, data: Dict[str, Any]) -> None:
        """Validate command data"""
        journaling_manager.recordScope("CommandFactory.validate_command", command_type=command_type, data=data)
        try:
            self.loader.validate_command(command_type.value, data)
            journaling_manager.recordDebug("Command data validated successfully")
        except Exception as e:
            journaling_manager.recordError(f"Command validation failed: {e}")
            raise

# Create global command factory
COMMAND_FACTORY = CommandFactory() 