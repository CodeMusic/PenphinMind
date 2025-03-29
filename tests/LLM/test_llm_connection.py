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
        
        # Initialize the LLM with setup parameters
        init_cmd = {
            "request_id": "sys_setup",
            "work_id": "sys",
            "action": "setup",
            "object": "None",
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
        print(f"\nSending setup: {json.dumps(init_cmd)}")
        s.send((json.dumps(init_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                print(f"Received byte: {data!r}")
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Setup response: {buffer.strip()}")
        
        # First try a ping command
        ping_cmd = {
            "request_id": "sys_ping",
            "work_id": "sys",
            "action": "ping",
            "object": "None",
            "data": {}
        }
        print(f"\nSending ping: {json.dumps(ping_cmd)}")
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
                print(f"Received byte: {data!r}")
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Ping response: {buffer.strip()}")
        
        # Now try an inference command
        print("\n\nTrying inference command")
        time.sleep(1)
        
        # Send an inference command
        infer_cmd = {
            "request_id": "test_inference",
            "work_id": "llm", 
            "action": "inference",
            "object": "llm.utf-8.stream",
            "data": {
                "text": "Hello, how are you?",
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
                print(f"Received byte: {data!r}")
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Inference response: {buffer.strip()}")
        
        # Try alternative command format - using delta instead of text
        print("\n\nTrying alternative command format")
        time.sleep(1)
        
        alt_cmd = {
            "request_id": "test_alt",
            "work_id": "llm",
            "action": "inference",
            "object": "llm.utf-8.stream",
            "data": {
                "delta": "Alternative format test",
                "index": 0,
                "finish": True
            }
        }
        print(f"Sending alternative command: {json.dumps(alt_cmd)}")
        s.send((json.dumps(alt_cmd) + "\n").encode())
        
        # Read response
        buffer = ""
        while True:
            try:
                data = s.recv(1).decode()
                if not data:
                    print("No more data received")
                    break
                buffer += data
                print(f"Received byte: {data!r}")
                if data == "\n":
                    print("Received newline, ending read")
                    break
            except socket.timeout:
                print("Socket timeout")
                break
        
        print(f"Alternative response: {buffer.strip()}")
        
        s.close()
        print("\nConnection closed")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection() 