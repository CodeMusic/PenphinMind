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
from Mind.Subcortex.BasalGanglia.basal_ganglia_integration import BasalGangliaIntegration
from Mind.Subcortex.BasalGanglia.tasks.display_visual_task import DisplayVisualTask

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
    _basal_ganglia = None
    _brain_mode = None  # Brain region mode from run.py (vc, ac, fc, full)
    _ui_mode = None     # UI mode for visualization (will be derived from brain mode)
    _cortex_communication_enabled = True  # Enable communication between cortices
    
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
        """
        Set the brain region mode from command line arguments
        
        Args:
            mode: Brain region mode ('vc', 'ac', 'fc', 'full')
        """
        if mode not in ["vc", "ac", "fc", "full"]:
            journaling_manager.recordWarning(f"Unknown brain mode: {mode}, defaulting to 'fc'")
            mode = "fc"
        
        cls._brain_mode = mode
        journaling_manager.recordInfo(f"Operational mode set to: {mode}")
        
        # Automatically derive the UI mode based on brain mode
        if mode == "full":
            cls._ui_mode = "full"  # Full pixel visualization for full brain mode
            cls._cortex_communication_enabled = True
            journaling_manager.recordInfo("UI mode set to 'full' with cortex communication enabled")
        elif mode == "fc":
            cls._ui_mode = "fc"  # Text visualization for frontal cortex mode
            journaling_manager.recordInfo("UI mode set to 'fc' (text visualization)")
        elif mode == "vc":
            cls._ui_mode = "full"  # Visual cortex mode should use full visualization
            journaling_manager.recordInfo("UI mode set to 'full' for visual cortex tests")
        else:
            cls._ui_mode = "headless"  # Headless for other modes
            journaling_manager.recordInfo("UI mode set to 'headless' (no visualization)")

    @classmethod
    async def initialize(cls, connection_type=None):
        """Initialize the SynapticPathways system."""
        journaling_manager.recordInfo(f"Initializing SynapticPathways with connection type: {connection_type}")
        
        try:
            # Get BG integration
            bg = cls.get_basal_ganglia()
            
            # Get communication task - use get_communication_task or direct _tasks access
            if hasattr(bg, "get_communication_task"):
                comm_task = bg.get_communication_task()
            else:
                # Fallback to direct task access if method doesn't exist
                comm_task = bg._tasks.get("CommunicationTask")
                if not comm_task:
                    # Create it if needed
                    from Mind.Subcortex.BasalGanglia.tasks.communication_task import CommunicationTask
                    comm_task = CommunicationTask(priority=1)
                    bg.add_task(comm_task)
            
            # Initialize communication
            if connection_type and comm_task:
                journaling_manager.recordInfo(f"Initializing communication with {connection_type}")
                success = await comm_task.initialize(connection_type)
                cls._initialized = success
                cls._connection_type = connection_type if success else None
                
                if success:
                    journaling_manager.recordInfo(f"Successfully connected using {connection_type}")
                    return True
            
            # Try existing connection
            elif cls._connection_type and comm_task:
                return await comm_task.initialize(cls._connection_type)
            
            # No connection specified
            else:
                journaling_manager.recordError("No connection type specified and no existing connection")
                return False
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing SynapticPathways: {e}")
            import traceback
            journaling_manager.recordError(f"Traceback: {traceback.format_exc()}")
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
            # Nothing to clean up in terms of transport
            pass
        else:
            try:
                # Disconnect the transport
                journaling_manager.recordInfo(f"Disconnecting {cls._connection_type} transport...")
                await cls._transport.disconnect()
                journaling_manager.recordInfo("Transport disconnected successfully")
            except Exception as e:
                journaling_manager.recordError(f"Error during transport cleanup: {e}")
                    
            # Shutdown BasalGanglia if it exists
            if cls._basal_ganglia:
                journaling_manager.recordInfo("Shutting down BasalGanglia task system")
                cls._basal_ganglia.shutdown()
                cls._basal_ganglia = None
        
        # Reset state
        cls._transport = None
        cls._initialized = False
        cls._connection_type = None
        cls._mode = None
        journaling_manager.recordInfo("Synaptic pathways cleaned up")

    @classmethod
    async def transmit_json(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transmit a command as JSON and get response using CommunicationTask
        
        This method is kept for backward compatibility but uses CommunicationTask
        """
        try:
            # Get communication task
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            # Send command
            return await comm_task.send_command(command)
            
        except Exception as e:
            journaling_manager.recordError(f"Error in transmit_json: {e}")
            raise CommandTransmissionError(f"Failed to transmit command: {e}")

    @classmethod
    async def send_command(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to the appropriate processor"""
        journaling_manager.recordInfo(f"\nProcessing command: {command}")
        
        command_type = command.get("type", "")
        command_action = command.get("command", "")
        
        # Handle LLM commands through BasalGanglia
        if command_type == "LLM":
            # Get a timestamp for request ID
            request_id = command.get("data", {}).get("request_id", f"llm_{int(time.time())}")
            
            # For setup commands, still use direct API as these configure the LLM system
            if command_action == "setup":
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
                
            # For actual generation, use the ThinkTask
            elif command_action == "generate":
                prompt = command.get("data", {}).get("prompt", "")
                # Use BasalGanglia for thinking tasks
                return await cls.think(prompt, stream=True)
            
            # Other LLM command types can be handled similarly
            else:
                # Continue with existing implementation for other actions
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
            # Use BasalGanglia for task management
            task = cls.get_basal_ganglia().system_command(command_type, data)
            
            # Wait for task to complete (this is a blocking operation)
            while task.active or not task.has_completed():
                await asyncio.sleep(0.1)
            
            # Return task result
            return task.result if task.result is not None else {"error": "Task completed with no result"}
            
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
            # If it's an LLM command, use the think task
            if command.command_type == CommandType.LLM:
                llm_command = command.to_dict()
                prompt = llm_command.get("data", {}).get("prompt", "")
                return await cls.think(prompt, stream=llm_command.get("data", {}).get("stream", False))
            
            # For other commands, use existing logic
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
    async def get_hardware_info(cls):
        """Get hardware information from the device"""
        try:
            # Create request with exact API format
            hwinfo_command = {
                "request_id": f"hwinfo_{int(time.time())}",
                "work_id": "sys",
                "action": "hwinfo"
            }
            
            # Send command
            journaling_manager.recordInfo("[SynapticPathways] 🐬 Requesting hardware info")
            response = await cls.transmit_json(hwinfo_command)
            
            # Check if response is valid before updating
            if response and not response.get("error", {}).get("code", 1):
                # Store in BOTH variables to ensure consistency
                cls.hardware_info = response.get("data", {})
                cls.current_hw_info = cls.hardware_info  # Sync both variables
                journaling_manager.recordInfo(f"[SynapticPathways] 🐧🐬 Updated hardware info: {cls.hardware_info}")
            else:
                error_msg = response.get("error", {}).get("message", "Unknown response format") if response else "No response"
                journaling_manager.recordWarning(f"[SynapticPathways] 🐧 Failed to get hardware info: {error_msg}")
                
            return cls.hardware_info
        except Exception as e:
            journaling_manager.recordError(f"[SynapticPathways] 🐧 Error getting hardware info: {e}")
            return {}

    @classmethod
    def format_hw_info(cls) -> str:
        """Format hardware info for display"""
        # Problem: You're using hardware_info but data is in current_hw_info
        hw = cls.hardware_info or {}
        
        # Extract values with proper defaults
        cpu = hw.get("cpu_loadavg", "N/A")
        mem = hw.get("mem", "N/A")
        temp_raw = hw.get("temperature", "N/A")
        
        # Format temperature properly - convert from millicelsius to celsius
        if isinstance(temp_raw, (int, float)) and temp_raw > 1000:
            temp = f"{temp_raw/1000:.1f}"
        else:
            temp = str(temp_raw)
        
        # Format network info
        net_info = ""
        if "eth_info" in hw and isinstance(hw["eth_info"], list) and len(hw["eth_info"]) > 0:
            eth = hw["eth_info"][0]  # Take first network interface
            ip = eth.get("ip", "N/A")
            net_info = f" | IP: {ip}"
        
        # Get update timestamp
        updated = time.strftime("%H:%M:%S") if hw else "N/A"
        
        # Format the hardware info string
        hw_info = f"🐧🐬 Hardware: CPU: {cpu}% | Memory: {mem}% | Temp: {temp}°C{net_info} | Updated: {updated}"
        return hw_info

    @classmethod
    async def get_available_models(cls) -> List[Dict[str, Any]]:
        """Get available models with proper error handling."""
        journaling_manager.recordInfo("[SynapticPathways] 🔍 Getting available models")
        
        try:
            # Get model management task
            bg = cls.get_basal_ganglia()
            
            if not bg:
                journaling_manager.recordError("[SynapticPathways] ❌ BasalGanglia not initialized")
                return cls.available_models
            
            # Get model task
            model_task = bg.get_model_management_task() if hasattr(bg, "get_model_management_task") else None
            
            if not model_task:
                journaling_manager.recordError("[SynapticPathways] ❌ ModelManagementTask not found")
                return cls.available_models
            
            # Request models
            journaling_manager.recordInfo("[SynapticPathways] 🔄 Requesting models from task")
            models = await model_task.get_available_models()
            
            # Check if we got models
            if models and len(models) > 0:
                journaling_manager.recordInfo(f"[SynapticPathways] ✅ Retrieved {len(models)} models")
                cls.available_models = models
                return models
            else:
                journaling_manager.recordWarning("[SynapticPathways] ⚠️ No models returned, using cached models")
            return cls.available_models
            
        except Exception as e:
            journaling_manager.recordError(f"[SynapticPathways] ❌ Error getting models: {e}")
            import traceback
            journaling_manager.recordError(f"[SynapticPathways] Stack trace: {traceback.format_exc()}")
            return cls.available_models

    @classmethod
    async def set_active_model(cls, model_name: str) -> bool:
        """Set active model using ModelManagementTask"""
        try:
            # Get model management task
            bg = cls.get_basal_ganglia()
            model_task = bg.get_model_management_task()
            
            # Set active model
            success = await model_task.set_active_model(model_name)
            
            # Update default model if successful
            if success:
                cls.default_llm_model = model_name
                
            return success
                
        except Exception as e:
            journaling_manager.recordError(f"Error setting active model: {e}")
            return False

    @classmethod
    async def reset_llm(cls) -> bool:
        """Reset LLM using ModelManagementTask"""
        try:
            # Get model management task
            bg = cls.get_basal_ganglia()
            model_task = bg.get_model_management_task()
            
            # Reset LLM
            return await model_task.reset_llm()
            
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
        """Test the connection with a ping command."""
        journaling_manager.recordInfo("\nPinging system...")
        
        if not cls._initialized:
            journaling_manager.recordError("Cannot ping - not connected")
            return False
        
        try:
            # Get the system command task using the correct method
            bg = cls.get_basal_ganglia()
            # Try both methods in case one exists
            if hasattr(bg, "get_system_command_task"):
                system_task = bg.get_system_command_task()
            elif hasattr(bg, "get_task"):
                system_task = bg.get_task("SystemCommandTask")
            else:
                # Direct access to _tasks if neither method exists
                system_task = bg._tasks.get("SystemCommandTask")
            
            if not system_task:
                journaling_manager.recordError("System command task not found")
                return False
            
            # Configure task for ping
            system_task.command = "ping"
            system_task.data = None
            system_task.completed = False
            system_task.active = True
            
            # Wait for task to complete
            max_wait = 5  # seconds
            start_time = time.time()
            
            while not system_task.completed and (time.time() - start_time) < max_wait:
                await asyncio.sleep(0.1)
            
            # Check result
            if system_task.completed and system_task.result:
                success = system_task.result.get("success", False)
                journaling_manager.recordInfo(f"Ping {'successful' if success else 'failed'}")
                return success
            else:
                journaling_manager.recordError("Ping timed out or failed")
                return False
            
        except Exception as e:
            journaling_manager.recordError(f"Error pinging system: {e}")
            import traceback
            journaling_manager.recordError(f"Ping traceback: {traceback.format_exc()}")
            return False

    @classmethod
    def get_basal_ganglia(cls):
        """Get or create the BasalGanglia instance."""
        if cls._basal_ganglia is None:
            journaling_manager.recordInfo("[SynapticPathways] 🏗️ Creating new BasalGanglia instance")
            
            # Import here to avoid circular imports
            from Mind.Subcortex.BasalGanglia.basal_ganglia_integration import BasalGangliaIntegration
            cls._basal_ganglia = BasalGangliaIntegration()
            
            # Verify initialization
            if hasattr(cls._basal_ganglia, "_tasks") and cls._basal_ganglia._tasks:
                task_names = list(cls._basal_ganglia._tasks.keys())
                journaling_manager.recordInfo(f"[SynapticPathways] ✅ BasalGanglia initialized with tasks: {task_names}")
            else:
                journaling_manager.recordWarning("[SynapticPathways] ⚠️ BasalGanglia may not be fully initialized")
        
        return cls._basal_ganglia

    @classmethod
    async def think(cls, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Use BasalGanglia to perform a thinking task with LLM"""
        journaling_manager.recordInfo(f"Initiating thinking task: {prompt[:50]}...")
        
        try:
            # Register thinking task
            task = cls.get_basal_ganglia().think(prompt, stream)
            
            # Wait for task to complete
            while task.active or not task.has_completed():
                await asyncio.sleep(0.1)
            
            # Return thinking result
            return task.result
        except Exception as e:
            journaling_manager.recordError(f"Error in thinking task: {e}")
            return {"error": str(e)}

    @classmethod
    def display_visual(cls, content: str = None, display_type: str = "text", 
                      visualization_type: str = None, visualization_params: dict = None) -> None:
        """
        Display visual content using BasalGanglia task system
        
        Args:
            content: Text content or image path to display
            display_type: Type of content ("text", "image", "animation")
            visualization_type: Special visualization type ("splash_screen", "game_of_life")
            visualization_params: Parameters for special visualizations
        """
        if visualization_type:
            journaling_manager.recordInfo(f"Registering {visualization_type} visualization task")
        else:
            journaling_manager.recordInfo(f"Registering display task for: {display_type}")
        
        # Register display task - non-blocking
        cls.get_basal_ganglia().display_visual(
            content=content, 
            display_type=display_type,
            visualization_type=visualization_type,
            visualization_params=visualization_params
        )

    @classmethod 
    def show_splash_screen(cls, title: str = "Penphin Mind", subtitle: str = "Neural Architecture") -> None:
        """Show application splash screen"""
        cls.display_visual(
            visualization_type="splash_screen",
            visualization_params={
                "title": title,
                "subtitle": subtitle
            }
        )
        
    @classmethod
    def run_game_of_life(cls, width: int = 20, height: int = 20, iterations: int = 10, 
                        initial_state: list = None) -> None:
        """Run Conway's Game of Life visualization"""
        cls.display_visual(
            visualization_type="game_of_life",
            visualization_params={
                "width": width,
                "height": height, 
                "iterations": iterations,
                "initial_state": initial_state
            }
        )

    @classmethod
    async def setup_llm(cls, model_name: str, params: dict = None) -> Dict[str, Any]:
        """Set up the LLM with specific parameters"""
        # This is a system operation since it configures the system
        data = {
            "model": model_name,
            **(params or {})
        }
        return await cls.send_system_command("setup", data)

    @classmethod
    async def run_llm_inference(cls, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Run inference with the LLM - this is a cognitive operation"""
        # This is a thinking operation, not a system command
        return await cls.think(prompt, stream)

    @classmethod
    async def think_with_pixel_grid(cls, prompt: str, 
                                   width: int = 64, 
                                   height: int = 64,
                                   color_mode: str = "grayscale") -> Dict[str, Any]:
        """
        Use BasalGanglia to perform a thinking task with LLM and visualize the output as a pixel grid
        
        Args:
            prompt: The prompt to send to the LLM
            width: Width of the pixel grid
            height: Height of the pixel grid
            color_mode: Visualization mode ('grayscale' or 'color')
        
        Returns:
            The final LLM response
        """
        journaling_manager.recordInfo(f"Initiating thinking task with pixel grid: {prompt[:50]}...")
        
        try:
            # Create pixel grid visualization task
            visual_task = cls.get_basal_ganglia().display_llm_pixel_grid(
                width=width,
                height=height,
                color_mode=color_mode
            )
            
            # Register thinking task
            task = cls.get_basal_ganglia().think(prompt, stream=True)
            
            # Continuously update visualization as we get results
            result = ""
            while task.active or not task.has_completed():
                if hasattr(task, 'result') and task.result:
                    # Update result and visualization if there's new content
                    if isinstance(task.result, str) and task.result != result:
                        result = task.result
                        # Update the visual task with new content
                        visual_task.update_stream(result)
                
                await asyncio.sleep(0.1)
            
            # Mark visualization as complete
            visual_task.update_stream(task.result, is_complete=True)
            
            # Return final thinking result
            return task.result
        except Exception as e:
            journaling_manager.recordError(f"Error in thinking task with pixel grid: {e}")
            return {"error": str(e)}

    @classmethod
    def create_llm_pixel_grid(cls, 
                             width: int = 64, 
                             height: int = 64,
                             wrap: bool = True,
                             color_mode: str = "grayscale") -> DisplayVisualTask:
        """
        Create an LLM token-to-pixel grid visualization task that can be updated manually
        
        Returns:
            The DisplayVisualTask instance that can be updated with update_stream()
        """
        return cls.get_basal_ganglia().display_llm_pixel_grid(
            width=width,
            height=height,
            wrap=wrap,
            color_mode=color_mode
        )

    @classmethod
    def create_llm_stream_visualization(cls, 
                                      highlight_keywords: bool = False,
                                      keywords: list = None,
                                      show_tokens: bool = False) -> DisplayVisualTask:
        """
        Create an LLM stream visualization task that can be updated manually
        
        Returns:
            The DisplayVisualTask instance that can be updated with update_stream()
        """
        return cls.get_basal_ganglia().display_llm_stream(
            highlight_keywords=highlight_keywords,
            keywords=keywords,
            show_tokens=show_tokens
        )

    @classmethod
    async def think_with_stream_visualization(cls, prompt: str, 
                                            highlight_keywords: bool = False,
                                            keywords: list = None,
                                            show_tokens: bool = False) -> Dict[str, Any]:
        """
        Use BasalGanglia to perform a thinking task with LLM and visualize the streaming output
        
        Args:
            prompt: The prompt to send to the LLM
            highlight_keywords: Whether to highlight keywords in the output
            keywords: List of keywords to highlight (if None, will be extracted from prompt)
            show_tokens: Whether to show token statistics
        
        Returns:
            The final LLM response
        """
        journaling_manager.recordInfo(f"Initiating thinking task with stream visualization: {prompt[:50]}...")
        
        try:
            # Extract keywords if not provided but highlighting is requested
            if highlight_keywords and not keywords:
                # Simple keyword extraction (in a real system, use NLP for better extraction)
                import re
                words = re.findall(r'\b[A-Za-z]{4,}\b', prompt)
                # Filter out common words
                common_words = {'what', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how'}
                keywords = [word for word in words if word.lower() not in common_words][:5]
                journaling_manager.recordInfo(f"Extracted keywords: {keywords}")
            
            # Create visualization task first
            visual_task = cls.get_basal_ganglia().display_llm_stream(
                highlight_keywords=highlight_keywords,
                keywords=keywords,
                show_tokens=show_tokens
            )
            
            # Register thinking task
            task = cls.get_basal_ganglia().think(prompt, stream=True)
            
            # Continuously update visualization as we get results
            result = ""
            while task.active or not task.has_completed():
                if hasattr(task, 'result') and task.result:
                    # Update result and visualization if there's new content
                    if isinstance(task.result, str) and task.result != result:
                        result = task.result
                        # Update the visual task with new content
                        visual_task.update_stream(result)
            
            await asyncio.sleep(0.1)
            
            # Mark visualization as complete
            visual_task.update_stream(task.result, is_complete=True)
            
            # Return final thinking result
            return task.result
        except Exception as e:
            journaling_manager.recordError(f"Error in thinking task with visualization: {e}")
            return {"error": str(e)}

    @classmethod
    def get_ui_mode(cls) -> str:
        """Get the current UI mode with fallback to fc"""
        if cls._ui_mode is None:
            # If UI mode not explicitly set, derive from brain mode
            if cls._brain_mode == "full":
                return "full"
            elif cls._brain_mode in ["fc", "vc"]:
                return "fc"
            else:
                return "headless"
        return cls._ui_mode

    @classmethod
    async def think_with_visualization(cls, prompt: str, 
                                      highlight_keywords: bool = False,
                                      keywords: list = None,
                                      show_tokens: bool = False) -> Dict[str, Any]:
        """
        Think with visualization based on current UI mode
        
        In full mode, enables communication between cortices (OccipitalLobe gets data from PrefrontalCortex)
        In fc mode, uses text stream visualization
        In headless mode, uses basic thinking without visualization
        
        Args:
            prompt: The prompt to send to the LLM
            highlight_keywords: Whether to highlight keywords (for text visualization)
            keywords: List of keywords to highlight
            show_tokens: Whether to show token statistics
            
        Returns:
            The thinking result
        """
        # Get UI mode based on current settings
        ui_mode = cls.get_ui_mode()
        journaling_manager.recordInfo(f"[CorpusCallosum] Thinking with visualization in {ui_mode} mode")
        
        try:
            # Select visualization based on mode
            if ui_mode == "full":
                # Full UI mode - use pixel grid visualization and enable cortex communication
                journaling_manager.recordInfo("[CorpusCallosum] Using pixel grid visualization with cortex communication")
                
                # Enable direct communication between OccipitalLobe and PrefrontalCortex
                if cls._cortex_communication_enabled:
                    occipital_area = None
                    
                    # Get the OccipitalLobe's visual processing area if registered
                    if "OccipitalLobe" in cls._integration_areas:
                        occipital_area = cls._integration_areas["OccipitalLobe"]
                        journaling_manager.recordInfo("[CorpusCallosum] OccipitalLobe integration area found")
                        
                        # Initialize it if needed
                        if hasattr(occipital_area, "initialize") and callable(occipital_area.initialize):
                            await occipital_area.initialize()
                    
                # Use pixel grid visualization
                return await cls.think_with_pixel_grid(
                    prompt=prompt,
                    width=64,
                    height=64,
                    color_mode="color"
                )
                
            elif ui_mode == "fc":
                # Frontend console mode - use text stream visualization
                journaling_manager.recordInfo("[CorpusCallosum] Using text stream visualization")
                return await cls.think_with_stream_visualization(
                    prompt=prompt,
                    highlight_keywords=highlight_keywords,
                    keywords=keywords,
                    show_tokens=show_tokens
                )
                
            else:
                # Headless or unknown mode - just think with no visualization
                journaling_manager.recordInfo("[CorpusCallosum] Using basic thinking (no visualization)")
                return await cls.think(prompt, stream=False)
                
        except Exception as e:
            journaling_manager.recordError(f"[CorpusCallosum] Error in think_with_visualization: {e}")
            # Fallback to basic thinking
            journaling_manager.recordInfo("[CorpusCallosum] Falling back to basic thinking due to error")
            return await cls.think(prompt, stream=False)

    @classmethod
    def enable_cortex_communication(cls, enabled: bool = True) -> None:
        """
        Enable or disable direct communication between cortices
        
        When enabled, cortices can directly communicate through CorpusCallosum
        When disabled, they operate more independently
        
        Args:
            enabled: Whether to enable cortex communication
        """
        cls._cortex_communication_enabled = enabled
        journaling_manager.recordInfo(f"[CorpusCallosum] Cortex communication {'enabled' if enabled else 'disabled'}")

    @classmethod
    async def relay_between_cortices(cls, source_cortex: str, target_cortex: str, 
                                    data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Relay data between cortices through the CorpusCallosum
        
        Args:
            source_cortex: Source cortex name
            target_cortex: Target cortex name
            data: Data to relay
            
        Returns:
            Response from target cortex
        """
        if not cls._cortex_communication_enabled:
            journaling_manager.recordWarning(f"[CorpusCallosum] Cortex communication disabled, "
                                             f"cannot relay from {source_cortex} to {target_cortex}")
            return {"error": "Cortex communication disabled"}
        
        journaling_manager.recordInfo(f"[CorpusCallosum] Relaying data from {source_cortex} to {target_cortex}")
        
        try:
            # Get the target integration area
            if target_cortex not in cls._integration_areas:
                journaling_manager.recordError(f"[CorpusCallosum] Target cortex not registered: {target_cortex}")
                return {"error": f"Target cortex not registered: {target_cortex}"}
            
            target_area = cls._integration_areas[target_cortex]
            
            # Check if target has process_data method
            if not hasattr(target_area, "process_data") or not callable(target_area.process_data):
                journaling_manager.recordError(f"[CorpusCallosum] Target cortex cannot process data: {target_cortex}")
                return {"error": f"Target cortex cannot process data: {target_cortex}"}
            
            # Relay the data
            response = await target_area.process_data(data)
            journaling_manager.recordInfo(f"[CorpusCallosum] Data relayed successfully to {target_cortex}")
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"[CorpusCallosum] Error relaying data: {e}")
            return {"error": str(e)}