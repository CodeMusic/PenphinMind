from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import time
import asyncio
from typing import Dict, Any, List
from Mind.CorpusCallosum.api_commands import (
    BaseCommand, 
    CommandType,
    LLMCommand, 
    SystemCommand, 
    create_command, 
    parse_response
)
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge

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
        self.active_model = None
        self.models = []
        self.models_loaded = False
        self.model_info = {}
        journaling_manager.recordInfo("[BasalGanglia] Created ModelManagementTask")
        
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
            # Create specific LLM setup command
            setup_command = LLMCommand.create_setup_command(
                model=model_name,
                response_format="llm.utf-8",
                input="llm.utf-8",
                enoutput=True,
                enkws=False,
                max_token_len=127,
                **(params or {})
            )
            
            # Execute through NeurocorticalBridge
            response = await NeurocorticalBridge.execute(setup_command)
            
            parsed = parse_response(response)
            if parsed["status"] == "ok":
                self.active_model = model_name
                self.result = {"success": True, "model": model_name}
                return True
            else:
                self.result = {"success": False, "error": parsed["message"]}
                return False
                
        except Exception as e:
            journaling_manager.recordError(f"[ModelManagementTask] Error setting active model: {e}")
            self.result = {"success": False, "error": str(e)}
            return False
    
    async def reset_llm(self) -> bool:
        """Reset the LLM system"""
        journaling_manager.recordScope("[BasalGanglia] Resetting LLM system")
        try:
            # Create specific system reset command
            reset_command = SystemCommand.create_reset_command(
                target="llm",
                request_id=f"reset_{int(time.time())}"
            )
            
            # Execute through NeurocorticalBridge
            response = await NeurocorticalBridge.execute(reset_command)
            return response.get("success", False)
            
        except Exception as e:
            journaling_manager.recordError(f"[ModelManagementTask] Reset error: {e}")
            return False
    
    # Add a method to manually request reload
    def request_reload(self):
        """Request that models be reloaded on next execution"""
        self.models_loaded = False
        self.active = True 