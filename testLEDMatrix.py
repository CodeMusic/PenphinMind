"""
Test script for LED Matrix functionality
"""

import logging
from typing import Dict, Any, Optional
from .Mind.mind import Mind

logger = logging.getLogger(__name__)

async def test_led_matrix():
    """Test LED Matrix functionality"""
    try:
        mind = Mind()
        await mind.initialize()
        
        # Test LED matrix
        await mind.set_background(255, 0, 0)  # Red
        await asyncio.sleep(1)
        await mind.set_background(0, 255, 0)  # Green
        await asyncio.sleep(1)
        await mind.set_background(0, 0, 255)  # Blue
        await asyncio.sleep(1)
        await mind.clear_matrix()
        
    except Exception as e:
        logger.error(f"LED Matrix test error: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_led_matrix()) 