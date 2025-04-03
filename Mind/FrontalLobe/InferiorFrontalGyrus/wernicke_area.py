"""
Neurological Function:
    Wernicke's Area (Inferior Frontal Gyrus) handles:
    - Language comprehension
    - Speech recognition
    - Word meaning
    - Semantic understanding
    - Context processing
    - Language interpretation
    - Meaning extraction

Project Function:
    Handles language comprehension:
    - Text understanding
    - Speech recognition
    - Word meaning extraction
    - Context analysis
    - Semantic processing
    - Language interpretation
"""

import logging
from typing import Dict, Any, Optional, List
from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.Subcortex.api_commands import CommandType, AudioCommand
from .llm import LLM

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class WernickeArea:
    """Handles language comprehension and speech recognition"""
    
    def __init__(self):
        """Initialize Wernicke's area"""
        journaling_manager.recordScope("WernickeArea.__init__")
        self._initialized = False
        self._processing = False
        self._llm = LLM()
        self.current_state = {
            "status": "idle",
            "error": None
        }
        
    async def initialize(self) -> None:
        """Initialize Wernicke's area"""
        journaling_manager.recordScope("WernickeArea.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Wernicke's area already initialized")
            return
            
        try:
            # Initialize LLM
            await self._llm.initialize()
            
            # Initialize components
            self._initialized = True
            journaling_manager.recordInfo("Wernicke's area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize Wernicke's area: {e}")
            raise
            
    async def recognize_speech(self, audio_data: bytes, language: str = "en") -> Dict[str, Any]:
        """Recognize speech from audio data"""
        journaling_manager.recordScope("WernickeArea.recognize_speech", language=language)
        try:
            if not self._initialized:
                journaling_manager.recordError("Wernicke's area not initialized")
                raise RuntimeError("Wernicke's area not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already processing speech")
                raise RuntimeError("Already processing speech")
                
            self._processing = True
            self.current_state["status"] = "processing"
            
            # Use LLM's ASR functionality
            response = await self._llm.send_asr(audio_data, language)
            
            # Process recognized text through LLM for better understanding
            if response.get("text"):
                processed_text = await self._llm.process_input(response["text"])
                response["processed_text"] = processed_text
            
            self._processing = False
            self.current_state["status"] = "completed"
            journaling_manager.recordInfo("Speech recognized successfully")
            
            return response
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error recognizing speech: {e}")
            raise
            
    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> Dict[str, Any]:
        """Transcribe audio to text"""
        journaling_manager.recordScope("WernickeArea.transcribe_audio", language=language)
        try:
            if not self._initialized:
                journaling_manager.recordError("Wernicke's area not initialized")
                raise RuntimeError("Wernicke's area not initialized")
                
            # Use LLM's Whisper functionality
            response = await self._llm.send_whisper(audio_data, language)
            
            # Process transcribed text through LLM for better understanding
            if response.get("text"):
                processed_text = await self._llm.process_input(response["text"])
                response["processed_text"] = processed_text
            
            journaling_manager.recordInfo("Audio transcribed successfully")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error transcribing audio: {e}")
            raise
            
    async def extract_meaning(self, text: str) -> Dict[str, Any]:
        """Extract meaning and context from text"""
        journaling_manager.recordScope("WernickeArea.extract_meaning", text=text)
        try:
            if not self._initialized:
                journaling_manager.recordError("Wernicke's area not initialized")
                raise RuntimeError("Wernicke's area not initialized")
                
            # Use LLM to extract meaning
            prompt = f"Analyze the following text and extract its meaning, key concepts, and context. Return a JSON with 'main_idea' (string), 'key_concepts' (list), 'context' (string), and 'tone' (string): {text}"
            response = await self._llm.process_input(prompt)
            
            journaling_manager.recordInfo("Meaning extracted successfully")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error extracting meaning: {e}")
            raise
            
    async def analyze_context(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze text in context"""
        journaling_manager.recordScope("WernickeArea.analyze_context", text=text, context=context)
        try:
            if not self._initialized:
                journaling_manager.recordError("Wernicke's area not initialized")
                raise RuntimeError("Wernicke's area not initialized")
                
            # Use LLM to analyze context
            prompt = f"Analyze the following text in the given context. Return a JSON with 'interpretation' (string), 'relevance' (string), 'implications' (list), and 'connections' (list):\nText: {text}\nContext: {context}"
            response = await self._llm.process_input(prompt)
            
            journaling_manager.recordInfo("Context analyzed successfully")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error analyzing context: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up Wernicke's area"""
        journaling_manager.recordScope("WernickeArea.cleanup")
        try:
            await self._llm.cleanup()
            self._initialized = False
            self.current_state["model"] = None
            journaling_manager.recordInfo("Wernicke's area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up Wernicke's area: {e}")
            raise 