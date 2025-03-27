from enum import Enum
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union, Type
import json
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
                "type": self.command_type.value,
                "timestamp": self.timestamp
            }
            journaling_manager.recordDebug(f"Converted command to dict: {data}")
            return data
            
        except Exception as e:
            journaling_manager.recordError(f"Error converting command to dict: {e}")
            raise
            
    def validate(self) -> bool:
        """Validate command data"""
        journaling_manager.recordScope("BaseCommand.validate")
        try:
            if not isinstance(self.command_type, CommandType):
                journaling_manager.recordError(f"Invalid command type: {self.command_type}")
                return False
                
            if not isinstance(self.timestamp, (int, float)):
                journaling_manager.recordError(f"Invalid timestamp: {self.timestamp}")
                return False
                
            journaling_manager.recordDebug("Command validated successfully")
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"Error validating command: {e}")
            return False

@dataclass
class ASRCommand(BaseCommand):
    """Automatic Speech Recognition commands"""
    input_audio: bytes
    language: str = "en"
    model_type: str = "base"
    
    def __post_init__(self):
        """Initialize ASR command"""
        journaling_manager.recordScope("ASRCommand.__post_init__")
        super().__post_init__()
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

@dataclass
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

@dataclass
class VADCommand(BaseCommand):
    """Voice Activity Detection commands"""
    audio_chunk: bytes
    threshold: float = 0.5
    frame_duration: int = 30
    
    def __post_init__(self):
        """Initialize VAD command"""
        journaling_manager.recordScope("VADCommand.__post_init__")
        super().__post_init__()
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

@dataclass
class LLMCommand(BaseCommand):
    """Large Language Model commands"""
    prompt: str
    max_tokens: int = 150
    temperature: float = 0.7
    model: str = "gpt-3.5-turbo"
    
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

@dataclass
class VLMCommand(BaseCommand):
    """Vision Language Model commands"""
    image_data: bytes
    prompt: Optional[str] = None
    task_type: str = "classify"
    
    def __post_init__(self):
        """Initialize VLM command"""
        journaling_manager.recordScope("VLMCommand.__post_init__")
        super().__post_init__()
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

@dataclass
class KWSCommand(BaseCommand):
    """Keyword Spotting commands"""
    keywords: List[str]
    sensitivity: float = 0.5
    audio_data: Optional[bytes] = None
    
    def __post_init__(self):
        """Initialize KWS command"""
        journaling_manager.recordScope("KWSCommand.__post_init__")
        super().__post_init__()
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

@dataclass
class SystemCommand(BaseCommand):
    """System control commands"""
    action: str
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize system command"""
        journaling_manager.recordScope("SystemCommand.__post_init__")
        super().__post_init__()
        if self.parameters is None:
            self.parameters = {}
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

@dataclass
class AudioCommand(BaseCommand):
    """Audio processing commands"""
    operation: str
    audio_data: bytes
    sample_rate: int = 16000
    channels: int = 1
    
    def __post_init__(self):
        """Initialize Audio command"""
        journaling_manager.recordScope("AudioCommand.__post_init__")
        super().__post_init__()
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

@dataclass
class CameraCommand(BaseCommand):
    """Camera control commands"""
    action: str
    resolution: tuple = (640, 480)
    format: str = "RGB"
    
    def __post_init__(self):
        """Initialize Camera command"""
        journaling_manager.recordScope("CameraCommand.__post_init__")
        super().__post_init__()
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

@dataclass
class YOLOCommand(BaseCommand):
    """YOLO object detection commands"""
    image_data: bytes
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.4
    
    def __post_init__(self):
        """Initialize YOLO command"""
        journaling_manager.recordScope("YOLOCommand.__post_init__")
        super().__post_init__()
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

@dataclass
class WhisperCommand(BaseCommand):
    """Whisper speech recognition commands"""
    audio_data: bytes
    language: Optional[str] = None
    task: str = "transcribe"
    
    def __post_init__(self):
        """Initialize Whisper command"""
        journaling_manager.recordScope("WhisperCommand.__post_init__")
        super().__post_init__()
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

@dataclass
class MeloTTSCommand(BaseCommand):
    """MeloTTS synthesis commands"""
    text: str
    speaker_id: str = "default"
    language: str = "en"
    style: Optional[str] = None
    
    def __post_init__(self):
        """Initialize MeloTTS command"""
        journaling_manager.recordScope("MeloTTSCommand.__post_init__")
        super().__post_init__()
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
    """Factory class for creating neural commands"""
    
    _command_types: Dict[CommandType, Type[BaseCommand]] = {}
    
    @classmethod
    def register_command_type(cls, command_type: CommandType, command_class: Type[BaseCommand]) -> None:
        """Register a command type with its class"""
        journaling_manager.recordScope("CommandFactory.register_command_type", command_type=command_type)
        try:
            if not issubclass(command_class, BaseCommand):
                journaling_manager.recordError(f"Invalid command class: {command_class}")
                raise ValueError(f"Command class must inherit from BaseCommand")
                
            cls._command_types[command_type] = command_class
            journaling_manager.recordDebug(f"Registered command type: {command_type} with class: {command_class.__name__}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error registering command type: {e}")
            raise
            
    @classmethod
    def create_command(cls, command_type: CommandType, **kwargs) -> BaseCommand:
        """Create a command instance"""
        journaling_manager.recordScope("CommandFactory.create_command", command_type=command_type, kwargs=kwargs)
        try:
            if command_type not in cls._command_types:
                journaling_manager.recordError(f"Unknown command type: {command_type}")
                raise ValueError(f"Unknown command type: {command_type}")
                
            command_class = cls._command_types[command_type]
            command = command_class(command_type=command_type, **kwargs)
            
            if not command.validate():
                journaling_manager.recordError("Command validation failed")
                raise ValueError("Invalid command data")
                
            journaling_manager.recordDebug(f"Created command: {command_type} with class: {command_class.__name__}")
            return command
            
        except Exception as e:
            journaling_manager.recordError(f"Error creating command: {e}")
            raise
            
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BaseCommand:
        """Create a command from dictionary data"""
        journaling_manager.recordScope("CommandFactory.from_dict", data=data)
        try:
            if not isinstance(data, dict):
                journaling_manager.recordError("Invalid data type")
                raise ValueError("Data must be a dictionary")
                
            if "type" not in data:
                journaling_manager.recordError("Missing command type")
                raise ValueError("Data must contain 'type' field")
                
            command_type = CommandType(data["type"])
            command = cls.create_command(command_type, **data)
            
            journaling_manager.recordDebug(f"Created command from dict: {command_type}")
            return command
            
        except Exception as e:
            journaling_manager.recordError(f"Error creating command from dict: {e}")
            raise
            
    @classmethod
    def from_json(cls, json_str: str) -> BaseCommand:
        """Create a command from JSON string"""
        journaling_manager.recordScope("CommandFactory.from_json", json_str=json_str)
        try:
            if not isinstance(json_str, str):
                journaling_manager.recordError("Invalid JSON string type")
                raise ValueError("Input must be a JSON string")
                
            data = json.loads(json_str)
            command = cls.from_dict(data)
            
            journaling_manager.recordDebug(f"Created command from JSON: {command.command_type}")
            return command
            
        except json.JSONDecodeError as e:
            journaling_manager.recordError(f"Invalid JSON format: {e}")
            raise
        except Exception as e:
            journaling_manager.recordError(f"Error creating command from JSON: {e}")
            raise 