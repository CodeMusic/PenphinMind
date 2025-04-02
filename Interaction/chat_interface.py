"""
PenphinMind Chat Interface
Interactive chat console for PenphinMind

This module provides the interactive user interface for chat
interactions, using the ChatManager to handle the communication
with the Mind system.
"""

import asyncio
import time
from typing import Optional, Any

from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.config import CONFIG
from Interaction.chat_manager import ChatManager

# Initialize journaling
journaling = SystemJournelingManager(CONFIG.log_level)

async def interactive_chat(mind=None):
    """
    Interactive chat interface for PenphinMind
    
    This function provides a text-based interface for chatting with the LLM.
    It uses the ChatManager to handle the communication with Mind.
    
    Args:
        mind: The Mind instance to use for communication
    """
    if not mind:
        journaling.recordError("[Chat] No Mind instance provided")
        print("Error: Mind not initialized")
        return
        
    journaling.recordInfo("[Chat] Starting interactive chat session")
    
    # Initialize the chat manager with the Mind instance
    chat_manager = ChatManager(mind)
    
    # Print welcome messages
    print_chat_header()
    print("Type your message and press Enter. Type 'exit' to return to the main menu.\n")
    
    # Initialize chat with default or auto-selected model
    print("Initializing chat system...")
    init_success = await chat_manager.initialize()
    
    if not init_success:
        print("Failed to initialize chat. Please check your connection and try again.")
        input("Press Enter to return to the main menu...")
        return
    
    # Show which model is active
    model_info = chat_manager.get_summary()
    print(f"Using model: {model_info['model']}\n")
    
    # Main chat loop
    while True:
        # Get user input
        user_input = input("🧠 You: ").strip()

        # Handle exit
        if user_input.lower() in ("exit", "quit", "menu"):
            journaling.recordInfo("[Chat] Ending session")
            print("Returning to main menu...")
            break

        # Skip empty input
        if not user_input:
            continue

        # Handle reset command
        if user_input.lower() == "reset":
            print("\nResetting LLM...")
            reset_result = await chat_manager.reset_chat()
            if reset_result.get("status") == "ok":
                print("LLM has been reset.\n")
            else:
                print(f"Reset failed: {reset_result.get('message', 'Unknown error')}\n")
            continue

        # Process thinking with streaming
        print("\n🐧🐬 PenphinMind: ", end="", flush=True)
        
        try:
            # Use chat_manager to send message with streaming
            response = await chat_manager.send_message(user_input, stream=True)
            
            if hasattr(response, "active"):  # It's a task
                # Wait for the task to complete, showing streaming results
                last_result = ""
                while response.active:
                    if hasattr(response, 'result') and response.result and response.result != last_result:
                        # Only print the new part of the response
                        new_part = response.result[len(last_result):]
                        print(new_part, end="", flush=True)
                        last_result = response.result
                    await asyncio.sleep(0.1)
                
                # Print any final result not yet displayed
                if hasattr(response, 'result') and response.result and response.result != last_result:
                    new_part = response.result[len(last_result):]
                    print(new_part, end="", flush=True)
                    
                # Make sure task properly stops
                if response.active and hasattr(response, 'stop') and callable(response.stop):
                    response.stop()
            elif isinstance(response, dict) and response.get("status") == "error":
                # Handle error response
                print(f"Error: {response.get('message', 'Unknown error')}")
                
                # If there's a model error, try an alternative one
                if "model" in str(response.get("message", "")).lower():
                    print("\nTrying an alternative model...")
                    if await chat_manager.try_alternative_model():
                        print("Switched to an alternative model. Please try again.")
                    else:
                        print("No alternative models available.")
            else:
                # Handle direct response
                print(response)
                    
        except Exception as e:
            journaling.recordError(f"Error in chat: {e}")
            import traceback
            journaling.recordError(f"Stack trace: {traceback.format_exc()}")
            print(f"Error processing your request: {e}")
            
        print()  # Add newline after response

def print_chat_header():
    """Print the chat interface header with penguin and dolphin emojis"""
    print("\n" + "=" * 60)
    print("                 🐧 PenphinMind Chat 🐬")
    print("=" * 60)
