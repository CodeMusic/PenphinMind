"""
M5Stack LLM Module API v1.0.0 Command Definitions
Single source of truth for hardware API commands
"""

from typing import Dict, Any, Optional
import time
import json
from enum import Enum, auto

class CommandType(Enum):
    """Command types for neural operations"""
    SYSTEM = "system"
    LLM = "llm"
    AUDIO = "audio"  # Single audio type

class BaseCommand:
    """Base class for all commands"""
    def __init__(self, request_id: str = None):
        self.request_id = request_id or f"cmd_{int(time.time())}"
        self.work_id = None
        self.action = None
        self.data = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary format"""
        return {
            "request_id": self.request_id,
            "work_id": self.work_id,
            "action": self.action,
            "data": self.data
        }

class LLMCommand(BaseCommand):
    """LLM-specific commands"""
    def __init__(self, request_id: str = None):
        super().__init__(request_id)
        self.work_id = "llm"

    @classmethod
    def create_setup_command(cls, 
                           model: str,
                           response_format: str = "llm.utf-8",
                           input: str = "llm.utf-8",
                           enoutput: bool = True,
                           enkws: bool = False,
                           max_token_len: int = 127,
                           prompt: Optional[str] = None,
                           **kwargs) -> 'LLMCommand':
        cmd = cls()
        cmd.action = "setup"
        cmd.data = {
            "model": model,
            "response_format": response_format,
            "input": input,
            "enoutput": enoutput,
            "enkws": enkws,
            "max_token_len": max_token_len,
            **({"prompt": prompt} if prompt else {}),
            **kwargs
        }
        return cmd

    @classmethod
    def create_think_command(cls,
                           prompt: str,
                           stream: bool = False,
                           **kwargs) -> 'LLMCommand':
        cmd = cls()
        cmd.action = "inference"
        cmd.data = {
            "delta": prompt,
            "stream": stream,
            **kwargs
        }
        return cmd

class SystemCommand(BaseCommand):
    """System-level commands"""
    def __init__(self, request_id: str = None):
        super().__init__(request_id)
        self.work_id = "sys"

    @classmethod
    def create_reset_command(cls,
                           target: str,
                           request_id: Optional[str] = None) -> 'SystemCommand':
        cmd = cls(request_id)
        cmd.action = "reset"
        cmd.data = {
            "target": target
        }
        return cmd

    @classmethod
    def create_ping_command(cls, request_id=None):
        """
        Create a ping command to check system connectivity
        
        Args:
            request_id: Optional request ID (auto-generated if not provided)
            
        Returns:
            Dict: Command dictionary
        """
        if not request_id:
            request_id = f"ping_{int(time.time())}"
            
        # Format exactly per API spec:
        # {
        #   "request_id": "001",
        #   "work_id": "sys",
        #   "action": "ping"
        # }
        return {
            "request_id": request_id,
            "work_id": "sys",
            "action": "ping"
        }

class AudioCommand(BaseCommand):
    """Base class for all audio-related commands"""
    
    def __init__(self, action: str, data: Dict[str, Any] = None, request_id: str = None):
        super().__init__(
            command_type=CommandType.AUDIO,
            action=action,
            data=data or {},
            request_id=request_id or f"audio_{int(time.time())}"
        )

    @classmethod
    def create_tts_command(cls, text: str, voice: str = "default", 
                          speed: float = 1.0, pitch: float = 1.0) -> 'AudioCommand':
        return cls(
            action="tts",
            data={
                "text": text,
                "voice": voice,
                "speed": speed,
                "pitch": pitch
            }
        )
    
    @classmethod
    def create_asr_command(cls, audio_data: bytes, 
                          language: str = "en") -> 'AudioCommand':
        return cls(
            action="asr",
            data={
                "audio_data": audio_data,
                "language": language
            }
        )
    
    @classmethod
    def create_vad_command(cls, audio_chunk: bytes = b'',
                          threshold: float = 0.5,
                          frame_duration: int = 30) -> 'AudioCommand':
        return cls(
            action="vad",
            data={
                "audio_chunk": audio_chunk,
                "threshold": threshold,
                "frame_duration": frame_duration
            }
        )
    
    @classmethod
    def create_whisper_command(cls, audio_data: bytes,
                             language: str = "en",
                             model_type: str = "base") -> 'AudioCommand':
        return cls(
            action="whisper",
            data={
                "audio_data": audio_data,
                "language": language,
                "model_type": model_type
            }
        )
        
    @classmethod
    def create_kws_command(cls, audio_data: bytes,
                          wake_word: str = "hey penphin") -> 'AudioCommand':
        return cls(
            action="kws",
            data={
                "audio_data": audio_data,
                "wake_word": wake_word
            }
        )

class WhisperCommand(BaseCommand):
    """Command for Whisper ASR operations"""
    
    def __init__(self, action: str, data: Dict[str, Any] = None, request_id: str = None):
        super().__init__(
            command_type=CommandType.ASR,  # Whisper is part of ASR system
            action=action,
            data=data or {},
            request_id=request_id
        )
    
    @classmethod
    def create_transcribe_command(cls, 
                                audio_data: bytes,
                                language: str = "en",
                                request_id: str = None) -> 'WhisperCommand':
        """Create a transcription command
        
        Args:
            audio_data: Raw audio bytes to transcribe
            language: Language code (default: "en")
            request_id: Optional request ID
        """
        return cls(
            action="transcribe",
            data={
                "audio": audio_data,
                "language": language
            },
            request_id=request_id or f"whisper_{int(time.time())}"
        )

def parse_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and standardize command response"""
    if not isinstance(response, dict):
        return {"status": "error", "message": "Invalid response format"}

    status = "ok" if response.get("success", False) else "error"
    return {
        "status": status,
        "message": response.get("message", ""),
        "data": response.get("data", {}),
        "error": response.get("error", None)
    }

# Factory for creating commands
class CommandFactory:
    @staticmethod
    def create_command(command_type: CommandType, **kwargs) -> BaseCommand:
        command_map = {
            CommandType.LLM: LLMCommand,
            CommandType.SYSTEM: SystemCommand,
            CommandType.AUDIO: AudioCommand
        }
        
        command_class = command_map.get(command_type)
        if not command_class:
            raise ValueError(f"Unknown command type: {command_type}")
            
        return command_class(**kwargs)

    @staticmethod
    def create_ping_command(request_id=None):
        """
        Create a ping command exactly according to API:
        {
            "request_id": "001",
            "work_id": "sys",
            "action": "ping"
        }
        """
        if not request_id:
            request_id = f"{int(time.time())}"
            
        return {
            "request_id": request_id,
            "work_id": "sys",
            "action": "ping"
        }
    
    @staticmethod
    def create_list_models_command(request_id=None):
        """
        Create a list models (lsmode) command exactly according to API:
        {
            "request_id": "001",
            "work_id": "sys",
            "action": "lsmode"
        }
        """
        if not request_id:
            request_id = f"{int(time.time())}"
            
        return {
            "request_id": request_id,
            "work_id": "sys",
            "action": "lsmode"
        }
    
    @staticmethod
    def create_hardware_info_command(request_id=None):
        """
        Create a hardware info command exactly according to API:
        {
            "request_id": "001",
            "work_id": "sys",
            "action": "hwinfo"
        }
        """
        if not request_id:
            request_id = f"{int(time.time())}"
            
        return {
            "request_id": request_id,
            "work_id": "sys",
            "action": "hwinfo"
        }
    
    @staticmethod
    def create_reset_command(request_id=None):
        """
        Create a reset command exactly according to API:
        {
            "request_id": "001",
            "work_id": "sys",
            "action": "reset"
        }
        """
        if not request_id:
            request_id = f"{int(time.time())}"
            
        return {
            "request_id": request_id,
            "work_id": "sys",
            "action": "reset"
        }
    
    @staticmethod
    def create_reboot_command(request_id=None):
        """
        Create a reboot command exactly according to API:
        {
            "request_id": "001",
            "work_id": "sys",
            "action": "reboot"
        }
        """
        if not request_id:
            request_id = f"{int(time.time())}"
            
        return {
            "request_id": request_id,
            "work_id": "sys",
            "action": "reboot"
        }
    
    @staticmethod
    def create_llm_setup_command(model_name, persona=None, request_id=None):
        """
        Create an LLM setup command exactly according to API:
        {
            "request_id": "4",
            "work_id": "llm",
            "action": "setup",
            "object": "llm.setup",
            "data": {
                "model": "qwen2.5-0.5b",
                "response_format": "llm.utf-8",
                "input": "llm.utf-8",
                "enoutput": true,
                "enkws": false,
                "max_token_len": 127,
                "prompt": "..."
            }
        }
        """
        if not request_id:
            request_id = f"{int(time.time())}"
            
        return {
            "request_id": request_id,
            "work_id": "llm",
            "action": "setup",
            "object": "llm.setup",
            "data": {
                "model": model_name,
                "response_format": "llm.utf-8",
                "input": "llm.utf-8",
                "enoutput": True,
                "enkws": False,
                "max_token_len": 127,
                "prompt": persona or ""
            }
        }
    
    @staticmethod
    def create_llm_inference_command(prompt, request_id=None, stream=False):
        """
        Create an LLM inference command exactly according to API:
        
        For non-streaming:
        {
            "request_id": "4",
            "work_id": "llm.1003",
            "action": "inference",
            "object": "llm.utf-8",
            "data": "What's ur name?"
        }
        
        For streaming:
        {
            "request_id": "4",
            "work_id": "llm.1003",
            "action": "inference",
            "object": "llm.utf-8.stream",
            "data": {
                "delta": "What's ur name?",
                "index": 0,
                "finish": true
            }
        }
        """
        if not request_id:
            request_id = f"{int(time.time())}"
            
        if stream:
            return {
                "request_id": request_id,
                "work_id": "llm.1003",
                "action": "inference",
                "object": "llm.utf-8.stream",
                "data": {
                    "delta": prompt,
                    "index": 0,
                    "finish": True
                }
            }
        else:
            return {
                "request_id": request_id,
                "work_id": "llm.1003",
                "action": "inference",
                "object": "llm.utf-8",
                "data": prompt
            }

def generate_request_id(prefix: str = "") -> str:
    """Generate unique request ID"""
    return f"{prefix}_{int(time.time())}"

# System Commands
SYSTEM_COMMANDS = {
    "lsmode": {
        "request_id": "",
        "work_id": "sys",
        "action": "lsmode",
        "object": "sys.lsmode",
        "data": "None"
    },
    "hwinfo": {
        "request_id": "",
        "work_id": "sys",
        "action": "hwinfo",
        "object": "sys.hwinfo",
        "data": "None"
    },
    "reset": {
        "request_id": "",
        "work_id": "sys",
        "action": "reset",
        "object": "None",
        "data": "None"
    },
    "reboot": {
        "request_id": "",
        "work_id": "sys",
        "action": "reboot",
        "object": "None",
        "data": "None"
    },
    "ping": {
        "request_id": "",
        "work_id": "sys",
        "action": "ping",
        "object": "None",
        "data": "None"
    }
}

# Audio Commands
AUDIO_COMMANDS = {
    "setup": {
        "request_id": "",
        "work_id": "sys",
        "action": "setup",
        "object": "audio.setup",
        "data": {
            "capcard": 0,
            "capdevice": 0,
            "capVolume": 0.5,
            "playcard": 0,
            "playdevice": 1,
            "playVolume": 0.5
        }
    },
    "pause": {
        "request_id": "",
        "work_id": "audio",
        "action": "pause",
        "object": "None",
        "data": "None"
    },
    "work": {
        "request_id": "",
        "work_id": "audio",
        "action": "work",
        "object": "None",
        "data": "None"
    },
    "exit": {
        "request_id": "",
        "work_id": "audio",
        "action": "exit",
        "object": "None",
        "data": "None"
    },
    "taskinfo": {
        "request_id": "",
        "work_id": "audio",
        "action": "taskinfo",
        "object": "None",
        "data": "None"
    }
}

# KWS (Keyword Spotting) Commands
KWS_COMMANDS = {
    "setup": {
        "request_id": "",
        "work_id": "kws",
        "action": "setup",
        "object": "kws.setup",
        "data": {
            "model": "sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01",
            "response_format": "kws.bool",
            "input": "sys.pcm",
            "enoutput": True,
            "kws": "HELLO"
        }
    },
    "pause": {
        "request_id": "",
        "work_id": "kws",
        "action": "pause",
        "object": "None",
        "data": "None"
    },
    "work": {
        "request_id": "",
        "work_id": "kws",
        "action": "work",
        "object": "None",
        "data": "None"
    },
    "exit": {
        "request_id": "",
        "work_id": "kws",
        "action": "exit",
        "object": "None",
        "data": "None"
    },
    "taskinfo": {
        "request_id": "",
        "work_id": "kws",
        "action": "taskinfo",
        "object": "None",
        "data": "None"
    }
}

# ASR (Automatic Speech Recognition) Commands
ASR_COMMANDS = {
    "setup": {
        "request_id": "",
        "work_id": "sys",
        "action": "setup",
        "object": "asr.setup",
        "data": {
            "model": "whisper.base",
            "response_format": "asr.utf-8",
            "input": "asr.base64.wav",
            "enoutput": True
        }
    },
    "inference": {
        "request_id": "",
        "work_id": "asr",
        "action": "inference",
        "object": "None",
        "data": {
            "audio": None
        }
    },
    "pause": {
        "request_id": "",
        "work_id": "asr",
        "action": "pause",
        "object": "None",
        "data": "None"
    },
    "work": {
        "request_id": "",
        "work_id": "asr",
        "action": "work",
        "object": "None",
        "data": "None"
    },
    "exit": {
        "request_id": "",
        "work_id": "asr",
        "action": "exit",
        "object": "None",
        "data": "None"
    },
    "taskinfo": {
        "request_id": "",
        "work_id": "asr",
        "action": "taskinfo",
        "object": "None",
        "data": "None"
    }
}

# LLM Commands
LLM_COMMANDS = {
    "setup": {
        "request_id": "",
        "work_id": "sys",
        "action": "setup",
        "object": "llm.setup",
        "data": {
            "model": None,
            "response_format": "llm.utf-8",
            "input": "llm.utf-8",
            "enoutput": True,
            "enkws": False,
            "max_token_len": 127,
            "prompt": None
        }
    },
    "inference": {
        "request_id": "",
        "work_id": "llm",
        "action": "inference",
        "object": "None",
        "data": {
            "delta": None,
            "index": 0,
            "finish": True
        }
    },
    "pause": {
        "request_id": "",
        "work_id": "llm",
        "action": "pause",
        "object": "None",
        "data": "None"
    },
    "work": {
        "request_id": "",
        "work_id": "llm",
        "action": "work",
        "object": "None",
        "data": "None"
    },
    "exit": {
        "request_id": "",
        "work_id": "llm",
        "action": "exit",
        "object": "None",
        "data": "None"
    },
    "taskinfo": {
        "request_id": "",
        "work_id": "llm",
        "action": "taskinfo",
        "object": "None",
        "data": "None"
    }
}

# TTS Commands
TTS_COMMANDS = {
    "setup": {
        "request_id": "",
        "work_id": "sys",
        "action": "setup",
        "object": "tts.setup",
        "data": {
            "model": "single_speaker_english_fast",
            "response_format": "tts.base64.wav",
            "input": "tts.utf-8.stream",
            "enoutput": True,
            "enkws": True
        }
    },
    "inference": {
        "request_id": "",
        "work_id": "tts",
        "action": "inference",
        "object": "None",
        "data": {
            "text": None
        }
    },
    "pause": {
        "request_id": "",
        "work_id": "tts",
        "action": "pause",
        "object": "None",
        "data": "None"
    },
    "work": {
        "request_id": "",
        "work_id": "tts",
        "action": "work",
        "object": "None",
        "data": "None"
    },
    "exit": {
        "request_id": "",
        "work_id": "tts",
        "action": "exit",
        "object": "None",
        "data": "None"
    },
    "taskinfo": {
        "request_id": "",
        "work_id": "tts",
        "action": "taskinfo",
        "object": "None",
        "data": "None"
    }
}

# Error codes from API specification
ERROR_CODES = {
    0: "Operation Successful!",
    -1: "Communication channel receive state machine reset warning!",
    -2: "JSON parsing error",
    -3: "sys action match error",
    -4: "Inference data push error",
    -5: "Model loading failed",
    -6: "Unit does not exist",
    -7: "Unknown operation",
    -8: "Unit resource allocation failed",
    -9: "Unit call failed",
    -10: "Model initialization failed",
    -11: "Model run error",
    -12: "Module not initialized",
    -13: "Module is already working",
    -14: "Module is not working",
    -19: "Unit resource release failed"
}

# Mapping from CommandType enum to unit_type string for create_command
COMMAND_TYPE_MAP = {
    CommandType.SYSTEM: "sys",
    CommandType.LLM: "llm",
    CommandType.AUDIO: "audio"
}

# Special case mappings for specific operations
SPECIAL_OPERATION_MAP = {
    "asr": "asr",         # ASR has its own module
    "tts": "tts",         # TTS has its own module
    "whisper": "asr",     # Whisper uses ASR module
    "kws": "kws"          # KWS has its own module
}

def command_type_to_unit_type(command_type: CommandType, operation: str = None) -> str:
    """Convert CommandType enum to unit_type string for create_command
    
    Args:
        command_type: The CommandType enum value
        operation: Optional operation name for special case handling
        
    Returns:
        str: The unit_type string expected by create_command
    """
    # First check if it's a special case operation
    if operation and operation in SPECIAL_OPERATION_MAP:
        return SPECIAL_OPERATION_MAP[operation]
    
    # Otherwise use the standard mapping
    return COMMAND_TYPE_MAP.get(command_type, "sys")

def create_command(unit_type, command_name, data=None):
    """
    Create a command dict with the specified unit type and command name.
    
    This function centralizes command creation to ensure proper API formatting.
    
    Args:
        unit_type: The unit type (can be CommandType enum or string)
        command_name: The command name
        data: Optional data for the command
        
    Returns:
        dict: Command dictionary
    """
    # Convert CommandType enum to string if needed
    if isinstance(unit_type, CommandType):
        unit_type = unit_type.value
    
    # Handle special system commands with exact API formats
    if unit_type == "sys":
        # Use CommandFactory for standard system commands
        if command_name == "ping":
            return CommandFactory.create_ping_command()
        elif command_name == "lsmode":
            return CommandFactory.create_list_models_command()
        elif command_name == "hwinfo":
            return CommandFactory.create_hardware_info_command()
        elif command_name == "reset":
            return CommandFactory.create_reset_command()
        elif command_name == "reboot":
            return CommandFactory.create_reboot_command()
    
    # Handle special LLM commands
    elif unit_type == "llm" and command_name == "setup" and isinstance(data, dict):
        # Use CommandFactory for LLM setup with model and persona
        model_name = data.get("model", "qwen2.5-0.5b")
        persona = data.get("prompt", "")
        return CommandFactory.create_llm_setup_command(model_name, persona)
    
    elif unit_type == "llm" and command_name == "inference" and data:
        # Handle LLM inference
        stream = data.get("stream", False)
        prompt = data.get("prompt", data.get("delta", ""))
        if isinstance(data, str):
            prompt = data
        return CommandFactory.create_llm_inference_command(prompt, stream=stream)
    
    # Generate request ID
    request_id = generate_request_id()
    
    # Create standard command structure
    command = {
        "request_id": request_id,
        "work_id": unit_type,
        "action": command_name
    }
    
    # Add data if provided
    if data:
        # For LLM inference in standard format
        if unit_type == "llm" and command_name == "inference":
            if isinstance(data, str):
                command["data"] = data
            elif isinstance(data, dict):
                command["data"] = data
        else:
            command["data"] = data
    
    return command

def parse_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Parse API response into standardized format"""
    if not response:
        return {"status": "error", "message": "Empty response"}
        
    if "error" in response:
        error_code = response["error"].get("code", -1)
        error_msg = ERROR_CODES.get(error_code, "Unknown error")
        return {
            "status": "error",
            "code": error_code,
            "message": error_msg,
            "data": response.get("data")
        }
        
    return {
        "status": "ok",
        "data": response.get("data", {}),
        "message": response.get("message", "Success")
    }

__all__ = [
    'BaseCommand',
    'CommandType',
    'LLMCommand',
    'SystemCommand',
    'AudioCommand',
    'create_command',
    'parse_response'
] 