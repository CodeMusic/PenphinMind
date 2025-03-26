"""
Mock GPIO module for development environments

This module provides a mock implementation of RPi.GPIO for development
and testing on non-Raspberry Pi systems.
"""

import logging
from typing import Optional, Callable, Dict
from enum import Enum

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

class MockGPIO:
    """Mock GPIO implementation"""
    
    def __init__(self):
        self._mode: Optional[str] = None
        self._pin_states: Dict[int, int] = {}
        self._pin_events: Dict[int, Dict] = {}
        self._cleanup_handlers: Dict[int, Callable] = {}
        self._pwm_pins: Dict[int, Dict] = {}
        
    def setmode(self, mode: str) -> None:
        """Set GPIO mode (BCM or BOARD)"""
        self._mode = mode
        logger.debug(f"GPIO mode set to {mode}")
        
    def setup(self, pin: int, direction: str, pull_up_down: Optional[str] = None, initial: Optional[int] = None) -> None:
        """Setup GPIO pin"""
        self._pin_states[pin] = HIGH if pull_up_down == PUD_UP else LOW
        if initial is not None:
            self._pin_states[pin] = initial
        logger.debug(f"Pin {pin} setup with direction {direction} and pull_up_down {pull_up_down}")
        
    def input(self, pin: int) -> int:
        """Read input from pin"""
        return self._pin_states.get(pin, LOW)
        
    def output(self, pin: int, state: int) -> None:
        """Set output on pin"""
        self._pin_states[pin] = state
        logger.debug(f"Pin {pin} set to {state}")
        
    def add_event_detect(
        self,
        pin: int,
        edge: str,
        callback: Optional[Callable] = None,
        bouncetime: Optional[int] = None
    ) -> None:
        """Add edge detection on pin"""
        self._pin_events[pin] = {
            "edge": edge,
            "callback": callback,
            "bouncetime": bouncetime
        }
        logger.debug(f"Event detection added to pin {pin}")
        
    def remove_event_detect(self, pin: int) -> None:
        """Remove edge detection from pin"""
        if pin in self._pin_events:
            del self._pin_events[pin]
            logger.debug(f"Event detection removed from pin {pin}")
            
    def cleanup(self, pin: Optional[int] = None) -> None:
        """Cleanup GPIO resources"""
        if pin is None:
            # Cleanup all pins
            self._pin_states.clear()
            self._pin_events.clear()
            self._pwm_pins.clear()
            logger.debug("All GPIO resources cleaned up")
        elif pin in self._pin_states:
            # Cleanup specific pin
            del self._pin_states[pin]
            if pin in self._pin_events:
                del self._pin_events[pin]
            if pin in self._pwm_pins:
                del self._pwm_pins[pin]
            logger.debug(f"Pin {pin} cleaned up")
            
    def simulate_input(self, pin: int, state: int) -> None:
        """
        Simulate input on a pin (development only)
        
        Args:
            pin: Pin number to simulate
            state: State to simulate (HIGH or LOW)
        """
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
                logger.debug(f"Simulated input on pin {pin}: {state}")
                
    def PWM(self, pin: int, frequency: float) -> 'PWM':
        """Create PWM instance for a pin"""
        if pin not in self._pwm_pins:
            self._pwm_pins[pin] = {"frequency": frequency, "duty_cycle": 0}
        return PWM(pin, frequency)

class PWM:
    """Mock PWM implementation"""
    
    def __init__(self, pin: int, frequency: float):
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0
        self._running = False
        
    def start(self, duty_cycle: float) -> None:
        """Start PWM with duty cycle"""
        self.duty_cycle = duty_cycle
        self._running = True
        logger.debug(f"PWM started on pin {self.pin} with duty cycle {duty_cycle}")
        
    def stop(self) -> None:
        """Stop PWM"""
        self._running = False
        logger.debug(f"PWM stopped on pin {self.pin}")
        
    def ChangeDutyCycle(self, duty_cycle: float) -> None:
        """Change duty cycle"""
        self.duty_cycle = duty_cycle
        logger.debug(f"PWM duty cycle changed to {duty_cycle} on pin {self.pin}")
        
    def ChangeFrequency(self, frequency: float) -> None:
        """Change frequency"""
        self.frequency = frequency
        logger.debug(f"PWM frequency changed to {frequency} on pin {self.pin}")

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