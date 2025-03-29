"""
Menu system for PenphinMind
"""

import os
import asyncio
from typing import Dict, Any, List
import time

from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

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
    clear_screen()
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
    print("3) Reboot")
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
            # Get the model name from the mode field, fallback to model field
            model_name = str(model.get("mode", model.get("model", "Unknown")))
            
            # Get capabilities and format them for display
            capabilities = model.get("capabilities", [])
            capabilities_str = ""
            if capabilities:
                capabilities_str = f" [{', '.join(capabilities)}]"
            
            # Log the individual model data for debugging
            journaling_manager.recordInfo(f"Model data: {model}")
            journaling_manager.recordInfo(f"Extracted model name: {model_name}")
            
            model_dict[count] = model
            print(f"{count}) {model_name}{capabilities_str}")
            count += 1
    
    print("\n0) Return to main menu")
    print()
    
    choice = input("Enter model number for details (0 to return): ")
    
    if not choice or choice == "0":
        return ""
    
    try:
        model_num = int(choice)
        if 1 <= model_num < count:
            await display_model_details(model_dict[model_num])
    except (ValueError, KeyError):
        print("Invalid selection. Press Enter to continue...")
        input()
    
    return ""

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
    
    # Get model identifier
    model_name = str(model.get('mode', model.get('model', "Unknown")))
    
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
    
    # Additional model properties
    size = model.get("size", "")
    version = model.get("version", "")
    
    if size:
        print(f"\nSize: {size}")
    if version:
        print(f"Version: {version}")
    
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
    print("Type 'exit' to return to main menu")
    print("Type 'reset' to reset the LLM\n")
    
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
    
    # Log which model we're using
    journaling_manager.recordInfo(f"Using LLM model: {SynapticPathways.default_llm_model}")
    
    # Send setup command
    print("Initializing LLM...")
    setup_response = await SynapticPathways.transmit_json(setup_command)
    journaling_manager.recordInfo(f"LLM setup response: {setup_response}")
    
    if setup_response and setup_response.get("error", {}).get("code", 1) == 0:
        print("LLM initialized successfully.\n")
    else:
        error_msg = setup_response.get("error", {}).get("message", "Unknown error")
        print(f"Error initializing LLM: {error_msg}")
        print("Press Enter to return to main menu...")
        input()
        return
    
    chat_history = []
    running = True
    
    while running:
        # Get user input
        user_input = input("You: ")
        
        # Check for exit command
        if user_input.lower() in ("exit", "quit", "menu"):
            # Clean up LLM resources before exiting
            exit_command = {
                "request_id": f"exit_{int(time.time())}",
                "work_id": llm_work_id,
                "action": "exit"
            }
            await SynapticPathways.transmit_json(exit_command)
            break
            
        # Check for reset command
        if user_input.lower() == "reset":
            print("\nResetting LLM...")
            
            # First exit current LLM session
            exit_command = {
                "request_id": f"exit_{int(time.time())}",
                "work_id": llm_work_id,
                "action": "exit"
            }
            await SynapticPathways.transmit_json(exit_command)
            
            # Reset the system
            result = await SynapticPathways.clear_and_reset()
            hw_info = SynapticPathways.format_hw_info()
            print(hw_info)
            
            # Reinitialize LLM with new work_id
            llm_work_id = f"llm.{int(time.time())}"
            setup_command["request_id"] = f"setup_{int(time.time())}"
            setup_command["work_id"] = llm_work_id
            
            # Make sure we're using the latest model (in case it changed)
            setup_command["data"]["model"] = SynapticPathways.default_llm_model
            journaling_manager.recordInfo(f"Reinitializing with LLM model: {SynapticPathways.default_llm_model}")
            
            setup_response = await SynapticPathways.transmit_json(setup_command)
            
            print("LLM has been reset.\n")
            continue
        
        if not user_input.strip():
            continue
            
        # Add user message to history
        chat_history.append({"role": "user", "content": user_input})
        
        # Generate LLM response
        print("\nAI: ", end="", flush=True)
        
        try:
            # Create LLM inference command
            inference_command = {
                "request_id": f"inference_{int(time.time())}",
                "work_id": llm_work_id,
                "action": "inference",
                "object": "llm.utf-8",
                "data": {
                    "delta": user_input,
                    "index": 0,
                    "finish": True
                }
            }
            
            # Send inference command
            response = await SynapticPathways.transmit_json(inference_command)
            journaling_manager.recordInfo(f"LLM inference response: {response}")
            
            # Check for errors
            if response and response.get("error", {}).get("code", 1) != 0:
                error_message = response.get("error", {}).get("message", "Unknown error")
                print(f"Error generating response: {error_message}")
                continue
                
            # Extract response
            if "data" in response:
                data = response["data"]
                if isinstance(data, dict) and "delta" in data:
                    # Handle streaming format response
                    ai_response = data.get("delta", "")
                    print(ai_response)
                elif isinstance(data, str):
                    # Handle direct string response
                    ai_response = data
                    print(ai_response)
                else:
                    # Unknown format
                    print("No valid response received.")
                    continue
                
                # Add AI response to history
                chat_history.append({"role": "assistant", "content": ai_response})
            else:
                print("No data in response.")
            
        except Exception as e:
            journaling_manager.recordError(f"Error in chat: {e}")
            print(f"An error occurred: {e}")
            
        print()  # Empty line after response

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
            await reboot_system()
        elif choice == "4":
            print("Exiting PenphinMind...")
            break
        else:
            print("Invalid choice. Press Enter to continue...")
            input()

# Entry point
if __name__ == "__main__":
    asyncio.run(run_menu_system()) 