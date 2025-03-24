from enum import Enum
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union
import json

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
        self.timestamp: float = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.command_type.value,
            "timestamp": self.timestamp
        }

@dataclass
class ASRCommand(BaseCommand):
    """Automatic Speech Recognition commands"""
    input_audio: bytes
    language: str = "en"
    model_type: str = "base"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "input_audio": self.input_audio.hex() if self.input_audio else None,
            "language": self.language,
            "model_type": self.model_type
        })
        return data

@dataclass
class TTSCommand(BaseCommand):
    """Text-to-Speech command"""
    def __init__(self, command_type: CommandType, text: str, voice_id: str = "default", 
                 speed: float = 1.0, pitch: float = 1.0):
        super().__init__(command_type)
        self.text = text
        self.voice_id = voice_id
        self.speed = speed
        self.pitch = pitch
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command_type": self.command_type.value,
            "text": self.text,
            "voice_id": self.voice_id,
            "speed": self.speed,
            "pitch": self.pitch
        }

@dataclass
class VADCommand(BaseCommand):
    """Voice Activity Detection commands"""
    audio_chunk: bytes
    threshold: float = 0.5
    frame_duration: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "audio_chunk": self.audio_chunk.hex(),
            "threshold": self.threshold,
            "frame_duration": self.frame_duration
        })
        return data

@dataclass
class LLMCommand(BaseCommand):
    """Large Language Model commands"""
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7
    model: str = "gpt-3.5-turbo"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "prompt": self.prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "model": self.model
        })
        return data

@dataclass
class VLMCommand(BaseCommand):
    """Vision Language Model commands"""
    image_data: bytes
    prompt: Optional[str] = None
    task_type: str = "classify"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "image_data": self.image_data.hex(),
            "prompt": self.prompt,
            "task_type": self.task_type
        })
        return data

@dataclass
class KWSCommand(BaseCommand):
    """Keyword Spotting commands"""
    keywords: List[str]
    sensitivity: float = 0.5
    audio_data: Optional[bytes] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "keywords": self.keywords,
            "sensitivity": self.sensitivity,
            "audio_data": self.audio_data.hex() if self.audio_data else None
        })
        return data

@dataclass
class SystemCommand(BaseCommand):
    """System control commands"""
    action: str
    parameters: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "action": self.action,
            "parameters": self.parameters or {}
        })
        return data

@dataclass
class AudioCommand(BaseCommand):
    """Audio processing commands"""
    operation: str
    audio_data: bytes
    sample_rate: int = 16000
    channels: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "operation": self.operation,
            "audio_data": self.audio_data.hex(),
            "sample_rate": self.sample_rate,
            "channels": self.channels
        })
        return data

@dataclass
class CameraCommand(BaseCommand):
    """Camera control commands"""
    action: str
    resolution: tuple = (640, 480)
    format: str = "RGB"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "action": self.action,
            "resolution": list(self.resolution),
            "format": self.format
        })
        return data

@dataclass
class YOLOCommand(BaseCommand):
    """YOLO object detection commands"""
    image_data: bytes
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.4
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "image_data": self.image_data.hex(),
            "confidence_threshold": self.confidence_threshold,
            "nms_threshold": self.nms_threshold
        })
        return data

@dataclass
class WhisperCommand(BaseCommand):
    """Whisper speech recognition commands"""
    audio_data: bytes
    language: Optional[str] = None
    task: str = "transcribe"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "audio_data": self.audio_data.hex(),
            "language": self.language,
            "task": self.task
        })
        return data

@dataclass
class MeloTTSCommand(BaseCommand):
    """MeloTTS synthesis commands"""
    text: str
    speaker_id: str = "default"
    language: str = "en"
    style: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "text": self.text,
            "speaker_id": self.speaker_id,
            "language": self.language,
            "style": self.style
        })
        return data

class CommandSerializer:
    """Handles command serialization/deserialization"""
    
    @staticmethod
    def serialize(command: BaseCommand) -> Dict[str, Any]:
        """Serialize command to dictionary format"""
        if not isinstance(command, BaseCommand):
            raise ValueError("Invalid command type")
            
        # Use the command's to_dict method if available
        if hasattr(command, 'to_dict'):
            return command.to_dict()
            
        # Fallback to basic serialization
        return {
            "command_type": command.command_type.value,
            **{k: v for k, v in command.__dict__.items() if not k.startswith('_')}
        }

class CommandFactory:
    """Factory class for creating neural commands"""
    
    @staticmethod
    def create_command(command_type: Union[str, CommandType], **kwargs) -> BaseCommand:
        """Create a command instance based on type"""
        if isinstance(command_type, str):
            command_type = CommandType(command_type.lower())
            
        command_map = {
            CommandType.ASR: ASRCommand,
            CommandType.TTS: TTSCommand,
            CommandType.VAD: VADCommand,
            CommandType.LLM: LLMCommand,
            CommandType.VLM: VLMCommand,
            CommandType.KWS: KWSCommand,
            CommandType.SYS: SystemCommand,
            CommandType.AUDIO: AudioCommand,
            CommandType.CAMERA: CameraCommand,
            CommandType.YOLO: YOLOCommand,
            CommandType.WHISPER: WhisperCommand,
            CommandType.MELOTTS: MeloTTSCommand
        }
        
        if command_type not in command_map:
            raise ValueError(f"Unknown command type: {command_type}")
            
        return command_map[command_type](command_type=command_type, **kwargs) 