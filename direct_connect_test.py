#!/usr/bin/env python
"""
Direct socket connection test to PenphinMind device
"""

import socket
import json
import time
import asyncio

# Connection settings
IP_ADDRESS = "10.0.0.141"  # The working IP address
PORT = 10001              # LLM service port

def test_socket_connection():
    """Test basic socket connection"""
    print(f"\n===== TESTING SOCKET CONNECTION =====")
    print(f"Target: {IP_ADDRESS}:{PORT}")
    
    try:
        # Create socket with timeout
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)  # 5 second timeout
            
            # Connect
            print("Connecting...")
            s.connect((IP_ADDRESS, PORT))
            print(f"✅ Socket connection established")
            
            # Send ping command
            ping_command = {
                "request_id": "001",
                "work_id": "sys",
                "action": "ping"
            }
            
            # Send command with newline terminator
            json_data = json.dumps(ping_command) + "\n"
            print(f"Sending: {json_data.strip()}")
            s.sendall(json_data.encode())
            
            # Read response
            buffer = bytearray()
            s.settimeout(5.0)
            
            try:
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    if b'\n' in chunk:  # Stop at newline
                        break
            except socket.timeout:
                if buffer:
                    print("Socket timeout with partial data")
                else:
                    print("Socket timeout with no data")
                    return False
            
            # Process response if we have data
            if buffer:
                response_str = buffer.decode().strip()
                print(f"Received: {response_str}")
                
                try:
                    # Parse JSON response
                    response_data = json.loads(response_str)
                    
                    # Check for success in error code
                    if "error" in response_data and isinstance(response_data["error"], dict):
                        error_code = response_data["error"].get("code", -1)
                        
                        if error_code == 0:
                            print(f"✅ Ping successful!")
                            return True
                        else:
                            error_msg = response_data["error"].get("message", "Unknown error")
                            print(f"❌ API error: {error_msg}")
                            return False
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response")
                    return False
            else:
                print("❌ No response data")
                return False
                
    except socket.timeout:
        print(f"❌ Connection timeout")
        return False
    except socket.error as e:
        print(f"❌ Socket error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_list_models():
    """Test listing available models"""
    print(f"\n===== LISTING AVAILABLE MODELS =====")
    
    try:
        # Create socket with timeout
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)  # 5 second timeout
            
            # Connect
            print("Connecting...")
            s.connect((IP_ADDRESS, PORT))
            
            # Send list models command
            list_command = {
                "request_id": "002",
                "work_id": "sys",
                "action": "lsmode"
            }
            
            # Send command with newline terminator
            json_data = json.dumps(list_command) + "\n"
            print(f"Sending: {json_data.strip()}")
            s.sendall(json_data.encode())
            
            # Read response
            buffer = bytearray()
            s.settimeout(10.0)  # Longer timeout for listing models
            
            try:
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    if b'\n' in chunk:  # Stop at newline
                        break
            except socket.timeout:
                if buffer:
                    print("Socket timeout with partial data")
                else:
                    print("Socket timeout with no data")
                    return False
            
            # Process response if we have data
            if buffer:
                response_str = buffer.decode().strip()
                
                try:
                    # Parse JSON response
                    response_data = json.loads(response_str)
                    
                    # Check for success in error code
                    if "error" in response_data and isinstance(response_data["error"], dict):
                        error_code = response_data["error"].get("code", -1)
                        
                        if error_code == 0:
                            print(f"✅ Models listed successfully!")
                            
                            # Display models if available
                            models = response_data.get("data", [])
                            if isinstance(models, list) and models:
                                print(f"Available models: {len(models)}")
                                for model in models:
                                    if isinstance(model, dict):
                                        name = model.get("name", "Unknown")
                                        print(f"  - {name}")
                            else:
                                print("No models available")
                                
                            return True
                        else:
                            error_msg = response_data["error"].get("message", "Unknown error")
                            print(f"❌ API error: {error_msg}")
                            return False
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response")
                    return False
            else:
                print("❌ No response data")
                return False
                
    except socket.timeout:
        print(f"❌ Connection timeout")
        return False
    except socket.error as e:
        print(f"❌ Socket error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_setup_model():
    """Test setting up a model and capturing its specific work_id"""
    print(f"\n===== SETTING UP MODEL =====")
    
    try:
        # Create socket with timeout
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)  # 5 second timeout
            
            # Connect
            print("Connecting...")
            s.connect((IP_ADDRESS, PORT))
            
            # Use one of the available models (you may need to change this)
            model_name = "qwen2.5-0.5b-prefill"
            
            # Send setup command
            setup_command = {
                "request_id": "003",
                "work_id": "llm",
                "action": "setup",
                "data": model_name
            }
            
            # Send command with newline terminator
            json_data = json.dumps(setup_command) + "\n"
            print(f"Sending: {json_data.strip()}")
            s.sendall(json_data.encode())
            
            # Read response
            buffer = bytearray()
            s.settimeout(30.0)  # Longer timeout for model setup
            
            try:
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    if b'\n' in chunk:  # Stop at newline
                        break
            except socket.timeout:
                if buffer:
                    print("Socket timeout with partial data")
                else:
                    print("Socket timeout with no data")
                    return None
            
            # Process response if we have data
            if buffer:
                response_str = buffer.decode().strip()
                print(f"Received: {response_str}")
                
                try:
                    # Parse JSON response
                    response_data = json.loads(response_str)
                    
                    # Check for success in error code
                    if "error" in response_data and isinstance(response_data["error"], dict):
                        error_code = response_data["error"].get("code", -1)
                        
                        if error_code == 0:
                            # Extract the work_id from the response
                            specific_work_id = response_data.get("work_id")
                            print(f"✅ Model set successfully!")
                            print(f"📝 Received specific work_id: {specific_work_id}")
                            return specific_work_id
                        else:
                            error_msg = response_data["error"].get("message", "Unknown error")
                            print(f"❌ API error: {error_msg}")
                            return None
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response")
                    return None
            else:
                print("❌ No response data")
                return None
                
    except socket.timeout:
        print(f"❌ Connection timeout")
        return None
    except socket.error as e:
        print(f"❌ Socket error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_inference(specific_work_id=None):
    """Test running inference with the specific work_id"""
    print(f"\n===== RUNNING INFERENCE =====")
    
    # If no specific work_id provided, use generic "llm"
    work_id = specific_work_id or "llm"
    print(f"Using work_id: {work_id}")
    
    try:
        # Create socket with timeout
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)  # 5 second timeout
            
            # Connect
            print("Connecting...")
            s.connect((IP_ADDRESS, PORT))
            
            # Simple test prompt
            prompt = "Tell me a short joke"
            
            # Send inference command
            # Include push=true to address the "inference data push false" error
            inference_command = {
                "request_id": "004",
                "work_id": work_id,  # Use the specific work_id if provided
                "action": "inference",
                "object": "llm.utf-8",
                "data": {
                    "prompt": prompt,
                    "push": "true"  # Include push parameter as string "true"
                }
            }
            
            # Send command with newline terminator
            json_data = json.dumps(inference_command) + "\n"
            print(f"Sending inference with prompt: \"{prompt}\" and push=true")
            s.sendall(json_data.encode())
            
            # Read response
            buffer = bytearray()
            s.settimeout(30.0)  # Longer timeout for inference
            
            try:
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    if b'\n' in chunk:  # Stop at newline
                        break
            except socket.timeout:
                if buffer:
                    print("Socket timeout with partial data")
                else:
                    print("Socket timeout with no data")
                    return False
            
            # Process response if we have data
            if buffer:
                response_str = buffer.decode().strip()
                print(f"Received: {response_str}")
                
                try:
                    # Parse JSON response
                    response_data = json.loads(response_str)
                    
                    # Check for success in error code
                    if "error" in response_data and isinstance(response_data["error"], dict):
                        error_code = response_data["error"].get("code", -1)
                        
                        if error_code == 0:
                            print(f"✅ Inference successful!")
                            
                            # Display response if available
                            text = response_data.get("data", "No response")
                            print(f"\nModel response: \"{text}\"")
                                
                            return True
                        else:
                            error_msg = response_data["error"].get("message", "Unknown error")
                            print(f"❌ API error: {error_msg}")
                            return False
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response")
                    return False
            else:
                print("❌ No response data")
                return False
                
    except socket.timeout:
        print(f"❌ Connection timeout")
        return False
    except socket.error as e:
        print(f"❌ Socket error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main entry point"""
    print("===== DIRECT CONNECTION TEST =====")
    print(f"Target device: {IP_ADDRESS}:{PORT}")
    
    # Test basic connection
    ping_success = test_socket_connection()
    
    # Initialize other test results
    models_success = False
    setup_success = False
    inference_success = False
    specific_inference_success = False
    
    # Test listing models if ping succeeds
    if ping_success:
        models_success = test_list_models()
        
        # Test setting up a model
        specific_work_id = test_setup_model()
        setup_success = specific_work_id is not None
        
        # Test inference with generic work_id
        inference_success = test_inference()
        
        # Test inference with specific work_id if available
        if specific_work_id:
            specific_inference_success = test_inference(specific_work_id)
    
    # Print summary
    print("\n===== TEST SUMMARY =====")
    print(f"Socket connection: {'✅ Success' if ping_success else '❌ Failed'}")
    print(f"List models: {'✅ Success' if models_success else '❌ Failed'}")
    print(f"Setup model: {'✅ Success' if setup_success else '❌ Failed'}")
    print(f"Generic inference: {'✅ Success' if inference_success else '❌ Failed'}")
    print(f"Specific work_id inference: {'✅ Success' if specific_inference_success else '❌ Failed'}")
    
    if ping_success and models_success and setup_success and specific_inference_success:
        print("\n✅ All tests passed! Device is ready for use.")
        print("🎉 The work_id fix is working correctly!")
    elif ping_success:
        print("\n⚠️ Basic connection works but some features may not be available.")
        if not specific_inference_success and inference_success:
            print("⚠️ The work_id fix may not be working correctly.")
    else:
        print("\n❌ Connection failed. Please check the device and network settings.")

if __name__ == "__main__":
    main() 