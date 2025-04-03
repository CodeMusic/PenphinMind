# LLM API Format Documentation

## Overview

This document outlines the correct format for LLM API requests based on our investigation of the inference errors.

## Key Findings

1. The API requires different structures for streaming vs. non-streaming requests
2. There is no documented "push" parameter in the API, despite the error messages referring to it
3. The correct command structure is critical for successful inference

## Command Structure

### Non-Streaming Inference Command

```json
{
  "request_id": "1234567890",
  "work_id": "llm",
  "action": "inference",
  "object": "llm.utf-8",
  "data": "The prompt text goes here as a string"
}
```

### Streaming Inference Command

```json
{
  "request_id": "1234567890",
  "work_id": "llm",
  "action": "inference",
  "object": "llm.utf-8.stream",
  "data": {
    "delta": "The prompt text goes here",
    "index": 0,
    "finish": true
  }
}
```

## Implementation Details

The `create_llm_inference_command` method in `Mind/Subcortex/neurocortical_bridge.py` has been updated to generate commands in the correct format:

```python
@staticmethod
def create_llm_inference_command(prompt, stream=False):
    """
    Create a command for LLM inference
    
    Args:
        prompt (str): The text prompt for inference
        stream (bool): Whether to stream the response
        
    Returns:
        dict: The command data structure
    """
    timestamp = int(time.time())
    
    if stream:
        # Streaming format with data as a dictionary
        return {
            "request_id": str(timestamp),
            "work_id": "llm",
            "action": "inference",
            "object": "llm.utf-8.stream",
            "data": {
                "delta": prompt,
                "index": 0,
                "finish": True
            }
        }
    else:
        # Non-streaming format with data as a string
        return {
            "request_id": str(timestamp),
            "work_id": "llm",
            "action": "inference",
            "object": "llm.utf-8",
            "data": prompt
        }
```

## Testing

We have created several test scripts to verify the command structure and functionality:

1. `tests/test_api_format.py` - Verifies the command structure conforms to API documentation
2. `tests/integration_test_llm_api.py` - Tests actual hardware communication with proper API format

## Troubleshooting

If experiencing issues with LLM inference:

1. Verify the command structure matches the API specification exactly
2. Check the response from the hardware for specific error messages
3. Ensure network connectivity is stable
4. Verify the device is powered on and in the correct state
5. Check logs for any hardware-specific errors

## References

- LLM Module API documentation
- Error code -4: Inference data push error 