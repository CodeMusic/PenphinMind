#!/usr/bin/env python3
"""
Test Push=True Parameter
------------------------
Tests if setting push=true in the inference command resolves
the "inference data push false" error.
"""

import sys
import os
import json
import asyncio
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the required modules
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager, SystemJournelingLevel
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge

# Set up debug logging
journaling_manager = SystemJournelingManager(level=SystemJournelingLevel.DEBUG)

async def test_push_parameter():
    """Test if push=true parameter fixes the inference error"""
    try:
        # Import the necessary components
        try:
            from Mind.Subcortex.transport_layer import WiFiTransport
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            from Mind.mind import Mind
        except ImportError as e:
            if 'paramiko' in str(e):
                print(f"\n⚠️ WARNING: {e}")
                print("This test will continue with direct API testing without SSH functionality.")
                from Mind.Subcortex.transport_layer import WiFiTransport
            else:
                raise
        
        print("\n===== TESTING PUSH=TRUE PARAMETER =====")
        
        # Test prompt
        test_prompt = "Write a short poem about debugging"
        
        # Create inference command 
        command = NeurocorticalBridge.create_llm_inference_command(
            prompt=test_prompt,
            stream=False
        )
        
        # Output the command for verification
        print("\nInference Command:")
        print(json.dumps(command, indent=2))
        
        # Verify push parameter is present and set to true
        if "push" in command["data"] and command["data"]["push"] is True:
            print("✅ 'push' parameter is present and set to TRUE")
        else:
            print("❌ 'push' parameter is missing or not set to TRUE")
        
        # Try to send the command directly if possible
        try:
            print("\nAttempting to send command to hardware...")
            
            # Initialize a Mind instance (minimal mode)
            # This will try to connect but won't fail the test if it can't
            mind = Mind()
            init_success = False
            
            try:
                # Try to initialize with a short timeout
                await asyncio.wait_for(mind.initialize(), timeout=5.0)
                init_success = True
                print("✅ Successfully initialized Mind instance")
            except (asyncio.TimeoutError, Exception) as e:
                print(f"⚠️ Could not fully initialize Mind: {str(e)}")
                print("Continuing with partial test...")
            
            if init_success:
                # Send the inference command
                print("\n🔄 Sending inference command to hardware...")
                response = await mind.neurocortical_bridge.execute("think", test_prompt)
                
                # Print the response
                print("\n=== LLM INFERENCE RESPONSE ===")
                print(json.dumps(response, indent=2))
                print("===============================")
                
                # Check if the response indicates success
                if response.get("status") == "success":
                    print("\n✅ SUCCESS: Inference command worked with push=true!")
                    print(f"Response text: {response.get('text', '')[:100]}...")
                else:
                    print(f"\n❌ ERROR: {response.get('error', response.get('message', 'Unknown error'))}")
                
                # Clean up
                await mind.close()
            else:
                # Try with direct WiFiTransport if Mind initialization failed
                print("\nTrying direct WiFiTransport approach...")
                
                # Get connection details from environment or use defaults
                ip = os.environ.get("PENPHIN_DEVICE_IP", "10.0.0.82")
                port = int(os.environ.get("PENPHIN_DEVICE_PORT", "10001"))
                
                # Create transport
                transport = WiFiTransport(ip, port)
                
                try:
                    # Connect
                    await transport.connect()
                    print(f"✅ Connected to device at {ip}:{port}")
                    
                    # Send command
                    print("\n🔄 Sending inference command via direct transport...")
                    serialized_command = json.dumps(command)
                    response_data = await transport.transmit(serialized_command)
                    
                    # Print response
                    print("\n=== DIRECT TRANSPORT RESPONSE ===")
                    print(response_data)
                    print("==================================")
                    
                    # Parse response if possible
                    try:
                        response_json = json.loads(response_data)
                        if isinstance(response_json, dict) and response_json.get("error", {}).get("code") != -4:
                            print("\n✅ SUCCESS: No inference data push error!")
                        else:
                            error_msg = response_json.get("error", {}).get("message", "Unknown error")
                            print(f"\n❌ ERROR: {error_msg}")
                    except json.JSONDecodeError:
                        print("\n⚠️ Couldn't parse response as JSON")
                        
                    # Close connection
                    await transport.disconnect()
                except Exception as e:
                    print(f"\n❌ Direct transport error: {e}")
        except Exception as e:
            print(f"\n⚠️ Could not test with hardware: {e}")
            print("Command structure verification completed, but hardware test failed.")
        
        print("\n===== TEST COMPLETE =====")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_push_parameter()) 