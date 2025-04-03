#!/usr/bin/env python
"""
Reset the PenphinMind device
"""

import socket
import json
import time

# Connection settings
IP_ADDRESS = "10.0.0.141"
PORT = 10001

def reset_device():
    """Send a reset command to the device"""
    print(f"\n===== RESETTING DEVICE =====")
    print(f"Target: {IP_ADDRESS}:{PORT}")
    
    try:
        # Create socket with timeout
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)  # 5 second timeout
            
            # Connect
            print("Connecting...")
            s.connect((IP_ADDRESS, PORT))
            print(f"✅ Socket connection established")
            
            # Send reset command
            reset_command = {
                "request_id": "999",
                "work_id": "sys",
                "action": "reset"
            }
            
            # Send command with newline terminator
            json_data = json.dumps(reset_command) + "\n"
            print(f"Sending reset command: {json_data.strip()}")
            s.sendall(json_data.encode())
            
            # Read response
            buffer = bytearray()
            s.settimeout(5.0)
            
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
                    print("Socket timeout with partial data")
                else:
                    print("Socket timeout with no data")
                    return False
            
            # Process response if we have data
            if buffer:
                response_str = buffer.decode().strip()
                print(f"Received: {response_str}")
                
                try:
                    # Parse JSON response
                    response_data = json.loads(response_str)
                    
                    # Check for success in error code
                    if "error" in response_data and isinstance(response_data["error"], dict):
                        error_code = response_data["error"].get("code", -1)
                        
                        if error_code == 0:
                            print(f"✅ Reset command successful!")
                            print("Device should now be resetting. Wait a few seconds before reconnecting.")
                            return True
                        else:
                            error_msg = response_data["error"].get("message", "Unknown error")
                            print(f"❌ API error: {error_msg}")
                            return False
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response")
                    return False
            else:
                print("❌ No response data")
                return False
                
    except socket.timeout:
        print(f"❌ Connection timeout")
        return False
    except socket.error as e:
        print(f"❌ Socket error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Send reset command
    reset_success = reset_device()
    
    if reset_success:
        print("\nWaiting 10 seconds for device to reboot...")
        time.sleep(10)
        print("Device should now be rebooted and ready for connections.")
    else:
        print("\nReset command failed. You may need to manually reset the device.") 