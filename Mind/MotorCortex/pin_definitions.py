"""
Hardware Pin Configuration:
    - GPIO pin definitions
    - Motor control pins
    - PWM pins
    - Servo control pins
    - Button and LED pins
"""

from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class PinDefinitions:
    """
    Centralized pin configuration for motor control and physical outputs
    """
    def __init__(self):
        """Initialize pin definitions"""
        journaling_manager.recordScope("PinDefinitions.__init__")
        
        # GPIO Pin Definitions
        self.BUTTON_PIN = 17
        self.LED_PIN = 18
        journaling_manager.recordDebug("Initialized GPIO pins")
        
        # Motor Control Pins
        self.MOTOR_LEFT_FORWARD = 23
        self.MOTOR_LEFT_BACKWARD = 24
        self.MOTOR_RIGHT_FORWARD = 25
        self.MOTOR_RIGHT_BACKWARD = 26
        journaling_manager.recordDebug("Initialized motor control pins")
        
        # PWM Pins
        self.MOTOR_LEFT_PWM = 12
        self.MOTOR_RIGHT_PWM = 13
        journaling_manager.recordDebug("Initialized PWM pins")
        
        # Servo Pins
        self.SERVO_HEAD_PAN = 19
        self.SERVO_HEAD_TILT = 20
        journaling_manager.recordDebug("Initialized servo pins")
        
        journaling_manager.recordInfo("Pin definitions initialized")
        
    def get_all_pins(self) -> dict:
        """Get all pin definitions"""
        journaling_manager.recordScope("PinDefinitions.get_all_pins")
        pins = {
            "button": self.BUTTON_PIN,
            "led": self.LED_PIN,
            "motor": {
                "left_forward": self.MOTOR_LEFT_FORWARD,
                "left_backward": self.MOTOR_LEFT_BACKWARD,
                "right_forward": self.MOTOR_RIGHT_FORWARD,
                "right_backward": self.MOTOR_RIGHT_BACKWARD
            },
            "pwm": {
                "left": self.MOTOR_LEFT_PWM,
                "right": self.MOTOR_RIGHT_PWM
            },
            "servo": {
                "head_pan": self.SERVO_HEAD_PAN,
                "head_tilt": self.SERVO_HEAD_TILT
            }
        }
        journaling_manager.recordDebug(f"Retrieved all pin definitions: {pins}")
        return pins
        
    def validate_pins(self) -> bool:
        """Validate pin configuration"""
        journaling_manager.recordScope("PinDefinitions.validate_pins")
        try:
            # Check for duplicate pins
            all_pins = [
                self.BUTTON_PIN,
                self.LED_PIN,
                self.MOTOR_LEFT_FORWARD,
                self.MOTOR_LEFT_BACKWARD,
                self.MOTOR_RIGHT_FORWARD,
                self.MOTOR_RIGHT_BACKWARD,
                self.MOTOR_LEFT_PWM,
                self.MOTOR_RIGHT_PWM,
                self.SERVO_HEAD_PAN,
                self.SERVO_HEAD_TILT
            ]
            
            if len(all_pins) != len(set(all_pins)):
                journaling_manager.recordError("Duplicate pin assignments detected")
                return False
                
            # Check pin ranges (assuming BCM numbering)
            for pin in all_pins:
                if not (0 <= pin <= 27):  # Raspberry Pi BCM pins 0-27
                    journaling_manager.recordError(f"Invalid pin number: {pin}")
                    return False
                    
            journaling_manager.recordInfo("Pin configuration validated successfully")
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"Error validating pins: {e}")
            return False 