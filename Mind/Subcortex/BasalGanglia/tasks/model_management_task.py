from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import time
import asyncio
from typing import Dict, Any, List

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class ModelManagementTask(NeuralTask):
    """Task to manage LLM models"""
    
    def __init__(self, priority: int = 4):
        """
        Initialize a model management task
        
        Args:
            priority: Task priority (lower = higher priority)
        """
        super().__init__(name="ModelManagementTask", priority=priority)
        self.task_type = TaskType.MODEL_MANAGEMENT
        self.active = True
        self.log = logging.getLogger("ModelManagementTask")
        journaling_manager.recordInfo("[BasalGanglia] Created ModelManagementTask")
        
        # Model information
        self.models = []
        self.default_model = ""
        self.active_model = ""
        self.models_loaded = False  # Track if we've already loaded models
        self.model_info = {}  # Cache for model info
        
    async def execute(self):
        """Execute the model management task."""
        # This task primarily works on-demand
        return {"status": "ready", "model_count": len(self.models)}
    
    def run(self):
        """Periodic task to check model status"""
        self.status = "running"
        journaling_manager.recordScope("[BasalGanglia] Running ModelManagementTask")
        
        # This task normally runs only when explicitly called
        # For continuous model monitoring, additional logic would be needed
        
        # Continue running
        return
    
    async def get_available_models(self):
        """Get available models from the API."""
        try:
            # Get communication task
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            bg = SynapticPathways.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                journaling_manager.recordError("[ModelManagementTask] ❌ Communication task not found")
                return self.models
            
            # Use EXACT format from documentation - this was working
            lsmode_command = {
                "request_id": "001",
                "work_id": "sys",
                "action": "lsmode"
            }
            
            # Log request
            journaling_manager.recordInfo("[ModelManagementTask] 📤 Requesting available models")
            
            # Send command and get response
            response = await comm_task.send_command(lsmode_command)
            journaling_manager.recordInfo(f"[ModelManagementTask] 📥 Models response received")
            journaling_manager.recordDebug(f"[ModelManagementTask] 📥 Response: {response}")
            
            if response and "data" in response:
                models_data = response["data"]
                if isinstance(models_data, list):
                    self.models = models_data
                    
                    # Update in SynapticPathways
                    SynapticPathways.available_models = self.models
                    
                    # Find default LLM model
                    for model in self.models:
                        if model.get("type") == "llm":
                            SynapticPathways.default_llm_model = model.get("model", "")
                            break
                    
                    journaling_manager.recordInfo(f"[ModelManagementTask] ✅ Found {len(self.models)} models")
                    return self.models
                else:
                    journaling_manager.recordError(f"[ModelManagementTask] ❌ Invalid models data format")
            else:
                journaling_manager.recordError(f"[ModelManagementTask] ❌ Invalid API response")
            
            return self.models
            
        except Exception as e:
            journaling_manager.recordError(f"[ModelManagementTask] ❌ Error getting models: {e}")
            import traceback
            journaling_manager.recordError(f"[ModelManagementTask] Stack trace: {traceback.format_exc()}")
            return self.models
    
    async def set_active_model(self, model_name: str, params: Dict[str, Any] = None) -> bool:
        """Set the active model"""
        journaling_manager.recordScope("[BasalGanglia] Setting active model", model=model_name)
        try:
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Default parameters
            default_params = {
                "response_format": "llm.utf-8",
                "input": "llm.utf-8",
                "enoutput": True,
                "enkws": False,
                "max_token_len": 127,
                "prompt": "You are a helpful assistant named Penphin."
            }
            
            # Merge with provided params
            model_params = {**default_params, **(params or {})}
            
            # Create setup command
            setup_command = {
                "request_id": f"setup_{int(time.time())}",
                "work_id": "sys",
                "action": "setup",
                "object": "llm.setup",
                "data": {
                    "model": model_name,
                    **model_params
                }
            }
            
            # Send command
            response = await SynapticPathways.transmit_json(setup_command)
            
            # Check response
            if response and not response.get("error", {}).get("code", 0):
                self.active_model = model_name
                journaling_manager.recordInfo(f"[BasalGanglia] Set active model to: {model_name}")
                self.result = {"success": True, "model": model_name}
                return True
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                journaling_manager.recordError(f"[BasalGanglia] Failed to set active model: {error_msg}")
                self.result = {"success": False, "error": error_msg}
                return False
                
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error setting active model: {e}")
            self.result = {"success": False, "error": str(e)}
            return False
    
    async def reset_llm(self) -> bool:
        """Reset the LLM system"""
        journaling_manager.recordScope("[BasalGanglia] Resetting LLM system")
        try:
            # Use NeurocorticalBridge for proper architectural layering
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            
            # Execute the reset operation through the bridge
            journaling_manager.recordInfo("[ModelManagementTask] Executing reset via NeurocorticalBridge")
            result = await NeurocorticalBridge.execute_operation("reset_llm")
            
            # Check response
            if result and result.get("status") == "ok":
                message = result.get("message", "Reset completed successfully")
                journaling_manager.recordInfo(f"[BasalGanglia] Reset successful: {message}")
                
                # Clear caches
                self.models = []
                self.default_model = ""
                self.active_model = ""
                
                # Wait for reset to complete
                await asyncio.sleep(3)
                
                self.result = {"success": True, "message": message}
                return True
            else:
                error_msg = result.get("message", "Unknown error") if result else "No response from bridge"
                journaling_manager.recordError(f"[BasalGanglia] Failed to reset LLM: {error_msg}")
                self.result = {"success": False, "error": error_msg}
                return False
                
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error resetting LLM: {e}")
            self.result = {"success": False, "error": str(e)}
            return False
    
    # Add a method to manually request reload
    def request_reload(self):
        """Request that models be reloaded on next execution"""
        self.models_loaded = False
        self.active = True 