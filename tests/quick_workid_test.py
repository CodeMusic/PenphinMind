#!/usr/bin/env python3
"""
Quick Work ID Test
----------------
A simple test script that directly demonstrates the importance of using
the correct work_id from LLM setup in subsequent inference commands.
"""

import sys
import os
import json
import asyncio
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import only what we need directly
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()
print(f"[TEST] SystemJournelingManager initialized")

async def main():
    """Test the work_id directly"""
    print("\n===== QUICK WORK ID TEST =====")
    
    try:
        # Initialize the transport
        print("\n1. Initializing transport...")
        await NeurocorticalBridge.initialize_system("tcp")
        
        # Create and send LLM setup command directly
        model_name = "qwen2.5-0.5b"
        print(f"\n2. Setting up LLM with model: {model_name}")
        
        setup_command = {
            "request_id": str(int(time.time())),
            "work_id": "llm",
            "action": "setup",
            "model": model_name,
            "response_format": "llm.utf-8",
            "input": "llm.utf-8",
            "enoutput": True,
            "enkws": False,
            "max_token_len": 127,
            "prompt": "You are a helpful assistant."
        }
        
        # Send the setup command
        print("Sending setup command...")
        setup_result = await NeurocorticalBridge._send_to_hardware(setup_command)
        
        # Debug output the result
        print("\nSetup Response:")
        print(json.dumps(setup_result, indent=2))
        
        # Extract the work_id from the setup response
        specific_work_id = None
        if isinstance(setup_result, dict) and "work_id" in setup_result:
            specific_work_id = setup_result["work_id"]
            print(f"\n✅ Found work_id in response: {specific_work_id}")
        else:
            print("\n⚠️ No work_id found in response, using default 'llm'")
            specific_work_id = "llm"
        
        # Pause to ensure setup is complete
        print("\nWaiting a moment for setup to complete...")
        await asyncio.sleep(1)
        
        # Now send an inference command with the specific work_id
        print(f"\n3. Testing inference with work_id: {specific_work_id}")
        
        inference_command = {
            "request_id": str(int(time.time())),
            "work_id": specific_work_id,  # Use the extracted work_id
            "action": "inference",
            "object": "llm.utf-8",
            "data": "Write a short poem about debugging."
        }
        
        # Send the inference command
        print("Sending inference command...")
        inference_result = await NeurocorticalBridge._send_to_hardware(inference_command)
        
        # Debug output the result
        print("\nInference Response:")
        print(json.dumps(inference_result, indent=2))
        
        # Check if inference succeeded
        if isinstance(inference_result, dict) and "error" in inference_result:
            error = inference_result.get("error", {})
            if isinstance(error, dict) and error.get("code") == 0:
                print("\n✅ Inference succeeded!")
                if "data" in inference_result:
                    data = inference_result.get("data", "")
                    print(f"Response: {data}")
            else:
                error_msg = error.get("message", "Unknown error")
                print(f"\n❌ Inference failed with error: {error_msg}")
        else:
            print("\n❌ Unexpected inference response format")
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        # Clean up resources
        try:
            await NeurocorticalBridge.cleanup()
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main()) 