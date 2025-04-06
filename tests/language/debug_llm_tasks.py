#!/usr/bin/env python3
"""
Debug LLM Tasks Test
-------------------
Test script to debug LLM setup and inference problems by:
1. Viewing active LLM tasks
2. Testing LLM setup with debug logging
3. Testing inference commands with different formats
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
    """Run the LLM debug tests"""
    print("\n===== LLM DEBUG TESTS =====")
    
    try:
        # Initialize the transport (required before we can send commands)
        print("\n1. Initializing transport...")
        init_result = await NeurocorticalBridge.initialize_system("tcp")
        if not init_result:
            print("❌ Failed to initialize transport, cannot continue")
            return
        
        print("\n✅ Transport initialized successfully")
        
        # View active LLM tasks
        print("\n2. Checking active LLM tasks...")
        tasks_result = await NeurocorticalBridge.get_active_llm_tasks()
        
        if tasks_result.get("status") == "ok":
            llm_tasks = tasks_result.get("llm_tasks", [])
            if llm_tasks:
                print(f"Found {len(llm_tasks)} active LLM tasks:")
                for task in llm_tasks:
                    print(f"  - {task['name']} ({task['status']})")
            else:
                print("No active LLM tasks found.")
        
        # Test LLM setup
        print("\n3. Testing LLM setup...")
        setup_test_result = await NeurocorticalBridge.test_llm_setup()
        
        # If setup succeeded, test custom inference command with push parameter
        if setup_test_result.get("setup_success", False):
            print("\n4. Testing custom inference command with push parameter...")
            
            # Create a custom inference command
            custom_command = {
                "request_id": str(int(time.time())),
                "work_id": "llm",
                "action": "inference",
                "object": "llm.utf-8",
                "push": "true",  # IMPORTANT: Using string "true", not boolean True
                "data": "Write a very short haiku about debugging."
            }
            
            print("\n--- CUSTOM INFERENCE COMMAND ---")
            print(json.dumps(custom_command, indent=2))
            
            # Send the command
            print("\nSending custom inference command...")
            custom_result = await NeurocorticalBridge._send_to_hardware(custom_command)
            
            print("\n--- CUSTOM INFERENCE RESPONSE ---")
            print(json.dumps(custom_result, indent=2))
            
            # Check if it succeeded
            if isinstance(custom_result, dict) and "error" in custom_result:
                error = custom_result.get("error", {})
                if isinstance(error, dict) and error.get("code") == 0:
                    print("\n✅ Custom inference with push parameter succeeded!")
                    if "data" in custom_result:
                        data = custom_result.get("data", "")
                        print(f"Response: {data}")
                else:
                    error_msg = error.get("message", "Unknown error")
                    print(f"\n❌ Custom inference failed: {error_msg}")
            else:
                print("\n❌ Custom inference failed: Unexpected response format")
        
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