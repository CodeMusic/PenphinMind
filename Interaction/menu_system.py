"""
PenphinMind Menu System
Handles all menu interactions and command routing through Mind's public interface
"""

from typing import Optional, Dict, Any
import asyncio
import os

from Mind.mind import Mind
from .chat_interface import interactive_chat
from Mind.FrontalLobe.PrefrontalCortex.system_journaling_manager import journaling_manager
from config import Config  # Import Config class instead of load_config

def print_header():
    """Print PenphinMind header"""
    print("\n" + "=" * 50)
    print("🐧🐬 PenphinMind System")
    print("=" * 50 + "\n")

async def display_main_menu(mind_instance: Mind) -> str:
    """Display main menu and get user choice"""
    print_header()
    
    # Get hardware info through Mind's public interface
    hw_info_result = await mind_instance.get_hardware_info()
    if hw_info_result.get("status") == "ok":
        print(hw_info_result.get("hardware_info", "Hardware info unavailable"))
    print()
    
    print("Main Menu:")
    print("1) Chat")
    print("2) Information")
    print("3) System")
    print("4) Exit")
    print()
    
    choice = input("Enter your choice (1-4): ")
    return choice.strip()

async def display_mind_selection() -> Mind:
    """Display available minds and get user selection"""
    # Use Mind.mind_config directly instead of config approach
    from Mind.mind_config import load_minds_config, get_available_minds
    
    minds_config = load_minds_config()
    minds = minds_config.get("minds", {})
    
    print("\nAvailable Minds:")
    print("1) Auto-detect Mind")
    
    # List configured minds
    mind_options = list(minds.keys())
    for i, mind_id in enumerate(mind_options, 2):  # Start from 2
        if mind_id == "auto":
            continue  # Skip auto as it's already listed
        mind_cfg = minds[mind_id]
        print(f"{i-1}) {mind_cfg['name']} [{mind_cfg['device_id']}] - {mind_cfg['connection']['ip']}")
    
    while True:
        try:
            choice = input(f"\nSelect mind (1-{len(mind_options)}): ").strip()
            if choice == "1":
                return Mind()  # Auto-detect
            
            choice_num = int(choice)
            if 2 <= choice_num <= len(mind_options)+1:
                mind_id = mind_options[choice_num - 2]
                return Mind(mind_id)
        except ValueError:
            pass
        print("Invalid selection, try again")

async def display_system_info(mind: Mind):
    """Display system information"""
    print("\nSystem Information:")
    print("-" * 30)
    
    # Get hardware info
    hw_info = await mind.get_hardware_info()
    if hw_info.get("status") == "ok":
        print(hw_info.get("hardware_info"))
    else:
        print("❌ Hardware info unavailable")
        
    # Get model info
    model_info = await mind.execute_operation("list_models")
    if model_info.get("status") == "ok":
        print("\nAvailable Models:")
        models = model_info.get("models", [])
        for model in models:
            print(f"- {model.get('name')} ({model.get('type')})")
    else:
        print("\n❌ Model info unavailable")
        
    input("\nPress Enter to continue...")

async def system_menu(mind: Mind):
    """System management menu"""
    while True:
        print("\nSystem Menu:")
        print("1) Reset LLM")
        print("2) Reboot Device")
        print("3) View Logs")
        print("4) Back to Main Menu")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            print("\nResetting LLM system...")
            result = await mind.reset_system()
            print("Reset " + ("successful" if result.get("status") == "ok" else "failed"))
            input("\nPress Enter to continue...")
            
        elif choice == "2":
            confirm = input("\nAre you sure you want to reboot? (y/N): ").strip().lower()
            if confirm == 'y':
                print("\nRebooting device...")
                result = await mind.execute_operation("reboot")
                print("Reboot command " + ("sent" if result.get("status") == "ok" else "failed"))
                input("\nPress Enter to continue...")
                
        elif choice == "3":
            # View last 20 lines of log
            try:
                with open("penphin.log", "r") as f:
                    lines = f.readlines()
                    print("\nRecent Logs:")
                    print("-" * 50)
                    for line in lines[-20:]:
                        print(line.strip())
            except Exception as e:
                print(f"\nError reading logs: {e}")
            input("\nPress Enter to continue...")
            
        elif choice == "4":
            break

async def start_chat(mind: Mind):
    """Start chat interface"""
    try:
        # Initialize chat
        print("\nInitializing chat system...")
        
        # Check connection
        ping_result = await mind.execute_operation("ping")
        if ping_result.get("status") != "ok":
            print("Error: Could not establish connection")
            input("\nPress Enter to continue...")
            return
            
        # Start interactive chat
        await interactive_chat(mind)
        
    except Exception as e:
        journaling_manager.recordError(f"Chat error: {e}")
        print(f"\nError: {e}")
        input("\nPress Enter to continue...")

async def run_menu_system():
    """Main menu system entry point"""
    try:
        # Get initial mind selection
        primary_mind = await display_mind_selection()
        
        while True:
            choice = await display_main_menu(primary_mind)
            
            if choice == "1":  # Chat
                await start_chat(primary_mind)
            elif choice == "2":  # Information
                await display_system_info(primary_mind)
            elif choice == "3":  # System
                await system_menu(primary_mind)
            elif choice == "4":  # Exit
                print("\nExiting PenphinMind system...")
                break
            else:
                print("\nInvalid choice. Please try again.")
                await asyncio.sleep(1)
                
    except Exception as e:
        journaling_manager.recordError(f"Menu system error: {e}")
        print(f"\nMenu system error: {e}") 