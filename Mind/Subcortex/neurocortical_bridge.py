"""
NeurocorticalBridge: A bridge between direct API calls and the task system

This module provides a unified interface for operations that can be executed
either directly or through the BasalGanglia task system, depending on their nature.
"""

import asyncio
import time
import json
from typing import Dict, Any, Optional, Callable, List, Union

from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.CorpusCallosum.api_commands import (
    create_command, 
    parse_response, 
    BaseCommand, 
    SystemCommand, 
    LLMCommand, 
    CommandType,
    AudioCommand
)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class NeurocorticalBridge:
    """Bridge between direct API calls and the task system"""
    
    OPERATION_MAP = {
        # LLM Operations
        "think": (CommandType.LLM, "inference"),
        "setup_llm": (CommandType.LLM, "setup"),
        "exit_llm": (CommandType.LLM, "exit"),
        
        # System Operations
        "ping": (CommandType.SYSTEM, "ping"),
        "hardware_info": (CommandType.SYSTEM, "hwinfo"),
        "reboot": (CommandType.SYSTEM, "reboot"),
        
        # Audio Operations
        "setup_audio": (CommandType.AUDIO, "setup"),
        "asr": (CommandType.AUDIO, "asr"),
        "tts": (CommandType.AUDIO, "tts"),
        "vad": (CommandType.AUDIO, "vad"),
        "whisper": (CommandType.AUDIO, "whisper")
    }
    
    @classmethod
    async def execute_operation(cls, operation: str, data: Dict[str, Any] = None, use_task: bool = None, stream: bool = False):
        try:
            if operation not in cls.OPERATION_MAP:
                return {"status": "error", "message": f"Unknown operation: {operation}"}

            command_type, action = cls.OPERATION_MAP[operation]
            # Create typed command instead of using create_command
            command = CommandFactory.create_command(
                command_type,
                action=action,
                data=data or {}
            )

            # Determine execution path
            if use_task:
                return await cls._execute_task(command)
            elif stream:
                return await cls._handle_stream(command)
            else:
                return await cls.execute(command)

        except Exception as e:
            journaling_manager.recordError(f"Operation execution error: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def _handle_stream(cls, command: BaseCommand) -> Dict[str, Any]:
        """Handle streaming operations"""
        try:
            if isinstance(command, LLMCommand):
                return await cls._handle_llm_stream(command)
            else:
                return {"status": "error", "message": "Streaming not supported for this operation"}
        except Exception as e:
            journaling_manager.recordError(f"Stream handling error: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def _handle_llm_stream(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LLM streaming operations"""
        try:
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Setup streaming
            setup_response = await cls.execute("setup_llm", {
                "response_format": "llm.utf-8.stream",
                "input": "llm.utf-8.stream",
                "enoutput": True,
                "stream": True
            })
            
            if setup_response["status"] != "ok":
                return setup_response
            
            # Send command and handle stream
            response = await SynapticPathways.transmit_json(command)
            
            # Cleanup after streaming
            await cls.execute("exit_llm", {"work_id": command["work_id"]})
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"LLM stream error: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def _execute_task(cls, command: BaseCommand) -> Dict[str, Any]:
        """Execute command through task system"""
        try:
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            bg = SynapticPathways.get_basal_ganglia()
            task = bg.get_task(command.work_id)
            
            if task:
                task.command = command.action
                task.data = command.data
                task.active = True
                await task.execute()
                return {"status": "ok", "response": "Task started", "task": task}
            else:
                return {"status": "error", "message": "Task not found"}
                
        except Exception as e:
            journaling_manager.recordError(f"Task execution error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def execute(cls, command: BaseCommand) -> Dict[str, Any]:
        """Execute a command through appropriate pathway"""
        try:
            # Execute through appropriate handler based on command type
            if isinstance(command, LLMCommand):
                return await cls._handle_llm_command(command)
            elif isinstance(command, SystemCommand):
                return await cls._handle_system_command(command)
            elif isinstance(command, AudioCommand):
                return await cls._handle_audio_command(command)
            else:
                return {"status": "error", "message": f"Unknown command type: {type(command)}"}
                
        except Exception as e:
            journaling_manager.recordError(f"Command execution error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _execute_direct(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command directly"""
        try:
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Get BasalGanglia instance
            bg = SynapticPathways.get_basal_ganglia()
            
            # Execute command directly
            comm_task = bg.get_communication_task()
            if comm_task:
                response = await comm_task.send_command(command)
                if response:
                    return {"status": "ok", "response": response}
                else:
                    return {"status": "error", "message": "No response"}
            else:
                return {"status": "error", "message": "Communication task not available"}
                
        except Exception as e:
            journaling_manager.recordError(f"Direct execution error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _handle_llm_command(cls, command: LLMCommand, stream: bool = False):
        """Handle LLM commands with proper routing"""
        action = command.action
        bg = cls.get_basal_ganglia()
        
        # For basic configuration commands, use communication task
        if action in ["setup", "reset"]:
            comm_task = bg.get_communication_task()
            return await comm_task.send_command(command)
            
        # For inference, use ThinkTask if possible
        elif action == "inference":
            prompt = command.data.get("delta", "")
            if prompt:
                stream_mode = command.stream if hasattr(command, "stream") else stream
                return bg.think(prompt=prompt, stream=stream_mode)
            
            comm_task = bg.get_communication_task()
            return await comm_task.send_command(command)
            
    @classmethod
    async def _handle_system_command(cls, command: SystemCommand):
        """Handle system commands by creating and executing appropriate tasks"""
        command_type = command.command_type
        data = command.data
        
        # Get SystemCommandTask from BasalGanglia
        bg = cls.get_basal_ganglia()
        system_task = bg.system_command(command_type, data)
        
        # Wait for task to complete (this is a blocking operation)
        while system_task.active or not system_task.has_completed():
            await asyncio.sleep(0.1)
        
        # Return task result
        return system_task.result if system_task.result is not None else {"error": "Task completed with no result"}
    
    @classmethod
    async def _handle_audio_command(cls, command: AudioCommand) -> Dict[str, Any]:
        """Handle audio commands based on their action"""
        try:
            if command.action == "tts":
                return await cls._handle_tts(command)
            elif command.action == "asr":
                return await cls._handle_asr(command)
            elif command.action == "vad":
                return await cls._handle_vad(command)
            elif command.action == "whisper":
                return await cls._handle_whisper(command)
            else:
                return {"status": "error", "message": f"Unknown audio action: {command.action}"}
        except Exception as e:
            journaling_manager.recordError(f"Audio command error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _direct_get_model(cls) -> Dict[str, Any]:
        """Get current active model directly without using task system"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        try:
            # Get communication task
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                return {"success": False, "error": "Communication task not available"}
                
            # Create get model command
            get_model_command = {
                "request_id": f"get_model_{int(time.time())}",
                "work_id": "sys",
                "action": "get_model"
            }
            
            # Send command directly through comm task
            response = await comm_task.send_command(get_model_command)
            
            # Process response
            if response and isinstance(response, dict):
                return {"success": True, "model": response.get("data", "")}
            else:
                return {"success": False, "error": "Invalid response format"}
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error getting model: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def _direct_list_models(cls) -> List[Dict[str, Any]]:
        """Direct model listing without using the task system"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        try:
            # Create list models request
            list_models_command = {
                "request_id": f"lsmode_{int(time.time())}",
                "work_id": "sys",
                "action": "lsmode"
            }
            
            # Special handling for lsmode to avoid recursion
            # We'll use a direct low-level communication here
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                journaling_manager.recordError("[NeurocorticalBridge] Communication task not available")
                return SynapticPathways.available_models
            
            # Send the command directly via communication task to avoid the recursion loop
            journaling_manager.recordInfo("[NeurocorticalBridge] Using direct communication for lsmode command")
            response = await comm_task.send_command(list_models_command)
            
            if response and isinstance(response, dict) and "data" in response:
                models_data = response["data"]
                if isinstance(models_data, list):
                    # Update shared cache
                    SynapticPathways.available_models = models_data
                    
                    return models_data
                else:
                    journaling_manager.recordError(f"[NeurocorticalBridge] Invalid models data format: {type(models_data)}")
            else:
                journaling_manager.recordError(f"[NeurocorticalBridge] Invalid models response: {response}")
            
            # Return cached models if available
            return SynapticPathways.available_models
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error listing models: {e}")
            return SynapticPathways.available_models
    
    @classmethod
    async def _direct_set_model(cls, model_name: str) -> Dict[str, Any]:
        """Direct model selection without using the task system"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        try:
            # Get communication task directly from BasalGanglia
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                journaling_manager.recordError("[NeurocorticalBridge] Communication task not available for set model")
                return {"success": False, "error": "Communication task not available"}
            
            # Create setup command with the selected model
            setup_command = {
                "request_id": f"setup_{int(time.time())}",
                "work_id": "sys",
                "action": "setup",
                "object": "llm.setup",
                "data": {
                    "model": model_name,
                    "response_format": "llm.utf-8.stream", 
                    "input": "llm.utf-8.stream", 
                    "enoutput": True,
                    "enkws": True,
                    "max_token_len": 127,
                    "unit": "llm"
                }
            }
            
            # Send command directly through communication task
            journaling_manager.recordInfo("[NeurocorticalBridge] Sending set model request directly through communication task")
            response = await comm_task.send_command(setup_command)
            
            if response and response.get("error", {}).get("code", 1) == 0:
                # Update default model
                SynapticPathways.default_llm_model = model_name
                return {"success": True, "model": model_name}
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error setting model: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def _direct_reset_llm(cls) -> Dict[str, Any]:
        try:
            reset_command = SystemCommand.create_reset_command(
                target="llm",
                request_id=f"reset_{int(time.time())}"
            )
            
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                return {"success": False, "error": "Communication task not available"}
                
            return await comm_task.send_command(reset_command)
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error resetting LLM: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def _direct_ping(cls) -> Dict[str, Any]:
        """Direct ping without using the task system"""
        try:
            ping_command = SystemCommand.create_ping_command()
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                return {"success": False, "error": "Communication task not available"}
            
            return await comm_task.send_command(ping_command)
            
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Ping error: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def get_basal_ganglia(cls):
        """Get BasalGanglia instance, avoiding circular imports"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        return SynapticPathways.get_basal_ganglia()

    @classmethod
    async def _direct_reset_system(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reset system command directly"""
        try:
            journaling_manager.recordInfo("[NeurocorticalBridge] Handling reset system command")
            
            # Get SystemCommandTask from BasalGanglia
            bg = cls.get_basal_ganglia()
            system_task = bg.get_task("SystemCommandTask")
            
            if not system_task:
                journaling_manager.recordInfo("[NeurocorticalBridge] Creating new SystemCommandTask for reset")
                from Mind.Subcortex.BasalGanglia.tasks.system_command_task import SystemCommandTask
                system_task = SystemCommandTask(command_type="reset")
                bg.register_task(system_task)
            else:
                # Configure existing task
                system_task.command = "reset"
                system_task.data = None
            
            # Execute the task
            journaling_manager.recordInfo("[NeurocorticalBridge] Executing reset command via SystemCommandTask")
            system_task.active = True
            result = await system_task.execute()
            return result
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error in reset_system: {e}")
            import traceback
            journaling_manager.recordError(f"[NeurocorticalBridge] Stack trace: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}

    @classmethod
    async def get_hardware_info(cls) -> Dict[str, Any]:
        """Get hardware information from the device"""
        try:
            return await cls.execute("hardware_info")
        except Exception as e:
            journaling_manager.recordError(f"Error getting hardware info: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def initialize_system(cls, connection_type: str = None) -> bool:
        """Initialize the entire system"""
        try:
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Initialize SynapticPathways first
            success = await SynapticPathways.initialize(connection_type)
            if not success:
                return False
                
            # Then initialize other systems
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"System initialization error: {e}")
            return False 