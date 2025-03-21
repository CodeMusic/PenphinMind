import RPi.GPIO as GPIO
from MotorCortex.pin_definitions import PinDefinitions
import time

class ButtonManager:
    def __init__(self):
        self.pins = PinDefinitions()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pins.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.is_pressed = False

    def wait_for_press(self):
        """
        Wait for button press and set state
        """
        while GPIO.input(self.pins.BUTTON_PIN):
            time.sleep(0.01)
        self.is_pressed = True
        return True

    def wait_for_release(self):
        """
        Wait for button release and reset state
        """
        while not GPIO.input(self.pins.BUTTON_PIN):
            time.sleep(0.01)
        self.is_pressed = False
        return True

    def is_button_pressed(self):
        """
        Return current button state
        """
        return self.is_pressed

    def __del__(self):
        """
        Cleanup GPIO on object destruction
        """
        GPIO.cleanup() 