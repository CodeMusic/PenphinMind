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
from typing import Dict, Any, Optional, Union
import paramiko
import serial
import serial.tools.list_ports
import re

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

class TransportError(Exception):
    """Base exception for transport layer errors"""
    pass

class ConnectionError(TransportError):
    """Raised when connection fails"""
    pass

class CommandError(TransportError):
    """Raised when command transmission fails"""
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

class SerialTransport(BaseTransport):
    """Serial communication transport layer"""
    
    def __init__(self):
        super().__init__()
        self._serial_port = None
        self._serial_connection = None
    
    def is_available(self) -> bool:
        """Check if serial connection is available"""
        if platform.system() == "Darwin":  # macOS
            journaling_manager.recordInfo("Checking macOS serial ports...")
            ports = serial.tools.list_ports.comports()
            for port in ports:
                journaling_manager.recordInfo(f"Found port: {port.device}")
                journaling_manager.recordInfo(f"Hardware ID: {port.hwid}")
                journaling_manager.recordInfo(f"Description: {port.description}")
                if "ax630" in port.description.lower() or "axera" in port.description.lower():
                    journaling_manager.recordInfo(f"Found AX630 device: {port.device}")
                    return True
        else:  # Linux (including Raspberry Pi) or Windows
                journaling_manager.recordInfo("Checking serial ports...")
                # First try to find AX630 by device name
                ports = serial.tools.list_ports.comports()
                for port in ports:
                    journaling_manager.recordInfo(f"Found port: {port.device}")
                    journaling_manager.recordInfo(f"Hardware ID: {port.hwid}")
                    journaling_manager.recordInfo(f"Description: {port.description}")
                    if "ax630" in port.description.lower() or "axera" in port.description.lower():
                        journaling_manager.recordInfo(f"Found AX630 device: {port.device}")
                        return True
                            
                    # If no AX630 found, check common Raspberry Pi ports
                    pi_ports = [
                        "/dev/ttyAMA0",  # Primary UART
                        "/dev/ttyAMA1",  # Secondary UART
                        "/dev/ttyUSB0",  # USB to Serial
                        "/dev/ttyUSB1",  # USB to Serial
                        "/dev/ttyS0",    # Serial
                        "/dev/ttyS1"     # Serial
                    ]
                    
                    for port in pi_ports:
                        if os.path.exists(port):
                            journaling_manager.recordInfo(f"Found Raspberry Pi port: {port}")
                            return True
                        
        journaling_manager.recordInfo("No suitable serial port found")
        return False
    
    def _find_serial_port(self) -> Optional[str]:
        """Find the serial port for the device"""
        if platform.system() == "Darwin":  # macOS
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if "ax630" in port.description.lower() or "axera" in port.description.lower():
                    return port.device
                    
        elif platform.system() == "Linux":
            # Check for AX630 by device name
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if "ax630" in port.description.lower() or "axera" in port.description.lower():
                    return port.device
                    
            # If not found, check common Raspberry Pi ports
            pi_ports = [
                "/dev/ttyAMA0",  # Primary UART
                "/dev/ttyAMA1",  # Secondary UART
                "/dev/ttyUSB0",  # USB to Serial
                "/dev/ttyUSB1",  # USB to Serial
                "/dev/ttyS0",    # Serial
                "/dev/ttyS1"     # Serial
            ]
            
            for port in pi_ports:
                if os.path.exists(port):
                    return port
        else:  # Windows
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if "ax630" in port.description.lower() or "axera" in port.description.lower():
                    return port.device
        
        return None
    
    async def connect(self) -> bool:
        """Connect to the serial device"""
        try:
            if not self.is_available():
                raise ConnectionError("No serial device available")
            
            self._serial_port = self._find_serial_port()
            if not self._serial_port:
                raise ConnectionError("No suitable serial port found")
            
            journaling_manager.recordInfo(f"Connecting to serial port: {self._serial_port}")
            
            self._serial_connection = serial.Serial(
                port=self._serial_port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # Clear any pending data
            while self._serial_connection.in_waiting:
                self._serial_connection.read()
                
            self.connected = True
            self.endpoint = self._serial_port
            journaling_manager.recordInfo("Serial connection established")
            
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"Serial connection error: {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close the serial connection"""
        if self._serial_connection and self._serial_connection.is_open:
            self._serial_connection.close()
            journaling_manager.recordInfo("Serial connection closed")
        
        self._serial_connection = None
        self.connected = False
    
    async def transmit(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command over serial and get response"""
        if not self.connected or not self._serial_connection or not self._serial_connection.is_open:
            raise ConnectionError("Serial connection not established")
        
        try:
            # Prepare command
            json_data = json.dumps(command) + "\n"
            journaling_manager.recordDebug(f"Sending command through serial: {json_data.strip()}")
            
            # Send command
            self._serial_connection.write(json_data.encode())
            self._serial_connection.flush()  # Ensure data is sent
            
            # Wait for response with timeout
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    response = self._serial_connection.readline().decode().strip()
                    if response:
                        try:
                            response_data = json.loads(response)
                            return response_data
                        except json.JSONDecodeError:
                            journaling_manager.recordError(f"Invalid JSON response: {response}")
                            continue
                except serial.SerialTimeoutException:
                    journaling_manager.recordError(f"Timeout on attempt {attempt + 1}")
                    continue
                
                time.sleep(1)  # Wait before next attempt
            
            raise CommandError("No response from device")
            
        except Exception as e:
            journaling_manager.recordError(f"Serial communication error: {str(e)}")
            raise CommandError(f"Serial communication failed: {str(e)}")

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
        """Find LLM service port and connect"""
        try:
            journaling_manager.recordInfo(f"Setting up TCP connection to {self.ip}:{self.port}...")
            
            # Try to connect and ping with current IP and port
            initial_connection = False
            try:
                # First check basic socket connection
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(3.0)  # 3 second timeout for initial connection
                    s.connect((self.ip, self.port))
                    
                    # If socket connects, try a ping command to verify LLM service
                    ping_command = {
                        "request_id": f"ping_{int(time.time())}",
                        "work_id": "sys",
                        "action": "ping",
                        "object": "system",
                        "data": None
                    }
                    
                    # Send ping and wait for response
                    json_data = json.dumps(ping_command) + "\n"
                    s.sendall(json_data.encode())
                    
                    # Wait for response with timeout
                    s.settimeout(3.0)
                    response = ""
                    while True:
                        chunk = s.recv(1).decode()
                        if not chunk:
                            break
                        response += chunk
                        if chunk == "\n":
                            break
                    
                    # Verify ping response
                    if response.strip():
                        try:
                            response_data = json.loads(response.strip())
                            if response_data.get("error", {}).get("code", -1) == 0:
                                initial_connection = True
                            else:
                                journaling_manager.recordError("Ping response indicated failure")
                        except json.JSONDecodeError:
                            journaling_manager.recordError("Invalid JSON response from ping")
                    else:
                        journaling_manager.recordError("Empty response from ping")
                    
            except (socket.timeout, ConnectionRefusedError, OSError, json.JSONDecodeError) as e:
                journaling_manager.recordInfo(f"Initial TCP connection/ping failed: {e}")
            
            if initial_connection:
                self.endpoint = f"{self.ip}:{self.port}"
                self.connected = True
                journaling_manager.recordInfo("TCP connection established and verified with ping")
                return True
            
            # If direct connection fails, try to discover IP via ADB
            journaling_manager.recordInfo("TCP connection failed. Attempting to discover IP via ADB...")
            ip_from_adb = await self._discover_ip_via_adb()
            
            if ip_from_adb:
                journaling_manager.recordInfo(f"Found device IP via ADB: {ip_from_adb}")
                # Update IP in instance and config
                self.ip = ip_from_adb
                CONFIG.llm_service["ip"] = ip_from_adb
                
                # Save to config for future use
                if CONFIG.save():
                    journaling_manager.recordInfo(f"Updated and saved configuration with new IP: {ip_from_adb}")
                else:
                    journaling_manager.recordWarning(f"Updated configuration with new IP: {ip_from_adb} but failed to save")
                
                # Try TCP connection with the new IP
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(3.0)
                        s.connect((self.ip, self.port))
                        
                        # Try ping with new IP
                        ping_command = {
                            "request_id": f"ping_{int(time.time())}",
                            "work_id": "sys",
                            "action": "ping",
                            "object": "system",
                            "data": None
                        }
                        
                        # Send ping and wait for response
                        json_data = json.dumps(ping_command) + "\n"
                        s.sendall(json_data.encode())
                        
                        # Wait for response with timeout
                        s.settimeout(3.0)
                        response = ""
                        while True:
                            chunk = s.recv(1).decode()
                            if not chunk:
                                break
                            response += chunk
                            if chunk == "\n":
                                break
                        
                        # Verify ping response
                        if response.strip():
                            try:
                                response_data = json.loads(response.strip())
                                if response_data.get("error", {}).get("code", -1) == 0:
                                    self.endpoint = f"{self.ip}:{self.port}"
                                    self.connected = True
                                    journaling_manager.recordInfo("TCP connection established and verified with discovered IP")
                                    return True
                            except json.JSONDecodeError:
                                journaling_manager.recordError("Invalid JSON response from ping with discovered IP")
                        
                except (socket.timeout, ConnectionRefusedError, OSError) as e:
                    journaling_manager.recordError(f"Connection/ping failed with discovered IP: {e}")
            
            # If we get here, both connection attempts failed
            journaling_manager.recordError("Failed to establish verified TCP connection with both configured and discovered IPs")
            self.connected = False
            return False
            
        except Exception as e:
            journaling_manager.recordError(f"TCP connection error: {e}")
            self.connected = False
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
    
    async def transmit(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command over TCP and get response"""
        if not self.connected:
            raise ConnectionError("TCP connection not established")
        
        try:
            ip, port = self.endpoint.split(":")
            port = int(port)
            
            # Connect to the LLM service
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                
                # Prepare JSON data - don't log it here, it's already logged in transmit_json
                json_data = json.dumps(command) + "\n"
                
                # Connect and send
                journaling_manager.recordDebug(f"Connecting to {ip}:{port}...")
                s.connect((ip, port))
                s.sendall(json_data.encode())
                journaling_manager.recordDebug(f"Command sent successfully to {ip}:{port}")
                
                # Wait for response using byte-by-byte approach
                buffer = ""
                journaling_manager.recordDebug("Waiting for response...")
                while True:
                    try:
                        data = s.recv(1).decode()
                        if not data:
                          journaling_manager.recordDebug("No more data received")
                          break
                        buffer += data
                        
                        # For chat responses, print characters as they arrive
                        if command.get("action") == "inference":
                            print(data, end="", flush=True)
                        
                        if data == "\n":
                            journaling_manager.recordDebug("Received complete response")
                            break
                    except socket.timeout:
                        journaling_manager.recordError("Socket timeout")
                        break
        
                # Parse response - don't log it here, it's already logged in transmit_json
                try:
                    response = json.loads(buffer.strip())
                    return response
                except json.JSONDecodeError:
                    journaling_manager.recordError(f"Failed to parse JSON: {buffer.strip()}")
                    return {
                        "request_id": command.get("request_id", f"error_{int(time.time())}"),
                        "work_id": command.get("work_id", "sys"),
                        "data": "None",
                        "error": {"code": -1, "message": "Failed to parse response"},
                        "object": command.get("object", "None"),
                        "created": int(time.time())
                    }
                
        except Exception as e:
            journaling_manager.recordError(f"TCP communication error: {str(e)}")
            raise CommandError(f"TCP communication failed: {str(e)}")

    def _find_llm_port(self, ssh) -> Optional[int]:
        """Find the port where the LLM service is running"""
        journaling_manager.recordInfo("\nChecking for LLM service port...")
        
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
        journaling_manager.recordInfo("\nTrying common ports...")
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
            ip, port = self.endpoint.split(":")
            port = int(port)
            
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
                json_data = json.dumps(command) + "\n"
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
                
                if buffer:
                    try:
                        response = json.loads(buffer.decode().strip())
                        return response
                    except json.JSONDecodeError as e:
                        journaling_manager.recordError(f"Failed to parse JSON: {e}")
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