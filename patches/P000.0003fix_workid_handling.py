#!/usr/bin/env python3
"""
Fix Work ID Handling
------------------
A script to directly patch the work_id handling in the code
without requiring the full Mind setup.
"""

import os
import sys
import json
import asyncio
import time
from pathlib import Path

async def test_workid_directly():
    """Test the work_id handling directly without depending on Mind class"""
    print("\n===== DIRECT WORK ID TEST =====")
    
    # First, make sure our patches directory is created
    patch_dir = Path(__file__).parent
    patch_dir.mkdir(exist_ok=True)
    
    # Import NeurocorticalBridge (may fail due to indentation)
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        print("✅ Successfully imported NeurocorticalBridge")
    except IndentationError:
        print("❌ Indentation error in NeurocorticalBridge")
        # Try to fix the indentation
        try:
            # Apply indentation fix
            bridge_file = Path(__file__).parent.parent / "Mind" / "Subcortex" / "neurocortical_bridge.py"
            with open(bridge_file, 'r') as f:
                content = f.read()
            
            # Fix set_model method indentation
            content = content.replace(
                "else:\n                # API returned an error\n                error_message = error.get(\"message\", \"Unknown error\")\n            return {",
                "else:\n                # API returned an error\n                error_message = error.get(\"message\", \"Unknown error\")\n                return {"
            )
            
            # Write fixed content back
            with open(bridge_file, 'w') as f:
                f.write(content)
            
            print("✅ Applied indentation fix, reimporting...")
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        except Exception as e:
            print(f"❌ Failed to fix indentation: {e}")
            return
    
    # Create a direct test to verify work_id handling
    # 1. Create a patch to modify create_llm_inference_command
    bridge_patch = """
# Add work_id parameter to create_llm_inference_command
def patched_create_llm_inference_command(prompt, request_id=None, stream=False, work_id=None):
    # Get a unique request ID if not provided
    if request_id is None:
        request_id = str(int(time.time()))
    
    # Use provided work_id or default to "llm"
    if work_id is None:
        work_id = "llm"
    
    print(f"Creating inference command with work_id: {work_id}")
    
    if stream:
        # Streaming format
        return {
            "request_id": request_id,
            "work_id": work_id,  # Use the specific work_id
            "action": "inference",
            "object": "llm.utf-8.stream",
            "data": {
                "delta": prompt,
                "index": 0,
                "finish": True
            }
        }
    else:
        # Non-streaming format
        return {
            "request_id": request_id,
            "work_id": work_id,  # Use the specific work_id
            "action": "inference",
            "object": "llm.utf-8",
            "data": prompt
        }
"""
    
    # Save the patch
    patch_file = patch_dir / "bridge_patch.py"
    with open(patch_file, 'w') as f:
        f.write(bridge_patch)
    
    print(f"✅ Created patch file: {patch_file}")
    
    # Apply the patch by monkey patching
    try:
        exec(bridge_patch)
        
        # Monkey patch the method
        original_method = NeurocorticalBridge.create_llm_inference_command
        NeurocorticalBridge.create_llm_inference_command = patched_create_llm_inference_command
        print("✅ Applied method patch")
    except Exception as e:
        print(f"❌ Failed to apply method patch: {e}")
        return
    
    # Now run a test to verify the work_id handling
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
        
        # Use our patched method
        inference_command = NeurocorticalBridge.create_llm_inference_command(
            prompt="Write a short poem about debugging.",
            work_id=specific_work_id  # Pass the specific work_id
        )
        
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
        
        # Restore the original method
        NeurocorticalBridge.create_llm_inference_command = original_method
        print("\n✅ Restored original method")
        
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
    asyncio.run(test_workid_directly()) 