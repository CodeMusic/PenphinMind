#!/usr/bin/env python3
"""
Simple test script to verify LLM inference command structure.
Only tests the command creation without executing it.
"""

import json
import time

def create_llm_inference_command(prompt, request_id=None, stream=False, work_id=None):
    """
    Create an LLM inference command in exact API format
    
    Args:
        prompt: The prompt to send to the LLM
        request_id: Optional request ID
        stream: Whether to stream the response
        work_id: Optional work_id override
        
    Returns:
        dict: Command dictionary formatted per API spec
    """
    if not request_id:
        request_id = f"{int(time.time())}"
        
    print(f"[DEBUG] Creating inference command with stream={stream}")
    print(f"[DEBUG] Prompt (first 100 chars): {prompt[:100]}...")
    
    command = {
        "request_id": request_id,
        "work_id": work_id or "llm",
        "action": "inference",
        "data": {
            "prompt": prompt,
            "stream": stream,
            "push": False  # Explicitly setting push to false
        }
    }
    
    print(f"[DEBUG] Command JSON: {json.dumps(command, indent=2)}")
    
    return command

def main():
    """Test LLM inference command creation"""
    print("\n===== TESTING LLM INFERENCE COMMAND STRUCTURE =====")
    
    # Create test prompt
    test_prompt = "Write a very short poem about debugging"
    print(f"Using test prompt: '{test_prompt}'")
    
    # Create command for normal mode
    print("\n----- NORMAL MODE -----")
    normal_command = create_llm_inference_command(
        prompt=test_prompt,
        request_id="test_001",
        stream=False
    )
    
    # Verify push parameter
    push_value = normal_command.get("data", {}).get("push", None)
    print(f"push parameter value: {push_value}")
    
    if push_value is False:
        print("✅ push parameter correctly set to false")
    else:
        print("❌ push parameter not properly set")
        
    # Create command for streaming mode
    print("\n----- STREAMING MODE -----")
    stream_command = create_llm_inference_command(
        prompt=test_prompt,
        request_id="test_002",
        stream=True
    )
    
    # Verify push parameter
    push_value = stream_command.get("data", {}).get("push", None)
    print(f"push parameter value: {push_value}")
    
    if push_value is False:
        print("✅ push parameter correctly set to false")
    else:
        print("❌ push parameter not properly set")
    
    print("\nTest completed successfully")

if __name__ == "__main__":
    main() 