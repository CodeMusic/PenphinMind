#!/usr/bin/env python3
import serial
import json
import time
import subprocess

def setup_port():
    """Get the device port and set permissions"""
    # Get device info
    devices = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True)
    print("\nADB Devices List:")
    print(devices.stdout)
    
    if "axera-ax620e" not in devices.stdout:
        raise Exception("AX620e device not found")
    
    # Find available ports
    result = subprocess.run(
        ["adb", "shell", "ls -l /dev/tty*"],
        capture_output=True,
        text=True
    )
    print("\nAvailable ports:")
    print(result.stdout)
    
    # Set permissions for ttyS1
    port = "/dev/ttyS1"
    subprocess.run(["adb", "shell", f"chmod 666 {port}"])
    return port

def login_to_device(port: str):
    """Login to the device with default credentials"""
    print("\nAttempting to login...")
    
    # Configure port
    subprocess.run([
        "adb", "shell", 
        f"stty -F {port} 115200 cs8 -cstopb -parenb"
    ])
    
    # Send username
    print("Sending username...")
    subprocess.run([
        "adb", "shell",
        f"echo 'root' > {port}"
    ])
    time.sleep(1)
    
    # Send password
    print("Sending password...")
    subprocess.run([
        "adb", "shell",
        f"echo '123456' > {port}"
    ])
    time.sleep(1)
    
    # Read any response
    print("Checking login response...")
    subprocess.run([
        "adb", "shell",
        f"cat {port}"
    ])
    
    print("Login sequence completed")

def send_raw_command(command: str):
    """Send a raw command to the device"""
    # Convert to JSON if not already
    try:
        json.loads(command)
        json_data = command
    except json.JSONDecodeError:
        json_data = json.dumps({
            "type": "LLM",
            "command": "generate",
            "data": {
                "prompt": command,
                "timestamp": int(time.time() * 1000),
                "version": "1.0",
                "request_id": f"chat_{int(time.time())}"
            }
        })
    
    # Add newline if not present
    if not json_data.endswith("\n"):
        json_data += "\n"
    
    print(f"\nSending: {json_data.strip()}")
    subprocess.run(["adb", "shell", f"echo -n '{json_data}' > /dev/ttyS1"])
    
    # Read response
    print("\nResponse:")
    subprocess.run(["adb", "shell", "dd if=/dev/ttyS1 bs=1 count=1024 2>/dev/null"])

def main():
    """Main function"""
    try:
        port = setup_port()
        print(f"\nUsing port: {port}")
        
        # Login first
        login_to_device(port)
        
        print("\nEnter commands (type 'exit' to quit):")
        print("1. For raw JSON, start with '{'")
        print("2. For text prompts, just type normally")
        
        while True:
            command = input("\n> ").strip()
            if command.lower() == 'exit':
                break
            send_raw_command(command)
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 