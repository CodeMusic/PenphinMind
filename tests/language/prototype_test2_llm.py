import os
import subprocess
import serial
import json
import time

# Constants
SERIAL_PORT = "/dev/ttyUSB0"  # Change if necessary
BAUD_RATE = 115200
ADB_IP = "192.168.1.100"  # Change to your device's IP

def is_adb_available():
    """Check if an ADB device is connected via USB or Wi-Fi."""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        devices = result.stdout.strip().split("\n")[1:]  # Ignore header
        return any(device.strip() and "device" in device for device in devices)
    except FileNotFoundError:
        return False  # ADB not installed

def is_serial_available():
    """Check if the Serial device is connected."""
    return os.path.exists(SERIAL_PORT)

def send_command(command):
    """Unified function to send a JSON command over ADB (USB/Wi-Fi) or Serial."""
    command_json = json.dumps(command)

    if is_adb_available():
        # Use ADB mode (USB or Wi-Fi)
        print("📡 Using ADB mode")
        try:
            adb_command = f"adb shell 'echo {command_json}'"
            result = subprocess.run(adb_command, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            return f"ADB Error: {e}"

    elif is_serial_available():
        # Use Serial mode
        print("🔌 Using Serial mode")
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
                ser.write(command_json.encode() + b'\n')
                time.sleep(0.5)  # Wait for response
                response = ser.readline().decode().strip()
                return response
        except Exception as e:
            return f"Serial Error: {e}"
    
    else:
        return "❌ No connection available"

# Example JSON Command
command_to_send = {"cmd": "set_mode", "mode": "active"}

# Send the command using the best available transport
response = send_command(command_to_send)
print("Response:", response)