#!/usr/bin/env python3
"""
Debug test script for chat functionality to diagnose push parameter issue.
This script creates a simplified chat interface to test direct LLM calls with debug output.
"""

import asyncio
import json
import sys
import os
import time
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel

# Initialize journaling system with DEBUG level
journaling_manager = SystemJournelingManager(level=SystemJournelingLevel.DEBUG)
print(f"🧠 Log level: {journaling_manager.currentLevel.name}")
print(f"🧠 Enabled levels: {', '.join([level.name for level in SystemJournelingLevel if level.value <= journaling_manager.currentLevel.value])}")

async def debug_chat():
    """Run a simplified chat interface for debugging"""
    try:
        print("\n===== DEBUG CHAT INTERFACE =====\n")
        
        # Import Mind directly
        from Mind.mind import Mind
        
        # Create Mind instance with default mind_id
        print("📋 Creating Mind instance...")
        mind = Mind()
        
        # Initialize the mind
        print("\n📋 Initializing Mind...")
        result = await mind.initialize()
        if not result:
            print("❌ Failed to initialize Mind!")
            return
        
        print("✅ Mind initialized successfully")
        
        # Ping the system to check connection
        print("\n📋 Checking connection with ping...")
        ping_result = await mind.ping_system()
        print(f"📊 Ping result: {ping_result.get('status', 'unknown')}")
        
        if ping_result.get("status") != "ok":
            print("❌ Failed to ping system! The connection may not be working.")
            print(f"Error: {ping_result.get('message', 'Unknown error')}")
        else:
            print("✅ Connection established successfully")
        
        # Get hardware info 
        print("\n📋 Getting hardware info...")
        hw_result = await mind.get_hardware_info()
        if hw_result.get("status") == "ok":
            print("✅ Hardware info retrieved")
            print(f"Hardware: {hw_result.get('hardware_info')}")
        else:
            print("⚠️ Couldn't get hardware info")
            
        # Chat loop
        print("\n===== CHAT STARTED =====")
        print("Type 'exit' to quit, 'debug' to toggle debug info")
        
        show_debug = True
        
        while True:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == "exit":
                print("Exiting chat...")
                break
                
            if user_input.lower() == "debug":
                show_debug = not show_debug
                print(f"Debug output {'enabled' if show_debug else 'disabled'}")
                continue
            
            # Print system response using think method
            print("\n🤖 System: ", end="", flush=True)
            start_time = time.time()
            
            # Call the think method
            response = await mind.think(user_input)
            
            # Check response
            if response.get("status") == "ok":
                print(response.get("response", ""))
            else:
                print(f"⚠️ Error: {response.get('message', 'Unknown error')}")
                
            # Show timing info
            elapsed = time.time() - start_time
            if show_debug:
                print(f"\n📊 Response time: {elapsed:.2f} seconds")
                
                # If there was an error, print detailed debug info
                if response.get("status") != "ok":
                    print("\n===== DEBUG INFORMATION =====")
                    print("Raw response:")
                    print(json.dumps(response.get("raw_response", {}), indent=2))
                    print("=============================")
        
        # Clean up
        print("\n📋 Cleaning up...")
        await mind.cleanup()
        print("✅ Resources cleaned up")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(debug_chat()) 