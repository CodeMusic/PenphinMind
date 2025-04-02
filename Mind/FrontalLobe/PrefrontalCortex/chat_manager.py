# Standard imports
import asyncio
import time
from typing import Dict, Any, Optional, List

# Project imports
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class ChatManager:
    """Manages chat interactions with the LLM system"""
    
    def __init__(self):
        """Initialize the chat manager"""
        self.active_model = None
        self.conversation_history = []
        self.active_task = None
        
    async def initialize(self, model_name: Optional[str] = None):
        """
        Initialize the chat manager with selected model
        
        Args:
            model_name: The model to use (or None to use default)
        """
        journaling_manager.recordInfo(f"[ChatManager] Initializing with model: {model_name}")
        
        # Get available models
        models = await NeurocorticalBridge.execute("list_models")
        
        # If no model specified, use first English model or first available model
        if not model_name:
            if models:
                for model in models:
                    if isinstance(model, dict) and model.get("name"):
                        # Check for language attribute if present
                        if "language" in model and model["language"] == "en":
                            model_name = model["name"]
                            break
                        
                # If no English model found, use first available
                if not model_name and models and isinstance(models[0], dict):
                    model_name = models[0].get("name")
        
        # Set the selected model
        if model_name:
            result = await NeurocorticalBridge.execute("set_model", {"model": model_name})
            self.active_model = model_name if result and result.get("success") else None
            
            if self.active_model:
                journaling_manager.recordInfo(f"[ChatManager] Using model: {self.active_model}")
            else:
                journaling_manager.recordError(f"[ChatManager] Failed to set model: {model_name}")
        else:
            journaling_manager.recordWarning("[ChatManager] No model available")
            
        return self.active_model is not None
        
    async def send_message(self, message: str, stream: bool = True):
        """
        Send a message to the LLM
        
        Args:
            message: The user message
            stream: Whether to stream the response
            
        Returns:
            Task or response string
        """
        journaling_manager.recordInfo(f"[ChatManager] Sending message (stream={stream})")
        
        # Add message to history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Use NeurocorticalBridge to think with proper routing
        # This will use the task system if stream=True, direct API if stream=False
        task_or_response = await NeurocorticalBridge.execute(
            "think", 
            {"prompt": message}, 
            use_task=stream,
            stream=stream
        )
        
        # If streaming, store the task
        if stream and hasattr(task_or_response, "id"):
            self.active_task = task_or_response
        else:
            # If direct API call, add the response to history
            self.conversation_history.append({"role": "assistant", "content": task_or_response})
            
        return task_or_response
        
    async def reset_chat(self):
        """Reset the chat"""
        journaling_manager.recordInfo("[ChatManager] Resetting chat")
        
        # Clear history
        self.conversation_history = []
        
        # Reset LLM
        await NeurocorticalBridge.execute("reset_llm") 