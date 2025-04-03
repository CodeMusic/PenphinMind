#!/usr/bin/env python3
"""
Fix Mind Work ID Handling
------------------------
Updates Mind class and NeurocorticalBridge to correctly use the
work_id from LLM setup in subsequent inference commands.
"""

import os
import sys
import json
from pathlib import Path

def update_mind_class():
    """Update Mind class to store and use work_id from setup"""
    # Define paths
    patches_dir = Path(__file__).parent
    root_dir = patches_dir.parent
    mind_path = root_dir / "Mind" / "mind.py"
    bridge_path = root_dir / "Mind" / "Subcortex" / "neurocortical_bridge.py"
    
    print(f"Updating Mind class at: {mind_path}")
    
    # Check if files exist
    if not mind_path.exists():
        print(f"Error: Mind class file not found at {mind_path}")
        return False
    
    if not bridge_path.exists():
        print(f"Error: NeurocorticalBridge file not found at {bridge_path}")
        return False
    
    # Read the Mind class file
    with open(mind_path, 'r') as f:
        mind_content = f.read()
    
    # Read the NeurocorticalBridge file
    with open(bridge_path, 'r') as f:
        bridge_content = f.read()
    
    # 1. Add _current_llm_work_id to Mind class if not already there
    class_var_code = """class Mind:
    \"\"\"Main interface for interacting with PenphinMind\"\"\"
    
    # Class variables
    _current_llm_work_id = None  # Store the current LLM work_id"""
    
    old_class_def = """class Mind:
    \"\"\"Main interface for interacting with PenphinMind\"\"\""""
    
    if "_current_llm_work_id" not in mind_content:
        print("Adding _current_llm_work_id class variable to Mind")
        mind_content = mind_content.replace(old_class_def, class_var_code)
    else:
        print("_current_llm_work_id already exists in Mind class")
    
    # 2. Update set_model method to store work_id
    set_model_update = """
            # If successful, store the model name
            if result.get("status") == "ok":
                self._llm_config["model"] = model_name
                journaling_manager.recordInfo(f"Model set to {model_name}")
                
                # Store the work_id from the setup response
                if "raw" in result and isinstance(result["raw"], dict):
                    self._current_llm_work_id = result["raw"].get("work_id")
                    if self._current_llm_work_id:
                        journaling_manager.recordInfo(f"Stored LLM work_id: {self._current_llm_work_id}")"""
    
    old_set_model_code = """
            # If successful, store the model name
            if result.get("status") == "ok":
                self._llm_config["model"] = model_name
                journaling_manager.recordInfo(f"Model set to {model_name}")"""
    
    if "Stored LLM work_id" not in mind_content:
        print("Updating set_model method to store work_id")
        mind_content = mind_content.replace(old_set_model_code, set_model_update)
    else:
        print("set_model already stores work_id")
    
    # 3. Update llm_inference method to use the stored work_id
    llm_inference_update = """
            # Use the work_id specified, or the stored work_id from setup, or default to "llm"
            effective_work_id = work_id or self._current_llm_work_id or "llm"
            
            # Log the inference request
            journaling_manager.recordInfo(f"LLM inference request - stream={stream}, work_id={effective_work_id}")"""
    
    old_llm_inference_code = """
            # Log the inference request
            journaling_manager.recordInfo(f"LLM inference request - stream={stream}")"""
    
    if "effective_work_id" not in mind_content:
        print("Updating llm_inference method to use stored work_id")
        mind_content = mind_content.replace(old_llm_inference_code, llm_inference_update)
    else:
        print("llm_inference already uses stored work_id")
    
    # 4. Add work_id parameter to data block in llm_inference
    data_update = """data={
                    "prompt": prompt,
                    "stream": stream,
                    "work_id": effective_work_id  # Pass the work_id to the operation
                },"""
    
    old_data_code = """data={
                    "prompt": prompt,
                    "stream": stream
                },"""
    
    if "effective_work_id" in mind_content and "work_id: effective_work_id" not in mind_content:
        print("Adding work_id to data block in llm_inference")
        mind_content = mind_content.replace(old_data_code, data_update)
    else:
        print("work_id already in data block")
    
    # 5. Update NeurocorticalBridge create_llm_inference_command to accept work_id
    create_cmd_update = """
    @classmethod
    def create_llm_inference_command(cls, prompt, request_id=None, stream=False, work_id=None):
        \"\"\"
        Create a command for LLM inference following the exact API format.
        
        For non-streaming, data is a string.
        For streaming, data is an object with delta, index, and finish.
        
        Args:
            prompt: The prompt text
            request_id: Optional request ID (generated if None)
            stream: Whether to use streaming mode
            work_id: Optional specific work_id from setup (e.g., "llm.1003") - if None, uses generic "llm"
            
        Returns:
            dict: Properly formatted command
        \"\"\"
        # Log the streaming mode being used
        journaling_manager = SystemJournelingManager()
        mode_str = "STREAMING" if stream else "NON-STREAMING"
        journaling_manager.recordInfo(f"🔍 Creating LLM inference command in {mode_str} mode")
        
        if request_id is None:
            request_id = str(int(time.time()))
        
        # Use the provided work_id if available, otherwise default to "llm"
        if work_id is None:
            work_id = "llm"
        
        # Log the work_id being used
        journaling_manager.recordInfo(f"Using work_id: {work_id}")"""
    
    old_create_cmd = """
    @classmethod
    def create_llm_inference_command(cls, prompt, request_id=None, stream=False):
        \"\"\"
        Create a command for LLM inference following the exact API format.
        
        For non-streaming, data is a string.
        For streaming, data is an object with delta, index, and finish.
        
        Args:
            prompt: The prompt text
            request_id: Optional request ID (generated if None)
            stream: Whether to use streaming mode
            
        Returns:
            dict: Properly formatted command
        \"\"\"
        # Log the streaming mode being used
        journaling_manager = SystemJournelingManager()
        mode_str = "STREAMING" if stream else "NON-STREAMING"
        journaling_manager.recordInfo(f"🔍 Creating LLM inference command in {mode_str} mode")
        
        if request_id is None:
            request_id = str(int(time.time()))"""
    
    if "work_id: Optional specific work_id" not in bridge_content:
        print("Updating create_llm_inference_command method to accept work_id parameter")
        bridge_content = bridge_content.replace(old_create_cmd, create_cmd_update)
    else:
        print("create_llm_inference_command already accepts work_id parameter")
    
    # 6. Update base_command creation in create_llm_inference_command
    base_cmd_update = """
        # Create base command structure
        base_command = {
            "request_id": request_id,
            "work_id": work_id,
            "action": "inference"
        }"""
    
    if "work_id: work_id" not in bridge_content and "work_id=None" in bridge_content:
        print("Updating base_command structure in create_llm_inference_command")
        bridge_content = bridge_content.replace("work_id = \"llm\"", "work_id = work_id or \"llm\"")
    else:
        print("base_command already uses work_id parameter")
    
    # Write updated content
    with open(mind_path, 'w') as f:
        f.write(mind_content)
    
    with open(bridge_path, 'w') as f:
        f.write(bridge_content)
    
    print("\n✅ Mind class and NeurocorticalBridge successfully updated to handle work_id correctly")
    print("Please restart any running application instances to apply the changes.")
    return True

def create_readme():
    """Create README explaining the work_id fix"""
    patches_dir = Path(__file__).parent
    readme_path = patches_dir / "WORKID_FIX_README.md"
    
    readme_content = """# LLM Work ID Fix

## Problem

The LLM inference was failing because we were using the generic "llm" work_id for inference
commands instead of the specific work_id returned from the setup command (e.g., "llm.1003").

## Fix Description

This patch updates two key components:

1. **Mind Class**:
   - Added `_current_llm_work_id` to store the work_id from setup
   - Updated `set_model` to extract and store the work_id from setup response
   - Updated `llm_inference` to use the stored work_id for inference commands

2. **NeurocorticalBridge**:
   - Updated `create_llm_inference_command` to accept work_id parameter
   - Modified command creation to use the specific work_id

## How It Works

The API sends a special work_id (like "llm.1003") when you set up a model. 
All subsequent inference commands for that model must use this specific work_id 
instead of the generic "llm" work_id.

Now the system properly captures this work_id during setup and uses it for all
inference commands, resolving the errors.

## Example

Setup response with work_id:
```json
{
  "created": 1683456789,
  "error": {
    "code": 0,
    "message": "setup done"
  },
  "request_id": "123456789",
  "work_id": "llm.1003"  // This specific ID must be used
}
```

## Usage

The fix is applied automatically once you run this patch. No manual changes needed.
Just restart any running applications to make sure the changes take effect.
"""
    
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"\nCreated README at: {readme_path}")

if __name__ == "__main__":
    print("Running Mind Work ID patch")
    if update_mind_class():
        create_readme()
    print("Patch complete") 