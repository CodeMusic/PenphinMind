#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Transport Layer Abstraction:
- Handles communication with hardware
- Manages connection methods (Serial, ADB, WiFi)
- Provides a unified interface for command transmission
"""

import asyncio
import json
import logging
import os
import platform
import socket
import subprocess
import time
import traceback
import re
from typing import Dict, Any, List, Optional, Union
import paramiko
import serial
import serial.tools.list_ports

from Mind.config import CONFIG
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

# Add recordWarning method to match usage
def recordWarning(self, message):
    """Log a warning message"""
    logging.warning(message)
SystemJournelingManager.recordWarning = recordWarning

# Add these at the module level, right after the imports and journaling manager
_direct_adb_failed = False  # Flag to remember if direct ADB call has failed
_adb_executable_path = None  # Cache the working executable path
_tcp_gateway_active = False  # Flag to indicate if TCP gateway is active and working

# Exception types
class TransportError(Exception):
    """Base class for transport-related exceptions"""
    pass

class ConnectionError(TransportError):
    """Raised when connection fails"""
    pass

class CommandError(TransportError):
    """Error during command execution"""
    pass

class BaseTransport:
    """Abstract base class for all transport types"""
    
    def __init__(self):
        self.connected = False
        self.endpoint = None
        self._serial_connection = None
    
    async def connect(self) -> bool:
        """Establish connection to the device"""
        raise NotImplementedError("Subclasses must implement connect()")
    
    async def disconnect(self) -> None:
        """Close the connection"""
        raise NotImplementedError("Subclasses must implement disconnect()")
    
    async def transmit(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command and receive a response"""
        raise NotImplementedError("Subclasses must implement transmit()")
    
    def is_available(self) -> bool:
        """Check if this transport type is available"""
        raise NotImplementedError("Subclasses must implement is_available()")
        
    def _log_transport_json(self, direction: str, data: Union[Dict[str, Any], str], transport_type: str = None):
        """Log JSON data being sent or received through the transport layer
        
        Args:
            direction: "SEND" or "RECEIVE" 
            data: JSON data as dict or string
            transport_type: Optional transport type identifier
        """
        if not transport_type:
            transport_type = self.__class__.__name__
        
        # Ensure data is a string for logging
        if isinstance(data, dict):
            data_str = json.dumps(data, indent=2)
        else:
            data_str = str(data)
            
        # Truncate if too large
        if len(data_str) > 1000:
            shortened = f"{data_str[:500]}...{data_str[-500:]}"
        else:
            shortened = data_str
            
        # Log with visual separation and direction indicators
        if direction == "SEND":
            header = f"=== 🐬 {transport_type} SENDING JSON ==="
            arrow = "  ↓ "
        else:  # RECEIVE
            header = f"=== 🐧 {transport_type} RECEIVING JSON ==="
            arrow = "  ↑ "
            
        journaling_manager.recordDebug(header)
        for line in shortened.split('\n'):
            journaling_manager.recordDebug(f"{arrow}{line}")
        journaling_manager.recordDebug("=" * len(header))

class SerialTransport(BaseTransport):
    """Serial communication transport layer"""
    
    def __init__(self):
        super().__init__()
        self._serial_port = None
        self._serial_connection = None
        self.port = str(CONFIG.llm_service["port"])  # 10001
        self._tunnel_active = False
        self.serial_settings = CONFIG.serial_settings
    
    def is_available(self) -> bool:
        """Check if serial connection is available"""
        # Don't fail here, just return True to allow discovery process
        return True
    
    def _find_serial_port(self) -> Optional[str]:
        """Find the device port through serial"""
        journaling_manager.recordInfo("Starting serial port discovery...")
        
        ports = serial.tools.list_ports.comports()
        if not ports:
            journaling_manager.recordInfo("No serial ports found")
            return None
        
        journaling_manager.recordInfo("\nChecking all available ports...")
        for port in ports:
            journaling_manager.recordInfo(f"\nChecking port: {port.device}")
            journaling_manager.recordInfo(f"Description: {port.description}")
            if port.vid is not None and port.pid is not None:
                journaling_manager.recordInfo(f"VID:PID: {port.vid:04x}:{port.pid:04x}")
            journaling_manager.recordInfo(f"Hardware ID: {port.hwid}")
            
            # Check for CH340 device (VID:PID = 1A86:7523)
            if port.vid == 0x1A86 and port.pid == 0x7523:
                journaling_manager.recordInfo(f"\nFound CH340 device on port: {port.device}")
                return port.device
            
            # Check for M5Stack USB device patterns
            patterns = ["m5stack", "m5 module", "m5module", "cp210x", "silicon labs"]
            if any(pattern.lower() in port.description.lower() for pattern in patterns):
                journaling_manager.recordInfo(f"\nFound matching device pattern on port: {port.device}")
                return port.device
                    
            # Check for any USB CDC device
            if "USB" in port.description.upper() and "CDC" in port.description.upper():
                journaling_manager.recordInfo(f"\nFound USB CDC device on port: {port.device}")
                return port.device
                    
            # If we get here and haven't found a match, but it's a CH340 device,
            # return it anyway (some Windows systems might not report the VID/PID correctly)
            if "CH340" in port.description.upper():
                journaling_manager.recordInfo(f"\nFound CH340 device by description on port: {port.device}")
                return port.device
        
        journaling_manager.recordInfo("\nNo suitable serial port found")
        return None
    
    async def _setup_tunnel(self) -> bool:
        """Setup port forwarding tunnel"""
        try:
            journaling_manager.recordInfo(f"\n>>> SETTING UP TUNNEL FOR PORT {self.port}")
            
            # First check shell access
            self._serial_connection.write(b"whoami\n")
            await asyncio.sleep(0.5)
            shell_check = ""
            while self._serial_connection.in_waiting:
                shell_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> SHELL ACCESS: {shell_check.strip()!r}")

            # Check if netcat exists
            self._serial_connection.write(b"which nc\n")
            await asyncio.sleep(0.5)
            nc_check = ""
            while self._serial_connection.in_waiting:
                nc_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> NETCAT AVAILABLE: {nc_check.strip()!r}")

            # Check current port status
            self._serial_connection.write(f"netstat -tln | grep {self.port}\n".encode())
            await asyncio.sleep(0.5)
            port_check = ""
            while self._serial_connection.in_waiting:
                port_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> CURRENT PORT STATUS: {port_check.strip()!r}")

            # Kill any existing netcat
            self._serial_connection.write(b"pkill -f 'nc -l'\n")
            await asyncio.sleep(0.5)
            while self._serial_connection.in_waiting:
                self._serial_connection.read()

            # Start netcat tunnel with error capture
            tunnel_cmd = f"nc -l -p {self.port} 2>&1 &\n"
            journaling_manager.recordInfo(f">>> STARTING TUNNEL: {tunnel_cmd.strip()}")
            self._serial_connection.write(tunnel_cmd.encode())
            await asyncio.sleep(1)

            # Check for any error output
            self._serial_connection.write(b"dmesg | tail\n")
            await asyncio.sleep(0.5)
            error_check = ""
            while self._serial_connection.in_waiting:
                error_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> SYSTEM MESSAGES: {error_check.strip()!r}")

            # Verify tunnel process
            self._serial_connection.write(b"ps | grep nc\n")
            await asyncio.sleep(0.5)
            ps_check = ""
            while self._serial_connection.in_waiting:
                ps_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> TUNNEL PROCESS: {ps_check.strip()!r}")

            # Final port check
            self._serial_connection.write(f"netstat -tln | grep {self.port}\n".encode())
            await asyncio.sleep(0.5)
            final_check = ""
            while self._serial_connection.in_waiting:
                final_check += self._serial_connection.read().decode()
            journaling_manager.recordInfo(f">>> FINAL PORT STATUS: {final_check.strip()!r}")

            if f":{self.port}" in final_check:
                self._tunnel_active = True
                journaling_manager.recordInfo(">>> TUNNEL ESTABLISHED SUCCESSFULLY")
                return True
            else:
                journaling_manager.recordError(">>> TUNNEL SETUP FAILED - Port not listening")
                return False

        except Exception as e:
            journaling_manager.recordError(f">>> TUNNEL SETUP ERROR: {str(e)}")
            journaling_manager.recordError(f">>> STACK TRACE: {traceback.format_exc()}")
            return False

    async def connect(self) -> bool:
        """Connect to serial and setup tunnel"""
        try:
            journaling_manager.recordInfo(">>> STARTING SERIAL CONNECTION")
            
            # Connect to serial port
            self._serial_port = self.serial_settings["port"]  # COM7
            journaling_manager.recordInfo(f">>> CONNECTING TO {self._serial_port}")
            
            self._serial_connection = serial.Serial(
                port=self._serial_port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            
            # Clear buffer
            while self._serial_connection.in_waiting:
                self._serial_connection.read()

            # Setup tunnel
            if not await self._setup_tunnel():
                journaling_manager.recordError(">>> FAILED TO SETUP TUNNEL")
                return False

            self.endpoint = f"127.0.0.1:{self.port}"
            self.connected = True
            return True
            
        except Exception as e:
            journaling_manager.recordError(f">>> CONNECTION ERROR: {e}")
            if self._serial_connection and self._serial_connection.is_open:
                self._serial_connection.close()
            return False

    async def transmit(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command through tunnel"""
        if not self.connected or not self._tunnel_active:
            raise ConnectionError("Tunnel not established")
        
        try:
            # Log the outgoing command
            self._log_transport_json("SEND", command, "SerialTransport")
            
            # Prepare the JSON data
            json_data = json.dumps(command) + "\n"
            journaling_manager.recordInfo("🔤 NETWORK RAW REQUEST (SERIAL):")
            journaling_manager.recordInfo(f"  {json_data.strip()}")
            
            # Send command through tunnel
            cmd = f"echo '{json_data.strip()}' | nc localhost {self.port}\n"
            journaling_manager.recordInfo(f">>> SENDING THROUGH TUNNEL: {cmd.strip()}")
            
            self._serial_connection.write(cmd.encode())
            self._serial_connection.flush()
            
            # Read response
            buffer = ""
            start_time = time.time()
            
            while (time.time() - start_time) < 5.0:
                if self._serial_connection.in_waiting:
                    char = self._serial_connection.read().decode()
                    buffer += char
                    journaling_manager.recordInfo(f">>> RECEIVED: {char!r}")
                    
                    if char == '\n':
                        # Log the raw response before parsing
                        journaling_manager.recordInfo("🔤 NETWORK RAW RESPONSE (SERIAL):")
                        journaling_manager.recordInfo(f"  {buffer.strip()}")
                        
                        try:
                            response = json.loads(buffer.strip())
                            journaling_manager.recordInfo(f">>> VALID JSON: {response}")
                            
                            # Log the received response
                            self._log_transport_json("RECEIVE", response, "SerialTransport")
                            
                            return response
                        except json.JSONDecodeError:
                            journaling_manager.recordInfo(f">>> INVALID JSON: {buffer.strip()!r}")
                            buffer = ""
                            continue
                await asyncio.sleep(0.1)
            
            journaling_manager.recordError(">>> NO RESPONSE (timeout)")
            raise CommandError("No valid response received")
            
        except Exception as e:
            journaling_manager.recordError(f">>> TRANSMISSION ERROR: {e}")
            raise CommandError(f"Command transmission failed: {e}")

    async def disconnect(self) -> None:
        """Clean up tunnel and connection"""
        try:
            if self._tunnel_active:
                journaling_manager.recordInfo(">>> CLEANING UP TUNNEL")
                self._serial_connection.write(b"pkill -f 'nc -l'\n")
                await asyncio.sleep(0.5)
                self._tunnel_active = False
            
            if self._serial_connection and self._serial_connection.is_open:
                self._serial_connection.close()
            
            self.connected = False
            journaling_manager.recordInfo(">>> DISCONNECTED")
        except Exception as e:
            journaling_manager.recordError(f">>> DISCONNECT ERROR: {e}")

class WiFiTransport(BaseTransport):
    """TCP communication transport layer"""
    
    def __init__(self):
        super().__init__()
        self.ip = CONFIG.llm_service["ip"]
        self.port = CONFIG.llm_service["port"]
        self.timeout = CONFIG.llm_service["timeout"]
    
    def is_available(self) -> bool:
        """Check if TCP connection is available"""
        try:
            # Try to resolve the hostname/IP
            socket.gethostbyname(self.ip)
            return True
        except Exception:
            return False
    
    async def connect(self) -> bool:
        """Find LLM service port and connect with IP discovery"""
        try:
            # Show clearly what IP we're trying to connect to
            journaling_manager.recordInfo(f"🔌 Attempting TCP connection to {self.ip}:{self.port}...")
            print(f"\n🔌 Attempting TCP connection to {self.ip}:{self.port}...")
            
            # Try direct connection with current IP
            initial_connection = False
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5.0)  # Increased timeout for more reliability
                    journaling_manager.recordInfo(f"Testing socket connection to {self.ip}:{self.port}...")
                    s.connect((self.ip, self.port))
                    
                    # Try a ping to verify LLM service using exact API format
                    ping_command = {
                        "request_id": "001",  # Use consistent ID from API spec 
                        "work_id": "sys",     # Exact format from API spec
                        "action": "ping"      # Simple ping operation
                    }
                    
                    # Log the ping command
                    journaling_manager.recordInfo(f"Sending ping command: {json.dumps(ping_command)}")
                    
                    # Send ping with newline terminator
                    json_data = json.dumps(ping_command) + "\n"
                    s.sendall(json_data.encode())
                    
                    # Read response in a more robust way - accumulate all data until timeout
                    buffer = bytearray()
                    s.settimeout(5.0)
                    
                    try:
                        while True:
                            chunk = s.recv(4096)  # Larger buffer
                            if not chunk:
                                break
                            buffer.extend(chunk)
                            if b'\n' in chunk:  # Stop at newline
                                break
                    except socket.timeout:
                        # Timeout is ok if we got any data
                        if buffer:
                            journaling_manager.recordInfo("Socket timeout but received data")
                        else:
                            journaling_manager.recordInfo("Socket timeout with no data")
                            
                    # Parse response if we have any data
                    if buffer:
                        response_str = buffer.decode().strip()
                        journaling_manager.recordInfo(f"Received raw response: {response_str}")
                        
                        try:
                            response_data = json.loads(response_str)
                            journaling_manager.recordInfo(f"Parsed JSON response: {json.dumps(response_data, indent=2)}")
                            
                            # Check for success in error code
                            if "error" in response_data and isinstance(response_data["error"], dict):
                                error_code = response_data["error"].get("code", -1)
                                
                                if error_code == 0:
                                    # Success! Connection established
                                    initial_connection = True
                                    self.endpoint = f"{self.ip}:{self.port}"
                                    self.connected = True
                                    journaling_manager.recordInfo(f"✅ TCP connection to {self.ip}:{self.port} successful!")
                                    print(f"✅ TCP connection to {self.ip}:{self.port} successful!")
                                    return True
                                else:
                                    journaling_manager.recordError(f"Ping error code {error_code}: {response_data['error'].get('message', 'Unknown error')}")
                            else:
                                journaling_manager.recordError(f"Unexpected response format - missing error field: {response_data}")
                        except json.JSONDecodeError:
                            journaling_manager.recordError(f"Failed to parse response as JSON: {response_str!r}")
                    else:
                        journaling_manager.recordError("Empty response from ping")
                        
            except socket.timeout:
                journaling_manager.recordError(f"Socket timeout connecting to {self.ip}:{self.port}")
                print(f"❌ Socket timeout connecting to {self.ip}:{self.port}")
            except socket.error as e:
                journaling_manager.recordError(f"Socket error connecting to {self.ip}:{self.port}: {e}")
                print(f"❌ Socket error connecting to {self.ip}:{self.port}: {e}")
            except Exception as e:
                journaling_manager.recordError(f"Error establishing TCP connection: {e}")
                print(f"❌ Error establishing TCP connection: {e}")
                
            # If the default connection didn't work, attempt IP discovery with ADB
            if not initial_connection:
                journaling_manager.recordInfo("Initial connection failed, trying ADB IP discovery...")
                ip_from_adb = self._get_ip_from_adb()
                
                if ip_from_adb and ip_from_adb != self.ip:
                    # Try with the new IP from ADB
                    journaling_manager.recordInfo(f"Found device IP from ADB: {ip_from_adb}")
                    self.ip = ip_from_adb  # Update the IP
                    
                    # Try connecting with the new IP
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.settimeout(5.0)  # Increased timeout
                            journaling_manager.recordInfo(f"🔄 Trying TCP connection with new IP: {ip_from_adb}:{self.port}...")
                            print(f"🔄 Trying TCP connection with new IP: {ip_from_adb}:{self.port}...")
                            s.connect((self.ip, self.port))
                            
                            # Send ping to verify in exact API format
                            ping_command = {
                                "request_id": "001", 
                                "work_id": "sys",
                                "action": "ping"
                            }
                            
                            # Send the ping command with newline
                            json_data = json.dumps(ping_command) + "\n"
                            s.sendall(json_data.encode())
                            
                            # More robust response reading
                            buffer = bytearray()
                            s.settimeout(5.0)
                            
                            try:
                                while True:
                                    chunk = s.recv(4096)
                                    if not chunk:
                                        break
                                    buffer.extend(chunk)
                                    if b'\n' in chunk:
                                        break
                            except socket.timeout:
                                pass
                                
                            # Process response if we got any data
                            if buffer:
                                response_str = buffer.decode().strip()
                                journaling_manager.recordInfo(f"Received raw response: {response_str}")
                                
                                try:
                                    response_data = json.loads(response_str)
                                    
                                    # Check success via error code
                                    if "error" in response_data and isinstance(response_data["error"], dict):
                                        error_code = response_data["error"].get("code", -1)
                                        
                                        if error_code == 0:
                                            # Connection succeeded!
                                            self.endpoint = f"{self.ip}:{self.port}"
                                            self.connected = True
                                            journaling_manager.recordInfo(f"✅ TCP connection with new IP successful!")
                                            print(f"✅ TCP connection with new IP successful!")
                                            return True
                                except json.JSONDecodeError:
                                    journaling_manager.recordError(f"Failed to parse response as JSON: {response_str!r}")
                    except Exception as e:
                        journaling_manager.recordError(f"Error connecting with IP from ADB: {e}")
            
            # If we get here, all connection attempts failed
            journaling_manager.recordError("All connection attempts failed")
            print("❌ Failed to establish TCP connection to device")
            return False
                
        except Exception as e:
            journaling_manager.recordError(f"Error in TCP connection process: {e}")
            import traceback
            journaling_manager.recordError(f"TCP connection error trace: {traceback.format_exc()}")
            return False
    
    async def _discover_ip_via_adb(self) -> Optional[str]:
        """Discover device IP address using ADB"""
        try:
            # Create an ADB transport to run commands
            adb_transport = get_transport("adb")
            if not await adb_transport.connect():
                journaling_manager.recordError("Failed to establish ADB connection for IP discovery")
                return None
            
            # First try to get IP from wlan0 interface
            try:
                output = run_adb_command(["shell", "ip", "addr", "show", "wlan0"])
                match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
                if match:
                    ip = match.group(1)
                    journaling_manager.recordInfo(f"Found IP from wlan0: {ip}")
                    return ip
            except Exception as e:
                journaling_manager.recordWarning(f"Error getting IP from wlan0: {e}")
            
            # If wlan0 fails, try eth0
            try:
                output = run_adb_command(["shell", "ip", "addr", "show", "eth0"])
                match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
                if match:
                    ip = match.group(1)
                    journaling_manager.recordInfo(f"Found IP from eth0: {ip}")
                    return ip
            except Exception as e:
                journaling_manager.recordWarning(f"Error getting IP from eth0: {e}")
            
            # If specific interfaces fail, try general IP commands
            try:
                # Try to get IP using ifconfig
                output = run_adb_command(["shell", "ifconfig"])
                matches = re.findall(r'inet addr:(\d+\.\d+\.\d+\.\d+)', output)
                if not matches:  # Try newer format
                    matches = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
                
                if matches:
                    for ip in matches:
                        if not ip.startswith("127."):  # Skip localhost
                            journaling_manager.recordInfo(f"Found IP from ifconfig: {ip}")
                            return ip
            except Exception as e:
                journaling_manager.recordWarning(f"Error getting IP from ifconfig: {e}")
            
            # If all else fails, try to get device ADB IP address
            try:
                # Get ADB devices with IP
                output = run_adb_command(["devices", "-l"])
                ip_matches = re.findall(r'(\d+\.\d+\.\d+\.\d+:\d+)', output)
                if ip_matches:
                    ip = ip_matches[0].split(':')[0]
                    journaling_manager.recordInfo(f"Found IP from ADB devices: {ip}")
                    return ip
            except Exception as e:
                journaling_manager.recordWarning(f"Error getting IP from ADB devices: {e}")
            
            # No IP found
            return None
        except Exception as e:
            journaling_manager.recordError(f"Error in IP discovery: {e}")
            return None
        finally:
            # Make sure to disconnect ADB transport if created
            if 'adb_transport' in locals() and adb_transport:
                await adb_transport.disconnect()
    
    async def disconnect(self) -> None:
        """Close TCP connection"""
        # Socket connections are closed after each transmission
        self.connected = False
        journaling_manager.recordInfo("TCP connection closed")
    
    async def transmit(self, command: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """Transmit command to device over TCP and get response"""
        if not self.connected:
            journaling_manager.recordError("Attempting to transmit but not connected")
            try:
                # Attempt to reconnect
                reconnect_result = await self.connect()
                if not reconnect_result:
                    return {
                        "error": {
                            "code": -1,
                            "message": "Failed to connect for transmission"
                        }
                    }
            except Exception as e:
                journaling_manager.recordError(f"Error reconnecting for transmission: {e}")
                return {
                    "error": {
                        "code": -1,
                        "message": f"Reconnection error: {str(e)}"
                    }
                }
        
        try:
            # Convert command to string if it's a dict
            if isinstance(command, dict):
                command_str = json.dumps(command) + "\n"
            else:
                # Ensure string command ends with newline
                command_str = command if command.endswith("\n") else command + "\n"
            
            # Debug log showing truncated command
            cmd_log = command_str[:200] + "..." if len(command_str) > 200 else command_str
            journaling_manager.recordInfo(f"📤 Transmitting: {cmd_log}")
            
            # Create fresh socket for this transmission
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10.0)  # Longer timeout for potentially complex operations
                
                # Connect and send
                try:
                    ip, port = self.ip, self.port
                    journaling_manager.recordInfo(f"Connecting to {ip}:{port} for transmission")
                    s.connect((ip, port))
                    
                    # Send command
                    s.sendall(command_str.encode())
                    journaling_manager.recordInfo("Command sent, awaiting response")
                    
                    # Receive response in chunks - more robust handling
                    buffer = bytearray()
                    s.settimeout(15.0)  # Generous timeout for response
                    
                    try:
                        while True:
                            chunk = s.recv(4096)
                            if not chunk:
                                break
                            buffer.extend(chunk)
                            if b'\n' in chunk:  # Stop at newline
                                break
                    except socket.timeout:
                        if buffer:
                            journaling_manager.recordInfo("Socket timeout but received partial data")
                        else:
                            journaling_manager.recordError("Socket timeout with no response data")
                            return {
                                "error": {
                                    "code": -1,
                                    "message": "Timeout waiting for response"
                                }
                            }
                    
                    # Process response if we have data
                    if buffer:
                        response_str = buffer.decode().strip()
                        
                        # Truncate long responses in log
                        resp_log = response_str[:200] + "..." if len(response_str) > 200 else response_str
                        journaling_manager.recordInfo(f"📥 Received: {resp_log}")
                        
                        try:
                            # Parse JSON response
                            response_data = json.loads(response_str)
                            return response_data
                        except json.JSONDecodeError:
                            journaling_manager.recordError(f"Failed to parse response as JSON: {resp_log!r}")
                            return {
                                "error": {
                                    "code": -1,
                                    "message": f"Invalid JSON response: {resp_log}"
                                }
                            }
                    else:
                        journaling_manager.recordError("Empty response from transmission")
                        return {
                            "error": {
                                "code": -1,
                                "message": "Empty response"
                            }
                        }
                            
                except socket.error as e:
                    self.connected = False  # Mark as disconnected on socket error
                    journaling_manager.recordError(f"Socket error during transmission: {e}")
                    return {
                        "error": {
                            "code": -1,
                            "message": f"Socket error: {str(e)}"
                        }
                    }
                    
        except Exception as e:
            journaling_manager.recordError(f"Error in TCP transmission: {e}")
            import traceback
            journaling_manager.recordError(f"Transmission error trace: {traceback.format_exc()}")
            return {
                "error": {
                    "code": -1,
                    "message": f"Transmission error: {str(e)}"
                }
            }

    def _find_llm_port(self, ssh) -> Optional[int]:
        """Find the port where the LLM service is running"""
        journaling_manager.recordInfo("\n🐧 Checking for LLM service port...")
        
        # Try netstat first to find the LLM service port
        journaling_manager.recordInfo("\nTrying netstat to find port...")
        stdin, stdout, stderr = ssh.exec_command("netstat -tulpn | grep llm_llm")
        for line in stdout:
            journaling_manager.recordInfo(f"Found port info: {line.strip()}")
            # Look for port number in the output
            if ":" in line:
                port = line.split(":")[-1].split()[0]
                journaling_manager.recordInfo(f"Found LLM service port: {port}")
                return int(port)
        
        # If we still can't find it, try to get the port from the process arguments
        journaling_manager.recordInfo("\nChecking process arguments...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep llm_llm")
        for line in stdout:
            if "llm_llm" in line and not "grep" in line:
                journaling_manager.recordInfo(f"Found process: {line.strip()}")
                # Try to find port in process arguments
                if "--port" in line:
                    port = line.split("--port")[1].split()[0]
                    journaling_manager.recordInfo(f"Found port in arguments: {port}")
                    return int(port)
        
        # If we get here, try common ports
        journaling_manager.recordInfo("\n🐬 Trying common ports...")
        common_ports = [10001, 8080, 80, 443, 5000, 8000, 3000]  # Put 10001 first since we know it works
        for port in common_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    # Get the IP from the SSH connection
                    ip = ssh.get_transport().getpeername()[0]
                    result = s.connect_ex((ip, port))
                    if result == 0:
                        journaling_manager.recordInfo(f"Port {port} is open and accepting connections")
                        return port
            except Exception as e:
                journaling_manager.recordError(f"Error checking port {port}: {e}")
        
        # If no port found, use the default
        journaling_manager.recordInfo(f"No LLM service port found, using default {CONFIG.llm_service['port']}")
        return CONFIG.llm_service["port"]

    def _get_ip_from_adb(self) -> Optional[str]:
        """Get device IP address using ADB"""
        try:
            journaling_manager.recordInfo("Attempting to discover device IP via ADB...")
            
            # Run ADB command to get device IP address
            cmd = ["adb", "shell", "ip", "addr", "show", "wlan0"]
            journaling_manager.recordInfo(f"Executing ADB command: {' '.join(cmd)}")
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                journaling_manager.recordError(f"ADB command failed: {stderr}")
                return None
                
            # Parse IP address from output using regex
            ip_pattern = r'inet\s+(\d+\.\d+\.\d+\.\d+)'
            match = re.search(ip_pattern, stdout)
            
            if match:
                ip_address = match.group(1)
                journaling_manager.recordInfo(f"Found IP address via ADB: {ip_address}")
                
                # Update the config with this IP
                old_ip = self.ip
                CONFIG.llm_service["ip"] = ip_address
                
                if CONFIG.save():
                    journaling_manager.recordInfo(f"Updated config: IP changed from {old_ip} to {ip_address}")
                
                return ip_address
            else:
                journaling_manager.recordInfo("No IP address found in ADB output")
                return None
                
        except Exception as e:
            journaling_manager.recordError(f"Error discovering IP via ADB: {e}")
            import traceback
            journaling_manager.recordError(f"ADB discovery error trace: {traceback.format_exc()}")
            return None

class ADBTransport(BaseTransport):
    """ADB communication transport layer"""
    
    def __init__(self):
        super().__init__()
        self.adb_path = CONFIG.adb_path
        self.port = str(CONFIG.llm_service["port"])  # Should be "10001"
        
    def _run_adb_command(self, command):
        """Run an ADB command using the module-level function with caching"""
        return run_adb_command(command)
    
    def is_available(self) -> bool:
        """Check if ADB is available and a device is connected"""
        try:
            # Start ADB server
            self._run_adb_command(["start-server"])
            
            # Check for connected devices
            devices_output = self._run_adb_command(["devices"])
            devices = devices_output.strip().split("\n")[1:]  # Skip header
            
            # Check if we have any devices in device state
            has_device = any(device.strip() and "device" in device for device in devices)
            journaling_manager.recordInfo(f"ADB device available: {has_device}")
            
            if not has_device:
                # Try to restart ADB server and check again
                journaling_manager.recordInfo("No devices found, trying to restart ADB server...")
                self._run_adb_command(["kill-server"])
                time.sleep(1)
                self._run_adb_command(["start-server"])
                time.sleep(2)
                
                # Check devices again
                devices_output = self._run_adb_command(["devices"])
                devices = devices_output.strip().split("\n")[1:]
                has_device = any(device.strip() and "device" in device for device in devices)
                journaling_manager.recordInfo(f"ADB device available after restart: {has_device}")
            
            return has_device
        except Exception as e:
            journaling_manager.recordError(f"Error checking ADB availability: {e}")
            return False
    
    async def connect(self) -> bool:
        """Set up port forwarding and connect to the device"""
        global _tcp_gateway_active
        
        try:
            if not self.is_available():
                raise ConnectionError("No ADB devices available")
            
            # Clear any existing forwards for this port
            try:
                self._run_adb_command(["forward", "--remove", f"tcp:{self.port}"])
                _tcp_gateway_active = False
            except Exception:
                pass
            
            # Forward local port to device port (both using LLM service port)
            journaling_manager.recordInfo(f"Setting up ADB port forwarding tcp:{self.port} -> tcp:{self.port}")
            self._run_adb_command(["forward", f"tcp:{self.port}", f"tcp:{self.port}"])
            
            # Verify port forwarding
            forwarding = self._run_adb_command(["forward", "--list"])
            if f"tcp:{self.port}" in forwarding:
                _tcp_gateway_active = True
                journaling_manager.recordInfo("Port forwarding verified")
            else:
                raise ConnectionError("Port forwarding not established")
            
            # Use localhost with the forwarded port
            self.endpoint = f"127.0.0.1:{self.port}"
            self.connected = True
            
            journaling_manager.recordInfo(f"ADB connection established at {self.endpoint}")
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"Error connecting via ADB: {e}")
            self.connected = False
            _tcp_gateway_active = False
            raise ConnectionError(f"ADB connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Remove port forwarding and disconnect"""
        if self.connected:
            try:
                self._run_adb_command(["forward", "--remove", f"tcp:{self.port}"])
                journaling_manager.recordInfo("ADB port forwarding removed")
                self.connected = False
            except Exception as e:
                journaling_manager.recordError(f"Error removing ADB port forwarding: {e}")
    
    async def transmit(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command via socket to the forwarded port"""
        global _tcp_gateway_active
        
        if not self.connected:
            if _tcp_gateway_active:
                # Try to re-establish the connection if gateway is marked active
                journaling_manager.recordInfo("TCP gateway marked active but connection lost, reconnecting...")
                await self.connect()
            else:
                raise ConnectionError("Not connected to device")
        
        try:
            # Log the outgoing command
            self._log_transport_json("SEND", command, "ADBTransport")
            
            ip, port = self.endpoint.split(":")
            port = int(port)
            
            # Prepare JSON data - log the exact string that will be sent
            json_data = json.dumps(command) + "\n"
            journaling_manager.recordInfo("🔤 NETWORK RAW REQUEST (ADB):")
            journaling_manager.recordInfo(f"  {json_data.strip()}")
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                
                try:
                    s.connect((ip, port))
                except Exception as e:
                    # Connection failed, TCP gateway might be down
                    journaling_manager.recordError(f"Socket connection failed: {e}")
                    _tcp_gateway_active = False
                    self.connected = False
                    raise ConnectionError("Failed to connect to forwarded port")
                
                # Mark gateway as active if connection succeeds
                _tcp_gateway_active = True
                
                # Send command
                s.sendall(json_data.encode())
                
                # Read response with larger buffer
                buffer = bytearray()
                while True:
                    try:
                        chunk = s.recv(4096)
                        if not chunk:
                            break
                        buffer.extend(chunk)
                        if b"\n" in chunk:
                                break
                    except socket.timeout:
                                break
                
                # Log the raw response before parsing
                raw_response = buffer.decode() if buffer else ""
                journaling_manager.recordInfo("🔤 NETWORK RAW RESPONSE (ADB):")
                journaling_manager.recordInfo(f"  {raw_response.strip()}")
                
                if buffer:
                    try:
                        response_str = buffer.decode().strip()
                        response = json.loads(response_str)
                        
                        # Log the received response
                        self._log_transport_json("RECEIVE", response, "ADBTransport")
                        
                        return response
                    except json.JSONDecodeError as e:
                        journaling_manager.recordError(f"Failed to parse JSON: {e}")
                        
                        # Log the failed response
                        self._log_transport_json("RECEIVE", f"INVALID JSON: {buffer.decode().strip()}", "ADBTransport")
                        
                        return {
                            "request_id": command.get("request_id", "error"),
                            "work_id": command.get("work_id", "local"),
                            "data": buffer.decode().strip(),
                            "error": {"code": -1, "message": f"Failed to parse response: {e}"},
                            "object": command.get("object", "None"),
                            "created": int(time.time())
                        }
                else:
                    journaling_manager.recordError("Empty response received")
                    _tcp_gateway_active = False  # Mark gateway as inactive on empty response
                    
                    # Log the empty response
                    self._log_transport_json("RECEIVE", "EMPTY RESPONSE", "ADBTransport")
                    
                    return {
                    "request_id": command.get("request_id", "error"),
                    "work_id": command.get("work_id", "local"),
                    "data": None,
                    "error": {"code": -2, "message": "Empty response"},
                        "object": command.get("object", "None"),
                        "created": int(time.time())
                    }
            
        except Exception as e:
            journaling_manager.recordError(f"Error transmitting command: {e}")
            _tcp_gateway_active = False  # Mark gateway as inactive on error
            raise CommandError(f"Command transmission failed: {e}")

# Transport factory
def get_transport(transport_type: str) -> BaseTransport:
    """Get the appropriate transport instance based on type"""
    if transport_type == "serial":
        return SerialTransport()
    elif transport_type == "wifi" or transport_type == "tcp":  # Support both for backward compatibility
        return WiFiTransport()  # Will be renamed in a later step
    elif transport_type == "adb":
        return ADBTransport()
    else:
        raise ValueError(f"Unsupported transport type: {transport_type}")

def run_adb_command(command_list):
    """Run an ADB command with fallback to absolute path from config.
    
    This is a standalone utility function that doesn't require a transport instance.
    Once direct ADB command fails, all subsequent calls will use the config path.
    
    Args:
        command_list: List of ADB command arguments
        
    Returns:
        Command output as string if successful
        
    Raises:
        ConnectionError: If command execution fails
    """
    global _direct_adb_failed, _adb_executable_path, _tcp_gateway_active
    
    # If running a command that affects the TCP gateway status
    is_gateway_command = (command_list and 
                         command_list[0] in ["start-server", "forward", "kill-server"])
    
    # If we already know direct ADB failed, use the cached path immediately
    if _direct_adb_failed and _adb_executable_path:
        try:
            journaling_manager.recordInfo(f"Using cached ADB path: {_adb_executable_path} {' '.join(command_list)}")
            result = subprocess.run(
                [_adb_executable_path] + command_list,
                capture_output=True,
                text=True,
                env=os.environ
            )
            if result.returncode == 0:
                # Update TCP gateway status for gateway commands
                if is_gateway_command and command_list[0] == "forward":
                    _tcp_gateway_active = True
                elif is_gateway_command and command_list[0] == "kill-server":
                    _tcp_gateway_active = False
                return result.stdout
            else:
                journaling_manager.recordError(f"ADB command failed with absolute path: {result.stderr}")
                # Mark TCP gateway as inactive on failure
                if is_gateway_command:
                    _tcp_gateway_active = False
                raise ConnectionError(f"ADB command failed: {result.stderr}")
        except Exception as e:
            journaling_manager.recordError(f"Error running ADB with cached path: {e}")
            # Mark TCP gateway as inactive on error
            if is_gateway_command:
                _tcp_gateway_active = False
            raise ConnectionError(f"ADB execution error: {e}")
    
    # If direct ADB hasn't failed yet, try it first
    if not _direct_adb_failed:
        try:
            # Try running adb directly
            journaling_manager.recordInfo(f"Running ADB command: adb {' '.join(command_list)}")
            result = subprocess.run(
                ["adb"] + command_list,
                capture_output=True,
                text=True,
                env=os.environ
            )
            if result.returncode == 0:
                # Update TCP gateway status for gateway commands
                if is_gateway_command and command_list[0] == "forward":
                    _tcp_gateway_active = True
                elif is_gateway_command and command_list[0] == "kill-server":
                    _tcp_gateway_active = False
                return result.stdout
            else:
                journaling_manager.recordError(f"ADB command failed: {result.stderr}")
                # Mark TCP gateway as inactive on failure
                if is_gateway_command:
                    _tcp_gateway_active = False
                _direct_adb_failed = True  # Mark direct ADB as failed
        except Exception as e:
            journaling_manager.recordInfo(f"Error running ADB: {e}. Trying absolute path from config...")
            # Mark TCP gateway as inactive on error
            if is_gateway_command:
                _tcp_gateway_active = False
            _direct_adb_failed = True  # Mark direct ADB as failed

    # Fallback to absolute path from config
    try:
        adb_path = CONFIG.adb_path
        if not adb_path.endswith(".exe") and platform.system() == "Windows":
            adb_path += ".exe"
        
        # Cache the path for future use
        _adb_executable_path = adb_path
            
        journaling_manager.recordInfo(f"Running ADB with absolute path: {adb_path} {' '.join(command_list)}")
        result = subprocess.run(
            [adb_path] + command_list,
            capture_output=True,
            text=True,
            env=os.environ
        )
        if result.returncode == 0:
            # Update TCP gateway status for gateway commands
            if is_gateway_command and command_list[0] == "forward":
                _tcp_gateway_active = True
            elif is_gateway_command and command_list[0] == "kill-server":
                _tcp_gateway_active = False
            return result.stdout
        else:
            journaling_manager.recordError(f"ADB command failed with absolute path: {result.stderr}")
            # Mark TCP gateway as inactive on failure
            if is_gateway_command:
                _tcp_gateway_active = False
            raise ConnectionError(f"ADB command failed: {result.stderr}")
    except Exception as e:
        journaling_manager.recordError(f"Error running ADB with absolute path: {e}")
        # Mark TCP gateway as inactive on error
        if is_gateway_command:
            _tcp_gateway_active = False
        raise ConnectionError(f"ADB execution error: {e}")