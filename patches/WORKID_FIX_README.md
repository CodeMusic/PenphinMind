# LLM Work ID Fix

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
