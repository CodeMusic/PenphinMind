#!/usr/bin/env python3
"""
Direct test for NeurocorticalBridge.create_llm_inference_command
This test verifies the push=false parameter is included without importing the full Mind class
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_inference_command():
    """Test the inference command creation directly"""
    print("\n===== TESTING COMMAND CREATION =====\n")
    
    try:
        # Import only NeurocorticalBridge
        from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        
        # Test command creation
        command = NeurocorticalBridge.create_llm_inference_command(
            prompt="This is a test prompt",
            stream=False
        )
        
        print("📝 CREATED COMMAND:")
        print(json.dumps(command, indent=2))
        
        # Check for push parameter
        if "data" in command and isinstance(command["data"], dict):
            push_value = command["data"].get("push")
            
            if push_value is False:
                print("\n✅ push parameter correctly set to False")
            elif push_value is None:
                print("\n❌ push parameter missing")
            else:
                print(f"\n❌ push parameter has unexpected value: {push_value}")
        else:
            print("\n❌ Invalid command structure: data field not found")
            
        # Print summary
        print("\n===== TEST SUMMARY =====")
        print(f"Command has push parameter: {'Yes' if push_value is not None else 'No'}")
        print(f"Push parameter value: {push_value}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_inference_command() 