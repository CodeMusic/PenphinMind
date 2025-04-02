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
        
        # Determine whether to use task based on operation if not specified
        if use_task is None:
            # These operations are better as direct calls
            simple_operations = ["hardware_info", "list_models", "ping", "get_model", "reset_llm"]
            # These operations are better as tasks
            task_operations = ["think", "tts", "asr", "display_visual"]
            
            use_task = operation in task_operations
        
        # Log the execution request
        journaling_manager.recordInfo(f"[NeurocorticalBridge] Executing {operation} (task: {use_task}, stream: {stream})")
        
        # Get basal ganglia instance
        bg = SynapticPathways.get_basal_ganglia()
        
        #
        # THINKING / LLM OPERATIONS
        #
        if operation == "think":
            prompt = data.get("prompt", "")
            
            if use_task:
                # Use the task system for streaming interactive sessions
                task = bg.think(prompt, stream=stream)
                return task
            else:
                # Use direct API for simple non-streaming queries
                return await cls._direct_llm_query(prompt)
                
        #
        # HARDWARE INFO OPERATIONS
        #
        elif operation == "hardware_info":
            if use_task and hasattr(bg, 'get_hardware_info_task'):
                # Use existing task
                hw_task = bg.get_hardware_info_task()
                if hw_task:
                    # Force a refresh
                    await hw_task.execute()
                    return hw_task.hardware_info
            
            # Direct API call
            return await cls._direct_hardware_info()
        
        #
        # MODEL OPERATIONS
        #
        elif operation == "list_models":
            if use_task and hasattr(bg, 'get_model_management_task'):
                # Use existing task
                model_task = bg.get_model_management_task()
                if model_task:
                    models = await model_task.get_available_models()
                    return models
            
            # Direct API call
            return await cls._direct_list_models()
            
        elif operation == "set_model":
            model_name = data.get("model", "")
            if not model_name:
                return {"success": False, "error": "No model specified"}
                
            if use_task and hasattr(bg, 'get_model_management_task'):
                # Use existing task
                model_task = bg.get_model_management_task()
                if model_task:
                    success = await model_task.set_active_model(model_name)
                    return {"success": success, "model": model_name}
            
            # Direct API call
            return await cls._direct_set_model(model_name)
        
        #
        # SYSTEM OPERATIONS
        #
        elif operation == "reset_llm":
            if use_task and hasattr(bg, 'get_model_management_task'):
                # Use existing task
                model_task = bg.get_model_management_task()
                if model_task:
                    success = await model_task.reset_llm()
                    return {"success": success}
            
            # Direct API call
            return await cls._direct_reset_llm()
            
        elif operation == "ping":
            if use_task:
                # Use system command task
                from Mind.Subcortex.BasalGanglia.tasks.system_command_task import SystemCommandTask
                ping_task = SystemCommandTask(command_type="ping")
                bg.register_task(ping_task)
                while ping_task.active:
                    await asyncio.sleep(0.1)
                return ping_task.result
            
            # Direct API call
            return await cls._direct_ping()
            
        #
        # UNKNOWN OPERATION
        #
        else:
            journaling_manager.recordError(f"[NeurocorticalBridge] Unknown operation: {operation}")
            return {"success": False, "error": f"Unknown operation: {operation}"}
    
    #
    # DIRECT API CALL IMPLEMENTATIONS
    #
    @classmethod
    async def _direct_llm_query(cls, prompt: str) -> str:
        """Direct LLM query without using the task system"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        # Create working session
        work_id = f"direct_llm_{int(time.time())}"
        
        try:
            # Set up LLM model
            setup_command = {
                "request_id": f"setup_{int(time.time())}",
                "work_id": work_id,
                "action": "setup",
                "object": "llm.setup",
                "data": {
                    "model": SynapticPathways.default_llm_model,
                    "response_format": "llm.utf-8.stream", 
                    "input": "llm.utf-8.stream", 
                    "enoutput": True,
                    "enkws": True,
                    "max_token_len": 127,
                    "unit": "llm"
                }
            }
            
            setup_response = await SynapticPathways.transmit_json(setup_command)
            
            if not setup_response or setup_response.get("error", {}).get("code", 1) != 0:
                error_msg = setup_response.get("error", {}).get("message", "Unknown error")
                journaling_manager.recordError(f"[NeurocorticalBridge] LLM setup error: {error_msg}")
                return f"Error: {error_msg}"
            
            # Send inference command
            inference_command = {
                "request_id": f"inference_{int(time.time())}",
                "work_id": work_id,
                "action": "inference",
                "data": {
                    "delta": prompt,
                    "index": 0,
                    "finish": True
                }
            }
            
            response = await SynapticPathways.transmit_json(inference_command)
            
            # Process response
            result = ""
            if "data" in response:
                data = response["data"]
                if isinstance(data, dict) and "delta" in data:
                    result = data.get("delta", "")
                elif isinstance(data, str):
                    result = data
                else:
                    result = str(data)
            else:
                error_code = response.get("error", {}).get("code", -1)
                error_msg = response.get("error", {}).get("message", "Unknown error")
                result = f"Error {error_code}: {error_msg}"
            
            return result
            
        finally:
            # Cleanup
            exit_command = {
                "request_id": f"exit_{int(time.time())}",
                "work_id": work_id,
                "action": "exit"
            }
            
            try:
                await SynapticPathways.transmit_json(exit_command)
            except Exception as e:
                journaling_manager.recordError(f"[NeurocorticalBridge] Error during LLM cleanup: {e}")
    
    @classmethod
    async def _direct_hardware_info(cls) -> Dict[str, Any]:
        """Direct hardware info query without using the task system"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        try:
            # Create hardware info request
            hwinfo_command = {
                "request_id": f"hwinfo_{int(time.time())}",
                "work_id": "sys",
                "action": "hwinfo"
            }
            
            response = await SynapticPathways.transmit_json(hwinfo_command)
            
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
            
            response = await SynapticPathways.transmit_json(list_models_command)
            
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
            
            response = await SynapticPathways.transmit_json(setup_command)
            
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
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        try:
            # Create reset command
            reset_command = {
                "request_id": f"reset_{int(time.time())}",
                "work_id": "sys",
                "action": "reset"
            }
            
            response = await SynapticPathways.transmit_json(reset_command)
            
            if response and response.get("error", {}).get("code", 1) == 0:
                return {"success": True}
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error resetting LLM: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def _direct_ping(cls) -> Dict[str, Any]:
        """Direct ping without using the task system"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        try:
            # Create ping command
            ping_command = {
                "request_id": f"ping_{int(time.time())}",
                "work_id": "sys",
                "action": "ping"
            }
            
            response = await SynapticPathways.transmit_json(ping_command)
            
            if response:
                return {"success": True, "response": response}
            else:
                return {"success": False, "error": "No response"}
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error pinging: {e}")
            return {"success": False, "error": str(e)} 