## Configuration

The streaming mode can be configured in the `minds_config.json` file through the `stream` setting:

```json
{
  "minds": {
    "auto": {
      "name": "PenphinMind",
      "device_id": "auto",
      "connection": {
        "type": "tcp",
        "ip": "auto",
        "port": "auto"
      },
      "llm": {
        "default_model": "qwen2.5-0.5b-prefill",
        "temperature": 0.7,
        "max_tokens": 127,
        "persona": "You are a helpful assistant named {name}.",
        "stream": true  // Set to false to disable streaming
      }
    }
  }
}
``` 

## When to Use Each Mode

### Streaming Mode (stream: true)
- **Benefits**: 
  - Faster perceived response time (text appears incrementally)
  - Better user experience for chat interfaces
  - Allows for handling interruptions
- **Use when**:
  - Building interactive chat interfaces
  - Working with longer responses
  - User experience is a priority

### Non-Streaming Mode (stream: false)
- **Benefits**:
  - Simpler implementation (no callback handling)
  - Single response to process
  - May be more stable on some hardware
- **Use when**:
  - Building non-interactive tools
  - Processing is done in batch
  - Troubleshooting issues with streaming mode

## Troubleshooting

If you encounter issues with LLM inference, try switching between streaming and non-streaming modes:

1. If streaming mode is failing, try setting `stream: false` in the config 