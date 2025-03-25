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
    _test_mode = False  # Only for hardware testing, not simulation
    _audio_cache_dir = Path("cache/audio")
    _command_handlers = {}
    welcome_message = ""

    @classmethod
    def set_test_mode(cls, enabled: bool = True) -> None:
        """Set hardware test mode status"""
        cls._test_mode = enabled
        logger.info(f"Neural processor test mode {'enabled' if enabled else 'disabled'}")

    # Core initialization and setup
    @classmethod
    async def initialize(cls, test_mode: bool = False) -> None:
        """Initialize the neural pathways system"""
        if cls._initialized:
            return
            
        try:
            # Set test mode
            cls._test_mode = test_mode
            logger.info(f"Initializing neural pathways in {'test' if test_mode else 'production'} mode")
            
            # Always attempt hardware setup unless in test mode
            if not test_mode:
                if await cls._setup_ax630e():
                    cls._initialized = True
                    return
                raise SerialConnectionError("No compatible neural processor found")
            else:
                # In test mode, just mark as initialized
                cls._initialized = True
                logger.info("Neural pathways initialized in test mode")
                return
                
        except Exception as e:
            logger.error(f"Failed to initialize neural pathways: {e}")
            raise

    @classmethod
    def _detect_platform(cls) -> None:
        """Detect platform and set test mode accordingly"""
        if platform.system() != "Linux" or not os.path.exists("/sys/firmware/devicetree/base/model"):
            cls._test_mode = True
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
                    cls._test_mode = True
                    return
            except KeyError:
                logger.error("Audio group not found")
                cls._test_mode = True
                return

            cls._test_mode = False
            cls.welcome_message = "Welcome to Penphin OS, the original AI bicameral mind."
            logger.info("Raspberry Pi platform detected, using hardware mode")

    @classmethod
    async def _setup_ax630e(cls) -> bool:
        """Set up direct connection to neural processor"""
        try:
            # Look for AX630 device
            ports = serial.tools.list_ports.comports()
            ax630_port = None
            
            print("\n=== Neural Processor Detection ===")
            print("Scanning for AX630...")
            
            for port in ports:
                # On macOS, AX630 typically appears as "usbserial-" or "tty.usbserial-"
                if (("usbserial" in port.device.lower() and "AX630" in port.hwid) or
                    ("AX630" in port.description)):
                    ax630_port = port.device
                    print(f"\n✓ AX630 Neural Processor detected!")
                    print("=" * 50)
                    print(f"Port: {port.device}")
                    print(f"Hardware ID: {port.hwid}")
                    print(f"Description: {port.description}")
                    print("=" * 50)
                    break
            
            if not ax630_port:
                print("\n❌ AX630 Neural Processor not found")
                print("\nTroubleshooting steps:")
                if platform.system() == "Darwin":  # macOS
                    print("1. Check USB connection")
                    print("2. Verify power supply")
                    print("3. Install USB-Serial driver:")
                    print("   brew install --cask silicon-labs-vcp-driver")
                    print("4. Check device permissions:")
                    print("   ls -l /dev/tty.usbserial*")
                    print("5. Fix permissions if needed:")
                    print("   sudo chmod 666 /dev/tty.usbserial*")
                else:  # Linux
                    print("1. Check USB connection")
                    print("2. Verify power supply")
                    print("3. Check device permissions:")
                    print("   sudo usermod -a -G dialout $USER")
                    print("   sudo usermod -a -G tty $USER")
                    print("4. Reload udev rules:")
                    print("   sudo udevadm control --reload-rules")
                    print("   sudo udevadm trigger")
                return False

            # Initialize serial connection
            cls._serial_connection = serial.Serial(
                port=ax630_port,
                baudrate=CONFIG.serial_baud_rate,
                timeout=CONFIG.serial_timeout
            )

            # Test connection
            cls._serial_connection.reset_input_buffer()
            cls._serial_connection.reset_output_buffer()
            
            # Send initialization command
            init_command = {
                "type": "SYSTEM",
                "command": "initialize",
                "data": {
                    "device": "AX630",
                    "mode": "neural_processor"
                }
            }
            
            json_data = json.dumps(init_command) + "\n"
            cls._serial_connection.write(json_data.encode())
            response = cls._serial_connection.readline().decode().strip()
            
            if not response:
                raise CommandTransmissionError("No response from neural processor during initialization")
            
            response_data = json.loads(response)
            if response_data.get("status") == "ok":
                print("\n✓ Neural processor initialized successfully")
                print(f"Firmware version: {response_data.get('version', 'unknown')}")
                print(f"Status: {response_data.get('state', 'unknown')}")
                return True
            else:
                raise CommandTransmissionError(f"Initialization failed: {response_data.get('message', 'unknown error')}")

        except Exception as e:
            logger.error(f"Error setting up neural processor: {e}")
            if cls._serial_connection:
                cls._serial_connection.close()
                cls._serial_connection = None
            return False

    # Primary command handling
    @classmethod
    async def transmit_json(cls, command: Union[Dict[str, Any], BaseCommand]) -> Dict[str, Any]:
        """Transmit commands to neural processor"""
        if not cls._initialized:
            await cls.initialize()

        # Convert command object to dict if needed
        if isinstance(command, BaseCommand):
            command = command.to_dict()

        # In test mode, return mock responses
        if cls._test_mode:
            logger.debug(f"Test mode - Command sent: {json.dumps(command, indent=2)}")
            
            # Mock response based on command type
            if command.get("type") == "LLM":
                mock_response = {
                    "status": "ok",
                    "response": f"Test mode response for prompt: {command.get('prompt', '')}",
                    "tokens_used": 50,
                    "model": "test-model"
                }
            elif command.get("type") == "TTS":
                mock_response = {
                    "status": "ok",
                    "audio_path": "test_audio.wav",
                    "duration": 2.5
                }
            elif command.get("type") == "ASR":
                mock_response = {
                    "status": "ok",
                    "text": "This is a test transcription",
                    "confidence": 0.95
                }
            else:
                mock_response = {
                    "status": "ok",
                    "message": f"Test mode - Command processed: {command.get('type', 'unknown')}"
                }
                
            logger.debug(f"Test mode - Response: {json.dumps(mock_response, indent=2)}")
            return mock_response

        # Production mode - attempt hardware communication
        retries = CONFIG.serial_max_retries
        retry_delay = CONFIG.serial_retry_delay
        
        for attempt in range(retries):
            try:
                if not cls._serial_connection or not cls._serial_connection.is_open:
                    await cls._setup_ax630e()

                json_data = json.dumps(command) + "\n"
                cls._serial_connection.write(json_data.encode())
                response = cls._serial_connection.readline().decode().strip()
                
                if not response:
                    raise CommandTransmissionError("No response from neural processor")
                    
                return json.loads(response)
                
            except Exception as e:
                logger.error(f"Transmission attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                raise CommandTransmissionError(f"Neural processor communication failed after {retries} attempts: {e}")

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
    async def cleanup(cls) -> None:
        """Clean up resources"""
        if cls._serial_connection and cls._serial_connection.is_open:
            cls._serial_connection.close()
            cls._serial_connection = None
        cls._initialized = False
        logger.info("Neural pathways closed")

    @classmethod
    async def _call_llm_api(cls, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Process requests through neural processor"""
        try:
            # Always use hardware communication
            command = {
                "type": "LLM",
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            return await cls.transmit_json(command)
            
        except Exception as e:
            logger.error(f"Neural processor error: {e}")
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
            if not cls._test_mode and assistant_response:
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

    @classmethod
    async def close_connections(cls) -> None:
        """Close all connections and clean up resources"""
        try:
            if cls._serial_connection and cls._serial_connection.is_open:
                cls._serial_connection.close()
                cls._serial_connection = None
            cls._initialized = False
            cls._test_mode = False
            logger.info("Neural pathways connections closed")
        except Exception as e:
            logger.error(f"Error closing neural pathways connections: {e}")
            raise 