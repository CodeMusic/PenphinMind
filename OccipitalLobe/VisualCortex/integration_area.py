"""
Visual Integration Area
- Coordinates information flow between visual processing regions
- Integrates features into coherent percepts
"""
import logging
from typing import Dict, Any, Optional
from .primary_visual_area import PrimaryVisualArea
from .secondary_visual_area import SecondaryVisualArea
from .associative_visual_area import AssociativeVisualArea

class IntegrationArea:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.primary = PrimaryVisualArea()
        self.secondary = SecondaryVisualArea()
        self.associative = AssociativeVisualArea()
        self.callback = None  # From old visual_cortex

    async def process_visual_input(self, image_data: bytes) -> Dict[str, Any]:
        """Coordinate complete visual processing pipeline"""
        try:
            # Process basic features
            basic_features = await self.primary.process_raw_visual(image_data)
            
            # Analyze complex patterns
            complex_features = await self.secondary.analyze_complex_features(image_data)
            
            # Object recognition
            objects = await self.associative.recognize_objects(image_data)

            result = {
                "basic_features": basic_features,
                "complex_features": complex_features,
                "objects": objects
            }
            
            if self.callback:
                await self.callback(result)
                
            return result

        except Exception as e:
            self.logger.error(f"Visual integration error: {e}")
            return {}

    async def set_processing_callback(self, callback: callable) -> None:
        """Set callback for visual processing results"""
        self.callback = callback
        self.logger.info("Visual processing callback set") 