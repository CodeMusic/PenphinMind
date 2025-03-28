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
        self._ser = None
        
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
                
            # Initialize serial connection
            if self.connection_type == "serial":
                self._ser = serial.Serial(
                    port=self.port,
                    baudrate=BAUD_RATE,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1,
                    xonxoff=False,  # Disable software flow control
                    rtscts=False,   # Disable hardware flow control
                    dsrdtr=False    # Disable DSR/DTR flow control
                )
                # Clear any existing data like in M5Module-LLM
                while self._ser.in_waiting:
                    self._ser.read()
                    
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
            # First try to list all available ports
            ports = serial.tools.list_ports.comports()
            print("\nAvailable ports:")
            for port in ports:
                print(f"  - {port.device}: {port.description}")
                print(f"    VID:PID: {port.vid:04x}:{port.pid:04x}")
                print(f"    Hardware ID: {port.hwid}")
                
            # Look for M5Stack USB device patterns
            for port in ports:
                # Check for M5Stack USB device patterns
                if any(pattern in port.description.lower() for pattern in [
                    "m5stack",
                    "m5 module",
                    "m5module",
                    "cp210x",
                    "silicon labs"
                ]):
                    print(f"\nFound M5Stack device port: {port.device}")
                    print(f"Device details: {port.description}")
                    print(f"Hardware ID: {port.hwid}")
                    return port.device
                    
            # If no M5Stack patterns found, try to find any USB CDC device
            for port in ports:
                if "USB" in port.description.upper() and "CDC" in port.description.upper():
                    print(f"\nFound USB CDC device port: {port.device}")
                    print(f"Device details: {port.description}")
                    print(f"Hardware ID: {port.hwid}")
                    return port.device
                    
            print("\nNo suitable serial port found")
            return None
            
        return None
        
    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to the LLM hardware"""
        if not self._initialized:
            raise RuntimeError("LLM interface not initialized")
            
        # Convert to simpler command structure like M5Module-LLM
        if command["type"] == "SYSTEM" and command["command"] == "ping":
            command_json = json.dumps({"cmd": "ping"}) + "\n"
        elif command["type"] == "LLM" and command["command"] == "generate":
            command_json = json.dumps({
                "cmd": "generate",
                "prompt": command["data"]["prompt"]
            }) + "\n"
        else:
            raise ValueError(f"Unsupported command type: {command['type']}")
            
        print(f"\nSending command: {command_json.strip()}")
        
        try:
            if self.connection_type == "adb":
                # Use ADB mode (USB or Wi-Fi)
                print("📡 Using ADB mode")
                
                # First check and fix permissions
                print(f"Checking permissions for {self.port}...")
                check_perms = subprocess.run(
                    ["adb", "shell", f"ls -l {self.port}"],
                    capture_output=True,
                    text=True
                )
                print(f"Current permissions: {check_perms.stdout.strip()}")
                
                # Try to configure the port
                print("Configuring port...")
                setup_commands = [
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
                    else:
                        print(f"Successfully ran: {cmd}")
                
                # Try to write to the port
                print("Writing command to port...")
                result = subprocess.run(
                    ["adb", "shell", f"echo -n '{command_json}' > {self.port}"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    raise Exception(f"Failed to send command: {result.stderr}")
                else:
                    print("Command written successfully")
                
                # Wait for response using M5Module-LLM approach
                start_time = time.time()
                buffer = ""
                last_data_time = time.time()
                read_count = 0
                
                print("Starting to read response...")
                while True:
                    # Check for data
                    result = subprocess.run(
                        ["adb", "shell", f"dd if={self.port} bs=1 count=1 2>/dev/null"],
                        capture_output=True,
                        text=True
                    )
                    
                    read_count += 1
                    if read_count % 100 == 0:
                        print(f"Read {read_count} bytes, buffer: {buffer}")
                    
                    if result.returncode == 0 and result.stdout:
                        buffer += result.stdout
                        last_data_time = time.time()
                        print(f"Received byte: {result.stdout!r}")
                        
                        # Check for complete message
                        if "\n" in buffer:
                            response = buffer.strip()
                            print(f"Response received: {response}")
                            try:
                                return json.loads(response)
                            except json.JSONDecodeError:
                                print(f"Invalid JSON response: {response}")
                                buffer = ""
                                continue
                    
                    # Check for timeout
                    if time.time() - start_time > 5:  # 5 second timeout
                        print(f"Timeout waiting for response. Buffer: {buffer!r}")
                        raise Exception("Timeout waiting for response")
                        
                    # Check for end of message (50ms without data)
                    if time.time() - last_data_time > 0.05:
                        if buffer:
                            response = buffer.strip()
                            print(f"Response received: {response}")
                            try:
                                return json.loads(response)
                            except json.JSONDecodeError:
                                print(f"Invalid JSON response: {response}")
                                buffer = ""
                    
                    time.sleep(0.005)  # 5ms delay like in M5Module-LLM
                    
            else:
                # Use Serial mode
                print("🔌 Using Serial mode")
                if not self._ser:
                    raise Exception("Serial connection not initialized")
                    
                # Clear any existing data
                self._ser.reset_input_buffer()
                
                # Write command
                self._ser.write(command_json.encode())
                print("Command written successfully")
                
                # Wait for response using M5Module-LLM approach
                start_time = time.time()
                buffer = ""
                last_data_time = time.time()
                read_count = 0
                
                print("Starting to read response...")
                while True:
                    if self._ser.in_waiting:
                        char = self._ser.read().decode()
                        buffer += char
                        last_data_time = time.time()
                        read_count += 1
                        
                        if read_count % 100 == 0:
                            print(f"Read {read_count} bytes, buffer: {buffer}")
                            
                        print(f"Received byte: {char!r}")
                        
                        # Check for complete message
                        if char == "\n":
                            response = buffer.strip()
                            print(f"Response received: {response}")
                            try:
                                return json.loads(response)
                            except json.JSONDecodeError:
                                print(f"Invalid JSON response: {response}")
                                buffer = ""
                                continue
                    
                    # Check for timeout
                    if time.time() - start_time > 5:  # 5 second timeout
                        print(f"Timeout waiting for response. Buffer: {buffer!r}")
                        raise Exception("Timeout waiting for response")
                        
                    # Check for end of message (50ms without data)
                    if time.time() - last_data_time > 0.05:
                        if buffer:
                            response = buffer.strip()
                            print(f"Response received: {response}")
                            try:
                                return json.loads(response)
                            except json.JSONDecodeError:
                                print(f"Invalid JSON response: {response}")
                                buffer = ""
                    
                    time.sleep(0.005)  # 5ms delay like in M5Module-LLM
                    
        except Exception as e:
            print(f"Error sending command: {e}")
            return f"Error: {e}"
            
    def cleanup(self) -> None:
        """Clean up the connection"""
        if self._ser:
            self._ser.close()
            self._ser = None
        self._initialized = False
            
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
    finally:
        llm.cleanup()

if __name__ == "__main__":
    main() 