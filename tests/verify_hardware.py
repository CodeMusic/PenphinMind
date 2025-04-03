#!/usr/bin/env python3
"""
Hardware Verification Script
---------------------------
Tests the LLM inference with the push=true parameter against actual hardware.
This script requires a connection to the device and possibly the paramiko module.

Steps to prepare:
1. Install paramiko: pip install paramiko
2. Make sure your device is connected and powered on
3. Run this script
"""

import sys
import os
import json
import asyncio
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the SystemJournelingManager for logging
try:
    from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel
    journaling_manager = SystemJournelingManager(level=SystemJournelingLevel.DEBUG)
except ImportError as e:
    print(f"Error importing SystemJournelingManager: {e}")
    print("Continuing with basic logging...")
    journaling_manager = None

# Create a simple logger if SystemJournelingManager fails
def log_debug(message):
    """Log debug message using journaling manager or print"""
    if journaling_manager:
        journaling_manager.recordDebug(message)
    else:
        print(f"[DEBUG] {message}")

def log_info(message):
    """Log info message using journaling manager or print"""
    if journaling_manager:
        journaling_manager.recordInfo(message)
    else:
        print(f"[INFO] {message}")

def log_error(message):
    """Log error message using journaling manager or print"""
    if journaling_manager:
        journaling_manager.recordError(message)
    else:
        print(f"[ERROR] {message}")

async def verify_hardware():
    """Verify the push=true fix with actual hardware"""
    try:
        print("\n===== HARDWARE VERIFICATION TEST =====")
        print("Testing if push=true parameter fixes the LLM inference error")
        print("==========================================")
        
        # Try to import required modules
        try:
            # Try to import Mind - this may fail if paramiko is missing
            from Mind.mind import Mind
            from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
            MIND_AVAILABLE = True
        except ImportError as e:
            if 'paramiko' in str(e):
                print(f"\n⚠️ WARNING: {e}")
                print("This test will continue with limited functionality.")
                print("Install paramiko with: pip install paramiko\n")
                from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
                MIND_AVAILABLE = False
            else:
                raise
        
        # First show the command structure
        print("\n--- STEP 1: COMMAND STRUCTURE VERIFICATION ---")
        test_prompt = "Write a short haiku about debugging code"
        
        command = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=False
        )
        
        # Output the command for verification
        print("\nInference Command Structure:")
        print(json.dumps(command, indent=2))
        
        # Verify push parameter is present and set to true
        if "push" in command["data"] and command["data"]["push"] is True:
            print("✅ 'push' parameter is present and set to TRUE")
        else:
            print("❌ 'push' parameter is missing or not set to TRUE")
        
        # Continue with hardware test only if Mind is available
        if not MIND_AVAILABLE:
            print("\n⚠️ Cannot continue with hardware test because paramiko is missing.")
            print("Please install paramiko and run the test again.")
            return
        
        # Initialize Mind
        print("\n--- STEP 2: CONNECTING TO HARDWARE ---")
        print("Initializing Mind and connecting to hardware...")
        
        # Check if the configuration file exists
        config_path = Path("minds_config.json")
        if not config_path.exists():
            print(f"⚠️ Configuration file not found at: {config_path.absolute()}")
            print("Using default configuration...")
            
        # Initialize Mind with auto settings or default mind
        try:
            mind = Mind()  # Default should try auto-discovery
            await mind.initialize()
            print("✅ Mind initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Mind: {e}")
            print("Trying with direct WiFi connection...")
            
            # Try with direct WiFi connection as fallback
            try:
                from Mind.Subcortex.transport_layer import WiFiTransport
                
                # Get connection details from environment or use defaults
                ip = os.environ.get("PENPHIN_DEVICE_IP", "10.0.0.82")
                port = int(os.environ.get("PENPHIN_DEVICE_PORT", "10001"))
                
                print(f"Connecting to device at {ip}:{port}...")
                transport = WiFiTransport(ip, port)
                await transport.connect()
                
                print("✅ Connected directly via WiFiTransport")
                
                # Define a simple function to send commands via transport
                async def send_command(cmd):
                    serialized = json.dumps(cmd)
                    print(f"Sending command: {serialized}")
                    response = await transport.transmit(serialized)
                    return json.loads(response) if response else None
                
                # Test ping command
                print("\nSending ping command...")
                ping_cmd = {"request_id": str(int(time.time())), "work_id": "sys", "action": "ping"}
                ping_response = await send_command(ping_cmd)
                
                if ping_response:
                    print("Ping response:")
                    print(json.dumps(ping_response, indent=2))
                else:
                    print("❌ No response to ping command")
                
                # Send LLM inference command directly
                print("\n--- STEP 3: TESTING INFERENCE WITH PUSH=TRUE ---")
                print("Sending inference command directly via transport...")
                
                inference_response = await send_command(command)
                
                print("\n=== LLM INFERENCE RESPONSE ===")
                print(json.dumps(inference_response, indent=2))
                print("===============================")
                
                # Check for success
                if inference_response:
                    error = inference_response.get("error", {})
                    if error.get("code") == -4 and "push" in error.get("message", ""):
                        print("❌ Still getting push parameter error!")
                    elif error.get("code", 0) != 0:
                        print(f"❌ Error: {error.get('message', 'Unknown error')}")
                    else:
                        print("✅ SUCCESS: No push parameter error!")
                        print("Inference appears to be working correctly.")
                else:
                    print("❌ No response received")
                
                # Clean up
                await transport.disconnect()
                return
            except Exception as e:
                print(f"❌ Direct connection also failed: {e}")
                import traceback
                print(traceback.format_exc())
                return
        
        # If we got here, Mind is initialized
        print("\n--- STEP 3: TESTING CONNECTIVITY ---")
        
        # Test basic ping
        print("Pinging system...")
        ping_result = await mind.ping_system()
        if ping_result and ping_result.get("status") == "ok":
            print("✅ Ping successful!")
        else:
            print(f"❌ Ping failed: {ping_result.get('message', 'Unknown error')}")
            
        # Get hardware info
        print("\nGetting hardware info...")
        hw_result = await mind.get_hardware_info()
        if hw_result and hw_result.get("status") == "ok":
            print("✅ Hardware info retrieved successfully!")
            
            # Get current model
            print("\nGetting current model...")
            model_result = await mind.get_model()
            if model_result and model_result.get("status") == "ok":
                current_model = model_result.get("response", "unknown")
                print(f"Current model: {current_model}")
            else:
                print("❓ Could not determine current model")
                
            # Try listing models
            print("\nListing available models...")
            models_result = await mind.list_models()
            if models_result and models_result.get("status") == "ok":
                models = models_result.get("response", [])
                print(f"Found {len(models)} models")
                
                # Find a small model to test with
                test_model = None
                for model in models:
                    if isinstance(model, dict):
                        model_name = model.get("mode", "")
                    else:
                        model_name = str(model)
                        
                    if "0.5b" in model_name or "tiny" in model_name:
                        test_model = model_name
                        print(f"Selected model for testing: {test_model}")
                        break
                
                if not test_model and models:
                    # Just use first model
                    if isinstance(models[0], dict):
                        test_model = models[0].get("mode", "")
                    else:
                        test_model = str(models[0])
                    print(f"Selected first available model: {test_model}")
                
                # Set model for testing
                if test_model:
                    print(f"\nSetting model to: {test_model}")
                    set_result = await mind.set_model(test_model)
                    if set_result and set_result.get("status") == "ok":
                        print(f"✅ Model set successfully to {test_model}")
                    else:
                        print(f"⚠️ Could not set model: {set_result.get('message', 'Unknown error')}")
                        print("Continuing with current model...")
            else:
                print(f"⚠️ Could not list models: {models_result.get('message', 'Unknown error')}")
                print("Continuing with current model...")
        else:
            print(f"⚠️ Could not get hardware info: {hw_result.get('message', 'Unknown error')}")
            print("Continuing with test anyway...")
        
        # Now test LLM inference with push=true
        print("\n--- STEP 4: TESTING LLM INFERENCE ---")
        print("Executing LLM inference with push=true...")
        
        response = await mind.neurocortical_bridge.execute("think", test_prompt)
        
        print("\n=== LLM INFERENCE RESPONSE ===")
        print(json.dumps(response, indent=2))
        print("===============================")
        
        if response.get("status") == "success":
            print("\n✅ SUCCESS: LLM inference worked with push=true!")
            print(f"Response text: {response.get('text', '')[:100]}...")
            
            # Test streaming
            print("\n--- STEP 5: TESTING STREAMING INFERENCE ---")
            print("Executing streaming inference...")
            
            chunks = []
            async def collect_chunk(chunk):
                chunks.append(chunk)
                print(".", end="", flush=True)
            
            streaming_response = await mind.neurocortical_bridge.execute(
                "think", 
                "Write a haiku about successful debugging", 
                stream=True,
                stream_callback=collect_chunk
            )
            
            print("\n\n=== STREAMING INFERENCE RESPONSE ===")
            print(json.dumps(streaming_response, indent=2))
            print("====================================")
            
            if streaming_response.get("status") == "success":
                print("\n✅ SUCCESS: Streaming inference also worked!")
                print(f"Received {len(chunks)} chunks")
                
                # Combine chunks
                if chunks:
                    full_text = "".join([c.get("text", "") for c in chunks])
                    print(f"\nCombined text: {full_text[:150]}...")
            else:
                print(f"\n❌ Streaming inference failed: {streaming_response.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ LLM inference failed: {response.get('error', 'Unknown error')}")
            print("\nChecking if error is related to push parameter...")
            
            error_msg = response.get("error", "").lower() if isinstance(response.get("error"), str) else ""
            if "push" in error_msg:
                print("‼️ Error still appears to be related to the push parameter!")
                print("The fix may not have been applied correctly or there might be another issue.")
            else:
                print("⚠️ Error does not seem to be related to the push parameter.")
                print("The push=true fix may be working, but there could be other issues.")
        
        # Clean up
        await mind.close()
        
        print("\n===== HARDWARE VERIFICATION COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(verify_hardware()) 