"""
Neurological Function:
    Primary somatosensory cortex (S1) processes tactile information.
    - Brodmann areas 1, 2, and 3
    - Processes touch, pressure, temperature, and pain
    - Maps physical sensations to specific body regions

Project Function:
    Maps to touch/button/GPIO functionality:
    - Button press/release detection
    - GPIO input handling
    - Tactile feedback processing
"""

import asyncio
from typing import Optional, Callable, Any, Dict
import logging
import platform
from pathlib import Path

from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...CorpusCallosum.neural_commands import CommandType, SystemCommand
from ...config import CONFIG

# Use RPi.GPIO if available, otherwise use mock
try:
    import RPi.GPIO as GPIO
    logger = logging.getLogger(__name__)
    logger.info("Using RPi.GPIO module")
except ImportError:
    from . import mock_gpio as GPIO
    logger = logging.getLogger(__name__)
    logger.info("Using mock GPIO module for development")

class TactileStimulusError(Exception):
    """Error handling tactile input"""
    pass

class PrimaryArea:
    """Primary somatosensory area handling tactile input"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.button_pin = CONFIG.tactile_button_pin
        self.pressed = False
        self.press_callback: Optional[Callable] = None
        self.release_callback: Optional[Callable] = None
        self._setup_tactile_pathway()
        
    def _setup_tactile_pathway(self) -> None:
        """Configure GPIO for tactile input"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                self.button_pin, 
                GPIO.BOTH, 
                callback=self._process_tactile_stimulus,
                bouncetime=50
            )
            self.logger.info(f"Tactile pathway initialized on pin {self.button_pin}")
        except Exception as e:
            self.logger.error(f"Tactile pathway setup error: {e}")
            raise TactileStimulusError(f"Failed to setup tactile pathway: {e}")
            
    def _process_tactile_stimulus(self, channel: int) -> None:
        """Process incoming tactile stimulus"""
        try:
            state = GPIO.input(self.button_pin)
            self.pressed = not state  # Button is active LOW
            
            if self.pressed and self.press_callback:
                asyncio.create_task(self._transmit_tactile_signal("tactile_press"))
                self.press_callback()
            elif not self.pressed and self.release_callback:
                asyncio.create_task(self._transmit_tactile_signal("tactile_release"))
                self.release_callback()
                
        except Exception as e:
            self.logger.error(f"Tactile stimulus processing error: {e}")
            
    async def _transmit_tactile_signal(self, signal_type: str) -> None:
        """Transmit tactile signal through synaptic pathways"""
        try:
            await SynapticPathways.transmit_json(
                SystemCommand(
                    command_type=CommandType.SYSTEM,
                    event=signal_type,
                    data={
                        "pin": self.button_pin,
                        "state": self.pressed
                    }
                )
            )
        except Exception as e:
            self.logger.error(f"Tactile signal transmission error: {e}")
            
    def register_press_receptor(self, callback: Callable) -> None:
        """Register callback for tactile press"""
        self.press_callback = callback
        
    def register_release_receptor(self, callback: Callable) -> None:
        """Register callback for tactile release"""
        self.release_callback = callback
        
    async def await_tactile_press(self) -> None:
        """Wait for tactile press stimulus"""
        while not self.pressed:
            await asyncio.sleep(0.01)
            
    async def await_tactile_release(self) -> None:
        """Wait for tactile release stimulus"""
        while self.pressed:
            await asyncio.sleep(0.01)
            
    def cleanup_tactile_pathway(self) -> None:
        """Clean up tactile pathway resources"""
        try:
            GPIO.cleanup(self.button_pin)
            self.logger.info("Tactile pathway cleanup complete")
        except Exception as e:
            self.logger.error(f"Tactile pathway cleanup error: {e}")
            raise TactileStimulusError(f"Failed to cleanup tactile pathway: {e}")
            
    async def process_tactile_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process complex tactile input data
        
        Args:
            input_data: Dictionary containing tactile input parameters
            
        Returns:
            Dict[str, Any]: Processed tactile data
        """
        try:
            # Process tactile input and return results
            # This can be expanded for more complex tactile processing
            return {
                "pin": self.button_pin,
                "state": self.pressed,
                "processed": True,
                **input_data
            }
        except Exception as e:
            self.logger.error(f"Tactile input processing error: {e}")
            return {
                "error": str(e),
                "processed": False
            } 