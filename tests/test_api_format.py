#!/usr/bin/env python3
"""
API Format Test
--------------
Tests that the LLM inference commands match the exact API format 
as specified in the documentation.
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_api_format():
    """Test that our commands match the documented API format exactly"""
    print("\n===== API FORMAT TEST =====")
    
    try:
        # Import NeurocorticalBridge directly
        from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        
        # Test prompt
        test_prompt = "Write a short poem about debugging code"
        
        # Create non-streaming command 
        non_stream_command = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=False
        )
        
        # Create streaming command
        stream_command = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=True
        )
        
        # Output the commands for verification
        print("\nNon-Streaming Command:")
        print(json.dumps(non_stream_command, indent=2))
        
        print("\nStreaming Command:")
        print(json.dumps(stream_command, indent=2))
        
        # Define correct format according to API docs
        non_streaming_format = {
            "request_id": "4",
            "work_id": "llm.1003",
            "action": "inference",
            "object": "llm.utf-8",
            "data": "What's ur name?"
        }
        
        streaming_format = {
            "request_id": "4",
            "work_id": "llm.1003",
            "action": "inference",
            "object": "llm.utf-8.stream",
            "data": {
                "delta": "What's ur name?",
                "index": 0,
                "finish": True
            }
        }
        
        # Verify non-streaming command structure
        print("\n--- NON-STREAMING VERIFICATION ---")
        # Check data is a string
        if isinstance(non_stream_command.get("data"), str):
            print("✅ data is correctly a string")
        else:
            print(f"❌ data should be a string, got {type(non_stream_command.get('data')).__name__}")
        
        # Check object field
        if non_stream_command.get("object") == "llm.utf-8":
            print("✅ object field is correctly 'llm.utf-8'")
        else:
            print(f"❌ object field should be 'llm.utf-8', got {non_stream_command.get('object')}")
        
        # Check action
        if non_stream_command.get("action") == "inference":
            print("✅ action field is correctly 'inference'")
        else:
            print(f"❌ action field should be 'inference', got {non_stream_command.get('action')}")
        
        # Check work_id format (should be llm or llm.XXXX)
        if non_stream_command.get("work_id") and non_stream_command.get("work_id").startswith("llm"):
            print("✅ work_id format is correct")
        else:
            print(f"❌ work_id should start with 'llm', got {non_stream_command.get('work_id')}")
        
        # Verify streaming command structure
        print("\n--- STREAMING VERIFICATION ---")
        # Check data is a dict with correct fields
        data = stream_command.get("data")
        if isinstance(data, dict):
            print("✅ data is correctly a dict")
            
            # Check for required fields
            if "delta" in data:
                print("✅ data contains 'delta' field")
            else:
                print("❌ data missing 'delta' field")
                
            if "index" in data:
                print("✅ data contains 'index' field")
            else:
                print("❌ data missing 'index' field")
                
            if "finish" in data:
                print("✅ data contains 'finish' field")
                if isinstance(data["finish"], bool):
                    print("✅ 'finish' is correctly a boolean")
                else:
                    print(f"❌ 'finish' should be a boolean, got {type(data['finish']).__name__}")
            else:
                print("❌ data missing 'finish' field")
        else:
            print(f"❌ data should be a dict, got {type(data).__name__}")
        
        # Check object field
        if stream_command.get("object") == "llm.utf-8.stream":
            print("✅ object field is correctly 'llm.utf-8.stream'")
        else:
            print(f"❌ object field should be 'llm.utf-8.stream', got {stream_command.get('object')}")
            
        # Verify fields that should not be present
        print("\n--- VERIFYING ABSENT FIELDS ---")
        
        # Check non-streaming doesn't have a stream parameter
        if "stream" not in non_stream_command.get("data", {}) and not isinstance(non_stream_command.get("data"), dict):
            print("✅ Non-streaming command correctly does not have a 'stream' parameter")
        else:
            print("❌ Non-streaming command should not have a 'stream' parameter")
            
        # Check neither have a push parameter
        ns_data = non_stream_command.get("data", {})
        if not isinstance(ns_data, dict) or "push" not in ns_data:
            print("✅ Non-streaming command correctly does not have a 'push' parameter")
        else:
            print("❌ Non-streaming command should not have a 'push' parameter")
            
        s_data = stream_command.get("data", {})
        if "push" not in s_data:
            print("✅ Streaming command correctly does not have a 'push' parameter")
        else:
            print("❌ Streaming command should not have a 'push' parameter")
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_api_format() 