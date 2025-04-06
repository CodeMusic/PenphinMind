#!/usr/bin/env python3
"""
Interactive Inference Test
------------------------
A simple interactive test that lets you try out LLM inference
with push=true against the hardware with your own prompts.

Prerequisites:
1. Install paramiko: pip install paramiko
2. Ensure your device is connected and powered on
"""

import sys
import os
import json
import asyncio
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import SystemJournelingManager
try:
    from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel
    journaling_manager = SystemJournelingManager(level=SystemJournelingLevel.DEBUG)
except ImportError as e:
    print(f"Error importing SystemJournelingManager: {e}")
    print("Continuing with basic logging...")
    journaling_manager = None

async def interactive_test():
    """Run an interactive test allowing custom prompts"""
    try:
        print("\n===== INTERACTIVE LLM INFERENCE TEST =====")
        print("Test LLM inference with push=true parameter")
        print("==========================================")
        
        # Try to import necessary modules
        try:
            from Mind.mind import Mind
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            MIND_AVAILABLE = True
        except ImportError as e:
            if 'paramiko' in str(e):
                print(f"\n⚠️ WARNING: {e}")
                print("This test requires paramiko for connecting to the device.")
                print("Install paramiko with: pip install paramiko")
                print("Then run this script again.\n")
                return
            else:
                raise
        
        # Show the command structure with push=true
        print("\nVerifying command structure includes push=true...")
        test_cmd = NeurocorticalBridge.create_llm_inference_command("Test", stream=False)
        if "push" in test_cmd["data"] and test_cmd["data"]["push"] is True:
            print("✅ Command includes push=true parameter")
        else:
            print("❌ Command does NOT include push=true parameter!")
            print("Please ensure the NeurocorticalBridge.create_llm_inference_command method has been updated.")
            return
        
        # Initialize Mind
        print("\nInitializing Mind and connecting to device...")
        mind = Mind()
        try:
            # Try to initialize with a timeout
            await asyncio.wait_for(mind.initialize(), timeout=10.0)
            print("✅ Connected to device successfully!")
        except asyncio.TimeoutError:
            print("⚠️ Connection is taking longer than expected, but continuing...")
        except Exception as e:
            print(f"❌ Failed to connect to device: {e}")
            print("Please check your device connection and configuration.")
            return
        
        # Test basic connectivity
        print("\nTesting connectivity with ping...")
        ping_result = await mind.ping_system()
        if ping_result and ping_result.get("status") == "ok":
            print("✅ Ping successful!")
        else:
            print(f"❌ Ping failed: {ping_result.get('message', 'Unknown error')}")
            print("Continuing anyway...")
        
        # Get hardware info
        print("\nGetting hardware info...")
        hw_result = await mind.get_hardware_info()
        if hw_result and hw_result.get("status") == "ok":
            print("✅ Hardware info retrieved successfully!")
        else:
            print(f"⚠️ Could not get hardware info: {hw_result.get('message', 'Unknown error')}")
        
        # Interactive loop for testing
        try:
            # First get and show available models
            print("\nGetting available models...")
            models_result = await mind.list_models()
            if models_result and models_result.get("status") == "ok":
                models = models_result.get("response", [])
                print(f"Found {len(models)} models")
                
                print("\nAvailable models:")
                model_dict = {}
                i = 1
                
                for model in models:
                    if isinstance(model, dict):
                        model_name = model.get("mode", "")
                        model_type = model.get("type", "")
                    else:
                        model_name = str(model)
                        model_type = "unknown"
                    
                    model_dict[i] = model_name
                    print(f"{i}) {model_name} ({model_type})")
                    i += 1
                
                # Let user select a model
                while True:
                    try:
                        selection = input("\nSelect model number (or Enter for default): ")
                        
                        if selection.strip() == "":
                            # Use default
                            print("Using default model...")
                            break
                        
                        model_num = int(selection)
                        if 1 <= model_num < i:
                            model_name = model_dict[model_num]
                            print(f"Setting model to: {model_name}")
                            
                            set_result = await mind.set_model(model_name)
                            if set_result and set_result.get("status") == "ok":
                                print(f"✅ Model set to: {model_name}")
                            else:
                                print(f"❌ Could not set model: {set_result.get('message', 'Unknown error')}")
                            break
                        else:
                            print("Invalid selection. Please try again.")
                    except ValueError:
                        print("Please enter a valid number.")
            else:
                print(f"⚠️ Could not list models: {models_result.get('message', 'Unknown error')}")
                print("Continuing with default model...")
            
            # Main interaction loop
            print("\n" + "=" * 50)
            print("      INTERACTIVE INFERENCE TEST")
            print("=" * 50)
            print("Type your prompts below to test the LLM.")
            print("Commands:")
            print("  /stream   - Toggle streaming mode (currently OFF)")
            print("  /quit     - Exit the test")
            print("=" * 50)
            
            streaming = False
            
            while True:
                # Get user prompt
                prompt = input("\nEnter your prompt: ")
                
                # Handle commands
                if prompt.strip().lower() == "/quit":
                    print("Exiting test...")
                    break
                elif prompt.strip().lower() == "/stream":
                    streaming = not streaming
                    print(f"Streaming mode: {'ON' if streaming else 'OFF'}")
                    continue
                elif not prompt.strip():
                    continue
                
                # Execute the prompt
                print(f"\nSending prompt to LLM ({streaming=})...")
                start_time = time.time()
                
                if streaming:
                    chunks = []
                    async def collect_chunk(chunk):
                        chunks.append(chunk)
                        text = chunk.get("text", "")
                        print(text, end="", flush=True)
                    
                    print("\nResponse: ", end="", flush=True)
                    response = await mind.neurocortical_bridge.execute(
                        "think", 
                        prompt, 
                        stream=True,
                        stream_callback=collect_chunk
                    )
                    
                    elapsed = time.time() - start_time
                    print(f"\n\nReceived {len(chunks)} chunks in {elapsed:.2f} seconds")
                    
                    if response.get("status") != "success":
                        print(f"\n❌ Error: {response.get('error', 'Unknown error')}")
                else:
                    response = await mind.neurocortical_bridge.execute("think", prompt)
                    elapsed = time.time() - start_time
                    
                    print("\nResponse:")
                    if response.get("status") == "success":
                        print(response.get("text", ""))
                    else:
                        print(f"❌ Error: {response.get('error', 'Unknown error')}")
                    
                    print(f"\nReceived in {elapsed:.2f} seconds")
                
        finally:
            # Clean up
            print("\nCleaning up...")
            await mind.close()
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(interactive_test()) 