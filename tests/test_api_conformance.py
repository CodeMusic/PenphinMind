#!/usr/bin/env python3
"""
API Conformance Test Script
Tests that the LLM inference commands match the documented API structure
with the required push:true parameter.
"""

import sys
import os
import json
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api_conformance():
    """Test that our commands conform to the documented API structure"""
    print("\n===== API CONFORMANCE TEST =====\n")
    
    try:
        # Import the NeurocorticalBridge directly
        from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        
        # Create a test prompt
        test_prompt = "Hello, how are you today?"
        
        # Generate the command using our method
        command = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=False
        )
        
        # Print the command for inspection
        print("Generated Inference Command:")
        print(json.dumps(command, indent=2))
        print()
        
        # Check API conformance by comparing with documented structure
        # Based on the device behavior, the correct structure is:
        documented_structure = {
            "request_id": "string value",
            "work_id": "llm.xxxx",
            "action": "inference",
            "object": "optional",
            "data": {
                "prompt": "string value",
                "stream": True or False,
                "push": True  # push parameter seems to be required and must be true
            }
        }
        
        # Check for documented fields
        print("API Conformance Analysis:")
        
        # Check top-level fields
        for field in ["request_id", "work_id", "action"]:
            if field in command:
                print(f"✅ Found required field: {field}")
            else:
                print(f"❌ Missing required field: {field}")
        
        # Check data field
        if "data" in command and isinstance(command["data"], dict):
            print("✅ Found data field")
            
            # Check data sub-fields
            if "prompt" in command["data"]:
                print("✅ Found prompt in data")
            else:
                print("❌ Missing prompt in data")
            
            if "stream" in command["data"]:
                print("✅ Found stream in data")
            else:
                print("❌ Missing stream in data")
            
            # Check for push parameter
            if "push" in command["data"]:
                if command["data"]["push"] is True:
                    print("✅ Found push=true in data")
                else:
                    print("❌ push parameter is present but not set to true")
            else:
                print("❌ Missing push parameter in data")
        else:
            print("❌ Missing or invalid data field")
        
        # Check if creating a streaming command works
        streaming_command = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=True
        )
        
        # Verify streaming parameter
        if streaming_command["data"]["stream"] == True:
            print("✅ Streaming parameter correctly set to True")
        else:
            print("❌ Streaming parameter not set correctly")
        
        # Verify push parameter in streaming command
        if "push" in streaming_command["data"] and streaming_command["data"]["push"] is True:
            print("✅ Push parameter correctly set to True in streaming command")
        else:
            print("❌ Push parameter not set correctly in streaming command")
        
        print("\nNOTE: Based on the error messages, it appears the device requires")
        print("      the push parameter to be present and set to TRUE, even though")
        print("      it may not be mentioned in the official documentation.")
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_api_conformance() 