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
    _mode = None  # Set by command line argument
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
    def set_mode(cls, mode: str) -> None:
        """Set operational mode from command line argument"""
        cls._mode = mode
        journaling_manager.recordInfo(f"Operational mode set to: {mode}")

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways.initialize")
        try:
            # Detect platform for hardware connection
            cls._detect_platform()
            
            # Only try to connect if we have a valid platform
            if cls._connection_type:
                if not await cls._setup_ax630e():
                    raise SerialConnectionError("Failed to connect to neural processor")
            else:
                raise SerialConnectionError("No valid hardware platform detected")
                    
            journaling_manager.recordInfo("Synaptic pathways initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize synaptic pathways: {e}")
            raise

    @classmethod
    def _detect_platform(cls) -> None:
        """Detect platform for hardware connection"""
        journaling_manager.recordInfo("\n=== Platform Detection ===")
        journaling_manager.recordInfo(f"System: {platform.system()}")
        journaling_manager.recordInfo(f"Platform: {platform.platform()}")
        journaling_manager.recordInfo(f"Machine: {platform.machine()}")
        
        # Check for ADB connection first
        if cls._is_adb_available():
            cls._connection_type = "adb"
            cls.welcome_message = "Welcome to PenphinMind."
            journaling_manager.recordInfo("ADB connection detected")
            return
            
        # Then check for Serial connection
        if cls._is_serial_available():
            cls._connection_type = "serial"
            cls.welcome_message = "Welcome to PenphinMind."
            journaling_manager.recordInfo("Serial connection detected")
            return
            
        # If no hardware connection found
        cls._connection_type = None
        cls.welcome_message = "Welcome to PenphinMind."
        journaling_manager.recordInfo("No hardware connection detected")

    @classmethod
    def _is_adb_available(cls) -> bool:
        """Check if an ADB device is connected."""
        journaling_manager.recordInfo("\n=== ADB Detection ===")
        try:
            # First check if adb is installed
            journaling_manager.recordInfo("Checking if ADB is installed...")
            which_result = subprocess.run(["which", "adb"], capture_output=True, text=True)
            if which_result.returncode != 0:
                journaling_manager.recordError("ADB not found in system path")
                return False
            journaling_manager.recordInfo(f"ADB found at: {which_result.stdout.strip()}")
            
            # First try to start the ADB server
            journaling_manager.recordInfo("Starting ADB server...")
            result = subprocess.run(["adb", "start-server"], capture_output=True, text=True)
            journaling_manager.recordInfo(f"ADB server start result: {result.stdout}")
            if result.stderr:
                journaling_manager.recordError(f"ADB server start error: {result.stderr}")
            
            # Then check for devices
            journaling_manager.recordInfo("Checking for ADB devices...")
            result = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True)
            journaling_manager.recordInfo(f"ADB devices output:\n{result.stdout}")
            
            devices = result.stdout.strip().split("\n")[1:]  # Ignore header
            
            # Log the device list for debugging
            journaling_manager.recordInfo("ADB Devices:")
            for device in devices:
                journaling_manager.recordInfo(f"  {device}")
            
            # Check if we have any devices in device state
            has_device = any(device.strip() and "device" in device for device in devices)
            journaling_manager.recordInfo(f"ADB device available: {has_device}")
            
            if not has_device:
                # Try to restart ADB server and check again
                journaling_manager.recordInfo("No devices found, trying to restart ADB server...")
                subprocess.run(["adb", "kill-server"], capture_output=True)
                time.sleep(1)
                subprocess.run(["adb", "start-server"], capture_output=True)
                time.sleep(2)
                
                # Check devices again
                result = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True)
                journaling_manager.recordInfo(f"ADB devices after restart:\n{result.stdout}")
                
                devices = result.stdout.strip().split("\n")[1:]
                has_device = any(device.strip() and "device" in device for device in devices)
                journaling_manager.recordInfo(f"ADB device available after restart: {has_device}")
            
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
        journaling_manager.recordInfo("\n=== Serial Port Detection ===")
        if platform.system() == "Darwin":  # macOS
            journaling_manager.recordInfo("Checking macOS serial ports...")
            ports = serial.tools.list_ports.comports()
            for port in ports:
                journaling_manager.recordInfo(f"Found port: {port.device}")
                journaling_manager.recordInfo(f"Hardware ID: {port.hwid}")
                journaling_manager.recordInfo(f"Description: {port.description}")
                if "ax630" in port.description.lower() or "axera" in port.description.lower():
                    journaling_manager.recordInfo(f"Found AX630 device: {port.device}")
                    return True
        else:  # Linux (including Raspberry Pi)
            journaling_manager.recordInfo("Checking Linux serial ports...")
            # First try to find AX630 by device name
            ports = serial.tools.list_ports.comports()
            for port in ports:
                journaling_manager.recordInfo(f"Found port: {port.device}")
                journaling_manager.recordInfo(f"Hardware ID: {port.hwid}")
                journaling_manager.recordInfo(f"Description: {port.description}")
                if "ax630" in port.description.lower() or "axera" in port.description.lower():
                    journaling_manager.recordInfo(f"Found AX630 device: {port.device}")
                    return True
                    
            # If no AX630 found, check common Raspberry Pi ports
            pi_ports = [
                "/dev/ttyAMA0",  # Primary UART
                "/dev/ttyAMA1",  # Secondary UART
                "/dev/ttyUSB0",  # USB to Serial
                "/dev/ttyUSB1",  # USB to Serial
                "/dev/ttyS0",    # Serial
                "/dev/ttyS1"     # Serial
            ]
            
            for port in pi_ports:
                if os.path.exists(port):
                    journaling_manager.recordInfo(f"Found Raspberry Pi port: {port}")
                    return True
                    
            # If no standard ports found, list all available ports
            journaling_manager.recordInfo("No standard ports found, listing all available ports:")
            ports = serial.tools.list_ports.comports()
            for port in ports:
                journaling_manager.recordInfo(f"Device: {port.device}")
                journaling_manager.recordInfo(f"Hardware ID: {port.hwid}")
                journaling_manager.recordInfo(f"Description: {port.description}")
                journaling_manager.recordInfo("-" * 50)
                
        journaling_manager.recordInfo("No suitable serial port found")
        return False

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
                    if platform.system() == "Darwin":  # macOS
                        # On macOS, try to find the port through ADB
                        result = subprocess.run(
                            ["adb", "shell", "getprop | grep tty"],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            journaling_manager.recordInfo("Device properties:")
                            journaling_manager.recordInfo(result.stdout)
                            
                            # Look for serial port in properties
                            for line in result.stdout.split('\n'):
                                if "tty" in line:
                                    # Extract port from property
                                    port_match = re.search(r'/dev/tty\S+', line)
                                    if port_match:
                                        serial_port = port_match.group(0)
                                        journaling_manager.recordInfo(f"Found AX630 port through ADB: {serial_port}")
                                        break
                            
                            if not serial_port:
                                # Try to find port through USB device list
                                result = subprocess.run(
                                    ["adb", "shell", "ls -l /dev/tty*"],
                                    capture_output=True,
                                    text=True
                                )
                                if result.returncode == 0:
                                    journaling_manager.recordInfo("Available ports:")
                                    journaling_manager.recordInfo(result.stdout)
                                    
                                    # Look for serial port in device list
                                    for line in result.stdout.split('\n'):
                                        if "ttyUSB" in line or "ttyACM" in line:
                                            port_match = re.search(r'/dev/tty\S+', line)
                                            if port_match:
                                                serial_port = port_match.group(0)
                                                journaling_manager.recordInfo(f"Found AX630 port in device list: {serial_port}")
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
                    
                # Wait for response with timeout
                max_attempts = 3
                for attempt in range(max_attempts):
                    journaling_manager.recordInfo(f"\nAttempt {attempt + 1} to read response:")
                    # Try multiple methods to read response
                    methods = [
                        f"cat {serial_port}",
                        f"dd if={serial_port} bs=1024 count=1",
                        f"hexdump -C {serial_port} -n 1024"
                    ]
                    
                    for method in methods:
                        journaling_manager.recordInfo(f"Trying: {method}")
                        result = subprocess.run(
                            ["adb", "shell", method],
                            capture_output=True,
                            text=True,
                            timeout=2  # 2 second timeout
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            response = result.stdout.strip()
                            journaling_manager.recordInfo(f"Response received: {response}")
                            
                            try:
                                response_data = json.loads(response)
                                if (response_data.get("type") == "SYSTEM" and 
                                    response_data.get("command") == "ping" and 
                                    response_data.get("data", {}).get("echo") == True):
                                    journaling_manager.recordInfo("Received valid command echo, connection successful")
                                    cls._connection_type = "adb"
                                    cls._serial_port = serial_port
                                    cls._initialized = True
                                    return True
                            except json.JSONDecodeError:
                                journaling_manager.recordError(f"Invalid JSON response: {response}")
                                continue
                    
                    time.sleep(1)  # Wait before next attempt
                
                journaling_manager.recordError("No valid response received after multiple attempts")
                return False
                
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
                return False
                
            # Open serial connection
            try:
                ser = serial.Serial(
                    port=serial_port,
                    baudrate=115200,
                    timeout=2.0,  # 2 second timeout
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
                
                # Wait for response with timeout
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        response = ser.readline().decode().strip()
                        if response:
                            journaling_manager.recordInfo(f"Response received: {response}")
                            try:
                                response_data = json.loads(response)
                                if (response_data.get("type") == "SYSTEM" and 
                                    response_data.get("command") == "ping" and 
                                    response_data.get("data", {}).get("echo") == True):
                                    journaling_manager.recordInfo("Received valid command echo, connection successful")
                                    cls._initialized = True
                                    return True
                            except json.JSONDecodeError:
                                journaling_manager.recordError(f"Invalid JSON response: {response}")
                                continue
                    except serial.SerialTimeoutException:
                        journaling_manager.recordError(f"Timeout on attempt {attempt + 1}")
                        continue
                    
                    time.sleep(1)  # Wait before next attempt
                
                journaling_manager.recordError("No valid response received after multiple attempts")
                ser.close()
                cls._serial_connection = None
                return False
                    
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
            # Ensure neural pathways are initialized
            if not cls._initialized:
                journaling_manager.recordInfo("Neural pathways not initialized, initializing now")
                await cls.initialize()
                
            # Log connection state
            journaling_manager.recordInfo(f"Current connection type: {cls._connection_type}")
            journaling_manager.recordInfo(f"Operational mode: {cls._mode}")
            journaling_manager.recordInfo(f"Serial port: {cls._serial_port}")
            journaling_manager.recordInfo(f"Serial connection: {'open' if cls._serial_connection and cls._serial_connection.is_open else 'closed'}")
            
            # Create command object first
            command_type = command.pop("command_type")  # Remove command_type from dict
            command_obj = CommandFactory.create_command(
                command_type=CommandType(command_type),
                **command
            )
            journaling_manager.recordInfo(f"Created command object: {command_obj.__class__.__name__}")
            
            # Validate command object
            cls._validate_command(command_obj)
            
            # Transmit command to hardware
            journaling_manager.recordInfo("Transmitting command to hardware")
            return await cls.transmit_json(command_obj)
            
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
    def _validate_command(cls, command: BaseCommand) -> None:
        """Validate a command"""
        journaling_manager.recordScope("SynapticPathways._validate_command", command=command)
        try:
            # Get command data without timestamp
            command_data = command.to_dict()
            command_data.pop('timestamp', None)
            
            # Validate command data
            CommandFactory.validate_command(command.command_type, command_data)
            journaling_manager.recordDebug("Command validated successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Command validation failed: {e}")
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
            cls._mode = None
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
                    
                # Wait for response with timeout
                max_attempts = 3
                for attempt in range(max_attempts):
                    journaling_manager.recordInfo(f"\nAttempt {attempt + 1} to read response:")
                    # Try multiple methods to read response
                    methods = [
                        f"cat {cls._serial_port}",
                        f"dd if={cls._serial_port} bs=1024 count=1",
                        f"hexdump -C {cls._serial_port} -n 1024"
                    ]
                    
                    for method in methods:
                        journaling_manager.recordInfo(f"Trying: {method}")
                        result = subprocess.run(
                            ["adb", "shell", method],
                            capture_output=True,
                            text=True,
                            timeout=2  # 2 second timeout
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            response = result.stdout.strip()
                            journaling_manager.recordInfo(f"Response received: {response}")
                            
                            try:
                                response_data = json.loads(response)
                                return response_data
                            except json.JSONDecodeError:
                                journaling_manager.recordError(f"Invalid JSON response: {response}")
                                continue
                    
                    time.sleep(1)  # Wait before next attempt
                
                journaling_manager.recordError("No valid response received after multiple attempts")
                raise CommandTransmissionError("No response from neural processor")
                
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
                    
                    # Wait for response with timeout
                    max_attempts = 3
                    for attempt in range(max_attempts):
                        try:
                            response = cls._serial_connection.readline().decode().strip()
                            if response:
                                try:
                                    response_data = json.loads(response)
                                    return response_data
                                except json.JSONDecodeError:
                                    journaling_manager.recordError(f"Invalid JSON response: {response}")
                                    continue
                        except serial.SerialTimeoutException:
                            journaling_manager.recordError(f"Timeout on attempt {attempt + 1}")
                            continue
                        
                        time.sleep(1)  # Wait before next attempt
                    
                    raise CommandTransmissionError("No response from neural processor")
                    
                except serial.SerialException as e:
                    journaling_manager.recordError(f"Serial communication error: {str(e)}")
                    journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
                    raise SerialConnectionError(f"Serial communication failed: {str(e)}")
            
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
            cls._mode = None
            journaling_manager.recordInfo("Neural pathways connections closed")
        except Exception as e:
            journaling_manager.recordError(f"Error closing neural pathways connections: {e}")
            raise 