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
from Mind.CorpusCallosum.transport_layer import get_transport, ConnectionError, CommandError, run_adb_command

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
    _transport = None
    _active_operation = False  # Tracks if an operation is in progress
    _final_shutdown = False    # Indicates this is the final application shutdown
    
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
    async def initialize(cls, connection_type=None):
        """Initialize the SynapticPathways system"""
        journaling_manager.recordInfo(f"Initializing SynapticPathways with connection type: {connection_type}")
        
        # If already initialized with the same transport type, don't reinitialize
        if cls._initialized and cls._transport and connection_type == cls._connection_type:
            journaling_manager.recordInfo(f"Already initialized with {connection_type} - reusing connection")
            return True
        
        # If connection type is specified, set device mode
        if connection_type:
            await cls.set_device_mode(connection_type)
            return cls._initialized
        
        # Try to use existing connection if available
        if cls._connection_type:
            journaling_manager.recordInfo(f"Using existing connection mode: {cls._connection_type}")
            if not cls._initialized:
                await cls.set_device_mode(cls._connection_type)
                return cls._initialized
        
        # No connection specified and none exists
        journaling_manager.recordError("No connection type specified and no existing connection")
        return False

    @classmethod
    async def set_device_mode(cls, mode: str) -> None:
        """Initialize the connection in the requested mode (serial, adb, or tcp)"""
        if mode not in ["serial", "adb", "tcp", "wifi"]:
            raise ValueError("Invalid mode. Use 'serial', 'adb', or 'tcp'")
        
        # Convert 'wifi' to 'tcp' for backward compatibility
        if mode == "wifi":
            mode = "tcp"
            journaling_manager.recordInfo("Converting 'wifi' mode to 'tcp' for clarity")
        
        journaling_manager.recordInfo(f"\nInitializing {mode} connection...")
        
        # Only cleanup if we're switching modes or not initialized
        if cls._connection_type != mode or not cls._initialized:
            journaling_manager.recordInfo(f"Cleaning up existing connections before establishing new {mode} connection...")
            await cls.cleanup()
        else:
            journaling_manager.recordInfo(f"Reusing existing {mode} connection - skipping cleanup")
        
        try:
            # Get appropriate transport
            journaling_manager.recordInfo(f"Creating {mode} transport...")
            cls._transport = get_transport(mode)
            cls._connection_type = mode  # Set connection type before connect attempt
            
            # Try to connect
            connect_start = time.time()
            connection_successful = await cls._transport.connect()
            connect_time = time.time() - connect_start
            
            if connection_successful:
                journaling_manager.recordInfo(f"{mode.capitalize()} connection established in {connect_time:.2f} seconds")
                
                # Test the connection with ping_system instead of transport.test_connection
                try:
                    journaling_manager.recordInfo(f"Testing {mode} connection...")
                    test_start = time.time()
                    connection_tested = await cls.ping_system()  # Use existing ping_system method
                    test_time = time.time() - test_start
                    
                    if connection_tested:
                        journaling_manager.recordInfo(f"{mode.capitalize()} connection tested successfully in {test_time:.2f} seconds")
                    else:
                        journaling_manager.recordWarning(f"{mode.capitalize()} connection test failed, but continuing anyway")
                except Exception as e:
                    journaling_manager.recordWarning(f"Connection test failed but continuing: {e}")
                    connection_tested = True  # Assume it works anyway
                
                # Set as initialized
                cls._initialized = True
                cls._connection_type = mode
                
                # Populate initial hardware info and models
                try:
                    journaling_manager.recordInfo("Getting initial hardware info...")
                    cls.current_hw_info = await cls.get_hardware_info()
                except Exception as e:
                    journaling_manager.recordWarning(f"Failed to get hardware info: {e}")
                
                try:
                    journaling_manager.recordInfo("Getting available models...")
                    cls.available_models = await cls.get_available_models()
                except Exception as e:
                    journaling_manager.recordWarning(f"Failed to get models: {e}")
                
                journaling_manager.recordInfo(f"{mode.capitalize()} connection setup complete!")
                return
            else:
                journaling_manager.recordError(f"Failed to establish {mode} connection after {connect_time:.2f} seconds")
                
                # If TCP connection failed and it wasn't already a retry with discovered IP,
                # the WiFiTransport.connect() method already tried ADB discovery and retried TCP
                if mode == "tcp":
                    # Both the initial TCP attempt and the ADB-discovered IP attempt failed
                    # Ask the user if they want to try ADB mode
                    try:
                        print("\n=========================================")
                        print("TCP connection failed with configured IP and with ADB-discovered IP.")
                        print("Would you like to try connecting via ADB mode instead? [Y/n]")
                        choice = input("Enter choice: ").strip().lower()
                        
                        # Default to yes if empty or 'y'
                        if not choice or choice.startswith('y'):
                            journaling_manager.recordInfo("User chose to try ADB mode as fallback")
                            # Clean up failed TCP transport
                            if cls._transport:
                                await cls._transport.disconnect()
                            
                            # Try ADB mode
                            await cls.set_device_mode("adb")
                            return
                        else:
                            journaling_manager.recordInfo("User chose not to try ADB mode")
                            print("Connection failed. Please check your device and try again.")
                    except Exception as e:
                        journaling_manager.recordError(f"Error during user prompt: {e}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error initializing {mode} connection: {e}")
            
            # If TCP connection failed with an exception, ask if user wants to try ADB
            if mode == "tcp":
                try:
                    print("\n=========================================")
                    print(f"TCP connection failed with error: {str(e)}")
                    print("Would you like to try connecting via ADB mode instead? [Y/n]")
                    choice = input("Enter choice (default: Y): ").strip().lower()
                    
                    # Default to yes if empty or 'y'
                    if not choice or choice.startswith('y'):
                        journaling_manager.recordInfo("User chose to try ADB mode after TCP error")
                        # Clean up if needed
                        if cls._transport:
                            await cls._transport.disconnect()
                        
                        # Try ADB mode
                        await cls.set_device_mode("adb")
                        return
                    else:
                        journaling_manager.recordInfo("User chose not to try ADB mode")
                        print("Connection failed. Please check your device and try again.")
                except Exception as prompt_err:
                    journaling_manager.recordError(f"Error during user prompt: {prompt_err}")

    @classmethod
    async def cleanup(cls) -> None:
        """Clean up resources before establishing a new connection or shutting down"""
        if not cls._initialized or not cls._transport:
            # Nothing to clean up
            return
        
        try:
            # Disconnect the transport
            journaling_manager.recordInfo(f"Disconnecting {cls._connection_type} transport...")
            await cls._transport.disconnect()
            journaling_manager.recordInfo("Transport disconnected successfully")
        except Exception as e:
            journaling_manager.recordError(f"Error during transport cleanup: {e}")
        
        # Reset state
        cls._transport = None
        cls._initialized = False
        cls._connection_type = None
        cls._mode = None
        journaling_manager.recordInfo("Synaptic pathways cleaned up")

    @classmethod
    async def transmit_json(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Transmit a command as JSON and get response"""
        if not cls._initialized or not cls._transport:
            raise ConnectionError("Transport not initialized")
        
        try:
            # Mark operation as active
            cls._active_operation = True
            
            # Log the command type
            command_type = command.get("action")
            journaling_manager.recordInfo(f"Command type: {command_type}")
            
            # Log the full JSON request at debug level
            journaling_manager.recordDebug(f"[JSON REQUEST] {json.dumps(command)}")
            
            # Transmit the command
            response = await cls._transport.transmit(command)
            
            # Log the full JSON response at debug level
            journaling_manager.recordDebug(f"[JSON RESPONSE] {json.dumps(response)}")
            
            return response
        except Exception as e:
            journaling_manager.recordError(f"Error in transmit_json: {e}")
            # Get detailed error information
            error_details = traceback.format_exc()
            journaling_manager.recordError(f"Error details: {error_details}")
            raise CommandTransmissionError(f"Failed to transmit command: {e}")
        finally:
            # Mark operation as complete
            cls._active_operation = False

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
                    "work_id": "llm",
                    "action": "setup",
                    "object": "llm.setup",
                    "data": {
                        "model": setup_data.get("model", "qwen2.5-0.5b"),
                        "response_format": "llm.utf-8.stream",
                        "input": "llm.utf-8.stream",
                        "enoutput": True,
                        "enkws": True,
                        "max_token_len": 127
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
                        "input": prompt
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
    def register_command_handler(cls, command_type: CommandType, handler: "Callable") -> None:
        """Register a handler for a specific command type"""
        cls._command_handlers[command_type] = handler
        journaling_manager.recordInfo(f"Registered handler for {command_type}")

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
    async def get_hardware_info(cls) -> Dict[str, Any]:
        """Get hardware information (CPU load, memory usage, temperature) from the device"""
        journaling_manager.recordInfo("\nRetrieving hardware information...")
        
        # Return cached info if not connected
        if not cls._initialized:
            journaling_manager.recordInfo("System not initialized - hardware info not available")
            return cls.current_hw_info
        
        if not cls._transport:
            journaling_manager.recordInfo("Transport layer not initialized - creating it now")
            # Try to create the transport if it's null but we're supposed to be initialized
            if cls._connection_type:
                try:
                    cls._transport = get_transport(cls._connection_type)
                    if not await cls._transport.connect():
                        journaling_manager.recordError(f"Failed to connect with {cls._connection_type}")
                        return cls.current_hw_info
                except Exception as e:
                    journaling_manager.recordError(f"Error creating transport: {e}")
                    return cls.current_hw_info
            else:
                journaling_manager.recordInfo("No connection type specified - using cached info")
                return cls.current_hw_info
        
        try:
            # Create hardware info command according to the API spec
            hw_info_command = {
                "request_id": f"hwinfo_{int(time.time())}",
                "work_id": "sys",
                "action": "hwinfo",  
                "object": "system"
            }
            
            # Send command with error handling
            journaling_manager.recordInfo(f"Sending hardware info request via {cls._connection_type}...")
            response = await cls.transmit_json(hw_info_command)
            
            # Guard against None response
            if response is None:
                journaling_manager.recordError("Received None response from hardware info request")
                return cls.current_hw_info
            
            # Debug the response
            journaling_manager.recordInfo(f"Hardware info response type: {type(response)}")
            if isinstance(response, dict):
                journaling_manager.recordInfo(f"Response keys: {list(response.keys())}")
            else:
                journaling_manager.recordInfo(f"Response: {response}")
            
            # Parse the response with better error handling
            if response and isinstance(response, dict) and "data" in response:
                data = response.get("data", {})
                
                # Guard against None data
                if data is None:
                    data = {}
                    journaling_manager.recordWarning("Received None in data field, using empty dict")
                
                # Get IP address
                ip_address = "N/A"
                if cls._connection_type == "tcp" and hasattr(cls._transport, 'ip'):
                    ip_address = cls._transport.ip
                elif "eth_info" in data and isinstance(data["eth_info"], list) and len(data["eth_info"]) > 0:
                    eth_info = data["eth_info"][0]
                    if "ip" in eth_info:
                        ip_address = eth_info["ip"]
                
                # Create hardware info dict with proper key names from actual response
                hw_info = {
                    "cpu_load": f"{data.get('cpu_loadavg', 0)}%",  # Use cpu_loadavg
                    "memory_usage": f"{data.get('mem', 0)}%",  # Use mem
                    "temperature": f"{float(data.get('temperature', 0))/1000:.1f}°C",  # Temperature is in millidegrees C
                    "ip_address": ip_address,
                    "timestamp": int(time.time())
                }
                
                # Update cached hardware info
                cls.current_hw_info = hw_info
                journaling_manager.recordInfo(f"Updated hardware info: {hw_info}")
                return hw_info
            else:
                journaling_manager.recordError("Invalid hardware info response format")
                return cls.current_hw_info
        except Exception as e:
            journaling_manager.recordError(f"Error retrieving hardware info: {e}")
            import traceback
            journaling_manager.recordError(f"Stack trace: {traceback.format_exc()}")
            return cls.current_hw_info

    @classmethod
    def format_hw_info(cls) -> str:
        """Format hardware info for display at the start of chat"""
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
    async def get_available_models(cls) -> List[Dict[str, Any]]:
        """Get a list of available models from the device using lsmode command"""
        # Check if initialized
        if not cls._initialized or not cls._transport:
            journaling_manager.recordInfo("Transport not initialized, returning cached models")
            return cls.available_models
        
        journaling_manager.recordInfo("\nGetting available models with lsmode command...")
        
        try:
            # Create lsmode command per API spec
            lsmode_command = {
                "request_id": f"lsmode_{int(time.time())}",
                "work_id": "sys",
                "action": "lsmode",  # API uses lsmode, not get_model_info
                "object": "system"
            }
            
            # Send the command
            journaling_manager.recordInfo(f"Sending lsmode request via {cls._connection_type}...")
            response = await cls.transmit_json(lsmode_command)
            
            if response is None:
                journaling_manager.recordError("Received None response from lsmode request")
                return cls.available_models
            
            # Parse data array from response
            model_list = []
            
            if isinstance(response, dict) and "data" in response:
                data = response["data"]
                
                if isinstance(data, list):
                    journaling_manager.recordInfo(f"Found {len(data)} total models")
                    
                    # Process all models in the data array
                    for model_entry in data:
                        if not isinstance(model_entry, dict):
                            continue
                        
                        # Store the complete model entry directly without modifying field names
                        # This preserves the original field names like "mode" instead of renaming
                        model_list.append(model_entry)
                        
                        # Log the model 
                        journaling_manager.recordInfo(f"Added model: {model_entry.get('mode', 'Unknown')} (type: {model_entry.get('type', 'Unknown')}, capabilities: {', '.join(model_entry.get('capabilities', []))})")
            
            # Update available models if we found any
            if model_list:
                journaling_manager.recordInfo(f"Updated model cache with {len(model_list)} models")
                cls.available_models = model_list
                
                # Set default model if not already set - prefer LLM type models
                if not cls.default_llm_model:
                    # Try to find LLM models first
                    llm_models = [m for m in model_list if m.get("type", "").lower() == "llm"]
                    if llm_models:
                        cls.default_llm_model = llm_models[0].get("mode", "")
                        journaling_manager.recordInfo(f"Set default LLM model to: {cls.default_llm_model}")
                    elif model_list:
                        cls.default_llm_model = model_list[0].get("mode", "")
                        journaling_manager.recordInfo(f"No LLM models found, using first model: {cls.default_llm_model}")
                
                return model_list
            
            return cls.available_models
            
        except Exception as e:
            journaling_manager.recordError(f"Error retrieving model info: {e}")
            journaling_manager.recordError(f"Stack trace: {traceback.format_exc()}")
            return cls.available_models

    @classmethod
    async def set_active_model(cls, model_name: str) -> bool:
        """Set the active model for LLM operations"""
        journaling_manager.recordInfo(f"\nSetting active model to: {model_name}")
        
        if not cls._initialized:
            journaling_manager.recordError("Cannot set model - not connected")
            return False
        
        try:
            # Create model setup command
            setup_command = {
                "request_id": f"setup_{int(time.time())}",
                "work_id": "sys",
                "action": "setup",
                "object": "llm.setup",
                "data": {
                    "model": model_name,
                    "response_format": "llm.utf-8",
                    "input": "llm.utf-8",
                    "enoutput": True,
                    "enkws": False,
                    "max_token_len": 127,
                    "prompt": "You are a helpful assistant named Penphin."
                }
            }
            
            # Send setup command
            response = await cls.transmit_json(setup_command)
            journaling_manager.recordInfo(f"Model setup response: {response}")
            
            # Check if setup was successful
            if response and not response.get("error", {}).get("code", 0):
                cls.default_llm_model = model_name
                return True
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                journaling_manager.recordError(f"Failed to set active model: {error_msg}")
                return False
                
        except Exception as e:
            journaling_manager.recordError(f"Error setting active model: {e}")
            return False

    @classmethod
    async def reset_llm(cls) -> bool:
        """Reset the LLM system"""
        journaling_manager.recordInfo("\nResetting LLM...")
        
        if not cls._initialized:
            journaling_manager.recordError("Cannot reset LLM - not connected")
            return False
        
        try:
            # Create reset command in the correct format
            reset_command = {
                "request_id": f"reset_{int(time.time())}",
                "work_id": "sys",
                "action": "reset",
                "object": "system"  # Use "system" not "sys"
            }
            
            # Send reset command
            journaling_manager.recordInfo("Sending reset command...")
            response = await cls.transmit_json(reset_command)
            journaling_manager.recordInfo(f"Reset response: {response}")
            
            # Check if reset was successful - error code 0 means success
            if response and response.get("error", {}).get("code", -1) == 0:
                # API shows message will be "llm server restarting ..."
                message = response.get("error", {}).get("message", "")
                journaling_manager.recordInfo(f"Reset successful: {message}")
                
                # Clear model cache to force refresh
                cls.available_models = []
                cls.default_llm_model = ""
                
                # Wait a moment for the reset to complete
                await asyncio.sleep(3)
                
                return True
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                journaling_manager.recordError(f"Failed to reset LLM: {error_msg}")
                return False
        except Exception as e:
            journaling_manager.recordError(f"Error resetting LLM: {e}")
            return False
    
    @classmethod
    async def reboot_device(cls) -> bool:
        """Reboot the device"""
        journaling_manager.recordInfo("\nRebooting device...")
        
        if not cls._initialized:
            journaling_manager.recordError("Cannot reboot - not connected")
            return False
        
        try:
            # Create reboot command in the correct format
            reboot_command = {
                "request_id": f"reboot_{int(time.time())}",
                "work_id": "sys",
                "action": "reboot",
                "object": "system"  # Use "system" not "sys"
            }
            
            # Send reboot command
            journaling_manager.recordInfo("Sending reboot command...")
            try:
                response = await cls.transmit_json(reboot_command)
                journaling_manager.recordInfo(f"Reboot response: {response}")
                
                # API shows message will be "rebooting ..."
                if response and response.get("error", {}).get("code", -1) == 0:
                    message = response.get("error", {}).get("message", "")
                    journaling_manager.recordInfo(f"Reboot initiated: {message}")
                    
                    # Clean up connection since device will reboot
                    await cls.cleanup()
                    return True
                else:
                    error_msg = response.get("error", {}).get("message", "Unknown error")
                    journaling_manager.recordError(f"Failed to reboot device: {error_msg}")
                    return False
            except Exception:
                # If we get an exception after sending the reboot command,
                # it might be because the device is already rebooting
                journaling_manager.recordInfo("Connection lost after reboot command - device may be rebooting")
                
                # Clean up existing connection
                await cls.cleanup()
                return True
        except Exception as e:
            journaling_manager.recordError(f"Error rebooting device: {e}")
            return False

    @classmethod
    async def get_available_models_from_response(cls, response) -> List[Dict[str, Any]]:
        """Parse models from a response object - helper for testing and debugging"""
        # Implementation is the same as the parsing section in get_available_models
        # This can be used to reprocess a response without making another request
        # You can copy the parsing logic from above
        pass

    @classmethod
    async def final_shutdown(cls) -> None:
        """Final cleanup when application is exiting"""
        journaling_manager.recordInfo("Final application shutdown - cleaning up all resources")
        await cls.cleanup()
        journaling_manager.recordInfo("Cleanup complete - application can safely exit")

    @classmethod
    def _get_ip_address(cls) -> str:
        """Get IP address of the device"""
        try:
            # Get IP address based on connection type
            if cls._connection_type == "tcp":
                # For TCP, return the IP we're connected to
                ip = cls._transport.ip if hasattr(cls._transport, 'ip') else "N/A"
                return ip
            elif cls._connection_type == "adb":
                # For ADB, try to get device IP
                try:
                    output = run_adb_command(["shell", "ip", "addr", "show", "wlan0"])
                    match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
                    if match:
                        return match.group(1)
                except Exception:
                    pass
            # If we couldn't get IP based on connection type, try socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            journaling_manager.recordError(f"Error getting IP address: {e}")
            return "N/A"

    @classmethod
    async def ping_system(cls) -> bool:
        """Test the connection with a ping command"""
        journaling_manager.recordInfo("\nPinging system...")
        
        if not cls._initialized or not cls._transport:
            journaling_manager.recordError("Cannot ping - not connected")
            return False
        
        try:
            # Create ping command in the correct format
            ping_command = {
                "request_id": f"ping_{int(time.time())}",
                "work_id": "sys",
                "action": "ping",
                "object": "system",
                "data": None
            }
            
            # Send ping command
            response = await cls.transmit_json(ping_command)
            
            # Check for successful response
            if response and response.get("error", {}).get("code", -1) == 0:
                journaling_manager.recordInfo("Ping successful!")
                return True
            else:
                journaling_manager.recordError("Ping failed")
                return False
        except Exception as e:
            journaling_manager.recordError(f"Error pinging system: {e}")
            return False