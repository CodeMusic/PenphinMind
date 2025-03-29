"""
Neurological Function:
    Language Processing Coordinator:
    - Coordinates between Broca's and Wernicke's areas
    - Manages language comprehension and production
    - Handles high-level language tasks
    - Integrates language with other cognitive functions

Project Function:
    Coordinates language processing:
    - Manages LLM instance
    - Coordinates between language areas
    - Provides high-level language interface
    - Handles complex language tasks
"""

import logging
from typing import Dict, Any, Optional
from ...config import CONFIG
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from ...FrontalLobe.InferiorFrontalGyrus.broca_area import BrocaArea
from ...FrontalLobe.InferiorFrontalGyrus.wernicke_area import WernickeArea
from ...FrontalLobe.InferiorFrontalGyrus.llm import LLM

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class LanguageProcessor:
    """Coordinates language processing between Broca's and Wernicke's areas"""
    
    def __init__(self):
        """Initialize the language processor"""
        journaling_manager.recordScope("LanguageProcessor.__init__")
        self._initialized = False
        self._processing = False
        self._llm = None
        self._broca = None
        self._wernicke = None
        self.current_state = {
            "status": "idle",
            "error": None
        }
        
    async def initialize(self) -> None:
        """Initialize the language processor"""
        journaling_manager.recordScope("LanguageProcessor.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Language processor already initialized")
            return
            
        try:
            # Initialize components
            self._llm = LLM()
            self._broca = BrocaArea()
            self._wernicke = WernickeArea()
            
            # Initialize all components
            await self._llm.initialize()
            await self._broca.initialize()
            await self._wernicke.initialize()
            
            self._initialized = True
            journaling_manager.recordInfo("Language processor initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize language processor: {e}")
            raise
            
    async def process_input(self, input_text: str) -> Dict[str, Any]:
        """Process text input through language system"""
        journaling_manager.recordScope("LanguageProcessor.process_input", input_text=input_text)
        try:
            if not self._initialized:
                journaling_manager.recordError("Language processor not initialized")
                raise RuntimeError("Language processor not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already processing input")
                raise RuntimeError("Already processing input")
                
            self._processing = True
            self.current_state["status"] = "processing"
            
            # Process through LLM for response generation
            llm_response = await self._llm.process_input(input_text)
            
            self._processing = False
            self.current_state["status"] = "completed"
            journaling_manager.recordInfo("Input processed successfully")
            
            return {
                "response": llm_response
            }
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error processing input: {e}")
            raise
            
    async def process_speech(self, audio_data: bytes) -> Dict[str, Any]:
        """Process speech input through language system"""
        journaling_manager.recordScope("LanguageProcessor.process_speech")
        try:
            if not self._initialized:
                journaling_manager.recordError("Language processor not initialized")
                raise RuntimeError("Language processor not initialized")
                
            # First, recognize speech through Wernicke's area
            recognition = await self._wernicke.recognize_speech(audio_data)
            
            if not recognition.get("text"):
                return {"status": "error", "message": "Failed to recognize speech"}
                
            # Then, process the recognized text
            return await self.process_input(recognition["text"])
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing speech: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up the language processor"""
        journaling_manager.recordScope("LanguageProcessor.cleanup")
        try:
            if self._llm:
                await self._llm.cleanup()
            if self._broca:
                await self._broca.cleanup()
            if self._wernicke:
                await self._wernicke.cleanup()
                
            self._initialized = False
            self._llm = None
            self._broca = None
            self._wernicke = None
            journaling_manager.recordInfo("Language processor cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up language processor: {e}")
            raise 