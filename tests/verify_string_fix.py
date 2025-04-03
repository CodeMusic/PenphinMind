#!/usr/bin/env python3
"""
Verify String Fix
----------------
Tests the LLM inference with the push="true" parameter (as a string) against actual hardware.

To prepare:
1. Install paramiko: pip install paramiko
2. Ensure device is connected and powered on
3. Run this script
"""

import sys
import os
import json
import asyncio
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the SystemJournelingManager for logging
try:
    from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel
    journaling_manager = SystemJournelingManager(level=SystemJournelingLevel.DEBUG)
except ImportError as e:
    print(f"Error importing SystemJournelingManager: {e}")
    print("Continuing with basic logging...")
    journaling_manager = None

def log(message, level="INFO"):
    """Log messages even if journaling_manager isn't available"""
    if journaling_manager:
        if level == "DEBUG":
            journaling_manager.recordDebug(message)
        elif level == "ERROR":
            journaling_manager.recordError(message)
        else:
            journaling_manager.recordInfo(message)
    
    print(f"[{level}] {message}")

async def verify_hardware():
    """Verify the push="true" string fix with actual hardware"""
    try:
        print("\n===== STRING FIX VERIFICATION TEST =====")
        print("Testing if push=\"true\" as a string parameter fixes the LLM inference error")
        print("===========================================")
        
        # Try to import required modules
        try:
            # Try to import Mind - this may fail if paramiko is missing
            from Mind.mind import Mind
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            MIND_AVAILABLE = True
        except ImportError as e:
            if 'paramiko' in str(e):
                print(f"\n⚠️ WARNING: {e}")
                print("You need to install paramiko to test with hardware.")
                print("Install paramiko with: pip install paramiko\n")
                print("This test will only check the command structure.")
                from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
                MIND_AVAILABLE = False
            else:
                raise
        
        # STEP 1: Verify the command structure has push="true" as a string
        print("\n--- STEP 1: COMMAND STRUCTURE VERIFICATION ---")
        test_prompt = "Write a haiku about debugging"
        
        command = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=False
        )
        
        # Output the command for verification
        print("\nInference Command:")
        print(json.dumps(command, indent=2))
        
        # Verify push parameter is present and set to string "true"
        push_value = command["data"].get("push")
        if push_value == "true":
            print("✅ 'push' parameter is present and set to string 'true'")
            print(f"Type: {type(push_value).__name__}")
            
            # Check the serialized JSON as well
            serialized = json.dumps(command)
            print("\nJSON Serialization:")
            print(serialized)
            
            if '"push":"true"' in serialized.replace(" ", ""):
                print("✅ JSON contains 'push':'true' as string")
            else:
                print("❌ JSON does NOT contain 'push':'true' as string")
                print("This is unexpected - check serialization!")
        else:
            print(f"❌ 'push' parameter has unexpected value: {push_value}")
            print(f"Type: {type(push_value).__name__}")
            print("The string fix has not been correctly applied!")
            return
        
        # If paramiko is not available, stop here
        if not MIND_AVAILABLE:
            print("\n⚠️ Cannot continue with hardware test because paramiko is missing.")
            print("The command structure looks correct with push=\"true\" as a string.")
            print("Install paramiko and run the test again to verify with hardware.")
            return
        
        # STEP 2: Initialize Mind and connect to hardware
        print("\n--- STEP 2: CONNECTING TO HARDWARE ---")
        print("Initializing Mind and connecting to hardware...")
        
        # Initialize Mind with auto settings or default mind
        try:
            mind = Mind()  # Default should try auto-discovery
            await mind.initialize()
            print("✅ Mind initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Mind: {e}")
            print("The device may not be connected or powered on.")
            return
        
        # STEP 3: Test direct communication
        print("\n--- STEP 3: TESTING DIRECT COMMUNICATION ---")
        
        # Test basic ping
        print("Pinging system...")
        ping_result = await mind.ping_system()
        if ping_result and ping_result.get("status") == "ok":
            print("✅ Ping successful!")
        else:
            print(f"❌ Ping failed: {ping_result.get('message', 'Unknown error')}")
            print("Cannot continue testing without basic connectivity.")
            await mind.close()
            return
        
        # STEP 4: Test LLM inference with push="true"
        print("\n--- STEP 4: TESTING LLM INFERENCE WITH STRING 'TRUE' ---")
        print("Executing LLM inference with push=\"true\" as string...")
        
        response = await mind.neurocortical_bridge.execute("think", test_prompt)
        
        print("\n=== LLM INFERENCE RESPONSE ===")
        print(json.dumps(response, indent=2))
        print("===============================")
        
        if response.get("status") == "success":
            print("\n✅ SUCCESS: LLM inference worked with push=\"true\" as string!")
            print(f"Response text: {response.get('text', '')[:100]}...")
            
            # Test streaming
            print("\n--- STEP 5: TESTING STREAMING INFERENCE ---")
            print("Executing streaming inference...")
            
            chunks = []
            async def collect_chunk(chunk):
                chunks.append(chunk)
                print(".", end="", flush=True)
            
            streaming_response = await mind.neurocortical_bridge.execute(
                "think", 
                "Write a haiku about fixing bugs", 
                stream=True,
                stream_callback=collect_chunk
            )
            
            print("\n\n=== STREAMING INFERENCE RESPONSE ===")
            print(json.dumps(streaming_response, indent=2))
            print("====================================")
            
            if streaming_response.get("status") == "success":
                print("\n✅ SUCCESS: Streaming inference also worked!")
                print(f"Received {len(chunks)} chunks")
                
                # Combine chunks
                if chunks:
                    full_text = "".join([c.get("text", "") for c in chunks])
                    print(f"\nCombined text: {full_text[:150]}...")
            else:
                print(f"\n❌ Streaming inference failed: {streaming_response.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ LLM inference failed: {response.get('error', 'Unknown error')}")
            print("\nEven with push=\"true\" as string, the error persists.")
            print("This suggests the issue might be something else or the API expects a different format.")
        
        # Clean up
        await mind.close()
        
        print("\n===== STRING FIX VERIFICATION COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(verify_hardware()) 