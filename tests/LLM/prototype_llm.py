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
            print("\n🔍 Initializing LLM interface...")
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
            
            # Send initial ping command without checking response
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
            try:
                self.send_command(ping_command)
            except Exception as e:
                print(f"Initial ping failed but continuing: {e}")
            
            # Add a delay after initialization
            time.sleep(1)
            
            return
            
        except Exception as e:
            print(f"Failed to initialize: {e}")
            if self.connection_type == "adb":
                print("\nTrying to recover ADB connection...")
                try:
                    # Kill any existing ADB server
                    subprocess.run(["adb", "kill-server"], capture_output=True, text=True)
                    time.sleep(1)
                    # Start new ADB server
                    subprocess.run(["adb", "start-server"], capture_output=True, text=True)
                    time.sleep(2)
                    # Try initialization again
                    print("Retrying initialization...")
                    self.initialize()
                    return
                except Exception as retry_error:
                    print(f"Recovery failed: {retry_error}")
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
                command_json = json.dumps({
                    "request_id": "sys_ping",
                    "work_id": "sys",
                    "action": "ping",
                    "object": "None",
                    "data": "None"
                }) + "\n"
            elif command["command"] == "set_mode":
                command_json = json.dumps({
                    "request_id": "sys_mode",
                    "work_id": "sys",
                    "action": "set_mode",
                    "object": "None",
                    "data": command["data"]["mode"]
                }) + "\n"
            else:
                raise ValueError(f"Unsupported system command: {command['command']}")
        elif command["type"] == "LLM" and command["command"] == "generate":
            # Match M5Module-LLM inference format
            command_json = json.dumps({
                "request_id": command["data"].get("request_id", "generate"),
                "work_id": "llm",  # Fixed work_id for LLM
                "action": "inference",
                "object": "llm.utf-8.stream",
                "data": {
                    "delta": command["data"]["prompt"],
                    "index": 0,
                    "finish": True
                }
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
                
                # Configure port with recommended settings
                print("Configuring port with recommended settings...")
                setup_commands = [
                    f"stty -F {self.port} {BAUD_RATE} raw -echo -crtscts -ixon -ixoff",
                    f"echo 0 > /sys/class/tty/{os.path.basename(self.port)}/device/power/control",
                    "sleep 1",
                    f"echo 1 > /sys/class/tty/{os.path.basename(self.port)}/device/power/control"
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
                
                # Clear any existing data first
                print("Clearing any existing data...")
                clear_result = subprocess.run(
                    ["adb", "shell", f"dd if={self.port} of=/dev/null bs=1 count=1000 iflag=nonblock 2>/dev/null || true"],
                    capture_output=True,
                    text=True
                )
                print(f"Buffer clear result: {clear_result.stdout!r}")
                
                # Try a second clear to ensure buffer is empty
                print("Double checking buffer is clear...")
                clear_result2 = subprocess.run(
                    ["adb", "shell", f"dd if={self.port} of=/dev/null bs=1 count=1000 iflag=nonblock 2>/dev/null || true"],
                    capture_output=True,
                    text=True
                )
                print(f"Second buffer clear result: {clear_result2.stdout!r}")
                
                # Add a small delay after clearing
                time.sleep(0.1)
                
                # Write command
                print("Writing command to port...")
                write_result = subprocess.run(
                    ["adb", "shell", f"echo -n '{command_json}' > {self.port}"],
                    capture_output=True,
                    text=True
                )
                print(f"Write result: returncode={write_result.returncode}, stderr={write_result.stderr!r}")
                
                # Add a small delay after writing
                time.sleep(0.1)
                
                # Read response using Arduino-like approach
                print("Starting to read response...")
                start_time = time.time()
                buffer = ""
                got_message = False
                last_data_time = time.time()
                
                while True:
                    # Read one character at a time like Arduino
                    read_result = subprocess.run(
                        ["adb", "shell", f"dd if={self.port} bs=1 count=1 iflag=nonblock 2>/dev/null"],
                        capture_output=True,
                        text=True
                    )
                    
                    if read_result.returncode == 0 and read_result.stdout:
                        got_message = True
                        char = read_result.stdout
                        print(f"Read char: {char!r}")
                        buffer += char
                        last_data_time = time.time()
                        
                        # Return immediately if we see a complete message
                        if char == "\n":
                            response = buffer.strip()
                            print(f"Complete message: {response}")
                            return parse_response(response)
                    
                    # Check if we have a complete message (50ms without new data)
                    if got_message and time.time() - last_data_time > 0.05:
                        if buffer:
                            response = buffer.strip()
                            print(f"End of message detected: {response}")
                            return parse_response(response)
                        break
                    
                    # Check for timeout
                    if time.time() - start_time > 5:  # 5 second timeout
                        print(f"Timeout waiting for response. Buffer: {buffer!r}")
                        return {
                            "error": {
                                "code": -2,
                                "message": "Timeout waiting for response"
                            }
                        }
                    
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
                
                # Read response using M5Module-LLM approach
                print("Starting to read response...")
                start_time = time.time()
                buffer = ""
                got_message = False
                last_data_time = time.time()
                
                while True:
                    # Check if there's any data available
                    if self._ser.in_waiting:
                        got_message = True
                        # Read one character at a time
                        char = self._ser.read(1).decode()
                        print(f"Read char: {char!r}")
                        buffer += char
                        last_data_time = time.time()
                        
                        # Return immediately if we see a newline
                        if char == "\n":
                            response = buffer.strip()
                            print(f"Complete message: {response}")
                            try:
                                return json.loads(response)
                            except json.JSONDecodeError:
                                print(f"Invalid JSON response: {response}")
                                return {"error": "Invalid JSON response"}
                    
                    # Check if we have a complete message (50ms without new data)
                    if got_message and time.time() - last_data_time > 0.05:
                        if buffer:
                            response = buffer.strip()
                            print(f"End of message detected: {response}")
                            try:
                                return json.loads(response)
                            except json.JSONDecodeError:
                                print(f"Invalid JSON response: {response}")
                                return {"error": "Invalid JSON response"}
                        break
                    
                    # Check for timeout
                    if time.time() - start_time > 5:  # 5 second timeout
                        print(f"Timeout waiting for response. Buffer: {buffer!r}")
                        raise Exception("Timeout waiting for response")
                    
                    time.sleep(0.005)  # 5ms delay like in M5Module-LLM
                    
        except Exception as e:
            print(f"Error sending command: {e}")
            return {"error": str(e)}
            
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
            
            # For WiFi mode, we need to use a different approach
            if mode == "wifi":
                print("WiFi mode requires device to be in WiFi mode first")
                print("Please ensure the device is in WiFi mode before continuing")
                time.sleep(5)  # Give user time to switch device mode
                
                # Try to find WiFi port
                if self._is_adb_available():
                    # Try to find WiFi-specific port
                    result = subprocess.run(
                        ["adb", "shell", "ip addr show wlan0"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
                        if ip_match:
                            wifi_ip = ip_match.group(1)
                            self.port = f"{wifi_ip}:{BAUD_RATE}"  # Use IP:port format
                            self.connection_type = "wifi"
                            print(f"Found WiFi connection at {self.port}")
                        else:
                            raise Exception("No WiFi IP address found")
                    else:
                        raise Exception("Failed to get WiFi information")
                else:
                    raise Exception("ADB not available for WiFi mode")
                    
            else:
                # For Serial and ADB modes, wait for device to switch
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
                    else:  # adb
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

    def check_connection(self) -> bool:
        """Check connection like M5Module-LLM"""
        try:
            # Send ping command
            ping_command = {
                "type": "SYSTEM",
                "command": "ping",
                "data": {
                    "timestamp": int(time.time() * 1000),
                    "version": "1.0",
                    "request_id": "connection_check",
                    "echo": True
                }
            }
            response = self.send_command(ping_command)
            
            # Check for OK response
            if isinstance(response, dict) and response.get("error", {}).get("code") == 0:
                print("Connection check successful")
                return True
            else:
                print(f"Connection check failed: {response}")
                return False
                
        except Exception as e:
            print(f"Connection check error: {e}")
            return False

def main():
    """Main function"""
    try:
        # First initialize to detect current mode
        print("\n🔍 Detecting current mode...")
        llm = LLMInterface()
        llm.initialize()
        current_mode = llm.connection_type or "auto-detect"
        
        while True:
            print("\n=== M5Module-LLM Interface ===")
            print("1. Send ping command")
            print("2. Generate text")
            print("3. Change connection mode")
            print("4. Exit")
            
            try:
                choice = input("\nSelect an option (1-4): ").strip()
                
                if choice == "1":
                    print("\n📡 Sending ping command...")
                    ping_command = {
                        "type": "SYSTEM",
                        "command": "ping",
                        "data": {
                            "timestamp": int(time.time() * 1000),
                            "version": "1.0",
                            "request_id": "ping_test",
                            "echo": True
                        }
                    }
                    response = llm.send_command(ping_command)
                    print(f"Ping response: {response}")
                    
                elif choice == "2":
                    prompt = input("\n💭 Enter your prompt: ").strip()
                    if prompt:
                        print("\n🤖 Generating response...")
                        command = {
                            "type": "LLM",
                            "command": "generate",
                            "data": {
                                "prompt": prompt,
                                "timestamp": int(time.time() * 1000),
                                "version": "1.0",
                                "request_id": f"generate_{int(time.time())}"
                            }
                        }
                        response = llm.send_command(command)
                        print(f"\nResponse: {response}")
                    
                elif choice == "3":
                    print("\n🔄 Available connection modes:")
                    print(f"1. Serial (direct USB) {' (CURRENT)' if current_mode == 'serial' else ''}")
                    print(f"2. ADB (Android Debug Bridge) {' (CURRENT)' if current_mode == 'adb' else ''}")
                    print(f"3. WiFi {' (CURRENT)' if current_mode == 'wifi' else ''}")
                    
                    mode_choice = input("\nSelect mode (1-3): ").strip()
                    if mode_choice == "1":
                        new_mode = "serial"
                    elif mode_choice == "2":
                        new_mode = "adb"
                    elif mode_choice == "3":
                        new_mode = "wifi"
                    else:
                        print("Invalid mode selection")
                        continue
                        
                    if new_mode != current_mode:
                        print(f"\n🔄 Switching to {new_mode} mode...")
                        try:
                            llm.set_device_mode(new_mode)
                            current_mode = new_mode
                            print(f"✅ Successfully switched to {new_mode} mode")
                        except Exception as e:
                            print(f"❌ Error switching mode: {e}")
                    else:
                        print(f"\nAlready in {current_mode} mode")
                    
                elif choice == "4":
                    print("\n👋 Goodbye!")
                    break
                    
                else:
                    print("\n❌ Invalid choice. Please select 1-4.")
                    
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Returning to main menu...")
                continue
                
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        if 'llm' in locals():
            llm.cleanup()

if __name__ == "__main__":
    main() 