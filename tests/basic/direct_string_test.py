#!/usr/bin/env python3
"""
Direct String Test
----------------
Tests the LLM inference with push="true" parameter using direct WiFiTransport,
without requiring the Mind class or paramiko.

This script directly connects to the device's API endpoint to test if the
string format of "push":"true" resolves the inference error.
"""

import sys
import os
import json
import asyncio
import time
import socket

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Basic logging function since we may not have SystemJournelingManager
def log(message, level="INFO"):
    """Simple logging function"""
    print(f"[{level}] {message}")

class SimpleWiFiTransport:
    """
    Simple TCP client to connect to the device API
    This avoids dependency on the full transport_layer with paramiko
    """
    def __init__(self, host="10.0.0.82", port=10001):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.connected = False

    async def connect(self):
        """Connect to TCP endpoint"""
        try:
            log(f"Connecting to {self.host}:{self.port}...")
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            self.connected = True
            log(f"Connected successfully to {self.host}:{self.port}", "DEBUG")
            return True
        except Exception as e:
            log(f"Connection error: {e}", "ERROR")
            return False

    async def disconnect(self):
        """Close the connection"""
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except:
                pass
            self.connected = False
            log("Disconnected", "DEBUG")

    async def transmit(self, command):
        """Send a command and receive response"""
        if not self.connected:
            log("Not connected!", "ERROR")
            return {"error": {"code": -1, "message": "Not connected"}}

        try:
            # Convert command to JSON string if it's a dict
            if isinstance(command, dict):
                command_str = json.dumps(command)
            else:
                command_str = command

            # Add newline if not present
            if not command_str.endswith("\n"):
                command_str += "\n"

            # Log the command
            log(f"Sending: {command_str.strip()}", "DEBUG")

            # Send the command
            self.writer.write(command_str.encode("utf-8"))
            await self.writer.drain()

            # Read response
            response = await self.reader.read(4096)
            response_str = response.decode("utf-8").strip()
            
            # Log the response
            log(f"Received: {response_str}", "DEBUG")

            # Parse JSON response
            try:
                return json.loads(response_str)
            except json.JSONDecodeError:
                log(f"Invalid JSON in response: {response_str}", "ERROR")
                return {"error": {"code": -1, "message": "Invalid JSON response"}}

        except Exception as e:
            log(f"Transmission error: {e}", "ERROR")
            return {"error": {"code": -1, "message": f"Transmission error: {str(e)}"}}

async def create_test_command(prompt, with_push_as_string=True):
    """Create a test LLM inference command"""
    command = {
        "request_id": str(int(time.time())),
        "work_id": "llm",
        "action": "inference",
        "data": {
            "prompt": prompt,
            "stream": False
        }
    }
    
    # Add push parameter based on flag
    if with_push_as_string:
        command["data"]["push"] = "true"  # As string
    
    return command

async def run_test():
    """Run the direct test"""
    try:
        print("\n===== DIRECT STRING TEST =====")
        print("Testing LLM inference with push=\"true\" parameter using direct TCP connection")
        print("===========================================")
        
        # Get connection details from environment or use defaults
        host = os.environ.get("PENPHIN_DEVICE_IP", "10.0.0.82")
        port = int(os.environ.get("PENPHIN_DEVICE_PORT", "10001"))
        
        # Create transport
        transport = SimpleWiFiTransport(host, port)
        
        # Step 1: Connect to device
        print("\n--- STEP 1: CONNECTING TO DEVICE ---")
        connect_result = await transport.connect()
        
        if not connect_result:
            print("❌ Failed to connect to device. Check IP/port and ensure device is powered on.")
            return
        
        print(f"✅ Connected to {host}:{port}")
        
        # Step 2: Send ping to verify connectivity
        print("\n--- STEP 2: VERIFYING CONNECTIVITY ---")
        ping_command = {
            "request_id": str(int(time.time())),
            "work_id": "sys",
            "action": "ping"
        }
        
        ping_response = await transport.transmit(ping_command)
        print("Ping response:")
        print(json.dumps(ping_response, indent=2))
        
        if not ping_response or not isinstance(ping_response, dict):
            print("❌ Invalid ping response. Device may not be responding correctly.")
            await transport.disconnect()
            return
        
        # Check if ping was successful (error code 0 means success in API)
        ping_error = ping_response.get("error", {})
        if isinstance(ping_error, dict) and ping_error.get("code") == 0:
            print("✅ Ping successful!")
        else:
            print("❌ Ping failed. Device may not be responding correctly.")
            await transport.disconnect()
            return
        
        # Step 3: Test with string push
        print("\n--- STEP 3: TESTING WITH PUSH=\"true\" AS STRING ---")
        test_prompt = "Write a haiku about debugging code"
        
        # Create command with push="true" as string
        string_command = await create_test_command(test_prompt, with_push_as_string=True)
        
        # Display the command
        print("\nCommand with push=\"true\" as string:")
        print(json.dumps(string_command, indent=2))
        
        # Check the serialized form
        serialized = json.dumps(string_command)
        print("\nSerialized JSON:")
        print(serialized)
        
        if '"push":"true"' in serialized.replace(" ", ""):
            print("✅ JSON contains 'push':'true' as string")
        else:
            print("❌ JSON does NOT contain 'push':'true' as string")
        
        # Send the command
        print("\nSending command with push=\"true\" as string...")
        string_response = await transport.transmit(string_command)
        
        print("\nResponse:")
        print(json.dumps(string_response, indent=2))
        
        # Check if it worked
        string_error = string_response.get("error", {})
        if isinstance(string_error, dict) and string_error.get("code") == 0:
            print("\n✅ SUCCESS: Command with push=\"true\" as string worked!")
            data = string_response.get("data", "")
            if data:
                print(f"Response text: {data[:100]}...")
            else:
                print("Response contains no data.")
        else:
            error_message = string_error.get("message", "Unknown error")
            print(f"\n❌ ERROR: {error_message}")
            
            # If it still mentions push, suggest other approaches
            if "push" in str(error_message).lower():
                print("\nThe error still mentions 'push'. Other options to try:")
                print("1. No push parameter at all")
                print("2. Integer values (0, 1) instead of boolean/string")
                print("3. Different capitalization ('True', 'TRUE')")
                
                # Try a version without push parameter for comparison
                print("\n--- STEP 4: TESTING WITHOUT PUSH PARAMETER ---")
                no_push_command = await create_test_command(test_prompt, with_push_as_string=False)
                print("\nCommand without push parameter:")
                print(json.dumps(no_push_command, indent=2))
                
                print("\nSending command without push parameter...")
                no_push_response = await transport.transmit(no_push_command)
                
                print("\nResponse:")
                print(json.dumps(no_push_response, indent=2))
        
        # Clean up
        await transport.disconnect()
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Try to clean up
        try:
            if transport and transport.connected:
                await transport.disconnect()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(run_test()) 