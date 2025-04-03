#!/usr/bin/env python3
"""
Verify Mind Work ID Handling Test
-------------------------------
Tests that the Mind class correctly stores and uses the work_id 
returned from LLM setup in subsequent inference commands.
"""

import sys
import os
import json
import asyncio
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Mind directly
from Mind.mind import Mind
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()
print(f"[TEST] SystemJournelingManager initialized")

async def main():
    """Test the work_id handling in Mind class"""
    print("\n===== MIND WORK ID TEST =====")
    
    # Create Mind instance
    try:
        # Initialize Mind
        print("\n1. Initializing Mind...")
        mind = Mind()
        
        # Connect to hardware
        print("\n2. Connecting to hardware...")
        await mind.connect()
        
        # Set a model (this should store the work_id internally)
        model_name = "qwen2.5-0.5b"
        print(f"\n3. Setting up model: {model_name}")
        setup_result = await mind.set_model(model_name)
        
        print("\nModel setup result:")
        print(json.dumps(setup_result, indent=2))
        
        # Check if work_id was stored
        print(f"\nStored work_id: {mind._current_llm_work_id}")
        
        if mind._current_llm_work_id:
            print("✅ Work ID was successfully stored")
        else:
            print("⚠️ No work_id was stored in Mind instance")
        
        # Test inference using the stored work_id
        print("\n4. Testing inference with stored work_id...")
        
        inference_result = await mind.llm_inference(
            prompt="Generate a short poem about coding.",
            stream=False
        )
        
        # Display inference result
        print("\nInference result:")
        print(inference_result)
        
        if inference_result:
            print("✅ LLM inference successful!")
        else:
            print("❌ LLM inference failed")
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        # Clean up resources
        if 'mind' in locals():
            try:
                await mind.cleanup()
            except Exception:
                pass

if __name__ == "__main__":
    asyncio.run(main()) 