import json
import serial
import serial.tools.list_ports
import time
import os
import stat
import pwd
import grp
from typing import Optional, Dict, Any, List, Union, Callable
from pathlib import Path
import subprocess
from enum import Enum
from dataclasses import dataclass
from .neural_commands import (
    BaseCommand, CommandType, CommandFactory, CommandSerializer,
    TTSCommand, ASRCommand, VADCommand, LLMCommand, VLMCommand,
    KWSCommand, SystemCommand, AudioCommand, CameraCommand,
    YOLOCommand, WhisperCommand, MeloTTSCommand
)
from config import CONFIG
import asyncio
import logging

logger = logging.getLogger(__name__)

class SerialConnectionError(Exception):
    """Error establishing serial connection"""
    pass

class CommandTransmissionError(Exception):
    """Error transmitting command"""
    pass

class SynapticPathways:
    """
    Manages JSON communication pathways between cortices with SSH-aware permissions.
    
    This class handles serial communication with proper error handling and retry logic,
    ensuring robust communication between different system components.
    """
    _serial_connection: Optional[serial.Serial] = None
    _managers: Dict[str, Any] = {}
    _command_handlers: Dict[CommandType, Callable] = {}
    _initialized = False

    @classmethod
    def register_command_handler(cls, command_type: CommandType, handler: Callable) -> None:
        """Register a handler for a specific command type"""
        cls._command_handlers[command_type] = handler

    @classmethod
    async def _check_device_permissions(cls, device_path: str) -> bool:
        """Check if we have permission to access the device"""
        try:
            if not os.path.exists(device_path):
                return False
                
            # Get device stats
            stat = os.stat(device_path)
            
            # Get owner and group info
            owner = pwd.getpwuid(stat.st_uid).pw_name
            group = grp.getgrgid(stat.st_gid).gr_name
            
            # Get current user info
            current_user = pwd.getpwuid(os.getuid()).pw_name
            user_groups = [g.gr_name for g in grp.getgrall() if current_user in g.gr_mem]
            
            # Get permissions in octal format
            perms = oct(stat.st_mode)[-3:]
            
            # Print detailed device info for debugging
            print(f"Device {device_path}:")
            print(f"  Owner: {owner}")
            print(f"  Group: {group}")
            print(f"  Current user: {current_user}")
            print(f"  User groups: {user_groups}")
            print(f"  Permissions: {perms}")
            
            # Check if user has access
            return (
                os.access(device_path, os.R_OK | os.W_OK) and
                (current_user == owner or
                 group in user_groups or
                 'dialout' in user_groups)
            )
            
        except Exception as e:
            logger.error(f"Error checking device permissions: {e}")
            return False

    @classmethod
    async def _find_device(cls) -> str:
        """
        Find the correct USB device by checking available ports.
        
        Returns:
            str: Path to the found device or default port
        """
        try:
            # Use asyncio.to_thread for blocking serial operations
            ports = await asyncio.to_thread(list, serial.tools.list_ports.comports())
            
            # Log all found ports for debugging
            logger.info("Found serial ports:")
            for port in ports:
                logger.info(f"  Port: {port.device}")
                logger.info(f"    Description: {port.description}")
                logger.info(f"    Hardware ID: {port.hwid}")
                logger.info(f"    USB Info: {port.usb_info()}")
                logger.info(f"    Interface: {port.interface}")
                
            # First try ports that match our expected hardware
            for port in ports:
                if ("USB" in port.device and 
                    await cls._check_device_permissions(port.device)):
                    logger.info(f"Found matching USB device: {port.device}")
                    return port.device
                    
            # Fall back to checking /dev/ttyUSB* directly
            proc = await asyncio.create_subprocess_exec(
                'ls', '/dev/ttyUSB*',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if stdout:
                devices = stdout.decode().strip().split('\n')
                logger.info(f"Found USB devices: {devices}")
                for device in devices:
                    if await cls._check_device_permissions(device):
                        return device
                    
        except Exception as e:
            logger.error(f"Error finding USB devices: {e}")
            
        return CONFIG.serial_default_port

    @classmethod
    async def _initialize_connection(cls) -> None:
        """Initialize serial connection with proper handshake"""
        if cls._serial_connection and cls._serial_connection.is_open:
            logger.debug("Connection already initialized")
            return
            
        # List of baud rates to try
        baud_rates = [115200, 9600, 57600, 38400]
        
        for attempt in range(CONFIG.serial_max_retries):
            try:
                # Find available device
                port = await cls._find_device()
                if not port:
                    logger.warning("No suitable USB device found")
                    await asyncio.sleep(CONFIG.serial_retry_delay)
                    continue
                    
                # Check device permissions
                if not await cls._check_device_permissions(port):
                    logger.warning(f"Insufficient permissions for {port}")
                    await asyncio.sleep(CONFIG.serial_retry_delay)
                    continue
                    
                # Try each baud rate
                for baud_rate in baud_rates:
                    try:
                        logger.info(f"Attempting connection to {port} at {baud_rate} baud")
                        
                        # Close any existing connection
                        if cls._serial_connection:
                            try:
                                cls._serial_connection.close()
                            except Exception as e:
                                logger.error(f"Error closing connection: {e}")
                        
                        # Wait for device to settle
                        await asyncio.sleep(1.0)
                        
                        # Open new connection with specific settings
                        cls._serial_connection = serial.Serial(
                            port=port,
                            baudrate=baud_rate,
                            timeout=CONFIG.serial_timeout,
                            write_timeout=CONFIG.serial_timeout,
                            bytesize=serial.EIGHTBITS,
                            parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE,
                            xonxoff=False,    # Disable software flow control
                            rtscts=False,     # Disable hardware (RTS/CTS) flow control
                            dsrdtr=False      # Disable hardware (DSR/DTR) flow control
                        )
                        
                        # Clear any pending data
                        cls._serial_connection.reset_input_buffer()
                        cls._serial_connection.reset_output_buffer()
                        
                        # Wait for device to be ready
                        await asyncio.sleep(2.0)
                        
                        logger.info("Testing connection...")
                        
                        # Send handshake command
                        handshake_cmd = {
                            "type": "handshake",
                            "version": "1.0",
                            "baud_rate": baud_rate
                        }
                        
                        # Convert to bytes and add newline
                        cmd_bytes = (json.dumps(handshake_cmd) + "\n").encode('utf-8')
                        
                        # Log the exact bytes being sent (for debugging)
                        logger.debug(f"Sending handshake bytes: {cmd_bytes!r}")
                        
                        # Write command with a small delay between bytes
                        for b in cmd_bytes:
                            cls._serial_connection.write(bytes([b]))
                            cls._serial_connection.flush()
                            await asyncio.sleep(0.001)  # 1ms delay between bytes
                        
                        # Wait for response
                        logger.debug("Waiting for handshake response...")
                        response = await asyncio.to_thread(cls._serial_connection.readline)
                        
                        if not response:
                            logger.warning(f"No response at {baud_rate} baud")
                            continue
                            
                        # Log raw response for debugging
                        logger.debug(f"Raw response: {response!r}")
                        
                        try:
                            response_data = json.loads(response.decode('utf-8'))
                            if response_data.get("status") == "ok":
                                logger.info(f"Successfully connected to {port} at {baud_rate} baud")
                                return
                            else:
                                logger.warning(f"Invalid handshake response: {response_data}")
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid handshake response format: {e}")
                            continue
                            
                    except (serial.SerialException, CommandTransmissionError) as e:
                        logger.warning(f"Failed at {baud_rate} baud: {e}")
                        continue
                        
                # If we get here, none of the baud rates worked
                logger.warning(f"No working baud rate found for {port}")
                
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                
            # Wait before next attempt
            await asyncio.sleep(CONFIG.serial_retry_delay)
            
        raise SerialConnectionError("Failed to establish connection after all attempts")

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the pathways system"""
        if cls._initialized:
            return
            
        try:
            await cls._initialize_connection()
            cls._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise

    @classmethod
    async def transmit_command(cls, command: BaseCommand) -> Dict[str, Any]:
        """Transmit a command through the neural pathway"""
        if not cls._initialized:
            await cls.initialize()
            
        try:
            # Serialize command to JSON
            command_json = CommandSerializer.serialize(command)
            
            # Add newline to mark end of command
            command_bytes = (command_json + "\n").encode('utf-8')
            
            logger.debug(f"Sending command: {command_json}")
            
            # Write command
            cls._serial_connection.write(command_bytes)
            cls._serial_connection.flush()
            
            # Read response
            response = await asyncio.to_thread(cls._serial_connection.readline)
            if not response:
                raise CommandTransmissionError("No response received")
                
            try:
                return json.loads(response.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid response format: {e}")
                raise CommandTransmissionError("Invalid response format")
                
        except Exception as e:
            logger.error(f"Command transmission error: {e}")
            raise CommandTransmissionError(str(e))

    @classmethod
    def register_manager(cls, manager_type: str, manager_instance: Any) -> None:
        """Register a manager instance for cross-cortex communication"""
        cls._managers[manager_type] = manager_instance

    @classmethod
    async def close_connections(cls) -> None:
        """Close all open connections"""
        if cls._serial_connection:
            try:
                # Send close command
                close_cmd = {
                    "type": "close",
                    "timestamp": time.time()
                }
                cmd_bytes = (json.dumps(close_cmd) + "\n").encode('utf-8')
                cls._serial_connection.write(cmd_bytes)
                cls._serial_connection.flush()
                
                # Wait briefly for any response
                await asyncio.sleep(0.1)
                
                # Close the connection
                cls._serial_connection.close()
                cls._serial_connection = None
                cls._initialized = False
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
                raise

    # Convenience methods for common commands
    @classmethod
    async def send_tts(cls, text: str, voice_id: str = "default", speed: float = 1.0, pitch: float = 1.0) -> Dict[str, Any]:
        """Send Text-to-Speech command"""
        command = TTSCommand(
            command_type=CommandType.TTS,
            text=text,
            voice_id=voice_id,
            speed=speed,
            pitch=pitch
        )
        return await cls.transmit_command(command)

    @classmethod
    async def send_asr(cls, audio_data: bytes, language: str = "en", model_type: str = "base") -> Dict[str, Any]:
        """Send Automatic Speech Recognition command"""
        command = ASRCommand(
            command_type=CommandType.ASR,
            input_audio=audio_data,
            language=language,
            model_type=model_type
        )
        return await cls.transmit_command(command)

    @classmethod
    async def send_llm(cls, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> Dict[str, Any]:
        """Send Large Language Model command"""
        command = LLMCommand(
            command_type=CommandType.LLM,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return await cls.transmit_command(command) 