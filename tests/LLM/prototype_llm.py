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
    
    def __init__(self, preferred_mode: str = None):
        """Initialize the LLM interface"""
        self.port = None
        self.connection_type = None
        self._initialized = False
        self._ser = None
        self.preferred_mode = preferred_mode  # Can be "serial", "adb", or None for auto-detect
        
    def initialize(self) -> None:
        """Initialize the connection to the LLM hardware"""
        if self._initialized:
            print("Already initialized")
            return
            
        try:
            print("\nInitializing LLM interface...")
            print(f"Preferred mode: {self.preferred_mode if self.preferred_mode else 'auto-detect'}")
            
            # Try to find the device port based on preferred mode
            if self.preferred_mode == "serial":
                print("Attempting serial connection...")
                if self._is_serial_available():
                    self.port = self._find_serial_port()
                    if self.port:
                        self.connection_type = "serial"
                        print(f"Found serial port: {self.port}")
                    else:
                        print("No suitable serial port found")
                else:
                    print("No serial ports available")
                    
            elif self.preferred_mode == "adb":
                print("Attempting ADB connection...")
                if self._is_adb_available():
                    self.port = self._find_adb_port()
                    if self.port:
                        self.connection_type = "adb"
                        print(f"Found ADB port: {self.port}")
                    else:
                        print("No suitable ADB port found")
                else:
                    print("ADB not available")
                    
            else:
                # Auto-detect mode
                print("Auto-detecting connection mode...")
                self.port = self._find_device_port()
                
            if not self.port:
                raise Exception("No suitable device port found")
                
            print(f"\nUsing {self.connection_type} mode with port {self.port}")
            
            # Initialize the connection
            if self.connection_type == "serial":
                print("Setting up serial connection...")
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
                # Clear any existing data
                while self._ser.in_waiting:
                    self._ser.read()
                print("Serial connection established")
                    
            self._initialized = True
            print(f"Successfully initialized {self.connection_type} connection to {self.port}")
            
        except Exception as e:
            print(f"Failed to initialize: {e}")
            raise
            
    def _find_device_port(self) -> Optional[str]:
        """Find the appropriate device port"""
        print("\nChecking for available connection methods...")
        
        # First try serial (preferred for direct connection)
        if self._is_serial_available():
            print("Found potential serial connection")
            serial_port = self._find_serial_port()
            if serial_port:
                print(f"Found valid serial port: {serial_port}")
                self.connection_type = "serial"
                return serial_port
                
        # Then try ADB
        if self._is_adb_available():
            print("Found ADB connection")
            adb_port = self._find_adb_port()
            if adb_port:
                print(f"Found valid ADB port: {adb_port}")
                self.connection_type = "adb"
                return adb_port
                
        print("No suitable connection method found")
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
        if not ports:
            print("No serial ports found")
            return False
            
        print("\nAvailable serial ports:")
        for port in ports:
            print(f"  - {port.device}: {port.description}")
            if port.vid is not None and port.pid is not None:
                print(f"    VID:PID: {port.vid:04x}:{port.pid:04x}")
            print(f"    Hardware ID: {port.hwid}")
            
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
                    if port.vid is not None and port.pid is not None:
                        print(f"VID:PID: {port.vid:04x}:{port.pid:04x}")
                    print(f"Hardware ID: {port.hwid}")
                    return port.device
                    
            # If no M5Stack patterns found, try to find any USB CDC device
            for port in ports:
                if "USB" in port.description.upper() and "CDC" in port.description.upper():
                    print(f"\nFound USB CDC device port: {port.device}")
                    print(f"Device details: {port.description}")
                    if port.vid is not None and port.pid is not None:
                        print(f"VID:PID: {port.vid:04x}:{port.pid:04x}")
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
        if command["type"] == "SYSTEM":
            if command["command"] == "ping":
                command_json = json.dumps({"cmd": "ping", "echo": True}) + "\n"
            elif command["command"] == "set_mode":
                command_json = json.dumps({
                    "cmd": "set_mode",
                    "mode": command["data"]["mode"],
                    "echo": True
                }) + "\n"
            else:
                raise ValueError(f"Unsupported system command: {command['command']}")
        elif command["type"] == "LLM" and command["command"] == "generate":
            command_json = json.dumps({
                "cmd": "generate",
                "prompt": command["data"]["prompt"],
                "echo": True
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
                write_result = subprocess.run(
                    ["adb", "shell", f"printf '{command_json}' > {self.port}"],
                    capture_output=True,
                    text=True
                )
                print(f"Write result: returncode={write_result.returncode}, stderr={write_result.stderr!r}")
                
                # Add a small delay after writing
                time.sleep(0.1)
                
                # Wait for response using M5Module-LLM approach
                start_time = time.time()
                buffer = ""
                last_data_time = time.time()
                read_count = 0
                check_count = 0
                
                print("Starting to read response...")
                while True:
                    check_count += 1
                    if check_count % 100 == 0:
                        print(f"Still waiting for data... (checks: {check_count}, time: {time.time() - start_time:.2f}s)")
                    
                    # First check if there's any data available
                    check_data = subprocess.run(
                        ["adb", "shell", f"dd if={self.port} bs=1 count=1 iflag=nonblock 2>/dev/null"],
                        capture_output=True,
                        text=True,
                        timeout=0.1
                    )
                    
                    if check_data.returncode == 0 and check_data.stdout:
                        # If we have data, read more bytes
                        read_result = subprocess.run(
                            ["adb", "shell", f"dd if={self.port} bs=1 count=100 iflag=nonblock 2>/dev/null"],
                            capture_output=True,
                            text=True,
                            timeout=0.1
                        )
                        
                        if read_result.returncode == 0 and read_result.stdout:
                            buffer += read_result.stdout
                            last_data_time = time.time()
                            read_count += len(read_result.stdout)
                            
                            # Check for complete message
                            if "\n" in buffer:
                                response = buffer.strip()
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
                check_count = 0
                
                print("Starting to read response...")
                while True:
                    check_count += 1
                    if check_count % 100 == 0:
                        print(f"Still waiting for data... (checks: {check_count}, time: {time.time() - start_time:.2f}s)")
                    
                    # Check if there's any data available
                    if self._ser.in_waiting:
                        # Read all available data
                        data = self._ser.read(self._ser.in_waiting)
                        buffer += data.decode()
                        last_data_time = time.time()
                        read_count += len(data)
                        
                        # Check for complete message
                        if "\n" in buffer:
                            response = buffer.strip()
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
            
    def change_mode(self, new_mode: str) -> None:
        """Change the connection mode"""
        if new_mode not in ["serial", "adb"]:
            raise ValueError("Invalid mode. Use 'serial' or 'adb'")
            
        print(f"\nSwitching to {new_mode} mode...")
        
        # Clean up existing connection
        self.cleanup()
        
        # Try to find port in new mode
        if new_mode == "serial":
            if self._is_serial_available():
                self.port = self._find_serial_port()
                if self.port:
                    self.connection_type = "serial"
                    print(f"Found serial port: {self.port}")
                else:
                    raise Exception("No suitable serial port found")
            else:
                raise Exception("No serial ports available")
        else:  # adb
            if self._is_adb_available():
                self.port = self._find_adb_port()
                if self.port:
                    self.connection_type = "adb"
                    print(f"Found ADB port: {self.port}")
                else:
                    raise Exception("No suitable ADB port found")
            else:
                raise Exception("ADB not available")
                
        # Initialize new connection
        if self.connection_type == "serial":
            print("Setting up serial connection...")
            self._ser = serial.Serial(
                port=self.port,
                baudrate=BAUD_RATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            while self._ser.in_waiting:
                self._ser.read()
            print("Serial connection established")
            
        self._initialized = True
        print(f"Successfully switched to {self.connection_type} mode with port {self.port}")
        
        # Test the new connection
        print("\nTesting new connection...")
        ping_command = {
            "type": "SYSTEM",
            "command": "ping",
            "data": {
                "timestamp": int(time.time() * 1000),
                "version": "1.0",
                "request_id": "mode_switch_ping",
                "echo": True
            }
        }
        response = self.send_command(ping_command)
        print(f"Mode switch test response: {response}")

    def set_device_mode(self, mode: str) -> None:
        """Change the device's mode (serial, adb, or wifi)"""
        if mode not in ["serial", "adb", "wifi"]:
            raise ValueError("Invalid mode. Use 'serial', 'adb', or 'wifi'")
            
        print(f"\nSetting device to {mode} mode...")
        
        try:
            # Clean up current connection first
            self.cleanup()
            
            # Wait for device to switch modes
            print("Waiting for device to switch modes...")
            time.sleep(5)  # Give device time to switch
            
            # Try to find port in new mode with retries
            max_retries = 3
            retry_delay = 2
            for attempt in range(max_retries):
                print(f"\nAttempt {attempt + 1} to find port in {mode} mode...")
                
                if mode == "serial":
                    if self._is_serial_available():
                        self.port = self._find_serial_port()
                        if self.port:
                            self.connection_type = "serial"
                            print(f"Found serial port: {self.port}")
                            break
                        else:
                            print("No suitable serial port found")
                    else:
                        print("No serial ports available")
                else:  # adb or wifi
                    if self._is_adb_available():
                        self.port = self._find_adb_port()
                        if self.port:
                            self.connection_type = "adb"
                            print(f"Found ADB port: {self.port}")
                            break
                        else:
                            print("No suitable ADB port found")
                    else:
                        print("ADB not available")
                
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
            
            if not self.port:
                raise Exception(f"Failed to find port in {mode} mode after {max_retries} attempts")
            
            # Initialize new connection
            if self.connection_type == "serial":
                print("Setting up serial connection...")
                self._ser = serial.Serial(
                    port=self.port,
                    baudrate=BAUD_RATE,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1,
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False
                )
                while self._ser.in_waiting:
                    self._ser.read()
                print("Serial connection established")
            
            self._initialized = True
            print(f"Successfully switched to {self.connection_type} mode with port {self.port}")
            
            # Test the new mode with retries
            print("\nTesting new mode...")
            for attempt in range(max_retries):
                try:
                    ping_command = {
                        "type": "SYSTEM",
                        "command": "ping",
                        "data": {
                            "timestamp": int(time.time() * 1000),
                            "version": "1.0",
                            "request_id": "mode_switch_ping",
                            "echo": True
                        }
                    }
                    response = self.send_command(ping_command)
                    print(f"Mode switch test response: {response}")
                    break
                except Exception as e:
                    print(f"Ping attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        print(f"Retrying ping in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        raise Exception(f"Failed to verify mode switch after {max_retries} attempts")
            
        except Exception as e:
            print(f"Error changing device mode: {e}")
            raise

def main():
    """Main function"""
    try:
        # First initialize to detect current mode
        print("Detecting current mode...")
        llm = LLMInterface()
        llm.initialize()
        current_mode = llm.connection_type or "auto-detect"
        
        while True:
            # Prompt for desired mode
            print("\nAvailable modes:")
            if current_mode == "serial":
                print("1. Serial (direct USB connection) (CURRENT)")
            else:
                print("1. Serial (direct USB connection)")
                
            if current_mode == "adb":
                print("2. ADB (Android Debug Bridge) (CURRENT)")
            else:
                print("2. ADB (Android Debug Bridge)")
                
            if current_mode == "wifi":
                print("3. WiFi (wireless connection) (CURRENT)")
            else:
                print("3. WiFi (wireless connection)")
            
            mode_input = input(f"\nSelect mode (1-3) [{current_mode}]: ").strip()
            
            if not mode_input:  # Empty input, use current mode
                print(f"Using current mode: {current_mode}")
                mode = current_mode
                break
                
            try:
                mode_num = int(mode_input)
                if mode_num == 1:
                    mode = "serial"
                elif mode_num == 2:
                    mode = "adb"
                elif mode_num == 3:
                    mode = "wifi"
                else:
                    print("Invalid selection. Please enter 1, 2, or 3.")
                    continue
                    
                # If selecting a different mode, change the device's mode
                if mode != current_mode:
                    print(f"\nChanging device mode from {current_mode} to {mode}...")
                    try:
                        llm.set_device_mode(mode)
                        print(f"Successfully switched to {mode} mode")
                        break
                    except Exception as e:
                        print(f"\n❌ Error: Failed to switch to {mode} mode: {e}")
                        print("Returning to mode selection menu...")
                        # Clean up and reinitialize in current mode
                        llm.cleanup()
                        llm = LLMInterface(current_mode)
                        llm.initialize()
                        continue
                break
                
            except ValueError:
                print("Please enter a number (1-3)")
            except Exception as e:
                print(f"Error changing device mode: {e}")
                print("Using current mode:", current_mode)
                mode = current_mode
                break
        
        # Clean up initial connection
        llm.cleanup()
        
        # Initialize with selected mode
        print(f"\nInitializing with {mode} mode...")
        llm = LLMInterface(mode)
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
        
        # Interactive mode
        print("\nEntering interactive mode. Commands:")
        print("  'exit' - quit")
        print("  'device serial' - set device to serial mode")
        print("  'device adb' - set device to ADB mode")
        print("  'device wifi' - set device to WiFi mode")
        
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Handle device mode commands
            if user_input.lower() == 'exit':
                break
            elif user_input.lower().startswith('device '):
                mode = user_input.lower().split()[1]
                try:
                    llm.set_device_mode(mode)
                    print(f"Successfully switched to {mode} mode")
                except Exception as e:
                    print(f"\n❌ Error: Failed to switch to {mode} mode: {e}")
                    print("Returning to mode selection menu...")
                    # Clean up and reinitialize in current mode
                    llm.cleanup()
                    llm = LLMInterface(current_mode)
                    llm.initialize()
                    continue
                continue
                
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