import asyncio
from typing import Optional, Callable, Any
import logging
from pathlib import Path
import RPi.GPIO as GPIO

from CorpusCallosum.synaptic_pathways import SynapticPathways
from CorpusCallosum.neuro_commands import CommandType, SystemCommand

logger = logging.getLogger(__name__)

class ButtonManager:
    """Manages button interactions and GPIO"""
    
    def __init__(self, button_pin: int = 17):
        self.logger = logger
        self.button_pin = button_pin
        self.pressed = False
        self.press_callback: Optional[Callable] = None
        self.release_callback: Optional[Callable] = None
        self._setup_gpio()
        
    def _setup_gpio(self) -> None:
        """Configure GPIO settings"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                self.button_pin, 
                GPIO.BOTH, 
                callback=self._handle_button_event,
                bouncetime=50
            )
            self.logger.info(f"GPIO initialized on pin {self.button_pin}")
        except Exception as e:
            self.logger.error(f"GPIO setup error: {e}")
            raise
            
    def _handle_button_event(self, channel: int) -> None:
        """Handle button state changes"""
        try:
            state = GPIO.input(self.button_pin)
            self.pressed = not state  # Button is active LOW
            
            if self.pressed and self.press_callback:
                asyncio.create_task(self._notify_system("button_press"))
                self.press_callback()
            elif not self.pressed and self.release_callback:
                asyncio.create_task(self._notify_system("button_release"))
                self.release_callback()
                
        except Exception as e:
            self.logger.error(f"Button event error: {e}")
            
    async def _notify_system(self, event: str) -> None:
        """Notify system of button events"""
        try:
            await SynapticPathways.transmit_command(
                SystemCommand(
                    command_type=CommandType.SYS,
                    action="button_event",
                    parameters={"event": event, "pin": self.button_pin}
                )
            )
        except Exception as e:
            self.logger.error(f"System notification error: {e}")
            
    def register_press_callback(self, callback: Callable) -> None:
        """Register callback for button press"""
        self.press_callback = callback
        
    def register_release_callback(self, callback: Callable) -> None:
        """Register callback for button release"""
        self.release_callback = callback
        
    async def wait_for_press(self) -> None:
        """Wait for button press"""
        while not self.pressed:
            await asyncio.sleep(0.01)
            
    async def wait_for_release(self) -> None:
        """Wait for button release"""
        while self.pressed:
            await asyncio.sleep(0.01)
            
    def cleanup(self) -> None:
        """Clean up GPIO resources"""
        try:
            GPIO.cleanup(self.button_pin)
            self.logger.info("GPIO cleanup complete")
        except Exception as e:
            self.logger.error(f"GPIO cleanup error: {e}") 