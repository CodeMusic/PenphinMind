#!/usr/bin/env python3
"""
Simple Work ID Test
----------------
A minimal test script that directly tests if using the correct work_id 
from LLM setup is required for inference commands.
"""

import sys
import os
import json
import asyncio
import time
import socket
from pathlib import Path

# Simple logging function
def log(message, level="INFO"):
    print(f"[{level}] {message}")

# Direct socket communication with device
class DeviceConnection:
    def __init__(self, host="10.0.0.141", port=6000):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        log(f"Created connection to {host}:{port}")
    
    async def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)  # 5 second timeout for connection
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(10.0)  # 10 second timeout for data
            self.connected = True
            log(f"✅ Connected to {self.host}:{self.port}")
            return True
        except socket.error as e:
            log(f"Connection failed: {e}", "ERROR")
            return False
    
    async def disconnect(self):
        if self.sock:
            self.sock.close()
        self.connected = False
        log("Disconnected from device")
    
    async def send_command(self, command):
        if not self.connected:
            if not await self.connect():
                return {"error": {"code": -1, "message": "Connection failed"}}
        
        try:
            # Convert command to JSON
            cmd_str = json.dumps(command)
            log(f"Sending: {cmd_str}")
            
            # Send command
            self.sock.sendall(cmd_str.encode('utf-8'))
            
            # Receive response
            data = b''
            start_time = time.time()
            
            while True:
                if time.time() - start_time > 15.0:  # 15 second timeout
                    log("Response timeout", "ERROR")
                    break
                
                try:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    
                    # Check if we have complete JSON
                    try:
                        json.loads(data.decode('utf-8'))
                        break  # If parsing succeeds, we have the full message
                    except json.JSONDecodeError:
                        continue  # Keep waiting for more data
                except socket.timeout:
                    log("Socket timeout", "WARNING")
                    break
                except socket.error as e:
                    log(f"Socket error: {e}", "ERROR")
                    break
            
            # Parse response
            if data:
                try:
                    result = json.loads(data.decode('utf-8'))
                    return result
                except json.JSONDecodeError as e:
                    log(f"Invalid response: {e}", "ERROR")
                    return {"error": {"code": -1, "message": "Invalid response"}}
            else:
                return {"error": {"code": -1, "message": "Empty response"}}
        except Exception as e:
            log(f"Error sending command: {e}", "ERROR")
            return {"error": {"code": -1, "message": f"Error: {e}"}}

async def try_connect_device():
    """Try to connect to the device using different IP/port combinations"""
    log("\n===== TRYING MULTIPLE CONNECTION OPTIONS =====")
    
    # List of potential IP addresses and ports to try
    hosts = ["10.0.0.141", "192.168.1.1", "192.168.43.130", "127.0.0.1"]
    ports = [6000, 6001, 5000, 80]
    
    # Try each combination
    for host in hosts:
        for port in ports:
            connection = DeviceConnection(host=host, port=port)
            log(f"Trying {host}:{port}...")
            if await connection.connect():
                log(f"✅ Successfully connected to {host}:{port}")
                
                # Try a basic ping to verify it's the right device
                ping_cmd = {
                    "request_id": str(int(time.time())),
                    "work_id": "sys",
                    "action": "ping"
                }
                
                result = await connection.send_command(ping_cmd)
                if isinstance(result, dict) and "error" in result:
                    error = result.get("error", {})
                    if isinstance(error, dict) and error.get("code") == 0:
                        log(f"✅ Ping successful on {host}:{port}")
                        await connection.disconnect()
                        return host, port
                
                await connection.disconnect()
    
    log("❌ Could not find working connection to device", "ERROR")
    return None, None

async def run_test():
    log("\n===== WORK ID TEST =====")
    
    # First find a working connection
    host, port = await try_connect_device()
    if not host:
        log("Aborting test - could not connect to device", "ERROR")
        return
    
    # Create connection with the working host/port
    connection = DeviceConnection(host=host, port=port)
    
    try:
        # Connect to device
        log("\n1. Connecting to device...")
        if not await connection.connect():
            log("Test aborted - cannot connect to device", "ERROR")
            return
        
        # Set up the LLM
        log("\n2. Setting up LLM...")
        setup_command = {
            "request_id": str(int(time.time())),
            "work_id": "llm",
            "action": "setup",
            "model": "qwen2.5-0.5b",
            "response_format": "llm.utf-8",
            "input": "llm.utf-8",
            "enoutput": True,
            "enkws": False,
            "max_token_len": 127,
            "prompt": "You are a helpful assistant."
        }
        
        setup_result = await connection.send_command(setup_command)
        log("\nSetup Response:")
        log(json.dumps(setup_result, indent=2))
        
        # Extract work_id from setup response
        specific_work_id = None
        if isinstance(setup_result, dict) and "work_id" in setup_result:
            specific_work_id = setup_result["work_id"]
            log(f"\n✅ Found work_id in response: {specific_work_id}")
        else:
            log("\n⚠️ No work_id found in setup response", "WARNING")
            specific_work_id = "llm"
        
        # Wait for setup to complete
        log("\nWaiting for setup to complete...")
        await asyncio.sleep(2)
        
        # Run inference with the specific work_id
        log(f"\n3. Testing inference with specific work_id: {specific_work_id}")
        inference_command = {
            "request_id": str(int(time.time())),
            "work_id": specific_work_id,  # Use the specific work_id from setup
            "action": "inference",
            "object": "llm.utf-8",
            "data": "Write a short haiku about debugging."
        }
        
        inference_result = await connection.send_command(inference_command)
        log("\nInference Response:")
        log(json.dumps(inference_result, indent=2))
        
        # Check if inference succeeded
        inference_success = False
        if isinstance(inference_result, dict) and "error" in inference_result:
            error = inference_result.get("error", {})
            if isinstance(error, dict) and error.get("code") == 0:
                inference_success = True
                log("✅ Inference with specific work_id succeeded!")
                if "data" in inference_result:
                    data = inference_result.get("data", "")
                    log(f"Response: {data}")
            else:
                error_msg = error.get("message", "Unknown error")
                log(f"❌ Inference with specific work_id failed: {error_msg}", "ERROR")
        else:
            log("❌ Unexpected response format", "ERROR")
        
        # If successful, try with generic "llm" work_id to see if it fails
        if inference_success and specific_work_id != "llm":
            log("\n4. Testing inference with generic 'llm' work_id for comparison")
            generic_command = {
                "request_id": str(int(time.time())),
                "work_id": "llm",  # Using generic work_id
                "action": "inference",
                "object": "llm.utf-8",
                "data": "Write a short haiku about programming."
            }
            
            generic_result = await connection.send_command(generic_command)
            log("\nGeneric work_id Response:")
            log(json.dumps(generic_result, indent=2))
            
            # Check if generic inference succeeded
            if isinstance(generic_result, dict) and "error" in generic_result:
                error = generic_result.get("error", {})
                if isinstance(error, dict) and error.get("code") == 0:
                    log("✅ Inference with generic work_id ALSO succeeded!")
                    if "data" in generic_result:
                        data = generic_result.get("data", "")
                        log(f"Response: {data}")
                    log("\n⚠️ This suggests work_id is NOT required to match!", "WARNING")
                else:
                    error_msg = error.get("message", "Unknown error")
                    log(f"❌ Inference with generic work_id failed: {error_msg}")
                    log("\n✅ This confirms specific work_id IS required!")
            else:
                log("❌ Unexpected response format for generic work_id test", "ERROR")
        
        log("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        log(f"Test error: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
    finally:
        await connection.disconnect()

if __name__ == "__main__":
    asyncio.run(run_test()) 