"""
Neurological Function:
    Prefrontal Cortex (PFC) handles executive functions:
    - Decision making
    - Planning
    - Personality expression
    - Social behavior

Project Function:
    Handles language model interactions:
    - Text generation
    - Response processing
    - Context management
    - Personality expression
"""

import logging
from typing import Dict, Any, Optional
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...CorpusCallosum.neural_commands import LLMCommand, CommandType
from ...config import CONFIG

logger = logging.getLogger(__name__)

async def process_prompt(prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> Dict[str, Any]:
    """
    Process a prompt through the AX630C neural processor over USB serial
    
    Args:
        prompt: Text to process
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        
    Returns:
        Dict[str, Any]: Processed response
    """
    try:
        # Create LLM command
        command = LLMCommand(
            command_type=CommandType.LLM,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Send command directly to AX630C
        response = await command.execute()
        
        return {
            "status": "ok",
            "response": response.get("text", "")
        }
        
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

class LLM:
    """Handles language model interactions"""
    
    def __init__(self):
        """Initialize the LLM handler"""
        self._initialized = False
        self._processing = False
        self.context = []
        self.personality_traits = {
            "empathy": 0.8,
            "curiosity": 0.9,
            "creativity": 0.7
        }
        
    async def initialize(self) -> None:
        """Initialize the LLM handler"""
        if self._initialized:
            return
            
        try:
            self._initialized = True
            logger.info("LLM handler initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM handler: {e}")
            raise
            
    async def process_input(self, input_text: str) -> Dict[str, Any]:
        """
        Process input text through the language model
        
        Args:
            input_text: Text to process
            
        Returns:
            Dict[str, Any]: Processed response
        """
        try:
            # Add input to context
            self.context.append({"role": "user", "content": input_text})
            
            # Create LLM command
            command = LLMCommand(
                command_type=CommandType.LLM,
                prompt=input_text,
                max_tokens=150,
                temperature=0.7
            )
            
            # Send command through SynapticPathways
            response = await SynapticPathways.send_command(command)
            
            # Add response to context
            if response.get("status") == "ok":
                self.context.append({"role": "assistant", "content": response.get("response", "")})
                return {
                    "status": "ok",
                    "response": response.get("response", ""),
                    "context_length": len(self.context)
                }
            else:
                return {
                    "status": "error",
                    "message": response.get("message", "Unknown error")
                }
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return {"status": "error", "message": str(e)}
            
    async def clear_context(self) -> None:
        """Clear the conversation context"""
        self.context = []
        logger.info("Conversation context cleared")
        
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            await self.clear_context()
            self._initialized = False
            logger.info("LLM handler cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up LLM handler: {e}")
            raise 