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
import stat
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Callable, Type
from enum import Enum
import subprocess
import re
import traceback
import threading
import socket
import paramiko

# Third-party imports
import serial
import serial.tools.list_ports

# Local imports
from Mind.CorpusCallosum.neural_commands import (
    BaseCommand, CommandType, CommandFactory, CommandSerializer,
    TTSCommand, ASRCommand, LLMCommand, SystemCommand, WhisperCommand, VADCommand
)
from Mind.CorpusCallosum.command_loader import CommandLoader
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
    _response_buffer = ""
    _response_callback = None
    _response_thread = None
    _stop_thread = False

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
            # Skip if already initialized
            if cls._initialized:
                journaling_manager.recordInfo("Synaptic pathways already initialized")
                return
                
            # Only try to connect if we have a valid connection type
            if not cls._connection_type:
                raise SerialConnectionError("No connection type specified")
                
            # Initialize the specified connection mode
            await cls.set_device_mode(cls._connection_type)
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
        
        # Use the connection type specified by command line argument
        if cls._connection_type == "wifi":
            cls.welcome_message = "Welcome to PenphinMind (WiFi)."
            journaling_manager.recordInfo("Using WiFi connection")
            return
        elif cls._connection_type == "adb":
            if cls._is_adb_available():
                cls.welcome_message = "Welcome to PenphinMind (ADB)."
                journaling_manager.recordInfo("Using ADB connection")
                return  
        elif cls._connection_type == "serial":
            if cls._is_serial_available():
                cls.welcome_message = "Welcome to PenphinMind (Serial)."
                journaling_manager.recordInfo("Using Serial connection")
                return
            
        # If we get here, the specified connection type is not available
        cls._connection_type = None
        cls.welcome_message = "Welcome to PenphinMind."
        journaling_manager.recordInfo(f"Specified connection type {cls._connection_type} not available")

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
            journaling_manager.recordInfo("\n=== Neural Processor Connection ===")
            
            # Only handle the specified connection type
            if cls._connection_type == "wifi":
                # WiFi connection is already set up in set_device_mode
                return True
            elif cls._connection_type == "serial":
                if not cls._is_serial_available():
                    journaling_manager.recordError("No serial ports available")
                    return False
                
                cls._serial_port = cls._find_serial_port()
                if not cls._serial_port:
                    journaling_manager.recordError("No suitable serial port found")
                    return False
                    
                # Open serial connection
                try:
                        cls._serial_connection = serial.Serial(
                            port=cls._serial_port,
                        baudrate=115200,
                            timeout=2.0,
                        write_timeout=5.0
                    )
                        return True
                except serial.SerialException as e:
                        journaling_manager.recordError(f"Serial connection error: {str(e)}")
                        return False
                    
            elif cls._connection_type == "adb":
                if not cls._is_adb_available():
                    journaling_manager.recordError("ADB not available")
                    return False
                    
                cls._serial_port = cls._find_adb_port()
                if not cls._serial_port:
                    journaling_manager.recordError("No suitable ADB port found")
                    return False
                    
                return True
                
            else:
                journaling_manager.recordError(f"Unsupported connection type: {cls._connection_type}")
                return False
                
        except Exception as e:
            journaling_manager.recordError(f"Connection error: {str(e)}")
            journaling_manager.recordError(f"Error details: {traceback.format_exc()}")
            return False

    @classmethod
    async def send_command(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to the hardware"""
        try:
            # Log connection state
            journaling_manager.recordInfo(f"Current connection type: {cls._connection_type}")
            journaling_manager.recordInfo(f"Operational mode: {cls._mode}")
            journaling_manager.recordInfo(f"Connection port: {cls._serial_port}")
            
            # Load command definitions
            command_loader = CommandLoader()
            command_definitions = command_loader._load_command_definitions()
            
            # Get command type and validate against definitions
            command_type_str = command.get("type", "").upper()  # Convert to uppercase for enum lookup
            try:
                command_type = CommandType[command_type_str]  # Use uppercase for enum lookup
            except KeyError:
                raise ValueError(f"Invalid command type: {command_type_str}")
                
            # For LLM commands, use the prototype format
            if command_type == CommandType.LLM and command.get("command") == "generate":
                # Create command object using LLMCommand class
                command_obj = LLMCommand(
                    command_type=command_type,
                    request_id=command.get("data", {}).get("request_id", f"generate_{int(time.time())}"),
                    work_id="llm",
                    action="inference",
                    object="llm.utf-8.stream",
                    data={
                        "text": command.get("data", ""),  # Get the text directly from data
                        "index": 0,
                        "finish": True
                    }
                ).to_dict()
                # Validate against command definitions
                command_loader.validate_command(command_type_str, command_obj)
            else:
                # Create command object using CommandFactory for other types
                command_obj = CommandFactory.create_command(
                        command_type=command_type,
                        action=command.get("command", "process"),
                        parameters=command.get("data", {})
                )
                command_obj = command_obj.to_dict()
            
            # Validate command against its definition using the uppercase command type
            command_loader.validate_command(command_type_str, command_obj)
            
            # Transmit command to hardware
            journaling_manager.recordInfo("Transmitting command to hardware")
            return await cls.transmit_json(command_obj)
            
        except Exception as e:
            journaling_manager.recordError(f"Unexpected error in send_command: {str(e)}")
            journaling_manager.recordError(f"Full error details:\n{traceback.format_exc()}")
            raise

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

    @classmethod
    def _start_response_thread(cls):
        """Start thread to continuously read responses"""
        cls._stop_thread = False
        cls._response_thread = threading.Thread(target=cls._read_responses)
        cls._response_thread.daemon = True
        cls._response_thread.start()

    @classmethod
    def _stop_response_thread(cls):
        """Stop the response reading thread"""
        cls._stop_thread = True
        if cls._response_thread:
            cls._response_thread.join()

    @classmethod
    def _read_responses(cls):
        """Continuously read responses from the serial port"""
        while not cls._stop_thread:
            if cls._connection_type == "serial" and cls._serial_connection and cls._serial_connection.is_open:
                try:
                    if cls._serial_connection.in_waiting:
                        char = cls._serial_connection.read().decode('utf-8')
                        cls._response_buffer += char
                        
                        # Check for complete JSON response
                        if char == '\n' and cls._response_buffer.strip():
                            try:
                                response = json.loads(cls._response_buffer.strip())
                                if cls._response_callback:
                                    cls._response_callback(response.get('data', ''))
                            except json.JSONDecodeError:
                                journaling_manager.recordError(f"Error decoding JSON: {cls._response_buffer}")
                            finally:
                                cls._response_buffer = ""
                except Exception as e:
                    journaling_manager.recordError(f"Error reading from serial: {e}")
            elif cls._connection_type == "adb":
                try:
                    # Read one character at a time using ADB
                    read_result = subprocess.run(
                        ["adb", "shell", f"dd if={cls._serial_port} bs=1 count=1 iflag=nonblock 2>/dev/null"],
                        capture_output=True,
                        text=True
                    )
                    
                    if read_result.returncode == 0 and read_result.stdout:
                        char = read_result.stdout
                        cls._response_buffer += char
                        
                        # Check for complete JSON response
                        if char == '\n' and cls._response_buffer.strip():
                            try:
                                response = json.loads(cls._response_buffer.strip())
                                if cls._response_callback:
                                    cls._response_callback(response.get('data', ''))
                            except json.JSONDecodeError:
                                journaling_manager.recordError(f"Error decoding JSON: {cls._response_buffer}")
                            finally:
                                cls._response_buffer = ""
                except Exception as e:
                    journaling_manager.recordError(f"Error reading from ADB: {e}")
            time.sleep(0.01)

    @classmethod
    async def set_device_mode(cls, mode: str) -> None:
        """Initialize the connection in the requested mode (serial, adb, or wifi)"""
        if mode not in ["serial", "adb", "wifi"]:
            raise ValueError("Invalid mode. Use 'serial', 'adb', or 'wifi'")
            
        journaling_manager.recordInfo(f"\nInitializing {mode} connection...")
        
        try:
            # Clean up current connection first
            await cls.cleanup()
            
            # For WiFi mode
            if mode == "wifi":
                journaling_manager.recordInfo("Setting up WiFi connection...")
                
                # Use LLM service configuration from CONFIG
                llm_ip = CONFIG.llm_service["ip"]
                llm_port = CONFIG.llm_service["port"]
                llm_timeout = CONFIG.llm_service["timeout"]
                
                journaling_manager.recordInfo(f"Using LLM service IP: {llm_ip}")
                
                # Use SSH to find the LLM service port
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                journaling_manager.recordInfo(f"\nConnecting to {llm_ip}:22...")
                ssh.connect(llm_ip, port=22, username="root", password="123456")
                
                # Find the LLM service port
                service_port = cls._find_llm_port(ssh)
                ssh.close()
                
                cls._serial_port = f"{llm_ip}:{service_port}"  # Use IP:port format
                cls._connection_type = "wifi"
                journaling_manager.recordInfo(f"Found WiFi connection at {cls._serial_port}")
                
            else:
                # For Serial and ADB modes
                journaling_manager.recordInfo(f"Setting up {mode} connection...")
                
                if mode == "serial":
                    if cls._is_serial_available():
                        cls._serial_port = cls._find_serial_port()
                        if cls._serial_port:
                            cls._connection_type = "serial"
                            journaling_manager.recordInfo(f"Found serial port: {cls._serial_port}")
                        else:
                            raise Exception("No suitable serial port found")
                    else:
                        raise Exception("No serial ports available")
                else:  # adb
                    if cls._is_adb_available():
                        cls._serial_port = cls._find_adb_port()
                        if cls._serial_port:
                            cls._connection_type = "adb"
                            journaling_manager.recordInfo(f"Found ADB port: {cls._serial_port}")
                        else:
                            raise Exception("No suitable ADB port found")
                    else:
                        raise Exception("ADB not available")
            
            # Initialize new connection
            if cls._connection_type == "serial":
                journaling_manager.recordInfo("Setting up serial connection...")
                cls._serial_connection = serial.Serial(
                    port=cls._serial_port,
                    baudrate=115200,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1,
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False
                )
                while cls._serial_connection.in_waiting:
                    cls._serial_connection.read()
                journaling_manager.recordInfo("Serial connection established")
            
            cls._initialized = True
            journaling_manager.recordInfo(f"Successfully initialized {cls._connection_type} connection with port {cls._serial_port}")
            
            # Test the connection
            journaling_manager.recordInfo("\nTesting connection...")
            # Create a proper SystemCommand object with sys_ping request_id
            ping_command = SystemCommand(
                command_type=CommandType.SYS,
                action="ping",
                parameters={
                    "timestamp": int(time.time() * 1000),
                    "version": "1.0",
                    "request_id": "sys_ping",  # Changed to match prototype
                    "echo": True
                }
            )
            response = await cls.transmit_json(ping_command)
            journaling_manager.recordInfo(f"Connection test response: {response}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing {mode} connection: {e}")
            raise

    @classmethod
    def _find_llm_port(cls, ssh) -> int:
        """Find the port where the LLM service is running"""
        journaling_manager.recordInfo("\nChecking for LLM service port...")
        
        # First try to find the port from the process
        stdin, stdout, stderr = ssh.exec_command("lsof -i -P -n | grep llm_llm")
        for line in stdout:
            journaling_manager.recordInfo(f"Found port info: {line.strip()}")
            # Look for port number in the output
            if ":" in line:
                port = line.split(":")[-1].split()[0]
                journaling_manager.recordInfo(f"Found LLM service port: {port}")
                return int(port)
        
        # If we couldn't find it through lsof, try netstat
        journaling_manager.recordInfo("\nTrying netstat to find port...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tulpn | grep llm_llm")
        for line in stdout:
            journaling_manager.recordInfo(f"Found port info: {line.strip()}")
            # Look for port number in the output
            if ":" in line:
                port = line.split(":")[-1].split()[0]
                journaling_manager.recordInfo(f"Found LLM service port: {port}")
                return int(port)
        
        # If we still can't find it, try to get the port from the process arguments
        journaling_manager.recordInfo("\nChecking process arguments...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep llm_llm")
        for line in stdout:
            if "llm_llm" in line and not "grep" in line:
                journaling_manager.recordInfo(f"Found process: {line.strip()}")
                # Try to find port in process arguments
                if "--port" in line:
                    port = line.split("--port")[1].split()[0]
                    journaling_manager.recordInfo(f"Found port in arguments: {port}")
                    return int(port)
        
        # If we get here, try common ports
        journaling_manager.recordInfo("\nTrying common ports...")
        common_ports = [10001, 8080, 80, 443, 5000, 8000, 3000]  # Put 10001 first since we know it works
        for port in common_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    # Get the IP from the SSH connection
                    ip = ssh.get_transport().getpeername()[0]
                    result = s.connect_ex((ip, port))
                    if result == 0:
                        journaling_manager.recordInfo(f"Port {port} is open and accepting connections")
                        return port
            except Exception as e:
                journaling_manager.recordError(f"Error checking port {port}: {e}")
        
        raise Exception("Could not find LLM service port")

    @classmethod
    async def transmit_json(cls, command: Union[BaseCommand, Dict[str, Any]]) -> Dict[str, Any]:
        """Transmit a command as JSON"""
        try:
            if not cls._initialized:
                journaling_manager.recordError("Neural pathways not initialized")
                raise CommandTransmissionError("Neural pathways not initialized")
                
            # Log connection state
            journaling_manager.recordInfo(f"Transmitting command using {cls._connection_type} connection")
            
            # Get command data and type
            if isinstance(command, BaseCommand):
                command_data = command.to_dict()
                command_type = command.command_type
            else:
                command_data = command
                command_type = command.get("command_type")
                
            journaling_manager.recordInfo(f"Command type: {command_type}")
            
            # Send command based on connection type
            if cls._connection_type == "wifi":
                # Parse IP and port from self._serial_port
                ip, port = cls._serial_port.split(":")
                port = int(port)
                
                # Connect to the LLM service
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5.0)  # 5 second timeout
                    journaling_manager.recordInfo(f"Connecting to {ip}:{port}...")
                    s.connect((ip, port))
                    journaling_manager.recordInfo("Connected successfully")
                    
                    # Send command
                    json_data = json.dumps(command_data) + "\n"
                    journaling_manager.recordInfo(f"Sending command: {json_data.strip()}")
                    s.sendall(json_data.encode())
                    journaling_manager.recordInfo("Command sent successfully")
                    
                    # Wait for response
                    buffer = ""
                    journaling_manager.recordInfo("Waiting for response...")
                    while True:
                        try:
                            data = s.recv(1).decode()
                            if not data:
                                journaling_manager.recordInfo("No more data received")
                                break
                            buffer += data
                            
                            # For chat responses, print characters as they arrive
                            if command_type == CommandType.LLM and command_data.get("action") == "inference":
                                print(data, end="", flush=True)
                            
                            if data == "\n":
                                journaling_manager.recordInfo("Received newline, ending read")
                                break
                        except socket.timeout:
                            journaling_manager.recordError("Socket timeout")
                            break
                    
                    journaling_manager.recordInfo(f"Received response: {buffer.strip()}")
                    try:
                        response = json.loads(buffer.strip())
                        # Parse response like the prototype
                        if response.get("work_id") == "llm" and response.get("action") == "inference":
                            return {
                                "status": "ok",
                                "response": response.get("data", {}).get("delta", ""),
                                "finished": response.get("data", {}).get("finish", False),
                                "index": response.get("data", {}).get("index", 0)
                            }
                        return response
                    except json.JSONDecodeError:
                        journaling_manager.recordError(f"Failed to parse JSON: {buffer.strip()}")
                        return {"error": "Failed to parse response", "raw": buffer.strip()}
                        
            elif cls._connection_type == "adb":
                if not cls._serial_port:
                    journaling_manager.recordError("No serial port configured for ADB")
                    raise SerialConnectionError("No serial port configured for ADB")
                    
                command_data = command_data
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
                
                command_data = command_data
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