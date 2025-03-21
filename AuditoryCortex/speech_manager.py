import serial
import serial.tools.list_ports
from typing import Optional

class SpeechManager:
    def __init__(self):
        self.serial_connection: Optional[serial.Serial] = None
        self.listening = False
        self._initialize_serial()

    def _initialize_serial(self, port="/dev/ttyUSB0", baud_rate=115200):
        """
        Initialize serial connection to LLM module
        """
        try:
            self.serial_connection = serial.Serial(port, baud_rate, timeout=2)
        except serial.SerialException as e:
            print(f"Error initializing serial connection: {e}")
            print("Available ports:")
            ports = serial.tools.list_ports.comports()
            for port in ports:
                print(f"  {port.device}: {port.description}")
            raise

    def start_recording(self):
        """
        Start recording audio via LLM module
        """
        if not self.serial_connection:
            self._initialize_serial()
            
        print("Recording... Speak now")
        self.serial_connection.write(b"STT:START\n")
        self.listening = True

    def stop_recording(self):
        """
        Stop recording and return transcribed text
        """
        if not self.listening:
            return "No audio recorded"
            
        try:
            response = self.serial_connection.readline().decode().strip()
            print(f"You said: {response}")
            return response
        except Exception as e:
            return f"Error processing audio: {e}"
        finally:
            self.listening = False

    def __del__(self):
        """
        Cleanup serial connection on object destruction
        """
        if self.serial_connection:
            self.serial_connection.close()