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
import re
import traceback

# Third-party imports
import serial
import serial.tools.list_ports

# Local imports
from Mind.CorpusCallosum.neural_commands import (
    BaseCommand, CommandType, CommandFactory, CommandSerializer,
    TTSCommand, ASRCommand, LLMCommand, SystemCommand, WhisperCommand, VADCommand
)
from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel

# Initialize journaling manager
journaling_manager = SystemJournelingManager(CONFIG.log_level)
journaling_manager.recordDebug(f"Initializing SynapticPathways with {CONFIG.log_level} level logging")

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
    _connection_type = None
    _serial_port = None

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
        journaling_manager.recordDebug("SynapticPathways instance initialized")
        journaling_manager.recordDebug(f"Current state: {self.current_state}")
        
    @classmethod
    def register_integration_area(cls, area_type: str, area_instance: Any) -> None:
        """Register an integration area for neural processing"""
        cls._integration_areas[area_type] = area_instance
        journaling_manager.recordInfo(f"Registered integration area: {area_type}")

    @classmethod
    def get_integration_area(cls, area_type: str) -> Any:
        """Get a registered integration area"""
        return cls._integration_areas.get(area_type)

    @classmethod
    def set_test_mode(cls, enabled: bool = True) -> None:
        """Set hardware test mode status"""
        cls._test_mode = enabled
        journaling_manager.recordInfo(f"Neural processor test mode {'enabled' if enabled else 'disabled'}")

    # Core initialization and setup
    @classmethod
    async def initialize(cls, test_mode: bool = False) -> None:
        """Initialize the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways.initialize", test_mode=test_mode)
        try:
            cls._test_mode = test_mode
            if test_mode:
                journaling_manager.recordDebug("Initializing in test mode")
                # Initialize test mode components
            else:
                journaling_manager.recordDebug("Initializing in production mode")
                # Initialize production components
                if not await cls._setup_ax630e():
                    raise SerialConnectionError("Failed to connect to neural processor")
                
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
            journaling_manager.recordInfo("Non-Raspberry Pi platform detected, enabling test mode")
        else:
            # Check audio device permissions
            try:
                audio_group = grp.getgrnam('audio')
                current_user = pwd.getpwuid(os.getuid()).pw_name
                if current_user not in audio_group.gr_mem:
                    journaling_manager.recordError("User not in 'audio' group. Please run:")
                    journaling_manager.recordError("sudo usermod -a -G audio $USER")
                    journaling_manager.recordError("Then log out and back in.")
                    cls._test_mode = True
                    return
            except KeyError:
                journaling_manager.recordError("Audio group not found")
                cls._test_mode = True
                return

            cls._test_mode = False
            cls.welcome_message = "Welcome to Penphin OS, the original AI bicameral mind."
            journaling_manager.recordInfo("Raspberry Pi platform detected, using hardware mode")

    @classmethod
    def _is_adb_available(cls) -> bool:
        """Check if an ADB device is connected."""
        try:
            # First try to start the ADB server
            subprocess.run(["adb", "start-server"], capture_output=True)
            
            # Then check for devices
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            devices = result.stdout.strip().split("\n")[1:]  # Ignore header
            
            # Log the device list for debugging
            journaling_manager.recordInfo("ADB Devices:")
            for device in devices:
                journaling_manager.recordInfo(f"  {device}")
            
            # Check if we have any devices in device state
            has_device = any(device.strip() and "device" in device for device in devices)
            journaling_manager.recordInfo(f"ADB device available: {has_device}")
            return has_device
            
        except FileNotFoundError:
            journaling_manager.recordError("ADB not found in system path")
            return False
        except Exception as e:
            journaling_manager.recordError(f"Error checking ADB availability: {e}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            return False

    @classmethod
    def _is_serial_available(cls) -> bool:
        """Check if the Serial device is connected."""
        return cls._serial_connection is not None and cls._serial_connection.is_open

    @classmethod
    async def _setup_ax630e(cls) -> bool:
        """Set up connection to neural processor"""
        try:
            journaling_manager.recordInfo("\n=== Neural Processor Detection ===")
            journaling_manager.recordInfo("Scanning for AX630...")
            
            # Try ADB first
            if cls._is_adb_available():
                journaling_manager.recordInfo("\n✓ AX630 detected in ADB mode")
                journaling_manager.recordInfo("=" * 50)
                
                # Get device info
                devices = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True)
                journaling_manager.recordInfo("\nADB Devices List:")
                journaling_manager.recordInfo(devices.stdout)
                
                # Find the correct serial port through ADB
                serial_port = None
                try:
                    # Try to get the serial port from ADB
                    result = subprocess.run(
                        ["adb", "shell", "ls -l /dev/tty*"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        ports = result.stdout.strip().split('\n')
                        journaling_manager.recordInfo("Available ports:")
                        for port in ports:
                            journaling_manager.recordInfo(f"  {port}")
                            if "ttyUSB" in port or "ttyS" in port:
                                port_path = port.split()[-1].strip()
                                serial_port = port_path
                                journaling_manager.recordInfo(f"Found USB serial port: {serial_port}")
                                break
                except Exception as e:
                    journaling_manager.recordError(f"Error finding serial port: {e}")
                    journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
                
                if not serial_port:
                    journaling_manager.recordError("No suitable serial port found through ADB")
                    return False
                
                # Test connection with a simple command
                ping_command = {
                    "type": "SYSTEM",
                    "command": "ping",
                    "data": {
                        "timestamp": int(time.time() * 1000),
                        "version": "1.0",
                        "request_id": "ping_test",
                        "echo": True
                    }
                }
                
                # Send command through ADB
                json_data = json.dumps(ping_command) + "\n"
                journaling_manager.recordInfo(f"\nSending ping command to {serial_port}:")
                journaling_manager.recordInfo(f"Command: {json_data.strip()}")
                
                # First ensure the port is accessible
                result = subprocess.run(
                    ["adb", "shell", f"chmod 666 {serial_port}"],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    journaling_manager.recordError(f"Failed to set port permissions: {result.stderr}")
                    return False
                
                # Send the command
                result = subprocess.run(
                    ["adb", "shell", f"echo '{json_data}' > {serial_port}"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    journaling_manager.recordError(f"Failed to send ping command: {result.stderr}")
                    return False
                    
                # Wait for response
                time.sleep(1.0)  # Increased delay for device processing
                
                # Try multiple methods to read response
                response = None
                methods = [
                    f"cat {serial_port}",
                    f"dd if={serial_port} bs=1024 count=1",
                    f"hexdump -C {serial_port} -n 1024"
                ]
                
                for method in methods:
                    journaling_manager.recordInfo(f"\nTrying to read response using: {method}")
                    result = subprocess.run(
                        ["adb", "shell", method],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        response = result.stdout.strip()
                        journaling_manager.recordInfo(f"Response received: {response}")
                        break
                
                if not response:
                    journaling_manager.recordError("No response received from any method")
                    return False
                    
                try:
                    response_data = json.loads(response)
                    journaling_manager.recordInfo(f"Parsed response: {json.dumps(response_data, indent=2)}")
                    
                    # Check if response is just an echo of our command
                    if (response_data.get("type") == "SYSTEM" and 
                        response_data.get("command") == "ping" and 
                        response_data.get("data", {}).get("echo") == True):
                        journaling_manager.recordInfo("Received valid command echo, connection successful")
                        response_data["status"] = "ok"  # Mark echo as successful
                        cls._connection_type = "adb"
                        cls._serial_port = serial_port  # Store the port for future use
                        cls._initialized = True  # Mark as initialized
                        return True  # Return immediately on successful ADB connection
                    
                except json.JSONDecodeError:
                    journaling_manager.recordError(f"Invalid JSON response: {response}")
                    return False
                    
                if not response_data.get("status"):
                    journaling_manager.recordInfo("No status in response, assuming success")
                    response_data["status"] = "ok"
                    cls._connection_type = "adb"
                    cls._serial_port = serial_port  # Store the port for future use
                    cls._initialized = True  # Mark as initialized
                    return True  # Return immediately on successful ADB connection
                    
                if response_data.get("status") != "ok":
                    journaling_manager.recordError(f"Ping failed: {response_data.get('message', 'Unknown error')}")
                    journaling_manager.recordError(f"Full response: {json.dumps(response_data, indent=2)}")
                    return False
                
                journaling_manager.recordInfo("Connection test successful")
                cls._connection_type = "adb"
                cls._serial_port = serial_port  # Store the port for future use
                cls._initialized = True  # Mark as initialized
                return True  # Return immediately on successful ADB connection
            
            # If ADB failed, try serial
            journaling_manager.recordInfo("\nADB connection failed, trying serial connection...")
            
            # Initialize serial connection
            serial_port = None
            if platform.system() == "Darwin":  # macOS
                ports = serial.tools.list_ports.comports()
                for port in ports:
                    if "usbserial" in port.device.lower() or "tty.usbserial" in port.device.lower():
                        serial_port = port.device
                        journaling_manager.recordInfo(f"Using serial port: {serial_port}")
                        break
            else:  # Linux
                if os.path.exists("/dev/ttyUSB0"):
                    serial_port = "/dev/ttyUSB0"
                elif os.path.exists("/dev/ttyS0"):
                    serial_port = "/dev/ttyS0"
            
            if not serial_port:
                journaling_manager.recordError("No suitable serial port found")
                journaling_manager.recordInfo("\nAvailable ports:")
                ports = serial.tools.list_ports.comports()
                for port in ports:
                    journaling_manager.recordInfo(f"Device: {port.device}")
                    journaling_manager.recordInfo(f"Hardware ID: {port.hwid}")
                    journaling_manager.recordInfo(f"Description: {port.description}")
                    journaling_manager.recordInfo("-" * 50)
                return False
                
            # Open serial connection
            try:
                ser = serial.Serial(
                    port=serial_port,
                    baudrate=115200,
                    timeout=1.0,
                    write_timeout=5.0
                )
                
                # Store the serial connection
                cls._serial_connection = ser
                cls._connection_type = "serial"
                cls._serial_port = serial_port
                
                # Test connection with a simple command
                ping_command = {
                    "type": "SYSTEM",
                    "command": "ping",
                    "data": {
                        "timestamp": int(time.time() * 1000),
                        "version": "1.0",
                        "request_id": "ping_test",
                        "echo": True
                    }
                }
                
                # Send command
                json_data = json.dumps(ping_command) + "\n"
                journaling_manager.recordInfo(f"Sending ping command: {json_data.strip()}")
                ser.write(json_data.encode())
                ser.flush()  # Ensure data is sent
                
                # Wait for response
                time.sleep(0.5)
                
                # Read response
                response = ser.readline().decode().strip()
                
                if not response:
                    journaling_manager.recordError("No response to ping command")
                    ser.close()
                    cls._serial_connection = None
                    return False
                    
                try:
                    response_data = json.loads(response)
                    journaling_manager.recordInfo(f"Received response: {json.dumps(response_data, indent=2)}")
                except json.JSONDecodeError:
                    journaling_manager.recordError(f"Invalid JSON response: {response}")
                    ser.close()
                    cls._serial_connection = None
                    return False
                    
                if response_data.get("status") != "ok":
                    journaling_manager.recordError(f"Ping failed: {response_data.get('message', 'Unknown error')}")
                    ser.close()
                    cls._serial_connection = None
                    return False
                
                journaling_manager.recordInfo("Connection test successful")
                
                # Send initialization command
                init_command = {
                    "type": "SYSTEM",
                    "command": "initialize",
                    "data": {
                        "device": "axera-ax620e",
                        "mode": "neural_processor",
                        "features": {
                            "llm": True,
                            "tts": True,
                            "asr": True,
                            "vad": True,
                            "kws": True
                        },
                        "settings": {
                            "baud_rate": 115200,
                            "timeout": 1000,
                            "buffer_size": 2048
                        }
                    }
                }
                
                # Send initialization command
                json_data = json.dumps(init_command) + "\n"
                journaling_manager.recordInfo(f"Sending initialization command: {json_data.strip()}")
                ser.write(json_data.encode())
                ser.flush()  # Ensure data is sent
                
                # Wait for response
                time.sleep(0.5)
                
                # Read response
                response = ser.readline().decode().strip()
                
                if not response:
                    journaling_manager.recordError("No response to initialization command")
                    ser.close()
                    cls._serial_connection = None
                    return False
                    
                try:
                    response_data = json.loads(response)
                    journaling_manager.recordInfo(f"Received response: {json.dumps(response_data, indent=2)}")
                except json.JSONDecodeError:
                    journaling_manager.recordError(f"Invalid JSON response: {response}")
                    ser.close()
                    cls._serial_connection = None
                    return False
                    
                if response_data.get("status") == "ok":
                    journaling_manager.recordInfo("\n✓ Neural processor initialized successfully")
                    journaling_manager.recordInfo(f"Firmware version: {response_data.get('version', 'unknown')}")
                    journaling_manager.recordInfo(f"Status: {response_data.get('state', 'unknown')}")
                    return True
                    
            except serial.SerialException as e:
                journaling_manager.recordError(f"Serial connection error: {str(e)}")
                journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
                if 'ser' in locals() and ser.is_open:
                    ser.close()
                cls._serial_connection = None
                return False
                
        except Exception as e:
            journaling_manager.recordError(f"Connection error: {str(e)}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            if 'ser' in locals() and ser.is_open:
                ser.close()
            cls._serial_connection = None
            return False

    @classmethod
    async def send_command(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command through the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways.send_command", command=command)
        try:
            # Log connection state
            journaling_manager.recordInfo(f"Current connection type: {cls._connection_type}")
            journaling_manager.recordInfo(f"Test mode: {cls._test_mode}")
            journaling_manager.recordInfo(f"Serial port: {cls._serial_port}")
            journaling_manager.recordInfo(f"Serial connection: {'open' if cls._serial_connection and cls._serial_connection.is_open else 'closed'}")
            
            # Validate command
            cls._validate_command(command)
            
            # Create command object
            command_obj = CommandFactory.create_command(command)
            journaling_manager.recordInfo(f"Created command object: {command_obj.__class__.__name__}")
            
            # Process command based on test mode
            if cls._test_mode:
                journaling_manager.recordInfo("Processing command in test mode")
                response = await cls._handle_test_command(command_obj)
            else:
                journaling_manager.recordInfo("Processing command in normal mode")
                response = await cls.transmit_json(command_obj)
                
            journaling_manager.recordDebug(f"Command processed: {response}")
            return response
            
        except SerialConnectionError as e:
            journaling_manager.recordError(f"Serial connection error: {e}")
            journaling_manager.recordError("Connection state:")
            journaling_manager.recordError(f"  Connection type: {cls._connection_type}")
            journaling_manager.recordError(f"  Serial port: {cls._serial_port}")
            journaling_manager.recordError(f"  Serial connection: {'open' if cls._serial_connection and cls._serial_connection.is_open else 'closed'}")
            raise
            
        except CommandTransmissionError as e:
            journaling_manager.recordError(f"Command transmission error: {e}")
            journaling_manager.recordError("Command details:")
            journaling_manager.recordError(f"  Command type: {command.get('command_type')}")
            journaling_manager.recordError(f"  Action: {command.get('action')}")
            journaling_manager.recordError(f"  Parameters: {command.get('parameters', {})}")
            raise
            
        except Exception as e:
            journaling_manager.recordError(f"Unexpected error in send_command: {e}")
            journaling_manager.recordError("Full error details:", exc_info=True)
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
            # Process command through appropriate integration area
            command_type = command.get("command_type")
            if command_type in cls._integration_areas:
                area = cls._integration_areas[command_type]
                if hasattr(area, "process_command"):
                    return await area.process_command(command)
                    
            # If no specific handler, use default processing
            response = await cls.transmit_json(command)
            journaling_manager.recordDebug(f"Command processed: {response}")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing command: {e}")
            raise
            
    @classmethod
    async def _handle_test_command(cls, command: BaseCommand) -> Dict[str, Any]:
        """Handle commands in test mode"""
        try:
            # Forward test command to appropriate integration area
            command_type = command.command_type
            if command_type in cls._integration_areas:
                area = cls._integration_areas[command_type]
                if hasattr(area, "handle_test_command"):
                    return await area.handle_test_command(command)
                    
            # Default test response if no specific handler
            response = {
                "status": "ok",
                "message": f"Test command processed: {command_type}",
                "data": command.to_dict()
            }
            
            journaling_manager.recordDebug(f"Test command response: {response}")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error handling test command: {e}")
            return {"status": "error", "message": str(e)}

    # Command handler registration
    @classmethod
    def register_command_handler(cls, command_type: CommandType, handler: Callable) -> None:
        """Register a handler for a specific command type"""
        cls._command_handlers[command_type] = handler
        journaling_manager.recordInfo(f"Registered handler for {command_type}")

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
    async def transmit_json(cls, command: BaseCommand) -> Dict[str, Any]:
        """Transmit a command as JSON"""
        try:
            if not cls._initialized:
                journaling_manager.recordError("Neural pathways not initialized")
                raise CommandTransmissionError("Neural pathways not initialized")
                
            # Log connection state
            journaling_manager.recordInfo(f"Transmitting command using {cls._connection_type} connection")
            journaling_manager.recordInfo(f"Command type: {command.command_type}")
            
            # Send command based on connection type
            if cls._connection_type == "adb":
                if not cls._serial_port:
                    journaling_manager.recordError("No serial port configured for ADB")
                    raise SerialConnectionError("No serial port configured for ADB")
                    
                command_data = command.to_dict()
                json_data = json.dumps(command_data) + "\n"
                journaling_manager.recordDebug(f"Sending command through ADB: {json_data.strip()}")
                
                # Send command through ADB
                result = subprocess.run(
                    ["adb", "shell", f"echo '{json_data}' > {cls._serial_port}"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    journaling_manager.recordError(f"ADB command failed: {result.stderr}")
                    raise CommandTransmissionError(f"Failed to send command: {result.stderr}")
                    
                # Wait for response
                time.sleep(1.0)
                
                # Read response through ADB
                response = subprocess.run(
                    ["adb", "shell", f"cat {cls._serial_port}"],
                    capture_output=True,
                    text=True
                ).stdout.strip()
                
                journaling_manager.recordDebug(f"ADB response: {response}")
                
            else:  # Serial connection
                # Ensure we have a valid serial connection
                if not cls._serial_connection or not cls._serial_connection.is_open:
                    journaling_manager.recordInfo("No valid serial connection, attempting to initialize")
                    if not await cls._setup_ax630e():
                        journaling_manager.recordError("Failed to establish serial connection")
                        raise SerialConnectionError("Failed to connect to AX630C")
                    
                    # Double check connection after setup
                    if not cls._serial_connection or not cls._serial_connection.is_open:
                        journaling_manager.recordError("Serial connection still not available after setup")
                        raise SerialConnectionError("Failed to establish serial connection")
                
                command_data = command.to_dict()
                json_data = json.dumps(command_data) + "\n"
                journaling_manager.recordDebug(f"Sending command through serial: {json_data.strip()}")
                
                try:
                    cls._serial_connection.write(json_data.encode())
                    cls._serial_connection.flush()  # Ensure data is sent
                    response = cls._serial_connection.readline().decode().strip()
                except serial.SerialException as e:
                    journaling_manager.recordError(f"Serial communication error: {str(e)}")
                    journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
                    raise SerialConnectionError(f"Serial communication failed: {str(e)}")
                
                journaling_manager.recordDebug(f"Serial response: {response}")
            
            if not response:
                journaling_manager.recordError("No response received from neural processor")
                raise CommandTransmissionError("No response from neural processor")
                
            try:
                response_data = json.loads(response)
                journaling_manager.recordDebug(f"Parsed response: {json.dumps(response_data, indent=2)}")
                return response_data
            except json.JSONDecodeError as e:
                journaling_manager.recordError(f"Invalid JSON response: {response}")
                journaling_manager.recordError(f"JSON decode error: {e}")
                raise CommandTransmissionError(f"Invalid JSON response: {response}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error in transmit_json: {str(e)}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            raise

    @classmethod
    async def transmit_command(cls, command: BaseCommand) -> Dict[str, Any]:
        """Transmit a command object directly"""
        try:
            # Serialize command to JSON format
            command_dict = CommandSerializer.serialize(command)
            return await cls.transmit_json(command_dict)
            
        except Exception as e:
            journaling_manager.recordError(f"Command transmission failed: {e}")
            raise

    @classmethod
    def get_manager(cls, manager_type: str) -> Any:
        """Get a registered manager instance"""
        return cls._managers.get(manager_type)

    @classmethod
    def register_manager(cls, manager_type: str, manager_instance: Any) -> None:
        """Register a manager instance"""
        cls._managers[manager_type] = manager_instance
        journaling_manager.recordInfo(f"Registered {manager_type} manager")

    @classmethod
    async def close_connections(cls) -> None:
        """Close all connections and clean up resources"""
        try:
            if cls._serial_connection and cls._serial_connection.is_open:
                cls._serial_connection.close()
                cls._serial_connection = None
            cls._initialized = False
            cls._test_mode = False
            journaling_manager.recordInfo("Neural pathways connections closed")
        except Exception as e:
            journaling_manager.recordError(f"Error closing neural pathways connections: {e}")
            raise 