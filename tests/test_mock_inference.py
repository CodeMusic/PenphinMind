#!/usr/bin/env python3
"""
Mock test for the inference command with push=false parameter.
This test simulates the WiFiTransport functionality to validate command structure.
"""

import asyncio
import json
import traceback
import sys
import os
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MockWiFiTransport:
    """Mock WiFiTransport class for testing command structure"""
    
    def __init__(self, ip="auto", port="auto"):
        self.ip = ip
        self.port = port
        self.connected = False
        
    async def connect(self):
        """Simulate connection"""
        print(f"📡 [MOCK] Connecting to {self.ip}:{self.port}")
        self.connected = True
        return True
        
    async def disconnect(self):
        """Simulate disconnection"""
        print("📡 [MOCK] Disconnecting")
        self.connected = False
        
    async def transmit(self, command):
        """
        Mock transmit function that validates command structure
        but doesn't actually send anything
        """
        print(f"📡 [MOCK] Transmitting command:")
        print(json.dumps(command, indent=2))
        
        # Check for API expected structure
        if not isinstance(command, dict):
            return {"error": {"code": 1, "message": "Command must be a dictionary"}}
            
        required_fields = ["request_id", "work_id", "action"]
        for field in required_fields:
            if field not in command:
                return {"error": {"code": 1, "message": f"Missing required field: {field}"}}
                
        # For inference commands, check data structure
        if command.get("work_id") == "llm" and command.get("action") == "inference":
            data = command.get("data", {})
            
            # Check if prompt exists
            if "prompt" not in data:
                return {"error": {"code": 1, "message": "Missing prompt in data"}}
                
            # Validate push parameter (this is where the actual issue might be)
            if "push" in data:
                push_value = data["push"]
                if not isinstance(push_value, bool):
                    return {"error": {"code": 1, "message": f"push parameter must be boolean, got {type(push_value)}"}}
                    
                # Check if push is explicitly set to false
                if push_value is not False:
                    return {"error": {"code": 1, "message": "push parameter must be false for inference", "push_value": push_value}}
                
                print(f"✅ push parameter correctly set to {push_value}")
            else:
                print("⚠️ No push parameter specified in command")
                
            # Check stream parameter
            if "stream" in data:
                stream_value = data["stream"]
                if not isinstance(stream_value, bool):
                    return {"error": {"code": 1, "message": f"stream parameter must be boolean, got {type(stream_value)}"}}
                
                print(f"✅ stream parameter set to {stream_value}")
                
            # Simulate successful response
            return {
                "created": time.time(),
                "error": {"code": 0, "message": "Success"},
                "request_id": command["request_id"],
                "work_id": command["work_id"],
                "data": "[MOCK RESPONSE] Hello, I'm a simulated response."
            }
            
        # For other commands, just return success
        return {
            "created": time.time(),
            "error": {"code": 0, "message": "Success"},
            "request_id": command["request_id"],
            "work_id": command["work_id"]
        }


async def create_and_test_command():
    """Create and test an inference command"""
    from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
    
    print("\n===== CREATING COMMAND USING NEUROCORTICAL BRIDGE =====")
    
    # Create a command using the actual method from NeurocorticalBridge
    command = NeurocorticalBridge.create_llm_inference_command(
        prompt="Hello, this is a test",
        stream=False
    )
    
    print("\n📝 COMMAND CREATED:")
    print(json.dumps(command, indent=2))
    
    # Verify push parameter
    push_value = command.get("data", {}).get("push")
    if push_value is False:
        print("✅ push parameter correctly set to False in created command")
    else:
        print(f"❌ push parameter not set correctly: {push_value}")
    
    # Test using mock transport
    transport = MockWiFiTransport()
    await transport.connect()
    
    print("\n===== SENDING COMMAND TO MOCK TRANSPORT =====")
    response = await transport.transmit(command)
    
    print("\n📥 MOCK RESPONSE:")
    print(json.dumps(response, indent=2))
    
    # Check if response indicates success
    if response.get("error", {}).get("code") == 0:
        print("✅ Command structure validated successfully")
    else:
        print(f"❌ Command validation failed: {response.get('error', {}).get('message')}")
    
    # Test also a manually created command
    print("\n===== TESTING MANUALLY CREATED COMMAND =====")
    manual_command = {
        "request_id": f"test_manual_{int(time.time())}",
        "work_id": "llm",
        "action": "inference",
        "data": {
            "prompt": "Test manual command",
            "stream": False,
            "push": False
        }
    }
    
    manual_response = await transport.transmit(manual_command)
    print("\n📥 MANUAL COMMAND RESPONSE:")
    print(json.dumps(manual_response, indent=2))
    
    # Clean up
    await transport.disconnect()


async def test_from_mind_method():
    """Test how the Mind.think method creates the command"""
    print("\n===== TESTING COMMAND CREATION FROM MIND CLASS =====")
    
    # Create a minimal version of the Mind.think method
    async def mock_mind_think(prompt, stream=False):
        # This replicates the logic in Mind.think
        think_command = {
            "request_id": f"think_{int(time.time())}",
            "work_id": "llm",
            "action": "inference",
            "data": {
                "prompt": prompt,
                "stream": stream
            }
        }
        
        print("📝 COMMAND CREATED BY MIND.THINK:")
        print(json.dumps(think_command, indent=2))
        
        # Check for push parameter
        if "push" not in think_command.get("data", {}):
            print("❌ push parameter not included in Mind.think command")
            
            # Fix by adding it
            think_command["data"]["push"] = False
            print("\n📝 FIXED COMMAND:")
            print(json.dumps(think_command, indent=2))
        
        # Test with mock transport
        transport = MockWiFiTransport()
        await transport.connect()
        response = await transport.transmit(think_command)
        await transport.disconnect()
        
        return response
    
    # Test the mock think method
    response = await mock_mind_think("Test from mock Mind.think")
    
    print("\n📥 RESPONSE FROM MOCK MIND.THINK:")
    print(json.dumps(response, indent=2))
    
    if response.get("error", {}).get("code") == 0:
        print("✅ Mind.think command structure validated successfully after fix")
    else:
        print(f"❌ Mind.think command validation failed: {response.get('error', {}).get('message')}")


async def main():
    """Main test function"""
    print("\n===== TESTING INFERENCE COMMAND STRUCTURE =====\n")
    
    try:
        # Test command creation directly from NeurocorticalBridge
        await create_and_test_command()
        
        # Test command creation from Mind.think method
        await test_from_mind_method()
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main()) 