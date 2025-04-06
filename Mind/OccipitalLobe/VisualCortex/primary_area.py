"""
Primary Visual Area - Core visual processing and LED matrix control
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...Subcortex.api_commands import CommandType
from config import CONFIG
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

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
        self._options = RGBMatrixOptions()
        
        # Load settings from CONFIG if available
        if hasattr(CONFIG, 'led_matrix'):
            led_config = CONFIG.led_matrix
            self._options.rows = led_config.get('rows', 64)
            self._options.cols = led_config.get('cols', 64)
            self._options.chain_length = led_config.get('chain_length', 1)
            self._options.parallel = led_config.get('parallel', 1)
            self._options.hardware_mapping = led_config.get('hardware_mapping', 'regular')
            self._options.brightness = led_config.get('brightness', 30)
            self._options.disable_hardware_pulsing = led_config.get('disable_hardware_pulsing', True)
            self._options.gpio_slowdown = led_config.get('gpio_slowdown', 2)
            self._options.pwm_lsb_nanoseconds = led_config.get('pwm_lsb_nanoseconds', 130)
            self._options.pwm_bits = led_config.get('pwm_bits', 11)
            logger.info(f"Loaded LED matrix settings from CONFIG. Brightness: {self._options.brightness}%, HW Pulsing: {'disabled' if self._options.disable_hardware_pulsing else 'enabled'}")
        else:
            # Default settings if CONFIG doesn't have led_matrix
            self._options.rows = 64
            self._options.cols = 64
            self._options.chain_length = 1
            self._options.parallel = 1
            self._options.hardware_mapping = 'regular'
            self._options.brightness = 30
            self._options.disable_hardware_pulsing = True
            self._options.gpio_slowdown = 2
            self._options.pwm_lsb_nanoseconds = 130
            self._options.pwm_bits = 11
            logger.info("Using default LED matrix settings (CONFIG.led_matrix not found)")
        
    async def initialize(self) -> bool:
        """
        Initialize the primary visual area
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if self._initialized:
            logger.info("Primary visual area already initialized")
            return True
            
        try:
            # First check if SynapticPathways is properly initialized
            # If not, we can still proceed with direct matrix creation
            synaptic_connected = False
            try:
                # Only try to check synaptic connection if the class is properly imported
                if hasattr(SynapticPathways, 'is_initialized') and SynapticPathways.is_initialized():
                    synaptic_connected = True
                    logger.info("SynapticPathways connected, checking for hardware before initializing")
            except Exception as e:
                logger.warning(f"SynapticPathways not available: {e}")
                # Continue with direct matrix regardless
            
            # Initialize LED matrix with options
            logger.info("Initializing RGB Matrix...")
            try:
                # Create the RGBMatrix instance directly
                self._matrix = RGBMatrix(options=self._options)
                logger.info("RGB Matrix initialized successfully")
            except Exception as e:
                logger.error(f"Failed to create RGBMatrix: {e}")
                journaling_manager.recordError(f"Failed to create RGBMatrix: {e}")
                return False
                
            self._initialized = True
            logger.info("Primary visual area initialized successfully")
            journaling_manager.recordInfo("Primary visual area initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize primary visual area: {e}")
            journaling_manager.recordError(f"Failed to initialize primary visual area: {e}")
            # Don't raise the exception, just return False so callers can try fallback options
            return False
            
    async def toggle_processing(self, enabled: bool) -> None:
        """Toggle visual processing"""
        self._processing = enabled
        logger.info(f"Visual processing {'enabled' if enabled else 'disabled'}")
        
    async def process_raw_visual(self, image_data: bytes) -> Dict[str, Any]:
        """Process raw visual input"""
        if not self._initialized:
            logger.warning("Cannot process visual input: PrimaryVisualArea not initialized")
            return {"error": "Not initialized"}
            
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
            logger.error(f"Error processing raw visual: {e}")
            journaling_manager.recordError(f"Error processing raw visual: {e}")
            return {"error": str(e)}
            
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
            logger.error(f"Error detecting edges: {e}")
            journaling_manager.recordError(f"Error detecting edges: {e}")
            return np.zeros_like(image[:,:,0]) 

    async def set_image(self, image: Image.Image) -> bool:
        """
        Sets an image to the matrix.
        
        Args:
            image: PIL Image to set on the matrix
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._initialized or self._matrix is None:
            logger.error("Cannot set image: PrimaryVisualArea not initialized")
            journaling_manager.recordError("Cannot set image: PrimaryVisualArea not initialized")
            return False
            
        try:
            # Ensure image dimensions match matrix dimensions
            if image.size != (self._options.cols, self._options.rows):
                logger.warning(f"Image size {image.size} doesn't match matrix size ({self._options.cols}, {self._options.rows}). Resizing...")
                image = image.resize((self._options.cols, self._options.rows))
                
            # Use the SetImage method to display the image on the matrix
            self._matrix.SetImage(image)
            journaling_manager.recordInfo(f"Image set on primary visual area: {image.size}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting image: {e}")
            journaling_manager.recordError(f"Error setting image: {e}")
            return False

    async def clear(self) -> bool:
        """
        Clear the matrix
        
        Returns:
            bool: True if operation succeeded, False otherwise
        """
        if not self._initialized or self._matrix is None:
            logger.warning("Cannot clear: PrimaryVisualArea not initialized")
            return False
            
        try:
            self._matrix.Clear()
            journaling_manager.recordInfo("Matrix cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing matrix: {e}")
            journaling_manager.recordError(f"Error clearing matrix: {e}")
            return False
            
    def get_options(self) -> RGBMatrixOptions:
        """Get a copy of the current matrix options"""
        return self._options
        
    def is_initialized(self) -> bool:
        """Check if the visual area is initialized"""
        return self._initialized and self._matrix is not None

    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self._initialized = False
            journaling_manager.recordInfo("Primary visual area cleaned up")
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up primary visual area: {e}")
            raise

    async def test_pattern(self) -> bool:
        """
        Display a test pattern on the matrix to verify it's working.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._initialized or self._matrix is None:
            logger.error("Cannot display test pattern: PrimaryVisualArea not initialized")
            return False
            
        try:
            import random
            from PIL import Image
            
            # Create a new image
            width, height = self._options.cols, self._options.rows
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
            
            # Display the image on the matrix
            self._matrix.SetImage(image)
            logger.info("Test pattern displayed on matrix")
            return True
            
        except Exception as e:
            logger.error(f"Error displaying test pattern: {e}")
            return False