#!/usr/bin/env python3
"""
LLM Command Format Test
-----------------------
Tests that the LLM inference command format is correct for both streaming and non-streaming modes.
This test focuses only on command structure without requiring hardware connectivity.
"""

import sys
import os
import json
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import only the system_journaling_manager directly
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()
print(f"[TEST] 🧠 SystemJournelingManager initialized with level: {journaling_manager.currentLevel.name}")

def test_command_formats():
    """
    Test the LLM inference command formats without requiring hardware connectivity
    This isolates our testing to just the command creation logic
    """
    print("\n===== COMMAND FORMAT TEST =====")
    
    # Import NeurocorticalBridge directly without importing Mind
    try:
        from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        print("✅ Successfully imported NeurocorticalBridge")
    except ImportError as e:
        print(f"❌ Error importing NeurocorticalBridge: {e}")
        return
    
    test_prompt = "Test prompt for LLM inference command creation"
    
    # Test non-streaming command format
    print("\n----- Non-Streaming Command Format -----")
    non_streaming_cmd = NeurocorticalBridge.create_llm_inference_command(
        prompt=test_prompt,
        stream=False
    )
    
    # Verify non-streaming format
    print(f"Command structure: {json.dumps(non_streaming_cmd, indent=2)}")
    
    if isinstance(non_streaming_cmd, dict):
        print("\nVerifying non-streaming command structure:")
        
        # Check required fields
        required_fields = ["request_id", "work_id", "action", "object", "data"]
        for field in required_fields:
            if field in non_streaming_cmd:
                print(f"✅ Field '{field}' is present")
            else:
                print(f"❌ Missing required field: '{field}'")
        
        # Check specific field values
        if non_streaming_cmd.get("work_id") == "llm":
            print("✅ work_id is 'llm'")
        else:
            print(f"❌ work_id should be 'llm', got: {non_streaming_cmd.get('work_id')}")
            
        if non_streaming_cmd.get("action") == "inference":
            print("✅ action is 'inference'")
        else:
            print(f"❌ action should be 'inference', got: {non_streaming_cmd.get('action')}")
            
        if non_streaming_cmd.get("object") == "llm.utf-8":
            print("✅ object is 'llm.utf-8'")
        else:
            print(f"❌ object should be 'llm.utf-8', got: {non_streaming_cmd.get('object')}")
        
        # Check data format for non-streaming mode
        data = non_streaming_cmd.get("data")
        if isinstance(data, str):
            print(f"✅ data is a string: '{data[:30]}...'")
        else:
            print(f"❌ data should be a string, got: {type(data)}")
    else:
        print(f"❌ Command is not a dictionary: {type(non_streaming_cmd)}")
    
    # Test streaming command format
    print("\n----- Streaming Command Format -----")
    streaming_cmd = NeurocorticalBridge.create_llm_inference_command(
        prompt=test_prompt,
        stream=True
    )
    
    # Verify streaming format
    print(f"Command structure: {json.dumps(streaming_cmd, indent=2)}")
    
    if isinstance(streaming_cmd, dict):
        print("\nVerifying streaming command structure:")
        
        # Check required fields
        required_fields = ["request_id", "work_id", "action", "object", "data"]
        for field in required_fields:
            if field in streaming_cmd:
                print(f"✅ Field '{field}' is present")
            else:
                print(f"❌ Missing required field: '{field}'")
        
        # Check specific field values
        if streaming_cmd.get("object") == "llm.utf-8.stream":
            print("✅ object is 'llm.utf-8.stream'")
        else:
            print(f"❌ object should be 'llm.utf-8.stream', got: {streaming_cmd.get('object')}")
        
        # Check data format for streaming mode
        data = streaming_cmd.get("data")
        if isinstance(data, dict):
            print("✅ data is a dictionary")
            
            # Check streaming-specific fields
            streaming_fields = ["delta", "index", "finish"]
            for field in streaming_fields:
                if field in data:
                    print(f"✅ data.{field} is present")
                else:
                    print(f"❌ Missing required streaming field: 'data.{field}'")
        else:
            print(f"❌ data should be a dictionary, got: {type(data)}")
    else:
        print(f"❌ Command is not a dictionary: {type(streaming_cmd)}")
    
    print("\n===== TEST SUMMARY =====")
    non_streaming_ok = isinstance(non_streaming_cmd, dict) and isinstance(non_streaming_cmd.get("data"), str)
    streaming_ok = isinstance(streaming_cmd, dict) and isinstance(streaming_cmd.get("data"), dict)
    
    print(f"Non-Streaming Command Format: {'✅ OK' if non_streaming_ok else '❌ Error'}")
    print(f"Streaming Command Format: {'✅ OK' if streaming_ok else '❌ Error'}")
    
    print("\n===== TEST COMPLETE =====")

if __name__ == "__main__":
    test_command_formats() 