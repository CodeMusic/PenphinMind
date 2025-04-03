#!/usr/bin/env python3
"""
Test Push String Parameter
-------------------------
Tests if setting push="true" as a string in the inference command 
resolves the "inference data push false" error.
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_push_parameter():
    """Test that push="true" as a string is included in inference command"""
    print("\n===== TESTING PUSH STRING PARAMETER =====")
    
    try:
        # Import NeurocorticalBridge directly
        from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        
        # Test prompt
        test_prompt = "Write a short poem about debugging"
        
        # Create inference command 
        command = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=False
        )
        
        # Output the command for verification
        print("\nInference Command:")
        print(json.dumps(command, indent=2))
        
        # Verify push parameter is present and set to string "true"
        if "push" in command["data"]:
            push_value = command["data"]["push"]
            if push_value == "true":
                print("\n✅ SUCCESS: 'push' parameter is present and set to string 'true'")
                print(f"Type: {type(push_value).__name__}")
            elif push_value is True:  # boolean True
                print("\n❌ ERROR: 'push' parameter is set to boolean True, not string 'true'")
                print(f"Type: {type(push_value).__name__}")
            else:
                print(f"\n❌ ERROR: 'push' parameter has unexpected value: {push_value}")
                print(f"Type: {type(push_value).__name__}")
        else:
            print("\n❌ ERROR: 'push' parameter is missing from the command")
        
        # Show serialized JSON to verify string format
        print("\nJSON Serialization:")
        serialized = json.dumps(command)
        print(serialized)
        
        # Check for the literal string "push":"true" in the serialized JSON
        if '"push":"true"' in serialized.replace(" ", ""):
            print("\n✅ JSON contains 'push':'true' as string")
        else:
            print("\n❌ JSON does NOT contain 'push':'true' as string")
            
            # Check for alternate formats
            if '"push":true' in serialized.replace(" ", ""):
                print("Found 'push':true as boolean instead")
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_push_parameter() 