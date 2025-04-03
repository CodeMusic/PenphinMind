"""
Primary Visual Area - Core visual processing and LED matrix control
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...CorpusCallosum.neural_commands import CommandType
from config import CONFIG  # Use absolute import
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image

logger = logging.getLogger(__name__)

class PrimaryVisualArea:
    """Core visual processing and LED matrix control"""
    
    def __init__(self):
        """Initialize the primary visual area"""
        self._initialized = False
        self._processing = False
        self._matrix = None
        self._options = RGBMatrixOptions()
        self._options.rows = 64
        self._options.cols = 64
        self._options.chain_length = 1
        self._options.parallel = 1
        self._options.hardware_mapping = 'regular'
        self._options.brightness = 30
        self._options.disable_hardware_pulsing = True
        
    async def initialize(self) -> None:
        """Initialize the primary visual area"""
        if self._initialized:
            return
            
        try:
            # Initialize LED matrix with the same options as test
            self._matrix = RGBMatrix(options=self._options)
            self._initialized = True
            logger.info("Primary visual area initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize primary visual area: {e}")
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
            logger.error(f"Error processing raw visual: {e}")
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
            logger.error(f"Error detecting edges: {e}")
            return np.zeros_like(image[:,:,0]) 

    async def set_image(self, image: Image.Image) -> None:
        """Set an image to the matrix"""
        if not self._initialized:
            raise RuntimeError("Matrix not initialized")
        self._matrix.SetImage(image)

    async def clear(self) -> None:
        """Clear the matrix"""
        if not self._initialized:
            raise RuntimeError("Matrix not initialized")
        self._matrix.Clear()