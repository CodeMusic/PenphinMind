#!/usr/bin/env python3
import asyncio
import logging
import platform
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from CorpusCallosum.synaptic_pathways import SynapticPathways
from CorpusCallosum.neural_commands import (
    CommandType,
    LLMCommand,
    TTSCommand,
    BaseCommand
)
from config import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestPenphinLLM")

class AIType(Enum):
    """Available AI types"""
    LOCAL = "local"
    CLOUD = "cloud"
    CUSTOM = "custom"

class CortexCategory(Enum):
    """Neural cortex categories"""
    AUDITORY = "AuditoryCortex"
    BICAMERAL = "BicameralCortex"
    FRONTAL = "FrontalLobe"
    HIPPOCAMPUS = "Hippocampus"
    OCCIPITAL = "OccipitalLobe"
    PARIETAL = "ParietalLobe"
    SOMATOSENSORY = "SomatosensoryCortex"
    TEMPORAL = "TemporalLobe"
    THALAMUS = "Thalamus"
    PENDING = "Pending Integration"

class TestPenphinLLM:
    """Test class for PenphinLLM functionality"""
    
    def __init__(self):
        self.logger = logger
        self.is_raspberry_pi = platform.system() == "Linux" and "raspberrypi" in platform.platform().lower()
        self.ai_type: Optional[AIType] = None
        self.custom_endpoint: Optional[str] = None
        self.model: str = "gpt-3.5-turbo"
        self.available_functions: Dict[str, List[str]] = {}
        self.chat_history: List[Dict[str, str]] = []
        self._load_available_functions()
        
    def _load_available_functions(self) -> None:
        """Load available functions from neural_commands"""
        # Get all command types
        command_types = [cmd.value for cmd in CommandType]
        
        # Get all cortex directories
        cortex_dirs = [cortex.value for cortex in CortexCategory]
        
        # Initialize function dictionary
        self.available_functions = {
            cortex: [] for cortex in cortex_dirs
        }
        
        # Map commands to their respective cortices
        for cmd in command_types:
            if cmd.startswith("AUDIO") or cmd.startswith("TTS") or cmd.startswith("ASR"):
                self.available_functions[CortexCategory.AUDITORY.value].append(cmd)
            elif cmd.startswith("LLM") or cmd.startswith("VLM"):
                self.available_functions[CortexCategory.BICAMERAL.value].append(cmd)
            elif cmd.startswith("BUTTON") or cmd.startswith("GPIO"):
                self.available_functions[CortexCategory.SOMATOSENSORY.value].append(cmd)
            elif cmd.startswith("CAMERA") or cmd.startswith("YOLO"):
                self.available_functions[CortexCategory.OCCIPITAL.value].append(cmd)
            elif cmd.startswith("MEMORY") or cmd.startswith("LEARNING"):
                self.available_functions[CortexCategory.HIPPOCAMPUS.value].append(cmd)
            elif cmd.startswith("SYSTEM"):
                self.available_functions[CortexCategory.THALAMUS.value].append(cmd)
            else:
                self.available_functions[CortexCategory.PENDING.value].append(cmd)
                
    async def initialize(self):
        """Initialize the test environment"""
        try:
            await SynapticPathways.initialize()
            self.logger.info(f"Running in {'hardware' if self.is_raspberry_pi else 'test'} mode")
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise
            
    async def get_device_functions(self) -> Dict[str, List[str]]:
        """Get available functions from the device"""
        try:
            response = await SynapticPathways.send_system_command("get_functions")
            return response.get("functions", {})
        except Exception as e:
            self.logger.error(f"Error getting device functions: {e}")
            return {}
            
    def display_function_status(self, device_functions: Dict[str, List[str]]) -> None:
        """Display available and pending functions"""
        print("\nFunction Status by Cortex:")
        print("=" * 50)
        
        for cortex, functions in self.available_functions.items():
            print(f"\n{cortex}:")
            print("-" * 30)
            
            # Get device functions for this cortex
            device_cortex_functions = device_functions.get(cortex, [])
            
            # Show implemented functions
            print("Implemented:")
            for func in functions:
                if func in device_cortex_functions:
                    print(f"  ✓ {func}")
                else:
                    print(f"  ✗ {func} (Not available on device)")
                    
            # Show device-only functions
            device_only = [f for f in device_cortex_functions if f not in functions]
            if device_only:
                print("\nDevice-only functions:")
                for func in device_only:
                    print(f"  ! {func} (Not integrated in code)")
                    
    async def select_ai_type(self) -> None:
        """Select AI type and configure"""
        print("\nSelect AI Type:")
        print("1. Local AI (Raspberry Pi)")
        print("2. Cloud AI (OpenAI)")
        print("3. Custom AI (OpenAI-compatible endpoint)")
        
        while True:
            try:
                choice = int(input("\nEnter your choice (1-3): "))
                if choice == 1:
                    self.ai_type = AIType.LOCAL
                    break
                elif choice == 2:
                    self.ai_type = AIType.CLOUD
                    break
                elif choice == 3:
                    self.ai_type = AIType.CUSTOM
                    self.custom_endpoint = input("Enter OpenAI-compatible endpoint URL: ")
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
                
    async def show_model_options(self) -> None:
        """Show and select AI model options"""
        if self.ai_type == AIType.LOCAL:
            print("\nLocal AI Models:")
            print("1. Default Model")
            print("2. List Available Models")
        else:
            print("\nCloud AI Models:")
            print("1. GPT-3.5 Turbo")
            print("2. GPT-4")
            print("3. Custom Model")
            
        while True:
            try:
                choice = int(input("\nEnter your choice: "))
                if self.ai_type == AIType.LOCAL:
                    if choice == 1:
                        self.model = "default"
                        break
                    elif choice == 2:
                        # Get available models from device
                        response = await SynapticPathways.send_system_command("list_models")
                        models = response.get("models", [])
                        print("\nAvailable Models:")
                        for i, model in enumerate(models, 1):
                            print(f"{i}. {model}")
                        model_choice = int(input("\nSelect model number: "))
                        if 1 <= model_choice <= len(models):
                            self.model = models[model_choice - 1]
                            break
                else:
                    if choice == 1:
                        self.model = "gpt-3.5-turbo"
                        break
                    elif choice == 2:
                        self.model = "gpt-4"
                        break
                    elif choice == 3:
                        self.model = input("Enter custom model name: ")
                        break
                print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
                
    async def show_help(self) -> None:
        """Show help information"""
        print("\nPenphinOS Test Interface Help:")
        print("=" * 50)
        print("\nAvailable Commands:")
        print("1. test - Run basic test sequence")
        print("2. model - Change AI model")
        print("3. functions - Show available functions")
        print("4. chat - Enter chat mode with command support")
        print("5. help - Show this help message")
        print("6. exit - Exit the program")
        print("\nChat Mode Commands:")
        print("- Use [command] syntax for instructions")
        print("- Type 'exit' to return to menu")
        print("- Example: [process audio] [convert to text] [generate response]")
        
    async def test_llm(self, prompt: str) -> Dict[str, Any]:
        """Test LLM functionality"""
        try:
            command = LLMCommand(
                command_type=CommandType.LLM,
                prompt=prompt,
                max_tokens=100,
                temperature=0.7
            )
            response = await SynapticPathways.transmit_json(command)
            self.logger.info(f"LLM Response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"LLM test error: {e}")
            raise
            
    async def test_tts(self, text: str) -> Dict[str, Any]:
        """Test TTS functionality"""
        try:
            command = TTSCommand(
                command_type=CommandType.TTS,
                text=text,
                voice_id="en-US-1",
                speed=1.0,
                pitch=1.0
            )
            response = await SynapticPathways.transmit_json(command)
            self.logger.info(f"TTS Response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"TTS test error: {e}")
            raise
            
    async def run_tests(self):
        """Run all tests"""
        try:
            # Test LLM
            await self.test_llm("What is the meaning of life?")
            
            # Test TTS
            await self.test_tts("Hello, this is a test of the text to speech system.")
            
        except Exception as e:
            self.logger.error(f"Test error: {e}")
            raise
            
    async def cleanup(self):
        """Clean up resources"""
        await SynapticPathways.close_connections()

    def _parse_command_instructions(self, text: str) -> List[str]:
        """Extract command instructions from square brackets"""
        pattern = r'\[(.*?)\]'
        return re.findall(pattern, text)

    async def _process_command_instructions(self, instructions: List[str]) -> str:
        """Process command instructions and return action plan"""
        try:
            # Create a prompt that includes available functions and instructions
            prompt = f"""You are PenphinOS, an AI assistant with access to various neural functions.
Available functions by cortex:
{json.dumps(self.available_functions, indent=2)}

The following command instructions were received:
{json.dumps(instructions, indent=2)}

Please analyze these instructions and provide a detailed action plan that:
1. Identifies which functions should be used
2. Specifies the order of operations
3. Notes any potential issues or requirements
4. Suggests any additional functions that might be needed

Format your response in a clear, structured way."""

            command = LLMCommand(
                command_type=CommandType.LLM,
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )
            response = await SynapticPathways.transmit_json(command)
            return response.get("response", "Failed to generate action plan")
        except Exception as e:
            self.logger.error(f"Error processing command instructions: {e}")
            return f"Error processing command instructions: {str(e)}"

    async def chat(self) -> None:
        """Enter chat mode with command instruction support"""
        print("\nEntering Chat Mode")
        print("Commands:")
        print("- [command] - Use square brackets for instructions")
        print("- ? or help - Show help information")
        print("- menu or exit - Return to main menu")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                # Handle special commands
                if user_input.lower() in ['menu', 'exit']:
                    break
                elif user_input.lower() in ['?', 'help']:
                    print("\nChat Mode Help:")
                    print("=" * 50)
                    print("Regular Chat:")
                    print("- Just type your message for a conversation")
                    print("\nCommand Instructions:")
                    print("- Use [command] syntax for instructions")
                    print("- Example: [process audio] [convert to text]")
                    print("\nSpecial Commands:")
                    print("- ? or help - Show this help message")
                    print("- menu or exit - Return to main menu")
                    print("\nAvailable Functions:")
                    for cortex, functions in self.available_functions.items():
                        if functions:
                            print(f"\n{cortex}:")
                            for func in functions:
                                print(f"  - {func}")
                    continue
                    
                # Check for command instructions
                instructions = self._parse_command_instructions(user_input)
                
                if instructions:
                    print("\nProcessing command instructions...")
                    action_plan = await self._process_command_instructions(instructions)
                    print("\nAction Plan:")
                    print(action_plan)
                    
                    # Add to chat history
                    self.chat_history.append({
                        "role": "user",
                        "content": user_input
                    })
                    self.chat_history.append({
                        "role": "assistant",
                        "content": action_plan
                    })
                else:
                    # Regular chat interaction
                    command = LLMCommand(
                        command_type=CommandType.LLM,
                        prompt=user_input,
                        max_tokens=150,
                        temperature=0.7
                    )
                    response = await SynapticPathways.transmit_json(command)
                    assistant_response = response.get("response", "")
                    
                    print(f"\nAssistant: {assistant_response}")
                    
                    # Add to chat history
                    self.chat_history.append({
                        "role": "user",
                        "content": user_input
                    })
                    self.chat_history.append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                    
            except Exception as e:
                self.logger.error(f"Chat error: {e}")
                print(f"\nError: {str(e)}")
                
    async def run_menu(self):
        """Run the main menu system"""
        try:
            # Select AI type
            await self.select_ai_type()
            
            while True:
                print("\nPenphinOS Test Interface")
                print("=" * 50)
                print(f"AI Type: {self.ai_type.value}")
                print(f"Model: {self.model}")
                print("\nOptions:")
                print("1. Run Tests")
                print("2. Change Model")
                print("3. Show Functions")
                print("4. Chat Mode")
                print("5. Help")
                print("6. Exit")
                
                try:
                    choice = int(input("\nEnter your choice: "))
                    
                    if choice == 1:
                        await self.run_tests()
                    elif choice == 2:
                        await self.show_model_options()
                    elif choice == 3:
                        if self.ai_type == AIType.LOCAL:
                            device_functions = await self.get_device_functions()
                            self.display_function_status(device_functions)
                        else:
                            print("\nFunction status only available for Local AI")
                    elif choice == 4:
                        await self.chat()
                    elif choice == 5:
                        await self.show_help()
                    elif choice == 6:
                        break
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
                    
        except Exception as e:
            self.logger.error(f"Menu error: {e}")
            raise
        finally:
            await self.cleanup()

async def main():
    """Main test function"""
    tester = TestPenphinLLM()
    try:
        await tester.initialize()
        await tester.run_menu()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 