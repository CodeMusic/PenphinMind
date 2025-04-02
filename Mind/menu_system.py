import os
import asyncio
from typing import Dict, Any, List
import time
import json

from Mind.mind import Mind
from Interaction.chat_interface import interactive_chat
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

# Create global Mind instance
mind = Mind()

def clear_screen():
    """Clear the terminal screen"""
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Unix/Linux/MacOS
        os.system('clear')

def print_header():
    """Print PenphinMind header"""
    print("=" * 60)
    print("                 🐧 PenphinMind 🐬")
    print("=" * 60)
    print()

async def get_current_model_info():
    """Get information about the currently active model"""
    # Use Mind to get active model
    active_model = await mind.get_model()
    
    if active_model and active_model.get("success"):
        if isinstance(active_model["model"], dict):
            return active_model["model"]
        elif isinstance(active_model["model"], str):
            if "details" in active_model:
                return active_model["details"]
            return {"model": active_model["model"], "type": active_model["model"].split("-")[0] if "-" in active_model["model"] else ""}
    
    # If API call fails, use the locally cached model name
    model_name = mind.get_default_model()
    if model_name:
        return {"model": model_name, "type": model_name.split("-")[0] if "-" in model_name else ""}
    
    return {"model": "No model selected", "type": ""}

async def display_main_menu() -> str:
    """Display main menu and get user choice"""
    print_header()
    
    # First establish connection with ping
    result = await mind.ping_system()
    
    # Then get hardware info
    hw_info_result = await mind.get_hardware_info()
    
    # Display hardware info
    hw_info = mind.format_hardware_info()
    print(hw_info)
    print()

async def display_model_list() -> str:
    """Display list of available models and get user choice"""
    clear_screen()
    print_header()
    
    # Refresh hardware info before displaying
    hw_info_result = await mind.get_hardware_info()
    
    # Display hardware info
    hw_info = mind.format_hardware_info()
    print(hw_info)

    # Show current active model if available
    current_model = mind.get_default_model()
    if current_model:
        print(f"\nCurrent active model: {current_model}")

async def reboot_system(mind_instance=None):
    """Reboot the M5Stack system"""
    clear_screen()
    print_header()
    
    # Use the global mind instance if not provided
    mind_instance = mind_instance or mind
    
    print("Rebooting system...")
    
    # Send reboot command
    result = await mind_instance.reboot_device()
    
    if result and result.get("status") == "ok":
        print("Reboot command sent successfully.")
        print("Device will restart. The application will lose connection.")
        print("You may need to restart the application after device reboot.")
        
        # Wait a moment to allow device to reboot
        print("\nWaiting for device to reboot...")
        await asyncio.sleep(5)
        
        # Try to reconnect and get hardware info
        try:
            print("Attempting to reconnect...")
            # Re-initialize the connection through Mind
            reconnect_result = await mind_instance.connect(mind_instance._connection_type)
            
            if reconnect_result:
                # Get updated hardware info
                hw_result = await mind_instance.get_hardware_info()
                print("\nDevice reconnected successfully!")
                print(mind_instance.format_hardware_info())
            else:
                print("\nFailed to reconnect")
        except Exception as e:
            journaling_manager.recordError(f"Error reconnecting after reboot: {e}")
            print("\nCould not reconnect to device after reboot.")
            print("You will need to restart the application manually.")
    else:
        error_msg = result.get("message", "Unknown error") if result else "No response"
        print(f"Reboot failed: {error_msg}")
    
    print("\nPress Enter to return to main menu...")
    input()

# Import interactive_chat here to avoid circular imports

# Start the interactive chat with the existing BasalGanglia instance
async def start_chat(mind_instance=None):
    """Start chat interface with LLM"""
    try:
        # Use the global mind instance if not provided
        mind_instance = mind_instance or mind
        
        # First establish a basic ping connection
        print("Establishing connection...")
        ping_result = await mind_instance.ping_system()
        if not ping_result or ping_result.get("status") != "ok":
            print("Error connecting to hardware. Press Enter to return to main menu...")
            input()
            return
        
        # Now refresh hardware info before displaying
        hw_info_result = await mind_instance.get_hardware_info()
        
        # Directly use the interactive chat interface with Mind
        # The ChatManager inside interactive_chat will handle model selection and setup
        await interactive_chat(mind_instance)
            
    except Exception as e:
        journaling_manager.recordError(f"Error starting chat: {e}")
        import traceback
        journaling_manager.recordError(f"Stack trace: {traceback.format_exc()}")
        print(f"\nError starting chat: {e}")
        input("\nPress Enter to return to main menu...")

async def manage_tasks():
    """Display and manage active tasks"""
    clear_screen()
    print_header()
    
    # Display hardware info
    hw_info_data = await mind.get_hardware_info()
    hw_info = mind.format_hardware_info()
    print(hw_info)
    
    print("\n=== Task Management ===")
    
    # Get task information from Mind's high-level API
    task_info = mind.get_task_status()
    
    # Display task information
    print("\nTasks Overview:")
    print(f"Total tasks: {task_info['total_count']}")
    
    # Show active tasks
    print("\nActive tasks:")
    if task_info['active_tasks']:
        for i, task in enumerate(task_info['active_tasks']):
            task_name = task.get("name", f"Task {i+1}")
            task_type = task.get("type", "Unknown")
            created_time = task.get("created_at", 0)
            
            time_str = "unknown time"
            if created_time:
                age = time.time() - created_time
                time_str = f"{age:.1f} seconds ago"
            
            print(f"  {i+1}. {task_name} (Type: {task_type}, Created: {time_str})")
    else:
        print("  No active tasks")
        
    # Show inactive tasks
    print("\nInactive tasks:")
    if task_info['inactive_tasks']:
        for i, task in enumerate(task_info['inactive_tasks']):
            task_name = task.get("name", f"Task {i+1}")
            task_type = task.get("type", "Unknown")
            
            print(f"  {i+1}. {task_name} (Type: {task_type})")
    else:
        print("  No inactive tasks")
    
    # Display device resource usage (indirect way to see task load)
    print("\nDevice Resource Usage:")
    hw_info = await mind.get_hardware_info()
    hw_data = hw_info.get("response", {}) if hw_info and isinstance(hw_info, dict) else {}
    
    cpu_load = hw_data.get("cpu_loadavg", "N/A")
    mem_usage = hw_data.get("mem", "N/A")
    temp = hw_data.get("temperature", "N/A")
    
    print(f"  CPU Load: {cpu_load}%")
    print(f"  Memory Usage: {mem_usage}%")
    if temp and temp != "N/A":
        temp_val = f"{temp:.1f}°C" if isinstance(temp, (int, float)) else temp
        print(f"  Temperature: {temp_val}")
    
    # Options for task management
    print("\nTask Management Options:")
    print("1) Refresh task information")
    print("2) Reset LLM system")
    print("0) Back to System Menu")
    
    option = input("\nEnter option: ").strip()
    
    if option == "1":
        # Just refresh by calling this function again
        await manage_tasks()
    elif option == "2":
        # Reset LLM
        print("\nResetting LLM system...")
        result = await mind.reset_system()
        reset_success = result.get("status") == "ok"
        print(f"Reset {'successful' if reset_success else 'failed'}")
        if not reset_success:
            print(f"Error: {result.get('message', 'Unknown error')}")
        input("\nPress Enter to continue...")
    else:
        # Any other input returns to system menu
        return 