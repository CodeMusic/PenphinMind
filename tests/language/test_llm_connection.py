import socket
import json
import time

def test_connection():
    try:
        # Try to connect
        print(f"Connecting to 10.0.0.194:10001...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)  # Increased timeout
        s.connect(('10.0.0.194', 10001))
        print("Connected!")
        
        # First send a reset command
        reset_cmd = {
            "request_id": "sys_reset",
            "work_id": "sys",
            "action": "reset",
            "object": "None",
            "data": "None"
        }
        print(f"\nSending reset command: {json.dumps(reset_cmd)}")
        s.send((json.dumps(reset_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Reset response: {buffer.strip()}")
        
        # Test ping
        ping_cmd = {
            "request_id": "sys_ping",
            "work_id": "sys",
            "action": "ping",
            "object": "None",
            "data": "None"
        }
        print(f"\nSending ping command: {json.dumps(ping_cmd)}")
        s.send((json.dumps(ping_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Ping response: {buffer.strip()}")
        
        # Initialize the LLM
        setup_cmd = {
            "request_id": "llm_setup",
            "work_id": "llm.1000",
            "action": "setup",
            "object": "llm.utf-8.stream",
            "data": json.dumps({
                "system_message": "You are a helpful assistant.",
                "enkws": True,
                "model": "default",
                "enoutput": True,
                "version": "1.0",
                "max_token_len": 2048,
                "wake_word": "hey penphin"
            })
        }
        print(f"\nSending setup command: {json.dumps(setup_cmd)}")
        s.send((json.dumps(setup_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Setup response: {buffer.strip()}")
        
        # Try a simple inference 
        print("\n\nTrying inference command")
        infer_cmd = {
            "request_id": "llm_inference",
            "work_id": "llm.1000", 
            "action": "inference",
            "object": "llm.utf-8.stream",
            "data": {
                "delta": "Hello, how are you?",
                "index": 0,
                "finish": True
            }
        }
        print(f"Sending inference command: {json.dumps(infer_cmd)}")
        s.send((json.dumps(infer_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Inference response: {buffer.strip()}")
        
        s.close()
        print("\nConnection closed")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection() 