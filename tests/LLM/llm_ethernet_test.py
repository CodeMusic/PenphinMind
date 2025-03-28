import socket
import json
import time
import paramiko

# LLM Device IP and Port
LLM_IP = "10.0.0.177"  # Your IP address
LLM_PORT = 22  # SSH port

# SSH Credentials
SSH_USERNAME = "root"  # Change this to your username
SSH_PASSWORD = "123456"  # Change this to your password

def find_llm_port(ssh) -> int:
    """Find the port where the LLM service is running"""
    print("\nChecking for LLM service port...")
    
    # First try to find the port from the process
    stdin, stdout, stderr = ssh.exec_command("lsof -i -P -n | grep llm_llm")
    for line in stdout:
        print(f"Found port info: {line.strip()}")
        # Look for port number in the output
        if ":" in line:
            port = line.split(":")[-1].split()[0]
            print(f"Found LLM service port: {port}")
            return int(port)
    
    # If we couldn't find it through lsof, try netstat
    print("\nTrying netstat to find port...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tulpn | grep llm_llm")
    for line in stdout:
        print(f"Found port info: {line.strip()}")
        # Look for port number in the output
        if ":" in line:
            port = line.split(":")[-1].split()[0]
            print(f"Found LLM service port: {port}")
            return int(port)
    
    # If we still can't find it, try to get the port from the process arguments
    print("\nChecking process arguments...")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep llm_llm")
    for line in stdout:
        if "llm_llm" in line and not "grep" in line:
            print(f"Found process: {line.strip()}")
            # Try to find port in process arguments
            if "--port" in line:
                port = line.split("--port")[1].split()[0]
                print(f"Found port in arguments: {port}")
                return int(port)
    
    # If we get here, try common ports
    print("\nTrying common ports...")
    common_ports = [8080, 80, 443, 5000, 8000, 3000, 10001]  # Added 10001 since it was in the listening ports
    for port in common_ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((LLM_IP, port))
                if result == 0:
                    print(f"Port {port} is open and accepting connections")
                    return port
        except Exception as e:
            print(f"Error checking port {port}: {e}")
    
    raise Exception("Could not find LLM service port")

def send_command(command: dict, timeout: float = 5.0) -> dict:
    """Send a command to the LLM device and wait for response"""
    try:
        # First, use SSH to check if the LLM service is running
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"\nConnecting to {LLM_IP}:{LLM_PORT}...")
        ssh.connect(
            LLM_IP, 
            port=LLM_PORT, 
            username=SSH_USERNAME,
            password=SSH_PASSWORD,
            timeout=timeout
        )
        
        # Find the LLM service port
        service_port = find_llm_port(ssh)
        print(f"\nFound LLM service on port {service_port}")
        
        # Now connect to the LLM service directly
        print(f"Connecting to LLM service on port {service_port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((LLM_IP, service_port))
            
            # Convert command to the format expected by the service
            if command["type"] == "LLM" and command["command"] == "generate":
                command_json = {
                    "request_id": command["data"]["request_id"],
                    "work_id": "llm",
                    "action": "inference",
                    "object": "llm.utf-8.stream",
                    "data": {
                        "delta": command["data"]["prompt"],
                        "index": 0,
                        "finish": True
                    }
                }
            else:
                command_json = command
            
            # Convert to string and send it
            command_str = json.dumps(command_json) + "\n"
            print(f"Sending command: {command_str.strip()}")
            s.sendall(command_str.encode())
            
            # Receive the response
            buffer = ""
            while True:
                try:
                    data = s.recv(1).decode()
                    if not data:
                        break
                    buffer += data
                    if data == "\n":
                        break
                except socket.timeout:
                    break
            
            print(f"Received response: {buffer.strip()}")
            try:
                return json.loads(buffer.strip())
            except json.JSONDecodeError:
                return {"error": "Failed to parse response", "raw": buffer.strip()}

    except paramiko.AuthenticationException:
        return {"error": "Authentication failed - check username and password"}
    except paramiko.SSHException as e:
        return {"error": f"SSH error: {str(e)}"}
    except ConnectionRefusedError:
        return {"error": "Connection refused - device may be offline or wrong port"}
    except socket.timeout:
        return {"error": "Connection timed out"}
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}
    finally:
        if 'ssh' in locals():
            ssh.close()

def test_ping():
    """Test basic connectivity with a ping command"""
    print("\n=== Testing Ping ===")
    ping_command = {
        "request_id": "sys_ping",
        "work_id": "sys",
        "action": "ping",
        "object": "None",
        "data": "None"
    }
    response = send_command(ping_command)
    print(f"Ping response: {response}")

def test_generate():
    """Test LLM generation with a simple prompt"""
    print("\n=== Testing Generate ===")
    prompt = "What is the capital of France?"
    generate_command = {
        "type": "LLM",
        "command": "generate",
        "data": {
            "prompt": prompt,
            "timestamp": int(time.time() * 1000),
            "version": "1.0",
            "request_id": f"generate_{int(time.time())}"
        }
    }
    response = send_command(generate_command)
    print(f"Generate response: {response}")

def main():
    """Main function"""
    while True:
        print("\n=== LLM Ethernet Test ===")
        print("1. Test Ping")
        print("2. Test Generate")
        print("3. Exit")
        
        try:
            choice = input("\nSelect an option (1-3): ").strip()
            
            if choice == "1":
                test_ping()
            elif choice == "2":
                test_generate()
            elif choice == "3":
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please select 1-3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

if __name__ == "__main__":
    main()
