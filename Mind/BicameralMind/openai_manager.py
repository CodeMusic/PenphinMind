"""
Project Function:
    Handles OpenAI integration:
    OpenAI Manager System:
    - Response generation
    - Context management
    - Error handling
    - State management
    - Feedback processing
    - Learning integration
"""

import openai
import os
from typing import Dict, Any, Optional
from ..FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class OpenAIManager:
    """Manages OpenAI API integration for response generation"""
    
    def __init__(self):
        """Initialize OpenAI manager"""
        journaling_manager.recordScope("OpenAIManager.__init__")
        try:
            self.api_key = os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                journaling_manager.recordError("OpenAI API key not found in environment variables")
                raise ValueError("OpenAI API key not found in environment variables")
                
            openai.api_key = self.api_key
            self.model = "gpt-4"
            journaling_manager.recordDebug(f"OpenAI manager initialized with model: {self.model}")
            
        except Exception as e:
            journaling_manager.recordError(f"Error initializing OpenAI manager: {e}")
            raise

    async def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response using OpenAI's API"""
        journaling_manager.recordScope("OpenAIManager.generate_response", prompt=prompt, context=context)
        try:
            messages = [{"role": "system", "content": "You are PenphinOS, a bicameral AI assistant."}]
            
            if context:
                messages.append({"role": "system", "content": f"Context: {str(context)}"})
                journaling_manager.recordDebug(f"Added context to messages: {context}")
                
            messages.append({"role": "user", "content": prompt})
            journaling_manager.recordDebug(f"Added user prompt to messages: {prompt}")

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages
            )
            
            result = response.choices[0].message.content
            journaling_manager.recordDebug(f"Generated response: {result}")
            return result
            
        except Exception as e:
            error_msg = f"OpenAI Error: {str(e)}"
            journaling_manager.recordError(error_msg)
            return error_msg 