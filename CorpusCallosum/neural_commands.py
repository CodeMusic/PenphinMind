from enum import Enum
from typing import Dict, Any

class NeuralCommands:
    """
    Defines standard JSON commands for neural pathway communication
    """
    
    class CommandTypes(Enum):
        START_RECORDING = "start_recording"
        STOP_RECORDING = "stop_recording"
        SPEAK_TEXT = "speak_text"
        GET_STATUS = "get_status"
        CONFIGURE = "configure"

    @staticmethod
    def create_command(command_type: CommandTypes, **kwargs) -> Dict[str, Any]:
        """
        Creates properly formatted JSON command
        """
        base_command = {
            "cmd": command_type.value
        }
        
        # Add any additional parameters
        base_command.update(kwargs)
        return base_command

    # Pre-defined command templates
    STT_START = {
        "cmd": CommandTypes.START_RECORDING.value,
        "mode": "stt"
    }
    
    STT_STOP = {
        "cmd": CommandTypes.STOP_RECORDING.value,
        "mode": "stt"
    }
    
    @staticmethod
    def tts_command(text: str) -> Dict[str, Any]:
        return {
            "cmd": NeuralCommands.CommandTypes.SPEAK_TEXT.value,
            "text": text
        } 