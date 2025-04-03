#!/usr/bin/env python
"""
Simple script to test TCP connection to port 10001 on different IP addresses
"""

import socket
import time
import json
import sys

# List of IP addresses to try
IP_ADDRESSES = [
    "127.0.0.1",        # Localhost
    "192.168.1.100",    # Common M5Stack IP
    "192.168.1.101",
    "192.168.0.100",
    "192.168.0.101",
    "10.0.0.82",
    # Add custom IPs below:
    # "your.custom.ip.here",
]

PORT = 10001  # LLM service port

def test_ping(ip, port):
    """Test connection with a ping command"""
    print(f"Testing connection to {ip}:{port}...")
    
    try:
        # Create socket with timeout
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)  # 2 second timeout
            
            # Attempt to connect
            result = s.connect_ex((ip, port))
            
            if result != 0:
                print(f"❌ Connection failed to {ip}:{port} - Error code: {result}")
                return False
            
            print(f"✅ Socket connection established to {ip}:{port}")
            
            # Try sending a ping command
            ping_command = {
                "request_id": "001",
                "work_id": "sys",
                "action": "ping"
            }
            
            # Send command with newline terminator
            json_data = json.dumps(ping_command) + "\n"
            s.sendall(json_data.encode())
            print(f"  Sent: {json_data.strip()}")
            
            # Set longer timeout for reading response
            s.settimeout(5.0)
            
            # Read response
            buffer = bytearray()
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
                    print("  Timeout with partial data")
                else:
                    print("  Timeout waiting for response")
                    return False
            
            # Process response if we have data
            if buffer:
                response_str = buffer.decode().strip()
                print(f"  Received: {response_str}")
                
                try:
                    # Parse JSON response
                    response_data = json.loads(response_str)
                    
                    # Check for success in error code
                    if "error" in response_data and isinstance(response_data["error"], dict):
                        error_code = response_data["error"].get("code", -1)
                        
                        if error_code == 0:
                            print(f"  ✅ Ping successful to {ip}:{port}")
                            return True
                        else:
                            print(f"  ❌ API error: {response_data['error'].get('message', 'Unknown error')}")
                            return False
                except json.JSONDecodeError:
                    print(f"  ❌ Invalid JSON response: {response_str}")
                    return False
            else:
                print("  ❌ No response data")
                return False
                
    except socket.timeout:
        print(f"❌ Connection timeout to {ip}:{port}")
        return False
    except socket.error as e:
        print(f"❌ Socket error connecting to {ip}:{port}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Test connections to multiple IP addresses"""
    print("===== LLM SERVICE CONNECTION TEST =====")
    print(f"Target port: {PORT}")
    print("Testing connection to different IP addresses...\n")
    
    # Keep track of successful connections
    successful_ips = []
    
    # Get custom IP from command line if provided
    custom_ip = None
    if len(sys.argv) > 1:
        custom_ip = sys.argv[1]
        print(f"Testing custom IP from command line: {custom_ip}")
        if test_ping(custom_ip, PORT):
            successful_ips.append(custom_ip)
        print()
    
    # Test each IP address in the list
    for ip in IP_ADDRESSES:
        # Skip if we already tested this IP as a custom IP
        if ip == custom_ip:
            continue
            
        if test_ping(ip, PORT):
            successful_ips.append(ip)
        print()  # Add blank line between tests
    
    # Print summary
    print("===== CONNECTION TEST SUMMARY =====")
    if successful_ips:
        print(f"✅ Successfully connected to {len(successful_ips)} IP addresses:")
        for ip in successful_ips:
            print(f"  - {ip}:{PORT}")
    else:
        print("❌ Could not connect to any IP address")
        print("\nTroubleshooting tips:")
        print("1. Make sure the device is powered on")
        print("2. Verify the device is connected to your network")
        print("3. Check your network settings and firewall")
        print("4. Try using a different network connection")
        print("5. Verify the correct IP address of your device")

if __name__ == "__main__":
    main() 