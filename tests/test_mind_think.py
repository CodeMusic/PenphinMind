#!/usr/bin/env python3
"""
Test script for Mind.think method to verify it includes push=false in commands
"""

import asyncio
import json
import sys
import os
import time
import traceback

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override the transport to capture the command without sending
class CommandCaptureTransport:
    """Transport that captures commands but doesn't send them"""
    
    def __init__(self):
        self.last_command = None
        
    async def connect(self):
        return True
        
    async def disconnect(self):
        pass
        
    async def transmit(self, command):
        """Capture the command and return mock success"""
        self.last_command = command
        print(f"📝 CAPTURED COMMAND:")
        print(json.dumps(command, indent=2))
        
        # Check for push parameter
        push_value = None
        if isinstance(command, dict) and "data" in command and isinstance(command["data"], dict):
            push_value = command["data"].get("push")
            
            if push_value is False:
                print("✅ push parameter correctly set to False")
            elif push_value is None:
                print("❌ push parameter missing")
            else:
                print(f"❌ push parameter has unexpected value: {push_value}")
        
        # Return mock success response
        return {
            "created": time.time(),
            "error": {"code": 0, "message": "Success"},
            "request_id": command.get("request_id", "unknown"),
            "work_id": command.get("work_id", "unknown"),
            "data": "[MOCK RESPONSE] This is a simulated response."
        }


async def test_mind_think():
    """Test the Mind.think method to verify it includes push=false"""
    print("\n===== TESTING MIND.THINK METHOD =====\n")
    
    try:
        # Import Mind and replace transport
        from Mind.mind import Mind
        from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        
        # Create command capture transport
        capture_transport = CommandCaptureTransport()
        
        # Backup original _send_to_hardware method
        original_send = NeurocorticalBridge._send_to_hardware
        
        # Override the send method to use our capture transport
        async def mock_send(command, stream_callback=None):
            return await capture_transport.transmit(command)
            
        # Patch the method
        NeurocorticalBridge._send_to_hardware = mock_send
        
        # Initialize a Mind instance
        print("Creating Mind instance...")
        mind = Mind(name="TestMind")
        
        # Call the think method
        print("\nCalling mind.think...")
        result = await mind.think("This is a test prompt")
        
        print("\n📥 RESULT FROM MIND.THINK:")
        print(json.dumps(result, indent=2))
        
        # Restore original method
        NeurocorticalBridge._send_to_hardware = original_send
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(traceback.format_exc())
        
        # Ensure we restore the original method
        if 'original_send' in locals() and 'NeurocorticalBridge' in locals():
            NeurocorticalBridge._send_to_hardware = original_send


if __name__ == "__main__":
    asyncio.run(test_mind_think()) 