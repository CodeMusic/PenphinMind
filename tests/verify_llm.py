#!/usr/bin/env python3
"""
Verify LLM Communication
-----------------------
Tests the end-to-end LLM communication to verify that our API calls are working correctly
after removing the undocumented "push" parameter.
"""

import sys
import os
import json
import asyncio
import time
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the SystemJournelingManager for logging
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel
# Set up debug logging
journaling_manager = SystemJournelingManager(level=SystemJournelingLevel.DEBUG)

async def test_llm_communication():
    """
    Test LLM communication and verify proper response handling
    """
    try:
        # Dynamically import to handle potential import errors gracefully
        try:
            from Mind.mind import Mind
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        except ImportError as e:
            if 'paramiko' in str(e):
                print(f"\n⚠️ WARNING: {e}")
                print("This test will continue with direct API testing without SSH functionality.")
                print("Install paramiko with: pip install paramiko\n")
                from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            else:
                raise

        # Test phase 1: Command generation
        print("\n===== PHASE 1: COMMAND GENERATION =====")
        test_prompt = "Write a haiku about debugging code"
        
        # Normal mode
        normal_command = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=False
        )
        print("\nNormal Command:")
        print(json.dumps(normal_command, indent=2))
        
        # Streaming mode
        stream_command = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=True
        )
        print("\nStreaming Command:")
        print(json.dumps(stream_command, indent=2))
        
        # Check for push parameter (should not be present)
        if "push" in normal_command["data"] or "push" in stream_command["data"]:
            print("❌ ERROR: 'push' parameter still present in command data!")
        else:
            print("✅ SUCCESS: No 'push' parameter in command data")

        # Test phase 2: Full execution (if Mind is available)
        try:
            # Initialize the cognitive architecture
            mind = Mind()
            await mind.initialize()
            
            print("\n===== PHASE 2: LLM EXECUTION =====")
            
            # Check connection
            is_connected = await mind.synaptic_pathways.is_connected()
            print(f"Connection status: {'✅ Connected' if is_connected else '❌ Not connected'}")
            
            if is_connected:
                # Get hardware info
                hw_info = await mind.synaptic_pathways.get_hardware_info()
                print(f"Hardware info: {hw_info}")
                
                # Test normal mode
                print("\nTesting normal mode inference...")
                start_time = time.time()
                response = await mind.neurocortical_bridge.execute("think", test_prompt)
                elapsed = time.time() - start_time
                
                print(f"Response received in {elapsed:.2f} seconds")
                print(f"Status: {response.get('status', 'Unknown')}")
                if response.get('status') == "success":
                    print("✅ SUCCESS: Normal inference worked!")
                    print(f"Response: {response.get('text', '')[:100]}...")
                else:
                    print(f"❌ ERROR: {response.get('error', 'Unknown error')}")
                
                # Test streaming mode
                print("\nTesting streaming mode inference...")
                chunks = []
                
                async def stream_callback(chunk):
                    chunks.append(chunk)
                    print(".", end="", flush=True)
                
                start_time = time.time()
                stream_response = await mind.neurocortical_bridge.execute(
                    "think", 
                    test_prompt,
                    stream=True,
                    stream_callback=stream_callback
                )
                elapsed = time.time() - start_time
                
                print(f"\nStreaming response received in {elapsed:.2f} seconds")
                print(f"Received {len(chunks)} chunks")
                if stream_response.get('status') == "success":
                    print("✅ SUCCESS: Streaming inference worked!")
                    complete_response = ''.join([c.get('text', '') for c in chunks])
                    print(f"Complete response: {complete_response[:100]}...")
                else:
                    print(f"❌ ERROR: {stream_response.get('error', 'Unknown error')}")
            
            # Cleanup
            await mind.close()
            
        except NameError:
            print("\n⚠️ Mind class not available - skipping execution test")
        except Exception as e:
            print(f"\n❌ ERROR during execution: {e}")
            import traceback
            print(traceback.format_exc())
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_llm_communication()) 