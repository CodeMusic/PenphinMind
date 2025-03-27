"""
Neurological Function:
    Synaptic Pathways System:
    - Neural communication
    - Signal transmission
    - Command routing
    - Response handling
    - Error management
    - State tracking
    - Connection management

Project Function:
    Handles neural communication:
    - Command transmission
    - Response processing
    - Error handling
    - State management
"""

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
from typing import Optional, Dict, Any, List, Union, Callable, Type
from enum import Enum
import subprocess

# Third-party imports
import serial
import serial.tools.list_ports

# Local imports
from Mind.CorpusCallosum.neural_commands import (
    BaseCommand, CommandType, CommandFactory, CommandSerializer,
    TTSCommand, ASRCommand, LLMCommand, SystemCommand, WhisperCommand, VADCommand
)
from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

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
    _managers: Dict[str, Any] = {}
    _initialized = False
    _test_mode = False  # Only for hardware testing, not simulation
    _audio_cache_dir = Path("cache/audio")
    _command_handlers: Dict[CommandType, Callable] = {}
    _integration_areas: Dict[str, Any] = {}
    welcome_message = ""

    def __init__(self):
        """Initialize the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways.__init__")
        self._initialized = False
        self._processing = False
        self.current_state = {
            "connection": None,
            "status": "idle",
            "error": None
        }
        
    @classmethod
    def register_integration_area(cls, area_type: str, area_instance: Any) -> None:
        """Register an integration area for neural processing"""
        cls._integration_areas[area_type] = area_instance
        logger.info(f"Registered integration area: {area_type}")

    @classmethod
    def get_integration_area(cls, area_type: str) -> Any:
        """Get a registered integration area"""
        return cls._integration_areas.get(area_type)

    @classmethod
    def set_test_mode(cls, enabled: bool = True) -> None:
        """Set hardware test mode status"""
        cls._test_mode = enabled
        logger.info(f"Neural processor test mode {'enabled' if enabled else 'disabled'}")

    # Core initialization and setup
    @classmethod
    async def initialize(cls, test_mode: bool = False) -> None:
        """Initialize the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways.initialize", test_mode=test_mode)
        try:
            if test_mode:
                journaling_manager.recordDebug("Initializing in test mode")
                # Initialize test mode components
            else:
                journaling_manager.recordDebug("Initializing in production mode")
                # Initialize production components
                
            journaling_manager.recordInfo("Synaptic pathways initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize synaptic pathways: {e}")
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
    def _is_adb_available(cls) -> bool:
        """Check if an ADB device is connected."""
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            devices = result.stdout.strip().split("\n")[1:]  # Ignore header
            return any(device.strip() and "device" in device for device in devices)
        except FileNotFoundError:
            return False  # ADB not installed

    @classmethod
    def _is_serial_available(cls) -> bool:
        """Check if the Serial device is connected."""
        return cls._serial_connection is not None and cls._serial_connection.is_open

    @classmethod
    async def _setup_ax630e(cls) -> bool:
        """Set up connection to neural processor"""
        try:
            print("\n=== Neural Processor Detection ===")
            print("Scanning for AX630...")
            
            # Check for ADB device first
            if cls._is_adb_available():
                print("\n✓ AX630 detected in ADB mode")
                print("=" * 50)
                return True
                
            # If not in ADB mode, try serial
            ports = serial.tools.list_ports.comports()
            ax630_port = None
            
            print("\nAvailable ports:")
            for port in ports:
                print(f"Device: {port.device}")
                print(f"Hardware ID: {port.hwid}")
                print(f"Description: {port.description}")
                print("-" * 50)
            
            for port in ports:
                # On macOS, check for any USB serial device
                if platform.system() == "Darwin":
                    if "usbserial" in port.device.lower() or "tty.usbserial" in port.device.lower():
                        ax630_port = port.device
                        print(f"\n✓ USB Serial device detected!")
                        print("=" * 50)
                        print(f"Port: {port.device}")
                        print(f"Hardware ID: {port.hwid}")
                        print(f"Description: {port.description}")
                        print("=" * 50)
                        break
                else:
                    # On Linux, look for AX630 identifier
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
                print("\n❌ No USB Serial device found")
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
            
            # Send initialization command directly
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
                
        except Exception as e:
            logger.error(f"Error setting up AX630: {e}")
            return False
            
    @classmethod
    async def send_command(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command through the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways.send_command", command=command)
        try:
            # Validate command
            cls._validate_command(command)
            
            # Process command
            response = await cls._process_command(command)
            journaling_manager.recordDebug(f"Command processed: {response}")
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error sending command: {e}")
            raise CommandTransmissionError(f"Failed to send command: {e}")
            
    @classmethod
    async def send_system_command(cls, command_type: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a system command through the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways.send_system_command", command_type=command_type, data=data)
        try:
            # Create system command
            command = SystemCommand(
                command_type=CommandType.SYS,
                action=command_type,
                parameters=data or {}
            )
            
            # Send command
            response = await cls.send_command(command.to_dict())
            journaling_manager.recordDebug(f"System command processed: {response}")
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error sending system command: {e}")
            raise CommandTransmissionError(f"Failed to send system command: {e}")
            
    @classmethod
    def _validate_command(cls, command: Dict[str, Any]) -> None:
        """Validate a command before sending"""
        journaling_manager.recordScope("SynapticPathways._validate_command", command=command)
        try:
            required_fields = ["command_type", "action"]
            for field in required_fields:
                if field not in command:
                    journaling_manager.recordError(f"Missing required field: {field}")
                    raise ValueError(f"Missing required field: {field}")
                    
            journaling_manager.recordDebug("Command validated successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Error validating command: {e}")
            raise
            
    @classmethod
    async def _process_command(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process a command through the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways._process_command", command=command)
        try:
            # TODO: Implement actual command processing
            # For now, return a mock response
            response = {
                "status": "ok",
                "message": f"Processed command: {command['action']}",
                "data": command.get("parameters", {})
            }
            
            journaling_manager.recordDebug(f"Command processed: {response}")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing command: {e}")
            raise
            
    @classmethod
    async def send_llm(cls, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> Dict[str, Any]:
        """Send an LLM command"""
        try:
            command = LLMCommand(
                command_type=CommandType.LLM,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return await cls.send_command(command.to_dict())
        except Exception as e:
            logger.error(f"Error sending LLM command: {e}")
            raise
            
    @classmethod
    async def send_tts(cls, text: str, voice_id: str = "default", speed: float = 1.0, pitch: float = 1.0) -> Dict[str, Any]:
        """Send a TTS command"""
        try:
            command = TTSCommand(
                command_type=CommandType.TTS,
                text=text,
                voice_id=voice_id,
                speed=speed,
                pitch=pitch
            )
            return await cls.send_command(command.to_dict())
        except Exception as e:
            logger.error(f"Error sending TTS command: {e}")
            raise
            
    @classmethod
    async def send_asr(cls, audio_data: bytes, language: str = "en", model_type: str = "base") -> Dict[str, Any]:
        """Send an ASR command"""
        try:
            command = ASRCommand(
                command_type=CommandType.ASR,
                input_audio=audio_data,
                language=language,
                model_type=model_type
            )
            return await cls.send_command(command.to_dict())
        except Exception as e:
            logger.error(f"Error sending ASR command: {e}")
            raise
            
    @classmethod
    async def send_vad(cls, audio_chunk: bytes, threshold: float = 0.5, frame_duration: int = 30) -> Dict[str, Any]:
        """Send a VAD command"""
        try:
            command = VADCommand(
                command_type=CommandType.VAD,
                audio_chunk=audio_chunk,
                threshold=threshold,
                frame_duration=frame_duration
            )
            return await cls.send_command(command.to_dict())
        except Exception as e:
            logger.error(f"Error sending VAD command: {e}")
            raise
            
    @classmethod
    async def send_whisper(cls, audio_data: bytes, language: str = "en", model_type: str = "base") -> Dict[str, Any]:
        """Send a Whisper command"""
        try:
            command = WhisperCommand(
                command_type=CommandType.WHISPER,
                audio_data=audio_data,
                language=language,
                model_type=model_type
            )
            return await cls.send_command(command.to_dict())
        except Exception as e:
            logger.error(f"Error sending Whisper command: {e}")
            raise
            
    @classmethod
    async def transmit_json(cls, command: BaseCommand) -> Dict[str, Any]:
        """Transmit a command as JSON"""
        try:
            if not cls._initialized:
                raise CommandTransmissionError("Neural pathways not initialized")
                
            # Always try to use the real AX630C hardware
            if not cls._serial_connection:
                if not await cls._setup_ax630e():
                    raise SerialConnectionError("Failed to connect to AX630C")
            
            # Send command directly to hardware
            command_data = command.to_dict()
            json_data = json.dumps(command_data) + "\n"
            cls._serial_connection.write(json_data.encode())
            response = cls._serial_connection.readline().decode().strip()
            
            if not response:
                raise CommandTransmissionError("No response from neural processor")
                
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error transmitting JSON: {e}")
            raise
            
    @classmethod
    async def _handle_test_command(cls, command: BaseCommand) -> Dict[str, Any]:
        """Handle commands in test mode"""
        try:
            if isinstance(command, LLMCommand):
                # Always try to use the real AX630C hardware
                if not cls._serial_connection:
                    if not await cls._setup_ax630e():
                        raise SerialConnectionError("Failed to connect to AX630C")
                
                # Send command directly to hardware
                command_data = command.to_dict()
                json_data = json.dumps(command_data) + "\n"
                cls._serial_connection.write(json_data.encode())
                response = cls._serial_connection.readline().decode().strip()
                
                if not response:
                    raise CommandTransmissionError("No response from neural processor")
                    
                return json.loads(response)
                
            elif isinstance(command, TTSCommand):
                return {"status": "ok", "audio": b"test_audio_data"}
            elif isinstance(command, ASRCommand):
                return {"status": "ok", "text": "Test transcribed text"}
            elif isinstance(command, VADCommand):
                return {"status": "ok", "vad_active": True}
            elif isinstance(command, WhisperCommand):
                return {"status": "ok", "text": "Test Whisper transcription"}
            else:
                return {"status": "ok", "message": "Test command processed"}
                
        except Exception as e:
            logger.error(f"Error handling test command: {e}")
            return {"status": "error", "message": str(e)}

    # Command handler registration
    @classmethod
    def register_command_handler(cls, command_type: CommandType, handler: Callable) -> None:
        """Register a handler for a specific command type"""
        cls._command_handlers[command_type] = handler
        logger.info(f"Registered handler for {command_type}")

    # Cleanup
    @classmethod
    async def cleanup(cls) -> None:
        """Clean up the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways.cleanup")
        try:
            # Clean up resources
            if cls._serial_connection and cls._serial_connection.is_open:
                cls._serial_connection.close()
                cls._serial_connection = None
            cls._initialized = False
            cls._test_mode = False
            journaling_manager.recordInfo("Synaptic pathways cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up synaptic pathways: {e}")
            raise

    @classmethod
    async def _call_llm_api(cls, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> Dict[str, Any]:
        """
        Call the local LLM API
        
        Args:
            prompt: Text to process
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Dict[str, Any]: Processed response
        """
        try:
            # Create LLM command
            command = LLMCommand(
                command_type=CommandType.LLM,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Send command directly to hardware
            if not cls._serial_connection:
                if not await cls._setup_ax630e():
                    raise SerialConnectionError("Failed to connect to AX630C")
            
            command_data = command.to_dict()
            json_data = json.dumps(command_data) + "\n"
            cls._serial_connection.write(json_data.encode())
            response = cls._serial_connection.readline().decode().strip()
            
            if not response:
                raise CommandTransmissionError("No response from neural processor")
                
            response_data = json.loads(response)
            return {
                "status": "ok",
                "response": response_data.get("text", "")
            }
            
        except Exception as e:
            logger.error(f"Error in LLM processing: {e}")
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