# Standard imports
import asyncio
import time
from typing import Dict, Any, Optional, List

# Project imports
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.config import CONFIG
from Mind.Subcortex.api_commands import (
    LLMCommand, SystemCommand, parse_response
)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class ChatManager:
    """Manages chat interactions with the LLM system"""
    
    def __init__(self):
        """Initialize the chat manager"""
        self.conversation_history = []
        self.active_model = None
        self.system_message = CONFIG.persona  # Initialize with config persona
        self.active_task = None
        
    async def initialize(self, model_name: Optional[str] = None, system_message: Optional[str] = None):
        """Initialize chat with model and system message (persona)"""
        system_message = system_message or CONFIG.persona
        
        if model_name:
            setup_command = LLMCommand.create_setup_command(
                model=model_name,
                prompt=system_message,
                response_format="llm.utf-8",
                input="llm.utf-8",
                enoutput=True,
                enkws=False,
                max_token_len=127
            )
            
            result = await NeurocorticalBridge.execute(setup_command)
            
            if result["status"] == "ok":
                self.active_model = model_name
                self.system_message = system_message
                journaling_manager.recordInfo(f"[ChatManager] Using model: {self.active_model} with persona")
            else:
                journaling_manager.recordError(f"[ChatManager] Failed to set model: {model_name}")
                
        return self.active_model is not None
        
    async def set_system_message(self, system_message: str):
        """Update system message/persona"""
        self.system_message = system_message
        if self.active_model:
            await self.initialize(self.active_model, system_message)
        
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