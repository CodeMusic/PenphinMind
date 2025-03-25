"""
Integration area for the Auditory Cortex, coordinating speech and audio processing
"""

from typing import Dict, Any
from CorpusCallosum.synaptic_pathways import SynapticPathways
from CorpusCallosum.neural_commands import CommandType, LLMCommand, TTSCommand, ASRCommand
from config import CONFIG
from .belt_area import BeltArea
from ..HeschlGyrus.primary_acoustic_area import PrimaryAcousticArea

class IntegrationArea:
    """Integration area for auditory processing"""
    
    def __init__(self):
        self.belt_area = BeltArea()
        self.primary_acoustic = PrimaryAcousticArea()
        
    async def process_auditory_input(self, audio_data: bytes) -> Dict[str, Any]:
        """Process incoming audio data"""
        try:
            # First process through primary acoustic area
            basic_features = await self.primary_acoustic.process_acoustic_signal(audio_data)
            
            # Then process through belt area for complex features
            complex_features = await self.belt_area.process_complex_features(audio_data)
            
            # Finally process through language model
            response = await SynapticPathways.send_llm(
                prompt=complex_features.get("text", ""),
                max_tokens=CONFIG.llm_max_tokens,
                temperature=CONFIG.llm_temperature
            )
            
            return {
                "basic_features": basic_features,
                "complex_features": complex_features,
                "response": response.get("response", "")
            }
        except Exception as e:
            raise Exception(f"Error processing auditory input: {e}")
            
    async def process_text(self, text: str) -> str:
        """Process text input through the language model"""
        try:
            response = await SynapticPathways.send_llm(
                prompt=text,
                max_tokens=CONFIG.llm_max_tokens,
                temperature=CONFIG.llm_temperature
            )
            return response.get("response", "")
        except Exception as e:
            raise Exception(f"Error processing text: {e}")
            
    async def record_audio(self, duration: float) -> bytes:
        """Record audio for specified duration"""
        try:
            return await self.primary_acoustic.record_acoustic_signal(duration)
        except Exception as e:
            raise Exception(f"Error recording audio: {e}")

class BrocaArea:
    """Speech production area"""
    
    async def generate_speech(self, text: str) -> bytes:
        """Generate speech from text"""
        try:
            response = await SynapticPathways.send_tts(
                text=text,
                voice_id=CONFIG.tts_voice_id,
                speed=CONFIG.tts_speed,
                pitch=CONFIG.tts_pitch
            )
            return response.get("audio", b"")
        except Exception as e:
            raise Exception(f"Error generating speech: {e}")

class WernickeArea:
    """Speech comprehension area"""
    
    async def process_linguistic_content(self, audio_data: bytes) -> str:
        """Process audio into text"""
        try:
            response = await SynapticPathways.send_asr(
                audio_data=audio_data,
                language=CONFIG.asr_language,
                model_type=CONFIG.asr_model_type
            )
            return response.get("text", "")
        except Exception as e:
            raise Exception(f"Error processing linguistic content: {e}") 