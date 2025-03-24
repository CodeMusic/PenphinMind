# Standard library imports
import asyncio
import json
import logging
import os
import platform
import pwd
import grp
import stat
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Callable

# Third-party imports
import serial
import serial.tools.list_ports
import openai

# Local imports
from .neural_commands import (
    BaseCommand, CommandType, CommandFactory, CommandSerializer,
    TTSCommand, ASRCommand, LLMCommand, SystemCommand, WhisperCommand, VADCommand
)
from config import CONFIG

logger = logging.getLogger(__name__)

class SerialConnectionError(Exception):
    """Raised when serial connection fails"""
    pass

class CommandTransmissionError(Exception):
    """Raised when command transmission fails"""
    pass

class SynapticPathways:
    """Manages neural communication pathways with hardware abstraction"""
    
    # Class variables
    _serial_connection: Optional[serial.Serial] = None
    _managers = {}
    _initialized = False
    _llm_test_mode = False
    _audio_cache_dir = Path("cache/audio")
    _command_handlers = {}
    welcome_message = ""

    # Core initialization and setup
    @classmethod
    async def initialize(cls) -> None:
        """Initialize the pathways system"""
        if cls._initialized:
            return
            
        try:
            # Detect platform and set mode
            cls._detect_platform()
            
            # Only try hardware setup on Raspberry Pi
            if not cls._llm_test_mode and await cls._setup_ax620e():
                cls._initialized = True
                return
                
            if cls._llm_test_mode:
                cls._initialized = True
                return
                
            raise SerialConnectionError("No compatible device found")
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise

    @classmethod
    def _detect_platform(cls) -> None:
        """Detect platform and set test mode accordingly"""
        if platform.system() != "Linux" or not os.path.exists("/sys/firmware/devicetree/base/model"):
            cls._llm_test_mode = True
            cls.welcome_message = "Welcome to the bicameral mind testing harness."
            logger.info("Non-Raspberry Pi platform detected, enabling test mode")
        else:
            # Check audio device permissions
            try:
                audio_group = grp.getgrnam('audio')
                current_user = pwd.getpwuid(os.getuid()).pw_name
                if current_user not in audio_group.gr_mem:
                    logger.error("User not in 'audio' group. Please run:")
                    logger.error("sudo usermod -a -G audio $USER")
                    logger.error("Then log out and back in.")
                    cls._llm_test_mode = True
                    return
            except KeyError:
                logger.error("Audio group not found")
                cls._llm_test_mode = True
                return

            cls._llm_test_mode = False
            cls.welcome_message = "Welcome to Penphin OS, the original AI bicameral mind."
            logger.info("Raspberry Pi platform detected, using hardware mode")

    @classmethod
    async def _setup_ax620e(cls) -> bool:
        """Set up direct connection to ax620e device"""
        if cls._llm_test_mode:
            logger.info("Running in LLM test mode")
            return True

        try:
            # Check device existence and permissions
            device_path = CONFIG.serial_default_port
            if not os.path.exists(device_path):
                logger.error(f"Device {device_path} not found")
                return False

            # Get device permissions and ownership
            st = os.stat(device_path)
            current_user = pwd.getpwuid(os.getuid()).pw_name
            device_user = pwd.getpwuid(st.st_uid).pw_name
            device_group = grp.getgrgid(st.st_gid).gr_name

            logger.info(f"Device permissions: {stat.filemode(st.st_mode)}")
            logger.info(f"Device owner: {device_user}:{device_group}")
            logger.info(f"Current user: {current_user}")

            # Check if user is in dialout group
            user_groups = [g.gr_name for g in grp.getgrall() if current_user in g.gr_mem]
            if 'dialout' not in user_groups:
                logger.error("User not in 'dialout' group. Please run:")
                logger.error("sudo usermod -a -G dialout $USER")
                logger.error("Then log out and back in.")
                return False

            # Initialize serial connection
            cls._serial_connection = serial.Serial(
                port=device_path,
                baudrate=CONFIG.serial_baud_rate,
                timeout=CONFIG.serial_timeout
            )

            # Test connection
            cls._serial_connection.reset_input_buffer()
            cls._serial_connection.reset_output_buffer()
            
            logger.info("Connection established successfully")
            return True

        except Exception as e:
            logger.error(f"Error setting up ax620e connection: {e}")
            if cls._serial_connection:
                cls._serial_connection.close()
                cls._serial_connection = None
            return False

    # Primary command handling
    @classmethod
    async def transmit_json(cls, command: Union[Dict[str, Any], BaseCommand]) -> Dict[str, Any]:
        """Transmit JSON commands with test mode awareness"""
        if not cls._initialized:
            await cls.initialize()

        # Convert command object to dict if needed
        if isinstance(command, BaseCommand):
            command = command.to_dict()

        if cls._llm_test_mode:
            return await cls._process_llm_test_command(command)

        # Real hardware communication
        retries = CONFIG.serial_max_retries
        retry_delay = CONFIG.serial_retry_delay
        
        for attempt in range(retries):
            try:
                if not cls._serial_connection or not cls._serial_connection.is_open:
                    await cls._setup_ax620e()

                json_data = json.dumps(command) + "\n"
                cls._serial_connection.write(json_data.encode())
                response = cls._serial_connection.readline().decode().strip()
                
                if not response:
                    raise CommandTransmissionError("No response received")
                    
                return json.loads(response)
                
            except Exception as e:
                logger.error(f"Transmission attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                raise CommandTransmissionError(f"Failed after {retries} attempts: {e}")

    @classmethod
    async def _process_llm_test_command(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process commands in LLM test mode - real LLM, no hardware"""
        cmd_type = command.get("command_type")
        logger.info(f"Processing command in LLM test mode: {cmd_type}")
        
        if cmd_type == CommandType.LLM.value:
            return await cls._call_llm_api(
                prompt=command.get("prompt", ""),
                max_tokens=command.get("max_tokens", 150),
                temperature=command.get("temperature", 0.7)
            )
            
        elif cmd_type == CommandType.TTS.value:
            # Always return test mode message for welcome
            text = command.get("text", "")
            if "Welcome to Penphin OS" in text:
                return {
                    "status": "ok",
                    "text": cls.welcome_message
                }
            return {"status": "ok", "text": text}
            
        elif cmd_type == CommandType.ASR.value:
            return {"status": "ok", "text": ""}
            
        return {
            "status": "ok",
            "command_type": cmd_type,
            "message": "Command acknowledged in LLM test mode"
        }

    # High-level command interfaces
    @classmethod
    async def send_llm(cls, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> Dict[str, Any]:
        """Send Large Language Model command"""
        command = LLMCommand(
            command_type=CommandType.LLM,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return await cls.transmit_json(command)

    @classmethod
    async def send_tts(cls, text: str, voice_id: str = "default", speed: float = 1.0, pitch: float = 1.0) -> Dict[str, Any]:
        """Send Text-to-Speech command"""
        try:
            command = TTSCommand(
                command_type=CommandType.TTS,
                text=text,
                voice_id=voice_id,
                speed=speed,
                pitch=pitch
            )
            return await cls.transmit_json(command)
        except Exception as e:
            logger.error(f"TTS command failed: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def send_asr(cls, audio_data: bytes, language: str = "en", model_type: str = "base") -> Dict[str, Any]:
        """Send Automatic Speech Recognition command"""
        command = ASRCommand(
            command_type=CommandType.ASR,
            input_audio=audio_data,
            language=language,
            model_type=model_type
        )
        return await cls.transmit_json(command)

    # Command handler registration
    @classmethod
    def register_command_handler(cls, command_type: CommandType, handler: Callable) -> None:
        """Register a handler for a specific command type"""
        cls._command_handlers[command_type] = handler
        logger.info(f"Registered handler for {command_type}")

    # Cleanup
    @classmethod
    async def close_connections(cls) -> None:
        """Clean up connections and resources"""
        if cls._serial_connection and cls._serial_connection.is_open:
            cls._serial_connection.close()
            cls._serial_connection = None
        cls._initialized = False
        logger.info("Connections closed")

    @classmethod
    async def _call_llm_api(cls, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Call the LLM API with error handling"""
        try:
            # Use OpenAI API directly in test mode
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are PenphinOS, a bicameral AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                "status": "ok",
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    @classmethod
    async def transmit_command(cls, command: BaseCommand) -> Dict[str, Any]:
        """Transmit a command object directly"""
        try:
            # Serialize command to JSON format
            command_dict = CommandSerializer.serialize(command)
            return await cls.transmit_json(command_dict)
            
        except Exception as e:
            logger.error(f"Command transmission failed: {e}")
            raise

    @classmethod
    async def process_assistant_interaction(cls, audio_data: bytes = None, text_input: str = None) -> Dict[str, Any]:
        """High-level method to process a complete assistant interaction"""
        try:
            # Process audio input if provided
            if audio_data and not text_input:
                asr_response = await cls.send_asr(audio_data)
                text_input = asr_response.get("text", "")
                if not text_input:
                    return {"status": "error", "message": "Failed to transcribe audio"}

            # Process text through LLM
            llm_response = await cls.send_llm(
                prompt=text_input,
                max_tokens=150
            )
            assistant_response = llm_response.get("response", "")

            # Generate audio response if not in test mode
            audio_path = None
            if not cls._llm_test_mode and assistant_response:
                tts_response = await cls.send_tts(assistant_response)
                audio_path = tts_response.get("audio_path")

            return {
                "status": "ok",
                "input_text": text_input,
                "assistant_response": assistant_response,
                "audio_path": audio_path
            }

        except Exception as e:
            logger.error(f"Assistant interaction failed: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def send_system_command(cls, command_type: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send system-level commands"""
        command = SystemCommand(
            command_type=CommandType.SYSTEM,
            system_command=command_type,
            data=data or {}
        )
        return await cls.transmit_json(command)

    @classmethod
    async def send_whisper_command(cls, audio_data: bytes, language: str = "en", task: str = "transcribe") -> Dict[str, Any]:
        """Send Whisper transcription command"""
        command = WhisperCommand(
            command_type=CommandType.WHISPER,
            audio_data=audio_data,
            language=language,
            task=task
        )
        return await cls.transmit_json(command)

    @classmethod
    async def send_vad_command(cls, audio_data: bytes, threshold: float = 0.5) -> Dict[str, Any]:
        """Send Voice Activity Detection command"""
        command = VADCommand(
            command_type=CommandType.VAD,
            audio_data=audio_data,
            threshold=threshold
        )
        return await cls.transmit_json(command)

    @classmethod
    def get_manager(cls, manager_type: str) -> Any:
        """Get a registered manager instance"""
        return cls._managers.get(manager_type)

    @classmethod
    def register_manager(cls, manager_type: str, manager_instance: Any) -> None:
        """Register a manager instance"""
        cls._managers[manager_type] = manager_instance
        logger.info(f"Registered {manager_type} manager") 