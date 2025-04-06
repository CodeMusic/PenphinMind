#!/usr/bin/env python3
"""
Test script for LLM inference with enhanced debug logging.
This test verifies that:
1. The push parameter is correctly set to false
2. Debug logging properly shows the JSON sent and received
"""

import asyncio
import json
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel
from Mind.mind import Mind
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge

# Set up debug logging
journaling_manager = SystemJournelingManager(level=SystemJournelingLevel.DEBUG)
print(f"\n[TEST] Setting up with Debug logging - Level: {journaling_manager.currentLevel.name}")
print(f"[TEST] Log levels enabled: {' '.join([level.name for level in SystemJournelingLevel if level.value <= journaling_manager.currentLevel.value])}\n")

async def test_inference():
    """Test LLM inference with debug logging"""
    try:
        print("\n===== TESTING LLM INFERENCE WITH DEBUG LOGGING =====")
        
        # Initialize Mind
        mind = Mind()
        print("[TEST] Initializing Mind...")
        await mind.initialize()
        
        # Create the inference command directly to inspect it
        test_prompt = "Write a very short poem about debugging"
        print(f"[TEST] Created test prompt: '{test_prompt}'")
        
        # Create the inference command using NeurocorticalBridge's method
        inference_command = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            request_id="test_001",
            stream=False
        )
        
        # Print the command to verify push=false
        print("\n[TEST] GENERATED INFERENCE COMMAND:")
        print(json.dumps(inference_command, indent=2))
        
        # Check for push parameter
        push_value = inference_command.get("data", {}).get("push", None)
        print(f"[TEST] push parameter value: {push_value}")
        
        if push_value is False:
            print("[TEST] ✅ push parameter correctly set to false")
        else:
            print("[TEST] ❌ push parameter not properly set")
        
        # Execute a think operation (which uses inference)
        print("\n[TEST] Executing think operation...")
        result = await mind.execute_operation("think", {"prompt": test_prompt})
        
        # Print the result
        print("\n[TEST] RESULT STATUS:", result.get("status"))
        print("[TEST] RESPONSE TRUNCATED:")
        response = result.get("response", "")
        print(response[:200] + "..." if len(response) > 200 else response)
        
        # Cleanup
        await mind.cleanup()
        print("\n[TEST] Test completed successfully")
        
    except Exception as e:
        print(f"[TEST] Error during test: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_inference()) 