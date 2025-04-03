# LLM Inference Work ID Fix

## Problem

When setting up LLM and running inference commands, we were encountering errors because we weren't using the specific `work_id` returned from the LLM setup command in subsequent inference commands.

## Key Findings

1. When you send an LLM setup command to the device, the API responds with a specific `work_id` (e.g., `"llm.1003"`) in the response.

2. All subsequent inference commands must use this specific `work_id` instead of the generic `"llm"` work_id.

3. The error "inference data push false" was a red herring - the actual issue was the incorrect work_id being used.

## Implementation Changes

### 1. Store the LLM Work ID

In the `Mind` class, we now store the specific work_id returned from the LLM setup command:

```python
class Mind:
    # Class variables
    _current_llm_work_id = None  # Store the current LLM work_id
    
    # ...
    
    async def set_model(self, model_name):
        # ...
        
        # If successful, store the work_id from the setup response
        if result.get("status") == "ok":
            if "raw" in result and isinstance(result["raw"], dict):
                self._current_llm_work_id = result["raw"].get("work_id")
                if self._current_llm_work_id:
                    journaling_manager.recordInfo(f"Stored LLM work_id: {self._current_llm_work_id}")
```

### 2. Use the Work ID for Inference

The `create_llm_inference_command` method now accepts a specific work_id parameter:

```python
@classmethod
def create_llm_inference_command(cls, prompt, request_id=None, stream=False, work_id=None):
    # ...
    
    # Use the provided work_id if available, otherwise default to "llm"
    if work_id is None:
        work_id = "llm"
    
    # Log the work_id being used
    journaling_manager.recordInfo(f"Using work_id: {work_id}")
    
    base_command = {
        "request_id": request_id,
        "work_id": work_id,  # Use the specific work_id
        "action": "inference"
        # ...
    }
```

### 3. Pass the Work ID in Inference Requests

The `llm_inference` method now passes the stored work_id:

```python
async def llm_inference(self, prompt, stream=None, callback=None, work_id=None):
    # ...
    
    # Use the work_id specified, or the stored work_id from setup, or default to "llm"
    effective_work_id = work_id or self._current_llm_work_id or "llm"
    
    # Log the inference request
    journaling_manager.recordInfo(f"LLM inference request - stream={stream}, work_id={effective_work_id}")
    
    # Create and execute command
    result = await NeurocorticalBridge.execute_operation(
        operation="think",
        data={
            "prompt": prompt,
            "stream": stream,
            "work_id": effective_work_id  # Pass the work_id to the operation
        },
        stream=stream
    )
```

## How to Test

Use the `test_llm_work_id.py` script to verify the fix:

```bash
python tests/test_llm_work_id.py
```

The test script:
1. Sets up the LLM and captures the specific work_id
2. Runs an inference command using the specific work_id
3. Runs another inference command using the generic "llm" work_id
4. Compares the results to confirm which approach works

## API Behavior Details

- The API returns a specific work_id like `"llm.1003"` after setup
- This work_id must be used for inference commands with the same model
- Using the wrong work_id will result in errors or no response
- When switching models, you'll get a new work_id from the setup command

## Logging Enhancements

We've also improved logging to make it easier to debug these issues:

1. Added logging for the work_id being used in inference commands
2. Added logging when capturing the work_id from setup responses
3. Added clear error messages when work_id related problems occur

## Fix Summary

The key insight is that LLM inference is a session-based API where you:
1. Set up the LLM (receive a session work_id)
2. Use that specific work_id for all subsequent commands
3. Start a new session when changing models

This fix ensures we're properly tracking and using the session work_id returned by the setup command. 