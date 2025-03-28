import socket
import json

# LLM Device IP and Port (default might be 8080 or 23 for Telnet)
LLM_IP = "10.0.0.114"
LLM_PORT = 8080  # Change if needed

# Ping command JSON
ping_command = {
    "request_id": "sys_ping",
    "action": "ping"
}

def send_ping():
    try:
        # Create a TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # Timeout after 5 seconds
            s.connect((LLM_IP, LLM_PORT))
            
            # Convert JSON to string and send it
            command_str = json.dumps(ping_command) + "\n"
            s.sendall(command_str.encode())

            # Receive the response
            response = s.recv(1024).decode()
            print(f"📡 Response from LLM: {response}")

    except Exception as e:
        print(f"⚠️ Connection failed: {e}")

if __name__ == "__main__":
    send_ping()
