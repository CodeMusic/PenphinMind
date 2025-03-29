import socket
import json
import time

def test_llm_service():
    # Connect to the service
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('10.0.0.177', 10001))
    
    # First send setup command
    setup = {
        "request_id": "sys_setup",
        "work_id": "llm",
        "action": "setup",
        "object": "None",
        "data": json.dumps({"max_token_len": 2048})
    }
    print("\nSending setup command:")
    print(f"Sending: {json.dumps(setup)}")
    s.send((json.dumps(setup) + "\n").encode())
    response = s.recv(1024).decode()
    print(f"Setup response: {response}")
    
    # Test 1: Send a command with proper request_id format
    test1 = {
        "request_id": "generate",  # Use fixed request_id like prototype
        "work_id": "llm",
        "action": "inference",
        "object": "llm.utf-8.stream",
        "data": {
            "delta": "hi",
            "index": 0,
            "finish": True
        }
    }
    print("\nTest 1 - Command with proper request_id:")
    print(f"Sending: {json.dumps(test1)}")
    s.send((json.dumps(test1) + "\n").encode())
    
    # Read response byte by byte
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
    print(f"Full response: {buffer.strip()}")
    
    # Test 2: Send command with longer prompt
    test2 = {
        "request_id": "generate",
        "work_id": "llm",
        "action": "inference",
        "object": "llm.utf-8.stream",
        "data": {
            "delta": "Hello, how are you today?",
            "index": 0,
            "finish": True
        }
    }
    print("\nTest 2 - Longer prompt:")
    print(f"Sending: {json.dumps(test2)}")
    s.send((json.dumps(test2) + "\n").encode())
    
    # Read response byte by byte
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
    print(f"Full response: {buffer.strip()}")
    
    # Test 3: Send command with streaming disabled
    test3 = {
        "request_id": "generate",
        "work_id": "llm",
        "action": "inference",
        "object": "llm.utf-8",  # No .stream suffix
        "data": {
            "delta": "hi",
            "index": 0,
            "finish": True
        }
    }
    print("\nTest 3 - Streaming disabled:")
    print(f"Sending: {json.dumps(test3)}")
    s.send((json.dumps(test3) + "\n").encode())
    
    # Read response byte by byte
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
    print(f"Full response: {buffer.strip()}")
    
    s.close()

if __name__ == "__main__":
    test_llm_service() 