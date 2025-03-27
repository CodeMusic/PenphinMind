"""
Mock GPIO module for development environments

This module provides a mock implementation of RPi.GPIO for development
and testing on non-Raspberry Pi systems.
"""

import logging
from typing import Optional, Callable, Dict
from enum import Enum
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

logger = logging.getLogger(__name__)

# GPIO modes
BCM = "BCM"
BOARD = "BOARD"

# Pin directions
IN = "IN"
OUT = "OUT"

# Pull up/down resistor configurations
PUD_UP = "PUD_UP"
PUD_DOWN = "PUD_DOWN"
PUD_OFF = "PUD_OFF"

# Edge detection types
BOTH = "BOTH"
RISING = "RISING"
FALLING = "FALLING"

# Pin states
HIGH = 1
LOW = 0

# Software PWM
HARD_PWM = 0
SOFT_PWM = 1

# Version info (for compatibility)
VERSION = "0.7.0"
RPI_INFO = {
    "P1_REVISION": 3,
    "RAM": "1024M",
    "REVISION": "a02082",
    "TYPE": "Pi 3 Model B",
    "PROCESSOR": "BCM2837",
    "MANUFACTURER": "Embest"
}

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class MockGPIO:
    """Mock GPIO implementation"""
    
    def __init__(self):
        self._mode: Optional[str] = None
        self._pin_states: Dict[int, int] = {}
        self._pin_events: Dict[int, Dict] = {}
        self._cleanup_handlers: Dict[int, Callable] = {}
        self._pwm_pins: Dict[int, Dict] = {}
        
    def setmode(self, mode: str) -> None:
        """Set GPIO mode"""
        try:
            self._mode = mode
            journaling_manager.recordDebug(f"GPIO mode set to {mode}")
        except Exception as e:
            journaling_manager.recordError(f"Error setting GPIO mode: {e}")
            raise
        
    def setup(self, pin: int, direction: str, pull_up_down: str = None) -> None:
        """Set up GPIO pin"""
        try:
            self._pin_states[pin] = HIGH if pull_up_down == PUD_UP else LOW
            journaling_manager.recordDebug(f"Pin {pin} setup with direction {direction} and pull_up_down {pull_up_down}")
        except Exception as e:
            journaling_manager.recordError(f"Error setting up GPIO pin: {e}")
            raise
        
    def input(self, pin: int) -> int:
        """Read input from pin"""
        return self._pin_states.get(pin, LOW)
        
    def output(self, pin: int, state: bool) -> None:
        """Set GPIO output"""
        try:
            self._pin_states[pin] = state
            journaling_manager.recordDebug(f"Pin {pin} set to {state}")
        except Exception as e:
            journaling_manager.recordError(f"Error setting GPIO output: {e}")
            raise
        
    def add_event_detect(self, pin: int, edge: str, callback: Callable) -> None:
        """Add event detection to GPIO pin"""
        try:
            self._pin_events[pin] = {
                "edge": edge,
                "callback": callback,
                "bouncetime": None
            }
            journaling_manager.recordDebug(f"Event detection added to pin {pin}")
        except Exception as e:
            journaling_manager.recordError(f"Error adding event detection: {e}")
            raise
        
    def remove_event_detect(self, pin: int) -> None:
        """Remove event detection from GPIO pin"""
        try:
            if pin in self._pin_events:
                del self._pin_events[pin]
                journaling_manager.recordDebug(f"Event detection removed from pin {pin}")
        except Exception as e:
            journaling_manager.recordError(f"Error removing event detection: {e}")
            raise
        
    def cleanup(self) -> None:
        """Clean up GPIO resources"""
        try:
            self._pin_states.clear()
            self._pin_events.clear()
            self._pwm_pins.clear()
            journaling_manager.recordDebug("All GPIO resources cleaned up")
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up GPIO: {e}")
            raise
        
    def cleanup_pin(self, pin: int) -> None:
        """Clean up specific GPIO pin"""
        try:
            if pin in self._pin_states:
                del self._pin_states[pin]
            if pin in self._pin_events:
                del self._pin_events[pin]
            if pin in self._pwm_pins:
                del self._pwm_pins[pin]
            journaling_manager.recordDebug(f"Pin {pin} cleaned up")
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up GPIO pin: {e}")
            raise
        
    def simulate_input(self, pin: int, state: bool) -> None:
        """Simulate input on GPIO pin"""
        try:
            if pin in self._pin_events:
                old_state = self._pin_states.get(pin, LOW)
                self._pin_states[pin] = state
                
                event = self._pin_events[pin]
                if event["callback"] and (
                    event["edge"] == BOTH or
                    (event["edge"] == RISING and state == HIGH) or
                    (event["edge"] == FALLING and state == LOW)
                ):
                    event["callback"](pin)
                    journaling_manager.recordDebug(f"Simulated input on pin {pin}: {state}")
        except Exception as e:
            journaling_manager.recordError(f"Error simulating GPIO input: {e}")
            raise
        
    def PWM(self, pin: int, frequency: float) -> 'PWM':
        """Create PWM instance for a pin"""
        if pin not in self._pwm_pins:
            self._pwm_pins[pin] = {"frequency": frequency, "duty_cycle": 0}
        return PWM(pin, frequency)

class PWM:
    """Mock PWM class"""
    
    def __init__(self, pin: int, frequency: float):
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0
        
    def start(self, duty_cycle: float) -> None:
        """Start PWM"""
        try:
            self.duty_cycle = duty_cycle
            journaling_manager.recordDebug(f"PWM started on pin {self.pin} with duty cycle {duty_cycle}")
        except Exception as e:
            journaling_manager.recordError(f"Error starting PWM: {e}")
            raise
        
    def stop(self) -> None:
        """Stop PWM"""
        try:
            journaling_manager.recordDebug(f"PWM stopped on pin {self.pin}")
        except Exception as e:
            journaling_manager.recordError(f"Error stopping PWM: {e}")
            raise
        
    def ChangeDutyCycle(self, duty_cycle: float) -> None:
        """Change PWM duty cycle"""
        try:
            self.duty_cycle = duty_cycle
            journaling_manager.recordDebug(f"PWM duty cycle changed to {duty_cycle} on pin {self.pin}")
        except Exception as e:
            journaling_manager.recordError(f"Error changing PWM duty cycle: {e}")
            raise
        
    def ChangeFrequency(self, frequency: float) -> None:
        """Change PWM frequency"""
        try:
            self.frequency = frequency
            journaling_manager.recordDebug(f"PWM frequency changed to {frequency} on pin {self.pin}")
        except Exception as e:
            journaling_manager.recordError(f"Error changing PWM frequency: {e}")
            raise

# Create global instance
_gpio = MockGPIO()

# Export module functions
setmode = _gpio.setmode
setup = _gpio.setup
input = _gpio.input
output = _gpio.output
add_event_detect = _gpio.add_event_detect
remove_event_detect = _gpio.remove_event_detect
cleanup = _gpio.cleanup
simulate_input = _gpio.simulate_input
PWM = _gpio.PWM 