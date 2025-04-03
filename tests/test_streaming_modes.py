#!/usr/bin/env python3
"""
LLM Streaming Modes Test
-----------------------
Tests both streaming and non-streaming modes with proper debug logging.
This script will help identify any issues with the LLM inference command formatting.
"""

import sys
import os
import json
import asyncio
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()
print(f"[SYSTEM] 🧠 SystemJournelingManager initialized with level: {journaling_manager.currentLevel.name}")

async def test_streaming_modes():
    """Test both streaming and non-streaming modes"""
    print("\n===== LLM STREAMING MODES TEST =====")
    
    try:
        # Import Mind
        from Mind.mind import Mind
        from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
        
        # Initialize Mind
        print("\n----- Initializing Mind -----")
        mind = Mind()
        
        # Set up a test prompt
        test_prompt = "Write a very short poem about debugging code"
        
        # Test the create_llm_inference_command method directly
        print("\n----- Testing Command Creation -----")
        
        # Non-streaming command
        print("\n1. Creating NON-STREAMING command:")
        non_streaming_cmd = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=False
        )
        print(json.dumps(non_streaming_cmd, indent=2))
        
        # Streaming command
        print("\n2. Creating STREAMING command:")
        streaming_cmd = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=True
        )
        print(json.dumps(streaming_cmd, indent=2))
        
        # Test non-streaming mode with explicit override
        print("\n----- Testing Non-Streaming Mode (Explicit) -----")
        try:
            # This should use explicit non-streaming mode
            response = await mind.llm_inference(
                prompt=test_prompt,
                stream=False
            )
            print(f"\nNon-streaming response received: {response[:100]}..." if response else "No response")
        except Exception as e:
            print(f"Non-streaming test failed: {e}")
            import traceback
            print(traceback.format_exc())
        
        # Test streaming mode with callback
        print("\n----- Testing Streaming Mode (Explicit) -----")
        try:
            chunks = []
            
            # Callback for streaming chunks
            def chunk_callback(text):
                chunks.append(text)
                print(f"Chunk received: {text[:30]}..." if len(text) > 30 else text)
            
            # This should use explicit streaming mode
            await mind.llm_inference(
                prompt=test_prompt,
                stream=True,
                callback=chunk_callback
            )
            
            # Wait a moment for all chunks to arrive
            await asyncio.sleep(1)
            
            # Print combined response
            combined = "".join(chunks)
            print(f"\nTotal streaming response: {combined[:100]}..." if combined else "No streaming response")
            
        except Exception as e:
            print(f"Streaming test failed: {e}")
            import traceback
            print(traceback.format_exc())
        
        # Print test summary
        print("\n===== TEST SUMMARY =====")
        print("1. Command Creation: ✓")
        print(f"2. Non-Streaming Test: {'✓' if response else '✗'}")
        print(f"3. Streaming Test: {'✓' if chunks else '✗'}")
        
        print("\n===== TEST COMPLETE =====")
    
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_streaming_modes()) 