import json
import serial
import serial.tools.list_ports
import time
import os
import stat
import pwd
import grp
from typing import Optional, Dict, Any
import subprocess

class SynapticPathways:
    """
    Manages JSON communication pathways between cortices with SSH-aware permissions
    """
    _serial_connection: Optional[serial.Serial] = None
    _managers = {}
    _max_retries = 3
    _retry_delay = 1.0
    _last_known_port = "/dev/ttyUSB0"

    @classmethod
    def _check_device_permissions(cls, port: str) -> bool:
        try:
            if not os.path.exists(port):
                print(f"Device {port} does not exist")
                return False

            # Get current user and group info
            current_user = pwd.getpwuid(os.getuid()).pw_name
            user_groups = [g.gr_name for g in grp.getgrall() if current_user in g.gr_mem]
            
            stat_info = os.stat(port)
            owner = pwd.getpwuid(stat_info.st_uid).pw_name
            group = grp.getgrgid(stat_info.st_gid).gr_name

            print(f"Device {port}:")
            print(f"  Owner: {owner}")
            print(f"  Group: {group}")
            print(f"  Current user: {current_user}")
            print(f"  User groups: {user_groups}")
            print(f"  Permissions: {oct(stat_info.st_mode)[-3:]}")

            # Check if user has access through group membership
            if 'dialout' not in user_groups:
                print("Adding user to dialout group...")
                try:
                    subprocess.run(['sudo', 'usermod', '-a', '-G', 'dialout', current_user], check=True)
                    print("Added to dialout group - please reconnect SSH session")
                    return False
                except subprocess.CalledProcessError as e:
                    print(f"Failed to add to dialout group: {e}")

            # Ensure device has correct permissions
            if not os.access(port, os.R_OK | os.W_OK):
                print("Fixing device permissions...")
                try:
                    subprocess.run(['sudo', 'chown', 'root:dialout', port], check=True)
                    subprocess.run(['sudo', 'chmod', '660', port], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Failed to fix permissions: {e}")
                    return False

            return True
            
        except Exception as e:
            print(f"Error checking permissions: {e}")
            return False

    @classmethod
    def _find_device(cls) -> str:
        """
        Find the correct USB device by checking available ports
        """
        try:
            # First try listing with sudo to ensure we can see all devices
            result = subprocess.run(['sudo', 'ls', '/dev/ttyUSB*'], 
                                  capture_output=True, 
                                  text=True)
            if result.stdout:
                devices = result.stdout.strip().split('\n')
                print(f"Found USB devices: {devices}")
                for device in devices:
                    if cls._check_device_permissions(device):
                        return device

            # Fallback to pyserial port listing
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if "USB" in port.device and cls._check_device_permissions(port.device):
                    return port.device
                    
        except Exception as e:
            print(f"Error finding USB devices: {e}")
            
        return cls._last_known_port

    @classmethod
    def initialize(cls, port=None, baud_rate=115200):
        """Initialize serial connection with SSH-aware retry logic"""
        retry_count = 0
        while retry_count < cls._max_retries:
            try:
                if cls._serial_connection:
                    try:
                        cls._serial_connection.close()
                    except:
                        pass

                port = port or cls._last_known_port
                if not cls._check_device_permissions(port):
                    raise serial.SerialException(f"Cannot access {port} - check SSH session")

                print(f"Attempting connection to {port}")
                cls._serial_connection = serial.Serial(
                    port=port,
                    baudrate=baud_rate,
                    timeout=2,
                    exclusive=True,
                    rtscts=True,  # Enable hardware flow control
                    dsrdtr=True   # Enable hardware flow control
                )
                
                # Clear any pending data
                cls._serial_connection.reset_input_buffer()
                cls._serial_connection.reset_output_buffer()
                time.sleep(0.1)  # Short delay after buffer clear
                
                print("Testing connection...")
                cls._serial_connection.write(b'{"cmd": "ping"}\n')
                time.sleep(0.1)  # Wait for response
                response = cls._serial_connection.readline()
                
                if not response:
                    raise serial.SerialException("No response from device")
                    
                print(f"Successfully connected to {port}")
                return
                
            except serial.SerialException as e:
                retry_count += 1
                print(f"Attempt {retry_count}: Connection failed: {e}")
                if retry_count < cls._max_retries:
                    print(f"Retrying in {cls._retry_delay} seconds...")
                    time.sleep(cls._retry_delay)
                else:
                    raise

    @classmethod
    def transmit_json(cls, command: Dict[str, Any]) -> str:
        """Transmit JSON commands with retry logic"""
        retry_count = 0
        while retry_count < cls._max_retries:
            try:
                if not cls._serial_connection or not cls._serial_connection.is_open:
                    cls.initialize()

                json_data = json.dumps(command) + "\n"
                cls._serial_connection.write(json_data.encode())
                response = cls._serial_connection.readline().decode().strip()
                
                if not response:
                    raise serial.SerialException("No data received")
                    
                return response
                
            except Exception as e:
                retry_count += 1
                print(f"Attempt {retry_count}: Neural transmission error: {e}")
                if retry_count < cls._max_retries:
                    print(f"Retrying in {cls._retry_delay} seconds...")
                    time.sleep(cls._retry_delay)
                    cls.initialize()  # Reinitialize with device search
                else:
                    raise

    @classmethod
    def register_manager(cls, manager_type: str, manager_instance):
        """
        Register a manager instance for cross-cortex communication
        """
        cls._managers[manager_type] = manager_instance

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
        if "redmine" in cls._managers:
            cls._managers["redmine"].log_learning(
                title="Signal Transmission",
                description=f"Signal: {signal}\nTarget: {target}\nResponse: {response}",
                category="communication"
            )
            
        return response

    @classmethod
    def close_connections(cls):
        """Safely close all connections"""
        if cls._serial_connection:
            try:
                cls._serial_connection.reset_input_buffer()
                cls._serial_connection.reset_output_buffer()
                cls._serial_connection.close()
            except:
                pass 