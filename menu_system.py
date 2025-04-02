"""
Menu system for PenphinMind
"""

import os
import asyncio
from typing import Dict, Any, List
import time
import json

from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.mind import Mind
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
# from Interaction.chat_interface import interactive_chat  # This causes circular import

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

# Create global Mind instance
mind = Mind()

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
    # Use Mind interface to get active model
    active_model = await mind.get_model()
    
    if active_model and active_model.get("status") == "ok":
        model_info = active_model.get("response", {})
        if isinstance(model_info, dict):
            return model_info
        elif isinstance(model_info, str):
            return {"model": model_info, "type": model_info.split("-")[0] if "-" in model_info else ""}
    
    return {"model": "No model selected", "type": ""}

async def display_main_menu() -> str:
    """Display main menu and get user choice"""
    print_header()
    
    # First establish connection with ping
    result = await mind.ping_system()
    
    # Then get hardware info
    hw_info_result = await mind.get_hardware_info()
    
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
    hw_info_result = await mind.get_hardware_info()
    
    # Display hardware info
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    
    print("\nAvailable Models:")
    print("----------------")
    
    # Get and display models using Mind
    models_result = await mind.list_models()
    models = models_result.get("response", []) if models_result.get("status") == "ok" else []
    
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
                result = await mind.set_model(model_name)
                if result.get("status") == "ok":
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

async def reboot_system(mind_instance=None):
    """Reboot the M5Stack system"""
    clear_screen()
    print_header()
    
    # Use the global mind instance if not provided
    mind_instance = mind_instance or mind
    
    print("Rebooting system...")
    
    result = await mind_instance.reboot_device()
    
    if result.get("status") == "ok":
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
                print(SynapticPathways.format_hw_info())
            else:
                print("\nFailed to reconnect")
        except Exception as e:
            journaling_manager.recordError(f"Error reconnecting after reboot: {e}")
            print("\nCould not reconnect to device after reboot.")
            print("You will need to restart the application manually.")
    else:
        error_msg = result.get("message", "Unknown error")
        print(f"Reboot failed: {error_msg}")
    
    print("\nPress Enter to return to main menu...")
    input()

async def start_chat(mind_instance=None):
    """Start chat interface with LLM"""
    clear_screen()
    print_header()
    
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
    
    # Display hardware info at the top of chat
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    
    print("\nWelcome to PenphinMind Chat\n")
    print("🔧 Initializing thought loop...\n")
    
    # Get the model from SynapticPathways
    model_name = SynapticPathways.default_llm_model
    
    # If no model selected, try to find one
    if not model_name:
        # Get models through Mind
        models_result = await mind_instance.list_models()
        models = models_result.get("response", []) if models_result.get("status") == "ok" else []
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
    
    # Log which model we're using
    journaling_manager.recordInfo(f"Using model: {model_name}")
    print(f"Setting up model: {model_name}...")
    
    # Set up the model using Mind
    setup_result = await mind_instance.set_model(model_name)
    
    if setup_result.get("status") == "ok":
        print("LLM initialized successfully.\n")
    else:
        error_msg = setup_result.get("message", "Unknown error")
        print(f"Error initializing LLM: {error_msg}")
        
        # Only try alternative models if the error indicates a model issue
        model_error = isinstance(error_msg, str) and ("model" in error_msg.lower() or "failed" in error_msg.lower())
        if model_error:
            print("\nTrying to find an alternative model...")
            
            # Get available models again through Mind
            models_result = await mind_instance.list_models()
            models = models_result.get("response", []) if models_result.get("status") == "ok" else []
            llm_models = [m for m in models if m.get("type", "").lower() == "llm"]
            
            # Try different models
            for alt_model in llm_models:
                alt_name = alt_model.get("mode", "")
                if alt_name != model_name:  # Skip the one that just failed
                    print(f"Trying model: {alt_name}...")
                    alt_result = await mind_instance.set_model(alt_name)
                    
                    if alt_result.get("status") == "ok":
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
                
                # Use Mind for reset
                reset_result = await mind_instance.reset_system()
                
                # Check reset result
                if reset_result.get("status") == "ok":
                    print("LLM reset successful")
                else:
                    error_msg = reset_result.get("message", "Unknown error")
                    print(f"Reset error: {error_msg}")
                
                # Try one more time
                print("\nRetrying initialization...")
                retry_result = await mind_instance.set_model(model_name)
                
                if retry_result.get("status") == "ok":
                    print("LLM initialized successfully after reset.\n")
                else:
                    error_msg = retry_result.get("message", "Unknown error")
                    print(f"Error initializing LLM after reset: {error_msg}")
                    print("\nPress Enter to return to main menu...")
                    input()
                    return
            else:
                print("\nPress Enter to return to main menu...")
                input()
                return
    
    # Import interactive_chat here to avoid circular imports
    from Interaction.chat_interface import interactive_chat
    
    # Start interactive chat with the Mind instance (no direct BasalGanglia access)
    await interactive_chat(mind_instance)

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
                hw_info_data = await mind.get_hardware_info()
                print("\n=== Hardware Information ===")
                print(json.dumps(hw_info_data, indent=2))
                input("\nPress Enter to continue...")
                
            elif choice == "2":
                # List Models
                models = await mind.list_models()
                print("\n=== Available Models ===")
                print(json.dumps(models, indent=2))
                input("\nPress Enter to continue...")
                
            elif choice == "3":
                # Ping System
                print("\nPinging system...")
                result = await mind.ping_system()
                ping_success = result and result.get("success", False)
                print(f"Ping {'successful' if ping_success else 'failed'}")
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
    
    # Use the global mind instance
    
    # Display hardware info
    hw_info_data = await mind.get_hardware_info()
    hw_info = SynapticPathways.format_hw_info()
    print(hw_info)
    
    print("\n=== Task Management ===")
    
    # Get task status information using Mind interface
    task_info = mind.get_task_status()
    
    # Display local tasks
    print("\nLocal Tasks:")
    print(f"Total tasks: {task_info['total_count']}")
    
    # Show active tasks
    print("\nActive tasks:")
    if task_info['active_tasks']:
        for i, task in enumerate(task_info['active_tasks']):
            task_name = task.get("name", f"Task {i+1}")
            task_type = task.get("type", "Unknown")
            created_time = task.get("created_at", None)
            
            time_str = "unknown time"
            if created_time and isinstance(created_time, (int, float)):
                age = time.time() - created_time
                time_str = f"{age:.1f} seconds ago"
            
            priority = task.get("priority", "Unknown")
            print(f"  {i+1}. {task_name} (Type: {task_type}, Priority: {priority}, Created: {time_str})")
    else:
        print("  No active tasks")
        
    # Show inactive tasks
    print("\nInactive tasks:")
    if task_info['inactive_tasks']:
        for i, task in enumerate(task_info['inactive_tasks']):
            task_name = task.get("name", f"Task {i+1}")
            task_type = task.get("type", "Unknown")
            priority = task.get("priority", "Unknown")
            
            print(f"  {i+1}. {task_name} (Type: {task_type}, Priority: {priority})")
    else:
        print("  No inactive tasks")
    
    # Display device resource usage (indirect way to see task load)
    print("\nDevice Resource Usage:")
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
        result = await mind.reset_system()
        reset_success = result.get("status") == "ok"
        print(f"Reset {'successful' if reset_success else 'failed'}")
        if not reset_success:
            print(f"Error: {result.get('message', 'Unknown error')}")
        input("\nPress Enter to continue...")
    else:
        # Any other input returns to system menu
        return

async def initialize_system(connection_type=None):
    """Initialize the system with the specified connection type"""
    # Set up the connection using the global mind instance
    result = await mind.connect(connection_type)
    if result:
        journaling_manager.recordInfo(f"System initialized with connection type: {connection_type}")
    else:
        journaling_manager.recordError(f"Failed to initialize system with connection type: {connection_type}")
    return result

async def run_menu_system(mind_instance=None):
    """Run the interactive menu system"""
    try:
        # Use global mind instance if not provided
        mind_instance = mind_instance or mind
        
        # Display the main menu and handle user choices
        while True:
            clear_screen()
            
            # Get main menu choice
            choice = await display_main_menu()
            
            if choice == "1":  # Chat
                await start_chat(mind_instance)
            elif choice == "2":  # Information
                await display_model_list()
            elif choice == "3":  # System
                await system_menu()
            elif choice == "4":  # Exit
                print("\nExiting PenphinMind menu system...")
                break
            else:
                print("\nInvalid choice. Please try again.")
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        print("\nMenu system interrupted.")
    except Exception as e:
        journaling_manager.recordError(f"Error in menu system: {e}")
        print(f"\nAn error occurred: {e}")
        import traceback
        journaling_manager.recordError(traceback.format_exc())

# Entry point
if __name__ == "__main__":
    asyncio.run(run_menu_system()) 