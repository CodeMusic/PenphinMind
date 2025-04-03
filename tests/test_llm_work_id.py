#!/usr/bin/env python3
"""
LLM Work ID Test
---------------
Tests that the LLM setup returns a specific work_id that must be used for subsequent inference commands.
This is important because the API requires the specific work_id returned from setup.
"""

import sys
import os
import json
import asyncio
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import only what we need
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel

# Set logging level to DEBUG for maximum visibility
journaling_manager = SystemJournelingManager(level=SystemJournelingLevel.DEBUG)
print(f"[TEST] 🧠 SystemJournelingManager initialized with level: {journaling_manager.currentLevel.name}")
print(f"[TEST] 🧠 Log levels enabled: {' '.join([level.name for level in SystemJournelingLevel if level.value <= journaling_manager.currentLevel.value])}")

async def main():
    """Test LLM setup and inference with correct work_id handling"""
    print("\n===== LLM WORK ID TEST =====")
    
    try:
        # Initialize the transport (required before we can send commands)
        print("\n1. Initializing transport...")
        init_result = await NeurocorticalBridge.initialize_system("tcp")
        if not init_result:
            print("❌ Failed to initialize transport, cannot continue")
            return
        
        print("\n✅ Transport initialized successfully")
        
        # Create LLM setup command
        model_name = "qwen2.5-0.5b"
        print(f"\n2. Setting up LLM with model: {model_name}")
        
        setup_command = NeurocorticalBridge.create_llm_setup_command(
            model_name=model_name,
            persona="You are a helpful assistant."
        )
        
        print("\n--- SETUP COMMAND ---")
        print(json.dumps(setup_command, indent=2))
        
        # Send setup command
        print("\nSending setup command...")
        setup_result = await NeurocorticalBridge._send_to_hardware(setup_command)
        
        print("\n--- SETUP RESPONSE ---")
        print(json.dumps(setup_result, indent=2))
        
        # Check if we got a successful response with work_id
        llm_work_id = None
        if isinstance(setup_result, dict) and "error" in setup_result:
            error = setup_result.get("error", {})
            if isinstance(error, dict) and error.get("code") == 0:
                # Success, extract work_id
                llm_work_id = setup_result.get("work_id", "llm")
                print(f"\n✅ LLM setup successful")
                print(f"📝 Captured work_id: {llm_work_id}")
            else:
                error_msg = error.get("message", "Unknown error")
                print(f"\n❌ LLM setup failed: {error_msg}")
                return
        else:
            print("\n❌ LLM setup failed: Unexpected response format")
            return
        
        # Test inference with the correct work_id
        print(f"\n3. Testing inference with work_id: {llm_work_id}")
        
        # For this test, directly create the command instead of using create_llm_inference_command
        # so we can explicitly set the work_id from setup
        inference_command = {
            "request_id": str(int(time.time())),
            "work_id": llm_work_id,  # Use the work_id from setup response
            "action": "inference",
            "object": "llm.utf-8",
            "data": "Write a very short haiku about neural networks."
        }
        
        print("\n--- INFERENCE COMMAND ---")
        print(json.dumps(inference_command, indent=2))
        
        # Send inference command
        print("\nSending inference command...")
        inference_result = await NeurocorticalBridge._send_to_hardware(inference_command)
        
        print("\n--- INFERENCE RESPONSE ---")
        print(json.dumps(inference_result, indent=2))
        
        # Check if inference succeeded
        if isinstance(inference_result, dict) and "error" in inference_result:
            error = inference_result.get("error", {})
            if isinstance(error, dict) and error.get("code") == 0:
                print("\n✅ Inference with correct work_id succeeded!")
                if "data" in inference_result:
                    data = inference_result.get("data", "")
                    print(f"Response: {data}")
            else:
                error_msg = error.get("message", "Unknown error")
                print(f"\n❌ Inference failed: {error_msg}")
        else:
            print("\n❌ Inference failed: Unexpected response format")
        
        # For comparison, test inference with generic "llm" work_id
        print("\n4. Testing inference with generic 'llm' work_id (for comparison)")
        
        generic_command = {
            "request_id": str(int(time.time())),
            "work_id": "llm",  # Using generic work_id instead of the one from setup
            "action": "inference",
            "object": "llm.utf-8",
            "data": "Write a very short haiku about machine learning."
        }
        
        print("\n--- GENERIC INFERENCE COMMAND ---")
        print(json.dumps(generic_command, indent=2))
        
        # Send generic inference command
        print("\nSending generic inference command...")
        generic_result = await NeurocorticalBridge._send_to_hardware(generic_command)
        
        print("\n--- GENERIC INFERENCE RESPONSE ---")
        print(json.dumps(generic_result, indent=2))
        
        # Check if generic inference succeeded
        if isinstance(generic_result, dict) and "error" in generic_result:
            error = generic_result.get("error", {})
            if isinstance(error, dict) and error.get("code") == 0:
                print("\n✅ Generic inference succeeded!")
                if "data" in generic_result:
                    data = generic_result.get("data", "")
                    print(f"Response: {data}")
            else:
                error_msg = error.get("message", "Unknown error")
                print(f"\n❌ Generic inference failed: {error_msg}")
        else:
            print("\n❌ Generic inference failed: Unexpected response format")
        
        # Summarize findings
        print("\n===== TEST SUMMARY =====")
        print(f"1. LLM Setup: {'✅ Success' if llm_work_id else '❌ Failed'}")
        if llm_work_id:
            print(f"   - work_id: {llm_work_id}")
        
        print(f"2. Inference with specific work_id: {'✅ Success' if inference_result.get('data') else '❌ Failed'}")
        
        print(f"3. Inference with generic work_id: {'✅ Success' if generic_result.get('data') else '❌ Failed'}")
        
        print("\n===== CONCLUSION =====")
        if llm_work_id and llm_work_id != "llm" and inference_result.get('data') and not generic_result.get('data'):
            print("✅ CONFIRMED: Must use specific work_id from setup response for inference")
        elif inference_result.get('data') and generic_result.get('data'):
            print("⚠️ Both specific and generic work_id worked")
        else:
            print("❓ Inconclusive test results, see details above")
        
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