"""
PenphinMind Chat Interface
Interactive chat console for PenphinMind

This module provides the interactive user interface for chat
interactions, using the ChatManager to handle the communication
with the Mind system.
"""

import os
import asyncio
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path

from Mind.mind import Mind
from .chat_manager import ChatManager
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from config import CONFIG  # Use absolute import

# Initialize journaling
journaling = SystemJournelingManager(CONFIG.log_level)

async def interactive_chat(primary_mind: Mind, secondary_mind: Mind = None):
    """Interactive chat with one or two minds
    
    Args:
        primary_mind: Primary mind instance for chat
        secondary_mind: Optional second mind for mind-to-mind chat
    """
    is_dual_mode = secondary_mind is not None
    
    # Display mind identities
    print("\n" + primary_mind.format_identity())
    if is_dual_mode:
        print(secondary_mind.format_identity())
        print("\n🔄 Mind-to-Mind Chat Mode")
    else:
        print("\n👤 User Chat Mode")
    
    # Check connections
    print("\n🔍 Checking connections...")
    p_status = await primary_mind.check_connection()
    if p_status.get("status") != "ok":
        print(f"⚠️ Error connecting to {primary_mind.name}: {p_status.get('message')}")
        print(f"⚠️ You may need to reset the device or check connection settings.")
        return
    else:
        print(f"✅ Successfully connected to {primary_mind.name}")
        
    if is_dual_mode:
        s_status = await secondary_mind.check_connection()
        if s_status.get("status") != "ok":
            print(f"⚠️ Error connecting to {secondary_mind.name}: {s_status.get('message')}")
            return
        else:
            print(f"✅ Successfully connected to {secondary_mind.name}")
    
    # Display hardware info
    print("\n🖥️ Hardware Information:")
    hw_info = await primary_mind.get_hardware_info()
    if hw_info.get("status") == "ok":
        print(hw_info.get("hardware_info"))
    else:
        print(f"⚠️ Could not retrieve hardware info: {hw_info.get('message')}")
    
    if is_dual_mode:
        hw_info = await secondary_mind.get_hardware_info()
        if hw_info.get("status") == "ok":
            print(hw_info.get("hardware_info"))
        else:
            print(f"⚠️ Could not retrieve hardware info: {hw_info.get('message')}")
    
    # Get active model
    try:
        model_info = await primary_mind.get_model()
        if model_info.get("status") == "ok":
            print(f"🧠 Active model: {model_info.get('model', 'Unknown')}")
        else:
            print(f"⚠️ Could not retrieve model info: {model_info.get('message')}")
    except Exception as e:
        print(f"⚠️ Error getting model info: {str(e)}")
    
    print("\n💭 Chat session started\n")
    
    while True:
        if is_dual_mode:
            # Mind to mind chat
            response = await primary_mind.process_thought("What would you like to discuss?")
            if response.get("status") != "ok":
                print(f"\n⚠️ Error: {response.get('message')}")
                continue
                
            print(f"\n{primary_mind.name}: {response.get('response')}")
            
            # Get second mind's response
            response = await secondary_mind.process_thought(response.get('response'))
            if response.get("status") == "ok":
                print(f"\n{secondary_mind.name}: {response.get('response')}")
            
        else:
            # Normal user chat
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ("exit", "quit", "menu"):
                print("\n🔚 Exiting chat session...")
                break
                
            if not user_input:
                continue
                
            print(f"\n{primary_mind.name}: ", end="", flush=True)
            response = await primary_mind.process_thought(user_input)
            
            if response.get("status") == "ok":
                print(response.get("response"))
            else:
                print(f"⚠️ Error: {response.get('message')}")

def print_chat_header():
    """Print the chat interface header with penguin and dolphin emojis"""
    print("\n" + "=" * 60)
    print("                 🐧 PenphinMind Chat 🐬")
    print("=" * 60)
