"""
Coordinates information flow between auditory processing regions
"""
import logging
from typing import Dict, Any, Optional
from CorpusCallosum.synaptic_pathways import SynapticPathways
from .primary_area import PrimaryArea
from .lateral_belt_area import LateralBeltArea
from .wernicke_area import WernickeArea
from .broca_area import BrocaArea
from .planum_temporale_area import PlanumTemporaleArea

class IntegrationArea:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.primary_area = PrimaryArea()
        self.lateral_belt = LateralBeltArea()
        self.wernicke = WernickeArea()
        self.broca = BrocaArea()
        self.planum_temporale = PlanumTemporaleArea()

    async def process_auditory_input(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Coordinate complete auditory processing pipeline
        """
        try:
            # Filter and process basic audio
            filtered_audio = await self.primary_area.filter_background_noise(audio_data)
            if not filtered_audio:
                return {}

            # Process complex patterns
            patterns = await self.lateral_belt.process_complex_patterns(filtered_audio)
            
            # Process linguistic content if present
            text = await self.wernicke.process_linguistic_content(filtered_audio)
            
            # Analyze musical and rhythmic features
            musical_features = await self.planum_temporale.analyze_patterns(filtered_audio)

            return {
                "patterns": patterns,
                "text": text,
                "musical_features": musical_features
            }

        except Exception as e:
            self.logger.error(f"Auditory integration error: {e}")
            return {}

    async def generate_response(self, input_data: Dict[str, Any]) -> Optional[bytes]:
        """
        Generate appropriate auditory response
        """
        try:
            # Format response content
            response_text = await self.broca.format_response(input_data)
            if not response_text:
                return None

            # Generate speech
            return await self.broca.generate_speech(response_text)

        except Exception as e:
            self.logger.error(f"Response generation error: {e}")
            return None

    async def analyze_complex_features(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of audio features
        """
        try:
            raw_features = await self.primary_area.process_raw_audio(audio_data)
            spectral_features = await self.lateral_belt.process_complex_patterns(audio_data)
            rhythm_features = await self.planum_temporale.process_rhythm(audio_data)

            return {
                "raw": raw_features,
                "spectral": spectral_features,
                "rhythm": rhythm_features
            }

        except Exception as e:
            self.logger.error(f"Complex feature analysis error: {e}")
            return {} 