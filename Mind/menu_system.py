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
from Interaction.chat_interface import interactive_chat

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
    model_number = input("Enter model number: ").strip()
    
    try:
        model_num = int(model_number)
        if 1 <= model_num < count:
            model = model_dict[model_num]
            model_name = model.get("mode", "")
            model_type = model.get("type", "").lower()
            
            # Check if it's a valid LLM model
            if model_type != "llm":
                print(f"\nWarning: Model '{model_name}' is type '{model_type}', not an LLM model.")
                confirm = input("Use anyway? (y/n): ").strip().lower()
                if confirm != "y":
                    print("Model selection cancelled.")
                    input("Press Enter to continue...")
                    return
            
            # Set as default model
            SynapticPathways.default_llm_model = model_name
            
            # Try to set active model
            success = await SynapticPathways.set_active_model(model_name)
            
            if success:
                print(f"\nSuccessfully set '{model_name}' as the active model.")
            else:
                print(f"\nModel '{model_name}' is selected but setting it active failed.")
                print("It will be used the next time you start a chat.")
            
            input("Press Enter to continue...")
        else:
            print("Invalid model number.")
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
    
    # Check if we have a default LLM model set
    if not SynapticPathways.default_llm_model:
        # Try to get models and set a default
        models = await SynapticPathways.get_available_models()
        journaling_manager.recordInfo(f"Available models: {models}")
        
        if models:
            # Find the first LLM model
            found_llm = False
            for model in models:
                model_name = model.get("mode", "")
                model_type = model.get("type", "").lower()
                
                if model_name and model_type == "llm":
                    SynapticPathways.default_llm_model = model_name
                    journaling_manager.recordInfo(f"Found LLM model, setting default to: {model_name}")
                    print(f"Using LLM model: {model_name}")
                    found_llm = True
                    break
            
            # If no LLM model found, try any model
            if not found_llm:
                for model in models:
                    model_name = model.get("mode", "")
                    if model_name:
                        SynapticPathways.default_llm_model = model_name
                        journaling_manager.recordInfo(f"No LLM found. Using model: {model_name}")
                        print(f"Using model: {model_name} (not an LLM model)")
                        break
        
        if not SynapticPathways.default_llm_model:
            # If still no model, try a common default
            SynapticPathways.default_llm_model = "qwen2.5-0.5b"
            journaling_manager.recordInfo(f"Using default fallback model: {SynapticPathways.default_llm_model}")
            print(f"Using default model: {SynapticPathways.default_llm_model}")
    
    # Log which model we're using
    journaling_manager.recordInfo(f"Attempting to use model: {SynapticPathways.default_llm_model}")
    
    # Initialize LLM with setup command
    llm_work_id = f"llm.{int(time.time())}"
    setup_command = {
        "request_id": f"setup_{int(time.time())}",
        "work_id": llm_work_id,
        "action": "setup",
        "object": "llm.setup",
        "data": {
            "model": SynapticPathways.default_llm_model,
            "response_format": "llm.utf-8", 
            "input": "llm.utf-8", 
            "enoutput": True,
            "enkws": False,
            "max_token_len": 127,
            "prompt": "You are a helpful assistant."
        }
    }
    
    # Send setup command
    print(f"Setting up model: {SynapticPathways.default_llm_model}...")
    setup_response = await SynapticPathways.transmit_json(setup_command)
    journaling_manager.recordInfo(f"LLM setup response: {setup_response}")
    
    if setup_response and setup_response.get("error", {}).get("code", 1) == 0:
        print("LLM initialized successfully.\n")
    else:
        # Try fallback to smallest model if not already using it
        error_msg = setup_response.get("error", {}).get("message", "Unknown error")
        journaling_manager.recordWarning(f"LLM setup error: {error_msg}")
        
        if SynapticPathways.default_llm_model != "qwen2.5-0.5b":
            print(f"First model failed: {error_msg}")
            print("Trying fallback model...\n")
            
            # Update model to smallest one
            SynapticPathways.default_llm_model = "qwen2.5-0.5b"
            setup_command["data"]["model"] = SynapticPathways.default_llm_model
            
            # Try again with fallback model
            setup_response = await SynapticPathways.transmit_json(setup_command)
            
            if setup_response and setup_response.get("error", {}).get("code", 1) == 0:
                print(f"Successfully initialized with fallback model: {SynapticPathways.default_llm_model}\n")
            else:
                error_msg = setup_response.get("error", {}).get("message", "Unknown error")
                print(f"Error initializing LLM: {error_msg}")
                print("\nYou may need to select a different model from the model list menu.")
                print("Press Enter to return to main menu...")
                input()
                return
        else:
            print(f"Error initializing LLM: {error_msg}")
            print("\nYou may need to select a different model from the model list menu.")
            print("Press Enter to return to main menu...")
            input()
            return
    
    # Get existing BasalGanglia instance
    bg = SynapticPathways.get_basal_ganglia()
    
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
        print("0) Back to Main Menu")
        print()
        
        choice = input("Enter your choice (0-4): ").strip()
        
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
                
            else:
                print("\nInvalid choice. Press Enter to continue...")
                input()
                
        except Exception as e:
            print(f"\nError: {e}")
            input("\nPress Enter to continue...")

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