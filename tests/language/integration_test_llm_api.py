#!/usr/bin/env python3
"""
LLM API Integration Test
-----------------------
Tests the LLM inference communication with hardware using the correct API format.
This script verifies both streaming and non-streaming modes.

Prerequisites:
- Device must be powered on and connected
- Network connection must be established
"""

import sys
import os
import json
import asyncio
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CognitiveBehavior:
    """Manages the testing behavior and communication flow"""
    
    def __init__(self):
        self.results = {
            "non_streaming": {"status": "not_tested", "response": None},
            "streaming": {"status": "not_tested", "response": None}
        }
    
    async def test_hardware_communication(self):
        """Test communication with hardware using both streaming and non-streaming modes"""
        print("\n===== LLM API INTEGRATION TEST =====")
        
        # First verify the command structure
        await self.verify_command_structure()
        
        try:
            # Import required modules
            from Mind.mind import Mind
            
            # Initialize Mind
            print("\n🔄 Initializing Mind system...")
            mind = Mind()
            
            # Connect to hardware
            print("🔄 Attempting to connect to hardware...")
            try:
                await mind.connect()
                print("✅ Successfully connected to hardware")
                
                # Test standard non-streaming inference
                await self.test_non_streaming_inference(mind)
                
                # Test streaming inference
                await self.test_streaming_inference(mind)
                
                # Disconnect
                print("\n🔄 Disconnecting from hardware...")
                await mind.disconnect()
                print("✅ Successfully disconnected from hardware")
                
            except Exception as e:
                print(f"❌ Hardware connection failed: {e}")
                print("⚠️ Skipping hardware tests")
                
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print("⚠️ Cannot continue with hardware testing")
        
        # Print final results
        self.print_results()
    
    async def verify_command_structure(self):
        """Verify the LLM inference command structure matches API requirements"""
        print("\n--- VERIFYING COMMAND STRUCTURE ---")
        
        try:
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            
            # Create test commands
            test_prompt = "Write a short poem about debugging code"
            
            # Non-streaming command
            non_stream_cmd = NeurocorticalBridge.create_llm_inference_command(
                prompt=test_prompt,
                stream=False
            )
            
            # Streaming command
            stream_cmd = NeurocorticalBridge.create_llm_inference_command(
                prompt=test_prompt,
                stream=True
            )
            
            # Validate non-streaming format
            print("\n🔍 Validating non-streaming command format:")
            if isinstance(non_stream_cmd.get("data"), str):
                print("  ✅ data is correctly a string: {}".format(non_stream_cmd.get("data")[:30] + "..."))
                if non_stream_cmd.get("object") == "llm.utf-8":
                    print("  ✅ object field is correctly 'llm.utf-8'")
                    self.results["non_streaming"]["status"] = "command_valid"
                else:
                    print(f"  ❌ object field should be 'llm.utf-8', got {non_stream_cmd.get('object')}")
            else:
                print(f"  ❌ data should be a string, got {type(non_stream_cmd.get('data')).__name__}")
            
            # Validate streaming format
            print("\n🔍 Validating streaming command format:")
            data = stream_cmd.get("data")
            if isinstance(data, dict) and "delta" in data and "index" in data and "finish" in data:
                print("  ✅ data contains all required fields (delta, index, finish)")
                if stream_cmd.get("object") == "llm.utf-8.stream":
                    print("  ✅ object field is correctly 'llm.utf-8.stream'")
                    self.results["streaming"]["status"] = "command_valid"
                else:
                    print(f"  ❌ object field should be 'llm.utf-8.stream', got {stream_cmd.get('object')}")
            else:
                print("  ❌ data missing required fields")
            
            # Print commands for verification
            print("\nNon-Streaming Command:")
            print(json.dumps(non_stream_cmd, indent=2))
            
            print("\nStreaming Command:")
            print(json.dumps(stream_cmd, indent=2))
            
            return True
            
        except Exception as e:
            print(f"❌ Command verification failed: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    async def test_non_streaming_inference(self, mind):
        """Test non-streaming LLM inference with hardware"""
        print("\n--- TESTING NON-STREAMING INFERENCE ---")
        
        try:
            # Send non-streaming inference request
            print("🔄 Sending non-streaming inference request...")
            response = await mind.llm_inference(
                prompt="Hello, tell me a short joke",
                stream=False
            )
            
            # Process response
            print(f"✅ Received response: {response[:50]}..." if response else "❌ No response received")
            
            # Update results
            self.results["non_streaming"]["status"] = "success" if response else "failed"
            self.results["non_streaming"]["response"] = response
            
        except Exception as e:
            print(f"❌ Non-streaming inference failed: {e}")
            self.results["non_streaming"]["status"] = "error"
            self.results["non_streaming"]["error"] = str(e)
    
    async def test_streaming_inference(self, mind):
        """Test streaming LLM inference with hardware"""
        print("\n--- TESTING STREAMING INFERENCE ---")
        
        try:
            # Define callback for streaming
            collected_text = []
            
            def stream_callback(text_chunk):
                collected_text.append(text_chunk)
                print(f"📝 Received chunk: {text_chunk[:30]}..." if text_chunk else "")
            
            # Send streaming inference request
            print("🔄 Sending streaming inference request...")
            await mind.llm_inference(
                prompt="Write a haiku about programming",
                stream=True,
                callback=stream_callback
            )
            
            # Process collected response
            full_response = "".join(collected_text)
            print(f"\n✅ Full streaming response: {full_response[:50]}..." if full_response else "❌ No response received")
            
            # Update results
            self.results["streaming"]["status"] = "success" if full_response else "failed"
            self.results["streaming"]["response"] = full_response
            
        except Exception as e:
            print(f"❌ Streaming inference failed: {e}")
            self.results["streaming"]["status"] = "error"
            self.results["streaming"]["error"] = str(e)
    
    def print_results(self):
        """Print the final test results summary"""
        print("\n===== TEST RESULTS =====")
        
        # Non-streaming results
        print("\nNon-Streaming Test:")
        status = self.results["non_streaming"]["status"]
        if status == "success":
            print("✅ SUCCESS - Non-streaming inference completed successfully")
            response = self.results["non_streaming"]["response"]
            print(f"Response: {response[:100]}..." if response else "")
        elif status == "command_valid":
            print("🟡 PARTIAL - Command format is valid but hardware test not completed")
        elif status == "error":
            print(f"❌ ERROR - {self.results['non_streaming'].get('error', 'Unknown error')}")
        else:
            print("⚠️ NOT TESTED")
        
        # Streaming results
        print("\nStreaming Test:")
        status = self.results["streaming"]["status"]
        if status == "success":
            print("✅ SUCCESS - Streaming inference completed successfully")
            response = self.results["streaming"]["response"]
            print(f"Response: {response[:100]}..." if response else "")
        elif status == "command_valid":
            print("🟡 PARTIAL - Command format is valid but hardware test not completed")
        elif status == "error":
            print(f"❌ ERROR - {self.results['streaming'].get('error', 'Unknown error')}")
        else:
            print("⚠️ NOT TESTED")
        
        print("\n===== TEST COMPLETE =====")

async def main():
    """Main entry point for the integration test"""
    behavior = CognitiveBehavior()
    await behavior.test_hardware_communication()

if __name__ == "__main__":
    asyncio.run(main()) 