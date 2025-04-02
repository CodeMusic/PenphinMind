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

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class NeurocorticalBridge:
    """Bridge between direct API calls and the task system"""
    
    @classmethod
    async def execute(cls, operation: str, data: Dict[str, Any] = None, use_task: bool = None, stream: bool = False):
        """
        Execute an operation either directly or through the task system
        
        Args:
            operation: The operation to perform (e.g., "think", "hardware_info", "list_models")
            data: Parameters for the operation
            use_task: Whether to use the task system (None = automatic decision based on operation)
            stream: Whether to stream results (for LLM operations)
            
        Returns:
            The result of the operation
        """
        # Import here to avoid circular imports
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        # Initialize data if None
        data = data or {}
        
        # Define operation categories
        direct_operations = {
            "hardware_info": cls._direct_hardware_info,
            "list_models": cls._direct_list_models,
            "lsmode": cls._direct_list_models,  # Alias for list_models
            "ping": cls._direct_ping,
            "get_model": cls._direct_get_model,
            "set_model": lambda model_name=data.get("model", ""): cls._direct_set_model(model_name),
            "reset_llm": cls._direct_reset_llm,
            "initialize_connection": lambda: SynapticPathways.initialize(data.get("connection_type")),
            "cleanup_connection": SynapticPathways.cleanup,
            "reboot_device": lambda: SynapticPathways.reboot_device(),
            "get_communication_task": lambda: cls.get_basal_ganglia().get_communication_task(),
            "reset_system": lambda: cls._direct_reset_system(data.get("command", {}))
        }
        
        task_operations = {
            "think": lambda: cls.get_basal_ganglia().think(data.get("prompt", ""), stream),
            "tts": lambda: cls.get_basal_ganglia().text_to_speech(data),
            "asr": lambda: cls.get_basal_ganglia().speech_to_text(data),
            "display_visual": lambda: cls.get_basal_ganglia().display_visual(**data),
            "llm_command": lambda: cls._handle_llm_command(data.get("command", {}), stream),
            "create_llm_pixel_grid": lambda: cls.get_basal_ganglia().display_llm_pixel_grid(
                width=data.get("width", 64),
                height=data.get("height", 64),
                wrap=data.get("wrap", True),
                color_mode=data.get("color_mode", "grayscale")
            ),
            "create_llm_stream": lambda: cls.get_basal_ganglia().display_llm_stream(
                highlight_keywords=data.get("highlight_keywords", False),
                keywords=data.get("keywords", None),
                show_tokens=data.get("show_tokens", False)
            ),
            "direct_command": lambda: cls.get_basal_ganglia().get_communication_task().send_command(data.get("command", {})),
            "system_command": lambda: cls._handle_system_command(data)
        }
        
        # Determine whether to use task if not specified
        if use_task is None:
            use_task = operation in task_operations
        
        # Log the execution request
        journaling_manager.recordInfo(f"[NeurocorticalBridge] Executing {operation} (task: {use_task}, stream: {stream})")
        
        try:
            # Use direct operation if available and not using task system
            if not use_task and operation in direct_operations:
                journaling_manager.recordInfo(f"[NeurocorticalBridge] Using direct operation for {operation}")
                return await direct_operations[operation]()
                
            # Use task operation if available and using task system    
            elif use_task and operation in task_operations:
                journaling_manager.recordInfo(f"[NeurocorticalBridge] Using task operation for {operation}")
                return await task_operations[operation]()
                
            # When direct operation is requested but only task is available, or vice versa
            elif operation in direct_operations:
                journaling_manager.recordInfo(f"[NeurocorticalBridge] Using direct operation (fallback) for {operation}")
                return await direct_operations[operation]()
                
            elif operation in task_operations:
                journaling_manager.recordInfo(f"[NeurocorticalBridge] Using task operation (fallback) for {operation}")
                return await task_operations[operation]()
                
            # Unknown operation
            else:
                journaling_manager.recordError(f"[NeurocorticalBridge] Unknown operation: {operation}")
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error executing operation {operation}: {e}")
            import traceback
            journaling_manager.recordError(f"[NeurocorticalBridge] Traceback: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def _handle_llm_command(cls, command: Dict[str, Any], stream: bool = False):
        """Handle LLM commands with proper routing"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        action = command.get("action", "")
        bg = cls.get_basal_ganglia()
        
        # For basic configuration commands, use communication task
        if action in ["setup", "reset"]:
            comm_task = bg.get_communication_task()
            return await comm_task.send_command(command)
            
        # For inference, use ThinkTask if possible
        elif action == "inference":
            # Try to get prompt from command
            prompt = ""
            if "data" in command and isinstance(command["data"], dict) and "delta" in command["data"]:
                prompt = command["data"]["delta"]
                
                # Check if we have a valid prompt
                if prompt:
                    # Get stream setting from command or use default
                    stream_mode = stream
                    if "stream" in command:
                        stream_mode = command["stream"]
                        
                    # Use ThinkTask
                    return bg.think(prompt=prompt, stream=stream_mode)
                    
            # If we couldn't get a prompt or create a task, fall back to communication task
            comm_task = bg.get_communication_task()
            return await comm_task.send_command(command)
            
        # Default to communication task for other actions
        else:
            comm_task = bg.get_communication_task()
            return await comm_task.send_command(command)
            
    @classmethod
    async def _handle_system_command(cls, command: Dict[str, Any]):
        """Handle system commands by creating and executing appropriate tasks"""
        command_type = command.get("command_type", "")
        data = command.get("data", {})
        
        # Get SystemCommandTask from BasalGanglia
        bg = cls.get_basal_ganglia()
        system_task = bg.system_command(command_type, data)
        
        # Wait for task to complete (this is a blocking operation)
        while system_task.active or not system_task.has_completed():
            await asyncio.sleep(0.1)
        
        # Return task result
        return system_task.result if system_task.result is not None else {"error": "Task completed with no result"}
    
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
    async def _direct_hardware_info(cls) -> Dict[str, Any]:
        """Direct hardware info query without using the task system"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        try:
            # Get communication task directly from BasalGanglia
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                journaling_manager.recordError("[NeurocorticalBridge] Communication task not available for hardware info")
                return SynapticPathways.current_hw_info
            
            # Create hardware info request
            hwinfo_command = {
                "request_id": f"hwinfo_{int(time.time())}",
                "work_id": "sys",
                "action": "hwinfo"
            }
            
            # Send command directly through communication task
            journaling_manager.recordInfo("[NeurocorticalBridge] Sending hardware info request directly through communication task")
            response = await comm_task.send_command(hwinfo_command)
            
            if response and isinstance(response, dict) and "data" in response:
                api_data = response["data"]
                
                # Create properly formatted hardware info
                hw_info = {
                    "cpu_loadavg": api_data.get("cpu_loadavg", 0),
                    "mem": api_data.get("mem", 0),
                    "temperature": api_data.get("temperature", 0),
                    "timestamp": time.time()
                }
                
                # Update shared cache
                SynapticPathways.current_hw_info = hw_info.copy()
                
                return hw_info
            else:
                journaling_manager.recordError(f"[NeurocorticalBridge] Invalid hardware info response: {response}")
                return SynapticPathways.current_hw_info
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error fetching hardware info: {e}")
            return SynapticPathways.current_hw_info
    
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
        """Direct LLM reset without using the task system"""
        try:
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Use direct API approach with proper command format
            reset_command = {
                "request_id": f"reset_{int(time.time())}",
                "work_id": "sys",
                "action": "reset"
            }
            
            # Log the command
            journaling_manager.recordInfo("[NeurocorticalBridge] Executing direct reset command")
            
            # Send through CommunicationTask to maintain architecture
            bg = SynapticPathways.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                journaling_manager.recordError("[NeurocorticalBridge] Communication task not available for reset")
                return {"success": False, "error": "Communication task not available"}
                
            # Execute through communication task
            response = await comm_task.send_command(reset_command)
            
            # Check standard API response format
            if response and "error" in response:
                error_code = response["error"].get("code", -1)
                success = (error_code == 0)
                
                if success:
                    return {"success": True}
                else:
                    error_msg = response["error"].get("message", "Unknown error")
                    return {"success": False, "error": error_msg}
            else:
                journaling_manager.recordError(f"[NeurocorticalBridge] Invalid reset response format")
                return {"success": False, "error": "Invalid response format"}
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error resetting LLM: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def _direct_ping(cls) -> Dict[str, Any]:
        """Direct ping without using the task system"""
        try:
            # Get communication task directly from BasalGanglia
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                journaling_manager.recordError("[NeurocorticalBridge] Communication task not available for ping")
                return {"success": False, "error": "Communication task not available"}
            
            # Create ping command
            ping_command = {
                "request_id": f"ping_{int(time.time())}",
                "work_id": "sys",
                "action": "ping"
            }
            
            # Send command directly through communication task
            journaling_manager.recordInfo("[NeurocorticalBridge] Sending ping directly through communication task")
            response = await comm_task.send_command(ping_command)
            
            if response:
                return {"success": True, "response": response}
            else:
                return {"success": False, "error": "No response"}
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error pinging: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    async def execute_operation(cls, operation: str, data: Dict[str, Any] = None, use_task: bool = None, stream: bool = False) -> Dict[str, Any]:
        """
        Execute an operation and return a standardized response format
        
        Args:
            operation: The operation to perform
            data: Parameters for the operation
            use_task: Whether to use the task system
            stream: Whether to stream results
            
        Returns:
            Dict[str, Any]: Standardized response in format:
            {
                "status": "ok" | "error",
                "response": <result data>,
                "task": <task object> (if task-based operation)
            }
        """
        try:
            # Execute the operation
            result = await cls.execute(operation, data, use_task, stream)
            
            # Handle different result types
            if isinstance(result, dict) and "error" in result:
                # Error response
                return {
                    "status": "error",
                    "message": result.get("error", "Unknown error")
                }
            elif isinstance(result, dict) and "success" in result:
                # Success/failure response
                if result.get("success", False):
                    return {
                        "status": "ok",
                        "response": result
                    }
                else:
                    error_msg = result.get("error", "Operation failed")
                    return {
                        "status": "error", 
                        "message": error_msg
                    }
            elif hasattr(result, "active") and hasattr(result, "has_completed"):
                # Task object
                return {
                    "status": "ok",
                    "response": "Task started",
                    "task": result
                }
            else:
                # Direct result
                return {
                    "status": "ok",
                    "response": result
                }
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Operation error: {e}")
            import traceback
            journaling_manager.recordError(f"[NeurocorticalBridge] {traceback.format_exc()}")
            return {
                "status": "error",
                "message": str(e)
            }

    @classmethod
    def get_basal_ganglia(cls):
        """
        Get the BasalGanglia instance
        
        This method provides controlled access to BasalGanglia
        from outside Subcortex through NeurocorticalBridge
        """
        from Mind.Subcortex.BasalGanglia.basal_ganglia_integration import BasalGangliaIntegration
        
        # Create or get a singleton instance of BasalGanglia
        if not hasattr(cls, '_basal_ganglia_instance') or cls._basal_ganglia_instance is None:
            cls._basal_ganglia_instance = BasalGangliaIntegration()
            journaling_manager.recordInfo("[NeurocorticalBridge] Created new BasalGanglia instance")
        
        return cls._basal_ganglia_instance

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