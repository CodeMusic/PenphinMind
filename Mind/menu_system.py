"""
Menu system for PenphinMind
"""

import os
import asyncio
from typing import Dict, Any, List
import time
import json

from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.mind import setup_connection
# from Interaction.chat_interface import interactive_chat  # This causes circular import

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

def clear_screen():
    """Clear the terminal screen"""
    pass
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Unix/Linux/MacOS
        os.system('clear')

def print_header():
    """Print PenphinMind header"""
    print("=" * 60)
    print("                     PenphinMind")
    print("=" * 60)
    print()

async def get_current_model_info():
    """Get information about the current active model"""
    active_model = await SynapticPathways.get_active_model()
    
    if active_model["success"]:
        if isinstance(active_model["model"], dict):
            return active_model["model"]
        elif isinstance(active_model["model"], str):
            if "details" in active_model:
                return active_model["details"]
            return {"model": active_model["model"], "type": active_model["model"].split("-")[0] if "-" in active_model["model"] else ""}
    
    return {"model": "No model selected", "type": ""}

async def display_main_menu() -> str:
    """Display main menu and get user choice"""
    print_header()
    
    # Refresh hardware info before displaying
    await SynapticPathways.get_hardware_info()
    
    # Display hardware info
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    print()
    
    print("Main Menu:")
    print("1) Chat")
    print("2) Information")
    print("3) System")
    print("4) Exit")
    print()
    
    choice = input("Enter your choice (1-4): ")
    return choice.strip()

async def display_model_list() -> str:
    """Display list of available models and get user choice"""
    clear_screen()
    print_header()
    
    # Refresh hardware info before displaying
    await SynapticPathways.get_hardware_info()
    
    # Display hardware info
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    
    print("\nAvailable Models:")
    print("----------------")
    
    # Get and display models - use cached models when available
    models = await SynapticPathways.get_available_models()
    
    # Log the models for debugging
    using_cached = len(SynapticPathways.available_models) > 0
    journaling_manager.recordInfo(f"Retrieved models (cached: {using_cached}): {models}")
    
    if using_cached:
        print(f"[Using cached model information - {len(models)} models available]")
    
    if not models:
        print("No models available or failed to retrieve model information.")
        print("Press Enter to return to main menu...")
        input()
        return ""
    
    # Show current active model if available
    current_model = SynapticPathways.default_llm_model
    if current_model:
        print(f"\nCurrent active model: {current_model}")
    
    # Build a list of models to display
    model_dict = {}
    count = 1
    
    # Group models by type
    model_types = {}
    for model in models:
        model_type = model.get("type", "unknown")
        if model_type not in model_types:
            model_types[model_type] = []
        model_types[model_type].append(model)
    
    # Display models by type
    for model_type, type_models in model_types.items():
        print(f"\n{model_type.upper()} Models:")
        for model in type_models:
            # Get the model name from the mode field (original API field)
            model_name = model.get("mode", "Unknown")
            
            # Get capabilities and format them for display
            capabilities = model.get("capabilities", [])
            capabilities_str = ""
            if capabilities:
                capabilities_str = f" [{', '.join(capabilities)}]"
            
            # Mark current active model
            active_marker = " ✓" if model_name == current_model else ""
            
            # Log the individual model data for debugging
            journaling_manager.recordInfo(f"Model data: {model}")
            journaling_manager.recordInfo(f"Using model name from 'mode' field: {model_name}")
            
            model_dict[count] = model
            print(f"{count}) {model_name}{capabilities_str}{active_marker}")
            count += 1
    
    print("\nOptions:")
    print("S) Select a model for chat")
    print("0) Return to main menu")
    print()
    
    choice = input("Enter model number, S to select a model, or 0 to return: ").strip()
    
    if not choice or choice == "0":
        return ""
    
    # Handle model selection
    if choice.lower() == "s":
        await select_model_for_chat(model_dict, count)
        return ""
    
    try:
        model_num = int(choice)
        if 1 <= model_num < count:
            await display_model_details(model_dict[model_num])
    except (ValueError, KeyError):
        print("Invalid selection. Press Enter to continue...")
        input()
    
    return ""

async def select_model_for_chat(model_dict, count):
    """Select a model for chat from the available models"""
    print("\nSelect a model for chat:")
    
    # First, show only LLM models for easier selection
    print("\nLLM Models (recommended):")
    llm_options = {}
    option_count = 1
    
    # Find and display LLM models first
    for idx, model in model_dict.items():
        model_name = model.get("mode", "")
        model_type = model.get("type", "").lower()
        
        if model_type == "llm":
            llm_options[option_count] = idx
            print(f"{option_count}) {model_name}")
            option_count += 1
    
    # If no LLM models found, show a message
    if not llm_options:
        print("  No dedicated LLM models found.")
    
    print("\nOther Models (may not work for chat):")
    for idx, model in model_dict.items():
        model_name = model.get("mode", "")
        model_type = model.get("type", "").lower()
        
        if model_type != "llm":
            llm_options[option_count] = idx
            print(f"{option_count}) {model_name} (Type: {model_type})")
            option_count += 1
    
    print("\n0) Cancel")
    
    # Get user choice
    model_option = input("\nEnter option number: ").strip()
    
    # Handle cancel
    if model_option == "0":
        print("Model selection cancelled.")
        input("Press Enter to continue...")
        return
    
    try:
        option_num = int(model_option)
        if 1 <= option_num < option_count:
            # Get the actual model index from our mapping
            model_idx = llm_options[option_num]
            model = model_dict[model_idx]
            
            model_name = model.get("mode", "")
            model_type = model.get("type", "").lower()
            
            # Warn if not an LLM
            if model_type != "llm":
                print(f"\nWarning: Model '{model_name}' is type '{model_type}', not an LLM model.")
                print("It may not work properly for chat.")
                confirm = input("Use anyway? (y/n): ").strip().lower()
                if confirm != "y":
                    print("Model selection cancelled.")
                    input("Press Enter to continue...")
                    return
            
            # Set as default model
            SynapticPathways.default_llm_model = model_name
            print(f"\nSelected '{model_name}' as the active model.")
            
            # Try to also set it on the device
            try:
                success = await SynapticPathways.set_active_model(model_name)
                if success:
                    print("Model activated successfully on the device.")
            except Exception as e:
                journaling_manager.recordError(f"Error setting active model: {e}")
                print("Note: Model will be activated when you start the chat.")
            
            input("Press Enter to continue...")
        else:
            print("Invalid option number.")
            input("Press Enter to continue...")
    except (ValueError, KeyError):
        print("Invalid selection.")
        input("Press Enter to continue...")

async def display_model_details(model: Dict[str, Any]):
    """Display detailed information about a specific model"""
    clear_screen()
    print_header()
    
    # Refresh hardware info before displaying
    await SynapticPathways.get_hardware_info()
    
    # Display hardware info
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    print()
    
    # Log the model data for debugging
    journaling_manager.recordInfo(f"Displaying details for model: {model}")
    print("[Using cached model information]")
    print()
    
    # Get model identifier from the mode field (original API field)
    model_name = model.get('mode', "Unknown")
    
    print("Model Details:")
    print("-------------")
    print(f"Name: {model_name}")
    print(f"Type: {model.get('type', '')}")
    
    # Display capabilities
    capabilities = model.get("capabilities", [])
    if capabilities:
        print("\nCapabilities:")
        for cap in capabilities:
            print(f"- {cap}")
    
    # Display input/output types
    print("\nInput Types:")
    input_types = model.get("input_type", [])
    if isinstance(input_types, list):
        for inp in input_types:
            print(f"- {inp}")
    else:
        print(f"- {input_types}")
    
    print("\nOutput Types:")
    output_types = model.get("output_type", [])
    if isinstance(output_types, list):
        for out in output_types:
            print(f"- {out}")
    else:
        print(f"- {output_types}")
    
    # Display mode parameters if available
    mode_params = model.get("mode_param", {})
    if mode_params:
        print("\nParameters:")
        for param_name, param_value in mode_params.items():
            print(f"- {param_name}: {param_value}")
    
    print("\nPress Enter to return to model list...")
    input()

async def reboot_system():
    """Reboot the M5Stack system"""
    clear_screen()
    print_header()
    
    print("Rebooting system...")
    
    result = await SynapticPathways.reboot_device()
    
    if result["success"]:
        print("Reboot command sent successfully.")
        print("Device will restart. The application will lose connection.")
        print("You may need to restart the application after device reboot.")
        
        # Wait a moment to allow device to reboot
        print("\nWaiting for device to reboot...")
        await asyncio.sleep(5)
        
        # Try to reconnect and get hardware info
        try:
            print("Attempting to reconnect...")
            # Re-initialize the connection
            await SynapticPathways.initialize()
            
            # Get updated hardware info
            hw_info = await SynapticPathways.get_hardware_info()
            print("\nDevice reconnected successfully!")
            print(SynapticPathways.format_hw_info())
        except Exception as e:
            journaling_manager.recordError(f"Error reconnecting after reboot: {e}")
            print("\nCould not reconnect to device after reboot.")
            print("You will need to restart the application manually.")
    else:
        print(f"Reboot failed: {result.get('message', 'Unknown error')}")
    
    print("\nPress Enter to return to main menu...")
    input()

async def start_chat():
    """Start chat interface with LLM"""
    clear_screen()
    print_header()
    
    # Refresh hardware info before displaying
    await SynapticPathways.get_hardware_info()
    
    # Display hardware info at the top of chat
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    
    print("\nWelcome to PenphinMind Chat\n")
    print("🔧 Initializing thought loop...\n")
    
    # Initialize LLM with setup command
    llm_work_id = f"llm.{int(time.time())}"
    
    # Get the model from SynapticPathways
    model_name = SynapticPathways.default_llm_model
    
    # If no model selected, try to find one
    if not model_name:
        models = await SynapticPathways.get_available_models()
        journaling_manager.recordInfo(f"Available models: {models}")
        
        if models:
            # IMPORTANT: First filter for only LLM models
            llm_models = [m for m in models if m.get("type", "").lower() == "llm"]
            journaling_manager.recordInfo(f"Found {len(llm_models)} LLM models: {llm_models}")
            
            if llm_models:
                # First try to find small LLM models
                for model in llm_models:
                    model_mode = model.get("mode", "")
                    if "0.5b" in model_mode or "tiny" in model_mode:
                        model_name = model_mode
                        journaling_manager.recordInfo(f"Selected small LLM model: {model_name}")
                        break
                
                # If no small model found, use the first LLM model
                if not model_name:
                    model_name = llm_models[0].get("mode", "")
                    journaling_manager.recordInfo(f"Selected first available LLM model: {model_name}")
            else:
                # No LLM models found, log this problem
                journaling_manager.recordWarning("No models with type 'llm' found. Trying any model.")
                
                # Then try non-LLM models with small size
                for model in models:
                    model_mode = model.get("mode", "")
                    if "0.5b" in model_mode or "tiny" in model_mode:
                        model_name = model_mode
                        journaling_manager.recordInfo(f"No LLM models found. Using small model: {model_name}")
                        break
                
                # If still no model, use the first one
                if not model_name and models:
                    model_name = models[0].get("mode", "")
                    journaling_manager.recordInfo(f"Using first available model (not LLM): {model_name}")
        
        # If still no model, use a fallback
        if not model_name:
            model_name = "qwen2.5-0.5b"
            journaling_manager.recordInfo(f"No suitable models found. Using default: {model_name}")
        
        # Set as default
        SynapticPathways.default_llm_model = model_name
    
    # Set up the model
    setup_command = {
        "request_id": f"setup_{int(time.time())}",
        "work_id": llm_work_id,
        "action": "setup",
        "object": "llm.setup",
        "data": {
            "model": model_name,
            "response_format": "llm.utf-8", 
            "input": "llm.utf-8", 
            "enoutput": True,
            "enkws": False,
            "max_token_len": 127,
            "prompt": "You are a helpful assistant."
        }
    }
    
    # Log which model we're using
    journaling_manager.recordInfo(f"Using model: {model_name}")
    print(f"Setting up model: {model_name}...")
    
    # Send setup command
    setup_response = await SynapticPathways.transmit_json(setup_command)
    
    if setup_response and setup_response.get("error", {}).get("code", 1) == 0:
        print("LLM initialized successfully.\n")
    else:
        error_msg = setup_response.get("error", {}).get("message", "Unknown error")
        print(f"Error initializing LLM: {error_msg}")
        
        # Only try alternative models if the error indicates a model issue
        model_error = "model" in error_msg.lower() or "failed" in error_msg.lower()
        if model_error:
            print("\nTrying to find an alternative model...")
            
            # Get available models again
            models = await SynapticPathways.get_available_models()
            llm_models = [m for m in models if m.get("type", "").lower() == "llm"]
            
            # Try different models
            for alt_model in llm_models:
                alt_name = alt_model.get("mode", "")
                if alt_name != model_name:  # Skip the one that just failed
                    print(f"Trying model: {alt_name}...")
                    setup_command["data"]["model"] = alt_name
                    alt_response = await SynapticPathways.transmit_json(setup_command)
                    
                    if alt_response and alt_response.get("error", {}).get("code", 1) == 0:
                        print(f"Successfully initialized with model: {alt_name}\n")
                        SynapticPathways.default_llm_model = alt_name  # Update default
                        model_name = alt_name
                        break
            else:
                print("All LLM models failed. Please try again later or select a different model.")
                print("\nPress Enter to return to main menu...")
                input()
                return
        else:
            # Ask if user wants to try reset
            print("\nWould you like to try resetting the LLM system? (y/n)")
            choice = input().strip().lower()
            
            if choice == 'y':
                print("\nResetting LLM system...")
                await SynapticPathways.reset_llm()
                
                # Try one more time
                print("\nRetrying initialization...")
                setup_response = await SynapticPathways.transmit_json(setup_command)
                
                if setup_response and setup_response.get("error", {}).get("code", 1) == 0:
                    print("LLM initialized successfully after reset.\n")
                else:
                    error_msg = setup_response.get("error", {}).get("message", "Unknown error")
                    print(f"Error initializing LLM after reset: {error_msg}")
                    print("\nPress Enter to return to main menu...")
                    input()
                    return
            else:
                print("\nPress Enter to return to main menu...")
                input()
                return
    
    # Get existing BasalGanglia instance
    bg = SynapticPathways.get_basal_ganglia()
    
    # Import interactive_chat here to avoid circular imports
    from Interaction.chat_interface import interactive_chat
    
    # Start the interactive chat with the existing BasalGanglia instance
    await interactive_chat(bg)

async def system_menu() -> None:
    """Display and handle system menu options"""
    while True:
        clear_screen()
        print_header()
        
        # Display hardware info
        hw_info = SynapticPathways.format_hw_info()
        print(hw_info)
        print()
        
        print("System Menu:")
        print("1) Hardware Info")
        print("2) List Models")
        print("3) Ping System")
        print("4) Reboot Device")
        print("5) Manage Tasks")  # New option
        print("0) Back to Main Menu")
        print()
        
        choice = input("Enter your choice (0-5): ").strip()
        
        try:
            if choice == "0":
                return
            elif choice == "1":
                # Hardware Info
                hw_info = await SynapticPathways.get_hardware_info()
                print("\n=== Hardware Information ===")
                print(json.dumps(hw_info, indent=2))
                input("\nPress Enter to continue...")
                
            elif choice == "2":
                # List Models
                models = await SynapticPathways.get_available_models()
                print("\n=== Available Models ===")
                print(json.dumps(models, indent=2))
                input("\nPress Enter to continue...")
                
            elif choice == "3":
                # Ping System
                print("\nPinging system...")
                result = await SynapticPathways.ping_system()
                print(f"Ping {'successful' if result else 'failed'}")
                input("\nPress Enter to continue...")
                
            elif choice == "4":
                # Reboot (using existing reboot_system function)
                await reboot_system()
                
            elif choice == "5":
                # New option: Manage Tasks
                await manage_tasks()
                
            else:
                print("\nInvalid choice. Press Enter to continue...")
                input()
                
        except Exception as e:
            print(f"\nError: {e}")
            input("\nPress Enter to continue...")

async def manage_tasks():
    """Display and manage active tasks"""
    clear_screen()
    print_header()
    
    # Display hardware info
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    
    print("\n=== Task Management ===")
    
    # Get BasalGanglia instance to examine tasks
    from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
    bg = SynapticPathways.get_basal_ganglia()
    
    # Display local tasks
    print("\nLocal Tasks:")
    
    # Handle both BasalGanglia and BasalGangliaIntegration types
    if hasattr(bg, "_tasks"):
        # BasalGangliaIntegration has _tasks dict
        tasks = list(bg._tasks.values())
        print(f"Total tasks: {len(tasks)}")
        
        # Group tasks by active status
        active_tasks = [t for t in tasks if hasattr(t, "active") and t.active]
        inactive_tasks = [t for t in tasks if hasattr(t, "active") and not t.active]
        
        # Show active tasks
        print("\nActive tasks:")
        if active_tasks:
            for i, task in enumerate(active_tasks):
                task_name = getattr(task, "name", f"Task {i+1}")
                task_type = getattr(task, "task_type", "Unknown")
                created_time = getattr(task, "creation_time", None)
                
                time_str = "unknown time"
                if created_time and isinstance(created_time, (int, float)):
                    age = time.time() - created_time
                    time_str = f"{age:.1f} seconds ago"
                
                print(f"  {i+1}. {task_name} (Type: {task_type}, Created: {time_str})")
        else:
            print("  No active tasks")
            
        # Show inactive tasks
        print("\nInactive tasks:")
        if inactive_tasks:
            for i, task in enumerate(inactive_tasks):
                task_name = getattr(task, "name", f"Task {i+1}")
                task_type = getattr(task, "task_type", "Unknown")
                
                print(f"  {i+1}. {task_name} (Type: {task_type})")
        else:
            print("  No inactive tasks")
            
    elif hasattr(bg, "task_queue"):
        # Original BasalGanglia has task_queue list
        tasks = bg.task_queue
        print(f"Total tasks: {len(tasks)}")
        
        # Group tasks by active status
        active_tasks = [t for t in tasks if hasattr(t, "active") and t.active]
        inactive_tasks = [t for t in tasks if hasattr(t, "active") and not t.active]
        
        # Show active tasks
        print("\nActive tasks:")
        if active_tasks:
            for i, task in enumerate(active_tasks):
                task_name = getattr(task, "name", f"Task {i+1}")
                task_priority = getattr(task, "priority", "Unknown")
                created_time = getattr(task, "creation_time", None)
                
                time_str = "unknown time"
                if created_time and isinstance(created_time, (int, float)):
                    age = time.time() - created_time
                    time_str = f"{age:.1f} seconds ago"
                
                print(f"  {i+1}. {task_name} (Priority: {task_priority}, Created: {time_str})")
        else:
            print("  No active tasks")
            
        # Show inactive tasks
        print("\nInactive tasks:")
        if inactive_tasks:
            for i, task in enumerate(inactive_tasks):
                task_name = getattr(task, "name", f"Task {i+1}")
                task_priority = getattr(task, "priority", "Unknown")
                completed = "Yes" if hasattr(task, "has_completed") and task.has_completed() else "No"
                
                print(f"  {i+1}. {task_name} (Priority: {task_priority}, Completed: {completed})")
        else:
            print("  No inactive tasks")
    else:
        print("  No task information available for this brain type")
    
    # Display device resource usage (indirect way to see task load)
    print("\nDevice Resource Usage:")
    await SynapticPathways.get_hardware_info()  # Refresh hardware info
    hw_info = SynapticPathways.current_hw_info
    
    cpu_load = hw_info.get("cpu_loadavg", "N/A")
    mem_usage = hw_info.get("mem", "N/A")
    temp = hw_info.get("temperature", "N/A")
    
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
        result = await SynapticPathways.reset_llm()
        print(f"Reset result: {result}")
        input("\nPress Enter to continue...")
    else:
        # Any other input returns to system menu
        return

async def run_menu_system(mind=None):
    """Run the main menu system
    
    Args:
        mind: Optional Mind instance for additional functionality
    """
    while True:
        choice = await display_main_menu()
        
        if choice == "1":
            await start_chat()
        elif choice == "2":
            await display_model_list()
        elif choice == "3":
            await system_menu()
        elif choice == "4":
            print("Exiting PenphinMind...")
            break
        else:
            print("Invalid choice. Press Enter to continue...")
            input()

async def initialize_system(connection_type=None):
    """Initialize the system with the specified connection type"""
    await setup_connection(connection_type)

# Entry point
if __name__ == "__main__":
    asyncio.run(run_menu_system()) 