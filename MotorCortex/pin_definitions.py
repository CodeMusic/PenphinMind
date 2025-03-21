class PinDefinitions:
    """
    Centralized pin configuration for motor control and physical outputs
    """
    def __init__(self):
        # GPIO Pin Definitions
        self.BUTTON_PIN = 17
        self.LED_PIN = 18
        
        # Motor Control Pins
        self.MOTOR_LEFT_FORWARD = 23
        self.MOTOR_LEFT_BACKWARD = 24
        self.MOTOR_RIGHT_FORWARD = 25
        self.MOTOR_RIGHT_BACKWARD = 26
        
        # PWM Pins
        self.MOTOR_LEFT_PWM = 12
        self.MOTOR_RIGHT_PWM = 13
        
        # Servo Pins
        self.SERVO_HEAD_PAN = 19
        self.SERVO_HEAD_TILT = 20 