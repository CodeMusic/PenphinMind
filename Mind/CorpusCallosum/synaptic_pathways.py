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
    current_hw_info = {
        "cpu_load": "N/A",
        "memory_usage": "N/A",
        "temperature": "N/A",
        "timestamp": 0
    }
    # Store available models
    available_models = []
    default_llm_model = ""
    
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
        """Send a command to the appropriate processor"""
        journaling_manager.recordInfo(f"\nProcessing command: {command}")
        
        command_type = command.get("type", "")
        command_action = command.get("command", "")
        
        # Handle LLM commands
        if command_type == "LLM":
            # Get a timestamp for request ID
            request_id = command.get("data", {}).get("request_id", f"llm_{int(time.time())}")
            
            # Generate a work ID if none provided
            work_id = f"llm.{int(time.time())}"
            
            if command_action == "setup":
                # Setup LLM with specified parameters
                setup_data = command.get("data", {})
                setup_command = {
                    "request_id": request_id,
                    "work_id": work_id,
                    "action": "setup",
                    "object": "llm.setup",
                    "data": {
                        "model": setup_data.get("model", "qwen2.5-0.5b"),
                        "response_format": setup_data.get("response_format", "llm.utf-8"),
                        "input": setup_data.get("input", "llm.utf-8"),
                        "enoutput": setup_data.get("enoutput", True),
                        "enkws": setup_data.get("enkws", False),
                        "max_token_len": setup_data.get("max_token_len", 127),
                        "prompt": setup_data.get("prompt", "You are a helpful assistant.")
                    }
                }
                return await cls.transmit_json(setup_command)
                
            elif command_action == "generate":
                # Inference with user input
                prompt = command.get("data", {}).get("prompt", "")
                inference_command = {
                    "request_id": request_id,
                    "work_id": work_id,
                    "action": "inference",
                    "object": "llm.utf-8",
                    "data": {
                        "delta": prompt,
                        "index": 0,
                        "finish": True
                    }
                }
                return await cls.transmit_json(inference_command)
                
            elif command_action == "exit":
                # Exit LLM session
                exit_command = {
                    "request_id": request_id,
                    "work_id": work_id,
                    "action": "exit"
                }
                return await cls.transmit_json(exit_command)
                
            elif command_action == "status":
                # Get LLM status
                status_command = {
                    "request_id": request_id,
                    "work_id": work_id,
                    "action": "taskinfo"
                }
                return await cls.transmit_json(status_command)
            
            else:
                # Unknown command
                return {
                    "error": {
                        "code": 1,
                        "message": f"Unknown LLM command: {command_action}"
                    }
                }
                
        # Handle other command types...
        # This would be implemented for other command types
        
        return {
            "error": {
                "code": 1,
                "message": f"Unknown command type: {command_type}"
            }
        }

    @classmethod
    async def send_system_command(cls, command_type: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a system command through the synaptic pathways"""
        journaling_manager.recordScope("SynapticPathways.send_system_command", command_type=command_type, data=data)
        try:
            # Map common system command types to proper API actions
            api_action = command_type
            api_object = "None"
            
            # Map command types to specific API actions and objects
            if command_type in ["status", "get_model_info"]:
                api_object = "llm"
            elif command_type == "reboot":
                api_object = "system"
                
            # Create system command in proper format
            command_dict = {
                "request_id": f"sys_{command_type}_{int(time.time())}",
                "work_id": "sys",
                "action": api_action,
                "object": api_object,
                "data": data if data else None  # Use None instead of "None" string
            }
            
            # Send command
            journaling_manager.recordInfo(f"Sending system command: {command_dict}")
            response = await cls.transmit_json(command_dict)
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
            # For ADB mode - using port forwarding to localhost:5555
            elif mode == "adb":
                journaling_manager.recordInfo("Setting up ADB connection over port forwarding...")
                
                if cls._is_adb_available():
                    # Check if port forwarding is already set up
                    result = subprocess.run(
                        ["adb", "forward", "--list"],
                        capture_output=True, 
                        text=True
                    )
                    if result.returncode == 0:
                        forwarding_set = "tcp:5555 tcp:5555" in result.stdout
                        journaling_manager.recordInfo(f"Port forwarding status: {'set up' if forwarding_set else 'not set up'}")
                        
                        # Set up port forwarding if not already established
                        if not forwarding_set:
                            journaling_manager.recordInfo("Setting up port forwarding tcp:5555 -> tcp:5555")
                            setup_result = subprocess.run(
                                ["adb", "forward", "tcp:5555", "tcp:5555"],
                                capture_output=True,
                                text=True
                            )
                            if setup_result.returncode != 0:
                                raise Exception(f"Failed to set up ADB port forwarding: {setup_result.stderr}")
                            journaling_manager.recordInfo("Port forwarding established successfully")
                    
                    # Use localhost:5555 for the connection
                    cls._serial_port = "127.0.0.1:5555"
                    cls._connection_type = "wifi"  # Use wifi implementation for socket connection
                    journaling_manager.recordInfo(f"Using ADB port forwarding at {cls._serial_port}")
                else:
                    raise Exception("ADB not available")
            else:  # serial mode
                journaling_manager.recordInfo(f"Setting up serial connection...")
                
                if cls._is_serial_available():
                    cls._serial_port = cls._find_serial_port()
                    if cls._serial_port:
                        cls._connection_type = "serial"
                        journaling_manager.recordInfo(f"Found serial port: {cls._serial_port}")
                    else:
                        raise Exception("No suitable serial port found")
                else:
                    raise Exception("No serial ports available")
            
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
            
            # Test the connection first
            journaling_manager.recordInfo("\nTesting connection...")
            ping_command = {
                "request_id": "sys_ping",
                "work_id": "sys",
                "action": "ping",
                "object": "system",
                "data": None
            }
            
            try:
                response = await cls.transmit_json(ping_command)
                journaling_manager.recordInfo(f"Connection test response: {response}")
                
                # Only continue with reset if ping succeeds
                if response and not response.get("error", {}).get("code", 0):
                    # Perform service reset (only on initial boot)
                    journaling_manager.recordInfo("\nPerforming initial service reset...")
                    reset_command = {
                        "request_id": "initial_reset",
                        "work_id": "sys",
                        "action": "reset",
                        "object": "llm",
                        "data": None
                    }
                    reset_response = await cls.transmit_json(reset_command)
                    journaling_manager.recordInfo(f"Service reset response: {reset_response}")
                    
                    # Brief pause to allow reset to complete
                    await asyncio.sleep(1)
                else:
                    journaling_manager.recordError("Ping test failed, skipping reset")
            except Exception as e:
                journaling_manager.recordError(f"Connection test failed: {e}")
                journaling_manager.recordError("Continuing without reset")
            
            # Get model info
            journaling_manager.recordInfo("\nGetting model info...")
            model_info_command = {
                "request_id": "sys_model_info",
                "work_id": "sys",
                "action": "lsmode",
                "object": "system",
                "data": None
            }
            
            try:
                model_info_response = await cls.transmit_json(model_info_command)
                journaling_manager.recordInfo(f"Model info response: {model_info_response}")
                
                # Parse and store available models
                if model_info_response and not model_info_response.get("error", {}).get("code", 0):
                    models_data = model_info_response.get("data", [])
                    if isinstance(models_data, list):
                        cls.available_models = models_data
                        
                        # Find LLM models and set default if found
                        llm_models = [model for model in models_data 
                                     if model.get("type", "").lower() == "llm" or 
                                     (isinstance(model.get("capabilities", []), list) and 
                                      any(cap in ["text_generation", "chat"] for cap in model.get("capabilities", [])))]
                        
                        if llm_models:
                            # Use the first LLM model as default
                            cls.default_llm_model = llm_models[0].get("mode", cls.default_llm_model)
                            journaling_manager.recordInfo(f"Set default LLM model to: {cls.default_llm_model}")
                        else:
                            journaling_manager.recordInfo(f"No LLM models found, using default: {cls.default_llm_model}")
                    else:
                        journaling_manager.recordError(f"Unexpected models data format: {models_data}")
            except Exception as e:
                journaling_manager.recordError(f"Model info check failed: {e}")
            
            # Get hardware info
            journaling_manager.recordInfo("\nGetting hardware info...")
            try:
                hw_info = await cls.get_hardware_info()
                journaling_manager.recordInfo(f"Hardware info: {hw_info}")
                # Store the hardware info in a class variable for later use
                cls.current_hw_info = hw_info
            except Exception as e:
                journaling_manager.recordError(f"Hardware info check failed: {e}")
                cls.current_hw_info = {
                    "cpu_load": "N/A",
                    "memory_usage": "N/A",
                    "temperature": "N/A",
                    "timestamp": int(time.time())
                }
            
            # Successfully initialized
            journaling_manager.recordInfo("\nM5Stack LLM Module connected and initialized successfully")
                        
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
                    
                    # Additional debug info for ADB connections
                    if ip == "127.0.0.1" and cls._connection_type == "wifi":
                        journaling_manager.recordInfo("This is an ADB connection over port forwarding")
                        journaling_manager.recordInfo("Ensure the device is connected and port forwarding is set up")
                        
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
                        # Don't try to modify the response format - just return it directly
                        journaling_manager.recordDebug(f"Received valid JSON response: {response}")
                        return response
                    except json.JSONDecodeError:
                        journaling_manager.recordError(f"Failed to parse JSON: {buffer.strip()}")
                        return {
                            "request_id": command_data.get("request_id", f"error_{int(time.time())}"),
                            "work_id": command_data.get("work_id", "sys"),
                            "data": "None",
                            "error": {"code": -1, "message": "Failed to parse response"},
                            "object": command_data.get("object", "None"),
                            "created": int(time.time())
                        }
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

    @classmethod
    def _parse_response(cls, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse response from M5Stack LLM module according to API format"""
        try:
            # M5Stack API response format has these fields:
            # {
            #   "created": timestamp,
            #   "data": data_content,
            #   "error": {"code": code, "message": "message"},
            #   "object": "object_name",
            #   "request_id": "request_id",
            #   "work_id": "work_id"
            # }
            
            # Check if this is already a valid M5Stack API response
            if all(k in response for k in ["request_id", "work_id"]):
                # Check if there's an error
                if response.get("error") and (
                    response["error"].get("code", 0) != 0 or response["error"].get("message", "")
                ):
                    journaling_manager.recordError(f"API error: {response['error']}")
                
                # Return the original response
                return response
                
            # For any other format, try to convert to M5Stack format
            timestamp = int(time.time())
            formatted_response = {
                "request_id": response.get("request_id", f"resp_{timestamp}"),
                "work_id": response.get("work_id", "sys"),
                "data": response.get("data", None),  # Use None instead of response as default
                "error": {"code": 0, "message": ""},
                "object": response.get("object", "None"),
                "created": timestamp
            }
            
            # Check if there was an error message in a non-standard format
            if "error" in response or "exception" in response:
                error_msg = response.get("error", response.get("exception", "Unknown error"))
                error_code = -1
                
                if isinstance(error_msg, dict):
                    error_code = error_msg.get("code", -1)
                    error_msg = error_msg.get("message", str(error_msg))
                
                formatted_response["error"] = {
                    "code": error_code,
                    "message": str(error_msg)
                }
            
            return formatted_response
            
        except Exception as e:
            journaling_manager.recordError(f"Error parsing response: {e}")
            return {
                "request_id": f"error_{int(time.time())}",
                "work_id": "sys",
                "data": "None",
                "error": {"code": -1, "message": f"Failed to parse response: {str(e)}"},
                "object": "None",
                "created": int(time.time())
            } 

    @classmethod
    async def clear_and_reset(cls) -> Dict[str, Any]:
        """Public method to manually reset the LLM state if needed"""
        journaling_manager.recordInfo("\nManually resetting LLM state...")
        
        results = {}
        
        # Reset LLM
        try:
            reset_command = {
                "request_id": "manual_reset_llm",
                "work_id": "sys",
                "action": "reset",
                "object": "llm",
                "data": None
            }
            reset_response = await cls.transmit_json(reset_command)
            journaling_manager.recordInfo(f"LLM reset response: {reset_response}")
            results["llm_reset"] = "success"
            
            # Brief pause to allow reset to complete
            await asyncio.sleep(1)
        except Exception as e:
            journaling_manager.recordError(f"Error resetting LLM: {e}")
            results["llm_reset"] = f"failed: {str(e)}"
            
        # Get hardware info after reset
        try:
            journaling_manager.recordInfo("\nGetting hardware info after reset...")
            hw_info = await cls.get_hardware_info()
            journaling_manager.recordInfo(f"Hardware info after reset: {hw_info}")
            cls.current_hw_info = hw_info
            results["hardware_info"] = hw_info
            
            # Format hardware info for display
            formatted_info = cls.format_hw_info()
            results["formatted_info"] = formatted_info
        except Exception as e:
            journaling_manager.recordError(f"Error getting hardware info after reset: {e}")
            results["hardware_info"] = f"failed: {str(e)}"
            
        return results

    @classmethod
    async def get_hardware_info(cls) -> Dict[str, Any]:
        """Get hardware information (CPU load, memory usage, temperature) from the device"""
        journaling_manager.recordInfo("\nRetrieving hardware information...")
        
        try:
            hw_info_command = {
                "request_id": f"hwinfo_{int(time.time())}",
                "work_id": "sys",
                "action": "hwinfo",
                "object": "system",
                "data": None
            }
            
            # Send the hardware info command
            response = await cls.transmit_json(hw_info_command)
            journaling_manager.recordInfo(f"Hardware info response: {response}")
            
            # Get IP address from connection
            ip_address = "N/A"
            if cls._connection_type == "wifi" and cls._serial_port:
                ip_address = cls._serial_port.split(":")[0]
            
            # Parse the response
            if response and "data" in response:
                # Initialize hardware info with default values
                hw_info = {
                    "cpu_load": "N/A",
                    "memory_usage": "N/A",
                    "temperature": "N/A",
                    "ip_address": ip_address,
                    "timestamp": int(time.time())
                }
                
                data = response.get("data", "")
                journaling_manager.recordInfo(f"Raw hardware info data: {data}")
                
                # Check if data is a dictionary (JSON format)
                if isinstance(data, dict):
                    # Extract CPU load - use cpu_loadavg field
                    if "cpu_loadavg" in data:
                        hw_info["cpu_load"] = data["cpu_loadavg"]
                    elif "cpu_load" in data:
                        hw_info["cpu_load"] = data["cpu_load"]
                    
                    # Extract memory usage - use mem field
                    if "mem" in data:
                        hw_info["memory_usage"] = data["mem"]
                    elif "memory" in data:
                        hw_info["memory_usage"] = data["memory"]
                    
                    # Extract temperature - convert if too high
                    if "temperature" in data:
                        temp_value = data["temperature"]
                        if isinstance(temp_value, (int, float)):
                            # Check if value is too high for Celsius
                            if temp_value > 100:  # Most temperatures over 100 are likely in deci-Celsius
                                # Convert from deci-Celsius to Celsius
                                temp_value = temp_value / 100
                            hw_info["temperature"] = f"{temp_value:.1f}"
                        else:
                            hw_info["temperature"] = temp_value
                
                # Check if data is a string (older format)
                elif isinstance(data, str):
                    # Extract CPU load
                    if "cpu_loadavg" in data:
                        cpu_match = re.search(r"cpu_loadavg\(([^)]+)\)", data)
                        if cpu_match:
                            hw_info["cpu_load"] = cpu_match.group(1)
                    
                    # Extract memory usage
                    if "mem" in data:
                        mem_match = re.search(r"mem\(([^)]+)\)", data)
                        if mem_match:
                            hw_info["memory_usage"] = mem_match.group(1)
                    
                    # Extract temperature
                    if "temperature" in data:
                        temp_match = re.search(r"temperature\(([^)]+)\)", data)
                        if temp_match:
                            temp_value = temp_match.group(1)
                            try:
                                temp_float = float(temp_value.replace("°C", "").strip())
                                if temp_float > 100:
                                    temp_float = temp_float / 10
                                hw_info["temperature"] = f"{temp_float:.1f}"
                            except ValueError:
                                hw_info["temperature"] = temp_value
                
                # Ensure values have appropriate units if not already included
                if hw_info["cpu_load"] != "N/A" and "%" not in str(hw_info["cpu_load"]):
                    hw_info["cpu_load"] = f"{hw_info['cpu_load']}%"
                if hw_info["memory_usage"] != "N/A" and "%" not in str(hw_info["memory_usage"]):
                    hw_info["memory_usage"] = f"{hw_info['memory_usage']}%"
                if hw_info["temperature"] != "N/A" and "°C" not in str(hw_info["temperature"]):
                    hw_info["temperature"] = f"{hw_info['temperature']}°C"
                
                journaling_manager.recordInfo(f"Parsed hardware info: {hw_info}")
                
                # Update the current_hw_info
                cls.current_hw_info = hw_info
                return hw_info
            else:
                journaling_manager.recordError("Failed to retrieve hardware info")
                return {
                    "cpu_load": "N/A",
                    "memory_usage": "N/A",
                    "temperature": "N/A",
                    "ip_address": ip_address,
                    "timestamp": int(time.time())
                }
                
        except Exception as e:
            journaling_manager.recordError(f"Error retrieving hardware info: {e}")
            # Get IP address from connection
            ip_address = "N/A"
            if cls._connection_type == "wifi" and cls._serial_port:
                ip_address = cls._serial_port.split(":")[0]
                
            return {
                "cpu_load": "N/A",
                "memory_usage": "N/A",
                "temperature": "N/A",
                "ip_address": ip_address,
                "error": str(e),
                "timestamp": int(time.time())
            }

    @classmethod
    async def reboot_device(cls) -> Dict[str, Any]:
        """Send a reboot command to fully restart the M5Stack system
        Note: This is a hard reboot - use with caution, as it will cause device to reconnect
        """
        journaling_manager.recordInfo("\nSending reboot command to device...")
        
        try:
            # Reboot command uses different object than reset
            reboot_command = {
                "request_id": f"reboot_{int(time.time())}",
                "work_id": "sys",
                "action": "reboot",
                "object": "system",  # Important: system object, not llm
                "data": None
            }
            
            # Send reboot command
            response = await cls.transmit_json(reboot_command)
            journaling_manager.recordInfo(f"Reboot command response: {response}")
            
            # Device will disconnect after reboot
            journaling_manager.recordInfo("Device is rebooting, connection will be lost")
            
            # Reset our connection state
            cls._initialized = False
            
            return {
                "success": True,
                "message": "Reboot command sent. Device is restarting.",
                "response": response
            }
        except Exception as e:
            journaling_manager.recordError(f"Error sending reboot command: {e}")
            return {
                "success": False,
                "message": f"Failed to reboot device: {str(e)}",
                "error": str(e)
            } 

    @classmethod
    def format_hw_info(cls) -> str:
        """Format hardware info for display at the start of chat
        Returns a formatted string with hardware info that can be displayed
        in the chat UI.
        """
        hw = cls.current_hw_info
        
        # Format timestamp as readable time
        timestamp = hw.get("timestamp", 0)
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp)) if timestamp else "N/A"
        
        # Get IP address
        ip_address = hw.get("ip_address", "N/A")
        ip_display = f"IP: {ip_address} | " if ip_address != "N/A" else ""
        
        # Format the hardware info in the requested format
        info_str = f"""~
{ip_display}CPU: {hw.get('cpu_load', 'N/A')} | Memory: {hw.get('memory_usage', 'N/A')} | Temp: {hw.get('temperature', 'N/A')} | Updated: {time_str}
~"""
        
        return info_str

    @classmethod
    async def set_active_model(cls, model_name: str) -> Dict[str, Any]:
        """Set the active model for LLM inference
        
        Args:
            model_name: The name of the model to activate
            
        Returns:
            Dictionary with result of the operation
        """
        journaling_manager.recordInfo(f"\nSetting active model to: {model_name}")
        
        try:
            # Prepare command to set model
            set_model_command = {
                "request_id": f"set_model_{int(time.time())}",
                "work_id": "sys",
                "action": "setmode",
                "object": "system",
                "data": model_name
            }
            
            # Send command
            response = await cls.transmit_json(set_model_command)
            journaling_manager.recordInfo(f"Set model response: {response}")
            
            # Check for success
            if response and not response.get("error", {}).get("code", 0):
                return {
                    "success": True,
                    "message": f"Successfully set active model to {model_name}",
                    "response": response
                }
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                return {
                    "success": False,
                    "message": f"Failed to set model: {error_msg}",
                    "response": response
                }
                
        except Exception as e:
            journaling_manager.recordError(f"Error setting active model: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            } 

    @classmethod
    async def get_active_model(cls) -> Dict[str, Any]:
        """Get information about the currently active model
        
        Returns:
            Dictionary with active model information
        """
        journaling_manager.recordInfo("\nGetting active model information...")
        
        try:
            # Prepare command to get active model
            get_model_command = {
                "request_id": f"get_active_model_{int(time.time())}",
                "work_id": "sys",
                "action": "getmode",
                "object": "system",
                "data": None
            }
            
            # Send command
            response = await cls.transmit_json(get_model_command)
            journaling_manager.recordInfo(f"Get active model response: {response}")
            
            # Check for success
            if response and not response.get("error", {}).get("code", 0):
                active_model = {
                    "success": True,
                    "model": response.get("data", "Unknown")
                }
                
                if isinstance(active_model["model"], dict):
                    # Response is a full model object
                    return active_model
                elif isinstance(active_model["model"], str):
                    # Response is just the model name, try to get full details
                    models = await cls.get_available_models()
                    
                    # Find the matching model
                    for model in models:
                        if model.get("model") == active_model["model"]:
                            active_model["details"] = model
                            break
                    
                    return active_model
                else:
                    return {
                        "success": True,
                        "model": "Unknown",
                        "message": "Could not parse active model information"
                    }
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                return {
                    "success": False,
                    "message": f"Failed to get active model: {error_msg}",
                    "response": response
                }
                
        except Exception as e:
            journaling_manager.recordError(f"Error getting active model: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }
    
    @classmethod
    async def get_available_models(cls) -> List[Dict[str, Any]]:
        """Get the list of available models
        
        Returns:
            List of model dictionaries with model information
        """
        journaling_manager.recordInfo("\nGetting available models...")
        
        # Return cached models if available
        if cls.available_models:
            journaling_manager.recordInfo(f"Using cached models ({len(cls.available_models)} available)")
            return cls.available_models
        
        try:
            # Prepare command to get models
            model_info_command = {
                "request_id": f"get_models_{int(time.time())}",
                "work_id": "sys",
                "action": "lsmode",
                "object": "system",
                "data": None
            }
            
            # Send command
            response = await cls.transmit_json(model_info_command)
            journaling_manager.recordInfo(f"Get models response: {response}")
            
            # Check for success and parse models
            if response and not response.get("error", {}).get("code", 0):
                models_data = response.get("data", [])
                
                if isinstance(models_data, list):
                    # Cache the models for future use
                    cls.available_models = models_data
                    
                    # Find LLM models and set default if found
                    llm_models = [model for model in models_data 
                                if model.get("type", "").lower() == "llm" or 
                                (isinstance(model.get("capabilities", []), list) and 
                                any(cap in ["text_generation", "chat"] for cap in model.get("capabilities", [])))]
                    
                    if llm_models:
                        # Use the first LLM model as default
                        cls.default_llm_model = llm_models[0].get("mode", cls.default_llm_model)
                        journaling_manager.recordInfo(f"Set default LLM model to: {cls.default_llm_model}")
                    
                    return cls.available_models
                else:
                    journaling_manager.recordError(f"Unexpected models data format: {models_data}")
                    return []
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                journaling_manager.recordError(f"Failed to get models: {error_msg}")
                return []
                
        except Exception as e:
            journaling_manager.recordError(f"Error getting models: {e}")
            return [] 