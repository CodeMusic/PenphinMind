"""
Neurological Terms:
    - Primary Visual Cortex
    - Striate Cortex
    - V1 (Visual Area 1)
    - Brodmann Area 17

Neurological Function:
    Primary Visual Area (V1) processes basic visual information:
    - Edge detection
    - Basic shape processing
    - Color detection
    - Orientation selectivity
    - Spatial frequency analysis
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from PIL import Image
import asyncio

logger = logging.getLogger(__name__)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class PrimaryVisualArea:
    """Core visual processing and LED matrix control"""
    
    def __init__(self):
        """Initialize the primary visual area"""
        self._initialized = False
        self._processing = False
        self._matrix = None
        
    async def initialize(self) -> None:
        """Initialize the primary visual area"""
        if self._initialized:
            return
            
        try:
            # Initialize LED matrix
            from rgbmatrix import RGBMatrix, RGBMatrixOptions
            
            # Setup matrix options
            options = RGBMatrixOptions()
            
            # Load settings from CONFIG if available
            if hasattr(CONFIG, 'led_matrix'):
                led_config = CONFIG.led_matrix
                options.rows = led_config.get('rows', 64)
                options.cols = led_config.get('cols', 64)
                options.chain_length = led_config.get('chain_length', 1)
                options.parallel = led_config.get('parallel', 1)
                options.hardware_mapping = led_config.get('hardware_mapping', 'regular')
                options.brightness = led_config.get('brightness', 30)
                options.disable_hardware_pulsing = led_config.get('disable_hardware_pulsing', True)
                options.gpio_slowdown = led_config.get('gpio_slowdown', 2)
                options.pwm_lsb_nanoseconds = led_config.get('pwm_lsb_nanoseconds', 130)
                options.pwm_bits = led_config.get('pwm_bits', 11)
            else:
                # Default settings if CONFIG doesn't have led_matrix
                options.rows = 64
                options.cols = 64
                options.chain_length = 1
                options.parallel = 1
                options.hardware_mapping = 'regular'
                options.brightness = 30
                options.disable_hardware_pulsing = True
                options.gpio_slowdown = 2
                options.pwm_lsb_nanoseconds = 130
                options.pwm_bits = 11
                
            # Create RGBMatrix instance
            self._matrix = RGBMatrix(options=options)
            self._initialized = True
            journaling_manager.recordInfo("Primary visual area initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize primary visual area: {e}")
            raise
            
    async def toggle_processing(self, enabled: bool) -> None:
        """Toggle visual processing"""
        self._processing = enabled
        logger.info(f"Visual processing {'enabled' if enabled else 'disabled'}")
        
    async def process_raw_visual(self, image_data: bytes) -> Dict[str, Any]:
        """Process raw visual input"""
        try:
            # Convert image data to numpy array
            image = np.frombuffer(image_data, dtype=np.uint8)
            image = image.reshape((CONFIG.visual_height, CONFIG.visual_width, 3))
            
            # Process basic visual features
            features = {
                "brightness": np.mean(image),
                "contrast": np.std(image),
                "edges": self._detect_edges(image)
            }
            
            return features
            
        except Exception as e:
            journaling_manager.recordError(f"Error processing raw visual: {e}")
            return {}
            
    def _detect_edges(self, image: np.ndarray) -> np.ndarray:
        """Detect edges in image"""
        try:
            # Convert to grayscale
            gray = np.mean(image, axis=2)
            
            # Simple edge detection
            edges = np.zeros_like(gray)
            edges[1:-1, 1:-1] = np.abs(gray[1:-1, 2:] - gray[1:-1, :-2]) + \
                               np.abs(gray[2:, 1:-1] - gray[:-2, 1:-1])
            
            return edges
            
        except Exception as e:
            journaling_manager.recordError(f"Error detecting edges: {e}")
            return np.zeros_like(image[:,:,0])

    async def set_image(self, image: Image.Image) -> bool:
        """
        Sets an image to the matrix (async version)
        
        Args:
            image: PIL Image to display
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._initialized or self._matrix is None:
            journaling_manager.recordError("Cannot set image: PrimaryVisualArea not initialized")
            return False
            
        try:
            # Use the matrix directly
            self._matrix.SetImage(image)
            return True
        except Exception as e:
            journaling_manager.recordError(f"Error setting image: {e}")
            return False
            
    def SetImage(self, image: Image.Image) -> None:
        """
        Non-async wrapper to set an image to the matrix.
        This provides compatibility with RGBMatrix interface.
        
        Args:
            image: PIL Image to display
        """
        if not self._initialized or self._matrix is None:
            journaling_manager.recordError("Cannot set image: PrimaryVisualArea not initialized")
            return
            
        try:
            # Direct call to matrix
            self._matrix.SetImage(image)
        except Exception as e:
            journaling_manager.recordError(f"Error in SetImage: {e}")
            
    async def test_pattern(self) -> bool:
        """
        Display a test pattern to verify matrix works
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._initialized or self._matrix is None:
            journaling_manager.recordError("Cannot display test pattern: Matrix not initialized")
            return False
            
        try:
            import random
            
            # Create a new image
            width = CONFIG.visual_width if hasattr(CONFIG, 'visual_width') else 64
            height = CONFIG.visual_height if hasattr(CONFIG, 'visual_height') else 64
            image = Image.new("RGB", (width, height))
            pixels = image.load()
            
            # Generate a random pattern
            for y in range(height):
                for x in range(width):
                    if random.randint(0, 1):
                        # Create varying colors
                        r = random.randint(0, 255)
                        g = random.randint(0, 255)
                        b = random.randint(0, 255)
                        pixels[x, y] = (r, g, b)
            
            # Display on matrix
            self._matrix.SetImage(image)
            journaling_manager.recordInfo("Test pattern displayed on matrix")
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"Error displaying test pattern: {e}")
            return False

    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._initialized = False
            journaling_manager.recordInfo("Primary visual area cleaned up")
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up primary visual area: {e}")
            raise 