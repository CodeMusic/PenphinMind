"""
Integration area for the Visual Cortex, handling visual processing and LED matrix control
"""

from typing import Dict, Any, Tuple
from CorpusCallosum.synaptic_pathways import SynapticPathways
from CorpusCallosum.neural_commands import CommandType, SystemCommand
from config import CONFIG
from .primary_visual_area import PrimaryVisualArea
from .secondary_visual_area import SecondaryVisualArea
from .associative_visual_area import AssociativeVisualArea

class IntegrationArea:
    """Integration area for visual processing"""
    
    def __init__(self):
        self.primary = PrimaryVisualArea()
        self.secondary = SecondaryVisualArea()
        self.associative = AssociativeVisualArea()
        
    async def set_background(self, r: int, g: int, b: int) -> None:
        """Set the LED matrix background color"""
        try:
            await SynapticPathways.send_system_command(
                command_type="set_background",
                data={"r": r, "g": g, "b": b}
            )
        except Exception as e:
            raise Exception(f"Error setting background: {e}")
            
    async def clear(self) -> None:
        """Clear the LED matrix"""
        try:
            await SynapticPathways.send_system_command(
                command_type="clear_matrix"
            )
        except Exception as e:
            raise Exception(f"Error clearing matrix: {e}")
            
    async def process_visual_input(self, image_data: bytes) -> Dict[str, Any]:
        """Process visual input data"""
        try:
            # Process basic features
            basic_features = await self.primary.process_raw_visual(image_data)
            
            # Process complex features
            complex_features = await self.secondary.analyze_complex_features(image_data)
            
            # Process object recognition
            objects = await self.associative.recognize_objects(image_data)
            
            return {
                "basic_features": basic_features,
                "complex_features": complex_features,
                "objects": objects
            }
        except Exception as e:
            raise Exception(f"Error processing visual input: {e}")
            
    async def initialize(self) -> None:
        """Initialize visual components"""
        # Initialize processing areas
        await self.primary.toggle_processing(True) 