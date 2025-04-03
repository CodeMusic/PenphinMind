#!/usr/bin/env python3
"""
Streaming Configuration Test
---------------------------
Tests that the streaming configuration option works correctly
in both streaming and non-streaming modes.
"""

import sys
import os
import json
import asyncio
import time
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager 
journaling_manager = SystemJournelingManager()
print(f"[SYSTEM] 🧠 SystemJournelingManager initialized with level: {journaling_manager.currentLevel.name}")

class StreamingConfigTest:
    """Test harness for streaming configuration"""
    
    def __init__(self):
        """Initialize the test harness"""
        self.mind = None
        self.original_config = None
        self.chunks = []
    
    def stream_callback(self, text_chunk):
        """Callback for streaming chunks"""
        self.chunks.append(text_chunk)
        print(f"📝 Stream chunk: {text_chunk[:30]}..." if len(text_chunk) > 30 else text_chunk)
    
    async def test_with_config(self, use_streaming: bool) -> Dict[str, Any]:
        """
        Test LLM inference with the specified streaming config
        
        Args:
            use_streaming: Whether to set the config to use streaming mode
            
        Returns:
            Dict with test results
        """
        # Import Mind and mind config modules
        from Mind.mind import Mind
        from Mind.mind_config import get_mind_by_id, save_mind_config
        
        # Get the current config
        mind_id = "auto"  # Default mind ID
        mind_config = get_mind_by_id(mind_id)
        
        # Store original config if this is the first run
        if self.original_config is None:
            self.original_config = {
                "stream": mind_config.get("llm", {}).get("stream", True)
            }
        
        # Update the config with the test setting
        mind_config["llm"]["stream"] = use_streaming
        save_mind_config(mind_id, mind_config)
        print(f"\n[TEST] Set LLM streaming config to: {use_streaming}")
        
        # Create a fresh Mind instance that will use this config
        self.mind = Mind(mind_id)
        print(f"[TEST] Created new Mind instance: {self.mind.name}")
        
        # Initialize the Mind
        init_result = await self.mind.initialize()
        print(f"[TEST] Mind initialization result: {init_result}")
        
        # Reset the chunks array
        self.chunks = []
        
        # Create a test prompt
        test_prompt = "Write a very short poem about debugging code"
        print(f"[TEST] Using test prompt: {test_prompt}")
        
        # Test inference using the llm_inference method
        print("\n[TEST] Testing LLM inference with config...")
        
        try:
            # Use a callback for streaming mode
            if use_streaming:
                print("[TEST] Using callback for streaming mode")
                start_time = time.time()
                # Start the inference - results will come through callback
                await self.mind.llm_inference(
                    prompt=test_prompt,
                    callback=self.stream_callback
                )
                duration = time.time() - start_time
                
                # Give a moment for all chunks to arrive
                await asyncio.sleep(1)
                
                # Collect all chunks into a final response
                response = "".join(self.chunks)
                
                # Report results
                print(f"[TEST] Received {len(self.chunks)} chunks")
                print(f"[TEST] Total response length: {len(response)} characters")
                print(f"[TEST] Duration: {duration:.2f} seconds")
                print(f"\n[TEST] RESPONSE (truncated):\n{response[:200]}...")
                
                return {
                    "mode": "streaming",
                    "config_setting": use_streaming,
                    "success": len(self.chunks) > 0,
                    "chunk_count": len(self.chunks),
                    "response_length": len(response),
                    "duration": duration
                }
                
            else:
                # Normal non-streaming mode
                print("[TEST] Using non-streaming mode")
                start_time = time.time()
                response = await self.mind.llm_inference(
                    prompt=test_prompt
                )
                duration = time.time() - start_time
                
                # Report results
                print(f"[TEST] Response length: {len(response) if response else 0} characters")
                print(f"[TEST] Duration: {duration:.2f} seconds")
                print(f"\n[TEST] RESPONSE (truncated):\n{response[:200]}...")
                
                return {
                    "mode": "non-streaming",
                    "config_setting": use_streaming,
                    "success": response and len(response) > 0,
                    "response_length": len(response) if response else 0,
                    "duration": duration
                }
                
        except Exception as e:
            print(f"[TEST] ❌ Error during test: {e}")
            import traceback
            print(traceback.format_exc())
            
            return {
                "mode": "streaming" if use_streaming else "non-streaming",
                "config_setting": use_streaming,
                "success": False,
                "error": str(e)
            }
    
    async def restore_config(self):
        """Restore the original config values"""
        if self.original_config:
            from Mind.mind_config import get_mind_by_id, save_mind_config
            
            mind_id = "auto"
            mind_config = get_mind_by_id(mind_id)
            
            # Restore the original streaming setting
            if "stream" in self.original_config:
                mind_config["llm"]["stream"] = self.original_config["stream"]
            
            # Save the restored config
            save_mind_config(mind_id, mind_config)
            print(f"\n[TEST] Restored original config: stream={self.original_config.get('stream')}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.mind:
            await self.mind.cleanup()

async def run_tests():
    """Run the streaming configuration tests"""
    print("\n===== STREAMING CONFIGURATION TEST =====")
    
    tester = StreamingConfigTest()
    results = []
    
    try:
        # Test with streaming disabled in config
        print("\n----- TESTING WITH STREAMING DISABLED IN CONFIG -----")
        result_non_streaming = await tester.test_with_config(use_streaming=False)
        results.append(result_non_streaming)
        
        # Cleanup between tests
        await tester.cleanup()
        
        # Test with streaming enabled in config
        print("\n----- TESTING WITH STREAMING ENABLED IN CONFIG -----")
        result_streaming = await tester.test_with_config(use_streaming=True)
        results.append(result_streaming)
        
        # Restore original config
        await tester.restore_config()
        
        # Test summary
        print("\n===== TEST RESULTS =====")
        
        for result in results:
            mode = result.get("mode", "unknown")
            config = result.get("config_setting", "unknown")
            success = result.get("success", False)
            
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{status} - Mode: {mode}, Config: {config}")
            
            if success:
                if mode == "streaming":
                    print(f"  Received {result.get('chunk_count', 0)} chunks")
                print(f"  Response length: {result.get('response_length', 0)} characters")
                print(f"  Duration: {result.get('duration', 0):.2f} seconds")
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print("\n===== TEST COMPLETE =====")
            
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        # Final cleanup
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(run_tests()) 