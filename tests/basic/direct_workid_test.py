#!/usr/bin/env python3
"""
Direct Work ID Test
----------------
A simple direct test script that directly uses TCP socket to test if
the work_id from LLM setup is needed for inference commands.
"""

import sys
import os
import json
import asyncio
import time
import socket
from pathlib import Path

# Define basic logging
def log(message, level="INFO"):
    """Simple logging function"""
    print(f"[{level}] {message}")

class DirectTransport:
    """A minimal direct transport implementation using TCP socket"""
    
    def __init__(self, host="127.0.0.1", port=6000):
        """Initialize transport with host and port"""
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        log(f"DirectTransport created for {host}:{port}")
    
    async def connect(self):
        """Connect to the device"""
        try:
            # Create a TCP/IP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(5.0)  # 5 second timeout
            self.connected = True
            log(f"Connected to {self.host}:{self.port}")
            return True
        except socket.error as e:
            log(f"Connection failed: {e}", "ERROR")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the device"""
        if self.sock:
            self.sock.close()
        self.connected = False
        log("Disconnected from device")
    
    async def transmit(self, command):
        """Transmit a command to the device"""
        if not self.connected:
            log("Not connected, attempting to connect...", "WARNING")
            if not await self.connect():
                return {"error": {"code": -1, "message": "Failed to connect"}}
        
        try:
            # Convert command to JSON if it's a dict
            if isinstance(command, dict):
                command_str = json.dumps(command)
            else:
                command_str = str(command)
                
            log(f"Sending: {command_str[:100]}...")
            
            # Send data
            self.sock.sendall(command_str.encode('utf-8'))
            
            # Receive response with a 5-second timeout
            start_time = time.time()
            data = b''
            
            while True:
                if time.time() - start_time > 10.0:  # 10 second max wait
                    log("Response timeout", "ERROR")
                    break
                
                try:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        # Connection closed
                        break
                    data += chunk
                    
                    # Try to parse what we have
                    try:
                        # Check if we have complete JSON
                        result = json.loads(data.decode('utf-8'))
                        break
                    except json.JSONDecodeError:
                        # Wait for more data
                        continue
                except socket.timeout:
                    log("Socket timeout while waiting for data", "WARNING")
                    break
                except socket.error as e:
                    log(f"Socket error: {e}", "ERROR")
                    break
            
            # Parse the response
            if data:
                try:
                    result = json.loads(data.decode('utf-8'))
                    return result
                except json.JSONDecodeError as e:
                    log(f"Invalid JSON response: {e}", "ERROR")
                    return {"error": {"code": -1, "message": f"Invalid JSON: {e}"}}
            else:
                return {"error": {"code": -1, "message": "Empty response"}}
                
        except Exception as e:
            log(f"Transmission error: {e}", "ERROR")
            return {"error": {"code": -1, "message": f"Transmission error: {e}"}}

async def test_workid():
    """Test if work_id from setup is needed for inference"""
    log("\n===== DIRECT WORK ID TEST =====")
    
    try:
        # Create the transport
        log("Creating transport...")
        transport = DirectTransport(host="192.168.43.130", port=6000)
        
        # Connect to device
        log("\n1. Connecting to device...")
        success = await transport.connect()
        if not success:
            log("Cannot connect to device, test aborted", "ERROR")
            return
        
        # First create and send LLM setup command
        model_name = "qwen2.5-0.5b"
        log(f"\n2. Setting up LLM with model: {model_name}")
        
        setup_command = {
            "request_id": str(int(time.time())),
            "work_id": "llm",
            "action": "setup",
            "model": model_name,
            "response_format": "llm.utf-8",
            "input": "llm.utf-8",
            "enoutput": True,
            "enkws": False,
            "max_token_len": 127,
            "prompt": "You are a helpful assistant."
        }
        
        # Send the setup command
        log("Sending setup command...")
        setup_result = await transport.transmit(setup_command)
        
        # Output the setup result
        log("\nSetup Response:")
        log(json.dumps(setup_result, indent=2))
        
        # Extract the work_id from setup response
        specific_work_id = None
        if isinstance(setup_result, dict) and "work_id" in setup_result:
            specific_work_id = setup_result["work_id"]
            log(f"\n✅ Found work_id in response: {specific_work_id}")
        else:
            log("\n⚠️ No work_id found in response, will use default 'llm'")
            specific_work_id = "llm"
        
        # Wait to ensure setup is complete
        log("\nWaiting a moment for setup to complete...")
        await asyncio.sleep(2)
        
        # Test inference with specific work_id
        log(f"\n3. Testing inference with work_id: {specific_work_id}")
        
        specific_command = {
            "request_id": str(int(time.time())),
            "work_id": specific_work_id,  # Use the work_id from setup
            "action": "inference",
            "object": "llm.utf-8",
            "data": "Write a very short poem about debugging."
        }
        
        # Send the inference command
        log("Sending inference command with specific work_id...")
        specific_result = await transport.transmit(specific_command)
        
        # Output the result
        log("\nInference Response (with specific work_id):")
        log(json.dumps(specific_result, indent=2))
        
        # Check if inference succeeded with specific work_id
        specific_success = False
        if isinstance(specific_result, dict) and "error" in specific_result:
            error = specific_result.get("error", {})
            if isinstance(error, dict) and error.get("code") == 0:
                specific_success = True
                log("✅ Inference with specific work_id succeeded!")
                if "data" in specific_result:
                    data = specific_result.get("data", "")
                    log(f"Response: {data}")
            else:
                error_msg = error.get("message", "Unknown error")
                log(f"❌ Inference with specific work_id failed: {error_msg}", "ERROR")
        else:
            log("❌ Unexpected response format with specific work_id", "ERROR")
        
        # If we want to also test with generic work_id
        if specific_success:
            log("\n4. For comparison, NOT testing with generic 'llm' work_id")
            log("   since specific work_id already succeeded")
        
        # Clean up
        await transport.disconnect()
        log("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        log(f"Test error: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")

if __name__ == "__main__":
    asyncio.run(test_workid()) 