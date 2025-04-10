"""
PenphinMind ChatManager
Manages chat sessions with the LLM system using the Mind interface

This component sits outside the Mind architecture and serves as an
interface between the user interaction layer and the Mind system.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List

from Mind.mind import Mind
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from config import CONFIG  # Use absolute import
from .chat_history import ConversationState

# Initialize journaling manager
journaling_manager = SystemJournelingManager(CONFIG.log_level)

class ChatManager:
    """
    Manages interactive chat sessions with the LLM system
    
    This is an external component that interacts with the Mind
    but is not part of the Mind's internal architecture.
    """
    
    def __init__(self, mind=None):
        """
        Initialize the chat manager
        
        Args:
            mind: The Mind instance to use for communication
        """
        self.mind = mind
        self.active_model = None
        self.conversation_state = ConversationState()
        self.last_response = ""
        self.chat_initialized = False
        self.model_setup_complete = False
        # Use the mind's persona if available
        self.system_message = mind._persona if mind else None
        
        # Set system message in conversation state
        if self.system_message:
            self.conversation_state.system_message = self.system_message
        
    async def initialize(self, model_name: Optional[str] = None):
        """
        Initialize the chat session
        
        Args:
            model_name: Specific model to use (or None to use default or auto-select)
            
        Returns:
            bool: Success status
        """
        journaling_manager.recordInfo(f"[ChatManager] Initializing chat with model: {model_name}")
        
        try:
            # Check connection with a ping
            ping_result = await self.mind.ping_system()
            if not ping_result or ping_result.get("status") != "ok":
                journaling_manager.recordError("[ChatManager] Connection check failed")
                return False
                
            # Use provided model or get default
            if not model_name:
                model_name = self.mind.get_default_model()
            
            # If still no model, we'll need to find one
            if not model_name:
                model_name = await self._find_suitable_model()
                
            # If we found a model, set it up
            if model_name:
                journaling_manager.recordInfo(f"[ChatManager] Using model: {model_name}")
                self.mind.set_default_model(model_name)
                
                # Log the persona being used
                journaling_manager.recordDebug(f"[ChatManager] Using persona: {self.mind._persona}")
                
                # Activate the model with mind's persona
                setup_result = await self.mind.set_model(model_name)
                if setup_result.get("status") == "ok":
                    self.active_model = model_name
                    self.model_setup_complete = True
                    journaling_manager.recordInfo(f"[ChatManager] Model {model_name} initialized with persona")
                else:
                    journaling_manager.recordError(f"[ChatManager] Failed to initialize model: {model_name}")
                    return False
            else:
                journaling_manager.recordError("[ChatManager] No suitable model found")
                return False
                
            # Clear history for new session
            self.conversation_state.clear_history()
            self.chat_initialized = True
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"[ChatManager] Initialization error: {e}")
            import traceback
            journaling_manager.recordError(f"[ChatManager] {traceback.format_exc()}")
            return False
    
    async def _find_suitable_model(self) -> Optional[str]:
        """
        Find a suitable model for chat
        
        This method tries to find the best LLM model available, preferring
        smaller models that are more likely to work on limited hardware.
        
        Returns:
            str: Model name or None if no suitable model found
        """
        journaling_manager.recordInfo("[ChatManager] Searching for suitable model")
        
        try:
            # First check if we have a configured default model in the Mind
            default_model = self.mind.get_default_model()
            if default_model:
                journaling_manager.recordInfo(f"[ChatManager] Using configured default model: {default_model}")
                return default_model
            
            # Get models through Mind if no default is configured or available
            models_result = await self.mind.list_models()
            models = models_result.get("response", []) if models_result.get("status") == "ok" else []
            
            if not models:
                journaling_manager.recordWarning("[ChatManager] No models available")
                return None
                
            # First filter for only LLM models
            llm_models = [m for m in models if m.get("type", "").lower() == "llm"]
            journaling_manager.recordInfo(f"[ChatManager] Found {len(llm_models)} LLM models")
            
            # Check specifically for deepseek model as that's the intended default
            for model in llm_models:
                model_mode = model.get("mode", "")
                if "deepseek" in model_mode.lower():
                    journaling_manager.recordInfo(f"[ChatManager] Selected deepseek model: {model_mode}")
                    return model_mode
            
            if llm_models:
                # First try to find small LLM models (more likely to work well)
                for model in llm_models:
                    model_mode = model.get("mode", "")
                    if any(small_marker in model_mode.lower() for small_marker in ["0.5b", "tiny", "small"]):
                        journaling_manager.recordInfo(f"[ChatManager] Selected small LLM model: {model_mode}")
                        return model_mode
                
                # If no small model found, use the first LLM model
                model_name = llm_models[0].get("mode", "")
                journaling_manager.recordInfo(f"[ChatManager] Selected first available LLM model: {model_name}")
                return model_name
            else:
                # No LLM models, try any model
                journaling_manager.recordWarning("[ChatManager] No specific LLM models found, trying any model")
                
                # Try to find a small model of any type
                for model in models:
                    model_mode = model.get("mode", "")
                    if any(small_marker in model_mode.lower() for small_marker in ["0.5b", "tiny", "small"]):
                        journaling_manager.recordInfo(f"[ChatManager] Selected small model: {model_mode}")
                        return model_mode
                
                # Use first available model
                if models:
                    model_name = models[0].get("mode", "")
                    journaling_manager.recordInfo(f"[ChatManager] Using first available model: {model_name}")
                    return model_name
            
            # Fallback to a common model name
            return "llm-model-deepseek-r1-1.5b-ax630c"
            
        except Exception as e:
            journaling_manager.recordError(f"[ChatManager] Error finding suitable model: {e}")
            return None
    
    async def send_message(self, message: str, stream: bool = True):
        """
        Send a user message and get response
        
        Args:
            message: The user message
            stream: Whether to stream the response
            
        Returns:
            Task or string response or Dict with error info
        """
        if not self.chat_initialized:
            return {"status": "error", "message": "Chat not initialized"}
            
        if not message.strip():
            return {"status": "error", "message": "Empty message"}
            
        journaling_manager.recordInfo(f"[ChatManager] Processing message: {message[:50]}...")
        
        # Add to conversation history using ConversationState
        self.conversation_state.add_user_message(message)
        
        try:
            # Process message through Mind's think function
            response = await self.mind.think(message, stream=stream)
            
            # If not streaming, store the response in history
            if not stream and isinstance(response, str):
                self.conversation_state.add_assistant_message(response)
                self.last_response = response
                
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"[ChatManager] Error sending message: {e}")
            return {"status": "error", "message": str(e)}
    
    async def reset_chat(self):
        """
        Reset the chat session
        
        Returns:
            Dict: Status information
        """
        journaling_manager.recordInfo("[ChatManager] Resetting chat")
        
        try:
            # Reset LLM through Mind
            reset_result = await self.mind.reset_system()
            
            # Clear conversation history
            self.conversation_state.clear_history()
            self.last_response = ""
            
            # Check result
            if reset_result.get("status") == "ok":
                journaling_manager.recordInfo("[ChatManager] Chat reset successful")
                
                # Re-initialize with the current model
                if self.active_model:
                    await self.initialize(self.active_model)
                    
                return {"status": "ok", "message": "Chat reset successful"}
            else:
                error_msg = reset_result.get("message", "Unknown error")
                journaling_manager.recordError(f"[ChatManager] Reset failed: {error_msg}")
                return {"status": "error", "message": error_msg}
                
        except Exception as e:
            journaling_manager.recordError(f"[ChatManager] Reset error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def try_alternative_model(self):
        """
        Try an alternative model if the current one fails
        
        Returns:
            bool: Success status
        """
        journaling_manager.recordInfo("[ChatManager] Trying alternative model")
        
        try:
            # Get models
            models_result = await self.mind.list_models()
            models = models_result.get("response", []) if models_result.get("status") == "ok" else []
            
            if not models:
                return False
                
            # Filter for LLM models
            llm_models = [m for m in models if m.get("type", "").lower() == "llm"]
            
            # Try different models, skipping the current one
            for model in llm_models:
                model_name = model.get("mode", "")
                
                if model_name and model_name != self.active_model:
                    journaling_manager.recordInfo(f"[ChatManager] Trying alternative model: {model_name}")
                    
                    # Try to initialize with this model
                    setup_result = await self.mind.set_model(model_name)
                    
                    if setup_result.get("status") == "ok":
                        # Update active model
                        self.active_model = model_name
                        self.mind.set_default_model(model_name)
                        journaling_manager.recordInfo(f"[ChatManager] Successfully switched to model: {model_name}")
                        return True
            
            return False
            
        except Exception as e:
            journaling_manager.recordError(f"[ChatManager] Error trying alternative model: {e}")
            return False
    
    def get_summary(self):
        """
        Get a summary of the chat session
        
        Returns:
            Dict: Session information
        """
        return {
            "initialized": self.chat_initialized,
            "model": self.active_model,
            "message_count": len(self.conversation_state.messages),
            "model_setup_complete": self.model_setup_complete
        }
        
    async def set_system_message(self, new_system_message: str):
        """
        Update the system message (persona) for the chat session
        
        Args:
            new_system_message: The new system message to use
            
        Returns:
            bool: Success status
        """
        journaling_manager.recordInfo("[ChatManager] Updating system message")
        journaling_manager.recordDebug(f"[ChatManager] New system message: {new_system_message}")
        
        try:
            self.system_message = new_system_message
            
            # If already initialized, reset the model with new persona
            if self.chat_initialized and self.active_model:
                # Update mind's persona
                if self.mind:
                    self.mind._persona = new_system_message
                
                # Reinitialize with the new persona
                setup_result = await self.mind.set_model(self.active_model)
                if setup_result.get("status") == "ok":
                    journaling_manager.recordInfo(f"[ChatManager] Model reinitialized with new persona")
                    return True
                else:
                    journaling_manager.recordError(f"[ChatManager] Failed to reinitialize model with new persona")
                    return False
            
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"[ChatManager] Error updating system message: {e}")
            import traceback
            journaling_manager.recordError(f"[ChatManager] {traceback.format_exc()}")
            return False 