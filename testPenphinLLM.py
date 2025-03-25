#!/usr/bin/env python3
import asyncio
import logging
import platform
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import sounddevice as sd
import numpy as np
import time
import sys

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from PenphinMind.mind import Mind
from config import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Default to INFO if config not available
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PenphinOS")

class AIType(Enum):
    """Available AI types"""
    LOCAL = "local"
    CLOUD = "cloud"
    CUSTOM = "custom"

class TestMode(Enum):
    """Available test modes"""
    TEXT = "text"
    AUDIO = "audio"
    INTEGRATED = "integrated"

class TestPenphinLLM:
    """Test class for PenphinLLM functionality"""
    
    def __init__(self):
        self.logger = logger
        self.mind = Mind()
        self.running = True
        
    async def initialize(self) -> None:
        """Initialize the test environment"""
        try:
            await self.mind.initialize()
            self.logger.info("Test environment initialized successfully")
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise
            
    async def test_text_mode(self, prompt: str) -> Dict[str, Any]:
        """Test LLM in text mode"""
        try:
            # Use mind's temporal lobe for text processing
            response = await self.mind.temporal_lobe["auditory"].process_text(prompt)
            return {"response": response}
        except Exception as e:
            self.logger.error(f"Text mode test error: {e}")
            raise
            
    async def test_audio_mode(self, duration: float = 5.0) -> Dict[str, Any]:
        """Test LLM in audio mode"""
        try:
            # Record audio
            self.logger.info(f"Recording audio for {duration} seconds...")
            audio_data = await self.mind.temporal_lobe["auditory"].record_audio(duration)
            
            # Process audio
            text = await self.mind.understand_speech(audio_data)
            self.logger.info(f"Understood text: {text}")
            
            # Generate response
            response_audio = await self.mind.generate_speech(text)
            
            return {
                "text": text,
                "audio": response_audio
            }
        except Exception as e:
            self.logger.error(f"Audio mode test error: {e}")
            raise
            
    async def test_integrated_mode(self) -> None:
        """Test LLM in integrated mode"""
        try:
            # Start listening
            await self.mind.start_listening()
            
            while self.running:
                # Process any incoming audio
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Integrated mode test error: {e}")
            raise
        finally:
            self.mind.stop_listening()
            
    async def cleanup(self) -> None:
        """Clean up resources"""
        self.running = False
        self.mind.stop_listening()
        
    async def chat(self) -> None:
        """Interactive chat mode"""
        try:
            print("\nEntering chat mode. Type 'exit' to quit.")
            while self.running:
                user_input = input("\nYou: ")
                if user_input.lower() == 'exit':
                    break
                    
                response = await self.test_text_mode(user_input)
                print(f"\nPenphinMind: {response['response']}")
                
        except Exception as e:
            self.logger.error(f"Chat error: {e}")
            raise
        finally:
            await self.cleanup()
            
    async def run_menu(self):
        """Run the test menu"""
        try:
            await self.initialize()
            
            while self.running:
                print("\nPenphinLLM Test Menu:")
                print("1. Text Mode")
                print("2. Audio Mode")
                print("3. Integrated Mode")
                print("4. Chat Mode")
                print("5. Exit")
                
                choice = input("\nSelect an option (1-5): ")
                
                if choice == "1":
                    prompt = input("Enter your prompt: ")
                    response = await self.test_text_mode(prompt)
                    print(f"\nResponse: {response['response']}")
                elif choice == "2":
                    response = await self.test_audio_mode()
                    print(f"\nUnderstood text: {response['text']}")
                elif choice == "3":
                    print("\nStarting integrated mode... Press Ctrl+C to exit")
                    await self.test_integrated_mode()
                elif choice == "4":
                    await self.chat()
                elif choice == "5":
                    break
                else:
                    print("Invalid option. Please try again.")
                    
        except Exception as e:
            self.logger.error(f"Menu error: {e}")
            raise
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    tester = TestPenphinLLM()
    await tester.run_menu()

if __name__ == "__main__":
    asyncio.run(main()) 