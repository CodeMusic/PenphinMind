'''
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
import threading
import paramiko
import socket

# Constants
BAUD_RATE = 115200
MAX_RETRIES = 3
RETRY_DELAY = 1.0
WINDOWS_SERIAL_PATTERNS = [
    "m5stack",
    "m5 module",
    "m5module",
    "cp210x",
    "silicon labs"
]

class LLMInterface:
    """Interface for communicating with the LLM hardware"""
    
    def __init__(self, preferred_mode: str = None):
        """Initialize the LLM interface"""
        self.port = None
        self.connection_type = None
        self._initialized = False
        self._ser = None
        self.preferred_mode = preferred_mode  # Can be "serial", "adb", or None for auto-detect
        self.response_buffer = ""
        self.response_callback = None
        self._response_thread = None
        self._stop_thread = False
        
    def _start_response_thread(self):
        """Start thread to continuously read responses"""
        self._stop_thread = False
        self._response_thread = threading.Thread(target=self._read_responses)
        self._response_thread.daemon = True
        self._response_thread.start()

    def _stop_response_thread(self):
        """Stop the response reading thread"""
        self._stop_thread = True
        if self._response_thread:
            self._response_thread.join()

    def _read_responses(self):
        """Continuously read responses from the serial port"""
        while not self._stop_thread:
            if self.connection_type == "serial" and self._ser and self._ser.is_open:
                try:
                    if self._ser.in_waiting:
                        char = self._ser.read().decode('utf-8')
                        self.response_buffer += char
                        
                        # Check for complete JSON response
                        if char == '\n' and self.response_buffer.strip():
                            try:
                                response = json.loads(self.response_buffer.strip())
                                if self.response_callback:
                                    self.response_callback(response.get('data', ''))
                            except json.JSONDecodeError:
                                print(f"Error decoding JSON: {self.response_buffer}")
                            finally:
                                self.response_buffer = ""
                except Exception as e:
                    print(f"Error reading from serial: {e}")
            elif self.connection_type == "adb":
                try:
                    # Read one character at a time using ADB
                    read_result = subprocess.run(
                        ["adb", "shell", f"dd if={self.port} bs=1 count=1 iflag=nonblock 2>/dev/null"],
                        capture_output=True,
                        text=True
                    )
                    
                    if read_result.returncode == 0 and read_result.stdout:
                        char = read_result.stdout
                        self.response_buffer += char
                        
                        # Check for complete JSON response
                        if char == '\n' and self.response_buffer.strip():
                            try:
                                response = json.loads(self.response_buffer.strip())
                                if self.response_callback:
                                    self.response_callback(response.get('data', ''))
                            except json.JSONDecodeError:
                                print(f"Error decoding JSON: {self.response_buffer}")
                            finally:
                                self.response_buffer = ""
                except Exception as e:
                    print(f"Error reading from ADB: {e}")
            time.sleep(0.01)

    def parse_response(self, response_str: str) -> Dict[str, Any]:
        """Parse the response from the LLM hardware"""
        try:
            response = json.loads(response_str)
            
            # Check for error response
            if "error" in response:
                return {
                    "error": {
                        "code": response.get("error", {}).get("code", -1),
                        "message": response.get("error", {}).get("message", "Unknown error")
                    }
                }
            
            # Check for system response
            if response.get("work_id") == "sys":
                if response.get("action") == "ping":
                    return {
                        "status": "ok",
                        "message": "Ping successful"
                    }
                elif response.get("action") == "reset":
                    return {
                        "status": "ok",
                        "message": "Reset successful"
                    }
                elif response.get("action") == "setup":
                    return {
                        "status": "ok",
                        "message": "Setup successful"
                    }
            
            # Check for LLM response
            if response.get("work_id") == "llm":
                if response.get("action") == "inference":
                    # Handle streaming response format
                    response_data = {
                        "status": "ok",
                        "response": response.get("data", {}).get("delta", ""),
                        "finished": response.get("data", {}).get("finish", False),
                        "index": response.get("data", {}).get("index", 0)
                    }
                    if response_data["finished"]:
                        response_data["response"] += "\n"
                    return response_data
            
            # Unknown response type
            return {
                "error": {
                    "code": -1,
                    "message": f"Unknown response type: {response}"
                }
            }
            
        except json.JSONDecodeError:
            return {
                "error": {
                    "code": -1,
                    "message": f"Failed to parse response: {response_str}"
                }
            }
        except Exception as e:
            return {
                "error": {
                    "code": -1,
                    "message": f"Error processing response: {str(e)}"
                }
            }

    def initialize(self) -> None:
        """Initialize the connection to the LLM hardware"""
        if self._initialized:
            print("Already initialized")
            return
            
        try:
            print("\n🔍 Initializing LLM interface...")
            print(f"Preferred mode: {self.preferred_mode if self.preferred_mode else 'auto-detect'}")
            
            # Try to find the device port based on preferred mode
            if self.preferred_mode == "wifi":
                print("Attempting WiFi connection...")
                wifi_ip = None
                
                # First try to get IP through ADB
                if self._is_adb_available():
                    print("Trying to get IP through ADB...")
                    result = subprocess.run(
                        ["adb", "shell", "ip addr show wlan0"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
                        if ip_match:
                            wifi_ip = ip_match.group(1)
                            print(f"Found WiFi IP through ADB: {wifi_ip}")
                
                # If ADB lookup failed, use known IP
                if not wifi_ip:
                    print("Using known IP address...")
                    wifi_ip = "10.0.0.177"
                    print(f"Using WiFi IP: {wifi_ip}")
                
                # Use SSH to find the LLM service port
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print(f"\nConnecting to {wifi_ip}:22...")
                ssh.connect(wifi_ip, port=22, username="root", password="123456")
                
                # Find the LLM service port
                service_port = self._find_llm_port(ssh)
                ssh.close()
                
                self.port = f"{wifi_ip}:{service_port}"  # Use IP:port format
                self.connection_type = "wifi"
                print(f"Found WiFi connection at {self.port}")
                self._initialized = True
                return
                    
            elif self.preferred_mode == "serial":
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
                print(f"Using baud rate: {BAUD_RATE}")
                
                try:
                self._ser = serial.Serial(
                    port=self.port,
                    baudrate=BAUD_RATE,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.1,
                    xonxoff=False,
                    rtscts=False,
                        dsrdtr=True  # Enable DTR for reset
                    )
                    
                    # Try to reset the device
                    print("Attempting device reset...")
                    self._ser.setDTR(False)
                    time.sleep(0.5)  # Longer delay for reset
                    self._ser.setDTR(True)
                    time.sleep(1.0)  # Give device time to stabilize
                    
                # Clear any existing data
                    print("Clearing any existing data...")
                while self._ser.in_waiting:
                        data = self._ser.read()
                        print(f"Cleared data: {data!r}")
                    
                    # Try a simple ping to test the connection
                    print("Testing connection...")
                    test_command = "AT\r\n"  # Simple AT command
                    self._ser.write(test_command.encode())
                    time.sleep(0.5)  # Give device time to respond
                    
                    if self._ser.in_waiting:
                        response = self._ser.read(self._ser.in_waiting)
                        print(f"Test response: {response!r}")
                    
                print("Serial connection established")
                    
                except Exception as e:
                    print(f"Error setting up serial connection: {e}")
                    if self._ser:
                        self._ser.close()
                        self._ser = None
                    raise
            
            # Start response thread
            self._start_response_thread()
            
            # Set initialized flag before sending commands
            self._initialized = True
            
            # 1. Check connection with ping
            print("\nSending initial ping command...")
            ping_command = {
                "type": "SYSTEM",
                "command": "ping",
                "data": {
                    "timestamp": int(time.time() * 1000),
                    "version": "1.0",
                    "request_id": "sys_ping",
                    "echo": True
                }
            }
            try:
                ping_result = self.send_command(ping_command)
                if not ping_result or "error" in ping_result:
                    print("Failed to ping device")
                    self._initialized = False
                    return
            except Exception as e:
                print(f"Error during ping: {e}")
                self._initialized = False
                return
            
            print(f"Successfully initialized {self.connection_type} connection to {self.port}")
            
        except Exception as e:
            print(f"Failed to initialize: {e}")
            self._initialized = False
            if self.connection_type == "adb":
                print("\nTrying to recover ADB connection...")
                try:
                    # Kill any existing ADB server
                    subprocess.run([self.adb_path, "kill-server"], capture_output=True, text=True)
                    time.sleep(1)
                    # Start new ADB server
                    subprocess.run([self.adb_path, "start-server"], capture_output=True, text=True)
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
        if platform.system() == "Windows":
            ports = serial.tools.list_ports.comports()
            
            print("\nChecking all available ports...")
            for port in ports:
                print(f"\nChecking port: {port.device}")
                print(f"Description: {port.description}")
                    if port.vid is not None and port.pid is not None:
                        print(f"VID:PID: {port.vid:04x}:{port.pid:04x}")
                    print(f"Hardware ID: {port.hwid}")
                
                # Check for CH340 device (VID:PID = 1A86:7523)
                if port.vid == 0x1A86 and port.pid == 0x7523:
                    print(f"\nFound CH340 device on port: {port.device}")
                    return port.device
                    
                # Check for M5Stack USB device patterns
                if any(pattern.lower() in port.description.lower() for pattern in WINDOWS_SERIAL_PATTERNS):
                    print(f"\nFound matching device pattern on port: {port.device}")
                    return port.device
                    
                # Check for any USB CDC device
                if "USB" in port.description.upper() and "CDC" in port.description.upper():
                    print(f"\nFound USB CDC device on port: {port.device}")
                    return port.device
                
                # If we get here and haven't found a match, but it's a CH340 device,
                # return it anyway (some Windows systems might not report the VID/PID correctly)
                if "CH340" in port.description.upper():
                    print(f"\nFound CH340 device by description on port: {port.device}")
                    return port.device
            
            print("\nNo suitable serial port found")
            return None
            
        return None
        
    def send_command(self, command: Dict[str, Any], timeout: float = 1.0) -> Dict[str, Any]:
        """Send a command to the LLM hardware"""
        if not self._initialized:
            raise RuntimeError("LLM interface not initialized")
            
        # Convert to simpler command structure like M5Module-LLM
        if command["type"] == "SYSTEM":
            if command["command"] == "ping":
                # Use exact same format as M5Module-LLM
                command_json = json.dumps({
                    "request_id": "sys_ping",  # Fixed request_id for ping
                    "work_id": "sys",
                    "action": "ping",
                    "object": "None",
                    "data": "None"
                }) + "\n"
            elif command["command"] == "reset":
                command_json = json.dumps({
                    "request_id": "sys_reset",  # Fixed request_id for reset
                    "work_id": "sys",
                    "action": "reset",
                    "object": "None",
                    "data": "None"
                }) + "\n"
            elif command["command"] == "setup":
                command_json = json.dumps({
                    "request_id": "sys_setup",  # Fixed request_id for setup
                    "work_id": "llm",
                    "action": "setup",
                    "object": "None",
                    "data": json.dumps({"max_token_len": command["data"]["max_token_len"]})
                }) + "\n"
            else:
                raise ValueError(f"Unsupported system command: {command['command']}")
        elif command["type"] == "LLM" and command["command"] == "generate":
            # Match M5Module-LLM inference format exactly
            command_json = json.dumps({
                "request_id": command["data"].get("request_id", "generate"),
                "work_id": "llm",
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
            if self.connection_type == "wifi":
                print("📡 Using WiFi mode")
                # Parse IP and port from self.port
                ip, port = self.port.split(":")
                port = int(port)
                
                # Connect to the LLM service
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(timeout)
                    print(f"Connecting to {ip}:{port}...")
                    s.connect((ip, port))
                    print("Connected successfully")
                    
                    # Send command
                    print("Sending command...")
                    print(f"Command bytes: {command_json.encode()}")
                    s.sendall(command_json.encode())
                    print("Command sent successfully")
                    
                    # Wait for response
                    buffer = ""
                    print("Waiting for response...")
                    while True:
                        try:
                            data = s.recv(1).decode()
                            if not data:
                                print("No more data received")
                                break
                            buffer += data
                            print(f"Received byte: {data!r}")
                            if data == "\n":
                                print("Received newline, ending read")
                                break
                        except socket.timeout:
                            print("Socket timeout")
                            break
                    
                    print(f"Received response: {buffer.strip()}")
                    try:
                        return json.loads(buffer.strip())
                    except json.JSONDecodeError:
                        print(f"Failed to parse JSON: {buffer.strip()}")
                        return {"error": "Failed to parse response", "raw": buffer.strip()}
                        
            elif self.connection_type == "serial":
                print("🔌 Using Serial mode")
                if not self._ser:
                    raise Exception("Serial connection not initialized")
                    
                # Clear any existing data first
                print("Clearing any existing data...")
                while self._ser.in_waiting:
                    data = self._ser.read()
                    print(f"Cleared data: {data!r}")
                    
                # Write command
                print("Writing command...")
                self._ser.write(command_json.encode())
                print("Command written successfully")
                
                # Wait for response with more detailed debugging
                start_time = time.time()
                buffer = ""
                got_message = False
                last_data_time = time.time()
                
                print("\nWaiting for response...")
                try:
                    while True:
                        if self._ser.in_waiting:
                            char = self._ser.read(1)
                            print(f"Received byte: {char!r}")
                            try:
                                char_decoded = char.decode('utf-8')
                                buffer += char_decoded
                                got_message = True
                                last_data_time = time.time()
                                print(f"Current buffer: {buffer!r}")
                                
                                # Return immediately if we see a newline
                                if char_decoded == "\n":
                                    response = buffer.strip()
                                    print(f"Complete message: {response}")
                                    return self.parse_response(response)
                            except UnicodeDecodeError:
                                print(f"Failed to decode byte: {char!r}")
                        
                        # Check if we have a complete message (50ms without new data)
                        if got_message and time.time() - last_data_time > 0.05:
                            if buffer:
                                response = buffer.strip()
                                print(f"End of message detected: {response}")
                                return self.parse_response(response)
                            break
                        
                        # Check for timeout
                        if time.time() - start_time > timeout:
                            print(f"Timeout waiting for response. Buffer: {buffer!r}")
                            return {
                                "error": {
                                    "code": -2,
                                    "message": "Timeout waiting for response"
                                }
                            }
                        
                        time.sleep(0.005)  # 5ms delay
                        
                except KeyboardInterrupt:
                    print("\nInterrupted by user")
                    raise  # Re-raise to be caught by outer try/except
                
            else:
                # Use ADB mode (USB or Wi-Fi)
                print("📡 Using ADB mode")
                
                # Configure port with recommended settings
                print("Configuring port with recommended settings...")
                setup_commands = [
                    f"stty -F {self.port} {BAUD_RATE} raw -echo -crtscts -ixon -ixoff -parodd -cstopb cs8"
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
                
                # Clear any existing data first (like ModuleMsg::clearMsg)
                print("Clearing any existing data...")
                clear_result = subprocess.run(
                    ["adb", "shell", f"dd if={self.port} of=/dev/null bs=1 count=2048 iflag=nonblock 2>/dev/null"],
                    capture_output=True,
                    text=True
                )
                print(f"Clear result: {clear_result.stdout}")
                
                # Write command (like ModuleComm::sendCmd)
                print("Writing command to port...")
                write_result = subprocess.run(
                    ["adb", "shell", f"echo -n '{command_json}' > {self.port}"],
                    capture_output=True,
                    text=True
                )
                print(f"Write result: returncode={write_result.returncode}, stderr={write_result.stderr!r}")
                
                # Wait for response with proper timeout
                start_time = time.time()
                buffer = ""
                got_message = False
                last_data_time = time.time()
                
                while True:
                    # Read one character at a time
                    read_result = subprocess.run(
                        ["adb", "shell", f"dd if={self.port} bs=1 count=1 iflag=nonblock 2>/dev/null"],
                        capture_output=True,
                        text=True
                    )
                    
                    if read_result.returncode == 0 and read_result.stdout:
                        char = read_result.stdout
                        buffer += char
                        got_message = True
                        last_data_time = time.time()
                        print(f"Received char: {char!r}")
                        
                        # Return immediately if we see a newline
                        if char == "\n":
                            response = buffer.strip()
                            print(f"Complete message: {response}")
                            return self.parse_response(response)
                    
                    # Check if we have a complete message (50ms without new data)
                    if got_message and time.time() - last_data_time > 0.05:
                        if buffer:
                            response = buffer.strip()
                            print(f"End of message detected: {response}")
                            return self.parse_response(response)
                        break
                    
                    # Check for timeout (use 2000ms like M5Module-LLM)
                    if time.time() - start_time > 2.0:
                        print(f"Timeout waiting for response. Buffer: {buffer!r}")
                        return {
                            "error": {
                                "code": -2,
                                "message": "Timeout waiting for response"
                            }
                        }
                    
                    time.sleep(0.005)  # 5ms delay
                
        except Exception as e:
            print(f"Error sending command: {e}")
            return {"error": str(e)}

    def cleanup(self) -> None:
        """Clean up the connection"""
        self._stop_response_thread()
        if self._ser:
            self._ser.close()
            self._ser = None
        self._initialized = False
        self.response_buffer = ""
        self.response_callback = None
            
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
                            # Use SSH to find the LLM service port
                            ssh = paramiko.SSHClient()
                            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                            ssh.connect(wifi_ip, port=22, username="root", password="123456")
                            
                            # Find the LLM service port
                            service_port = self._find_llm_port(ssh)
                            ssh.close()
                            
                            self.port = f"{wifi_ip}:{service_port}"  # Use IP:port format
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
                    break  # Success, exit retry loop
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

    def _find_llm_port(self, ssh) -> int:
        """Find the port where the LLM service is running"""
        print("\nChecking for LLM service port...")
        
        # First try to find the port from the process
        stdin, stdout, stderr = ssh.exec_command("lsof -i -P -n | grep llm_llm")
        for line in stdout:
            print(f"Found port info: {line.strip()}")
            # Look for port number in the output
            if ":" in line:
                port = line.split(":")[-1].split()[0]
                print(f"Found LLM service port: {port}")
                return int(port)
        
        # If we couldn't find it through lsof, try netstat
        print("\nTrying netstat to find port...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tulpn | grep llm_llm")
        for line in stdout:
            print(f"Found port info: {line.strip()}")
            # Look for port number in the output
            if ":" in line:
                port = line.split(":")[-1].split()[0]
                print(f"Found LLM service port: {port}")
                return int(port)
        
        # If we still can't find it, try to get the port from the process arguments
        print("\nChecking process arguments...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep llm_llm")
        for line in stdout:
            if "llm_llm" in line and not "grep" in line:
                print(f"Found process: {line.strip()}")
                # Try to find port in process arguments
                if "--port" in line:
                    port = line.split("--port")[1].split()[0]
                    print(f"Found port in arguments: {port}")
                    return int(port)
        
        # If we get here, try common ports
        print("\nTrying common ports...")
        common_ports = [10001, 8080, 80, 443, 5000, 8000, 3000]  # Put 10001 first since we know it works
        for port in common_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    # Get the IP from the SSH connection
                    ip = ssh.get_transport().getpeername()[0]
                    result = s.connect_ex((ip, port))
                    if result == 0:
                        print(f"Port {port} is open and accepting connections")
                        return port
            except Exception as e:
                print(f"Error checking port {port}: {e}")
        
        raise Exception("Could not find LLM service port")

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
        # First ask for connection mode
        print("\n=== M5Module-LLM Connection Mode ===")
        print("1. Serial (direct USB)")
        print("2. ADB (Android Debug Bridge)")
        print("3. WiFi")
        
        while True:
            try:
                mode_choice = input("\nSelect connection mode (1-3): ").strip()
                if mode_choice == "1":
                    preferred_mode = "serial"
                    break
                elif mode_choice == "2":
                    preferred_mode = "adb"
                    break
                elif mode_choice == "3":
                    preferred_mode = "wifi"
                    break
                else:
                    print("\n❌ Invalid choice. Please select 1-3.")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                return
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue
        
        # Initialize with preferred mode
        print(f"\n🔍 Initializing in {preferred_mode} mode...")
        llm = LLMInterface(preferred_mode=preferred_mode)
        llm.initialize()
        current_mode = llm.connection_type or "auto-detect"
        
        while True:
            try:
            print("\n=== M5Module-LLM Interface ===")
            print("1. Send ping command")
            print("2. Generate text")
            print("3. Change connection mode")
            print("4. Exit")
            
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
                    try:
                    response = llm.send_command(ping_command)
                    print(f"Ping response: {response}")
                    except KeyboardInterrupt:
                        print("\nPing command interrupted by user")
                        continue
                    
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
                        try:
                        response = llm.send_command(command)
                        print(f"\nResponse: {response}")
                        except KeyboardInterrupt:
                            print("\nGenerate command interrupted by user")
                            continue
                    
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
                    
            except KeyboardInterrupt:
                print("\nOperation interrupted by user")
                continue
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Returning to main menu...")
                continue
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        if 'llm' in locals():
            llm.cleanup()

if __name__ == "__main__":
    main() '''