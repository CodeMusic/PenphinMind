"""
Configuration Usage Example

This file demonstrates the proper way to use both configuration systems in PenphinMind.
It follows best practices to avoid circular dependencies and maintain a clear separation
between mind-specific and system-wide configurations.
"""

from typing import Dict, Any

# System-wide configuration import
from config import CONFIG

# Mind-specific configuration imports
from Mind.mind_config import get_mind_by_id, get_default_mind_id, load_minds_config, save_mind_config

def print_system_config_example():
    """Example of using system-wide configuration"""
    print("\n=== System-wide Configuration Example ===")
    print(f"Log Level: {CONFIG.log_level}")
    print(f"Debug Mode: {CONFIG.debug_mode}")
    
    print("\nSerial Settings:")
    print(f"  Port: {CONFIG.serial_settings['port']}")
    print(f"  Baud Rate: {CONFIG.serial_settings['baud_rate']}")
    print(f"  Timeout: {CONFIG.serial_settings['timeout']}s")
    
    print("\nAudio Settings:")
    print(f"  Sample Rate: {CONFIG.sample_rate}Hz")
    print(f"  Channels: {CONFIG.channels}")
    print(f"  Volume: {CONFIG.audio_device_controls['volume']}%")

def print_mind_config_example():
    """Example of using mind-specific configuration"""
    print("\n=== Mind-specific Configuration Example ===")
    
    # Get default mind ID
    default_mind_id = get_default_mind_id()
    print(f"Default Mind ID: {default_mind_id}")
    
    # Get config for the default mind
    mind_config = get_mind_by_id(default_mind_id)
    
    print(f"Mind Name: {mind_config['name']}")
    print(f"Device ID: {mind_config['device_id']}")
    
    print("\nConnection Settings:")
    print(f"  Type: {mind_config['connection']['type']}")
    print(f"  IP: {mind_config['connection']['ip']}")
    print(f"  Port: {mind_config['connection']['port']}")
    
    print("\nLLM Settings:")
    print(f"  Default Model: {mind_config['llm']['default_model']}")
    print(f"  Temperature: {mind_config['llm']['temperature']}")
    print(f"  Max Tokens: {mind_config['llm']['max_tokens']}")
    
    # Format the persona string if it contains placeholders
    persona = mind_config['llm']['persona']
    formatted_persona = persona.format(name=mind_config['name'])
    print(f"  Persona: {formatted_persona}")

def print_all_mind_configs():
    """Example of accessing all three minds: penphin, dolphin, and penguin"""
    print("\n=== All Available Minds ===")
    
    # Load minds config to get all minds
    minds_config = load_minds_config()
    minds = minds_config.get("minds", {})
    
    # Loop through each mind
    for mind_id, mind_data in minds.items():
        print(f"\nMind ID: {mind_id}")
        print(f"Name: {mind_data.get('name', 'Unknown')}")
        print(f"Device ID: {mind_data.get('device_id', 'Unknown')}")
        
        # Connection info
        connection = mind_data.get("connection", {})
        print(f"Connection: {connection.get('type', 'Unknown')} - {connection.get('ip', 'auto')}:{connection.get('port', 'auto')}")
        
        # LLM info
        llm = mind_data.get("llm", {})
        print(f"LLM Model: {llm.get('default_model', 'Unknown')}")

def get_combined_config(mind_id: str = None) -> Dict[str, Any]:
    """
    Example function that combines mind-specific and system-wide settings
    
    This demonstrates how to properly use both configuration systems together.
    
    Args:
        mind_id: ID of the mind to use, or None for default
        
    Returns:
        Combined configuration dictionary
    """
    # Get mind-specific config
    mind_config = get_mind_by_id(mind_id)
    
    # Create a combined config
    combined_config = {
        # Mind-specific settings
        "name": mind_config["name"],
        "device_id": mind_config["device_id"],
        "connection": mind_config["connection"].copy(),
        "llm_settings": mind_config["llm"].copy(),
        
        # System-wide settings
        "debug": CONFIG.debug_mode,
        "log_level": CONFIG.log_level,
        "audio": {
            "sample_rate": CONFIG.sample_rate,
            "channels": CONFIG.channels,
            "volume": CONFIG.audio_device_controls["volume"]
        },
        "serial": CONFIG.serial_settings.copy()
    }
    
    return combined_config

def get_device_connection(mind_id: str = None) -> Dict[str, Any]:
    """
    Get connection settings for a specific mind or the default mind
    
    This demonstrates how to access device connection settings for
    a specific mind, with fallback to the default "auto" mind.
    
    Args:
        mind_id: ID of the mind to use, or None for default
        
    Returns:
        Connection settings dictionary
    """
    # Try to get the requested mind first
    if mind_id:
        try:
            mind_config = get_mind_by_id(mind_id)
            connection = mind_config.get("connection", {})
            print(f"Using connection settings from mind: {mind_id}")
            return connection
        except Exception as e:
            print(f"Error getting mind {mind_id}: {e}")
            # Fall through to default
    
    # Get the default mind as fallback
    default_mind = get_mind_by_id("auto")
    connection = default_mind.get("connection", {})
    print(f"Using connection settings from default mind: auto")
    return connection

def init_transport_example():
    """
    Example demonstrating how to initialize a transport connection
    using mind-specific configuration instead of system-wide config
    
    This shows how to properly deal with the 'Config' object has no attribute 'llm_service' error
    by accessing connection settings from mind configuration instead.
    """
    print("\n=== Transport Initialization Example ===")
    
    # Get connection settings from mind config
    mind_id = "penphin"  # Try with specific mind
    connection = get_device_connection(mind_id)
    
    # Now use these settings directly instead of CONFIG.llm_service
    print(f"Initializing transport for mind: {mind_id}")
    print(f"  Connection type: {connection.get('type', 'tcp')}")
    print(f"  IP address: {connection.get('ip', '127.0.0.1')}")
    print(f"  Port: {connection.get('port', 8000)}")
    
    # Sample code for transport class initialization
    print("\nExample transport initialization code:")
    print("```")
    print("def initialize_transport(mind_id):")
    print("    # Get connection settings from mind config")
    print("    mind_config = get_mind_by_id(mind_id)")
    print("    connection = mind_config.get('connection', {})")
    print("    ")
    print("    # Use connection settings directly")
    print("    transport = WiFiTransport(")
    print("        ip=connection.get('ip', '127.0.0.1'),")
    print("        port=connection.get('port', 8000)")
    print("    )")
    print("    return transport")
    print("```")

def demonstrate_auto_discovery():
    """
    Demonstrate how the system handles 'auto' connection values
    
    This shows how the system will:
    1. Check for IPs in minds_config.json when 'auto' values are encountered
    2. Try to discover valid connection using prioritized IPs
    3. Update the mind configuration with successful connection details
    """
    print("\n=== Auto-Discovery Demo ===")
    
    # Load minds config to check if any minds still have auto values
    from Mind.mind_config import load_minds_config, save_mind_config, get_mind_by_id
    minds_config = load_minds_config()
    minds = minds_config.get("minds", {})
    
    # Check if any minds still have auto values
    has_auto_values = False
    for mind_id, mind_data in minds.items():
        connection = mind_data.get("connection", {})
        if connection.get("ip") == "auto" or connection.get("port") == "auto":
            has_auto_values = True
            break
    
    if has_auto_values:
        print("Some minds still have 'auto' values in their configuration.")
    else:
        print("All minds have been updated with discovered values!")
        print("This happens automatically when the system successfully connects to a device.")
        
        # Option to restore "auto" values (commented out by default)
        # Uncomment the following lines to restore auto values for demonstration purposes
        '''
        print("\nWould you like to restore 'auto' values for demonstration? [y/N]: ", end="")
        choice = input().strip().lower()
        if choice == 'y':
            # Get the auto mind configuration
            auto_mind = get_mind_by_id("auto")
            
            # Set connection values back to auto
            auto_mind["connection"]["ip"] = "auto"
            auto_mind["connection"]["port"] = "auto"
            
            # Save the updated configuration
            if save_mind_config("auto", auto_mind):
                print("✅ 'auto' values restored for the 'auto' mind!")
                print("Run this script again to see the auto-discovery process.")
            else:
                print("❌ Failed to restore 'auto' values")
        '''
    
    # Import connection-related classes to demonstrate the process
    try:
        from Mind.Subcortex.transport_layer import WiFiTransport
        
        # Create a transport instance with auto settings (for demonstration)
        print("\nDemonstrating WiFiTransport with 'auto' settings...")
        print("(This is a simulation - no actual connection will be attempted)")
        
        print(f"\nDiscovery process explanation:")
        print("1. When 'auto' values are provided, the system will:")
        print("   a. First check all IPs in minds_config.json and try each of them")
        
        # Get actual IP addresses from the minds config
        config_ips = []
        for mind_id, mind_data in minds.items():
            connection = mind_data.get("connection", {})
            ip = connection.get("ip")
            if ip and ip != "auto" and ip not in config_ips:
                config_ips.append(ip)
        
        ip_list = ", ".join(config_ips) if config_ips else "none found"
        print(f"      - Found IP addresses: {ip_list}")
        print("   b. Try common IP addresses like 192.168.1.100, 192.168.0.100, etc.")
        print("   c. Attempt to use local network IP address detection")
        print("   d. If ADB is available, try to discover Android device IPs")
        
        print("\n2. When a connection succeeds:")
        print("   a. The system updates the mind configuration with the successful values")
        print("   b. Future connections will use these values directly")
        
        print("\nThis process ensures that:")
        print("- 'auto' settings work out-of-the-box")
        print("- Once a successful connection is found, it's remembered")
        print("- Different minds can connect to different devices automatically")
        
        # Show the current values from the auto mind
        default_mind = minds.get("auto", {})
        connection = default_mind.get("connection", {})
        print(f"\nCurrent auto mind connection settings (after discovery):")
        print(f"  IP: {connection.get('ip', 'unknown')}")
        print(f"  Port: {connection.get('port', 'unknown')}")
        
        # Quick demo of how auto values are handled in code
        print("\nCode execution with auto values:")
        print("1. When WiFiTransport is initialized with auto values:")
        print("   transport = WiFiTransport(ip='auto', port='auto')")
        print("2. The _discover_local_ip method is called to find valid IPs")
        print("3. The _try_alternative_connections method is called to try connections")
        print("4. When a connection succeeds, the mind config is updated")
        print("5. Future connections reuse the discovered values automatically")
    
    except ImportError as e:
        print(f"Could not import required modules: {e}")
        print("This is just a demonstration - when running the actual system, the modules would be available.")

if __name__ == "__main__":
    # Show examples of both configuration types
    print_system_config_example()
    print_mind_config_example()
    
    # Show all configured minds (penphin, dolphin, penguin)
    print_all_mind_configs()
    
    # Example of combining configurations
    print("\n=== Combined Configuration Example ===")
    combined = get_combined_config()
    print(f"Name: {combined['name']}")
    print(f"Log Level: {combined['log_level']}")
    print(f"LLM Model: {combined['llm_settings']['default_model']}")
    print(f"Connection IP: {combined['connection']['ip']}")
    
    # Example of getting device connection settings
    print("\n=== Device Connection Example ===")
    # Get connection for specific mind (penphin)
    penphin_conn = get_device_connection("penphin")
    print(f"Penphin connection: {penphin_conn}")
    
    # Try dolphin mind
    dolphin_conn = get_device_connection("dolphin")
    print(f"Dolphin connection: {dolphin_conn}")
    
    # Try penguin mind
    penguin_conn = get_device_connection("penguin")
    print(f"Penguin connection: {penguin_conn}")
    
    # Fallback to default mind
    unknown_conn = get_device_connection("unknown_mind")
    print(f"Unknown mind connection (using default): {unknown_conn}")
    
    # Show how to fix the transport layer error
    init_transport_example()
    
    # Demonstrate the auto-discovery process
    demonstrate_auto_discovery() 