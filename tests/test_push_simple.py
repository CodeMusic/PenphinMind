#!/usr/bin/env python3
"""
Simple Push Parameter Test
-------------------------
Tests that the LLM inference command includes push=true
without trying to connect to hardware.
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_push_parameter():
    """Test that push=true is included in inference command"""
    print("\n===== TESTING PUSH=TRUE PARAMETER =====")
    
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
        
        # Verify push parameter is present and set to true
        if "push" in command["data"]:
            if command["data"]["push"] is True:
                print("\n✅ SUCCESS: 'push' parameter is present and set to TRUE")
            else:
                print(f"\n❌ ERROR: 'push' parameter is present but has value: {command['data']['push']}")
        else:
            print("\n❌ ERROR: 'push' parameter is missing from the command")
        
        # Compare with previous command structure that caused error
        print("\nPrevious failing command had:")
        print("  - push parameter missing or set to false")
        print("  - received error: 'inference data push false'")
        print("\nWith this change:")
        print("  - push parameter is explicitly set to TRUE")
        print("  - error should be resolved if the device requires push=true")
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_push_parameter() 