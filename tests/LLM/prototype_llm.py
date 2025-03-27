#!/usr/bin/env python3
import subprocess
import json
import time
import sys
from typing import Dict, Any, Optional
import platform
import re
import serial.tools.list_ports
import serial
import os

# Constants
BAUD_RATE = 115200
MAX_RETRIES = 3
RETRY_DELAY = 1.0

class LLMInterface:
    """Interface for communicating with the LLM hardware"""
    
    def __init__(self):
        """Initialize the LLM interface"""
        self.port = None
        self.connection_type = None
        self._initialized = False
        
    def initialize(self) -> None:
        """Initialize the connection to the LLM hardware"""
        if self._initialized:
            print("Already initialized")
            return
            
        try:
            # Try to find the device port
            self.port = self._find_device_port()
            if not self.port:
                raise Exception("No suitable device port found")
                
            self._initialized = True
            print(f"Initialized connection to {self.port}")
            
        except Exception as e:
            print(f"Failed to initialize: {e}")
            raise
            
    def _find_device_port(self) -> Optional[str]:
        """Find the appropriate device port"""
        # First try ADB
        if self._is_adb_available():
            print("Found ADB connection")
            self.connection_type = "adb"
            return self._find_adb_port()
            
        # Then try serial
        if self._is_serial_available():
            print("Found serial connection")
            self.connection_type = "serial"
            return self._find_serial_port()
            
        return None
        
    def _is_adb_available(self) -> bool:
        """Check if ADB is available"""
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            devices = result.stdout.strip().split("\n")[1:]
            return any(device.strip() and "device" in device for device in devices)
        except FileNotFoundError:
            return False
            
    def _is_serial_available(self) -> bool:
        """Check if serial connection is available"""
        ports = serial.tools.list_ports.comports()
        return bool(ports)
        
    def _find_adb_port(self) -> Optional[str]:
        """Find the device port through ADB"""
        try:
            # Try to get the port through device properties
            result = subprocess.run(
                ["adb", "shell", "ls -l /dev/tty*"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if "ttyS" in line and "dialout" in line:
                        port_match = re.search(r'/dev/ttyS\d+', line)
                        if port_match:
                            return port_match.group(0)
                            
            # Try ttyUSB or ttyACM
            result = subprocess.run(
                ["adb", "shell", "ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.split('\n'):
                    if "ttyUSB" in line or "ttyACM" in line:
                        port_match = re.search(r'/dev/tty(USB|ACM)\d+', line)
                        if port_match:
                            return port_match.group(0)
                            
        except Exception as e:
            print(f"Error finding ADB port: {e}")
            
        return None
        
    def _find_serial_port(self) -> Optional[str]:
        """Find the device port through serial"""
        if platform.system() == "Darwin":  # macOS
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if "usbserial" in port.device.lower() or "tty.usbserial" in port.device.lower():
                    return port.device
        return None
        
    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to the LLM hardware"""
        if not self._initialized:
            raise RuntimeError("LLM interface not initialized")
            
        command_json = json.dumps(command) + "\n"
        print(f"\nSending command: {command_json.strip()}")
        
        try:
            if self.connection_type == "adb":
                # Use ADB mode (USB or Wi-Fi)
                print("📡 Using ADB mode")
                
                # First ensure the port is accessible and properly configured
                setup_commands = [
                    f"chmod 666 {self.port}",
                    f"stty -F {self.port} {BAUD_RATE} cs8 -cstopb -parenb raw -echo -icanon min 1 time 0"
                ]
                
                for cmd in setup_commands:
                    result = subprocess.run(
                        ["adb", "shell", cmd],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        print(f"Warning: Failed to run {cmd}: {result.stderr}")
                
                # Send command through ADB
                result = subprocess.run(
                    ["adb", "shell", f"echo -n '{command_json}' > {self.port}"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    raise Exception(f"Failed to send command: {result.stderr}")
                
                # Wait for response
                max_attempts = 3
                for attempt in range(max_attempts):
                    print(f"\nAttempt {attempt + 1} to read response:")
                    
                    # Try to read response using dd for better control
                    try:
                        result = subprocess.run(
                            ["adb", "shell", f"dd if={self.port} bs=1 count=1024 2>/dev/null"],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            response = result.stdout.strip()
                            print(f"Response received: {response}")
                            
                            try:
                                return json.loads(response)
                            except json.JSONDecodeError:
                                print(f"Invalid JSON response: {response}")
                                continue
                    except subprocess.TimeoutExpired:
                        print(f"Timeout while reading response")
                        continue
                    
                    time.sleep(1)  # Wait before next attempt
                
                raise Exception("No valid response received after multiple attempts")
                    
            else:
                # Use Serial mode
                print("🔌 Using Serial mode")
                with serial.Serial(self.port, BAUD_RATE, timeout=2) as ser:
                    ser.write(command_json.encode())
                    time.sleep(0.5)  # Wait for response
                    response = ser.readline().decode().strip()
                    return response
                    
        except Exception as e:
            print(f"Error sending command: {e}")
            return f"Error: {e}"
            
def main():
    """Main function"""
    try:
        # Initialize LLM interface
        llm = LLMInterface()
        llm.initialize()
        
        # Send initial ping command
        print("\nSending initial ping command...")
        ping_command = {
            "type": "SYSTEM",
            "command": "ping",
            "data": {
                "timestamp": int(time.time() * 1000),
                "version": "1.0",
                "request_id": "initial_ping",
                "echo": True
            }
        }
        response = llm.send_command(ping_command)
        print(f"Initial ping response: {response}")
        
        # Send test command
        print("\nSending test command...")
        test_command = {
            "type": "SYSTEM",
            "command": "ping",
            "data": {
                "timestamp": int(time.time() * 1000),
                "version": "1.0",
                "request_id": "ping_test",
                "echo": True
            }
        }
        response = llm.send_command(test_command)
        print(f"Test response: {response}")
        
        # Interactive mode
        print("\nEntering interactive mode. Type 'exit' to quit.")
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            if user_input.lower() == 'exit':
                break
                
            # Create LLM command
            command = {
                "type": "LLM",
                "command": "generate",
                "data": {
                    "prompt": user_input,
                    "timestamp": int(time.time() * 1000),
                    "version": "1.0",
                    "request_id": f"chat_{int(time.time())}"
                }
            }
            
            # Send command and get response
            try:
                response = llm.send_command(command)
                print(f"\nAssistant: {response}")
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 