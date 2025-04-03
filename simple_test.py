#!/usr/bin/env python
"""
Simple test script to connect to the PenphinMind device
"""

import asyncio
import json
import sys
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
from Mind.Subcortex.journaling import SystemJournelingManager

journaling_manager = SystemJournelingManager()

async def test_connection():
    """Test connection to the device"""
    print("\n===== TESTING CONNECTION =====")
    print("Initializing NeurocorticalBridge...")
    
    # Initialize with TCP transport
    result = await NeurocorticalBridge.initialize("tcp")
    
    if not result:
        print("❌ Failed to initialize transport")
        return False
    
    print("✅ Transport initialized")
    
    # Get hardware info
    print("\nGetting hardware info...")
    hw_info = await NeurocorticalBridge.get_hardware_info()
    
    if hw_info and hw_info.get("status") == "ok":
        print("✅ Hardware info retrieved successfully")
        print(f"Device: {hw_info.get('data', {}).get('model', 'Unknown')}")
        print(f"Firmware: {hw_info.get('data', {}).get('firmware', 'Unknown')}")
        print(f"Memory: {hw_info.get('data', {}).get('memory', 'Unknown')}")
    else:
        print("❌ Failed to get hardware info")
        print(f"Response: {hw_info}")
        return False
    
    # List available models
    print("\nListing available models...")
    models_result = await NeurocorticalBridge.execute_operation("list_models")
    
    if models_result and models_result.get("status") == "ok":
        print("✅ Models retrieved successfully")
        models = models_result.get("models", [])
        if models:
            print(f"Available models: {len(models)}")
            for model in models:
                print(f"  - {model.get('name')}")
        else:
            print("No models available")
    else:
        print("❌ Failed to list models")
        print(f"Response: {models_result}")
    
    return True

async def main():
    """Main entry point"""
    try:
        success = await test_connection()
        if success:
            print("\n✅ Connection test succeeded")
        else:
            print("\n❌ Connection test failed")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 