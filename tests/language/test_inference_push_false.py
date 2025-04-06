#!/usr/bin/env python3
"""
Direct test for the inference command with push=false parameter.
This test focuses specifically on LLM inference API behavior with the push parameter.
"""

import asyncio
import json
import traceback
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel


async def test_inference_direct():
    """Test direct LLM inference command with explicit push parameter"""
    print("\n===== DIRECT INFERENCE COMMAND TEST WITH PUSH=FALSE =====\n")
    
    # Set up detailed logging
    journaling_manager = SystemJournelingManager(level=SystemJournelingLevel.DEBUG)
    print(f"Logging level: {journaling_manager.currentLevel.name}")
    
    try:
        # Import transport layer directly
        from Mind.Subcortex.transport_layer import WiFiTransport, get_transport
        from Mind.mind_config import get_mind_by_id, get_default_mind_id
        
        # Get default mind configuration
        mind_id = get_default_mind_id()
        mind_config = get_mind_by_id(mind_id)
        print(f"Using mind: {mind_id}")
        
        # Get connection settings
        connection = mind_config.get("connection", {})
        ip = connection.get("ip", "auto")
        port = connection.get("port", "auto")
        print(f"Connection settings: IP={ip}, Port={port}")
        
        # Create transport with these settings
        transport = WiFiTransport(ip=ip, port=port)
        print(f"Created transport: {transport}")
        
        # Connect to the device
        print("\nConnecting to device...")
        connected = await transport.connect()
        if not connected:
            print("❌ Failed to connect to device!")
            return
        
        print("✅ Connected to device successfully")
        
        # Create a basic inference command with explicit push=false
        inference_command = {
            "request_id": "test_001",
            "work_id": "llm",
            "action": "inference",
            "data": {
                "prompt": "Say hello briefly",
                "stream": False,
                "push": False  # Explicit push=false
            }
        }
        
        # Log the command
        print("\n📤 SENDING COMMAND:")
        print(json.dumps(inference_command, indent=2))
        
        # Send the command
        print("\nSending inference command...")
        response = await transport.transmit(inference_command)
        
        # Log the response
        print("\n📥 RAW RESPONSE:")
        print(json.dumps(response, indent=2) if response else "None")
        
        # Analyze the response 
        if isinstance(response, dict):
            # Check for API error format
            if "error" in response:
                error = response.get("error", {})
                if isinstance(error, dict):
                    error_code = error.get("code", -1)
                    if error_code == 0:
                        # API success (code 0)
                        data = response.get("data", None)
                        print("\n✅ INFERENCE SUCCESSFUL")
                        print(f"Response data: {data}")
                    else:
                        # API error
                        error_msg = error.get("message", "Unknown error")
                        print(f"\n❌ API ERROR: {error_msg}")
                        print(f"Error code: {error_code}")
                else:
                    print(f"\n❌ Invalid error format: {error}")
            else:
                print(f"\n❌ Response missing error field: {response}")
        else:
            print(f"\n❌ Invalid response type: {type(response)}")
        
        # Create a version WITHOUT push parameter for comparison
        inference_command_no_push = {
            "request_id": "test_002",
            "work_id": "llm",
            "action": "inference",
            "data": {
                "prompt": "Say hello briefly",
                "stream": False
                # No push parameter
            }
        }
        
        # Log the command
        print("\n📤 SENDING COMMAND WITHOUT PUSH PARAMETER:")
        print(json.dumps(inference_command_no_push, indent=2))
        
        # Send the command
        print("\nSending inference command without push parameter...")
        response2 = await transport.transmit(inference_command_no_push)
        
        # Log the response
        print("\n📥 RAW RESPONSE:")
        print(json.dumps(response2, indent=2) if response2 else "None")
        
        # Disconnect
        print("\nDisconnecting from device...")
        await transport.disconnect()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_inference_direct()) 