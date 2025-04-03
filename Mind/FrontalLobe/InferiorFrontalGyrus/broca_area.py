"""
Neurological Function:
    Broca's Area (Inferior Frontal Gyrus) handles:
    - Speech production
    - Language generation
    - Grammar processing
    - Sentence structure
    - Word formation
    - Articulatory planning
    - Language fluency

Project Function:
    Handles language production:
    - Text generation
    - Grammar checking
    - Sentence construction
    - Word selection
    - Language fluency
"""

import logging
from typing import Dict, Any, Optional, List
from ...config import CONFIG
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from ...CorpusCallosum.api_commands import CommandType, TTSCommand
from .llm import LLM

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

def get_synaptic_pathways():
    """Get SynapticPathways while avoiding circular imports"""
    from ...CorpusCallosum.synaptic_pathways import SynapticPathways
    return SynapticPathways

class BrocaArea:
    """Handles language production and speech generation"""
    
    def __init__(self):
        """Initialize Broca's area"""
        journaling_manager.recordScope("BrocaArea.__init__")
        self._initialized = False
        self._processing = False
        self._llm = LLM()
        self.current_state = {
            "status": "idle",
            "error": None
        }
        
    async def initialize(self) -> None:
        """Initialize Broca's area"""
        journaling_manager.recordScope("BrocaArea.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Broca's area already initialized")
            return
            
        try:
            # Initialize LLM
            await self._llm.initialize()
            
            # Initialize components
            self._initialized = True
            journaling_manager.recordInfo("Broca's area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize Broca's area: {e}")
            raise
            
    async def generate_speech(self, text: str, voice_id: str = "default", speed: float = 1.0, pitch: float = 1.0) -> Dict[str, Any]:
        """Generate speech from text"""
        journaling_manager.recordScope("BrocaArea.generate_speech", text=text)
        try:
            if not self._initialized:
                journaling_manager.recordError("Broca's area not initialized")
                raise RuntimeError("Broca's area not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already processing speech")
                raise RuntimeError("Already processing speech")
                
            self._processing = True
            self.current_state["status"] = "processing"
            
            # Use LLM to process text first
            processed_text = await self._llm.process_input(text)
            
            # Create TTS command with processed text
            command = TTSCommand(
                command_type=CommandType.TTS,
                text=processed_text.get("response", text),
                voice_id=voice_id,
                speed=speed,
                pitch=pitch
            )
            
            # Send command through synaptic pathways
            SynapticPathways = get_synaptic_pathways()
            response = await SynapticPathways.send_command(command.to_dict())
            
            self._processing = False
            self.current_state["status"] = "completed"
            journaling_manager.recordInfo("Speech generated successfully")
            
            return response
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error generating speech: {e}")
            raise
            
    async def check_grammar(self, text: str) -> Dict[str, Any]:
        """Check grammar and sentence structure"""
        journaling_manager.recordScope("BrocaArea.check_grammar", text=text)
        try:
            if not self._initialized:
                journaling_manager.recordError("Broca's area not initialized")
                raise RuntimeError("Broca's area not initialized")
                
            # Use LLM to check grammar
            prompt = f"Check the grammar and sentence structure of the following text. Return a JSON with 'is_correct' (boolean), 'corrections' (list of corrections), and 'explanation' (string): {text}"
            response = await self._llm.process_input(prompt)
            
            journaling_manager.recordInfo("Grammar check completed")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error checking grammar: {e}")
            raise
            
    async def construct_sentence(self, words: List[str]) -> Dict[str, Any]:
        """Construct a grammatically correct sentence from words"""
        journaling_manager.recordScope("BrocaArea.construct_sentence", words=words)
        try:
            if not self._initialized:
                journaling_manager.recordError("Broca's area not initialized")
                raise RuntimeError("Broca's area not initialized")
                
            # Use LLM to construct sentence
            prompt = f"Construct a grammatically correct sentence using these words: {', '.join(words)}"
            response = await self._llm.process_input(prompt)
            
            journaling_manager.recordInfo("Sentence constructed successfully")
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"Error constructing sentence: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up Broca's area"""
        journaling_manager.recordScope("BrocaArea.cleanup")
        try:
            await self._llm.cleanup()
            self._initialized = False
            self.current_state["model"] = None
            journaling_manager.recordInfo("Broca's area cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up Broca's area: {e}")
            raise 