import serial
import serial.tools.list_ports
from typing import Optional

class SynapticPathways:
    """
    Manages communication pathways between different cortices using static members
    """
    # Static members for shared access across all instances
    _serial_connection: Optional[serial.Serial] = None
    _speech_manager = None
    _audio_manager = None
    _button_manager = None
    _redmine_manager = None
    _consciousness_manager = None

    @classmethod
    def initialize(cls, port="/dev/ttyUSB0", baud_rate=115200):
        """
        Initialize all static connections and managers
        """
        try:
            if not cls._serial_connection:
                cls._serial_connection = serial.Serial(port, baud_rate, timeout=1)
        except serial.SerialException as e:
            print(f"Error initializing serial connection: {e}")
            print("Available ports:")
            ports = serial.tools.list_ports.comports()
            for port in ports:
                print(f"  {port.device}: {port.description}")
            raise

    @classmethod
    def register_manager(cls, manager_type: str, manager_instance):
        """
        Register a manager instance for cross-cortex communication
        """
        if manager_type == "speech":
            cls._speech_manager = manager_instance
        elif manager_type == "audio":
            cls._audio_manager = manager_instance
        elif manager_type == "button":
            cls._button_manager = manager_instance
        elif manager_type == "redmine":
            cls._redmine_manager = manager_instance
        elif manager_type == "consciousness":
            cls._consciousness_manager = manager_instance

    @classmethod
    def transmit_signal(cls, signal: str, target: str = "TTS"):
        """
        Transmit signals between cortices
        """
        if not cls._serial_connection:
            cls.initialize()

        command = f"{target}:{signal}\n"
        cls._serial_connection.write(command.encode())
        response = cls._serial_connection.readline().decode().strip()
        
        # Log the interaction if redmine manager is available
        if cls._redmine_manager:
            cls._redmine_manager.log_learning(
                title="Signal Transmission",
                description=f"Signal: {signal}\nTarget: {target}\nResponse: {response}",
                category="communication"
            )
            
        return response

    @classmethod
    def close_connections(cls):
        """
        Safely close all connections
        """
        if cls._serial_connection:
            cls._serial_connection.close()
            cls._serial_connection = None 