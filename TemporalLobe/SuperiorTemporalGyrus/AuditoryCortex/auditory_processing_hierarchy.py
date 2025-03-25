"""
Neurological Function:
    The auditory processing hierarchy in the Superior Temporal Gyrus follows
    a core-belt-parabelt organization, with increasing complexity of processing
    at each level.

Project Function:
    Coordinates the hierarchical flow of auditory processing through:
    - Core areas (Primary Acoustic Area)
    - Belt areas (Lateral Belt)
    - Parabelt areas
    - Integration with higher processing areas
"""

from typing import Dict, Any
from ..HeschlGyrus.primary_acoustic_area import PrimaryAcousticArea
from .lateral_belt_area import LateralBeltArea
from .parabelt_area import ParabeltArea

class AuditoryProcessingHierarchy:
    """
    Coordinates the hierarchical flow of auditory processing through
    the Superior Temporal Gyrus.
    """
    
    def __init__(self):
        self.primary_area = PrimaryAcousticArea()
        self.lateral_belt = LateralBeltArea()
        self.parabelt = ParabeltArea()
        
    async def process_auditory_stream(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process audio through the complete hierarchy
        
        Args:
            audio_data: Raw audio input
            
        Returns:
            Dict containing processed features from all levels
        """
        # Primary processing
        primary_features = await self.primary_area.process_frequency_components(audio_data)
        
        # Belt processing
        belt_features = await self.lateral_belt.analyze_spectrotemporal_patterns(audio_data)
        
        # Parabelt processing
        integrated_features = await self.parabelt.integrate_auditory_features(audio_data)
        
        return {
            "primary": primary_features,
            "belt": belt_features,
            "parabelt": integrated_features
        } 